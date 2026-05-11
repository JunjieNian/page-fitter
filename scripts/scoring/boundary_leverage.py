#!/usr/bin/env python3
"""Distance-to-page-break leverage. See references/boundary-scoring.md."""
from __future__ import annotations


ALPHA = 2.0  # last page boost
BETA = 0.6   # column-break boost
GAMMA = 0.8  # downstream paragraph pullable
DELTA = 1.5  # downstream is float/heading


def compute(
    *,
    is_last_page: bool,
    is_near_column_break: bool,
    downstream_paragraph_pullable: bool,
    downstream_is_float_or_heading: bool,
    float_risk: float,
) -> float:
    leverage = 1.0
    if is_last_page:
        leverage += ALPHA
    if is_near_column_break:
        leverage += BETA
    if downstream_paragraph_pullable:
        leverage += GAMMA
    if downstream_is_float_or_heading:
        leverage -= DELTA

    leverage *= max(0.0, 1.0 - 0.5 * max(float_risk, 0.0))
    return leverage
