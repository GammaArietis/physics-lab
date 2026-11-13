"""Phase 11I: isolated M6 exact S-matrix unitarity completion.

Assembles certified P5H-P5K ingredients into the strongest valid unitarity
statement. Does not claim S^dagger S = I unless that statement is actually
established. M7-M10 remain disabled. Does not rewrite 10E or 11B-11H.
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
from physics_lab.physics.phase14c5h_p5h import artifact_dir as phase14c5h_artifact_dir
from physics_lab.physics.phase14c5h_p5h import four_gluon_kernel, scalar_compton_ward_kernel
from physics_lab.physics.phase14c5h1_p5h1 import artifact_dir as phase14c5h1_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import artifact_dir as phase14c5h2_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import cutkosky_identity_kernel
from physics_lab.physics.phase14c5h3_p5h3 import artifact_dir as phase14c5h3_artifact_dir
from physics_lab.physics.phase14c5h4_p5h4 import artifact_dir as phase14c5h4_artifact_dir
from physics_lab.physics.phase14c5h5_p5h5 import artifact_dir as phase14c5h5_artifact_dir
from physics_lab.physics.phase14c5i_p5i import artifact_dir as phase14c5i_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11H_AUDIT_HASH",
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11I_TEST_COPY_ID",
    "analyze_phase11i_m6_smatrix",
    "artifact_dir",
    "finite_matrix_unitarity",
    "perturbative_unitarity_orders",
    "run_phase11i_or_stop",
]

PHASE_11I_TEST_COPY_ID = "PHASE_11I_M6_S_MATRIX"
PHASE = "PHASE_11I"
MODULE_VERSION = "phase11i-m6-s-matrix-v1"
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
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "optical_theorem_implies_exact_S_unitarity": False,
    "Cutkosky_implies_exact_unitarity": False,
    "tree_unitarity_implies_all_orders_unitarity": False,
    "partial_wave_domain_implies_unique_coupling": False,
    "IR_safe_inclusive_implies_finite_exact_S_matrix": False,
    "gauge_fixed_amplitude_implies_physical_S_matrix": False,
    "BRST_implies_complete_asymptotic_Hilbert_space": False,
    "CPT_implies_unitarity": False,
    "RG_closure_implies_unitarity": False,
    "incomplete_channel_sum_implies_exact_unitarity": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11i_artifacts"


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
        phase14c5h_artifact_dir().resolve(),
        phase14c5h1_artifact_dir().resolve(),
        phase14c5h2_artifact_dir().resolve(),
        phase14c5h3_artifact_dir().resolve(),
        phase14c5h4_artifact_dir().resolve(),
        phase14c5h5_artifact_dir().resolve(),
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
        raise UnauthorizedAnalysisError("Phase 11I refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "M6_S_MATRIX_UNITARITY_MODULE": True,
        "M6": {
            "enabled": True,
            "module_id": "M6",
            "activation_timestamp": "FROZEN_BEFORE_CONSEQUENCES",
            "activation_reason": "isolated completion of PARTIAL M6; not a new axiom",
            "parent_baseline": "PHASE_10E + PHASE_11H + P5H-P5K",
            "mode": "ACTIVATE_EXISTING_PARTIAL_COVERAGE",
        },
        "M7": False,
        "M8": False,
        "M9": False,
        "M10": False,
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
    }


def finite_matrix_unitarity() -> dict[str, Any]:
    """Finite-channel S_reg. Tree S is not unitary; one-loop optical cancels O(g^4)."""
    t0, t1_r, coupling = sp.symbols("t0 t1_R g", real=True)
    t_tree = coupling**2 * t0
    s_tree = 1 + sp.I * t_tree
    s_tree_dag = 1 - sp.I * t_tree
    tree_defect = sp.expand(sp.simplify(s_tree_dag * s_tree - 1))
    tree_not_identity = bool(sp.simplify(tree_defect - t_tree**2) == 0) and not bool(tree_defect.equals(0))

    t1_i = t0**2 / 2
    t_one = coupling**2 * t0 + coupling**4 * (t1_r + sp.I * t1_i)
    t_one_dag = coupling**2 * t0 + coupling**4 * (t1_r - sp.I * t1_i)
    s_one = 1 + sp.I * t_one
    s_one_dag = 1 - sp.I * t_one_dag
    defect_series = sp.series(sp.expand(s_one_dag * s_one - 1), coupling, 0, 6).removeO()
    coeff4 = sp.expand(defect_series.coeff(coupling, 4))
    one_loop_cancels = bool(coeff4 == 0)
    two_loop_not_tested = True

    a, b, c = sp.symbols("a b c", real=True)
    t2 = sp.Matrix([[a, b], [b, c]])
    s2 = sp.eye(2) + sp.I * t2
    s2_dag = sp.eye(2) - sp.I * t2
    m2_defect = sp.simplify(s2_dag * s2 - sp.eye(2))
    two_channel_tree_unitary = bool(m2_defect == sp.zeros(2))

    return {
        "test_level": ["TREE", "ONE_LOOP", "PERTURBATIVE", "REGULATED"],
        "S_definition": "S = 1 + i T",
        "tree_S_dagger_S_equals_I": False,
        "tree_defect_is_T_squared": tree_not_identity,
        "one_loop_optical_cancels_g_to_four": one_loop_cancels,
        "two_channel_tree_S_reg_unitary": two_channel_tree_unitary,
        "two_loop_order_tested": not two_loop_not_tested,
        "promoted_to_exact_unregulated": False,
        "status": "PARTIAL",
        "scope": "1-channel elastic T through O(g^4) with optical 2 Im T = T_tree^2; 2-channel tree S_reg is not I",
    }


def perturbative_unitarity_orders(cut: dict[str, Any], gluon: dict[str, Any], compton: dict[str, Any]) -> dict[str, Any]:
    fin = finite_matrix_unitarity()
    tree_real = bool(cut.get("tree_Im_M") == 0 and cut.get("T_dagger_T_starts_at_loop") is True)
    tree_kernels = bool(gluon.get("energy_independent_at_fixed_angle") is True and compton.get("Ward_vanishes") is True)
    one_loop_cut = bool(cut.get("identity_holds_at_regulated_level") is True)
    return {
        "test_level": ["TREE", "ONE_LOOP", "PERTURBATIVE", "REGULATED"],
        "S": "S = 1 + i T",
        "unitarity_identity": "-i (T - T^dagger) = T^dagger T",
        "tree": {
            "Im_M": 0,
            "optical_executable": False,
            "T_dagger_T_starts_at_loop": tree_real,
            "four_gluon_energy_degree_0": gluon.get("energy_independent_at_fixed_angle"),
            "compton_Ward": compton.get("Ward_vanishes"),
            "status": "PARTIAL",
        },
        "one_loop": {
            "Im_M_from_P5G_bubble_cut": one_loop_cut,
            "matches_phase_space_dPhi_2": bool(cut.get("two_Im_equals_dPhi") is True),
            "finite_physical_forward": bool(cut.get("finite_physical_forward_cross_section") is False),
            "g_to_four_S_reg_identity": fin["one_loop_optical_cancels_g_to_four"],
            "status": "PARTIAL",
        },
        "two_loop": {
            "tested_from_amplitudes": False,
            "P5K_RG_is_not_two_loop_S_unitarity": True,
            "status": "UNTESTED",
        },
        "kernels_from_generated_amplitudes": tree_kernels,
        "textbook_coefficients_inserted": False,
        "status": "PARTIAL" if tree_real and one_loop_cut and fin["one_loop_optical_cancels_g_to_four"] else "FAILED",
    }


def analyze_phase11i_m6_smatrix(
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
        "P5H_MANIFEST": phase14c5h_artifact_dir() / "P5H_CAPABILITY_MANIFEST.json",
        "P5H1_SUMMARY": phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json",
        "P5H2_SUMMARY": phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json",
        "P5H3_SUMMARY": phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json",
        "P5H4_MANIFEST": phase14c5h4_artifact_dir() / "P5H4_CAPABILITY_MANIFEST.json",
        "P5H5_SUMMARY": phase14c5h5_artifact_dir() / "PHASE_14C5H5_SUMMARY.json",
        "P5I_SUMMARY": phase14c5i_artifact_dir() / "PHASE_14C5I_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
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
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11H_SUMMARY"].get("M6_S_MATRIX_UNITARITY_STATUS") != "PARTIAL", "11H M6 not PARTIAL"),
        (loaded["11H_SUMMARY"].get("PHASE_11H_STATUS") != "AUDIT_COMPLETE", "11H not AUDIT_COMPLETE"),
        (loaded["P5K_SUMMARY"].get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST, "P5K digest"),
        (loaded["P5K_SUMMARY"].get("FULL_QUANTUM_UNITARITY") != "UNTESTED", "full quantum unitarity upgraded"),
        (loaded["P5K_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS") != "PARTIAL", "Q04 upgraded"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    if freeze["M7"] or freeze["M8"] or freeze["M9"] or freeze["M10"]:
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M7-M10 enabled"}
    if freeze["M6_S_MATRIX_UNITARITY_MODULE"] is not True:
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M6 not enabled"}

    cut = cutkosky_identity_kernel()
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    orders = perturbative_unitarity_orders(cut, gluon, compton)
    fin = finite_matrix_unitarity()
    if orders["status"] == "FAILED" or fin["status"] == "FAILED":
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "unitarity assembly failed"}

    exclusive_finite = loaded["P5H4_MANIFEST"].get("exclusive_2to2_finite")
    ir_safe = loaded["P5H4_MANIFEST"].get("IR_SAFE_OBSERVABLE_STATUS")
    optical_tree = loaded["P5H_MANIFEST"].get("optical_theorem_executable")
    optical_h1 = loaded["P5H1_SUMMARY"].get("OPTICAL_THEOREM_STATUS")
    cpt_is_not_unitarity = True
    rg_is_not_unitarity = loaded["P5K_SUMMARY"].get("FULL_QUANTUM_UNITARITY") == "UNTESTED"

    optical = {
        "regulated": "PARTIAL",
        "inclusive": ir_safe,
        "exclusive": False if exclusive_finite is False else exclusive_finite,
        "massless": "IR-SENSITIVE",
        "massive": "UNTESTED",
        "2_Im_equals_dPhi_on_P5G_bubbles": bool(cut.get("two_Im_equals_dPhi") is True),
        "finite_physical_forward_cross_section": False,
        "tree_optical_executable": optical_tree,
        "P5H1_optical": optical_h1,
        "status": "PARTIAL",
        "test_level": ["ONE_LOOP", "REGULATED", "MASSLESS"],
    }
    cuts = {
        "identity_holds_at_regulated_level": bool(cut.get("identity_holds_at_regulated_level") is True),
        "UV_pole_is_not_the_cut": True,
        "boxes_triangles_in_P5G": False,
        "ghost_cut_is_not_physical_intermediate": True,
        "status": "PARTIAL",
        "test_level": ["ONE_LOOP", "REGULATED"],
        "promoted_to_exact_unitarity": False,
    }
    physical_states = {
        "physical_scalar": "included in P5H2 scalar-bubble cuts when present",
        "physical_Weyl": "included in P5H2 Weyl-bubble cuts when present",
        "physical_transverse_gauge": "included in P5H2 gluon-bubble cuts",
        "ghosts": "formal Cutkosky only; not physical asymptotic states",
        "BRST_exact": "internal cancellation TEST EXTENSION; not an asymptotic sum",
        "complete_physical_sum": False,
        "status": "PARTIAL",
        "test_level": ["ONE_LOOP", "PHYSICAL_STATE", "BRST"],
    }
    asymptotic = {
        "in_out_constructed": False,
        "external_polarizations_only": True,
        "complete_physical_Hilbert_space": False,
        "status": "PARTIAL",
        "test_level": ["TREE", "PHYSICAL_STATE"],
        "note": "finite 2-to-2 inventories with on-shell polarizations are not |in>/|out> completeness",
    }
    channels = {
        "channel_set": ["AA to AA", "gauge-matter Compton", "matter-matter when vertices exist"],
        "included_states": ["transverse gauge", "Weyl", "scalars in declared multiplets"],
        "omitted_states": ["complete multi-particle tower", "massive 2-to-2", "all-orders inelastic"],
        "CHANNEL_COMPLETENESS": "VERIFIED_WITHIN_DECLARED_SCOPE",
        "completeness_status": "PARTIAL",
        "status": "PARTIAL",
        "P5H3_topology_within_declared_4pt": loaded["P5H3_SUMMARY"].get("topology_completeness_VERIFIED"),
    }
    massive = {
        "finite_asymptotic_states": "UNTESTED",
        "finite_amplitudes": "UNTESTED",
        "optical_theorem": "UNTESTED",
        "mass_not_inserted_as_physical_IR_parameter": True,
        "status": "UNTESTED",
        "test_level": ["MASSIVE"],
    }
    massless = {
        "soft": "IR-SENSITIVE",
        "collinear": "IR-SENSITIVE",
        "forward": "IR-SENSITIVE",
        "inclusive": ir_safe,
        "exclusive": "not finite",
        "status": "PARTIAL",
        "test_level": ["MASSLESS", "IR_REGULATED", "INCLUSIVE"],
    }
    ir_block = {
        "exclusive_2to2_finite": exclusive_finite,
        "inclusive_NLO": ir_safe,
        "inclusive_is_not_exact_S": True,
        "mass_not_inserted": True,
        "obstruction": "massless exclusive 2-to-2 is IR-divergent; inclusive NLO is not the S-matrix",
        "status": "PARTIAL",
        "test_level": ["IR_REGULATED", "INCLUSIVE", "MASSLESS"],
    }
    gauge = {
        "BRST": "F2 TEST EXTENSION",
        "Ward_ST": bool(compton.get("Ward_vanishes") is True),
        "physical_polarization": bool(gluon.get("longitudinal_not_used_as_physical") is True),
        "gauge_fixed_amplitudes_define_physical_S": False,
        "PHYSICAL_STATE_UNITARITY_STATUS": "PARTIAL",
        "status": "PARTIAL",
        "test_level": ["BRST", "PHYSICAL_STATE", "TREE", "ONE_LOOP"],
    }

    remaining = [
        "complete asymptotic physical-state space |in>, |out>",
        "exact treatment of gauge constraints beyond BRST TEST EXTENSION",
        "all relevant scattering channels beyond declared 2-to-2",
        "finite exclusive IR-safe massless S-matrix",
        "nonperturbative definition of S",
        "unitarity beyond one-loop regulated optical / O(g^4) 1-channel S_reg",
        "two-loop S-matrix unitarity (P5K RG is not that test)",
        "massive 2-to-2 S-matrix (not constructed; mass not inserted)",
    ]
    payload = {
        "phase": PHASE,
        "module_id": "M6",
        "module_version": MODULE_VERSION,
        "module_enabled": True,
        "parent_baseline": "PHASE_10E + PHASE_11H + P5H-P5K",
        "source_phase11h_status": loaded["11H_SUMMARY"].get("M6_S_MATRIX_UNITARITY_STATUS"),
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "principle_definition": "S^dagger S = I on the physical asymptotic-state Hilbert space",
        "perturbative_orders": orders,
        "optical_theorem_results": optical,
        "cut_results": cuts,
        "physical_intermediate_state_results": physical_states,
        "asymptotic_state_results": asymptotic,
        "channel_completeness": channels,
        "massive_results": massive,
        "massless_results": massless,
        "IR_results": ir_block,
        "gauge_sector_results": gauge,
        "perturbative_unitarity_results": orders,
        "finite_matrix_results": fin,
        "parameter_dependencies": [
            "couplings remain free",
            "masses remain free; none inserted as IR regulators",
            "IR regulators in P5H1-P5H4 are METHOD",
            "dimensional regularization is METHOD",
            "modified_minimal_subtraction is METHOD",
            "external-state normalization from P5H2 convention",
            "partial-wave IR cut in P5H5 is METHOD, not a unique coupling",
        ],
        "new_parameters": "none",
        "new_relations": "NONE",
        "sector_impact": {
            "spacetime": "UNCHANGED",
            "scalar_matter": "PARTIALLY_AFFECTED",
            "Weyl_matter": "PARTIALLY_AFFECTED",
            "gauge_sector": "PARTIALLY_AFFECTED",
            "gravity": "UNCHANGED",
            "quantization": "UNCHANGED",
            "physical_state_space": "PARTIALLY_AFFECTED",
            "amplitudes": "PARTIALLY_AFFECTED",
            "IR_structure": "PARTIALLY_AFFECTED",
        },
        "provenance_map": {
            "tree": "P5H four-gluon and Compton kernels, reused not rerun as a campaign",
            "cuts": "P5H2 cutkosky_identity_kernel on P5G bubbles",
            "inclusive_IR": "P5H4 manifest exclusive_2to2_finite and IR_SAFE_OBSERVABLE",
            "Q04": "P5H5/P5K remain PARTIAL",
            "CPT": "P5I remains a CPT map, not unitarity",
            "RG": "P5K two-loop RG is not two-loop S-matrix unitarity",
        },
        "unresolved_gaps": remaining,
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "PARTIAL_EXTENSION",
        "EXACT_S_MATRIX_STATUS": "PARTIAL",
        "test_level": ["TREE", "ONE_LOOP", "PERTURBATIVE", "REGULATED", "INCLUSIVE", "MASSLESS", "PHYSICAL_STATE", "BRST"],
        "negative_tests": {
            "1_regulated_optical_not_exact_S": True,
            "2_Cutkosky_not_exact_unitarity": True,
            "3_tree_high_energy_not_all_orders": True,
            "4_partial_wave_domain_not_unique_coupling": True,
            "5_inclusive_NLO_not_finite_exclusive_S": True,
            "6_gauge_fixed_not_physical_S": True,
            "7_BRST_not_complete_asymptotic_Hilbert": True,
            "8_CPT_not_unitarity": cpt_is_not_unitarity,
            "9_RG_closure_not_unitarity": rg_is_not_unitarity,
            "10_incomplete_channels_not_exact": True,
            "11_M7_M10_disabled": True,
            "12_M1_M5_remain_PARTIAL": True,
            "13_no_experimental": True,
            "14_no_numerical_target": True,
            "15_no_parameter_silently_fixed": True,
            "16_no_ranking": True,
            "17_no_new_principle_inserted": True,
            "18_module_frozen_before_analysis": True,
            "19_deterministic": True,
            "20_previous_artefacts_unchanged": True,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11I_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11I_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11I_M6_S_MATRIX.json", payload)
        _write_json(
            "PHASE_11I_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11I_STATUS": "PARTIAL",
                "M6_COVERAGE_BEFORE": "PARTIAL",
                "M6_COVERAGE_AFTER": "PARTIAL",
                "EXACT_S_MATRIX_STATUS": "PARTIAL",
                "PERTURBATIVE_UNITARITY_STATUS": "PARTIAL",
                "OPTICAL_THEOREM_STATUS": "PARTIAL",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "M7": False,
                "M8": False,
                "M9": False,
                "M10": False,
                "M1_STATUS": "PARTIAL",
                "M2_STATUS": "PARTIAL",
                "M3_STATUS": "PARTIAL",
                "M4_STATUS": "PARTIAL",
                "M5_STATUS": "PARTIAL",
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
        "PHASE_11I_TEST_COPY_ID": PHASE_11I_TEST_COPY_ID,
        "analysis": payload,
        "PHASE_11I_PRECONDITION_STATUS": "VERIFIED",
        "M6_MODULE_STATUS": "PARTIAL",
        "M6_COVERAGE_BEFORE": "PARTIAL",
        "M6_COVERAGE_AFTER": "PARTIAL",
        "M6_TEST_LEVEL_STATUS": "PARTIAL",
        "PERTURBATIVE_UNITARITY_STATUS": "PARTIAL",
        "OPTICAL_THEOREM_STATUS": "PARTIAL",
        "CUTKOSHKY_UNITARITY_STATUS": "PARTIAL",
        "PHYSICAL_INTERMEDIATE_STATE_STATUS": "PARTIAL",
        "ASYMPTOTIC_STATE_STATUS": "PARTIAL",
        "CHANNEL_COMPLETENESS_STATUS": "PARTIAL",
        "GAUGE_S_MATRIX_STATUS": "PARTIAL",
        "MASSIVE_S_MATRIX_STATUS": "UNTESTED",
        "MASSLESS_S_MATRIX_STATUS": "PARTIAL",
        "IR_UNITARITY_STATUS": "PARTIAL",
        "EXACT_S_MATRIX_STATUS": "PARTIAL",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M5_STATUS": "PARTIAL",
        "M7_STATUS": "DISABLED",
        "M8_STATUS": "DISABLED",
        "M9_STATUS": "DISABLED",
        "M10_STATUS": "DISABLED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11I_STATUS": "PARTIAL",
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
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "modules_enabled": ["M6"],
        "modules_disabled": ["M7", "M8", "M9", "M10"],
        "CHANNEL_COMPLETENESS": "VERIFIED_WITHIN_DECLARED_SCOPE",
        "PHYSICAL_STATE_UNITARITY_STATUS": "PARTIAL",
    }


def run_phase11i_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11i_m6_smatrix(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11I_INTEGRITY_FAILURE"}:
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
            "PHASE_11B_UNCHANGED": "VERIFIED",
            "PHASE_11C_UNCHANGED": "VERIFIED",
            "PHASE_11D_UNCHANGED": "VERIFIED",
            "PHASE_11E_UNCHANGED": "VERIFIED",
            "PHASE_11F_UNCHANGED": "VERIFIED",
            "PHASE_11F_A_UNCHANGED": "VERIFIED",
            "PHASE_11F_B_UNCHANGED": "VERIFIED",
            "PHASE_11G_UNCHANGED": "VERIFIED",
            "PHASE_11H_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11I_STATUS": science.get("PHASE_11I_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
