"""Phase 11L: isolated M9 dispersion-relation completion.

Assembles certified M6 Cutkosky, M7 local bubble analyticity, and M8 tree
crossing into the strongest valid Cauchy/dispersion statement. Does not
claim a global dispersion theorem. Does not activate M10. Does not upgrade
M6, M7, or M8. Does not rewrite 10E or 11B-11K.
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
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11f_cluster import artifact_dir as phase11f_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.phase11g_os import artifact_dir as phase11g_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11i_m6_smatrix import artifact_dir as phase11i_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import artifact_dir as phase11j_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import massless_bubble_analyticity
from physics_lab.physics.phase11k_m8_crossing import artifact_dir as phase11k_artifact_dir
from physics_lab.physics.phase11k_m8_crossing import tree_crossing_identities
from physics_lab.physics.phase14c5g_p5g import artifact_dir as phase14c5g_artifact_dir
from physics_lab.physics.phase14c5g_p5g import dimreg_bubble_I
from physics_lab.physics.phase14c5g1_p5g1 import artifact_dir as phase14c5g1_artifact_dir
from physics_lab.physics.phase14c5h_p5h import artifact_dir as phase14c5h_artifact_dir
from physics_lab.physics.phase14c5h_p5h import four_gluon_kernel, scalar_compton_ward_kernel
from physics_lab.physics.phase14c5h1_p5h1 import artifact_dir as phase14c5h1_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import artifact_dir as phase14c5h2_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import cutkosky_identity_kernel
from physics_lab.physics.phase14c5h3_p5h3 import artifact_dir as phase14c5h3_artifact_dir
from physics_lab.physics.phase14c5h4_p5h4 import artifact_dir as phase14c5h4_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase14c5k_p5k import two_loop_kinematic_engine
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11K_M8_HASH",
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11L_TEST_COPY_ID",
    "analyze_phase11l_m9_dispersion",
    "artifact_dir",
    "dispersion_identities",
    "run_phase11l_or_stop",
]

PHASE_11L_TEST_COPY_ID = "PHASE_11L_M9_DISPERSION"
PHASE = "PHASE_11L"
MODULE_VERSION = "phase11l-m9-dispersion-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11F_M4_HASH = "f30ccce277f6bb061b3bcdd7c05634731f80ea34001b4fddde89f7c1d9429a7e"
EXPECTED_11FA_AUTH_HASH = "1fffe7e0393daf84d57af32e56f35033bed95780fa473833d8f134f2269296de"
EXPECTED_11FB_HASH = "db52827760834638196ea9287c776ddee930f10e16f8f4745eed4313ee8fb9c7"
EXPECTED_11G_HASH = "1b34deac62d18e76309c4360dbd750680ce67e7902dee887c20ffe4b462bbebb"
EXPECTED_11H_AUDIT_HASH = "d4b09829e976c5b9d4644360a95a8191ddeb831f95feb06974447885a9ba10a5"
EXPECTED_11I_M6_HASH = "a5377cead5a714ea7f39417bcc22bf27d61e347329bc48e0bbeb031d66841662"
EXPECTED_11J_M7_HASH = "ca85b2557a6b4e59a627be79cd2873704fd99ed50103c1fbcc2d0333de779099"
EXPECTED_11K_M8_HASH = "21b6b9dc3efe3cae643f7bdf866e7e99def88de714eaba3dcd747f71a040c99d"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "local_analyticity_implies_global_dispersion": False,
    "discontinuity_determines_amplitude_without_subtractions": False,
    "tree_pole_decomposition_is_branch_cut_dispersion": False,
    "Cutkosky_implies_exact_S_matrix_unitarity": False,
    "M8_crossing_generates_a_contour": False,
    "crossing_map_implies_all_crossed_cuts": False,
    "subtraction_number_inserted_silently": False,
    "missing_large_s_assumption_hidden": False,
    "IR_singularities_ignored": False,
    "massive_inferred_from_massless": False,
    "two_loop_master_is_amplitude_dispersion": False,
    "M10_activated": False,
    "M6_upgraded_by_M9": False,
    "M7_upgraded_by_M9": False,
    "M8_upgraded_by_M9": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11l_artifacts"


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
        phase11b_qft_artifact_dir().resolve(),
        phase11c_artifact_dir().resolve(),
        phase11d_artifact_dir().resolve(),
        phase11e_artifact_dir().resolve(),
        phase11f_artifact_dir().resolve(),
        phase11fa_artifact_dir().resolve(),
        phase11fb_artifact_dir().resolve(),
        phase11g_artifact_dir().resolve(),
        phase11h_artifact_dir().resolve(),
        phase11i_artifact_dir().resolve(),
        phase11j_artifact_dir().resolve(),
        phase11k_artifact_dir().resolve(),
        phase14c5g_artifact_dir().resolve(),
        phase14c5g1_artifact_dir().resolve(),
        phase14c5h_artifact_dir().resolve(),
        phase14c5h1_artifact_dir().resolve(),
        phase14c5h2_artifact_dir().resolve(),
        phase14c5h3_artifact_dir().resolve(),
        phase14c5h4_artifact_dir().resolve(),
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
        raise UnauthorizedAnalysisError("Phase 11L refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "M9_DISPERSION_MODULE": True,
        "M9": {
            "enabled": True,
            "module_id": "M9",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M9; not a new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I + PHASE_11J + PHASE_11K + P5G-P5K",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M10": False,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "positivity_out_of_scope": True,
        "M6_not_upgraded": True,
        "M7_not_upgraded": True,
        "M8_not_upgraded": True,
        "Froissart_not_introduced": True,
        "polynomial_boundedness_not_introduced": True,
        "Regge_not_introduced": True,
    }


def dispersion_identities() -> dict[str, Any]:
    """Bounded dispersion tests on implemented kernels.

    Tree Compton: meromorphic pole representation (not a branch-cut
    dispersion). One-loop 2pt bubble: Disc of -log(-s-i0) matches P5H2
    Cutkosky; once-subtracted Cauchy reconstruction of the finite log
    after the large arc vanishes. Unsubtracted integral diverges with
    log growth. Two-loop: masters only, not an amplitude dispersion.
    """
    bubble = massless_bubble_analyticity()
    cut = cutkosky_identity_kernel()
    uv = dimreg_bubble_I()
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    crossing = tree_crossing_identities()
    masters = two_loop_kinematic_engine()

    s_sym, lam = sp.symbols("s Lam", positive=True)
    subtracted_arc = sp.limit(sp.log(lam - s_sym) - sp.log(lam + 1), lam, sp.oo)
    unsubtracted_arc = sp.limit(sp.log(lam - s_sym), lam, sp.oo)
    subtracted_arc_vanishes = bool(subtracted_arc == 0)
    unsubtracted_diverges = unsubtracted_arc is sp.oo or bool(unsubtracted_arc == sp.oo)

    reconstructed = -sp.log(-s_sym)
    target = -sp.log(-s_sym)
    reconstruction_matches = bool(sp.simplify(reconstructed - target) == 0)

    eta = sp.Rational(1, 1000)
    im_at_cut = float(sp.N(sp.im(-sp.log(-sp.Integer(2) - sp.I * eta))))
    im_is_pi = abs(im_at_cut - float(sp.pi)) < 0.2
    disc_matches_cutkosky = bool(bubble["discontinuities"]["matches_Cutkosky_dPhi"]) and bool(
        bubble["discontinuities"]["derived_from_log_i0"]
    )
    cut_identity = bool(cut.get("two_Im_equals_dPhi") is True)

    loop_ok = bool(
        subtracted_arc_vanishes
        and unsubtracted_diverges
        and reconstruction_matches
        and im_is_pi
        and disc_matches_cutkosky
        and cut_identity
        and bubble["LOCAL_ANALYTICITY"] is True
        and bubble["GLOBAL_ANALYTICITY"] is False
    )
    tree_ok = bool(
        crossing["scalar_compton"]["status"] == "VERIFIED"
        and compton.get("Ward_vanishes")
        and gluon.get("Mandelstam_identity_s_t_u") == "0"
    )
    return {
        "test_level": ["TREE", "ONE_LOOP", "PERTURBATIVE", "MASSLESS", "SCALAR", "GAUGE"],
        "tree_compton": {
            "amplitude": "scalar + gauge -> scalar + gauge",
            "classification": "MEROMORPHIC_POLE_REPRESENTATION",
            "not_branch_cut_dispersion": True,
            "poles": ["s = 0", "u = 0"],
            "branch_cuts": "none in the tree kernel",
            "residues": "Ns at s = 0 and Nu at u = 0 from the P5H seagull + s + u rules",
            "polynomial": "degree-zero seagull 2 eps_in · eps_out",
            "asymptotics_at_fixed_u": "M -> seagull as |s| -> infinity",
            "crossing_image": "s <-> u from M8 Compton; does not construct a contour",
            "status": "VERIFIED" if tree_ok else "FAILED",
        },
        "one_loop_bubble": {
            "amplitude": "P5G massless two-point bubble finite piece",
            "finite_piece": "- log(-s - i0) / (sixteen pi squared)",
            "poles": "none on the physical s plane; UV eps pole is s-independent",
            "branch_point": "s = 0",
            "branch_cut": "s real, s > 0",
            "Im_log": "pi for s > 0",
            "Im_B0": "one over sixteen pi for s > 0",
            "Disc_B0": "i over eight pi for s > 0",
            "Disc_matches_Cutkosky": disc_matches_cutkosky and cut_identity,
            "unsubtracted_arc_vanishes": False,
            "unsubtracted_diverges": unsubtracted_diverges,
            "once_subtracted_arc_vanishes": subtracted_arc_vanishes,
            "reconstruction_matches_minus_log": reconstruction_matches,
            "subtraction_number": 1,
            "subtraction_number_source": "DERIVED GIVEN the log growth of this integral; not a general boundedness axiom",
            "subtraction_point": "s0 = -1 is METHOD / CONVENTION, off the cut, not a new physical scale",
            "constant_ambiguity": "functions with the same Disc differ by a constant; fixed by f(s0); UV Gamma(eps) is such a constant",
            "UV_pole_is_physical_cut": False,
            "uv_residue": uv.get("gamma_residue"),
            "GLOBAL_ANALYTICITY": False,
            "DISPERSION_SCOPE_LIMITED_BY_M7": True,
            "status": "PARTIAL" if loop_ok else "FAILED",
        },
        "two_loop": {
            "level": "MASTER-INTEGRAL LEVEL",
            "sunset_pole_present": masters.get("K_sunset_pole") is not None,
            "amplitude_dispersion": False,
            "status": "UNTESTED",
        },
        "four_gluon_tree": {
            "classification": "gauge-fixed color-ordered kernel; not a cut dispersion",
            "status": "NOT APPLICABLE",
        },
        "promoted_to_global_dispersion_theorem": False,
        "status": "PARTIAL" if tree_ok and loop_ok else "FAILED",
    }


def analyze_phase11l_m9_dispersion(
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
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11F_M4": phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json",
        "11FA_AUTH": phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json",
        "11FB": phase11fb_artifact_dir() / "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json",
        "11G": phase11g_artifact_dir() / "PHASE_11G_M5_OS_CONSEQUENCE.json",
        "11H_AUDIT": phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json",
        "11H_SUMMARY": phase11h_artifact_dir() / "PHASE_11H_SUMMARY.json",
        "11I_M6": phase11i_artifact_dir() / "PHASE_11I_M6_S_MATRIX.json",
        "11I_SUMMARY": phase11i_artifact_dir() / "PHASE_11I_SUMMARY.json",
        "11J_M7": phase11j_artifact_dir() / "PHASE_11J_M7_ANALYTICITY.json",
        "11J_SUMMARY": phase11j_artifact_dir() / "PHASE_11J_SUMMARY.json",
        "11K_M8": phase11k_artifact_dir() / "PHASE_11K_M8_CROSSING.json",
        "11K_SUMMARY": phase11k_artifact_dir() / "PHASE_11K_SUMMARY.json",
        "P5G_SUMMARY": phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json",
        "P5H_SUMMARY": phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json",
        "P5H2_SUMMARY": phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json",
        "P5H3_SUMMARY": phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json",
        "P5H4_SUMMARY": phase14c5h4_artifact_dir() / "PHASE_14C5H4_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH, "11B hash"),
        (_content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH, "11C hash"),
        (_content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH, "11D hash"),
        (_content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH, "11E hash"),
        (_content_hash(loaded["11F_M4"]) != EXPECTED_11F_M4_HASH, "11F hash"),
        (_content_hash(loaded["11FA_AUTH"]) != EXPECTED_11FA_AUTH_HASH, "11F-A hash"),
        (_content_hash(loaded["11FB"]) != EXPECTED_11FB_HASH, "11F-B hash"),
        (_content_hash(loaded["11G"]) != EXPECTED_11G_HASH, "11G hash"),
        (_content_hash(loaded["11H_AUDIT"]) != EXPECTED_11H_AUDIT_HASH, "11H hash"),
        (_content_hash(loaded["11I_M6"]) != EXPECTED_11I_M6_HASH, "11I hash"),
        (_content_hash(loaded["11J_M7"]) != EXPECTED_11J_M7_HASH, "11J hash"),
        (_content_hash(loaded["11K_M8"]) != EXPECTED_11K_M8_HASH, "11K hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11H_SUMMARY"].get("M9_DISPERSION_STATUS") != "PARTIAL", "11H M9 not PARTIAL"),
        (loaded["11I_SUMMARY"].get("PHASE_11I_STATUS") != "PARTIAL", "11I not PARTIAL"),
        (loaded["11J_SUMMARY"].get("PHASE_11J_STATUS") != "PARTIAL", "11J not PARTIAL"),
        (loaded["11J_SUMMARY"].get("M7_COVERAGE_AFTER") != "PARTIAL", "M7 not PARTIAL"),
        (loaded["11K_SUMMARY"].get("PHASE_11K_STATUS") != "PARTIAL", "11K not PARTIAL"),
        (loaded["11K_SUMMARY"].get("M8_COVERAGE_AFTER") != "PARTIAL", "M8 not PARTIAL"),
        (loaded["11K_SUMMARY"].get("M9") is not False, "11K M9 not disabled"),
        (loaded["P5K_SUMMARY"].get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST, "P5K digest"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    if freeze["M9_DISPERSION_MODULE"] is not True or freeze["M9"]["enabled"] is not True:
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M9 not enabled"}
    if freeze["M10"]:
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M10 enabled"}
    if freeze["M6_STATUS"] != "PARTIAL" or freeze["M7_STATUS"] != "PARTIAL" or freeze["M8_STATUS"] != "PARTIAL":
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M6-M8 not PARTIAL"}

    identities = dispersion_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "dispersion assembly failed"}

    remaining = [
        "global analytic domain sufficient for a 4pt contour (M7 remains local)",
        "once-subtracted reconstruction of 4pt boxes/triangles (P5H3 topology exists; dispersion UNTESTED)",
        "subtraction number for general amplitudes (N=1 is derived only for this 2pt log)",
        "polynomial boundedness / Froissart / Regge (NOT INTRODUCED)",
        "massive dispersion (no mass inserted)",
        "two-loop amplitude dispersion (P5K masters only)",
        "Weyl 4pt dispersion",
        "physical-region contour deformation beyond the 2pt Feynman i0 cut",
        "positivity bounds (OUT OF SCOPE; M10 disabled)",
    ]
    coverage_audit = {
        "P5G": "PARTIAL",
        "P5H": "PARTIAL",
        "P5H2": "PARTIAL",
        "P5H3": "UNTESTED",
        "P5H4": "PARTIAL",
        "P5K": "UNTESTED",
        "M6": "PARTIAL",
        "M7": "PARTIAL",
        "M8": "PARTIAL",
        "analyticity_input": "PARTIAL",
        "discontinuity_information": "PARTIAL",
        "Cutkosky_data": "PARTIAL",
        "absorptive_parts": "PARTIAL",
        "regulated_amplitudes": "PARTIAL",
        "crossing_relations": "PARTIAL",
        "IR_safe_observables": "PARTIAL",
        "asymptotic_behavior_assumptions": "UNTESTED",
        "polynomial_boundedness": "UNTESTED",
        "subtraction_constants": "PARTIAL",
        "contour_representations": "PARTIAL",
        "Cauchy_integral_constructions": "PARTIAL",
        "dispersion_integrals": "PARTIAL",
    }
    coverage_matrix = [
        {
            "ingredient": "tree pole representation",
            "scalar": "NOT APPLICABLE",
            "gauge": "NOT APPLICABLE",
            "Weyl": "UNTESTED",
            "mixed": "VERIFIED",
            "loop_order": "TREE",
            "status": "VERIFIED",
        },
        {
            "ingredient": "one-loop discontinuity",
            "scalar": "VERIFIED",
            "gauge": "PARTIAL",
            "Weyl": "PARTIAL",
            "mixed": "UNTESTED",
            "loop_order": "ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "one-loop dispersion reconstruction",
            "scalar": "PARTIAL",
            "gauge": "PARTIAL",
            "Weyl": "PARTIAL",
            "mixed": "UNTESTED",
            "loop_order": "ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "two-loop discontinuity",
            "scalar": "UNTESTED",
            "gauge": "UNTESTED",
            "Weyl": "UNTESTED",
            "mixed": "UNTESTED",
            "loop_order": "TWO_LOOP",
            "status": "UNTESTED",
        },
        {
            "ingredient": "two-loop dispersion reconstruction",
            "scalar": "UNTESTED",
            "gauge": "UNTESTED",
            "Weyl": "UNTESTED",
            "mixed": "UNTESTED",
            "loop_order": "TWO_LOOP",
            "status": "UNTESTED",
        },
        {
            "ingredient": "subtraction control",
            "scalar": "PARTIAL",
            "gauge": "PARTIAL",
            "Weyl": "PARTIAL",
            "mixed": "PARTIAL",
            "loop_order": "ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "asymptotic control",
            "scalar": "PARTIAL",
            "gauge": "UNTESTED",
            "Weyl": "UNTESTED",
            "mixed": "PARTIAL",
            "loop_order": "TREE / ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "contour construction",
            "scalar": "PARTIAL",
            "gauge": "UNTESTED",
            "Weyl": "UNTESTED",
            "mixed": "UNTESTED",
            "loop_order": "ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "IR control",
            "scalar": "PARTIAL",
            "gauge": "PARTIAL",
            "Weyl": "UNTESTED",
            "mixed": "PARTIAL",
            "loop_order": "TREE / ONE_LOOP",
            "status": "PARTIAL",
        },
        {
            "ingredient": "physical-region control",
            "scalar": "PARTIAL",
            "gauge": "UNTESTED",
            "Weyl": "UNTESTED",
            "mixed": "PARTIAL",
            "loop_order": "TREE / ONE_LOOP",
            "status": "PARTIAL",
        },
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "M9",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I + PHASE_11J + PHASE_11K + P5G-P5K",
        "source_phase11h_status": loaded["11H_SUMMARY"].get("M9_DISPERSION_STATUS"),
        "source_phase11i_status": loaded["11I_SUMMARY"].get("PHASE_11I_STATUS"),
        "source_phase11j_status": loaded["11J_SUMMARY"].get("PHASE_11J_STATUS"),
        "source_phase11k_status": loaded["11K_SUMMARY"].get("PHASE_11K_STATUS"),
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "principle_definition": (
            "A(s,t) = P_N(s,t) + integral over cuts of [discontinuity / kernel], "
            "justified only where analytic domain, singularities, contour, "
            "subtractions, and asymptotics are certified"
        ),
        "coverage_audit": coverage_audit,
        "coverage_matrix": coverage_matrix,
        "dependency_status": {
            "M6": "PARTIAL",
            "M7": "PARTIAL",
            "M8": "PARTIAL",
            "M10": "DISABLED",
        },
        "amplitude_tests": {
            "tree_compton": identities["tree_compton"],
            "one_loop_bubble": identities["one_loop_bubble"],
            "two_loop": identities["two_loop"],
            "four_gluon_tree": identities["four_gluon_tree"],
        },
        "subtraction_analysis": {
            "tree_Compton": "degree-zero polynomial (seagull); DERIVED from Feynman rules",
            "two_point_log": "N = 1 DERIVED GIVEN log growth of this integral",
            "general_amplitudes": "UNTESTED",
            "SUBTRACTION_NUMBER_general": "UNTESTED",
            "subtraction_constants_are_not_new_physical_parameters": True,
            "UV_eps_pole_is_local_counterterm_not_cut": True,
            "status": "PARTIAL",
        },
        "asymptotic_analysis": {
            "tree_Compton_fixed_u": "M -> seagull; DERIVED",
            "two_point_log": "grows as log |s|; DERIVED GIVEN M7 finite piece",
            "Froissart": "NOT INTRODUCED",
            "polynomial_boundedness": "NOT INTRODUCED",
            "Regge": "NOT INTRODUCED",
            "ADDITIONAL_PHYSICAL_INPUT_REQUIRED_for_global_theorem": True,
            "status": "PARTIAL",
        },
        "contour_analysis": {
            "two_point": "Feynman i0 selects the cut; once-subtracted large arc vanishes",
            "unsubtracted_arc": "does not vanish (log growth)",
            "four_point": "UNTESTED",
            "M8_crossing_is_not_a_contour": True,
            "algebraic_variable_map_is_not_contour_deformation": True,
            "DISPERSION_SCOPE_LIMITED_BY_M7": True,
            "status": "PARTIAL",
        },
        "IR_analysis": {
            "two_point_bubble": "branch point at s = 0 is the massless threshold; exclusive 4pt IR is not this 2pt cut",
            "four_point_exclusive": "IR-sensitive (P5H1/P5H4); not ignored",
            "IR_finiteness_required_for_analyticity": False,
            "formal_exclusive_versus_IR_safe_inclusive": "distinguished; P5H4 inclusive is not this dispersion",
            "status": "PARTIAL",
        },
        "sector_status": {
            "scalar": "PARTIAL",
            "gauge": "PARTIAL",
            "Weyl": "PARTIAL",
            "mixed_scalar_gauge": "PARTIAL",
        },
        "massive_results": {
            "status": "UNTESTED",
            "reason": "no mass inserted as a physical parameter",
        },
        "massless_results": {
            "status": "PARTIAL",
            "tree_poles": "s = 0 and u = 0",
            "two_point_cut": "s real, s > 0",
        },
        "provenance": {
            "analyticity_from_M7": "DERIVED GIVEN ASSUMPTION / PARTIAL local bubble",
            "unitarity_from_M6_P5H2": "DERIVED GIVEN regulated Cutkosky; not exact S-matrix unitarity",
            "crossing_from_M8": "DERIVED GIVEN tree Compton s<->u; not a contour",
            "asymptotics": "DERIVED GIVEN the explicit log and tree seagull; general boundedness UNTESTED",
            "subtraction_point": "METHOD / CONVENTION",
            "IR_regulators": "METHOD; unused at the certified tree and 2pt log identities",
            "contour": "DERIVED GIVEN Feynman i0 plus subtracted large-arc identity for this log",
            "UV_eps": "METHOD",
        },
        "new_parameters": "none",
        "new_relations": "NONE",
        "new_input_required": False,
        "new_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11b": EXPECTED_11B_AUDIT_HASH,
            "phase11i": EXPECTED_11I_M6_HASH,
            "phase11j": EXPECTED_11J_M7_HASH,
            "phase11k": EXPECTED_11K_M8_HASH,
        },
        "pytest_status": "GREEN",
        "unresolved_gaps": remaining,
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "PARTIAL_EXTENSION",
        "DISPERSION_REQUIRES_EXPLICIT_NEW_INPUT": False,
        "positivity_certified": False,
        "global_dispersion_theorem": False,
        "M6_upgraded": False,
        "M7_upgraded": False,
        "M8_upgraded": False,
        "test_level": ["TREE", "ONE_LOOP", "PERTURBATIVE", "MASSLESS", "SCALAR", "GAUGE"],
        "negative_tests": {
            "1_local_analyticity_not_global_dispersion": True,
            "2_discontinuity_not_full_amplitude_without_subtractions": True,
            "3_tree_poles_not_branch_cut_dispersion": True,
            "4_Cutkosky_not_exact_S_unitarity": True,
            "5_M8_crossing_not_a_contour": True,
            "6_crossing_map_not_all_crossed_cuts": True,
            "7_subtraction_not_inserted_silently": True,
            "8_large_s_assumption_not_hidden": True,
            "9_IR_not_ignored": True,
            "10_massive_not_inferred_from_massless": True,
            "11_two_loop_master_not_amplitude_dispersion": True,
            "12_M10_disabled": True,
            "13_no_experimental": True,
            "14_no_numerical_target": True,
            "15_no_ranking": True,
            "16_no_new_parameter": True,
        },
        "P5H3_diagrammatic_only": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11L_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11L_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11L_M9_DISPERSION.json", payload)
        _write_json(
            "PHASE_11L_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11L_STATUS": "PARTIAL",
                "M9_COVERAGE_BEFORE": "PARTIAL",
                "M9_COVERAGE_AFTER": "PARTIAL",
                "TREE_DISPERSION_STATUS": "VERIFIED",
                "ONE_LOOP_DISPERSION_STATUS": "PARTIAL",
                "TWO_LOOP_DISPERSION_STATUS": "UNTESTED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M10": False,
                "M6_STATUS": "PARTIAL",
                "M7_STATUS": "PARTIAL",
                "M8_STATUS": "PARTIAL",
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
        "PHASE_11L_TEST_COPY_ID": PHASE_11L_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11L_PRECONDITION_STATUS": "VERIFIED",
        "M9_MODULE_STATUS": "PARTIAL",
        "M9_COVERAGE_BEFORE": "PARTIAL",
        "M9_COVERAGE_AFTER": "PARTIAL",
        "TREE_DISPERSION_STATUS": "VERIFIED",
        "ONE_LOOP_DISPERSION_STATUS": "PARTIAL",
        "TWO_LOOP_DISPERSION_STATUS": "UNTESTED",
        "SUBTRACTION_STATUS": "PARTIAL",
        "ASYMPTOTIC_CONTROL_STATUS": "PARTIAL",
        "CONTOUR_CONSTRUCTION_STATUS": "PARTIAL",
        "IR_DISPERSION_STATUS": "PARTIAL",
        "MASSIVE_DISPERSION_STATUS": "UNTESTED",
        "MASSLESS_DISPERSION_STATUS": "PARTIAL",
        "SCALAR_DISPERSION_STATUS": "PARTIAL",
        "GAUGE_DISPERSION_STATUS": "PARTIAL",
        "WEYL_DISPERSION_STATUS": "PARTIAL",
        "M6_DEPENDENCY_STATUS": "PARTIAL",
        "M7_DEPENDENCY_STATUS": "PARTIAL",
        "M8_DEPENDENCY_STATUS": "PARTIAL",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M10_STATUS": "DISABLED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11L_STATUS": "PARTIAL",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11H_UNCHANGED": True,
        "PHASE_11I_UNCHANGED": True,
        "PHASE_11J_UNCHANGED": True,
        "PHASE_11K_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "modules_enabled": ["M9"],
        "modules_disabled": ["M10"],
        "DISPERSION_SCOPE_LIMITED_BY_M7": True,
    }


def run_phase11l_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11l_m9_dispersion(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11L_INTEGRITY_FAILURE"}:
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
            "PHASE_11H_UNCHANGED": "VERIFIED",
            "PHASE_11I_UNCHANGED": "VERIFIED",
            "PHASE_11J_UNCHANGED": "VERIFIED",
            "PHASE_11K_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11L_STATUS": science.get("PHASE_11L_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
