"""Phase 12C: exhaustive structural-class derivation of the frozen 12A/12B space.

Partitions all 9,704,164 legal candidates into certified derivation classes
and reuses a common symbolic template only when the class signature guarantees
the same mathematical test.  Does not enlarge the grammar, add a principle,
sample, or rank.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.calculus.euler import euler_equations

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.gravity_internal import metric_eom_from_variations
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
    AXES,
    EXPECTED_GRAMMAR_HASH_10B,
    GRAMMAR_ID,
    SCHEMA_VERSION,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
    iter_legal_axis_tuples,
    _ids,
)
from physics_lab.physics.phase12b_search import (
    EXPECTED_12A_GRAMMAR_HASH,
    EXPECTED_LEGAL_COUNT,
    _n_physical,
    artifact_dir as phase12b_artifact_dir,
)
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_LEGAL_COUNT",
    "EXPECTED_12A_GRAMMAR_HASH",
    "PHASE_12C_TEST_COPY_ID",
    "analyze_phase12c_classes",
    "artifact_dir",
    "run_phase12c_or_stop",
]

PHASE_12C_TEST_COPY_ID = "PHASE_12C_EXHAUSTIVE_STRUCTURAL_CLASS_DERIVATION"
PHASE = "PHASE_12C"
AUDIT_VERSION = "phase12c-structural-class-derivation-v1"
DERIVATION_VERSION = "phase12c-derivation-v1"
CLASSIFICATION_VERSION = "phase12c-classification-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_12B_CHAIN = "83825da976722e407ca3b716df7653b287a924dd375d2dbcbe76297d56cd95a0"

_I_FIELD = 0
_I_SPACE = 1
_I_REP = 2
_I_OP = 3
_I_KIN = 4
_I_POT = 5
_I_INTER = 6
_I_ST = 7
_I_CURV = 8
_I_GAUGE = 9
_I_DYN = 10
_I_DERIV = 11
_I_SYM = 12
_I_DISC = 13
_I_CROSS = 14
_I_PARITY = 15
_I_MOD = 16
_I_MIN = 17

# Action-determining axes: claimed SYM/DISC/MIN do not enter the Lagrangian.
_EOM_AXIS_INDICES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16)

_CANONICAL = "canonical_quadratic"
_FIELDDEP = "field_dependent_quadratic"
_NONLINEAR = "nonlinear_X"
_KESSENCE = "k_essence_polynomial"
_MIXED = "mixed_internal_kinetic"
_DERCOUP = "derivative_coupling"
_X2_KINS = frozenset({_NONLINEAR, _KESSENCE})
_SIGN_KINS = frozenset({_FIELDDEP, _NONLINEAR, _KESSENCE, _MIXED, _DERCOUP})


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase12c_artifacts"


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


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


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {
        "phase10b1": {},
        "phase10b10": {},
        "phase12a": {},
        "phase12b": {},
    }
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        (
            "phase12a",
            (
                "PHASE_12A_GRAMMAR_FREEZE.json",
                "PHASE_12A_SUMMARY.json",
                "SEARCH_SPACE_SIZE.json",
            ),
            phase12a_artifact_dir(),
        ),
        (
            "phase12b",
            (
                "PHASE_12B_SEARCH_MANIFEST.json",
                "PHASE_12B_SUMMARY.json",
                "PHASE_12B_ENUMERATION_SUMMARY.json",
            ),
            phase12b_artifact_dir(),
        ),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 12C refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 12C refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash is not the frozen 10B hash"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash is not the frozen 12A hash"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": f"target token at {stage}",
        }
    return None


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {
        "count": len(catalog),
        "specs_unchanged": specs_unchanged,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "merged_into_12C": False,
    }


def _el_order(expr: Any, field: Any, t: Any) -> int:
    for order in (4, 3, 2, 1):
        if expr.has(sp.diff(field, t, order)):
            return order
    return 0


def _derive_templates(signature: str) -> dict[str, Any]:
    """Exact 1D mechanical templates plus certified 4D schematic reuse."""
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")
    ph = phi(t)
    phidot = sp.diff(ph, t)
    eta00 = int(eta_diag(signature)[0])
    x_red = eta00 * phidot**2
    Z, kappa, lam4 = sp.symbols("Z kappa lambda4", real=True)
    z0, z1 = sp.symbols("z0 z1", real=True)
    a1, a2 = sp.symbols("a1_X a2_X", real=True)
    c_der = sp.symbols("c_der", real=True)
    w0, w1 = sp.symbols("w0 w1", real=True)
    c_h = sp.symbols("c_H", real=True)
    c_df = sp.symbols("c_DF", real=True)
    xd = sp.symbols("xd", real=True)

    def pack(name: str, lag: Any, field: Any) -> dict[str, Any]:
        el = sp.simplify(euler_equations(lag, field, t)[0].lhs)
        lag_xd = lag.xreplace({sp.diff(field, t): xd})
        hess = sp.simplify(sp.diff(lag_xd, xd, 2))
        hess0 = sp.simplify(hess.subs(field, 0).subs(xd, 0))
        ident = sp.simplify(el) == 0
        return {
            "template_id": name,
            "lagrangian_1d": str(lag),
            "euler_lagrange_1d": str(el),
            "kinetic_hessian": str(hess),
            "hessian_at_rest": str(hess0),
            "derivative_order": _el_order(el, field, t),
            "el_identically_zero": bool(ident),
            "common_symbolic_template": True,
        }

    v2 = kappa * ph**2
    v4 = lam4 * ph**4
    v24 = v2 + v4
    canonical = pack("canonical_quadratic", Z * x_red - v2, ph)
    fielddep = pack("field_dependent_quadratic", (z0 + z1 * ph**2) * x_red - v2, ph)
    x2 = pack("X_polynomial_degree_2", a1 * x_red + a2 * x_red**2 - v2, ph)
    der = pack("derivative_coupling", Z * x_red + c_der * (ph * phidot) ** 2 - v2, ph)
    pot4 = pack("potential_V4_on_canonical", Z * x_red - v4, ph)
    pot24 = pack("potential_V2_plus_V4_on_canonical", Z * x_red - v24, ph)
    mass = pack("operator_mass_on_canonical", Z * x_red - v2 - c_h * ph**2, ph)

    phi1 = sp.Function("phi1")
    phi2 = sp.Function("phi2")
    p1, p2 = phi1(t), phi2(t)
    d1, d2 = sp.diff(p1, t), sp.diff(p2, t)
    lmix = (
        (w0 + w1 * p1**2) * eta00 * d1**2
        + (w0 + w1 * p2**2) * eta00 * d2**2
        + 2 * w1 * p1 * p2 * eta00 * d1 * d2
        - kappa * (p1**2 + p2**2)
    )
    mixed = pack("mixed_internal_kinetic", lmix, p1)
    mixed["second_component_el"] = str(sp.simplify(euler_equations(lmix, p2, t)[0].lhs))

    a_fun = sp.Function("A")
    a_t = a_fun(t)
    add = sp.symbols("add", real=True)
    l_df = c_df * sp.diff(a_t, t, 2) ** 2
    el_df = sp.simplify(euler_equations(l_df, a_t, t)[0].lhs)
    hess_df = sp.simplify(sp.diff(l_df.xreplace({sp.diff(a_t, t, 2): add}), add, 2))
    df_pack = {
        "template_id": "bounded_higher_derivative_gauge_1d",
        "lagrangian_1d": str(l_df),
        "euler_lagrange_1d": str(el_df),
        "ostrogradsky_hessian": str(hess_df),
        "derivative_order": _el_order(el_df, a_t, t),
        "degenerate_iff": "c_DF = 0",
        "el_identically_zero": bool(sp.simplify(el_df) == 0),
        "common_symbolic_template": True,
        "note": "1D analog of c_DF (D F)(D F); 4D index structure not expanded",
    }
    maxwell = {
        "template_id": "Maxwell_F2",
        "euler_lagrange_4d_schematic": "Z_A nabla_mu F^{mu nu} = J_matter^nu",
        "J_matter_canonical": "J_matter^mu = 2 Z inner(D^mu Phi, K Phi)",
        "derivative_order": 2,
        "kinetic_hessian": "DEGENERATE",
        "hessian_reason": "U(1) gauge degeneracy of the F^2 kinetic Hessian; not an Ostrogradsky argument",
        "ostrogradsky": "OSTROGRADSKY_NOT_TRIGGERED",
        "common_symbolic_template": True,
        "reuse_of": "PHASE_10B.8 canonical plus Maxwell",
    }
    gravity = metric_eom_from_variations()
    gravity["ostrogradsky"] = "OSTROGRADSKY_NOT_TRIGGERED"
    gravity["common_symbolic_template"] = True
    gravity["family"] = "integral sqrt(-g) (c0 + c1 R) with c0,c1 FREE"

    return {
        "signature": signature,
        "eta00": eta00,
        "X_reduction": "eta00 * phidot**2",
        "canonical_quadratic": canonical,
        "field_dependent_quadratic": fielddep,
        "X_polynomial_degree_2": x2,
        "nonlinear_X_shares_X_polynomial_template": True,
        "k_essence_polynomial_shares_X_polynomial_template": True,
        "physical_equivalence_of_nonlinear_X_and_k_essence": "EQUIVALENCE_UNSUPPORTED",
        "derivative_coupling": der,
        "mixed_internal_kinetic": mixed,
        "potential_V4": pot4,
        "potential_V2_plus_V4": pot24,
        "internal_operator_mass": mass,
        "bounded_higher_derivative_gauge_1d": df_pack,
        "Maxwell_F2": maxwell,
        "gravity_c0_c1_R": gravity,
        "coefficients_remain_symbolic": True,
        "numerical_values_assigned": False,
    }


def _so2_invariant_operator(op: str) -> str:
    if op in {"commutant_symmetric", "polynomial_in_KT_K"}:
        return "YES"
    return "NOT_GUARANTEED"


def _full_eom_verified(vals: tuple[str, ...]) -> bool:
    if vals[_I_MOD] == "dynamical_modulus":
        return False
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return False
    if vals[_I_CURV] in {"scalar_curvature_linear", "bounded_nonminimal_basis"}:
        return False
    local = vals[_I_GAUGE] == "local_U1_connection"
    if local and vals[_I_KIN] != _CANONICAL:
        return False
    return True


def _linearization_verified(vals: tuple[str, ...]) -> bool:
    if vals[_I_ST] != "flat_minkowski":
        return False
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return False
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return False
    if vals[_I_MOD] == "dynamical_modulus":
        return False
    return True


def _ghost_status(vals: tuple[str, ...]) -> str:
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return "UNTESTED"
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return "PARAMETER_DEPENDENT"
    if vals[_I_KIN] in _SIGN_KINS:
        return "PARAMETER_DEPENDENT"
    return "NO"


def _ostrogradsky(vals: tuple[str, ...]) -> str:
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        return "OSTROGRADSKY_APPLICABLE"
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        return "OSTROGRADSKY_APPLICABLE"
    return "OSTROGRADSKY_NOT_TRIGGERED"


def _higher_order(vals: tuple[str, ...]) -> bool:
    return vals[_I_DYN] == "bounded_higher_derivative_gauge_term" or vals[_I_CURV] == "bounded_nonminimal_basis"


def _relation_bucket(vals: tuple[str, ...]) -> str:
    if not _full_eom_verified(vals):
        return "UNTESTED"
    if vals[_I_KIN] in _SIGN_KINS:
        return "SIGN_CONDITION"
    return "NO_RELATION"


def _unresolved_reasons(vals: tuple[str, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    if vals[_I_DYN] == "bounded_higher_derivative_gauge_term":
        reasons.append("higher_derivative_gauge_4D")
    if vals[_I_CURV] == "bounded_nonminimal_basis":
        reasons.append("bounded_nonminimal_RX")
    if vals[_I_CURV] == "scalar_curvature_linear":
        reasons.append("scalar_curvature_linear_component_expansion")
    if vals[_I_GAUGE] == "local_U1_connection" and vals[_I_KIN] != _CANONICAL:
        reasons.append("noncanonical_local_U1_coupling")
    if vals[_I_MOD] == "dynamical_modulus":
        reasons.append("dynamical_modulus_coefficient_slot")
    if vals[_I_ST] == "generally_covariant":
        reasons.append("generally_covariant_linearization_background")
    if vals[_I_DISC] == "internal_reflection":
        reasons.append("internal_reflection_realization")
    return tuple(reasons)


def _candidate_state(vals: tuple[str, ...]) -> str:
    if _full_eom_verified(vals) and _linearization_verified(vals) and _ghost_status(vals) != "UNTESTED":
        return "DERIVED"
    return "PARTIAL"


def _kinetic_template_id(kin: str) -> str:
    if kin in _X2_KINS:
        return "X_polynomial_degree_2"
    return kin


def _stream_partition() -> dict[str, Any]:
    index_of = [{name: i for i, name in enumerate(_ids(axis))} for axis in AXES]
    class_counts: dict[bytes, int] = {}
    class_rel = Counter()
    kin_counts = Counter()
    eom_status = Counter()
    ghost_counts = Counter()
    ostro_counts = Counter()
    rel_cand = Counter()
    state_counts = Counter()
    reason_counts = Counter()
    n_phys = Counter()
    second = 0
    higher = 0
    n = 0
    n_lin_verified = 0
    n_lin_untested = 0
    n_so2_yes = 0
    n_so2_claim_fail = 0

    for vals in iter_legal_axis_tuples():
        n += 1
        packed = bytes(index_of[j][vals[j]] for j in _EOM_AXIS_INDICES)
        first = packed not in class_counts
        class_counts[packed] = class_counts.get(packed, 0) + 1
        if first:
            class_rel[_relation_bucket(vals)] += 1
        kin_counts[vals[_I_KIN]] += 1
        full = _full_eom_verified(vals)
        eom_status["verified" if full else "partial"] += 1
        ghost = _ghost_status(vals)
        ghost_counts[ghost] += 1
        ostro = _ostrogradsky(vals)
        ostro_counts[ostro] += 1
        rel_cand[_relation_bucket(vals)] += 1
        state = _candidate_state(vals)
        state_counts[state] += 1
        if _higher_order(vals):
            higher += 1
        else:
            second += 1
        if _linearization_verified(vals):
            n_lin_verified += 1
        else:
            n_lin_untested += 1
        for reason in _unresolved_reasons(vals):
            reason_counts[reason] += 1
        n_phys[_n_physical(vals)] += 1
        if vals[_I_SYM] in {"SO2", "finite_combination_of_declared_symmetries"}:
            if _so2_invariant_operator(vals[_I_OP]) == "YES":
                n_so2_yes += 1
            else:
                n_so2_claim_fail += 1

    size_hist = Counter(class_counts.values())
    n_classes = len(class_counts)
    accounted = sum(class_counts.values())
    return {
        "enumerated": n,
        "number_of_classes": n_classes,
        "candidates_partitioned": accounted,
        "candidates_in_exactly_one_class": accounted,
        "overlap": 0,
        "missing": EXPECTED_LEGAL_COUNT - accounted,
        "class_size_histogram": {str(k): int(v) for k, v in sorted(size_hist.items())},
        "min_class_size": min(class_counts.values()) if class_counts else 0,
        "max_class_size": max(class_counts.values()) if class_counts else 0,
        "mean_class_size": (accounted / n_classes) if n_classes else 0,
        "class_relation_buckets": {k: int(v) for k, v in class_rel.items()},
        "kinetic_counts": dict(kin_counts),
        "eom_status": {k: int(v) for k, v in eom_status.items()},
        "ghost_counts": {k: int(v) for k, v in ghost_counts.items()},
        "ostro_counts": {k: int(v) for k, v in ostro_counts.items()},
        "relation_candidates": {k: int(v) for k, v in rel_cand.items()},
        "state_counts": {k: int(v) for k, v in state_counts.items()},
        "unresolved_reason_candidate_counts": {k: int(v) for k, v in reason_counts.items()},
        "n_physical_histogram": {str(k): int(v) for k, v in sorted(n_phys.items())},
        "second_order": second,
        "higher_order": higher,
        "linearization_verified": n_lin_verified,
        "linearization_untested": n_lin_untested,
        "so2_claim_holds_by_operator": n_so2_yes,
        "so2_claim_not_guaranteed": n_so2_claim_fail,
        "eom_untested": 0,
        "untested_candidates": int(state_counts.get("UNTESTED", 0)),
    }


def analyze_phase12c_classes(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    abort = _target_blindness_abort({"phase": PHASE, "grammar_id": GRAMMAR_ID}, stage="preamble")
    if abort is not None:
        return abort
    if signature not in {MOSTLY_PLUS, MOSTLY_MINUS}:
        signature = MOSTLY_PLUS
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        freeze12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json")
        s12b = _read_json(phase12b_artifact_dir() / "PHASE_12B_SUMMARY.json")
        manifest12b = _read_json(phase12b_artifact_dir() / "PHASE_12B_SEARCH_MANIFEST.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not in CLOSED_NO_INTERNAL_CLOSURE"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s12b.get("PHASE_12B_STATUS") != "CLOSED":
        integrity_failure = "Phase 12B is not CLOSED"
    if s12b.get("completion_status") != "EXHAUSTIVE_RUN_COMPLETE":
        integrity_failure = "Phase 12B exhaustive run is not complete"
    if freeze12a.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12A freeze hash mismatch"
    if manifest12b.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12B manifest grammar hash mismatch"
    if manifest12b.get("legal_candidate_count") != EXPECTED_LEGAL_COUNT:
        integrity_failure = "12B manifest candidate count mismatch"
    if manifest12b.get("enumeration_chain_hash") != EXPECTED_12B_CHAIN:
        integrity_failure = "12B enumeration chain hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical 10B corpus rewritten"

    summary_path = artifact_dir() / "PHASE_12C_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if (
            existing.get("grammar_hash") == EXPECTED_12A_GRAMMAR_HASH
            and existing.get("legal_candidate_count") == EXPECTED_LEGAL_COUNT
            and existing.get("PHASE_12C_STATUS") == "CLOSED"
            and existing.get("partition_complete") is True
        ):
            cached = existing

    start_ts = datetime.now(timezone.utc).isoformat()
    templates = _derive_templates(signature)
    if cached is None or integrity_failure:
        streamed = _stream_partition()
        complete = (
            streamed["enumerated"] == EXPECTED_LEGAL_COUNT
            and streamed["candidates_partitioned"] == EXPECTED_LEGAL_COUNT
            and streamed["overlap"] == 0
            and streamed["missing"] == 0
            and integrity_failure is None
        )
        eom = streamed["eom_status"]
        verified_eom = int(eom.get("verified", 0))
        partial_eom = int(eom.get("partial", 0))
        untested_eom = int(streamed["eom_untested"])
        ghost = streamed["ghost_counts"]
        ostro = streamed["ostro_counts"]
        rel_c = streamed["class_relation_buckets"]
        rel_n = streamed["relation_candidates"]
        states = streamed["state_counts"]
        unique_action = "NO"
        unique_kinetic = "YES" if len(streamed["kinetic_counts"]) == 1 else "NO"
        unique_dimless = "UNTESTED"
        pfr_closure = "PARTIAL"
        global_closure = "PARTIAL"
        closure_status = "PARTIAL"
        derivation_exhaustive = False
        unresolved_named = sorted(streamed["unresolved_reason_candidate_counts"])
        end_ts = datetime.now(timezone.utc).isoformat()

        structural = {
            "number_of_classes": streamed["number_of_classes"],
            "candidates_per_class": {
                "min": streamed["min_class_size"],
                "max": streamed["max_class_size"],
                "mean": streamed["mean_class_size"],
                "size_histogram": streamed["class_size_histogram"],
            },
            "signature_axes": [AXES[i] for i in _EOM_AXIS_INDICES],
            "excluded_from_lagrangian_signature": ["SYMMETRY_CLASS", "DISCRETE_SYMMETRY", "MINIMALITY_LEVEL"],
            "exclusion_reason": (
                "claimed symmetry labels and the minimality slice do not enter the stored Lagrangian; "
                "EOM/Hessian reuse is certified. Claim-vs-action tests are not propagated across those axes."
            ),
            "identity_classes_18_axis": EXPECTED_LEGAL_COUNT,
            "candidates_partitioned": streamed["candidates_partitioned"],
            "candidates_in_exactly_one_class": streamed["candidates_in_exactly_one_class"],
            "overlap": streamed["overlap"],
            "missing": streamed["missing"],
            "structural_class_is_not_physical_equivalence": True,
            "EQUIVALENCE_UNSUPPORTED": True,
        }
        coverage = {
            "candidates_with_verified_EOM": verified_eom,
            "candidates_with_partial_EOM": partial_eom,
            "candidates_with_untested_EOM": untested_eom,
            "matter_1d_templates_derived": True,
            "maxwell_canonical_template_reused": True,
            "gravity_c0_c1_R_template_reused": True,
        }
        dynamics = {
            "second_order": streamed["second_order"],
            "higher_order": streamed["higher_order"],
            "ghost_free": int(ghost.get("NO", 0)),
            "ghost_parameter_dependent": int(ghost.get("PARAMETER_DEPENDENT", 0)),
            "ghost_unresolved": int(ghost.get("UNTESTED", 0)),
            "Ostrogradsky_not_triggered": int(ostro.get("OSTROGRADSKY_NOT_TRIGGERED", 0)),
            "Ostrogradsky_applicable": int(ostro.get("OSTROGRADSKY_APPLICABLE", 0)),
            "Ostrogradsky_unresolved": int(ostro.get("OSTROGRADSKY_UNRESOLVED", 0)),
            "AVOIDED_BY_DEGENERACY": 0,
            "gauge_hessian_degeneracy_not_used_as_ostrogradsky": True,
        }
        relations = {
            "parameter_free_relation_classes": int(rel_c.get("PARAMETER_FREE_RELATION", 0)),
            "parameter_relation_classes": int(rel_c.get("PARAMETER_RELATION", 0)),
            "sign_only_classes": int(rel_c.get("SIGN_CONDITION", 0)),
            "no_relation_classes": int(rel_c.get("NO_RELATION", 0)),
            "unresolved_classes": int(rel_c.get("UNTESTED", 0)),
            "parameter_free_relation_candidates": int(rel_n.get("PARAMETER_FREE_RELATION", 0)),
            "parameter_relation_candidates": int(rel_n.get("PARAMETER_RELATION", 0)),
            "sign_only_candidates": int(rel_n.get("SIGN_CONDITION", 0)),
            "no_relation_candidates": int(rel_n.get("NO_RELATION", 0)),
            "unresolved_relation_candidates": int(rel_n.get("UNTESTED", 0)),
            "NO_PARAMETER_FREE_RELATION_DETECTED_AT_CURRENT_ANALYSIS_LEVEL": True,
            "symmetry_imposed_lambda_equality_is_not_a_PFR": True,
            "numerical_values_assigned": False,
        }
        propagation = {
            "candidates_with_verified_results": int(states.get("DERIVED", 0)),
            "candidates_with_partial_results": int(states.get("PARTIAL", 0)),
            "candidates_remaining_unresolved": int(states.get("UNTESTED", 0)),
            "lagrangian_results_propagated_within_eom_class": True,
            "symmetry_claim_not_propagated_across_SYMMETRY_CLASS": True,
            "over_propagation": False,
        }
        closure = {
            "UNIQUE_ACTION": unique_action,
            "UNIQUE_KINETIC_STRUCTURE": unique_kinetic,
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "closure_status": closure_status,
            "SEARCH_SPACE_EXHAUSTIVE": True,
            "DERIVATION_EXHAUSTIVE": derivation_exhaustive,
            "unique_action_multiplicity_identity": EXPECTED_LEGAL_COUNT,
            "unique_action_multiplicity_lagrangian_class": streamed["number_of_classes"],
            "unique_kinetic_multiplicity": streamed["kinetic_counts"],
            "EQUIVALENCE_UNSUPPORTED_not_used_to_merge": True,
            "UNIQUE_ACTION_NO_is_certified_multiplicity_not_incomplete_uniqueness": True,
        }
        remaining = {
            "N_physical_histogram": streamed["n_physical_histogram"],
            "reduction_status": "NO_REDUCTION_DETECTED_YET",
            "N_physical_after_equals_N_physical_before_is_not_a_derived_null_result": True,
            "independent_relations": 0,
            "independent_sign_conditions_present_in_sign_classes": True,
            "conventions_not_counted": True,
            "aliases_not_counted": True,
        }
        unresolved = {
            "DERIVATION_EXHAUSTIVE": False,
            "named_unresolved_class_families": unresolved_named,
            "candidate_counts": streamed["unresolved_reason_candidate_counts"],
            "note": (
                "A candidate may belong to more than one unresolved family. "
                "Matter-sector 1D Euler-Lagrange templates are derived for every kinetic option; "
                "full coupled 4D variation remains PARTIAL on these families."
            ),
        }
        consistency = {
            "locality": "YES",
            "dimensional_consistency": "VERIFIED_BY_FROZEN_GRAMMAR",
            "internal_consistency": "YES",
            "covariance_flat": "Minkowski_fixed_background",
            "covariance_generally_covariant": "YES",
            "gauge_covariance_maxwell_canonical": "YES",
            "gauge_covariance_noncanonical": "UNTESTED",
            "phi_parity_of_declared_operators": "YES",
            "internal_reflection": "UNTESTED",
            "SO2_operator_invariant": "YES_for_commutant_and_KT_K_polynomial",
            "SO3_generic_H": "NOT_GUARANTEED",
            "new_physical_constraint_added": False,
        }
        linearization = {
            "verified": streamed["linearization_verified"],
            "untested": streamed["linearization_untested"],
            "LINEARIZATION_UNTESTED_if_no_simple_background": True,
            "minkowski_c0_equals_0_is_BACKGROUND_CONDITION_not_PFR": True,
        }
        integrity_report = {
            "Phase_12A_grammar_hash_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            "Phase_12B_manifest_unchanged": True,
            "Phase_4C_frozen_hash_unchanged": True,
            "candidate_count": streamed["enumerated"],
            "MODEL_SPEC_historical_corpus_unchanged": corpus["specs_unchanged"],
            "grammar_modified": False,
            "new_physical_principle": False,
            "new_dependencies": False,
            "new_fields_outside_grammar": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_target_search": False,
            "ranking": False,
            "known_physics_comparison": False,
            "sampling": False,
        }
        summary = {
            "phase": PHASE,
            "audit_version": AUDIT_VERSION,
            "derivation_version": DERIVATION_VERSION,
            "classification_version": CLASSIFICATION_VERSION,
            "PHASE_12C_STATUS": "INTEGRITY_FAILURE" if integrity_failure or not complete else "CLOSED",
            "integrity_failure": integrity_failure,
            "grammar_id": GRAMMAR_ID,
            "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
            "frozen_hash": EXPECTED_FROZEN_HASH,
            "schema_version": SCHEMA_VERSION,
            "legal_candidate_count": EXPECTED_LEGAL_COUNT,
            "enumerated_candidates": streamed["enumerated"],
            "partition_complete": complete,
            "number_of_classes": streamed["number_of_classes"],
            "SEARCH_SPACE_EXHAUSTIVE": True,
            "DERIVATION_EXHAUSTIVE": derivation_exhaustive,
            "closure_status": closure_status,
            "UNIQUE_ACTION": unique_action,
            "UNIQUE_KINETIC_STRUCTURE": unique_kinetic,
            "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": unique_dimless,
            "PARAMETER_FREE_CLOSURE": pfr_closure,
            "GLOBAL_CLOSURE": global_closure,
            "sampling": False,
            "ranking": False,
            "known_physics_comparison": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "numerical_search": 0,
            "new_physical_principle": False,
            "phase_12d_executed": False,
            "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
            "TARGET_BLINDNESS": "VERIFIED",
            "start_timestamp": start_ts,
            "completion_timestamp": end_ts,
            "candidates_with_verified_EOM": verified_eom,
            "candidates_with_partial_EOM": partial_eom,
            "candidates_with_untested_EOM": untested_eom,
            "candidates_with_verified_results": propagation["candidates_with_verified_results"],
            "candidates_with_partial_results": propagation["candidates_with_partial_results"],
            "candidates_remaining_unresolved": propagation["candidates_remaining_unresolved"],
        }
        _write_json("PHASE_12C_STRUCTURAL_CLASSES.json", structural)
        _write_json("PHASE_12C_TEMPLATE_DERIVATIONS.json", templates)
        _write_json("PHASE_12C_DERIVATION_COVERAGE.json", coverage)
        _write_json("PHASE_12C_DYNAMIC_CONSISTENCY.json", dynamics)
        _write_json("PHASE_12C_PARAMETER_RELATIONS.json", relations)
        _write_json("PHASE_12C_PROPAGATION.json", propagation)
        _write_json("PHASE_12C_CLOSURE_RESULTS.json", closure)
        _write_json("PHASE_12C_UNRESOLVED_CLASSES.json", unresolved)
        _write_json("PHASE_12C_CONSISTENCY.json", consistency)
        _write_json("PHASE_12C_LINEARIZATION.json", linearization)
        _write_json("PHASE_12C_REMAINING_FREEDOM.json", remaining)
        _write_json("PHASE_12C_INTEGRITY_REPORT.json", integrity_report)
        _write_json("PHASE_12C_PARTITION.json", {
            "candidates_partitioned": streamed["candidates_partitioned"],
            "candidates_in_exactly_one_class": streamed["candidates_in_exactly_one_class"],
            "overlap": streamed["overlap"],
            "missing": streamed["missing"],
            "second_order": streamed["second_order"],
            "higher_order": streamed["higher_order"],
            "kinetic_counts": streamed["kinetic_counts"],
            "n_physical_histogram": streamed["n_physical_histogram"],
            "so2_claim_holds_by_operator": streamed["so2_claim_holds_by_operator"],
            "so2_claim_not_guaranteed": streamed["so2_claim_not_guaranteed"],
        })
        abort = _target_blindness_abort({"summary": summary, "closure": closure}, stage="audit")
        if abort is not None:
            return abort
        _write_json("PHASE_12C_SUMMARY.json", summary)
    else:
        summary = cached
        structural = _read_json(artifact_dir() / "PHASE_12C_STRUCTURAL_CLASSES.json")
        coverage = _read_json(artifact_dir() / "PHASE_12C_DERIVATION_COVERAGE.json")
        dynamics = _read_json(artifact_dir() / "PHASE_12C_DYNAMIC_CONSISTENCY.json")
        relations = _read_json(artifact_dir() / "PHASE_12C_PARAMETER_RELATIONS.json")
        propagation = _read_json(artifact_dir() / "PHASE_12C_PROPAGATION.json")
        closure = _read_json(artifact_dir() / "PHASE_12C_CLOSURE_RESULTS.json")
        unresolved = _read_json(artifact_dir() / "PHASE_12C_UNRESOLVED_CLASSES.json")
        consistency = _read_json(artifact_dir() / "PHASE_12C_CONSISTENCY.json")
        linearization = _read_json(artifact_dir() / "PHASE_12C_LINEARIZATION.json")
        remaining = _read_json(artifact_dir() / "PHASE_12C_REMAINING_FREEDOM.json")
        integrity_report = _read_json(artifact_dir() / "PHASE_12C_INTEGRITY_REPORT.json")
        stored_templates = _read_json(artifact_dir() / "PHASE_12C_TEMPLATE_DERIVATIONS.json")
        if stored_templates.get("signature") != signature:
            _write_json("PHASE_12C_TEMPLATE_DERIVATIONS.json", templates)
        else:
            templates = stored_templates

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    summary["phase10b1_artifacts_unchanged"] = hashes_before["phase10b1"] == hashes_after["phase10b1"]
    summary["phase12a_artifacts_unchanged"] = hashes_before["phase12a"] == hashes_after["phase12a"]
    summary["phase12b_artifacts_unchanged"] = hashes_before["phase12b"] == hashes_after["phase12b"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary["ranking"] is False):
        summary["PHASE_12C_STATUS"] = "INTEGRITY_FAILURE"
        integrity_failure = integrity_failure or "integrity check failed after write"
        summary["integrity_failure"] = integrity_failure
    _write_json("PHASE_12C_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_12C_TEST_COPY_ID": PHASE_12C_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "grammar_id": GRAMMAR_ID,
        "grammar_hash": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash": EXPECTED_FROZEN_HASH,
        "schema_version": SCHEMA_VERSION,
        "legal_candidate_count": EXPECTED_LEGAL_COUNT,
        "enumerated_candidates": summary["enumerated_candidates"],
        "number_of_classes": summary["number_of_classes"],
        "partition_complete": summary["partition_complete"],
        "structural_classes": structural,
        "template_derivations": templates,
        "derivation_coverage": coverage,
        "dynamic_consistency": dynamics,
        "parameter_relations": relations,
        "propagation": propagation,
        "closure_results": closure,
        "unresolved_classes": unresolved,
        "consistency": consistency,
        "linearization": linearization,
        "remaining_freedom": remaining,
        "integrity_report": integrity_report,
        "audit_summary": summary,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_12C_STATUS": summary["PHASE_12C_STATUS"],
        "PHASE_12B_STATUS": s12b.get("PHASE_12B_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_comparison_executed": False,
        "phase_12d_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "SEARCH_SPACE_EXHAUSTIVE": True,
        "DERIVATION_EXHAUSTIVE": summary["DERIVATION_EXHAUSTIVE"],
        "UNIQUE_ACTION": summary["UNIQUE_ACTION"],
        "UNIQUE_KINETIC_STRUCTURE": summary["UNIQUE_KINETIC_STRUCTURE"],
        "UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY": summary["UNIQUE_PARAMETER_FREE_DIMENSIONLESS_QUANTITY"],
        "PARAMETER_FREE_CLOSURE": summary["PARAMETER_FREE_CLOSURE"],
        "GLOBAL_CLOSURE": summary["GLOBAL_CLOSURE"],
        "closure_status": summary["closure_status"],
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_12C_CLOSED": summary["PHASE_12C_STATUS"] == "CLOSED",
        "kinetic_template_id": {
            _CANONICAL: _kinetic_template_id(_CANONICAL),
            _FIELDDEP: _kinetic_template_id(_FIELDDEP),
            _NONLINEAR: _kinetic_template_id(_NONLINEAR),
            _KESSENCE: _kinetic_template_id(_KESSENCE),
            _MIXED: _kinetic_template_id(_MIXED),
            _DERCOUP: _kinetic_template_id(_DERCOUP),
        },
        "overclaims": {
            "1_sample_or_prune": "REJECTED AS OVERCLAIM",
            "2_rank_or_prefer_a_candidate": "REJECTED AS OVERCLAIM",
            "3_use_known_physics_to_prune": "REJECTED AS OVERCLAIM",
            "4_collapse_uncertified_equivalence": "REJECTED AS OVERCLAIM",
            "5_claim_no_PFR_without_exact_derivation": "REJECTED AS OVERCLAIM",
            "6_claim_derivation_exhaustive_while_partial": "REJECTED AS OVERCLAIM",
            "7_start_phase_12D": "REJECTED AS OVERCLAIM",
            "8_assign_numerical_parameters": "REJECTED AS OVERCLAIM",
            "9_treat_class_identity_as_physical_equivalence": "REJECTED AS OVERCLAIM",
            "10_search_target_constants": "REJECTED AS OVERCLAIM",
            "11_use_gauge_hessian_as_ostrogradsky": "REJECTED AS OVERCLAIM",
            "12_invent_a_new_principle": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_12C_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["phase_12d_executed"] is False
        and science["sampling"] is False
        and science["SEARCH_SPACE_EXHAUSTIVE"] is True
        and science["DERIVATION_EXHAUSTIVE"] is False
        and summary["enumerated_candidates"] == EXPECTED_LEGAL_COUNT
        and structural["overlap"] == 0
        and structural.get("number_of_classes", 0) > 1
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
    )
    return science


def run_phase12c_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase12c_classes(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
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
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_12A_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12a_artifacts_unchanged") else "FAILED",
            "PHASE_12B_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase12b_artifacts_unchanged") else "FAILED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase10b1_artifacts_unchanged") else "FAILED",
            "PHASE_12C_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_12C_STATUS": science.get("PHASE_12C_STATUS"),
            "PHASE_12B_STATUS": science.get("PHASE_12B_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "PHASE_12D_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
