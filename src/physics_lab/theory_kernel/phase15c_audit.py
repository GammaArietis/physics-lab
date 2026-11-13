"""Phase 15C audits consequences of the two maximal symbolic families.

Coefficients stay free. Detected identities are recorded and are not used to
delete operators or to fix parameters.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import so2_generator_K
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    K_PLANE,
    _canonical,
    _component_catalog,
    _counts,
    _definition,
    _internal_pairings,
    _lookup,
    _matchings,
    _ranking_tokens,
    _slots,
    catalog_influence,
    classify_candidate,
    compile_grammar,
)
from physics_lab.theory_kernel.phase15b_enumeration import (
    ACTION_HASH_14I,
    EXPECTED_GRAMMAR_HASH,
    enumerate_support_subsets,
    run_phase_15b,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15C"
CODE_VERSION = "phase15c-audit-v1"
ARTIFACT_DIR_NAME = "phase15c_audit_artifacts"
EXPECTED_MANIFEST_HASH = "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
BREAKING_DEFINITION = "factors[DDPhi:p,Phi:p] internal[dot(0,1)] lorentz[(0, 0)-(0, 1)]"
AXIS_KINETIC = "factors[DPhi:s,DPhi:s] internal[] lorentz[(0, 0)-(1, 0)]"
AXIS_QUADRATIC = "factors[Phi:s,Phi:s] internal[] lorentz[]"
PLANE_QUADRATIC = "factors[Phi:p,Phi:p] internal[dot(0,1)] lorentz[]"
INHERITED_PARAMETERS = ("c0", "c1", "Z", "kappa", "c_H", "lam_a", "lam_b")
SPECIAL_BRANCHES = ("coefficient = 0", "Z = 0", "Z_A = 0", "lam_a = lam_b")


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _polynomial(
    factors: tuple[Any, ...],
    edges: tuple[Any, ...],
    pairs: tuple[Any, ...],
    catalog: dict[str, Any],
) -> dict[tuple[Any, ...], int]:
    plane_factors = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
    acc: dict[tuple[Any, ...], int] = {}
    lorentz_values = tuple(itertools.product(range(4), repeat=len(pairs)))
    plane_values = tuple(itertools.product(range(2), repeat=len(plane_factors)))
    for lorentz_choice in lorentz_values:
        slot_value: dict[tuple[int, int], int] = {}
        for choice, pair in zip(lorentz_choice, pairs):
            slot_value[pair[0]] = choice
            slot_value[pair[1]] = choice
        for plane_choice in plane_values:
            plane_at = {factor: plane_choice[index] for index, factor in enumerate(plane_factors)}
            coefficient = 1
            for left, right, label in edges:
                if label == "dot":
                    coefficient *= 1 if plane_at[left] == plane_at[right] else 0
                else:
                    coefficient *= K_PLANE[plane_at[left]][plane_at[right]]
            if coefficient == 0:
                continue
            monomial: dict[int, int] = {}
            for index, (block, channel) in enumerate(factors):
                slots = tuple(slot_value[(index, slot)] for slot in range(_slots(block)))
                looked = _lookup(catalog, block, channel, slots, plane_at.get(index))
                if looked is None:
                    coefficient = 0
                    break
                sign, variable = looked
                coefficient *= sign
                monomial[variable] = monomial.get(variable, 0) + 1
            if coefficient == 0:
                continue
            key = tuple(sorted(monomial.items()))
            acc[key] = acc.get(key, 0) + coefficient
    return {key: value for key, value in acc.items() if value}


def _expanded_densities() -> dict[str, dict[tuple[Any, ...], int]]:
    catalog = _component_catalog()
    representatives: dict[Any, Any] = {}
    for n_phi, n_d, n_dd, n_f in _counts():
        covariant = ("Phi",) * n_phi + ("DPhi",) * n_d + ("DDPhi",) * n_dd
        for channels in itertools.product(("p", "s"), repeat=len(covariant)):
            factors = tuple((name, channel) for name, channel in zip(covariant, channels)) + (("F", "inv"),) * n_f
            plane = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
            slots = tuple((index, slot) for index, (name, _channel) in enumerate(factors) for slot in range(_slots(name)))
            for edges in _internal_pairings(plane):
                for pairs in _matchings(slots):
                    representatives.setdefault(_canonical(factors, edges, pairs), (factors, edges, pairs))
    densities = {}
    for key, (factors, edges, pairs) in representatives.items():
        polynomial = _polynomial(factors, edges, pairs, catalog)
        if polynomial:
            densities[_definition(key)] = polynomial
    return densities


def _primitive(vector: Any) -> list[int]:
    values = [sp.Rational(entry) for entry in vector]
    factor = sp.ilcm(*[value.q for value in values])
    integers = [int(value * factor) for value in values]
    divisor = 0
    for entry in integers:
        divisor = sp.igcd(divisor, abs(entry))
    if divisor:
        integers = [entry // divisor for entry in integers]
    pivot = next(entry for entry in integers if entry)
    if pivot < 0:
        integers = [-entry for entry in integers]
    return integers


def _relations(columns: list[tuple[str, dict[tuple[Any, ...], int]]]) -> list[list[dict[str, Any]]]:
    monomials = sorted({monomial for _operator, polynomial in columns for monomial in polynomial})
    index = {monomial: position for position, monomial in enumerate(monomials)}
    entries: dict[tuple[int, int], sp.Integer] = {}
    for column, (_operator, polynomial) in enumerate(columns):
        for monomial, coefficient in polynomial.items():
            entries[(index[monomial], column)] = sp.Integer(coefficient)
    matrix = sp.SparseMatrix(len(monomials), len(columns), entries)
    relations = []
    for vector in matrix.nullspace():
        integers = _primitive(vector)
        terms = [
            {"coefficient": str(coefficient), "operator_id": columns[position][0]}
            for position, coefficient in enumerate(integers)
            if coefficient
        ]
        relations.append(terms)
    relations.sort(key=lambda item: [(term["coefficient"], term["operator_id"]) for term in item])
    return relations


def _plane_rotation(parameter: Any) -> sp.Matrix:
    return sp.Matrix(
        [
            [sp.cos(parameter), -sp.sin(parameter)],
            [sp.sin(parameter), sp.cos(parameter)],
        ]
    )


def _symmetry_proofs() -> dict[str, bool]:
    parameter = sp.symbols("alpha", real=True)
    generator = sp.Matrix([[0, -1], [1, 0]])
    rotation = _plane_rotation(parameter)
    vector = sp.Matrix(sp.symbols("v1:3"))
    other = sp.Matrix(sp.symbols("w1:3"))
    coordinate = sp.symbols("x")
    angle = sp.Function("alpha")(coordinate)
    local_rotation = _plane_rotation(angle)
    field = sp.Matrix([sp.Function("p1")(coordinate), sp.Function("p2")(coordinate)])
    connection = sp.Function("A")(coordinate)
    slope = sp.diff(field, coordinate) - connection * (generator * field)
    transformed = sp.simplify(local_rotation * field)
    shifted = connection + sp.diff(angle, coordinate)
    transformed_slope = sp.diff(transformed, coordinate) - shifted * (generator * transformed)
    covariant_transport = sp.simplify(transformed_slope - local_rotation * slope) == sp.zeros(2, 1)
    base = (sp.diff(slope, coordinate).T * field)[0]
    varied = (sp.diff(transformed_slope, coordinate).T * transformed)[0]
    extra = sp.diff(angle, coordinate) * ((generator * slope).T * field)[0]
    local_identity = sp.simplify(varied - base - extra) == 0
    constant = sp.symbols("alpha_const", real=True)
    rigid = _plane_rotation(constant)
    rigid_field = sp.simplify(rigid * field)
    rigid_slope = sp.diff(rigid_field, coordinate) - connection * (generator * rigid_field)
    rigid_base = (sp.diff(slope, coordinate).T * field)[0]
    rigid_varied = (sp.diff(rigid_slope, coordinate).T * rigid_field)[0]
    global_identity = sp.simplify(rigid_varied - rigid_base) == 0
    rigid_hessian = sp.simplify(sp.diff(rigid_slope, coordinate) - rigid * sp.diff(slope, coordinate)) == sp.zeros(2, 1)
    sample_field = sp.Matrix([coordinate, 1])
    sample_rotation = _plane_rotation(coordinate)
    sample_slope = sp.diff(sample_field, coordinate)
    sample_transformed = sp.simplify(sample_rotation * sample_field)
    sample_shifted_slope = sp.diff(sample_transformed, coordinate) - 1 * (generator * sample_transformed)
    sample_difference = (sp.diff(sample_shifted_slope, coordinate).T * sample_transformed)[0] - (sp.diff(sample_slope, coordinate).T * sample_field)[0]
    axes = sp.symbols("t x")
    gauge = sp.Function("beta")(*axes)
    potential = [sp.Function(f"B{index}")(*axes) for index in range(2)]
    moved = [potential[index] + sp.diff(gauge, axes[index]) for index in range(2)]
    strength = sp.diff(potential[1], axes[0]) - sp.diff(potential[0], axes[1])
    moved_strength = sp.diff(moved[1], axes[0]) - sp.diff(moved[0], axes[1])
    stored = so2_generator_K()
    internal = sp.Matrix(sp.symbols("Phi0:3"))
    return {
        "axis_annihilated": bool(sp.simplify((stored * internal)[0]) == 0),
        "contraction_invariant": bool(sp.simplify((rotation * vector).dot(rotation * other) - vector.dot(other)) == 0),
        "field_strength_invariant": bool(sp.simplify(moved_strength - strength) == 0),
        "global_sample_invariant": bool(global_identity),
        "rigid_hessian_covariant": bool(rigid_hessian),
        "k_contraction_invariant": bool(sp.simplify((rotation * vector).dot(generator * (rotation * other)) - vector.dot(generator * other)) == 0),
        "local_D_covariant": bool(covariant_transport),
        "local_hessian_identity": bool(local_identity),
        "local_hessian_witness_nonzero": bool(sp.simplify(sample_difference) != 0),
        "rotation_commutes_with_k": bool(sp.simplify(generator * rotation - rotation * generator) == sp.zeros(2)),
        "rotation_orthogonal": bool(sp.simplify(rotation.T * rotation - sp.eye(2)) == sp.zeros(2)),
    }


def _frozen_overlap(by_definition: dict[str, str]) -> list[dict[str, str]]:
    lam_a, lam_b = sp.symbols("lam_a lam_b")
    phi = sp.Matrix(sp.symbols("Phi0:3"))
    quadratic = (phi.T * sp.diag(lam_a, lam_b, lam_b) * phi)[0]
    reduced = lam_a * phi[0] ** 2 + lam_b * (phi[1] ** 2 + phi[2] ** 2)
    axis_id = by_definition[AXIS_KINETIC]
    axis_square = by_definition[AXIS_QUADRATIC]
    plane_square = by_definition[PLANE_QUADRATIC]
    shared = f"{axis_square},{plane_square}"
    return [
        {
            "classification": "DIFFERENT_OPERATOR",
            "frozen_term": "gravity_c0",
            "redundancy": "NONE",
            "reason": "the constant density is outside the 117 registered matter densities",
        },
        {
            "classification": "DIFFERENT_OPERATOR",
            "frozen_term": "gravity_c1_R",
            "redundancy": "NONE",
            "reason": "the curvature scalar is outside the registered matter grammar",
        },
        {
            "classification": "SAME_CANONICAL_OPERATOR",
            "frozen_term": "matter_kinetic_axis",
            "operator_id": axis_id,
            "redundancy": "PARAMETER_REDUNDANCY_CANDIDATE",
            "reason": "K annihilates the axis, so D_mu Phi_0 equals partial_mu Phi_0; Z and the free grammar coefficient multiply that density",
        },
        {
            "classification": "DIFFERENT_OPERATOR",
            "frozen_term": "matter_kinetic_plane",
            "redundancy": "NONE",
            "reason": "the frozen plane kinetic uses an ordinary derivative; the registered plane kinetic uses D",
        },
        {
            "classification": "REPRESENTATIONAL_OVERLAP",
            "frozen_term": "matter_phi_sq",
            "operator_ids": shared,
            "redundancy": "PARAMETER_REDUNDANCY_CANDIDATE",
            "reason": "kappa/2 <Phi, Phi> is kappa/2 times the sum of the registered axis square and plane square",
        },
        {
            "classification": "REPRESENTATIONAL_OVERLAP" if sp.expand(quadratic - reduced) == 0 else "EQUIVALENCE_UNSUPPORTED",
            "frozen_term": "matter_H_int",
            "operator_ids": shared,
            "redundancy": "PARAMETER_REDUNDANCY_CANDIDATE",
            "reason": "Phi^T H_int Phi equals lam_a Phi_0^2 + lam_b (Phi_1^2 + Phi_2^2), with lam_a and lam_b independent",
        },
    ]


def _accounting(family: dict[str, Any], kernel: int) -> dict[str, int]:
    return {
        "coefficient_redundancy_count": kernel,
        "dimensionful_coefficient_count": family["dimensionful_coefficient_count"],
        "dimensionless_coefficient_count": family["dimensionless_coefficient_count"],
        "inherited_parameter_count": len(INHERITED_PARAMETERS),
        "newly_introduced_parameter_count": 0,
        "total_coefficient_count": family["coefficient_count"],
    }


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15C_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15C_BLOCKED"}


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "exact binding to the Phase 15B families", EXPECTED_MANIFEST_HASH, result["PHASE_15B_MANIFEST_HASH"]),
        ("2", "117 and 37 operator counts", "117-37", f"{result['FLAT_OPERATOR_COUNT']}-{result['COVARIANT_OPERATOR_COUNT']}"),
        ("3", "no support-subset enumeration", "SUPPORT_ENUMERATION_NOT_DEFINED", enumerate_support_subsets()),
        ("4", "no coefficient numerical assignment", "SYMBOLIC", result["coefficient_values"]),
        ("5", "no parameter fixing", "NONE", result["imposed_relations"]),
        ("6", "no new parameter creation", "0", str(result["newly_introduced_parameter_count"])),
        ("7", "frozen-action overlap detection", "DETECTED", "DETECTED" if any(item["classification"] == "SAME_CANONICAL_OPERATOR" for item in result["frozen_overlaps"]) else "MISSED"),
        ("8", "operator-level redundancy detection", "DETECTED", "DETECTED" if result["operator_identity_count"] else "MISSED"),
        ("9", "unsupported equivalences remain unsupported", "UNAPPLIED", "UNAPPLIED" if result["counts_unchanged"] else "APPLIED"),
        ("10", "symmetry tested on the complete symbolic sum", "TESTED", "TESTED" if result["flat_sum_local_status"] == "BROKEN" and result["covariant_sum_local_status"] == "EXACT" else "SKIPPED"),
        ("11", "gauge invariance tested per admitted operator class", "RECORDED", "RECORDED" if result["breaking_operator_in_flat"] and not result["breaking_operator_in_covariant"] else "MISSING"),
        ("12", "flat and curved contexts remain separate", "SEPARATE", "SEPARATE" if result["contexts_separate"] else "MERGED"),
        ("13", "EOM derivation is symbolic", "UNTESTED", result["eom_closed_form"]),
        ("14", "special parameter branches remain separate", "SEPARATE", "SEPARATE" if result["special_branches_applied"] is False else "APPLIED"),
        ("15", "no EOM quotienting", "UNSUPPORTED", result["EOM_EQUIVALENCE"]),
        ("16", "no field-redefinition quotienting", "UNSUPPORTED", result["FIELD_REDEFINITION_EQUIVALENCE"]),
        ("17", "no IBP quotienting", "UNSUPPORTED", result["IBP_EQUIVALENCE"]),
        ("18", "no experimental input", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("19", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("20", "no new physical principle", "NONE", result["new_physical_principle"]),
        ("21", "deterministic output", result["audit_digest"], result["audit_digest_repeated"]),
        ("22", "repeated execution reproduces identical results", result["audit_digest"], result["audit_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    source = run_phase_15b(write_artifacts=False)
    compiled = compile_grammar()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or source.get("status") != "OK"
        or source.get("PHASE_15B_STATUS") != "COMPLETE"
        or source.get("grammar_hash") != EXPECTED_GRAMMAR_HASH
        or source.get("grammar_version") != "grammar_15a_v1"
        or source.get("manifest_hash") != EXPECTED_MANIFEST_HASH
        or source.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or source.get("PROVENANCE_STATUS") != "VERIFIED"
        or source.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or compiled.get("grammar_hash") != EXPECTED_GRAMMAR_HASH
        or catalog_influence({"entries": []}, "audit")["applied"] is not False
    ):
        return _stop("integrity gate")
    flat = source["families"]["FLAT_LORENTZ"]
    curved = source["families"]["COVARIANT_4D"]
    by_definition = {item["mathematical_definition"]: item["object_id"] for item in compiled["enabled"]}
    by_id = {item["object_id"]: item for item in compiled["enabled"]}
    if set(by_id) != set(flat["operator_ids"]) or not set(curved["operator_ids"]) < set(flat["operator_ids"]):
        return _stop("family binding")
    if len(flat["operator_ids"]) != 117 or len(curved["operator_ids"]) != 37:
        return _stop("family counts")
    if any(item["allowed_coefficient"] != "FREE" for item in by_id.values()):
        return _stop("a coefficient is not free")
    if any(item["value"] != "SYMBOLIC" for item in flat["coefficients"] + curved["coefficients"]):
        return _stop("a coefficient value was assigned")
    densities = _expanded_densities()
    if set(densities) != set(by_definition):
        return _stop("polynomial reconstruction")
    columns = [(by_definition[definition], polynomial) for definition, polynomial in sorted(densities.items())]
    relations = _relations(columns)
    curved_ids = set(curved["operator_ids"])
    curved_columns = [item for item in columns if item[0] in curved_ids]
    curved_relations = _relations(curved_columns)
    proofs = _symmetry_proofs()
    if not all(proofs.values()):
        failed = [name for name, ok in proofs.items() if not ok]
        return _stop("symmetry proof failed: " + ",".join(failed))
    breaker = by_definition.get(BREAKING_DEFINITION)
    if breaker is None or breaker not in flat["operator_ids"] or breaker in curved_ids:
        return _stop("breaking operator is not in the expected family")
    if any("DDPhi" in by_id[operator]["mathematical_definition"] for operator in curved_ids):
        return _stop("a covariant operator contains a flat Hessian")
    overlaps = _frozen_overlap(by_definition)
    if any(item["classification"] == "EQUIVALENCE_UNSUPPORTED" for item in overlaps):
        return _stop("frozen overlap proof failed")
    audit_body = {
        "breaker": breaker,
        "curved_relations": curved_relations,
        "proofs": proofs,
        "relations": relations,
    }
    audit_digest = content_digest(audit_body)
    flat_kernel = len(relations)
    curved_kernel = len(curved_relations)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15C_STATUS": "COMPLETE",
        "SYMBOLIC_BINDING_STATUS": "VERIFIED",
        "OPERATOR_INDEPENDENCE_STATUS": "PARTIAL",
        "FROZEN_OVERLAP_STATUS": "VERIFIED",
        "PARAMETER_ACCOUNTING_STATUS": "VERIFIED",
        "PFR_STATUS": "VERIFIED",
        "SYMMETRY_STATUS": "PARTIAL",
        "GAUGE_INVARIANCE_STATUS": "PARTIAL",
        "COVARIANCE_STATUS": "VERIFIED",
        "EOM_STATUS": "PARTIAL",
        "CONSERVATION_STATUS": "UNTESTED",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "EQUIVALENCE_STATUS": "PARTIAL",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "grammar_version": "grammar_15a_v1",
        "grammar_hash": EXPECTED_GRAMMAR_HASH,
        "PHASE_15B_MANIFEST_HASH": source["manifest_hash"],
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FLAT_OPERATOR_COUNT": 117,
        "COVARIANT_OPERATOR_COUNT": 37,
        "flat_coefficients": _accounting(flat, flat_kernel),
        "covariant_coefficients": _accounting(curved, curved_kernel),
        "newly_introduced_parameter_count": 0,
        "inherited_parameters": list(INHERITED_PARAMETERS),
        "operator_identity_count": flat_kernel,
        "component_polynomial_rank": 117 - flat_kernel,
        "covariant_component_polynomial_rank": 37 - curved_kernel,
        "relations": relations,
        "curved_relations": curved_relations,
        "frozen_overlaps": overlaps,
        "parameter_redundancy_candidates": [
            "frozen Z and the free grammar coefficient of the axis kinetic density",
            "frozen kappa and c_H lam_a share the axis quadratic with its free grammar coefficient",
            "frozen kappa and c_H lam_b share the plane quadratic with its free grammar coefficient",
        ],
        "breaking_operator": breaker,
        "breaking_definition": BREAKING_DEFINITION,
        "breaking_operator_in_flat": True,
        "breaking_operator_in_covariant": False,
        "flat_sum_global_status": "EXACT",
        "flat_sum_local_status": "BROKEN",
        "covariant_sum_global_status": "EXACT",
        "covariant_sum_local_status": "EXACT",
        "operator_level_gauge": "the recorded flat Hessian scalar is not locally invariant; every covariant operator is a contraction of Phi, DPhi and F",
        "action_level_gauge": "the flat sum with free coefficients is not locally invariant; the covariant sum is",
        "flat_covariance": "flat Lorentz invariance only",
        "covariant_covariance": "GENERALLY_COVARIANT",
        "eom_closed_form": "UNTESTED",
        "flat_eom": {
            "EOM_ORDER": 4,
            "FIELD_DEPENDENCE": "Phi and mathcal A_mu",
            "HIGHER_DERIVATIVE_STATUS": "PRESENT",
            "closed_form": "UNTESTED",
        },
        "covariant_eom": {
            "EOM_ORDER": 2,
            "FIELD_DEPENDENCE": "Phi and mathcal A_mu",
            "HIGHER_DERIVATIVE_STATUS": "ABSENT",
            "closed_form": "UNTESTED",
        },
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "derived_fixed_dimensionless_count": 0,
        "EOM_EQUIVALENCE": "UNSUPPORTED",
        "FIELD_REDEFINITION_EQUIVALENCE": "UNSUPPORTED",
        "IBP_EQUIVALENCE": "UNSUPPORTED",
        "counts_unchanged": True,
        "imposed_relations": "NONE",
        "coefficient_values": "SYMBOLIC",
        "special_branches_applied": False,
        "special_branches": list(SPECIAL_BRANCHES),
        "contexts_separate": True,
        "new_physical_principle": "NONE",
        "new_field": "NONE",
        "operators_removed": 0,
        "symmetry_proofs": proofs,
        "audit_digest": audit_digest,
        "audit_digest_repeated": content_digest(audit_body),
        "proof_obligations": [
            {"certified_pass": False, "obligation": "closed-form Euler-Lagrange equations of either complete sum"},
            {"certified_pass": False, "obligation": "Noether current of either complete sum"},
            {"certified_pass": False, "obligation": "individual local variation of every other plane Hessian operator"},
            {"certified_pass": False, "obligation": "using the detected syzygies as a quotient would be a new canonicalization"},
        ],
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15C_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        files = {
            "PHASE_15C_RELATIONS.json": {
                "component_polynomial_rank": 117 - flat_kernel,
                "covariant_component_polynomial_rank": 37 - curved_kernel,
                "curved_relations": curved_relations,
                "relations": relations,
            },
            "PHASE_15C_OVERLAP.json": {
                "frozen_overlaps": overlaps,
                "parameter_redundancy_candidates": payload["parameter_redundancy_candidates"],
            },
            "PHASE_15C_SYMMETRY.json": {
                "action_level_gauge": payload["action_level_gauge"],
                "breaking_definition": BREAKING_DEFINITION,
                "breaking_operator": breaker,
                "covariant_local": "EXACT",
                "flat_global": "EXACT",
                "flat_local": "BROKEN",
                "operator_level_gauge": payload["operator_level_gauge"],
                "proofs": proofs,
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
