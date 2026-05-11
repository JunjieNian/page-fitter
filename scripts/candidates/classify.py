#!/usr/bin/env python3
"""Tag candidates with type/structural flags. See references/candidate-types.md."""
from __future__ import annotations

import re


_FLOAT_ENVS = {"figure", "figure*", "table", "table*", "algorithm", "algorithm2e"}
_PROOF_ENVS = {"proof"}


_RE_NUMERIC = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|\\%|pp|ms|ns|gb|mb|fps|x)?\b", re.IGNORECASE)
_RE_COMPARATIVE = re.compile(
    r"\b(?:better|worse|higher|lower|larger|smaller|outperforms?|exceeds?|surpasses?|"
    r"improves?|reduces?)\b",
    re.IGNORECASE,
)
_RE_CLAIM_VERB = re.compile(
    r"\b(?:we (?:show|prove|demonstrate|introduce|propose|present)|"
    r"this (?:shows|proves|demonstrates))\b",
    re.IGNORECASE,
)


def classify(node: dict, candidate_type: str) -> dict:
    env_stack = set(node.get("env_stack", []))
    return {
        "float_adjacent": bool(env_stack & _FLOAT_ENVS),
        "in_abstract": "abstract" in env_stack,
        "in_proof": bool(env_stack & _PROOF_ENVS),
        "is_argument_load_bearing": candidate_type
        in {"sentence_claim", "sentence_proof_step", "display_equation"},
        "algorithm_local": "algorithm" in env_stack or "algorithm2e" in env_stack,
    }


def classify_sentence(sent: str, env_stack: list[str]) -> str:
    """Pick a sentence_* type per the rubric in candidate-types.md."""
    env_set = set(env_stack)
    if env_set & _PROOF_ENVS:
        return "sentence_proof_step"
    if _RE_CLAIM_VERB.search(sent) or _RE_COMPARATIVE.search(sent) or _RE_NUMERIC.search(sent):
        return "sentence_claim"
    # rough section-opening detector: very short, ends with a period, starts with "In this"
    if sent.lower().startswith(("in this section", "in this paper", "in what follows")):
        return "section_opening"
    return "sentence_descriptive"
