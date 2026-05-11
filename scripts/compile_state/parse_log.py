#!/usr/bin/env python3
"""Extract overfull/underfull boxes and float-defer warnings from a .log.

CLI:
    python parse_log.py <main.log> [--out <json>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_RE_OVERFULL = re.compile(
    r"^Overfull \\hbox \(([\d.]+)pt too wide\) in paragraph at lines (\d+)--(\d+)"
)
_RE_UNDERFULL = re.compile(r"^Underfull \\vbox .* at lines (\d+)--(\d+)")
_RE_FLOAT_DEFER = re.compile(r"`!t' float specifier changed to `!tp'")
_RE_FLOAT_NOT_ON_PAGE = re.compile(r"Float .* not on page")
_RE_FLOAT_TOO_LARGE = re.compile(r"Float too large for page")


def parse_log(log_path: Path) -> dict:
    overfull = []
    underfull = []
    float_warnings = []

    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    for ln in lines:
        m = _RE_OVERFULL.match(ln)
        if m:
            overfull.append(
                {
                    "overflow_pt": float(m.group(1)),
                    "line_start": int(m.group(2)),
                    "line_end": int(m.group(3)),
                }
            )
            continue
        m = _RE_UNDERFULL.match(ln)
        if m:
            underfull.append(
                {"line_start": int(m.group(1)), "line_end": int(m.group(2))}
            )
            continue
        if (
            _RE_FLOAT_DEFER.search(ln)
            or _RE_FLOAT_NOT_ON_PAGE.search(ln)
            or _RE_FLOAT_TOO_LARGE.search(ln)
        ):
            float_warnings.append({"raw": ln.strip()})

    return {
        "overfull_hbox": overfull,
        "underfull_vbox": underfull,
        "float_warnings": float_warnings,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("log")
    p.add_argument("--out")
    args = p.parse_args(argv)

    out = parse_log(Path(args.log).resolve())
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
