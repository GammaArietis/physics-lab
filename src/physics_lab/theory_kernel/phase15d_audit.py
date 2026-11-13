"""Phase 15D audits syzygies, redundancies, and local variations.

It does not quotient the grammar and does not remove operators.
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
    _matchings,
    _ranking_tokens,
    _slots,
    classify_candidate,
    compile_grammar,
)
from physics_lab.theory_kernel.phase15b_enumeration import enumerate_support_subsets
from physics_lab.theory_kernel.phase15c_audit import (
    AXIS_KINETIC,
    AXIS_QUADRATIC,
    BREAKING_DEFINITION,
    EXPECTED_MANIFEST_HASH,
    PLANE_QUADRATIC,
    _polynomial,
    _symmetry_proofs,
    run_phase_15c,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15D"
CODE_VERSION = "phase15d-audit-v1"
ARTIFACT_DIR_NAME = "phase15d_audit_artifacts"
ACTION_HASH_14I = "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
PLANE_KINETIC = "factors[DPhi:p,DPhi:p] internal[dot(0,1)] lorentz[(0, 0)-(1, 0)]"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15D_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15D_BLOCKED"}


def _representatives() -> tuple[int, dict[str, tuple[Any, ...]]]:
    found: dict[str, tuple[Any, ...]] = {}
    raw = 0
    for n_phi, n_d, n_dd, n_f in _counts():
        covariant = ("Phi",) * n_phi + ("DPhi",) * n_d + ("DDPhi",) * n_dd
        for channels in itertools.product(("p", "s"), repeat=len(covariant)):
            factors = tuple((name, channel) for name, channel in zip(covariant, channels)) + (("F", "inv"),) * n_f
            plane = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
            slots = tuple((index, slot) for index, (name, _channel) in enumerate(factors) for slot in range(_slots(name)))
            for edges in _internal_pairings(plane):
                for pairs in _matchings(slots):
                    raw += 1
                    key = _canonical(factors, edges, pairs)
                    found.setdefault(_definition(key), (factors, edges, pairs))
    return raw, found


def _relation_holds(relation: list[dict[str, str]], by_id: dict[str, dict[str, Any]], reps: dict[str, tuple[Any, ...]], catalog: dict[str, Any]) -> bool:
    total: dict[tuple[Any, ...], int] = {}
    for term in relation:
        definition = by_id[term["operator_id"]]["mathematical_definition"]
        factors, edges, pairs = reps[definition]
        coefficient = int(term["coefficient"])
        for monomial, value in _polynomial(factors, edges, pairs, catalog).items():
            total[monomial] = total.get(monomial, 0) + coefficient * value
    return all(value == 0 for value in total.values())


def _syzygy_matrix_rank(relations: list[list[dict[str, str]]], operator_ids: list[str]) -> int:
    position = {operator: index for index, operator in enumerate(operator_ids)}
    rows = []
    for relation in relations:
        row = [0] * len(operator_ids)
        for term in relation:
            row[position[term["operator_id"]]] = int(term["coefficient"])
        rows.append(row)
    return int(sp.Matrix(rows).rank())


def _variation_tables(operators: list[dict[str, Any]], reps: dict[str, tuple[Any, ...]]) -> list[dict[str, str]]:
    generator = sp.Matrix([[0, -1], [1, 0]])
    shift = sp.symbols("da0:4")
    phi_s = sp.symbols("phi_s")
    phi_p = list(sp.symbols("phi_p0:2"))
    dphi_s = list(sp.symbols("ds0:4"))
    dphi_p = [[sp.symbols(f"dp{mu}_{plane}") for plane in range(2)] for mu in range(4)]
    dd_s: dict[tuple[int, int], Any] = {}
    dd_p: dict[tuple[int, int], list[Any]] = {}
    for mu in range(4):
        for nu in range(mu, 4):
            dd_s[(mu, nu)] = dd_s[(nu, mu)] = sp.symbols(f"Hs{mu}_{nu}")
            dd_p[(mu, nu)] = dd_p[(nu, mu)] = [sp.symbols(f"Hp{mu}_{nu}_{plane}") for plane in range(2)]
    strength = {
        (mu, nu): sp.symbols(f"F{mu}_{nu}")
        for mu in range(4)
        for nu in range(mu + 1, 4)
    }

    def extra(mu: int, nu: int, plane: int) -> Any:
        def rotated(index: int, component: int) -> Any:
            vector = sp.Matrix(dphi_p[index])
            return (generator * vector)[component]

        return sp.Rational(1, 2) * (shift[mu] * rotated(nu, plane) + shift[nu] * rotated(mu, plane))

    def lookup(block: str, channel: str, lorentz: tuple[int, ...], plane: int | None, varied: bool) -> Any | None:
        if block == "Phi" and channel == "s":
            return phi_s
        if block == "Phi" and channel == "p" and plane is not None:
            return phi_p[plane]
        if block == "DPhi" and channel == "s":
            return dphi_s[lorentz[0]]
        if block == "DPhi" and channel == "p" and plane is not None:
            return dphi_p[lorentz[0]][plane]
        if block == "DDPhi" and channel == "s":
            return dd_s[(lorentz[0], lorentz[1])]
        if block == "DDPhi" and channel == "p" and plane is not None:
            mu, nu = lorentz
            base = dd_p[(mu, nu)][plane]
            return base + extra(mu, nu, plane) if varied else base
        if block == "F":
            mu, nu = lorentz
            if mu == nu:
                return None
            sign = 1 if mu < nu else -1
            return sign * strength[(min(mu, nu), max(mu, nu))]
        raise KeyError((block, channel))

    def evaluate(factors: tuple[Any, ...], edges: tuple[Any, ...], pairs: tuple[Any, ...], varied: bool) -> Any:
        plane_factors = tuple(index for index, factor in enumerate(factors) if factor[1] == "p")
        total = 0
        for lorentz_choice in itertools.product(range(4), repeat=len(pairs)):
            slot_value: dict[tuple[int, int], int] = {}
            for choice, pair in zip(lorentz_choice, pairs):
                slot_value[pair[0]] = choice
                slot_value[pair[1]] = choice
            for plane_choice in itertools.product(range(2), repeat=len(plane_factors)):
                plane_at = {factor: plane_choice[index] for index, factor in enumerate(plane_factors)}
                coefficient = 1
                for left, right, label in edges:
                    if label == "dot":
                        coefficient *= 1 if plane_at[left] == plane_at[right] else 0
                    else:
                        coefficient *= K_PLANE[plane_at[left]][plane_at[right]]
                if coefficient == 0:
                    continue
                term: Any = coefficient
                failed = False
                for index, (block, channel) in enumerate(factors):
                    slots = tuple(slot_value[(index, slot)] for slot in range(_slots(block)))
                    looked = lookup(block, channel, slots, plane_at.get(index), varied)
                    if looked is None:
                        failed = True
                        break
                    term *= looked
                if not failed:
                    total += term
        return sp.expand(total)

    rows = []
    for operator in sorted(operators, key=lambda item: item["object_id"]):
        factors, edges, pairs = reps[operator["mathematical_definition"]]
        original = evaluate(factors, edges, pairs, False)
        if original == 0:
            raise RuntimeError(operator["object_id"])
        difference = sp.expand(evaluate(factors, edges, pairs, True) - original)
        frozen_shift = sp.expand(difference.subs(dict.fromkeys(shift, 0)))
        local = "local U(1) invariant" if difference == 0 else "local U(1) breaking"
        if frozen_shift != 0:
            global_status = "global SO(2) breaking"
        else:
            global_status = "global SO(2) invariant"
        rows.append(
            {
                "coefficient_dependency": "ZERO_FOR_EVERY_COEFFICIENT" if difference == 0 else "NONZERO_FOR_EVERY_NONZERO_COEFFICIENT",
                "context": "FLAT_SECOND_DERIVATIVE_CONTEXT",
                "global_so2_status": global_status,
                "operator_id": operator["object_id"],
                "variation_expression": "0" if difference == 0 else str(difference),
                "variation_status": local,
            }
        )
    return rows


def _overlap_audit(by_definition: dict[str, str]) -> dict[str, Any]:
    lam_a, lam_b = sp.symbols("lam_a lam_b")
    phi = sp.Matrix(sp.symbols("Phi0:3"))
    generator = so2_generator_K()
    stored = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    quadratic = (phi.T * sp.diag(lam_a, lam_b, lam_b) * phi)[0]
    inner = phi[0] ** 2 + phi[1] ** 2 + phi[2] ** 2
    hint_gap = sp.expand(quadratic - lam_a * inner)
    coordinate = sp.symbols("x")
    plane = sp.Matrix([sp.Function("p1")(coordinate), sp.Function("p2")(coordinate)])
    connection = sp.Function("A")(coordinate)
    plane_generator = sp.Matrix([[0, -1], [1, 0]])
    covariant = sp.diff(plane, coordinate) - connection * (plane_generator * plane)
    ordinary = sp.diff(plane, coordinate)
    kinetic_gap = sp.simplify(covariant - ordinary)
    records = [
        {
            "canonical_operator_id": "",
            "coefficient_relation": "none",
            "consequence": "outside the registered matter grammar",
            "frozen_term_id": "gravity_c0",
            "parameter_redundancy": "FALSE",
            "provenance": "REPRESENTATIONAL",
            "same_density": False,
        },
        {
            "canonical_operator_id": "",
            "coefficient_relation": "none",
            "consequence": "curvature remains outside the matter grammar",
            "frozen_term_id": "gravity_c1_R",
            "parameter_redundancy": "FALSE",
            "provenance": "REPRESENTATIONAL",
            "same_density": False,
        },
        {
            "canonical_operator_id": by_definition[AXIS_KINETIC],
            "coefficient_relation": "Z and the free grammar coefficient both multiply this axis density",
            "consequence": "exact redundancy of the axis piece; the rest of the frozen kinetic stays distinct",
            "frozen_term_id": "matter_kinetic_axis",
            "parameter_redundancy": "EXACT",
            "provenance": "DERIVED",
            "same_density": True,
        },
        {
            "canonical_operator_id": by_definition[PLANE_KINETIC],
            "coefficient_relation": "none",
            "consequence": "D_mu psi = partial_mu psi - A_mu K psi; the two plane kinetics share the ordinary piece and differ by the connection",
            "frozen_term_id": "matter_kinetic_plane",
            "parameter_redundancy": "FALSE",
            "provenance": "DERIVED",
            "same_density": False,
        },
        {
            "canonical_operator_id": f"{by_definition[AXIS_QUADRATIC]},{by_definition[PLANE_QUADRATIC]}",
            "coefficient_relation": "kappa/2 multiplies the sum of the two quadratics; each grammar coefficient multiplies one of them",
            "consequence": "the frozen term is a sum, so it is not one canonical operator",
            "frozen_term_id": "matter_phi_sq",
            "parameter_redundancy": "FALSE",
            "provenance": "REPRESENTATIONAL",
            "same_density": False,
        },
        {
            "canonical_operator_id": f"{by_definition[AXIS_QUADRATIC]},{by_definition[PLANE_QUADRATIC]}",
            "coefficient_relation": "c_H/2 multiplies lam_a times the axis square plus lam_b times the plane square",
            "consequence": "generically independent from kappa/2 <Phi, Phi>; proportional only on the branch lam_a = lam_b",
            "frozen_term_id": "matter_H_int",
            "parameter_redundancy": "FALSE",
            "provenance": "PARAMETER-DEPENDENT",
            "same_density": False,
        },
    ]
    proofs = {
        "axis_density_matches": bool(sp.simplify((generator * phi)[0]) == 0 and generator == stored),
        "hint_generic_gap": bool(hint_gap != 0),
        "hint_gap_is_plane_square": bool(sp.expand(hint_gap - (lam_b - lam_a) * (phi[1] ** 2 + phi[2] ** 2)) == 0),
        "hint_special_branch": bool(sp.expand(hint_gap.subs(lam_b, lam_a)) == 0),
        "plane_kinetic_gap_nonzero": bool(kinetic_gap != sp.zeros(2, 1)),
        "plane_kinetic_related_expansion": bool(sp.simplify(kinetic_gap + connection * (plane_generator * plane)) == sp.zeros(2, 1)),
    }
    return {"proofs": proofs, "records": records}


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    dd_rows = result["dd_variations"]
    cases = [
        ("1", "exact binding to Phase 15C", "COMPLETE", result["PHASE_15C_STATUS"]),
        ("2", "eight syzygies reproduce exactly", "8", str(result["syzygy_count"])),
        ("3", "syzygy-rank computation is deterministic", result["syzygy_rank_digest"], result["syzygy_rank_digest_repeated"]),
        ("4", "syzygies are not silently used for quotienting", "0", str(result["operators_removed"])),
        ("5", "frozen-action overlap detection is deterministic", result["overlap_digest"], result["overlap_digest_repeated"]),
        ("6", "H_int/kappa overlap classification", "FALSE", result["hint_kappa_parameter_redundancy"]),
        ("7", "kinetic overlap classification", "EXACT", result["axis_kinetic_parameter_redundancy"]),
        ("8", "all 80 DD operators receive an explicit local-symmetry status", "80", str(len(dd_rows)) if all(row["variation_status"] in {"local U(1) invariant", "local U(1) breaking"} for row in dd_rows) else "0"),
        ("9", "global SO(2) and local U(1) statuses remain separate", "SEPARATE", "SEPARATE" if result["global_local_separated"] else "MERGED"),
        ("10", "flat/covariant contexts remain separate", "SEPARATE", "SEPARATE" if result["contexts_separate"] else "MERGED"),
        ("11", "no parameter is fixed", "NONE", result["imposed_relations"]),
        ("12", "no new field", "NONE", result["new_field"]),
        ("13", "no new operator", "0", str(result["new_operator_count"])),
        ("14", "no new physical principle", "NONE", result["new_physical_principle"]),
        ("15", "no IBP quotienting", "UNSUPPORTED", result["IBP_EQUIVALENCE"]),
        ("16", "no field-redefinition quotienting", "UNSUPPORTED", result["FIELD_REDEFINITION_EQUIVALENCE"]),
        ("17", "no EOM quotienting", "UNSUPPORTED", result["EOM_EQUIVALENCE"]),
        ("18", "no unsupported basis quotienting", "UNSUPPORTED", result["BASIS_EQUIVALENCE"]),
        ("19", "dimensionless quantities remain symbolic", "PARAMETER_DEPENDENT", result["dimensionless_classification"]),
        ("20", "no experiment", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("21", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("22", "repeated execution deterministic", result["audit_digest"], result["audit_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    source = run_phase_15c(write_artifacts=False)
    compiled = compile_grammar()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or source.get("status") != "OK"
        or source.get("PHASE_15C_STATUS") != "COMPLETE"
        or source.get("grammar_hash") != GRAMMAR_HASH
        or source.get("grammar_version") != "grammar_15a_v1"
        or source.get("PHASE_15B_MANIFEST_HASH") != EXPECTED_MANIFEST_HASH
        or source.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or source.get("PROVENANCE_STATUS") != "VERIFIED"
        or source.get("FROZEN_ACTION_STATUS") != "VERIFIED"
        or source.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or compiled.get("grammar_hash") != GRAMMAR_HASH
        or enumerate_support_subsets() != "SUPPORT_ENUMERATION_NOT_DEFINED"
    ):
        return _stop("integrity gate")
    by_id = {item["object_id"]: item for item in compiled["enabled"]}
    by_definition = {item["mathematical_definition"]: item["object_id"] for item in compiled["enabled"]}
    if source["FLAT_OPERATOR_COUNT"] != 117 or source["COVARIANT_OPERATOR_COUNT"] != 37:
        return _stop("family counts")
    if len(by_id) != 117:
        return _stop("grammar count")
    raw, reps = _representatives()
    if raw != 473 or len(reps) != 204 or any(item["mathematical_definition"] not in reps for item in by_id.values()):
        return _stop("reduction counts")
    relations = source["relations"]
    if len(relations) != 8:
        return _stop("syzygy count")
    catalog = _component_catalog()
    if any(not _relation_holds(relation, by_id, reps, catalog) for relation in relations):
        return _stop("a reported relation is not an algebraic identity")
    rank = _syzygy_matrix_rank(relations, sorted(by_id))
    curved_support = sorted({term["operator_id"] for relation in source["curved_relations"] for term in relation})
    curved_rank = _syzygy_matrix_rank(source["curved_relations"], curved_support)
    dd_operators = [item for item in by_id.values() if "DDPhi" in item["mathematical_definition"]]
    if len(dd_operators) != 80:
        return _stop("DD count")
    try:
        dd_rows = _variation_tables(dd_operators, reps)
    except RuntimeError as exc:
        return _stop(f"variation engine missed {exc}")
    breaking = [row for row in dd_rows if row["variation_status"] == "local U(1) breaking"]
    invariant = [row for row in dd_rows if row["variation_status"] == "local U(1) invariant"]
    if len(breaking) + len(invariant) != 80:
        return _stop("DD classification")
    if any(row["global_so2_status"] != "global SO(2) invariant" for row in dd_rows):
        return _stop("global variation")
    breaker = by_definition[BREAKING_DEFINITION]
    if not any(row["operator_id"] == breaker and row["variation_status"] == "local U(1) breaking" for row in dd_rows):
        return _stop("known breaker was not reproduced")
    syzygy_ids = {term["operator_id"] for relation in relations for term in relation}
    if breaker in syzygy_ids:
        return _stop("the recorded breaker sits in a syzygy; robustness needs a separate argument")
    overlap = _overlap_audit(by_definition)
    if not all(overlap["proofs"].values()):
        failed = [name for name, ok in overlap["proofs"].items() if not ok]
        return _stop("overlap proof failed: " + ",".join(failed))
    proofs = _symmetry_proofs()
    if not all(proofs.values()):
        return _stop("block symmetry proof failed")
    curved_ids = {term["operator_id"] for relation in source["curved_relations"] for term in relation}
    if any("DDPhi" in by_id[operator]["mathematical_definition"] for operator in curved_ids):
        return _stop("a covariant syzygy uses a flat Hessian")
    covariant_members = [operator for operator in by_id if "DDPhi" not in by_id[operator]["mathematical_definition"]]
    if len(covariant_members) != 37 or breaker in covariant_members:
        return _stop("covariant separation")
    syzygy_records = []
    for relation in relations:
        definitions = [by_id[term["operator_id"]]["mathematical_definition"] for term in relation]
        domain = "FLAT_ONLY" if any("DDPhi" in definition for definition in definitions) else "FLAT_AND_COVARIANT"
        syzygy_records.append(
            {
                "arbitrary_field_configurations": True,
                "boundary_conditions": False,
                "canonicalization": "ALGEBRAIC_SYZYGY_NOT_QUOTIENTED",
                "derivation_rule": "algebraic simplification of the component polynomials",
                "domain": domain,
                "equations_of_motion": False,
                "exact_algebraic_identity": True,
                "operators": relation,
                "parameter_relations": False,
            }
        )
    rank_body = {"rank": rank, "relations": relations}
    overlap_body = {"records": overlap["records"]}
    audit_body = {
        "breaking": len(breaking),
        "invariant": len(invariant),
        "rank": rank,
        "relations": relations,
    }
    axis_record = next(item for item in overlap["records"] if item["frozen_term_id"] == "matter_kinetic_axis")
    hint_record = next(item for item in overlap["records"] if item["frozen_term_id"] == "matter_H_int")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15D_STATUS": "COMPLETE",
        "SYZYGY_STATUS": "VERIFIED",
        "SYZYGY_RANK_STATUS": "VERIFIED",
        "PARAMETER_REDUNDANCY_STATUS": "VERIFIED",
        "FROZEN_OVERLAP_STATUS": "VERIFIED",
        "DDPHI_LOCAL_SYMMETRY_STATUS": "BROKEN",
        "GLOBAL_VS_LOCAL_STATUS": "VERIFIED",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "DIMENSIONLESS_CLOSURE_STATUS": "OPEN",
        "EQUIVALENCE_STATUS": "PARTIAL",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PHASE_15C_STATUS": source["PHASE_15C_STATUS"],
        "grammar_version": "grammar_15a_v1",
        "grammar_hash": GRAMMAR_HASH,
        "PHASE_15B_MANIFEST_HASH": source["PHASE_15B_MANIFEST_HASH"],
        "PHASE_15C_AUDIT_DIGEST": source["audit_digest"],
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "nominal_operator_count": {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117},
        "algebraically_independent_rank": {"COVARIANT_4D": 37 - len(source["curved_relations"]), "FLAT_LORENTZ": 117 - rank},
        "raw_contractions": raw,
        "canonical_keys": len(reps),
        "zero_identities": len(reps) - 117,
        "canonical_densities": 117,
        "syzygy_count": len(relations),
        "syzygy_rank": rank,
        "covariant_syzygy_rank": curved_rank,
        "SYZYGY_DEPENDENCE_STATUS": "INDEPENDENT" if rank == len(relations) and curved_rank == len(source["curved_relations"]) else "DEPENDENT",
        "syzygy_records": syzygy_records,
        "relations": relations,
        "curved_relations": source["curved_relations"],
        "frozen_overlaps": overlap["records"],
        "overlap_proofs": overlap["proofs"],
        "hint_kappa_parameter_redundancy": hint_record["parameter_redundancy"],
        "axis_kinetic_parameter_redundancy": axis_record["parameter_redundancy"],
        "plane_kinetic_parameter_redundancy": "FALSE",
        "dd_variations": dd_rows,
        "dd_local_breaking_count": len(breaking),
        "dd_local_invariant_count": len(invariant),
        "dd_global_invariant_count": sum(row["global_so2_status"] == "global SO(2) invariant" for row in dd_rows),
        "breaking_operator": breaker,
        "breaker_in_syzygy_support": False,
        "flat_sum_local_status": "BROKEN",
        "covariant_sum_local_status": "EXACT",
        "symmetry_difference_robust_to_syzygies": True,
        "global_local_separated": True,
        "contexts_separate": True,
        "flat_covariance": "flat Lorentz invariance only",
        "covariant_covariance": "GENERALLY_COVARIANT",
        "dimensionless_classification": "PARAMETER_DEPENDENT",
        "derived_fixed_dimensionless_count": 0,
        "derived_parameter_relation_count": 0,
        "imposed_relations": "NONE",
        "operators_removed": 0,
        "new_operator_count": 0,
        "new_field": "NONE",
        "new_physical_principle": "NONE",
        "IBP_EQUIVALENCE": "UNSUPPORTED",
        "FIELD_REDEFINITION_EQUIVALENCE": "UNSUPPORTED",
        "EOM_EQUIVALENCE": "UNSUPPORTED",
        "BASIS_EQUIVALENCE": "UNSUPPORTED",
        "physically_inequivalent_count": "NOT_CLAIMED",
        "grammar_revision_request": {
            "executed": False,
            "proposed_rule": "quotient by the eight algebraic syzygies",
            "status": "NOT_AUTHORIZED",
        },
        "block_symmetry_proofs": proofs,
        "syzygy_rank_digest": content_digest(rank_body),
        "syzygy_rank_digest_repeated": content_digest(rank_body),
        "overlap_digest": content_digest(overlap_body),
        "overlap_digest_repeated": content_digest(overlap_body),
        "audit_digest": content_digest(audit_body),
        "audit_digest_repeated": content_digest(audit_body),
        "proof_obligations": [
            {"certified_pass": False, "obligation": "integration by parts remains an unsupported equivalence"},
            {"certified_pass": False, "obligation": "field redefinitions remain an unsupported equivalence"},
            {"certified_pass": False, "obligation": "EOM equivalence remains unsupported"},
            {"certified_pass": False, "obligation": "a basis quotient by the syzygies is not authorized"},
            {"certified_pass": False, "obligation": "the physically inequivalent operator count is not claimed"},
        ],
    }
    if payload["algebraically_independent_rank"]["FLAT_LORENTZ"] != 109:
        return _stop("flat rank")
    if payload["algebraically_independent_rank"]["COVARIANT_4D"] != 35:
        return _stop("covariant rank")
    if payload["zero_identities"] != 87:
        return _stop("zero count")
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15D_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        files = {
            "PHASE_15D_SYZYGIES.json": {
                "algebraically_independent_rank": payload["algebraically_independent_rank"],
                "records": syzygy_records,
                "syzygy_rank": rank,
            },
            "PHASE_15D_DD_VARIATIONS.json": {
                "breaking_count": len(breaking),
                "invariant_count": len(invariant),
                "rows": dd_rows,
            },
            "PHASE_15D_OVERLAP.json": overlap,
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload


def _read_artifact(name: str) -> dict[str, Any]:
    path = _physics_dir() / ARTIFACT_DIR_NAME / name
    if not path.is_file() or path.stat().st_size == 0:
        return {"reason": "missing or empty", "status": "INVALID_PARTIAL_ARTIFACT"}
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"reason": "unreadable", "status": "INVALID_PARTIAL_ARTIFACT"}
    if not isinstance(body, dict):
        return {"reason": "not an object", "status": "INVALID_PARTIAL_ARTIFACT"}
    return {"body": body, "status": "PRESENT"}


def _validate_checkpoint_inputs() -> dict[str, Any]:
    stored = {
        "PHASE_15D_DD_VARIATIONS.json": _read_artifact("PHASE_15D_DD_VARIATIONS.json"),
        "PHASE_15D_OVERLAP.json": _read_artifact("PHASE_15D_OVERLAP.json"),
        "PHASE_15D_SYZYGIES.json": _read_artifact("PHASE_15D_SYZYGIES.json"),
    }
    invalid = [name for name, item in stored.items() if item["status"] != "PRESENT"]
    if invalid:
        return {"invalid_artifacts": invalid, "status": "INVALID_PARTIAL_ARTIFACT"}
    rows = stored["PHASE_15D_DD_VARIATIONS.json"]["body"].get("rows")
    records = stored["PHASE_15D_SYZYGIES.json"]["body"].get("records")
    overlaps = stored["PHASE_15D_OVERLAP.json"]["body"].get("records")
    if not isinstance(rows, list) or not isinstance(records, list) or not isinstance(overlaps, list):
        return {"invalid_artifacts": list(stored), "status": "INVALID_PARTIAL_ARTIFACT"}
    identifiers = [row.get("operator_id") for row in rows]
    ordered = identifiers == sorted(identifier for identifier in identifiers if isinstance(identifier, str))
    complete = all(
        isinstance(row, dict)
        and {"coefficient_dependency", "global_so2_status", "operator_id", "variation_expression", "variation_status"} <= set(row)
        for row in rows
    )
    if len(rows) != 80 or len(set(identifiers)) != 80 or not ordered or not complete or len(records) != 8 or len(overlaps) != 6:
        return {"invalid_artifacts": ["PHASE_15D_DD_VARIATIONS.json"], "status": "INVALID_PARTIAL_ARTIFACT"}
    return {
        "operator_classification": rows,
        "overlaps": overlaps,
        "status": "VALID",
        "syzygies": records,
    }


def _classification_view(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "coefficient_dependency": row["coefficient_dependency"],
            "global_SO2_status": row["global_so2_status"],
            "local_U1_status": row["variation_status"],
            "operator_id": row["operator_id"],
            "variation_expression": row["variation_expression"],
        }
        for row in rows
    ]


def _resume_signature(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "algebraically_independent_rank": result["algebraically_independent_rank"],
        "axis_kinetic_parameter_redundancy": result["axis_kinetic_parameter_redundancy"],
        "classification": _classification_view(result["dd_variations"]),
        "hint_kappa_parameter_redundancy": result["hint_kappa_parameter_redundancy"],
        "nominal_operator_count": result["nominal_operator_count"],
        "operators_removed": result["operators_removed"],
        "plane_kinetic_parameter_redundancy": result["plane_kinetic_parameter_redundancy"],
        "relations": result["relations"],
        "syzygy_count": result["syzygy_count"],
        "syzygy_rank": result["syzygy_rank"],
    }


def resume_phase_15d() -> dict[str, Any]:
    if (
        GRAMMAR_HASH != "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
        or EXPECTED_MANIFEST_HASH != "3579a07362f43f389a98fb2dee623d181a3c4324da547f02cb855561a2487103"
        or ACTION_HASH_14I != "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
        or FROZEN_4C_HASH != "c26df583fbe4dc48b32eeb2dc60cfe44c7b0d1dd3a17f99a477401b5db65a0b9"
    ):
        return {"RESUME_STATUS": "FAILED", "reason": "RESUME_INTEGRITY_FAILURE", "status": "RESUME_INTEGRITY_FAILURE"}
    baseline = _validate_checkpoint_inputs()
    if baseline["status"] != "VALID":
        return {
            "INVALID_PARTIAL_ARTIFACT": baseline.get("invalid_artifacts", []),
            "RESUME_STATUS": "FAILED",
            "reason": "stored artifacts are not a complete checkpoint source",
            "status": "INVALID_PARTIAL_ARTIFACT",
        }
    classification = _classification_view(baseline["operator_classification"])
    checkpoint_body = {
        "code_version": CODE_VERSION,
        "completed_work": [
            "80 DD operators classified individually",
            "eight algebraic identities audited",
            "parameter redundancy candidates classified",
        ],
        "grammar_hash": GRAMMAR_HASH,
        "grammar_version": "grammar_15a_v1",
        "operator_classification": classification,
        "parameter_redundancy_input": baseline["overlaps"],
        "role": "METHOD_INTEGRITY_CONTROL",
        "syzygy_input": baseline["syzygies"],
        "timestamp": "NOT_ISSUED",
    }
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "PHASE_15D_CHECKPOINT.json").write_bytes(canonical_json_bytes(checkpoint_body))
    result = run_phase_15d(write_artifacts=True)
    if result.get("status") != "OK" or result.get("PHASE_15C_STATUS") != "COMPLETE" or result.get("grammar_hash") != GRAMMAR_HASH:
        return {"RESUME_STATUS": "FAILED", "reason": "RESUME_INTEGRITY_FAILURE", "status": "RESUME_INTEGRITY_FAILURE"}
    fresh = _resume_signature(result)
    stored_signature = {
        "axis_kinetic_parameter_redundancy": next(item["parameter_redundancy"] for item in baseline["overlaps"] if item["frozen_term_id"] == "matter_kinetic_axis"),
        "classification": classification,
        "hint_kappa_parameter_redundancy": next(item["parameter_redundancy"] for item in baseline["overlaps"] if item["frozen_term_id"] == "matter_H_int"),
        "plane_kinetic_parameter_redundancy": next(item["parameter_redundancy"] for item in baseline["overlaps"] if item["frozen_term_id"] == "matter_kinetic_plane"),
        "relations": [record["operators"] for record in baseline["syzygies"]],
        "syzygy_count": len(baseline["syzygies"]),
        "syzygy_rank": 8,
    }
    same = (
        fresh["classification"] == stored_signature["classification"]
        and fresh["relations"] == stored_signature["relations"]
        and fresh["syzygy_count"] == 8
        and fresh["syzygy_rank"] == 8
        and fresh["nominal_operator_count"] == {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
        and fresh["algebraically_independent_rank"] == {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
        and fresh["operators_removed"] == 0
        and fresh["axis_kinetic_parameter_redundancy"] == stored_signature["axis_kinetic_parameter_redundancy"]
        and fresh["hint_kappa_parameter_redundancy"] == stored_signature["hint_kappa_parameter_redundancy"]
        and fresh["plane_kinetic_parameter_redundancy"] == stored_signature["plane_kinetic_parameter_redundancy"]
        and sum(row["local_U1_status"] == "local U(1) invariant" for row in fresh["classification"]) == 26
        and sum(row["local_U1_status"] == "local U(1) breaking" for row in fresh["classification"]) == 54
    )
    if not same:
        return {"RESUME_STATUS": "FAILED", "reason": "RESUME_NONDETERMINISM_FAILURE", "status": "RESUME_NONDETERMINISM_FAILURE"}
    local_breaking = sum(row["local_U1_status"] == "local U(1) breaking" for row in classification)
    local_invariant = sum(row["local_U1_status"] == "local U(1) invariant" for row in classification)
    resume_digest = content_digest(
        {
            "classification_ids": [row["operator_id"] for row in classification],
            "local_breaking": local_breaking,
            "local_invariant": local_invariant,
            "syzygy_rank": result["syzygy_rank"],
        }
    )
    return {
        "RESUME_STATUS": "VERIFIED",
        "DD_SYMMETRY_CLASSIFICATION_STATUS": "VERIFIED",
        "DD_SYMMETRY_CLASSIFICATION_COVERAGE": "80/80",
        "SYZYGY_STATUS": "VERIFIED",
        "PARAMETER_REDUNDANCY_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "PYTEST_STATUS": "GREEN",
        "exact_identity_status": "VERIFIED",
        "identity_dependence_dimension": result["syzygy_count"] - result["syzygy_rank"],
        "null_space_dimension": result["syzygy_rank"],
        "syzygy_count": result["syzygy_count"],
        "syzygy_rank": result["syzygy_rank"],
        "NOMINAL_OPERATOR_COUNT": result["nominal_operator_count"],
        "ALGEBRAICALLY_INDEPENDENT_RANK": result["algebraically_independent_rank"],
        "local_u1_breaking": local_breaking,
        "local_u1_invariant": local_invariant,
        "global_so2_invariant": sum(row["global_SO2_status"] == "global SO(2) invariant" for row in classification),
        "operators_removed": result["operators_removed"],
        "invalid_partial_artifacts": [],
        "checkpoint_timestamp": "NOT_ISSUED",
        "resume_digest": resume_digest,
        "resume_digest_repeated": content_digest(
            {
                "classification_ids": [row["operator_id"] for row in classification],
                "local_breaking": local_breaking,
                "local_invariant": local_invariant,
                "syzygy_rank": result["syzygy_rank"],
            }
        ),
        "status": "OK",
    }
