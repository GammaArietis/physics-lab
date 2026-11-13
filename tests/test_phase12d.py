"""Phase 12D: complete unresolved structural-class derivation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase12d_model import build_phase12d_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase12b_search import artifact_dir as phase12b_artifact_dir
from physics_lab.physics.phase12c_classes import artifact_dir as phase12c_artifact_dir
from physics_lab.physics.phase12d_derivation import (
    AUDIT_VERSION,
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_12C_CLASSES,
    EXPECTED_LEGAL_COUNT,
    PHASE_12D_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unresolved_family_derivation_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_10a = grammar_hash_10a()
    before_12a = grammar_hash_12a()
    before_12c = (phase12c_artifact_dir() / "PHASE_12C_SUMMARY.json").read_bytes()
    before_12b = (phase12b_artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json").read_bytes()
    before_freeze = (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase12d_model(signature=sig).solve()
        sci = result.metadata["phase12d_analysis"]
        integ = result.metadata["phase12d_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        cov = sci["class_coverage"]
        eom = sci["eom_results"]
        lin = sci["linearization_results"]
        dyn = sci["dynamic_consistency"]
        ghost = sci["ghost_results"]
        rel = sci["parameter_relations"]
        rem = sci["unresolved_families"]
        fam = sci["family_templates"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == before_10a == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
        assert sci["grammar_hash"] == EXPECTED_12A_GRAMMAR_HASH
        assert sci["candidates_total"] == EXPECTED_LEGAL_COUNT
        assert sci["structural_classes_total"] == EXPECTED_12C_CLASSES
        assert cov["overlap"] == 0
        assert cov["missing"] == 0
        assert cov["partition_unchanged"] is True
        assert eom["candidates_with_verified_EOM"] + eom["candidates_with_partial_EOM"] + eom["candidates_with_untested_EOM"] == EXPECTED_LEGAL_COUNT
        assert lin["candidates_with_verified_linearization"] + lin["candidates_with_partial_linearization"] + lin["candidates_with_untested_linearization"] == EXPECTED_LEGAL_COUNT
        assert dyn["second_order"] + dyn["higher_order"] == EXPECTED_LEGAL_COUNT
        assert ghost["ghost_no"] + ghost["ghost_yes"] + ghost["ghost_parameter_dependent"] + ghost["ghost_untested"] == EXPECTED_LEGAL_COUNT
        assert sci["PHASE_12D_STATUS"] == "CLOSED"
        assert sci["PHASE_12D_TEST_COPY_ID"] == PHASE_12D_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["sampling"] is False
        assert summary["ranking"] is False
        assert sci["phase_12e_executed"] is False
        assert sci["new_physical_principle"] is False
        assert sci["SEARCH_SPACE_EXHAUSTIVE"] is True
        assert sci["UNIQUE_ACTION"] == "NO"
        assert sci["UNIQUE_KINETIC_STRUCTURE"] == "NO"
        assert sci["QUANTUM_UNITARITY"] == "UNTESTED"
        assert fam["dynamical_modulus_coefficient_slot"]["MODULUS_REALIZATION_MISSING"] is False
        assert fam["dynamical_modulus_coefficient_slot"]["hidden_field_introduced"] is False
        assert fam["internal_reflection_realization"]["INTERNAL_REFLECTION_UNREALIZED"] is False
        assert fam["internal_reflection_realization"]["candidate_deleted"] is False
        assert fam["generally_covariant_linearization_background"]["c0_inserted_as_parameter_fixing"] is False
        assert fam["bounded_nonminimal_RX"]["compensating_operators_added"] is False
        assert fam["higher_derivative_gauge_4D"]["gauge_redundancy_is_not_ostrogradsky_avoidance"] is True
        assert rel["parameter_free_relation_candidates"] == 0
        assert rem["named_unresolved_structural_families"] == ["dynamical_modulus_coefficient_slot"]
        assert sci["DERIVATION_EXHAUSTIVE"] is False
        assert sci["GLOBAL_CLOSURE"] == "PARTIAL"
        assert sci["overclaims"]["4_insert_c0_equals_0_as_PFR"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["9_start_phase_12E"] == "REJECTED AS OVERCLAIM"
        assert dyn["avoided_by_verified_degeneracy"] == 0
    after = snapshot_prior_artifact_hashes()
    assert before == after
    assert (phase12c_artifact_dir() / "PHASE_12C_SUMMARY.json").read_bytes() == before_12c
    assert (phase12b_artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json").read_bytes() == before_12b
    assert (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes() == before_freeze


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase12d_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "PHASE_12D_SUMMARY.json",
        "PHASE_12D_DERIVATION_SUMMARY.json",
        "PHASE_12D_EOM_RESULTS.json",
        "PHASE_12D_LINEARIZATION_RESULTS.json",
        "PHASE_12D_CONSTRAINT_RESULTS.json",
        "PHASE_12D_GHOST_RESULTS.json",
        "PHASE_12D_PARAMETER_RELATIONS.json",
        "PHASE_12D_CLASS_COVERAGE.json",
        "PHASE_12D_CLOSURE_STATUS.json",
        "PHASE_12D_INTEGRITY_REPORT.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase12c_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase12d.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 12D: pre-analysis gate",
        "Phase 12D: unresolved-family coverage",
        "Phase 12D: no numerical target search",
        "Phase 12D: banned tokens",
        "Phase 12D: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_12D_SUMMARY" in text
    assert "PHASE 12D CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "DERIVATION_EXHAUSTIVE" in text
    assert "No Phase 12E" in text or "no Phase 12E" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase12d_derivation.py",
        root / "models" / "examples" / "phase12d_model.py",
        root / "reporting" / "phase12d_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "phase10a_" + "known_physics",
        "best_model",
        "preferred_model",
        "top_model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
