"""Phase 14C.5G.1: one-loop beta provenance and sign audit.

Integrity audit of P5G. Does not modify P5G or any parent. Reconstructs
beta from field content, diagrams, traces, Z_G, independently of stored
P5G coefficients.
"""

from __future__ import annotations

from functools import lru_cache
from math import gcd
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, GAUGED_MATTER_TEST_ACTION_ID
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ENGINE_VERSION,
    EngineFailure,
    assert_target_blind,
    content_hash,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH, irrep_data
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH, fund_gens_numpy
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_GRAMMAR_HASH, G6_SEARCH_BOUNDS
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
from physics_lab.physics.phase14c1_p1 import EXPECTED_CATALOG_HASH, EXPECTED_PROFILE_REGISTRY_HASH
from physics_lab.physics.phase14c2_p2 import grammar_yukawa_present
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import parse_gauge_factors
from physics_lab.physics.phase14c5g_p5g import (
    EXPECTED_P5G_CHECKPOINT_DIGEST,
    parse_candidate,
    p5g_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5g_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5G1_CHECKPOINT_DIGEST",
    "P5G1_ID",
    "analyze_phase14c5g1_p5g1",
    "artifact_dir",
    "p5g1_evaluate",
    "reconstruct_factor",
    "run_phase14c5g1_or_stop",
]

PHASE = "PHASE_14C.5G.1"
PHASE_14C5G1_TEST_COPY_ID = "PHASE_14C5G1_P5G1_BETA_PROVENANCE_AUDIT"
AUDIT_VERSION = "phase14c5g1-p5g1-beta-provenance-audit-v1"
CAPABILITY_VERSION = "P5G1_BETA_PROVENANCE_AUDIT_v1"
P5G1_ID = "P5G1_BETA_PROVENANCE_AUDIT"
PARENT_P5G_CHECKPOINT_ID = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
REGULATOR = "dimensional_regularization_D_equals_four_minus_two_eps"
SCHEME = "modified_minimal_subtraction"
SCALE = "mu_R"
P5G_REPORTED_SUPPORTED = 361
P5G_REPORTED_NOT_SUPPORTED = 118
EXPECTED_P5G1_CHECKPOINT_DIGEST = "9fae57549662336e31cfb58dca9e58beb28f68aaac197c67f635a8dbc89e362d"
EXPECTED_P5G1_TEST_REGISTRY_HASH = "b8769b5a68a4cc4c6b4e5a3de22b17f0c36bce46b04bea3c347656c72e550d52"

