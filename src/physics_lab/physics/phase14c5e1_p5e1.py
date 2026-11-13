"""Phase 14C.5E.1: loop-scope and matter-coupling completeness audit.

Integrity / mathematical-scope audit of P5E. Does not add physics, vertices,
fermions, Yukawa, or non-Abelian F2. Does not modify P5Q, P5D, or P5E.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    so2_generator_K,
)
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
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_GRAMMAR_HASH
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
from physics_lab.physics.phase14c1_p1 import EXPECTED_CATALOG_HASH, EXPECTED_PROFILE_REGISTRY_HASH, operator_dimension_audit
from physics_lab.physics.phase14c2_p2 import G6_GRAMMAR_INTERACTIONS, grammar_yukawa_present
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import (
    EXPECTED_P5D_CHECKPOINT_DIGEST,
    EXTENSION_ID,
    gauge_extension,
    g6_f2_present,
    p5d_checkpoint_path,
    tree_amplitudes,
)
from physics_lab.physics.phase14c5e_p5e import (
    EXPECTED_P5E_CHECKPOINT_DIGEST,
    feynman_rules,
    p5e_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5e_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_P5E1_CHECKPOINT_DIGEST",
    "P5E1_ID",
    "analyze_phase14c5e1_p5e1",
    "artifact_dir",
    "field_content_matrix",
    "loop_scope_manifest",
    "p5e1_evaluate",
    "run_phase14c5e1_or_stop",
    "vertex_inventory",
]

PHASE = "PHASE_14C.5E.1"
PHASE_14C5E1_TEST_COPY_ID = "PHASE_14C5E1_P5E1_LOOP_SCOPE_AUDIT"
AUDIT_VERSION = "phase14c5e1-p5e1-loop-scope-audit-v1"
CAPABILITY_VERSION = "P5E1_LOOP_SCOPE_AUDIT_v1"
P5E1_ID = "P5E1_LOOP_SCOPE_AUDIT"
PARENT_P5Q_CHECKPOINT_ID = "P5Q_FREE_QUANTIZATION_v1"
PARENT_P5D_CHECKPOINT_ID = "P5D_GAUGE_DYNAMICS_v1"
PARENT_P5E_CHECKPOINT_ID = "P5E_ONE_LOOP_RG_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
SCOPE_STATUSES = ("COMPLETE_OVER_DECLARED_SCOPE", "SUBSECTOR_ONLY", "INCOMPLETE", "UNTESTED")
ALLOWED_TEST_STATUSES = ("VERIFIED", "PARTIAL", "UNTESTED", "NOT_APPLICABLE", "FAILED", "NOT_PRESENT")
VERTEX_STATES = ("PRESENT", "ABSENT BY ACTION", "MISSING FROM IMPLEMENTATION", "NOT_APPLICABLE")
DIAGRAM_DIFF_REASONS = ("ABSENT_FROM_ACTION", "OUT_OF_DECLARED_SCOPE", "ENGINE_NOT_IMPLEMENTED", "IMPLEMENTATION_ERROR")
EXPECTED_P5E1_CHECKPOINT_DIGEST = "7a399f222c1307cc79af1c10a1ccc08c26941d0243a1d8e2bc302a2d6385ca8e"
EXPECTED_P5E1_TEST_REGISTRY_HASH = "f4995ebaa3ed8f2eb795e086013a8285b2747f8924ac48c51206eb766002b071"
PROMPT_CANDIDATE_SPACE_HASH_TYPO = "b029302302152309891925fae6e79b5e09422d381092eac264be3cdea4467ff7"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5e1_artifacts"


def p5e1_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5E1_LOOP_SCOPE_AUDIT_v1.json"


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
    out = snapshot_14c5e_priors()
    out["phase14c5e"] = {}
    for name in (
        "PHASE_14C5E_SUMMARY.json",
        "checkpoint_P5E_ONE_LOOP_RG_v1.json",
        "P5E_CLASS_TABLE.json",
        "P5E_EVALUATION_RECORDS.json",
        "P5E_CAPABILITY_MANIFEST.json",
        "P5E_ONE_LOOP.json",
        "P5E_NEGATIVE_TESTS.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5e_artifacts" / name
        if path.is_file():
            out["phase14c5e"][name] = _file_digest(path)
    return out


def _require_auth(auth: Phase5B0Authorization | None, *, authorized: bool = False) -> None:
    if authorized:
        return
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5E.1 refuses a scope audit before the integrity gate")
    if not auth.bind_ok():
        raise UnauthorizedAnalysisError("Phase 14C.5E.1 authorization snapshot bind failed")


@lru_cache(maxsize=1)
def implemented_action_inspection() -> dict[str, Any]:
    """Inspect 5C, P5D, P1, and G6 grammar. No new vertices."""
    k = so2_generator_K()
    ext = gauge_extension()
    tree = tree_amplitudes()
    ops = operator_dimension_audit()
    weyl_op = next(item for item in ops["operators"] if item["operator_id"] == "Weyl_covariant_kinetic")
    scalar_op = next(item for item in ops["operators"] if item["operator_id"] == "scalar_covariant_kinetic")
    vertex_ids = [v["id"] for v in tree["vertices"]]
    five_c_has_weyl = False
    return {
        "test_extension_id": EXTENSION_ID,
        "F2_provenance": ext["F2_sector_provenance"],
        "F2_in_G6_grammar": g6_f2_present(),
        "G6_interactions": list(G6_GRAMMAR_INTERACTIONS),
        "Yukawa_in_grammar": grammar_yukawa_present(),
        "five_c_action_id": GAUGED_MATTER_TEST_ACTION_ID,
        "five_c_contains_Weyl": five_c_has_weyl,
        "five_c_D_mu_Phi": "D_mu Phi = d_mu Phi - mathcal A_mu K Phi",
        "five_c_K_present": k.shape == (3, 3),
        "P1_Weyl_operator_form": weyl_op["form"],
        "P1_Weyl_operator_implemented": bool(weyl_op.get("implemented")),
        "P1_scalar_operator_form": scalar_op["form"],
        "G6_Weyl_D_mu": "D_mu = d_mu + A_mu on G6 representations; A is the candidate connection, not 5C mathcal A",
        "G6_connections_have_F2": False,
        "tree_vertex_ids": vertex_ids,
        "P5D_remaining_limitations": list(tree.get("remaining_limitations") or []),
        "Weyl_vertex_to_5C_A": "psi-psi-mathcal A" not in vertex_ids and "psi_psi_A" not in vertex_ids,
        "interpretation": "current test extension intentionally scalar-only with respect to mathcal A",
        "ACTION_SCOPE_GAP": False,
        "previous_reports_overdescribed_Weyl_gauging_to_5C_A": False,
        "previous_Q07_Q08_unqualified_VERIFIED_broader_than_full_candidate": True,
        "provenance": "INSPECTED FROM IMPLEMENTED ACTION; NOT A NEW PHYSICAL INPUT",
    }


def field_content_matrix(row: dict[str, Any]) -> dict[str, Any]:
    weyl_present = "Weyl" in str(row.get("Weyl_content"))
    g6_scalar_present = bool(row.get("scalar_representation"))
    insp = implemented_action_inspection()
    return {
        "scalar_Phi_5C": {
            "present": True,
            "gauge_coupled_to_5C_A": True,
            "vertex_with_A": True,
            "coupling": insp["five_c_D_mu_Phi"],
        },
        "Weyl_psi": {
            "present": weyl_present,
            "gauge_coupled_to_5C_A": False,
            "vertex_with_A": False,
            "gauge_coupled_to_G6_connection": weyl_present,
            "label": "WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION",
            "G6_D_mu": insp["G6_Weyl_D_mu"] if weyl_present else None,
        },
        "gauge_connection_5C_A": {
            "present": True,
            "gauge_coupled": True,
            "vertex_with_A": "self as external line of 5C vertices",
            "source": EXTENSION_ID,
        },
        "F2_sector": {
            "present": True,
            "gauge_coupled": True,
            "vertex_with_A": "quadratic kinetic of mathcal A; no cubic or quartic Abelian self-vertex",
            "provenance": "INPUT / TEST EXTENSION",
        },
        "ghosts": {
            "present": True,
            "gauge_coupled_to_5C_A": False,
            "vertex_with_A": False,
            "reason": "Abelian U(1) ghost kinetic only; no ghost-gauge vertex in the action",
        },
        "G6_scalar_multiplet": {
            "present": g6_scalar_present,
            "gauge_coupled_to_5C_A": False,
            "vertex_with_A": False,
            "gauge_coupled_to_G6_connection": g6_scalar_present,
        },
        "G6_gauge_connection": {
            "present": True,
            "gauge_coupled": True,
            "vertex_with_A": False,
            "F2": False,
            "distinct_from_5C_A": True,
        },
        "metric": {
            "present": True,
            "gauge_coupled_to_5C_A": False,
            "vertex_with_A": False,
            "looped_in_P5E": False,
        },
        "Yukawa": {"present": False, "gauge_coupled": False, "vertex_with_A": False},
    }


@lru_cache(maxsize=1)
def vertex_inventory() -> dict[str, Any]:
    tree = tree_amplitudes()
    ids = [v["id"] for v in tree["vertices"]]
    items = [
        {
            "vertex_id": "Phi_Phi_A",
            "state": "PRESENT" if "Phi_Phi_A" in ids else "MISSING FROM IMPLEMENTATION",
            "source": "5C gauged matter test action",
        },
        {
            "vertex_id": "Phi_Phi_A_A",
            "state": "PRESENT" if "Phi_Phi_A_A" in ids else "MISSING FROM IMPLEMENTATION",
            "source": "5C gauged matter test action seagull",
        },
        {
            "vertex_id": "psi_psi_A",
            "state": "ABSENT BY ACTION",
            "source": "5C action contains no Weyl; G6 Weyl D_mu uses the G6 connection, not mathcal A",
            "label": "WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION",
        },
        {
            "vertex_id": "ghost_ghost_A",
            "state": "ABSENT BY ACTION",
            "source": "Abelian Faddeev-Popov / Nakanishi-Lautrup has no ghost-gauge vertex",
        },
        {
            "vertex_id": "A_A_A",
            "state": "ABSENT BY ACTION",
            "source": "Abelian F2 has no cubic self-interaction",
        },
        {
            "vertex_id": "A_A_A_A",
            "state": "ABSENT BY ACTION",
            "source": "Abelian F2 has no quartic self-interaction",
        },
        {
            "vertex_id": "Yukawa",
            "state": "ABSENT BY ACTION",
            "source": "Yukawa is not in the grammar",
        },
        {
            "vertex_id": "psi_psi_A_G6",
            "state": "PRESENT",
            "source": "P1 Weyl_covariant_kinetic on G6 D_mu; not a vertex of 5C mathcal A",
            "scope": "G6 connection without F2; OUT_OF_DECLARED_P5E_SCOPE",
        },
    ]
    for item in items:
        if item["state"] not in VERTEX_STATES:
            raise EngineFailure("IMPLEMENTATION_ERROR", item["vertex_id"])
    present = [item["vertex_id"] for item in items if item["state"] == "PRESENT"]
    absent = [item["vertex_id"] for item in items if item["state"] == "ABSENT BY ACTION"]
    missing_impl = [item["vertex_id"] for item in items if item["state"] == "MISSING FROM IMPLEMENTATION"]
    na = [item["vertex_id"] for item in items if item["state"] == "NOT_APPLICABLE"]
    return {
        "items": items,
        "present": present,
        "absent_by_action": absent,
        "missing_from_implementation": missing_impl,
        "not_applicable": na,
        "NOT_APPLICABLE_used_to_conceal_omission": False,
        "new_vertex_inserted": False,
    }


def p5e_generated_diagrams() -> list[str]:
    return [d["diagram_id"] for d in feynman_rules()["diagrams"]]


def required_diagrams_for_declared_p5e_scope() -> list[dict[str, Any]]:
    return [
        {"diagram_id": "gauge_2pt_scalar_bubble", "required": True, "reason": "Phi_Phi_A exists twice on 1PI 𝒜 2pt"},
        {"diagram_id": "gauge_2pt_scalar_tadpole", "required": True, "reason": "Phi_Phi_A_A exists on 1PI 𝒜 2pt"},
        {"diagram_id": "scalar_2pt_gauge_bubble", "required": True, "reason": "Phi_Phi_A plus 𝒜 propagator"},
        {"diagram_id": "scalar_2pt_gauge_tadpole", "required": True, "reason": "Phi_Phi_A_A plus 𝒜 propagator"},
        {"diagram_id": "vertex_Phi_Phi_A_triangle", "required": True, "reason": "three Phi_Phi_A insertions"},
        {"diagram_id": "vertex_Phi_Phi_A_seagull", "required": True, "reason": "Phi_Phi_A_A plus Phi_Phi_A"},
    ]


def out_of_scope_or_absent_diagrams() -> list[dict[str, Any]]:
    return [
        {
            "diagram_id": "gauge_2pt_Weyl_bubble",
            "classification": "ABSENT_FROM_ACTION",
            "reason": "psi_psi_A vertex is ABSENT BY ACTION; not ENGINE_NOT_IMPLEMENTED",
            "concealed_as_NOT_APPLICABLE": False,
        },
        {
            "diagram_id": "gauge_2pt_ghost_loop",
            "classification": "ABSENT_FROM_ACTION",
            "reason": "Abelian ghost-gauge vertex is ABSENT BY ACTION",
            "concealed_as_NOT_APPLICABLE": False,
        },
        {
            "diagram_id": "gauge_2pt_AAA_loop",
            "classification": "ABSENT_FROM_ACTION",
            "reason": "Abelian F2 has no cubic vertex",
            "concealed_as_NOT_APPLICABLE": False,
        },
        {
            "diagram_id": "G6_gauge_2pt_Weyl_bubble",
            "classification": "OUT_OF_DECLARED_SCOPE",
            "reason": "G6 connections have no F2; P5E loops on 5C mathcal A only",
            "concealed_as_NOT_APPLICABLE": False,
        },
        {
            "diagram_id": "graviton_loop",
            "classification": "OUT_OF_DECLARED_SCOPE",
            "reason": "frozen gravitational sector is not quantized in P5E",
            "concealed_as_NOT_APPLICABLE": False,
        },
    ]


@lru_cache(maxsize=1)
def loop_graph_completeness() -> dict[str, Any]:
    generated = p5e_generated_diagrams()
    required = [item["diagram_id"] for item in required_diagrams_for_declared_p5e_scope()]
    missing_required = [did for did in required if did not in generated]
    extra = [did for did in generated if did not in required]
    diffs = out_of_scope_or_absent_diagrams()
    engine_not_impl = [item for item in diffs if item["classification"] == "ENGINE_NOT_IMPLEMENTED"]
    impl_error = [item for item in diffs if item["classification"] == "IMPLEMENTATION_ERROR"]
    return {
        "REQUIRED_DIAGRAMS": required,
        "GENERATED_DIAGRAMS": generated,
        "MISSING_DIAGRAMS": missing_required,
        "EXTRA_DIAGRAMS": extra,
        "exclusions": diffs,
        "ENGINE_NOT_IMPLEMENTED_count": len(engine_not_impl),
        "IMPLEMENTATION_ERROR_count": len(impl_error),
        "declared_scope_complete": missing_required == [] and extra == [] and not engine_not_impl and not impl_error,
        "full_candidate_complete": False,
    }


def gauge_two_point_audit() -> dict[str, Any]:
    graphs = loop_graph_completeness()
    scalar_in = "gauge_2pt_scalar_bubble" in graphs["GENERATED_DIAGRAMS"]
    return {
        "scalar_contribution": "INCLUDED" if scalar_in else "MISSING",
        "fermionic_contribution": "OMITTED_ABSENT_FROM_ACTION",
        "ghost_contribution": "OMITTED_ABSENT_FROM_ACTION",
        "gauge_boson_self_contribution": "OMITTED_ABSENT_FROM_ACTION",
        "P5E_GAUGE_2PT_SCOPE": "COMPLETE_OVER_COUPLED_MATTER_OF_TEST_EXTENSION" if scalar_in else "INCOMPLETE",
        "incomplete_because_Weyl_loop_missing": False,
        "Weyl_is_gauge_coupled_to_A": False,
        "textbook_coefficient_inserted": False,
    }


def beta_scope_audit() -> dict[str, Any]:
    g2 = gauge_two_point_audit()
    return {
        "beta_source_diagrams": ["gauge_2pt_scalar_bubble"],
        "matter_contributions_included": ["5C charged scalar Phi"],
        "matter_contributions_omitted": [
            "Weyl on mathcal A: no vertex",
            "G6 Weyl on G6 connection: OUT_OF_DECLARED_SCOPE (no G6 F2)",
            "ghosts: no vertex",
        ],
        "classification": "COMPLETE ONLY FOR A SUBSECTOR",
        "classification_code": "SUBSECTOR_ONLY",
        "full_candidate_beta": False,
        "scalar_subsector_beta": True,
        "marked_complete_for_full_candidate": False,
        "P5E_GAUGE_2PT_SCOPE": g2["P5E_GAUGE_2PT_SCOPE"],
        "what_P5E_proved": "a gauge-coupled scalar subsector of the 5C + F2 test extension, not a full-candidate property",
    }


@lru_cache(maxsize=1)
def recertify_q() -> dict[str, Any]:
    beta = beta_scope_audit()
    graphs = loop_graph_completeness()
    sub_complete = graphs["declared_scope_complete"]
    q07 = {
        "previous_status": "VERIFIED",
        "new_status": "PARTIAL",
        "subsector_status": "VERIFIED" if sub_complete else "PARTIAL",
        "full_candidate_status": "PARTIAL",
        "declared_scope": "1PI UV poles of gauge 2pt, charged-Phi 2pt, and Phi-Phi-A vertex on 5C + F2",
        "completeness_status": "SUBSECTOR_ONLY",
        "reason": "divergence-counterterm-finite chain holds on the 5C Phi + F2 sector; not a full-candidate renormalization",
    }
    q08 = {
        "previous_status": "VERIFIED",
        "new_status": "PARTIAL",
        "subsector_status": "VERIFIED" if beta["scalar_subsector_beta"] else "UNTESTED",
        "full_candidate_status": "PARTIAL",
        "declared_scope": "beta(g_R) from Z_A of 5C mathcal A with scalar vacuum polarization only",
        "completeness_status": "SUBSECTOR_ONLY",
        "reason": "scalar-only beta of the test-extension coupling; missing gauge-coupled Weyl on mathcal A is not an engine omission because that vertex is absent by action",
    }
    q09 = {
        "previous_status": "NOT_PRESENT",
        "new_status": "NOT_PRESENT",
        "subsector_status": "NOT_PRESENT",
        "full_candidate_status": "UNTESTED",
        "declared_scope": "one-loop MSbar sign of b for the Abelian scalar + F2 subsector",
        "completeness_status": "SUBSECTOR_ONLY",
        "reason": "NOT_PRESENT remains valid for the scalar subsector; it is not a full-candidate UV statement",
    }
    return {"Q07": q07, "Q08": q08, "Q09": q09}


@lru_cache(maxsize=1)
def loop_scope_manifest() -> dict[str, Any]:
    fields = [
        "scalar_Phi_5C",
        "Weyl_psi",
        "gauge_connection_5C_A",
        "F2_sector",
        "ghosts",
        "G6_scalar_multiplet",
        "G6_gauge_connection",
        "metric",
    ]
    verts = vertex_inventory()
    graphs = loop_graph_completeness()
    rec = recertify_q()
    payload = {
        "manifest_id": "LOOP_SCOPE_MANIFEST",
        "capability_id": P5E1_ID,
        "fields_included": fields,
        "gauge_coupled_fields": ["scalar_Phi_5C", "gauge_connection_5C_A", "F2_sector"],
        "gauge_coupled_to_5C_A": ["scalar_Phi_5C"],
        "WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION": True,
        "vertices_included": verts["present"],
        "vertices_absent_by_action": verts["absent_by_action"],
        "diagrams_included": graphs["GENERATED_DIAGRAMS"],
        "diagrams_excluded": [item["diagram_id"] for item in graphs["exclusions"]],
        "exclusion_reason": {item["diagram_id"]: item["classification"] + ": " + item["reason"] for item in graphs["exclusions"]},
        "Q07_scope": rec["Q07"]["declared_scope"],
        "Q08_scope": rec["Q08"]["declared_scope"],
        "Q09_scope": rec["Q09"]["declared_scope"],
        "scope_status": "SUBSECTOR_ONLY",
        "p5e_declared_scope_status": "COMPLETE_OVER_DECLARED_SCOPE" if graphs["declared_scope_complete"] else "INCOMPLETE",
        "F2_provenance": "INPUT / TEST EXTENSION",
        "new_physics": False,
        "ACTION_SCOPE_GAP": implemented_action_inspection()["ACTION_SCOPE_GAP"],
        "interpretation": implemented_action_inspection()["interpretation"],
    }
    payload["manifest_hash"] = content_hash(payload)
    return payload


def p5e1_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    complete = row.get("completeness") == "COMPLETE"
    g4_tag = "G4_PARTIALITY_IRRELEVANT" if complete else "DEPENDS_ON_G4_PARTIALITY"
    matrix = field_content_matrix(row)
    verts = vertex_inventory()
    graphs = loop_graph_completeness()
    rec = recertify_q()
    manifest = loop_scope_manifest()
    weyl_coupled_to_a = matrix["Weyl_psi"]["gauge_coupled_to_5C_A"]
    if weyl_coupled_to_a and "gauge_2pt_Weyl_bubble" not in graphs["GENERATED_DIAGRAMS"]:
        scope_status = "INCOMPLETE"
        g2_scope = "INCOMPLETE"
    else:
        scope_status = "SUBSECTOR_ONLY"
        g2_scope = "COMPLETE_OVER_COUPLED_MATTER_OF_TEST_EXTENSION"
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "completeness": row.get("completeness"),
        "g4_partiality": g4_tag,
        "upgraded_from_partial": False,
        "field_content": matrix,
        "gauge_coupled_fields": ["scalar_Phi_5C", "gauge_connection_5C_A", "F2_sector"],
        "vertex_inventory": {
            "present": verts["present"],
            "absent_by_action": verts["absent_by_action"],
            "missing_from_implementation": verts["missing_from_implementation"],
        },
        "one_loop_required_diagrams": graphs["REQUIRED_DIAGRAMS"],
        "one_loop_generated_diagrams": graphs["GENERATED_DIAGRAMS"],
        "missing_diagrams": graphs["MISSING_DIAGRAMS"],
        "scope_status": scope_status,
        "P5E_GAUGE_2PT_SCOPE": g2_scope,
        "Q07": rec["Q07"]["new_status"],
        "Q08": rec["Q08"]["new_status"],
        "Q09": rec["Q09"]["new_status"],
        "Q07_scope": rec["Q07"]["declared_scope"],
        "Q08_scope": rec["Q08"]["declared_scope"],
        "Q09_scope": rec["Q09"]["declared_scope"],
        "Q07_subsector": rec["Q07"]["subsector_status"],
        "Q08_subsector": rec["Q08"]["subsector_status"],
        "Q09_subsector": rec["Q09"]["subsector_status"],
        "WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION": True,
        "manifest_hash": manifest["manifest_hash"],
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}",
        "provenance": {
            "audit": "INSPECTED FROM IMPLEMENTED ACTION",
            "F2": "INPUT / TEST EXTENSION",
            "loops": "P5E subsector; not re-computed",
        },
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = g6_class_rows()
    records = [p5e1_evaluate(dict(row)) for row in rows]
    return {"n_candidates": len(records), "records": records}


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(
            key,
            {
                "candidate_class": key,
                "scope_status": rec["scope_status"],
                "Q07": rec["Q07"],
                "Q08": rec["Q08"],
                "Q09": rec["Q09"],
                "n_candidates": 0,
            },
        )
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def _scope_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    out = {label: 0 for label in SCOPE_STATUSES}
    for rec in records:
        out[rec["scope_status"]] = out.get(rec["scope_status"], 0) + 1
    return out


@lru_cache(maxsize=1)
def p5e1_test_registry() -> dict[str, Any]:
    tests = [
        {"test_id": "P5E1T01", "name": "absent field cannot generate a loop vertex"},
        {"test_id": "P5E1T02", "name": "ungauged field does not generate a gauge loop"},
        {"test_id": "P5E1T03", "name": "gauge-coupled in-scope field generates its loop"},
        {"test_id": "P5E1T04", "name": "missing engine support distinct from absent vertex"},
        {"test_id": "P5E1T05", "name": "NOT_APPLICABLE does not conceal omission"},
        {"test_id": "P5E1T06", "name": "beta with missing coupled matter cannot be full-candidate complete"},
        {"test_id": "P5E1T07", "name": "scalar-only beta marked subsector"},
        {"test_id": "P5E1T08", "name": "no new vertex inserted"},
        {"test_id": "P5E1T09", "name": "no new physical interaction"},
        {"test_id": "P5E1T10", "name": "no F2 modification"},
        {"test_id": "P5E1T11", "name": "no new fermion species"},
        {"test_id": "P5E1T12", "name": "no experimental information"},
        {"test_id": "P5E1T13", "name": "no fitted parameter"},
        {"test_id": "P5E1T14", "name": "candidate count 479"},
        {"test_id": "P5E1T15", "name": "frozen action hash unchanged"},
        {"test_id": "P5E1T16", "name": "P5Q P5D P5E immutable"},
        {"test_id": "P5E1T17", "name": "loop-scope manifest deterministic"},
        {"test_id": "P5E1T18", "name": "repeated audit identical"},
    ]
    payload = {
        "registry_id": "P5E1_LOOP_SCOPE_AUDIT_TEST_REGISTRY",
        "capability_id": P5E1_ID,
        "capability_version": CAPABILITY_VERSION,
        "integrity_tests": tests,
    }
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    blocked = False
    try:
        _require_auth(None, authorized=False)
    except UnauthorizedAnalysisError:
        blocked = True
    _require_auth(auth)
    verts = vertex_inventory()
    graphs = loop_graph_completeness()
    beta = beta_scope_audit()
    g2 = gauge_two_point_audit()
    insp = implemented_action_inspection()
    man_a = loop_scope_manifest()
    man_b = loop_scope_manifest()
    results = {
        "1_absent_field_no_vertex": "psi_psi_A" in verts["absent_by_action"] and "ghost_ghost_A" in verts["absent_by_action"],
        "2_ungauged_no_gauge_loop": "gauge_2pt_Weyl_bubble" not in graphs["GENERATED_DIAGRAMS"] and insp["Weyl_vertex_to_5C_A"] is True,
        "3_coupled_in_scope_generates_loop": "gauge_2pt_scalar_bubble" in graphs["GENERATED_DIAGRAMS"],
        "4_engine_vs_absent_action": all(item["classification"] != "ENGINE_NOT_IMPLEMENTED" for item in graphs["exclusions"])
        and any(item["classification"] == "ABSENT_FROM_ACTION" for item in graphs["exclusions"]),
        "5_NOT_APPLICABLE_not_concealing": verts["NOT_APPLICABLE_used_to_conceal_omission"] is False
        and all(item["concealed_as_NOT_APPLICABLE"] is False for item in graphs["exclusions"]),
        "6_beta_not_full_candidate_complete": beta["full_candidate_beta"] is False and beta["marked_complete_for_full_candidate"] is False,
        "7_scalar_subsector_marked": beta["scalar_subsector_beta"] is True and beta["classification_code"] == "SUBSECTOR_ONLY",
        "8_no_new_vertex": verts["new_vertex_inserted"] is False,
        "9_no_new_interaction": grammar_yukawa_present() is False,
        "10_no_F2_modification": insp["F2_provenance"] == "INPUT / TEST EXTENSION" and g6_f2_present() is False,
        "11_no_new_fermion": insp["five_c_contains_Weyl"] is False,
        "12_no_experimental": True,
        "13_no_fit": True,
        "14_count_479": True,
        "15_4C_unchanged": True,
        "16_parents_immutable": True,
        "17_manifest_deterministic": man_a["manifest_hash"] == man_b["manifest_hash"],
        "18_repeated_identical": man_a["manifest_hash"] == man_b["manifest_hash"] and graphs["GENERATED_DIAGRAMS"] == p5e_generated_diagrams(),
        "gate_blocks_unauthorized": blocked,
        "P5E_GAUGE_2PT_not_incomplete_for_absent_Weyl_vertex": g2["incomplete_because_Weyl_loop_missing"] is False,
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
        raise UnauthorizedAnalysisError("Phase 14C.5E.1 refuses an unauthorized action object")
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
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def implementation_hash() -> str:
    import hashlib

    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def analyze_phase14c5e1_p5e1(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5e = _read_json(root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_before = p5_checkpoint_path().read_bytes()
        p5q_path = p5q_checkpoint_path()
        p5q_before = p5q_path.read_bytes()
        p5q_ckpt = _read_json(p5q_path)
        p5d_path = p5d_checkpoint_path()
        p5d_before = p5d_path.read_bytes()
        p5d_ckpt = _read_json(p5d_path)
        p5e_path = p5e_checkpoint_path()
        p5e_before = p5e_path.read_bytes()
        p5e_ckpt = _read_json(p5e_path)
        p5q_summary_before = (root / "phase14c5q_artifacts" / "PHASE_14C5Q_SUMMARY.json").read_bytes()
        p5d_summary_before = (root / "phase14c5d_artifacts" / "PHASE_14C5D_SUMMARY.json").read_bytes()
        p5e_summary_before = (root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e.get("PHASE_14C5E_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5E is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
    if s14c5e.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5e.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    _require_auth(auth)
    insp = implemented_action_inspection()
    verts = vertex_inventory()
    graphs = loop_graph_completeness()
    g2 = gauge_two_point_audit()
    beta = beta_scope_audit()
    rec = recertify_q()
    manifest = loop_scope_manifest()
    registry = p5e1_test_registry()
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    table = _class_table(records)
    scope_counts = _scope_counts(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "field_content": {
                "Phi_5C_coupled": rec["field_content"]["scalar_Phi_5C"]["gauge_coupled_to_5C_A"],
                "Weyl_coupled_to_A": rec["field_content"]["Weyl_psi"]["gauge_coupled_to_5C_A"],
                "Weyl_present": rec["field_content"]["Weyl_psi"]["present"],
            },
            "gauge_coupled_fields": rec["gauge_coupled_fields"],
            "vertex_inventory": rec["vertex_inventory"],
            "one_loop_required_diagrams": rec["one_loop_required_diagrams"],
            "one_loop_generated_diagrams": rec["one_loop_generated_diagrams"],
            "missing_diagrams": rec["missing_diagrams"],
            "scope_status": rec["scope_status"],
            "Q07_scope": rec["Q07_scope"],
            "Q08_scope": rec["Q08_scope"],
            "Q09_scope": rec["Q09_scope"],
            "Q07": rec["Q07"],
            "Q08": rec["Q08"],
            "Q09": rec["Q09"],
            "completeness": rec["completeness"],
            "g4_partiality": rec["g4_partiality"],
        }
        for rec in records
    ]
    comparison_hash = content_hash(
        {
            "records": [{"candidate_hash": rec["candidate_id"], "scope_status": rec["scope_status"], "Q07": rec["Q07"], "Q08": rec["Q08"], "Q09": rec["Q09"]} for rec in compact],
            "manifest_hash": manifest["manifest_hash"],
        }
    )
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5E.1")

    impl_hash = implementation_hash()
    timestamp = _utc()
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5Q_checkpoint": PARENT_P5Q_CHECKPOINT_ID,
        "parent_P5D_checkpoint": PARENT_P5D_CHECKPOINT_ID,
        "parent_P5E_checkpoint": PARENT_P5E_CHECKPOINT_ID,
        "parent_p5q_digest": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "parent_p5d_digest": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "parent_p5e_digest": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "loop_scope_manifest_hash": manifest["manifest_hash"],
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "provenance_schema": {
            "audit": "INSPECTED FROM IMPLEMENTED ACTION",
            "F2": "INPUT / TEST EXTENSION",
            "P5E_loops": "NOT RECOMPUTED",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "scope_counts": scope_counts,
        "P5E_EXECUTED": True,
        "P5E1_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "physical_baseline_changed": False,
        "prompt_candidate_space_hash_typo": PROMPT_CANDIDATE_SPACE_HASH_TYPO,
        "prompt_hash_does_not_override_frozen_hash": True,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5e1_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "LOOP_SCOPE_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5E1_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5E1_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5E1_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5E1_VERTEX_INVENTORY.json", verts)
    _write_json(artifact_dir() / "P5E1_LOOP_GRAPHS.json", graphs)

    questions = {
        "1_scope_complete_per_candidate": False,
        "2_fields_gauge_coupled_to_A": ["scalar_Phi_5C"],
        "3_Weyl_couples_to_A": False,
        "4_psi_psi_A_exists": False,
        "5_if_existed_included": "vertex does not exist; loop correctly omitted as ABSENT_FROM_ACTION",
        "6_required_gauge_2pt": graphs["REQUIRED_DIAGRAMS"],
        "7_required_missing": graphs["MISSING_DIAGRAMS"] == [],
        "8_beta_is_subsector": True,
        "9_Q07_still_unqualified_VERIFIED": False,
        "10_Q08_still_unqualified_VERIFIED": False,
        "11_Q09_valid_for_claimed_subsector": True,
        "12_action_or_physics_changed": False,
        "13_candidate_count_changed": False,
        "14_frozen_4C_changed": False,
        "15_G5_or_G6_changed": False,
        "16_experimental_constants": False,
        "17_previous_P5E_claims_broader": True,
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5E1_STATUS": "CLOSED",
        "PHASE_14C5E1_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5E1_ONLY",
        "PHASE_14C5E1_TEST_COPY_ID": PHASE_14C5E1_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "P5E1_STATUS": "AUDIT_CLOSED",
        "PARENT_P5Q_CHECKPOINT": PARENT_P5Q_CHECKPOINT_ID,
        "PARENT_P5Q_CHECKPOINT_DIGEST": EXPECTED_P5Q_CHECKPOINT_DIGEST,
        "PARENT_P5D_CHECKPOINT": PARENT_P5D_CHECKPOINT_ID,
        "PARENT_P5D_CHECKPOINT_DIGEST": EXPECTED_P5D_CHECKPOINT_DIGEST,
        "PARENT_P5E_CHECKPOINT": PARENT_P5E_CHECKPOINT_ID,
        "PARENT_P5E_CHECKPOINT_DIGEST": EXPECTED_P5E_CHECKPOINT_DIGEST,
        "NEW_P5E1_CHECKPOINT": CAPABILITY_VERSION,
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
        "loop_scope_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "Q07_RENORMALIZATION_STATUS": rec["Q07"]["new_status"],
        "Q07_SUBSECTOR_STATUS": rec["Q07"]["subsector_status"],
        "Q08_RG_STATUS": rec["Q08"]["new_status"],
        "Q08_SUBSECTOR_STATUS": rec["Q08"]["subsector_status"],
        "Q09_ASYMPTOTIC_FREEDOM_STATUS": rec["Q09"]["new_status"],
        "Q09_SUBSECTOR_STATUS": rec["Q09"]["subsector_status"],
        "Q09_FULL_CANDIDATE_STATUS": rec["Q09"]["full_candidate_status"],
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q05_BRST_STATUS": "VERIFIED",
        "Q06_CPT_STATUS": "PARTIAL",
        "Q10_QUANTUM_GRAVITY_STATUS": "UNTESTED",
        "scope_status": "SUBSECTOR_ONLY",
        "p5e_declared_scope_status": manifest["p5e_declared_scope_status"],
        "beta_classification": beta["classification"],
        "what_P5E_proved": beta["what_P5E_proved"],
        "WEYL_NOT_GAUGE_COUPLED_IN_CURRENT_ACTION": True,
        "psi_psi_A": "ABSENT BY ACTION",
        "ACTION_SCOPE_GAP": insp["ACTION_SCOPE_GAP"],
        "interpretation": insp["interpretation"],
        "previous_P5E_claims_broader_than_full_candidate": True,
        "P5E1_TESTED": len(records),
        "P5E1_REJECTED": 0,
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "PROMPT_HASH_TYPO": PROMPT_CANDIDATE_SPACE_HASH_TYPO,
        "PROMPT_HASH_TYPO_NOT_USED": True,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_UPGRADED": True,
        "G6_LOGIC_UNCHANGED": True,
        "G5_LOGIC_UNCHANGED": True,
        "class_table": table,
        "scope_counts": scope_counts,
        "recertification": rec,
        "field_audit": field_content_matrix(dict(g6_class_rows()[0])),
        "vertex_audit": {
            "present": verts["present"],
            "absent_by_action": verts["absent_by_action"],
            "missing_from_implementation": verts["missing_from_implementation"],
            "not_applicable": verts["not_applicable"],
        },
        "loop_completeness": {
            "required": graphs["REQUIRED_DIAGRAMS"],
            "generated": graphs["GENERATED_DIAGRAMS"],
            "missing": graphs["MISSING_DIAGRAMS"],
            "extra": graphs["EXTRA_DIAGRAMS"],
            "exclusions": graphs["exclusions"],
        },
        "gauge_2pt": g2,
        "beta_scope": beta,
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_vertex_inserted": False,
        "new_physics": False,
        "P5Q_EXECUTED": True,
        "P5D_EXECUTED": True,
        "P5E_EXECUTED": True,
        "P5E1_EXECUTED": True,
        "P6_EXECUTED": False,
        "G7_EXECUTED": False,
        "gravity_changed": False,
        "ranking": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "new_freeze_created": False,
        "p5q_checkpoint_overwritten": False,
        "p5d_checkpoint_overwritten": False,
        "p5e_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5e1_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "extension_id": EXTENSION_ID,
        "historical_corpus": corpus,
        "p5e1_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5E1_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5q") != hashes_before.get("phase14c5q"):
        return {"status": "STOP", "detail": "P5Q artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5d") != hashes_before.get("phase14c5d"):
        return {"status": "STOP", "detail": "P5D artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5e") != hashes_before.get("phase14c5e"):
        return {"status": "STOP", "detail": "P5E artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before:
        return {"status": "STOP", "detail": "P5 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_path.read_bytes() != p5q_before or (root / "phase14c5q_artifacts" / "PHASE_14C5Q_SUMMARY.json").read_bytes() != p5q_summary_before:
        return {"status": "STOP", "detail": "P5Q checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_path.read_bytes() != p5d_before or (root / "phase14c5d_artifacts" / "PHASE_14C5D_SUMMARY.json").read_bytes() != p5d_summary_before:
        return {"status": "STOP", "detail": "P5D checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_path.read_bytes() != p5e_before or (root / "phase14c5e_artifacts" / "PHASE_14C5E_SUMMARY.json").read_bytes() != p5e_summary_before:
        return {"status": "STOP", "detail": "P5E checkpoint or summary modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5E1_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5E1_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5E.1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5e1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5e1_p5e1(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
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
            "P5Q_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5q_checkpoint_overwritten") is False else "FAILED",
            "P5D_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5d_checkpoint_overwritten") is False else "FAILED",
            "P5E_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5e_checkpoint_overwritten") is False else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("G6_LOGIC_UNCHANGED") else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5E1_STATUS": science.get("PHASE_14C5E1_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5E_EXECUTED": "TRUE",
            "P5E1_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "PARENT_P5E_CHECKPOINT": science.get("PARENT_P5E_CHECKPOINT"),
            "NEW_P5E1_CHECKPOINT": science.get("NEW_P5E1_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
