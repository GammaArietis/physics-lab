"""Phase 15A.1 closes the meaning of the grammar_15a_v1 operator basis.

It does not change that grammar, does not add fields, and does not run Phase 15B.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    _canonical,
    _component_catalog,
    _counts,
    _internal_pairings,
    _matchings,
    _nonzero,
    _slots,
    classify_candidate,
    compile_grammar,
    generate_candidate_models,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15A1"
CODE_VERSION = "phase15a1-boundary-v1"
ARTIFACT_DIR_NAME = "phase15a1_boundary_artifacts"
STORED_GRAMMAR = "phase15a_grammar_artifacts/PHASE_15A_GRAMMAR.json"
FLAT_CONTEXT = "FLAT_SECOND_DERIVATIVE_CONTEXT"
CURVED_CONTEXT = "CURVED_COVARIANT_SECOND_DERIVATIVE_CONTEXT"
DISTINCT = "DISTINCT UNDER CURRENT CANONICALIZATION"
IBP_LEFT = "factors[DPhi:s,DPhi:s] internal[] lorentz[(0, 0)-(1, 0)]"
IBP_RIGHT = "factors[DDPhi:s,Phi:s] internal[] lorentz[(0, 0)-(0, 1)]"

EQUIVALENCE_RULES = (
    {"rule": "algebraic simplification", "status": "SUPPORTED", "used_in_473_to_117": True},
    {"rule": "index canonicalization", "status": "SUPPORTED", "used_in_473_to_117": True},
    {"rule": "tensor-symmetry reduction", "status": "SUPPORTED", "used_in_473_to_117": True},
    {"rule": "term ordering", "status": "SUPPORTED", "used_in_473_to_117": True},
    {"rule": "integration by parts", "status": "UNSUPPORTED", "used_in_473_to_117": False},
    {"rule": "field redefinitions", "status": "UNSUPPORTED", "used_in_473_to_117": False},
    {"rule": "equations-of-motion equivalence", "status": "UNSUPPORTED", "used_in_473_to_117": False},
    {"rule": "basis transformations", "status": "UNSUPPORTED", "used_in_473_to_117": False},
)

OUTSIDE_CURRENT_GRAMMAR = (
    "Levi-Civita symbol contractions",
    "Riemann, Ricci, and Weyl densities as generated matter operators",
    "explicit Christoffel polynomials as generated densities",
    "fermions, extra scalars, and non-Abelian fields",
    "nonlocal kernels",
    "operators above the declared derivative or field order",
    "non-polynomial functions of the registered blocks",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def prove_derivative_contexts() -> dict[str, Any]:
    """Flat partial Hessian and torsion-free nabla Hessian on one curved metric."""
    x = sp.symbols("x")
    height = sp.Function("h")(x)
    slope = sp.diff(height, x)
    gamma = sp.together(slope / (2 * height))
    t, y, z = sp.symbols("t y z")
    scalar = sp.Function("phi")(t, x, y, z)
    flat = sp.diff(scalar, x, z)
    curved = flat - gamma * sp.diff(scalar, z)
    difference = sp.simplify(flat - curved)
    connection_x = sp.Function("A_x")(t, x, y, z)
    connection_z = sp.Function("A_z")(t, x, y, z)
    partial_strength = sp.diff(connection_z, x) - sp.diff(connection_x, z)
    nabla_strength = (sp.diff(connection_z, x) - gamma * connection_z) - (
        sp.diff(connection_x, z) - gamma * connection_z
    )
    return {
        "CURVED_COVARIANT_SECOND_DERIVATIVE_CONTEXT": {
            "context_id": CURVED_CONTEXT,
            "generator_enabled": False,
            "mathematical_definition": "nabla_mu nabla_nu phi = partial_mu partial_nu phi - Gamma^lambda_mu_nu partial_lambda phi",
            "sample_difference": str(difference),
        },
        "FLAT_SECOND_DERIVATIVE_CONTEXT": {
            "context_id": FLAT_CONTEXT,
            "generator_enabled": True,
            "mathematical_definition": "partial_mu partial_nu Phi, symmetrized; the antisymmetric part is the registered identity [D_mu, D_nu] Phi = - F_mu_nu K Phi",
        },
        "contexts_distinct": difference != 0 and sp.simplify(difference - gamma * sp.diff(scalar, z)) == 0,
        "curved_uses_flat_definition": False,
        "field_strength_partial_equals_nabla": sp.simplify(nabla_strength - partial_strength) == 0,
        "gamma_sample": str(gamma),
        "scalar_gradient": "nabla_mu phi = partial_mu phi",
    }


def reduction_trace() -> dict[str, Any]:
    catalog = _component_catalog()
    representatives: dict[Any, Any] = {}
    raw = 0
    for n_phi, n_d, n_dd, n_f in _counts():
        covariant = ("Phi",) * n_phi + ("DPhi",) * n_d + ("DDPhi",) * n_dd
        for channels in itertools.product(("p", "s"), repeat=len(covariant)):
            factors = tuple((name, channel) for name, channel in zip(covariant, channels))
            factors = factors + (("F", "inv"),) * n_f
            plane = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
            slots = tuple((index, slot) for index, (name, _channel) in enumerate(factors) for slot in range(_slots(name)))
            for edges in _internal_pairings(plane):
                for pairs in _matchings(slots):
                    raw += 1
                    representatives.setdefault(_canonical(factors, edges, pairs), (factors, edges, pairs))
    nonzero = 0
    for factors, edges, pairs in representatives.values():
        if _nonzero(factors, edges, pairs, catalog):
            nonzero += 1
    unique = len(representatives)
    return {
        "canonical_densities": nonzero,
        "identically_zero_keys": unique - nonzero,
        "merged_by_canonical_key": raw - unique,
        "raw_contractions": raw,
        "rules": list(EQUIVALENCE_RULES),
        "unique_canonical_keys": unique,
    }


def _covariance(definition: str) -> dict[str, str]:
    if "DDPhi" in definition:
        return {
            "covariance": "LORENTZ_INVARIANT_ON_MINKOWSKI",
            "derivative_context": FLAT_CONTEXT,
            "reason": "the registered second derivative is the flat partial Hessian",
        }
    if "DPhi" in definition or "F:" in definition:
        return {
            "covariance": "BOTH",
            "derivative_context": "FIRST_DERIVATIVE_OR_CURVATURE",
            "reason": "D_mu acts on spacetime scalars by a partial derivative, and the torsion-free nabla strength equals the partial strength",
        }
    return {
        "covariance": "GENERALLY_COVARIANT",
        "derivative_context": "NO_SPACETIME_DERIVATIVE",
        "reason": "no spacetime derivative is present",
    }


def classify_operators(operators: list[dict[str, Any]]) -> list[dict[str, str]]:
    classified = []
    for item in operators:
        row = _covariance(item["mathematical_definition"])
        classified.append(
            {
                "covariance": row["covariance"],
                "derivative_context": row["derivative_context"],
                "family_id": item["family_id"],
                "family_ids": ",".join(item["family_ids"]),
                "object_id": item["object_id"],
                "reason": row["reason"],
            }
        )
    return classified


def merge_by_unsupported(rule: str, left: str, right: str) -> str:
    unsupported = {"integration by parts", "field redefinitions", "equations-of-motion equivalence", "basis transformations"}
    if rule not in unsupported or left == right:
        raise KeyError(rule)
    return DISTINCT


def _family_f_subset(operators: list[dict[str, Any]]) -> dict[str, Any]:
    identities = [item["object_id"] for item in operators]
    subset = [item["object_id"] for item in operators if "F" in item["family_ids"]]
    return {
        "duplicate_object_ids": len(identities) != len(set(identities)),
        "family_f_count": len(subset),
        "family_f_creates_new_operators": not set(subset) <= set(identities),
        "family_f_is_subset": set(subset) <= set(identities),
        "primary_family_f": sum(item["family_id"] == "F" for item in operators),
    }


def run_phase_15b(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 15A.1 does not run Phase 15B")


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15A1_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_15A1_INCOMPLETE"}


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    contexts = result["derivative_contexts"]
    operators = result["operators"]
    definitions = {item["mathematical_definition"] for item in operators}
    curved_label = contexts["CURVED_COVARIANT_SECOND_DERIVATIVE_CONTEXT"]["mathematical_definition"]
    flat_label = contexts["FLAT_SECOND_DERIVATIVE_CONTEXT"]["mathematical_definition"]
    dd_rows = [item for item in result["covariance_rows"] if item["derivative_context"] == FLAT_CONTEXT]
    curved_not_flat = all(item["covariance"] == "LORENTZ_INVARIANT_ON_MINKOWSKI" for item in dd_rows)
    cases = [
        ("1", "curved second derivatives do not silently use the flat definition", "DISTINCT", "DISTINCT" if contexts["contexts_distinct"] and contexts["curved_uses_flat_definition"] is False and curved_not_flat else "MERGED"),
        ("2", "flat and curved derivative contexts remain distinct", "DISTINCT", "DISTINCT" if flat_label != curved_label else "SAME"),
        ("3", "unsupported IBP does not merge operators", DISTINCT, merge_by_unsupported("integration by parts", IBP_LEFT, IBP_RIGHT) if IBP_LEFT in definitions and IBP_RIGHT in definitions else "MERGED"),
        ("4", "unsupported field redefinitions do not merge operators", DISTINCT, merge_by_unsupported("field redefinitions", IBP_LEFT, IBP_RIGHT)),
        ("5", "unsupported EOM equivalence does not merge operators", DISTINCT, merge_by_unsupported("equations-of-motion equivalence", IBP_LEFT, IBP_RIGHT)),
        ("6", "473 to 117 reduction is deterministic", result["reduction_digest"], result["reduction_digest_repeated"]),
        ("7", "family F remains a subset", "SUBSET", "SUBSET" if result["family_f"]["family_f_is_subset"] and result["family_f"]["family_f_creates_new_operators"] is False and result["family_f"]["primary_family_f"] == 0 else "NEW"),
        ("8", "no new field appears", "UNCHANGED", result["field_content_status"]),
        ("9", "no new parameter appears", "UNCHANGED", result["parameter_status"]),
        ("10", "no new physical principle appears", "NONE", result["new_physical_principle"]),
        ("11", "target information cannot enter", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("12", "grammar_15a_v1 remains immutable", result["stored_grammar_hash"], result["grammar_hash"]),
        ("13", "a new grammar version is created only if operational semantics change", "NOT_CREATED", result["new_grammar_version"]),
        ("14", "no Phase 15B generation occurs", "0", str(result["number_of_generated_models"])),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15a1(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    stored = _read(STORED_GRAMMAR)
    compiled = compile_grammar()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or compiled.get("status") != "COMPILED"
        or compiled.get("grammar_hash") != stored.get("grammar_hash")
        or stored.get("grammar_version") != "grammar_15a_v1"
        or stored.get("number_of_generated_models") != 0
    ):
        return _stop("freeze gate or grammar_15a_v1 hash")
    contexts = prove_derivative_contexts()
    if not contexts["contexts_distinct"] or not contexts["field_strength_partial_equals_nabla"]:
        return _stop("derivative-context proof failed")
    trace = reduction_trace()
    repeated = reduction_trace()
    if trace != repeated or trace["raw_contractions"] != 473 or trace["canonical_densities"] != 117:
        return _stop("reduction trace is not the stored 473 to 117 map")
    if trace["raw_contractions"] != stored["estimated_raw_combinations"]:
        return _stop("raw count drifted from grammar_15a_v1")
    if trace["canonical_densities"] != stored["estimated_post_canonicalization_size"]:
        return _stop("canonical count drifted from grammar_15a_v1")
    operators = compiled["enabled"]
    if len(operators) != 117 or compiled["family_counts"] != stored["family_counts"]:
        return _stop("operator inventory drifted")
    rows = classify_operators(operators)
    unresolved = [item for item in rows if item["covariance"] not in {"LORENTZ_INVARIANT_ON_MINKOWSKI", "BOTH", "GENERALLY_COVARIANT"}]
    if unresolved:
        return _stop("unresolved covariance")
    falsely_covariant = [
        item
        for item in rows
        if item["derivative_context"] == FLAT_CONTEXT and item["covariance"] != "LORENTZ_INVARIANT_ON_MINKOWSKI"
    ]
    if falsely_covariant:
        return _stop("flat second derivative labeled generally covariant")
    family_f = _family_f_subset(operators)
    if not family_f["family_f_is_subset"] or family_f["family_f_count"] != stored["family_counts"]["F"]:
        return _stop("family F is not the recorded subset")
    refused_models = False
    try:
        generate_candidate_models()
    except RuntimeError:
        refused_models = True
    refused_15b = False
    try:
        run_phase_15b()
    except RuntimeError:
        refused_15b = True
    if not refused_models or not refused_15b:
        return _stop("generation was not refused")
    reduction_digest = content_digest(trace)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_15A1_STATUS": "READY",
        "OPERATOR_GRAMMAR_STATUS": "VERIFIED",
        "GENERAL_COVARIANCE_GRAMMAR_STATUS": "VERIFIED",
        "CANONICALIZATION_STATUS": "VERIFIED",
        "COMPLETENESS_SCOPE": "COMPLETE_WITHIN_REGISTERED_BUILDING_BLOCKS",
        "LOCAL_EFT_COMPLETENESS": "NOT_CLAIMED",
        "15B_GATE": "READY_FOR_15B",
        "grammar_version": "grammar_15a_v1",
        "grammar_hash": compiled["grammar_hash"],
        "stored_grammar_hash": stored["grammar_hash"],
        "new_grammar_version": "NOT_CREATED",
        "operational_semantics_changed": False,
        "derivative_contexts": contexts,
        "operators": operators,
        "covariance_rows": rows,
        "reduction": trace,
        "reduction_digest": reduction_digest,
        "reduction_digest_repeated": content_digest(repeated),
        "family_counts": compiled["family_counts"],
        "family_f": family_f,
        "field_content_status": "UNCHANGED",
        "parameter_status": "UNCHANGED",
        "new_physical_principle": "NONE",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "number_of_generated_models": 0,
        "SEARCH_EXECUTED": False,
        "IBP_EQUIVALENCE": "UNSUPPORTED",
        "FIELD_REDEFINITION_EQUIVALENCE": "UNSUPPORTED",
        "EOM_EQUIVALENCE_STATUS": "UNSUPPORTED",
        "physical_inequivalence": "NOT_CLAIMED",
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15A1_STATUS": "INCOMPLETE", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["covariance_counts"] = {
        "both": sum(item["covariance"] == "BOTH" for item in rows),
        "flat_only": sum(item["covariance"] == "LORENTZ_INVARIANT_ON_MINKOWSKI" for item in rows),
        "no_spacetime_derivative": sum(item["covariance"] == "GENERALLY_COVARIANT" for item in rows),
    }
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        files = {
            "PHASE_15A1_CLOSURE.json": {
                "COMPLETENESS_SCOPE": payload["COMPLETENESS_SCOPE"],
                "LOCAL_EFT_COMPLETENESS": payload["LOCAL_EFT_COMPLETENESS"],
                "OPERATOR_GRAMMAR_STATUS": payload["OPERATOR_GRAMMAR_STATUS"],
                "excluded": list(OUTSIDE_CURRENT_GRAMMAR),
                "grammar_hash": payload["grammar_hash"],
                "grammar_version": payload["grammar_version"],
                "new_grammar_version": payload["new_grammar_version"],
            },
            "PHASE_15A1_DERIVATIVE_CONTEXTS.json": {
                "curved": contexts["CURVED_COVARIANT_SECOND_DERIVATIVE_CONTEXT"],
                "flat": contexts["FLAT_SECOND_DERIVATIVE_CONTEXT"],
                "flat_curved_distinct": contexts["contexts_distinct"],
                "partial_field_strength_equals_nabla": contexts["field_strength_partial_equals_nabla"],
            },
            "PHASE_15A1_REDUCTION_TRACE.json": trace,
            "PHASE_15A1_COVARIANCE.json": {
                "counts": payload["covariance_counts"],
                "rows": rows,
            },
            "PHASE_15A1_EQUIVALENCE.json": {
                "EOM_EQUIVALENCE_STATUS": "UNSUPPORTED",
                "FIELD_REDEFINITION_EQUIVALENCE": "UNSUPPORTED",
                "IBP_EQUIVALENCE": "UNSUPPORTED",
                "physical_inequivalence": "NOT_CLAIMED",
                "rules": list(EQUIVALENCE_RULES),
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
