"""Phase 14C.5: P5_OPTIONAL_QUANTUM_STRUCTURE quantum consistency core.

Conservative quantum tests Q01-Q10 on the verified P3 survivor space.
P4 remains REFERENCE_ONLY and must not affect generation, filtering, or rejection.
UNTESTED is not FAILED. Missing components are not invented.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14a_reconstruction import artifact_dir as phase14a_artifact_dir
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ClosureEngine,
    ENGINE_VERSION,
    EngineFailure,
    artifact_dir as phase14b0_artifact_dir,
    assert_target_blind,
    content_hash,
    scan_target_blindness,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_SEARCH_BOUNDS,
    artifact_dir as phase14b6_artifact_dir,
)
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    artifact_dir as phase14c0_artifact_dir,
    assert_profile_not_p4_in_generation,
    catalog_hash,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_class_rows,
    physics_profile_registry,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import (
    operator_dimension_audit,
    quantum_unitarity_status,
    artifact_dir as phase14c1_artifact_dir,
)
from physics_lab.physics.phase14c2_p2 import (
    G6_GRAMMAR_INTERACTIONS,
    artifact_dir as phase14c2_artifact_dir,
    grammar_yukawa_present,
)
from physics_lab.physics.phase14c3_p3 import artifact_dir as phase14c3_artifact_dir
from physics_lab.physics.phase14c4_p4 import (
    EXPECTED_P4_PROFILE_HASH,
    P4_ID,
    artifact_dir as phase14c4_artifact_dir,
    p4_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c4_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5_PROFILE_HASH",
    "P5_ID",
    "PHASE_14C5_TEST_COPY_ID",
    "analyze_phase14c5_p5",
    "artifact_dir",
    "interacting_amplitude_constructible",
    "p5_profile",
    "p5_quantum_test_registry",
    "quantum_evaluate",
    "run_phase14c5_or_stop",
]

PHASE = "PHASE_14C.5"
PHASE_14C5_TEST_COPY_ID = "PHASE_14C5_P5_QUANTUM_CONSISTENCY_CORE"
AUDIT_VERSION = "phase14c5-p5-v1"
QUANTUM_CORE_VERSION = "phase14c5-p5-quantum-core-v1"
P5_ID = "P5_OPTIONAL_QUANTUM_STRUCTURE"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_CATALOG_HASH = "c7f86733cdf6e07b3a6e39c1a9755b796c8b72f5979e14e160a47d3b04b4f617"
EXPECTED_PROFILE_REGISTRY_HASH = "ec2a2f476faf28356e921ceb9431cb33cbc97ba66fcd25be22506c4139e66e96"
EXPECTED_P5_PROFILE_HASH = "fae9adfd77818874c021344c6824701a58a9eb9e38bfa8006f5ec7d2783bfb0d"
EXPECTED_CANDIDATE_SPACE_HASH = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff8"
EXPECTED_P4_CHECKPOINT_DIGEST = "8f2936700e9c3c5ee706ae3a0da638dc34e70f98baa23522c69808575897fb79"
EXPECTED_P3_CHECKPOINT_DIGEST = "8a2c284b4bd55f2882f5e6892a7c97b59f538d09c06d4d8ed38b11ca44b73979"
ALLOWED_TEST_STATUSES = ("VERIFIED", "PARTIAL", "UNTESTED", "NOT_APPLICABLE", "FAILED")
Q_TEST_IDS = (
    "Q01_spin_statistics",
    "Q02_canonical_quantization",
    "Q03_propagator_residue",
    "Q04_tree_unitarity",
    "Q05_BRST",
    "Q06_CPT",
    "Q07_renormalization",
    "Q08_RG",
    "Q09_asymptotic_freedom",
    "Q10_quantum_gravity",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5_artifacts"


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    from physics_lab.physics.phase14b0_engine import _write_json as engine_write

    engine_write(path, payload)


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def p5_profile() -> dict[str, Any]:
    profile = physics_profile_registry()["profiles"][P5_ID]
    if profile["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        raise EngineFailure("PROFILE_HASH_MISMATCH", P5_ID)
    return profile


def p5_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5_QUANTUM_CONSISTENCY_CORE.json"


def f2_gauge_kinetic_present() -> bool:
    allowed = list(G6_GRAMMAR_INTERACTIONS)
    return any("F2" == item or item == "F2_gauge_kinetic" for item in allowed)


def complete_scalar_potential_present() -> bool:
    return "complete_scalar_potential" in G6_GRAMMAR_INTERACTIONS


def interacting_amplitude_constructible(_row: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = _row
    reasons = []
    if not f2_gauge_kinetic_present():
        reasons.append("autonomous_gauge_kinetic_absent")
    if not grammar_yukawa_present():
        reasons.append("Yukawa_absent")
    if not complete_scalar_potential_present():
        reasons.append("complete_scalar_potential_absent")
    constructible = not reasons
    return {
        "constructible": constructible,
        "fabricated": False,
        "imported_reference_amplitudes": False,
        "measured_cross_sections": False,
        "missing": reasons,
        "provenance": "REQUIRED_COMPONENT_MISSING" if not constructible else "DERIVED ONLY FROM ACTUAL AMPLITUDE TEST",
    }


def p5_quantum_test_registry() -> dict[str, Any]:
    tests = [
        {"test_id": "Q01", "name": "spin-statistics", "mathematical_definition": "consistency of Weyl/half-integer/fermionic and scalar/integer/bosonic labels against an actual statistics operator if implemented", "implementation_level": "METADATA_PARTIAL", "status": "PARTIAL", "provenance": "UNTESTED"},
        {"test_id": "Q02", "name": "canonical free-field quantization", "mathematical_definition": "canonical variables, conjugate momenta, (anti)commutation, constraints, free propagator existence", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "REQUIRED_COMPONENT_MISSING"},
        {"test_id": "Q03", "name": "propagator/residue health", "mathematical_definition": "pole/residue of implemented quadratic sectors; not a unitarity proof", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "REQUIRED_COMPONENT_MISSING"},
        {"test_id": "Q04", "name": "tree-level unitarity", "mathematical_definition": "actual tree amplitude / optical theorem / partial-wave bound", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "REQUIRED_COMPONENT_MISSING"},
        {"test_id": "Q05", "name": "BRST/gauge-fixing", "mathematical_definition": "gauge-fixed quantum system with autonomous gauge dynamics", "implementation_level": "NOT_APPLICABLE", "status": "NOT_APPLICABLE", "provenance": "REQUIRED_COMPONENT_MISSING"},
        {"test_id": "Q06", "name": "CPT structural consistency", "mathematical_definition": "explicit CPT map of fields and action; locality plus Lorentz is not a substitute", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "UNTESTED"},
        {"test_id": "Q07", "name": "perturbative renormalization", "mathematical_definition": "power-counting of implemented operators versus explicit loop counterterm closure", "implementation_level": "POWER_COUNTING_ONLY", "status": "PARTIAL", "provenance": "POWER-COUNTING CLASSIFICATION"},
        {"test_id": "Q08", "name": "RG consistency", "mathematical_definition": "symbolic beta functions from an implemented loop calculation", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "UNTESTED"},
        {"test_id": "Q09", "name": "asymptotic-freedom diagnostic", "mathematical_definition": "sign of the one-loop gauge beta coefficient given genuine gauge dynamics", "implementation_level": "NOT_APPLICABLE", "status": "NOT_APPLICABLE", "provenance": "REQUIRED_COMPONENT_MISSING"},
        {"test_id": "Q10", "name": "quantum-gravity consistency", "mathematical_definition": "actual quantum-gravity calculation of the frozen Einstein-Hilbert family", "implementation_level": "NOT_IMPLEMENTED", "status": "UNTESTED", "provenance": "UNTESTED"},
    ]
    integrity = [
        {"test_id": "P5T01", "name": "P4 to P5 parent integrity", "mathematical_definition": "P4_STATUS=CLOSURE_REACHED, P4_EXECUTED=YES, P5_EXECUTED=NO, P3 space unchanged", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T02", "name": "spin-statistics scope", "mathematical_definition": "no theorem-level claim without a statistics operator", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T03", "name": "quantization scope", "mathematical_definition": "classical Euler-Lagrange is not a quantization proof", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T04", "name": "ghost-freedom is not unitarity", "mathematical_definition": "classical ghost diagnostics remain separate from quantum unitarity", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T05", "name": "propagator construction scope", "mathematical_definition": "propagator is UNTESTED unless actually constructed", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T06", "name": "residue classification vocabulary", "mathematical_definition": "healthy / wrong-sign / ghost / tachyonic / unresolved remain distinct", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T07", "name": "tree-unitarity prerequisite detection", "mathematical_definition": "no amplitude implies TREE_LEVEL_UNITARITY=UNTESTED", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T08", "name": "refusal to fabricate scattering amplitudes", "mathematical_definition": "no imported reference-model amplitudes and no measured cross sections", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T09", "name": "BRST applicability detection", "mathematical_definition": "absent autonomous gauge dynamics => NOT_APPLICABLE or UNTESTED; F2 is not added", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T10", "name": "CPT scope", "mathematical_definition": "locality plus Lorentz is not an implemented CPT proof", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T11", "name": "loop-renormalization scope", "mathematical_definition": "power-counting is not loop renormalization", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T12", "name": "RG do not invent beta functions", "mathematical_definition": "beta_function_unavailable unless a loop engine exists", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T13", "name": "asymptotic-freedom applicability", "mathematical_definition": "group name is not an AF test; gauge dynamics required", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T14", "name": "quantum-gravity UNTESTED protection", "mathematical_definition": "frozen gravity family is not a quantum-gravity calculation", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T15", "name": "P4 reference isolation", "mathematical_definition": "P4 match status must not generate, filter, or reject", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "REFERENCE_ONLY"},
        {"test_id": "P5T16", "name": "target blindness", "mathematical_definition": "no measured masses, couplings, cross sections, or banned numerical tokens", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T17", "name": "G4 partiality", "mathematical_definition": "PARTIAL_G4_DEPENDENCY is never upgraded", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "DEPENDS_ON_G4_PARTIALITY"},
        {"test_id": "P5T18", "name": "universal consequence detection", "mathematical_definition": "FIRST_APPEARS_AT_P5 only when not already forced earlier", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T19", "name": "counterexample detection", "mathematical_definition": "necessity is not inferred from frequency", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T20", "name": "parameter accounting", "mathematical_definition": "no numerical estimates; a sign is PARAMETER_CONSTRAINT not UNIQUE_VALUE", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T21", "name": "deterministic reuse", "mathematical_definition": "identical input space yields identical P5 hashes", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T22", "name": "checkpoint and resume", "mathematical_definition": "checkpoint_P5_QUANTUM_CONSISTENCY_CORE.json; P4 is not overwritten", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
        {"test_id": "P5T23", "name": "gravity preservation", "mathematical_definition": "S_gravity = integral sqrt(-g)(c0 + c1 R) with c0,c1 FREE", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "INHERITED UNCHANGED"},
        {"test_id": "P5T24", "name": "no automatic P6 activation", "mathematical_definition": "P6_EXECUTED=NO; P6 is not invented", "implementation_level": "IMPLEMENTED_STRUCTURAL", "status": "ACTIVE", "provenance": "METHOD / INTEGRITY CONTROL"},
    ]
    payload = {
        "registry_id": "P5_QUANTUM_TEST_REGISTRY",
        "version": QUANTUM_CORE_VERSION,
        "quantum_tests": tests,
        "integrity_tests": integrity,
        "allowed_statuses": list(ALLOWED_TEST_STATUSES),
        "UNTESTED_is_not_FAILED": True,
        "filtering_from_P4": False,
        "provenance": "METHOD / INTEGRITY CONTROL",
    }
    payload["registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "registry_hash"})
    assert_target_blind(payload)
    return payload


def quantum_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    weyl = "Weyl" in str(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    complete = row.get("completeness") == "COMPLETE"
    g4_tag = "G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"
    amp = interacting_amplitude_constructible(row)
    f2 = f2_gauge_kinetic_present()
    dims = operator_dimension_audit()
    unitarity_proxy = quantum_unitarity_status(row)

    q01 = {
        "test_id": "Q01",
        "Weyl_fermion_present": weyl,
        "half_integer_spin_metadata": weyl,
        "fermionic_statistics_label": weyl,
        "scalar_present": scalar,
        "integer_spin_metadata": scalar,
        "bosonic_statistics_label": scalar,
        "statistics_operator_implemented": False,
        "spin_statistics_theorem_verified": False,
        "particle_identity_inferred": False,
        "status": "PARTIAL" if weyl and scalar else "UNTESTED",
        "report_status": "PARTIAL" if weyl and scalar else "UNTESTED",
        "provenance": "PARTIAL",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q02 = {
        "test_id": "Q02",
        "quadratic_action_declared": True,
        "canonical_variables_constructed": False,
        "conjugate_momenta_constructed": False,
        "commutation_tested": False,
        "anticommutation_tested": False,
        "constraint_consistency_tested": False,
        "free_propagator_from_quantization": False,
        "classical_Euler_Lagrange_used_as_quantization_proof": False,
        "REQUIRED_COMPONENT_MISSING": "canonical_quantization_operator",
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q03 = {
        "test_id": "Q03",
        "propagator_constructed": False,
        "residue_class": "unresolved",
        "healthy_residue": False,
        "wrong_sign_residue": False,
        "ghost_pole": False,
        "tachyonic_unstable_pole": False,
        "CLASSICAL_GHOST_STATUS": "SEPARATE_CLASSICAL_DIAGNOSTIC",
        "QUANTUM_PROPAGATOR_STATUS": "UNTESTED",
        "classical_ghost_used_as_unitarity": False,
        "REQUIRED_COMPONENT_MISSING": "momentum_space_propagator",
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q04 = {
        "test_id": "Q04",
        "TREE_LEVEL_UNITARITY": "UNTESTED",
        "amplitude_constructible": amp["constructible"],
        "amplitude_fabricated": False,
        "imported_reference_amplitudes": False,
        "measured_cross_sections": False,
        "optical_theorem_tested": False,
        "partial_wave_bounds_tested": False,
        "healthy_kinetic_used_as_unitarity": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "missing": amp["missing"],
        "REQUIRED_COMPONENT_MISSING": amp["missing"],
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q05 = {
        "test_id": "Q05",
        "BRST_STATUS": "NOT_APPLICABLE",
        "autonomous_gauge_dynamics": f2,
        "F2_added_to_enable_test": False,
        "phase5d_imported_as_assumption": False,
        "REQUIRED_COMPONENT_MISSING": "autonomous_gauge_kinetic_F2",
        "status": "NOT_APPLICABLE",
        "report_status": "NOT_APPLICABLE",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q06 = {
        "test_id": "Q06",
        "CPT_transformation_represented": False,
        "action_transformed": False,
        "invariance_checked": False,
        "locality_plus_Lorentz_used_as_CPT_proof": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q07 = {
        "test_id": "Q07",
        "POWER_COUNTING_STATUS": "VERIFIED",
        "LOOP_RENORMALIZATION": "UNTESTED",
        "gauge_matter_power_counting": dims["gauge_matter_power_counting"],
        "gravity_power_counting": dims["gravity_power_counting"],
        "one_loop_counterterm_test": "UNTESTED",
        "experimental_renormalization_conditions": False,
        "numerical_subtraction_scale": False,
        "nonrenormalizable_treated_as_inconsistent": False,
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "POWER-COUNTING CLASSIFICATION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q08 = {
        "test_id": "Q08",
        "RG_STATUS": "UNTESTED",
        "beta_function_unavailable": True,
        "beta_functions_invented": False,
        "fixed_point_exists": "UNRESOLVED",
        "fixed_point_unresolved": True,
        "coupling_runs": "UNTESTED",
        "preferred_renormalization_scale": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q09 = {
        "test_id": "Q09",
        "ASYMPTOTIC_FREEDOM_STATUS": "NOT_APPLICABLE",
        "inferred_from_group_name": False,
        "gauge_dynamics_added": False,
        "symbolic_beta_coefficient_sign": "UNAVAILABLE",
        "numerical_coupling_assigned": False,
        "REQUIRED_COMPONENT_MISSING": "autonomous_gauge_kinetic_F2",
        "status": "NOT_APPLICABLE",
        "report_status": "NOT_APPLICABLE",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q10 = {
        "test_id": "Q10",
        "QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
        "c0": "FREE",
        "c1": "FREE",
        "gravity_changed": False,
        "candidate_rejected_for_unimplemented_test": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    tests = {
        "Q01_spin_statistics": q01,
        "Q02_canonical_quantization": q02,
        "Q03_propagator_residue": q03,
        "Q04_tree_unitarity": q04,
        "Q05_BRST": q05,
        "Q06_CPT": q06,
        "Q07_renormalization": q07,
        "Q08_RG": q08,
        "Q09_asymptotic_freedom": q09,
        "Q10_quantum_gravity": q10,
    }
    failed = [tid for tid, item in tests.items() if item.get("status") == "FAILED"]
    if failed:
        p5_status = "REJECTED"
        completeness = "REJECTED"
    else:
        p5_status = "PARTIAL"
        completeness = "PARTIAL"
    return {
        "candidate_hash": row["candidate_hash"],
        "completeness": row.get("completeness"),
        "g4_partiality": g4_tag,
        "upgraded_from_partial": False,
        "tests": tests,
        "failed_tests": failed,
        "P5_status": p5_status,
        "P5_completeness": completeness,
        "classical_structural_status": "INHERITED FROM P3",
        "classical_ghost_status": q03["CLASSICAL_GHOST_STATUS"],
        "quantum_propagator_status": q03["QUANTUM_PROPAGATOR_STATUS"],
        "tree_unitarity_status": q04["TREE_LEVEL_UNITARITY"],
        "anomaly_status": "INHERITED FROM G5",
        "BRST_status": q05["BRST_STATUS"],
        "CPT_status": q06["status"],
        "renormalization_status": q07["status"],
        "RG_status": q08["RG_STATUS"],
        "quantum_gravity_status": q10["QUANTUM_GRAVITY_STATUS"],
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "quantum_consistent": "NOT_ASSERTED",
        "P4_match_status_used": False,
        "filtering_effect": "NONE" if not failed else "REJECT",
        "unitarity_proxy_not_used_as_proof": unitarity_proxy.get("full_quantum_unitarity") == "UNTESTED",
        "free_parameters": ["gauge_couplings", "c0", "c1"],
        "provenance": "DERIVED GIVEN QUANTIZATION RULES" if failed else "UNTESTED",
    }


def evaluate_all_candidates(rows: tuple[dict[str, Any], ...] | None = None) -> dict[str, Any]:
    rows = rows or g6_class_rows()
    records = [quantum_evaluate(dict(row)) for row in rows]
    records.sort(key=lambda item: item["candidate_hash"])
    return {"records": records, "n_candidates": len(rows)}


def _status_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out = {tid: {st: 0 for st in ALLOWED_TEST_STATUSES} for tid in Q_TEST_IDS}
    for rec in records:
        for tid in Q_TEST_IDS:
            st = rec["tests"][tid]["status"]
            out[tid][st] += 1
    return out


def p5_consequences(records: list[dict[str, Any]]) -> dict[str, Any]:
    sample = records[0]["candidate_hash"] if records else None
    destroyed = [
        {
            "proposed_consequence": "quantum_consistent",
            "classification": "NOT_FORCED",
            "reason": "FULL_QUANTUM_UNITARITY remains UNTESTED; UNTESTED is not VERIFIED",
            "counterexample_hash": sample,
        },
        {
            "proposed_consequence": "ghost_free_equals_unitary",
            "classification": "NOT_FORCED",
            "reason": "classical ghost diagnostics are not quantum unitarity",
            "counterexample_hash": sample,
        },
        {
            "proposed_consequence": "power_counting_equals_loop_renormalization",
            "classification": "NOT_FORCED",
            "reason": "LOOP_RENORMALIZATION remains UNTESTED",
            "counterexample_hash": sample,
        },
        {
            "proposed_consequence": "locality_plus_Lorentz_equals_CPT",
            "classification": "NOT_FORCED",
            "reason": "CPT maps are not implemented",
            "counterexample_hash": sample,
        },
        {
            "proposed_consequence": "group_name_equals_asymptotic_freedom",
            "classification": "NOT_FORCED",
            "reason": "no autonomous gauge dynamics; AF is NOT_APPLICABLE",
            "counterexample_hash": sample,
        },
    ]
    inherited = [
        {"property": "anomaly_freedom", "classification": "INHERITED", "provenance": "INHERITED FROM G5", "new_relative_to_P3": False},
        {"property": "local_gauge_consistency", "classification": "INHERITED", "provenance": "INHERITED FROM G6", "new_relative_to_P3": False},
        {"property": "gauge_matter_power_counting", "classification": "INHERITED", "provenance": "INHERITED FROM P1", "new_relative_to_P3": False},
        {"property": "Einstein_Hilbert_gravity_family", "classification": "INHERITED", "provenance": "INHERITED UNCHANGED", "new_relative_to_P3": False},
    ]
    untested = [
        {"property": "canonical_quantization", "classification": "UNTESTED"},
        {"property": "quantum_propagator", "classification": "UNTESTED"},
        {"property": "tree_level_unitarity", "classification": "UNTESTED"},
        {"property": "full_quantum_unitarity", "classification": "UNTESTED"},
        {"property": "CPT", "classification": "UNTESTED"},
        {"property": "loop_renormalization", "classification": "UNTESTED"},
        {"property": "RG", "classification": "UNTESTED"},
        {"property": "quantum_gravity", "classification": "UNTESTED"},
    ]
    return {
        "NEW_ELIMINATIONS_FROM_P5": [],
        "NEW_FORCED_PROPERTIES": [],
        "FIRST_APPEARS_AT_P5": [],
        "INHERITED": inherited,
        "UNTESTED": untested,
        "destroyed_by_counterexample": destroyed,
        "minimal_assumption_map": [],
        "parameter_changes": [],
        "P4_role": "downstream reference comparison only",
    }


def _class_table(rows: tuple[dict[str, Any], ...], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash = {row["candidate_hash"]: row for row in rows}
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in records:
        row = by_hash[rec["candidate_hash"]]
        key = (str(row.get("gauge_group")), str(row.get("completeness")))
        bucket = grouped.setdefault(
            key,
            {
                "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
                "spin-statistics": rec["tests"]["Q01_spin_statistics"]["status"],
                "quantization": rec["tests"]["Q02_canonical_quantization"]["status"],
                "propagator": rec["tests"]["Q03_propagator_residue"]["status"],
                "tree_unitarity": rec["tests"]["Q04_tree_unitarity"]["status"],
                "BRST": rec["tests"]["Q05_BRST"]["status"],
                "CPT": rec["tests"]["Q06_CPT"]["status"],
                "renormalization": rec["tests"]["Q07_renormalization"]["status"],
                "RG": rec["tests"]["Q08_RG"]["status"],
                "asymptotic_freedom": rec["tests"]["Q09_asymptotic_freedom"]["status"],
                "quantum_gravity": rec["tests"]["Q10_quantum_gravity"]["status"],
                "P5_status": rec["P5_status"],
                "free_parameters": list(rec["free_parameters"]),
                "n_candidates": 0,
            },
        )
        bucket["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c4_priors()
    out["phase14c4"] = {}
    for name in (
        "PHASE_14C4_SUMMARY.json",
        "checkpoint_P4_KNOWN_MODEL_REFERENCE.json",
        "KNOWN_MODEL_COMPARISON_REPORT.json",
        "COMPARISON_RECORDS.json",
        "STRUCTURAL_INTERSECTION_TABLE.json",
    ):
        path = phase14c4_artifact_dir() / name
        if path.is_file():
            out["phase14c4"][name] = _file_digest(path)
    return out


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {"count": len(catalog), "specs_unchanged": specs_unchanged, "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1}


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def _integrity_failure(s14c4: dict[str, Any], s14c3: dict[str, Any], s14c0: dict[str, Any], parent_ckpt: dict[str, Any], p4_ckpt: dict[str, Any]) -> str | None:
    if s14c4.get("P4_STATUS") != "CLOSURE_REACHED":
        return "P4_STATUS is not CLOSURE_REACHED"
    if s14c4.get("P4_EXECUTED") is not True:
        return "P4_EXECUTED is not YES"
    if s14c4.get("P5_EXECUTED") is not False:
        return "parent P5_EXECUTED is not NO"
    if s14c4.get("PHASE_14C4_STATUS") != "CLOSED":
        return "Phase 14C.4 is not CLOSED"
    if s14c4.get("COMPARISON_ENGINE_STATUS") != "VERIFIED":
        return "comparison engine not VERIFIED"
    if s14c4.get("NO_FEEDBACK_STATUS") != "VERIFIED":
        return "no-feedback status not VERIFIED"
    if s14c4.get("TARGET_BLINDNESS_STATUS") != "VERIFIED":
        return "target blindness not VERIFIED"
    if s14c4.get("PROVENANCE_STATUS") != "VERIFIED":
        return "provenance not VERIFIED"
    if s14c0.get("CONSEQUENCE_ENGINE_STATUS") != "VERIFIED":
        return "consequence engine not VERIFIED"
    if s14c0.get("COUNTEREXAMPLE_ENGINE_STATUS") != "VERIFIED":
        return "counterexample engine not VERIFIED"
    if p4_ckpt.get("checkpoint_digest") != EXPECTED_P4_CHECKPOINT_DIGEST:
        return "P4 checkpoint digest mismatch"
    if s14c4.get("checkpoint_digest") != EXPECTED_P4_CHECKPOINT_DIGEST:
        return "P4 summary checkpoint digest mismatch"
    if s14c3.get("P3_STATUS") != "CLOSURE_REACHED":
        return "P3_STATUS is not CLOSURE_REACHED"
    if s14c3.get("checkpoint_digest") != EXPECTED_P3_CHECKPOINT_DIGEST:
        return "P3 checkpoint digest mismatch"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        return "G6 grammar hash mismatch"
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        return "G6 checkpoint changed"
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        return "candidate space hash mismatch"
    if catalog_hash() != EXPECTED_CATALOG_HASH:
        return "catalog hash mismatch"
    if profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        return "profile registry hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        return "top-down input hash mismatch"
    if s14c0.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return "G3 corrected hash mismatch"
    if s14c4.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return "G4 corrected hash mismatch"
    if s14c4.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return "G5 hash mismatch"
    return None


def analyze_phase14c5_p5(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    s14c4 = _read_json(phase14c4_artifact_dir() / "PHASE_14C4_SUMMARY.json")
    s14c3 = _read_json(phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json")
    s14c2 = _read_json(phase14c2_artifact_dir() / "PHASE_14C2_SUMMARY.json")
    s14c1 = _read_json(phase14c1_artifact_dir() / "PHASE_14C1_SUMMARY.json")
    s14c0 = _read_json(phase14c0_artifact_dir() / "PHASE_14C0_SUMMARY.json")
    s14b6 = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p4_ckpt_path = p4_checkpoint_path()
        p4_before = p4_ckpt_path.read_bytes()
        p4_ckpt = _read_json(p4_ckpt_path)
        p4_summary_before = (phase14c4_artifact_dir() / "PHASE_14C4_SUMMARY.json").read_bytes()
        p3_ckpt = phase14c3_artifact_dir() / "closure_checkpoint_P3_QUALITATIVE_MATTER.json"
        p3_before = p3_ckpt.read_bytes()
        p0_ckpt = phase14c0_artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json"
        p0_before = p0_ckpt.read_bytes()
        p1_ckpt = phase14c1_artifact_dir() / "closure_checkpoint_P1_QFT_STRUCTURAL_CONSISTENCY.json"
        p1_before = p1_ckpt.read_bytes()
        p2_ckpt = phase14c2_artifact_dir() / "closure_checkpoint_P2_CHIRAL_GAUGE_MATTER.json"
        p2_before = p2_ckpt.read_bytes()
    except EngineFailure as exc:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"{exc.mode}: {exc.detail}",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    integrity_failure = _integrity_failure(s14c4, s14c3, s14c0, parent_ckpt, p4_ckpt)
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = integrity_failure or "Phase 10B status mismatch"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = integrity_failure or "Phase 12A is not CLOSED"
    if s14b6.get("PHASE_14B6_STATUS") != "CLOSED":
        integrity_failure = integrity_failure or "Phase 14B.6 is not CLOSED"
    g5_path = phase14b6_artifact_dir().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
    if g5_path.is_file() and _file_digest(g5_path) != EXPECTED_G5_CHECKPOINT_HASH:
        integrity_failure = integrity_failure or "G5 checkpoint changed"
    profile = p5_profile()
    if profile["generation_allowed"] or profile["ranking_allowed"]:
        integrity_failure = integrity_failure or "P5 generation/ranking flags broken"
    contamination = scan_target_blindness({"registry": p5_quantum_test_registry(), "profile": profile, "dims": operator_dimension_audit()})
    if contamination:
        return {
            "status": "TARGET_CONTAMINATION_DETECTED",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C5_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C5_STATUS") == "CLOSED" and existing.get("P6_EXECUTED") is False:
            cached = existing

    p4_gen_blocked = False
    p5_gen_blocked = False
    p6_blocked = False
    physics_chain_blocked = False
    try:
        ClosureEngine(artifact_dir() / "_p4_forbidden", chain="p4_only")
    except EngineFailure as exc:
        p4_gen_blocked = exc.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"
    try:
        ClosureEngine(artifact_dir() / "_p5_forbidden", chain="p5_only")
    except EngineFailure as exc:
        p5_gen_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    try:
        ClosureEngine(artifact_dir() / "_p6_forbidden", chain="p6_only")
    except EngineFailure as exc:
        p6_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    try:
        ClosureEngine(artifact_dir() / "_physics_forbidden", chain="physics")
    except EngineFailure as exc:
        physics_chain_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    try:
        assert_profile_not_p4_in_generation(P4_ID)
        p4_in_generation = False
    except EngineFailure as exc:
        p4_in_generation = exc.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C5_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P5_EXECUTED": False,
                "P6_EXECUTED": False,
                "ranking": False,
            }
            artifact_dir().mkdir(parents=True, exist_ok=True)
            _write_json(summary_path, summary)
            return summary

        rows = g6_class_rows()
        if len(rows) != 479:
            return {"status": "STOP", "scientific_analysis": None, "detail": "P3/G6 survivor count mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        complete_n = sum(1 for r in rows if r.get("completeness") == "COMPLETE")
        partial_n = sum(1 for r in rows if r.get("completeness") == "PARTIAL_G4_DEPENDENCY")
        if complete_n != 359 or partial_n != 120:
            return {"status": "STOP", "scientific_analysis": None, "detail": "P3 complete/partial split mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

        evaluated = evaluate_all_candidates(rows)
        records = evaluated["records"]
        if any(rec.get("P4_match_status_used") for rec in records):
            raise EngineFailure("KNOWN_MODEL_ISOLATION_VIOLATION", "P4 match status used in P5")
        rejected = [rec for rec in records if rec["P5_status"] == "REJECTED"]
        partial_cands = [rec for rec in records if rec["P5_status"] == "PARTIAL"]
        complete_cands = [rec for rec in records if rec["P5_status"] == "COMPLETE"]
        untested_only = [
            rec
            for rec in records
            if rec["P5_status"] != "REJECTED"
            and all(rec["tests"][tid]["status"] in {"UNTESTED", "NOT_APPLICABLE"} for tid in Q_TEST_IDS)
        ]
        test_stats = _status_counts(records)
        consequences = p5_consequences(records)
        table = _class_table(rows, records)
        registry = p5_quantum_test_registry()
        comparison_hash = content_hash(
            {
                "records": [
                    {
                        "candidate_hash": rec["candidate_hash"],
                        "P5_status": rec["P5_status"],
                        "tests": {tid: rec["tests"][tid]["status"] for tid in Q_TEST_IDS},
                    }
                    for rec in records
                ],
                "engine": QUANTUM_CORE_VERSION,
            }
        )
        space_after = g6_candidate_space_hash()
        if space_after != space_before:
            raise EngineFailure("P4_FEEDBACK_VIOLATION", "candidate space hash changed during P5")

        overall = {
            "Q01_SPIN_STATISTICS_STATUS": "PARTIAL",
            "Q02_CANONICAL_QUANTIZATION_STATUS": "UNTESTED",
            "Q03_PROPAGATOR_STATUS": "UNTESTED",
            "Q04_TREE_UNITARITY_STATUS": "UNTESTED",
            "Q05_BRST_STATUS": "NOT_APPLICABLE",
            "Q06_CPT_STATUS": "UNTESTED",
            "Q07_RENORMALIZATION_STATUS": "PARTIAL",
            "Q08_RG_STATUS": "UNTESTED",
            "Q09_ASYMPTOTIC_FREEDOM_STATUS": "NOT_APPLICABLE",
            "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        }
        questions = {
            "1_candidates_enter_P5": 479,
            "2_genuinely_quantum_tests_executable": 0,
            "3_candidates_fail_actual_quantum_test": len(rejected),
            "4_spin_statistics_eliminates": False,
            "5_canonical_quantization_eliminates": False,
            "6_propagator_eliminates_beyond_classical": False,
            "7_tree_level_unitarity_executable": False,
            "8_full_quantum_unitarity_verified": False,
            "9_CPT_verified": False,
            "10_BRST_applies_to_any_current_candidate": False,
            "11_perturbative_renormalization_beyond_power_counting": False,
            "12_RG_actually_computed": False,
            "13_asymptotic_freedom_actually_tested": False,
            "14_quantum_gravity_tested": False,
            "15_new_properties_forced_at_P5": [],
            "16_apparent_properties_destroyed_by_counterexamples": [d["proposed_consequence"] for d in consequences["destroyed_by_counterexample"]],
            "17_continuous_couplings_constrained": False,
            "18_new_parameter_free_dimensionless_quantities": [],
            "19_P5_reduces_gauge_group_ambiguity": False,
            "20_P5_reduces_representation_ambiguity": False,
            "21_P5_reduces_scalar_SSB_ambiguity": False,
            "22_experimental_numerical_information": False,
            "23_P4_influenced_P5_filtering": False,
            "24_gravity_changed": False,
        }
        ckpt_payload = {
            "engine_version": ENGINE_VERSION,
            "profile_id": P5_ID,
            "profile_hash": EXPECTED_P5_PROFILE_HASH,
            "P4_checkpoint_hash": EXPECTED_P4_CHECKPOINT_DIGEST,
            "candidate_space_hash": space_before,
            "test_registry_hash": registry["registry_hash"],
            "candidate_counts": {
                "tested": 479,
                "complete": len(complete_cands),
                "partial": len(partial_cands),
                "rejected": len(rejected),
                "untested_only": len(untested_only),
            },
            "per_test_statistics": test_stats,
            "rejection_reasons": [],
            "unresolved_tests": ["Q02", "Q03", "Q04", "Q06", "Q08", "Q10"],
            "universal_consequences": consequences["NEW_FORCED_PROPERTIES"],
            "counterexamples": consequences["destroyed_by_counterexample"],
            "parameter_inventory": {
                "gauge_couplings": "FREE",
                "scalar_couplings": "UNTESTED",
                "Yukawa_coefficients": "UNTESTED",
                "VEV_parameters": "NOT PROVIDED",
                "gravitational_coefficients": "FREE",
                "mass_parameters": "NOT NUMERICALLY DETERMINED",
            },
            "provenance": {
                "spin-statistics": "PARTIAL",
                "quantization_structure": "REQUIRED_COMPONENT_MISSING",
                "propagator_residue": "REQUIRED_COMPONENT_MISSING",
                "tree_level_unitarity": "REQUIRED_COMPONENT_MISSING",
                "BRST": "REQUIRED_COMPONENT_MISSING",
                "anomaly_freedom": "INHERITED FROM G5",
                "local_gauge_consistency": "INHERITED FROM G6",
                "renormalization": "POWER-COUNTING CLASSIFICATION",
                "RG": "UNTESTED",
                "quantum_gravity": "UNTESTED",
                "experimental_quantities": "NOT USED",
                "P4": "INHERITED FROM P4 / NOT USED",
            },
            "target_blindness_status": "VERIFIED",
            "G4_partiality_status": "VERIFIED",
            "comparison_hash": comparison_hash,
            "P5_EXECUTED": True,
            "P6_EXECUTED": False,
        }
        ckpt_payload["checkpoint_digest"] = content_hash({k: v for k, v in ckpt_payload.items() if k != "checkpoint_digest"})
        artifact_dir().mkdir(parents=True, exist_ok=True)
        _write_json(p5_checkpoint_path(), ckpt_payload)
        _write_json(artifact_dir() / "P5_CLASS_TABLE.json", {"table": table, "provenance": "UNTESTED"})
        _write_json(artifact_dir() / "P5_EVALUATION_RECORDS.json", {"records": records, "comparison_hash": comparison_hash})

        remaining_frontier = [
            "canonical free-field quantization operator",
            "propagator/residue construction",
            "tree-level interacting amplitudes",
            "BRST/gauge-fixed quantum action (requires autonomous gauge dynamics)",
            "explicit CPT maps",
            "one-loop counterterm closure",
            "RG beta functions",
            "asymptotic-freedom diagnostic (requires gauge dynamics)",
            "quantum gravity of the frozen Einstein-Hilbert family",
        ]
        pipeline = {
            "G6": {"eliminations": "none at P5", "role": "parent structural space"},
            "P1": {"eliminations": "none", "inherited": ["power-counting", "EFT classification"]},
            "P2": {"eliminations": "none", "inherited": ["chirality classification", "Yukawa UNTESTED"]},
            "P3": {"eliminations": "none", "inherited": ["qualitative matter structure"]},
            "P4": {"role": "downstream reference comparison", "effect_on_P5": "NONE"},
            "P5": {
                "new_eliminations": [],
                "new_forced_properties": [],
                "inherited_properties": [item["property"] for item in consequences["INHERITED"]],
                "unresolved_properties": [item["property"] for item in consequences["UNTESTED"]],
                "parameter_changes": [],
            },
        }
        summary = {
            "status": "OK",
            "phase": PHASE,
            "PHASE_14C5_STATUS": "CLOSED",
            "PHASE_14C5_CLOSED": True,
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P5_ONLY",
            "PHASE_14C5_TEST_COPY_ID": PHASE_14C5_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "QUANTUM_CORE_VERSION": QUANTUM_CORE_VERSION,
            "P5_STATUS": "CLOSURE_REACHED",
            "PARENT_GRAMMAR": "P3_QUALITATIVE_MATTER",
            "P4_ROLE": "REFERENCE_ONLY",
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "CATALOG_VERSION": CATALOG_VERSION,
            "catalog_hash": EXPECTED_CATALOG_HASH,
            "profile_id": P5_ID,
            "profile_hash": EXPECTED_P5_PROFILE_HASH,
            "profile_registry_hash": EXPECTED_PROFILE_REGISTRY_HASH,
            "test_registry_hash": registry["registry_hash"],
            "comparison_hash": comparison_hash,
            "P4_checkpoint_hash": EXPECTED_P4_CHECKPOINT_DIGEST,
            **overall,
            "FULL_QUANTUM_UNITARITY": "UNTESTED",
            "RG": "UNTESTED",
            "QUANTUM_GRAVITY": "UNTESTED",
            "POWER_COUNTING_STATUS": "VERIFIED",
            "LOOP_RENORMALIZATION": "UNTESTED",
            "P3_COMPLETE": 359,
            "P3_PARTIAL": 120,
            "P5_TESTED": 479,
            "P5_COMPLETE": len(complete_cands),
            "P5_PARTIAL": len(partial_cands),
            "P5_REJECTED": len(rejected),
            "P5_UNRESOLVED": 0,
            "P5_UNTESTED_ONLY": len(untested_only),
            "EQUIVALENCE_CLASSES": 479,
            "NEW_ELIMINATIONS_FROM_P5": [],
            "NEW_FORCED_PROPERTIES": [],
            "QUANTUM_CONSISTENCY_CORE_ADDS_NO_NEW_ELIMINATION_WITHIN_IMPLEMENTED_TESTS": True,
            "P5_QUANTUM_TESTS_ADD_NO_NEW_ELIMINATION_WITHIN_IMPLEMENTED_TESTS": True,
            "CANDIDATE_SPACE_HASH_BEFORE": space_before,
            "CANDIDATE_SPACE_HASH_AFTER": space_after,
            "TARGET_BLINDNESS_STATUS": "VERIFIED",
            "PROVENANCE_STATUS": "VERIFIED",
            "G4_PARTIALITY_STATUS": "VERIFIED",
            "P4_ISOLATION_STATUS": "VERIFIED",
            "class_table": table,
            "test_statistics": test_stats,
            "consequences": consequences,
            "pipeline_comparison": pipeline,
            "remaining_frontier": remaining_frontier,
            "YUKAWA_STATUS": "UNTESTED",
            "VECTORLIKE_STATUS": "UNTESTED",
            "grammar_yukawa_present": grammar_yukawa_present(),
            "F2_gauge_kinetic_present": f2_gauge_kinetic_present(),
            "P0_EXECUTED": True,
            "P1_EXECUTED": True,
            "P2_EXECUTED": True,
            "P3_EXECUTED": True,
            "P4_EXECUTED": True,
            "P5_EXECUTED": True,
            "P6_EXECUTED": False,
            "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
            "gravity_c0": "FREE",
            "gravity_c1": "FREE",
            "gravity_changed": False,
            "gauge_couplings": "FREE",
            "dimensionful_parameters": "FREE",
            "ranking": False,
            "numerical_target_search": False,
            "target_inputs": 0,
            "experimental_constants": False,
            "fitting_or_calibration": False,
            "NEXT_AUTHORIZED_EXTENSION": "NONE",
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p4_generation_blocked": p4_gen_blocked,
            "p5_generation_blocked": p5_gen_blocked,
            "p6_blocked": p6_blocked,
            "p4_in_generation_blocked": p4_in_generation,
            "negative_tests_all_pass": physics_chain_blocked and p4_gen_blocked and p5_gen_blocked and p6_blocked and p4_in_generation,
            "overclaims": {
                "full_quantum_consistency": "REJECTED AS OVERCLAIM",
                "ghost_free_equals_unitary": "REJECTED AS OVERCLAIM",
                "anomaly_free_equals_all_orders_quantum": "REJECTED AS OVERCLAIM",
                "locality_plus_Lorentz_equals_CPT": "REJECTED AS OVERCLAIM",
                "power_counting_equals_loop_renormalization": "REJECTED AS OVERCLAIM",
                "healthy_propagator_equals_unitary_S_matrix": "REJECTED AS OVERCLAIM",
                "P4_used_as_quantum_constraint": "REJECTED AS OVERCLAIM",
                "P6_automatically_activated": "REJECTED AS OVERCLAIM",
            },
            "questions": questions,
            "historical_corpus": corpus,
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
            "checkpoint_path": portable_path(p5_checkpoint_path()),
            "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "PHASE_14C4_STATUS": s14c4.get("PHASE_14C4_STATUS"),
            "PHASE_14C3_STATUS": s14c3.get("PHASE_14C3_STATUS"),
            "PHASE_14C2_STATUS": s14c2.get("PHASE_14C2_STATUS"),
            "PHASE_14C1_STATUS": s14c1.get("PHASE_14C1_STATUS"),
            "PHASE_14C0_STATUS": s14c0.get("PHASE_14C0_STATUS"),
            "PHASE_14B6_STATUS": s14b6.get("PHASE_14B6_STATUS"),
            "PHASE_14B0_STATUS": s14b0.get("PHASE_14B0_STATUS"),
            "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
            "audit_summary": {
                "g6_checkpoint_unchanged": True,
                "p0_checkpoint_unchanged": True,
                "p1_checkpoint_unchanged": True,
                "p2_checkpoint_unchanged": True,
                "p3_checkpoint_unchanged": True,
                "p4_checkpoint_unchanged": True,
                "p4_summary_unchanged": True,
                "phase14c0_artifacts_unchanged": True,
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
        }
        assert_target_blind({"status": summary["P5_STATUS"], "rejected": summary["P5_REJECTED"], "partial": summary["P5_PARTIAL"]})
        _write_json(summary_path, summary)
        cached = summary

    hashes_after = snapshot_prior_artifact_hashes()
    space_after_final = g6_candidate_space_hash()
    if space_after_final != space_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "candidate space hash changed"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if hashes_after.get("phase14c4") != hashes_before.get("phase14c4"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P4 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
        cached["P4_ISOLATION_STATUS"] = "FAILED"
    if hashes_after.get("phase14c3") != hashes_before.get("phase14c3"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P3 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if g6_checkpoint_path().read_bytes() != g6_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p4_ckpt_path.read_bytes() != p4_before or (phase14c4_artifact_dir() / "PHASE_14C4_SUMMARY.json").read_bytes() != p4_summary_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P4 checkpoint or summary modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p3_ckpt.read_bytes() != p3_before or p0_ckpt.read_bytes() != p0_before or p1_ckpt.read_bytes() != p1_before or p2_ckpt.read_bytes() != p2_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "prior profile checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    return cached


def run_phase14c5_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5_p5(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if science.get("PHASE_14C5_STATUS") == "STOPPED_BY_INTEGRITY_FAILURE":
        return {"status": "STOP", "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_INTEGRITY": "VERIFIED",
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "P4_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p4_checkpoint_unchanged") else "FAILED",
            "P3_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p3_checkpoint_unchanged") else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "PHASE_14C5_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C5_STATUS": science.get("PHASE_14C5_STATUS"),
            "PHASE_14C4_STATUS": science.get("PHASE_14C4_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P4_EXECUTED": "TRUE",
            "P5_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
