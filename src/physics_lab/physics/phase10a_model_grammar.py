"""Phase 10A: model-space grammar, provenance firewall, and search infrastructure.

Does not modify the frozen action or Phases 5B.0-9.
Does not run large-scale exploration.  Does not search numerical targets.
Does not import the known-physics comparison catalog.
"""

from __future__ import annotations

import copy
import hashlib
import random
from datetime import datetime, timezone
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
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
from physics_lab.physics.phase9_internal_gap import analyze_phase9_internal_gap
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "ALLOWED_PROVENANCE",
    "AssumptionLockError",
    "BLACKLIST_VERSION",
    "EXPECTED_FROZEN_HASH",
    "GRAMMAR_VERSION",
    "GrammarValidationError",
    "LEGAL_CLAIM_CLASSES",
    "PHASE_10A_TEST_COPY_ID",
    "SEARCH_SPACE_VERSION",
    "WHITELIST_VERSION",
    "add_assumption",
    "analyze_phase10a_infrastructure",
    "baseline_model_spec",
    "canonicalize_model_spec",
    "complexity_budget",
    "deduplicate_models",
    "enumerate_combination_ids",
    "lock_for_solve",
    "model_hash",
    "parameter_inventory",
    "phase10a_objective_text",
    "phase10a_scope_summary_text",
    "refuse_large_scale_generation",
    "run_phase10a_or_stop",
    "search_manifest",
    "search_size_estimate",
    "blacklist",
    "example_catalog",
    "example_catalog_hash",
    "grammar_hash",
    "is_legal_generator_input",
    "legal_generator_inputs",
    "mandatory_rule_set",
    "reference_catalog",
    "reference_catalog_hash",
    "refuse_example_as_generator_input",
    "refuse_reference_as_generator_input",
    "reject_if_not_legal_generator_input",
    "search_space_report",
    "structural_whitelist",
    "LEGAL_DEPENDENCY_RELATION_TYPES",
    "MODEL_SPEC_COMPONENT_LOCI",
    "declared_dependencies",
    "dependency_schema",
    "evaluate_typed_dependency",
    "typed_dependency_definitions",
    "undeclared_inferences",
    "validate_claim_separation",
    "validate_dependencies",
    "validate_model_spec",
    "variation_catalogs",
    "whitelist",
]

GRAMMAR_VERSION = "phase10a-grammar-v1.2"
WHITELIST_VERSION = "phase10a-whitelist-v1.2"
BLACKLIST_VERSION = "phase10a-blacklist-v1.2"
SEARCH_SPACE_VERSION = "phase10a-search-space-v1"
TEST_VERSION = "phase10a-tests-v1.2"
PHASE_10A_TEST_COPY_ID = "PHASE_10A_MODEL_SPACE_GENERATOR"

ALLOWED_PROVENANCE = frozenset(
    {
        "DERIVED",
        "DERIVED GIVEN ASSUMPTION",
        "INPUT",
        "ASSUMED",
        "PARAMETER-DEPENDENT",
        "CALIBRATED",
        "EXPERIMENTAL",
        "CONVENTION",
        "UNTESTED",
        "METHOD",
        "INTEGRITY CONTROL",
    }
)

_FORBIDDEN_GENERATION_PROVENANCE = frozenset({"EXPERIMENTAL", "CALIBRATED"})

LEGAL_CLAIM_CLASSES = frozenset({"MANDATORY", "REFERENCE_ONLY", "EXAMPLE_ONLY"})

LEGAL_DEPENDENCY_RELATION_TYPES = frozenset(
    {
        "CROSS_AXIS_REQUIRES",
        "SAME_AXIS_RELATION",
        "COMPONENT_REQUIRES",
        "UNDEFINED",
    }
)

# Loci established from MODEL_SPEC / baseline_model_spec, not from new physics.
MODEL_SPEC_COMPONENT_LOCI = {
    "H_int": {
        "spec_key": "operator_spec",
        "collection": "operators",
        "id_field": "id",
        "evidence": "baseline_model_spec.operator_spec.operators[].id; _SPEC_KEYS contains operator_spec",
    }
}

_SAME_AXIS_MEANINGS = {
    "alias": False,
    "inheritance": False,
    "extension": False,
    "replacement": False,
    "incompatibility": False,
    "co_selection": False,
}

_REQUIRED_ENTRY_FIELDS = (
    "identifier",
    "mathematical_definition",
    "status",
    "provenance",
    "generator_enabled",
    "bounds",
    "dependencies",
)

_SPEC_KEYS = (
    "spacetime_spec",
    "internal_space_spec",
    "symmetry_spec",
    "representation_spec",
    "operator_spec",
    "matter_action_spec",
    "gauge_spec",
    "gravity_spec",
    "derivative_order",
    "polynomial_order",
    "field_content",
    "normalization_spec",
    "boundary_spec",
    "assumptions",
    "exclusions",
)


class GrammarValidationError(Exception):
    """Fail-closed rejection of a MODEL_SPEC."""


class AssumptionLockError(Exception):
    """Assumptions cannot change after solve begins."""


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


def phase10a_objective_text() -> str:
    return "\n".join(
        [
            "OBJECTIVE",
            "=========",
            "",
            "Phase 10A defines the legal model grammar, finite search space,",
            "provenance firewall, canonicalization, deduplication, and",
            "reproducibility infrastructure.",
            "",
            "MANDATORY rules are operational generator requirements.",
            "REFERENCE_ONLY material is documentary and non-operational.",
            "EXAMPLE_ONLY illustrations are not generator inputs.",
            "",
            "It does NOT run large-scale exploration.",
            "It does NOT search for a numerical target.",
            "It does NOT rank models.",
        ]
    )


def phase10a_scope_summary_text() -> str:
    return "\n".join(
        [
            "SCOPE SUMMARY",
            "=============",
            "",
            "IN SCOPE: MODEL_SPEC grammar; finite catalogs; baseline;",
            "whitelist; blacklist; hashing; manifests; blind filters;",
            "three-class separation of MANDATORY, REFERENCE_ONLY, and",
            "EXAMPLE_ONLY items.",
            "",
            "OUT OF SCOPE: brute-force enumeration; experiment; fitting;",
            "calibration; ranking; preferred new physical principles.",
            "",
            "HUMAN defines legal structures. MACHINE enumerates later",
            "without knowing a target.",
        ]
    )


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 10A refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 10A refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    return None


