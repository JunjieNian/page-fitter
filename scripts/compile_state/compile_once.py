#!/usr/bin/env python3
"""Conditional first compile via the best available LaTeX compiler.

Auto-detects, in order:
    1. Explicit `--compiler <cmd>` flag (CLI) or `compiler_override` arg (lib).
    2. `PAGE_FITTER_LATEX_CMD` env var (full command, optionally with flags).
    3. `latexmk` on PATH.
    4. `pdflatex` / `xelatex` / `lualatex` on PATH (run twice for ref settling).

If `latexmk` is found, it is invoked with `-pdf -synctex=1 -interaction=nonstopmode -halt-on-error`.
Otherwise the chosen single-engine command is invoked twice with the same
`-synctex=1 -interaction=nonstopmode -halt-on-error` flags.

CLI:
    python compile_once.py <main.tex> [--force] [--compiler "<cmd ...>"]
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

_FALLBACK_ENGINES = ["pdflatex", "xelatex", "lualatex"]
_COMMON_FLAGS = ["-synctex=1", "-interaction=nonstopmode", "-halt-on-error"]


def _newest_source_mtime(project_root: Path) -> float:
    newest = 0.0
    for tex in project_root.rglob("*.tex"):
        if any(part.startswith(".") for part in tex.parts):
            continue
        mt = tex.stat().st_mtime
        if mt > newest:
            newest = mt
    return newest


def needs_compile(main_tex: Path, force: bool) -> bool:
    if force:
        return True
    project_root = main_tex.parent
    pdf = main_tex.with_suffix(".pdf")
    synctex = project_root / (main_tex.stem + ".synctex.gz")
    if not pdf.exists() or not synctex.exists():
        return True
    pdf_mt = pdf.stat().st_mtime
    synctex_mt = synctex.stat().st_mtime
    src_mt = _newest_source_mtime(project_root)
    return src_mt > min(pdf_mt, synctex_mt)


def detect_compiler(override: str | None = None) -> tuple[list[str], int]:
    """Return (argv_template, num_passes).

    `override` may be a string like "pdflatex" or "xelatex --shell-escape" or
    even a full path. If it begins with `latexmk`, we run once; otherwise twice.
    """
    raw = override or os.environ.get("PAGE_FITTER_LATEX_CMD")
    if raw:
        argv = shlex.split(raw)
        if not argv:
            raise RuntimeError("Empty compiler command.")
        if not shutil.which(argv[0]):
            raise RuntimeError(f"Compiler not found on PATH: {argv[0]!r}")
        # Ensure synctex / interaction flags are present; add if not.
        for flag in _COMMON_FLAGS:
            key = flag.split("=")[0]
            if not any(a == flag or a.startswith(key + "=") or a == key for a in argv[1:]):
                argv.append(flag)
        passes = 1 if Path(argv[0]).name == "latexmk" else 2
        if Path(argv[0]).name == "latexmk" and "-pdf" not in argv:
            argv.insert(1, "-pdf")
        return argv, passes

    # Auto-detect.
    if shutil.which("latexmk"):
        return ["latexmk", "-pdf", *_COMMON_FLAGS], 1
    for engine in _FALLBACK_ENGINES:
        if shutil.which(engine):
            return [engine, *_COMMON_FLAGS], 2
    raise RuntimeError(
        "No LaTeX compiler found. Install latexmk/pdflatex/xelatex/lualatex, "
        "or set PAGE_FITTER_LATEX_CMD to a custom command."
    )


def run_latexmk(main_tex: Path, compiler_override: str | None = None) -> int:
    """Compile `main_tex`. Name kept for backward compatibility — actually
    runs latexmk OR a 2-pass single-engine fallback, depending on what is
    available."""
    argv_base, passes = detect_compiler(compiler_override)
    cmd = argv_base + [main_tex.name]
    rc = 0
    for _ in range(passes):
        proc = subprocess.run(
            cmd,
            cwd=main_tex.parent,
            capture_output=True,
            text=True,
        )
        rc = proc.returncode
        if rc != 0:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            return rc
    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("main_tex")
    p.add_argument("--force", action="store_true")
    p.add_argument("--compiler", default=None,
                   help="Override compiler command (e.g. 'pdflatex' or 'xelatex --shell-escape'). "
                        "Can also be set via PAGE_FITTER_LATEX_CMD.")
    args = p.parse_args(argv)

    main_tex = Path(args.main_tex).resolve()
    if not main_tex.exists():
        print(f"main tex not found: {main_tex}", file=sys.stderr)
        return 2

    project_root = main_tex.parent
    pdf = main_tex.with_suffix(".pdf")
    synctex = project_root / (main_tex.stem + ".synctex.gz")
    log = main_tex.with_suffix(".log")

    ran = False
    rc = 0
    if needs_compile(main_tex, args.force):
        rc = run_latexmk(main_tex, compiler_override=args.compiler)
        ran = True
        if rc != 0:
            return rc

    argv_used, passes = detect_compiler(args.compiler)
    out = {
        "ran_compile": ran,
        "compiler": argv_used[0],
        "passes": passes,
        "pdf": str(pdf.relative_to(project_root)),
        "synctex": str(synctex.relative_to(project_root)) if synctex.exists() else None,
        "log": str(log.relative_to(project_root)) if log.exists() else None,
        "exit_code": rc,
        "project_root": str(project_root),
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
