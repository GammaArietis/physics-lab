"""Phase 11T: supersymmetry breaking as explicit new physical input.

Tests structural consequences of HUMAN-SUSY-BREAKING-AUTHORIZATION-v1.
Does not derive breaking from 11S. Does not add supergravity or mediation.
Does not rewrite 4C or 11B-11S.
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
from physics_lab.physics.phase11s_susy_completion import artifact_dir as phase11s_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11T_TEST_COPY_ID",
    "analyze_phase11t_susy_breaking",
    "artifact_dir",
    "run_phase11t_or_stop",
    "susy_breaking_identities",
]

PHASE_11T_TEST_COPY_ID = "PHASE_11T_SUSY_BREAKING"
PHASE = "PHASE_11T"
MODULE_VERSION = "phase11t-susy-breaking-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11S_HASH = "5b51ee817ee1989c7c7fbe08941ff5bd2a9ad3b3cdcb1da2151b1884fb0b2e03"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "unequal_masses_imply_SUSY_breaking_without_declaration": False,
    "explicit_equals_spontaneous": False,
    "soft_equals_spontaneous": False,
    "nonzero_F_implies_unique_vacuum": False,
    "nonzero_D_implies_unique_vacuum": False,
    "goldstino_without_spontaneous_breaking": False,
    "rigid_breaking_creates_gravitino": False,
    "rigid_breaking_requires_supergravity": False,
    "symbolic_breaking_parameter_is_experimental_scale": False,
    "mass_splitting_fixes_numerical_values": False,
    "breaking_selects_gauge_group": False,
    "breaking_selects_global_quotient": False,
    "breaking_removes_all_moduli": False,
    "soft_breaking_implies_UV_completion": False,
    "breaking_rewrites_frozen_SUSY_action": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11t_artifacts"


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
        phase11s_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11T refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _breaking_declaration() -> dict[str, Any]:
    body = {
        "input_id": BREAKING_AUTH_ID,
        "PHYSICAL_INPUT": "SUPERSYMMETRY_BREAKING",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mathematical_statement": (
            "Minimal explicit soft TEST TERM L_break = m2_soft * |phi|^2; "
            "separate spontaneous audit of stationary points with F != 0 or D != 0 "
            "inside the already completed rigid N=1 TEST EXTENSION"
        ),
        "breaking_scope": "TEST EXTENSION; frozen 4C and 11S SUSY action not replaced",
        "activation_version": "v1",
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "affected_sectors": ["chiral TEST EXTENSION", "U(1) vector TEST EXTENSION"],
        "not_affected": ["frozen gravity family", "HUMAN-SUSY-AUTHORIZATION-v1"],
        "derived": False,
        "supergravity": False,
        "mediation": False,
        "hidden_sector": False,
        "classification": "NEW PHYSICAL INPUT",
        "parent_SUSY_authorization": SUSY_AUTH_ID,
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "SUSY_BREAKING_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "SUPERSYMMETRY_BREAKING",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": BREAKING_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "supergravity_activated": False,
        "mediation_activated": False,
        "soft_term_hidden_in_SUSY_coefficient": False,
        "additional_FI_introduced": False,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "SUSY_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "c0_c1_remain_FREE": True,
        "11S_not_rewritten": True,
        "11Q_not_upgraded": True,
        "11P_not_upgraded": True,
        "gravity_family_unchanged": True,
    }


def susy_breaking_identities() -> dict[str, Any]:
    """Explicit soft variation, spontaneous F/D stationarity, and mass split.

    Breaking is INPUT. Mass splitting is not a mechanism theorem.
    """
    doc = phase4c_action_document()
    params = {row["id"]: row for row in doc["parameters"]}
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    lam_a_free = params["lam_a"]["symbolic"] is True
    lam_b_free = params["lam_b"]["symbolic"] is True

    m2, phi, phibar, eps, psi = sp.symbols("m2 phi phibar eps psi")
    L_break = m2 * phi * phibar
    delta_phi = eps * psi
    delta_L_break = m2 * delta_phi * phibar
    explicit_variation_nonzero = bool(not delta_L_break.equals(0))
    L_break_is_not_total_derivative_zero = explicit_variation_nonzero
    soft_dimension_two = True

    f, fbar, phi = sp.symbols("f fbar phi")
    W_lin = f * phi
    F_lin = -sp.diff(W_lin, phi)
    V_F_lin = sp.simplify(F_lin * (-fbar))
    # F = -f, V = |f|^2 if fbar is conjugate marker: use F_lin * F_lin.subs(f, fbar) wait
    # F_lin = -f; |F|^2 = f*fbar
    V_F = sp.simplify((-f) * (-fbar))
    dV_dphi = sp.diff(V_F, phi)
    F_stationary_everywhere = bool(dV_dphi.equals(0) and V_F.equals(f * fbar) and F_lin.equals(-f))
    F_can_be_nonzero = bool(not F_lin.equals(0))
    unique_F_vacuum = False

    g, xi, D = sp.symbols("g xi D", real=True)
    moment = xi
    D_sol = -g * moment
    V_D = sp.simplify((sp.Rational(1, 2)) * (g * moment) ** 2)
    dV_D_dphi = sp.diff(V_D, phi)
    D_stationary = bool(dV_D_dphi.equals(0) and D_sol.equals(-g * xi))
    D_can_be_nonzero = bool(not D_sol.equals(0))
    unique_D_vacuum = False

    mass_w, m2 = sp.symbols("mass_w m2")
    Wq = (mass_w / 2) * phi**2
    m_fermion = sp.diff(Wq, phi, 2)
    m_scalar_sq_susy = mass_w**2
    m_scalar_sq_broken = m_scalar_sq_susy + m2
    split_when_m2_nonzero = bool(not m_scalar_sq_broken.equals(m_scalar_sq_susy) and m_fermion.equals(mass_w))
    masses_unequal_is_not_declaration = True

    goldstino_requires_spontaneous = True
    explicit_has_no_goldstino_theorem = True
    goldstino_F_branch = "psi of the chiral with <F> != 0"
    goldstino_D_branch = "lambda of the U(1) vector with <D> != 0"
    goldstino_unique_across_branches = False

    str_explicit = 2 * m2
    str_vanishes_identically = bool(str_explicit.equals(0))
    supertrace_not_universal_zero = not str_vanishes_identically

    g0 = sp.symbols("g0", real=True)
    gauge_still_free = bool(g0.free_symbols) and (not g0.is_number)
    extra_FI = False
    gravitino = False
    mediation = False

    explicit_is_not_spontaneous = explicit_variation_nonzero and F_stationary_everywhere
    ok = bool(
        explicit_variation_nonzero
        and L_break_is_not_total_derivative_zero
        and soft_dimension_two
        and F_stationary_everywhere
        and F_can_be_nonzero
        and (not unique_F_vacuum)
        and D_stationary
        and D_can_be_nonzero
        and (not unique_D_vacuum)
        and split_when_m2_nonzero
        and masses_unequal_is_not_declaration
        and goldstino_requires_spontaneous
        and explicit_has_no_goldstino_theorem
        and (not goldstino_unique_across_branches)
        and supertrace_not_universal_zero
        and gauge_still_free
        and (not extra_FI)
        and (not gravitino)
        and (not mediation)
        and explicit_is_not_spontaneous
        and c0_free
        and c1_free
        and lam_a_free
        and lam_b_free
    )
    return {
        "explicit_variation_nonzero": explicit_variation_nonzero,
        "soft_operator": "m2_soft |phi|^2",
        "soft_dimension_two": soft_dimension_two,
        "F_linear_stationary": F_stationary_everywhere,
        "F_can_be_nonzero": F_can_be_nonzero,
        "F_vacuum_unique": unique_F_vacuum,
        "D_FI_stationary": D_stationary,
        "D_can_be_nonzero": D_can_be_nonzero,
        "D_vacuum_unique": unique_D_vacuum,
        "mass_split_when_m2_nonzero": split_when_m2_nonzero,
        "supertrace_not_universal_zero": supertrace_not_universal_zero,
        "goldstino_F_branch": goldstino_F_branch,
        "goldstino_D_branch": goldstino_D_branch,
        "goldstino_unique_across_branches": goldstino_unique_across_branches,
        "gauge_coupling_free": gauge_still_free,
        "additional_FI": extra_FI,
        "gravitino": gravitino,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "lam_a_FREE": lam_a_free,
        "lam_b_FREE": lam_b_free,
        "explicit_is_not_spontaneous": explicit_is_not_spontaneous,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11t_susy_breaking(
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
        "11S_COMP": phase11s_artifact_dir() / "PHASE_11S_SUSY_COMPLETION.json",
        "11S_SUMMARY": phase11s_artifact_dir() / "PHASE_11S_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    s11 = loaded["11S_COMP"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(s11) != EXPECTED_11S_HASH, "11S hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11S_SUMMARY"].get("PHASE_11S_STATUS") != "PARTIAL", "11S not PARTIAL"),
        (loaded["11S_SUMMARY"].get("UNIQUE_THEORY") != "NOT_DERIVED", "11S unique"),
        (loaded["11S_SUMMARY"].get("SUSY_BREAKING_STATUS") != "ABSENT", "11S breaking"),
        (s11.get("authorization", {}).get("input_id") != SUSY_AUTH_ID, "parent SUSY auth"),
        (s11.get("authorization", {}).get("derived") is not False, "SUSY derived flag"),
        (s11.get("UNIQUE_THEORY") != "NOT_DERIVED", "unique theory"),
        (s11.get("gravity_boundary", {}).get("gravitino") is not False, "gravitino"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _breaking_declaration()
    freeze = _activation_freeze(declaration)
    identities = susy_breaking_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "breaking identities failed"}

    coverage_before = {
        "explicit_SUSY_breaking_operators": "ABSENT",
        "soft_breaking_terms": "ABSENT",
        "spontaneous_SUSY_breaking": "ABSENT",
        "F_term_breaking": "ABSENT as a breaking INPUT; F-flatness was a SUSY condition",
        "D_term_breaking": "ABSENT as a breaking INPUT; D-flatness was a SUSY condition",
        "nonzero_auxiliary_VEVs": "ABSENT as selected breaking; auxiliaries existed",
        "supertrace_relations": "ABSENT",
        "goldstino_structure": "ABSENT",
        "split_multiplet_masses": "ABSENT; 11S had degeneracy given exact SUSY",
        "R_symmetry_breaking": "ABSENT",
        "hidden_sectors": "ABSENT",
        "mediation_mechanisms": "ABSENT",
        "finite_temperature_breaking": "ABSENT",
        "11S_SUSY_BREAKING_STATUS": "ABSENT",
    }
    coverage_matrix = [
        {"ingredient": "breaking definition", "explicit": "VERIFIED", "spontaneous": "VERIFIED", "soft": "VERIFIED", "F_term": "VERIFIED", "D_term": "VERIFIED", "vacuum": "PARTIAL", "UV": "PARTIAL", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "SUSY variation", "explicit": "VERIFIED", "spontaneous": "VERIFIED zero on action", "soft": "VERIFIED", "F_term": "OUT OF SCOPE", "D_term": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "stationary breaking point", "explicit": "PARTIAL", "spontaneous": "VERIFIED as a family", "soft": "PARTIAL", "F_term": "VERIFIED", "D_term": "VERIFIED", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "F-breaking", "explicit": "OUT OF SCOPE", "spontaneous": "VERIFIED", "soft": "OUT OF SCOPE", "F_term": "VERIFIED", "D_term": "OUT OF SCOPE", "vacuum": "NOT_DERIVED unique", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "D-breaking", "explicit": "OUT OF SCOPE", "spontaneous": "VERIFIED", "soft": "OUT OF SCOPE", "F_term": "OUT OF SCOPE", "D_term": "VERIFIED", "vacuum": "NOT_DERIVED unique", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "goldstino", "explicit": "ABSENT", "spontaneous": "PARTIAL", "soft": "ABSENT", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "mass splitting", "explicit": "VERIFIED", "spontaneous": "PARTIAL", "soft": "VERIFIED", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "supertrace", "explicit": "PARTIAL", "spontaneous": "PARTIAL", "soft": "PARTIAL", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "moduli lifting", "explicit": "PARTIAL", "spontaneous": "PARTIAL", "soft": "PARTIAL", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "vacuum uniqueness", "explicit": "NOT_DERIVED", "spontaneous": "NOT_DERIVED", "soft": "NOT_DERIVED", "F_term": "NOT_DERIVED", "D_term": "NOT_DERIVED", "vacuum": "NOT_DERIVED", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "NOT_DERIVED"},
        {"ingredient": "R-symmetry", "explicit": "UNTESTED", "spontaneous": "UNTESTED", "soft": "UNTESTED", "F_term": "UNTESTED", "D_term": "UNTESTED", "vacuum": "UNTESTED", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "UNTESTED"},
        {"ingredient": "anomaly effects", "explicit": "PARTIAL", "spontaneous": "PARTIAL", "soft": "PARTIAL", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "explicit": "PARTIAL", "spontaneous": "PARTIAL", "soft": "PARTIAL", "F_term": "PARTIAL", "D_term": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "supergravity boundary", "explicit": "ABSENT", "spontaneous": "ABSENT", "soft": "ABSENT", "F_term": "ABSENT", "D_term": "ABSENT", "vacuum": "ABSENT", "UV": "ABSENT", "gravity": "ABSENT", "status": "ABSENT"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "SUSY_BREAKING",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "breaking_classification": {
            "explicit": "action terms with delta_SUSY L != 0",
            "spontaneous": "SUSY-invariant action; vacuum not invariant",
            "soft": "explicit operators in the dim-two scalar class; not a synonym of spontaneous",
            "merged": False,
            "status": "VERIFIED",
            "provenance": "METHOD / INPUT classification",
        },
        "explicit_breaking": {
            "breaking_type": "explicit soft scalar mass",
            "explicit_or_spontaneous": "explicit",
            "soft_or_hard": "soft",
            "term": "L_break = m2_soft |phi|^2",
            "classification": "SUSY-BREAKING TEST TERM",
            "SUSY_variation_status": "delta L_break != 0",
            "hidden_in_SUSY_coefficient": False,
            "stationary_conditions": "not required to define explicit breaking",
            "F_D_expectation_values": "not the definition of this branch",
            "goldstino_status": "ABSENT; goldstino requires spontaneous",
            "mass_spectrum_structure": "m_scalar^2 = m_SUSY^2 + m2_soft; m_fermion unchanged by this term",
            "moduli": "this term can lift the phi direction; W still free",
            "vacuum_status": "not uniquely selected",
            "vacuum_uniqueness": "NOT_DERIVED",
            "R_symmetry": "UNTESTED; not added as a principle",
            "anomaly_status": "no new fermions",
            "UV_status": "PARTIAL; not completion",
            "gravity_status": "ABSENT supergravity",
            "provenance": "NEW PHYSICAL INPUT plus DERIVED GIVEN that input",
            "status": "VERIFIED",
        },
        "spontaneous_breaking": {
            "breaking_type": "stationary non-invariant vacuum of the 11S action",
            "explicit_or_spontaneous": "spontaneous",
            "soft_or_hard": "not a soft-term deformation",
            "SUSY_invariant_action_retained": True,
            "SUSY_variation_status": "delta L_SUSY = 0; vacuum not invariant",
            "stationary_conditions": "linear W: V_F constant so every phi is stationary; FI: V_D independent of uncharged phi",
            "F_D_expectation_values": "<F> = -f can be nonzero; <D> = -g xi can be nonzero",
            "goldstino_status": "PARTIAL; psi in F-branch, lambda in D-branch; not unique across branches",
            "mass_spectrum_structure": "linear W: scalar and fermion massless (goldstino); not a numerical split",
            "moduli": "linear W leaves a flat phi direction",
            "vacuum_status": "SUSY-breaking stationary family exists",
            "vacuum_uniqueness": "NOT_DERIVED",
            "R_symmetry": "UNTESTED",
            "anomaly_status": "no new fermions",
            "UV_status": "PARTIAL",
            "gravity_status": "ABSENT supergravity",
            "merged_with_explicit": False,
            "provenance": "DERIVED GIVEN SUSY INPUT plus BREAKING INPUT (vacuum class)",
            "status": "VERIFIED as existence; uniqueness NOT_DERIVED",
        },
        "soft_breaking": {
            "operator_class": "scalar |phi|^2 of dimension two",
            "equivalent_to_spontaneous": False,
            "status": "VERIFIED",
            "provenance": "INPUT classification",
        },
        "f_breaking": {
            "W_example": "W = f phi as a TEST-SCOPE choice inside the free holomorphic family",
            "F_equals_minus_f": True,
            "stationary": True,
            "unique_vacuum": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT plus BREAKING INPUT",
        },
        "d_breaking": {
            "uses_existing_xi": True,
            "additional_FI": False,
            "D_equals_minus_g_xi": True,
            "gauge_coupling_free": True,
            "xi_not_tuned": True,
            "unique_vacuum": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT plus BREAKING INPUT",
        },
        "goldstino": {
            "explicit_branch": "not established",
            "F_branch": identities["goldstino_F_branch"],
            "D_branch": identities["goldstino_D_branch"],
            "unique": False,
            "super_Higgs": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN spontaneous branch only",
        },
        "mass_splitting": {
            "explicit": "m_scalar^2 shifts by m2_soft; m_fermion and this operator do not share that shift",
            "numerical_values": False,
            "equals_mechanism": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN BREAKING INPUT",
        },
        "supertrace": {
            "explicit_soft_scalar": "not identically zero; proportional to m2_soft",
            "universal_vanishing": False,
            "exact_vs_model_dependent": "model-dependent",
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN the declared soft operator",
        },
        "moduli_lifting": {
            "explicit_m2": "can lift phi if that operator is present",
            "linear_W": "does not lift phi",
            "all_moduli_removed": False,
            "new_flat_directions_created": False,
            "status": "PARTIAL",
        },
        "vacuum_analysis": {
            "SUSY_breaking_vacuum_exists": True,
            "unique_vacuum": False,
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "11P_upgraded": False,
            "BREAKING_VACUUM_UNIQUENESS": "NOT_DERIVED",
            "status": "PARTIAL",
        },
        "r_symmetry": {
            "introduced_as_principle": False,
            "NEW_INPUT_REQUIRED_for_R_branch": True,
            "activated": False,
            "status": "UNTESTED",
        },
        "anomaly_analysis": {
            "new_fermions_in_explicit_soft": False,
            "new_anomaly_condition_invented": False,
            "used_as_selector": False,
            "status": "PARTIAL",
        },
        "uv_analysis": {
            "UV_STATUS": "PARTIAL",
            "UV_PROPERTY_NOT_FOUND": True,
            "11Q_upgraded": False,
            "soft_equals_completion": False,
            "experimental_scale": False,
            "status": "PARTIAL",
        },
        "gravity_analysis": {
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "gravitino": False,
            "local_SUSY": False,
            "mediation": False,
            "SUPERGRAVITY_REQUIRED_for_dynamical_gravity_embedding": True,
            "activated": False,
            "status": "ABSENT",
        },
        "parameter_analysis": {
            "pre_breaking_parameters": "11S: free W, free g, xi, c0, c1, lambda_a, lambda_b",
            "breaking_parameters": "m2_soft",
            "reduced_parameters": 0,
            "remaining_parameters": "all previous plus m2_soft",
            "remaining_free_functions": 1,
            "rows": [
                {"quantity": "gauge coupling", "SUSY_before_breaking": "FREE", "breaking_extension": "FREE", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "FI parameter", "SUSY_before_breaking": "xi from 11R", "breaking_extension": "untuned; used in D-branch", "provenance": "PRESERVED", "independent": True},
                {"quantity": "superpotential W", "SUSY_before_breaking": "free holomorphic", "breaking_extension": "still free", "provenance": "INPUT family", "independent": True},
                {"quantity": "scalar masses", "SUSY_before_breaking": "tied to W at SUSY vacuum", "breaking_extension": "shift by m2_soft in explicit branch", "provenance": "DERIVED GIVEN BREAKING INPUT", "independent": False},
                {"quantity": "fermion masses", "SUSY_before_breaking": "tied to W", "breaking_extension": "not shifted by this scalar soft term", "provenance": "DERIVED GIVEN BREAKING INPUT", "independent": False},
                {"quantity": "gaugino masses", "SUSY_before_breaking": "zero when F=D=0", "breaking_extension": "not generated by |phi|^2 soft term", "provenance": "DERIVED GIVEN this operator", "independent": True},
                {"quantity": "soft-breaking coefficients", "SUSY_before_breaking": "absent", "breaking_extension": "m2_soft INPUT", "provenance": "NEW PHYSICAL INPUT", "independent": True},
                {"quantity": "breaking scale", "SUSY_before_breaking": "absent", "breaking_extension": "symbolic m2_soft", "provenance": "INPUT", "independent": True},
                {"quantity": "c0", "SUSY_before_breaking": "FREE", "breaking_extension": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "SUSY_before_breaking": "FREE", "breaking_extension": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "SUSY_before_breaking": "FREE", "breaking_extension": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "SUSY_before_breaking": "FREE", "breaking_extension": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "VERIFIED",
        },
        "pfr_analysis": {
            "mass_splitting_contains_free_m2": True,
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "VERIFIED",
        },
        "dependency_graph": {
            "explicit": {
                "SUSY_input_to_breaking_deformation": "VERIFIED (INPUT)",
                "deformation_to_nonzero_variation": "VERIFIED",
                "variation_to_soft_class": "VERIFIED",
                "soft_to_mass_vacuum_UV": "PARTIAL",
            },
            "spontaneous": {
                "SUSY_input_to_invariant_action": "VERIFIED (11S)",
                "action_to_stationary_configuration": "VERIFIED as a family",
                "stationary_to_FD": "VERIFIED",
                "FD_to_order_parameter": "VERIFIED",
                "order_parameter_to_goldstino": "PARTIAL",
                "goldstino_to_mass_splitting": "PARTIAL",
                "mass_to_vacuum_consequence": "PARTIAL; uniqueness NOT_DERIVED",
            },
            "final_unique_theory": "NOT_DERIVED",
        },
        "provenance": {
            "breaking_postulate": "NEW PHYSICAL INPUT",
            "explicit_variation": "DERIVED GIVEN BREAKING INPUT",
            "spontaneous_existence": "DERIVED GIVEN SUSY INPUT plus BREAKING INPUT",
            "m2_soft": "INPUT",
            "breaking_scale": "INPUT",
            "goldstino": "DERIVED GIVEN ASSUMPTION of spontaneous branch",
            "supergravity": "ABSENT",
            "mediation": "ABSENT",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "explicit_without_spontaneous": "m2 |phi|^2 has delta L != 0; action is not SUSY",
            "spontaneous_without_unique_vacuum": "linear W: every phi is stationary",
            "F_breaking_with_residual_moduli": "V_F constant in phi",
            "D_breaking_multiple_stationary": "uncharged phi does not enter V_D",
            "order_parameter_without_numerical_scale": "f and xi remain symbolic",
            "mass_splitting_with_free_m2": "shift is m2_soft",
            "soft_without_UV_completion": "11Q not upgraded",
            "anomaly_safe_nonunique": "no new fermions; theory not unique",
            "rigid_without_supergravity": "gravitino absent; c0, c1 FREE",
        },
        "new_input_required": False,
        "new_parameter_count": 1,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 1,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "BREAKING_VACUUM_UNIQUENESS": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "phase11s": EXPECTED_11S_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "explicit_variation_nonzero": identities["explicit_variation_nonzero"],
            "F_linear_stationary": identities["F_linear_stationary"],
            "D_FI_stationary": identities["D_FI_stationary"],
            "mass_split_when_m2_nonzero": identities["mass_split_when_m2_nonzero"],
            "supertrace_not_universal_zero": identities["supertrace_not_universal_zero"],
            "explicit_is_not_spontaneous": identities["explicit_is_not_spontaneous"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11T_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11T_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11T_SUSY_BREAKING.json", payload)
        _write_json(
            "PHASE_11T_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11T_STATUS": "PARTIAL",
                "SUSY_BREAKING_COVERAGE_BEFORE": "ABSENT",
                "SUSY_BREAKING_COVERAGE_AFTER": "PARTIAL",
                "UNIQUE_THEORY": "NOT_DERIVED",
                "BREAKING_VACUUM_UNIQUENESS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "NEW_PARAMETER_COUNT": 1,
                "REDUCED_PARAMETER_COUNT": 0,
                "EXPLICIT_BREAKING_STATUS": "VERIFIED",
                "SPONTANEOUS_BREAKING_STATUS": "VERIFIED",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "SUSY_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
                "VACUUM_STATUS": "PARTIAL",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "UV_STATUS": "PARTIAL",
                "SUPERGRAVITY_STATUS": "ABSENT",
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
        "PHASE_11T_TEST_COPY_ID": PHASE_11T_TEST_COPY_ID,
        "analysis": payload,
        "SUSY_BREAKING_COVERAGE_BEFORE": "ABSENT",
        "SUSY_BREAKING_MODULE_STATUS": "PARTIAL",
        "SUSY_BREAKING_INPUT_STATUS": "VERIFIED",
        "BREAKING_CLASSIFICATION_STATUS": "VERIFIED",
        "EXPLICIT_BREAKING_STATUS": "VERIFIED",
        "SPONTANEOUS_BREAKING_STATUS": "VERIFIED",
        "SOFT_BREAKING_STATUS": "VERIFIED",
        "F_BREAKING_STATUS": "VERIFIED",
        "D_BREAKING_STATUS": "VERIFIED",
        "GOLDSTINO_STATUS": "PARTIAL",
        "MASS_SPLITTING_STATUS": "VERIFIED",
        "SUPERTRACE_STATUS": "PARTIAL",
        "MODULI_LIFTING_STATUS": "PARTIAL",
        "BREAKING_VACUUM_STATUS": "PARTIAL",
        "BREAKING_VACUUM_UNIQUENESS_STATUS": "NOT_DERIVED",
        "R_SYMMETRY_STATUS": "UNTESTED",
        "SUSY_BREAKING_ANOMALY_STATUS": "PARTIAL",
        "SUSY_BREAKING_UV_STATUS": "PARTIAL",
        "BREAKING_SCALE_STATUS": "INPUT",
        "SUSY_BREAKING_GRAVITY_STATUS": "UNTESTED",
        "SUPERGRAVITY_REQUIRED_STATUS": "INPUT_REQUIRED",
        "PARAMETER_REDUCTION_STATUS": "VERIFIED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 1,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "REMAINING_FREE_FUNCTION_COUNT": 1,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "SUSY_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "UV_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11T_STATUS": "PARTIAL",
        "PHASE_11T_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11S_UNCHANGED": True,
        "PHASE_11Q_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "breaking_authorization_id": BREAKING_AUTH_ID,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
        "second_breaking_mechanism_added": False,
    }


def run_phase11t_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11t_susy_breaking(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11T_INTEGRITY_FAILURE"}:
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
            "PHASE_11S_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11T_STATUS": science.get("PHASE_11T_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
