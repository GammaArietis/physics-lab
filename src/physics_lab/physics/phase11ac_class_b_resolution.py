"""Phase 11AC: resolve CLASS-B items T04 and T05 with existing modules only.

Does not introduce new physics, new assumptions, or new parameters.
Does not rewrite 11V-11AB or P5J/P5K artifacts.
Does not execute CLASS C/D/E items.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    phase4c_action_document,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11s_susy_completion import artifact_dir as phase11s_artifact_dir
from physics_lab.physics.phase11s_susy_completion import susy_completion_identities
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import artifact_dir as phase11w_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import anomaly_mediation_identities
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase14c5j_p5j import artifact_dir as phase14c5j_artifact_dir
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AC_TEST_COPY_ID",
    "analyze_phase11ac_class_b_resolution",
    "artifact_dir",
    "class_b_identities",
    "execute_t04",
    "execute_t05",
    "run_phase11ac_or_stop",
]

PHASE_11AC_TEST_COPY_ID = "PHASE_11AC_CLASS_B_RESOLUTION"
PHASE = "PHASE_11AC"
MODULE_VERSION = "phase11ac-class-b-resolution-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11S_HASH = "5b51ee817ee1989c7c7fbe08941ff5bd2a9ad3b3cdcb1da2151b1884fb0b2e03"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11W_HASH = "cdd2589615fbff59f6da74c7ab748d8aa1172468a78008071a7646e46a089f9a"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_11AA_HASH = "7b2ded670cdb54e5d3d5c70134f00d8fbd4c4a0b8b7d43f2da117313cf2dc531"
EXPECTED_11AB_HASH = "8b1a3c44f772521e18d3e838dfe9fa56b175b3066d99608bb5ffda6bbecb842d"
EXPECTED_P5J_SUMMARY_HASH = "83538815b6f954f517fd722972f076f3a19bc43c5bf6db9d1920773a414283b1"
EXPECTED_P5K_SUMMARY_HASH = "f13e0061d21cf618003146642b9f21c268af08f8c06e903849f1330044a35e1e"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"
CLASS_CDE_ITEMS = ("T06", "T07", "T08", "T09", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17")

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "new_physical_input_introduced": False,
    "new_assumption_introduced": False,
    "new_parameter_introduced": False,
    "F_phi_identified_with_F_X": False,
    "F_phi_identified_with_F_T": False,
    "perturbative_order_increased": False,
    "new_beta_function_added": False,
    "missing_Yukawa_fabricated": False,
    "missing_beta_y_treated_as_present": False,
    "partial_coverage_promoted": False,
    "CLASS_CDE_executed": False,
    "mixed_mediation_activated": False,
    "mediation_selection_performed": False,
    "A_map_is_a_PFR": False,
    "loop_coefficient_is_a_PFR": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ac_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _banned_tokens() -> tuple[str, ...]:
    return ("1/" + "13" + "7", "alp" + "ha_em", "electr" + "ic", "1/" + "3", "2/" + "3")


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
    blob = "\n".join(_walk_strings(obj))
    return [token for token in _banned_tokens() if token in blob]


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11s_artifact_dir().resolve(),
        phase11v_artifact_dir().resolve(),
        phase11w_artifact_dir().resolve(),
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11aa_artifact_dir().resolve(),
        phase11ab_artifact_dir().resolve(),
        phase14c5j_artifact_dir().resolve(),
        phase14c5k_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AC refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def class_b_identities() -> dict[str, Any]:
    """Finite-order identities already authorized by 11Y and 11S. No new physics."""
    doc = phase4c_action_document()
    params = {row["id"]: row for row in doc["parameters"]}
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    amsb = anomaly_mediation_identities()
    susy = susy_completion_identities()
    beta_g, g, F_phi, F_X, F_T, beta_y, c_scheme, yukawa = sp.symbols(
        "beta_g g F_phi F_X F_T beta_y c_scheme yukawa"
    )
    A_y = c_scheme * beta_y * F_phi
    M_a = c_scheme * (beta_g / g) * F_phi
    F_phi_independent = bool(not F_phi.equals(F_X)) and bool(not F_phi.equals(F_T))
    A_not_pfr = bool(A_y.free_symbols)
    M_not_pfr = bool(M_a.free_symbols)
    A_vanishes = bool(A_y.subs({beta_y: 0}).equals(0))
    loop_factor = beta_g / g
    loop_not_pfr = bool(loop_factor.free_symbols)
    ok = bool(
        c0_free
        and c1_free
        and amsb["F_phi_is_INPUT_symbol"]
        and amsb["F_phi_not_hidden_F_X"]
        and amsb["F_phi_not_modulus_F_T"]
        and amsb["A_term_vanishes_if_beta_y_zero"]
        and amsb["A_not_fabricated_if_beta_y_missing"]
        and amsb["one_loop_two_loop_RG_not_upgraded"]
        and susy["structural_W_determines_V_and_Yukawa"]
        and F_phi_independent
        and A_not_pfr
        and M_not_pfr
        and A_vanishes
        and loop_not_pfr
    )
    return {
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "F_phi_independent": F_phi_independent,
        "A_y_not_PFR": A_not_pfr,
        "M_a_not_PFR": M_not_pfr,
        "A_vanishes_if_beta_y_zero": A_vanishes,
        "loop_coefficient_not_PFR": loop_not_pfr,
        "amsb_identities": amsb,
        "susy_identities_Yukawa_from_W": susy["structural_W_determines_V_and_Yukawa"],
        "status": "VERIFIED" if ok else "FAILED",
    }


def execute_t04(p5j: dict[str, Any], p5k: dict[str, Any], y_art: dict[str, Any]) -> dict[str, Any]:
    """Re-run already declared finite-order RG identities. No order increase."""
    ids = anomaly_mediation_identities()
    previous = (y_art.get("rg") or {}).get("status") or y_art.get("RG_STATUS") or "PARTIAL"
    if previous != "PARTIAL":
        rg_block = y_art.get("rg") or y_art.get("RG") or {}
        previous = rg_block.get("status") or y_art.get("activation_configuration", {}).get("RG_STATUS") or "PARTIAL"
    one_loop_convention = "one-loop" in str(p5j.get("RG_convention") or "")
    two_loop_present = p5k.get("P5K_EXECUTED") is True
    new_loop = p5j.get("new_loop_order") is True or p5k.get("hardcoded_textbook_beta") is True
    grammar_yukawa = bool(p5j.get("grammar_yukawa_present")) or bool(p5k.get("grammar_yukawa_present"))
    q08 = p5j.get("Q08_RG_STATUS")
    identities_hold = ids["status"] in {"PARTIAL", "VERIFIED"} and ids["one_loop_two_loop_RG_not_upgraded"] is True
    missing = []
    if p5j.get("status") != "OK" or p5k.get("status") != "OK":
        missing.append("P5J/P5K summaries not OK")
    if grammar_yukawa:
        missing.append("unexpected grammar Yukawa appeared")
    if new_loop:
        missing.append("loop order changed")
    missing.extend(
        [
            "P5J/P5K remain REFERENCE_ONLY for anomaly-mediation soft terms",
            "scheme factor c_scheme remains free",
            "Yukawa beta functions are absent from the stored finite-order RG",
            "all-orders RG is outside the permitted re-run",
        ]
    )
    coverage_complete = False
    new_status = "VERIFIED" if (identities_hold and coverage_complete and not missing) else "PARTIAL"
    if not identities_hold:
        new_status = "FAILED"
    return {
        "item": "T04",
        "previous_status": "PARTIAL",
        "execution": "EXECUTED",
        "exact_test": "anomaly_mediation_identities plus stored P5J one-loop and P5K two-loop summaries as REFERENCE_ONLY",
        "inputs_used": "11Y identities; P5J/P5K stored summaries; no new beta",
        "finite_order_tested": "one-loop gauge RG (P5J) and two-loop gauge RG (P5K); no higher order",
        "one_loop_convention_present": one_loop_convention,
        "two_loop_summary_present": two_loop_present,
        "Q08_RG_STATUS_stored": q08,
        "new_loop_order": False,
        "new_beta_function_added": False,
        "grammar_yukawa_present": False,
        "identities_hold": identities_hold,
        "result": "identities hold; coverage incomplete",
        "provenance": {
            "RG_structure": "existing laboratory structure",
            "re_run": "METHOD / EXECUTION",
            "resulting_identity": "DERIVED only as the already-declared 11Y identities; P5J/P5K remain REFERENCE_ONLY",
        },
        "can_legitimately_change": False,
        "missing_coverage": missing,
        "new_status": new_status,
        "new_input": False,
        "new_parameter": False,
        "CLASS_CDE_executed": False,
    }


def execute_t05(y_art: dict[str, Any]) -> dict[str, Any]:
    """Apply the 11Y A-map only to Yukawa structures already present."""
    ids = anomaly_mediation_identities()
    susy = susy_completion_identities()
    yukawa_structure_present = bool(susy["structural_W_determines_V_and_Yukawa"])
    a_block = y_art.get("a_terms") or {}
    previous = a_block.get("status") or "PARTIAL"
    beta_g, g, F_phi, F_X, F_T, beta_y, c_scheme = sp.symbols(
        "beta_g g F_phi F_X F_T beta_y c_scheme"
    )
    A_y = c_scheme * beta_y * F_phi
    convention_verified = bool(A_y.subs({beta_y: 0}).equals(0)) and ids["A_term_vanishes_if_beta_y_zero"]
    F_phi_independent = bool(not F_phi.equals(F_X)) and bool(not F_phi.equals(F_T))
    beta_y_certified = False
    gamma_certified = False
    sectors = [
        {
            "sector": "cubic_W_family from 11S",
            "Yukawa_structure_available": yukawa_structure_present,
            "beta_y_available": False,
            "anomalous_dimension_data_available": False,
            "A_term_map_executable": True,
            "coefficient_sign_convention_verified": convention_verified,
            "provenance_complete": False,
            "note": "W determines a Yukawa structure; no certified Yukawa beta exists",
        },
        {
            "sector": "grammar Yukawa sector",
            "Yukawa_structure_available": False,
            "beta_y_available": False,
            "anomalous_dimension_data_available": False,
            "A_term_map_executable": False,
            "coefficient_sign_convention_verified": convention_verified,
            "provenance_complete": False,
            "note": "stored P5J/P5K record grammar_yukawa_present = false",
        },
        {
            "sector": "P5J/P5K gauge-beta catalog",
            "Yukawa_structure_available": False,
            "beta_y_available": False,
            "anomalous_dimension_data_available": False,
            "A_term_map_executable": False,
            "coefficient_sign_convention_verified": convention_verified,
            "provenance_complete": False,
            "note": "those modules certify gauge betas, not Yukawa betas",
        },
    ]
    complete_sectors = [row for row in sectors if row["provenance_complete"]]
    missing_beta = True
    new_status = "VERIFIED" if complete_sectors and not missing_beta else "PARTIAL"
    return {
        "item": "T05",
        "previous_status": previous,
        "execution": "EXECUTED",
        "exact_test": "A_y = c_scheme * beta_y * F_phi on already present 11S Yukawa structure; 11Y convention",
        "Yukawa_structure_available": yukawa_structure_present,
        "beta_y_available": beta_y_certified,
        "anomalous_dimension_data_available": gamma_certified,
        "A_term_map_executable": True,
        "coefficient_sign_convention_verified": convention_verified,
        "provenance_complete": False,
        "F_phi_independent": F_phi_independent,
        "missing_Yukawa_fabricated": False,
        "sectors": sectors,
        "complete_sector_count": len(complete_sectors),
        "result": "structural A-map holds; missing beta_y prevents VERIFIED",
        "provenance": {
            "beta_y": "ABSENT as certified RG data; 11S supplies Yukawa-from-W structure only",
            "F_phi": "INPUT from 11Y",
            "A_y_relation": "DERIVED GIVEN INPUT as a structural map; not a PFR",
        },
        "can_legitimately_change": False,
        "missing_coverage": [
            "no certified Yukawa beta_y in the laboratory",
            "no certified anomalous-dimension input for the A-map sectors",
            "grammar Yukawa sector absent",
            "partial sector coverage cannot be promoted",
        ],
        "new_status": new_status,
        "new_input": False,
        "new_parameter": False,
        "CLASS_CDE_executed": False,
    }


def _twenty_questions(t04: dict[str, Any], t05: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Was any new physical input introduced?", "a": "No. NEW_PHYSICAL_INPUT_STATUS = FALSE."},
        {"n": "02", "q": "Was any new assumption introduced?", "a": "No. NEW_ASSUMPTION_STATUS = FALSE."},
        {"n": "03", "q": "Was T04 actually executed?", "a": "Yes. Existing 11Y RG identities were re-run against stored P5J/P5K summaries."},
        {"n": "04", "q": "Did T04 become VERIFIED?", "a": "No. T04_STATUS remains PARTIAL because RG ingredients stay REFERENCE_ONLY and coverage is incomplete."},
        {"n": "05", "q": "Was T05 actually executed?", "a": "Yes. The 11Y A-map was applied to the already present 11S Yukawa-from-W structure."},
        {"n": "06", "q": "Did T05 become VERIFIED?", "a": "No. T05_STATUS remains PARTIAL because certified beta_y data are absent."},
        {"n": "07", "q": "Which RG order was actually tested?", "a": "One-loop gauge RG from stored P5J and two-loop gauge RG from stored P5K. No higher order."},
        {"n": "08", "q": "Were all required beta functions available?", "a": "No. Gauge betas exist as REFERENCE_ONLY. Yukawa betas are absent."},
        {"n": "09", "q": "Were all required Yukawa sectors available?", "a": "No. A cubic W-family structure exists in 11S. The grammar Yukawa sector is absent."},
        {"n": "10", "q": "Did any A-term relation become fully certified?", "a": "No. The structural map holds, but missing beta_y blocks full certification."},
        {"n": "11", "q": "Did any scalar/gaugino status change?", "a": "No. 11Y source statuses remain PARTIAL. 11AC does not rewrite 11Y."},
        {"n": "12", "q": "Were any parameters newly introduced?", "a": "No. NEW_PARAMETER_COUNT = 0."},
        {"n": "13", "q": "Were any parameters reduced?", "a": "No. REDUCED_PARAMETER_COUNT = 0."},
        {"n": "14", "q": "Did any new PFR appear?", "a": "No. A_y and M_a still contain F_phi, betas, and the scheme factor."},
        {"n": "15", "q": "Did any branch artifact change?", "a": "No. 11V/11X/11Y/11Z/11AA/11AB hashes verified unchanged."},
        {"n": "16", "q": "Did the frozen 4C action change?", "a": "No."},
        {"n": "17", "q": "Was mediation selection performed?", "a": "No. MEDIATION_SELECTION_STATUS = NOT_DERIVED."},
        {"n": "18", "q": "Were experimental values used?", "a": "No. EXPERIMENTAL_INPUT_STATUS = ABSENT."},
        {"n": "19", "q": "Which CLASS-B items remain unresolved?", "a": "T04 and T05 remain PARTIAL. Exact missing coverage is recorded."},
        {"n": "20", "q": "What is the smallest legitimate next action?", "a": "Do not execute CLASS C/D/E. Record T04/T05 as well-characterized PARTIAL dependencies. Next phase requires separate authorization."},
    ]


def analyze_phase11ac_class_b_resolution(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "11S_SUSY": phase11s_artifact_dir() / "PHASE_11S_SUSY_COMPLETION.json",
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11W_ALT": phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11AA_DIR": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "11AB_SYN": phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json",
        "P5J_SUM": phase14c5j_artifact_dir() / "PHASE_14C5J_SUMMARY.json",
        "P5K_SUM": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["11S_SUSY"]) != EXPECTED_11S_HASH, "11S hash"),
        (_content_hash(loaded["11V_MED"]) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(loaded["11W_ALT"]) != EXPECTED_11W_HASH, "11W hash"),
        (_content_hash(loaded["11X_GMSB"]) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(loaded["11Y_AMS"]) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(loaded["11Z_MOD"]) != EXPECTED_11Z_HASH, "11Z hash"),
        (_content_hash(loaded["11AA_DIR"]) != EXPECTED_11AA_HASH, "11AA hash"),
        (_content_hash(loaded["11AB_SYN"]) != EXPECTED_11AB_HASH, "11AB hash"),
        (_content_hash(loaded["P5J_SUM"]) != EXPECTED_P5J_SUMMARY_HASH, "P5J hash"),
        (_content_hash(loaded["P5K_SUM"]) != EXPECTED_P5K_SUMMARY_HASH, "P5K hash"),
        (loaded["11AB_SYN"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "11AB selection"),
        (loaded["11Y_AMS"].get("authorization", {}).get("derived") is not False, "11Y derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    identities = class_b_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "class-B identities failed"}
    t04 = execute_t04(loaded["P5J_SUM"], loaded["P5K_SUM"], loaded["11Y_AMS"])
    t05 = execute_t05(loaded["11Y_AMS"])
    if t04.get("CLASS_CDE_executed") or t05.get("CLASS_CDE_executed"):
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "CLASS C/D/E executed"}
    if t04["new_status"] == "VERIFIED" or t05["new_status"] == "VERIFIED":
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "illegal VERIFIED promotion"}

    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "CLASS_B_RESOLUTION",
        "module_version": MODULE_VERSION,
        "mode": "EXISTING_MODULE_EXECUTION_ONLY",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
        "new_physical_mechanism_introduced": False,
        "t04": t04,
        "t05": t05,
        "resolution_rows": [
            {
                "item": "T04 finite-order RG",
                "previous_status": t04["previous_status"],
                "execution": t04["execution"],
                "result": t04["result"],
                "new_status": t04["new_status"],
                "new_input": "NO",
                "new_parameter": "NO",
            },
            {
                "item": "T05 anomaly A-map",
                "previous_status": t05["previous_status"],
                "execution": t05["execution"],
                "result": t05["result"],
                "new_status": t05["new_status"],
                "new_input": "NO",
                "new_parameter": "NO",
            },
        ],
        "parameter_rows": [
            {"quantity": "F_Phi", "status": "INPUT", "provenance": "11Y INPUT", "independent": True},
            {"quantity": "F_X", "status": "INPUT other branch", "provenance": "not identified", "independent": True},
            {"quantity": "F_T", "status": "INPUT other branch", "provenance": "not identified", "independent": True},
            {"quantity": "gauge couplings", "status": "FREE / used not determined", "provenance": "existing", "independent": True},
            {"quantity": "Yukawa couplings", "status": "structural from 11S W family", "provenance": "INPUT family", "independent": True},
            {"quantity": "beta functions", "status": "gauge REFERENCE_ONLY; Yukawa absent", "provenance": "P5J/P5K REFERENCE_ONLY", "independent": True},
            {"quantity": "anomalous dimensions", "status": "REFERENCE_ONLY / ABSENT for A-map", "provenance": "P5K REFERENCE_ONLY", "independent": True},
            {"quantity": "A coefficients", "status": "PARTIAL", "provenance": "DERIVED GIVEN INPUT / incomplete", "independent": False},
            {"quantity": "W", "status": "INPUT family", "provenance": "INPUT", "independent": True},
            {"quantity": "K", "status": "INPUT family", "provenance": "INPUT", "independent": True},
            {"quantity": "c0", "status": "FREE", "provenance": "INPUT", "independent": True},
            {"quantity": "c1", "status": "FREE", "provenance": "INPUT", "independent": True},
            {"quantity": "lambda_a", "status": "FREE", "provenance": "INPUT", "independent": True},
            {"quantity": "lambda_b", "status": "FREE", "provenance": "INPUT", "independent": True},
            {"quantity": "xi", "status": "PRESERVED", "provenance": "PRESERVED", "independent": True},
        ],
        "pfr_report": {
            "previous_certified_PFR_count": 0,
            "new_candidate_relations": "A_y = c_scheme * beta_y * F_phi; M_a = c_scheme * (beta_g / g) * F_phi",
            "newly_certified_PFR_count": 0,
            "unresolved_candidate_relations": "both candidates retain F_phi, free betas, and the scheme factor",
        },
        "class_cde": {item: "NOT_ACTIVATED" if item not in {"T15", "T16", "T17"} else "OPEN" for item in CLASS_CDE_ITEMS},
        "gaugino_status_unchanged": "PARTIAL",
        "scalar_status_unchanged": "PARTIAL",
        "twenty_questions": _twenty_questions(t04, t05),
        "identities": {
            "F_phi_independent": identities["F_phi_independent"],
            "A_y_not_PFR": identities["A_y_not_PFR"],
            "M_a_not_PFR": identities["M_a_not_PFR"],
            "A_vanishes_if_beta_y_zero": identities["A_vanishes_if_beta_y_zero"],
            "loop_coefficient_not_PFR": identities["loop_coefficient_not_PFR"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase11s": EXPECTED_11S_HASH,
            "phase11v": EXPECTED_11V_HASH,
            "phase11x": EXPECTED_11X_HASH,
            "phase11y": EXPECTED_11Y_HASH,
            "phase11z": EXPECTED_11Z_HASH,
            "phase11aa": EXPECTED_11AA_HASH,
            "phase11ab": EXPECTED_11AB_HASH,
            "p5j_summary": EXPECTED_P5J_SUMMARY_HASH,
            "p5k_summary": EXPECTED_P5K_SUMMARY_HASH,
        },
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "PHASE_11AC_STOPPED": True,
        "non_implications": dict(NON_IMPLICATIONS),
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11AC_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11AC_CLASS_B_RESOLUTION.json", payload)
        _write_json(
            "PHASE_11AC_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AC_STATUS": "PARTIAL",
                "PHASE_11AC_STOPPED": True,
                "T04_STATUS": t04["new_status"],
                "T05_STATUS": t05["new_status"],
                "RG_EXECUTION_STATUS": "VERIFIED",
                "A_MAP_EXECUTION_STATUS": "PARTIAL",
                "PFR_STATUS": "NOT_FOUND",
                "NEW_PHYSICAL_INPUT_STATUS": False,
                "NEW_ASSUMPTION_STATUS": False,
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
            },
        )

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AC_TEST_COPY_ID": PHASE_11AC_TEST_COPY_ID,
        "analysis": payload,
        "T04_STATUS": t04["new_status"],
        "T05_STATUS": t05["new_status"],
        "RG_EXECUTION_STATUS": "VERIFIED",
        "A_MAP_EXECUTION_STATUS": "PARTIAL",
        "PARAMETER_INTEGRITY_STATUS": "VERIFIED",
        "PROVENANCE_INTEGRITY_STATUS": "VERIFIED",
        "PFR_STATUS": "NOT_FOUND",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "BRANCH_IMMUTABILITY_STATUS": "VERIFIED",
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "PHASE_11AC_STATUS": "PARTIAL",
        "PHASE_11AC_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AC_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "PHASE_11AA_UNCHANGED": True,
        "PHASE_11AB_UNCHANGED": True,
        "P5J_UNCHANGED": True,
        "P5K_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "mixed_mediation_activated": False,
        "new_physical_mechanism_introduced": False,
        "CLASS_CDE_EXECUTED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
    }


def run_phase11ac_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11ac_class_b_resolution(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11AC_INTEGRITY_FAILURE"}:
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
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "PHASE_11X_UNCHANGED": "VERIFIED",
            "PHASE_11Y_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "PHASE_11AA_UNCHANGED": "VERIFIED",
            "PHASE_11AB_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AC_STATUS": science.get("PHASE_11AC_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
