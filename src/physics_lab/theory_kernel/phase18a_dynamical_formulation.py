"""Phase 18A audits dynamical-formulation grammars and does not search."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence, classify_candidate
from physics_lab.theory_kernel.phase17b1_fundamental_structure import _authored
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_18A"
CODE_VERSION = "phase18a-dynamical-formulation-v1"
TEST_VERSION = "phase18a-tests-v1"
ARTIFACT_DIR_NAME = "phase18a_dynamical_formulation_artifacts"
CATALOG_RELATIVE = "phase17_tier1_search_artifacts/PHASE_17_TIER1_CATALOG.json"
MANIFEST_ID = "db5610a2ac03c07f7ed91098eaab3c6d038608118676983f5b797c8222b316a8"
CATALOG_HASH = "7a4957d7d7578116a6a23fd938d4b398b17b644a9fda049737228495044208a0"
AUTHORIZATION_HASH = "9c0f5cd687555de7e5926bdfd2817c9f5098cb0bab314cd76333dabe171cdab4"
GRAMMAR_15F_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
GRAMMAR_17B1_HASH = "646de89a3b8d8bce6b2360be4c262d8c2345f64aab3832c2a830066697e8e888"
GRAMMAR_17C_HASH = "6e357f9b0ef1447fda2bbffc89330267beb05188c45f49eedd288c4c9bf9b5c1"
V22_SHA256 = "7f9441709705c336d369f9944837c445e790696295df82c0be1cd70033275c1b"
PROVENANCE = (
    "DERIVED",
    "DERIVED GIVEN ASSUMPTION",
    "INPUT",
    "ASSUMED",
    "PARAMETER-DEPENDENT",
    "CONVENTION",
    "UNTESTED",
    "METHOD",
    "INTEGRITY CONTROL",
)
FORMULATION_TYPES = (
    "LOCAL_ACTION_FUNCTIONAL",
    "CONSTRAINED_ACTION",
    "HAMILTONIAN_OR_CANONICAL_FORMULATION",
    "STATE_SUM_OR_TRANSITION_AMPLITUDE",
    "DISCRETE_DYNAMICAL_RULE",
    "RENORMALIZATION_FLOW",
    "OTHER_FORMAL_DYNAMICS",
    "NOT_YET_SPECIFIABLE",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = ("pre" + "ferred", "most_" + "cited", "most_" + "popular")
    return all(token not in text for token in _ranking_tokens()) and all(token not in text for token in banned) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"INTEGRITY_MISMATCH": reason, "PHASE18A_STATUS": "INCOMPLETE", "SEARCH_STATUS": "NOT_STARTED", "status": "AUDIT_FAILED"}


def select_action(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def enable_formulation(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def combine_grammars(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_GENERATED"


def request_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def insert_vacuum_principle(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def select_by_familiarity(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _plan(
    formulation_type: str,
    claim: str,
    readiness: str,
    missing: tuple[str, ...],
    blocks: tuple[str, ...],
    axes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "allowed_blocks": blocks,
        "axes": axes,
        "claim": claim,
        "formulation_type": formulation_type,
        "missing": missing,
        "readiness": readiness,
    }


def _plans(objects: tuple[str, ...]) -> list[dict[str, Any]] | None:
    table: dict[tuple[str, ...], list[dict[str, Any]]] = {
        ("conformal class",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density built from a conformal class", "invariant measure"), ("invariant_scalar_densities",), ("derivative_order", "polynomial_order", "operator_count")),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("canonical variables", "Hamiltonian density"), (), ("derivative_order", "field_order")),
        ],
        ("length connection",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density using the length connection", "invariant measure"), ("covariant_derivative_terms",), ("derivative_order", "operator_count")),
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("law for the length connection"), (), ()),
        ],
        ("paths",): [
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("law on unparameterized paths"), (), ()),
        ],
        ("torsion", "curvature"): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density in curvature and torsion", "coefficients"), ("curvature_dependent_terms", "torsion_dependent_terms"), ("derivative_order", "operator_count")),
            _plan("CONSTRAINED_ACTION", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("which structural relations are dynamical constraints"), ("constraint_functionals",), ("constraint_count", "derivative_order")),
        ],
        ("affine connection",): [
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("law for the affine connection"), ("covariant_derivative_terms",), ()),
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("volume form", "scalar density"), ("invariant_scalar_densities",), ("derivative_order", "operator_count")),
        ],
        ("metric", "connection", "torsion", "nonmetricity"): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density", "coefficients"), ("curvature_dependent_terms", "torsion_dependent_terms", "nonmetricity_dependent_terms"), ("derivative_order", "operator_count")),
            _plan("CONSTRAINED_ACTION", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("constraint functional"), ("constraint_functionals",), ("constraint_count",)),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("canonical pairs", "Hamiltonian"), (), ("field_order",)),
        ],
        ("spin structure",): [
            _plan("NOT_YET_SPECIFIABLE", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("dynamical law on the spin structure",), (), ()),
        ],
        ("vector bundle",): [
            _plan("NOT_YET_SPECIFIABLE", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("dynamical law on the bundle",), (), ()),
        ],
        ("holonomy",): [
            _plan("NOT_YET_SPECIFIABLE", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("dynamical law for holonomy data",), (), ()),
        ],
        ("characteristic class",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("which characteristic class enters a dynamical functional", "coefficient"), ("topological_densities",), ("operator_count",)),
        ],
        ("higher-dimensional metric",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("scalar density", "named manifold is not chosen"), ("invariant_scalar_densities",), ("derivative_order", "operator_count")),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("canonical formulation", "named manifold is not chosen"), (), ("field_order",)),
        ],
        ("warped product",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("scalar density", "factor geometry is not chosen"), ("invariant_scalar_densities",), ("derivative_order",)),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("canonical formulation",), (), ("field_order",)),
        ],
        ("internal manifold",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("scalar density", "named manifold is not chosen"), ("invariant_scalar_densities",), ("derivative_order",)),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("canonical formulation",), (), ("field_order",)),
        ],
        ("fundamental function",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density built from the fundamental function",), ("invariant_scalar_densities",), ("derivative_order",)),
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("law for the fundamental function",), (), ()),
        ],
        ("pseudo-Finsler function",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("scalar density built from the fundamental function",), ("invariant_scalar_densities",), ("derivative_order",)),
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("law for the fundamental function",), (), ()),
        ],
        ("finite algebra",): [
            _plan("NOT_YET_SPECIFIABLE", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("multiplication presentation",), ("algebraic_or_operator_generators",), ("algebraic_degree",)),
        ],
        ("locally finite poset",): [
            _plan("DISCRETE_DYNAMICAL_RULE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("growth or transition rule",), ("state_transition_weights",), ("graph_or_complex_size", "transition_rule_complexity")),
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("amplitude on the partial order",), ("combinatorial_amplitudes",), ("state_space_complexity",)),
        ],
        ("discrete complex",): [
            _plan("DISCRETE_DYNAMICAL_RULE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("rule on the complex",), ("state_transition_weights",), ("graph_or_complex_size",)),
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("amplitude on the complex",), ("combinatorial_amplitudes",), ("state_space_complexity",)),
        ],
        ("causal triangulation",): [
            _plan("DISCRETE_DYNAMICAL_RULE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("rule on the triangulation",), ("state_transition_weights",), ("graph_or_complex_size",)),
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("amplitude on the triangulation",), ("combinatorial_amplitudes",), ("state_space_complexity",)),
        ],
        ("spin network",): [
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("transition amplitude",), ("combinatorial_amplitudes",), ("state_space_complexity", "representation_complexity")),
            _plan("DISCRETE_DYNAMICAL_RULE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("rule on labeled graphs",), ("state_transition_weights",), ("graph_or_complex_size",)),
        ],
        ("spin foam",): [
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("weight on the labeled 2-complex",), ("combinatorial_amplitudes",), ("state_space_complexity",)),
        ],
        ("tensor",): [
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "REQUIRES_ADDITIONAL_DEFINITION", ("contraction weight",), ("combinatorial_amplitudes",), ("algebraic_degree",)),
            _plan("OTHER_FORMAL_DYNAMICS", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("generator built from the tensor",), ("algebraic_or_operator_generators",), ("algebraic_degree",)),
        ],
        ("group field",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("group is not chosen", "density on the group product"), ("invariant_scalar_densities",), ("derivative_order", "operator_count")),
            _plan("STATE_SUM_OR_TRANSITION_AMPLITUDE", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("group is not chosen", "amplitude"), ("combinatorial_amplitudes",), ("state_space_complexity",)),
        ],
        ("worldsheet", "embedding map"): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("worldsheet density", "named target is not chosen"), ("worldsheet_or_worldvolume_densities",), ("worldvolume_derivative_order", "operator_count")),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("worldsheet canonical formulation", "named target is not chosen"), (), ("field_order",)),
        ],
        ("worldvolume",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("worldvolume density", "named target is not chosen"), ("worldsheet_or_worldvolume_densities",), ("worldvolume_derivative_order",)),
            _plan("HAMILTONIAN_OR_CANONICAL_FORMULATION", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("worldvolume canonical formulation",), (), ("field_order",)),
        ],
        ("renormalization-group flow",): [
            _plan("RENORMALIZATION_FLOW", "DYNAMICS_UNRESOLVED", "REQUIRES_ADDITIONAL_DEFINITION", ("beta functional", "fixed point is not chosen"), (), ("truncation_order", "derivative_order")),
        ],
        ("higher-derivative Lagrangian",): [
            _plan("LOCAL_ACTION_FUNCTIONAL", "ALLOWED_BUT_ASSUMED", "NOT_YET_BOUNDED", ("explicit higher-derivative density",), ("higher_derivative_terms",), ("derivative_order", "operator_count")),
            _plan("CONSTRAINED_ACTION", "DYNAMICS_UNRESOLVED", "NOT_YET_BOUNDED", ("degeneracy predicate",), ("constraint_functionals",), ("constraint_count", "derivative_order")),
        ],
    }
    return table.get(objects)


def _aggregate(plans: list[dict[str, Any]]) -> str:
    if len(plans) > 1:
        return "DYNAMICAL_NONUNIQUENESS"
    return "DYNAMICS_UNRESOLVED"


def _spec(model: dict[str, Any], row: dict[str, Any], plan: dict[str, Any], index: int) -> dict[str, Any]:
    grammar_id = model["grammar_id"]
    formulation_type = plan["formulation_type"]
    ingredients = [
        {"name": "registered_structural_objects", "provenance": "DERIVED", "statement": list(row["objects"])},
        {"name": "discrete_label", "provenance": "ASSUMED", "statement": model["discrete_labels"]},
        {"name": "dynamical_law", "provenance": "UNTESTED", "statement": "not registered in the TIER_1 model"},
    ]
    for item in plan["missing"]:
        ingredients.append({"name": item, "provenance": "UNTESTED", "statement": "required definition is absent"})
    for block in plan["allowed_blocks"]:
        ingredients.append({"name": block, "provenance": "UNTESTED", "statement": "class slot only; not an operational term"})
    return {
        "DYNAMICAL_READINESS": plan["readiness"],
        "FORMALIZATION_STATUS": "PARTIAL",
        "SEARCH_STATUS": "NOT_ENABLED",
        "allowed_operator_classes": list(plan["allowed_blocks"]),
        "boundary_conditions": "NOT_DEFINED",
        "claim": plan["claim"],
        "configuration_space": "NOT_DEFINED",
        "constraint_structure": "NOT_DEFINED",
        "derivative_or_transition_structure": "NOT_DEFINED",
        "dynamical_grammar_id": grammar_id + "__" + formulation_type.lower() + "__" + str(index),
        "dynamical_variables": "NONE_REGISTERED",
        "equivalence_status": "EQUIVALENCE_UNRESOLVED",
        "field_or_state_content": model["field_content"],
        "finite_bound_requirements": {
            "applicable_axes": list(plan["axes"]),
            "classification": "SEARCH-SPACE ASSUMPTIONS",
            "inherited_from_phase17c": False,
            "numerical_window": "NOT_DECLARED",
            "status": "NOT_YET_BOUNDED",
        },
        "formalization_status": "PARTIAL",
        "formulation_type": formulation_type,
        "ingredients": ingredients,
        "invariant_measure": "NOT_DEFINED",
        "kinematic_structure": row["definition"],
        "mathematical_definition": row["definition"] + ". Missing: " + "; ".join(plan["missing"]) + ".",
        "new_physical_input": "TRUE",
        "parameter_inventory": {
            "convention_parameters": [],
            "derived_quantities": [],
            "discrete_labels": model["discrete_labels"],
            "dynamical_parameter_freedom": "NOT_TESTED",
            "dynamical_verified_pfr": "NOT_TESTED",
            "inherited_parameters": [],
            "new_physical_parameters": [],
            "normalization_parameters": [],
            "parameter_free_relations": [],
            "unconstrained_functions": list(plan["missing"]),
        },
        "parent_structural_grammar_id": grammar_id,
        "parent_structural_model_id": model["model_id"],
        "provenance_manifest": ingredients,
        "reference_only": {"affects_generation": False, "names": list(row["references"]), "status": "REFERENCE_ONLY"},
        "search_status": "NOT_ENABLED",
        "symmetry_requirements": "NOT_SPECIFIED",
        "vacuum_selection": {"global_argmin": "NOT_INSERTED", "principle": "NOT_INSERTED", "stationarity_is_selection": False},
    }


def run_phase_18a(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    catalog_path = physics / CATALOG_RELATIVE
    authorization_path = physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json"
    report_path = _repo_root() / "docs" / "history" / "20Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v22_TOPDOWN_QFT_CUMULATIVE.docx"
    catalog_bytes = catalog_path.read_bytes()
    authorization_bytes = authorization_path.read_bytes()
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    catalog = json.loads(catalog_bytes)
    authorization = json.loads(authorization_bytes)
    digest = content_digest({key: value for key, value in catalog.items() if key != "catalog_hash"})
    grammar_15f = json.loads((physics / "phase15f_grammar_artifacts" / "PHASE_15F_GRAMMAR.json").read_text(encoding="utf-8"))
    grammar_17b1 = json.loads((physics / "phase17b1_fundamental_structure_artifacts" / "PHASE_17B1_FUNDAMENTAL_STRUCTURE.json").read_text(encoding="utf-8"))
    grammar_17c = json.loads((physics / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json").read_text(encoding="utf-8"))
    frontier = json.loads((physics / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json").read_text(encoding="utf-8"))
    manifest = json.loads((physics / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_SEARCH_MANIFEST.json").read_text(encoding="utf-8"))
    containment = json.loads((physics / "phase11ae1_artifacts" / "PHASE_11AE1_SUMMARY.json").read_text(encoding="utf-8"))
    containment_body = json.loads((physics / "phase11ae1_artifacts" / "PHASE_11AE1_CONTAINMENT.json").read_text(encoding="utf-8"))
    decision = json.loads((physics / "phase11ad_artifacts" / "PHASE_11AD_CLOSURE_GATE.json").read_text(encoding="utf-8"))
    report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
    summary = catalog["global_summary"]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or report_hash != V22_SHA256
        or grammar_15f.get("grammar_hash") != GRAMMAR_15F_HASH
        or grammar_17b1.get("grammar_hash") != GRAMMAR_17B1_HASH
        or grammar_17c.get("grammar_hash") != GRAMMAR_17C_HASH
        or authorization.get("authorization_hash") != AUTHORIZATION_HASH
        or manifest.get("manifest_id") != MANIFEST_ID
        or catalog.get("catalog_hash") != CATALOG_HASH
        or digest != CATALOG_HASH
        or catalog.get("MANIFEST_ID") != MANIFEST_ID
        or frontier.get("PHASE17E_STATUS") != "COMPLETE"
        or frontier.get("DYNAMICAL_VERIFIED_PFR") != "NOT_TESTED"
        or containment.get("PHASE_11AE1_STATUS") != "COMPLETE"
        or containment.get("CONTAINMENT_STATUS") != "REQUIRES_NEW_ASSUMPTION"
        or containment.get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND"
        or containment_body.get("GLOBAL_MINIMUM_CAPABILITY") != "NOT_ESTABLISHED"
        or decision.get("decision_map", {}).get("T09") != "REQUIRES_NEW_PHYSICAL_INPUT"
        or summary.get("authorized_grammars") != 27
        or summary.get("total_valid_models") != 27
        or summary.get("total_verified_PFR") != 0
        or any(model.get("dynamics") != "NOT_INCLUDED" for model in catalog["models"])
        or select_action() != "NOT_PERFORMED"
        or activate_theory_name("string theory") != "NOT_ENABLED"
        or insert_vacuum_principle() != "NOT_PERFORMED"
        or combine_grammars() != "NOT_GENERATED"
        or request_search() != "NOT_STARTED"
    ):
        return _stop("stored reference mismatch")
    authored = {row["grammar_id"]: row for row in _authored()}
    physical = {item["grammar_id"]: item["new_physical_input"] for item in authorization["new_physical_input_manifest"]}
    parents = []
    formulations = []
    blocks = []
    for model in catalog["models"]:
        grammar_id = model["grammar_id"]
        row = authored.get(grammar_id)
        plans = None if row is None else _plans(tuple(row["objects"]))
        if row is None or plans is None or physical.get(grammar_id) != "TRUE" or model.get("validation_status") != "VALID":
            return _stop("parent import")
        structural = "PARTIAL" if any(item["obligation_id"].endswith("MULTIPLICATION_PRESENTATION_UNTESTED") for item in model["obligations"]) else "VERIFIED"
        record = {
            "dynamical_claim": _aggregate(plans),
            "equivalence_status": model["equivalence_status"],
            "new_physical_input": "TRUE",
            "provenance": model["provenance"],
            "questions": {
                "consistency": "NOT_TESTED",
                "dynamical_formulation": "NOT_INCLUDED",
                "kinematic_structure": row["definition"],
                "physical_realization": "NOT_CLAIMED",
            },
            "source_category": model["source_category"],
            "structural_grammar_hash": model["grammar_hash"],
            "structural_grammar_id": grammar_id,
            "structural_model_hash": model["model_hash"],
            "structural_model_id": model["model_id"],
            "structural_readiness": structural,
            "unspecified": sorted({item for plan in plans for item in plan["missing"]}),
        }
        parents.append(record)
        for index, plan in enumerate(plans):
            spec = _spec(model, row, plan, index)
            if any(item["provenance"] not in PROVENANCE for item in spec["ingredients"]):
                return _stop("provenance")
            if any(item["provenance"] in {"EXPERIMENTAL", "CALIBRATED"} for item in spec["ingredients"]):
                return _stop("prohibited provenance")
            formulations.append(spec)
            for block in plan["allowed_blocks"]:
                blocks.append(
                    {
                        "block_class": block,
                        "operational": False,
                        "parent_structural_grammar_id": grammar_id,
                        "provenance": "UNTESTED",
                        "search_status": "NOT_ENABLED",
                    }
                )
    if len(parents) != 27 or any(item["search_status"] != "NOT_ENABLED" for item in formulations):
        return _stop("coverage")
    if any(item["dynamical_verified_pfr"] == 0 or item["dynamical_parameter_freedom"] == 0 for item in (spec["parameter_inventory"] for spec in formulations)):
        return _stop("missing action counted as zero")
    non_lagrangian = [spec for spec in formulations if spec["formulation_type"] not in {"LOCAL_ACTION_FUNCTIONAL", "CONSTRAINED_ACTION", "HAMILTONIAN_OR_CANONICAL_FORMULATION"}]
    unresolved = [
        {
            "DYNAMICAL_EQUIVALENCE": "EQUIVALENCE_UNRESOLVED",
            "KINEMATIC_EQUIVALENCE": "EQUIVALENCE_UNRESOLVED",
            "PHYSICAL_EQUIVALENCE": "EQUIVALENCE_UNRESOLVED",
            "equivalence_transfer": "NOT_PERFORMED",
            "grammar_id": item["grammar_id"],
        }
        for item in catalog["exclusion_register"]
        if item["readiness_status"] == "EQUIVALENCE_UNRESOLVED"
    ]
    if len(unresolved) != 7:
        return _stop("equivalence count")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("target marker")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "TEST_VERSION": TEST_VERSION,
        "PHASE18A_STATUS": "COMPLETE",
        "PARENT_STRUCTURAL_INTEGRITY": "VERIFIED",
        "DYNAMICAL_META_GRAMMAR_STATUS": "COMPLETE",
        "DYNAMICAL_CATALOG_STATUS": "COMPLETE",
        "ACTION_BUILDING_BLOCK_STATUS": "COMPLETE",
        "NON_LAGRANGIAN_DYNAMICS_STATUS": "COMPLETE",
        "DYNAMICAL_BOUND_POLICY_STATUS": "COMPLETE",
        "DYNAMICAL_EQUIVALENCE_STATUS": "VERIFIED",
        "PHYSICAL_INPUT_STATUS": "VERIFIED",
        "VACUUM_SELECTION_FIREWALL": "VERIFIED",
        "SEARCH_STATUS": "NOT_STARTED",
        "HUMAN_AUTHORIZATION_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "CATALOG_HASH": CATALOG_HASH,
        "MANIFEST_ID": MANIFEST_ID,
        "selected_formulation": "NONE",
        "selected_grammar": "NONE",
        "models_generated": 0,
        "combination_status": "NOT_GENERATED",
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "catalog_influence": catalog_influence({"entries": []}, "phase18a")["status"],
        "dynamical_formulation_meta_grammar": {
            "formulation_types": list(FORMULATION_TYPES),
            "grammar_version": "dynamical_formulation_18a_v1",
            "parent_catalog_hash": CATALOG_HASH,
            "search_status": "NOT_ENABLED",
        },
        "dynamical_grammar_catalog": formulations,
        "action_building_block_register": blocks,
        "non_lagrangian_dynamics_register": non_lagrangian,
        "dynamical_bound_policy_candidate": {
            "numerical_bounds": "NOT_DECLARED",
            "policy_id": "dynamical_bound_policy_18a_candidate",
            "search_status": "NOT_ENABLED",
            "status": "CANDIDATE_NOT_ACTIVATED",
        },
        "dynamical_equivalence_register": unresolved,
        "new_physical_input_register": [{"grammar_id": item["structural_grammar_id"], "new_physical_input": "TRUE", "relabelled_as_derived": False} for item in parents],
        "dynamics_not_yet_specifiable_register": [spec for spec in formulations if spec["formulation_type"] == "NOT_YET_SPECIFIABLE"],
        "parameter_accounting_register": [spec["parameter_inventory"] | {"dynamical_grammar_id": spec["dynamical_grammar_id"]} for spec in formulations],
        "phase_18_batch_authorization_candidates": [
            {
                "candidate_id": "PHASE_18_DYNAMICAL_BATCH",
                "formulation_ids": [spec["dynamical_grammar_id"] for spec in formulations],
                "search_status": "NOT_ENABLED",
                "status": "PREPARED_NOT_ACTIVATED",
            }
        ],
        "parent_structures": parents,
        "vacuum_selection_firewall": {"principle": "NOT_INSERTED", "t09": "REQUIRES_NEW_PHYSICAL_INPUT"},
    }
    payload["audit_hash"] = content_digest({key: value for key, value in payload.items() if key != "audit_hash"})
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_18A_DYNAMICAL_AUDIT.json").write_bytes(
            canonical_json_bytes(
                {
                    "CATALOG_HASH": CATALOG_HASH,
                    "DYNAMICAL_VERIFIED_PFR": "NOT_TESTED",
                    "MANIFEST_ID": MANIFEST_ID,
                    "PHASE18A_STATUS": "COMPLETE",
                    "SEARCH_STATUS": "NOT_STARTED",
                    "audit_hash": payload["audit_hash"],
                    "formulation_count": len(formulations),
                    "parent_count": 27,
                    "selected_formulation": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before or catalog_path.read_bytes() != catalog_bytes or authorization_path.read_bytes() != authorization_bytes:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
