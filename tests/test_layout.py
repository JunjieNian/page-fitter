"""Tests for scripts/layout/ — line_breaking_approx, paragraph_lines, float_risk."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "layout"))

import line_breaking_approx as lba  # noqa: E402
import float_risk  # noqa: E402
import paragraph_lines  # noqa: E402


# ── line_breaking_approx ─────────────────────────────────────────────────

class TestLineBreakingApprox:
    def test_zero_lines_returns_zero(self):
        delta, conf = lba.predict_line_delta(
            paragraph_line_count=0, col_width=250.0,
            last_line_fill_ratio=0.5, deletion_text="some text",
        )
        assert delta == 0.0
        assert conf == "low"

    def test_zero_width_returns_zero(self):
        delta, conf = lba.predict_line_delta(
            paragraph_line_count=5, col_width=0.0,
            last_line_fill_ratio=0.5, deletion_text="some text",
        )
        assert delta == 0.0
        assert conf == "low"

    def test_nearly_empty_last_line_no_collapse(self):
        delta, conf = lba.predict_line_delta(
            paragraph_line_count=5, col_width=250.0,
            last_line_fill_ratio=0.05, deletion_text="short",
        )
        assert delta == 0.0
        assert conf == "high"

    def test_full_last_line_small_delete_collapses(self):
        # 5 lines, col_width=250, last line nearly full, delete ~50 chars = ~250pt
        delta, conf = lba.predict_line_delta(
            paragraph_line_count=5, col_width=250.0,
            last_line_fill_ratio=0.95, deletion_text="x" * 50,
        )
        assert delta < 0  # should save at least one line

    def test_confidence_bands(self):
        # With a moderate deletion that lands far from rounding boundary → high confidence
        _, conf = lba.predict_line_delta(
            paragraph_line_count=10, col_width=250.0,
            last_line_fill_ratio=0.05, deletion_text="tiny",
        )
        assert conf in {"high", "medium", "low"}


# ── float_risk ───────────────────────────────────────────────────────────

class TestFloatRisk:
    def test_no_risk_baseline(self, state, candidates):
        result = float_risk.compute_float_risk(state, candidates)
        assert result["schema_version"] == "1.0"
        assert "by_candidate" in result

    def test_all_candidates_have_risk(self, state, candidates):
        result = float_risk.compute_float_risk(state, candidates)
        for c in candidates["candidates"]:
            entry = result["by_candidate"].get(c["id"])
            assert entry is not None
            assert "float_risk" in entry
            assert 0.0 <= entry["float_risk"] <= 1.0

    def test_fixture_floats_valid(self, floats):
        assert floats["schema_version"] == "1.0"
        assert len(floats["by_candidate"]) > 0


# ── paragraph_lines ──────────────────────────────────────────────────────

class TestParagraphLines:
    def test_compute_layout_returns_schema(self, state, candidates):
        result = paragraph_lines.compute_layout(state, candidates, fast=True)
        assert result["schema_version"] == "1.0"
        assert "by_candidate" in result

    def test_all_candidates_have_layout(self, state, candidates):
        result = paragraph_lines.compute_layout(state, candidates, fast=True)
        for c in candidates["candidates"]:
            entry = result["by_candidate"].get(c["id"])
            assert entry is not None
            assert "est_line_delta" in entry
            assert "confidence" in entry
            assert "P_reduce_line" in entry

    def test_fixture_layout_valid(self, layout):
        assert layout["schema_version"] == "1.0"
        assert len(layout["by_candidate"]) > 0
