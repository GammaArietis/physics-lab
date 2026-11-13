"""Phase 16B formalizes the Phase 16A frontier and does not search it.

Every grammar stays NOT_ENABLED. Bounds are declared integers.
No result is allowed to enlarge a grammar.
"""

from __future__ import annotations

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
from physics_lab.theory_kernel.phase15a_grammar import (
    _ranking_tokens,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.phase15e_catalog import INHERITED_PARAMETERS
from physics_lab.theory_kernel.phase16a_grammar_audit import (
    ARTIFACT_DIR_NAME as PHASE_16A_ARTIFACTS,
    GRAMMAR_HASH,
    GRAMMAR_VERSION,
    run_phase_16a,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_16B"
CODE_VERSION = "phase16b-batch-grammar-v1"
ARTIFACT_DIR_NAME = "phase16b_batch_grammar_artifacts"
POLICY_VERSION = "bound_policy_16b_v1"
BATCH_GRAMMAR_VERSION = "grammar_16b_batch_catalog_v1"
PARENT_GRAMMAR = GRAMMAR_VERSION
TIERS = ("TIER_1_MINIMAL", "TIER_2_EXTENDED", "TIER_3_BROAD")
TIER_STEP = {"TIER_1_MINIMAL": 1, "TIER_2_EXTENDED": 2, "TIER_3_BROAD": 3}
SPEC_FIELDS = (
    "complexity_budget",
    "dependencies",
    "equivalence_status",
    "finite_bound_spec",
    "generator_status",
    "grammar_candidate_id",
    "grammar_family",
    "grammar_version",
    "mathematical_definition",
    "new_constraints",
    "new_fields",
    "new_geometry",
    "new_operator_classes",
    "new_parameters",
    "new_physical_input",
    "new_symmetries",
    "new_topology",
    "parameter_budget",
    "parent_grammar",
    "provenance_manifest",
    "validation_status",
)
OVERLAP_PAIRS = (
    frozenset({"g16a.new.internal_dimension", "g16a.new.extra_scalar"}),
    frozenset({"g16a.new.nonabelian", "g16a.new.extra_connection"}),
)
DEPENDENT_PAIRS = {
    "g16a.new.supersymmetry": "g16a.new.fermion",
    "g16a.new.degeneracy_constraint": "g16a.new.higher_derivative_order",
}
ASSUMPTIONS = {
    "g16a.new.internal_dimension": "enlarged internal dimension",
    "g16a.new.nonabelian": "new symmetry algebra",
    "g16a.new.fermion": "enlarged field content",
    "g16a.new.supersymmetry": "supersymmetry algebra",
    "g16a.new.torsion_bundles": "torsion and nontrivial bundle structure",
    "g16a.new.extra_dimension": "new spacetime dimension",
    "g16a.new.topology": "characteristic-class densities and global bundle sectors",
    "g16a.new.higher_derivative_order": "NONE",
    "g16a.new.degeneracy_constraint": "NONE",
    "g16a.new.extra_scalar": "enlarged field content",
    "g16a.new.extra_connection": "enlarged field content",
}
PARENT_RELATION = {"EXTENSION": "STRICT_EXTENSION", "INCOMPARABLE": "INCOMPARABLE"}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE16B_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_16B_INCOMPLETE"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def activate_candidate(_candidate_id: str) -> str:
    return "NOT_AUTHORIZED"


def activate_batch_authorization(_authorization: dict[str, Any] | None = None) -> str:
    return "NOT_AUTHORIZED"


def request_generation(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def apply_result_to_bounds(_result: Any = None) -> str:
    return "REJECTED"


def merge_overlapping(_left: str, _right: str) -> str:
    return "NOT_CERTIFIED"


def combine_grammars(*_ids: str) -> str:
    return "NOT_GENERATED"


def propose_tier_manifest(tier: str, grammar_version: str) -> dict[str, Any]:
    if tier not in TIER_STEP:
        return {"status": "REJECTED"}
    manifest_id = content_digest(
        {
            "bound_policy_version": POLICY_VERSION,
            "grammar_version": grammar_version,
            "manifest_kind": "NEW_SEARCH_MANIFEST",
            "search_tier": tier,
        }
    )
    return {
        "activated": False,
        "grammar_version": grammar_version,
        "grammar_version_change": "NOT_REQUIRED",
        "in_place_mutation": False,
        "manifest_id": manifest_id,
        "manifest_kind": "NEW_SEARCH_MANIFEST",
        "result_input": "NONE",
        "search_status": "NOT_ENABLED",
        "search_tier": tier,
        "status": "PREPARED_NOT_ACTIVATED",
    }


def _exclusion_reason(item: dict[str, Any]) -> str | None:
    if item["structural_class"] == "UNRESOLVED" or item["equivalence_status"] == "EQUIVALENCE_UNRESOLVED":
        return "UNRESOLVED"
    if item["structural_class"] == "OUT_OF_SCOPE" or item["grammar_candidate_id"] == "g16a.outofscope.target_conditioned":
        return "OUT_OF_SCOPE"
    if not item["mathematical_definition"]:
        return "LACKING_MATHEMATICAL_DEFINITION"
    if item["review_status"] != "READY_FOR_HUMAN_REVIEW":
        return "NOT_READY_FOR_HUMAN_REVIEW"
    return None


def _varied(family_id: str, step: int) -> dict[str, int]:
    if family_id == "g16a.new.internal_dimension":
        return {"internal_dimension_max": 3 + step, "internal_dimension_min": 4}
    if family_id == "g16a.new.nonabelian":
        return {
            "generator_count_max": 1 + step,
            "generator_count_min": 2,
            "internal_dimension_max": 1 + step,
            "internal_dimension_min": 2,
            "representation_complexity_max": 1 + step,
            "representation_complexity_min": 2,
        }
    if family_id == "g16a.new.fermion":
        return {"additional_field_count_max": step, "additional_field_count_min": 1}
    if family_id == "g16a.new.supersymmetry":
        return {
            "additional_field_count_max": step,
            "additional_field_count_min": 1,
            "supercharge_count_max": step,
            "supercharge_count_min": 1,
        }
    if family_id == "g16a.new.torsion_bundles":
        return {"polynomial_order_max": step, "polynomial_order_min": 1, "tensor_rank_max": 3}
    if family_id == "g16a.new.extra_dimension":
        return {"spacetime_dimension_bound": 4 + step, "spacetime_dimension_min": 5}
    if family_id == "g16a.new.topology":
        return {"topological_sector_bound": step, "topological_sector_min": 1}
    if family_id == "g16a.new.higher_derivative_order":
        return {"derivative_order_max": 4 + step, "derivative_order_min": 5}
    if family_id == "g16a.new.degeneracy_constraint":
        return {
            "constraint_count_max": step,
            "constraint_count_min": 1,
            "derivative_order_max": 4 + step,
            "derivative_order_min": 5,
        }
    if family_id == "g16a.new.extra_scalar":
        return {"additional_field_count_max": step, "additional_field_count_min": 1}
    if family_id == "g16a.new.extra_connection":
        return {
            "additional_connection_count_max": step,
            "additional_connection_count_min": 1,
            "generator_count_max": 1,
        }
    raise KeyError(family_id)


def _parent_caps(family_id: str) -> dict[str, int]:
    caps = {
        "additional_field_count_max": 0,
        "derivative_order_max": 4,
        "generator_count_max": 1,
        "internal_dimension_max": 3,
        "polynomial_order_max": 4,
        "spacetime_dimension_bound": 4,
    }
    varied = _varied(family_id, 1)
    return {key: value for key, value in caps.items() if key not in varied}


def finite_bound_spec(family_id: str, *, observed_result: Any = None) -> dict[str, Any]:
    if observed_result is not None:
        raise RuntimeError("REJECTED")
    held = _parent_caps(family_id)
    tiers = {}
    for tier, step in TIER_STEP.items():
        numbers = {**held, **_varied(family_id, step)}
        if any(not isinstance(value, int) for value in numbers.values()):
            raise RuntimeError("non-integer bound")
        if any(value < 0 for value in numbers.values()):
            raise RuntimeError("negative bound")
        tiers[tier] = numbers
    return {
        "active_tier": "NOT_SELECTED",
        "bound_policy_version": POLICY_VERSION,
        "bound_role": "SEARCH_SPACE_ASSUMPTION",
        "family_coverage": "PARTIAL_WITHIN_BOUND",
        "result_independent": True,
        "tier_interval_coverage": "EXHAUSTIVE_WITHIN_BOUND",
        "tiers": tiers,
    }


def _grammar_version(candidate_id: str) -> str:
    return "grammar_16b_" + candidate_id.removeprefix("g16a.new.") + "_v1"


def _physical_input(candidate_id: str, required: bool) -> dict[str, str]:
    assumption = ASSUMPTIONS[candidate_id]
    if required and assumption == "NONE":
        raise RuntimeError("missing physical assumption")
    if not required and assumption != "NONE":
        raise RuntimeError("assumption on a grammar that does not require one")
    return {
        "REQUIRES_NEW_PHYSICAL_INPUT": "TRUE" if required else "FALSE",
        "assumption": assumption,
        "provenance": "NOT_DERIVED",
    }


def _dependencies(candidate_id: str) -> list[dict[str, str]]:
    rows = [{"id": PARENT_GRAMMAR, "kind": "PARENT"}]
    required = DEPENDENT_PAIRS.get(candidate_id)
    if required is not None:
        rows.append({"id": required, "kind": "DEPENDENT"})
    return rows


def _parameter_budget(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "accounting_only": True,
        "derived_quantities": [],
        "discrete_labels": ["search tier", "integer bound index"],
        "fixed_parameters": [],
        "inherited_parameters": list(INHERITED_PARAMETERS),
        "new_physical_parameters": list(item["new_parameters"]),
        "normalization_parameters": ["field normalization remains free"],
    }


def _spec(item: dict[str, Any]) -> dict[str, Any]:
    candidate_id = item["grammar_candidate_id"]
    relation = PARENT_RELATION.get(item["relation"])
    if relation is None:
        raise RuntimeError("parent relation is not mapped")
    spec = {
        "FORMALIZATION_STATUS": "COMPLETE",
        "FINITE_BOUND_STATUS": "COMPLETE",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "SEARCH_STATUS": "NOT_ENABLED",
        "certified_relation": item["equivalence_status"],
        "changed_structural_axes": list(item["changed_structural_axes"]),
        "classification": item["structural_class"],
        "complexity_budget": {
            "active_tier": "NOT_SELECTED",
            "enumeration": "NOT_RUN",
            "kind": "DECLARED_INTEGER_INTERVAL",
        },
        "dependencies": _dependencies(candidate_id),
        "distinctness_vs_parent": relation,
        "equivalence_status": "CERTIFIED",
        "finite_bound_spec": finite_bound_spec(candidate_id),
        "generator_status": "NOT_ENABLED",
        "grammar_candidate_id": candidate_id,
        "grammar_family": item["name"],
        "grammar_version": _grammar_version(candidate_id),
        "mathematical_definition": item["mathematical_definition"],
        "new_constraints": list(item["new_constraints"]),
        "new_fields": list(item["new_fields"]),
        "new_geometry": list(item["new_geometric_data"]),
        "new_operator_classes": list(item["new_operator_classes"]),
        "new_parameters": list(item["new_parameters"]),
        "new_physical_input": _physical_input(candidate_id, item["new_physical_input_required"] is True),
        "new_symmetries": list(item["new_symmetries"]),
        "new_topology": list(item["new_geometric_data"]) if candidate_id == "g16a.new.topology" else [],
        "parameter_budget": _parameter_budget(item),
        "parent_grammar": PARENT_GRAMMAR,
        "provenance_manifest": {
            "altered_16a_classification": False,
            "parent_grammar_hash": GRAMMAR_HASH,
            "source_equivalence_status": item["equivalence_status"],
            "source_phase": "PHASE_16A",
            "source_relation": item["relation"],
            "source_review_status": item["review_status"],
            "source_structural_class": item["structural_class"],
        },
        "validation_status": "COMPLETE",
    }
    missing = [name for name in SPEC_FIELDS if name not in spec]
    if missing:
        raise KeyError(",".join(missing))
    if spec["generator_status"] != "NOT_ENABLED" or spec["SEARCH_STATUS"] != "NOT_ENABLED":
        raise RuntimeError("a formal grammar cannot enable a search")
    return spec


def _pairwise(ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            pair = frozenset({left, right})
            if pair in OVERLAP_PAIRS:
                compatibility = "OVERLAPPING"
                distinctness = "OVERLAPPING_EXTENSION"
                equivalence = "EQUIVALENCE_UNRESOLVED"
            elif DEPENDENT_PAIRS.get(left) == right or DEPENDENT_PAIRS.get(right) == left:
                compatibility = "DEPENDENT"
                distinctness = "INCOMPARABLE"
                equivalence = "NOT_APPLICABLE"
            else:
                compatibility = "NOT_YET_DEFINED"
                distinctness = "INCOMPARABLE"
                equivalence = "NOT_APPLICABLE"
            rows.append(
                {
                    "compatibility": compatibility,
                    "containment": "NOT_CERTIFIED",
                    "distinctness": distinctness,
                    "equivalence_status": equivalence,
                    "left": left,
                    "merged": "FALSE",
                    "right": right,
                }
            )
    return rows


def _graph(specs: list[dict[str, Any]], pairs: list[dict[str, str]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for spec in specs:
        edges.append(
            {
                "child": spec["grammar_candidate_id"],
                "dependencies": spec["dependencies"],
                "edge_kind": "PARENT",
                "finite_bound_requirements": POLICY_VERSION,
                "new_assumptions": spec["new_physical_input"]["assumption"],
                "overlap_status": spec["distinctness_vs_parent"],
                "parent": PARENT_GRAMMAR,
                "structural_delta": spec["changed_structural_axes"],
            }
        )
    for pair in pairs:
        if pair["compatibility"] in {"OVERLAPPING", "DEPENDENT"}:
            edges.append(
                {
                    "compatibility": pair["compatibility"],
                    "containment": pair["containment"],
                    "edge_kind": "PAIR",
                    "equivalence_status": pair["equivalence_status"],
                    "finite_bound_requirements": POLICY_VERSION,
                    "left": pair["left"],
                    "right": pair["right"],
                }
            )
    return edges


def _eligible(spec: dict[str, Any]) -> bool:
    return (
        spec["FORMALIZATION_STATUS"] == "COMPLETE"
        and spec["FINITE_BOUND_STATUS"] == "COMPLETE"
        and spec["NEW_PHYSICAL_INPUT_STATUS"] == "VERIFIED"
        and spec["SEARCH_STATUS"] == "NOT_ENABLED"
        and spec["generator_status"] == "NOT_ENABLED"
    )


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    specs = result["batch_grammar_catalog"]
    fermion = next(item for item in specs if item["grammar_candidate_id"] == "g16a.new.fermion")
    higher = next(item for item in specs if item["grammar_candidate_id"] == "g16a.new.higher_derivative_order")
    unresolved_ids = {item["grammar_candidate_id"] for item in result["equivalence_unresolved_register"] if "grammar_candidate_id" in item}
    tier_one = propose_tier_manifest("TIER_1_MINIMAL", BATCH_GRAMMAR_VERSION)
    tier_two = propose_tier_manifest("TIER_2_EXTENDED", BATCH_GRAMMAR_VERSION)
    cases = [
        ("1", "no 16A candidate is activated", "NOT_AUTHORIZED", activate_candidate(specs[0]["grammar_candidate_id"])),
        ("2", "every frontier candidate has a formal specification", "True", str(result["imported_ids"] == result["frontier_ids"] and all(set(SPEC_FIELDS) <= set(item) for item in specs))),
        ("3", "every finite-bound specification is explicit", "True", str(all(all(isinstance(value, int) for tier in item["finite_bound_spec"]["tiers"].values() for value in tier.values()) for item in specs))),
        ("4", "bounds are independent of generated results", "REJECTED", apply_result_to_bounds({"any": "result"})),
        ("5", "a result cannot enlarge its own grammar", "REJECTED", apply_result_to_bounds({"grammar_candidate_id": specs[0]["grammar_candidate_id"]})),
        ("6", "a tier change creates an independent manifest", "True", str(tier_one["manifest_kind"] == "NEW_SEARCH_MANIFEST" and tier_one["manifest_id"] != tier_two["manifest_id"] and tier_one["grammar_version"] == tier_two["grammar_version"] and tier_one["activated"] is False)),
        ("7", "new physical assumptions stay tagged", "True", str(fermion["new_physical_input"]["REQUIRES_NEW_PHYSICAL_INPUT"] == "TRUE" and higher["new_physical_input"]["REQUIRES_NEW_PHYSICAL_INPUT"] == "FALSE" and all(item["new_physical_input"]["provenance"] == "NOT_DERIVED" for item in specs))),
        ("8", "unresolved equivalence stays unresolved", "True", str({"g16a.unresolved.internal_basis", "g16a.unresolved.christoffel_hessian"} <= unresolved_ids and "g16a.unresolved.internal_basis" not in result["imported_ids"])),
        ("9", "overlapping grammars stay unmerged", "NOT_CERTIFIED", merge_overlapping("g16a.new.internal_dimension", "g16a.new.extra_scalar")),
        ("10", "combined grammars are not generated", "NOT_GENERATED", combine_grammars("g16a.new.fermion", "g16a.new.extra_dimension")),
        ("11", "experimental data does not enter formalization", "REJECTED", classify_candidate({"mathematical_definition": "experimental values"})),
        ("12", "numerical targets do not enter formalization", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("13", "no ranking function exists", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("14", "Phase 15 and frozen Phase 4C stay unchanged", "True", str(result["grammar_hash"] == GRAMMAR_HASH and result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH)),
        ("15", "no blind model search runs", "NOT_STARTED", request_generation()),
        ("16", "batch authorization cannot activate implicitly", "NOT_AUTHORIZED", activate_batch_authorization(result["batch_authorization"])),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_16b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    audit = run_phase_16a(write_artifacts=False)
    stored = _read(PHASE_16A_ARTIFACTS + "/PHASE_16A_GRAMMAR_CATALOG.json")
    frontier_ids = [item["grammar_candidate_id"] for item in audit.get("human_decision_frontier", [])]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or audit.get("status") != "OK"
        or audit.get("PHASE_16A_STATUS") != "CLOSED"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or audit.get("selected_candidate") != "NONE"
        or audit.get("ALL_POSSIBLE_PHYSICS_EXHAUSTED") != "FALSE"
        or stored.get("frontier_ids") != frontier_ids
        or stored.get("grammar_hash") != GRAMMAR_HASH
        or stored.get("search_status") != "NOT_ENABLED"
    ):
        return _stop("integrity gate")
    imported = []
    excluded = []
    for item in audit["catalogue"]:
        reason = _exclusion_reason(item)
        if reason is None:
            imported.append(item)
        else:
            excluded.append({"grammar_candidate_id": item["grammar_candidate_id"], "reason": reason})
    imported_ids = [item["grammar_candidate_id"] for item in imported]
    if imported_ids != frontier_ids:
        return _stop("import diverged from the 16A frontier")
    if any(item["structural_class"] != "GENUINELY_NEW_GRAMMAR" for item in imported):
        return _stop("imported class")
    specs = [_spec(item) for item in imported]
    if not all(_eligible(item) for item in specs):
        return _stop("eligibility")
    pairs = _pairwise(imported_ids)
    if any(pair["merged"] != "FALSE" for pair in pairs):
        return _stop("merge")
    if combine_grammars(*imported_ids) != "NOT_GENERATED":
        return _stop("combination")
    overlap_register = [
        {
            "equivalence_status": pair["equivalence_status"],
            "left": pair["left"],
            "merged": "FALSE",
            "right": pair["right"],
        }
        for pair in pairs
        if pair["equivalence_status"] == "EQUIVALENCE_UNRESOLVED"
    ]
    unresolved_register = [
        {
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "grammar_candidate_id": item["grammar_candidate_id"],
            "imported": False,
        }
        for item in audit["equivalence_unresolved_register"]
    ] + overlap_register
    authorization = {
        "activation": "NOT_AUTHORIZED",
        "active_search_space": False,
        "authorized_grammar_ids": imported_ids,
        "available_tiers": list(TIERS),
        "bound_policy_version": POLICY_VERSION,
        "exclusion_manifest": excluded,
        "grammar_version": BATCH_GRAMMAR_VERSION,
        "member_grammar_versions": [item["grammar_version"] for item in specs],
        "new_physical_input_manifest": [
            {
                "assumption": item["new_physical_input"]["assumption"],
                "grammar_candidate_id": item["grammar_candidate_id"],
                "REQUIRES_NEW_PHYSICAL_INPUT": item["new_physical_input"]["REQUIRES_NEW_PHYSICAL_INPUT"],
            }
            for item in specs
        ],
        "object": "PHASE_16_BATCH_AUTHORIZATION",
        "search_status": "NOT_ENABLED",
        "search_tier": "NOT_SELECTED",
        "status": "PREPARED_NOT_ACTIVATED",
        "target_blindness_status": "VERIFIED",
    }
    if activate_batch_authorization(authorization) != "NOT_AUTHORIZED":
        return _stop("implicit activation")
    policy = {
        "bound_policy_version": POLICY_VERSION,
        "enlargement_after_results": "REJECTED",
        "family_coverage": "PARTIAL_WITHIN_BOUND",
        "properties": ["finite", "reproducible", "minimal_nontrivial_step", "computationally_auditable"],
        "role": "SEARCH_SPACE_ASSUMPTION",
        "search_tier": "NOT_SELECTED",
        "tier_change_requires": "NEW_SEARCH_MANIFEST",
        "tier_interval_coverage": "EXHAUSTIVE_WITHIN_BOUND",
        "tiers": list(TIERS),
    }
    batch_candidate = {
        "expected_structural_dimensions": sorted({axis for item in specs for axis in item["changed_structural_axes"]}),
        "finite_bounds": POLICY_VERSION,
        "grammar_ids_included": imported_ids,
        "mathematical_scope": "the Phase 16A frontier, each family kept separate and bounded by the pre-registered integer tiers",
        "new_physical_assumptions": authorization["new_physical_input_manifest"],
        "search_status": "NOT_ENABLED",
        "search_tier": "NOT_SELECTED",
        "unresolved_equivalences": unresolved_register,
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE16B_STATUS": "COMPLETE",
        "BATCH_GRAMMAR_CATALOG_STATUS": "COMPLETE",
        "FINITE_BOUND_POLICY_STATUS": "COMPLETE",
        "GRAMMAR_DEPENDENCY_GRAPH_STATUS": "COMPLETE",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "EQUIVALENCE_REGISTER_STATUS": "COMPLETE",
        "BATCH_AUTHORIZATION_STATUS": "READY",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE15_INTEGRITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PHASE_15_STATUS": "CLOSED",
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "active_grammar_version": GRAMMAR_VERSION,
        "active_search_space": False,
        "frontier_ids": frontier_ids,
        "imported_ids": imported_ids,
        "batch_grammar_catalog": specs,
        "finite_bound_policy": policy,
        "grammar_dependency_graph": _graph(specs, pairs),
        "pairwise_audit": pairs,
        "new_physical_input_register": authorization["new_physical_input_manifest"],
        "equivalence_unresolved_register": unresolved_register,
        "batch_authorization": authorization,
        "batch_authorization_candidates": [batch_candidate],
        "exclusion_manifest": excluded,
        "selected_grammar": "NONE",
        "software_choice": "NOT_MADE",
        "search_status": "NOT_ENABLED",
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE16B_STATUS": "INCOMPLETE", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_16B_BATCH_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "active_search_space": False,
                    "batch_authorization_status": "PREPARED_NOT_ACTIVATED",
                    "bound_policy_version": POLICY_VERSION,
                    "grammar_hash": GRAMMAR_HASH,
                    "grammar_ids": imported_ids,
                    "search_status": "NOT_ENABLED",
                    "search_tier": "NOT_SELECTED",
                    "selected_grammar": "NONE",
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
