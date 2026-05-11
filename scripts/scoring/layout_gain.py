#!/usr/bin/env python3
"""Estimated rendered-line savings, in baseline-skips. See references/boundary-scoring.md."""
from __future__ import annotations


def height_saved_pt(est_line_delta: float, baseline_skip: float) -> float:
    """est_line_delta is signed (negative = lines saved); we report a positive
    "height saved in points" only when delta is negative."""
    if est_line_delta >= 0:
        return 0.0
    return abs(est_line_delta) * baseline_skip
