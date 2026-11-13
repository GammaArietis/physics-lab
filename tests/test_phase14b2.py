"""Phase 14B.2: G2 compact non-Abelian activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b2_model import build_phase14b2_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b1_g1 import artifact_dir as phase14b1_artifact_dir
from physics_lab.physics.phase14b2_g2 import (
    AUDIT_VERSION,
    EXPECTED_G1_GRAMMAR_HASH,
    GROUP_SEARCH_BOUNDS,
    N_SU_SEARCH_LIMIT,
    PHASE_14B2_TEST_COPY_ID,
    U1_FACTOR_SEARCH_LIMIT,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g2_activation_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_g1 = (phase14b1_artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json").read_bytes()
    before_14b1 = (phase14b1_artifact_dir() / "PHASE_14B1_SUMMARY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b2_model(signature=sig).solve()
        sci = result.metadata["phase14b2_analysis"]
        integ = result.metadata["phase14b2_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == "G2_COMPACT_NONABELIAN"
        assert sci["PARENT_GRAMMAR"] == "G1_FERMIONIC_CHIRAL"
        assert sci["audit_summary"]["PARENT_GRAMMAR_HASH"] == EXPECTED_G1_GRAMMAR_HASH
        assert sci["G2_EXECUTED"] is True
        assert sci["G3_EXECUTED"] is False
        assert sci["G2_STATUS"] == "CLOSURE_REACHED"
        assert sci["G1_COMPATIBLE"] == 2
        assert sci["G2_COMPATIBLE"] == 12
        assert sci["METADATA_PRUNED"] == 0
        assert sci["GENERATED"] == 12
        assert sci["REJECTED"] == 0
        assert sci["RAW_COMBINATIONS"] == 12
        assert sci["TOP_DOWN_COMPATIBLE"] == 12
        assert sci["EQUIVALENCE_CLASSES"] == 12
        assert sci["G1_SURVIVORS_REUSED"] == 2
        assert sci["G2_NEW_CANDIDATES_GENERATED"] == 12
        assert sci["G0_REGENERATED"] == 0
        assert sci["G1_FULL_SEARCH_REGENERATED"] == 0
        assert sci["NONABELIAN_GRAMMAR_EXPANDS_THE_SURVIVING_THEORY_SPACE"] is True
        assert sci["QUALITATIVE_GAUGE_STRUCTURE_DOES_NOT_SELECT_A_UNIQUE_GROUP_WITHIN_THE_DECLARED_G2_BOUNDS"] is True
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G3_FINITE_REPRESENTATIONS"
        assert sci["anomaly_status"] == "DEFERRED_TO_G5"
        assert sci["vector_mass_structure"] == "DEFERRED_TO_G4"
        assert list(sci["GROUP_SEARCH_BOUNDS"]["N_range"]) == list(N_SU_SEARCH_LIMIT)
        assert list(sci["GROUP_SEARCH_BOUNDS"]["product_U1_factors_k"]) == list(U1_FACTOR_SEARCH_LIMIT)
        assert sci["GROUP_SEARCH_BOUNDS"]["N_range_is_search_bound_not_prediction"] is True
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B2_TEST_COPY_ID"] == PHASE_14B2_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        inv = sci["parameter_inventory"]
        assert all(row["anomaly_status"] == "DEFERRED_TO_G5" for row in inv)
        assert all(row["vector_mass_structure"] == "DEFERRED_TO_G4" for row in inv)
        assert all(row["provenance"]["gauge_coupling"] == "FREE / PARAMETER-DEPENDENT" for row in inv)
        assert all("representation_slot" in row["symbolic_representation_slots"] for row in inv)
        assert (phase14b1_artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json").read_bytes() == before_g1
        assert (phase14b1_artifact_dir() / "PHASE_14B1_SUMMARY.json").read_bytes() == before_14b1
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b1"] == after["phase14b1"]
        assert (artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").is_file()
        assert not (phase14b1_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").is_file()
        _ = ENGINE_VERSION
        _ = GROUP_SEARCH_BOUNDS


def test_phase14b2_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b2.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.2: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.2: G2 coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.2: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.2: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.2: experimental firewall"] == CheckStatus.PASS