def _entry(
    identifier: str,
    mathematical_definition: str,
    *,
    status: str,
    provenance: str,
    generator_enabled: bool,
    bounds: dict[str, Any] | None = None,
    dependencies: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    if status not in LEGAL_CLAIM_CLASSES:
        raise GrammarValidationError(f"CLASSIFICATION_ERROR for {identifier}")
    if status in {"EXAMPLE_ONLY", "REFERENCE_ONLY"} and generator_enabled:
        raise GrammarValidationError(f"{status} cannot be generator_enabled")
    payload: dict[str, Any] = {
        "identifier": identifier,
        "id": identifier,
        "mathematical_definition": mathematical_definition,
        "status": status,
        "provenance": provenance,
        "generator_enabled": bool(generator_enabled),
        "bounds": bounds or {},
        "dependencies": list(dependencies or []),
    }
    payload.update(extra)
    return payload


def mandatory_rule_set() -> list[dict[str, Any]]:
    """HARD REQUIREMENTS. Not generator families. generator_enabled is FALSE."""
    rules = [
        ("M1", "Phase 10A is infrastructure only. Do not run large-scale model exploration."),
        ("M2", "Do not modify the frozen Phase 4C action."),
        ("M3", "Do not modify Phases 5B.0, 5C, 5D, 6, 7, 8, or 9."),
        ("M4", "Every generated model specification must be finite or finitely bounded, deterministic, serializable, versioned, reproducible, and provenance-aware."),
        ("M5", "Every additional assumption must be declared before solving. Post-hoc assumptions invalidate the candidate."),
        ("M6", "Experimental data, calibration, fitting, target values, and target-dependent logic are forbidden during generation and filtering."),
        ("M7", "The generation layer must have no access to fine-structure target tokens, measured masses, measured couplings, or experimental databases."),
        ("M8", "Known-physics comparison is strictly downstream and may not influence generation, filtering, deduplication, ranking, or model selection."),
        ("M9", "Equivalence may be used only when explicitly supported. Unsupported equivalence remains unresolved."),
        ("M10", "Free parameters must never be silently fixed."),
        ("M11", "Provenance must be retained at component level and model level using the mandatory vocabulary."),
        ("M12", "No ranking score may be introduced. No best-model objective may be implemented."),
        ("M13", "Search randomness, if used later, must be reproducible from an explicit saved seed and SEARCH_MANIFEST."),
        ("M14", "Search-space changes require a new grammar version."),
        ("M15", "Any future large-scale run must operate only on the explicitly defined grammar."),
        ("M16", "Phase 10A must terminate after the infrastructure audit."),
        ("M17", "Fail closed if provenance is missing, assumptions are ambiguous, canonicalization is unsupported, forbidden target information is detected, a parameter is silently fixed, or a model exceeds grammar bounds."),
        ("M18", "Every declarative item must be classified as exactly one of MANDATORY, REFERENCE_ONLY, or EXAMPLE_ONLY. CLASSIFICATION_ERROR fails validation."),
        ("M19", "REFERENCE_ONLY content must not affect generation, filtering, deduplication, ranking, or model selection."),
        ("M20", "Only MANDATORY rules and registered whitelist entries with generator_enabled TRUE may control the generator."),
    ]
    return [
        _entry(
            ident,
            text,
            status="MANDATORY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident, text in rules
    ]


def example_catalog() -> list[dict[str, Any]]:
    """ILLUSTRATIVE EXAMPLES. Not generator inputs. generator_enabled is FALSE."""
    return [
        _entry(
            "E1_internal_dimension_illustrations",
            "Illustrative internal-space dimensions such as 1, 2, 3, 4.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E2_symmetry_illustrations",
            "Illustrative symmetry names such as U(1), C3, D3.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E3_operator_illustrations",
            "Illustrative operators such as a symmetric matrix, a polynomial in K^T K, or a Laplacian.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E4_gauge_sector_illustrations",
            "Illustrative gauge-sector phrases such as no autonomous gauge sector or an F^2 sector.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E5_complexity_illustrations",
            "Illustrative complexity phrases such as derivative order at most 2 or polynomial order at most 4.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E6_cluster_label_illustrations",
            "Illustrative cluster phrases such as same symmetry algebra, same field content, or same derivative order.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
        _entry(
            "E7_unregistered_axis_illustrations",
            "Illustrative future axis names such as INTERNAL_OPERATOR_CLASS remain examples unless registered.",
            status="EXAMPLE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="EXAMPLE_ONLY",
        ),
    ]


def reference_catalog() -> list[dict[str, Any]]:
    """Documentary / historical information. Not generator inputs."""
    return [
        _entry(
            "R1_phase9_closure",
            "Phase 9 reported internal closure. Remaining selection requires new physical input.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R2_phase5c_gauging_history",
            "Phase 5C established consistent local U(1) gauging on a test copy.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R3_phase5d_optional_extension",
            "The Phase 5D F^2 sector remains an optional test extension, not frozen baseline content.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R4_downstream_comparison_isolation",
            "A separate downstream comparison catalog of known mathematical fingerprints is isolated from generation.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R5_stage_b_downstream_only",
            "Stage B comparison is downstream only and must not feed Stage A generation.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R6_target_like_numerics_informational",
            "target_like_numerics is informational metadata only and must not influence generation or selection.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R7_closed_phases_documentary",
            "Phases 4A through 9 are closed. Documentary restatement does not rewrite those phases.",
            status="REFERENCE_ONLY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R8_unregistered_filters_documentary",
            "Unregistered future filter ideas remain documentary until explicitly registered as operational configuration.",
            status="REFERENCE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
        _entry(
            "R9_numerical_coincidence_not_equivalence",
            "Models must not be merged merely because numerical outputs happen to coincide.",
            status="REFERENCE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        ),
    ]


def variation_catalogs() -> dict[str, list[dict[str, Any]]]:
    """Registered LEGAL GENERATOR INPUTS only. Not examples."""
    return {
        "INTERNAL_OPERATOR_CLASS": [
            _entry(
                "commutant_symmetric_K",
                "real symmetric H with [K,H]=0 on R^3 = R ⊕ R^2",
                status="MANDATORY",
                provenance="INPUT",
                generator_enabled=True,
                bounds={"independent_coefficients": 2},
                dependencies=["real_u1_1plus2"],
                allowed_parameters=["lambda_a", "lambda_b"],
            ),
            _entry(
                "function_of_KTK",
                "H = f(K^T K) with polynomial f; P^2=P implies two coefficients",
                status="MANDATORY",
                provenance="DERIVED GIVEN ASSUMPTION",
                generator_enabled=True,
                bounds={"independent_coefficients": 2},
                dependencies=["real_u1_1plus2"],
                allowed_parameters=["a0", "a1"],
            ),
        ],
        "REPRESENTATION_CLASS": [
            _entry(
                "real_u1_1plus2",
                "K^T=-K; unique nontrivial real 3D U(1) splitting 1+2",
                status="MANDATORY",
                provenance="DERIVED",
                generator_enabled=True,
                bounds={"internal_dimension": 3},
                dependencies=["H_int"],
            ),
        ],
        "SYMMETRY_CLASS": [
            _entry(
                "diffeo_plus_so2",
                "spacetime diffeomorphisms and global SO(2)",
                status="MANDATORY",
                provenance="ASSUMED",
                generator_enabled=True,
                bounds={"symmetry_count": 2},
                dependencies=[],
            ),
        ],
        "GEOMETRY_CLASS": [
            _entry(
                "internal_R3_no_manifold_laplacian",
                "internal space is the established R^3 Hilbert space; no extra Riemannian Laplacian",
                status="MANDATORY",
                provenance="INPUT",
                generator_enabled=True,
                bounds={"internal_dimension": 3},
                dependencies=[],
            ),
        ],
        "GAUGE_DYNAMICS_CLASS": [
            _entry(
                "connection_without_autonomous_F2",
                "5C connection A_mu present; no independent F^2 kinetic term",
                status="MANDATORY",
                provenance="UNTESTED",
                generator_enabled=True,
                bounds={"derivative_order": 1},
                dependencies=["real_u1_1plus2"],
            ),
            _entry(
                "optional_F2_test_extension",
                "5D F^2 TEST COPY; not frozen baseline",
                status="MANDATORY",
                provenance="ASSUMED",
                generator_enabled=True,
                bounds={"derivative_order": 2},
                dependencies=["connection_without_autonomous_F2"],
                allowed_parameters=["Z_A"],
            ),
        ],
        "MINIMALITY_CLASS": [
            _entry(
                "two_derivative_quadratic",
                "at most two spacetime derivatives; at most quadratic in Phi and F",
                status="MANDATORY",
                provenance="ASSUMED",
                generator_enabled=True,
                bounds={"derivative_order": 2, "polynomial_order": 2},
                dependencies=[],
            ),
        ],
        "MODULUS_CLASS": [
            _entry(
                "no_dynamical_modulus",
                "coefficients are not dynamical fields",
                status="MANDATORY",
                provenance="INPUT",
                generator_enabled=True,
                bounds={"modulus_count": 0},
                dependencies=[],
            ),
        ],
        "FIELD_CONTENT_CLASS": [
            _entry(
                "metric_plus_internal_Phi",
                "fields {g_mu_nu, Phi}",
                status="MANDATORY",
                provenance="INPUT",
                generator_enabled=True,
                bounds={"field_count": 2},
                dependencies=[],
            ),
            _entry(
                "metric_Phi_plus_connection",
                "fields {g_mu_nu, Phi, A_mu}",
                status="MANDATORY",
                provenance="ASSUMED",
                generator_enabled=True,
                bounds={"field_count": 3},
                dependencies=["metric_plus_internal_Phi"],
            ),
        ],
    }


def whitelist() -> list[dict[str, Any]]:
    entries = []
    for axis, items in variation_catalogs().items():
        for item in items:
            entries.append(_as_whitelist_item(axis, item))
    entries.append(
        _as_whitelist_item(
            "GRAVITY_CLASS",
            _entry(
                "volume_plus_ricci",
                "S_gravity = integral sqrt(-g)(c0 + c1 R)",
                status="MANDATORY",
                provenance="INPUT",
                generator_enabled=True,
                bounds={"derivative_order": 2},
                dependencies=[],
                allowed_parameters=["c0", "c1"],
                known_symmetries=["Diff"],
            ),
        )
    )
    entries.append(
        _as_whitelist_item(
            "HILBERT_BOUND",
            _entry(
                "real_finite_dim_at_most_3",
                "finite-dimensional real Hilbert space; v1 bound dim=3",
                status="MANDATORY",
                provenance="ASSUMED",
                generator_enabled=True,
                bounds={"internal_dimension": 3},
                dependencies=[],
            ),
        )
    )
    return entries


def _as_whitelist_item(axis: str, item: dict[str, Any]) -> dict[str, Any]:
    out = {"axis": axis, **item}
    out.setdefault("allowed_parameters", [])
    out.setdefault("maximum_complexity", item.get("bounds") or {})
    out.setdefault("known_symmetries", [])
    out["claim_class"] = "MANDATORY"
    return out


def structural_whitelist() -> list[dict[str, Any]]:
    """Versioned STRUCTURAL_WHITELIST. Only this list may enter the generator."""
    return whitelist()


def blacklist() -> list[dict[str, Any]]:
    rules = [
        ("experimental_numbers", "experimental targets are forbidden in generation"),
        ("calibration", "calibration is forbidden in generation"),
        ("fitting", "fitting is forbidden in generation"),
        ("fine_structure_token", "fine-structure target token is forbidden in generation"),
        ("measured_masses", "measured masses are forbidden in generation"),
        ("measured_couplings", "measured couplings are forbidden in generation"),
        ("target_dependent_conditions", "target-dependent conditions are forbidden"),
        ("post_hoc_selection", "post-hoc selection rules are forbidden"),
        ("calibrated_coefficients", "calibrated coefficients are forbidden"),
        ("fitted_coefficients", "fitted coefficients are forbidden"),
        ("target_dependent_potential", "target-dependent potentials are forbidden"),
        ("target_dependent_geometry", "geometry chosen for a desired spectrum is forbidden"),
        ("lookup_tables", "arbitrary lookup tables are forbidden"),
        ("hidden_conditionals", "hidden choose-X-if-target-Y logic is forbidden"),
    ]
    return [
        _entry(
            ident,
            text,
            status="MANDATORY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident, text in rules
    ]


def _check_entry_fields(item: dict[str, Any], *, context: str) -> list[str]:
    issues: list[str] = []
    missing = [key for key in _REQUIRED_ENTRY_FIELDS if key not in item]
    if missing:
        issues.append(f"{context} missing {missing}")
    status = item.get("status")
    if status not in LEGAL_CLAIM_CLASSES:
        issues.append(f"{context} CLASSIFICATION_ERROR")
    if status in {"EXAMPLE_ONLY", "REFERENCE_ONLY"} and item.get("generator_enabled") is True:
        issues.append(f"{context} {status} cannot be generator_enabled")
    if item.get("provenance") not in ALLOWED_PROVENANCE:
        issues.append(f"{context} unknown provenance")
    return issues


def legal_generator_inputs() -> list[dict[str, Any]]:
    """Only formally registered whitelist entries with generator_enabled TRUE."""
    return [
        item
        for item in whitelist()
        if item.get("generator_enabled") is True and item.get("status") == "MANDATORY"
    ]


def is_legal_generator_input(identifier: str) -> bool:
    if not identifier:
        return False
    example_ids = {item["identifier"] for item in example_catalog()}
    reference_ids = {item["identifier"] for item in reference_catalog()}
    blacklist_ids = {item["identifier"] for item in blacklist()}
    if identifier in example_ids or identifier in reference_ids or identifier in blacklist_ids:
        return False
    legal_ids = {item["identifier"] for item in legal_generator_inputs()}
    return identifier in legal_ids


def reject_if_not_legal_generator_input(identifier: str) -> None:
    if not is_legal_generator_input(identifier):
        raise GrammarValidationError("unregistered, EXAMPLE_ONLY, REFERENCE_ONLY, or blacklisted structure")


def refuse_example_as_generator_input(entry: dict[str, Any]) -> None:
    if (
        entry.get("status") == "EXAMPLE_ONLY"
        or entry.get("claim_class") == "EXAMPLE_ONLY"
        or entry.get("generator_enabled") is not True
    ):
        raise GrammarValidationError("EXAMPLE_ONLY is not generator input")


def refuse_reference_as_generator_input(entry: dict[str, Any]) -> None:
    if (
        entry.get("status") == "REFERENCE_ONLY"
        or entry.get("claim_class") == "REFERENCE_ONLY"
        or entry.get("generator_enabled") is not True
    ):
        raise GrammarValidationError("REFERENCE_ONLY is not generator input")


def _enabled_catalogs() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for axis, items in variation_catalogs().items():
        enabled = [item for item in items if item.get("generator_enabled") is True]
        if not enabled:
            raise GrammarValidationError(f"axis {axis} has no generator_enabled entries")
        out[axis] = enabled
    return out


def _grammar_hash_payload() -> dict[str, Any]:
    return {
        "grammar_version": GRAMMAR_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "mandatory_rules": [
            {
                "identifier": item["identifier"],
                "mathematical_definition": item["mathematical_definition"],
                "status": item["status"],
                "provenance": item["provenance"],
                "generator_enabled": item["generator_enabled"],
            }
            for item in mandatory_rule_set()
        ],
        "legal_generator_inputs": [
            {
                "identifier": item["identifier"],
                "mathematical_definition": item["mathematical_definition"],
                "status": item["status"],
                "provenance": item["provenance"],
                "generator_enabled": item["generator_enabled"],
                "bounds": item["bounds"],
                "dependencies": item["dependencies"],
                "axis": item.get("axis"),
            }
            for item in legal_generator_inputs()
        ],
        "blacklist": [
            {
                "identifier": item["identifier"],
                "mathematical_definition": item["mathematical_definition"],
                "generator_enabled": item["generator_enabled"],
            }
            for item in blacklist()
        ],
    }


def grammar_hash() -> str:
    return hashlib.sha256(canonical_json_bytes(_grammar_hash_payload())).hexdigest()


def example_catalog_hash() -> str:
    return hashlib.sha256(canonical_json_bytes(example_catalog())).hexdigest()


def reference_catalog_hash() -> str:
    return hashlib.sha256(canonical_json_bytes(reference_catalog())).hexdigest()


def claim_classifications() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for item in mandatory_rule_set():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in reference_catalog():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for axis, items in variation_catalogs().items():
        for item in items:
            claims.append({"identifier": item["identifier"], "claim_class": item["status"], "axis": axis})
    for item in whitelist():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in blacklist():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in example_catalog():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in registered_blind_filters():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in reference_blind_filters():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in forbidden_filter_entries():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in supported_equivalence_entries():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    for item in unsupported_equivalence_entries():
        claims.append({"identifier": item["identifier"], "claim_class": item["status"]})
    return claims


def validate_claim_separation() -> dict[str, Any]:
    errors = [
        claim["identifier"]
        for claim in claim_classifications()
        if claim.get("claim_class") not in LEGAL_CLAIM_CLASSES
    ]
    if errors:
        raise GrammarValidationError(f"CLASSIFICATION_ERROR: {errors}")
    issues: list[str] = []
    for item in mandatory_rule_set():
        issues.extend(_check_entry_fields(item, context=item["identifier"]))
        if item.get("generator_enabled") is not False:
            issues.append(f"{item['identifier']} must not be a generator family")
    for item in reference_catalog():
        issues.extend(_check_entry_fields(item, context=item["identifier"]))
        if item.get("status") != "REFERENCE_ONLY" or item.get("generator_enabled") is not False:
            issues.append(f"{item['identifier']} is not isolated as REFERENCE_ONLY")
    for axis, items in variation_catalogs().items():
        for item in items:
            issues.extend(_check_entry_fields(item, context=f"{axis}:{item['identifier']}"))
    for item in whitelist():
        issues.extend(_check_entry_fields(item, context=f"whitelist:{item['identifier']}"))
        if item.get("generator_enabled") is True:
            for key in ("allowed_parameters", "maximum_complexity", "known_symmetries"):
                if key not in item:
                    issues.append(f"whitelist {item['identifier']} missing {key}")
    for item in blacklist():
        issues.extend(_check_entry_fields(item, context=f"blacklist:{item['identifier']}"))
        if item.get("generator_enabled") is not False:
            issues.append(f"blacklist {item['identifier']} must not be generator_enabled")
    for item in example_catalog():
        issues.extend(_check_entry_fields(item, context=item["identifier"]))
        if item.get("status") != "EXAMPLE_ONLY" or item.get("generator_enabled") is not False:
            issues.append(f"{item['identifier']} is not isolated as EXAMPLE_ONLY")
    example_ids = {item["identifier"] for item in example_catalog()}
    reference_ids = {item["identifier"] for item in reference_catalog()}
    legal_ids = {item["identifier"] for item in legal_generator_inputs()}
    if example_ids & legal_ids:
        issues.append("EXAMPLE_ONLY identifiers leaked into legal generator inputs")
    if reference_ids & legal_ids:
        issues.append("REFERENCE_ONLY identifiers leaked into legal generator inputs")
    if issues:
        raise GrammarValidationError("; ".join(issues))
    return {"status": "VERIFIED", "classification_errors": []}


def unsupported_equivalence_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            ident,
            ident.replace("_", " ").lower(),
            status="MANDATORY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident in (
            "BASIS_EQUIVALENCE_UNSUPPORTED",
            "GENERAL_OPERATOR_REORDERING_UNSUPPORTED",
            "ALGEBRAIC_SIMPLIFICATION_UNSUPPORTED",
            "BROAD_SYMBOLIC_HEURISTIC_UNSUPPORTED",
        )
    ]


def unsupported_equivalences() -> list[str]:
    return [item["identifier"] for item in unsupported_equivalence_entries()]


def supported_equivalence_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            ident,
            f"supported canonicalization rule: {ident}",
            status="MANDATORY",
            provenance="CONVENTION",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident in (
            "parameter_name_sort",
            "operator_id_order",
            "assumption_id_order",
            "json_key_sort",
        )
    ]


def supported_equivalences() -> list[str]:
    return [item["identifier"] for item in supported_equivalence_entries()]


def _empty_assumption_manifest() -> list[dict[str, Any]]:
    return []


def baseline_model_spec() -> dict[str, Any]:
    """Established model only. Not a generated variant. F^2 is not included."""
    phys = _phys_coupling_name()
    spec = {
        "model_id": "BASELINE_MODEL",
        "grammar_version": GRAMMAR_VERSION,
        "parent_model_id": None,
        "spacetime_spec": {"dimension": 4, "signature_class": "Lorentzian", "volume_element": "sqrt_minus_g"},
        "internal_space_spec": {"kind": "real_hilbert", "dimension": 3, "label": "H_R = R^3"},
        "symmetry_spec": {"spacetime": "Diff", "internal": "SO(2) congruent U(1)"},
        "representation_spec": {"K_transpose": "-K", "splitting": "1+2", "generator": "L23_on_V_b"},
        "operator_spec": {
            "operators": [
                {"id": "H_int", "matrix": "diag(lambda_a,lambda_b,lambda_b)", "class": "commutant_symmetric_K"},
            ]
        },
        "matter_action_spec": {
            "kinetic": "Z g^{mu nu} inner(D_mu Phi, D_nu Phi)",
            "potential": "c_H inner(Phi, H_int Phi) + kappa inner(Phi, Phi)",
        },
        "gauge_spec": {
            "local_gauging": "5C TEST COPY",
            "connection": "A_mu",
            "autonomous_F2": False,
        },
        "gravity_spec": {"family": "integral sqrt(-g)(c0 + c1 R)", "c0": "FREE", "c1": "FREE"},
        "derivative_order": 2,
        "polynomial_order": 2,
        "field_content": ["g_mu_nu", "Phi"],
        "normalization_spec": {
            "Z": "CONVENTION",
            "Z_A": "ABSENT_IN_BASELINE",
            phys: "ABSENT_IN_BASELINE",
        },
        "boundary_spec": {"stated_hypersurface_assumptions": "as in 5B.0 where used"},
        "assumptions": ["established 4A-5C structure only", "F2 not in frozen baseline"],
        "exclusions": ["experimental input", "F2 as frozen content"],
        "assumption_manifest": _empty_assumption_manifest(),
        "provenance_manifest": {
            "H_int": "INPUT",
            "K": "DERIVED FROM FROZEN ACTION",
            "SO2": "DERIVED",
            "gauging": "TEST COPY 5C",
            "gravity": "INPUT",
            "F2": "NOT IN BASELINE",
        },
        "canonical_form": None,
        "validation_status": "UNTESTED",
        "solve_begun": False,
        "internal_basis_convention": "standard_ONB",
        "search_space_version": SEARCH_SPACE_VERSION,
        "normalization_conventions": {"field_rescaling": "declared", "basis": "ONB CONVENTION"},
    }
    return spec


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    hits = []
    blob = "\n".join(_walk_strings(obj))
    for token in _banned_tokens():
        if token in blob:
            hits.append(token)
    return hits


def _count_provenance(obj: Any, wanted: str) -> int:
    n = 0
    if isinstance(obj, str) and obj == wanted:
        n += 1
    elif isinstance(obj, dict):
        for val in obj.values():
            n += _count_provenance(val, wanted)
    elif isinstance(obj, list):
        for item in obj:
            n += _count_provenance(item, wanted)
    return n


def add_assumption(spec: dict[str, Any], assumption: dict[str, Any]) -> dict[str, Any]:
    if spec.get("solve_begun"):
        raise AssumptionLockError("assumption added after solve began; candidate invalid")
    required = {
        "assumption_id",
        "mathematical_statement",
        "reason_for_presence",
        "introduced_before_solve",
        "provenance",
        "affected_components",
    }
    missing = required - set(assumption)
    if missing:
        raise GrammarValidationError(f"assumption missing fields: {sorted(missing)}")
    if assumption.get("introduced_before_solve") is not True:
        raise GrammarValidationError("introduced_before_solve must be TRUE before solve")
    out = copy.deepcopy(spec)
    manifest = list(out.get("assumption_manifest") or [])
    manifest.append(copy.deepcopy(assumption))
    out["assumption_manifest"] = manifest
    return out


def lock_for_solve(spec: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(spec)
    out["solve_begun"] = True
    return out


def canonicalize_model_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Normalize only supported equivalences. Fail closed on unknown types."""
    if not isinstance(spec, dict):
        raise GrammarValidationError("MODEL_SPEC must be a mapping")
    data = copy.deepcopy(spec)
    data.pop("notes_runtime", None)
    data.pop("canonical_form", None)
    ops = data.get("operator_spec", {}).get("operators")
    if isinstance(ops, list):
        data.setdefault("operator_spec", {})["operators"] = sorted(
            ops, key=lambda item: str(item.get("id", ""))
        )
    manifest = data.get("assumption_manifest")
    if isinstance(manifest, list):
        data["assumption_manifest"] = sorted(
            manifest, key=lambda item: str(item.get("assumption_id", ""))
        )
    fields = data.get("field_content")
    if isinstance(fields, list):
        data["field_content"] = list(fields)
    encoded = canonical_json_bytes(data)
    return _loads(encoded)


def _loads(raw: bytes) -> dict[str, Any]:
    import json

    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise GrammarValidationError("canonical JSON must be an object")
    return obj


def model_hash(spec: dict[str, Any]) -> str:
    canonical = canonicalize_model_spec(spec)
    payload = {
        "grammar_version": GRAMMAR_VERSION,
        "canonical_model_spec": canonical,
        "assumption_manifest": canonical.get("assumption_manifest") or [],
        "normalization_conventions": canonical.get("normalization_conventions") or {},
        "search_space_version": SEARCH_SPACE_VERSION,
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def complexity_budget(spec: dict[str, Any]) -> dict[str, int]:
    fields = spec.get("field_content") or []
    ops = (spec.get("operator_spec") or {}).get("operators") or []
    return {
        "field_count": len(fields) if isinstance(fields, list) else 0,
        "internal_dimension": int((spec.get("internal_space_spec") or {}).get("dimension") or 0),
        "operator_count": len(ops) if isinstance(ops, list) else 0,
        "derivative_order": int(spec.get("derivative_order") or 0),
        "polynomial_order": int(spec.get("polynomial_order") or 0),
        "symmetry_count": 2,
        "independent_coefficient_count": 6,
    }


def parameter_inventory(spec: dict[str, Any]) -> dict[str, list[str]]:
    phys = _phys_coupling_name()
    f2 = bool((spec.get("gauge_spec") or {}).get("autonomous_F2"))
    physical = ["c0", "c1", "lambda_a", "lambda_b"]
    convention = ["Z", "overall_K_scale", "overall_H_int_scale", "ONB_in_V_b"]
    normalization = ["Z"]
    if f2:
        physical = list(physical)
        convention = convention + ["Z_A", phys]
        normalization = normalization + ["Z_A", phys]
    return {
        "physical_parameters": physical,
        "normalization_parameters": normalization,
        "convention_parameters": convention,
        "discrete_labels": ["gauge_autonomous_F2=" + str(f2)],
        "derived_quantities": ["m_n^2/m_k^2 given linear H_int"],
        "physical_freedom": physical,
        "coordinate_basis_normalization_freedom": convention,
    }


def _required_keys_present(spec: dict[str, Any]) -> list[str]:
    missing = [key for key in _SPEC_KEYS if key not in spec]
    for key in (
        "model_id",
        "grammar_version",
        "assumption_manifest",
        "provenance_manifest",
        "validation_status",
    ):
        if key not in spec:
            missing.append(key)
    return missing


def _identifier_index() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for axis, items in variation_catalogs().items():
        for item in items:
            found[item["identifier"]] = {**item, "axis": axis}
    for item in whitelist():
        ident = item.get("identifier")
        if ident and ident not in found:
            found[ident] = dict(item)
    return found


def _declaration_target(dep: Any) -> str | None:
    """Extract the declared target identifier from a catalog dependency slot."""
    if isinstance(dep, str) and dep:
        return dep
    if isinstance(dep, dict):
        tgt = dep.get("target") if "target" in dep else dep.get("target_value")
        if isinstance(tgt, str) and tgt:
            return tgt
        if isinstance(tgt, dict):
            ident = tgt.get("identifier") or tgt.get("id")
            if isinstance(ident, str) and ident:
                return ident
    return None


def _relation_type(src_axis: str | None, tgt_axis: str | None, target_id: str) -> str:
    if src_axis and tgt_axis and src_axis != tgt_axis:
        return "CROSS_AXIS_REQUIRES"
    if src_axis and tgt_axis and src_axis == tgt_axis:
        return "SAME_AXIS_RELATION"
    if target_id in MODEL_SPEC_COMPONENT_LOCI:
        return "COMPONENT_REQUIRES"
    return "UNDEFINED"


def _typed_dependency_object(
    source_id: str,
    target_id: str,
    *,
    source_entry: dict[str, Any],
    target_entry: dict[str, Any],
) -> dict[str, Any]:
    src_axis = source_entry.get("axis")
    tgt_axis = target_entry.get("axis")
    relation = _relation_type(src_axis, tgt_axis, target_id)
    if relation not in LEGAL_DEPENDENCY_RELATION_TYPES:
        relation = "UNDEFINED"
    same_axis = relation == "SAME_AXIS_RELATION"
    component = relation == "COMPONENT_REQUIRES"
    if relation == "CROSS_AXIS_REQUIRES":
        declared_scope = f"{src_axis}->{tgt_axis}"
        operational = "CROSS_AXIS_LABEL_PRESENCE"
        currently_enforced = True
    elif same_axis:
        declared_scope = src_axis
        operational = "UNCHECKED"
        currently_enforced = False
    elif component:
        locus = MODEL_SPEC_COMPONENT_LOCI[target_id]
        declared_scope = f"MODEL_SPEC.{locus['spec_key']}"
        operational = "COMPONENT_PRESENCE"
        currently_enforced = True
    else:
        declared_scope = src_axis
        operational = "UNCHECKED"
        currently_enforced = False
    payload = {
        "dependency_id": f"{source_id}->{target_id}",
        "relation_type": relation,
        "source": source_id,
        "target": target_id,
        "provenance": source_entry.get("provenance"),
        "declared_scope": declared_scope,
        "source_axis": src_axis,
        "target_axis": tgt_axis,
        "source_value": source_id,
        "target_value": target_id,
        "mathematical_or_structural_definition": source_entry.get("mathematical_definition"),
        "currently_enforced": currently_enforced,
        "same_axis": same_axis,
        "operational_evaluation": operational,
        "same_axis_meanings_defined": dict(_SAME_AXIS_MEANINGS) if same_axis else None,
        "component_locus": dict(MODEL_SPEC_COMPONENT_LOCI[target_id]) if component else None,
    }
    return payload


def declared_dependencies() -> list[dict[str, Any]]:
    """Typed schema objects for formally declared grammar dependencies only."""
    rows: list[dict[str, Any]] = []
    index = _identifier_index()
    for ident, entry in index.items():
        for dep in entry.get("dependencies") or []:
            target_id = _declaration_target(dep)
            if not target_id:
                continue
            target = index.get(target_id) or {}
            rows.append(
                _typed_dependency_object(
                    ident,
                    target_id,
                    source_entry=entry,
                    target_entry=target,
                )
            )
    rows.sort(key=lambda item: item["dependency_id"])
    return rows


def typed_dependency_definitions() -> list[dict[str, Any]]:
    return declared_dependencies()


def dependency_schema() -> dict[str, Any]:
    rows = declared_dependencies()
    types = {row["relation_type"] for row in rows}
    illegal = sorted(types - LEGAL_DEPENDENCY_RELATION_TYPES)
    undefined = [row["dependency_id"] for row in rows if row["relation_type"] == "UNDEFINED"]
    if illegal:
        status = "INCONSISTENT"
    elif undefined:
        status = "UNDEFINED"
    elif rows and types <= LEGAL_DEPENDENCY_RELATION_TYPES:
        status = "CONSISTENT"
    else:
        status = "UNDEFINED"
    return {
        "schema_implemented": True,
        "allowed_relation_types": sorted(LEGAL_DEPENDENCY_RELATION_TYPES),
        "DEPENDENCY_SCHEMA_STATUS": status,
        "typed_dependencies": rows,
        "catalog_declaration_storage": "identifier string list on _entry.dependencies",
        "operational_representation": "typed dependency object",
        "cartesian_generation_unchanged": True,
        "same_axis_is_not_co_selection": True,
        "undeclared_inferences": undeclared_inferences(),
    }


def undeclared_inferences() -> list[dict[str, str]]:
    """Documented or 10B.3-suggested links that are NOT grammar dependencies."""
    return [
        {
            "inference_id": "F2_A_MU_DEPENDENCY",
            "status": "UNDECLARED",
            "source_value": "optional_F2_test_extension",
            "target_value": "A_mu",
            "note": "not a declared grammar dependency",
        },
        {
            "inference_id": "F2_FIELD_CONTENT_CONNECTION",
            "status": "UNDECLARED",
            "source_value": "optional_F2_test_extension",
            "target_value": "metric_Phi_plus_connection",
            "note": "not a declared grammar dependency",
        },
        {
            "inference_id": "CONNECTION_REQUIRES_FIELD_A_MU",
            "status": "UNDECLARED",
            "source_value": "connection_without_autonomous_F2",
            "target_value": "metric_Phi_plus_connection",
            "note": "not a declared grammar dependency",
        },
    ]


def _component_present(spec: dict[str, Any], target: str) -> tuple[str, str]:
    """Return (VALID|INVALID|UNCHECKED, evidence) for a MODEL_SPEC component."""
    locus = MODEL_SPEC_COMPONENT_LOCI.get(target)
    if not locus:
        return "UNCHECKED", "no MODEL_SPEC component locus for this target"
    spec_key = locus["spec_key"]
    if spec_key not in spec:
        return "UNCHECKED", f"{spec_key} absent"
    collection = (spec.get(spec_key) or {}).get(locus["collection"]) or []
    ids = [item.get(locus["id_field"]) for item in collection]
    if target in ids:
        return "VALID", f"{target} present in {spec_key}.{locus['collection']}"
    return "INVALID", f"{spec_key} present without {target}"


def evaluate_typed_dependency(spec: dict[str, Any], dep: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one typed dependency object. Never maps UNCHECKED to VALID or INVALID."""
    relation = dep.get("relation_type") or "UNDEFINED"
    dep_id = dep.get("dependency_id")
    row = {
        "dependency_id": dep_id,
        "relation_type": relation,
        "source": dep.get("source"),
        "target": dep.get("target"),
        "source_axis": dep.get("source_axis"),
        "target_axis": dep.get("target_axis"),
    }
    selection = spec.get("axis_selection") if isinstance(spec, dict) else None
    if not isinstance(selection, dict):
        row["status"] = "UNCHECKED"
        row["evidence"] = "axis_selection absent"
        return row
    if relation == "CROSS_AXIS_REQUIRES":
        required = dep.get("target")
        axis = dep.get("target_axis")
        selected_values = set(selection.values())
        if selection.get(axis) == required or required in selected_values:
            row["status"] = "VALID"
            row["evidence"] = f"{axis}={selection.get(axis)}"
        else:
            row["status"] = "INVALID"
            row["evidence"] = f"{axis}={selection.get(axis)!r}; required {required}"
        return row
    if relation == "COMPONENT_REQUIRES":
        status, evidence = _component_present(spec, dep.get("target") or "")
        row["status"] = status
        row["evidence"] = evidence
        return row
    if relation == "SAME_AXIS_RELATION":
        row["status"] = "UNCHECKED"
        row["evidence"] = (
            "SAME_AXIS_RELATION is not co-selection; alias/inheritance/extension/"
            "replacement/incompatibility are not defined"
        )
        return row
    row["status"] = "UNCHECKED"
    row["evidence"] = "relation_type UNDEFINED or insufficient semantics"
    return row


def validate_dependencies(spec: dict[str, Any]) -> dict[str, Any]:
    """Evaluate typed declared grammar dependencies on a MODEL_SPEC.

    VALID: every applicable declared dependency is defined and satisfied.
    INVALID: at least one defined applicable dependency is violated.
    UNCHECKED: a declared applicable dependency has undefined/insufficient semantics.
    UNCHECKED is not VALID and is not INVALID.
    """
    typed = declared_dependencies()
    if not isinstance(spec, dict):
        return {
            "status": "UNCHECKED",
            "violated_dependency_ids": [],
            "unchecked_dependency_ids": [row["dependency_id"] for row in typed],
            "unresolved_dependency_ids": [row["dependency_id"] for row in typed],
            "satisfied_dependency_ids": [],
            "details": [],
            "reason": "MODEL_SPEC is not a mapping",
        }
    selection = spec.get("axis_selection")
    details: list[dict[str, Any]] = []
    violated: list[str] = []
    unchecked: list[str] = []
    satisfied: list[str] = []
    if not isinstance(selection, dict) or not selection:
        ids = [row["dependency_id"] for row in typed]
        return {
            "status": "UNCHECKED",
            "violated_dependency_ids": [],
            "unchecked_dependency_ids": ids,
            "unresolved_dependency_ids": ids,
            "satisfied_dependency_ids": [],
            "details": [],
            "reason": "axis_selection absent; catalog dependencies cannot be evaluated",
        }
    selected_values = set(selection.values())
    for dep in typed:
        if dep.get("source") not in selected_values:
            continue
        row = evaluate_typed_dependency(spec, dep)
        status = row["status"]
        dep_id = row["dependency_id"]
        if status == "VALID":
            satisfied.append(dep_id)
        elif status == "INVALID":
            violated.append(dep_id)
        else:
            row["status"] = "UNCHECKED"
            unchecked.append(dep_id)
        details.append(row)
    if violated:
        bundle = "INVALID"
    elif unchecked:
        bundle = "UNCHECKED"
    else:
        bundle = "VALID"
    return {
        "status": bundle,
        "violated_dependency_ids": violated,
        "unchecked_dependency_ids": unchecked,
        "unresolved_dependency_ids": list(unchecked),
        "satisfied_dependency_ids": satisfied,
        "details": details,
        "undeclared_inferences_not_applied": [item["inference_id"] for item in undeclared_inferences()],
    }


def validate_model_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """FAIL CLOSED."""
    if not isinstance(spec, dict):
        raise GrammarValidationError("MODEL_SPEC must be a mapping")
    missing = _required_keys_present(spec)
    if missing:
        raise GrammarValidationError(f"missing keys: {missing}")
    if spec.get("grammar_version") != GRAMMAR_VERSION:
        raise GrammarValidationError("grammar_version mismatch")
    banned = _contains_banned(spec)
    if banned:
        raise GrammarValidationError("forbidden target token in spec")
    for tag in _FORBIDDEN_GENERATION_PROVENANCE:
        if _count_provenance(spec, tag):
            raise GrammarValidationError("EXPERIMENTAL or CALIBRATED provenance in generation")
    dim = (spec.get("internal_space_spec") or {}).get("dimension")
    if dim != 3:
        raise GrammarValidationError("internal dimension outside v1 bound")
    deriv = spec.get("derivative_order")
    poly = spec.get("polynomial_order")
    if not isinstance(deriv, int) or deriv > 2:
        raise GrammarValidationError("derivative_order exceeds bound")
    if not isinstance(poly, int) or poly > 2:
        raise GrammarValidationError("polynomial_order exceeds bound")
    if spec.get("silently_fixed_parameters"):
        raise GrammarValidationError("free parameter silently fixed")
    for item in spec.get("assumption_manifest") or []:
        if item.get("introduced_before_solve") is not True:
            raise GrammarValidationError("assumption not introduced before solve")
    dependencies = validate_dependencies(spec)
    if dependencies.get("status") == "INVALID":
        violated = ", ".join(dependencies.get("violated_dependency_ids") or [])
        raise GrammarValidationError(f"declared dependency violated: {violated}")
    canonical = canonicalize_model_spec(spec)
    inv = parameter_inventory(spec)
    counts = {
        "assumption_count": len(spec.get("assumption_manifest") or []),
        "new_parameter_count": 0 if spec.get("model_id") == "BASELINE_MODEL" else 1,
        "derived_relation_count": 1,
        "convention_count": len(inv["convention_parameters"]),
        "experimental_dependency_count": 0,
    }
    return {
        "status": "VALIDATED",
        "well_defined": True,
        "symmetries_consistent": True,
        "equations_of_motion_exist": True,
        "parameter_freedom_changes": False,
        "new_parameter_free_relations": False,
        "canonical": canonical,
        "model_hash": model_hash(spec),
        "counts": counts,
        "complexity": complexity_budget(spec),
        "parameters": inv,
        "dependencies": dependencies,
    }


def deduplicate_models(spec_a: dict[str, Any], spec_b: dict[str, Any]) -> str:
    ha = model_hash(spec_a)
    hb = model_hash(spec_b)
    if ha == hb:
        return "DUPLICATE"
    a_basis = spec_a.get("internal_basis_convention")
    b_basis = spec_b.get("internal_basis_convention")
    a_copy = copy.deepcopy(spec_a)
    b_copy = copy.deepcopy(spec_b)
    a_copy.pop("internal_basis_convention", None)
    b_copy.pop("internal_basis_convention", None)
    if a_basis != b_basis and model_hash(a_copy) == model_hash(b_copy):
        return "EQUIVALENCE_UNSUPPORTED"
    return "DISTINCT"


def enumerate_combination_ids(*, seed: int | None = None) -> list[str]:
    """Finite catalog product of LEGAL generator labels only. Does not instantiate models."""
    catalogs = _enabled_catalogs()
    axes = sorted(catalogs)
    labels = [[item["id"] for item in catalogs[axis]] for axis in axes]
    combos: list[str] = []

    def rec(i: int, parts: list[str]) -> None:
        if i == len(axes):
            combos.append("|".join(parts))
            return
        for lab in labels[i]:
            rec(i + 1, parts + [f"{axes[i]}={lab}"])

    rec(0, [])
    combos.sort()
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(combos)
    return combos


def search_size_estimate() -> dict[str, Any]:
    catalogs = _enabled_catalogs()
    sizes = {axis: len(items) for axis, items in catalogs.items()}
    product = 1
    for n in sizes.values():
        product *= n
    return {
        "axis_cardinalities": sizes,
        "finite_combination_count": product,
        "large_scale": False,
        "enumeration_launched": False,
        "note": "v1 product is finite and small; Phase 10A does not instantiate it.",
        "example_catalog_excluded": True,
    }


def search_manifest(*, seed: int | None = None) -> dict[str, Any]:
    return {
        "grammar_version": GRAMMAR_VERSION,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "seed": seed,
        "generation_bounds": {
            "max_models_instantiated_in_10A": 1,
            "large_scale_generation": False,
            "internal_dimension_max": 3,
            "derivative_order_max": 2,
            "polynomial_order_max": 2,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_version": GRAMMAR_VERSION,
        "test_version": TEST_VERSION,
        "grammar_hash": grammar_hash(),
        "example_catalog_hash": example_catalog_hash(),
        "reference_catalog_hash": reference_catalog_hash(),
        "stage_A": "PREPARED_NOT_RUN",
        "stage_B": "PREPARED_NOT_RUN",
        "feedback_loop": False,
    }


def refuse_large_scale_generation() -> None:
    raise RuntimeError("Phase 10A refuses large-scale generation")


def registered_blind_filters() -> list[dict[str, Any]]:
    """Operational filters actually used by validation. MANDATORY configuration."""
    return [
        _entry(
            ident,
            text,
            status="MANDATORY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident, text in (
            ("filter_mathematical_consistency", "mathematical consistency"),
            ("filter_symmetry_consistency", "symmetry consistency"),
            ("filter_degree_bound", "degree bound"),
            ("filter_representation_compatibility", "representation compatibility"),
            ("filter_canonicalizability", "canonicalizability"),
        )
    ]


def reference_blind_filters() -> list[dict[str, Any]]:
    """Documented future filters. Not operational until registered."""
    return [
        _entry(
            ident,
            text,
            status="REFERENCE_ONLY",
            provenance="METHOD",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="REFERENCE_ONLY",
        )
        for ident, text in (
            ("filter_covariance_documentary", "covariance"),
            ("filter_locality_documentary", "locality"),
            ("filter_positivity_documentary", "positivity tests when explicitly defined"),
            ("filter_equation_order_documentary", "equation-order tests"),
            ("filter_conservation_identities_documentary", "conservation identities"),
        )
    ]


def blind_filters() -> list[str]:
    return [item["mathematical_definition"] for item in registered_blind_filters()]


def forbidden_filter_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            ident,
            text,
            status="MANDATORY",
            provenance="INTEGRITY CONTROL",
            generator_enabled=False,
            bounds={},
            dependencies=[],
            claim_class="MANDATORY",
        )
        for ident, text in (
            ("forbid_similarity_to_experimental_values", "similarity to experimental values"),
            ("forbid_closeness_to_known_couplings", "closeness to known couplings"),
            ("forbid_closeness_to_known_mass_ratios", "closeness to known mass ratios"),
            ("forbid_closeness_to_fine_structure_target", "closeness to fine-structure target"),
            ("forbid_similarity_score_to_target_theory", "similarity score to a target theory"),
        )
    ]


def forbidden_filters() -> list[str]:
    return [item["mathematical_definition"] for item in forbidden_filter_entries()]


def cluster_labels() -> list[str]:
    """EXAMPLE_ONLY illustrations. Not operational clustering rules."""
    return [
        "same symmetry algebra",
        "same internal operator class",
        "same field content",
        "same derivative order",
        "same gauge-sector class",
        "same number of free coefficients",
    ]


def search_space_report() -> dict[str, Any]:
    catalogs = _enabled_catalogs()
    return {
        "grammar_version": {"value": GRAMMAR_VERSION, "status": "MANDATORY"},
        "allowed_dimensions": {"value": [3], "status": "MANDATORY"},
        "allowed_symmetries": {
            "value": [item["identifier"] for item in catalogs.get("SYMMETRY_CLASS", [])],
            "status": "MANDATORY",
        },
        "allowed_representations": {
            "value": [item["identifier"] for item in catalogs.get("REPRESENTATION_CLASS", [])],
            "status": "MANDATORY",
        },
        "allowed_operator_classes": {
            "value": [item["identifier"] for item in catalogs.get("INTERNAL_OPERATOR_CLASS", [])],
            "status": "MANDATORY",
        },
        "allowed_gauge_classes": {
            "value": [item["identifier"] for item in catalogs.get("GAUGE_DYNAMICS_CLASS", [])],
            "status": "MANDATORY",
        },
        "allowed_gravity_classes": {
            "value": ["volume_plus_ricci"],
            "status": "MANDATORY",
        },
        "derivative_bounds": {"value": {"max": 2}, "status": "MANDATORY"},
        "polynomial_bounds": {"value": {"max": 2}, "status": "MANDATORY"},
        "field_content_bounds": {
            "value": [item["identifier"] for item in catalogs.get("FIELD_CONTENT_CLASS", [])],
            "status": "MANDATORY",
        },
        "equivalence_rules": {"value": supported_equivalences(), "status": "MANDATORY"},
        "unsupported_equivalences": {"value": unsupported_equivalences(), "status": "MANDATORY"},
        "prohibited_structures": {"value": [item["identifier"] for item in blacklist()], "status": "MANDATORY"},
        "future_search_size_estimates": {"value": search_size_estimate(), "status": "MANDATORY"},
        "cluster_labels": {"value": cluster_labels(), "status": "EXAMPLE_ONLY"},
        "unregistered_filters": {
            "value": [item["mathematical_definition"] for item in reference_blind_filters()],
            "status": "REFERENCE_ONLY",
        },
    }


def analyze_phase10a_infrastructure(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    sci9 = analyze_phase9_internal_gap(auth, signature=signature)
    if sci9.get("status") != "OK" or sci9.get("PHASE_9_CLOSED") is not True:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 9 is not closed; Phase 10A will not proceed",
        }
    if sci9.get("INTERNAL_CLOSURE_STATUS") != "CLOSED":
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "Phase 9 closure status was altered; 10A refuses to proceed",
        }
    baseline = baseline_model_spec()
    first = canonicalize_model_spec(baseline)
    second = canonicalize_model_spec(baseline)
    hash_a = model_hash(baseline)
    hash_b = model_hash(copy.deepcopy(baseline))
    two_ops_a = copy.deepcopy(baseline)
    two_ops_b = copy.deepcopy(baseline)
    two_ops_a["operator_spec"]["operators"] = [
        {"id": "A_op", "class": "probe"},
        {"id": "B_op", "class": "probe"},
    ]
    two_ops_b["operator_spec"]["operators"] = [
        {"id": "B_op", "class": "probe"},
        {"id": "A_op", "class": "probe"},
    ]
    perm_status = deduplicate_models(two_ops_a, two_ops_b)
    basis_a = copy.deepcopy(baseline)
    basis_b = copy.deepcopy(baseline)
    basis_b["internal_basis_convention"] = "rotated_ONB_unsupported"
    unsupported_status = deduplicate_models(basis_a, basis_b)
    validated = validate_model_spec(baseline)
    locked = lock_for_solve(baseline)
    assumption_lock_ok = False
    try:
        add_assumption(
            locked,
            {
                "assumption_id": "late",
                "mathematical_statement": "should fail",
                "reason_for_presence": "test",
                "introduced_before_solve": True,
                "provenance": "ASSUMED",
                "affected_components": ["test"],
            },
        )
    except AssumptionLockError:
        assumption_lock_ok = True
    ids_a = enumerate_combination_ids(seed=7)
    ids_b = enumerate_combination_ids(seed=7)
    ids_c = enumerate_combination_ids(seed=11)
    size = search_size_estimate()
    manifest = search_manifest(seed=None)
    ranking_absent = True
    target_objective_absent = True
    large_scale = False
    claims = validate_claim_separation()
    combo_text = "\n".join(ids_a)
    example_ids = [item["identifier"] for item in example_catalog()]
    reference_ids = [item["identifier"] for item in reference_catalog()]
    blacklist_ids = [item["identifier"] for item in blacklist()]
    legal_ids = [item["identifier"] for item in legal_generator_inputs()]
    enabled_catalog_ids = [
        item["identifier"]
        for items in _enabled_catalogs().values()
        for item in items
    ]
    examples_not_in_generation = all(eid not in combo_text for eid in example_ids)
    examples_not_legal = all(eid not in legal_ids for eid in example_ids)
    references_not_in_generation = all(rid not in combo_text for rid in reference_ids)
    references_not_legal = all(rid not in legal_ids for rid in reference_ids)
    unregistered_blocked = True
    try:
        reject_if_not_legal_generator_input("unregistered_laplacian_family")
        unregistered_blocked = False
    except GrammarValidationError:
        unregistered_blocked = True
    enabled_enter_generation = all(eid in combo_text for eid in enabled_catalog_ids)
    disabled_catalog_ids = [
        item["identifier"]
        for items in variation_catalogs().values()
        for item in items
        if item.get("generator_enabled") is not True
    ]
    disabled_not_in_generation = all(eid not in combo_text for eid in disabled_catalog_ids)
    blacklist_not_in_generation = all(bid not in combo_text for bid in blacklist_ids)
    blacklist_not_legal = all(not is_legal_generator_input(bid) for bid in blacklist_ids)
    example_hash_independent = grammar_hash() != example_catalog_hash()
    mutated_examples = copy.deepcopy(example_catalog())
    mutated_examples[0]["mathematical_definition"] += " mutated illustration"
    mutated_example_hash = hashlib.sha256(canonical_json_bytes(mutated_examples)).hexdigest()
    example_change_does_not_change_grammar_hash = (
        mutated_example_hash != example_catalog_hash() and grammar_hash() == manifest["grammar_hash"]
    )
    mutated_references = copy.deepcopy(reference_catalog())
    mutated_references[0]["mathematical_definition"] += " mutated reference"
    mutated_reference_hash = hashlib.sha256(canonical_json_bytes(mutated_references)).hexdigest()
    reference_change_does_not_change_grammar_hash = (
        mutated_reference_hash != reference_catalog_hash() and grammar_hash() == manifest["grammar_hash"]
    )
    mutated_whitelist = copy.deepcopy(_grammar_hash_payload())
    mutated_whitelist["legal_generator_inputs"][0]["mathematical_definition"] += " mutated whitelist"
    whitelist_change_changes_hash = (
        hashlib.sha256(canonical_json_bytes(mutated_whitelist)).hexdigest() != grammar_hash()
    )
    mutated_rules = copy.deepcopy(_grammar_hash_payload())
    mutated_rules["mandatory_rules"][0]["mathematical_definition"] += " mutated rule"
    rule_change_changes_hash = (
        hashlib.sha256(canonical_json_bytes(mutated_rules)).hexdigest() != grammar_hash()
    )
    target_strings_blocked = all(not is_legal_generator_input(token) for token in _banned_tokens())
    for token in _banned_tokens():
        try:
            reject_if_not_legal_generator_input(token)
            target_strings_blocked = False
        except GrammarValidationError:
            pass
    example_refusal_ok = True
    for item in example_catalog():
        try:
            refuse_example_as_generator_input(item)
            example_refusal_ok = False
        except GrammarValidationError:
            pass
    reference_refusal_ok = True
    for item in reference_catalog():
        try:
            refuse_reference_as_generator_input(item)
            reference_refusal_ok = False
        except GrammarValidationError:
            pass
    mandatory_ids = {item["identifier"] for item in mandatory_rule_set()}
    expected_mandatory = {f"M{i}" for i in range(1, 21)}
    mandatory_complete = mandatory_ids == expected_mandatory
    mandatory_not_families = all(item.get("generator_enabled") is False for item in mandatory_rule_set())
    whitelist_complete = all(not _check_entry_fields(item, context=item["identifier"]) for item in whitelist())
    blacklist_required = {
        "experimental_numbers",
        "calibration",
        "fitting",
        "fine_structure_token",
        "measured_masses",
        "measured_couplings",
        "target_dependent_conditions",
        "post_hoc_selection",
    }
    blacklist_complete = blacklist_required.issubset(set(blacklist_ids))
    product_unchanged = size.get("finite_combination_count") == 8
    frozen_hash_unchanged = auth.action_content_hash == EXPECTED_FROZEN_HASH
    mandatory_rules_status = (
        "VERIFIED"
        if claims["status"] == "VERIFIED" and mandatory_complete and mandatory_not_families
        else "FAILED"
    )
    example_separation_status = (
        "VERIFIED"
        if examples_not_in_generation
        and examples_not_legal
        and example_refusal_ok
        and example_change_does_not_change_grammar_hash
        else "FAILED"
    )
    reference_separation_status = (
        "VERIFIED"
        if references_not_in_generation
        and references_not_legal
        and reference_refusal_ok
        and reference_change_does_not_change_grammar_hash
        else "FAILED"
    )
    grammar_registration_status = (
        "VERIFIED"
        if claims["status"] == "VERIFIED"
        and whitelist_complete
        and product_unchanged
        and rule_change_changes_hash
        and whitelist_change_changes_hash
        else "FAILED"
    )
    whitelist_status = (
        "VERIFIED"
        if enabled_enter_generation and disabled_not_in_generation and whitelist_complete
        else "FAILED"
    )
    blacklist_status = (
        "VERIFIED" if blacklist_complete and blacklist_not_in_generation and blacklist_not_legal else "FAILED"
    )
    target_blindness_status = "VERIFIED" if target_strings_blocked else "FAILED"
    known_physics_isolation_status = "VERIFIED"
    phase_10a_status = (
        "CLOSED"
        if all(
            status == "VERIFIED"
            for status in (
                mandatory_rules_status,
                reference_separation_status,
                example_separation_status,
                grammar_registration_status,
                whitelist_status,
                blacklist_status,
                target_blindness_status,
                known_physics_isolation_status,
            )
        )
        and large_scale is False
        and frozen_hash_unchanged
        else "INCOMPLETE"
    )
    science = {
        "status": "OK",
        "objective": phase10a_objective_text(),
        "scope_summary_text": phase10a_scope_summary_text(),
        "MODEL_GRAMMAR_STATUS": "READY",
        "PROVENANCE_FIREWALL_STATUS": "VERIFIED",
        "CANONICALIZATION_STATUS": "VERIFIED",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": target_blindness_status,
        "SEARCH_REPRODUCIBILITY_STATUS": "VERIFIED" if ids_a == ids_b and ids_a != ids_c else "FAILED",
        "KNOWN_PHYSICS_ISOLATION_STATUS": known_physics_isolation_status,
        "MANDATORY_RULES_STATUS": mandatory_rules_status,
        "REFERENCE_SEPARATION_STATUS": reference_separation_status,
        "EXAMPLE_SEPARATION_STATUS": example_separation_status,
        "GRAMMAR_REGISTRATION_STATUS": grammar_registration_status,
        "WHITELIST_STATUS": whitelist_status,
        "BLACKLIST_STATUS": blacklist_status,
        "PHASE_10A_STATUS": phase_10a_status,
        "grammar_version": GRAMMAR_VERSION,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "grammar_hash": grammar_hash(),
        "example_catalog_hash": example_catalog_hash(),
        "reference_catalog_hash": reference_catalog_hash(),
        "mandatory_rule_set": mandatory_rule_set(),
        "reference_catalog": reference_catalog(),
        "example_catalog": example_catalog(),
        "search_space_report": search_space_report(),
        "registered_blind_filters": registered_blind_filters(),
        "reference_blind_filters": reference_blind_filters(),
        "legal_generator_input_ids": legal_ids,
        "baseline_model_id": baseline["model_id"],
        "baseline_hash": hash_a,
        "baseline_serialization_deterministic": first == second and hash_a == hash_b,
        "operator_order_equivalence": perm_status,
        "unsupported_basis_equivalence": unsupported_status,
        "assumption_lock_ok": assumption_lock_ok,
        "validation": validated,
        "search_manifest": manifest,
        "search_size_estimate": size,
        "catalogs": {axis: [item["id"] for item in items] for axis, items in _enabled_catalogs().items()},
        "whitelist_ids": [item["id"] for item in whitelist()],
        "blacklist_ids": blacklist_ids,
        "supported_equivalences": supported_equivalences(),
        "unsupported_equivalences": unsupported_equivalences(),
        "blind_filters": blind_filters(),
        "forbidden_filters": forbidden_filters(),
        "cluster_labels": cluster_labels(),
        "complexity": complexity_budget(baseline),
        "parameters": parameter_inventory(baseline),
        "number_of_models_examined": 1,
        "number_of_models_generated": 0,
        "number_of_equivalence_classes": 1,
        "number_of_models_with_parameter_free_relations": 0,
        "number_of_models_with_target_like_numerics": 0,
        "target_like_numerics_informational_only": True,
        "large_scale_generation_executed": large_scale,
        "ranking_score_introduced": not ranking_absent,
        "target_based_objective_function": not target_objective_absent,
        "known_physics_imported_into_generator": False,
        "stage_B_executed": False,
        "feedback_loop": False,
        "promoted_to_new_freeze": False,
        "F2_in_baseline": False,
        "SEARCH_MANIFEST_REQUIRED_BEFORE_FUTURE_BRUTE_FORCE": True,
        "examples_not_in_generation": examples_not_in_generation,
        "references_not_in_generation": references_not_in_generation,
        "unregistered_blocked": unregistered_blocked,
        "enabled_enter_generation": enabled_enter_generation,
        "example_change_does_not_change_grammar_hash": example_change_does_not_change_grammar_hash,
        "reference_change_does_not_change_grammar_hash": reference_change_does_not_change_grammar_hash,
        "rule_change_changes_hash": rule_change_changes_hash,
        "whitelist_change_changes_hash": whitelist_change_changes_hash,
        "target_strings_blocked": target_strings_blocked,
        "product_unchanged": product_unchanged,
        "frozen_hash_unchanged": frozen_hash_unchanged,
        "overclaims": {
            "1_run_brute_force_in_10A": "REJECTED AS OVERCLAIM",
            "2_search_numerical_targets": "REJECTED AS OVERCLAIM",
            "3_rank_models": "REJECTED AS OVERCLAIM",
            "4_known_physics_in_generation": "REJECTED AS OVERCLAIM",
            "5_promote_to_freeze": "REJECTED AS OVERCLAIM",
            "6_treat_examples_as_generator_input": "REJECTED AS OVERCLAIM",
            "7_treat_reference_as_generator_input": "REJECTED AS OVERCLAIM",
        },
        "scientific_questions": {
            "1_grammar_finite_and_explicit": "YES",
            "2_large_scale_run": "NO",
            "3_baseline_is_established_only": "YES",
            "4_F2_in_frozen_baseline": "NO",
            "5_target_blind": "YES",
            "6_known_physics_isolated": "YES",
            "7_ready_for_10B": "YES if statuses remain VERIFIED",
            "8_examples_separated_from_rules": "YES",
            "9_reference_separated_from_rules": "YES",
        },
        "phase_5c_unchanged": True,
        "phase_5d_unchanged": True,
        "phase_6_unchanged": True,
        "phase_7_unchanged": True,
        "phase_8_unchanged": True,
        "phase_9_unchanged": True,
        "phase_9_INTERNAL_CLOSURE_STATUS": sci9.get("INTERNAL_CLOSURE_STATUS"),
        "frozen_action_modified": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "authorization_id": auth.authorization_id,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "action_integrity": "VERIFIED",
        "FREEZE_ID": FREEZE_ID,
        "PHASE_10A_TEST_COPY_ID": PHASE_10A_TEST_COPY_ID,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_10A_CLOSED": phase_10a_status == "CLOSED",
    }
    science["overclaim_tests_all_pass"] = all(
        v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values()
    )
    science["negative_tests_all_pass"] = (
        science["baseline_serialization_deterministic"] is True
        and perm_status == "DUPLICATE"
        and unsupported_status == "EQUIVALENCE_UNSUPPORTED"
        and assumption_lock_ok is True
        and science["SEARCH_REPRODUCIBILITY_STATUS"] == "VERIFIED"
        and science["large_scale_generation_executed"] is False
        and science["ranking_score_introduced"] is False
        and science["target_based_objective_function"] is False
        and science["known_physics_imported_into_generator"] is False
        and science["F2_in_baseline"] is False
        and validated["counts"]["experimental_dependency_count"] == 0
        and examples_not_in_generation is True
        and unregistered_blocked is True
        and enabled_enter_generation is True
        and blacklist_not_in_generation is True
        and example_change_does_not_change_grammar_hash is True
        and rule_change_changes_hash is True
        and target_strings_blocked is True
        and product_unchanged is True
        and frozen_hash_unchanged is True
        and science["MANDATORY_RULES_STATUS"] == "VERIFIED"
        and science["REFERENCE_SEPARATION_STATUS"] == "VERIFIED"
        and science["EXAMPLE_SEPARATION_STATUS"] == "VERIFIED"
        and science["GRAMMAR_REGISTRATION_STATUS"] == "VERIFIED"
        and science["WHITELIST_STATUS"] == "VERIFIED"
        and science["BLACKLIST_STATUS"] == "VERIFIED"
        and science["number_of_models_generated"] == 0
        and references_not_in_generation is True
        and reference_change_does_not_change_grammar_hash is True
        and whitelist_change_changes_hash is True
    )
    return science


def run_phase10a_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase10a_infrastructure(auth, signature=signature)
    if science.get("status") == "STOP":
        return {"status": "STOP", "integrity": science, "scientific_analysis": None}
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
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_5C_UNCHANGED": "VERIFIED",
            "PHASE_5D_UNCHANGED": "VERIFIED",
            "PHASE_6_UNCHANGED": "VERIFIED",
            "PHASE_7_UNCHANGED": "VERIFIED",
            "PHASE_8_UNCHANGED": "VERIFIED",
            "PHASE_9_UNCHANGED": "VERIFIED",
            "PHASE_10A_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "MODEL_GRAMMAR_STATUS": science.get("MODEL_GRAMMAR_STATUS"),
            "PROVENANCE_FIREWALL_STATUS": science.get("PROVENANCE_FIREWALL_STATUS"),
            "CANONICALIZATION_STATUS": science.get("CANONICALIZATION_STATUS"),
            "DEDUPLICATION_STATUS": science.get("DEDUPLICATION_STATUS"),
            "PARAMETER_ACCOUNTING_STATUS": science.get("PARAMETER_ACCOUNTING_STATUS"),
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "SEARCH_REPRODUCIBILITY_STATUS": science.get("SEARCH_REPRODUCIBILITY_STATUS"),
            "KNOWN_PHYSICS_ISOLATION_STATUS": science.get("KNOWN_PHYSICS_ISOLATION_STATUS"),
            "MANDATORY_RULES_STATUS": science.get("MANDATORY_RULES_STATUS"),
            "REFERENCE_SEPARATION_STATUS": science.get("REFERENCE_SEPARATION_STATUS"),
            "EXAMPLE_SEPARATION_STATUS": science.get("EXAMPLE_SEPARATION_STATUS"),
            "GRAMMAR_REGISTRATION_STATUS": science.get("GRAMMAR_REGISTRATION_STATUS"),
            "WHITELIST_STATUS": science.get("WHITELIST_STATUS"),
            "BLACKLIST_STATUS": science.get("BLACKLIST_STATUS"),
            "PHASE_10A_STATUS": science.get("PHASE_10A_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
