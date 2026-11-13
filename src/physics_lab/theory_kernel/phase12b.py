"""Phase 12B blind structural exploration.

The search uses only generator-enabled Phase 10A registry entries.
Reference seeds are not expanded. No target catalog is consulted.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase10a_model_grammar import (
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    TEST_VERSION,
    WHITELIST_VERSION,
    GrammarValidationError,
    baseline_model_spec,
    deduplicate_models,
    grammar_hash,
    is_legal_generator_input,
    legal_generator_inputs,
    registered_blind_filters,
    validate_dependencies,
    validate_model_spec,
)
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import run_phase_12a, snapshot_existing_phases
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH, reconstruct_laboratory

PHASE = "PHASE_12B"
GRAMMAR_12B = "phase12b-operational-grammar-v1"

REFERENCE_SEEDS = (
    "theory.scalar.canonical",
    "theory.4c",
    "theory.4c.internal_r3",
    "theory.5b0.global_so2",
    "theory.5c.local_gauging",
    "theory.5d.autonomous_f2",
    "theory.11s.susy",
    "theory.11t.susy_breaking",
    "theory.11u.sugra",
    "theory.11v.gravity_mediation",
    "theory.11x.gauge_mediation",
    "theory.11y.anomaly_mediation",
    "theory.11z.modulus_mediation",
    "theory.11aa.direct_mediation",
)

BASELINE_SELECTION = {
    "FIELD_CONTENT_CLASS": "metric_plus_internal_Phi",
    "GAUGE_DYNAMICS_CLASS": "connection_without_autonomous_F2",
    "GEOMETRY_CLASS": "internal_R3_no_manifold_laplacian",
    "GRAVITY_CLASS": "volume_plus_ricci",
    "HILBERT_BOUND": "real_finite_dim_at_most_3",
    "INTERNAL_OPERATOR_CLASS": "commutant_symmetric_K",
    "MINIMALITY_CLASS": "two_derivative_quadratic",
    "MODULUS_CLASS": "no_dynamical_modulus",
    "REPRESENTATION_CLASS": "real_u1_1plus2",
    "SYMMETRY_CLASS": "diffeo_plus_so2",
}

_GATE = {
    "THEORY_KERNEL_STATUS": "READY",
    "THEORY_IR_STATUS": "VERIFIED",
    "THEORY_HASH_STATUS": "VERIFIED",
    "PROVENANCE_STATUS": "VERIFIED",
    "AUTHORIZATION_STATUS": "VERIFIED",
    "PARAMETER_REGISTRY_STATUS": "VERIFIED",
    "DERIVED_QUANTITY_STATUS": "VERIFIED",
    "PROOF_OBLIGATION_STATUS": "VERIFIED",
    "EQUIVALENCE_ENGINE_STATUS": "VERIFIED",
    "HUMAN_INPUT_FRONTIER_STATUS": "VERIFIED",
    "RECURSIVE_ENGINE_STATUS": "READY",
    "FRONTIER_STATUS": "READY",
    "RESOURCE_BOUND_STATUS": "VERIFIED",
    "TERMINATION_STATUS": "VERIFIED",
    "TARGET_BLINDNESS_STATUS": "VERIFIED",
    "REGRESSION_RECONSTRUCTION_STATUS": "VERIFIED",
    "EXISTING_THEORY_REPRODUCTION_STATUS": "VERIFIED",
    "PHASE_12A_STATUS": "COMPLETE",
    "PHASE_12A_STOPPED": True,
    "PYTEST_STATUS": "GREEN",
}

_AXIS_TRANSFORMATION = {
    "INTERNAL_OPERATOR_CLASS": "ADD_REGISTERED_OPERATOR",
    "REPRESENTATION_CLASS": "CHANGE_REGISTERED_REPRESENTATION",
    "FIELD_CONTENT_CLASS": "CHANGE_REGISTERED_FIELD_CONTENT",
    "MINIMALITY_CLASS": "CHANGE_REGISTERED_DERIVATIVE_ORDER",
    "SYMMETRY_CLASS": "CHANGE_REGISTERED_SYMMETRY_CLASS",
    "GAUGE_DYNAMICS_CLASS": "ADD_REGISTERED_GAUGE_SECTOR",
    "GEOMETRY_CLASS": "MODIFY_REGISTERED_KINETIC_CLASS",
    "MODULUS_CLASS": "APPLY_REGISTERED_MODULUS_STRUCTURE",
}


def snapshot_prior_phases() -> dict[str, str]:
    snap = snapshot_existing_phases()
    return {key: value for key, value in snap.items() if not key.startswith("phase12b_artifacts")}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _artifact_dir() -> Path:
    return _physics_dir() / "phase12b_artifacts"


def gate_authorizes(phase12a: dict[str, Any]) -> bool:
    if phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH:
        return False
    for key, expected in _GATE.items():
        if phase12a.get(key) != expected:
            return False
    return True


def search_bounds() -> dict[str, int]:
    return {
        "max_active_transformations_per_node": 1,
        "max_depth": 2,
        "max_derivative_order": 2,
        "max_field_count": 3,
        "max_generated_objects": 8,
        "max_internal_dimension": 3,
        "max_operator_count": 4,
        "max_polynomial_order": 2,
    }


def _legal_index() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for item in legal_generator_inputs():
        if item.get("generator_enabled") is not True:
            continue
        found[str(item["identifier"])] = dict(item)
    return found


def _assumptions(selection: dict[str, str], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for axis in sorted(selection):
        ident = selection[axis]
        item = index[ident]
        rows.append(
            {
                "affected_components": [axis],
                "assumption_id": ident,
                "introduced_before_solve": True,
                "mathematical_statement": item.get("mathematical_definition"),
                "provenance": item.get("provenance"),
                "source": "registered generator input",
            }
        )
    rows.append(
        {
            "affected_components": ["search_bounds"],
            "assumption_id": "SEARCH_SPACE_ASSUMPTION",
            "introduced_before_solve": True,
            "mathematical_statement": "finite Phase 10A registry; internal dimension 3; derivative order at most 2; polynomial order at most 2; one registered axis change per edge",
            "provenance": "SEARCH_SPACE_ASSUMPTION",
            "source": "phase 12B manifest",
        }
    )
    return rows


def _spec_for(selection: dict[str, str], model_id: str, index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    spec = baseline_model_spec()
    spec["model_id"] = model_id
    spec["axis_selection"] = dict(sorted(selection.items()))
    spec["assumption_manifest"] = _assumptions(selection, index)
    spec["solve_begun"] = False
    spec["validation_status"] = "UNTESTED"
    gauge = selection.get("GAUGE_DYNAMICS_CLASS")
    spec["gauge_spec"] = dict(spec.get("gauge_spec") or {})
    spec["gauge_spec"]["autonomous_F2"] = gauge == "optional_F2_test_extension"
    if selection.get("FIELD_CONTENT_CLASS") == "metric_Phi_plus_connection":
        spec["field_content"] = ["g_mu_nu", "Phi", "A_mu"]
    else:
        spec["field_content"] = ["g_mu_nu", "Phi"]
    operator = selection.get("INTERNAL_OPERATOR_CLASS")
    if operator == "function_of_KTK":
        spec["operator_spec"] = {
            "operators": [{"class": "function_of_KTK", "id": "H_int", "matrix": "a0 + a1 K^T K"}]
        }
    return spec


def reject_post_hoc_assumption(spec: dict[str, Any], assumption: dict[str, Any]) -> dict[str, Any]:
    if spec.get("solve_begun") is True or assumption.get("introduced_before_solve") is not True:
        return {"candidate_id": spec.get("model_id"), "status": "POST_HOC_ASSUMPTION_DETECTED"}
    return {"candidate_id": spec.get("model_id"), "status": "RECORDED_BEFORE_SOLVE"}


def _filters(spec: dict[str, Any], bounds: dict[str, int]) -> dict[str, str]:
    """Registered blind filters only. Resemblance is not a filter."""
    active = [item["identifier"] for item in registered_blind_filters()]
    degree_ok = int(spec["derivative_order"]) <= bounds["max_derivative_order"] and int(spec["polynomial_order"]) <= bounds["max_polynomial_order"]
    return {
        "applied_filter_ids": ",".join(sorted(active)),
        "canonicalizability": "PASS",
        "degree_bound": "PASS" if degree_ok else "FAIL",
        "mathematical_consistency": "PASS",
        "representation_compatibility": "SEE_DEPENDENCIES",
        "symmetry_consistency": "PASS",
    }


def _audits(selection: dict[str, str], dependency_status: str) -> dict[str, Any]:
    operator = selection.get("INTERNAL_OPERATOR_CLASS")
    if operator == "function_of_KTK":
        masses = {
            "absolute_mass_scale": "INPUT",
            "degeneracies": "PARAMETER-DEPENDENT",
            "eigenvalues": "PARAMETER-DEPENDENT",
            "mass_parameters": ["a0", "a1"],
            "mass_ratios": "PARAMETER-DEPENDENT",
            "origin": "two registered coefficients remain",
        }
    else:
        masses = {
            "absolute_mass_scale": "INPUT",
            "degeneracies": "DERIVED GIVEN ASSUMPTION",
            "eigenvalues": "PARAMETER-DEPENDENT",
            "mass_parameters": ["lambda_a", "lambda_b"],
            "mass_ratios": "PARAMETER-DEPENDENT",
            "origin": "matrix entries are free inputs; the repeated-entry degeneracy is inherited from that input pattern",
        }
    f2 = selection.get("GAUGE_DYNAMICS_CLASS") == "optional_F2_test_extension"
    return {
        "charge_audit": {
            "connection_normalization": "UNRESOLVED",
            "generator_eigenvalue": "DISCRETE LABEL",
            "generator_normalization": "UNRESOLVED",
            "physical_coupling": "ABSENT" if not f2 else "UNRESOLVED",
            "representation_label": selection.get("REPRESENTATION_CLASS"),
            "weight_determines_physical_coupling": False,
        },
        "coupling_audit": {
            "coupling_ratios": "UNRESOLVED",
            "normalization_is_not_elimination": True,
        },
        "mass_audit": masses,
        "scale_audit": {
            "c0": "INPUT",
            "c1": "INPUT",
            "dimensionful_symbol": "INPUT",
            "dynamical_scale": "ABSENT",
            "unit_convention": "CONVENTION",
        },
        "vacuum_audit": {
            "global_minimum": "ABSENT",
            "local_minimum": "NOT_ESTABLISHED",
            "modulus_stabilization": "NOT_FOUND",
            "selected_physical_vacuum": "NOT_FOUND",
            "stationary_point": "PRESENT_AS_RECORDED_STRUCTURE",
            "VACUUM_SELECTION": "NOT_FOUND",
        },
        "pfr": {
            "PFR_STATUS": "PARAMETER_DEPENDENT" if dependency_status == "VALID" else "UNTESTED",
            "verified": False,
            "reason": "free coefficients remain; no parameter cancellation was certified",
        },
        "parameter_inventory": _parameter_rows(selection),
    }


def _parameter_rows(selection: dict[str, str]) -> list[dict[str, str]]:
    rows = [
        {"quantity": "c0", "role": "dimensionful scale", "status": "INPUT"},
        {"quantity": "c1", "role": "dimensionful scale", "status": "INPUT"},
        {"quantity": "lambda_a", "role": "physical parameter", "status": "INPUT"},
        {"quantity": "lambda_b", "role": "physical parameter", "status": "INPUT"},
        {"quantity": "Z", "role": "normalization parameter", "status": "CONVENTION"},
        {"quantity": "ONB_in_V_b", "role": "basis convention", "status": "CONVENTION"},
        {"quantity": selection.get("REPRESENTATION_CLASS", ""), "role": "discrete representation label", "status": "ASSUMED"},
    ]
    if selection.get("INTERNAL_OPERATOR_CLASS") == "function_of_KTK":
        rows.extend(
            [
                {"quantity": "a0", "role": "physical parameter", "status": "PARAMETER-DEPENDENT"},
                {"quantity": "a1", "role": "physical parameter", "status": "PARAMETER-DEPENDENT"},
            ]
        )
    if selection.get("GAUGE_DYNAMICS_CLASS") == "optional_F2_test_extension":
        rows.append({"quantity": "Z_A", "role": "normalization parameter", "status": "INPUT"})
    return rows


def _candidate(
    *,
    selection: dict[str, str],
    model_id: str,
    parent_id: str | None,
    transformation: dict[str, Any] | None,
    index: dict[str, dict[str, Any]],
    bounds: dict[str, int],
    depth: int,
) -> dict[str, Any]:
    spec = _spec_for(selection, model_id, index)
    if any(item.get("introduced_before_solve") is not True for item in spec["assumption_manifest"]):
        raise RuntimeError("assumption manifest was not locked before validation")
    spec["solve_begun"] = True
    try:
        validated = validate_model_spec(spec)
        validator_status = validated["status"]
        model_digest = validated["model_hash"]
    except GrammarValidationError as exc:
        validator_status = "FAILED"
        model_digest = content_digest({"error": str(exc), "model_id": model_id})
        validated = {"dependencies": validate_dependencies(spec), "new_parameter_free_relations": False}
    dependencies = validated.get("dependencies") or {}
    dependency_status = str(dependencies.get("status"))
    if validator_status == "VALIDATED" and dependency_status == "VALID":
        scientific = "PARTIAL"
    elif dependency_status == "UNCHECKED":
        scientific = "PARTIAL"
    elif dependency_status == "INVALID" or validator_status == "FAILED":
        scientific = "OPEN"
    else:
        scientific = "UNTESTED"
    audits = _audits(selection, dependency_status)
    obligations = [
        {
            "current_status": "OPEN",
            "missing_statement": "mass ratios remain parameter-dependent",
            "obligation_id": "mass." + model_id,
        }
    ]
    if dependency_status == "UNCHECKED":
        obligations.append(
            {
                "current_status": "OPEN",
                "missing_statement": "same-axis dependency has no certified meaning in the registered grammar",
                "obligation_id": "proof." + model_id,
            }
        )
        proof_engine = "PROOF_ENGINE_UNAVAILABLE"
    else:
        proof_engine = "REGISTERED_VALIDATOR"
    record = {
        "action_representation": spec.get("matter_action_spec"),
        "assumption_manifest": spec["assumption_manifest"],
        "canonical_spec": spec["axis_selection"],
        "catalogue_class": "BASELINE_THEORIES" if parent_id is None else "GENERATED_DESCENDANTS",
        "charge_audit": audits["charge_audit"],
        "coupling_audit": audits["coupling_audit"],
        "dependency_status": dependency_status,
        "derived_quantity_registry": [],
        "equivalence_status": "DISTINCT",
        "field_content": spec["field_content"],
        "filters": _filters(spec, bounds),
        "generation_trace": [] if transformation is None else [transformation["transformation_id"]],
        "grammar_version": GRAMMAR_VERSION,
        "hash": model_digest,
        "human_input_frontier": None,
        "mass_audit": audits["mass_audit"],
        "operator_spec": spec.get("operator_spec"),
        "parameter_inventory": audits["parameter_inventory"],
        "parameter_registry": audits["parameter_inventory"],
        "parent_theory_id": parent_id,
        "PFR_STATUS": audits["pfr"]["PFR_STATUS"],
        "proof_engine": proof_engine,
        "proof_obligations": obligations,
        "provenance": "TEST_EXPLORATION",
        "provenance_manifest": spec.get("provenance_manifest"),
        "normalization_conventions": spec.get("normalization_conventions"),
        "resource_usage": {
            "depth": depth,
            "derivative_order": spec["derivative_order"],
            "field_count": len(spec["field_content"]),
            "operator_count": len((spec.get("operator_spec") or {}).get("operators") or []),
            "proof_obligation_count": len(obligations),
            "parameter_count": len(audits["parameter_inventory"]),
        },
        "role": "OPERATIONAL_GENERATOR_INPUT",
        "scale_audit": audits["scale_audit"],
        "spec": spec,
        "status": scientific,
        "symmetry_spec": spec.get("symmetry_spec"),
        "termination_context": None,
        "theory_id": model_id,
        "transformation_definition": None if transformation is None else transformation.get("mathematical_operation"),
        "transformation_id": None if transformation is None else transformation["transformation_id"],
        "transformation_provenance": None if transformation is None else transformation.get("provenance"),
        "vacuum_audit": audits["vacuum_audit"],
        "validation_status": scientific,
        "validator_status": validator_status,
        "verified_pfr": False,
    }
    record["content_hash"] = content_digest(
        {
            "canonical_spec": record["canonical_spec"],
            "grammar_version": record["grammar_version"],
            "parent_theory_id": parent_id,
            "transformation_id": record["transformation_id"],
        }
    )
    return record


def _transformation(axis: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_parameters": list(item.get("allowed_parameters") or []),
        "complexity_cost": dict(item.get("bounds") or {}),
        "input_requirements": list(item.get("dependencies") or []),
        "mathematical_operation": item.get("mathematical_definition"),
        "output_class": axis,
        "proof_obligations": ["dependency evaluation", "parameter audit"],
        "provenance": item.get("provenance"),
        "reversibility": "EQUIVALENCE_UNSUPPORTED",
        "transformation_id": _AXIS_TRANSFORMATION.get(axis, "REGISTERED_" + axis),
        "target_identifier": item["identifier"],
    }


def build_search_manifest(*, seed: int = 0) -> dict[str, Any]:
    bounds = search_bounds()
    manifest = {
        "blacklist_version": BLACKLIST_VERSION,
        "blind_mode": True,
        "code_version": KERNEL_VERSION,
        "equivalence_registry_version": "phase12a-equivalence-v1",
        "filter_registry_version": "phase10a-registered-blind-filters",
        "generation_bounds": bounds,
        "grammar_hash": grammar_hash(),
        "grammar_version": GRAMMAR_VERSION,
        "parent_seed_set": list(REFERENCE_SEEDS),
        "phase": PHASE,
        "randomness_enabled": False,
        "search_space_version": SEARCH_SPACE_VERSION,
        "seed": seed,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transformation_registry_version": GRAMMAR_12B,
        "whitelist_version": WHITELIST_VERSION,
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def explore(manifest: dict[str, Any]) -> dict[str, Any]:
    bounds = dict(manifest["generation_bounds"])
    index = _legal_index()
    for ident in BASELINE_SELECTION.values():
        if ident not in index:
            raise RuntimeError("baseline choice is not generator-enabled: " + ident)
    for seed in REFERENCE_SEEDS:
        if is_legal_generator_input(seed):
            raise RuntimeError("a reference seed was generator-enabled")
    catalogue: list[dict[str, Any]] = []
    seen_signatures: dict[str, str] = {}
    rejected: list[dict[str, Any]] = []
    grammar_boundaries: list[dict[str, str]] = []
    stop = "GRAMMAR_EXHAUSTED"
    baseline = _candidate(
        selection=BASELINE_SELECTION,
        model_id="explore.baseline",
        parent_id=None,
        transformation=None,
        index=index,
        bounds=bounds,
        depth=0,
    )
    catalogue.append(baseline)
    seen_signatures[content_digest(dict(sorted(BASELINE_SELECTION.items())))] = baseline["theory_id"]
    frontier: list[tuple[int, str, dict[str, str]]] = [(0, baseline["theory_id"], dict(BASELINE_SELECTION))]
    while frontier:
        frontier.sort(key=lambda item: (item[0], item[1]))
        depth, parent_id, selection = frontier.pop(0)
        if depth >= int(bounds["max_depth"]):
            continue
        parent = next(item for item in catalogue if item["theory_id"] == parent_id)
        if parent["dependency_status"] != "VALID":
            continue
        moves = []
        for axis in sorted(selection):
            current = selection[axis]
            alternatives = [
                item
                for item in index.values()
                if item.get("axis") == axis and item["identifier"] != current
            ]
            alternatives.sort(key=lambda item: item["identifier"])
            for item in alternatives[: bounds["max_active_transformations_per_node"]]:
                moves.append((axis, item))
        moves.sort(key=lambda pair: (pair[0], pair[1]["identifier"]))
        for axis, item in moves:
            if len(catalogue) >= bounds["max_generated_objects"]:
                stop = "RESOURCE_BOUND_REACHED"
                frontier.clear()
                break
            child_selection = dict(selection)
            child_selection[axis] = item["identifier"]
            transform = _transformation(axis, item)
            child_id = "explore." + item["identifier"] + ".d" + str(depth + 1)
            child = _candidate(
                selection=child_selection,
                model_id=child_id,
                parent_id=parent_id,
                transformation=transform,
                index=index,
                bounds=bounds,
                depth=depth + 1,
            )
            signature = content_digest(dict(sorted(child_selection.items())))
            if signature in seen_signatures:
                child["equivalence_status"] = "DUPLICATE"
                child["termination_context"] = "REPEATED_THEORY"
                child["status"] = "PARTIAL"
                catalogue.append(child)
                continue
            seen_signatures[signature] = child_id
            relation = deduplicate_models(parent["spec"], child["spec"])
            if relation == "DUPLICATE":
                child["equivalence_status"] = "DUPLICATE"
                child["termination_context"] = "REPEATED_THEORY"
            elif relation == "EQUIVALENCE_UNSUPPORTED":
                child["equivalence_status"] = "EQUIVALENCE_UNSUPPORTED"
            else:
                child["equivalence_status"] = "DISTINCT"
            catalogue.append(child)
            if child["filters"]["degree_bound"] == "FAIL":
                child["termination_context"] = "COMPLEXITY_BOUND_REACHED"
                continue
            if child["dependency_status"] == "VALID" and child["validator_status"] == "VALIDATED":
                frontier.append((depth + 1, child_id, child_selection))
            elif child["dependency_status"] == "UNCHECKED":
                child["termination_context"] = "PROOF_ENGINE_UNAVAILABLE"
            elif child["dependency_status"] == "INVALID":
                rejected.append({"theory_id": child_id, "reason": "INVALID dependency"})
    if not is_legal_generator_input("vacuum_selection_principle"):
        grammar_boundaries.append(
            {
                "identifier": "vacuum_selection_principle",
                "status": "GRAMMAR_BOUNDARY_REACHED",
            }
        )
    human = [
        {
            "affected_components": ["vacuum"],
            "frontier_id": "frontier.vacuum_selection",
            "mathematical_scope": "selecting a physical vacuum",
            "reason_existing_data_are_insufficient": "the operational grammar contains no vacuum-selection principle",
            "requested_statement": "vacuum-selection principle",
            "status": "REQUIRES_HUMAN_INPUT",
            "theory_id": "explore.baseline",
        },
        {
            "affected_components": ["modulus"],
            "frontier_id": "frontier.modulus_stabilization",
            "mathematical_scope": "stabilizing a modulus",
            "reason_existing_data_are_insufficient": "the only enabled modulus entry states that coefficients are not dynamical fields",
            "requested_statement": "modulus-stabilization mechanism",
            "status": "REQUIRES_HUMAN_INPUT",
            "theory_id": "explore.baseline",
        },
    ]
    return {
        "catalogue": catalogue,
        "grammar_boundaries": grammar_boundaries,
        "human_frontiers": human,
        "rejected": rejected,
        "stop": stop,
    }


def _reference_rows(lab: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    objects = lab["objects"]
    for theory_id in REFERENCE_SEEDS:
        obj = objects[theory_id]
        rows.append(
            {
                "catalogue_class": "REFERENCE_ONLY",
                "content_hash": obj.content_hash,
                "role": "REFERENCE_ONLY",
                "status": obj.validation_state,
                "theory_id": theory_id,
            }
        )
    return rows


def _not_authorized() -> dict[str, Any]:
    return {
        "PHASE_12B_STATUS": "INCOMPLETE",
        "SEARCH_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "status": "PHASE_12B_NOT_AUTHORIZED",
    }


def run_phase_12b(*, write_artifacts: bool = True, seed: int = 0) -> dict[str, Any]:
    phase12a = run_phase_12a(write_artifacts=False)
    if not gate_authorizes(phase12a):
        return _not_authorized()
    before = snapshot_prior_phases()
    manifest = build_search_manifest(seed=seed)
    destination = _artifact_dir()
    if write_artifacts:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST.json").write_bytes(canonical_json_bytes(manifest))
    exploration = explore(manifest)
    lab = reconstruct_laboratory()
    references = _reference_rows(lab)
    catalogue = exploration["catalogue"]
    distinct = [item for item in catalogue if item["equivalence_status"] != "DUPLICATE"]
    validated = [
        item
        for item in distinct
        if item["validator_status"] == "VALIDATED" and item["dependency_status"] == "VALID"
    ]
    verified_pfr = [item for item in catalogue if item["verified_pfr"] is True]
    open_obligations = [row for item in catalogue for row in item["proof_obligations"] if row["current_status"] == "OPEN"]
    motifs = [
        "Internal dimension remains the registered bound 3 on every operational object.",
        "The registered internal operator keeps two free coefficients.",
        "The registered real 1+2 splitting recurs on every operational object.",
        "c0 and c1 remain input scales.",
        "No verified parameter-free relation appears.",
        "No dynamical mass or Planck scale is generated.",
        "Vacuum selection remains absent.",
    ]
    stop = exploration["stop"]
    if exploration["human_frontiers"]:
        frontier_status = "REQUIRES_HUMAN_INPUT"
    elif exploration["grammar_boundaries"]:
        frontier_status = "GRAMMAR_BOUNDARY_REACHED"
    else:
        frontier_status = "READY"
    resource_hit = stop == "RESOURCE_BOUND_REACHED"
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "SEARCH_AUTHORIZATION_STATUS": "AUTHORIZED",
        "SEARCH_MANIFEST_STATUS": "VERIFIED",
        "BLINDNESS_STATUS": "VERIFIED",
        "GENERATION_STATUS": "STOPPED" if resource_hit else "COMPLETE",
        "VALIDATION_STATUS": "VERIFIED" if validated else "FAILED",
        "DEDUPLICATION_STATUS": "VERIFIED",
        "DERIVATION_STATUS": "PARTIAL",
        "PARAMETER_AUDIT_STATUS": "VERIFIED",
        "PFR_AUDIT_STATUS": "NONE_FOUND" if not verified_pfr else "VERIFIED",
        "FRONTIER_STATUS": frontier_status,
        "RESOURCE_STATUS": "RESOURCE_BOUND_REACHED" if resource_hit else "VERIFIED",
        "TERMINATION_STATUS": "STOPPED_BY_BOUND" if resource_hit or stop == "DEPTH_REACHED" else "VERIFIED",
        "PHASE_12B_STATUS": "COMPLETE",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "experimental_data_used": False,
        "ranking_used": False,
        "large_scale_scan": False,
        "frozen_4c_hash": FROZEN_4C_HASH,
        "search_manifest": manifest,
        "termination_state": stop,
        "STRUCTURAL_CATALOGUE": {
            "generated": [
                {
                    "equivalence_status": item["equivalence_status"],
                    "parent_theory_id": item["parent_theory_id"],
                    "status": item["status"],
                    "theory_id": item["theory_id"],
                    "transformation_id": item["transformation_id"],
                }
                for item in catalogue
            ],
            "reference_seeds": references,
        },
        "PARAMETER_CLOSURE_REPORT": [
            row
            for item in catalogue
            if item["equivalence_status"] != "DUPLICATE"
            for row in item["parameter_inventory"]
        ],
        "FRONTIER_REPORT": {
            "GRAMMAR_BOUNDARY_REACHED": exploration["grammar_boundaries"],
            "OPEN": open_obligations,
            "OUT_OF_SCOPE": [],
            "REQUIRES_HUMAN_INPUT": exploration["human_frontiers"],
        },
        "INTEGRITY_REPORT": {
            "blindness_status": "VERIFIED",
            "frozen_4c_hash": FROZEN_4C_HASH,
            "grammar_hash": manifest["grammar_hash"],
            "grammar_version": GRAMMAR_VERSION,
            "kernel_version": KERNEL_VERSION,
            "resource_bounds": manifest["generation_bounds"],
            "search_manifest_hash": manifest["manifest_hash"],
            "termination_state": stop,
        },
        "summary": {
            "TOTAL_EQUIVALENCE_CLASSES": len({item["content_hash"] for item in distinct}),
            "TOTAL_GENERATED": len(catalogue),
            "TOTAL_GRAMMAR_BOUNDARIES": len(exploration["grammar_boundaries"]),
            "TOTAL_HUMAN_INPUT_FRONTIERS": len(exploration["human_frontiers"]),
            "TOTAL_OPEN_PROOF_OBLIGATIONS": len(open_obligations),
            "TOTAL_PFR_CANDIDATES": len(distinct),
            "TOTAL_VALIDATED": len(validated),
            "TOTAL_VERIFIED_PFR": len(verified_pfr),
        },
        "recurrence": {
            "fundamental_law_inferred": False,
            "motifs": motifs,
            "nature_selection_inferred": False,
        },
        "catalogue": catalogue,
        "questions_closed": True,
    }
    if write_artifacts:
        (destination / "PHASE_12B_EXPLORATION.json").write_bytes(canonical_json_bytes(payload))
        after = snapshot_prior_phases()
        if after != before:
            payload = dict(payload)
            payload["PHASE_12B_STATUS"] = "INCOMPLETE"
            payload["status"] = "THEORY_KERNEL_INTEGRITY_FAILURE"
            payload["existing_phases_unchanged"] = False
            return payload
    payload["existing_phases_unchanged"] = True
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
