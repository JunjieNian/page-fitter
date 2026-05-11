"""Tests for scripts/verify/ — apply_edits, revert."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "verify"))

import apply_edits  # noqa: E402
import revert as revert_mod  # noqa: E402


# ── apply_edits internals ────────────────────────────────────────────────

class TestApplyToText:
    def test_delete_span(self):
        text = "Hello, beautiful world!"
        result = apply_edits._apply_to_text("delete_span", None, text, 5, 16)
        assert result == "Hello world!"

    def test_delete_span_at_start(self):
        text = "Hello world"
        result = apply_edits._apply_to_text("delete_span", None, text, 0, 6)
        assert result == "world"

    def test_compress_to_first_sentence(self):
        text = "First. Second sentence goes here."
        payload = {"keep": "First."}
        result = apply_edits._apply_to_text("compress_to_first_sentence", payload, text, 0, len(text))
        assert result == "First."

    def test_merge_cites_is_noop(self):
        text = r"\cite{a,b,c}"
        result = apply_edits._apply_to_text("merge_cites", None, text, 0, len(text))
        assert result == text  # v1: no-op

    def test_unknown_action_is_noop(self):
        text = "unchanged"
        result = apply_edits._apply_to_text("unknown_future_action", None, text, 0, 5)
        assert result == text

    def test_out_of_bounds_clamped(self):
        text = "short"
        result = apply_edits._apply_to_text("delete_span", None, text, 0, 999)
        assert result == ""


class TestApplyEdits:
    def test_missing_ids_reported(self, ranked, tmp_path):
        result = apply_edits.apply_edits(ranked, tmp_path, ["nonexistent_id"], None)
        assert "nonexistent_id" in result["missing"]
        assert result["applied"] == []

    def test_apply_on_missing_file(self, ranked, tmp_path):
        # Pick a real candidate ID but point at an empty project root
        real_ids = [s["id"] for s in ranked["scored"][:1]]
        result = apply_edits.apply_edits(ranked, tmp_path, real_ids, None)
        assert any(s["reason"] == "file_missing" for s in result["skipped"])


# ── revert ───────────────────────────────────────────────────────────────

class TestRevert:
    def test_revert_restores_bak(self, tmp_path):
        tex = tmp_path / "test.tex"
        bak = tmp_path / "test.tex.bak"
        tex.write_text("modified content")
        bak.write_text("original content")
        # Make bak newer so force is not required
        import os
        os.utime(bak, (bak.stat().st_mtime + 10, bak.stat().st_mtime + 10))

        result = revert_mod.revert(tmp_path, force=False)
        assert "test.tex" in result["restored"]
        assert tex.read_text() == "original content"

    def test_revert_refuses_newer_target(self, tmp_path):
        tex = tmp_path / "test.tex"
        bak = tmp_path / "test.tex.bak"
        bak.write_text("original content")
        import time; time.sleep(0.05)
        tex.write_text("newer content")

        result = revert_mod.revert(tmp_path, force=False)
        assert len(result["refused"]) == 1
        assert tex.read_text() == "newer content"  # unchanged

    def test_revert_force_overrides(self, tmp_path):
        tex = tmp_path / "test.tex"
        bak = tmp_path / "test.tex.bak"
        bak.write_text("original content")
        import time; time.sleep(0.05)
        tex.write_text("newer content")

        result = revert_mod.revert(tmp_path, force=True)
        assert "test.tex" in result["restored"]
        assert tex.read_text() == "original content"
