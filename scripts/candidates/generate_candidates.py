#!/usr/bin/env python3
"""Produce candidates.json from state.json + a LaTeX project.

See references/candidate-types.md for the taxonomy.

CLI:
    python generate_candidates.py <state.json> [--filter near-boundary]
                                  [--out candidates.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import classify  # noqa: E402
import parse_latex  # noqa: E402

_DISCOURSE_PATTERNS = [
    r"\bFurthermore,\s*",
    r"\bMoreover,\s*",
    r"\bIn addition,\s*",
    r"\bIt is worth noting that,?\s*",
    r"\bAs mentioned (?:above|earlier),?\s*",
    r"\bAs we (?:have )?(?:seen|discussed),?\s*",
    r"\bIn other words,\s*",
    r"\bThat is to say,\s*",
]

_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\\])")

# Detects sentence text that *starts* with what looks like a leftover
# macro optional-/required-arg block (e.g. "[4][1-5]" after pylatexenc fails
# to consume \lipsum's optional args). Editing such a span would corrupt the
# preceding macro call.
_MACRO_RESIDUE = re.compile(r"^\s*[\[{][^\]\}]{0,40}[\]\}]")


def _split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Return (start, end, sentence) tuples within a chars block."""
    pieces: list[tuple[int, int, str]] = []
    cursor = 0
    for m in _SENT_END.finditer(text):
        end = m.start()
        seg = text[cursor:end].strip()
        if seg:
            pieces.append((cursor, end, seg))
        cursor = m.end()
    tail = text[cursor:].strip()
    if tail:
        pieces.append((cursor, len(text), tail))
    return pieces


def _candidate_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"c{counter[0]:03d}"


def _pdf_loc_for(state: dict, file_rel: str, line: int) -> dict | None:
    """Find the PDF block whose synctex range contains (file_rel, line)."""
    project_main = Path(state["main_tex"]).name
    for page in state["pdf"]["pages"]:
        for blk in page["blocks"]:
            sx = blk.get("synctex")
            if not sx:
                continue
            if Path(sx["file"]).name not in {file_rel, project_main, Path(file_rel).name}:
                continue
            if sx["first_line"] - 2 <= line <= sx["last_line"] + 2:
                bbox = blk["bbox"]
                return {
                    "page": page["page"],
                    "column": blk["column"],
                    "x": (bbox[0] + bbox[2]) / 2.0,
                    "y": (bbox[1] + bbox[3]) / 2.0,
                    "block_id": blk["block_id"],
                }
    return None


def _is_near_boundary(state: dict, pdf_loc: dict | None) -> bool:
    if pdf_loc is None:
        return False
    last_page = state["pdf"]["page_count"]
    if pdf_loc["page"] == last_page:
        return True
    if pdf_loc["page"] == last_page - 1 and pdf_loc.get("column", 0) >= 1:
        return True
    return False


def generate_candidates(state: dict, *, filter_near_boundary: bool = False) -> dict:
    project_root = Path(state["project_root"])
    main_tex = project_root / state["main_tex"]
    parsed = parse_latex.parse_project(main_tex)

    counter = [0]
    candidates: list[dict] = []

    def _line_offset(text: str, offset: int) -> int:
        return text.count("\n", 0, max(0, offset))

    for node in parsed["nodes"]:
        kind = node["kind"]
        text = node["text"]
        file_rel = node["file"]
        base_line = node["line"]

        # type-1: discourse transitions inside chars
        if kind == "chars":
            base_abs = node["col_start"]  # file-absolute start of this chars block
            for pat in _DISCOURSE_PATTERNS:
                for m in re.finditer(pat, text):
                    abs_start = base_abs + m.start()
                    abs_end = base_abs + m.end()
                    line_n = base_line + _line_offset(text, m.start())
                    pdf_loc = _pdf_loc_for(state, file_rel, line_n)
                    if filter_near_boundary and not _is_near_boundary(state, pdf_loc):
                        continue
                    candidates.append(
                        {
                            "id": _candidate_id(counter),
                            "type": "discourse_transition",
                            "src_loc": {
                                "file": file_rel,
                                "line": line_n,
                                "col_start": abs_start,
                                "col_end": abs_end,
                                "text": m.group(0).strip(),
                            },
                            "pdf_loc": pdf_loc,
                            "tags": classify.classify(node, "discourse_transition"),
                            "edit_action": "delete_span",
                            "edit_payload": None,
                        }
                    )

            # type-4/5/7: sentence-level candidates
            for s_start, s_end, sent in _split_sentences(text):
                if _MACRO_RESIDUE.match(sent):
                    # Skip — editing this would corrupt the preceding macro.
                    continue
                sent_type = classify.classify_sentence(sent, env_stack=node["env_stack"])
                abs_start = base_abs + s_start
                abs_end = base_abs + s_end
                line_n = base_line + _line_offset(text, s_start)
                pdf_loc = _pdf_loc_for(state, file_rel, line_n)
                if filter_near_boundary and not _is_near_boundary(state, pdf_loc):
                    continue
                candidates.append(
                    {
                        "id": _candidate_id(counter),
                        "type": sent_type,
                        "src_loc": {
                            "file": file_rel,
                            "line": line_n,
                            "col_start": abs_start,
                            "col_end": abs_end,
                            "text": sent[:200],
                        },
                        "pdf_loc": pdf_loc,
                        "tags": classify.classify(node, sent_type),
                        "edit_action": "delete_span",
                        "edit_payload": None,
                    }
                )

        # type-2: caption tail
        if kind == "caption":
            sentences = _split_sentences(text)
            if len(sentences) >= 2:
                base_abs = node["col_start"]  # file-absolute start of caption inner text
                end_abs = node["col_end"]
                tail_start = sentences[1][0]
                tail = text[tail_start:].strip()
                line_n = base_line + _line_offset(text, tail_start)
                pdf_loc = _pdf_loc_for(state, file_rel, line_n)
                if filter_near_boundary and not _is_near_boundary(state, pdf_loc):
                    continue
                candidates.append(
                    {
                        "id": _candidate_id(counter),
                        "type": "caption_tail",
                        "src_loc": {
                            "file": file_rel,
                            "line": line_n,
                            "col_start": base_abs + tail_start,
                            "col_end": end_abs,
                            "text": tail[:200],
                        },
                        "pdf_loc": pdf_loc,
                        "tags": classify.classify(node, "caption_tail"),
                        "edit_action": "compress_to_first_sentence",
                        "edit_payload": {"keep": sentences[0][2]},
                    }
                )

        # type-3: cite cluster (one candidate per individual cite — merging
        # is decided at apply time when neighbors are detected)
        if kind == "cite":
            pdf_loc = _pdf_loc_for(state, file_rel, base_line)
            if filter_near_boundary and not _is_near_boundary(state, pdf_loc):
                continue
            candidates.append(
                {
                    "id": _candidate_id(counter),
                    "type": "cite_cluster",
                    "src_loc": {
                        "file": file_rel,
                        "line": base_line,
                        "col_start": node["col_start"],
                        "col_end": node["col_end"],
                        "text": text[:80],
                    },
                    "pdf_loc": pdf_loc,
                    "tags": classify.classify(node, "cite_cluster"),
                    "edit_action": "merge_cites",
                    "edit_payload": None,
                }
            )

    return {"schema_version": "1.0", "candidates": candidates}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("state_json")
    p.add_argument("--filter", choices=["near-boundary"], default=None)
    p.add_argument("--out")
    args = p.parse_args(argv)

    state = json.loads(Path(args.state_json).read_text())
    out = generate_candidates(
        state, filter_near_boundary=(args.filter == "near-boundary")
    )
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
