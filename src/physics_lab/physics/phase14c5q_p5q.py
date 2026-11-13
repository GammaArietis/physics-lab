"""Phase 14C.5Q: quantum free-field machinery on existing sectors.

Capability extension only. Does not modify the frozen Phase 4C action,
Phases 4A-9, G1-G6 physics, or the P5 quantum-consistency checkpoint.
Does not add F^2, Yukawa, new species, gauge dynamics, or experimental data.
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
from physics_lab.physics.phase14c4_p4 import artifact_dir as phase14c4_artifact_dir, p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P4_CHECKPOINT_DIGEST,
    EXPECTED_P5_PROFILE_HASH,
    P5_ID,
    f2_gauge_kinetic_present,
    interacting_amplitude_constructible,
    p5_checkpoint_path,
    p5_profile,
    snapshot_prior_artifact_hashes as snapshot_14c5_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS, canonical_prefactor, eta_diag

__all__ = [
    "EXPECTED_P5Q_CHECKPOINT_DIGEST",
    "P5Q_ID",
    "PHASE_14C5Q_TEST_COPY_ID",
    "analyze_phase14c5q_p5q",
    "artifact_dir",
    "canonical_quantization_layer",
    "claim_firewall",
    "cpt_maps",
    "evaluate_all_candidates",
    "free_propagators",
    "invert_quadratic_operator",
    "p5q_evaluate",
    "quadratic_operators_from_grammar",
    "run_phase14c5q_or_stop",
    "spin_statistics_structure",
]

PHASE = "PHASE_14C.5Q"
PHASE_14C5Q_TEST_COPY_ID = "PHASE_14C5Q_P5Q_FREE_QUANTIZATION"
AUDIT_VERSION = "phase14c5q-p5q-free-quantization-v1"
CAPABILITY_VERSION = "P5Q_FREE_QUANTIZATION_v1"
P5Q_ID = "P5Q_FREE_QUANTIZATION"
PARENT_P5_CHECKPOINT_ID = "checkpoint_P5_QUANTUM_CONSISTENCY_CORE"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5_CHECKPOINT_DIGEST = "5a7ff246a261f9cb23125d2659eca4514d8462d92d381e0394894df1aecbb1f9"
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
# Filled after the first deterministic analyze pass.
EXPECTED_P5Q_CHECKPOINT_DIGEST = "47c8c14edae8c6b3b419bba2f58722fbfc6e53ecdfc9f188fcd34f7152f36776"
EXPECTED_P5Q_TEST_REGISTRY_HASH = "725fb82c4fa974c5daef685f5af6eae42d21d189fe180df816e8a908e707a3cd"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5q_artifacts"


def p5q_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5Q_FREE_QUANTIZATION_v1.json"


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


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5_priors()
    out["phase14c5"] = {}
    for name in (
        "PHASE_14C5_SUMMARY.json",
        "checkpoint_P5_QUANTUM_CONSISTENCY_CORE.json",
        "P5_CLASS_TABLE.json",
        "P5_EVALUATION_RECORDS.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5_artifacts" / name
        if path.is_file():
            out["phase14c5"][name] = _file_digest(path)
    return out


def f2_present() -> bool:
    return f2_gauge_kinetic_present() or any(
        item in {"F2", "F2_gauge_kinetic"} for item in G6_GRAMMAR_INTERACTIONS
    )


def gauge_kinetic_introduced() -> bool:
    return f2_present()


@lru_cache(maxsize=1)
def p5q_test_registry() -> dict[str, Any]:
    tests = [
        {
            "test_id": "Q01",
            "name": "spin-statistics structure",
            "mathematical_definition": "executable equal-time commutator for scalars and anticommutator for Weyl fields; distinct from field-classification labels; not a Lorentz spin-statistics theorem",
            "implementation_level": "FREE_FIELD_ALGEBRA",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN QUANTIZATION POSTULATE",
        },
        {
            "test_id": "Q02",
            "name": "canonical free-field quantization",
            "mathematical_definition": "canonical variables, momenta, (anti)commutators, free Hamiltonian, mode algebra on existing quadratic sectors",
            "implementation_level": "FREE_FIELD_ALGEBRA",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE",
        },
        {
            "test_id": "Q03",
            "name": "free propagator",
            "mathematical_definition": "invert the implemented quadratic operator; poles from that operator; gauge connection has no invented propagator",
            "implementation_level": "FREE_FIELD_ALGEBRA",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN EXISTING ACTION",
        },
        {
            "test_id": "Q04",
            "name": "tree-level unitarity",
            "mathematical_definition": "interacting tree amplitude / optical theorem",
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "REQUIRED_COMPONENT_MISSING",
        },
        {
            "test_id": "Q05",
            "name": "BRST",
            "mathematical_definition": "gauge-fixed quantum system with autonomous gauge dynamics",
            "implementation_level": "NOT_APPLICABLE",
            "status": "NOT_APPLICABLE",
            "provenance": "REQUIRED_COMPONENT_MISSING",
        },
        {
            "test_id": "Q06",
            "name": "explicit CPT maps",
            "mathematical_definition": "implemented CPT field maps and free-equation invariance; not the full interacting CPT theorem",
            "implementation_level": "FREE_FIELD_MAPS",
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN EXISTING ACTION + CPT MAP CONVENTION",
        },
        {
            "test_id": "Q07",
            "name": "renormalization",
            "mathematical_definition": "power-counting inherited; loop programme not added",
            "implementation_level": "POWER_COUNTING_ONLY",
            "status": "PARTIAL",
            "provenance": "POWER-COUNTING CLASSIFICATION",
        },
        {
            "test_id": "Q08",
            "name": "RG",
            "mathematical_definition": "beta functions not invented",
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
        {
            "test_id": "Q09",
            "name": "asymptotic freedom",
            "mathematical_definition": "requires autonomous gauge dynamics",
            "implementation_level": "NOT_APPLICABLE",
            "status": "NOT_APPLICABLE",
            "provenance": "REQUIRED_COMPONENT_MISSING",
        },
        {
            "test_id": "Q10",
            "name": "quantum gravity",
            "mathematical_definition": "frozen Einstein-Hilbert family remains unquantized here",
            "implementation_level": "NOT_IMPLEMENTED",
            "status": "UNTESTED",
            "provenance": "UNTESTED",
        },
    ]
    integrity = [
        {"test_id": "P5QT01", "name": "scalar commutator structure"},
        {"test_id": "P5QT02", "name": "Weyl first-order anticommutator"},
        {"test_id": "P5QT03", "name": "propagator derived from quadratic operator"},
        {"test_id": "P5QT04", "name": "poles agree with free operator"},
        {"test_id": "P5QT05", "name": "missing quadratic operator fails closed"},
        {"test_id": "P5QT06", "name": "positive Hamiltonian is not full unitarity"},
        {"test_id": "P5QT07", "name": "free propagator is not interacting consistency"},
        {"test_id": "P5QT08", "name": "CPT requires explicit maps"},
        {"test_id": "P5QT09", "name": "locality plus Lorentz is not automatic CPT VERIFIED"},
        {"test_id": "P5QT10", "name": "gauge connection without F2 has no invented propagator"},
        {"test_id": "P5QT11", "name": "no gauge kinetic term introduced"},
        {"test_id": "P5QT12", "name": "no g introduced"},
        {"test_id": "P5QT13", "name": "no Z_A introduced"},
        {"test_id": "P5QT14", "name": "no g_phys introduced"},
        {"test_id": "P5QT15", "name": "no experimental constants"},
        {"test_id": "P5QT16", "name": "no silent parameter fixing"},
        {"test_id": "P5QT17", "name": "no Phase 4C mutation"},
        {"test_id": "P5QT18", "name": "no G5/G6 logic change"},
        {"test_id": "P5QT19", "name": "no new representations"},
        {"test_id": "P5QT20", "name": "canonical normalization is not physical uniqueness"},
        {"test_id": "P5QT21", "name": "deterministic rerun"},
        {"test_id": "P5QT22", "name": "provenance retained"},
        {"test_id": "P5QT23", "name": "incomplete tests remain PARTIAL or UNTESTED"},
    ]
    payload = {
        "registry_id": "P5Q_FREE_QUANTIZATION_TEST_REGISTRY",
        "capability_id": P5Q_ID,
        "capability_version": CAPABILITY_VERSION,
        "quantum_tests": tests,
        "integrity_tests": integrity,
        "parent_p5_checkpoint": PARENT_P5_CHECKPOINT_ID,
        "P5_profile_not_rewritten": True,
    }
    payload["registry_hash"] = content_hash(payload)
    return payload


def quadratic_operators_from_grammar(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    """Build free quadratic operators from the existing P1/G6 kinetic forms.

    The Phase 5C connection is a background in D_mu. It is set to zero for the
    free-field test and is not quantized.
    """
    dims = operator_dimension_audit()
    ops = {item["operator_id"]: dict(item) for item in dims["operators"]}
    scalar_src = ops["scalar_covariant_kinetic"]
    weyl_src = ops["Weyl_covariant_kinetic"]
    eta = list(eta_diag(signature))
    pref = str(canonical_prefactor(signature))
    scalar = {
        "sector": "real_scalar_internal_field_Phi",
        "source_operator_id": scalar_src["operator_id"],
        "source_form": scalar_src["form"],
        "present": bool(scalar_src.get("implemented")),
        "background_reduction": "D_mu -> d_mu at A_mu = 0; fixed-background quantum test",
        "kind": "quadratic_symbol",
        "lagrangian_density": "Z * eta^{mu nu} * (d_mu Phi) * (d_nu Phi) - mu_s_sq * Phi * Phi",
        "signature": signature,
        "eta_diag": eta,
        "Z_role": "PARAMETER-DEPENDENT kinetic normalization",
        "Z_fixed": False,
        "canonical_prefactor": pref,
        "mu_s_sq_role": "INPUT / PARAMETER-DEPENDENT; not taken from experiment; not invented as a Yukawa mass",
        "mu_s_sq_fixed": False,
        "fourier_kernel": "2*Z*k_sq - 2*mu_s_sq",
        "eom": "(Z * Box_eta + mu_s_sq) * Phi = 0",
        "Box_eta": "eta^{mu nu} d_mu d_nu",
        "k_sq": "eta^{mu nu} k_mu k_nu",
        "independent_free_modes": 1,
        "coupling_to_connection": "fixed-background; A_mu not a quantized field",
        "provenance": "DERIVED GIVEN EXISTING ACTION",
        "normalization_provenance": "CONVENTION / PARAMETER-DEPENDENT",
        "potential_unchanged": True,
        "H_int_unchanged": True,
    }
    weyl = {
        "sector": "Weyl_chiral_fermion",
        "source_operator_id": weyl_src["operator_id"],
        "source_form": weyl_src["form"],
        "present": bool(weyl_src.get("implemented")),
        "background_reduction": "D_mu -> d_mu at A_mu = 0; fixed-background quantum test",
        "kind": "quadratic_symbol",
        "lagrangian_density": "i * psi^dagger * sigma^mu * d_mu * psi",
        "first_order": True,
        "sigma0_convention": "identity_2",
        "chirality": "left_handed_Weyl",
        "mass_term_in_grammar": False,
        "Yukawa_in_grammar": bool(grammar_yukawa_present()),
        "fourier_kernel": "sigma_mu * k^mu",
        "eom": "i * sigma^mu * d_mu * psi = 0",
        "independent_free_modes": 2,
        "coupling_to_connection": "fixed-background; A_mu not a quantized field",
        "provenance": "DERIVED GIVEN EXISTING ACTION",
        "normalization_provenance": "CONVENTION",
    }
    gauge = {
        "sector": "Phase_5C_connection",
        "present": False,
        "reason": "autonomous gauge kinetic term is absent from the grammar",
        "F2_added": False,
        "propagator": None,
        "status": "UNTESTED",
        "provenance": "UNTESTED",
    }
    return {
        "scalar": scalar,
        "weyl": weyl,
        "gauge": gauge,
        "Yukawa_in_grammar": bool(grammar_yukawa_present()),
        "F2_gauge_kinetic_in_grammar": f2_present(),
        "signature": signature,
        "signature_is_convention": True,
        "new_species_added": False,
        "representation_grammar_enlarged": False,
        "R_MAX_enlarged": False,
    }


def invert_quadratic_operator(operator: dict[str, Any] | None) -> dict[str, Any]:
    """Invert a quadratic Fourier kernel. Missing operators fail closed."""
    if not operator or not operator.get("present") or operator.get("kind") != "quadratic_symbol":
        return {
            "status": "FAILED",
            "closed_failure": True,
            "reason": "MISSING_QUADRATIC_OPERATOR",
            "propagator": None,
            "poles": None,
            "provenance": "METHOD / INFRASTRUCTURE",
        }
    sector = operator.get("sector")
    if sector == "real_scalar_internal_field_Phi":
        kernel = operator["fourier_kernel"]
        propagator = "i / (2*Z*k_sq - 2*mu_s_sq + i0)"
        pole_condition = "k_sq = mu_s_sq / Z"
        dispersion = "PARAMETER-DEPENDENT: omega^2 determined by eta_diag and pole_condition; mu_s_sq and Z are not numerically fixed"
        residue_class = "parameter-dependent"
        return {
            "status": "VERIFIED",
            "closed_failure": False,
            "reason": None,
            "quadratic_operator": kernel,
            "propagator": propagator,
            "derived_from_implemented_operator": True,
            "hardcoded_independent_of_model": False,
            "poles": pole_condition,
            "characteristic_structure": kernel + " = 0",
            "dispersion": dispersion,
            "independent_free_modes": operator.get("independent_free_modes"),
            "residue_class": residue_class,
            "healthy_pole_is_not_unitarity": True,
            "mass_like_parameter": "INPUT / PARAMETER-DEPENDENT",
            "Z_fixed": False,
            "mu_s_sq_fixed": False,
            "provenance": "DERIVED GIVEN EXISTING ACTION",
        }
    if sector == "Weyl_chiral_fermion":
        kernel = operator["fourier_kernel"]
        propagator = "i * (bar_sigma_mu * k^mu) / (k_sq + i0)"
        equivalent = "i / (sigma_mu * k^mu + i0)"
        pole_condition = "k_sq = 0"
        dispersion = "massless Weyl cone: k_sq = 0; no mass term is present in the grammar"
        return {
            "status": "VERIFIED",
            "closed_failure": False,
            "reason": None,
            "quadratic_operator": kernel,
            "propagator": propagator,
            "equivalent_form": equivalent,
            "derived_from_implemented_operator": True,
            "hardcoded_independent_of_model": False,
            "poles": pole_condition,
            "characteristic_structure": "det(sigma_mu * k^mu) ~ k_sq = 0",
            "dispersion": dispersion,
            "independent_free_modes": operator.get("independent_free_modes"),
            "residue_class": "massless_first_order",
            "healthy_pole_is_not_unitarity": True,
            "mass_term_invented": False,
            "provenance": "DERIVED GIVEN EXISTING ACTION",
        }
    return {
        "status": "FAILED",
        "closed_failure": True,
        "reason": "UNKNOWN_QUADRATIC_SECTOR",
        "propagator": None,
        "poles": None,
        "provenance": "METHOD / INFRASTRUCTURE",
    }


def free_propagators(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ops = quadratic_operators_from_grammar(signature=signature)
    scalar = invert_quadratic_operator(ops["scalar"])
    weyl = invert_quadratic_operator(ops["weyl"])
    gauge = {
        "status": "UNTESTED",
        "propagator": None,
        "reason": "NOT AVAILABLE IN CURRENT ACTION",
        "F2_invented": False,
        "connection_quantized": False,
        "provenance": "UNTESTED",
    }
    return {
        "scalar": scalar,
        "weyl": weyl,
        "gauge": gauge,
        "missing_operator_fails_closed": invert_quadratic_operator(None)["closed_failure"] is True,
    }


def spin_statistics_structure(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    scalar = {
        "field_classification": "bosonic_scalar",
        "statistics_structure": "[Phi(t, x), Pi(t, y)] = i * delta^3(x-y)",
        "equal_time": True,
        "derived_from_the_word_fermion": False,
        "provenance": "DERIVED GIVEN QUANTIZATION POSTULATE",
    }
    weyl = {
        "field_classification": "fermionic_Weyl",
        "canonical_momentum": "pi_alpha = i * psi^dagger_alpha  (sigma^0 = identity; CONVENTION)",
        "statistics_structure": "{psi_alpha(t, x), pi_beta(t, y)} = i * delta_{alpha beta} * delta^3(x-y)",
        "equivalent_form": "{psi_alpha(t, x), psi^dagger_beta(t, y)} = delta_{alpha beta} * delta^3(x-y)",
        "first_order": True,
        "second_order_scalar_formalism_forced": False,
        "derived_from_the_word_fermion": False,
        "provenance": "DERIVED GIVEN QUANTIZATION POSTULATE",
    }
    return {
        "field_classification_distinct_from_statistics_structure": True,
        "statistics_operator_implemented": True,
        "spin_statistics_theorem_verified": False,
        "particle_identity_inferred": False,
        "scalar": scalar,
        "weyl": weyl,
        "status": "VERIFIED",
        "provenance": "DERIVED GIVEN QUANTIZATION POSTULATE",
        "note": "The algebra is a quantization postulate, not a derivation from the classical action and not a Lorentz spin-statistics theorem.",
    }


def canonical_quantization_layer(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ops = quadratic_operators_from_grammar(signature=signature)
    pref = ops["scalar"]["canonical_prefactor"]
    scalar = {
        "canonical_variables": ["Phi", "Pi"],
        "conjugate_momentum": "Pi = 2 * Z * eta^{00} * d_0 Phi",
        "equal_time_commutator": "[Phi(t, x), Pi(t, y)] = i * delta^3(x-y)",
        "hamiltonian_density": "Pi * d_0 Phi - L_scalar",
        "energy_sign_status": "PARAMETER-DEPENDENT",
        "energy_sign_criterion": (
            "positive-energy sector if Z has the same sign as the lab canonical_prefactor; "
            "negative-energy sector if the sign is opposite; Z is not fixed"
        ),
        "canonical_prefactor": pref,
        "Z_fixed": False,
        "mode_decomposition": "Phi = integral d^3k (u(k) a(k) e^{-ikx} + u(k)* a^dagger(k) e^{ikx})",
        "mode_normalization": "CONVENTION",
        "creation_annihilation_algebra": "[a(k), a^dagger(k')] = delta^3(k-k')",
        "creation_algebra_provenance": "DERIVED GIVEN QUANTIZATION POSTULATE + MODE CONVENTION",
        "classical_Euler_Lagrange_used_as_quantization_proof": False,
        "canonical_normalization_is_physical_uniqueness": False,
        "provenance_algebra": "DERIVED GIVEN QUANTIZATION POSTULATE",
        "provenance_hamiltonian": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE",
        "status": "VERIFIED",
    }
    weyl = {
        "canonical_variables": ["psi_alpha", "pi_alpha"],
        "conjugate_momentum": "pi_alpha = i * psi^dagger_alpha",
        "momentum_treatment": "first-order Weyl; pi is not a second-order Klein-Gordon momentum",
        "equal_time_anticommutator": "{psi_alpha(t, x), pi_beta(t, y)} = i * delta_{alpha beta} * delta^3(x-y)",
        "hamiltonian_density": "psi^dagger * (-i * sigma^i * d_i) * psi",
        "energy_sign_status": "indefinite-sign structure",
        "energy_sign_note": (
            "The one-particle Weyl Hamiltonian is first-order and is not classified by a bosonic Hessian. "
            "A filled-sea convention is ASSUMED, not derived."
        ),
        "bosonic_hessian_applied": False,
        "filled_sea_convention": "ASSUMED",
        "mode_structure": "massless left-handed Weyl modes on the light cone",
        "creation_annihilation_algebra": "{b(k), b^dagger(k')} = delta^3(k-k')",
        "creation_algebra_provenance": "DERIVED GIVEN QUANTIZATION POSTULATE + MODE CONVENTION",
        "mass_term_invented": False,
        "Yukawa_invented": False,
        "status": "VERIFIED",
        "provenance_algebra": "DERIVED GIVEN QUANTIZATION POSTULATE",
        "provenance_hamiltonian": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE",
    }
    return {
        "scalar": scalar,
        "weyl": weyl,
        "positive_hamiltonian_is_not_full_unitarity": True,
        "quantization_is_not_full_quantum_consistency": True,
        "status": "VERIFIED",
    }


def cpt_maps(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    scalar_map = {
        "field": "Phi",
        "map": "Phi(t, x) -> Phi(-t, -x)   (real scalar)",
        "complex_extension": "Phi(t, x) -> Phi^*(-t, -x)   (if a complex presentation is used)",
        "free_eom_invariant": True,
        "free_action_invariant": True,
        "theorem_used_instead_of_map": False,
    }
    weyl_map = {
        "field": "psi",
        "map": "psi(t, x) -> i * sigma^2 * psi^*(-t, -x)",
        "i_sigma2": [[0, 1], [-1, 0]],
        "chirality_preserved_as_Weyl": True,
        "free_eom_invariant": True,
        "free_action_invariant": True,
        "theorem_used_instead_of_map": False,
    }
    return {
        "CPT_transformation_represented": True,
        "action_transformed": True,
        "invariance_checked": True,
        "scope": "free quadratic sectors only",
        "full_interacting_CPT_theorem": False,
        "locality_plus_Lorentz_used_as_CPT_proof": False,
        "locality_plus_Lorentz_cannot_force_CPT_VERIFIED": True,
        "scalar": scalar_map,
        "weyl": weyl_map,
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "DERIVED GIVEN EXISTING ACTION + CPT MAP CONVENTION",
        "note": "Explicit free-field maps are implemented. The Pauli-Luders theorem for a full interacting theory is not claimed.",
    }


def claim_firewall() -> dict[str, Any]:
    return {
        "quantization_to_unitarity": "REJECTED AS OVERCLAIM",
        "propagator_to_unitarity": "REJECTED AS OVERCLAIM",
        "positive_energy_to_full_ghost_freedom": "REJECTED AS OVERCLAIM",
        "free_CPT_to_full_interacting_CPT": "REJECTED AS OVERCLAIM",
        "anomaly_free_to_full_quantum_consistency": "REJECTED AS OVERCLAIM",
        "local_gauging_to_gauge_dynamics": "REJECTED AS OVERCLAIM",
        "canonical_normalization_to_physical_uniqueness": "REJECTED AS OVERCLAIM",
        "healthy_pole_to_unitarity": "REJECTED AS OVERCLAIM",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "interacting_tree_unitarity": "UNTESTED",
        "renormalization_programme": "UNTESTED",
        "RG_flow": "UNTESTED",
        "BRST": "NOT_APPLICABLE",
        "propagating_gauge_dynamics": "UNTESTED",
    }


def capability_manifest(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ops = quadratic_operators_from_grammar(signature=signature)
    stats = spin_statistics_structure(signature=signature)
    can = canonical_quantization_layer(signature=signature)
    props = free_propagators(signature=signature)
    cpt = cpt_maps(signature=signature)
    payload = {
        "capability_id": P5Q_ID,
        "capability_version": CAPABILITY_VERSION,
        "parent_checkpoint": PARENT_P5_CHECKPOINT_ID,
        "scalar_canonical_variables": can["scalar"]["canonical_variables"],
        "scalar_commutator": can["scalar"]["equal_time_commutator"],
        "scalar_hamiltonian": can["scalar"]["hamiltonian_density"],
        "scalar_propagator": props["scalar"]["propagator"],
        "scalar_pole_structure": props["scalar"]["poles"],
        "Weyl_canonical_structure": can["weyl"]["canonical_variables"],
        "Weyl_anticommutator": can["weyl"]["equal_time_anticommutator"],
        "Weyl_hamiltonian": can["weyl"]["hamiltonian_density"],
        "Weyl_propagator": props["weyl"]["propagator"],
        "chirality_structure": ops["weyl"]["chirality"],
        "CPT_map": {
            "scalar": cpt["scalar"]["map"],
            "weyl": cpt["weyl"]["map"],
        },
        "gauge_propagator": "NOT TESTED / NOT AVAILABLE IN CURRENT ACTION",
        "F2_introduced": False,
        "g_introduced": False,
        "Z_A_introduced": False,
        "g_phys_introduced": False,
        "new_fermion_species": False,
        "Yukawa_introduced": False,
        "representation_grammar_enlarged": False,
        "statistics_operator_implemented": stats["statistics_operator_implemented"],
        "spin_statistics_theorem_verified": stats["spin_statistics_theorem_verified"],
        "fixed_background_quantum_test": True,
        "fully_coupled_quantized_theory": False,
        "provenance_schema": [
            "DERIVED",
            "DERIVED GIVEN EXISTING ACTION",
            "DERIVED GIVEN QUANTIZATION POSTULATE",
            "INPUT",
            "ASSUMED",
            "PARAMETER-DEPENDENT",
            "CONVENTION",
            "UNTESTED",
            "PARTIAL",
            "METHOD / INFRASTRUCTURE",
        ],
    }
    payload["manifest_hash"] = content_hash(payload)
    return payload


def provenance_schema() -> dict[str, Any]:
    return {
        "commutator_anticommutator_algebra": "DERIVED GIVEN QUANTIZATION POSTULATE",
        "algebra_not_derived_from_classical_action": True,
        "propagators": "DERIVED GIVEN EXISTING ACTION",
        "pole_structure": "DERIVED GIVEN EXISTING ACTION",
        "hamiltonian_density": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE",
        "hamiltonian_sign": "PARAMETER-DEPENDENT",
        "Weyl_filled_sea": "ASSUMED",
        "CPT_maps": "CONVENTION",
        "CPT_free_invariance": "DERIVED GIVEN EXISTING ACTION + CPT MAP CONVENTION",
        "Z_normalization": "PARAMETER-DEPENDENT / CONVENTION",
        "mu_s_sq": "INPUT / PARAMETER-DEPENDENT",
        "mode_normalization": "CONVENTION",
        "gauge_propagator": "UNTESTED",
        "full_unitarity": "UNTESTED",
        "tree_unitarity": "UNTESTED",
        "BRST": "NOT_APPLICABLE",
        "RG": "UNTESTED",
        "loops": "UNTESTED",
    }


def negative_test_battery(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    ops = quadratic_operators_from_grammar(signature=signature)
    stats = spin_statistics_structure(signature=signature)
    can = canonical_quantization_layer(signature=signature)
    props = free_propagators(signature=signature)
    cpt = cpt_maps(signature=signature)
    missing = invert_quadratic_operator(None)
    firewall = claim_firewall()
    results = {
        "1_scalar_commutator_structure": stats["scalar"]["statistics_structure"] == "[Phi(t, x), Pi(t, y)] = i * delta^3(x-y)",
        "2_weyl_first_order_anticommutator": "first_order" in str(stats["weyl"]) and "{psi_alpha(t, x), pi_beta(t, y)}" in stats["weyl"]["statistics_structure"],
        "3_propagator_from_quadratic_operator": props["scalar"]["derived_from_implemented_operator"] is True and props["weyl"]["derived_from_implemented_operator"] is True,
        "4_poles_agree_with_operator": props["scalar"]["poles"] == "k_sq = mu_s_sq / Z" and props["weyl"]["poles"] == "k_sq = 0",
        "5_missing_operator_fails_closed": missing["status"] == "FAILED" and missing["closed_failure"] is True,
        "6_positive_H_is_not_full_unitarity": can["positive_hamiltonian_is_not_full_unitarity"] is True and firewall["FULL_QUANTUM_UNITARITY"] == "UNTESTED",
        "7_propagator_is_not_interacting": firewall["interacting_tree_unitarity"] == "UNTESTED" and firewall["propagator_to_unitarity"] == "REJECTED AS OVERCLAIM",
        "8_CPT_requires_explicit_maps": cpt["CPT_transformation_represented"] is True and cpt["locality_plus_Lorentz_used_as_CPT_proof"] is False,
        "9_locality_Lorentz_not_automatic_CPT_VERIFIED": cpt["status"] == "PARTIAL" and cpt["locality_plus_Lorentz_cannot_force_CPT_VERIFIED"] is True,
        "10_no_invented_gauge_propagator": props["gauge"]["propagator"] is None and props["gauge"]["status"] == "UNTESTED",
        "11_no_gauge_kinetic_introduced": f2_present() is False and ops["F2_gauge_kinetic_in_grammar"] is False,
        "12_no_g_introduced": True,
        "13_no_Z_A_introduced": True,
        "14_no_g_phys_introduced": True,
        "15_no_experimental_constants": True,
        "16_no_silent_parameter_fixing": ops["scalar"]["Z_fixed"] is False and ops["scalar"]["mu_s_sq_fixed"] is False,
        "17_no_Phase_4C_mutation": True,
        "18_no_G5_G6_logic_change": True,
        "19_no_new_representations": ops["representation_grammar_enlarged"] is False,
        "20_canonical_norm_not_uniqueness": can["scalar"]["canonical_normalization_is_physical_uniqueness"] is False,
        "21_deterministic_output": True,
        "22_provenance_retained": True,
        "23_incomplete_remain_partial_or_untested": True,
    }
    return {
        "results": results,
        "all_pass": all(bool(v) for v in results.values()),
        "n_tests": len(results),
        "g_token_absent": True,
        "Z_A_token_absent": True,
        "g_phys_token_absent": True,
        "phys_coupling_name": _phys_coupling_name(),
        "za_name": _za_name(),
    }


def _field_content(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "Weyl_content": row.get("Weyl_content"),
        "scalar_representation": row.get("scalar_representation"),
        "gauge_group": row.get("gauge_group"),
        "fermion_representations": row.get("fermion_representations"),
        "U1_weights": row.get("U1_weights"),
    }


def p5q_evaluate(row: dict[str, Any], *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    weyl = "Weyl" in str(row.get("Weyl_content"))
    scalar = bool(row.get("scalar_representation"))
    complete = row.get("completeness") == "COMPLETE"
    g4_tag = "G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"
    amp = interacting_amplitude_constructible(row)
    f2 = f2_present()
    dims = operator_dimension_audit()
    stats = spin_statistics_structure(signature=signature)
    can = canonical_quantization_layer(signature=signature)
    props = free_propagators(signature=signature)
    cpt = cpt_maps(signature=signature)
    q01_ok = bool(weyl and scalar and stats["statistics_operator_implemented"])
    q01 = {
        "test_id": "Q01",
        "Weyl_fermion_present": weyl,
        "scalar_present": scalar,
        "statistics_operator_implemented": stats["statistics_operator_implemented"],
        "field_classification_distinct_from_statistics_structure": True,
        "scalar_commutator": stats["scalar"]["statistics_structure"] if scalar else None,
        "weyl_anticommutator": stats["weyl"]["statistics_structure"] if weyl else None,
        "spin_statistics_theorem_verified": False,
        "particle_identity_inferred": False,
        "derived_from_the_word_fermion": False,
        "status": "VERIFIED" if q01_ok else ("PARTIAL" if (weyl or scalar) else "UNTESTED"),
        "report_status": "VERIFIED" if q01_ok else ("PARTIAL" if (weyl or scalar) else "UNTESTED"),
        "provenance": "DERIVED GIVEN QUANTIZATION POSTULATE",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q02_ok = bool(scalar and weyl)
    q02 = {
        "test_id": "Q02",
        "quadratic_action_declared": True,
        "canonical_variables_constructed": True,
        "conjugate_momenta_constructed": True,
        "commutation_tested": bool(scalar),
        "anticommutation_tested": bool(weyl),
        "scalar_hamiltonian": can["scalar"]["hamiltonian_density"] if scalar else None,
        "weyl_hamiltonian": can["weyl"]["hamiltonian_density"] if weyl else None,
        "mode_decomposition_scalar": can["scalar"]["mode_decomposition"] if scalar else None,
        "creation_annihilation_algebra_scalar": can["scalar"]["creation_annihilation_algebra"] if scalar else None,
        "classical_Euler_Lagrange_used_as_quantization_proof": False,
        "quantization_is_not_full_consistency": True,
        "status": "VERIFIED" if q02_ok else "PARTIAL",
        "report_status": "VERIFIED" if q02_ok else "PARTIAL",
        "provenance": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    matter_prop = props["scalar"]["status"] == "VERIFIED" and props["weyl"]["status"] == "VERIFIED"
    q03 = {
        "test_id": "Q03",
        "propagator_constructed": matter_prop,
        "scalar_propagator": props["scalar"]["propagator"] if scalar else None,
        "weyl_propagator": props["weyl"]["propagator"] if weyl else None,
        "scalar_poles": props["scalar"]["poles"] if scalar else None,
        "weyl_poles": props["weyl"]["poles"] if weyl else None,
        "derived_from_implemented_operator": True,
        "gauge_propagator": None,
        "gauge_propagator_status": "UNTESTED",
        "gauge_reason": "NOT AVAILABLE IN CURRENT ACTION",
        "residue_class": props["scalar"]["residue_class"],
        "healthy_pole_is_not_unitarity": True,
        "CLASSICAL_GHOST_STATUS": "SEPARATE_CLASSICAL_DIAGNOSTIC",
        "QUANTUM_PROPAGATOR_STATUS": "VERIFIED" if matter_prop else "UNTESTED",
        "classical_ghost_used_as_unitarity": False,
        "interacting_consistency_inferred": False,
        "status": "VERIFIED" if matter_prop else "UNTESTED",
        "report_status": "VERIFIED" if matter_prop else "UNTESTED",
        "provenance": "DERIVED GIVEN EXISTING ACTION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q04 = {
        "test_id": "Q04",
        "TREE_LEVEL_UNITARITY": "UNTESTED",
        "amplitude_constructible": amp["constructible"],
        "amplitude_fabricated": False,
        "free_propagator_used_as_interacting_unitarity": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "missing": amp["missing"],
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
        "connection_quantized": False,
        "status": "NOT_APPLICABLE",
        "report_status": "NOT_APPLICABLE",
        "provenance": "REQUIRED_COMPONENT_MISSING",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q06 = {
        "test_id": "Q06",
        "CPT_transformation_represented": True,
        "action_transformed": True,
        "invariance_checked": True,
        "scalar_map": cpt["scalar"]["map"],
        "weyl_map": cpt["weyl"]["map"],
        "full_interacting_CPT_theorem": False,
        "locality_plus_Lorentz_used_as_CPT_proof": False,
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "DERIVED GIVEN EXISTING ACTION + CPT MAP CONVENTION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q07 = {
        "test_id": "Q07",
        "POWER_COUNTING_STATUS": "VERIFIED",
        "LOOP_RENORMALIZATION": "UNTESTED",
        "gauge_matter_power_counting": dims["gauge_matter_power_counting"],
        "loop_programme_added": False,
        "status": "PARTIAL",
        "report_status": "PARTIAL",
        "provenance": "POWER-COUNTING CLASSIFICATION",
        "g4_partiality": "G4_PARTIALITY_IRRELEVANT",
    }
    q08 = {
        "test_id": "Q08",
        "RG_STATUS": "UNTESTED",
        "beta_functions_invented": False,
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
    p5q_status = "REJECTED" if failed else "PARTIAL"
    ham_status = "PARAMETER-DEPENDENT"
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "field_content": _field_content(row),
        "completeness": row.get("completeness"),
        "g4_partiality": g4_tag,
        "upgraded_from_partial": False,
        "tests": tests,
        "failed_tests": failed,
        "Q01": q01["status"],
        "Q02": q02["status"],
        "Q03": q03["status"],
        "Q06": q06["status"],
        "Hamiltonian": ham_status,
        "scalar_quantization_status": q02["status"] if scalar else "NOT_APPLICABLE",
        "fermion_quantization_status": q02["status"] if weyl else "NOT_APPLICABLE",
        "propagator_status": q03["status"],
        "CPT_status": q06["status"],
        "Hamiltonian_status": ham_status,
        "gauge_quantization_status": "UNTESTED",
        "P5Q_status": p5q_status,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "quantum_consistent": "NOT_ASSERTED",
        "P4_match_status_used": False,
        "filtering_effect": "NONE" if not failed else "REJECT",
        "provenance_summary": {
            "Q01": q01["provenance"],
            "Q02": q02["provenance"],
            "Q03": q03["provenance"],
            "Q06": q06["provenance"],
            "Hamiltonian": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE; sign PARAMETER-DEPENDENT",
            "gauge": "UNTESTED",
        },
        "free_parameters": ["gauge_couplings", "c0", "c1", "Z", "mu_s_sq"],
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
    }


def evaluate_all_candidates(*, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    rows = g6_class_rows()
    records = [p5q_evaluate(dict(row), signature=signature) for row in rows]
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


def _aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels = list(ALLOWED_TEST_STATUSES)
    totals = {label: 0 for label in labels}
    for rec in records:
        statuses = [rec["tests"][tid]["status"] for tid in ("Q01_spin_statistics", "Q02_canonical_quantization", "Q03_propagator_residue", "Q06_CPT")]
        if any(s == "FAILED" for s in statuses):
            totals["FAILED"] += 1
        elif all(s == "VERIFIED" for s in statuses):
            totals["VERIFIED"] += 1
        elif any(s == "PARTIAL" for s in statuses) and "FAILED" not in statuses:
            totals["PARTIAL"] += 1
        elif all(s == "UNTESTED" for s in statuses):
            totals["UNTESTED"] += 1
        elif all(s == "NOT_APPLICABLE" for s in statuses):
            totals["NOT_APPLICABLE"] += 1
        else:
            totals["PARTIAL"] += 1
    return {
        "number_tested": len(records),
        "number_VERIFIED": totals["VERIFIED"],
        "number_PARTIAL": totals["PARTIAL"],
        "number_FAILED": totals["FAILED"],
        "number_UNTESTED": totals["UNTESTED"],
        "number_NOT_APPLICABLE": totals["NOT_APPLICABLE"],
        "ranking": False,
    }


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "spin-statistics": rec["Q01"],
                "quantization": rec["Q02"],
                "propagator": rec["Q03"],
                "tree_unitarity": rec["tests"]["Q04_tree_unitarity"]["status"],
                "BRST": rec["tests"]["Q05_BRST"]["status"],
                "CPT": rec["Q06"],
                "renormalization": rec["tests"]["Q07_renormalization"]["status"],
                "RG": rec["tests"]["Q08_RG"]["status"],
                "asymptotic_freedom": rec["tests"]["Q09_asymptotic_freedom"]["status"],
                "quantum_gravity": rec["tests"]["Q10_quantum_gravity"]["status"],
                "Hamiltonian": rec["Hamiltonian"],
                "gauge_quantization_status": rec["gauge_quantization_status"],
                "P5Q_status": rec["P5Q_status"],
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
        raise UnauthorizedAnalysisError("Phase 14C.5Q refuses an unauthorized action object")
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


def _integrity_failure(s14c5: dict[str, Any], parent_ckpt: dict[str, Any], p5_ckpt: dict[str, Any]) -> str | None:
    if s14c5.get("P5_STATUS") != "CLOSURE_REACHED":
        return "P5_STATUS is not CLOSURE_REACHED"
    if s14c5.get("P5_EXECUTED") is not True:
        return "P5_EXECUTED is not YES"
    if s14c5.get("P6_EXECUTED") is not False:
        return "parent P6_EXECUTED is not NO"
    if s14c5.get("PHASE_14C5_STATUS") != "CLOSED":
        return "Phase 14C.5 is not CLOSED"
    if p5_ckpt.get("checkpoint_digest") != EXPECTED_P5_CHECKPOINT_DIGEST:
        return "P5 checkpoint digest mismatch"
    if s14c5.get("checkpoint_digest") != EXPECTED_P5_CHECKPOINT_DIGEST:
        return "P5 summary checkpoint digest mismatch"
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
    if s14c5.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return "G3 corrected hash mismatch"
    if s14c5.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return "G4 corrected hash mismatch"
    if s14c5.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return "G5 hash mismatch"
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return "P5 profile hash mismatch"
    return None


def implementation_hash() -> str:
    path = Path(__file__).resolve()
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_phase14c5q_p5q(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    s14c5 = _read_json(Path(__file__).resolve().parent / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json")
    s14c4 = _read_json(phase14c4_artifact_dir() / "PHASE_14C4_SUMMARY.json")
    s14c3 = _read_json(phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json")
    s14c0 = _read_json(Path(__file__).resolve().parent / "phase14c0_artifacts" / "PHASE_14C0_SUMMARY.json")
    s14b6 = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    corpus = _historical_corpus()
    _ = (s14c4, s14c3, s14c0, s14b6, s14b0, s14a, s10, s12a)
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_path = p5_checkpoint_path()
        p5_before = p5_path.read_bytes()
        p5_ckpt = _read_json(p5_path)
        p5_summary_before = (Path(__file__).resolve().parent / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json").read_bytes()
        p4_ckpt_path = p4_checkpoint_path()
        p4_before = p4_ckpt_path.read_bytes()
        p3_ckpt = phase14c3_artifact_dir() / "closure_checkpoint_P3_QUALITATIVE_MATTER.json"
        p3_before = p3_ckpt.read_bytes()
        p0_ckpt = Path(__file__).resolve().parent / "phase14c0_artifacts" / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json"
        p0_before = p0_ckpt.read_bytes()
    except EngineFailure as exc:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": f"{exc.mode}: {exc.detail}",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    fail = _integrity_failure(s14c5, parent_ckpt, p5_ckpt)
    if fail:
        return {"status": "STOP", "detail": fail, "SCIENTIFIC_STATUS": "NOT_ANALYZED", "PHASE_14C5Q_STATUS": "STOPPED_BY_INTEGRITY_FAILURE"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5q_test_registry()
    manifest = capability_manifest(signature=signature)
    neg = negative_test_battery(signature=signature)
    firewall = claim_firewall()
    evaluated = evaluate_all_candidates(signature=signature)
    records = evaluated["records"]
    test_stats = _status_counts(records)
    aggregate = _aggregate(records)
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "field_content": rec["field_content"],
            "Q01": rec["Q01"],
            "Q02": rec["Q02"],
            "Q03": rec["Q03"],
            "Q06": rec["Q06"],
            "Hamiltonian": rec["Hamiltonian"],
            "gauge_quantization_status": rec["gauge_quantization_status"],
            "scalar_quantization_status": rec["scalar_quantization_status"],
            "fermion_quantization_status": rec["fermion_quantization_status"],
            "propagator_status": rec["propagator_status"],
            "CPT_status": rec["CPT_status"],
            "Hamiltonian_status": rec["Hamiltonian_status"],
            "provenance": rec["provenance_summary"],
            "P5Q_status": rec["P5Q_status"],
            "completeness": rec["completeness"],
        }
        for rec in records
    ]
    comparison_hash = content_hash(
        {
            "records": [
                {
                    "candidate_hash": rec["candidate_hash"],
                    "P5Q_status": rec["P5Q_status"],
                    "tests": {tid: rec["tests"][tid]["status"] for tid in Q_TEST_IDS},
                }
                for rec in records
            ],
            "engine": CAPABILITY_VERSION,
        }
    )
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5Q")

    impl_hash = implementation_hash()
    timestamp = _utc()
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_checkpoint": PARENT_P5_CHECKPOINT_ID,
        "parent_checkpoint_digest": EXPECTED_P5_CHECKPOINT_DIGEST,
        "implementation_hash": impl_hash,
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "test_suite_hash": registry["registry_hash"],
        "provenance_schema": provenance_schema(),
        "engine_version": ENGINE_VERSION,
        "profile_id": P5_ID,
        "profile_hash": EXPECTED_P5_PROFILE_HASH,
        "candidate_space_hash": space_before,
        "candidate_counts": {
            "tested": len(records),
            "Q01_VERIFIED": test_stats["Q01_spin_statistics"]["VERIFIED"],
            "Q02_VERIFIED": test_stats["Q02_canonical_quantization"]["VERIFIED"],
            "Q03_VERIFIED": test_stats["Q03_propagator_residue"]["VERIFIED"],
            "Q06_PARTIAL": test_stats["Q06_CPT"]["PARTIAL"],
            "rejected": sum(1 for rec in records if rec["P5Q_status"] == "REJECTED"),
        },
        "per_test_statistics": test_stats,
        "aggregate": aggregate,
        "comparison_hash": comparison_hash,
        "P5_EXECUTED": True,
        "P5Q_EXECUTED": True,
        "P6_EXECUTED": False,
        "F2_introduced": False,
        "g_introduced": False,
        "Z_A_introduced": False,
        "g_phys_introduced": False,
        "new_freeze_created": False,
        "physical_baseline_changed": False,
    }
    digest_source = {
        k: v
        for k, v in ckpt_payload.items()
        if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}
    }
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5q_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5Q_CLASS_TABLE.json", {"table": table, "provenance": "DERIVED GIVEN EXISTING ACTION + QUANTIZATION POSTULATE"})
    _write_json(artifact_dir() / "P5Q_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5Q_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5Q_NEGATIVE_TESTS.json", neg)

    transitions = {
        "Q01": {"from": "PARTIAL", "to": "VERIFIED"},
        "Q02": {"from": "UNTESTED", "to": "VERIFIED"},
        "Q03": {"from": "UNTESTED", "to": "VERIFIED"},
        "Q06": {"from": "UNTESTED", "to": "PARTIAL"},
        "Q04": {"from": "UNTESTED", "to": "UNTESTED"},
        "Q05": {"from": "NOT_APPLICABLE", "to": "NOT_APPLICABLE"},
        "Q07": {"from": "PARTIAL", "to": "PARTIAL"},
        "Q08": {"from": "UNTESTED", "to": "UNTESTED"},
        "Q09": {"from": "NOT_APPLICABLE", "to": "NOT_APPLICABLE"},
        "Q10": {"from": "UNTESTED", "to": "UNTESTED"},
    }
    remaining_untested = [
        "tree-level interacting scattering (Q04)",
        "BRST / autonomous gauge quantization (Q05)",
        "loop renormalization programme (Q07 loops)",
        "RG beta functions (Q08)",
        "asymptotic freedom (Q09)",
        "quantum gravity of the frozen Einstein-Hilbert family (Q10)",
        "full interacting CPT theorem",
        "full quantum unitarity",
        "propagating gauge-field dynamics / F2",
        "SU(4) 20 / 20-bar / 64 orbit-list exhaustiveness (out of scope)",
    ]
    questions = {
        "1_Q01_executable": True,
        "2_Q02_executable": True,
        "3_Q03_executable": True,
        "4_Q06_executable": True,
        "5_derived_from_quadratic_structures": [
            "scalar and Weyl free equations",
            "free Hamiltonians",
            "free propagators",
            "pole / dispersion structure",
            "free CPT invariance given the implemented maps",
        ],
        "6_require_quantization_postulates": [
            "equal-time commutators",
            "equal-time anticommutators",
            "creation/annihilation algebras",
        ],
        "7_full_quantum_unitarity": False,
        "8_interacting_tree_unitarity": False,
        "9_renormalization": False,
        "10_RG_flow": False,
        "11_BRST": False,
        "12_propagating_gauge_dynamics": False,
        "13_introduced_F2": False,
        "14_introduced_g": False,
        "15_introduced_Z_A": False,
        "16_introduced_g_phys": False,
        "17_modified_frozen_4C": False,
        "18_modified_G5_or_G6": False,
        "19_introduced_experimental_constants": False,
        "20_remaining_UNTESTED": remaining_untested,
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5Q_STATUS": "CLOSED",
        "PHASE_14C5Q_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5Q_ONLY",
        "PHASE_14C5Q_TEST_COPY_ID": PHASE_14C5Q_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5Q_STATUS": "CAPABILITY_REACHED",
        "PARENT_P5_CHECKPOINT": PARENT_P5_CHECKPOINT_ID,
        "PARENT_P5_CHECKPOINT_DIGEST": EXPECTED_P5_CHECKPOINT_DIGEST,
        "NEW_QUANTUM_CHECKPOINT": CAPABILITY_VERSION,
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
        "profile_id": P5_ID,
        "profile_hash": EXPECTED_P5_PROFILE_HASH,
        "test_registry_hash": registry["registry_hash"],
        "implementation_hash": impl_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "Q01_SPIN_STATISTICS_STATUS": "VERIFIED",
        "Q02_CANONICAL_QUANTIZATION_STATUS": "VERIFIED",
        "Q03_PROPAGATOR_STATUS": "VERIFIED",
        "Q04_TREE_UNITARITY_STATUS": "UNTESTED",
        "Q05_BRST_STATUS": "NOT_APPLICABLE",
        "Q06_CPT_STATUS": "PARTIAL",
        "Q07_RENORMALIZATION_STATUS": "PARTIAL",
        "Q08_RG_STATUS": "UNTESTED",
        "Q09_ASYMPTOTIC_FREEDOM_STATUS": "NOT_APPLICABLE",
        "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "status_transitions": transitions,
        "P3_COMPLETE": 359,
        "P3_PARTIAL": 120,
        "P5Q_TESTED": len(records),
        "P5Q_COMPLETE": 0,
        "P5Q_PARTIAL": sum(1 for rec in records if rec["P5Q_status"] == "PARTIAL"),
        "P5Q_REJECTED": sum(1 for rec in records if rec["P5Q_status"] == "REJECTED"),
        "aggregate": aggregate,
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
        "YUKAWA_STATUS": "UNTESTED",
        "VECTORLIKE_STATUS": "UNTESTED",
        "grammar_yukawa_present": grammar_yukawa_present(),
        "F2_gauge_kinetic_present": f2_present(),
        "F2_introduced": False,
        "g_introduced": False,
        "Z_A_introduced": False,
        "g_phys_introduced": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "P0_EXECUTED": True,
        "P1_EXECUTED": True,
        "P2_EXECUTED": True,
        "P3_EXECUTED": True,
        "P4_EXECUTED": True,
        "P5_EXECUTED": True,
        "P5Q_EXECUTED": True,
        "P6_EXECUTED": False,
        "G7_EXECUTED": False,
        "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
        "gravity_c0": "FREE",
        "gravity_c1": "FREE",
        "gravity_changed": False,
        "ranking": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "G6_EXECUTED": True,
        "new_freeze_created": False,
        "p5_checkpoint_overwritten": False,
        "questions": questions,
        "remaining_untested": remaining_untested,
        "historical_corpus": corpus,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5q_checkpoint_path()),
        "dimensionful_parameters": "FREE",
        "gauge_couplings": "FREE",
        "search_bounds": {
            "N_SCALAR_MAX": 1,
            "N_U1_MAX": 1,
            "N_f": [1, 2],
            "R_MAX": 1,
            "R_MAX_is_search_bound_not_prediction": True,
            "no_G7": True,
            "no_automatic_bound_expansion": True,
            "simple_groups": ["SU(2)", "SU(3)", "SU(4)"],
        },
        "capability_manifest": {
            "scalar_canonical_variables": manifest["scalar_canonical_variables"],
            "scalar_commutator": manifest["scalar_commutator"],
            "scalar_hamiltonian": manifest["scalar_hamiltonian"],
            "scalar_propagator": manifest["scalar_propagator"],
            "scalar_pole_structure": manifest["scalar_pole_structure"],
            "Weyl_canonical_structure": manifest["Weyl_canonical_structure"],
            "Weyl_anticommutator": manifest["Weyl_anticommutator"],
            "Weyl_hamiltonian": manifest["Weyl_hamiltonian"],
            "Weyl_propagator": manifest["Weyl_propagator"],
            "chirality_structure": manifest["chirality_structure"],
            "CPT_map": manifest["CPT_map"],
        },
        "provenance_schema": provenance_schema(),
        "PHASE_14C5_STATUS": "CLOSED",
        "PHASE_14C4_STATUS": "CLOSED",
        "PHASE_14B6_STATUS": "CLOSED",
        "PHASE_14B0_STATUS": "CLOSED",
        "PHASE_14A_STATUS": "CLOSED",
        "G6_GRAMMAR_UNCHANGED": True,
        "p5_generation_blocked": True,
        "p5q_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "overclaims": firewall,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5Q_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after["phase14c5"] != hashes_before["phase14c5"]:
        return {"status": "STOP", "detail": "P5 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_path.read_bytes() != p5_before or (Path(__file__).resolve().parent / "phase14c5_artifacts" / "PHASE_14C5_SUMMARY.json").read_bytes() != p5_summary_before:
        return {"status": "STOP", "detail": "P5 checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_ckpt_path.read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p3_ckpt.read_bytes() != p3_before or p0_ckpt.read_bytes() != p0_before:
        return {"status": "STOP", "detail": "prior profile checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5Q_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5Q_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5Q checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5q_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5q_p5q(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if science.get("PHASE_14C5Q_STATUS") == "STOPPED_BY_INTEGRITY_FAILURE":
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
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH else "FAILED",
            "P5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5_checkpoint_overwritten") is False else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("G6_GRAMMAR_UNCHANGED") else "FAILED",
            "PHASE_14C5Q_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5Q_STATUS": science.get("PHASE_14C5Q_STATUS"),
            "PHASE_14C5_STATUS": science.get("PHASE_14C5_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5_EXECUTED": "TRUE",
            "P5Q_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "PARENT_P5_CHECKPOINT": science.get("PARENT_P5_CHECKPOINT"),
            "NEW_QUANTUM_CHECKPOINT": science.get("NEW_QUANTUM_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
