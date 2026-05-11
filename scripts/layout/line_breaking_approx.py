#!/usr/bin/env python3
"""Knuth-Plass-lite line-delta predictor. See references/line-breaking.md."""
from __future__ import annotations

import math

_PT_PER_CHAR = 5.0  # rough average for 10pt body text in two-column papers


def predict_line_delta(
    *,
    paragraph_line_count: int,
    col_width: float,
    last_line_fill_ratio: float,
    deletion_text: str,
) -> tuple[float, str]:
    """Return (signed est_line_delta, confidence_band).

    Negative = lines saved. Confidence in {high, medium, low}.
    """
    if paragraph_line_count <= 0 or col_width <= 0:
        return 0.0, "low"

    # Approximate paragraph text width and the "remaining glue" on the last line.
    # If we delete `W_c` worth of glyphs and the last line has `slack` of glue,
    # we save a line iff `W_c >= slack`.
    last_line_used = last_line_fill_ratio * col_width
    last_line_slack = col_width - last_line_used  # how empty the last line is

    w_c = max(len(deletion_text), 0) * _PT_PER_CHAR

    # If the paragraph's last line is essentially empty (slack ≈ col_w),
    # a small deletion cannot collapse a line.
    if last_line_fill_ratio < 0.10 and w_c < col_width * 0.8:
        return 0.0, "high"

    # Knuth-Plass-lite: full text width minus deletion, divided by col_w.
    total_w = paragraph_line_count * col_width - last_line_slack
    new_total = max(total_w - w_c, 0.0)
    new_lines = math.ceil(new_total / col_width)
    delta = float(new_lines - paragraph_line_count)  # negative = saved

    # Confidence band: distance from the rounding boundary.
    new_frac = new_total / col_width
    distance_from_int = abs(new_frac - round(new_frac))
    if distance_from_int >= 0.30:
        confidence = "high"
    elif distance_from_int >= 0.15:
        confidence = "medium"
    else:
        confidence = "low"

    return delta, confidence
