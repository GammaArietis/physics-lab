"""Independent Phase 10B.4 checks: freeze identity, isolation, no invented deps."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase10b4_validation import (
    analyze_phase10b4_validation,
    snapshot_prior_artifact_hashes,
)


def test_independent_validation_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10b4_validation(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["RAW_SEARCH_SPACE_SIZE"] == 8
    assert sci["audit_summary"]["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert sci["audit_summary"]["grammar_changes"] == 0
    assert sci["audit_summary"]["new_physics"] == 0
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["known_physics_comparison_executed"] is False
    assert sci["large_scale_generation_executed"] is False
    assert sci["models_merged"] is False
    assert sci["PHASE_10B4_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    result_ids = set()
    for item in sci["dependency_validation_results"]:
        result_ids.update(item["violated_dependency_ids"])
        result_ids.update(item["unchecked_dependency_ids"])
        result_ids.update(item["satisfied_dependency_ids"])
    assert result_ids <= declared_ids


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b4_validation.py",
        root / "models" / "examples" / "phase10b4_model.py",
        root / "reporting" / "phase10b4_report.py",
        root / "tests" / "phase10b4_test.py",
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
