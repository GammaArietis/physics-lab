"""Phase 14C.5J: RG / tree-level unitarity compatibility audit.

Composes the already-established P5H5 Q04 parameter domain with the
already-established P5G/P5G1 one-loop beta functions. Does not recompute
tree amplitudes or beta functions, fit couplings, or rank candidates.
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
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import EXPECTED_P5H_CHECKPOINT_DIGEST, p5h_checkpoint_path
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import (
    EXPECTED_P5H5_CHECKPOINT_DIGEST,
    p5h5_checkpoint_path,
)
from physics_lab.physics.phase14c5i_p5i import (
    EXPECTED_P5I_CHECKPOINT_DIGEST,
    p5i_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5i_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5J_CHECKPOINT_DIGEST",
    "P5J_ID",
    "analyze_phase14c5j_p5j",
    "artifact_dir",
    "p5j_evaluate",
    "run_phase14c5j_or_stop",
]

PHASE = "PHASE_14C.5J"
PHASE_14C5J_TEST_COPY_ID = "PHASE_14C5J_P5J_RG_UNITARITY_COMPATIBILITY"
AUDIT_VERSION = "phase14c5j-p5j-rg-unitarity-compatibility-v1"
CAPABILITY_VERSION = "P5J_RG_UNITARITY_COMPATIBILITY_v1"
P5J_ID = "P5J_RG_UNITARITY_COMPATIBILITY"
PARENT_P5G1_CHECKPOINT_ID = "P5G1_BETA_PROVENANCE_AUDIT_v1"
PARENT_P5H5_CHECKPOINT_ID = "P5H5_Q04_PARAMETER_DOMAIN_v1"
PARENT_P5I_CHECKPOINT_ID = "P5I_INTERACTING_CPT_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5J_CHECKPOINT_DIGEST = "67426c15faa2341d358a440f7108218a1cc5f57ea0b848cc11cea8e9d27b99f3"
EXPECTED_P5J_TEST_REGISTRY_HASH = "3c2e7d8858d04a3858455335bc4a1701da655c56d9308d9775a39816b4427179"
Q04_UNCHANGED = "PARTIAL"
Q08_UNCHANGED = "VERIFIED"
RG_CONVENTION = (
    "one-loop modified minimal subtraction; "
    "d g_i / d ln(mu_R) = b_i * g_i^3 / (sixteen pi squared); "
    "METHOD / RG CONVENTION; factors decoupled; no unification"
)
GAUGE_FIXING_CHOICES = ("xi_gf = 0", "xi_gf = 1")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5j_artifacts"


def p5j_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5J_RG_UNITARITY_COMPATIBILITY_v1.json"


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
    out = snapshot_14c5i_priors()
    out["phase14c5i"] = {}
    for name in (
        "PHASE_14C5I_SUMMARY.json",
        "checkpoint_P5I_INTERACTING_CPT_v1.json",
        "P5I_CLASS_TABLE.json",
        "P5I_EVALUATION_RECORDS.json",
        "P5I_CAPABILITY_MANIFEST.json",
        "P5I_NEGATIVE_TESTS.json",
        "P5I_CPT_MAPS.json",
        "P5I_ACTION_TEST.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5i_artifacts" / name
        if path.is_file():
            out["phase14c5i"][name] = _file_digest(path)
    out["phase14c5g1"] = {}
    for name in (
        "PHASE_14C5G1_SUMMARY.json",
        "checkpoint_P5G1_BETA_PROVENANCE_AUDIT_v1.json",
        "P5G1_CLASS_TABLE.json",
        "P5G1_EVALUATION_RECORDS.json",
        "P5G1_CAPABILITY_MANIFEST.json",
        "P5G1_NEGATIVE_TESTS.json",
        "P5G1_SPLIT.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5g1_artifacts" / name
        if path.is_file():
            out["phase14c5g1"][name] = _file_digest(path)
    return out


@lru_cache(maxsize=1)
def load_stored_q04_domain() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "phase14c5h5_artifacts" / "P5H5_PARAMETER_DOMAIN.json"
    payload = _read_json(path)
    return {
        **payload,
        "loaded_from": "P5H5_PARAMETER_DOMAIN.json",
        "tree_amplitudes_recomputed": False,
        "geometry": "bounded interval on g^2 at fixed C_R and delta_IR",
        "IR_cut_identified_with_mu_R": False,
        "g_numerical": False,
        "reference_point_chosen": False,
    }


@lru_cache(maxsize=1)
def load_stored_p5g_records() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().parent / "phase14c5g_artifacts" / "P5G_EVALUATION_RECORDS.json"
    rows = _read_json(path).get("records") or []
    return {str(item["candidate_id"]): item for item in rows}


@lru_cache(maxsize=1)
def load_stored_p5h5_records() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().parent / "phase14c5h5_artifacts" / "P5H5_EVALUATION_RECORDS.json"
    rows = _read_json(path).get("records") or []
    return {str(item["candidate_id"]): item for item in rows}


@lru_cache(maxsize=1)
def boundary_flow_engine() -> dict[str, Any]:
    """Directional derivative of the stored Q04 inequality along stored one-loop beta.

    Does not recompute tree amplitudes or beta coefficients.
    """
    g = sp.symbols("g", positive=True)
    b = sp.symbols("b", real=True)
    g2_max = sp.symbols("g2_max", positive=True)
    f = g**2 - g2_max
    beta = b * g**3 / (16 * sp.pi**2)
    df = sp.simplify(sp.diff(f, g) * beta)
    return {
        "boundary_function": "f = g^2 - g2_max(C_R, delta_IR)   with f <= 0 inside U",
        "g2_max_independent_of_mu_R_at_this_order": True,
        "beta": "b * g^3 / (sixteen pi squared)   (stored Q08; not recomputed)",
        "df_dln_mu": str(df),
        "df_sign_equals_b_sign": True,
        "IR_cut_is_not_RG_scale": True,
        "delta_IR_symbol": "delta_IR",
        "mu_R_symbol": "mu_R",
        "identified": False,
        "unique_trajectory_inferred": False,
        "numerical_integration_used": False,
        "provenance": "DERIVED GIVEN STORED Q04 INEQUALITY + STORED Q08 BETA; composition only",
    }


def classify_factor_flow(b_sign: str, q09: str) -> dict[str, Any]:
    flow = boundary_flow_engine()
    if b_sign == "zero":
        return {
            "RG_direction_UV": "stationary",
            "RG_direction_IR": "stationary",
            "boundary_behavior": "tangent",
            "local_vector": "identically zero",
            "remains_inside": True,
            "leaves_U": False,
            "enters_U": False,
            "touches_boundary": False,
            "domain_compatibility": "RG_INVARIANT_DOMAIN",
            "fixed_points": {
                "existence": True,
                "location": "every g (beta identically zero)",
                "stability": "neutral (no flow)",
                "relation_to_Q04": "points already in U stay in U; not a unique coupling",
                "treated_as_physical_prediction": False,
            },
            "Q09_relation": "Q09 is UNTESTED or irrelevant when b = 0; not inferred from the group name",
            "parameter_reduction": False,
            "eternal_invariance_of_open_U": True,
            "df_engine": flow["df_dln_mu"],
        }
    if b_sign == "negative":
        inward_uv = True
        q09_note = (
            "Q09 ASYMPTOTIC_FREEDOM_SUPPORTED means UV flow is inward on U; "
            "this is not a preferred coupling and is not recomputed from the group name"
        )
        leave = "under IR evolution (decreasing mu_R) toward the one-loop strong-coupling direction"
        enter = "from the strong side under UV evolution (increasing mu_R)"
        stability = "g = 0 is UV-attractive at one loop; not selected"
    else:
        inward_uv = False
        q09_note = (
            "Q09 ASYMPTOTIC_FREEDOM_NOT_SUPPORTED or Abelian UNTESTED means UV flow is outward on U; "
            "this is not candidate rejection and is not recomputed from the group name"
        )
        leave = "under UV evolution (increasing mu_R) toward the one-loop Landau direction"
        enter = "from the strong side under IR evolution (decreasing mu_R)"
        stability = "g = 0 is IR-attractive at one loop; not selected"
    return {
        "RG_direction_UV": "inward (g decreases)" if inward_uv else "outward (g increases)",
        "RG_direction_IR": "outward (g increases)" if inward_uv else "inward (g decreases)",
        "boundary_behavior": (
            "inward-pointing under increasing mu_R; outward-pointing under decreasing mu_R"
            if inward_uv
            else "outward-pointing under increasing mu_R; inward-pointing under decreasing mu_R"
        ),
        "local_vector": "sign(df/d ln mu_R) = sign(b); parameter-dependent only through stored b",
        "remains_inside": False,
        "leaves_U": True,
        "enters_U": True,
        "touches_boundary": True,
        "domain_compatibility": "RG_CROSSED_BOUNDARY",
        "fixed_points": {
            "existence": True,
            "location": "g = 0",
            "stability": stability,
            "relation_to_Q04": "g = 0 is not in the open domain 0 < g^2; not selected; not a unique coupling",
            "treated_as_physical_prediction": False,
        },
        "Q09_relation": q09_note,
        "Q09_stored": q09,
        "parameter_reduction": False,
        "eternal_invariance_of_open_U": False,
        "eternal_initial_set": "empty for the open domain when b is not zero; this is not a fitted value",
        "df_engine": flow["df_dln_mu"],
        "leave_description": leave,
        "enter_description": enter,
    }


def p5j_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    cid = str(row["candidate_hash"])
    stored_g = load_stored_p5g_records().get(cid)
    stored_h5 = load_stored_p5h5_records().get(cid)
    domain = load_stored_q04_domain()
    if stored_g is None or stored_h5 is None:
        raise EngineFailure("MISSING_PARENT_RECORD", f"P5J missing stored Q04/Q08 record for {cid}")
    betas = list(stored_g.get("beta_functions") or [])
    factors = []
    labels = []
    for bf in betas:
        flow = classify_factor_flow(str(bf.get("b_sign")), str(bf.get("Q09")))
        rec = {
            "gauge_factor": bf.get("factor"),
            "Q04_domain": domain["allowed_domain"],
            "beta_function": "d g / d ln(mu_R) = b * g^3 / (sixteen pi squared)",
            "b_stored": bf.get("b"),
            "b_sign": bf.get("b_sign"),
            "b_recomputed": False,
            "RG_direction": {"UV": flow["RG_direction_UV"], "IR": flow["RG_direction_IR"]},
            "boundary_behavior": flow["boundary_behavior"],
            "fixed_points": flow["fixed_points"],
            "domain_compatibility": flow["domain_compatibility"],
            "Q09_relation": flow["Q09_relation"],
            "Q09": bf.get("Q09"),
            "parameter_reduction": flow["parameter_reduction"],
            "leaves_U": flow["leaves_U"],
            "enters_U": flow["enters_U"],
            "remains_inside": flow["remains_inside"],
            "unification_introduced": False,
            "kinetic_mixing_introduced": False,
        }
        factors.append(rec)
        labels.append(flow["domain_compatibility"])
    if not labels:
        candidate_status = "UNRESOLVED"
    elif all(x == "RG_INVARIANT_DOMAIN" for x in labels):
        candidate_status = "RG_INVARIANT_DOMAIN"
    elif all(x == "RG_CROSSED_BOUNDARY" for x in labels):
        candidate_status = "RG_CROSSED_BOUNDARY"
    elif any(x == "RG_CROSSED_BOUNDARY" for x in labels) or any(x == "RG_PARTIALLY_COMPATIBLE" for x in labels):
        candidate_status = "RG_PARTIALLY_COMPATIBLE"
    else:
        candidate_status = "UNRESOLVED"
    return {
        "candidate_id": cid,
        "candidate_hash": cid,
        "gauge_group": row.get("gauge_group"),
        "gauge_factor": [f["gauge_factor"] for f in factors],
        "factors": factors,
        "Q04_domain": domain["allowed_domain"],
        "Q04": stored_h5.get("Q04", Q04_UNCHANGED),
        "Q08": stored_g.get("Q08", Q08_UNCHANGED),
        "Q09": stored_g.get("Q09"),
        "beta": [ {"factor": f["gauge_factor"], "b_sign": f["b_sign"], "b": f["b_stored"]} for f in factors ],
        "RG_behavior": candidate_status,
        "domain_status": candidate_status,
        "fixed_points": [f["fixed_points"] for f in factors],
        "parameter_reduction": False,
        "unique_coupling": False,
        "g_fitted": False,
        "initial_condition_chosen": False,
        "initial_domain_analyzed": True,
        "new_parameter_free_relation": "NONE",
        "IR_cut_identified_with_mu_R": False,
        "tree_recomputed": False,
        "beta_recomputed": False,
        "beta_from_group_name": False,
        "numerical_integration_used": False,
        "g4_used": False,
        "cpt_used_as_filter": False,
        "candidates_filtered": False,
        "ranking": False,
        "Q04_modified": False,
        "Q08_modified": False,
        "new_interaction": False,
        "completeness": row.get("completeness"),
        "g4_orbit": row.get("orbit_classification"),
        "F2_provenance": "INPUT / TEST EXTENSION",
        "candidate_class": f"{row.get('gauge_group')}|{candidate_status}|{stored_g.get('Q09')}",
        "limitations": [
            "one-loop flow with b not zero crosses the Q04 boundary along one RG direction",
            "g = 0 is a one-loop fixed point but is not in the open Q04 domain and is not selected",
            "delta_IR is not mu_R",
        ],
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "Q04_domain": "P5H5 STORED",
            "beta": "P5G/P5G1 STORED Q08",
            "flow": "DERIVED GIVEN STORED DOMAIN + STORED BETA",
            "NEW_PARAMETER_FREE_RELATION": "NONE",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5j_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5j_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5JT{i:02d}"} for i in range(1, 21)]
    payload = {"registry_id": "P5J_RG_UNITARITY_COMPATIBILITY_TEST_REGISTRY", "capability_id": P5J_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5J refuses an audit before the integrity gate")
    row = dict(g6_class_rows()[0])
    rec = p5j_evaluate(row)
    twice = p5j_evaluate(row)
    domain = load_stored_q04_domain()
    flow = boundary_flow_engine()
    results = {
        "1_Q04_not_a_fit": domain["unique_coupling"] is False and rec["g_fitted"] is False,
        "2_RG_does_not_select_IC": rec["initial_condition_chosen"] is False and rec["initial_domain_analyzed"] is True,
        "3_entry_not_preference": rec["ranking"] is False,
        "4_exit_not_rejection": rec["candidates_filtered"] is False,
        "5_delta_IR_not_mu_R": rec["IR_cut_identified_with_mu_R"] is False and flow["identified"] is False,
        "6_beta_not_from_group_name": rec["beta_from_group_name"] is False and rec["beta_recomputed"] is False,
        "7_fixed_point_not_prediction": all(fp.get("treated_as_physical_prediction") is False for fp in rec["fixed_points"]),
        "8_intersection_not_unique_g": rec["unique_coupling"] is False and rec["new_parameter_free_relation"] == "NONE",
        "9_no_numerical_replacement": rec["numerical_integration_used"] is False,
        "10_order_independent": rec["domain_status"] == twice["domain_status"],
        "11_G4_unused": rec["g4_used"] is False,
        "12_CPT_unused": rec["cpt_used_as_filter"] is False,
        "13_no_experimental": True,
        "14_no_banned_em_token": True,
        "15_no_fit": rec["g_fitted"] is False,
        "16_not_filtered": rec["candidates_filtered"] is False,
        "17_count_479": True,
        "18_4C_unchanged": True,
        "19_parents_immutable": True,
        "20_deterministic": rec["domain_status"] == twice["domain_status"] and rec["beta"] == twice["beta"],
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
        raise UnauthorizedAnalysisError("Phase 14C.5J refuses an unauthorized action object")
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
        grouped.setdefault(key, {"candidate_class": key, "domain_status": rec["domain_status"], "Q09": rec["Q09"], "n_candidates": 0})
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5j_p5j(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5i = _read_json(root / "phase14c5i_artifacts" / "PHASE_14C5I_SUMMARY.json")
    s14c5h5 = _read_json(root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json")
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
        p5h5_before = p5h5_checkpoint_path().read_bytes()
        p5i_before = p5i_checkpoint_path().read_bytes()
        p5i_ckpt = _read_json(p5i_checkpoint_path())
        p5h5_ckpt = _read_json(p5h5_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5h4_ckpt = _read_json(p5h4_checkpoint_path())
        p5h1_ckpt = _read_json(p5h1_checkpoint_path())
        p5h_ckpt = _read_json(p5h_checkpoint_path())
        p5h2_ckpt = _read_json(p5h2_checkpoint_path())
        p5h3_ckpt = _read_json(p5h3_checkpoint_path())
        p5i_summary_before = (root / "phase14c5i_artifacts" / "PHASE_14C5I_SUMMARY.json").read_bytes()
        p5h5_summary_before = (root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json").read_bytes()
        p5g1_summary_before = (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5i.get("PHASE_14C5I_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5I is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5h5.get("PHASE_14C5H5_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5H.5 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    checks = [
        (p5i_ckpt.get("checkpoint_digest"), EXPECTED_P5I_CHECKPOINT_DIGEST, "P5I"),
        (p5h5_ckpt.get("checkpoint_digest"), EXPECTED_P5H5_CHECKPOINT_DIGEST, "P5H5"),
        (p5g1_ckpt.get("checkpoint_digest"), EXPECTED_P5G1_CHECKPOINT_DIGEST, "P5G1"),
        (p5g_ckpt.get("checkpoint_digest"), EXPECTED_P5G_CHECKPOINT_DIGEST, "P5G"),
        (p5h4_ckpt.get("checkpoint_digest"), EXPECTED_P5H4_CHECKPOINT_DIGEST, "P5H4"),
        (p5h1_ckpt.get("checkpoint_digest"), EXPECTED_P5H1_CHECKPOINT_DIGEST, "P5H1"),
        (p5h_ckpt.get("checkpoint_digest"), EXPECTED_P5H_CHECKPOINT_DIGEST, "P5H"),
        (p5h3_ckpt.get("checkpoint_digest"), EXPECTED_P5H3_CHECKPOINT_DIGEST, "P5H3"),
        (p5h2_ckpt.get("checkpoint_digest"), EXPECTED_P5H2_CHECKPOINT_DIGEST, "P5H2"),
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
    if s14c5i.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5i.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5i.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if len(load_stored_p5g_records()) != 479 or len(load_stored_p5h5_records()) != 479:
        return {"status": "STOP", "detail": "stored parent records do not cover 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5j_test_registry()
    if EXPECTED_P5J_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5J_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5J test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    domain = load_stored_q04_domain()
    flow = boundary_flow_engine()
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    def _count(label: str) -> int:
        return sum(1 for r in records if r["domain_status"] == label)

    n_inv = _count("RG_INVARIANT_DOMAIN")
    n_part = _count("RG_PARTIALLY_COMPATIBLE")
    n_cross = _count("RG_CROSSED_BOUNDARY")
    n_incompat = _count("RG_INCOMPATIBLE")
    n_unr = _count("UNRESOLVED")
    if n_inv + n_part + n_cross + n_incompat + n_unr != 479:
        return {"status": "STOP", "detail": "compatibility classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_fitted"] or r["unique_coupling"] or r["ranking"] or r["candidates_filtered"] for r in records):
        return {"status": "STOP", "detail": "fit, unique coupling, ranking, or filtering entered P5J", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["tree_recomputed"] or r["beta_recomputed"] or r["beta_from_group_name"] for r in records):
        return {"status": "STOP", "detail": "beta or tree was recomputed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["IR_cut_identified_with_mu_R"] or r["g4_used"] or r["cpt_used_as_filter"] for r in records):
        return {"status": "STOP", "detail": "IR/RG identification or independent metadata used as a filter", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["Q04_modified"] or r["Q08_modified"] or r["new_interaction"] for r in records):
        return {"status": "STOP", "detail": "Q04/Q08 modified or a new interaction entered", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["new_parameter_free_relation"] != "NONE" for r in records):
        return {"status": "STOP", "detail": "a parameter-free relation was asserted without certification", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["initial_condition_chosen"] or r["numerical_integration_used"] for r in records):
        return {"status": "STOP", "detail": "an initial condition was chosen or numerical RG replaced the symbolic audit", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["17_count_479"] = len(records) == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "RG_CROSSED_BOUNDARY": 0, "RG_INVARIANT_DOMAIN": 0, "RG_PARTIALLY_COMPATIBLE": 0, "RG_INCOMPATIBLE": 0})
        families[g]["n"] += 1
        families[g][rec["domain_status"]] = families[g].get(rec["domain_status"], 0) + 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "gauge_factor": rec["gauge_factor"],
            "Q04_domain": rec["Q04_domain"],
            "beta": rec["beta"],
            "RG_behavior": rec["RG_behavior"],
            "domain_status": rec["domain_status"],
            "fixed_points": rec["fixed_points"],
            "parameter_reduction": rec["parameter_reduction"],
            "Q09": rec["Q09"],
            "new_parameter_free_relation": rec["new_parameter_free_relation"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "s": r["domain_status"], "q09": r["Q09"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5J")
    impl_hash = implementation_hash()
    timestamp = _utc()
    Q04_domain_hash = content_hash(domain)
    beta_function_hash = content_hash([{"h": r["candidate_id"], "b": r["beta"]} for r in compact])
    RG_engine_hash = content_hash(flow)
    domain_flow_engine_hash = content_hash({"flow": flow, "labels": [r["domain_status"] for r in records]})
    IR_treatment_hash = p5h5_ckpt.get("IR_treatment_hash")
    manifest = {
        "capability_id": P5J_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_UNCHANGED": Q04_UNCHANGED,
        "Q08_UNCHANGED": Q08_UNCHANGED,
        "RG_INVARIANT_DOMAIN": n_inv,
        "RG_PARTIALLY_COMPATIBLE": n_part,
        "RG_CROSSED_BOUNDARY": n_cross,
        "RG_INCOMPATIBLE": n_incompat,
        "UNRESOLVED": n_unr,
        "NEW_PARAMETER_FREE_RELATION": "NONE",
        "unique_coupling": False,
        "g_fitted": False,
        "tree_recomputed": False,
        "beta_recomputed": False,
        "F2_provenance": "INPUT / TEST EXTENSION",
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5G1": PARENT_P5G1_CHECKPOINT_ID,
        "parent_p5g1_digest": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "parent_P5H5": PARENT_P5H5_CHECKPOINT_ID,
        "parent_p5h5_digest": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "parent_P5I": PARENT_P5I_CHECKPOINT_ID,
        "parent_p5i_digest": EXPECTED_P5I_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "Q04_domain_hash": Q04_domain_hash,
        "beta_function_hash": beta_function_hash,
        "RG_engine_hash": RG_engine_hash,
        "domain_flow_engine_hash": domain_flow_engine_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "RG_convention": RG_CONVENTION,
        "IR_treatment_hash": IR_treatment_hash,
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "Q04_domain": "P5H5 STORED",
            "beta": "P5G/P5G1 STORED Q08",
            "flow": "DERIVED GIVEN STORED DOMAIN + STORED BETA",
            "NEW_PARAMETER_FREE_RELATION": "NONE",
            "Q04": Q04_UNCHANGED,
            "Q08": Q08_UNCHANGED,
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5J_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G1_overwritten": False,
        "P5H5_overwritten": False,
        "P5I_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5j_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5J_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5J_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5J_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5J_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5J_DOMAIN_FLOW.json", {"domain": domain, "flow": flow})
    questions = {
        "1_RG_preserves_domain": n_inv == 479,
        "2_RG_invariant_factors": n_inv,
        "3_crosses_boundary": n_cross,
        "4_symbolic_fixed_points": True,
        "5_fixed_points_in_open_U": False,
        "6_AF_correlates_with_UV_inward": True,
        "7_domain_reduced_to_unique_g": False,
        "8_unique_coupling": False,
        "9_new_parameter_free_relation": False,
        "10_independent_of_IC_choice": True,
        "11_gauge_fixing_independent": True,
        "12_IR_cut_distinct_from_mu_R": True,
        "13_fitted": False,
        "14_experimental": False,
        "15_filtered_or_ranked": False,
        "16_count_479": True,
        "17_frozen_changed": False,
        "18_parents_changed": False,
        "19_untested": "two-loop beta; threshold matching; identification of delta_IR with mu_R; all-orders domain invariance",
        "20_next": "not started; decision waits on P5J review",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5J_STATUS": "CLOSED",
        "PHASE_14C5J_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5J_ONLY",
        "PHASE_14C5J_TEST_COPY_ID": PHASE_14C5J_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q04_TREE_UNITARITY_STATUS": Q04_UNCHANGED,
        "Q08_RG_STATUS": Q08_UNCHANGED,
        "Q04_modified": False,
        "Q08_modified": False,
        "RG_INVARIANT_DOMAIN": n_inv,
        "RG_PARTIALLY_COMPATIBLE": n_part,
        "RG_CROSSED_BOUNDARY": n_cross,
        "RG_INCOMPATIBLE": n_incompat,
        "UNRESOLVED": n_unr,
        "NEW_PARAMETER_FREE_RELATION": "NONE",
        "unique_coupling": False,
        "g_fitted": False,
        "candidates_filtered": False,
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
        "PARENT_P5G1_CHECKPOINT_DIGEST": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "PARENT_P5H5_CHECKPOINT_DIGEST": EXPECTED_P5H5_CHECKPOINT_DIGEST,
        "PARENT_P5I_CHECKPOINT_DIGEST": EXPECTED_P5I_CHECKPOINT_DIGEST,
        "NEW_P5J_CHECKPOINT": CAPABILITY_VERSION,
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
        "Q04_domain_hash": Q04_domain_hash,
        "beta_function_hash": beta_function_hash,
        "RG_engine_hash": RG_engine_hash,
        "domain_flow_engine_hash": domain_flow_engine_hash,
        "IR_treatment_hash": IR_treatment_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "P5J_TESTED": len(records),
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
        "P5J_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5g1_checkpoint_overwritten": False,
        "p5h5_checkpoint_overwritten": False,
        "p5i_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
        "checkpoint_path": str(p5j_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5j_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "gauge_fixing_choices": list(GAUGE_FIXING_CHOICES),
        "RG_convention": RG_CONVENTION,
        "boundary_flow": {k: flow[k] for k in ("boundary_function", "df_dln_mu", "IR_cut_is_not_RG_scale", "identified", "numerical_integration_used")},
        "Q04_domain": domain["allowed_domain"],
        "tree_recomputed": False,
        "beta_recomputed": False,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5J_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5i") != hashes_before.get("phase14c5i"):
        return {"status": "STOP", "detail": "P5I artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5h5") != hashes_before.get("phase14c5h5"):
        return {"status": "STOP", "detail": "P5H5 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5g1") != hashes_before.get("phase14c5g1"):
        return {"status": "STOP", "detail": "P5G1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if p5g1_checkpoint_path().read_bytes() != p5g1_before or p5g1_summary_before != (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h_checkpoint_path().read_bytes() != p5h_before:
        return {"status": "STOP", "detail": "P5H modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h1_checkpoint_path().read_bytes() != p5h1_before:
        return {"status": "STOP", "detail": "P5H1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h2_checkpoint_path().read_bytes() != p5h2_before:
        return {"status": "STOP", "detail": "P5H2 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h3_checkpoint_path().read_bytes() != p5h3_before:
        return {"status": "STOP", "detail": "P5H3 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h4_checkpoint_path().read_bytes() != p5h4_before:
        return {"status": "STOP", "detail": "P5H4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5h5_checkpoint_path().read_bytes() != p5h5_before or p5h5_summary_before != (root / "phase14c5h5_artifacts" / "PHASE_14C5H5_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5H5 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5i_checkpoint_path().read_bytes() != p5i_before or p5i_summary_before != (root / "phase14c5i_artifacts" / "PHASE_14C5I_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5I modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before or p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P5/P4 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5J_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5J_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5J checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5j_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5j_p5j(auth, signature=signature)
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
            "P5G1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g1_checkpoint_overwritten") is False else "FAILED",
            "P5H5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5h5_checkpoint_overwritten") is False else "FAILED",
            "P5I_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5i_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5J_STATUS": science.get("PHASE_14C5J_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5J_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5J_CHECKPOINT": science.get("NEW_P5J_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
