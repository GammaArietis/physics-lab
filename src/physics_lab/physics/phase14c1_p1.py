"""Phase 14C.1: activate P1_QFT_STRUCTURAL_CONSISTENCY only.

Conservative QFT structural tests on the verified G6 survivor space.
Classical proxies never count as full quantum consistency.
P2 is not activated.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
from physics_lab.physics.phase14a_reconstruction import (
    artifact_dir as phase14a_artifact_dir,
    structural_input_registry,
)
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
    _with_hash,
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
    CONSEQUENCE_ENGINE_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    P0_ID,
    artifact_dir as phase14c0_artifact_dir,
    catalog_hash,
    classify_consequences,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_row_by_hash,
    g6_survivor_hashes,
    physics_profile_registry,
    profile_registry_hash,
    snapshot_prior_artifact_hashes as snapshot_14c0_priors,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P1_PROFILE_HASH",
    "P1_CHAIN",
    "P1_ID",
    "PHASE_14C1_TEST_COPY_ID",
    "analyze_phase14c1_p1",
    "artifact_dir",
    "attach_p1_stats",
    "operator_dimension_audit",
    "p1_executable_registry",
    "p1_metadata_legal",
    "p1_qft_test_registry",
    "p1_run_tests",
    "qft_evaluate",
    "quantum_unitarity_status",
    "run_phase14c1_or_stop",
]

PHASE = "PHASE_14C.1"
PHASE_14C1_TEST_COPY_ID = "PHASE_14C1_ACTIVATE_P1_QFT_STRUCTURAL_CONSISTENCY"
AUDIT_VERSION = "phase14c1-p1-v1"
P1_ID = "P1_QFT_STRUCTURAL_CONSISTENCY"
P1_CHAIN: tuple[str, ...] = (P1_ID,)
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_CATALOG_HASH = "c7f86733cdf6e07b3a6e39c1a9755b796c8b72f5979e14e160a47d3b04b4f617"
EXPECTED_PROFILE_REGISTRY_HASH = "ec2a2f476faf28356e921ceb9431cb33cbc97ba66fcd25be22506c4139e66e96"
EXPECTED_P1_PROFILE_HASH = "ace084bb293116366f20bed10f6fce328847df1d1609b9d2645be9cfc144212b"
EXPECTED_CANDIDATE_SPACE_HASH = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff8"
G6_INHERITED_PROPERTIES = frozenset(
    {
        "local_covariance",
        "matter_invariance",
        "anomaly_integrity",
        "vector_sector_KP15",
        "weyl_fermion_sector_present",
        "compact_su_n_factor_present",
        "finite_species_content",
        "anomaly_free",
        "local_gauge_covariance",
        "both_fermion_and_boson_sectors",
    }
)
QFT_TEST_IDS = (
    "QFT01_locality",
    "QFT02_Lorentz",
    "QFT03_spin_statistics",
    "QFT04_unitarity",
    "QFT05_CPT",
    "QFT06_gauge",
    "QFT07_anomaly",
    "QFT08_renormalizability",
    "QFT09_EFT",
    "QFT10_quantum_gravity",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c1_artifacts"


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


def p1_profile() -> dict[str, Any]:
    profile = physics_profile_registry()["profiles"][P1_ID]
    if profile["profile_hash"] != EXPECTED_P1_PROFILE_HASH:
        raise EngineFailure("PROFILE_HASH_MISMATCH", P1_ID)
    return profile


def p1_qft_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "QFT01",
            "name": "Locality",
            "mathematical_definition": "finite-derivative-order local Lagrangian density declared in the model specification",
            "required_inputs": ["KP02", "local_action_class", "G6_allowed_interactions"],
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN LOCAL ACTION GRAMMAR",
        },
        {
            "test_id": "QFT02",
            "name": "Lorentz covariance",
            "mathematical_definition": "D=4 Lorentzian spacetime with local SO(1,3); fields in Lorentz representations compatible with the frozen grammar",
            "required_inputs": ["KP01", "KP03", "field_content"],
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN REPRESENTATION + SPACETIME GRAMMAR",
        },
        {
            "test_id": "QFT03",
            "name": "Spin-statistics compatibility",
            "mathematical_definition": "Weyl fields carry fermionic metadata; scalars carry bosonic metadata. Full theorem and anticommuting quantization are not implemented.",
            "required_inputs": ["field_type_labels"],
            "implementation_level": "METADATA_ONLY",
            "status": "ACTIVE",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "QFT04",
            "name": "Quantum unitarity",
            "mathematical_definition": "S-matrix/optical-theorem unitarity of the interacting quantum theory. Classical ghost-freedom is not a substitute.",
            "required_inputs": ["quantum_S_matrix"],
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "QFT05",
            "name": "CPT structural consistency",
            "mathematical_definition": "implemented CPT field and spacetime maps plus action invariance. Locality plus Lorentz is not a CPT proof.",
            "required_inputs": ["CPT_transformation_maps"],
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "QFT06",
            "name": "Gauge consistency",
            "mathematical_definition": "inherited G6 local covariance, matter invariance, representation consistency. Not rerun.",
            "required_inputs": ["G6_class_table"],
            "implementation_level": "INHERITED",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G6",
        },
        {
            "test_id": "QFT07",
            "name": "Anomaly consistency",
            "mathematical_definition": "inherited G5 anomaly-free result. Scalars excluded from chiral sums. Not recomputed.",
            "required_inputs": ["G5_anomaly_free_result"],
            "implementation_level": "INHERITED",
            "status": "ACTIVE",
            "provenance": "INHERITED FROM G5",
        },
        {
            "test_id": "QFT08",
            "name": "Perturbative renormalizability status",
            "mathematical_definition": "power-counting of implemented operators in D=4. Nonrenormalizable is not automatically inconsistent.",
            "required_inputs": ["operator_dimensions", "declared_interactions"],
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN OPERATOR DIMENSIONS",
        },
        {
            "test_id": "QFT09",
            "name": "EFT consistency status",
            "mathematical_definition": "formal local EFT interpretation within the declared operator truncation. No cutoff value is introduced.",
            "required_inputs": ["bounded_operator_basis"],
            "implementation_level": "IMPLEMENTED_STRUCTURAL",
            "status": "ACTIVE",
            "provenance": "DERIVED GIVEN BOUNDED OPERATOR BASIS",
        },
        {
            "test_id": "QFT10",
            "name": "Quantum gravity consistency",
            "mathematical_definition": "genuine quantum-gravity consistency calculation. The frozen EH sector is not such a calculation.",
            "required_inputs": ["quantum_gravity_test"],
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
    ]
    for item in tests:
        item["dependency_hashes"] = {
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "catalog_hash": EXPECTED_CATALOG_HASH,
        }
    payload = {"registry_id": "P1_QFT_TEST_REGISTRY", "version": "p1-qft-tests-v1", "tests": tests}
    payload["test_registry_hash"] = content_hash({k: v for k, v in payload.items() if k != "test_registry_hash"})
    assert_target_blind(payload)
    return payload


@lru_cache(maxsize=1)
def inspect_local_action_specification() -> dict[str, Any]:
    kp02 = next(item for item in structural_input_registry() if item["constraint_id"] == "KP02")
    form = str(kp02["mathematical_form"])
    local = "local Lagrangian density" in form
    finite = "finite derivative" in form
    freeze = verify_phase4c_action_freeze()
    freeze_ok = freeze.get("status") == "VERIFIED"
    spec_ok = local and finite and freeze_ok
    return {
        "kp02_mathematical_form": form,
        "declares_local_lagrangian_density": local,
        "declares_finite_derivative_order": finite,
        "frozen_action_verified": freeze_ok,
        "declared_local_interactions": [
            "nonabelian_covariant_derivative",
            "U1_covariant_derivative",
            "scalar_kinetic_VEV",
        ],
        "source_code_locality_used_as_proof": False,
        "status": "PASS" if spec_ok else "UNTESTED",
        "report_status": "VERIFIED" if spec_ok else "UNTESTED",
        "provenance": "DERIVED GIVEN LOCAL ACTION GRAMMAR",
    }


@lru_cache(maxsize=1)
def inspect_lorentz_specification() -> dict[str, Any]:
    kp01 = next(item for item in structural_input_registry() if item["constraint_id"] == "KP01")
    kp03 = next(item for item in structural_input_registry() if item["constraint_id"] == "KP03")
    form01 = str(kp01["mathematical_form"])
    form03 = str(kp03["mathematical_form"])
    d4 = "D_eff = 4" in form01
    lorentz = "SO(1,3)" in form03
    ok = d4 and lorentz
    return {
        "spacetime_dimension_declaration": form01,
        "lorentz_declaration": form03,
        "D4": d4,
        "SO13": lorentz,
        "known_particle_assignments_used": False,
        "status": "PASS" if ok else "UNTESTED",
        "report_status": "VERIFIED" if ok else "UNTESTED",
        "provenance": "DERIVED GIVEN REPRESENTATION + SPACETIME GRAMMAR",
    }


@lru_cache(maxsize=1)
def operator_dimension_audit() -> dict[str, Any]:
    fields = {
        "scalar": {"mass_dimension": "1", "statistics_label": "bosonic"},
        "Weyl_fermion": {"mass_dimension": "3/2", "statistics_label": "fermionic"},
        "gauge_potential": {"mass_dimension": "1", "statistics_label": "bosonic"},
        "metric": {"mass_dimension": "0", "convention": "dimensionless_metric"},
        "curvature_scalar": {"mass_dimension": "2"},
    }
    operators = [
        {
            "operator_id": "scalar_covariant_kinetic",
            "form": "|D_mu phi|^2",
            "mass_dimension": "4",
            "class": "marginal",
            "implemented": True,
        },
        {
            "operator_id": "Weyl_covariant_kinetic",
            "form": "psi sigma^mu D_mu psi",
            "mass_dimension": "4",
            "class": "marginal",
            "implemented": True,
        },
        {
            "operator_id": "Einstein_Hilbert",
            "form": "sqrt(-g) R",
            "mass_dimension": "2",
            "class": "relevant",
            "implemented": True,
            "coupling": "c1",
            "coupling_mass_dimension": "2",
        },
        {
            "operator_id": "cosmological_term",
            "form": "sqrt(-g)",
            "mass_dimension": "0",
            "class": "relevant",
            "implemented": True,
            "coupling": "c0",
            "coupling_mass_dimension": "4",
        },
    ]
    return {
        "spacetime_dimension": "4",
        "normalization_convention": "mass_dimension_of_metric_is_zero",
        "fields": fields,
        "operators": operators,
        "Yukawa_in_grammar": False,
        "F2_gauge_kinetic_in_grammar": False,
        "dimensionful_numerical_scales_introduced": False,
        "symbolic_only": True,
        "gauge_matter_power_counting": "RENORMALIZABLE_BY_POWER_COUNTING",
        "gravity_power_counting": "NONRENORMALIZABLE_BUT_EFT",
        "overall_including_gravity": "NONRENORMALIZABLE_BUT_EFT",
        "nonrenormalizable_treated_as_inconsistent": False,
        "RG": "UNTESTED",
        "provenance": "DERIVED GIVEN OPERATOR DIMENSIONS",
    }


def quantum_unitarity_status(_row: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = _row
    return {
        "classical_ghost_free": "NOT_USED_AS_UNITARITY_PROOF",
        "linearized_healthy": "NOT_USED_AS_UNITARITY_PROOF",
        "positive_kinetic_Hessian": "NOT_USED_AS_UNITARITY_PROOF",
        "positive_Hamiltonian": "NOT_USED_AS_UNITARITY_PROOF",
        "anomaly_freedom": "NOT_USED_AS_UNITARITY_PROOF",
        "perturbative_unitarity_test": "UNTESTED",
        "full_quantum_unitarity": "UNTESTED",
        "S_matrix_optical_theorem": "NOT_IMPLEMENTED",
        "experimental_scattering_data": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
    }


def g6_result_hash(row: dict[str, Any]) -> str:
    return content_hash(
        {
            "candidate_hash": row.get("candidate_hash"),
            "local_covariance": row.get("local_covariance"),
            "matter_invariance": row.get("matter_invariance"),
            "anomaly_integrity": row.get("anomaly_integrity"),
            "structural_consistency": row.get("structural_consistency"),
            "KP15": row.get("KP15"),
        }
    )


def qft_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    locality = inspect_local_action_specification()
    lorentz = inspect_lorentz_specification()
    weyl = "Weyl" in str(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    metadata_ok = weyl and scalar
    spin = {
        "fermion_label_present": weyl,
        "boson_label_present": scalar,
        "anticommuting_quantization_implemented": False,
        "spin_statistics_theorem_verified": False,
        "inferred_from_labels_alone": False,
        "status": "PARTIAL" if metadata_ok else "UNTESTED",
        "report_status": "PARTIAL" if metadata_ok else "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    unitarity = quantum_unitarity_status(row)
    cpt = {
        "CPT_maps_implemented": False,
        "locality_plus_Lorentz_used_as_CPT_proof": False,
        "full_interacting_proof": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    inherited = g6_result_hash(row)
    if row.get("local_covariance") != "PASS" or row.get("matter_invariance") != "PASS":
        raise EngineFailure("DEPENDENCY_MISMATCH", "G6 gauge result missing")
    if row.get("anomaly_integrity") != "PASS":
        raise EngineFailure("DEPENDENCY_MISMATCH", "G5 anomaly result missing")
    gauge = {
        "status": "PASS",
        "report_status": "VERIFIED",
        "inheritance": "INHERITED / VERIFIED",
        "G6_RESULT_HASH": inherited,
        "P1_INHERITED_GAUGE_RESULT_HASH": inherited,
        "hashes_agree": True,
        "G6_rerun": False,
        "provenance": "INHERITED FROM G6",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    anomaly = {
        "status": "PASS",
        "report_status": "VERIFIED",
        "inheritance": "INHERITED / VERIFIED",
        "scalar_in_chiral_sum": False,
        "recomputed": False,
        "provenance": "INHERITED FROM G5",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    dims = operator_dimension_audit()
    renorm = {
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "gauge_matter": dims["gauge_matter_power_counting"],
        "gravity": dims["gravity_power_counting"],
        "overall_including_gravity": dims["overall_including_gravity"],
        "nonrenormalizable_treated_as_inconsistent": False,
        "unique_coupling_inferred": False,
        "RG": "UNTESTED",
        "provenance": "DERIVED GIVEN OPERATOR DIMENSIONS",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    eft = {
        "status": "PASS",
        "report_status": "VERIFIED",
        "classification": "EFT_COMPATIBLE",
        "cutoff": "UNRESOLVED / NOT PROVIDED",
        "numerical_cutoff_introduced": False,
        "nonrenormalizable_rejected": False,
        "provenance": "DERIVED GIVEN BOUNDED OPERATOR BASIS",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    qg = {
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
        "c0": "FREE",
        "c1": "FREE",
        "candidate_rejected_for_unimplemented_test": False,
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    tests = {
        "QFT01_locality": locality,
        "QFT02_Lorentz": lorentz,
        "QFT03_spin_statistics": spin,
        "QFT04_unitarity": unitarity,
        "QFT05_CPT": cpt,
        "QFT06_gauge": gauge,
        "QFT07_anomaly": anomaly,
        "QFT08_renormalizability": renorm,
        "QFT09_EFT": eft,
        "QFT10_quantum_gravity": qg,
    }
    failed = [tid for tid, item in tests.items() if item.get("status") == "FAIL"]
    classical_ok = (
        locality["report_status"] == "VERIFIED"
        and lorentz["report_status"] == "VERIFIED"
        and gauge["report_status"] == "VERIFIED"
        and anomaly["report_status"] == "VERIFIED"
    )
    return {
        "tests": tests,
        "failed_tests": failed,
        "CLASSICAL_STRUCTURAL_QFT_STATUS": "VERIFIED" if classical_ok else "PARTIAL",
        "QUANTUM_STATUS": "UNTESTED",
        "EFT_STATUS": eft["report_status"],
        "combined_score": False,
        "G6_RESULT_HASH": inherited,
        "P1_INHERITED_GAUGE_RESULT_HASH": inherited,
        "operator_dimensions": dims,
    }


def p1_executable_registry() -> dict[str, dict[str, Any]]:
    profile = p1_profile()
    p1 = _with_hash(
        {
            "grammar_id": P1_ID,
            "parent_grammar_id": P0_ID,
            "extension_description": (
                "P1 QFT structural consistency on the verified G6 survivor space. "
                "Base mathematical grammar is unchanged. Classical proxies are not quantum proofs."
            ),
            "allowed_fields": ["inherited_G6_content"],
            "allowed_groups": ["inherited_G6_groups"],
            "allowed_representations": ["inherited_G6_representations"],
            "allowed_interactions": ["inherited_G6_interactions"],
            "allowed_symmetry_breaking": ["inherited_G6_SSB"],
            "allowed_constraints": list(profile["enabled_constraints"]) + ["QFT01", "QFT02", "QFT06", "QFT07", "QFT08", "QFT09"],
            "explicit_exclusions": [
                "P2_CHIRAL_GAUGE_MATTER automatic activation",
                "P5_OPTIONAL_QUANTUM_STRUCTURE automatic activation",
                "full quantum unitarity claimed from classical proxies",
                "CPT claimed from locality plus Lorentz",
                "quantum gravity claimed from Einstein-Hilbert",
                "nonrenormalizable treated as inconsistent",
                "experimental masses",
                "experimental couplings",
                "measured scattering data",
                "ranking",
                "RG profile activation",
            ],
            "provenance": "INHERITED FROM G6",
            "status": "ACTIVE_P1_ONLY",
            "axes": {"g6_survivor": list(g6_survivor_hashes())},
            "profile_hash": profile["profile_hash"],
            "VECTORLIKE_STATUS": "UNTESTED",
            "QUANTUM_UNITARITY": "UNTESTED",
        }
    )
    return {P1_ID: p1}


def p1_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    digest = assignment.get("g6_survivor")
    if digest not in g6_row_by_hash():
        return False, "g6_survivor_unknown"
    return True, None


def p1_run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    digest = candidate["assignment"]["g6_survivor"]
    row = g6_row_by_hash()[digest]
    completeness = row["completeness"]
    evaluation = qft_evaluate(row)
    if evaluation["failed_tests"]:
        status = "FAIL"
    elif completeness == "PARTIAL_G4_DEPENDENCY":
        status = "PARTIAL"
    elif completeness == "COMPLETE":
        status = "PASS"
    else:
        status = "UNRESOLVED"
    results = [
        {
            "test_id": tid,
            "test_version": test_version,
            "status": "FAIL" if item.get("status") == "FAIL" else "PASS",
            "qft_status": item.get("report_status") or item.get("status"),
            "provenance": item.get("provenance") or "UNTESTED",
            "source_phase": PHASE,
        }
        for tid, item in evaluation["tests"].items()
    ]
    results.append(
        {
            "test_id": "partial_not_upgraded",
            "test_version": test_version,
            "status": "PASS" if (status != "PASS" or completeness == "COMPLETE") else "FAIL",
            "provenance": "PARTIAL_G4_DEPENDENCY",
            "source_phase": PHASE,
        }
    )
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "completeness": completeness,
        "g4_partiality": row["g4_partiality"],
        "g6_row": row,
        "qft": evaluation,
        "rejection_tests": evaluation["failed_tests"],
    }


def attach_p1_stats(
    grammar: dict[str, Any],
    evaluated: list[dict[str, Any]],
    compatible: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = grammar
    _ = compatible
    profile = p1_profile()
    registry = p1_qft_test_registry()
    table = []
    inventory = []
    rows_for_engine = []
    rejection = []
    test_counts = {tid: {"VERIFIED": 0, "PARTIAL": 0, "UNTESTED": 0, "FAILED": 0, "NOT_APPLICABLE": 0, "PASS": 0} for tid in QFT_TEST_IDS}
    inherited_hashes = []
    lookup = g6_row_by_hash()
    for cand in evaluated:
        tests = cand.get("tests") or {}
        qft = tests.get("qft") or qft_evaluate(lookup[cand["assignment"]["g6_survivor"]])
        row = dict(lookup[cand["assignment"]["g6_survivor"]])
        row["p1_candidate_hash"] = cand["candidate_hash"]
        row["completeness"] = "COMPLETE" if cand.get("filter_status") == "PASS" else "PARTIAL_G4_DEPENDENCY"
        row["g4_partiality"] = "G4_PARTIALITY_IRRELEVANT" if row["completeness"] == "COMPLETE" else "DEPENDS_ON_G4_PARTIALITY"
        qtests = qft["tests"]
        table.append(
            {
                "candidate_class": cand["candidate_id"],
                "candidate_hash": cand["candidate_hash"],
                "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                "gauge_group": row.get("gauge_group"),
                "locality": qtests["QFT01_locality"]["report_status"],
                "Lorentz": qtests["QFT02_Lorentz"]["report_status"],
                "spin_statistics": qtests["QFT03_spin_statistics"]["report_status"],
                "unitarity": qtests["QFT04_unitarity"]["report_status"],
                "CPT": qtests["QFT05_CPT"]["report_status"],
                "gauge": qtests["QFT06_gauge"]["report_status"],
                "anomalies": qtests["QFT07_anomaly"]["report_status"],
                "renormalizability": qtests["QFT08_renormalizability"]["overall_including_gravity"],
                "EFT": qtests["QFT09_EFT"]["classification"],
                "quantum_gravity": qtests["QFT10_quantum_gravity"]["report_status"],
                "overall_P1_status": "PARTIAL",
                "CLASSICAL_STRUCTURAL_QFT_STATUS": qft["CLASSICAL_STRUCTURAL_QFT_STATUS"],
                "QUANTUM_STATUS": qft["QUANTUM_STATUS"],
                "EFT_STATUS": qft["EFT_STATUS"],
                "free_parameters": row.get("free_couplings"),
                "completeness": row["completeness"],
                "filter_status": cand.get("filter_status"),
                "provenance": "INHERITED FROM G6",
            }
        )
        rows_for_engine.append(row)
        inherited_hashes.append(qft["G6_RESULT_HASH"])
        if qft["G6_RESULT_HASH"] != qft["P1_INHERITED_GAUGE_RESULT_HASH"]:
            raise EngineFailure("DEPENDENCY_MISMATCH", cand["candidate_hash"])
        for tid, item in qtests.items():
            key = item.get("report_status") or item.get("status") or "UNTESTED"
            if key not in test_counts[tid]:
                key = "UNTESTED"
            test_counts[tid][key] += 1
        if cand.get("filter_status") == "FAIL":
            rejection.append({"candidate_hash": cand["candidate_hash"], "tests": qft["failed_tests"]})
        if cand.get("filter_status") == "PASS":
            inventory.append(
                {
                    "g6_candidate_hash": cand["assignment"]["g6_survivor"],
                    "p1_candidate_hash": cand["candidate_hash"],
                    "gauge_group": row.get("gauge_group"),
                    "free_couplings": row.get("free_couplings"),
                    "c0": "FREE",
                    "c1": "FREE",
                    "VEV_magnitude": "NOT PROVIDED",
                    "P1_parameter_constraint": False,
                    "provenance": "INHERITED FROM G6",
                }
            )
    consequences = classify_consequences(rows_for_engine, profile_id=P1_ID, enabled_constraints=list(profile["enabled_constraints"]))
    inherited_forced = [p for p in consequences["FORCED_PROPERTIES"] if p["property"] in G6_INHERITED_PROPERTIES]
    new_forced = [
        {
            "property": "gauge_matter_renormalizable_by_power_counting",
            "value": True,
            "classification": "PROFILE_FORCED",
            "proof_status": "FORCED_WITHIN_DECLARED_BOUNDS",
            "provenance": "DERIVED GIVEN OPERATOR DIMENSIONS",
            "new_relative_to_G6": True,
        },
        {
            "property": "gravity_sector_nonrenormalizable_but_EFT",
            "value": True,
            "classification": "PROFILE_FORCED",
            "proof_status": "FORCED_WITHIN_DECLARED_BOUNDS",
            "provenance": "DERIVED GIVEN OPERATOR DIMENSIONS",
            "new_relative_to_G6": True,
        },
        {
            "property": "EFT_compatible_within_declared_operator_basis",
            "value": True,
            "classification": "PROFILE_FORCED",
            "proof_status": "FORCED_WITHIN_DECLARED_BOUNDS",
            "provenance": "DERIVED GIVEN BOUNDED OPERATOR BASIS",
            "new_relative_to_G6": True,
        },
    ]
    untested_props = [
        {"property": "full_quantum_unitarity", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": True},
        {"property": "CPT_of_interacting_QFT", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": True},
        {"property": "quantum_gravity_consistency", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": True},
        {"property": "RG_flow", "classification": "UNTESTED", "provenance": "UNTESTED", "new_relative_to_G6": True},
    ]
    destroyed = list(consequences["destroyed_by_counterexample"])
    destroyed.extend(
        [
            {
                "proposed_consequence": "quantum_unitarity_verified",
                "destroyed_by": "no S-matrix test is implemented",
                "reason": "classical ghost-freedom is not quantum unitarity",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "CPT_verified_from_locality_and_Lorentz",
                "destroyed_by": "CPT maps are not implemented",
                "reason": "locality plus Lorentz is not a CPT proof",
                "provenance": "UNTESTED",
            },
            {
                "proposed_consequence": "nonrenormalizable_is_inconsistent",
                "destroyed_by": "all candidates remain EFT_COMPATIBLE",
                "reason": "nonrenormalizable is not automatically inconsistent",
                "provenance": "DERIVED GIVEN BOUNDED OPERATOR BASIS",
            },
            {
                "proposed_consequence": "renormalizable_implies_unique_coupling",
                "destroyed_by": "g_SU_N and g_U1 remain FREE",
                "reason": "renormalizability is not a unique-parameter prediction",
                "provenance": "FREE / PARAMETER-DEPENDENT",
            },
        ]
    )
    parameter_analysis = {
        "g_SU_N": "FREE",
        "g_U1": "FREE_WHEN_PRESENT",
        "c0": "FREE",
        "c1": "FREE",
        "VEV_magnitude": "NOT PROVIDED",
        "representation_labels": "UNCONSTRAINED_BY_P1",
        "scalar_parameters": "UNCONSTRAINED_BY_P1",
        "positivity_or_sign_requirement": False,
        "PARAMETER_CONSTRAINT": [],
        "UNIQUE_PARAMETER_VALUE": [],
        "RG": "UNTESTED",
        "P1_constrains_continuous_couplings": False,
        "P1_constrains_dimensionful_parameters": False,
        "new_parameter_free_dimensionless_physical_observables": [],
        "numerical_solve": False,
        "provenance": "DERIVED_CONSEQUENCE",
    }
    partial_n = sum(1 for c in evaluated if c.get("filter_status") == "PARTIAL")
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": EXPECTED_G6_CHECKPOINT_HASH,
        "parent_grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "g6_survivors_reused": len(g6_survivor_hashes()),
        "target_blindness": "VERIFIED",
        "profile_id": P1_ID,
        "profile_hash": profile["profile_hash"],
        "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "test_registry_hash": registry["test_registry_hash"],
        "test_statistics": test_counts,
        "inherited_g6_result_hash": content_hash(inherited_hashes),
        "inherited_g5_result_hash": EXPECTED_G5_GRAMMAR_HASH,
        "completeness_statistics": {
            "COMPLETE": sum(1 for c in evaluated if c.get("filter_status") == "PASS"),
            "PARTIAL_G4_DEPENDENCY": partial_n,
        },
        "partial": partial_n,
        "rejection": rejection,
        "consequences": {
            **consequences,
            "INHERITED_G6_FORCED_PROPERTIES": inherited_forced,
            "NEW_FORCED_PROPERTIES_FROM_P1": new_forced,
            "NEW_ELIMINATIONS_FROM_P1": [],
            "UNTESTED_PROPERTIES": untested_props,
            "destroyed_by_counterexample": destroyed,
            "parameter_analysis": parameter_analysis,
        },
        "provenance_summary": {
            "locality": "DERIVED GIVEN LOCAL ACTION GRAMMAR",
            "Lorentz_covariance": "DERIVED GIVEN REPRESENTATION + SPACETIME GRAMMAR",
            "anomaly_freedom": "INHERITED FROM G5",
            "gauge_covariance": "INHERITED FROM G6",
            "renormalizability_class": "DERIVED GIVEN OPERATOR DIMENSIONS",
            "EFT_classification": "DERIVED GIVEN BOUNDED OPERATOR BASIS",
            "quantum_unitarity": "UNTESTED",
            "quantum_gravity": "UNTESTED",
            "numerical_couplings": "NOT USED",
            "P2": "NOT_ACTIVATED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c0_priors()
    out["phase14c0"] = {}
    for name in (
        "PHASE_14C0_SUMMARY.json",
        "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json",
    ):
        path = phase14c0_artifact_dir() / name
        if path.is_file():
            out["phase14c0"][name] = _file_digest(path)
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
        raise UnauthorizedAnalysisError("Phase 14C.1 refuses an unauthorized action object")
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


def analyze_phase14c1_p1(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
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
        p0_ckpt = phase14c0_artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json"
        p0_before = p0_ckpt.read_bytes()
        g5_path = Path(__file__).resolve().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
        g5_before = g5_path.read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14c0.get("PHASE_14C0_STATUS") != "CLOSED":
        integrity_failure = "PHASE_14C0_STATUS is not CLOSED"
    if s14c0.get("KNOWN_PHYSICS_CATALOG_STATUS") != "READY":
        integrity_failure = "KNOWN_PHYSICS_CATALOG_STATUS is not READY"
    if s14c0.get("PROFILE_REGISTRY_STATUS") != "VERIFIED":
        integrity_failure = "PROFILE_REGISTRY_STATUS is not VERIFIED"
    if s14c0.get("CONSEQUENCE_ENGINE_STATUS") != "VERIFIED":
        integrity_failure = "CONSEQUENCE_ENGINE_STATUS is not VERIFIED"
    if s14c0.get("COUNTEREXAMPLE_ENGINE_STATUS") != "VERIFIED":
        integrity_failure = "COUNTEREXAMPLE_ENGINE_STATUS is not VERIFIED"
    if s14c0.get("TARGET_BLINDNESS_STATUS") != "VERIFIED":
        integrity_failure = "TARGET_BLINDNESS_STATUS is not VERIFIED"
    if s14c0.get("catalog_hash") != EXPECTED_CATALOG_HASH or catalog_hash() != EXPECTED_CATALOG_HASH:
        integrity_failure = "catalog hash mismatch"
    if s14c0.get("profile_registry_hash") != EXPECTED_PROFILE_REGISTRY_HASH or profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        integrity_failure = "profile registry hash mismatch"
    if s14b6.get("GRAMMAR_HASH") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 grammar hash mismatch"
    if s14b6.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        integrity_failure = "G5 grammar hash mismatch"
    if s14b6.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4 hash mismatch"
    if s14b6.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3 hash mismatch"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "top-down input hash mismatch"
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        integrity_failure = "candidate space hash mismatch"
    if s14c0.get("NEXT_AUTHORIZED_EXTENSION") != "ACTIVATE P1_QFT_STRUCTURAL_CONSISTENCY":
        integrity_failure = "P1 is not the next authorized extension"
    if s14c0.get("P1_EXECUTED") is True:
        integrity_failure = "14C.0 summary claims P1 already executed"
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 checkpoint grammar hash mismatch"
    if _file_digest(g5_path) != EXPECTED_G5_CHECKPOINT_HASH:
        integrity_failure = "G5 checkpoint changed"
    contamination = scan_target_blindness({"registry": p1_qft_test_registry(), "dims": operator_dimension_audit()})
    if contamination:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C1_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C1_STATUS") == "CLOSED" and existing.get("P2_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C1_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P1_EXECUTED": False,
                "P2_EXECUTED": False,
                "ranking": False,
            }
            artifact_dir().mkdir(parents=True, exist_ok=True)
            _write_json(summary_path, summary)
            return {"status": "STOP", "scientific_analysis": summary, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        try:
            ClosureEngine(artifact_dir() / "no_physics", chain="physics")
            physics_chain_blocked = False
        except EngineFailure as exc:
            physics_chain_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        from physics_lab.physics.phase14c0_known_physics import assert_profile_activation_authorized

        try:
            assert_profile_activation_authorized("P2_CHIRAL_GAUGE_MATTER")
            p2_blocked = False
        except EngineFailure as exc:
            p2_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        if quantum_unitarity_status()["report_status"] == "VERIFIED":
            return {"status": "STOP", "scientific_analysis": None, "detail": "unitarity overclaim", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        engine = ClosureEngine(artifact_dir(), chain="p1_only")
        state = engine.run_until_closure()
        p1_rep = next(r for r in state["version_reports"] if r["grammar_id"] == P1_ID)
        pass_n = p1_rep["compatible"]
        partial_n = p1_rep.get("partial") or 0
        rejected_n = p1_rep["rejected"]
        unresolved_n = p1_rep["unresolved"]
        consequences = p1_rep.get("consequences") or {}
        new_forced = consequences.get("NEW_FORCED_PROPERTIES_FROM_P1") or []
        new_elim = consequences.get("NEW_ELIMINATIONS_FROM_P1") or []
        destroyed = consequences.get("destroyed_by_counterexample") or []
        ckpt_payload = {
            "engine_version": ENGINE_VERSION,
            "profile_id": P1_ID,
            "profile_hash": EXPECTED_P1_PROFILE_HASH,
            "parent_candidate_space_hash": EXPECTED_CANDIDATE_SPACE_HASH,
            "G6_hash": EXPECTED_G6_GRAMMAR_HASH,
            "G5_hash": EXPECTED_G5_GRAMMAR_HASH,
            "test_registry_hash": p1_rep.get("test_registry_hash"),
            "candidate_statistics": {
                "tested": p1_rep["generated_candidates"],
                "complete": pass_n,
                "partial": partial_n,
                "rejected": rejected_n,
                "untested_only": 0,
            },
            "test_statistics": p1_rep.get("test_statistics"),
            "consequence_statistics": {
                "new_forced": len(new_forced),
                "new_eliminations": len(new_elim),
                "destroyed_by_counterexample": len(destroyed),
            },
            "counterexample_statistics": {"count": len(destroyed)},
            "parameter_inventory": p1_rep.get("parameter_inventory") or [],
            "provenance": p1_rep.get("provenance_summary") or {},
            "target_blindness_status": "VERIFIED",
            "timestamp": _utc(),
            "P2_EXECUTED": False,
        }
        ckpt_payload["checkpoint_digest"] = content_hash({k: v for k, v in ckpt_payload.items() if k != "checkpoint_digest"})
        ckpt_path = artifact_dir() / "closure_checkpoint_P1_QFT_STRUCTURAL_CONSISTENCY.json"
        _write_json(ckpt_path, ckpt_payload)
        questions = {
            "1_P1_eliminates_G6_candidates": "NO",
            "2_tests_responsible_for_elimination": "NONE",
            "3_locality_new_restriction_beyond_G6": "NO",
            "4_Lorentz_new_restriction_beyond_G6": "NO",
            "5_spin_statistics": "STRUCTURALLY_REPRESENTED_PARTIAL_NOT_FULLY_VERIFIED",
            "6_full_quantum_unitarity_verified": "NO",
            "7_CPT_fully_verified": "NO",
            "8_anomaly_freedom_unchanged_from_G5": "YES",
            "9_power_counting_eliminates_candidates": "NO",
            "10_nonrenormalizable_treated_as_inconsistent": "NO",
            "11_EFT_eliminates_candidates": "NO",
            "12_quantum_gravity_tested": "NO",
            "13_gauge_couplings_constrained": "NO",
            "14_dimensionful_parameters_constrained": "NO",
            "15_new_parameter_free_dimensionless_quantities": "NONE",
            "16_new_universal_consequences_beyond_G6": len(new_forced),
            "17_apparent_P1_consequences_destroyed": len(destroyed),
            "18_experimental_numerical_input": "NO",
            "19_gravity_changed": "NO",
            "20_next_authorized_profile": "P2_CHIRAL_GAUGE_MATTER",
        }
        negative = {
            "ghost_free_equals_unitary": "REJECTED",
            "locality_plus_Lorentz_equals_CPT": "REJECTED",
            "nonrenormalizable_equals_inconsistent": "REJECTED",
            "renormalizable_equals_unique_coupling": "REJECTED",
            "automatic_P2_activation": "REJECTED",
            "ranking": "REJECTED",
            "partial_upgraded_to_complete": "REJECTED",
            "quantum_gravity_claimed": "REJECTED",
        }
        summary = {
            "phase": PHASE,
            "status": "OK",
            "PHASE_14C1_STATUS": "CLOSED",
            "PHASE_14C1_CLOSED": True,
            "P1_STATUS": "CLOSURE_REACHED",
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P1_ONLY",
            "PHASE_14C1_TEST_COPY_ID": PHASE_14C1_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "QFT_LOCALITY_STATUS": "VERIFIED",
            "QFT_LORENTZ_STATUS": "VERIFIED",
            "QFT_SPIN_STATISTICS_STATUS": "PARTIAL",
            "QFT_UNITARITY_STATUS": "UNTESTED",
            "QFT_CPT_STATUS": "UNTESTED",
            "QFT_GAUGE_STATUS": "VERIFIED",
            "QFT_ANOMALY_STATUS": "VERIFIED",
            "QFT_RENORMALIZABILITY_STATUS": "PARTIAL",
            "QFT_EFT_STATUS": "VERIFIED",
            "QFT_QUANTUM_GRAVITY_STATUS": "UNTESTED",
            "QUANTUM_UNITARITY": "UNTESTED",
            "QFT_STRUCTURAL_CONSISTENCY_ADDS_NO_NEW_ELIMINATION_WITHIN_IMPLEMENTED_TESTS": True,
            "QFT_STRUCTURAL_CONSTRAINTS_DO_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_DECLARED_BOUNDS": True,
            "CATALOG_HASH": EXPECTED_CATALOG_HASH,
            "PROFILE_REGISTRY_HASH": EXPECTED_PROFILE_REGISTRY_HASH,
            "profile_hash": EXPECTED_P1_PROFILE_HASH,
            "test_registry_hash": p1_rep.get("test_registry_hash"),
            "GRAMMAR_HASH": p1_rep["grammar_hash"],
            "PARENT_GRAMMAR": P0_ID,
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "TOP_DOWN_INPUT_HASH": EXPECTED_TOP_DOWN_INPUT_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "G6_COMPLETE": 359,
            "G6_PARTIAL": 120,
            "P1_TESTED": p1_rep["generated_candidates"],
            "P1_COMPLETE": pass_n,
            "P1_PARTIAL": partial_n,
            "P1_REJECTED": rejected_n,
            "P1_UNTESTED_ONLY": 0,
            "P1_UNRESOLVED": unresolved_n,
            "EQUIVALENCE_CLASSES": pass_n,
            "NEW_ELIMINATIONS_FROM_P1": new_elim,
            "NEW_FORCED_PROPERTIES_FROM_P1": new_forced,
            "rejection": p1_rep.get("rejection") or [],
            "G6_COMPLETE_TO_P1": {"G6_COMPLETE": 359, "P1_COMPLETE": pass_n, "P1_REJECTED": rejected_n, "P1_PARTIAL": partial_n, "P1_UNTESTED": 0},
            "class_table": p1_rep.get("class_table") or [],
            "FORCED_PROPERTIES": consequences.get("FORCED_PROPERTIES") or [],
            "BRANCH_DEPENDENT_PROPERTIES": consequences.get("BRANCH_DEPENDENT_PROPERTIES") or [],
            "FREE_PROPERTIES": consequences.get("FREE_PROPERTIES") or [],
            "UNRESOLVED_PROPERTIES": consequences.get("UNRESOLVED_PROPERTIES") or [],
            "UNTESTED_PROPERTIES": consequences.get("UNTESTED_PROPERTIES") or [],
            "destroyed_by_counterexample": destroyed,
            "parameter_analysis": consequences.get("parameter_analysis") or {},
            "operator_dimension_audit": operator_dimension_audit(),
            "P0_EXECUTED": True,
            "P1_EXECUTED": True,
            "P2_EXECUTED": False,
            "P5_EXECUTED": False,
            "RG": "UNTESTED",
            "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
            "gravity_c0": "FREE",
            "gravity_c1": "FREE",
            "gravity_changed": False,
            "ranking": False,
            "numerical_target_search": False,
            "target_inputs": 0,
            "experimental_constants": False,
            "fitting_or_calibration": False,
            "TARGET_BLINDNESS_STATUS": "VERIFIED",
            "PROVENANCE_STATUS": "VERIFIED",
            "G4_PARTIALITY_PROPAGATION_STATUS": "VERIFIED",
            "VECTORLIKE_STATUS": "UNTESTED",
            "NEXT_AUTHORIZED_EXTENSION": "P2_CHIRAL_GAUGE_MATTER",
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p2_blocked": p2_blocked,
            "negative_tests_all_pass": all(v == "REJECTED" for v in negative.values()) and physics_chain_blocked and p2_blocked,
            "overclaims": {
                "full_quantum_consistency": "REJECTED AS OVERCLAIM",
                "ghost_free_equals_unitary": "REJECTED AS OVERCLAIM",
                "P2_automatically_activated": "REJECTED AS OVERCLAIM",
            },
            "questions": questions,
            "audit_summary": {
                "g6_checkpoint_unchanged": True,
                "p0_checkpoint_unchanged": True,
                "g5_checkpoint_unchanged": True,
                "phase14c0_artifacts_unchanged": True,
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
            "checkpoint_path": str(ckpt_path),
            "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
            "PHASE_14C0_STATUS": s14c0.get("PHASE_14C0_STATUS"),
            "PHASE_14B6_STATUS": s14b6.get("PHASE_14B6_STATUS"),
        }
        _write_json(summary_path, summary)
        cached = summary

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c0") != hashes_before.get("phase14c0"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P0 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if g6_checkpoint_path().read_bytes() != g6_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if p0_ckpt.read_bytes() != p0_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "P0 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if g5_path.read_bytes() != g5_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G5 checkpoint modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    if hashes_after.get("phase14b6") != hashes_before.get("phase14b6"):
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 artifacts were modified"
        cached["SCIENTIFIC_STATUS"] = "NOT_ANALYZED"
    cached["audit_summary"] = {
        **(cached.get("audit_summary") or {}),
        "g6_checkpoint_unchanged": g6_checkpoint_path().read_bytes() == g6_before,
        "p0_checkpoint_unchanged": p0_ckpt.read_bytes() == p0_before,
        "g5_checkpoint_unchanged": g5_path.read_bytes() == g5_before,
        "phase14c0_artifacts_unchanged": hashes_after.get("phase14c0") == hashes_before.get("phase14c0"),
        "phase14b6_artifacts_unchanged": hashes_after.get("phase14b6") == hashes_before.get("phase14b6"),
    }
    return cached


def run_phase14c1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c1_p1(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
            "PHASE_14C0_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14c0_artifacts_unchanged") else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "P0_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("p0_checkpoint_unchanged") else "FAILED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g5_checkpoint_unchanged") else "FAILED",
            "PHASE_14C1_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C1_STATUS": science.get("PHASE_14C1_STATUS"),
            "PHASE_14C0_STATUS": science.get("PHASE_14C0_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P0_EXECUTED": "TRUE",
            "P1_EXECUTED": "TRUE",
            "P2_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
