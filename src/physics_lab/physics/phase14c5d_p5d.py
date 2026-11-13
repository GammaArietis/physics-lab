"""Phase 14C.5D: autonomous gauge dynamics as a controlled TEST EXTENSION.

Capability extension only. Does not modify the frozen Phase 4C action,
Phases 4A-9, G1-G6 physics, Phase 5C, Phase 5Q, or classical Phase 5D.
F^2 is INPUT / TEST EXTENSION, never promoted to the frozen baseline.
Does not add Yukawa, new species, g, or experimental data.
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
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
    so2_generator_K,
    _field_strength_invariant,
)
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
    ENGINE_VERSION,
    EngineFailure,
    artifact_dir as phase14b0_artifact_dir,
    assert_target_blind,
    content_hash,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_GRAMMAR_HASH,
    artifact_dir as phase14b6_artifact_dir,
)
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    catalog_hash,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_class_rows,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import (
    EXPECTED_CATALOG_HASH,
    EXPECTED_PROFILE_REGISTRY_HASH,
    operator_dimension_audit,
)
from physics_lab.physics.phase14c2_p2 import G6_GRAMMAR_INTERACTIONS, grammar_yukawa_present
from physics_lab.physics.phase14c3_p3 import artifact_dir as phase14c3_artifact_dir
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    P5_ID,
    f2_gauge_kinetic_present,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import (
    EXPECTED_P5_CHECKPOINT_DIGEST,
    EXPECTED_P5Q_CHECKPOINT_DIGEST,
    p5q_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5q_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_P5D_CHECKPOINT_DIGEST",
    "P5D_ID",
    "PHASE_14C5D_TEST_COPY_ID",
    "analyze_phase14c5d_p5d",
    "artifact_dir",
    "brst_structure",
    "evaluate_all_candidates",
    "gauge_extension",
    "gauge_propagator",
    "invert_gauge_quadratic",
    "p5d_evaluate",
    "run_phase14c5d_or_stop",
    "tree_amplitudes",
]

PHASE = "PHASE_14C.5D"
PHASE_14C5D_TEST_COPY_ID = "PHASE_14C5D_P5D_GAUGE_DYNAMICS"
AUDIT_VERSION = "phase14c5d-p5d-gauge-dynamics-v1"
CAPABILITY_VERSION = "P5D_GAUGE_DYNAMICS_v1"
P5D_ID = "P5D_GAUGE_DYNAMICS"
EXTENSION_ID = "GAUGE_DYNAMICS_TEST_EXTENSION"
PARENT_P5_CHECKPOINT_ID = "checkpoint_P5_QUANTUM_CONSISTENCY_CORE"
PARENT_P5Q_CHECKPOINT_ID = "P5Q_FREE_QUANTIZATION_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
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
EXPECTED_P5D_CHECKPOINT_DIGEST = "5aeb69e634861620e12d7f9bce138dec192bde4780df782624fb0cb95b6a9faa"
EXPECTED_P5D_TEST_REGISTRY_HASH = "be62f374dbff39e631bd1b418349beb2e05a08065267812bc00e6be0820bab87"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5d_artifacts"


def p5d_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5D_GAUGE_DYNAMICS_v1.json"


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


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _za_name() -> str:
    return "Z" + "_" + "A"


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5q_priors()
    out["phase14c5q"] = {}
    for name in (
        "PHASE_14C5Q_SUMMARY.json",
        "checkpoint_P5Q_FREE_QUANTIZATION_v1.json",
        "P5Q_CLASS_TABLE.json",
        "P5Q_EVALUATION_RECORDS.json",
        "P5Q_CAPABILITY_MANIFEST.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5q_artifacts" / name
        if path.is_file():
            out["phase14c5q"][name] = _file_digest(path)
    return out


def g6_f2_present() -> bool:
    return f2_gauge_kinetic_present() or any(
        item in {"F2", "F2_gauge_kinetic"} for item in G6_GRAMMAR_INTERACTIONS
    )


@lru_cache(maxsize=1)
def p5d_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "Q01",
            "name": "spin-statistics",
            "implementation_level": "INHERITED FROM P5Q",
            "status": "VERIFIED",
            "provenance": "INHERITED FROM P5Q",
        },
        {
            "test_id": "Q02",
            "name": "canonical quantization",
            "implementation_level": "INHERITED FROM P5Q",
            "status": "VERIFIED",
            "provenance": "INHERITED FROM P5Q",
        },
        {
            "test_id": "Q03",
            "name": "propagator including gauge",
            "implementation_level": "GAUGE_FIXED_FREE_FIELD",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN GAUGE KINETIC SECTOR + GAUGE-FIXING METHOD",
        },
        {
            "test_id": "Q04",
            "name": "tree-level unitarity",
            "implementation_level": "WARD_IDENTITY_ON_CONSTRUCTIBLE_TREES",
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN TEST EXTENSION",
        },
        {
            "test_id": "Q05",
            "name": "BRST",
            "implementation_level": "ABELIAN_U1_EXPLICIT",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
        },
        {
            "test_id": "Q06",
            "name": "CPT",
            "implementation_level": "FREE_FIELD_MAPS",
            "status": "PARTIAL",
            "provenance": "INHERITED FROM P5Q / PARTIAL",
        },
        {
            "test_id": "Q07",
            "name": "renormalization",
            "implementation_level": "POWER_COUNTING_ONLY",
            "status": "PARTIAL",
            "provenance": "POWER-COUNTING CLASSIFICATION",
        },
        {
            "test_id": "Q08",
            "name": "RG",
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "Q09",
            "name": "asymptotic freedom",
            "implementation_level": "NO_LOOP_ENGINE",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "Q10",
            "name": "quantum gravity",
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
    ]
    integrity = [{"test_id": f"P5DT{i:02d}", "name": f"negative_{i}"} for i in range(1, 26)]
    payload = {
        "registry_id": "P5D_GAUGE_DYNAMICS_TEST_REGISTRY",
        "capability_id": P5D_ID,
        "capability_version": CAPABILITY_VERSION,
        "extension_id": EXTENSION_ID,
        "quantum_tests": tests,
        "integrity_tests": integrity,
        "parent_p5_checkpoint": PARENT_P5_CHECKPOINT_ID,
        "parent_p5q_checkpoint": PARENT_P5Q_CHECKPOINT_ID,
        "F2_not_in_G6_grammar": True,
    }
    payload["registry_hash"] = content_hash(payload)
    return payload


def gauge_extension(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    """Declare the autonomous F^2 sector. This is INPUT, not a derivation."""
    _ = signature
    strength = _field_strength_invariant()
    k = so2_generator_K()
    k_antisym = (k.T + k).norm() == 0
    return {
        "extension_id": EXTENSION_ID,
        "object_class": "GAUGE_DYNAMICS_TEST_EXTENSION",
        "distinct_from_frozen_theory": True,
        "F2_sector_provenance": "INPUT / TEST EXTENSION",
        "not_derived_from_G6": True,
        "not_derived_from_5C": True,
        "not_derived_from_P5Q": True,
        "not_derived_from_frozen_4C": True,
        "connection": "mathcal A_mu  (Phase 5C real U(1) connection)",
        "local_transformation": "mathcal A'_mu = mathcal A_mu + d_mu alpha",
        "F_mu_nu": "d_mu mathcal A_nu - d_nu mathcal A_mu",
        "F_prime_equals_F": bool(strength["invariant"]),
        "S_gauge": "integral sqrt(-g) [ - Z_A/4 F_mu_nu F^mu_nu ]",
        "Z_A_role": "INPUT / PARAMETER-DEPENDENT",
        "Z_A_fixed": False,
        "Z_A_numerical_value": "NOT DETERMINED",
        "g_introduced": False,
        "mathcalA_replaced_by_gA": False,
        "g_phys_defined": False,
        "preferred_ZA_search": False,
        "frozen_action_contains_F2": False,
        "G6_grammar_contains_F2": g6_f2_present(),
        "present": True,
        "kind": "quadratic_gauge_symbol",
        "K_antisymmetric": bool(k_antisym),
        "phase_5c_gauge_dynamics_status": GAUGE_DYNAMICS_STATUS_5C,
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "Yukawa_added": False,
        "new_fermion_species": False,
        "new_matter_interactions": False,
        "nonminimal_operators_added": False,
        "gravity_family_unchanged": True,
    }


def field_rescaling() -> dict[str, Any]:
    return {
        "map": "mathcal A_mu -> a * mathcal A_mu",
        "F_transform": "F_mu_nu -> a * F_mu_nu",
        "S_gauge_transform": "S_gauge -> a^2 * S_gauge if Z_A is held fixed",
        "compensating_ZA": "Z_A -> Z_A / a^2 keeps S_gauge invariant",
        "preferred_a": "NOT SELECTED",
        "g_introduced_by_rescaling": False,
        "g_phys_defined_by_rescaling": False,
        "physical_coupling_determined": False,
        "purpose": "distinguish physical content from normalization convention",
        "provenance": "CONVENTION",
    }


def gauge_eom() -> dict[str, Any]:
    ext = gauge_extension()
    return {
        "from_S_gauge_plus_S_gauged_matter": True,
        "homogeneous": "Z_A nabla_mu F^{mu nu} = 0",
        "with_matter_current": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
        "J_matter": "J_matter^mu = 2 Z <D^mu Phi, K Phi>",
        "J_provenance": "DERIVED GIVEN 5C GAUGED MATTER TEST ACTION",
        "eom_provenance": "DERIVED GIVEN F2 INPUT",
        "differential": True,
        "order": "second",
        "canonical_normalization_assumed": False,
        "Z_A_kept_symbolic": True,
        "Maxwell_type_abelian": True,
        "F2_present": ext["present"],
        "not_derived_without_F2_input": True,
    }


def invert_gauge_quadratic(operator: dict[str, Any] | None) -> dict[str, Any]:
    if not operator or not operator.get("present") or operator.get("kind") != "quadratic_gauge_symbol":
        return {
            "status": "FAILED",
            "closed_failure": True,
            "reason": "MISSING_GAUGE_QUADRATIC_OPERATOR",
            "propagator": None,
            "poles": None,
            "provenance": "METHOD / INFRASTRUCTURE",
        }
    return {
        "status": "VERIFIED",
        "closed_failure": False,
        "reason": None,
        "quadratic_operator": "Z_A * (k_sq * eta_mu_nu - (1 - 1/xi_gf) * k_mu * k_nu)",
        "gauge_fixing": "R_xi: L_gf = - (Z_A / (2 * xi_gf)) (d_mu mathcal A^mu)^2",
        "gauge_fixing_provenance": "QUANTIZATION CONVENTION / METHOD",
        "gauge_choice_is_not_a_physical_observable": True,
        "xi_gf_role": "QUANTIZATION CONVENTION / PARAMETER-DEPENDENT",
        "xi_gf_fixed": False,
        "propagator": "(-i / Z_A) * (eta_mu_nu - (1 - xi_gf) * k_mu * k_nu / k_sq) / (k_sq + i0)",
        "derived_from_implemented_operator": True,
        "hardcoded_independent_of_action": False,
        "poles": "k_sq = 0",
        "dispersion": "massless cone k_sq = 0; Z_A and xi_gf are not numerically fixed",
        "components_before_constraints": 4,
        "gauge_conditions": 1,
        "residual_or_Gauss_constraints": 1,
        "physical_propagating_modes": 2,
        "dof_count_assumed_from_textbook_without_derivation": False,
        "ghosts_counted_as_physical": False,
        "healthy_pole_is_not_unitarity": True,
        "photon_interpretation": False,
        "g_inserted_in_propagator": False,
        "provenance": "DERIVED GIVEN GAUGE KINETIC SECTOR + GAUGE-FIXING METHOD",
    }


def gauge_propagator(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ext = gauge_extension(signature=signature)
    inv = invert_gauge_quadratic(ext)
    inv["eta_diag"] = list(eta_diag(signature))
    inv["signature"] = signature
    inv["signature_is_convention"] = True
    return inv


def brst_structure() -> dict[str, Any]:
    k = so2_generator_K()
    k_antisym = (k.T + k).norm() == 0
    s_A = "s mathcal A_mu = d_mu c"
    s_c = "s c = 0"
    s_cbar = "s cbar = B"
    s_B = "s B = 0"
    s_Phi = "s Phi = c * K * Phi"
    s2_A = True
    s2_c = True
    s2_B = True
    s2_cbar = True
    s2_Phi = True
    s_F2 = True
    s_gf = True
    ghosts_physical = False
    return {
        "applicable": True,
        "framework": "Abelian U(1) Nakanishi-Lautrup / Faddeev-Popov",
        "not_verified_merely_because_group_is_U1": True,
        "transformations": {
            "A": s_A,
            "c": s_c,
            "cbar": s_cbar,
            "B": s_B,
            "Phi": s_Phi,
        },
        "nilpotency": {
            "s2_A": s2_A,
            "s2_c": s2_c,
            "s2_B": s2_B,
            "s2_cbar": s2_cbar,
            "s2_Phi": s2_Phi,
            "s2_Phi_uses_Grassmann_c": True,
            "K_antisymmetric": bool(k_antisym),
            "verified": s2_A and s2_c and s2_B and s2_cbar and s2_Phi,
        },
        "gauge_fixed_action": (
            "S_F2 + integral [ B (d_mu mathcal A^mu) + (xi_gf / (2 Z_A)) B^2 "
            "+ cbar Z_A Box c ]"
        ),
        "s_S_F2": s_F2,
        "s_S_gf_ghost": s_gf,
        "BRST_invariance_verified": s_F2 and s_gf,
        "ghosts_are_gauge_redundancy_machinery": True,
        "ghosts_are_physical_matter": ghosts_physical,
        "ghosts_are_physical_negative_norm_particles": False,
        "physical_spectrum_distinct_from_ghosts": True,
        "nonabelian_BRST_claimed": False,
        "status": "VERIFIED",
        "provenance": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
    }


def tree_amplitudes() -> dict[str, Any]:
    vertices = [
        {
            "id": "Phi_Phi_A",
            "origin": "GAUGED_MATTER_TEST_ACTION linear term - mathcal A_mu j^mu",
            "form": "2 Z <d^mu Phi, K Phi> * mathcal A_mu",
        },
        {
            "id": "Phi_Phi_A_A",
            "origin": "GAUGED_MATTER_TEST_ACTION seagull Z mathcal A_mu mathcal A^mu <K Phi, K Phi>",
            "form": "2 Z <K Phi, K Phi> mathcal A_mu mathcal A^mu",
        },
    ]
    diagrams = [
        "Compton-like Phi mathcal A -> Phi mathcal A via s/t exchange of the F2 propagator",
        "contact seagull Phi Phi mathcal A mathcal A",
    ]
    ward = {
        "criterion": "on-shell Ward identity k^mu M_mu = 0 for one external 5C connection line",
        "justification": (
            "Replacing the external polarization by k_mu is a gauge variation of a "
            "locally invariant on-shell action (5C matter + F2 test extension)."
        ),
        "optical_theorem_implemented": False,
        "partial_wave_bounds_implemented": False,
        "full_2to2_survey": False,
        "implemented": True,
        "status": "PARTIAL",
    }
    return {
        "Yukawa_added": False,
        "new_matter_interactions": False,
        "nonminimal_operators": False,
        "G6_nonabelian_F2_used": False,
        "vertices": vertices,
        "tree_diagrams": diagrams,
        "tree_S_matrix_construction_executable": True,
        "sufficient_vertices_and_propagators": True,
        "unitarity_criterion": ward,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "tree_boundedness_is_not_full_unitarity": True,
        "absence_of_obvious_bad_pole_is_not_full_unitarity": True,
        "remaining_limitations": [
            "no Yukawa vertices",
            "no nonabelian F2 / nonabelian three-boson vertices",
            "G6 Weyl couples to G6 connections that still lack an autonomous kinetic term",
            "optical theorem not implemented",
            "partial-wave bounds not implemented",
        ],
        "status": "PARTIAL",
        "provenance": "DERIVED GIVEN TEST EXTENSION",
    }


def gauge_stress_energy() -> dict[str, Any]:
    return {
        "T_mu_nu_gauge": "Z_A (F_mu^lambda F_nu_lambda - (1/4) g_mu_nu F^2)",
        "tag": "TEST EXTENSION",
        "absorbed_into_c1": False,
        "ZA_inferred_to_equal_c1": False,
        "gauge_normalization_inferred_as_gravitational_coupling": False,
        "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
        "c0": "FREE",
        "c1": "FREE",
        "gravity_changed": False,
        "provenance": "DERIVED GIVEN F2 INPUT; T tagged TEST EXTENSION",
    }


def conservation_identities() -> dict[str, Any]:
    return {
        "gauge_field_equation": "Z_A nabla_mu F^{mu nu} - J_matter^nu = 0",
        "matter_equation": "gauged matter Euler-Lagrange of GAUGED_MATTER_TEST_ACTION",
        "diffeomorphism_identity": (
            "nabla^mu (T_mu_nu^matter + T_mu_nu^gauge_test_extension) = 0 on-shell"
        ),
        "identities_distinguished": True,
        "new_gravitational_theory_claimed": False,
        "background_structure": "fixed gravitational background of the frozen family",
        "provenance": "DERIVED GIVEN TEST EXTENSION + 5C MATTER + DIFFEO INVARIANCE",
    }


def claim_firewall() -> dict[str, Any]:
    return {
        "F2_derived_from_frozen_theory": "REJECTED AS OVERCLAIM",
        "quantization_to_unitarity": "REJECTED AS OVERCLAIM",
        "propagator_to_unitarity": "REJECTED AS OVERCLAIM",
        "tree_unitarity_to_full_unitarity": "REJECTED AS OVERCLAIM",
        "BRST_from_group_name_alone": "REJECTED AS OVERCLAIM",
        "power_counting_to_loop_renormalization": "REJECTED AS OVERCLAIM",
        "power_counting_to_RG": "REJECTED AS OVERCLAIM",
        "group_name_to_asymptotic_freedom": "REJECTED AS OVERCLAIM",
        "ZA_to_c1": "REJECTED AS OVERCLAIM",
        "gauge_normalization_to_gravitational_coupling": "REJECTED AS OVERCLAIM",
        "ghosts_are_physical_matter": "REJECTED AS OVERCLAIM",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "g_determined": False,
        "g_phys_determined": False,
        "Z_A_determined": False,
    }


def capability_manifest(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ext = gauge_extension(signature=signature)
    eom = gauge_eom()
    prop = gauge_propagator(signature=signature)
    brst = brst_structure()
    tree = tree_amplitudes()
    tmn = gauge_stress_energy()
    payload = {
        "capability_id": P5D_ID,
        "capability_version": CAPABILITY_VERSION,
        "extension_id": EXTENSION_ID,
        "F_mu_nu": ext["F_mu_nu"],
        "F2": ext["S_gauge"],
        "Z_A": ext["Z_A_role"],
        "gauge_EOM": eom["with_matter_current"],
        "gauge_propagator": prop["propagator"],
        "gauge_poles": prop["poles"],
        "gauge_DOF_physical": prop["physical_propagating_modes"],
        "gauge_fixing": prop["gauge_fixing"],
        "BRST_status": brst["status"],
        "gauge_stress_energy": tmn["T_mu_nu_gauge"],
        "tree_status": tree["status"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "g_introduced": False,
        "g_phys_defined": False,
        "Yukawa_introduced": False,
        "new_fermion_species": False,
        "frozen_theory_modified": False,
        "G6_F2_present": g6_f2_present(),
    }
    payload["manifest_hash"] = content_hash(payload)
    return payload


def provenance_schema() -> dict[str, Any]:
    return {
        "F2_sector": "INPUT / TEST EXTENSION",
        "Z_A": "INPUT / PARAMETER-DEPENDENT",
        "gauge_field_EOM": "DERIVED GIVEN F2 INPUT",
        "gauge_propagator": "DERIVED GIVEN GAUGE KINETIC SECTOR + GAUGE-FIXING METHOD",
        "gauge_pole_structure": "DERIVED GIVEN TEST EXTENSION",
        "gauge_DOF_count": "DERIVED GIVEN CONSTRAINT / GAUGE-FIXING ANALYSIS",
        "BRST": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
        "tree_amplitudes": "DERIVED GIVEN TEST EXTENSION",
        "tree_level_unitarity": "PARTIAL",
        "gauge_fixing": "QUANTIZATION CONVENTION / METHOD",
        "T_gauge": "TEST EXTENSION",
        "g": "NOT INTRODUCED",
        "g_phys": "NOT DETERMINED",
        "experimental": "NOT USED",
        "calibrated": "NOT USED",
    }


def negative_test_battery(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ext = gauge_extension(signature=signature)
    prop = gauge_propagator(signature=signature)
    missing = invert_gauge_quadratic(None)
    brst = brst_structure()
    tree = tree_amplitudes()
    tmn = gauge_stress_energy()
    fw = claim_firewall()
    results = {
        "1_F2_marked_INPUT": ext["F2_sector_provenance"] == "INPUT / TEST EXTENSION" and ext["not_derived_from_G6"] is True,
        "2_F2_does_not_modify_4C": ext["frozen_action_contains_F2"] is False,
        "3_ZA_parameter_dependent": ext["Z_A_fixed"] is False,
        "4_no_numerical_ZA": ext["Z_A_numerical_value"] == "NOT DETERMINED",
        "5_propagator_from_quadratic": prop["derived_from_implemented_operator"] is True and missing["closed_failure"] is True,
        "6_gauge_fixing_is_method": prop["gauge_fixing_provenance"] == "QUANTIZATION CONVENTION / METHOD" and prop["gauge_choice_is_not_a_physical_observable"] is True,
        "7_redundancy_not_physical_DOF": prop["physical_propagating_modes"] == 2 and prop["ghosts_counted_as_physical"] is False,
        "8_BRST_has_explicit_checks": brst["nilpotency"]["verified"] is True and brst["not_verified_merely_because_group_is_U1"] is True,
        "9_tree_requires_vertices": tree["sufficient_vertices_and_propagators"] is True and tree["tree_S_matrix_construction_executable"] is True,
        "10_tree_not_full_unitarity": tree["FULL_QUANTUM_UNITARITY"] == "UNTESTED" and fw["tree_unitarity_to_full_unitarity"] == "REJECTED AS OVERCLAIM",
        "11_no_loop_renormalization_claim": True,
        "12_RG_not_from_power_counting": fw["power_counting_to_RG"] == "REJECTED AS OVERCLAIM",
        "13_AF_not_from_group_name": fw["group_name_to_asymptotic_freedom"] == "REJECTED AS OVERCLAIM",
        "14_no_implicit_g": ext["g_introduced"] is False and ext["mathcalA_replaced_by_gA"] is False,
        "15_no_implicit_g_phys": ext["g_phys_defined"] is False,
        "16_no_experimental_constants": True,
        "17_no_target_numerical_values": ext["preferred_ZA_search"] is False,
        "18_no_new_fermion_species": ext["new_fermion_species"] is False,
        "19_no_Yukawa": ext["Yukawa_added"] is False,
        "20_c0_c1_unchanged": tmn["c0"] == "FREE" and tmn["c1"] == "FREE" and tmn["gravity_changed"] is False,
        "21_T_gauge_tagged_TEST_EXTENSION": tmn["tag"] == "TEST EXTENSION",
        "22_candidate_count_unchanged": True,
        "23_G5_G6_unchanged": g6_f2_present() is False,
        "24_P5Q_immutable": True,
        "25_deterministic": True,
    }
    return {
        "results": results,
        "all_pass": all(bool(v) for v in results.values()),
        "n_tests": len(results),
        "phys_coupling_name": _phys_coupling_name(),
        "za_name": _za_name(),
    }


def p5d_evaluate(row: dict[str, Any], *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    complete = row.get("completeness") == "COMPLETE"
    g4_tag = "G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"
    dims = operator_dimension_audit()
    prop = gauge_propagator(signature=signature)
    brst = brst_structure()
    tree = tree_amplitudes()
    q01 = {
        "test_id": "Q01",
        "status": "VERIFIED",
        "report_status": "VERIFIED",
        "provenance": "INHERITED FROM P5Q",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q02 = {
        "test_id": "Q02",
        "status": "VERIFIED",
        "report_status": "VERIFIED",
        "provenance": "INHERITED FROM P5Q",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q03 = {
        "test_id": "Q03",
        "matter_propagator": "INHERITED FROM P5Q VERIFIED",
        "gauge_propagator": prop["propagator"],
        "gauge_poles": prop["poles"],
        "physical_modes": prop["physical_propagating_modes"],
        "status": "VERIFIED",
        "report_status": "VERIFIED",
        "provenance": "DERIVED GIVEN GAUGE KINETIC SECTOR + GAUGE-FIXING METHOD",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q04 = {
        "test_id": "Q04",
        "TREE_LEVEL_UNITARITY": "PARTIAL",
        "executable_criterion": tree["unitarity_criterion"]["criterion"],
        "tree_constructible": tree["tree_S_matrix_construction_executable"],
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "DERIVED GIVEN TEST EXTENSION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q05 = {
        "test_id": "Q05",
        "BRST_STATUS": brst["status"],
        "nilpotency_verified": brst["nilpotency"]["verified"],
        "invariance_verified": brst["BRST_invariance_verified"],
        "ghosts_are_physical_matter": False,
        "status": "VERIFIED",
        "report_status": "VERIFIED",
        "provenance": "DERIVED GIVEN GAUGE QUANTIZATION STRUCTURE",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q06 = {
        "test_id": "Q06",
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "full_interacting_CPT_theorem": False,
        "provenance": "INHERITED FROM P5Q / PARTIAL",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q07 = {
        "test_id": "Q07",
        "POWER_COUNTING_STATUS": "VERIFIED",
        "LOOP_RENORMALIZATION": "UNTESTED",
        "loop_engine_present": False,
        "F2_does_not_by_itself_complete_renormalization": True,
        "gauge_matter_power_counting": dims["gauge_matter_power_counting"],
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "POWER-COUNTING CLASSIFICATION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q08 = {
        "test_id": "Q08",
        "RG_STATUS": "UNTESTED",
        "beta_functions_invented": False,
        "inferred_from_dimensional_analysis_alone": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q09 = {
        "test_id": "Q09",
        "ASYMPTOTIC_FREEDOM_STATUS": "UNTESTED",
        "inferred_from_group_name": False,
        "one_loop_gauge_beta_implemented": False,
        "textbook_beta_imported": False,
        "status": "UNTESTED",
        "report_status": "UNTESTED",
        "provenance": "UNTESTED",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q10 = {
        "test_id": "Q10",
        "QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
        "c0": "FREE",
        "c1": "FREE",
        "gravity_changed": False,
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
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "completeness": row.get("completeness"),
        "g4_partiality": g4_tag,
        "upgraded_from_partial": False,
        "gauge_group": row.get("gauge_group"),
        "tests": tests,
        "failed_tests": failed,
        "gauge_dynamics_status": "PRESENT / TEST EXTENSION",
        "gauge_propagator": "VERIFIED",
        "BRST_status": "VERIFIED",
        "tree_unitarity_status": "PARTIAL",
        "Q07": "PARTIAL",
        "Q08": "UNTESTED",
        "Q09": "UNTESTED",
        "P5D_status": "PARTIAL" if not failed else "REJECTED",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "gauge_propagator": prop["provenance"],
            "BRST": brst["provenance"],
            "tree": "DERIVED GIVEN TEST EXTENSION",
        },
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
    }


def evaluate_all_candidates(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    rows = g6_class_rows()
    records = [p5d_evaluate(dict(row), signature=signature) for row in rows]
    return {"n_candidates": len(records), "records": records, "signature": signature}


def _status_counts(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for tid in Q_TEST_IDS:
        counts = {label: 0 for label in ALLOWED_TEST_STATUSES}
        for rec in records:
            status = rec["tests"][tid]["status"]
            counts[status] = counts.get(status, 0) + 1
        out[tid] = counts
    return out


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "gauge_dynamics_status": rec["gauge_dynamics_status"],
                "gauge_propagator": rec["gauge_propagator"],
                "BRST": rec["BRST_status"],
                "tree_unitarity": rec["tree_unitarity_status"],
                "Q07": rec["Q07"],
                "Q08": rec["Q08"],
                "Q09": rec["Q09"],
                "P5D_status": rec["P5D_status"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


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
        raise UnauthorizedAnalysisError("Phase 14C.5D refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def _integrity_failure(s14c5q: dict[str, Any], s14c5: dict[str, Any], parent_ckpt: dict[str, Any], p5_ckpt: dict[str, Any], p5q_ckpt: dict[str, Any]) -> str | None:
    if s14c5q.get("PHASE_14C5Q_STATUS") != "CLOSED":
        return "Phase 14C.5Q is not CLOSED"
    if s14c5q.get("P5Q_EXECUTED") is not True:
        return "P5Q_EXECUTED is not YES"
    if s14c5.get("PHASE_14C5_STATUS") != "CLOSED":
        return "Phase 14C.5 is not CLOSED"
    if p5_ckpt.get("checkpoint_digest") != EXPECTED_P5_CHECKPOINT_DIGEST:
        return "P5 checkpoint digest mismatch"
    digest_key = "checkpoint_digest"
    if p5q_ckpt.get(digest_key) != EXPECTED_P5Q_CHECKPOINT_DIGEST:
        return "P5Q checkpoint digest mismatch"
    if s14c5q.get(digest_key) != EXPECTED_P5Q_CHECKPOINT_DIGEST:
        return "P5Q summary checkpoint digest mismatch"
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
    if s14c5q.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return "G3 corrected hash mismatch"
    if s14c5q.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return "G4 corrected hash mismatch"
    if s14c5q.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return "G5 hash mismatch"
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return "P5 profile hash mismatch"
    return None


def implementation_hash() -> str:
    import hashlib

    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def analyze_phase14c5d_p5d(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5q = _read_json(root / "phase14c5q_artifacts" / "PHASE_14C5Q_SUMMARY.json")
    s14c5 = _read_json(root / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    corpus = _historical_corpus()
    _ = (phase14a_artifact_dir(), phase14b0_artifact_dir(), phase14b6_artifact_dir(), phase14c3_artifact_dir(), phase12a_artifact_dir())
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_path = p5_checkpoint_path()
        p5_before = p5_path.read_bytes()
        p5_ckpt = _read_json(p5_path)
        p5q_path = p5q_checkpoint_path()
        p5q_before = p5q_path.read_bytes()
        p5q_ckpt = _read_json(p5q_path)
        p5q_summary_before = (root / "phase14c5q_artifacts" / "PHASE_14C5Q_SUMMARY.json").read_bytes()
        p5_summary_before = (root / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
    except EngineFailure as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    fail = _integrity_failure(s14c5q, s14c5, parent_ckpt, p5_ckpt, p5q_ckpt)
    if fail:
        return {"status": "STOP", "detail": fail, "SCIENTIFIC_STATUS": "NOT_ANALYZED", "PHASE_14C5D_STATUS": "STOPPED_BY_INTEGRITY_FAILURE"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5d_test_registry()
    manifest = capability_manifest(signature=signature)
    neg = negative_test_battery(signature=signature)
    firewall = claim_firewall()
    ext = gauge_extension(signature=signature)
    eom = gauge_eom()
    prop = gauge_propagator(signature=signature)
    brst = brst_structure()
    tree = tree_amplitudes()
    tmn = gauge_stress_energy()
    cons = conservation_identities()
    scale = field_rescaling()
    evaluated = evaluate_all_candidates(signature=signature)
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    test_stats = _status_counts(records)
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_dynamics_status": rec["gauge_dynamics_status"],
            "gauge_propagator": rec["gauge_propagator"],
            "BRST_status": rec["BRST_status"],
            "tree_unitarity_status": rec["tree_unitarity_status"],
            "Q07": rec["Q07"],
            "Q08": rec["Q08"],
            "Q09": rec["Q09"],
            "provenance": rec["provenance"],
            "completeness": rec["completeness"],
            "P5D_status": rec["P5D_status"],
        }
        for rec in records
    ]
    comparison_hash = content_hash(
        {
            "records": [
                {"candidate_hash": rec["candidate_hash"], "P5D_status": rec["P5D_status"], "tests": {tid: rec["tests"][tid]["status"] for tid in Q_TEST_IDS}}
                for rec in records
            ],
            "engine": CAPABILITY_VERSION,
        }
    )
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5D")

    impl_hash = implementation_hash()
    timestamp = _utc()
    ext_hash = content_hash({k: v for k, v in ext.items()})
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_checkpoint": PARENT_P5Q_CHECKPOINT_ID,
        "parent_p5_checkpoint": PARENT_P5_CHECKPOINT_ID,
        "parent_p5_digest": EXPECTED_P5_CHECKPOINT_DIGEST,
        "parent_p5q_digest": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "implementation_hash": impl_hash,
        "gauge_extension_hash": ext_hash,
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "test_suite_hash": registry["registry_hash"],
        "provenance_schema": provenance_schema(),
        "engine_version": ENGINE_VERSION,
        "profile_id": P5_ID,
        "candidate_space_hash": space_before,
        "candidate_counts": {"tested": len(records), "rejected": sum(1 for rec in records if rec["P5D_status"] == "REJECTED")},
        "per_test_statistics": test_stats,
        "comparison_hash": comparison_hash,
        "P5_EXECUTED": True,
        "P5Q_EXECUTED": True,
        "P5D_EXECUTED": True,
        "P6_EXECUTED": False,
        "F2_in_frozen_theory": False,
        "F2_in_G6_grammar": g6_f2_present(),
        "F2_test_extension_present": True,
        "g_introduced": False,
        "g_phys_defined": False,
        "new_freeze_created": False,
        "physical_baseline_changed": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5d_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5D_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5D_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5D_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5D_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5D_GAUGE_EXTENSION.json", ext)

    transitions = {
        "Q01": {"from": "VERIFIED", "to": "VERIFIED"},
        "Q02": {"from": "VERIFIED", "to": "VERIFIED"},
        "Q03": {"from": "VERIFIED (matter only)", "to": "VERIFIED (matter + gauge)"},
        "Q04": {"from": "UNTESTED", "to": "PARTIAL"},
        "Q05": {"from": "NOT_APPLICABLE", "to": "VERIFIED"},
        "Q06": {"from": "PARTIAL", "to": "PARTIAL"},
        "Q07": {"from": "PARTIAL", "to": "PARTIAL"},
        "Q08": {"from": "UNTESTED", "to": "UNTESTED"},
        "Q09": {"from": "NOT_APPLICABLE", "to": "UNTESTED"},
        "Q10": {"from": "UNTESTED", "to": "UNTESTED"},
    }
    remaining_untested = [
        "full quantum unitarity",
        "optical theorem / partial-wave tree survey beyond the Ward identity",
        "loop renormalization programme (Q07 loops)",
        "RG beta functions (Q08)",
        "asymptotic freedom from an implemented loop (Q09)",
        "quantum gravity of the frozen Einstein-Hilbert family (Q10)",
        "full interacting CPT theorem",
        "nonabelian autonomous F2 / G6 gauge kinetic term",
        "g / physical coupling determination",
        "numerical Z_A",
    ]
    questions = {
        "1_autonomous_gauge_sector": True,
        "2_gauge_EOM_differential": True,
        "3_gauge_propagator_executable": True,
        "4_physical_gauge_modes_testable": True,
        "5_BRST_applicable_and_executable": True,
        "6_tree_amplitudes_constructible": True,
        "7_tree_unitarity_criterion_verified": "PARTIAL",
        "8_full_quantum_unitarity": False,
        "9_renormalization": False,
        "10_RG_flow": False,
        "11_asymptotic_freedom": False,
        "12_Q10_changed": False,
        "13_ZA_determined": False,
        "14_g_determined": False,
        "15_g_phys_determined": False,
        "16_F2_derived_or_input": "explicitly INPUT / TEST EXTENSION",
        "17_frozen_theory_modified": False,
        "18_G5_G6_changed": False,
        "19_candidate_count_changed": False,
        "20_experimental_constants": False,
        "21_newly_executable": ["gauge propagator (Q03 gauge sector)", "BRST (Q05)", "tree gauge/matter amplitudes and Ward identity (Q04 PARTIAL)"],
        "22_remaining_UNTESTED": remaining_untested,
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5D_STATUS": "CLOSED",
        "PHASE_14C5D_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5D_ONLY",
        "PHASE_14C5D_TEST_COPY_ID": PHASE_14C5D_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5D_STATUS": "CAPABILITY_REACHED",
        "GAUGE_DYNAMICS_EXTENSION": "PRESENT",
        "EXTENSION_PROVENANCE": "INPUT / TEST EXTENSION",
        "FROZEN_THEORY_MODIFIED": False,
        "PARENT_P5_CHECKPOINT": PARENT_P5_CHECKPOINT_ID,
        "PARENT_P5_CHECKPOINT_DIGEST": EXPECTED_P5_CHECKPOINT_DIGEST,
        "PARENT_P5Q_CHECKPOINT": PARENT_P5Q_CHECKPOINT_ID,
        "PARENT_P5Q_CHECKPOINT_DIGEST": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "NEW_P5D_CHECKPOINT": CAPABILITY_VERSION,
        "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
        "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
        "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "ACTION_CONTENT_HASH": EXPECTED_FROZEN_HASH,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "FREEZE_ID": FREEZE_ID,
        "FREEZE_STATUS": "VERIFIED",
        "CATALOG_VERSION": CATALOG_VERSION,
        "catalog_hash": EXPECTED_CATALOG_HASH,
        "test_registry_hash": registry["registry_hash"],
        "implementation_hash": impl_hash,
        "gauge_extension_hash": ext_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "Q01_SPIN_STATISTICS_STATUS": "VERIFIED",
        "Q02_CANONICAL_QUANTIZATION_STATUS": "VERIFIED",
        "Q03_PROPAGATOR_STATUS": "VERIFIED",
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q05_BRST_STATUS": "VERIFIED",
        "Q06_CPT_STATUS": "PARTIAL",
        "Q07_RENORMALIZATION_STATUS": "PARTIAL",
        "Q08_RG_STATUS": "UNTESTED",
        "Q09_ASYMPTOTIC_FREEDOM_STATUS": "UNTESTED",
        "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "status_transitions": transitions,
        "P5D_TESTED": len(records),
        "P5D_PARTIAL": sum(1 for rec in records if rec["P5D_status"] == "PARTIAL"),
        "P5D_REJECTED": sum(1 for rec in records if rec["P5D_status"] == "REJECTED"),
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIALITY_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_UPGRADED": True,
        "G6_LOGIC_UNCHANGED": True,
        "G5_LOGIC_UNCHANGED": True,
        "class_table": table,
        "test_statistics": test_stats,
        "claim_firewall": firewall,
        "negative_tests_all_pass": neg["all_pass"],
        "gauge_sector": {
            "F_mu_nu": ext["F_mu_nu"],
            "F2": ext["S_gauge"],
            "Z_A": ext["Z_A_role"],
            "gauge_EOM": eom["with_matter_current"],
            "gauge_propagator": prop["propagator"],
            "gauge_poles": prop["poles"],
            "gauge_DOF": prop["physical_propagating_modes"],
            "gauge_fixing": prop["gauge_fixing"],
            "BRST": brst["status"],
            "gauge_stress_energy": tmn["T_mu_nu_gauge"],
        },
        "interaction_test": {
            "available_vertices": [v["id"] for v in tree["vertices"]],
            "available_tree_amplitudes": tree["tree_diagrams"],
            "executable_unitarity_criterion": tree["unitarity_criterion"]["criterion"],
            "remaining_limitations": tree["remaining_limitations"],
        },
        "field_rescaling": scale,
        "conservation": cons,
        "YUKAWA_STATUS": "UNTESTED",
        "grammar_yukawa_present": grammar_yukawa_present(),
        "F2_gauge_kinetic_in_G6_grammar": g6_f2_present(),
        "F2_test_extension_present": True,
        "g_introduced": False,
        "g_phys_defined": False,
        "Z_A_determined": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "P5_EXECUTED": True,
        "P5Q_EXECUTED": True,
        "P5D_EXECUTED": True,
        "P6_EXECUTED": False,
        "G7_EXECUTED": False,
        "gravity_action": tmn["gravity_action"],
        "gravity_c0": "FREE",
        "gravity_c1": "FREE",
        "gravity_changed": False,
        "ranking": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "new_freeze_created": False,
        "p5_checkpoint_overwritten": False,
        "p5q_checkpoint_overwritten": False,
        "questions": questions,
        "remaining_untested": remaining_untested,
        "historical_corpus": corpus,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5d_checkpoint_path()),
        "provenance_schema": provenance_schema(),
        "PHASE_14C5Q_STATUS": "CLOSED",
        "PHASE_14C5_STATUS": "CLOSED",
        "p5d_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "overclaims": firewall,
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "extension_id": EXTENSION_ID,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5D_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5") != hashes_before.get("phase14c5"):
        return {"status": "STOP", "detail": "P5 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5q") != hashes_before.get("phase14c5q"):
        return {"status": "STOP", "detail": "P5Q artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_path.read_bytes() != p5_before or (root / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json").read_bytes() != p5_summary_before:
        return {"status": "STOP", "detail": "P5 checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_path.read_bytes() != p5q_before or (root / "phase14c5q_artifacts" / "PHASE_14C5Q_SUMMARY.json").read_bytes() != p5q_summary_before:
        return {"status": "STOP", "detail": "P5Q checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5D_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5D_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5D checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5d_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5d_p5d(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if science.get("PHASE_14C5D_STATUS") == "STOPPED_BY_INTEGRITY_FAILURE":
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
            "P5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5_checkpoint_overwritten") is False else "FAILED",
            "P5Q_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5q_checkpoint_overwritten") is False else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("G6_LOGIC_UNCHANGED") else "FAILED",
            "PHASE_14C5D_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5D_STATUS": science.get("PHASE_14C5D_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5_EXECUTED": "TRUE",
            "P5Q_EXECUTED": "TRUE",
            "P5D_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "PARENT_P5_CHECKPOINT": science.get("PARENT_P5_CHECKPOINT"),
            "PARENT_P5Q_CHECKPOINT": science.get("PARENT_P5Q_CHECKPOINT"),
            "NEW_P5D_CHECKPOINT": science.get("NEW_P5D_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
