"""Tests for scripts/scoring/ — layout_gain, boundary_leverage, rank."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct imports of the scoring modules.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "scoring"))

import boundary_leverage  # noqa: E402
import layout_gain  # noqa: E402
import rank as rank_mod  # noqa: E402

# ── layout_gain ──────────────────────────────────────────────────────────

class TestHeightSaved:
    def test_negative_delta_returns_positive_height(self):
        assert layout_gain.height_saved_pt(-1.0, 12.0) == 12.0

    def test_zero_delta_returns_zero(self):
        assert layout_gain.height_saved_pt(0.0, 12.0) == 0.0

    def test_positive_delta_returns_zero(self):
        assert layout_gain.height_saved_pt(1.0, 12.0) == 0.0

    def test_large_negative_delta(self):
        assert layout_gain.height_saved_pt(-3.0, 10.0) == 30.0


# ── boundary_leverage ────────────────────────────────────────────────────

class TestBoundaryLeverage:
    def test_baseline_no_flags(self):
        lev = boundary_leverage.compute(
            is_last_page=False,
            is_near_column_break=False,
            downstream_paragraph_pullable=False,
            downstream_is_float_or_heading=False,
            float_risk=0.0,
        )
        assert lev == 1.0

    def test_last_page_boost(self):
        lev = boundary_leverage.compute(
            is_last_page=True,
            is_near_column_break=False,
            downstream_paragraph_pullable=False,
            downstream_is_float_or_heading=False,
            float_risk=0.0,
        )
        assert lev == 1.0 + boundary_leverage.ALPHA

    def test_column_break_boost(self):
        lev = boundary_leverage.compute(
            is_last_page=False,
            is_near_column_break=True,
            downstream_paragraph_pullable=False,
            downstream_is_float_or_heading=False,
            float_risk=0.0,
        )
        assert lev == 1.0 + boundary_leverage.BETA

    def test_downstream_pullable_boost(self):
        lev = boundary_leverage.compute(
            is_last_page=False,
            is_near_column_break=False,
            downstream_paragraph_pullable=True,
            downstream_is_float_or_heading=False,
            float_risk=0.0,
        )
        assert lev == 1.0 + boundary_leverage.GAMMA

    def test_float_or_heading_penalty(self):
        lev = boundary_leverage.compute(
            is_last_page=False,
            is_near_column_break=False,
            downstream_paragraph_pullable=False,
            downstream_is_float_or_heading=True,
            float_risk=0.0,
        )
        assert lev == 1.0 - boundary_leverage.DELTA

    def test_float_risk_attenuates(self):
        lev = boundary_leverage.compute(
            is_last_page=True,
            is_near_column_break=False,
            downstream_paragraph_pullable=False,
            downstream_is_float_or_heading=False,
            float_risk=1.0,
        )
        # (1 + ALPHA) * max(0, 1 - 0.5*1.0)
        expected = (1.0 + boundary_leverage.ALPHA) * 0.5
        assert abs(lev - expected) < 1e-9

    def test_all_boosts_combined(self):
        lev = boundary_leverage.compute(
            is_last_page=True,
            is_near_column_break=True,
            downstream_paragraph_pullable=True,
            downstream_is_float_or_heading=False,
            float_risk=0.0,
        )
        expected = 1.0 + boundary_leverage.ALPHA + boundary_leverage.BETA + boundary_leverage.GAMMA
        assert abs(lev - expected) < 1e-9


# ── rank ─────────────────────────────────────────────────────────────────

class TestRank:
    def test_rank_returns_schema_version(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=2,
        )
        assert result["schema_version"] == "1.0"
        assert "scored" in result
        assert "summary" in result

    def test_rank_candidate_count_matches(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=None,
        )
        assert result["summary"]["total_candidates"] == len(candidates["candidates"])

    def test_scored_sorted_descending(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=None,
        )
        scores = [s["score"] for s in result["scored"]]
        assert scores == sorted(scores, reverse=True)

    def test_buckets_are_valid(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=None,
        )
        valid_buckets = {"high_leverage", "marginal", "not_worth"}
        for item in result["scored"]:
            assert item["bucket"] in valid_buckets

    def test_summary_counts_add_up(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=None,
        )
        s = result["summary"]
        assert s["high_leverage"] + s["marginal"] + s["not_worth"] == s["total_candidates"]


class TestRenderReport:
    def test_report_contains_sections(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=2,
        )
        report = rank_mod.render_report(result, triage=True)
        assert "# page-fitter report" in report
        assert "High-leverage edits" in report
        assert "Marginal edits" in report
        assert "Not worth editing" in report

    def test_triage_mode_noted(self, state, candidates, layout, floats):
        result = rank_mod.rank(
            state, candidates, layout, floats, None,
            triage=True, page_limit=2,
        )
        report = rank_mod.render_report(result, triage=True)
        assert "Triage mode" in report
