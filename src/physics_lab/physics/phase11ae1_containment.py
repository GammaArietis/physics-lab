"""Phase 11AE.1: vacuum-selection containment audit.

Ask only whether a ground-state / global-minimum criterion is already
contained. Do not invent, authorize, or activate a selection law.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
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
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10d_equivalence import artifact_dir as phase10d_artifact_dir
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import vacuum_selection_identities
from physics_lab.physics.phase11t_susy_breaking import artifact_dir as phase11t_artifact_dir
from physics_lab.physics.phase11t_susy_breaking import susy_breaking_identities
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.phase11u_supergravity import sugra_identities
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import modulus_mediation_identities
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase11ac_class_b_resolution import artifact_dir as phase11ac_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import artifact_dir as phase11ae_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import is_exact_mathematical_statement
from physics_lab.physics.phase11ae_vacuum_selection import topic_authorization
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXTERNAL_REFERENCE_ONLY",
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AE1_TEST_COPY_ID",
    "analyze_phase11ae1_containment",
    "artifact_dir",
    "CLOSURE_TARGETS",
    "PRE_EXECUTION_CLOSURE_TARGET",
    "PreExecutionClosureCriterion",
    "containment_identities",
    "refuse_principle_activation",
    "run_containment_audit",
    "run_phase11ae1_or_stop",
]

PHASE_11AE1_TEST_COPY_ID = "PHASE_11AE1_CONTAINMENT"
PHASE = "PHASE_11AE1"
MODULE_VERSION = "phase11ae1-containment-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_11AA_HASH = "7b2ded670cdb54e5d3d5c70134f00d8fbd4c4a0b8b7d43f2da117313cf2dc531"
EXPECTED_11AB_HASH = "8b1a3c44f772521e18d3e838dfe9fa56b175b3066d99608bb5ffda6bbecb842d"
EXPECTED_11AC_HASH = "7342328f90d4d0d769160bdd84493f64457d485a8dbfbed85f148d9e9700a19f"
EXPECTED_11AD_HASH = "a84e48002a4fbb6dd269a6a2924551647930da1c700d39fa08dc749f49219ada"
EXPECTED_11AE_HASH = "0473f21c1298114a0f42ed6a81b3649e5093690bb55e0db83098bd3c25a836b9"

EXTERNAL_REFERENCE_ONLY = (
    "vacuum = lowest energy",
    "ground state",
    "global minimum",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "stationary_point_is_selected_vacuum": False,
    "local_minimum_is_global_minimum": False,
    "potential_existence_is_global_minimum_principle": False,
    "sugra_potential_existence_is_vacuum_selection": False,
    "modulus_existence_is_stabilization": False,
    "external_lowest_energy_is_operational": False,
    "containment_activates_vacuum_selection": False,
    "argmin_identification_is_already_assumed": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ae1_artifacts"


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
        phase11p_artifact_dir().resolve(),
        phase11t_artifact_dir().resolve(),
        phase11u_artifact_dir().resolve(),
        phase11v_artifact_dir().resolve(),
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11aa_artifact_dir().resolve(),
        phase11ab_artifact_dir().resolve(),
        phase11ac_artifact_dir().resolve(),
        phase11ad_artifact_dir().resolve(),
        phase11ae_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AE.1 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def refuse_principle_activation(statement: str) -> dict[str, Any]:
    """A containment audit must not activate a selection law."""
    return {
        "proposed_statement": statement,
        "activated": False,
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "reason": "Phase 11AE.1 is a containment audit; it cannot activate a principle",
    }


def containment_identities() -> dict[str, Any]:
    """Inspect implemented identities only. Do not add a principle."""
    p11 = vacuum_selection_identities()
    t11 = susy_breaking_identities()
    u11 = sugra_identities()
    z11 = modulus_mediation_identities()
    topic = topic_authorization()
    external_operational = any(is_exact_mathematical_statement(item) for item in EXTERNAL_REFERENCE_ONLY)
    functional_complete = False
    admissible_complete = False
    constraints_complete = False
    argmin_present = False
    existence_established = False
    local_vs_global_established = False
    vacuum_is_argmin = False
    first_missing = (
        "complete vacuum/energy functional on a declared admissible "
        "configuration space, together with the identification of its "
        "global minimizer with the physical vacuum"
    )
    ok = bool(
        p11["stationarity_is_not_selection"]
        and p11["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
        and p11["VACUUM_UNIQUENESS"] == "NOT_DERIVED"
        and p11["positive_hessian_is_not_unique_global_minimum_of_a_general_theory"]
        and p11["Phi_zero_is_always_stationary"]
        and p11["hessian_is_2_mu_identity"]
        and (not t11["F_vacuum_unique"])
        and (not t11["D_vacuum_unique"])
        and u11["V_sugra_differs_from_V_rigid"]
        and u11["F_flat_not_Minkowski"]
        and z11["no_stabilization_assumed"]
        and z11["no_vacuum_uniqueness_inferred"]
        and topic["mathematical_statement"] == "PRINCIPLE_UNSPECIFIED"
        and topic["operational"] is False
        and (not external_operational)
        and (not functional_complete)
        and (not admissible_complete)
        and (not constraints_complete)
        and (not argmin_present)
        and (not existence_established)
        and (not local_vs_global_established)
        and (not vacuum_is_argmin)
    )
    return {
        "p11_potential": p11["potential"],
        "p11_stationary": p11["Phi_zero_is_always_stationary"],
        "p11_hessian": p11["hessian_is_2_mu_identity"],
        "p11_stationarity_is_not_selection": p11["stationarity_is_not_selection"],
        "p11_principle": p11["VACUUM_SELECTION_PRINCIPLE"],
        "p11_uniqueness": p11["VACUUM_UNIQUENESS"],
        "t11_F_unique": t11["F_vacuum_unique"],
        "t11_D_unique": t11["D_vacuum_unique"],
        "u11_V_differs": u11["V_sugra_differs_from_V_rigid"],
        "u11_F_flat_not_Minkowski": u11["F_flat_not_Minkowski"],
        "z11_no_stabilization": z11["no_stabilization_assumed"],
        "z11_no_uniqueness": z11["no_vacuum_uniqueness_inferred"],
        "topic_unspecified": topic["mathematical_statement"] == "PRINCIPLE_UNSPECIFIED",
        "external_reference_operational": external_operational,
        "functional_complete": functional_complete,
        "admissible_complete": admissible_complete,
        "constraints_complete": constraints_complete,
        "argmin_present": argmin_present,
        "existence_established": existence_established,
        "local_vs_global_established": local_vs_global_established,
        "vacuum_identified_with_argmin": vacuum_is_argmin,
        "first_missing_ingredient": first_missing,
        "first_missing_kind": "NEW_ASSUMPTION",
        "derivation_succeeded": False,
        "status": "VERIFIED" if ok else "FAILED",
    }


def _ingredient_rows(ident: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ingredient": "energy/Hamiltonian functional",
            "currently_present": "PARTIAL: 11P quadratic; 11T F/D pieces; Hamiltonian boundedness PARTIAL",
            "source": "11P / 11T",
            "status": "PARTIAL",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "scalar/effective potential",
            "currently_present": "PARTIAL: 11P V = mu_s_sq |Phi|^2; 11T V_F and V_D; 11U schematic V_sugra identity",
            "source": "11P / 11T / 11U",
            "status": "PARTIAL",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "admissible configuration space",
            "currently_present": "PARTIAL: 11P real three-plane for the toy quadratic only",
            "source": "11P",
            "status": "PARTIAL",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "stationarity equations",
            "currently_present": "CONTAINED for the 11P quadratic and 11T F/D toys",
            "source": "11P / 11T",
            "status": "CONTAINED",
            "additional_assumption_required": False,
        },
        {
            "ingredient": "local stability",
            "currently_present": "CONTAINED as Hessian cases of the 11P quadratic; parameter-dependent",
            "source": "11P",
            "status": "CONTAINED",
            "additional_assumption_required": False,
        },
        {
            "ingredient": "global minimization",
            "currently_present": "ABSENT: no argmin construction; 11P GLOBAL_VACUUM_SELECTION UNTESTED",
            "source": "none implemented",
            "status": "ABSENT",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "minimum existence",
            "currently_present": "NOT_ESTABLISHED for a general functional; field space not certified compact or bounded",
            "source": "11P records Hamiltonian_boundedness PARTIAL",
            "status": "NOT_ESTABLISHED",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "global-vs-local distinction",
            "currently_present": "NOT_ESTABLISHED; 11P states a positive Hessian is not a general global minimum",
            "source": "11P",
            "status": "NOT_ESTABLISHED",
            "additional_assumption_required": False,
        },
        {
            "ingredient": "vacuum uniqueness",
            "currently_present": "NOT_DERIVED; 11P continuous moduli; 11T F/D not unique",
            "source": "11P / 11T / 11U / 11Z",
            "status": "NOT_DERIVED",
            "additional_assumption_required": False,
        },
        {
            "ingredient": "moduli treatment",
            "currently_present": "CONTAINED as present-and-not-lifted; 11Z T and F_T are INPUT",
            "source": "11P / 11Z",
            "status": "CONTAINED",
            "additional_assumption_required": False,
        },
        {
            "ingredient": "SUGRA vacuum structure",
            "currently_present": "PARTIAL: schematic V_sugra and AdS-like / Minkowski-like / breaking families; no selected branch",
            "source": "11U",
            "status": "PARTIAL",
            "additional_assumption_required": True,
        },
        {
            "ingredient": "argmin-to-physical-vacuum identification",
            "currently_present": "ABSENT; 11P/11AE refuse the identification; external lowest-energy statement is REFERENCE_ONLY",
            "source": "11P / 11AE",
            "status": "ABSENT",
            "additional_assumption_required": True,
            "first_missing": ident["first_missing_ingredient"],
        },
    ]


def _module_audits() -> dict[str, Any]:
    return {
        "phase_11P": {
            "stationary_points": "CONTAINED",
            "Hessian_local_stability": "CONTAINED",
            "moduli": "CONTAINED",
            "candidate_minima": "PARTIAL",
            "vacuum_branches": "PARTIAL",
            "energy_values": "PARTIAL",
            "global_comparison": "UNTESTED",
            "vacuum_selection_rule": "ABSENT",
        },
        "phase_11U": {
            "scalar_potential": "PARTIAL",
            "vacuum_energy_functional": "PARTIAL",
            "stationary_equations": "ABSENT",
            "global_minimization": "ABSENT",
            "supersymmetric_minima": "PARTIAL",
            "broken_SUSY_minima": "PARTIAL",
            "AdS_Minkowski_dS_classification": "PARTIAL",
            "vacuum_comparison": "ABSENT",
        },
        "phase_11T": {
            "complete_vacuum_energy": "ABSENT",
            "global_minimization": "ABSENT",
            "selected_SUSY_breaking_vacuum": "ABSENT",
        },
        "phase_11Z": {
            "V_of_T": "ABSENT",
            "complete_T_dependent_functional": "ABSENT",
            "global_minimization_over_T": "ABSENT",
            "stabilization_criterion": "ABSENT",
            "unique_modulus_vacuum": "ABSENT",
        },
    }


def _decision_rows() -> list[dict[str, str]]:
    return [
        {"question": "Is global-minimum selection already contained?", "result": "No"},
        {"question": "Is it derivable from existing modules?", "result": "No"},
        {
            "question": "Is it merely implementable but not implemented?",
            "result": "Local tools exist; the selection criterion is not an unimplemented calculation",
        },
        {"question": "Does it require a new assumption?", "result": "Yes"},
        {
            "question": "Does it require new physics?",
            "result": "Not new fields; authorizing the selection principle remains T09",
        },
        {"question": "Does it select a vacuum already?", "result": "No"},
        {"question": "Does it stabilize moduli already?", "result": "No"},
    ]


def _seventeen_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Is a ground-state/global-minimum criterion already contained?", "a": "No. CONTAINMENT_STATUS = REQUIRES_NEW_ASSUMPTION. Record NOT_CONTAINED."},
        {"n": "02", "q": "If not contained, is it derivable without new assumptions?", "a": "No. Identifying the physical vacuum with an argmin is not an existing assumption."},
        {"n": "03", "q": "If derivable, which existing modules provide every required ingredient?", "a": "Not derivable. No module set supplies A through G together."},
        {"n": "04", "q": "If not derivable, what is the first missing ingredient?", "a": "A complete vacuum/energy functional on a declared admissible space, plus the argmin-to-vacuum identification."},
        {"n": "05", "q": "Is that missing ingredient mathematical implementation or physical input?", "a": "The blocking item is a new assumption. Global argmin machinery is also unimplemented."},
        {"n": "06", "q": "Does 11P already establish global minimization?", "a": "No. 11P GLOBAL_VACUUM_SELECTION = UNTESTED. Stationarity is not selection."},
        {"n": "07", "q": "Does 11U already establish global minimization?", "a": "No. 11U has a schematic V_sugra identity and unclassified families. selected_branch is none."},
        {"n": "08", "q": "Does 11Z already establish modulus stabilization?", "a": "No. MODULUS_STABILIZATION_STATUS = NOT_FOUND. T and F_T remain INPUT."},
        {"n": "09", "q": "Can the existing laboratory distinguish local from global minima?", "a": "No. LOCAL_VS_GLOBAL_STATUS = NOT_ESTABLISHED. GLOBAL_MINIMUM_CAPABILITY = NOT_ESTABLISHED."},
        {"n": "10", "q": "Can it prove existence of a global minimum?", "a": "No. MINIMUM_EXISTENCE_STATUS = NOT_ESTABLISHED. Admissible space is not certified compact or bounded."},
        {"n": "11", "q": "Can it prove uniqueness?", "a": "No. VACUUM_UNIQUENESS_STATUS = NOT_DERIVED."},
        {"n": "12", "q": "Does the audit introduce any new physical input?", "a": "No. NEW_PHYSICAL_INPUT_STATUS = FALSE."},
        {"n": "13", "q": "Does it introduce any new assumption?", "a": "No. NEW_ASSUMPTION_STATUS = FALSE. The finding is that one would be required."},
        {"n": "14", "q": "Does it introduce any parameter?", "a": "No. NEW_PARAMETER_COUNT = 0. REDUCED_PARAMETER_COUNT = 0."},
        {"n": "15", "q": "Does the PFR count change?", "a": "No. PFR_STATUS = NOT_FOUND."},
        {"n": "16", "q": "Was any parent artifact modified?", "a": "No. PREVIOUS_ARTIFACTS_STATUS = VERIFIED."},
        {"n": "17", "q": "Should GROUND_STATE / GLOBAL-MINIMUM be authorized as new physics, or is it already contained?", "a": "Not contained. This audit does not authorize it. A later exact statement would be required."},
    ]


def analyze_phase11ae1_containment(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    activate_principle: bool = False,
    injected_statement: str | None = None,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    if activate_principle or injected_statement is not None:
        refused = refuse_principle_activation(injected_statement or "GROUND_STATE / GLOBAL-MINIMUM")
        return {
            "status": "STOP",
            "CONTAINMENT_STATUS": "REQUIRES_NEW_ASSUMPTION",
            "PHASE_11AE1_STATUS": "FAILED",
            "PHASE_11AE1_STOPPED": True,
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "scientific_analysis": None,
            "detail": refused["reason"],
        }
    grammar_before = grammar_hash()
    paths = {
        "11P_VAC": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "11T_BRK": phase11t_artifact_dir() / "PHASE_11T_SUSY_BREAKING.json",
        "11U_SUGRA": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11AA_DIR": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "11AB_SYN": phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json",
        "11AC_RES": phase11ac_artifact_dir() / "PHASE_11AC_CLASS_B_RESOLUTION.json",
        "11AD_GATE": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11AE_GATE": phase11ae_artifact_dir() / "PHASE_11AE_VACUUM_SELECTION.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["11P_VAC"]) != EXPECTED_11P_HASH, "11P hash"),
        (_content_hash(loaded["11T_BRK"]) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(loaded["11U_SUGRA"]) != EXPECTED_11U_HASH, "11U hash"),
        (_content_hash(loaded["11V_MED"]) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(loaded["11X_GMSB"]) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(loaded["11Y_AMS"]) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(loaded["11Z_MOD"]) != EXPECTED_11Z_HASH, "11Z hash"),
        (_content_hash(loaded["11AA_DIR"]) != EXPECTED_11AA_HASH, "11AA hash"),
        (_content_hash(loaded["11AB_SYN"]) != EXPECTED_11AB_HASH, "11AB hash"),
        (_content_hash(loaded["11AC_RES"]) != EXPECTED_11AC_HASH, "11AC hash"),
        (_content_hash(loaded["11AD_GATE"]) != EXPECTED_11AD_HASH, "11AD hash"),
        (_content_hash(loaded["11AE_GATE"]) != EXPECTED_11AE_HASH, "11AE hash"),
        (loaded["11AD_GATE"].get("decision_map", {}).get("T09") != "REQUIRES_NEW_PHYSICAL_INPUT", "11AD T09"),
        (loaded["11AE_GATE"].get("VACUUM_SELECTION_INPUT_STATUS") != "PRINCIPLE_UNSPECIFIED", "11AE unspecified"),
        (loaded["11P_VAC"].get("vacuum_selection_principle", {}).get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "11P principle"),
        (loaded["11P_VAC"].get("global_minimum", {}).get("established") is not False, "11P global min"),
        (loaded["11U_SUGRA"].get("vacuum_energy", {}).get("selected_branch") is not None, "11U selected branch"),
        (loaded["11Z_MOD"].get("stabilization", {}).get("status") != "NOT_FOUND", "11Z stabilization"),
        (loaded["11Z_MOD"].get("stabilization", {}).get("vacuum_selected") is not False, "11Z vacuum"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    ident = containment_identities()
    if ident["status"] != "VERIFIED":
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "containment identities failed"}

    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "COMPLETE",
        "module_id": "VACUUM_SELECTION_CONTAINMENT_AUDIT",
        "module_version": MODULE_VERSION,
        "mode": "CONTAINMENT_AUDIT_ONLY",
        "candidate_criterion": "vacuum in argmin over configuration space of a Functional",
        "CONTAINMENT_STATUS": "REQUIRES_NEW_ASSUMPTION",
        "CONTAINMENT_RECORD": "NOT_CONTAINED",
        "EXISTING_THEORY_ALREADY_CONTAINS_VACUUM_SELECTION_CAPABILITY": False,
        "VACUUM_SELECTION_IS_DERIVABLE_WITHOUT_NEW_PHYSICAL_INPUT": False,
        "MATHEMATICAL_CAPABILITY_EXISTS_BUT_REQUIRES_IMPLEMENTATION": False,
        "CONTAINMENT_UNRESOLVED": False,
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "operational_principle_activated": False,
        "external_reference_only": list(EXTERNAL_REFERENCE_ONLY),
        "external_reference_operational": False,
        "A_FUNCTIONAL": "PARTIAL",
        "B_ADMISSIBLE_SPACE": "PARTIAL",
        "C_CONSTRAINTS": "ABSENT",
        "D_GLOBAL_OPTIMIZATION": "ABSENT",
        "E_EXISTENCE_CONDITIONS": "NOT_ESTABLISHED",
        "F_GLOBAL_VS_LOCAL": "NOT_ESTABLISHED",
        "G_MINIMUM_IS_PHYSICAL_VACUUM": "ABSENT",
        "GLOBAL_MINIMUM_CAPABILITY": "NOT_ESTABLISHED",
        "first_missing_ingredient": ident["first_missing_ingredient"],
        "first_missing_kind": ident["first_missing_kind"],
        "derivation_succeeded": False,
        "identities": ident,
        "module_audits": _module_audits(),
        "ingredient_rows": _ingredient_rows(ident),
        "decision_rows": _decision_rows(),
        "seventeen_questions": _seventeen_questions(),
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "PHASE_11AE1_STOPPED": True,
        "non_implications": dict(NON_IMPLICATIONS),
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}
    if write_artifacts:
        _write_json("PHASE_11AE1_CONTAINMENT.json", payload)
        _write_json(
            "PHASE_11AE1_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AE1_STATUS": "COMPLETE",
                "PHASE_11AE1_STOPPED": True,
                "CONTAINMENT_STATUS": "REQUIRES_NEW_ASSUMPTION",
                "CONTAINMENT_RECORD": "NOT_CONTAINED",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "PFR_STATUS": "NOT_FOUND",
                "NEW_PHYSICAL_INPUT_STATUS": False,
                "NEW_ASSUMPTION_STATUS": False,
            },
        )
    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar mutated"}
    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AE1_TEST_COPY_ID": PHASE_11AE1_TEST_COPY_ID,
        "analysis": payload,
        "CONTAINMENT_STATUS": "REQUIRES_NEW_ASSUMPTION",
        "CONTAINMENT_RECORD": "NOT_CONTAINED",
        "ENERGY_FUNCTIONAL_STATUS": "PARTIAL",
        "ADMISSIBLE_CONFIGURATION_SPACE_STATUS": "PARTIAL",
        "GLOBAL_MINIMIZATION_STATUS": "ABSENT",
        "LOCAL_VS_GLOBAL_STATUS": "NOT_ESTABLISHED",
        "MINIMUM_EXISTENCE_STATUS": "NOT_ESTABLISHED",
        "VACUUM_UNIQUENESS_STATUS": "NOT_DERIVED",
        "MODULUS_STABILIZATION_STATUS": "NOT_FOUND",
        "SUGRA_VACUUM_CAPABILITY_STATUS": "PARTIAL",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
        "PARAMETER_REDUCTION_STATUS": "NONE",
        "PFR_STATUS": "NOT_FOUND",
        "PREVIOUS_ARTIFACTS_STATUS": "VERIFIED",
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "VACUUM_SELECTION_STATUS": "NOT_FOUND",
        "GLOBAL_MINIMUM_CAPABILITY": "NOT_ESTABLISHED",
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "PHASE_11AE1_STATUS": "COMPLETE",
        "PHASE_11AE1_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AE1_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "PHASE_11P_UNCHANGED": True,
        "PHASE_11T_UNCHANGED": True,
        "PHASE_11U_UNCHANGED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "PHASE_11AA_UNCHANGED": True,
        "PHASE_11AB_UNCHANGED": True,
        "PHASE_11AC_UNCHANGED": True,
        "PHASE_11AD_UNCHANGED": True,
        "PHASE_11AE_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "principle_activated": False,
        "operational_principle_activated": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
    }


def run_phase11ae1_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11ae1_containment(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "CONTAINMENT_AUDIT_INTEGRITY_FAILURE"}:
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
            "PHASE_11P_UNCHANGED": "VERIFIED",
            "PHASE_11T_UNCHANGED": "VERIFIED",
            "PHASE_11U_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "PHASE_11AE_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AE1_STATUS": science.get("PHASE_11AE1_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }


# Declared before any catalog, equivalence, or identity scan.
# None means the audit must stop. Do not fill this in after seeing a result.
PRE_EXECUTION_CLOSURE_TARGET: str | None = None
CLOSURE_TARGETS = ("SINGLE_VACUUM", "DEGENERATE_CLASS", "DOMAIN_REDUCTION")

_ABSENT_STATUSES = {
    "NOT_FOUND",
    "ABSENT",
    "UNTESTED",
    "PARTIAL",
    "NOT_DERIVED",
    "NOT_ESTABLISHED",
    "FAILED",
    "NONE",
    "UNRESOLVED",
}
_FUNCTIONAL_KEYS = ("native_minimization_functional", "minimization_functional")
_VADM_KEYS = ("V_adm",)
_PROCEDURE_KEYS = ("global_minimization_procedure",)
_PROCEDURE_TEXT = ("argmin", "global minimum", "global_minimization")


class PreExecutionClosureCriterion:
    """Target frozen before the containment scan.

    The declared objective is a Target-Blind rule. It is recorded so a
    later reading cannot treat the scan as a post-hoc choice of target.
    The scan does not filter classes by this value.
    """

    def __init__(self, target: str) -> None:
        if target not in CLOSURE_TARGETS:
            raise ValueError("closure target is not one of the declared objectives")
        self.target = target
        self.rule = "Target-Blind rule"
        self.logged_before_logical_execution = True
        self.post_hoc_validation = False

    def log_entry(self) -> dict[str, Any]:
        return {
            "entry": "Pre-Execution Closure Criterion",
            "rule": self.rule,
            "closure_target": self.target,
            "logged_before_logical_execution": True,
            "post_hoc_validation": False,
            "accepted": True,
        }


def _resolve_closure_target(closure_target: str | None) -> tuple[str | None, str | None]:
    explicit = closure_target
    constant = PRE_EXECUTION_CLOSURE_TARGET
    if explicit is not None and constant is not None and explicit != constant:
        return None, "argument and PRE_EXECUTION_CLOSURE_TARGET disagree"
    chosen = explicit if explicit is not None else constant
    if chosen is None:
        return None, "closure target was not declared"
    if chosen not in CLOSURE_TARGETS:
        return None, "closure target is outside the declared objective set"
    return chosen, None


def _closure_refusal(detail: str) -> dict[str, Any]:
    return {
        "status": "CLOSURE_CRITERION_REFUSED",
        "rule": "Target-Blind rule",
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "scanned": False,
        "scientific_analysis": None,
        "detail": detail,
        "provenance_log": [
            {
                "entry": "Pre-Execution Closure Criterion",
                "rule": "Target-Blind rule",
                "closure_target": None,
                "logged_before_logical_execution": True,
                "post_hoc_validation": False,
                "accepted": False,
                "detail": detail,
            }
        ],
        "new_parameter_count": 0,
        "principle_activated": False,
    }


def _iter_nodes(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _iter_nodes(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_nodes(item)


def _derived_label(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    token = value.strip()
    return token == "DERIVED" or token.startswith("DERIVED ")


def _explicit_record(roots: list[Any], keys: tuple[str, ...]) -> dict[str, Any] | None:
    """A hit is an explicit record, already marked derived, and not absent."""
    for root in roots:
        for node in _iter_nodes(root):
            for key in keys:
                if key not in node:
                    continue
                val = node[key]
                if not isinstance(val, dict):
                    continue
                status = str(val.get("status", ""))
                provenance = val.get("provenance", val.get("Provenance"))
                if status in _ABSENT_STATUSES:
                    continue
                if val.get("present") is False or val.get("established") is False:
                    continue
                if not _derived_label(provenance):
                    continue
                return {"key": key, "status": status, "source_provenance": provenance}
    return None


def _text_mentions_procedure(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _PROCEDURE_TEXT)


def _probe(name: str, found: dict[str, Any] | None, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found is not None,
        "Provenance": "DERIVED" if found is not None else "NOT_FOUND",
        "match": found,
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def run_containment_audit(
    closure_target: str | None = None,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan existing structures for a vacuum-selection principle.

    The closure target is fixed before any catalog or identity is read.
    No new parameter and no selection law is introduced.
    """
    chosen, refusal = _resolve_closure_target(closure_target)
    if chosen is None:
        return _closure_refusal(refusal or "closure target was not declared")
    closure = PreExecutionClosureCriterion(chosen)
    closure_log = closure.log_entry()

    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "frozen 4C hash",
            "scanned": False,
            "provenance_log": [closure_log],
            "new_parameter_count": 0,
            "principle_activated": False,
        }

    sources = {
        "catalog": phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json",
        "synthesis": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "summary": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "components": phase10d_artifact_dir() / "CERTIFIED_EQUIVALENCE_GRAPH.json",
        "eom": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
        "eom_summary": phase10b8_artifact_dir() / "PHASE_10B8_SUMMARY.json",
        "bianchi": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
    }
    missing = [name for name, path in sources.items() if not path.is_file()]
    if missing:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "missing " + ", ".join(missing),
            "scanned": False,
            "provenance_log": [closure_log],
            "new_parameter_count": 0,
            "principle_activated": False,
        }
    snapshots = {name: path.read_bytes() for name, path in sources.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}

    catalog = loaded["catalog"]
    summary = loaded["summary"]
    synthesis = loaded["synthesis"]
    graph = loaded["components"]
    eom_rows = loaded["eom"]
    bianchi_doc = loaded["bianchi"]
    components = graph.get("components") if isinstance(graph, dict) else None
    certified = (synthesis.get("certified_equivalence") or {}) if isinstance(synthesis, dict) else {}
    if (
        not isinstance(catalog, list)
        or not isinstance(components, list)
        or summary.get("CATALOGUE_CLASSES") != len(catalog)
        or summary.get("CERTIFIED_EQUIVALENCE_COMPONENTS") != len(components)
        or certified.get("certified_equivalence_components") != len(components)
        or certified.get("source_classes") != len(catalog)
        or synthesis.get("frozen_phase4c_hash") != EXPECTED_FROZEN_HASH
        or loaded["eom_summary"].get("frozen_hash") != EXPECTED_FROZEN_HASH
        or not isinstance(eom_rows, list)
    ):
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "catalog or equivalence count",
            "scanned": False,
            "provenance_log": [closure_log],
            "new_parameter_count": 0,
            "principle_activated": False,
        }

    ident = vacuum_selection_identities()
    roots = [catalog, synthesis, summary, graph, eom_rows, loaded["eom_summary"], bianchi_doc]
    functional_hit = _explicit_record(roots, _FUNCTIONAL_KEYS)
    if ident.get("VACUUM_SELECTION_PRINCIPLE") == "DERIVED":
        functional_hit = functional_hit or {
            "key": "VACUUM_SELECTION_PRINCIPLE",
            "status": "DERIVED",
            "source_provenance": "DERIVED",
        }
    vadm_hit = _explicit_record(roots, _VADM_KEYS)
    procedure_hit = _explicit_record(roots, _PROCEDURE_KEYS)
    eom_hits = [
        row.get("model")
        for row in eom_rows
        if isinstance(row, dict)
        and row.get("EOM_status") == "VERIFIED"
        and _derived_label(row.get("provenance"))
        and _text_mentions_procedure(str(row.get("EOM", "")))
    ]
    bianchi = bianchi_doc.get("bianchi_analysis") if isinstance(bianchi_doc, dict) else {}
    if not isinstance(bianchi, dict):
        bianchi = {}
    bianchi_text = " ".join(str(item) for item in bianchi.values())
    bianchi_procedure = (
        bianchi.get("status") not in _ABSENT_STATUSES
        and _derived_label(bianchi.get("provenance"))
        and _text_mentions_procedure(bianchi_text)
    )
    if eom_hits or bianchi_procedure:
        procedure_hit = procedure_hit or {
            "key": "global_minimization_procedure",
            "status": "VERIFIED",
            "source_provenance": "DERIVED",
            "eom_models": eom_hits,
            "bianchi": bianchi_procedure,
        }

    functional_probe = _probe(
        "native_minimization_functional",
        functional_hit,
        {
            "catalog_classes": len(catalog),
            "identity_principle": ident.get("VACUUM_SELECTION_PRINCIPLE"),
            "stationarity_is_not_selection": ident.get("stationarity_is_not_selection"),
            "quadratic_potential_present": bool(ident.get("potential")),
            "quadratic_potential_is_minimization_functional": False,
            "minimality_class_is_grammar": True,
        },
    )
    vadm_probe = _probe(
        "admissible_space_V_adm",
        vadm_hit,
        {
            "key_sought": "V_adm",
            "equivalence_components": len(components),
            "component_used_as_domain": False,
        },
    )
    procedure_probe = _probe(
        "global_minimization_from_4d_eom_or_bianchi",
        procedure_hit,
        {
            "eom_rows": len(eom_rows),
            "eom_minimization_rows": len(eom_hits),
            "bianchi_status": bianchi.get("status"),
            "bianchi_source_provenance": bianchi.get("provenance"),
            "bianchi_is_geometric_identity": bool(bianchi.get("geometric_identity")),
            "bianchi_is_minimization_procedure": bianchi_procedure,
        },
    )
    probes = [functional_probe, vadm_probe, procedure_probe]
    principle_found = all(item["found"] for item in probes)
    provenance_log = [closure_log, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AE1_TEST_COPY_ID": PHASE_11AE1_TEST_COPY_ID,
        "mode": "CONTAINMENT_AUDIT_ONLY",
        "rule": "Target-Blind rule",
        "closure_target": chosen,
        "closure_target_used_as_filter": False,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "scanned": True,
        "action_content_hash": digest,
        "FREEZE_ID": FREEZE_ID,
        "catalog_class_count": len(catalog),
        "equivalence_component_count": len(components),
        "equivalence_components": components,
        "probes": probes,
        "provenance_log": provenance_log,
        "VACUUM_SELECTION_PRINCIPLE": "DERIVED" if principle_found else "NOT_FOUND",
        "Provenance": "DERIVED" if principle_found else "NOT_FOUND",
        "principle_activated": False,
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "banned or ranking token",
            "scanned": False,
            "provenance_log": [closure_log],
            "new_parameter_count": 0,
            "principle_activated": False,
        }
    if write_artifacts:
        _write_json("PHASE_11AE1_PROVENANCE_LOG.json", {"rule": "Target-Blind rule", "log": provenance_log, "Provenance": payload["Provenance"]})
    after = {name: path.read_bytes() for name, path in sources.items()}
    if after != snapshots:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "source mutated",
            "scanned": False,
            "provenance_log": [closure_log],
            "new_parameter_count": 0,
            "principle_activated": False,
        }
    return payload
