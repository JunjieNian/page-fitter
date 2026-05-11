#!/usr/bin/env python3
"""Bundle compile_once / parse_pdf / parse_synctex / parse_log into one
state.json. See references/output-schema.md.

CLI:
    python snapshot.py <main.tex> --out <state.json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# We import sibling modules. Allow running as a script.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compile_once  # noqa: E402
import parse_log  # noqa: E402
import parse_pdf  # noqa: E402
import parse_synctex  # noqa: E402


def _attach_synctex_to_blocks(pdf_state: dict, synctex_parsed: dict) -> list[str]:
    """Attach a synctex {file, first_line, last_line} to every block, by
    nearest-neighbor reverse lookup of block bbox center.

    Returns a list of warnings (block_ids without a synctex link)."""
    rev = synctex_parsed["reverse"]
    warnings: list[str] = []
    for page in pdf_state["pages"]:
        for blk in page["blocks"]:
            x = (blk["bbox"][0] + blk["bbox"][2]) / 2.0
            # SyncTeX y origin is top-left, PyMuPDF y origin is also top-left
            # for fitz coordinates, so we can compare directly. We accept some
            # imprecision and use a generous tolerance.
            y = (blk["bbox"][1] + blk["bbox"][3]) / 2.0
            hit = parse_synctex.reverse_lookup(rev, page["page"], x, y, tol=80.0)
            if hit is None:
                blk["synctex"] = None
                if blk.get("kind") == "paragraph":
                    warnings.append(blk["block_id"])
                continue
            f, ln = hit
            blk["synctex"] = {"file": f, "first_line": ln, "last_line": ln}
    return warnings


def build_snapshot(main_tex: Path, force: bool = False, compiler: str | None = None) -> dict:
    project_root = main_tex.parent

    # Step 1: compile if needed.
    if compile_once.needs_compile(main_tex, force):
        compile_once.run_latexmk(main_tex, compiler_override=compiler)

    pdf_path = main_tex.with_suffix(".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not produced: {pdf_path}")
    pdf_state = parse_pdf.parse_pdf(pdf_path)

    synctex_index = project_root / (main_tex.stem + ".synctex.gz")
    if not synctex_index.exists():
        synctex_index = project_root / (main_tex.stem + ".synctex")
    synctex_parsed = parse_synctex.parse_synctex_index(synctex_index)
    synctex_meta = parse_synctex.serialize(synctex_parsed)
    missing_blocks = _attach_synctex_to_blocks(pdf_state, synctex_parsed)
    if missing_blocks:
        synctex_meta["warnings"].append(
            {"unmapped_blocks": missing_blocks[:50], "count": len(missing_blocks)}
        )

    log_path = main_tex.with_suffix(".log")
    log_state = parse_log.parse_log(log_path) if log_path.exists() else {}

    return {
        "schema_version": "1.0",
        "main_tex": main_tex.name,
        "project_root": str(project_root),
        "pdf": pdf_state,
        "synctex": synctex_meta,
        "log": log_state,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("main_tex")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--compiler", default=None)
    args = p.parse_args(argv)

    main_tex = Path(args.main_tex).resolve()
    snap = build_snapshot(main_tex, force=args.force, compiler=args.compiler)
    Path(args.out).write_text(json.dumps(snap, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
