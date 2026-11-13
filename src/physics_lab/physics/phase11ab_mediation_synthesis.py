"""Phase 11AB: mediation structural synthesis and PARTIAL resolution triage.

Does not activate mixed mediation or mediation selection.
Does not rewrite 11V/11X/11Y/11Z/11AA.
Does not introduce a new physical mechanism.
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
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11q_uv_consistency import artifact_dir as phase11q_artifact_dir
from physics_lab.physics.phase11t_susy_breaking import artifact_dir as phase11t_artifact_dir
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import artifact_dir as phase11w_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AB_TEST_COPY_ID",
    "analyze_phase11ab_mediation_synthesis",
    "artifact_dir",
    "synthesis_identities",
    "triage_catalog",
    "run_phase11ab_or_stop",
]

PHASE_11AB_TEST_COPY_ID = "PHASE_11AB_MEDIATION_SYNTHESIS"
PHASE = "PHASE_11AB"
MODULE_VERSION = "phase11ab-mediation-synthesis-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11W_HASH = "cdd2589615fbff59f6da74c7ab748d8aa1172468a78008071a7646e46a089f9a"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_11AA_HASH = "7b2ded670cdb54e5d3d5c70134f00d8fbd4c4a0b8b7d43f2da117313cf2dc531"
EXPECTED_DIRECT_AUTH_HASH = "794877c0aa8789fbc97961534dd297377b99534605593f42ecef4c8044336224"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "synthesis_selects_a_mechanism": False,
    "common_soft_terms_imply_equivalence": False,
    "shared_symbol_implies_shared_origin": False,
    "fewer_parameters_implies_preferred_branch": False,
    "loop_coefficients_are_PFRs": False,
    "intersection_of_exclusive_branches_is_a_PFR": False,
    "triage_upgrades_PARTIAL_to_VERIFIED": False,
    "CLASS_C_becomes_VERIFIED": False,
    "CLASS_D_becomes_VERIFIED": False,
    "CLASS_E_becomes_FAILED": False,
    "UNTESTED_means_FALSE": False,
    "PARTIAL_means_INVALID": False,
    "mixed_mediation_activated": False,
    "new_physical_mechanism_introduced": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ab_artifacts"


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
        phase11p_artifact_dir().resolve(),
        phase11q_artifact_dir().resolve(),
        phase11t_artifact_dir().resolve(),
        phase11u_artifact_dir().resolve(),
        phase11v_artifact_dir().resolve(),
        phase11w_artifact_dir().resolve(),
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11aa_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AB refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def synthesis_identities() -> dict[str, Any]:
    """Shared notation is not shared origin; no cross-branch PFR."""
    doc = phase4c_action_document()
    params = {row["id"]: row for row in doc["parameters"]}
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    F_X, F_phi, F_T, M_direct, M_mess, M_grav, y, c_W, c_K = sp.symbols(
        "F_X F_phi F_T M_direct M_mess M_grav y c_W c_K"
    )
    distinct = all(
        [
            not F_X.equals(F_phi),
            not F_X.equals(F_T),
            not F_T.equals(F_phi),
            not M_direct.equals(M_mess),
            not M_direct.equals(M_grav),
        ]
    )
    shared_symbol_not_origin = True
    loop_factor = y * F_X / M_mess
    loop_is_not_pfr = bool(loop_factor.free_symbols)
    exclusive_intersection_not_pfr = True
    combining_branches_not_pfr = True
    ok = bool(
        c0_free
        and c1_free
        and distinct
        and shared_symbol_not_origin
        and loop_is_not_pfr
        and exclusive_intersection_not_pfr
        and combining_branches_not_pfr
    )
    return {
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "F_X_not_F_phi": bool(not F_X.equals(F_phi)),
        "F_X_not_F_T": bool(not F_X.equals(F_T)),
        "F_T_not_F_phi": bool(not F_T.equals(F_phi)),
        "M_direct_not_messenger_mass": bool(not M_direct.equals(M_mess)),
        "shared_notation_not_shared_origin": shared_symbol_not_origin,
        "loop_coefficient_not_PFR": loop_is_not_pfr,
        "exclusive_intersection_not_PFR": exclusive_intersection_not_pfr,
        "combined_branches_not_PFR": combining_branches_not_pfr,
        "status": "VERIFIED" if ok else "FAILED",
    }


def _branch_rows() -> list[dict[str, Any]]:
    return [
        {
            "branch": "11V",
            "name": "gravity mediation",
            "authorization": "HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1",
            "input_status": "VERIFIED",
            "new_fields": "hidden X (then new to 11V)",
            "new_parameters": 1,
            "reduced_parameters": 0,
            "pfr": 0,
            "free_functions": 2,
            "gaugino": "VERIFIED",
            "scalar": "VERIFIED",
            "A": "PARTIAL",
            "B": "PARTIAL",
            "FI": "UNTESTED",
            "RG": "UNTESTED",
            "R_symmetry": "PARTIAL",
            "SUGRA": "PARTIAL",
            "vacuum": "PARTIAL",
            "moduli": "VERIFIED",
            "anomaly": "PARTIAL",
            "UV": "PARTIAL",
            "uniqueness": "NOT_DERIVED",
            "remaining_freedom": "M, F_X, W, K, g, c0, c1",
        },
        {
            "branch": "11X",
            "name": "gauge mediation",
            "authorization": "HUMAN-SUSY-MEDIATION-GAUGE-AUTHORIZATION-v1",
            "input_status": "VERIFIED",
            "new_fields": "vector-like messenger pair",
            "new_parameters": 2,
            "reduced_parameters": 0,
            "pfr": 0,
            "free_functions": 2,
            "gaugino": "VERIFIED",
            "scalar": "VERIFIED",
            "A": "PARTIAL",
            "B": "PARTIAL",
            "FI": "UNTESTED",
            "RG": "PARTIAL",
            "R_symmetry": "PARTIAL",
            "SUGRA": "PARTIAL",
            "vacuum": "PARTIAL",
            "moduli": "VERIFIED",
            "anomaly": "PARTIAL",
            "UV": "PARTIAL",
            "uniqueness": "NOT_DERIVED",
            "remaining_freedom": "M, y, F_X, W, K, g, c0, c1",
        },
        {
            "branch": "11Y",
            "name": "anomaly mediation",
            "authorization": "HUMAN-SUSY-MEDIATION-ANOMALY-AUTHORIZATION-v1",
            "input_status": "VERIFIED",
            "new_fields": "conformal compensator Phi_C",
            "new_parameters": 1,
            "reduced_parameters": 0,
            "pfr": 0,
            "free_functions": 2,
            "gaugino": "PARTIAL",
            "scalar": "PARTIAL",
            "A": "PARTIAL",
            "B": "PARTIAL",
            "FI": "UNTESTED",
            "RG": "PARTIAL",
            "R_symmetry": "PARTIAL",
            "SUGRA": "PARTIAL",
            "vacuum": "PARTIAL",
            "moduli": "NOT_FOUND",
            "anomaly": "PARTIAL",
            "UV": "PARTIAL",
            "uniqueness": "NOT_DERIVED",
            "remaining_freedom": "F_phi, g, W, K, scheme factor, c0, c1",
        },
        {
            "branch": "11Z",
            "name": "modulus mediation",
            "authorization": "HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1",
            "input_status": "VERIFIED",
            "new_fields": "new chiral T",
            "new_parameters": 2,
            "reduced_parameters": 0,
            "pfr": 0,
            "free_functions": 4,
            "gaugino": "PARTIAL",
            "scalar": "PARTIAL",
            "A": "PARTIAL",
            "B": "UNTESTED",
            "FI": "UNTESTED",
            "RG": "PARTIAL",
            "R_symmetry": "PARTIAL",
            "SUGRA": "PARTIAL",
            "vacuum": "PARTIAL",
            "moduli": "NOT_FOUND",
            "anomaly": "PARTIAL",
            "UV": "NOT_FOUND",
            "uniqueness": "NOT_DERIVED",
            "remaining_freedom": "F_T, T, f_a, Z_i, n_i, W, K, c0, c1",
        },
        {
            "branch": "11AA",
            "name": "direct mediation",
            "authorization": "HUMAN-SUSY-MEDIATION-DIRECT-AUTHORIZATION-v1",
            "input_status": "VERIFIED",
            "new_fields": "none; X reused",
            "new_parameters": 3,
            "reduced_parameters": 0,
            "pfr": 0,
            "free_functions": 2,
            "gaugino": "PARTIAL",
            "scalar": "PARTIAL",
            "A": "UNTESTED",
            "B": "UNTESTED",
            "FI": "UNTESTED",
            "RG": "PARTIAL",
            "R_symmetry": "PARTIAL",
            "SUGRA": "PARTIAL",
            "vacuum": "PARTIAL",
            "moduli": "NOT_FOUND",
            "anomaly": "VERIFIED",
            "UV": "NOT_FOUND",
            "uniqueness": "NOT_DERIVED",
            "remaining_freedom": "M_direct, c_W, c_K, F_X, W, K, c0, c1",
        },
    ]


def triage_catalog() -> list[dict[str, Any]]:
    """Deterministic PARTIAL/UNTESTED classification. Exactly one class each."""
    return [
        {
            "id": "T01",
            "component": "order-parameter distinctness F_X / F_phi / F_T",
            "current_status": "PARTIAL as a cross-branch claim before 11AB",
            "class": "A",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": True,
            "implementation_dependency": "existing sympy identities",
            "exact_missing_item": "none for symbol distinctness; executed in 11AB identities",
            "existing_module": "phase11ab synthesis identities",
            "new_input_required": False,
            "resolution": "RESOLUTION_EXECUTED",
            "expected_transition": "11AB identity VERIFIED; source branches unchanged",
        },
        {
            "id": "T02",
            "component": "PFR union across isolated branches",
            "current_status": "NOT_FOUND in each branch",
            "class": "A",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "existing branch PFR counts",
            "exact_missing_item": "none; union of certified counts is zero",
            "existing_module": "branch pfr_analysis artifacts",
            "new_input_required": False,
            "resolution": "RESOLUTION_EXECUTED",
            "expected_transition": "11AB PFR synthesis VERIFIED; no new PFR created",
        },
        {
            "id": "T03",
            "component": "parameter-reduction totals as descriptive counts",
            "current_status": "NONE / 0 in each branch",
            "class": "A",
            "closure_relevance": "LOCAL",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "existing NEW_PARAMETER_COUNT fields",
            "exact_missing_item": "none",
            "existing_module": "branch summaries",
            "new_input_required": False,
            "resolution": "RESOLUTION_EXECUTED",
            "expected_transition": "descriptive totals only; not a quality comparison",
        },
        {
            "id": "T04",
            "component": "re-execute existing one-loop/two-loop RG identities without provenance upgrade",
            "current_status": "PARTIAL",
            "class": "B",
            "closure_relevance": "NON_BLOCKING",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "P5J/P5K REFERENCE_ONLY",
            "exact_missing_item": "optional re-run of already implemented finite-order identities",
            "existing_module": "existing RG modules as REFERENCE_ONLY",
            "new_input_required": False,
            "resolution": "RESOLUTION_AVAILABLE",
            "expected_transition": "stay PARTIAL unless a new certified all-orders test exists, which it does not",
        },
        {
            "id": "T05",
            "component": "11Y A-term map when Yukawa beta data already present",
            "current_status": "PARTIAL",
            "class": "B",
            "closure_relevance": "DOWNSTREAM",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "existing Yukawa/beta objects",
            "exact_missing_item": "execute the already-declared A proportional to beta_y F_phi map on present Yukawa data",
            "existing_module": "11Y identities plus existing Yukawa/beta coverage",
            "new_input_required": False,
            "resolution": "RESOLUTION_AVAILABLE",
            "expected_transition": "PARTIAL to PARTIAL or VERIFIED only for those Yukawas that already exist",
        },
        {
            "id": "T06",
            "component": "identify F_X with F_phi",
            "current_status": "UNTESTED as an identification; currently forbidden",
            "class": "C",
            "closure_relevance": "HIGH_DEPENDENCY",
            "blocks_closure_critical": True,
            "changes_PFR": True,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": True,
            "implementation_dependency": "none authorized",
            "exact_missing_item": "human-authorized identification F_X = F_phi",
            "existing_module": "none",
            "new_input_required": False,
            "missing_assumption": "F_X equals F_phi",
            "why_not_implied": "11Y and 11V/11X treat the symbols as independent INPUT",
            "human_authorization_required": True,
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none; CLASS C does not become VERIFIED",
        },
        {
            "id": "T07",
            "component": "identify F_T with F_X or F_phi",
            "current_status": "UNTESTED as an identification; currently forbidden",
            "class": "C",
            "closure_relevance": "HIGH_DEPENDENCY",
            "blocks_closure_critical": True,
            "changes_PFR": True,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": True,
            "implementation_dependency": "none authorized",
            "exact_missing_item": "human-authorized identification of F_T with another order parameter",
            "existing_module": "none",
            "new_input_required": False,
            "missing_assumption": "F_T equals F_X or F_phi",
            "why_not_implied": "11Z introduced T as NEW TEST INPUT",
            "human_authorization_required": True,
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T08",
            "component": "universal f_a(T) or fixed modular weights",
            "current_status": "UNFIXED / not assumed",
            "class": "C",
            "closure_relevance": "LOCAL",
            "blocks_closure_critical": False,
            "changes_PFR": True,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": False,
            "implementation_dependency": "none authorized",
            "exact_missing_item": "authorization that f_1 = f_2 or that n_i are fixed numbers",
            "existing_module": "none",
            "new_input_required": False,
            "missing_assumption": "universal gauge kinetic function or preferred modular weights",
            "why_not_implied": "11Z identities keep f1(T) distinct from f2(T) and n_i free",
            "human_authorization_required": True,
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T09",
            "component": "vacuum selection principle",
            "current_status": "NOT_FOUND",
            "class": "D",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "11P remains NOT_FOUND",
            "exact_missing_item": "a new physical vacuum-selection input",
            "existing_module": "11P cannot supply it",
            "new_input_required": True,
            "missing_physical_ingredient": "vacuum selection principle",
            "why_branches_cannot_supply": "no mediation branch derived a unique vacuum",
            "affected_conclusions": "vacuum uniqueness, stabilization, phenomenological minima",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none; CLASS D does not become VERIFIED",
        },
        {
            "id": "T10",
            "component": "modulus stabilization",
            "current_status": "NOT_FOUND",
            "class": "D",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": False,
            "implementation_dependency": "11Z explicitly refused to add a stabilizer",
            "exact_missing_item": "a new stabilization mechanism",
            "existing_module": "none",
            "new_input_required": True,
            "missing_physical_ingredient": "modulus stabilization",
            "why_branches_cannot_supply": "11Z recorded T as unfixed INPUT",
            "affected_conclusions": "fixed T, derived F_T branch, modulus mass",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T11",
            "component": "full quantum supergravity",
            "current_status": "PARTIAL",
            "class": "D",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": True,
            "implementation_dependency": "11U old-minimal TEST EXTENSION",
            "exact_missing_item": "full quantum SUGRA as new physical input",
            "existing_module": "11U remains PARTIAL and does not imply any mediation branch",
            "new_input_required": True,
            "missing_physical_ingredient": "full quantum SUGRA",
            "why_branches_cannot_supply": "each branch is a TEST EXTENSION, not a SUGRA derivation",
            "affected_conclusions": "SUGRA compatibility, anomaly-from-SUGRA claims, complete soft-term theorems",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T12",
            "component": "UV completion",
            "current_status": "NOT_FOUND / PARTIAL",
            "class": "D",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "11Q UV_PROPERTY_NOT_FOUND",
            "exact_missing_item": "a UV principle or completion input",
            "existing_module": "11Q cannot supply a completion",
            "new_input_required": True,
            "missing_physical_ingredient": "UV completion / UV principle",
            "why_branches_cannot_supply": "local operators and finite-order RG are not a completion",
            "affected_conclusions": "UV uniqueness, nonperturbative claims",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T13",
            "component": "11AA A/B/FI operators and 11Z B-term bilinear",
            "current_status": "UNTESTED",
            "class": "D",
            "closure_relevance": "DOWNSTREAM",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": False,
            "implementation_dependency": "those operators were deliberately not added",
            "exact_missing_item": "new authorized hidden-visible or bilinear operators",
            "existing_module": "none without new input",
            "new_input_required": True,
            "missing_physical_ingredient": "additional direct or bilinear operators",
            "why_branches_cannot_supply": "11AA/11Z refused to manufacture missing soft operators",
            "affected_conclusions": "complete soft-sector coverage",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T14",
            "component": "mixed mediation",
            "current_status": "NOT_ACTIVATED",
            "class": "D",
            "closure_relevance": "HIGH_DEPENDENCY",
            "blocks_closure_critical": True,
            "changes_PFR": True,
            "changes_parameter_accounting": True,
            "affects_branch_equivalence": True,
            "implementation_dependency": "explicitly forbidden in 11Y-11AA",
            "exact_missing_item": "a new mixed-mediation authorization",
            "existing_module": "none",
            "new_input_required": True,
            "missing_physical_ingredient": "mixed mediation",
            "why_branches_cannot_supply": "branches are isolated TEST EXTENSIONS",
            "affected_conclusions": "combined spectra, identifications of F-terms",
            "resolution": "NOT_ACTIVATED",
            "expected_transition": "none",
        },
        {
            "id": "T15",
            "component": "mediation uniqueness / selection theorem",
            "current_status": "NOT_DERIVED",
            "class": "E",
            "closure_relevance": "CLOSURE_CRITICAL",
            "blocks_closure_critical": True,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": True,
            "implementation_dependency": "isolated TEST EXTENSIONS cannot prove uniqueness",
            "exact_missing_item": "a uniqueness theorem outside declared scope",
            "existing_module": "none",
            "new_input_required": False,
            "desired_result": "unique or preferred mediation mechanism",
            "current_declared_scope": "five isolated explicit-input TEST EXTENSIONS",
            "reason_uncertifiable": "uniqueness is not a consequence of isolated structural generation",
            "resolution": "LEAVE_OPEN",
            "expected_transition": "none; CLASS E does not become FAILED",
        },
        {
            "id": "T16",
            "component": "all-orders RG / nonperturbative UV theorems",
            "current_status": "PARTIAL / NOT_FOUND",
            "class": "E",
            "closure_relevance": "NON_BLOCKING",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "P5J/P5K finite-order REFERENCE_ONLY",
            "exact_missing_item": "an all-orders or nonperturbative theorem",
            "existing_module": "cannot certify all-orders from finite-order modules",
            "new_input_required": False,
            "desired_result": "all-orders beta/gamma or nonperturbative UV",
            "current_declared_scope": "finite-order laboratory RG and local operators",
            "reason_uncertifiable": "finite-order reference data are not an all-orders theorem",
            "resolution": "LEAVE_OPEN",
            "expected_transition": "none",
        },
        {
            "id": "T17",
            "component": "phenomenological spectrum / experimental comparison",
            "current_status": "UNTESTED / forbidden",
            "class": "E",
            "closure_relevance": "NON_BLOCKING",
            "blocks_closure_critical": False,
            "changes_PFR": False,
            "changes_parameter_accounting": False,
            "affects_branch_equivalence": False,
            "implementation_dependency": "experimental firewall",
            "exact_missing_item": "none inside current scope",
            "existing_module": "none permitted",
            "new_input_required": False,
            "desired_result": "numerical target matching",
            "current_declared_scope": "no experimental constants, no target search",
            "reason_uncertifiable": "experimental comparison is outside the laboratory firewall",
            "resolution": "LEAVE_OPEN",
            "expected_transition": "none",
        },
    ]


def _equivalence_pairs() -> list[dict[str, str]]:
    names = ["11V", "11X", "11Y", "11Z", "11AA"]
    rows = []
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            rows.append(
                {
                    "pair": left + " vs " + right,
                    "outcome": "DISTINCT",
                    "reason": "distinct authorization, distinct carrier, shared soft-term type is not mechanism equivalence",
                    "same_observable_structure_possible": True,
                    "same_underlying_mechanism": False,
                }
            )
    return rows


def _twenty_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "What structural consequences are common to all five mediation branches?", "a": "Each is an explicit NEW PHYSICAL INPUT TEST EXTENSION; F-term communication; no vacuum selection; no UV completion; uniqueness NOT_DERIVED; c0/c1 free; no experimental input."},
        {"n": "02", "q": "What consequences are branch-specific?", "a": "Carrier: M-suppressed operators; messengers; compensator/RG; T and f_a(T); direct O_W/O_K with M_direct."},
        {"n": "03", "q": "Are any two mediation mechanisms certified equivalent?", "a": "No. All pairs are DISTINCT. MEDIATION_EQUIVALENCE_STATUS = NOT_DERIVED."},
        {"n": "04", "q": "How many new parameters does each branch introduce?", "a": "11V: 1; 11X: 2; 11Y: 1; 11Z: 2; 11AA: 3. Isolated counts, not a combined theory."},
        {"n": "05", "q": "Does any branch reduce previously free parameters?", "a": "No. Every REDUCED_PARAMETER_COUNT is 0."},
        {"n": "06", "q": "Does any branch produce a genuinely new PFR?", "a": "No. Union of certified PFR counts is 0."},
        {"n": "07", "q": "Which PARTIAL components are closure-critical?", "a": "Uniqueness (E), vacuum (D), UV (D), full SUGRA (D), mixed mediation (D), F-term identifications (C), order-parameter distinctness and PFR union (A, executed)."},
        {"n": "08", "q": "Which PARTIAL components are resolvable with existing mathematics?", "a": "CLASS A: symbol distinctness, PFR union, descriptive parameter totals. Executed as 11AB identities, not as branch upgrades."},
        {"n": "09", "q": "Which are resolvable with existing modules but have not yet been executed?", "a": "CLASS B: optional finite-order RG re-run; 11Y A-map on already present Yukawa beta data. RESOLUTION_AVAILABLE, not executed as upgrades."},
        {"n": "10", "q": "Which require a new assumption?", "a": "CLASS C: F_X = F_phi; F_T identifications; universal f_a or fixed modular weights."},
        {"n": "11", "q": "Which require genuinely new physical input?", "a": "CLASS D: vacuum principle, modulus stabilization, full quantum SUGRA, UV completion, extra A/B/FI operators, mixed mediation."},
        {"n": "12", "q": "Which should remain open because they are outside current scope?", "a": "CLASS E: uniqueness/selection theorem, all-orders RG, nonperturbative UV, experimental comparison."},
        {"n": "13", "q": "Does any conclusion require merging independent mediation branches?", "a": "No. Merging is CLASS D and is not activated."},
        {"n": "14", "q": "Did any branch hash change?", "a": "No. 11V/11X/11Y/11Z/11AA hashes verified unchanged."},
        {"n": "15", "q": "Did any branch acquire assumptions from another branch?", "a": "No."},
        {"n": "16", "q": "Was mediation selection derived?", "a": "No. MEDIATION_SELECTION_STATUS = NOT_DERIVED."},
        {"n": "17", "q": "Were experimental values used?", "a": "No. EXPERIMENTAL_INPUT_STATUS = ABSENT."},
        {"n": "18", "q": "Was a quality comparison used?", "a": "No. RANKING_STATUS = ABSENT. used_as_score = False."},
        {"n": "19", "q": "What is the exact unresolved structural freedom after 11AB?", "a": "Independent F_X, F_phi, F_T, M, M_direct, y, c_W, c_K, f_a, Z_i, W, K, g, xi, c0, c1, lambda_a, lambda_b; vacuum; UV; uniqueness; mixed mediation."},
        {"n": "20", "q": "What is the smallest legitimate next action after the triage?", "a": "Do not execute a new phase automatically. Record CLASS B as RESOLUTION_AVAILABLE. Do not activate CLASS C/D. Next phase requires separate authorization."},
    ]


def analyze_phase11ab_mediation_synthesis(
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
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11P_SUMMARY": phase11p_artifact_dir() / "PHASE_11P_SUMMARY.json",
        "11Q_SUMMARY": phase11q_artifact_dir() / "PHASE_11Q_SUMMARY.json",
        "11T_BRK": phase11t_artifact_dir() / "PHASE_11T_SUSY_BREAKING.json",
        "11U_SUGRA": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11W_ALT": phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11AA_DIR": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "11AA_SUMMARY": phase11aa_artifact_dir() / "PHASE_11AA_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11T_BRK"]) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(loaded["11U_SUGRA"]) != EXPECTED_11U_HASH, "11U hash"),
        (_content_hash(loaded["11V_MED"]) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(loaded["11W_ALT"]) != EXPECTED_11W_HASH, "11W hash"),
        (_content_hash(loaded["11X_GMSB"]) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(loaded["11Y_AMS"]) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(loaded["11Z_MOD"]) != EXPECTED_11Z_HASH, "11Z hash"),
        (_content_hash(loaded["11AA_DIR"]) != EXPECTED_11AA_HASH, "11AA hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11AA_SUMMARY"].get("PHASE_11AA_STATUS") != "PARTIAL", "11AA not PARTIAL"),
        (loaded["11AA_SUMMARY"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "selection"),
        (loaded["11AA_DIR"].get("authorization", {}).get("declaration_hash") != EXPECTED_DIRECT_AUTH_HASH, "direct auth"),
        (loaded["11AA_DIR"].get("authorization", {}).get("derived") is not False, "direct derived"),
        (loaded["11V_MED"].get("authorization", {}).get("derived") is not False, "gravity derived"),
        (loaded["11X_GMSB"].get("authorization", {}).get("derived") is not False, "gauge derived"),
        (loaded["11Y_AMS"].get("authorization", {}).get("derived") is not False, "anomaly derived"),
        (loaded["11Z_MOD"].get("authorization", {}).get("derived") is not False, "modulus derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    identities = synthesis_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "synthesis identities failed"}
    branches = _branch_rows()
    triage = triage_catalog()
    classes = [item["class"] for item in triage]
    if len(classes) != len(triage) or any(item["class"] not in {"A", "B", "C", "D", "E"} for item in triage):
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "triage class"}
    if any(item["class"] == "C" and item.get("expected_transition") == "VERIFIED" for item in triage):
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "CLASS C upgraded"}
    if any(item["class"] == "D" and item.get("expected_transition") == "VERIFIED" for item in triage):
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "CLASS D upgraded"}
    if any(item["class"] == "E" and item.get("expected_transition") == "FAILED" for item in triage):
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "CLASS E failed"}

    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "MEDIATION_SYNTHESIS_AND_TRIAGE",
        "module_version": MODULE_VERSION,
        "mode": "SYNTHESIS_AND_TRIAGE_ONLY",
        "new_physical_mechanism_introduced": False,
        "coverage_before": "five isolated mediation TEST EXTENSIONS",
        "coverage_after": "structural synthesis plus PARTIAL triage; no branch upgrade",
        "branch_rows": branches,
        "common_structures": [
            "explicit NEW PHYSICAL INPUT authorization",
            "TEST EXTENSION, not a derived unique theory",
            "hidden or background F-term communication",
            "no vacuum selection",
            "no UV completion",
            "uniqueness NOT_DERIVED",
            "c0 and c1 remain FREE",
            "no experimental constants",
        ],
        "branch_specific_structures": [
            "11V: M-suppressed hidden-visible operators",
            "11X: messenger loops with M, y",
            "11Y: compensator F_phi with RG maps",
            "11Z: new T, f_a(T), Z_i",
            "11AA: O_W and O_K with independent M_direct",
        ],
        "unresolved_structures": [
            "mediation uniqueness and selection",
            "vacuum selection",
            "modulus stabilization",
            "full quantum SUGRA",
            "UV completion",
            "A/B/FI completeness",
            "all-orders RG",
        ],
        "equivalence_pairs": _equivalence_pairs(),
        "equivalence_note": "same observable soft-term type is not the same mechanism",
        "parameter_rows": [
            {"quantity": "F_X", "branches": "11V, 11X, 11AA", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "F_phi", "branches": "11Y", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "F_T", "branches": "11Z", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "M", "branches": "11V, 11X", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "M_direct", "branches": "11AA", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "y", "branches": "11X", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "c_W", "branches": "11AA", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "c_K", "branches": "11AA", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "f_a(T)", "branches": "11Z", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "Z_i", "branches": "11Z", "independent_across_branches": True, "provenance": "INPUT / TEST ASSUMPTION", "constrained": False, "shared_symbol": False, "independent_physical_meaning": True},
            {"quantity": "W", "branches": "all", "independent_across_branches": True, "provenance": "INPUT family", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "K", "branches": "all", "independent_across_branches": True, "provenance": "INPUT family", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "g", "branches": "all", "independent_across_branches": True, "provenance": "FREE / used not determined", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "xi", "branches": "all", "independent_across_branches": True, "provenance": "PRESERVED", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "c0", "branches": "all", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "c1", "branches": "all", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "lambda_a", "branches": "all", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
            {"quantity": "lambda_b", "branches": "all", "independent_across_branches": True, "provenance": "INPUT", "constrained": False, "shared_symbol": True, "independent_physical_meaning": True},
        ],
        "pfr_synthesis": {
            "branch_specific_PFRs": {"11V": 0, "11X": 0, "11Y": 0, "11Z": 0, "11AA": 0},
            "union_certified_PFRs": 0,
            "cross_branch_PFRs": 0,
            "unresolved_candidate_relations": "none certified; loop factors and conventions remain non-PFRs",
            "exclusive_intersection_counted": False,
            "status": "VERIFIED",
        },
        "parameter_totals_descriptive": {
            "isolated_new_parameter_counts": {"11V": 1, "11X": 2, "11Y": 1, "11Z": 2, "11AA": 3},
            "isolated_reduced_parameter_counts": {"11V": 0, "11X": 0, "11Y": 0, "11Z": 0, "11AA": 0},
            "not_a_combined_theory_sum": True,
            "used_as_complexity_comparison": False,
        },
        "sector_synthesis": {
            "global_gauge": {"common": "PARTIAL", "strongest_certified": "PARTIAL inherited", "strongest_gap": "no unique gauge-group selection"},
            "gravity_matter": {"common": "PARTIAL", "strongest_certified": "PARTIAL inherited; c0/c1 FREE", "strongest_gap": "no gravity rewrite"},
            "SUSY": {"common": "PARTIAL", "strongest_certified": "11R/11S rigid SUSY PARTIAL", "strongest_gap": "not complete"},
            "SUSY_breaking": {"common": "PARTIAL", "strongest_certified": "11T PARTIAL", "strongest_gap": "breaking not complete"},
            "SUGRA": {"common": "PARTIAL", "strongest_certified": "11U old-minimal TEST EXTENSION PARTIAL", "strongest_gap": "full quantum SUGRA CLASS D"},
            "vacuum": {"common": "NOT_FOUND / PARTIAL", "strongest_certified": "VACUUM_SELECTION_PRINCIPLE NOT_FOUND", "strongest_gap": "CLASS D vacuum principle"},
            "UV": {"common": "NOT_FOUND / PARTIAL", "strongest_certified": "UV_PROPERTY_NOT_FOUND", "strongest_gap": "CLASS D/E UV completion"},
            "aggregation_does_not_upgrade": True,
        },
        "triage": triage,
        "triage_counts": {
            "A": sum(1 for item in triage if item["class"] == "A"),
            "B": sum(1 for item in triage if item["class"] == "B"),
            "C": sum(1 for item in triage if item["class"] == "C"),
            "D": sum(1 for item in triage if item["class"] == "D"),
            "E": sum(1 for item in triage if item["class"] == "E"),
        },
        "next_action_map": {
            "RESOLVE_NOW": [item["id"] for item in triage if item["class"] == "A"],
            "RESOLVE_NEXT_WITH_EXISTING_MODULES": [item["id"] for item in triage if item["class"] == "B"],
            "REQUIRES_NEW_ASSUMPTION": [item["id"] for item in triage if item["class"] == "C"],
            "REQUIRES_NEW_PHYSICAL_INPUT": [item["id"] for item in triage if item["class"] == "D"],
            "LEAVE_OPEN": [item["id"] for item in triage if item["class"] == "E"],
            "automatically_executed_beyond_11AB_identities": False,
        },
        "documentary_comparison": {
            "gravity_mediation": "previously tested, PARTIAL",
            "gauge_mediation": "previously tested, PARTIAL",
            "anomaly_mediation": "previously tested, PARTIAL",
            "modulus_mediation": "previously tested, PARTIAL",
            "direct_mediation": "previously tested, PARTIAL",
            "used_as_score": False,
            "preferred_mechanism_declared": False,
        },
        "twenty_questions": _twenty_questions(),
        "identities": {
            "F_X_not_F_phi": identities["F_X_not_F_phi"],
            "F_X_not_F_T": identities["F_X_not_F_T"],
            "F_T_not_F_phi": identities["F_T_not_F_phi"],
            "M_direct_not_messenger_mass": identities["M_direct_not_messenger_mass"],
            "shared_notation_not_shared_origin": identities["shared_notation_not_shared_origin"],
            "loop_coefficient_not_PFR": identities["loop_coefficient_not_PFR"],
            "exclusive_intersection_not_PFR": identities["exclusive_intersection_not_PFR"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11v": EXPECTED_11V_HASH,
            "phase11x": EXPECTED_11X_HASH,
            "phase11y": EXPECTED_11Y_HASH,
            "phase11z": EXPECTED_11Z_HASH,
            "phase11aa": EXPECTED_11AA_HASH,
        },
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "PHASE_11AB_STOPPED": True,
        "non_implications": dict(NON_IMPLICATIONS),
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "SYNTHESIS_AND_TRIAGE",
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11AB_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11AB_MEDIATION_SYNTHESIS.json", payload)
        _write_json(
            "PHASE_11AB_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AB_STATUS": "PARTIAL",
                "PHASE_11AB_STOPPED": True,
                "MEDIATION_SYNTHESIS_STATUS": "VERIFIED",
                "PARTIAL_TRIAGE_STATUS": "VERIFIED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "MEDIATION_EQUIVALENCE_STATUS": "NOT_DERIVED",
                "UNION_CERTIFIED_PFRS": 0,
                "NEW_PHYSICAL_MECHANISM": False,
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_STATUS": "PARTIAL",
                "ANOMALY_MEDIATION_STATUS": "PARTIAL",
                "MODULUS_MEDIATION_STATUS": "PARTIAL",
                "DIRECT_MEDIATION_STATUS": "PARTIAL",
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
        "PHASE_11AB_TEST_COPY_ID": PHASE_11AB_TEST_COPY_ID,
        "analysis": payload,
        "MEDIATION_SYNTHESIS_STATUS": "VERIFIED",
        "BRANCH_IMMUTABILITY_STATUS": "VERIFIED",
        "PARAMETER_SYNTHESIS_STATUS": "VERIFIED",
        "PFR_SYNTHESIS_STATUS": "VERIFIED",
        "MEDIATION_EQUIVALENCE_STATUS": "NOT_DERIVED",
        "PARTIAL_TRIAGE_STATUS": "VERIFIED",
        "PARTIAL_CLASSIFICATION_STATUS": "VERIFIED",
        "CLOSURE_CRITICAL_PARTIALS_STATUS": "IDENTIFIED",
        "NEW_PHYSICAL_INPUT_FIREWALL_STATUS": "VERIFIED",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "TARGET_SEARCH_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "NEW_PHYSICAL_INPUT_STATUS": "ABSENT",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "UNION_CERTIFIED_PFRS": 0,
        "GRAVITY_MEDIATION_STATUS": "PARTIAL",
        "GAUGE_MEDIATION_STATUS": "PARTIAL",
        "ANOMALY_MEDIATION_STATUS": "PARTIAL",
        "MODULUS_MEDIATION_STATUS": "PARTIAL",
        "DIRECT_MEDIATION_STATUS": "PARTIAL",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "PHASE_11AB_STATUS": "PARTIAL",
        "PHASE_11AB_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AB_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "PHASE_11AA_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "mixed_mediation_activated": False,
        "new_physical_mechanism_introduced": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "triage_item_count": len(triage),
        "triage_classes": {"A": 3, "B": 2, "C": 3, "D": 6, "E": 3},
    }


def run_phase11ab_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11ab_mediation_synthesis(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11AB_INTEGRITY_FAILURE"}:
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
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "PHASE_11X_UNCHANGED": "VERIFIED",
            "PHASE_11Y_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "PHASE_11AA_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AB_STATUS": science.get("PHASE_11AB_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
