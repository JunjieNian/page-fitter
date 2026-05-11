#!/usr/bin/env python3
"""Per-paragraph line metrics for each candidate. See references/line-breaking.md.

Outputs layout.json (schema in references/output-schema.md).

CLI:
    python paragraph_lines.py <state.json> <candidates.json> [--out layout.json] [--fast]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import line_breaking_approx  # noqa: E402


def _block_lookup(state: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            out[blk["block_id"]] = {**blk, "page_obj": page}
    return out


def _last_line_fill_ratio(blk: dict) -> float:
    page_obj = blk["page_obj"]
    cols = page_obj["columns"]
    col = cols[blk["column"]] if blk["column"] < len(cols) else cols[0]
    col_w = max(col["text_width"], 1.0)

    line_bboxes = blk.get("line_bboxes") or []
    if not line_bboxes:
        return 0.0
    last = line_bboxes[-1]
    last_w = max(last[2] - last[0], 0.0)
    return min(last_w / col_w, 1.0)


def _word_width_estimate(text: str, col_w: float) -> float:
    """Crude width estimate: 5pt per char, scaled to fraction of col width."""
    if col_w <= 0:
        return 0.0
    pt_per_char = 5.0
    return min(len(text) * pt_per_char / col_w, 1.0)


def compute_layout(state: dict, candidates: dict, *, fast: bool) -> dict:
    blocks = _block_lookup(state)
    out: dict[str, dict] = {}

    for c in candidates["candidates"]:
        pdf_loc = c.get("pdf_loc")
        if not pdf_loc:
            out[c["id"]] = {
                "host_paragraph": None,
                "paragraph_line_count": 0,
                "last_line_fill_ratio": 0.0,
                "est_line_delta": 0.0,
                "confidence": "low",
                "P_reduce_line": 0.0,
            }
            continue

        blk = blocks.get(pdf_loc["block_id"])
        if not blk:
            out[c["id"]] = {
                "host_paragraph": None,
                "paragraph_line_count": 0,
                "last_line_fill_ratio": 0.0,
                "est_line_delta": 0.0,
                "confidence": "low",
                "P_reduce_line": 0.0,
            }
            continue

        page_obj = blk["page_obj"]
        cols = page_obj["columns"]
        col = cols[blk["column"]] if blk["column"] < len(cols) else cols[0]
        col_w = max(col["text_width"], 1.0)

        line_count = len(blk.get("line_bboxes") or [])
        fill = _last_line_fill_ratio(blk)
        text = c["src_loc"]["text"]
        word_frac = _word_width_estimate(text, col_w)
        p_reduce = max(0.0, min(1.0, fill + word_frac - 1.0))

        if fast:
            est_delta = -1.0 if p_reduce >= 0.5 else 0.0
            confidence = "medium" if p_reduce >= 0.7 or p_reduce <= 0.1 else "low"
        else:
            est_delta, confidence = line_breaking_approx.predict_line_delta(
                paragraph_line_count=line_count,
                col_width=col_w,
                last_line_fill_ratio=fill,
                deletion_text=text,
            )

        out[c["id"]] = {
            "host_paragraph": blk["block_id"],
            "paragraph_line_count": line_count,
            "last_line_fill_ratio": round(fill, 3),
            "est_line_delta": round(est_delta, 2),
            "confidence": confidence,
            "P_reduce_line": round(p_reduce, 3),
        }

    return {"schema_version": "1.0", "by_candidate": out}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("state_json")
    p.add_argument("candidates_json")
    p.add_argument("--out")
    p.add_argument("--fast", action="store_true")
    args = p.parse_args(argv)

    state = json.loads(Path(args.state_json).read_text())
    candidates = json.loads(Path(args.candidates_json).read_text())
    out = compute_layout(state, candidates, fast=args.fast)
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
