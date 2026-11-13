"""Independent Phase 11B.4 checks: freeze identity, isolation, one principle."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase11b4_rg import (
    EXPECTED_GRAMMAR_HASH,
    PRINCIPLE_ID,
    analyze_phase11b4_rg,
    snapshot_prior_artifact_hashes,
)


def test_independent_rg_test_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11b4_rg(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash == EXPECTED_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["new_principle_count"] == 1
    assert sci["audit_summary"]["new_principle_id"] == PRINCIPLE_ID
    assert sci["PRINCIPLE_EFFECT"] == "RG_UNTESTED"
    assert sci["NEW_PFR"] == "NONE"
    assert sci["UNIQUE_ACTION"] == "NO"
    assert sci["loop_engine_present"] is False
    assert sci["dimension_symbols"]["classical_beta_r_lambda"] == "0"
    assert sci["phase_11b5_executed"] is False
    assert sci["PHASE_11B4_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["12_start_next_11B_phase"] == "REJECTED AS OVERCLAIM"
    assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b4_rg.py",
        root / "models" / "examples" / "phase11b4_model.py",
        root / "reporting" / "phase11b4_report.py",
        root / "tests" / "phase11b4_test.py",
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
