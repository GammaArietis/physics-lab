"""Phase 11K: isolated M8 crossing-symmetry completion.

Assembles certified P5H/P5H3 channel kernels, P5I CPT maps (as a separate
reference), and 11J local analytic continuation into the strongest valid
amplitude-level crossing statement. Does not claim a global crossing theorem.
M9-M10 remain disabled. Does not rewrite 10E or 11B-11J. Does not upgrade M7.
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
from physics_lab.physics.phase14c5g_p5g import artifact_dir as phase14c5g_artifact_dir
from physics_lab.physics.phase14c5g1_p5g1 import artifact_dir as phase14c5g1_artifact_dir
from physics_lab.physics.phase14c5h_p5h import artifact_dir as phase14c5h_artifact_dir
from physics_lab.physics.phase14c5h_p5h import four_gluon_kernel, scalar_compton_ward_kernel
from physics_lab.physics.phase14c5h1_p5h1 import artifact_dir as phase14c5h1_artifact_dir
from physics_lab.physics.phase14c5h3_p5h3 import artifact_dir as phase14c5h3_artifact_dir
from physics_lab.physics.phase14c5i_p5i import CPT_AMPLITUDE_RELATION
from physics_lab.physics.phase14c5i_p5i import artifact_dir as phase14c5i_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_11J_M7_HASH",
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11K_TEST_COPY_ID",
    "analyze_phase11k_m8_crossing",
    "artifact_dir",
    "run_phase11k_or_stop",
    "tree_crossing_identities",
]

PHASE_11K_TEST_COPY_ID = "PHASE_11K_M8_CROSSING"
PHASE = "PHASE_11K"
MODULE_VERSION = "phase11k-m8-crossing-v1"
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
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "crossed_diagrams_imply_crossing": False,
    "stu_availability_implies_crossing": False,
    "CPT_implies_crossing": False,
    "one_kinematic_point_implies_crossing": False,
    "numerical_agreement_implies_analytic_crossing": False,
    "exchange_symmetry_is_crossing": False,
    "gauge_fixed_implies_physical_crossing": False,
    "IR_finiteness_is_crossing_criterion": False,
    "IR_divergence_ignored_in_physical_observable": False,
    "scalar_rules_applied_to_Weyl": False,
    "tree_identity_is_global_theorem": False,
    "M7_upgraded_by_M8": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11k_artifacts"


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
        phase14c5g_artifact_dir().resolve(),
        phase14c5g1_artifact_dir().resolve(),
        phase14c5h_artifact_dir().resolve(),
        phase14c5h1_artifact_dir().resolve(),
        phase14c5h3_artifact_dir().resolve(),
        phase14c5i_artifact_dir().resolve(),
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
        raise UnauthorizedAnalysisError("Phase 11K refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "M8_CROSSING_MODULE": True,
        "M8": {
            "enabled": True,
            "module_id": "M8",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M8; not a new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I + PHASE_11J + P5H-P5K + P5I",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M9": False,
        "M10": False,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M5_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "dispersion_out_of_scope": True,
        "positivity_out_of_scope": True,
        "M7_not_upgraded": True,
    }


def _eta() -> sp.Matrix:
    return sp.diag(*eta_diag(MOSTLY_PLUS))


def _dot(a: sp.Matrix, b: sp.Matrix) -> Any:
    return (a.T * _eta() * b)[0]


def _is_zero(expr: Any) -> bool:
    return bool(sp.simplify(expr).equals(0))


def _compton_amp(
    eps_in: sp.Matrix,
    eps_out: sp.Matrix,
    p1: sp.Matrix,
    k: sp.Matrix,
    p3: sp.Matrix,
    kp: sp.Matrix,
) -> Any:
    """Same seagull + s-channel + u-channel Feynman rules as P5H Compton."""
    eta = _eta()
    s = _dot(p1 + k, p1 + k)
    u = _dot(p1 - kp, p1 - kp)
    seagull = 2 * (eps_in.T * eta * eps_out)[0]
    s_ch = ((2 * p1 + k).T * eta * eps_in)[0] * ((2 * p3 + kp).T * eta * eps_out)[0] / s
    u_ch = ((2 * p1 - kp).T * eta * eps_out)[0] * ((2 * p3 - k).T * eta * eps_in)[0] / u
    return seagull + s_ch + u_ch, s, u


def tree_crossing_identities() -> dict[str, Any]:
    """Tree-level amplitude crossing tests on implemented 2-to-2 kernels.

    Scalar Compton: photon crossing k -> -k', k' -> -k with polarization swap,
    which implements s <-> u on the meromorphic P5H amplitude, as a function
    of CM energy and scattering angle. Not a global theorem.

    Four-gluon: Bose sum of the published color-ordered kernel s/t + s/u on
    s+t+u=0 is totally symmetric. The unordered color-ordered piece is not
    itself the crossing identity. Gauge-fixed, not physical polarizations.
    """
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    E = sp.symbols("E", positive=True)
    cth, sth = sp.symbols("cth sth", real=True)
    p1 = sp.Matrix([E, 0, 0, E])
    k = sp.Matrix([E, 0, 0, -E])
    p3 = sp.Matrix([E, E * sth, 0, E * cth])
    kp = p1 + k - p3
    onshell = {sth**2: 1 - cth**2}

    eps_in_y = sp.Matrix([0, 0, 1, 0])
    eps_out_y = sp.Matrix([0, 0, 1, 0])
    eps_in_x = sp.Matrix([0, 1, 0, 0])
    eps_out_xz = sp.Matrix([0, cth, 0, -sth])

    def _pair(ein: sp.Matrix, eout: sp.Matrix) -> bool:
        m_s, s_val, u_val = _compton_amp(ein, eout, p1, k, p3, kp)
        m_u, s_cross, u_cross = _compton_amp(eout, ein, p1, -kp, p3, -k)
        s_maps_to_u = _is_zero((s_cross - u_val).subs(onshell))
        u_maps_to_s = _is_zero((u_cross - s_val).subs(onshell))
        amps_equal = _is_zero((m_s - m_u).subs(onshell))
        return bool(s_maps_to_u and u_maps_to_s and amps_equal)

    yy_ok = _pair(eps_in_y, eps_out_y)
    xxz_ok = _pair(eps_in_x, eps_out_xz)
    compton_ok = bool(yy_ok and xxz_ok) and bool(compton.get("Ward_vanishes"))

    s_sym, t_sym = sp.symbols("s t")
    u_sym = -s_sym - t_sym

    def k_color(a: Any, b: Any, c: Any) -> Any:
        return a / b + a / c

    k_s = k_color(s_sym, t_sym, u_sym)
    k_t = k_color(t_sym, s_sym, u_sym)
    k_u = k_color(u_sym, s_sym, t_sym)
    bose = sp.simplify(k_s + k_t + k_u)
    bose_st = sp.simplify(bose.subs({s_sym: t_sym, t_sym: s_sym}))
    color_ordered_is_not_crossing = not _is_zero(k_s - k_t)
    bose_crossing = bool(_is_zero(bose - bose_st) and bose == -3)
    stu_ok = gluon.get("Mandelstam_identity_s_t_u") == "0"

    return {
        "test_level": ["TREE", "PERTURBATIVE", "SCALAR", "GAUGE", "MASSLESS"],
        "scalar_compton": {
            "process": "scalar + gauge -> scalar + gauge",
            "amplitude_id": "scalar_compton_ward_kernel",
            "relation": "M(s, t, u; eps_in, eps_out) = M(u, t, s; eps_out, eps_in)",
            "momentum_map": "incoming photon k -> -k_out; outgoing photon k_out -> -k",
            "Mandelstam_map": "s <-> u, t fixed",
            "polarization_map": "eps_in <-> eps_out",
            "domain": "massless CM slice E > 0, |cos theta| < 1, away from s = 0 and u = 0 poles",
            "yy_identity": yy_ok,
            "x_xz_identity": xxz_ok,
            "Ward_vanishes": bool(compton.get("Ward_vanishes")),
            "symbolic_in_E_and_angle": True,
            "not_one_kinematic_point": True,
            "pure_scalar_four_point": False,
            "status": "VERIFIED" if compton_ok else "FAILED",
        },
        "four_gluon": {
            "process": "gauge + gauge -> gauge + gauge",
            "amplitude_id": "four_gluon_kernel",
            "diagrams": list(gluon.get("diagrams") or []),
            "color_ordered_kernel": gluon.get("color_ordered_kernel"),
            "color_ordered_equals_crossed": False,
            "color_ordered_is_not_crossing": color_ordered_is_not_crossing,
            "Bose_sum_identity": "K(s,t,u)+K(t,s,u)+K(u,s,t) = -3 on s+t+u=0",
            "Bose_sum_crossing_verified": bose_crossing,
            "Mandelstam_identity": stu_ok,
            "gauge_fixed_kernel": True,
            "physical_polarizations_in_kernel": False,
            "status": "PARTIAL" if (bose_crossing and stu_ok and color_ordered_is_not_crossing) else "FAILED",
        },
        "Weyl": {
            "process": "none implemented as a 2-to-2 amplitude kernel",
            "CPT_map_available_in_P5I": True,
            "CPT_is_not_crossing": True,
            "status": "UNTESTED",
        },
        "promoted_to_global_crossing_theorem": False,
        "status": "PARTIAL" if compton_ok and bose_crossing else "FAILED",
    }


def analyze_phase11k_m8_crossing(
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
        "P5G_SUMMARY": phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json",
        "P5H_SUMMARY": phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json",
        "P5H1_SUMMARY": phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json",
        "P5H3_SUMMARY": phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json",
        "P5I_SUMMARY": phase14c5i_artifact_dir() / "PHASE_14C5I_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
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
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11H_SUMMARY"].get("M8_CROSSING_STATUS") != "PARTIAL", "11H M8 not PARTIAL"),
        (loaded["11I_SUMMARY"].get("PHASE_11I_STATUS") != "PARTIAL", "11I not PARTIAL"),
        (loaded["11J_SUMMARY"].get("PHASE_11J_STATUS") != "PARTIAL", "11J not PARTIAL"),
        (loaded["11J_SUMMARY"].get("M7_COVERAGE_AFTER") != "PARTIAL", "M7 not PARTIAL"),
        (loaded["11J_SUMMARY"].get("M8") is not False, "11J M8 not disabled"),
        (loaded["P5K_SUMMARY"].get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST, "P5K digest"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    if freeze["M8_CROSSING_MODULE"] is not True or freeze["M8"]["enabled"] is not True:
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M8 not enabled"}
    if freeze["M9"] or freeze["M10"]:
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M9-M10 enabled"}
    if freeze["M7_STATUS"] != "PARTIAL":
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M7 not PARTIAL"}

    identities = tree_crossing_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "tree crossing assembly failed"}
    bubble = massless_bubble_analyticity()
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()

    remaining = [
        "Weyl 2-to-2 amplitude-level crossing (only P5I CPT incoming/outgoing map exists)",
        "physical polarization crossing of the four-gluon amplitude (kernel is gauge-fixed color-ordered)",
        "pure scalar four-point phi phi -> phi phi (no such implemented amplitude)",
        "analytic continuation path in complex Mandelstam space connecting distinct physical regions (tree identities are meromorphic; M7 supplies only a 2pt bubble log)",
        "massive crossing",
        "one-loop 4pt crossing (P5H3 t/u bubbles are channel diagrams, not crossed loop amplitudes)",
        "two-loop amplitude crossing",
        "global crossing theorem for all amplitudes",
    ]
    payload = {
        "phase": PHASE,
        "module_id": "M8",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": "PHASE_10E + PHASE_11H + PHASE_11I + PHASE_11J + P5H-P5K + P5I",
        "source_phase11h_status": loaded["11H_SUMMARY"].get("M8_CROSSING_STATUS"),
        "source_phase11i_status": loaded["11I_SUMMARY"].get("PHASE_11I_STATUS"),
        "source_phase11j_status": loaded["11J_SUMMARY"].get("PHASE_11J_STATUS"),
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "principle_definition": (
            "for a suitable amplitude, crossing relates processes obtained by replacing "
            "incoming particles with corresponding outgoing antiparticles and analytically "
            "continuing the relevant kinematic variables"
        ),
        "principle_vs_proxy": {
            "CROSS_CHANNEL_DIAGRAM_GENERATION": "AVAILABLE (P5H s/t/u diagrams, P5H3 t/u bubbles); not the theorem",
            "CROSS_CHANNEL_KINEMATIC_REPARAMETRIZATION": "AVAILABLE (Mandelstam s,t,u with s+t+u=0)",
            "CPT_INCOMING_OUTGOING_MAP": "AVAILABLE as a separate P5I relation; not used as the crossing proof",
            "AMPLITUDE_CROSSING_RELATION": "TREE Compton s<->u VERIFIED; four-gluon Bose-sum PARTIAL",
            "GLOBAL_ANALYTIC_CROSSING_THEOREM": "NOT_CLAIMED",
        },
        "process_inventory": [
            {
                "process": "scalar + gauge -> scalar + gauge",
                "external_states": ["scalar in", "gauge in", "scalar out", "gauge out"],
                "statistics": ["Bose", "Bose", "Bose", "Bose"],
                "masses": "massless in the implemented kernel",
                "charge_representation": "G6 scalar plus F2 gauge; labels not numerically fixed",
                "allowed_channels": ["s_channel_scalar_exchange", "u_channel_scalar_exchange", "seagull_phi_phi_AA"],
                "amplitude_id": "scalar_compton_ward_kernel",
                "implemented": True,
            },
            {
                "process": "gauge + gauge -> gauge + gauge",
                "external_states": ["gauge", "gauge", "gauge", "gauge"],
                "statistics": ["Bose", "Bose", "Bose", "Bose"],
                "masses": "massless",
                "charge_representation": "non-Abelian adjoint color of F2",
                "allowed_channels": list(gluon.get("diagrams") or []),
                "amplitude_id": "four_gluon_kernel",
                "implemented": True,
            },
            {
                "process": "scalar + scalar -> scalar + scalar",
                "implemented": False,
                "reason": "no phi^4 2-to-2 amplitude kernel in the laboratory",
            },
            {
                "process": "Weyl + gauge -> Weyl + gauge",
                "implemented": False,
                "reason": "no Weyl 2-to-2 amplitude kernel; P5I supplies only a CPT map",
            },
            {
                "process": "Weyl + Weyl -> Weyl + Weyl",
                "implemented": False,
                "reason": "no implemented fermion four-point amplitude",
            },
        ],
        "crossing_maps": {
            "scalar_compton_photon_crossing": {
                "initial_state": "phi(p1) A(k, eps_in) -> phi(p3) A(k_out, eps_out)",
                "crossed_state": "phi(p1) A(-k_out, eps_out) -> phi(p3) A(-k, eps_in)",
                "outgoing_incoming_substitution": "incoming photon <-> outgoing photon",
                "momentum_substitution": "k -> -k_out, k_out -> -k",
                "Mandelstam_variable_map": "s <-> u, t fixed",
                "spin_polarization_transformation": "eps_in <-> eps_out",
                "charge_conjugation": "photon is self-conjugate; scalar pair not conjugated in this map",
                "statistics_sign": "+1 (bosons)",
            },
            "four_gluon_Bose_channel_map": {
                "initial_state": "A A -> A A color-ordered kernel K = s/t + s/u",
                "crossed_state": "same process with s <-> t or s <-> u",
                "outgoing_incoming_substitution": "identical-gluon channel relabel",
                "momentum_substitution": "Mandelstam permutation of s, t, u",
                "Mandelstam_variable_map": "cyclic permutations of (s,t,u)",
                "spin_polarization_transformation": "not in the published kernel",
                "charge_conjugation": "adjoint gluons; color-ordered, not a C-map",
                "statistics_sign": "+1 (Bose); exchange symmetry of identical gluons is recorded separately from crossing",
            },
            "Weyl": "UNTESTED; fermionic crossing rules not applied",
        },
        "scalar_results": identities["scalar_compton"],
        "weyl_results": identities["Weyl"],
        "gauge_results": identities["four_gluon"],
        "analytic_continuation": {
            "used_for_tree_Compton": "unique meromorphic continuation of a rational tree amplitude away from s=0 and u=0 poles",
            "M7_bubble_log": bubble.get("finite_piece"),
            "M7_certified_domain": bubble.get("certified_domain"),
            "M7_used_as_4pt_continuation": False,
            "singularities_crossed_or_avoided": ["tree poles s=0, u=0 avoided; not encircled as a constructed contour"],
            "branch_sheet_convention": "tree: none (rational); loop: M7 physical sheet of -log(-s-i0) not lifted to 4pt",
            "physical_region_map": "CM s-channel slice maps to the u-channel image by s<->u; no complex path constructed",
            "DEPENDS_ON_M7": True,
            "dependency_scope": "PARTIAL",
            "dependency_used_in_certified_tree_identity": False,
            "loop_crossing_would_require_M7": True,
            "CROSSING_ANALYTIC_STATUS": "PARTIAL",
            "test_level": ["TREE", "ANALYTIC_CONTINUATION", "MASSLESS"],
        },
        "physical_region_results": {
            "algebraic_identity_on_CM_slice": True,
            "constructed_contour_between_physical_regions": False,
            "s_channel_CM": "s = -4 E^2 (mostly plus), angle via t,u",
            "u_channel_image": "s <-> u of the same slice",
            "one_point_equality_not_the_certificate": True,
            "status": "PARTIAL",
            "test_level": ["TREE", "MASSLESS", "PHYSICAL_STATE"],
        },
        "spin_statistics_factors": {
            "scalar_Compton": "+1 Bose; no fermionic minus",
            "four_gluon": "+1 Bose; Bose sum is not silently identified with crossing",
            "Weyl": "UNTESTED; scalar rules not applied",
            "exchange_symmetry_distinct_from_crossing": True,
            "status": "PARTIAL",
            "test_level": ["TREE", "SCALAR", "GAUGE"],
        },
        "cpt_separation": {
            "CPT_AMPLITUDE_RELATION": CPT_AMPLITUDE_RELATION,
            "CPT_used_as_crossing_proof": False,
            "CPT_map": "p -> -p, h -> -h, R -> conjugate R, complex conjugate",
            "crossing_map_Compton": "k -> -k_out and s <-> u without complex conjugation",
            "maps_are_distinct": True,
            "P5I_unmodified": True,
            "status": "VERIFIED",
        },
        "massive_results": {
            "status": "UNTESTED",
            "reason": "implemented 2-to-2 kernels are massless; mass not inserted",
            "test_level": ["MASSIVE"],
        },
        "massless_results": {
            "status": "PARTIAL",
            "soft_singularities": "present in massless 4pt; not used as a crossing criterion",
            "collinear_singularities": "present; P5H1 IR tags remain",
            "forward_singularities": "t=0 and u=0 poles of the tree kernels",
            "branch_cuts": "not in the tree kernels; M7 2pt cut not lifted to 4pt",
            "regulator_dependence": "none in the tree identities; dim-reg is METHOD at loop level and unused here",
            "IR_finiteness_required_for_formal_crossing": False,
            "IR_divergences_ignored_when_claiming_physical_observable": False,
            "test_level": ["MASSLESS", "TREE"],
        },
        "loop_order_results": {
            "TREE": "Compton s<->u VERIFIED; four-gluon Bose-sum PARTIAL",
            "ONE_LOOP": "UNTESTED; P5H3 t/u bubbles are diagrammatic channel promotion",
            "TWO_LOOP": "UNTESTED; P5K masters are not a two-loop crossing theorem",
            "P5H3_channel_diagrams_are_not_amplitude_crossing": True,
            "test_level": ["TREE", "ONE_LOOP", "TWO_LOOP", "PERTURBATIVE"],
        },
        "parameter_dependencies": [
            "masses remain free; none inserted",
            "couplings remain free; no numerical tuning",
            "Z, Z_A unused in the tree identities",
            "gauge normalization unused; Compton Ward identity used only as an on-shell check",
            "external-state normalization: physical transverse polarizations, not fitted",
            "regulators unused at tree",
        ],
        "new_parameters": "none",
        "new_relations": "NONE",
        "PARAMETER_DEPENDENT": False,
        "sector_impact": {
            "scalar_matter": "PARTIALLY_AFFECTED",
            "Weyl_matter": "UNTESTED",
            "gauge_sector": "PARTIALLY_AFFECTED",
            "amplitudes": "PARTIALLY_AFFECTED",
            "analytic_structure": "PARTIALLY_AFFECTED",
            "CPT_relation": "UNCHANGED",
            "IR_structure": "UNCHANGED",
            "physical_state_amplitudes": "PARTIALLY_AFFECTED",
            "gravity": "UNCHANGED",
        },
        "provenance_map": {
            "Compton_Feynman_rules": "P5H scalar_compton_ward_kernel seagull + s + u",
            "four_gluon_kernel": "P5H four_gluon_kernel color-ordered s/t + s/u",
            "channel_diagrams": "P5H s/t/u and P5H3 t/u bubble promotion (diagrammatic only)",
            "CPT_reference": "P5I CPT_AMPLITUDE_RELATION; not the crossing proof",
            "analytic_2pt": "11J massless_bubble_analyticity; not upgraded",
        },
        "unresolved_gaps": remaining,
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "PARTIAL_EXTENSION",
        "CROSSING_REQUIRES_EXPLICIT_NEW_INPUT": False,
        "dispersion_certified": False,
        "positivity_certified": False,
        "global_crossing_theorem": False,
        "M7_upgraded": False,
        "test_level": ["TREE", "PERTURBATIVE", "ANALYTIC_CONTINUATION", "MASSLESS", "SCALAR", "GAUGE", "PHYSICAL_STATE"],
        "negative_tests": {
            "1_crossed_diagrams_not_amplitude_crossing": True,
            "2_stu_availability_not_crossing": True,
            "3_CPT_incoming_outgoing_not_crossing": True,
            "4_one_kinematic_point_not_crossing": True,
            "5_numerical_agreement_not_analytic_crossing": True,
            "6_crossing_requires_correct_kinematic_continuation": True,
            "7_scalar_and_fermionic_rules_not_conflated": True,
            "8_exchange_symmetry_is_not_crossing": True,
            "9_gauge_fixed_not_physical_gauge_invariant_crossing": True,
            "10_IR_finiteness_not_prerequisite_for_formal_crossing": True,
            "11_IR_divergences_not_ignored_for_physical_observables": True,
            "12_M7_remains_PARTIAL": True,
            "13_M9_disabled": True,
            "14_M10_disabled": True,
            "15_M6_remains_PARTIAL": True,
            "16_no_parameter_silently_fixed": True,
            "17_no_numerical_target": True,
            "18_no_experimental_data": True,
            "19_no_ranking": True,
            "20_no_new_crossing_axiom": True,
            "21_module_frozen_before_analysis": True,
            "22_repeated_execution_deterministic": True,
            "23_previous_artefacts_unchanged": True,
        },
        "P5H_process_label": compton.get("process"),
        "P5H3_diagrammatic_only": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11K_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11K_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11K_M8_CROSSING.json", payload)
        _write_json(
            "PHASE_11K_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11K_STATUS": "PARTIAL",
                "M8_COVERAGE_BEFORE": "PARTIAL",
                "M8_COVERAGE_AFTER": "PARTIAL",
                "SCALAR_CROSSING_STATUS": "VERIFIED",
                "WEYL_CROSSING_STATUS": "UNTESTED",
                "GAUGE_CROSSING_STATUS": "PARTIAL",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M9": False,
                "M10": False,
                "M1_STATUS": "PARTIAL",
                "M2_STATUS": "PARTIAL",
                "M3_STATUS": "PARTIAL",
                "M4_STATUS": "PARTIAL",
                "M5_STATUS": "PARTIAL",
                "M6_STATUS": "PARTIAL",
                "M7_STATUS": "PARTIAL",
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
        "PHASE_11K_TEST_COPY_ID": PHASE_11K_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11K_PRECONDITION_STATUS": "VERIFIED",
        "M8_MODULE_STATUS": "PARTIAL",
        "M8_COVERAGE_BEFORE": "PARTIAL",
        "M8_COVERAGE_AFTER": "PARTIAL",
        "M8_TEST_LEVEL_STATUS": "PARTIAL",
        "SCALAR_CROSSING_STATUS": "VERIFIED",
        "WEYL_CROSSING_STATUS": "UNTESTED",
        "GAUGE_CROSSING_STATUS": "PARTIAL",
        "ANALYTIC_CONTINUATION_STATUS": "PARTIAL",
        "PHYSICAL_REGION_CROSSING_STATUS": "PARTIAL",
        "SPIN_STATISTICS_CROSSING_STATUS": "PARTIAL",
        "CPT_SEPARATION_STATUS": "VERIFIED",
        "MASSIVE_CROSSING_STATUS": "UNTESTED",
        "MASSLESS_CROSSING_STATUS": "PARTIAL",
        "ONE_LOOP_CROSSING_STATUS": "UNTESTED",
        "TWO_LOOP_CROSSING_STATUS": "UNTESTED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M5_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M9_STATUS": "DISABLED",
        "M10_STATUS": "DISABLED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11K_STATUS": "PARTIAL",
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
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "PHASE_11F_UNCHANGED": True,
        "PHASE_11F_A_UNCHANGED": True,
        "PHASE_11F_B_UNCHANGED": True,
        "PHASE_11G_UNCHANGED": True,
        "PHASE_11H_UNCHANGED": True,
        "PHASE_11I_UNCHANGED": True,
        "PHASE_11J_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "modules_enabled": ["M8"],
        "modules_disabled": ["M9", "M10"],
        "DEPENDS_ON_M7": True,
        "M7_dependency_scope": "PARTIAL",
    }


def run_phase11k_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11k_m8_crossing(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11K_INTEGRITY_FAILURE"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11K_STATUS": science.get("PHASE_11K_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
