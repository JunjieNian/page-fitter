#!/usr/bin/env python3
"""Mark candidates near pending floats. See references/float-placement.md.

CLI:
    python float_risk.py <state.json> <candidates.json> [--out floats.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RHO1 = 0.4  # float-adjacent
_RHO2 = 0.6  # upstream deferred float
_RHO3 = 0.8  # same-page float that already moved


def _block_lookup(state: dict) -> dict[str, dict]:
    out = {}
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            out[blk["block_id"]] = {**blk, "page_obj": page}
    return out


def _next_block(state: dict, current_block_id: str) -> dict | None:
    """Return the next text block in PDF reading order."""
    flat = []
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            flat.append(blk)
    for i, blk in enumerate(flat):
        if blk["block_id"] == current_block_id and i + 1 < len(flat):
            return flat[i + 1]
    return None


def compute_float_risk(state: dict, candidates: dict) -> dict:
    deferred = state.get("log", {}).get("float_warnings", [])
    has_any_deferred = bool(deferred)

    out: dict[str, dict] = {}

    for c in candidates["candidates"]:
        risk = 0.0
        near = []
        downstream_block_or_heading = False

        if c.get("tags", {}).get("float_adjacent"):
            risk += _RHO1
            near.append("float_env")

        if has_any_deferred:
            risk += _RHO2

        # downstream check: is the next block a float caption or a heading?
        pdf_loc = c.get("pdf_loc")
        if pdf_loc and pdf_loc.get("block_id"):
            nxt = _next_block(state, pdf_loc["block_id"])
            if nxt and nxt.get("kind") in {"caption", "heading", "float"}:
                downstream_block_or_heading = True

        risk = min(risk, 1.0)
        out[c["id"]] = {
            "float_risk": round(risk, 3),
            "near_floats": near,
            "downstream_is_float_or_heading": downstream_block_or_heading,
        }

    return {"schema_version": "1.0", "by_candidate": out}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("state_json")
    p.add_argument("candidates_json")
    p.add_argument("--out")
    args = p.parse_args(argv)

    state = json.loads(Path(args.state_json).read_text())
    candidates = json.loads(Path(args.candidates_json).read_text())
    out = compute_float_risk(state, candidates)
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
