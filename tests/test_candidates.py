"""Tests for scripts/candidates/ — classify, generate_candidates."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "candidates"))

import classify  # noqa: E402
import generate_candidates as gc  # noqa: E402


# ── classify ─────────────────────────────────────────────────────────────

class TestClassify:
    def test_classify_returns_expected_keys(self):
        node = {"env_stack": []}
        result = classify.classify(node, "sentence_descriptive")
        assert set(result.keys()) == {
            "float_adjacent",
            "in_abstract",
            "in_proof",
            "is_argument_load_bearing",
            "algorithm_local",
        }

    def test_float_adjacent_in_figure(self):
        node = {"env_stack": ["figure"]}
        result = classify.classify(node, "caption_tail")
        assert result["float_adjacent"] is True

    def test_in_abstract(self):
        node = {"env_stack": ["abstract"]}
        result = classify.classify(node, "sentence_descriptive")
        assert result["in_abstract"] is True

    def test_in_proof(self):
        node = {"env_stack": ["proof"]}
        result = classify.classify(node, "sentence_proof_step")
        assert result["in_proof"] is True

    def test_load_bearing_types(self):
        node = {"env_stack": []}
        for t in ("sentence_claim", "sentence_proof_step", "display_equation"):
            assert classify.classify(node, t)["is_argument_load_bearing"] is True
        assert classify.classify(node, "sentence_descriptive")["is_argument_load_bearing"] is False


class TestClassifySentence:
    def test_proof_env_overrides(self):
        assert classify.classify_sentence("This is trivial.", env_stack=["proof"]) == "sentence_proof_step"

    def test_claim_verb(self):
        assert classify.classify_sentence("We show that X is optimal.", env_stack=[]) == "sentence_claim"

    def test_comparative(self):
        assert classify.classify_sentence("Our method outperforms the baseline.", env_stack=[]) == "sentence_claim"

    def test_numeric(self):
        assert classify.classify_sentence("Accuracy reaches 95.3 percent.", env_stack=[]) == "sentence_claim"

    def test_section_opening(self):
        assert classify.classify_sentence("In this section, we describe the algorithm.", env_stack=[]) == "section_opening"

    def test_descriptive_fallback(self):
        assert classify.classify_sentence("The sky is blue.", env_stack=[]) == "sentence_descriptive"


# ── generate_candidates internals ────────────────────────────────────────

class TestSplitSentences:
    def test_single_sentence(self):
        result = gc._split_sentences("Hello world.")
        assert len(result) == 1
        assert result[0][2] == "Hello world."

    def test_two_sentences(self):
        result = gc._split_sentences("First sentence. Second sentence.")
        assert len(result) == 2
        assert result[0][2] == "First sentence."
        assert result[1][2] == "Second sentence."

    def test_empty_string(self):
        assert gc._split_sentences("") == []


class TestMacroResidue:
    def test_detects_optional_arg(self):
        assert gc._MACRO_RESIDUE.match("[3][1-5] lorem ipsum")

    def test_no_match_on_normal_text(self):
        assert gc._MACRO_RESIDUE.match("Normal sentence.") is None


class TestGenerateCandidates:
    def test_returns_schema_version(self, state):
        result = gc.generate_candidates(state)
        assert result["schema_version"] == "1.0"
        assert "candidates" in result

    def test_candidates_have_required_fields(self, state):
        result = gc.generate_candidates(state)
        for c in result["candidates"][:5]:
            assert "id" in c
            assert "type" in c
            assert "src_loc" in c
            assert "edit_action" in c

    def test_candidate_ids_unique(self, state):
        result = gc.generate_candidates(state)
        ids = [c["id"] for c in result["candidates"]]
        assert len(ids) == len(set(ids))

    def test_fixture_candidates_match(self, candidates):
        """The fixture's candidates.json should have valid structure."""
        assert candidates["schema_version"] == "1.0"
        assert len(candidates["candidates"]) > 0
