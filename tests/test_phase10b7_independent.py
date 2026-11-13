"""Independent Phase 10B.7 checks: freeze identity, isolation, no invented deps."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase10b7_revalidation import (
    analyze_phase10b7_revalidation,
    snapshot_prior_artifact_hashes,
)


def test_independent_revalidation_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10b7_revalidation(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["candidates_analyzed"] == 8
    assert sci["audit_summary"]["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert sci["audit_summary"]["new_assumptions"] == 0
    assert sci["audit_summary"]["new_dependencies"] == 0
    assert sci["audit_summary"]["grammar_hash_unchanged"] is True
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["known_physics_comparison_executed"] is False
    assert sci["large_scale_generation_executed"] is False
    assert sci["models_merged"] is False
    assert sci["PHASE_10B7_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    for item in sci["revalidated_candidate_results"]:
        if item["dependency_status"] == "UNCHECKED":
            assert item["dependency_status"] != "VALID"
            assert item["dependency_status"] != "INVALID"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b7_revalidation.py",
        root / "models" / "examples" / "phase10b7_model.py",
        root / "reporting" / "phase10b7_report.py",
        root / "tests" / "phase10b7_test.py",
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
