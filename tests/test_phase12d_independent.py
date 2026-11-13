"""Independent Phase 12D checks: freeze identity, isolation, no 12E."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase12c_classes import artifact_dir as phase12c_artifact_dir
from physics_lab.physics.phase12d_derivation import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_12C_CLASSES,
    EXPECTED_LEGAL_COUNT,
    analyze_phase12d_derivation,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)


def test_independent_family_derivation_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_12c = (phase12c_artifact_dir() / "PHASE_12C_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase12d_derivation(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["candidates_total"] == EXPECTED_LEGAL_COUNT
    assert sci["structural_classes_total"] == EXPECTED_12C_CLASSES
    assert sci["sampling"] is False
    assert sci["phase_12e_executed"] is False
    assert sci["SEARCH_SPACE_EXHAUSTIVE"] is True
    assert sci["DERIVATION_EXHAUSTIVE"] is False
    assert sci["GLOBAL_CLOSURE"] == "PARTIAL"
    assert sci["PHASE_12D_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["9_start_phase_12E"] == "REJECTED AS OVERCLAIM"
    assert sci["overclaims"]["8_claim_no_closure_from_incomplete_derivation"] == "REJECTED AS OVERCLAIM"
    assert (phase12c_artifact_dir() / "PHASE_12C_SUMMARY.json").read_bytes() == before_12c
    assert (artifact_dir() / "PHASE_12D_SUMMARY.json").is_file()
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase12d_derivation.py",
        root / "models" / "examples" / "phase12d_model.py",
        root / "reporting" / "phase12d_report.py",
        root / "tests" / "phase12d_test.py",
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
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
