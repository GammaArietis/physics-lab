"""Independent Phase 11B.6 checks: freeze identity, isolation, two principles."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase11b6_scale_conformal import (
    EXPECTED_GRAMMAR_HASH,
    PRINCIPLE_IDS,
    analyze_phase11b6_scale_conformal,
    snapshot_prior_artifact_hashes,
)


def test_independent_scale_conformal_test_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11b6_scale_conformal(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash == EXPECTED_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["new_principle_count"] == 2
    assert sci["audit_summary"]["new_principle_ids"] == list(PRINCIPLE_IDS)
    assert sci["scale_summary"]["PRINCIPLE_EFFECT"] == "INCONSISTENT"
    assert sci["conformal_summary"]["PRINCIPLE_EFFECT"] == "CONFORMAL_COMPLETION_REQUIRED"
    assert sci["scale_summary"]["NEW_PFR"] == "NONE"
    assert sci["conformal_summary"]["NEW_PFR"] == "NONE"
    assert sci["scale_summary"]["UNIQUE_ACTION"] == "NO"
    assert sci["dilaton_added"] is False
    assert sci["improvement_added"] is False
    assert sci["GRAVITY_SCALE_INVARIANCE_OBSTRUCTED"] is True
    assert sci["CONFORMAL_COMPLETION_REQUIRED"] is True
    assert sci["phase_11b7_executed"] is False
    assert sci["PHASE_11B6_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["12_start_next_11B_phase"] == "REJECTED AS OVERCLAIM"
    assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"
    assert sci["principle"]["branches_combined"] is False


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b6_scale_conformal.py",
        root / "models" / "examples" / "phase11b6_model.py",
        root / "reporting" / "phase11b6_report.py",
        root / "tests" / "phase11b6_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "phase10a_" + "known_physics" not in text
        assert "KNOWN_PHYSICS_CATALOG" not in text
