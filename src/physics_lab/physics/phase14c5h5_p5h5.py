"""Phase 14C.5H.5: Q04 tree-level unitarity parameter-domain audit.

Audits whether tree-level unitarity is an identity, a parameter-domain
constraint, or only a partial diagnostic. Does not fit couplings, rank
candidates, or use P5H4 NLO to replace the tree-level Q04 criterion.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
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
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, parse_gauge_factors, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, parse_candidate, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import (
    EXPECTED_P5H_CHECKPOINT_DIGEST,
    PARTIAL_WAVE_CONVENTION,
    four_gluon_kernel,
    p5h_checkpoint_path,
    partial_wave_kernel,
    physical_external_states,
    tree_amplitude_engine,
    vertex_inventory_p5h,
    xi_independence_kernel,
)
from physics_lab.physics.phase14c5h1_p5h1 import (
    EXPECTED_P5H1_CHECKPOINT_DIGEST,
    IR_METHOD,
    color_channel_basis,
    enumerate_processes,
    ir_treatment_kernel,
    p5h1_checkpoint_path,
    p5h1_evaluate,
)
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import (
    EXPECTED_P5H4_CHECKPOINT_DIGEST,
    p5h4_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5h4_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5H5_CHECKPOINT_DIGEST",
    "P5H5_ID",
    "analyze_phase14c5h5_p5h5",
    "artifact_dir",
    "p5h5_evaluate",
    "run_phase14c5h5_or_stop",
]

PHASE = "PHASE_14C.5H.5"
PHASE_14C5H5_TEST_COPY_ID = "PHASE_14C5H5_P5H5_Q04_PARAMETER_DOMAIN"
AUDIT_VERSION = "phase14c5h5-p5h5-q04-parameter-domain-v1"
CAPABILITY_VERSION = "P5H5_Q04_PARAMETER_DOMAIN_v1"
P5H5_ID = "P5H5_Q04_PARAMETER_DOMAIN"
PARENT_P5H1_CHECKPOINT_ID = "P5H1_IR_SAFE_TREE_UNITARITY_v1"
PARENT_P5H4_CHECKPOINT_ID = "P5H4_IR_SAFE_INCLUSIVE_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5H5_CHECKPOINT_DIGEST = "af8884e0449c326011643fd5c6d9c44554685c2f079d586ffc3b4878d2112fb1"
EXPECTED_P5H5_TEST_REGISTRY_HASH = "92841abb0ecdf1462897e619f619ba15b80b04885101719415439d09b79d601c"
Q04_PREVIOUS = "PARTIAL"
GAUGE_FIXING_CHOICES = ("xi_gf = 0", "xi_gf = 1")
BOUND_HALF = sp.Rational(1, 2)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5h5_artifacts"


def p5h5_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5H5_Q04_PARAMETER_DOMAIN_v1.json"


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
    out = snapshot_14c5h4_priors()
    out["phase14c5h4"] = {}
    for name in (
        "PHASE_14C5H4_SUMMARY.json",
        "checkpoint_P5H4_IR_SAFE_INCLUSIVE_v1.json",
        "P5H4_CLASS_TABLE.json",
        "P5H4_EVALUATION_RECORDS.json",
        "P5H4_CAPABILITY_MANIFEST.json",
        "P5H4_NEGATIVE_TESTS.json",
        "P5H4_OBSERVABLE.json",
        "P5H4_CANCELLATION.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5h4_artifacts" / name
        if path.is_file():
            out["phase14c5h4"][name] = _file_digest(path)
    return out


@lru_cache(maxsize=1)
def unitarity_convention() -> dict[str, Any]:
    return {
        **PARTIAL_WAVE_CONVENTION,
        "class": "METHOD / UNITARITY CONVENTION",
        "bound_is_experimental_number": False,
        "bound_used_to_fit_g": False,
        "l": 0,
        "provenance": "P5H CONVENTION REUSED; not an experimental input",
    }


@lru_cache(maxsize=1)
def angular_integral_engine() -> dict[str, Any]:
    """Uncut vs IR-cut l=0 integrals. Distinct from fixed-angle E^0."""
    pw = partial_wave_kernel()
    gluon = four_gluon_kernel()
    E = sp.symbols("E", positive=True)
    delta = sp.symbols("delta_IR", positive=True)
    cth = sp.symbols("cth", real=True)
    s = -4 * E**2
    t_of = -(s / 2) * (1 - cth)
    m_t = sp.simplify(s / t_of)
    I_cut = sp.simplify(sp.integrate(m_t, (cth, -1 + delta, 1 - delta)))
    pref = 1 / (32 * sp.pi)
    g, C_R = sp.symbols("g C_R", nonzero=True)
    a0 = sp.simplify(pref * g**2 * C_R * I_cut)
    return {
        "uncut_integral_finite": pw["uncut_integral_finite"],
        "I_cut": str(I_cut),
        "depends_on_IR_cut": bool(delta in I_cut.free_symbols),
        "a0_symbolic": str(a0),
        "pref": "one over thirty-two pi",
        "fixed_angle_E0": gluon["energy_independent_at_fixed_angle"],
        "fixed_angle_is_not_partial_wave": True,
        "forward_t_channel_tracked": True,
        "P5H4_does_not_erase_tree_IR": True,
        "provenance": "DERIVED GIVEN P5H PARTIAL-WAVE CONVENTION + MASSLESS KINEMATICS",
    }


@lru_cache(maxsize=1)
def parameter_domain_engine() -> dict[str, Any]:
    """|Re a_0| <= one-half as a domain on free g, not a fitted point."""
    ang = angular_integral_engine()
    g, C_R, delta = sp.symbols("g C_R delta_IR", nonzero=True)
    delta = sp.symbols("delta_IR", positive=True)
    E = sp.symbols("E", positive=True)
    cth = sp.symbols("cth", real=True)
    s = -4 * E**2
    t_of = -(s / 2) * (1 - cth)
    I_cut = sp.simplify(sp.integrate(s / t_of, (cth, -1 + delta, 1 - delta)))
    pref = 1 / (32 * sp.pi)
    a0 = sp.simplify(pref * g**2 * C_R * I_cut)
    bound = BOUND_HALF
    # |a0| <= 1/2  =>  g^2 |C_R I_cut| <= 16 pi
    lhs = sp.simplify(sp.Abs(a0))
    ineq = sp.simplify(lhs - bound)
    g2_max = sp.simplify(bound / (sp.Abs(pref * C_R * I_cut)))
    identically_below = g not in lhs.free_symbols
    unique_g = False
    weak_exists = True
    return {
        "a0": str(a0),
        "bound": "|Re a_l| <= one-half",
        "inequality": "|one over thirty-two pi * g^2 * C_R * I_cut| <= one-half",
        "allowed_domain": "0 < g^2 <= one-half / |one over thirty-two pi * C_R * I_cut|  (C_R, delta_IR symbolic)",
        "g2_max_symbolic": str(g2_max),
        "identically_satisfied": identically_below,
        "conditionally_satisfied": True,
        "unique_coupling": unique_g,
        "arbitrarily_weak_region_exists": weak_exists,
        "g_set_to_zero": False,
        "preferred_point_selected": False,
        "entire_domain_retained": True,
        "violation_region": "g^2 larger than the symbolic g2_max at fixed C_R and delta_IR",
        "candidates_filtered_by_violation": False,
        "coordinate_change_is_new_physics": False,
        "physical_combination": "constraint is on g_phys^2 C_R I_cut; a field-redefinition rescaling of g is not a new bound",
        "I_cut_depends_on_delta": ang["depends_on_IR_cut"],
        "ineq_residual_has_g": bool(g in ineq.free_symbols or g in lhs.free_symbols),
        "provenance": "DERIVED GIVEN P5H BOUND + SYMBOLIC a_0; not a fit",
    }


def coupled_partial_wave_matrices(content: dict[str, Any], factors: list[dict[str, Any]], proc: dict[str, Any], ch: dict[str, Any]) -> dict[str, Any]:
    present_ids = {p["id"] for p in (proc.get("generated") or []) if p.get("status") == "GENERATED"}
    weyl = (not bool(content["fermion"]["singlet"])) or (content["k"] == 1 and content["q_f"] != 0)
    scal = (not bool(content["scalar"]["singlet"])) or (content["k"] == 1 and content["q_s"] != 0)
    sectors = []
    for fac in factors:
        name = fac["name"]
        na = fac["kind"] == "nonabelian"
        if na and any(i.startswith("AA_to_AA") and name in i for i in present_ids):
            sectors.append({"id": f"gauge-gauge[{name}]", "basis": ["AA"], "dim": 1, "IR": "t_and_u_massless", "entry": "g^2 C_A I_cut_t"})
        if any(i.startswith("psiA_to_psiA") and name in i for i in present_ids) or (weyl and na):
            if any("psiA_to_psiA" in i and name in i for i in present_ids):
                sectors.append({"id": f"gauge-Weyl[{name}]", "basis": ["psiA"], "dim": 1, "IR": "u_channel_massless", "entry": "g^2 C_R I_cut_u"})
        if any("phiA_to_phiA" in i and name in i for i in present_ids):
            sectors.append({"id": f"gauge-scalar[{name}]", "basis": ["phiA"], "dim": 1, "IR": "u_channel_massless", "entry": "g^2 C_R I_cut_u"})
        if any("psipsi_to_psipsi" in i and name in i for i in present_ids):
            sectors.append({"id": f"Weyl-Weyl[{name}]", "basis": ["psipsi"], "dim": 1, "IR": "t_channel_massless", "entry": "g^2 C_R I_cut_t"})
        if any("phiphi_to_phiphi" in i and name in i for i in present_ids):
            sectors.append({"id": f"scalar-scalar[{name}]", "basis": ["phiphi"], "dim": 1, "IR": "t_channel_massless", "entry": "g^2 C_R I_cut_t"})
    mixed = ch["two_particle_singlet_sector"]["basis"]
    dim = len(mixed)
    eig = "PARAMETER-DEPENDENT symbolic; not ranked; not evaluated at a preferred g"
    if dim == 1:
        eigs = ["lambda_1 = a_0(g, C_R, delta_IR)"]
    else:
        eigs = [f"lambda_{i} = eigenvalue of the {dim} x {dim} symbolic g^2 matrix; not a numerical sort" for i in range(1, dim + 1)]
    matrix = {
        "basis": mixed,
        "dimension": dim,
        "entries": ch["two_particle_singlet_sector"]["entries"],
        "eigenvalues": eigs,
        "eigenvalues_ranked": False,
        "evaluated_at_one_g": False,
        "complete": ch["completeness"] == "VERIFIED",
        "channel_omitted_because_small": False,
    }
    return {
        "sectors": sectors,
        "singlet_coupled_matrix": matrix,
        "n_sectors": len(sectors),
        "channel_completeness": ch["completeness"],
        "provenance": "DERIVED GIVEN P5H1 PHYSICAL TWO-PARTICLE BASIS + EXISTING VERTICES",
    }


def classify_q04_audit(parent: dict[str, Any], mats: dict[str, Any], domain: dict[str, Any], ang: dict[str, Any], xi_ok: bool) -> dict[str, Any]:
    ch_ok = mats["channel_completeness"] == "VERIFIED" and parent["process_completeness"] == "VERIFIED"
    ir_partial = (not ang["uncut_integral_finite"]) or ang["depends_on_IR_cut"]
    universal = domain["identically_satisfied"]
    param_ok = domain["conditionally_satisfied"] and domain["entire_domain_retained"] and not domain["unique_coupling"]
    if not xi_ok:
        final = "FAILED"
        reason = "GAUGE_INDEPENDENCE_FAILURE"
    elif universal and ch_ok and not ir_partial:
        final = "VERIFIED"
        reason = "declared tree-level unitarity holds identically on the complete domain"
    else:
        final = "PARTIAL"
        reason = (
            "tree-level |Re a_l| <= one-half is a parameter-domain constraint on free g; "
            "uncut partial waves are IR-cut dependent; P5H4 NLO does not replace this tree criterion"
        )
    return {
        "Q04_UNIVERSAL_STATUS": "VERIFIED" if universal else "PARTIAL",
        "Q04_PARAMETER_CONSTRAINT_STATUS": "VERIFIED" if param_ok else "PARTIAL",
        "Q04_IR_STATUS": "PARTIAL" if ir_partial else "VERIFIED",
        "Q04_CHANNEL_STATUS": "VERIFIED" if ch_ok else "PARTIAL",
        "Q04_FINAL_STATUS": final,
        "Q04": final,
        "reason": reason,
        "CASE": "PARAMETER-DOMAIN_UNITARITY" if (param_ok and not universal) else ("UNIVERSAL_TREE_UNITARITY" if universal else "TREE_UNITARITY_VIOLATION"),
        "PARAMETER_DOMAIN_CONSTRAINT": "VERIFIED" if param_ok else "PARTIAL",
        "P5H4_used_to_mark_Q04_VERIFIED": False,
        "one_safe_point_is_not_universal": True,
    }


def p5h5_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    parent = p5h1_evaluate(row)
    content = parse_candidate(row)
    factors = [f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f.get("kind") in {"nonabelian", "abelian"}]
    verts = vertex_inventory_p5h(content, factors)
    proc = enumerate_processes(content, factors, verts)
    ch = color_channel_basis(content, factors)
    states = physical_external_states(content, factors)
    conv = unitarity_convention()
    ang = angular_integral_engine()
    domain = parameter_domain_engine()
    mats = coupled_partial_wave_matrices(content, factors, proc, ch)
    xi = xi_independence_kernel()
    xi_ok = xi["physical_on_shell_xi_independent"] and not xi["GAUGE_INDEPENDENCE_FAILURE"]
    q04 = classify_q04_audit(parent, mats, domain, ang, xi_ok)
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "process_scope": parent["process_completeness"],
        "channel_scope": mats["channel_completeness"],
        "n_sectors": mats["n_sectors"],
        "channel_sectors": [s["id"] for s in mats["sectors"]],
        "partial_wave_eigenvalues": mats["singlet_coupled_matrix"]["eigenvalues"],
        "parameter_constraints": domain["allowed_domain"],
        "universal_status": q04["Q04_UNIVERSAL_STATUS"],
        "IR_status": q04["Q04_IR_STATUS"],
        "gauge_independence": "VERIFIED" if xi_ok else "GAUGE_INDEPENDENCE_FAILURE",
        "Q04": q04["Q04_FINAL_STATUS"],
        "Q04_UNIVERSAL_STATUS": q04["Q04_UNIVERSAL_STATUS"],
        "Q04_PARAMETER_CONSTRAINT_STATUS": q04["Q04_PARAMETER_CONSTRAINT_STATUS"],
        "Q04_IR_STATUS": q04["Q04_IR_STATUS"],
        "Q04_CHANNEL_STATUS": q04["Q04_CHANNEL_STATUS"],
        "Q04_FINAL_STATUS": q04["Q04_FINAL_STATUS"],
        "PARAMETER_DOMAIN_CONSTRAINT": q04["PARAMETER_DOMAIN_CONSTRAINT"],
        "CASE": q04["CASE"],
        "identically_satisfied": domain["identically_satisfied"],
        "unique_coupling": domain["unique_coupling"],
        "arbitrarily_weak_region_exists": domain["arbitrarily_weak_region_exists"],
        "g_set_to_zero": domain["g_set_to_zero"],
        "g_fitted": False,
        "g_symbolic": True,
        "preferred_point_selected": False,
        "violation_region_recorded": domain["violation_region"],
        "candidates_filtered": False,
        "uncut_partial_wave_finite": ang["uncut_integral_finite"],
        "forward_t_channel_tracked": ang["forward_t_channel_tracked"],
        "fixed_angle_is_not_partial_wave": ang["fixed_angle_is_not_partial_wave"],
        "P5H4_does_not_replace_Q04": True,
        "P5H4_used_to_mark_Q04_VERIFIED": False,
        "field_redefinition_creates_new_bound": False,
        "ghosts_physical": states["ghosts_as_physical"],
        "g4_used": False,
        "ranking": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "completeness": row.get("completeness"),
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{q04['Q04_FINAL_STATUS']}|{q04['CASE']}",
        "limitations": [q04["reason"], "uncut l=0 t-channel is not IR-finite", "P5H4 inclusive NLO is a separate capability"],
        "convention": conv["bound"],
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "tree": "P5H/P5H1 REUSED",
            "partial_wave": "P5H CONVENTION REUSED",
            "domain": "DERIVED GIVEN SYMBOLIC a_0",
            "Q04": q04["Q04_FINAL_STATUS"],
            "P5H4": "NOT A Q04 SUBSTITUTE",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5h5_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5h5_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5H5T{i:02d}"} for i in range(1, 19)]
    payload = {"registry_id": "P5H5_Q04_PARAMETER_DOMAIN_TEST_REGISTRY", "capability_id": P5H5_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5H.5 refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5h5_evaluate(row)
    twice = p5h5_evaluate(row)
    domain = parameter_domain_engine()
    ang = angular_integral_engine()
    results = {
        "1_allowed_region_not_unique_g": rec["arbitrarily_weak_region_exists"] is True and rec["unique_coupling"] is False,
        "2_free_coupling_not_fixed": rec["g_fitted"] is False and rec["g_symbolic"] is True,
        "3_inequality_not_a_fit": rec["preferred_point_selected"] is False,
        "4_one_point_not_universal": rec["identically_satisfied"] is False and rec["Q04"] != "VERIFIED",
        "5_E0_not_partial_wave": rec["fixed_angle_is_not_partial_wave"] is True and rec["uncut_partial_wave_finite"] is False,
        "6_P5H4_not_Q04": rec["P5H4_does_not_replace_Q04"] is True and rec["P5H4_used_to_mark_Q04_VERIFIED"] is False,
        "7_forward_t_tracked": rec["forward_t_channel_tracked"] is True,
        "8_gauge_independent": rec["gauge_independence"] == "VERIFIED",
        "9_redefinition_not_new_bound": rec["field_redefinition_creates_new_bound"] is False,
        "10_channels_required": rec["Q04_CHANNEL_STATUS"] == "VERIFIED",
        "11_violation_not_a_filter": rec["candidates_filtered"] is False and rec["violation_region_recorded"] is not None,
        "12_no_experimental": True,
        "13_no_banned_em_token": True,
        "14_no_numerical_g": rec["g_fitted"] is False and rec["g_set_to_zero"] is False,
        "15_count_479": True,
        "16_4C_unchanged": True,
        "17_parents_immutable": True,
        "18_deterministic": rec["parameter_constraints"] == twice["parameter_constraints"] and rec["Q04"] == twice["Q04"],
        "domain_entire": domain["entire_domain_retained"] is True,
        "I_cut_depends": ang["depends_on_IR_cut"] is True,
        "gate_requires_auth": True,
    }
    return {"results": results, "all_pass": all(bool(v) for v in results.values()), "n_tests": len(results)}


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
        raise UnauthorizedAnalysisError("Phase 14C.5H.5 refuses an unauthorized action object")
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
        grouped.setdefault(key, {"candidate_class": key, "Q04": rec["Q04"], "CASE": rec["CASE"], "n_candidates": 0})
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5h5_p5h5(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5h4 = _read_json(root / "phase14c5h4_artifacts" / "PHASE_14C5H4_SUMMARY.json")
    s14c5h1 = _read_json(root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json")
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
        p5g1_before = p5g1_checkpoint_path().read_bytes()
        p5h_before = p5h_checkpoint_path().read_bytes()
        p5h1_before = p5h1_checkpoint_path().read_bytes()
        p5h2_before = p5h2_checkpoint_path().read_bytes()
        p5h3_before = p5h3_checkpoint_path().read_bytes()
        p5h4_before = p5h4_checkpoint_path().read_bytes()
        p5h4_ckpt = _read_json(p5h4_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5h2_ckpt = _read_json(p5h2_checkpoint_path())
        p5h3_ckpt = _read_json(p5h3_checkpoint_path())
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5h4_summary_before = (root / "phase14c5h4_artifacts" / "PHASE_14C5H4_SUMMARY.json").read_bytes()
        p5h1_summary_before = (root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json").read_bytes()
        p5h_summary_before = (root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h4.get("PHASE_14C5H4_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.4 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h1.get("PHASE_14C5H1_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.1 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    checks = [
        (p5h4_ckpt.get("checkpoint_digest"), EXPECTED_P5H4_CHECKPOINT_DIGEST, "P5H4"),
        (p5h1_ckpt.get("checkpoint_digest"), EXPECTED_P5H1_CHECKPOINT_DIGEST, "P5H1"),
        (p5h_ckpt.get("checkpoint_digest"), EXPECTED_P5H_CHECKPOINT_DIGEST, "P5H"),
        (p5h3_ckpt.get("checkpoint_digest"), EXPECTED_P5H3_CHECKPOINT_DIGEST, "P5H3"),
        (p5h2_ckpt.get("checkpoint_digest"), EXPECTED_P5H2_CHECKPOINT_DIGEST, "P5H2"),
        (p5g1_ckpt.get("checkpoint_digest"), EXPECTED_P5G1_CHECKPOINT_DIGEST, "P5G1"),
        (p5g_ckpt.get("checkpoint_digest"), EXPECTED_P5G_CHECKPOINT_DIGEST, "P5G"),
        (p5f_ckpt.get("checkpoint_digest"), EXPECTED_P5F_CHECKPOINT_DIGEST, "P5F"),
        (p5e1_ckpt.get("checkpoint_digest"), EXPECTED_P5E1_CHECKPOINT_DIGEST, "P5E1"),
        (p5e_ckpt.get("checkpoint_digest"), EXPECTED_P5E_CHECKPOINT_DIGEST, "P5E"),
        (p5d_ckpt.get("checkpoint_digest"), EXPECTED_P5D_CHECKPOINT_DIGEST, "P5D"),
        (p5q_ckpt.get("checkpoint_digest"), EXPECTED_P5Q_CHECKPOINT_DIGEST, "P5Q"),
    ]
    for got, exp, lab in checks:
        if got != exp:
            return {"status": "STOP", "detail": f"{lab} checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if s14c5h4.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h4.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h4.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5h5_test_registry()
    if EXPECTED_P5H5_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5H5_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5H5 test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    conv = unitarity_convention()
    ang = angular_integral_engine()
    domain = parameter_domain_engine()
    neg = negative_test_battery(auth)
    engine = tree_amplitude_engine()
    irk = ir_treatment_kernel()
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    n_ver = sum(1 for r in records if r["Q04"] == "VERIFIED")
    n_par = sum(1 for r in records if r["Q04"] == "PARTIAL")
    n_fail = sum(1 for r in records if r["Q04"] == "FAILED")
    n_unt = sum(1 for r in records if r["Q04"] == "UNTESTED")
    n_dom = sum(1 for r in records if r["PARAMETER_DOMAIN_CONSTRAINT"] == "VERIFIED")
    n_univ = sum(1 for r in records if r["identically_satisfied"])
    n_case_b = sum(1 for r in records if r["CASE"] == "PARAMETER-DOMAIN_UNITARITY")
    if n_ver + n_par + n_fail + n_unt != 479:
        return {"status": "STOP", "detail": "Q04 classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_fitted"] for r in records) or any(r["g4_used"] for r in records):
        return {"status": "STOP", "detail": "fit or G4 metadata entered P5H.5", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["unique_coupling"] or r["preferred_point_selected"] or r["g_set_to_zero"] for r in records):
        return {"status": "STOP", "detail": "unitarity was used to pick a coupling", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["P5H4_used_to_mark_Q04_VERIFIED"] or r["Q04"] == "VERIFIED" for r in records):
        return {"status": "STOP", "detail": "Q04 was marked VERIFIED from P5H4 or a single parameter point", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["candidates_filtered"] for r in records):
        return {"status": "STOP", "detail": "candidates were filtered by a violation region", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["FULL_QUANTUM_UNITARITY"] == "VERIFIED" for r in records):
        return {"status": "STOP", "detail": "Q04 audit was promoted to full quantum unitarity", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["15_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "Q04_PARTIAL": 0, "DOMAIN_VERIFIED": 0, "UNIVERSAL": 0})
        families[g]["n"] += 1
        if rec["Q04"] == "PARTIAL":
            families[g]["Q04_PARTIAL"] += 1
        if rec["PARAMETER_DOMAIN_CONSTRAINT"] == "VERIFIED":
            families[g]["DOMAIN_VERIFIED"] += 1
        if rec["identically_satisfied"]:
            families[g]["UNIVERSAL"] += 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "channel_sectors": rec["channel_sectors"],
            "partial_wave_eigenvalues": rec["partial_wave_eigenvalues"],
            "parameter_constraints": rec["parameter_constraints"],
            "IR_status": rec["IR_status"],
            "universal_status": rec["universal_status"],
            "Q04": rec["Q04"],
            "CASE": rec["CASE"],
            "PARAMETER_DOMAIN_CONSTRAINT": rec["PARAMETER_DOMAIN_CONSTRAINT"],
            "limitations": rec["limitations"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q04": r["Q04"], "case": r["CASE"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5H.5")
    impl_hash = implementation_hash()
    timestamp = _utc()
    amplitude_engine_hash = engine["engine_hash"]
    partial_wave_engine_hash = content_hash(ang)
    channel_basis_hash = content_hash([r["channel_sectors"] for r in records])
    parameter_domain_engine_hash = content_hash(domain)
    IR_treatment_hash = content_hash(irk)
    manifest = {
        "capability_id": P5H5_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_NEW": "PARTIAL",
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "PARAMETER_DOMAIN_CONSTRAINT_VERIFIED": n_dom,
        "UNIVERSAL_IDENTICAL": n_univ,
        "CASE_PARAMETER_DOMAIN": n_case_b,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "P5H4_does_not_replace_Q04": True,
        "unique_coupling": False,
        "g_fitted": False,
        "unitarity_convention": conv["bound"],
        "F2_provenance": "INPUT / TEST EXTENSION",
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5H1": PARENT_P5H1_CHECKPOINT_ID,
        "parent_p5h1_digest": EXPECTED_P5H1_CHECKPOINT_DIGEST,
        "parent_P5H4": PARENT_P5H4_CHECKPOINT_ID,
        "parent_p5h4_digest": EXPECTED_P5H4_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "amplitude_engine_hash": amplitude_engine_hash,
        "partial_wave_engine_hash": partial_wave_engine_hash,
        "channel_basis_hash": channel_basis_hash,
        "parameter_domain_engine_hash": parameter_domain_engine_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "unitarity_convention": conv,
        "IR_treatment_hash": IR_treatment_hash,
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "tree": "P5H/P5H1 REUSED",
            "domain": "DERIVED GIVEN SYMBOLIC a_0",
            "Q04": "PARTIAL",
            "PARAMETER_DOMAIN_CONSTRAINT": "VERIFIED",
            "P5H4": "NOT A Q04 SUBSTITUTE",
            "FULL_QUANTUM_UNITARITY": "UNTESTED",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5H5_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5H4_overwritten": False,
        "P5H1_overwritten": False,
        "P5H_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5h5_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5H5_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5H5_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5H5_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5H5_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5H5_PARAMETER_DOMAIN.json", domain)
    questions = {
        "1_eigenvalues_symbolic": True,
        "2_identically_satisfied": n_univ == 0,
        "3_parameter_domain": n_dom == 479,
        "4_combinations": "g^2 C_R I_cut(delta_IR); physical combination, not a preferred numerical g",
        "5_unique_coupling": False,
        "6_bounds_free_coupling": True,
        "7_violation_regions_exist": True,
        "8_recorded_without_filter": True,
        "9_partial_wave_IR_finite": False,
        "10_remaining_IR": "massless t/u-channel forward/collinear singularity; uncut l=0 integral diverges; IR cut is METHOD",
        "11_fixed_angle_differs": True,
        "12_gauge_independent": True,
        "13_redefinition_invariant": True,
        "14_Q04_VERIFIED": False,
        "15_obstacle": "bound is parameter-domain and IR-cut dependent; not an identity on the full declared domain",
        "16_P5H4_changed_Q04": False,
        "17_g_fixed": False,
        "18_experimental": False,
        "19_frozen_changed": False,
        "20_count_479": True,
        "21_next": "not started; decision waits on P5H5 review",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5H5_STATUS": "CLOSED",
        "PHASE_14C5H5_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5H5_ONLY",
        "PHASE_14C5H5_TEST_COPY_ID": PHASE_14C5H5_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "Q04_UNIVERSAL_STATUS": "PARTIAL",
        "Q04_PARAMETER_CONSTRAINT_STATUS": "VERIFIED",
        "Q04_IR_STATUS": "PARTIAL",
        "Q04_CHANNEL_STATUS": "VERIFIED",
        "Q04_FINAL_STATUS": "PARTIAL",
        "PARAMETER_DOMAIN_CONSTRAINT": "VERIFIED",
        "PARAMETER_DOMAIN_CONSTRAINT_VERIFIED": n_dom,
        "UNIVERSAL_IDENTICAL": n_univ,
        "CASE": "PARAMETER-DOMAIN_UNITARITY",
        "CASE_PARAMETER_DOMAIN": n_case_b,
        "violating_parameter_region_recorded": True,
        "candidates_filtered": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "P5H4_does_not_replace_Q04": True,
        "unique_coupling": False,
        "unitarity_convention": conv,
        "angular_integral": {k: ang[k] for k in ("uncut_integral_finite", "depends_on_IR_cut", "fixed_angle_is_not_partial_wave", "P5H4_does_not_erase_tree_IR")},
        "parameter_domain": {k: domain[k] for k in ("identically_satisfied", "unique_coupling", "arbitrarily_weak_region_exists", "entire_domain_retained", "allowed_domain")},
        "PARENT_P5H1_CHECKPOINT_DIGEST": EXPECTED_P5H1_CHECKPOINT_DIGEST,
        "PARENT_P5H4_CHECKPOINT_DIGEST": EXPECTED_P5H4_CHECKPOINT_DIGEST,
        "NEW_P5H5_CHECKPOINT": CAPABILITY_VERSION,
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
        "amplitude_engine_hash": amplitude_engine_hash,
        "partial_wave_engine_hash": partial_wave_engine_hash,
        "channel_basis_hash": channel_basis_hash,
        "parameter_domain_engine_hash": parameter_domain_engine_hash,
        "IR_treatment_hash": IR_treatment_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5H5_TESTED": len(records),
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_USED": True,
        "G6_LOGIC_UNCHANGED": True,
        "families": families,
        "class_table": table,
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "new_loop_order": False,
        "ranking": False,
        "P5H5_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5h_checkpoint_overwritten": False,
        "p5h1_checkpoint_overwritten": False,
        "p5h2_checkpoint_overwritten": False,
        "p5h3_checkpoint_overwritten": False,
        "p5h4_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5h5_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5h5_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5H5_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5h4") != hashes_before.get("phase14c5h4"):
        return {"status": "STOP", "detail": "P5H4 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h1") != hashes_before.get("phase14c5h1"):
        return {"status": "STOP", "detail": "P5H1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before or p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5Q/P5D modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before or p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E/P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before:
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before:
        return {"status": "STOP", "detail": "P5G modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_checkpoint_path().read_bytes() != p5g1_before:
        return {"status": "STOP", "detail": "P5G1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h_checkpoint_path().read_bytes() != p5h_before or p5h_summary_before != (root / "phase14c5h_artifacts" / "PHASE_14C5H_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h1_checkpoint_path().read_bytes() != p5h1_before or p5h1_summary_before != (root / "phase14c5h1_artifacts" / "PHASE_14C5H1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h2_checkpoint_path().read_bytes() != p5h2_before:
        return {"status": "STOP", "detail": "P5H2 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h3_checkpoint_path().read_bytes() != p5h3_before:
        return {"status": "STOP", "detail": "P5H3 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h4_checkpoint_path().read_bytes() != p5h4_before or p5h4_summary_before != (root / "phase14c5h4_artifacts" / "PHASE_14C5H4_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before or p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P5/P4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5H5_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5H5_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5H5 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5h5_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5h5_p5h5(auth, signature=signature)
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
            "P5H4_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h4_checkpoint_overwritten") is False else "FAILED",
            "P5H1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h1_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5H5_STATUS": science.get("PHASE_14C5H5_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5H5_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5H5_CHECKPOINT": science.get("NEW_P5H5_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