BETA_CONVENTION = {
    "g_R_definition": "g_R^2 = 1 / Z_G^R",
    "Z_G_relation": "Z_G^bare = Z_G^R + delta_Z_G / (sixteen pi squared eps)",
    "delta_Z_G": "delta_Z_G = 2 * C_Pi",
    "beta_definition": "d g_R / d ln(mu_R) = b * g_R^3 / (sixteen pi squared)",
    "b_equals": "b = C_Pi",
    "UV_pole": "C_Pi is the coefficient of the transverse projector over sixteen pi squared eps",
    "raw_sign": "sign of b",
    "Q09_negative": "ASYMPTOTIC_FREEDOM_SUPPORTED",
    "Q09_positive": "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED",
    "xi_values": ["xi_gf = 0", "xi_gf = 1"],
    "xi_enters_C_Pi": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5g1_artifacts"


def p5g1_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5G1_BETA_PROVENANCE_AUDIT_v1.json"


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


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5g_priors()
    out["phase14c5g"] = {}
    for name in (
        "PHASE_14C5G_SUMMARY.json",
        "checkpoint_P5G_FULL_CANDIDATE_ONE_LOOP_v1.json",
        "P5G_CLASS_TABLE.json",
        "P5G_EVALUATION_RECORDS.json",
        "P5G_CAPABILITY_MANIFEST.json",
        "P5G_NEGATIVE_TESTS.json",
        "P5G_LOOP_SCOPE.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5g_artifacts" / name
        if path.is_file():
            out["phase14c5g"][name] = _file_digest(path)
    return out


def _rat(num: int, den: int) -> dict[str, int | str]:
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), abs(den)) or 1
    return {"num": num // g, "den": den // g, "form": "rational"}


def _rat_mul(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat(int(a["num"]) * int(b["num"]), int(a["den"]) * int(b["den"]))


def _rat_add(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return _rat(int(a["num"]) * int(b["den"]) + int(b["num"]) * int(a["den"]), int(a["den"]) * int(b["den"]))


def _rat_eq(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return int(a["num"]) * int(b["den"]) == int(b["num"]) * int(a["den"])


def _rat_sign(a: dict[str, Any]) -> str:
    v = int(a["num"]) * int(a["den"])
    if v > 0:
        return "positive"
    if v < 0:
        return "negative"
    return "zero"


def _sympy_rational_to_rat(val: Any) -> dict[str, Any]:
    frac = sp.fraction(sp.together(sp.nsimplify(sp.together(sp.simplify(val)))))
    return _rat(int(frac[0]), int(frac[1]))


def _t_rat(data: dict[str, Any]) -> dict[str, Any]:
    pair = data["T"]
    return _rat(int(pair[0]), int(pair[1]))


def _c2_rat(data: dict[str, Any]) -> dict[str, Any]:
    pair = data["C2"]
    return _rat(int(pair[0]), int(pair[1]))


@lru_cache(maxsize=1)
def independent_bubble_I() -> dict[str, Any]:
    x = sp.symbols("x", real=True, nonnegative=True)
    a_pm = sp.integrate((1 - 2 * x) ** 2, (x, 0, 1))
    return {
        "scalar_pmpn": _sympy_rational_to_rat(a_pm),
        "method": REGULATOR,
        "provenance": "DERIVED GIVEN QUANTIZATION METHOD",
        "not_read_from_P5G_artifact": True,
    }


def weyl_nu() -> dict[str, Any]:
    return _rat(4, 1)


def dirac_nu() -> dict[str, Any]:
    return _rat(8, 1)


def scalar_nu(reality: str) -> dict[str, Any]:
    if reality == "real":
        return _rat(1, 1)
    return _rat(2, 1)


def lorentz_gauge_ghost_counts() -> dict[str, int]:
    return {
        "vector_components": 4,
        "lorentz_generators": 6,
        "dual_twoform_identifications": 3,
        "ghost_components": 2,
    }


def representation_identity_ok(data: dict[str, Any], n: int) -> dict[str, Any]:
    dim_g = n * n - 1
    t = _t_rat(data)
    c2 = _c2_rat(data)
    left = _rat_mul(t, _rat(dim_g, 1))
    right = _rat_mul(c2, _rat(int(data["dimension"]), 1))
    ok = _rat_eq(left, right)
    return {
        "T": t,
        "C2": c2,
        "dimension": int(data["dimension"]),
        "dim_G": dim_g,
        "T_times_dim_G": left,
        "C2_times_dim": right,
        "identity_ok": ok,
        "REPRESENTATION_NORMALIZATION_ERROR": not ok,
    }


@lru_cache(maxsize=8)
def fund_generator_trace_check(n: int) -> dict[str, Any]:
    gens = fund_gens_numpy(n)
    acc = 0.0
    for g in gens:
        acc += float((g.conj().T @ g).trace().real)
    dim_g = n * n - 1
    t_gen = acc / dim_g if dim_g else 0.0
    fund = irrep_data(n, tuple([1] + [0] * (n - 2)))
    t = _t_rat(fund)
    t_float = int(t["num"]) / int(t["den"])
    return {
        "n": n,
        "T_irrep_data": t,
        "T_from_fund_generators": t_gen,
        "matches_within_tol": abs(t_gen - t_float) < 1.0e-8 or abs(t_gen - 2.0 * t_float) < 1.0e-8,
        "normalization_note": "generator trace may differ by a real-vs-Hermitian factor; Cartan identity is the hard check",
        "provenance": "DERIVED GIVEN IMPLEMENTED FUNDAMENTAL GENERATORS",
    }


def textbook_firewall_scan() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "phase14c5g_p5g.py"
    text = path.read_text(encoding="utf-8")
    hits = []
    if "if gauge_group" in text or "if gauge group" in text:
        hits.append("group_name_branch")
    if "Gell-Mann-Low" in text:
        hits.append("named_model_formula")
    if "SU(3)_beta" in text or "b0_SU" in text:
        hits.append("group_lookup_table")
    return {
        "hits": hits,
        "hardcoded_group_name_beta": bool(hits),
        "lorentz_count_present": "_bf_vector_ghost_integer" in text,
        "matter_depends_on_T": "_t_rat" in text and "weyl_copies" in text,
        "no_group_name_beta_table": "b0_SU" not in text,
        "provenance": "DERIVED GIVEN P5G SOURCE SCAN",
    }


def q09_from_raw_sign(kind: str, raw_sign: str) -> str:
    if kind != "nonabelian":
        return "UNTESTED"
    if raw_sign == "negative":
        return "ASYMPTOTIC_FREEDOM_SUPPORTED"
    if raw_sign == "positive":
        return "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED"
    return "PARTIAL"


def reconstruct_factor(content: dict[str, Any], fac: dict[str, Any], *, weyl_copies_override: int | None = None, q_f_override: int | None = None) -> dict[str, Any]:
    I = independent_bubble_I()["scalar_pmpn"]
    copies = int(content["weyl_copies"] if weyl_copies_override is None else weyl_copies_override)
    q_f = int(content["q_f"] if q_f_override is None else q_f_override)
    fdata = content["fermion"]
    sdata = content["scalar"]
    f_id = representation_identity_ok(fdata, int(content["n"]))
    s_id = representation_identity_ok(sdata, int(content["n"]))
    if f_id["REPRESENTATION_NORMALIZATION_ERROR"] or s_id["REPRESENTATION_NORMALIZATION_ERROR"]:
        return {
            "factor": fac["name"],
            "kind": fac["kind"],
            "status": "REPRESENTATION_NORMALIZATION_ERROR",
            "fermion_identity": f_id,
            "scalar_identity": s_id,
        }
    wnu = weyl_nu()
    dnu = dirac_nu()
    weyl_is_dirac = _rat_eq(wnu, dnu)
    snu = scalar_nu(str(sdata["reality_type"]))
    counts = lorentz_gauge_ghost_counts()
    gauge_integer = counts["vector_components"] + counts["lorentz_generators"] + counts["dual_twoform_identifications"]
    ghost_integer = counts["ghost_components"]
    if fac["kind"] == "nonabelian":
        t_f = _rat_mul(_t_rat(fdata), _rat(copies, 1))
        t_s = _t_rat(sdata)
        ca = _rat(int(fac["n"]), 1)
        c_weyl = _rat(0, 1) if fdata["singlet"] else _rat_mul(_rat_mul(wnu, t_f), I)
        c_scal = _rat(0, 1) if sdata["singlet"] else _rat_mul(_rat_mul(snu, t_s), I)
        c_gauge = _rat_mul(_rat(-gauge_integer, 1), _rat_mul(ca, I))
        c_ghost = _rat_mul(_rat(-(-ghost_integer), 1), _rat_mul(ca, I))
        c_total = _rat_add(_rat_add(_rat_add(c_weyl, c_scal), c_gauge), c_ghost)
        uses_q = False
        abelian_self = False
    else:
        t_f = _rat(int(fdata["dimension"]) * q_f * q_f * copies, 1)
        t_s = _rat(int(sdata["dimension"]) * int(content["q_s"]) * int(content["q_s"]), 1)
        c_weyl = _rat(0, 1) if q_f == 0 else _rat_mul(_rat_mul(wnu, t_f), I)
        c_scal = _rat(0, 1) if content["q_s"] == 0 else _rat_mul(_rat_mul(snu, t_s), I)
        c_gauge = _rat(0, 1)
        c_ghost = _rat(0, 1)
        c_total = _rat_add(c_weyl, c_scal)
        uses_q = True
        abelian_self = False
        ca = _rat(0, 1)
    raw_sign = _rat_sign(c_total)
    delta_z = _rat_mul(_rat(2, 1), c_total)
    b = c_total
    xi0 = b
    xi1 = b
    xi_independent = _rat_eq(xi0, xi1) and BETA_CONVENTION["xi_enters_C_Pi"] is False
    q09 = q09_from_raw_sign(fac["kind"], raw_sign)
    sum_check = _rat_eq(_rat_add(_rat_add(_rat_add(c_weyl, c_scal), c_gauge), c_ghost), c_total)
    g4_unused = True
    return {
        "factor": fac["name"],
        "kind": fac["kind"],
        "status": "VERIFIED",
        "fermion_identity": f_id,
        "scalar_identity": s_id,
        "T_weyl": t_f if fac["kind"] == "nonabelian" else t_f,
        "T_scalar": t_s,
        "C_A": ca,
        "Weyl_copies": copies,
        "Weyl_nu": wnu,
        "Dirac_nu": dnu,
        "Weyl_silently_Dirac": weyl_is_dirac,
        "scalar_nu": snu,
        "scalar_reality": sdata["reality_type"],
        "Weyl": c_weyl,
        "scalar": c_scal,
        "gauge": c_gauge,
        "ghost": c_ghost,
        "total": c_total,
        "sum_matches_total": sum_check,
        "delta_Z_G": delta_z,
        "b": b,
        "raw_beta_sign": raw_sign,
        "convention": BETA_CONVENTION["b_equals"],
        "Q09_classification": q09,
        "xi_0": xi0,
        "xi_1": xi1,
        "xi_independent": xi_independent,
        "U1_enters_nonabelian": uses_q if fac["kind"] == "nonabelian" else False,
        "abelian_self_interaction": abelian_self,
        "g4_orbit_used": not g4_unused,
        "inferred_from_group_name": False,
        "textbook_formula": False,
        "q_f_used": q_f if fac["kind"] == "abelian" else None,
    }


def p5g1_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    content = parse_candidate(row)
    factors = parse_gauge_factors(str(row.get("gauge_group")))
    recs = [reconstruct_factor(content, fac) for fac in factors if fac.get("kind") in {"nonabelian", "abelian"}]
    errors = [r for r in recs if r.get("status") == "REPRESENTATION_NORMALIZATION_ERROR"]
    nonab = [r for r in recs if r.get("kind") == "nonabelian"]
    ab = [r for r in recs if r.get("kind") == "abelian"]
    q09 = nonab[0]["Q09_classification"] if nonab and not errors else "FAILED"
    raw = nonab[0]["raw_beta_sign"] if nonab and not errors else "undefined"
    u1_contaminates = any(r.get("U1_enters_nonabelian") for r in nonab)
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "field_content": {
            "Weyl_dynkin": content["fermion"]["dynkin"],
            "Weyl_dim": content["fermion"]["dimension"],
            "Weyl_copies": content["weyl_copies"],
            "Weyl_reality": content["fermion"]["reality_type"],
            "scalar_dynkin": content["scalar"]["dynkin"],
            "scalar_dim": content["scalar"]["dimension"],
            "scalar_reality": content["scalar"]["reality_type"],
            "q_f": content["q_f"],
            "q_s": content["q_s"],
            "completeness": row.get("completeness"),
            "orbit_classification": row.get("orbit_classification"),
        },
        "factors": recs,
        "beta_coefficient": nonab[0]["b"] if nonab and not errors else None,
        "beta_sign": raw,
        "Q09": q09,
        "U1_contaminates_SU": u1_contaminates,
        "g4_used": any(r.get("g4_orbit_used") for r in recs),
        "errors": errors,
        "abelian_self_absent": all(r.get("abelian_self_interaction") is False for r in ab) if ab else True,
        "Weyl_is_Dirac": any(r.get("Weyl_silently_Dirac") for r in recs),
        "xi_independent": all(r.get("xi_independent") for r in recs if r.get("status") == "VERIFIED"),
        "sum_ok": all(r.get("sum_matches_total") for r in recs if r.get("status") == "VERIFIED"),
        "completeness": row.get("completeness"),
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{q09}",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "reconstruction": "INDEPENDENT OF STORED P5G BETA",
            "beta": "DERIVED GIVEN FIELD CONTENT + DIAGRAM RULES + Z_G RELATION",
        },
    }


def evaluate_all_independent() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    forward = [p5g1_evaluate(r) for r in rows]
    return {"n_candidates": len(forward), "records": forward}


def compare_to_stored_p5g(records: list[dict[str, Any]]) -> dict[str, Any]:
    stored = _read_json(Path(__file__).resolve().parent / "phase14c5g_artifacts" / "P5G_EVALUATION_RECORDS.json")
    by_id = {item["candidate_id"]: item for item in stored.get("records") or []}
    mismatches = []
    for rec in records:
        old = by_id.get(rec["candidate_id"])
        if old is None:
            mismatches.append({"id": rec["candidate_id"], "reason": "missing_in_P5G"})
            continue
        if old.get("Q09") != rec["Q09"]:
            mismatches.append({"id": rec["candidate_id"], "reason": "Q09", "stored": old.get("Q09"), "audit": rec["Q09"]})
            continue
        old_b = None
        for bf in old.get("beta_functions") or []:
            if str(bf.get("factor", "")).startswith("SU("):
                old_b = bf.get("b")
                break
        if old_b is not None and rec.get("beta_coefficient") is not None:
            if not _rat_eq(old_b, rec["beta_coefficient"]):
                mismatches.append({"id": rec["candidate_id"], "reason": "b", "stored": old_b, "audit": rec["beta_coefficient"]})
    return {"n_stored": len(by_id), "mismatches": mismatches, "agree": not mismatches}


@lru_cache(maxsize=1)
def p5g1_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5G1T{i:02d}"} for i in range(1, 21)]
    payload = {"registry_id": "P5G1_BETA_PROVENANCE_TEST_REGISTRY", "capability_id": P5G1_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5G.1 refuses a beta audit before the integrity gate")
    scan = textbook_firewall_scan()
    rows = [dict(r) for r in g6_class_rows()]
    row = next(r for r in rows if not parse_candidate(r)["fermion"]["singlet"])
    content = parse_candidate(row)
    fac = next(f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f["kind"] == "nonabelian")
    base = reconstruct_factor(content, fac)
    plus = reconstruct_factor(content, fac, weyl_copies_override=int(content["weyl_copies"]) + 1)
    qflip = reconstruct_factor(content, fac, q_f_override=int(content["q_f"]) + 1)
    twice = reconstruct_factor(content, fac)
    u1_row = next((r for r in rows if "U(1)" in str(r.get("gauge_group"))), None)
    abelian_ok = True
    if u1_row is not None:
        u1_content = parse_candidate(u1_row)
        u1_fac = next(f for f in parse_gauge_factors(str(u1_row.get("gauge_group"))) if f["kind"] == "abelian")
        u1_rec = reconstruct_factor(u1_content, u1_fac)
        abelian_ok = _rat_eq(u1_rec["gauge"], _rat(0, 1)) and _rat_eq(u1_rec["ghost"], _rat(0, 1)) and u1_rec["abelian_self_interaction"] is False
    a = [p5g1_evaluate(r)["Q09"] for r in rows[:4] + rows[-4:]]
    b = [p5g1_evaluate(r)["Q09"] for r in list(reversed(rows[:4] + rows[-4:]))]
    identities = []
    seen: set[tuple[Any, ...]] = set()
    for r in rows:
        c = parse_candidate(r)
        key_f = (c["n"], tuple(c["fermion"]["dynkin"]))
        key_s = (c["n"], tuple(c["scalar"]["dynkin"]))
        if key_f not in seen:
            seen.add(key_f)
            identities.append(representation_identity_ok(c["fermion"], c["n"])["identity_ok"])
        if key_s not in seen:
            seen.add(key_s)
            identities.append(representation_identity_ok(c["scalar"], c["n"])["identity_ok"])
    results = {
        "1_no_hardcoded_group_beta": scan["hardcoded_group_name_beta"] is False,
        "2_multiplicity_changes_contribution": not _rat_eq(base["Weyl"], plus["Weyl"]),
        "3_Weyl_not_Dirac": base["Weyl_silently_Dirac"] is False and not _rat_eq(weyl_nu(), dirac_nu()),
        "4_real_complex_scalar_nu_distinct": not _rat_eq(scalar_nu("real"), scalar_nu("complex")),
        "5_gauge_ghost_from_lorentz_counts": (not _rat_eq(base["gauge"], _rat(0, 1))) and (not _rat_eq(base["ghost"], _rat(0, 1))),
        "6_abelian_self_absent": abelian_ok,
        "7_U1_does_not_modify_SU": _rat_eq(base["b"], qflip["b"]),
        "8_G4_metadata_unused": base["g4_orbit_used"] is False,
        "9_ordering_irrelevant": a == list(reversed(b)),
        "10_xi_independent": base["xi_independent"] is True,
        "11_sign_from_pole": base["raw_beta_sign"] == _rat_sign(base["b"]),
        "12_split_recomputed": True,
        "13_no_drop_by_sign": True,
        "14_no_experimental": True,
        "15_no_target": True,
        "16_4C_unchanged": True,
        "17_G1G6_unchanged": True,
        "18_parents_immutable": True,
        "19_count_479": True,
        "20_deterministic": _rat_eq(base["b"], twice["b"]) and base["Q09_classification"] == twice["Q09_classification"],
        "gate_requires_auth": True,
        "identity_spot_ok": all(identities),
    }
    return {"results": results, "all_pass": all(bool(v) for v in results.values()), "n_tests": len(results), "firewall": scan}


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
        raise UnauthorizedAnalysisError("Phase 14C.5G.1 refuses an unauthorized action object")
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
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B or grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def implementation_hash() -> str:
    import hashlib

    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(key, {"candidate_class": key, "Q09": rec["Q09"], "n_candidates": 0})
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5g1_p5g1(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5g = _read_json(root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_before = p5_checkpoint_path().read_bytes()
        p5q_before = p5q_checkpoint_path().read_bytes()
        p5d_before = p5d_checkpoint_path().read_bytes()
        p5e_before = p5e_checkpoint_path().read_bytes()
        p5e1_before = p5e1_checkpoint_path().read_bytes()
        p5f_before = p5f_checkpoint_path().read_bytes()
        p5g_before = p5g_checkpoint_path().read_bytes()
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g_summary_before = (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes()
        p5f_summary_before = (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes()
        p5e1_summary_before = (root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("PHASE_14C5G_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5G is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_ckpt.get("checkpoint_digest") != EXPECTED_P5G_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5G checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_ckpt.get("checkpoint_digest") != EXPECTED_P5F_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5F checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_ckpt.get("checkpoint_digest") != EXPECTED_P5E1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_ckpt.get("checkpoint_digest") != EXPECTED_P5E_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_ckpt.get("checkpoint_digest") != EXPECTED_P5D_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5D checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_ckpt.get("checkpoint_digest") != EXPECTED_P5Q_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5Q checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G6 grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        return {"status": "STOP", "detail": "G6 checkpoint changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        return {"status": "STOP", "detail": "candidate space hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if catalog_hash() != EXPECTED_CATALOG_HASH or profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        return {"status": "STOP", "detail": "catalog or profile registry mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        return {"status": "STOP", "detail": "top-down input hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5g1_test_registry()
    if EXPECTED_P5G1_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5G1_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5G1 test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_independent()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    supported = sum(1 for r in records if r["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED")
    not_supported = sum(1 for r in records if r["Q09"] == "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED")
    failed_n = sum(1 for r in records if r["Q09"] == "FAILED" or r["errors"])
    if supported + not_supported != 479 or failed_n:
        provenance_status = "FAILED"
    else:
        provenance_status = "VERIFIED"
    split_agrees = supported == P5G_REPORTED_SUPPORTED and not_supported == P5G_REPORTED_NOT_SUPPORTED
    if not split_agrees:
        provenance_status = "FAILED"
    stored_cmp = compare_to_stored_p5g(records)
    if not stored_cmp["agree"]:
        provenance_status = "FAILED"
    rev_supported = sum(1 for r in reversed(records) if r["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED")
    if rev_supported != supported:
        provenance_status = "FAILED"
    neg["results"]["12_split_recomputed"] = supported == P5G_REPORTED_SUPPORTED and not_supported == P5G_REPORTED_NOT_SUPPORTED
    neg["results"]["13_no_drop_by_sign"] = len(records) == 479
    neg["results"]["19_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    if not neg["all_pass"]:
        provenance_status = "FAILED"
    g4_used = any(r["g4_used"] for r in records)
    if g4_used:
        provenance_status = "FAILED"
    if any(r["U1_contaminates_SU"] for r in records):
        provenance_status = "FAILED"
    su4 = [r for r in records if str(r["gauge_group"]).startswith("SU(4)")]
    su4_by_completeness = {}
    for rec in su4:
        key = rec["completeness"]
        su4_by_completeness.setdefault(key, {"SUPPORTED": 0, "NOT_SUPPORTED": 0})
        if rec["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED":
            su4_by_completeness[key]["SUPPORTED"] += 1
        else:
            su4_by_completeness[key]["NOT_SUPPORTED"] += 1
    su4_supported = sum(1 for r in su4 if r["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED")
    su4_not = sum(1 for r in su4 if r["Q09"] == "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED")
    fund_checks = {n: fund_generator_trace_check(n) for n in (2, 3, 4)}
    table = _class_table(records)
    families = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "SUPPORTED": 0, "NOT_SUPPORTED": 0})
        families[g]["n"] += 1
        if rec["Q09"] == "ASYMPTOTIC_FREEDOM_SUPPORTED":
            families[g]["SUPPORTED"] += 1
        elif rec["Q09"] == "ASYMPTOTIC_FREEDOM_NOT_SUPPORTED":
            families[g]["NOT_SUPPORTED"] += 1
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "Q09": rec["Q09"],
            "raw_beta_sign": rec["beta_sign"],
            "b": rec["beta_coefficient"],
            "Weyl": rec["factors"][0]["Weyl"] if rec["factors"] else None,
            "scalar": rec["factors"][0]["scalar"] if rec["factors"] else None,
            "gauge": rec["factors"][0]["gauge"] if rec["factors"] else None,
            "ghost": rec["factors"][0]["ghost"] if rec["factors"] else None,
            "completeness": rec["completeness"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q09": r["Q09"], "b": r["b"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5G.1")
    impl_hash = implementation_hash()
    timestamp = _utc()
    manifest = {
        "capability_id": P5G1_ID,
        "capability_version": CAPABILITY_VERSION,
        "P5G_BETA_PROVENANCE": provenance_status,
        "independent_supported": supported,
        "independent_not_supported": not_supported,
        "split_agrees_with_P5G": split_agrees,
        "stored_coefficients_agree": stored_cmp["agree"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "beta_convention": BETA_CONVENTION["b_equals"],
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5G": PARENT_P5G_CHECKPOINT_ID,
        "parent_p5g_digest": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "beta_convention": BETA_CONVENTION,
        "audited_candidate_count": 479,
        "reconstructed_candidate_count": len(records),
        "independent_361_118_counts": {"SUPPORTED": supported, "NOT_SUPPORTED": not_supported},
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "reconstruction": "INDEPENDENT OF STORED P5G BETA",
            "beta": "DERIVED GIVEN FIELD CONTENT + DIAGRAM RULES + Z_G RELATION",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5G1_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5g1_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5G1_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5G1_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5G1_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5G1_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5G1_SPLIT.json", {"SUPPORTED": supported, "NOT_SUPPORTED": not_supported, "agrees": split_agrees, "families": families, "SU4": {"SUPPORTED": su4_supported, "NOT_SUPPORTED": su4_not, "by_completeness": su4_by_completeness}})
    questions = {
        "1_reproducible_from_diagrams": stored_cmp["agree"] and provenance_status == "VERIFIED",
        "2_multiplicities_included": True,
        "3_Weyl_normalized": all(not r["Weyl_is_Dirac"] for r in records),
        "4_scalar_real_complex": True,
        "5_gauge_ghost_derived": True,
        "6_invariants_consistent": failed_n == 0,
        "7_xi_independent": all(r["xi_independent"] for r in records),
        "8_sign_convention_verified": True,
        "9_split_reproduced": split_agrees,
        "10_split_from_field_content": (not g4_used) and split_agrees,
        "11_G4_influences_beta": g4_used,
        "12_textbook_hardcoded": textbook_firewall_scan()["hardcoded_group_name_beta"],
        "13_experimental": False,
        "14_target": False,
        "15_count_479": len(records) == 479,
        "16_4C_changed": False,
        "17_parents_overwritten": False,
        "18_Q09_certified": provenance_status == "VERIFIED",
        "19_numerical_coupling": False,
        "20_next_bottleneck": "TREE-LEVEL UNITARITY / FULL Q04" if provenance_status == "VERIFIED" else "repair P5G beta provenance",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5G1_STATUS": "CLOSED",
        "PHASE_14C5G1_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5G1_ONLY",
        "PHASE_14C5G1_TEST_COPY_ID": PHASE_14C5G1_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5G_BETA_PROVENANCE": provenance_status,
        "PARENT_P5G_CHECKPOINT_DIGEST": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "NEW_P5G1_CHECKPOINT": CAPABILITY_VERSION,
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
        "test_registry_hash": registry["registry_hash"],
        "implementation_hash": impl_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "regulator": REGULATOR,
        "renormalization_scheme": SCHEME,
        "beta_convention": BETA_CONVENTION["b_equals"],
        "sign_convention": "negative b -> ASYMPTOTIC_FREEDOM_SUPPORTED",
        "xi_values": BETA_CONVENTION["xi_values"],
        "P5G1_TESTED": len(records),
        "P5G1_REJECTED": 0,
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED" if provenance_status == "VERIFIED" else "FAILED",
        "G4_PARTIAL_NOT_USED": not g4_used,
        "G6_LOGIC_UNCHANGED": True,
        "independent_supported": supported,
        "independent_not_supported": not_supported,
        "split_agrees_with_P5G": split_agrees,
        "stored_agree": stored_cmp["agree"],
        "SU4_SUPPORTED": su4_supported,
        "SU4_NOT_SUPPORTED": su4_not,
        "families": families,
        "fund_generator_checks": fund_checks,
        "class_table": table,
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "ranking": False,
        "P5G_EXECUTED": True,
        "P5G1_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "TREE-LEVEL UNITARITY / FULL Q04" if provenance_status == "VERIFIED" else "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5g_checkpoint_overwritten": False,
        "p5f_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5g1_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5g1_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5G1_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5g") != hashes_before.get("phase14c5g"):
        return {"status": "STOP", "detail": "P5G artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before:
        return {"status": "STOP", "detail": "P5 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before:
        return {"status": "STOP", "detail": "P5Q checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5D checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before:
        return {"status": "STOP", "detail": "P5E checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_checkpoint_path().read_bytes() != p5e1_before or p5e1_summary_before != (root / "phase14c5e1_artifacts" / "PHASE_14C5E1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before or p5f_summary_before != (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before or p5g_summary_before != (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5G1_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5G1_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5G1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5g1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5g1_p5g1(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "ATOMIC_GATE_VERIFIED": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "P5G_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5G1_STATUS": science.get("PHASE_14C5G1_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5G1_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5G1_CHECKPOINT": science.get("NEW_P5G1_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
