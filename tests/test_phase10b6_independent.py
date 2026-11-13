"""Independent Phase 10B.6 checks: freeze identity, isolation, typed schema."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import (
    LEGAL_DEPENDENCY_RELATION_TYPES,
    declared_dependencies,
    grammar_hash,
)
from physics_lab.physics.phase10b6_schema import (
    analyze_phase10b6_schema,
    snapshot_prior_artifact_hashes,
)


def test_independent_schema_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10b6_schema(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["RAW_SEARCH_SPACE_SIZE"] == 8
    assert sci["audit_summary"]["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert sci["audit_summary"]["grammar_changed"] == 0
    assert sci["audit_summary"]["new_physics"] == 0
    assert sci["audit_summary"]["new_dependencies_added"] == 0
    assert sci["audit_summary"]["schema_implemented"] is True
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["known_physics_comparison_executed"] is False
    assert sci["large_scale_generation_executed"] is False
    assert sci["models_merged"] is False
    assert sci["PHASE_10B6_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    typed_ids = {row["dependency_id"] for row in sci["typed_dependency_definitions"]}
    assert typed_ids == declared_ids
    for row in sci["typed_dependency_definitions"]:
        assert row["relation_type"] in LEGAL_DEPENDENCY_RELATION_TYPES
    for item in sci["dependency_evaluation_results"]:
        if item["dependency_status"] == "UNCHECKED":
            assert item["dependency_status"] != "VALID"
            assert item["dependency_status"] != "INVALID"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b6_schema.py",
        root / "models" / "examples" / "phase10b6_model.py",
        root / "reporting" / "phase10b6_report.py",
        root / "tests" / "phase10b6_test.py",
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
