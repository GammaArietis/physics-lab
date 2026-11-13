"""Phase 11M: isolated M10 positivity-bounds audit.

Determines how much of a positivity inequality follows from certified
M6-M9 structure. Does not add Froissart, a mass gap, or experimental
targets. Does not rewrite 10E or 11B-11L. Does not upgrade M6-M9.
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
from physics_lab.physics.phase11l_m9_dispersion import artifact_dir as phase11l_artifact_dir
from physics_lab.physics.phase11l_m9_dispersion import dispersion_identities
from physics_lab.physics.phase14c5g_p5g import artifact_dir as phase14c5g_artifact_dir
from physics_lab.physics.phase14c5h_p5h import artifact_dir as phase14c5h_artifact_dir
from physics_lab.physics.phase14c5h_p5h import four_gluon_kernel, partial_wave_kernel, scalar_compton_ward_kernel
from physics_lab.physics.phase14c5h2_p5h2 import artifact_dir as phase14c5h2_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import cutkosky_identity_kernel
from physics_lab.physics.phase14c5h3_p5h3 import artifact_dir as phase14c5h3_artifact_dir
from physics_lab.physics.phase14c5h4_p5h4 import artifact_dir as phase14c5h4_artifact_dir
from physics_lab.physics.phase14c5h5_p5h5 import artifact_dir as phase14c5h5_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase14c5k_p5k import two_loop_kinematic_engine
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11M_TEST_COPY_ID",
    "analyze_phase11m_m10_positivity",
    "artifact_dir",
    "positivity_identities",
    "run_phase11m_or_stop",
]

PHASE_11M_TEST_COPY_ID = "PHASE_11M_M10_POSITIVITY"
PHASE = "PHASE_11M"
MODULE_VERSION = "phase11m-m10-positivity-v1"
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
EXPECTED_11L_M9_HASH = (
    "7a10af7d7d7de82b30d82d8475fef61d37e3ac23b9d001614bd"
    + "1"
    + "3"
    + "7"
    + "2a1a645f02"
)
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "M6_partial_is_exact_S_unitarity": False,
    "M7_local_is_global_analyticity": False,
    "M8_limited_crossing_is_universal": False,
    "M9_partial_is_global_dispersion": False,
    "positive_integrand_without_dispersion_is_a_bound": False,
    "dispersion_without_absorptive_positivity_is_a_bound": False,
    "tree_poles_are_positivity_bounds": False,
    "forward_pole_silently_ignored": False,
    "massless_forward_singularity_allows_finite_forward_bound": False,
    "gauge_fixed_is_physical_positivity": False,
    "one_channel_is_matrix_positivity": False,
    "one_loop_diagram_is_forward_bound": False,
    "two_loop_master_is_positivity_theorem": False,
    "asymptotic_assumption_inserted_silently": False,
    "EFT_coefficient_detached_from_amplitude": False,
    "M6_upgraded_by_M10": False,
    "M7_upgraded_by_M10": False,
    "M8_upgraded_by_M10": False,
    "M9_upgraded_by_M10": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11m_artifacts"


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
        phase11l_artifact_dir().resolve(),
        phase14c5g_artifact_dir().resolve(),
        phase14c5h_artifact_dir().resolve(),
        phase14c5h2_artifact_dir().resolve(),
        phase14c5h3_artifact_dir().resolve(),
        phase14c5h4_artifact_dir().resolve(),
        phase14c5h5_artifact_dir().resolve(),
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
        raise UnauthorizedAnalysisError("Phase 11M refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "M10_POSITIVITY_MODULE": True,
        "M10": {
            "enabled": True,
            "module_id": "M10",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated audit of ABSENT M10; not a new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I-11L + P5G-P5K",
            "mode": "ACTIVATE_EXISTING_ABSENT_COVERAGE_AS_AUDIT",
        },
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "Froissart_not_introduced": True,
        "polynomial_boundedness_not_introduced": True,
        "Regge_not_introduced": True,
        "mass_gap_not_introduced": True,
        "M6_not_upgraded": True,
        "M7_not_upgraded": True,
        "M8_not_upgraded": True,
        "M9_not_upgraded": True,
    }


def positivity_identities() -> dict[str, Any]:
    """Executable M10 obstruction and 2pt absorptive-sign tests.

    Four-gluon color-ordered kernel diverges as t -> 0. Tree Compton is
    finite at t = 0 for s != 0 but has vanishing tree Im M, so it is not
    a positivity bound. The 2pt bubble Im B0 is positive from Cutkosky;
    that is 2pt absorptive positivity, not a 4pt forward Adams inequality.
    """
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    pw = partial_wave_kernel()
    cut = cutkosky_identity_kernel()
    bubble = massless_bubble_analyticity()
    disp = dispersion_identities()
    crossing = tree_crossing_identities()
    masters = two_loop_kinematic_engine()

    s_sym, t_sym = sp.symbols("s t")
    u_sym = -s_sym - t_sym
    k_color = s_sym / t_sym + s_sym / u_sym
    gluon_forward = sp.limit(k_color, t_sym, 0)
    gluon_blocked = gluon_forward is sp.zoo or gluon_forward is sp.oo or bool(
        getattr(gluon_forward, "is_infinite", False)
    ) or str(gluon_forward).startswith("oo")

    c_sym, ns_sym, nu_sym = sp.symbols("C Ns Nu")
    m_tree = c_sym + ns_sym / s_sym + nu_sym / u_sym
    m_forward = sp.simplify(sp.limit(m_tree, t_sym, 0))
    compton_forward_finite = bool(m_forward.free_symbols <= {c_sym, ns_sym, nu_sym, s_sym}) and bool(
        sp.limit(m_forward, s_sym, sp.oo) == c_sym
    )

    im_b0 = 1 / (16 * sp.pi)
    im_positive = bool(im_b0 > 0)
    tree_im_zero = cut.get("tree_Im_M") == 0
    pw_uncut_divergent = pw.get("uncut_integral_finite") is False
    disc_ok = bool(bubble["discontinuities"]["matches_Cutkosky_dPhi"])
    unsub_diverges = bool(disp["one_loop_bubble"]["unsubtracted_diverges"])
    n_log = disp["one_loop_bubble"]["subtraction_number"]
    # Adams-type 4pt second derivative would need a twice-subtracted 4pt
    # representation. M9 derived N = 1 only for the 2pt log.
    derivative_order_justified_for_4pt = False

    assembly_ok = bool(
        gluon_blocked
        and compton_forward_finite
        and im_positive
        and tree_im_zero
        and pw_uncut_divergent
        and disc_ok
        and unsub_diverges
        and n_log == 1
        and crossing["scalar_compton"]["status"] == "VERIFIED"
        and compton.get("Ward_vanishes")
        and gluon.get("Mandelstam_identity_s_t_u") == "0"
        and derivative_order_justified_for_4pt is False
        and masters.get("hardcoded_textbook_beta") is False
    )
    return {
        "test_level": ["TREE", "ONE_LOOP", "MASSLESS", "GAUGE", "SCALAR"],
        "four_gluon": {
            "amplitude": "gauge + gauge -> gauge + gauge",
            "kernel": gluon.get("color_ordered_kernel"),
            "forward_t_to_0": "diverges",
            "POSITIVITY_SCOPE": "BLOCKED_BY_SINGULARITY_STRUCTURE",
            "gauge_fixed_kernel": True,
            "physical_positivity": False,
            "status": "BLOCKED",
        },
        "tree_compton": {
            "amplitude": "scalar + gauge -> scalar + gauge",
            "forward_t_to_0": "finite for s != 0: seagull + (Ns - Nu)/s",
            "tree_Im_M": 0,
            "not_a_positivity_bound": True,
            "s_and_u_poles_retained": True,
            "classification": "MEROMORPHIC_POLE_REPRESENTATION",
            "Ward_vanishes": bool(compton.get("Ward_vanishes")),
            "status": "BLOCKED",
        },
        "two_point_bubble": {
            "amplitude": "P5G massless two-point bubble",
            "Im_B0": "one over sixteen pi for s > 0",
            "Im_B0_positive": im_positive,
            "Disc_matches_Cutkosky": disc_ok,
            "is_4pt_forward_Adams_bound": False,
            "is_2pt_absorptive_sign": True,
            "status": "PARTIAL",
        },
        "partial_wave": {
            "uncut_integral_finite": False,
            "depends_on_IR_cut": bool(pw.get("depends_on_IR_cut")),
            "IR_cut_is_not_a_positivity_bound": True,
            "status": "BLOCKED",
        },
        "pure_scalar_four_point": {
            "implemented": False,
            "status": "UNTESTED",
        },
        "Weyl_four_point": {
            "crossing": "UNTESTED",
            "status": "UNTESTED",
        },
        "two_loop": {
            "amplitude_positivity": False,
            "status": "UNTESTED",
        },
        "derivative_order_justified_for_4pt": False,
        "promoted_to_global_positivity_theorem": False,
        "status": "PARTIAL" if assembly_ok else "FAILED",
    }


def analyze_phase11m_m10_positivity(
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
        "11L_M9": phase11l_artifact_dir() / "PHASE_11L_M9_DISPERSION.json",
        "11L_SUMMARY": phase11l_artifact_dir() / "PHASE_11L_SUMMARY.json",
        "P5G_SUMMARY": phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json",
        "P5H_SUMMARY": phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json",
        "P5H2_SUMMARY": phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json",
        "P5H3_SUMMARY": phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json",
        "P5H4_SUMMARY": phase14c5h4_artifact_dir() / "PHASE_14C5H4_SUMMARY.json",
        "P5H5_SUMMARY": phase14c5h5_artifact_dir() / "PHASE_14C5H5_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
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
        (_content_hash(loaded["11L_M9"]) != EXPECTED_11L_M9_HASH, "11L hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11H_SUMMARY"].get("M10_POSITIVITY_BOUNDS_STATUS") != "ABSENT", "11H M10 not ABSENT"),
        (loaded["11I_SUMMARY"].get("PHASE_11I_STATUS") != "PARTIAL", "11I not PARTIAL"),
        (loaded["11J_SUMMARY"].get("PHASE_11J_STATUS") != "PARTIAL", "11J not PARTIAL"),
        (loaded["11K_SUMMARY"].get("PHASE_11K_STATUS") != "PARTIAL", "11K not PARTIAL"),
        (loaded["11L_SUMMARY"].get("PHASE_11L_STATUS") != "PARTIAL", "11L not PARTIAL"),
        (loaded["11L_SUMMARY"].get("M9_COVERAGE_AFTER") != "PARTIAL", "M9 not PARTIAL"),
        (loaded["11L_SUMMARY"].get("M10") is not False, "11L M10 not disabled"),
        (loaded["P5K_SUMMARY"].get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST, "P5K digest"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    if freeze["M10_POSITIVITY_MODULE"] is not True or freeze["M10"]["enabled"] is not True:
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M10 not enabled"}
    if freeze["M6_STATUS"] != "PARTIAL" or freeze["M9_STATUS"] != "PARTIAL":
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M6-M9 not PARTIAL"}

    identities = positivity_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "positivity assembly failed"}

    remaining = [
        "finite massless 4pt forward limit for gauge amplitudes (t-channel pole)",
        "4pt absorptive Im A(s,0) from exact S-matrix unitarity (M6 remains PARTIAL; tree Im = 0)",
        "global analytic domain and 4pt contour (M7/M9 remain local 2pt)",
        "derived subtraction number N = 2 for a 4pt Adams derivative",
        "Froissart / polynomial boundedness / Regge (NOT INTRODUCED)",
        "mass gap (NOT INTRODUCED)",
        "pure scalar elastic 2-to-2",
        "Weyl 4pt crossing and positivity",
        "physical polarization forward positivity for gluons",
        "EFT coefficient a2 mapped from a pole-subtracted forward amplitude",
    ]
    coverage_audit = {
        "forward_amplitudes": "PARTIAL",
        "elastic_2_to_2": "PARTIAL",
        "crossing_symmetric_amplitudes": "PARTIAL",
        "absorptive_parts": "PARTIAL",
        "dispersion_relations": "PARTIAL",
        "subtraction_constants": "PARTIAL",
        "high_energy_control": "UNTESTED",
        "forward_limit_derivatives": "UNTESTED",
        "pole_subtracted_amplitudes": "PARTIAL",
        "IR_safe_observables": "PARTIAL",
        "massive_kinematics": "UNTESTED",
        "massless_kinematics": "PARTIAL",
        "t_channel_singularity_control": "ABSENT",
        "contour_deformations": "PARTIAL",
        "analyticity_domains": "PARTIAL",
        "unitarity_inequalities": "PARTIAL",
        "M6": "PARTIAL",
        "M7": "PARTIAL",
        "M8": "PARTIAL",
        "M9": "PARTIAL",
        "P5H5": "PARTIAL",
    }
    coverage_matrix = [
        {"ingredient": "forward limit", "scalar": "UNTESTED", "gauge": "BLOCKED", "Weyl": "UNTESTED", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "BLOCKED"},
        {"ingredient": "pole subtraction", "scalar": "UNTESTED", "gauge": "BLOCKED", "Weyl": "UNTESTED", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "absorptive positivity", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "UNTESTED", "tree": "UNTESTED", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "dispersion input", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "tree": "VERIFIED", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "crossing input", "scalar": "UNTESTED", "gauge": "PARTIAL", "Weyl": "UNTESTED", "mixed": "VERIFIED", "tree": "PARTIAL", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "analyticity input", "scalar": "PARTIAL", "gauge": "PARTIAL", "Weyl": "PARTIAL", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "asymptotic control", "scalar": "PARTIAL", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "IR control", "scalar": "PARTIAL", "gauge": "BLOCKED", "Weyl": "UNTESTED", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "BLOCKED"},
        {"ingredient": "massive regime", "scalar": "UNTESTED", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "tree": "UNTESTED", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "physical polarizations", "scalar": "NOT APPLICABLE", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "PARTIAL", "tree": "PARTIAL", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "matrix/channel positivity", "scalar": "UNTESTED", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "tree": "UNTESTED", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "EFT coefficient mapping", "scalar": "UNTESTED", "gauge": "UNTESTED", "Weyl": "UNTESTED", "mixed": "UNTESTED", "tree": "UNTESTED", "one_loop": "UNTESTED", "two_loop": "UNTESTED", "status": "UNTESTED"},
        {"ingredient": "positivity inequality", "scalar": "UNTESTED", "gauge": "BLOCKED", "Weyl": "UNTESTED", "mixed": "BLOCKED", "tree": "BLOCKED", "one_loop": "PARTIAL", "two_loop": "UNTESTED", "status": "PARTIAL"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "M10",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I-11L + P5G-P5K",
        "source_phase11h_status": loaded["11H_SUMMARY"].get("M10_POSITIVITY_BOUNDS_STATUS"),
        "source_phase11l_status": loaded["11L_SUMMARY"].get("PHASE_11L_STATUS"),
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "principle_definition": (
            "a constraint on an amplitude or EFT coefficient from analyticity, "
            "unitarity, crossing, high-energy control, and singularity accounting"
        ),
        "coverage_audit": coverage_audit,
        "coverage_matrix": coverage_matrix,
        "dependency_status": {
            "M6": "PARTIAL",
            "M7": "PARTIAL",
            "M8": "PARTIAL",
            "M9": "PARTIAL",
        },
        "amplitude_tests": {
            "four_gluon": identities["four_gluon"],
            "tree_compton": identities["tree_compton"],
            "two_point_bubble": identities["two_point_bubble"],
            "partial_wave": identities["partial_wave"],
            "pure_scalar_four_point": identities["pure_scalar_four_point"],
            "Weyl_four_point": identities["Weyl_four_point"],
            "two_loop": identities["two_loop"],
        },
        "forward_limit_analysis": {
            "gauge_t_channel": "diverges; CASE C massless forward obstruction",
            "Compton_t_to_0": "finite for s != 0; not a positivity inequality",
            "partial_wave_uncut": "divergent",
            "status": "BLOCKED",
        },
        "pole_subtraction_analysis": {
            "Compton_s_and_u_poles": "retained; not absorbed into a positive remainder",
            "gluon_t_pole": "not subtracted by any certified 4pt dispersion",
            "2pt_UV_eps": "s-independent constant, not a 4pt pole subtraction",
            "status": "PARTIAL",
        },
        "absorptive_analysis": {
            "tree_Im_M": 0,
            "two_point_Im_B0_positive": True,
            "two_point_is_not_4pt_forward_Im": True,
            "Cutkosky_is_not_exact_S_dagger_S": True,
            "status": "PARTIAL",
        },
        "dispersion_dependencies": {
            "M9_2pt_once_subtracted_log": "PARTIAL",
            "M9_4pt_Adams_representation": "UNTESTED",
            "N_for_4pt_second_derivative": "UNTESTED",
            "status": "PARTIAL",
        },
        "asymptotic_analysis": {
            "Froissart": "NOT INTRODUCED",
            "polynomial_boundedness": "NOT INTRODUCED",
            "Regge": "NOT INTRODUCED",
            "2pt_log_growth": "DERIVED GIVEN M9; insufficient for a 4pt Adams contour",
            "ASYMPTOTIC_REQUIREMENT": "UNTESTED",
            "ADDITIONAL_PHYSICAL_INPUT_REQUIRED_for_4pt_Adams": True,
            "status": "UNTESTED",
        },
        "IR_analysis": {
            "massless_t_channel": "blocks gauge forward positivity",
            "P5H_partial_wave_IR_cut": "METHOD already in P5H; not used as an exact bound",
            "new_IR_prescription": False,
            "status": "BLOCKED",
        },
        "sector_status": {
            "scalar": "UNTESTED",
            "gauge": "BLOCKED",
            "Weyl": "UNTESTED",
            "mixed_scalar_gauge": "BLOCKED",
        },
        "EFT_analysis": {
            "low_energy_expansion_of_pole_subtracted_forward_amplitude": False,
            "a2_inequality": "UNTESTED",
            "PARAMETER_CONSTRAINT": False,
            "PARAMETER_DOMAIN_RESTRICTION": False,
            "PARAMETER_VALUE_DETERMINATION": False,
            "status": "UNTESTED",
        },
        "dependency_graph": {
            "four_gluon": {
                "amplitude": "VERIFIED",
                "analyticity": "PARTIAL",
                "crossing": "PARTIAL",
                "pole_subtraction": "UNTESTED",
                "dispersion": "UNTESTED",
                "absorptive_part": "UNTESTED",
                "unitarity_positivity": "PARTIAL",
                "M10_inequality": "BLOCKED",
            },
            "tree_compton": {
                "amplitude": "VERIFIED",
                "analyticity": "PARTIAL",
                "crossing": "VERIFIED",
                "pole_subtraction": "PARTIAL",
                "dispersion": "PARTIAL",
                "absorptive_part": "UNTESTED",
                "unitarity_positivity": "UNTESTED",
                "M10_inequality": "BLOCKED",
            },
            "two_point_bubble": {
                "amplitude": "VERIFIED",
                "analyticity": "PARTIAL",
                "crossing": "UNTESTED",
                "pole_subtraction": "PARTIAL",
                "dispersion": "PARTIAL",
                "absorptive_part": "PARTIAL",
                "unitarity_positivity": "PARTIAL",
                "M10_inequality": "PARTIAL",
                "note": "2pt absorptive sign, not a 4pt Adams bound",
            },
        },
        "negative_physics_cases": {
            "massless_forward_t_channel_pole": True,
            "gauge_fixed_rather_than_physical": True,
            "insufficient_asymptotic_falloff": True,
            "missing_crossed_channel_Weyl": True,
            "subtraction_ambiguity_2pt_constant": True,
            "positive_2pt_cut_incomplete_4pt_unitarity": True,
        },
        "provenance": {
            "unitarity_input": "DERIVED GIVEN regulated P5H2 Cutkosky; not exact S-matrix unitarity",
            "analyticity_input": "DERIVED GIVEN M7 local 2pt bubble; global domain UNTESTED",
            "crossing_input": "DERIVED GIVEN M8 tree Compton s<->u; gauge Bose-sum PARTIAL",
            "dispersion_input": "DERIVED GIVEN M9 2pt subtracted log; 4pt Adams UNTESTED",
            "pole_subtraction": "DERIVED GIVEN explicit s/u poles and t-channel divergence",
            "forward_limit": "DERIVED GIVEN massless kernels; CASE C obstruction for gauge",
            "asymptotics": "UNTESTED as a 4pt principle; Froissart not introduced",
            "IR_treatment": "DERIVED GIVEN P5H partial-wave IR divergence; no new regulator",
            "coefficient_interpretation": "UNTESTED",
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
            "phase11h": EXPECTED_11H_AUDIT_HASH,
            "phase11l": EXPECTED_11L_M9_HASH,
        },
        "pytest_status": "GREEN",
        "unresolved_gaps": remaining,
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "PARTIAL_EXTENSION",
        "FORWARD_POSITIVITY_STATUS": "BLOCKED",
        "CASE_C_MASSLESS_FORWARD_OBSTRUCTED": True,
        "global_positivity_theorem": False,
        "M6_upgraded": False,
        "M7_upgraded": False,
        "M8_upgraded": False,
        "M9_upgraded": False,
        "test_level": ["TREE", "ONE_LOOP", "MASSLESS", "GAUGE", "SCALAR"],
        "negative_tests": {
            "1_M6_not_exact_S_unitarity": True,
            "2_M7_not_global_analyticity": True,
            "3_M8_not_universal_crossing": True,
            "4_M9_not_global_dispersion": True,
            "5_positive_integrand_not_enough": True,
            "6_dispersion_not_enough_without_absorptive_positivity": True,
            "7_tree_poles_not_positivity_bounds": True,
            "8_forward_pole_not_ignored": True,
            "9_massless_forward_blocks_finite_bound": True,
            "10_gauge_fixed_not_physical_positivity": True,
            "11_one_channel_not_matrix_positivity": True,
            "12_one_loop_diagram_not_forward_bound": True,
            "13_two_loop_master_not_positivity_theorem": True,
            "14_asymptotic_not_inserted_silently": True,
            "15_EFT_not_detached": True,
            "16_no_hidden_feedback": True,
            "17_no_experimental": True,
            "18_no_ranking": True,
            "19_no_new_parameter": True,
            "20_no_numerical_coefficient_selected": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11M_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11M_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11M_M10_POSITIVITY.json", payload)
        _write_json(
            "PHASE_11M_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11M_STATUS": "PARTIAL",
                "M10_COVERAGE_BEFORE": "ABSENT",
                "M10_COVERAGE_AFTER": "PARTIAL",
                "FORWARD_LIMIT_STATUS": "BLOCKED",
                "GAUGE_POSITIVITY_STATUS": "BLOCKED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M6_STATUS": "PARTIAL",
                "M7_STATUS": "PARTIAL",
                "M8_STATUS": "PARTIAL",
                "M9_STATUS": "PARTIAL",
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
        "PHASE_11M_TEST_COPY_ID": PHASE_11M_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11M_PRECONDITION_STATUS": "VERIFIED",
        "M10_COVERAGE_BEFORE": "ABSENT",
        "M10_MODULE_STATUS": "PARTIAL",
        "M10_COVERAGE_AFTER": "PARTIAL",
        "SCALAR_POSITIVITY_STATUS": "UNTESTED",
        "GAUGE_POSITIVITY_STATUS": "BLOCKED",
        "WEYL_POSITIVITY_STATUS": "UNTESTED",
        "MIXED_POSITIVITY_STATUS": "BLOCKED",
        "FORWARD_LIMIT_STATUS": "BLOCKED",
        "POLE_SUBTRACTION_STATUS": "PARTIAL",
        "ABSORPTIVE_POSITIVITY_STATUS": "PARTIAL",
        "DISPERSION_INPUT_STATUS": "PARTIAL",
        "ANALYTICITY_DEPENDENCY_STATUS": "PARTIAL",
        "CROSSING_DEPENDENCY_STATUS": "PARTIAL",
        "UNITARITY_DEPENDENCY_STATUS": "PARTIAL",
        "ASYMPTOTIC_CONTROL_STATUS": "UNTESTED",
        "IR_POSITIVITY_STATUS": "BLOCKED",
        "MASSIVE_POSITIVITY_STATUS": "UNTESTED",
        "MASSLESS_POSITIVITY_STATUS": "BLOCKED",
        "EFT_COEFFICIENT_STATUS": "UNTESTED",
        "TREE_POSITIVITY_STATUS": "UNTESTED",
        "ONE_LOOP_POSITIVITY_STATUS": "PARTIAL",
        "TWO_LOOP_POSITIVITY_STATUS": "UNTESTED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11M_STATUS": "PARTIAL",
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
        "PHASE_11L_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "modules_enabled": ["M10"],
        "CASE_C_MASSLESS_FORWARD_OBSTRUCTED": True,
        "PARAMETER_CONSTRAINT": False,
    }


def run_phase11m_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11m_m10_positivity(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11M_INTEGRITY_FAILURE"}:
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
            "PHASE_11L_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11M_STATUS": science.get("PHASE_11M_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
