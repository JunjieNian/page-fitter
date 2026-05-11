"""Shared fixtures for page-fitter tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixture"
PF_DIR = FIXTURE_DIR / ".page-fitter"


@pytest.fixture()
def state():
    return json.loads((PF_DIR / "state.json").read_text())


@pytest.fixture()
def candidates():
    return json.loads((PF_DIR / "candidates.json").read_text())


@pytest.fixture()
def layout():
    return json.loads((PF_DIR / "layout.json").read_text())


@pytest.fixture()
def floats():
    return json.loads((PF_DIR / "floats.json").read_text())


@pytest.fixture()
def ranked():
    return json.loads((PF_DIR / "ranked.json").read_text())
