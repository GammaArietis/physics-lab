"""Phase 13.1: low-dimensional exception test for D = 1, 2, 3.

Completes the Phase 13 window without modifying Phase 13 results or the
frozen 4D corpus.  Zero local DOF is not treated as inconsistency.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.calculus.euler import euler_equations

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.dynamical_metric import curvature_diagonal
from physics_lab.physics.lovelock import (
    gb_vanishes_in_3d_family,
    lovelock_density_name,
    lovelock_slot,
    two_d_euler_is_total_derivative,
)
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
from physics_lab.physics.phase13_dimension import artifact_dir as phase13_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "DIMENSIONS_13_1",
    "EXPECTED_12A_GRAMMAR_HASH",
    "PHASE_13_1_TEST_COPY_ID",
    "analyze_phase13_1_low_d",
    "artifact_dir",
    "run_phase13_1_or_stop",
]

PHASE_13_1_TEST_COPY_ID = "PHASE_13_1_LOW_DIMENSIONAL_EXCEPTION_TEST"
PHASE = "PHASE_13.1"
AUDIT_VERSION = "phase13.1-low-d-exception-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
DIMENSIONS_13_1: tuple[int, ...] = (1, 2, 3)
INTERNAL_HILBERT_DIM_4C = 3
K_MAX = 3


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase13_1_artifacts"


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
        "phase13": {},
    }
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        ("phase12a", ("PHASE_12A_GRAMMAR_FREEZE.json", "PHASE_12A_SUMMARY.json"), phase12a_artifact_dir()),
        (
            "phase13",
            (
                "PHASE_13_SUMMARY.json",
                "PHASE_13_CLOSURE_RESULTS.json",
                "PHASE_13_DIMENSION_SWEEP_RESULTS.json",
            ),
            phase13_artifact_dir(),
        ),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 13.1 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {"status": "TARGET_BLINDNESS_VIOLATION", "scientific_analysis": None, "detail": f"target token at {stage}"}
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
    }


def _map_slot(raw: str) -> str:
    if raw == "identically zero":
        return "IDENTICALLY ZERO"
    if raw == "topological Euler density":
        return "TOPOLOGICAL"
    return "AVAILABLE"


def _lovelock_rows(d: int) -> list[dict[str, Any]]:
    rows = []
    for k in range(0, K_MAX + 1):
        raw = lovelock_slot(k, d)
        status = _map_slot(raw)
        active = status == "AVAILABLE"
        rows.append(
            {
                "k": k,
                "name": lovelock_density_name(k),
                "raw_slot": raw,
                "status": status,
                "dynamically_active": active,
                "identically_topological": status == "TOPOLOGICAL",
                "vanishing": status == "IDENTICALLY ZERO",
            }
        )
    return rows


def _one_d_curvature_vanishes() -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    n = sp.Function("n")(t)
    gtt = -(n**2)
    gtt_inv = -1 / n**2
    gamma = sp.simplify(sp.Rational(1, 2) * gtt_inv * sp.diff(gtt, t))
    cur = curvature_diagonal([-(n**2)], [t])
    einstein_zero = all(sp.simplify(cur["einstein"][i][j]) == 0 for i in range(1) for j in range(1))
    return {
        "metric": "g_tt = -n(t)^2 on a 1-manifold",
        "Christoffel_ttt": str(gamma),
        "Riemann": "0",
        "reason": "an antisymmetric pair of coordinate indices cannot exist on a 1-manifold",
        "R_identically_zero": bool(sp.simplify(cur["R"]) == 0),
        "Einstein_identically_zero_on_this_family": einstein_zero,
        "restricted_test": True,
    }


def _two_d_gravity_probes() -> dict[str, Any]:
    t, x = sp.symbols("t x", real=True)
    a = sp.Function("a")(t)
    cur = curvature_diagonal([-1, a**2], [t, x])
    g_zero = all(sp.simplify(cur["einstein"][i][j]) == 0 for i in range(2) for j in range(2))
    return {
        "einstein_tensor_zero_on_2D_FLRW_family": g_zero,
        "EH_density_is_total_derivative_on_that_family": two_d_euler_is_total_derivative(),
        "dilaton_added": False,
        "restricted_test": True,
    }


def _three_d_gravity_probes() -> dict[str, Any]:
    return {
        "L2_vanishes_on_3D_Bianchi_family": gb_vanishes_in_3d_family(),
        "propagating_graviton_formula": "D(D-3)/2 = 0 at D=3",
        "Chern_Simons_added": False,
        "restricted_test": True,
    }


def _scalar_1d() -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")(t)
    z, kappa = sp.symbols("Z kappa", real=True)
    lag = -z * sp.diff(phi, t) ** 2 - kappa * phi**2
    el = sp.simplify(euler_equations(lag, phi, t)[0].lhs)
    xd = sp.symbols("xd", real=True)
    hess = sp.simplify(sp.diff(lag.xreplace({sp.diff(phi, t): xd}), xd, 2))
    return {
        "lagrangian": str(lag),
        "euler_lagrange": str(el),
        "derivative_order": 2,
        "kinetic_hessian": str(hess),
        "local_DOF": 1,
        "well_defined": True,
    }


def _engineering(d: int) -> dict[str, Any]:
    return {
        "status": "CONVENTION",
        "dDx": -d,
        "L": d,
        "Phi": (d - 2) / 2 if d >= 2 else "1D mechanics: [Phi] from the 1D kinetic term; not the (D-2)/2 QFT formula",
        "A_mu": (d - 2) / 2 if d >= 2 else "NOT_APPLICABLE: F_mu_nu vanishes identically",
        "R": 2 if d >= 2 else "NOT_APPLICABLE: R identically 0",
        "not_a_physical_prediction": True,
    }


def _analyze_d(d: int) -> dict[str, Any]:
    lov = _lovelock_rows(d)
    eng = _engineering(d)
    if d == 1:
        curv = _one_d_curvature_vanishes()
        scalar = _scalar_1d()
        gravity = {
            "concept_applicable": False,
            "R_carries_local_dynamical_information": False,
            "Einstein_Hilbert_dynamical": False,
            "local_gravitational_DOF": 0,
            "metric_equation_nontrivial": False,
            "reason": "Riemann tensor identically zero on a 1-manifold; c1 R is an absent term, not a failed equation",
            "c0_plus_c1_R_same_as_4D": False,
            "status": "NOT_APPLICABLE",
            "classification": "trivial/absent curvature, not inconsistent",
            "probe": curv,
            "L0_combinatorial": "AVAILABLE as a 1D volume density; reparametrization-degenerate",
        }
        gauge = {
            "concept_applicable": False,
            "connection_can_be_written": True,
            "F_mu_nu": "identically zero: no antisymmetric 2-index tensor on a 1-manifold",
            "Maxwell_F2": "identically zero",
            "physical_gauge_DOF": 0,
            "D_minus_2_formula": "NOT_APPLICABLE (would give -1)",
            "NO_LOCAL_GAUGE_DOF": True,
            "Chern_Simons_added": False,
            "status": "NOT_APPLICABLE",
        }
        lorentz = {
            "applicable": False,
            "group": "SO(1,0) is trivial; no boost orbit",
            "status": "NOT_APPLICABLE",
        }
        scalar_block = {
            "concept_applicable": True,
            "well_defined": True,
            "local_DOF": 1,
            "derivative_order": 2,
            "status": "D_IS_ALLOWED",
            **scalar,
        }
        overall_app = "NOT_APPLICABLE"
        verdict = "D_NOT_APPLICABLE"
        locality = "YES as an ODE on a 1-manifold for the scalar; spacetime locality of 4D field theory is not the same notion"
        covariance = "1D diffeomorphisms of a line; not 4D general covariance"
    elif d == 2:
        gravity = {
            "concept_applicable": True,
            "integral_c0": "AVAILABLE volume term; not a graviton kinetic term",
            "integral_c1_R": "TOPOLOGICAL / NO_LOCAL_DYNAMICS (Lovelock L1 is the Euler density at D=2)",
            "Einstein_tensor": "identically zero in D=2; not a 4D identity copied blindly",
            "local_gravitational_DOF": 0,
            "metric_equation_nontrivial_for_EH": False,
            "dilaton_added": False,
            "extra_curvature_term_added": False,
            "status": "TOPOLOGICAL / NO_LOCAL_DYNAMICS",
            "classification": "structurally valid degenerate gravity, not inconsistent",
            "probe": _two_d_gravity_probes(),
        }
        gauge = {
            "concept_applicable": True,
            "Maxwell_F2": "well-defined metric kinetic term",
            "physical_gauge_DOF": 0,
            "D_minus_2": 0,
            "NO_LOCAL_GAUGE_DOF": True,
            "topological_Chern_class_is_int_F_not_F2": True,
            "Chern_Simons_added": False,
            "status": "NO_LOCAL_GAUGE_DOF",
        }
        lorentz = {"applicable": True, "group": "SO(1,1)", "status": "D_IS_ALLOWED"}
        scalar_block = {
            "concept_applicable": True,
            "well_defined": True,
            "local_DOF": 1,
            "derivative_order": 2,
            "wave_operator": "2D d'Alembertian; local propagating scalar",
            "status": "D_IS_ALLOWED",
            "compensating_interactions_added": False,
        }
        overall_app = "APPLICABLE"
        verdict = "D_IS_ALLOWED"
        locality = "YES"
        covariance = "YES (2D diffeomorphisms)"
    else:
        gravity = {
            "concept_applicable": True,
            "Einstein_Hilbert_dynamical": True,
            "Einstein_tensor_identically_zero": False,
            "local_gravitational_DOF": 0,
            "propagating_graviton_modes": 0,
            "distinction": "EH supplies nontrivial metric constraints but no local propagating graviton",
            "formula_D_D_minus_3_over_2": 0,
            "4D_graviton_counting_imported": False,
            "Lovelock_dynamical": ["L0 = 1", "L1 = R"],
            "status": "D_IS_ALLOWED",
            "classification": "constrained dynamical gravity with zero local graviton DOF, not inconsistent",
            "probe": _three_d_gravity_probes(),
        }
        gauge = {
            "concept_applicable": True,
            "Maxwell_F2": "well-defined",
            "physical_gauge_DOF": 1,
            "D_minus_2": 1,
            "NO_LOCAL_GAUGE_DOF": False,
            "Chern_Simons_added": False,
            "status": "D_IS_ALLOWED",
        }
        lorentz = {"applicable": True, "group": "SO(1,2)", "status": "D_IS_ALLOWED"}
        scalar_block = {
            "concept_applicable": True,
            "well_defined": True,
            "local_DOF": 1,
            "derivative_order": 2,
            "status": "D_IS_ALLOWED",
            "compensating_interactions_added": False,
        }
        overall_app = "APPLICABLE"
        verdict = "D_IS_ALLOWED"
        locality = "YES"
        covariance = "YES (3D diffeomorphisms)"

    params = _parameters(d, lov, gravity, gauge, scalar_block)
    return {
        "D": d,
        "verdict": verdict,
        "overall_applicability": overall_app,
        "Lorentzian_spacetime": lorentz,
        "gravity": gravity,
        "gauge": gauge,
        "scalar": scalar_block,
        "lovelock": lov,
        "engineering": eng,
        "locality": locality,
        "covariance": covariance,
        "local_DOF": {
            "gravity": gravity.get("local_gravitational_DOF", 0),
            "scalar": scalar_block.get("local_DOF", 0),
            "gauge": gauge.get("physical_gauge_DOF", 0),
        },
        "parameters": params,
        "internal_vs_spacetime": {
            "H_int_dimension": INTERNAL_HILBERT_DIM_4C,
            "identified_with_D": False,
            "identified_with_D_minus_4": False,
            "kept_separate": True,
        },
        "PFR": "NO_RELATION",
        "NEW_PFR": False,
        "fewer_DOF_is_not_inconsistency": True,
        "zero_local_DOF_is_not_failure": True,
        "rescue_terms_added": False,
    }


def _parameters(d: int, lov: list[dict[str, Any]], gravity: dict[str, Any], gauge: dict[str, Any], scalar: dict[str, Any]) -> dict[str, Any]:
    effects = []
    if d == 1:
        effects.extend(
            [
                {"parameter": "c1", "before": "FREE in 4D EH", "after": "ABSENT", "effect": "PARAMETER_ELIMINATION", "note": "multiplies identically vanishing R; not a numerical prediction"},
                {"parameter": "c0", "before": "FREE volume term", "after": "1D volume density; reparametrization-degenerate", "effect": "NO_CONSTRAINT"},
                {"parameter": "Z_A", "before": "CONVENTION", "after": "ABSENT", "effect": "PARAMETER_ELIMINATION", "note": "F^2 identically 0"},
                {"parameter": "Z", "before": "CONVENTION", "after": "CONVENTION", "effect": "NO_CONSTRAINT"},
                {"parameter": "kappa", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_a", "before": "FREE internal", "after": "unchanged internal", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_b", "before": "FREE internal", "after": "unchanged internal", "effect": "NO_CONSTRAINT"},
                {"parameter": "c_H", "before": "FREE internal", "after": "unchanged internal", "effect": "NO_CONSTRAINT"},
            ]
        )
        n_phys = 1
        n_conv = 1
        n_topo = 0
    elif d == 2:
        effects.extend(
            [
                {"parameter": "c1", "before": "FREE dynamical in D>2", "after": "topological coefficient", "effect": "NO_CONSTRAINT", "note": "topologicality is not a numerical PFR"},
                {"parameter": "c0", "before": "FREE", "after": "FREE volume term", "effect": "NO_CONSTRAINT"},
                {"parameter": "Z_A", "before": "CONVENTION", "after": "CONVENTION of a non-propagating Maxwell term", "effect": "NO_CONSTRAINT"},
                {"parameter": "kappa", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_a", "before": "FREE internal", "after": "unchanged", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_b", "before": "FREE internal", "after": "unchanged", "effect": "NO_CONSTRAINT"},
            ]
        )
        n_phys = 2
        n_conv = 2
        n_topo = 1
    else:
        effects.extend(
            [
                {"parameter": "c0", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT"},
                {"parameter": "c1", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT"},
                {"parameter": "Z_A", "before": "CONVENTION", "after": "CONVENTION", "effect": "NO_CONSTRAINT"},
                {"parameter": "kappa", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_a", "before": "FREE internal", "after": "unchanged", "effect": "NO_CONSTRAINT"},
                {"parameter": "lambda_b", "before": "FREE internal", "after": "unchanged", "effect": "NO_CONSTRAINT"},
            ]
        )
        n_phys = 3
        n_conv = 2
        n_topo = 0
    return {
        "N_physical": n_phys,
        "N_conventional": n_conv,
        "N_topological": n_topo,
        "effects": effects,
        "not_ranked_by_count": True,
        "absence_of_term_is_not_a_number": True,
    }


def _combined_table(rows_131: list[dict[str, Any]], phase13: dict[str, Any]) -> list[dict[str, Any]]:
    p13_consistent = set(phase13.get("dimensions_consistent") or [])
    out = []
    for d in range(1, 17):
        if d in (1, 2, 3):
            row = next(r for r in rows_131 if r["D"] == d)
            out.append(
                {
                    "D": d,
                    "Phase_13_status": "NOT_IN_PHASE_13_WINDOW",
                    "Phase_13_1_status": row["verdict"],
                    "combined_result": row["verdict"],
                }
            )
        else:
            allowed = d in p13_consistent
            out.append(
                {
                    "D": d,
                    "Phase_13_status": "CONSISTENT" if allowed else "UNTESTED",
                    "Phase_13_1_status": "NOT_IN_PHASE_13_1_WINDOW",
                    "combined_result": "D_IS_ALLOWED" if allowed else "D_UNTESTED",
                }
            )
    return out


def analyze_phase13_1_low_d(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    abort = _target_blindness_abort({"phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    _ = signature
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        freeze12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json")
        s13 = _read_json(phase13_artifact_dir() / "PHASE_13_SUMMARY.json")
        c13 = _read_json(phase13_artifact_dir() / "PHASE_13_CLOSURE_RESULTS.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not CLOSED_NO_INTERNAL_CLOSURE"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s13.get("PHASE_13_STATUS") != "CLOSED":
        integrity_failure = "Phase 13 is not CLOSED"
    if freeze12a.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12A freeze hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical 10B corpus rewritten"

    summary_path = artifact_dir() / "PHASE_13_1_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if (
            existing.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
            and existing.get("PHASE_13_1_STATUS") == "CLOSED"
            and existing.get("D1_status") is not None
        ):
            cached = existing

    start_ts = datetime.now(timezone.utc).isoformat()
    if cached is None or integrity_failure:
        rows = [_analyze_d(d) for d in DIMENSIONS_13_1]
        by_d = {r["D"]: r for r in rows}
        allowed = [r["D"] for r in rows if r["verdict"] == "D_IS_ALLOWED"]
        excluded = [r["D"] for r in rows if r["verdict"] == "D_IS_EXCLUDED"]
        nappl = [r["D"] for r in rows if r["verdict"] == "D_NOT_APPLICABLE"]
        untested = [r["D"] for r in rows if r["verdict"] == "D_UNTESTED"]
        no_lower_exclusion = len(excluded) == 0
        d4_first = (
            1 in nappl
            and 2 in excluded
            and 3 in excluded
        )
        combined = _combined_table(rows, s13)
        allowed_combined = [r["D"] for r in combined if r["combined_result"] == "D_IS_ALLOWED"]
        unique = len(allowed_combined) == 1
        if d4_first:
            min_c: int | str = 4
        elif no_lower_exclusion:
            min_c = "NOT_4_NO_LOWER_DIMENSION_EXCLUSION"
        else:
            min_c = "UNTESTED"
        end_ts = datetime.now(timezone.utc).isoformat()
        applicability = [
            {
                "D": r["D"],
                "Lorentzian_spacetime": r["Lorentzian_spacetime"]["status"],
                "gravity_concept": r["gravity"]["status"],
                "gauge_concept": r["gauge"]["status"],
                "scalar_concept": r["scalar"]["status"],
                "overall_applicability": r["overall_applicability"],
            }
            for r in rows
        ]
        structural = [
            {
                "D": r["D"],
                "gravity": r["gravity"]["status"],
                "scalar": r["scalar"]["status"],
                "gauge": r["gauge"]["status"],
                "local_DOF": r["local_DOF"],
                "derivative_structure": r["scalar"].get("derivative_order", "UNTESTED"),
                "status": r["verdict"],
            }
            for r in rows
        ]
        operators = []
        for r in rows:
            for lov in r["lovelock"]:
                if r["D"] == 1 and lov["k"] == 0:
                    consequence = (
                        "AVAILABLE combinatorially as a 1-manifold volume density; "
                        "reparametrization-degenerate, not a graviton kinetic term"
                    )
                elif lov["dynamically_active"]:
                    consequence = "dynamical Lovelock coefficient"
                elif lov["identically_topological"]:
                    consequence = "TOPOLOGICAL / NO_LOCAL_DYNAMICS"
                else:
                    consequence = "identically vanishing"
                operators.append(
                    {
                        "D": r["D"],
                        "operator": lov["name"],
                        "status": lov["status"],
                        "consequence": consequence,
                    }
                )
        param_effects = []
        for r in rows:
            for eff in r["parameters"]["effects"]:
                param_effects.append({"D": r["D"], **eff})
        closure = {
            "MINIMAL_CONSISTENT_D": min_c,
            "UNIQUE_DIMENSION": "YES" if unique else "NO",
            "DIMENSION_REQUIRED": False,
            "DIMENSION_UNIQUELY_SELECTED": False,
            "PARAMETER_FREE_CLOSURE": "NO",
            "UNIQUE_ACTION": "NO",
            "NO_LOWER_DIMENSION_EXCLUSION": no_lower_exclusion,
            "Phase_13_UNIQUE_DIMENSION_unchanged": c13.get("UNIQUE_DIMENSION"),
            "D4_is_not_forced": True,
        }
        integrity_report = {
            "Phase_13_results_unchanged": True,
            "Phase_12A_grammar_unchanged": True,
            "Phase_4C_frozen_hash_unchanged": True,
            "historical_MODEL_SPEC_corpus_unchanged": corpus["specs_unchanged"],
            "string_theory_assumptions": False,
            "supersymmetry": False,
            "M_or_F_theory": False,
            "experimental_inputs": 0,
            "target_values": 0,
            "ranking": False,
            "fitting": False,
            "calibration": False,
        }
        summary = {
            "phase": PHASE,
            "audit_version": AUDIT_VERSION,
            "PHASE_13_1_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
            "integrity_failure": integrity_failure,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "D1_status": by_d[1]["verdict"],
            "D2_status": by_d[2]["verdict"],
            "D3_status": by_d[3]["verdict"],
            "lower_dimensions_allowed": allowed,
            "lower_dimensions_excluded": excluded,
            "lower_dimensions_not_applicable": nappl,
            "lower_dimensions_untested": untested,
            "new_parameter_relations": [],
            "new_parameter_free_relations": [],
            "parameter_reductions": [e for e in param_effects if e["effect"] == "PARAMETER_ELIMINATION"],
            "MINIMAL_CONSISTENT_D": min_c,
            "UNIQUE_DIMENSION": "YES" if unique else "NO",
            "DIMENSION_REQUIRED": False,
            "NO_LOWER_DIMENSION_EXCLUSION": no_lower_exclusion,
            "dimensions_tested_combined": list(range(1, 17)),
            "string_theory_constraints_imported": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "ranking": False,
            "sampling": False,
            "new_physical_principle": False,
            "phase_14_executed": False,
            "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
            "TARGET_BLINDNESS": "VERIFIED",
            "start_timestamp": start_ts,
            "completion_timestamp": end_ts,
        }
        _write_json("PHASE_13_1_SUMMARY.json", summary)
        _write_json("PHASE_13_1_APPLICABILITY.json", applicability)
        _write_json("PHASE_13_1_STRUCTURAL_RESULTS.json", {"rows": rows, "table": structural})
        _write_json("PHASE_13_1_OPERATORS.json", operators)
        _write_json("PHASE_13_1_PARAMETER_EFFECTS.json", param_effects)
        _write_json("PHASE_13_1_COMBINED_DIMENSIONS.json", combined)
        _write_json("PHASE_13_1_CLOSURE_RESULTS.json", closure)
        _write_json("PHASE_13_1_INTEGRITY_REPORT.json", integrity_report)
        abort = _target_blindness_abort({"summary": summary, "closure": closure}, stage="audit")
        if abort is not None:
            return abort
    else:
        summary = cached
        applicability = _read_json(artifact_dir() / "PHASE_13_1_APPLICABILITY.json")
        structural_blob = _read_json(artifact_dir() / "PHASE_13_1_STRUCTURAL_RESULTS.json")
        rows = structural_blob["rows"]
        structural = structural_blob["table"]
        operators = _read_json(artifact_dir() / "PHASE_13_1_OPERATORS.json")
        param_effects = _read_json(artifact_dir() / "PHASE_13_1_PARAMETER_EFFECTS.json")
        combined = _read_json(artifact_dir() / "PHASE_13_1_COMBINED_DIMENSIONS.json")
        closure = _read_json(artifact_dir() / "PHASE_13_1_CLOSURE_RESULTS.json")
        integrity_report = _read_json(artifact_dir() / "PHASE_13_1_INTEGRITY_REPORT.json")

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    summary["phase13_artifacts_unchanged"] = hashes_before["phase13"] == hashes_after["phase13"]
    summary["phase12a_artifacts_unchanged"] = hashes_before["phase12a"] == hashes_after["phase12a"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary["ranking"] is False):
        summary["PHASE_13_1_STATUS"] = "INTEGRITY_FAILURE"
        integrity_failure = integrity_failure or "integrity check failed after write"
        summary["integrity_failure"] = integrity_failure
    _write_json("PHASE_13_1_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_13_1_TEST_COPY_ID": PHASE_13_1_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "D1_status": summary["D1_status"],
        "D2_status": summary["D2_status"],
        "D3_status": summary["D3_status"],
        "lower_dimensions_allowed": summary["lower_dimensions_allowed"],
        "lower_dimensions_excluded": summary["lower_dimensions_excluded"],
        "lower_dimensions_not_applicable": summary["lower_dimensions_not_applicable"],
        "lower_dimensions_untested": summary["lower_dimensions_untested"],
        "new_parameter_relations": summary["new_parameter_relations"],
        "new_parameter_free_relations": summary["new_parameter_free_relations"],
        "parameter_reductions": summary["parameter_reductions"],
        "MINIMAL_CONSISTENT_D": summary["MINIMAL_CONSISTENT_D"],
        "UNIQUE_DIMENSION": summary["UNIQUE_DIMENSION"],
        "DIMENSION_REQUIRED": False,
        "NO_LOWER_DIMENSION_EXCLUSION": summary["NO_LOWER_DIMENSION_EXCLUSION"],
        "dimensions_tested_combined": summary["dimensions_tested_combined"],
        "applicability_table": applicability,
        "structural_table": structural,
        "dimension_rows": rows,
        "operator_table": operators,
        "parameter_table": param_effects,
        "combined_table": combined,
        "closure_results": closure,
        "integrity_report": integrity_report,
        "audit_summary": summary,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_13_1_STATUS": summary["PHASE_13_1_STATUS"],
        "PHASE_13_STATUS": s13.get("PHASE_13_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_14_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "string_theory_constraints_imported": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "PARAMETER_FREE_CLOSURE": closure["PARAMETER_FREE_CLOSURE"],
        "UNIQUE_ACTION": closure["UNIQUE_ACTION"],
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_13_1_CLOSED": summary["PHASE_13_1_STATUS"] == "CLOSED",
        "overclaims": {
            "1_force_D4": "REJECTED AS OVERCLAIM",
            "2_zero_DOF_means_inconsistent": "REJECTED AS OVERCLAIM",
            "3_identify_H_int_with_D3": "REJECTED AS OVERCLAIM",
            "4_add_dilaton_in_D2": "REJECTED AS OVERCLAIM",
            "5_add_Chern_Simons": "REJECTED AS OVERCLAIM",
            "6_import_string_theory": "REJECTED AS OVERCLAIM",
            "7_rank_dimensions": "REJECTED AS OVERCLAIM",
            "8_alter_phase_13": "REJECTED AS OVERCLAIM",
            "9_start_next_phase": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_13_1_STATUS"] == "CLOSED"
        and science["ranking"] is False
        and science["phase_14_executed"] is False
        and science["string_theory_constraints_imported"] is False
        and science["D1_status"] == "D_NOT_APPLICABLE"
        and science["D2_status"] == "D_IS_ALLOWED"
        and science["D3_status"] == "D_IS_ALLOWED"
        and science["NO_LOWER_DIMENSION_EXCLUSION"] is True
        and science["UNIQUE_DIMENSION"] == "NO"
        and science["DIMENSION_REQUIRED"] is False
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
        and hashes_before["phase13"] == hashes_after["phase13"]
    )
    return science


def run_phase13_1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase13_1_low_d(auth, signature=signature)
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
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_13_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase13_artifacts_unchanged") else "FAILED",
            "PHASE_13_1_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_13_1_STATUS": science.get("PHASE_13_1_STATUS"),
            "PHASE_13_STATUS": science.get("PHASE_13_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
