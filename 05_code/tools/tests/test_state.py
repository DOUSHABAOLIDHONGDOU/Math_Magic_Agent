"""Tests for state default / save / load / migrate / trust profile."""

from __future__ import annotations

import json

import pytest


def test_default_state_has_required_fields(isolated_project):
    from mm._state import default_state

    state = default_state()
    assert state["stage"] == "INIT"
    assert state["trust_profile"] == "strict"
    assert "Q1" in state["questions"]
    assert "A" in state["questions"]["Q1"]["schemes"]


def test_save_load_round_trip(isolated_project):
    from mm._state import default_state, load_state, save_state

    state = default_state()
    state["problem"]["title"] = "T"
    save_state(state, snapshot=False)
    loaded = load_state()
    assert loaded["problem"]["title"] == "T"


def test_migrate_state_adds_trust_profile(isolated_project):
    from mm._state import migrate_state

    state = {"version": "0.1.0", "stage": "INIT", "problem": {"title": "x"}}
    changed = migrate_state(state)
    assert changed is True
    assert state["trust_profile"] == "strict"
    assert "questions" in state


def test_migrate_state_preserves_question_progress(isolated_project):
    from mm._state import default_state, migrate_state

    state = default_state()
    # Pretend we're upgrading from an older version with custom progress.
    state["version"] = "0.0.1"
    state["questions"]["Q1"]["paper_written"] = True
    state["questions"]["Q1"]["confirmed_scheme"] = "B"
    changed = migrate_state(state)
    assert changed is True
    assert state["questions"]["Q1"]["paper_written"] is True
    assert state["questions"]["Q1"]["confirmed_scheme"] == "B"


def test_set_trust_profile_rejects_unknown(isolated_project):
    from mm._state import set_trust_profile

    state = {"trust_profile": "strict"}
    with pytest.raises(SystemExit):
        set_trust_profile(state, "yolo")


def test_assert_question_unlocked_blocks_skipping(minimal_state):
    from mm._state import assert_question_unlocked, load_state

    state = load_state()
    # Q1 hasn't been paper_written, so Q2 must be locked.
    with pytest.raises(SystemExit):
        assert_question_unlocked(state, "Q2")


def test_state_snapshots_are_written(isolated_project):
    from mm import _paths
    from mm._state import default_state, save_state

    state = default_state()
    save_state(state)
    snapshots = list((_paths.state_snapshots_dir()).glob("state_*.json"))
    assert snapshots, "save_state should write a snapshot when snapshot=True (the default)"


def test_load_state_writes_default_when_missing(isolated_project):
    from mm._state import load_state

    state = load_state()
    payload = json.loads((isolated_project / "00_shared" / "workflow_state.json").read_text(encoding="utf-8"))
    assert payload["version"] == state["version"]
