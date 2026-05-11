#!/usr/bin/env python3
"""Parse a PDF into per-page text-block bboxes and column clusters.

Uses PyMuPDF. Outputs JSON conforming to the `pdf` field of state.json
(see references/output-schema.md).

CLI:
    python parse_pdf.py <pdf-path> [--out <json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

def _import_fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:  # pragma: no cover
        sys.stderr.write("PyMuPDF (`pip install pymupdf`) is required.\n")
        raise


def cluster_columns(blocks: list[dict], page_width: float) -> list[dict]:
    """Cluster blocks by their x-midpoint into 1 or 2 columns."""
    if not blocks:
        return [{"x_min": 0.0, "x_max": page_width, "text_width": page_width}]

    midpoints = sorted((b["bbox"][0] + b["bbox"][2]) / 2.0 for b in blocks)
    half = page_width / 2.0
    left = [m for m in midpoints if m < half]
    right = [m for m in midpoints if m >= half]

    # If both sides have substantial mass, treat as 2-column.
    if left and right and len(left) >= 2 and len(right) >= 2:
        cols = []
        for side in (left, right):
            xs_min = min(b["bbox"][0] for b in blocks if (b["bbox"][0] + b["bbox"][2]) / 2 in side)
            xs_max = max(b["bbox"][2] for b in blocks if (b["bbox"][0] + b["bbox"][2]) / 2 in side)
            cols.append({"x_min": xs_min, "x_max": xs_max, "text_width": xs_max - xs_min})
        cols.sort(key=lambda c: c["x_min"])
        return cols

    xs_min = min(b["bbox"][0] for b in blocks)
    xs_max = max(b["bbox"][2] for b in blocks)
    return [{"x_min": xs_min, "x_max": xs_max, "text_width": xs_max - xs_min}]


def assign_column(bbox: list[float], cols: list[dict]) -> int:
    cx = (bbox[0] + bbox[2]) / 2.0
    for i, col in enumerate(cols):
        if col["x_min"] - 1.0 <= cx <= col["x_max"] + 1.0:
            return i
    return 0


def classify_block(d: dict) -> str:
    """Heuristic kind classification — paragraph / heading / caption / display_math / float."""
    text = d.get("text", "").strip()
    if not text:
        return "float"
    head = text[:24].lower()
    if head.startswith(("figure", "table", "algorithm")) and ":" in text[:40]:
        return "caption"
    # Heading heuristic: short, mostly title-case or numbered
    if len(text) < 80 and text.split() and text.split()[0].rstrip(".").replace(".", "").isdigit():
        return "heading"
    return "paragraph"


def parse_page(page, page_index: int) -> dict:
    raw = page.get_text("dict")
    page_w, page_h = page.rect.width, page.rect.height

    blocks: list[dict] = []
    block_idx = 0
    line_skips: list[float] = []

    for blk in raw.get("blocks", []):
        if blk.get("type", 0) != 0:  # 0 = text
            continue
        text = "\n".join(
            "".join(span["text"] for span in line["spans"])
            for line in blk.get("lines", [])
        )
        bbox = [float(v) for v in blk.get("bbox", [0, 0, 0, 0])]
        line_bboxes = [
            [float(v) for v in line.get("bbox", [0, 0, 0, 0])]
            for line in blk.get("lines", [])
        ]
        # Track baseline-skips between consecutive lines in this block.
        for a, b in zip(line_bboxes, line_bboxes[1:]):
            line_skips.append(b[1] - a[1])

        block_idx += 1
        blocks.append(
            {
                "block_id": f"p{page_index + 1}.b{block_idx}",
                "bbox": bbox,
                "text": text,
                "line_bboxes": line_bboxes,
            }
        )

    cols = cluster_columns(blocks, page_w)
    baseline = median(line_skips) if line_skips else 12.0

    out_blocks = []
    for b in blocks:
        out_blocks.append(
            {
                "block_id": b["block_id"],
                "bbox": b["bbox"],
                "column": assign_column(b["bbox"], cols),
                "kind": classify_block(b),
                "line_bboxes": b["line_bboxes"],
                # synctex link is filled in later by parse_synctex.py
                "synctex": None,
                "text_preview": b["text"][:120],
            }
        )

    return {
        "page": page_index + 1,
        "width": page_w,
        "height": page_h,
        "columns": cols,
        "baseline_skip": baseline,
        "blocks": out_blocks,
    }


def parse_pdf(pdf_path: Path) -> dict:
    fitz = _import_fitz()
    doc = fitz.open(pdf_path)
    pages = [parse_page(p, i) for i, p in enumerate(doc)]
    return {
        "path": str(pdf_path.name),
        "page_count": len(pages),
        "pages": pages,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("--out")
    args = p.parse_args(argv)

    out = parse_pdf(Path(args.pdf).resolve())
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
