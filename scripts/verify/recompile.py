#!/usr/bin/env python3
"""Verification compile + page-count diff.

CLI:
    python recompile.py <main.tex> --old-page-count N [--compiler "<cmd>"]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "compile_state"))

import compile_once  # noqa: E402


def _page_count(pdf: Path) -> int:
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError("PyMuPDF required for page-count diff.") from e
    return fitz.open(pdf).page_count


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("main_tex")
    p.add_argument("--old-page-count", type=int, required=True)
    p.add_argument("--compiler", default=None)
    args = p.parse_args(argv)

    main_tex = Path(args.main_tex).resolve()
    rc = compile_once.run_latexmk(main_tex, compiler_override=args.compiler)
    if rc != 0:
        sys.stderr.write(f"latex compile failed (rc={rc}); see .log for details.\n")
        return rc

    pdf = main_tex.with_suffix(".pdf")
    new_n = _page_count(pdf)
    out = {
        "old_page_count": args.old_page_count,
        "new_page_count": new_n,
        "delta": new_n - args.old_page_count,
        "pdf": str(pdf),
    }
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
