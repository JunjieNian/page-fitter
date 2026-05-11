#!/usr/bin/env python3
"""Final ranking + report writer. See references/boundary-scoring.md and output-schema.md.

CLI:
    python rank.py <state.json> <candidates.json> <layout.json> <floats.json>
                   [<semantic.json>] [--triage]
                   [--out report.md] [--json ranked.json]
                   [--page-limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import boundary_leverage  # noqa: E402
import layout_gain  # noqa: E402


# Triage type-class medians (mirror references/candidate-types.md).
_TRIAGE_COSTS = {
    "discourse_transition": 1,
    "caption_tail": 2,
    "cite_cluster": 1,
    "sentence_descriptive": 2,
    "sentence_claim": 4,
    "sentence_proof_step": 5,
    "section_opening": 3,
    "display_equation": 5,
}

EPS = 0.5
HIGH_THRESHOLD = 0.6
NOT_WORTH_THRESHOLD = 0.2


def _baseline_skip_for(state: dict, page_num: int) -> float:
    for page in state["pdf"]["pages"]:
        if page["page"] == page_num:
            return page.get("baseline_skip", 12.0)
    return 12.0


def _block(state: dict, block_id: str | None) -> dict | None:
    if not block_id:
        return None
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            if blk["block_id"] == block_id:
                return {**blk, "page_obj": page}
    return None


def _is_near_column_break(state: dict, blk: dict | None) -> bool:
    if not blk:
        return False
    page = blk["page_obj"]
    if len(page["columns"]) < 2:
        return False
    line_bboxes = blk.get("line_bboxes") or []
    if not line_bboxes:
        return False
    last_y = line_bboxes[-1][3]
    page_h = page["height"]
    return last_y >= page_h * 0.85


def _downstream_pullable(state: dict, block_id: str) -> bool:
    flat = []
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            flat.append(blk)
    for i, blk in enumerate(flat):
        if blk["block_id"] == block_id and i + 1 < len(flat):
            return flat[i + 1].get("kind") == "paragraph"
    return False


def _bucket(score: float, confidence: str, est_line_delta: float, rank_idx: int) -> str:
    if est_line_delta == 0:
        return "not_worth"
    if score <= NOT_WORTH_THRESHOLD:
        return "not_worth"
    if confidence == "low" and score < HIGH_THRESHOLD:
        return "not_worth"
    if score >= HIGH_THRESHOLD and rank_idx < 10:
        return "high_leverage"
    if rank_idx < 20:
        return "marginal"
    return "not_worth"


def _resolve_cost(c: dict, semantic: dict | None, triage: bool) -> int:
    if semantic and c["id"] in semantic.get("by_candidate", {}):
        return int(semantic["by_candidate"][c["id"]].get("semantic_cost", 3))
    if triage:
        return _TRIAGE_COSTS.get(c["type"], 3)
    return 3  # default neutral if neither path provided


def rank(
    state: dict,
    candidates: dict,
    layout: dict,
    floats: dict,
    semantic: dict | None,
    *,
    triage: bool,
    page_limit: int | None,
) -> dict:
    last_page = state["pdf"]["page_count"]
    scored = []

    for c in candidates["candidates"]:
        cid = c["id"]
        L = layout["by_candidate"].get(cid, {})
        F = floats["by_candidate"].get(cid, {})
        pdf_loc = c.get("pdf_loc") or {}

        est_delta = float(L.get("est_line_delta", 0.0))
        baseline = _baseline_skip_for(state, pdf_loc.get("page", 1)) if pdf_loc else 12.0
        height_saved = layout_gain.height_saved_pt(est_delta, baseline)

        blk = _block(state, pdf_loc.get("block_id"))
        is_last_page = pdf_loc.get("page") == last_page
        is_col_break = _is_near_column_break(state, blk)
        downstream_pullable = (
            _downstream_pullable(state, pdf_loc["block_id"])
            if pdf_loc.get("block_id") else False
        )

        leverage = boundary_leverage.compute(
            is_last_page=bool(is_last_page),
            is_near_column_break=is_col_break,
            downstream_paragraph_pullable=downstream_pullable,
            downstream_is_float_or_heading=bool(F.get("downstream_is_float_or_heading")),
            float_risk=float(F.get("float_risk", 0.0)),
        )

        cost = _resolve_cost(c, semantic, triage)
        p_reduce = float(L.get("P_reduce_line", 0.0))
        score = (p_reduce * height_saved * leverage) / max(cost, EPS)

        scored.append(
            {
                "id": cid,
                "score": round(score, 3),
                "components": {
                    "P_reduce_line": p_reduce,
                    "est_height_saved_pt": round(height_saved, 2),
                    "boundary_leverage": round(leverage, 3),
                    "semantic_cost": cost,
                    "float_risk": float(F.get("float_risk", 0.0)),
                },
                "confidence": L.get("confidence", "low"),
                "est_line_delta": est_delta,
                "candidate": c,
                "rationale": _rationale(c, L, F, is_last_page, downstream_pullable),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    for idx, item in enumerate(scored):
        item["bucket"] = _bucket(item["score"], item["confidence"], item["est_line_delta"], idx)

    summary = {
        "total_candidates": len(scored),
        "high_leverage": sum(1 for s in scored if s["bucket"] == "high_leverage"),
        "marginal": sum(1 for s in scored if s["bucket"] == "marginal"),
        "not_worth": sum(1 for s in scored if s["bucket"] == "not_worth"),
        "current_page_count": last_page,
        "page_limit": page_limit,
    }
    return {"schema_version": "1.0", "scored": scored, "summary": summary}


def _rationale(c, L, F, is_last_page, downstream_pullable) -> str:
    bits = []
    if is_last_page:
        bits.append("on last page")
    fill = L.get("last_line_fill_ratio", 0.0)
    bits.append(f"last-line fill {int(fill * 100)}%")
    if downstream_pullable:
        bits.append("next block is a paragraph (pullable)")
    if F.get("float_risk", 0):
        bits.append(f"float risk {F['float_risk']:.2f}")
    return "; ".join(bits)


def render_report(ranked: dict, *, triage: bool) -> str:
    s = ranked["summary"]
    lines = ["# page-fitter report", ""]
    if triage:
        lines.append(
            "> **Triage mode** — semantic cost is type-class median, not per-candidate. "
            "Re-run without `--triage` for a higher-confidence ranking before applying multi-edit batches."
        )
        lines.append("")
    cur = s["current_page_count"]
    lim = s["page_limit"]
    if lim is not None:
        delta = cur - lim
        if delta > 0:
            lines.append(f"Current: **{cur} pages** — limit: **{lim}** — need to lose: **{delta} page(s)**.")
        else:
            lines.append(f"Current: **{cur} pages** — limit: **{lim}** — already under limit.")
    else:
        lines.append(f"Current page count: **{cur}**.")
    lines.append("")

    def _section(title: str, bucket: str):
        items = [x for x in ranked["scored"] if x["bucket"] == bucket]
        lines.append(f"## {title} ({len(items)})")
        if not items:
            lines.append("_(none)_")
            lines.append("")
            return
        lines.append("| ID | File:Line | Type | Δ lines | Leverage | Cost | Conf | Rationale |")
        lines.append("|----|-----------|------|---------|----------|------|------|-----------|")
        for it in items:
            cand = it["candidate"]
            src = cand["src_loc"]
            lines.append(
                f"| {it['id']} | {src['file']}:{src['line']} | {cand['type']} | "
                f"{it['est_line_delta']:+.1f} | {it['components']['boundary_leverage']:.2f} | "
                f"{it['components']['semantic_cost']} | {it['confidence']} | {it['rationale']} |"
            )
        lines.append("")

    _section("High-leverage edits", "high_leverage")
    _section("Marginal edits", "marginal")
    _section("Not worth editing", "not_worth")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("state_json")
    p.add_argument("candidates_json")
    p.add_argument("layout_json")
    p.add_argument("floats_json")
    p.add_argument("semantic_json", nargs="?")
    p.add_argument("--triage", action="store_true")
    p.add_argument("--out", help="report.md path")
    p.add_argument("--json", help="ranked.json path")
    p.add_argument("--page-limit", type=int, default=None)
    args = p.parse_args(argv)

    state = json.loads(Path(args.state_json).read_text())
    candidates = json.loads(Path(args.candidates_json).read_text())
    layout = json.loads(Path(args.layout_json).read_text())
    floats = json.loads(Path(args.floats_json).read_text())
    semantic = json.loads(Path(args.semantic_json).read_text()) if args.semantic_json else None

    ranked = rank(
        state, candidates, layout, floats, semantic,
        triage=args.triage, page_limit=args.page_limit,
    )

    if args.json:
        Path(args.json).write_text(json.dumps(ranked, indent=2))
    if args.out:
        Path(args.out).write_text(render_report(ranked, triage=args.triage))
    if not (args.json or args.out):
        sys.stdout.write(json.dumps(ranked, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
