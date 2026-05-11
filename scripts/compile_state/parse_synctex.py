#!/usr/bin/env python3
"""Wrap `synctex view` / `synctex edit` into a Python interface.

Builds two indices:
    - forward: (file, line) -> [(page, x, y, w, h), ...]
    - reverse: query by (page, x, y) -> (file, line)

The reverse query is implemented as approximate nearest-neighbor by
linear scan; for the small papers we target (≤ 30 pages, ≤ a few thousand
records), a KDTree is overkill.

CLI:
    python parse_synctex.py <main.tex> [--out <json>]

The JSON output is the `synctex` section plus a per-block `synctex` link
that callers can splice into the parse_pdf.py block list.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

_RE_INPUT = re.compile(r"^Input:(\d+):(.+)$")
_RE_PAGE = re.compile(r"^\{(\d+)$")
_RE_RECORD_BOX = re.compile(
    r"^[hvxk](?P<tag>\d+),(?P<line>\d+)(?:,\d+)?:(?P<x>-?\d+),(?P<y>-?\d+)(?::(?P<w>-?\d+),(?P<h>-?\d+),(?P<d>-?\d+))?$"
)


def _open_synctex(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def parse_synctex_index(synctex_path: Path) -> dict:
    """Best-effort parser of the textual SyncTeX index format.

    Returns a dict with two indices keyed for downstream use. We deliberately
    avoid trying to be a complete SyncTeX parser; we extract just enough to
    build forward + reverse maps over text records.
    """
    files: dict[int, str] = {}
    forward: dict[tuple[str, int], list[tuple[int, float, float, float, float]]] = {}
    reverse: list[tuple[int, float, float, str, int]] = []

    current_page: int | None = None
    current_file: int | None = None  # noqa: F841

    with _open_synctex(synctex_path) as fh:
        for raw in fh:
            line = raw.rstrip("\n")

            m_in = _RE_INPUT.match(line)
            if m_in:
                tag = int(m_in.group(1))
                files[tag] = m_in.group(2)
                continue

            m_pg = _RE_PAGE.match(line)
            if m_pg:
                current_page = int(m_pg.group(1))
                continue

            m_rec = _RE_RECORD_BOX.match(line)
            if m_rec and current_page is not None:
                tag = int(m_rec.group("tag"))
                src_line = int(m_rec.group("line"))
                # SyncTeX coordinates: integer scaled-points (sp); 65536 sp = 1 pt
                x = int(m_rec.group("x")) / 65536.0
                y = int(m_rec.group("y")) / 65536.0
                w = float(m_rec.group("w") or 0) / 65536.0
                h = float(m_rec.group("h") or 0) / 65536.0
                src_file = files.get(tag, f"<tag-{tag}>")
                key = (src_file, src_line)
                forward.setdefault(key, []).append((current_page, x, y, w, h))
                reverse.append((current_page, x, y, src_file, src_line))

    return {
        "files": files,
        "forward": forward,
        "reverse": reverse,
    }


def reverse_lookup(reverse_index, page: int, x: float, y: float, tol: float = 12.0):
    """Approximate reverse: nearest record on the same page within `tol` points."""
    best = None
    best_d2 = None
    for p, rx, ry, f, ln in reverse_index:
        if p != page:
            continue
        dx = rx - x
        dy = ry - y
        d2 = dx * dx + dy * dy
        if best_d2 is None or d2 < best_d2:
            best_d2 = d2
            best = (f, ln)
    if best is None:
        return None
    if best_d2 ** 0.5 > tol:
        return None
    return best


def serialize(parsed: dict) -> dict:
    """JSON-friendly form (drops the in-memory KDTree-ish list, keeps stats)."""
    fwd = parsed["forward"]
    out = {
        "available": True,
        "files": parsed["files"],
        "forward_index_size": sum(len(v) for v in fwd.values()),
        "warnings": [],
    }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("main_tex")
    p.add_argument("--out")
    args = p.parse_args(argv)

    main_tex = Path(args.main_tex).resolve()
    project_root = main_tex.parent
    candidate = project_root / (main_tex.stem + ".synctex.gz")
    if not candidate.exists():
        candidate = project_root / (main_tex.stem + ".synctex")
    if not candidate.exists():
        sys.stderr.write(
            f"SyncTeX index missing for {main_tex.name}.\n"
            f"  Re-compile with: latexmk -synctex=1 -pdf {main_tex.name}\n"
        )
        return 2

    parsed = parse_synctex_index(candidate)
    out = serialize(parsed)
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
