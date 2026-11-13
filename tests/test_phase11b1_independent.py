"""Independent Phase 11B.1 checks: freeze identity, isolation, one principle."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase11b1_scales import (
    EXPECTED_GRAMMAR_HASH,
    PRINCIPLE_ID,
    analyze_phase11b1_scales,
    snapshot_prior_artifact_hashes,
)


def test_independent_scale_test_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11b1_scales(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash == EXPECTED_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["candidates_analyzed"] == 8
    assert sci["audit_summary"]["new_principle_count"] == 1
    assert sci["audit_summary"]["new_principle_id"] == PRINCIPLE_ID
    assert sci["audit_summary"]["grammar_hash_unchanged"] is True
    assert sci["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
    assert sci["PRINCIPLE_EFFECT"] == "INCONSISTENT_WITH_SEALED_MODEL"
    assert sci["GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE"] is True
    assert sci["NEW_PFR"] == "NO_NEW_PFR"
    assert sci["UNIQUE_ACTION"] == "NO"
    assert sci["phase_11b2_executed"] is False
    assert sci["second_principle_introduced"] is False
    assert sci["PHASE_11B1_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["7_repair_gravity_with_a_new_field"] == "REJECTED AS OVERCLAIM"
    assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b1_scales.py",
        root / "models" / "examples" / "phase11b1_model.py",
        root / "reporting" / "phase11b1_report.py",
        root / "tests" / "phase11b1_test.py",
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
