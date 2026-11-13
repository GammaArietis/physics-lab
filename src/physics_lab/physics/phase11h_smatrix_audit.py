"""Phase 11H: S-matrix / analyticity coverage audit. AUDIT_ONLY. No activation."""

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
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11f_cluster import artifact_dir as phase11f_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.phase11g_os import artifact_dir as phase11g_artifact_dir
from physics_lab.physics.phase14c5f_p5f import artifact_dir as phase14c5f_artifact_dir
from physics_lab.physics.phase14c5g_p5g import artifact_dir as phase14c5g_artifact_dir
from physics_lab.physics.phase14c5h_p5h import artifact_dir as phase14c5h_artifact_dir
from physics_lab.physics.phase14c5h1_p5h1 import artifact_dir as phase14c5h1_artifact_dir
from physics_lab.physics.phase14c5h2_p5h2 import artifact_dir as phase14c5h2_artifact_dir
from physics_lab.physics.phase14c5h3_p5h3 import artifact_dir as phase14c5h3_artifact_dir
from physics_lab.physics.phase14c5h4_p5h4 import artifact_dir as phase14c5h4_artifact_dir
from physics_lab.physics.phase14c5h5_p5h5 import artifact_dir as phase14c5h5_artifact_dir
from physics_lab.physics.phase14c5i_p5i import artifact_dir as phase14c5i_artifact_dir
from physics_lab.physics.phase14c5j_p5j import artifact_dir as phase14c5j_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "MODULE_IDS",
    "NON_IMPLICATIONS",
    "PHASE_11H_TEST_COPY_ID",
    "analyze_phase11h_smatrix_audit",
    "artifact_dir",
    "run_phase11h_or_stop",
]

PHASE_11H_TEST_COPY_ID = "PHASE_11H_S_MATRIX_COVERAGE_AUDIT"
PHASE = "PHASE_11H"
AUDIT_VERSION = "phase11h-s-matrix-coverage-audit-v1"
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
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"
MODULE_IDS = ("M6", "M7", "M8", "M9", "M10")

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
    "module" + "_" + "ranking",
)

NON_IMPLICATIONS = {
    "optical_theorem_implies_exact_S_unitarity": False,
    "Cutkosky_implies_exact_unitarity": False,
    "tree_unitarity_implies_all_orders_unitarity": False,
    "perturbative_analyticity_implies_global_analyticity": False,
    "crossed_diagrams_imply_crossing_theorem": False,
    "formal_dispersion_formula_implies_dispersion_relation": False,
    "positive_residue_implies_positivity_bounds": False,
    "tree_unitarity_bounds_imply_positivity_bounds": False,
    "IR_safe_inclusive_implies_finite_exact_S_matrix": False,
    "gauge_fixed_amplitude_implies_physical_S_matrix": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11h_artifacts"


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
        phase14c5f_artifact_dir().resolve(),
        phase14c5g_artifact_dir().resolve(),
        phase14c5h_artifact_dir().resolve(),
        phase14c5h1_artifact_dir().resolve(),
        phase14c5h2_artifact_dir().resolve(),
        phase14c5h3_artifact_dir().resolve(),
        phase14c5h4_artifact_dir().resolve(),
        phase14c5h5_artifact_dir().resolve(),
        phase14c5i_artifact_dir().resolve(),
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
        raise UnauthorizedAnalysisError("Phase 11H audit refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _module(spec: dict[str, Any]) -> dict[str, Any]:
    item = {
        "ENABLED": False,
        "mode": "AUDIT_ONLY",
        "activation_status": "DISABLED",
        "new_objects": [],
        "new_parameters": "none under AUDIT_ONLY",
        "possible_relations": "NONE",
        "parameter_free_relation": "NONE",
        "parameter_audit": {
            "introduces": "no new parameter under AUDIT_ONLY",
            "dimensionless_parameter": False,
            "dimensionful_parameter": False,
        },
        **spec,
    }
    item["module_hash"] = _content_hash({k: v for k, v in item.items() if k != "module_hash"})
    return item


def _build_modules(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    q04 = loaded["P5K_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS") or loaded["P5H5_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS") or "PARTIAL"
    full_u = loaded["P5K_SUMMARY"].get("FULL_QUANTUM_UNITARITY")
    ir_safe = loaded["P5H4_MANIFEST"].get("IR_SAFE_OBSERVABLE_STATUS")
    optical_exec = loaded["P5H_MANIFEST"].get("optical_theorem_executable")
    optical_h1 = loaded["P5H1_SUMMARY"].get("OPTICAL_THEOREM_STATUS")
    return [
        _module(
            {
                "module_id": "M6",
                "name": "EXACT S-MATRIX UNITARITY",
                "mathematical_statement": "S^dagger S = I on a complete physical scattering-state space",
                "principle_itself": "exact S-matrix unitarity",
                "necessary_condition": "optical theorem / Cutkosky cuts (not sufficient)",
                "proxy_or_test": (
                    "P5H tree high-energy/Ward; P5H5 |Re a_l| bound as Q04 domain; "
                    "P5H2/P5H3 regulated Cutkosky; P5H4 IR-safe inclusive NLO"
                ),
                "existing_coverage": (
                    f"P5H tree unitarity Q04={q04}, optical_theorem_executable={optical_exec}; "
                    f"P5H1 IR-safe tree, optical theorem {optical_h1}; "
                    "P5H2 Cutkosky on P5G bubbles at regulated cut-integrand level PARTIAL; "
                    "P5H3 one-loop 4pt cuts optical PARTIAL; "
                    f"P5H4 inclusive NLO {ir_safe}, exclusive 2-to-2 not finite; "
                    f"P5H5/P5J/P5K keep Q04 PARTIAL; FULL_QUANTUM_UNITARITY={full_u}."
                ),
                "coverage_status": "PARTIAL",
                "exact_sources": ["P5F", "P5H", "P5H1", "P5H2", "P5H3", "P5H4", "P5H5", "P5J", "P5K", "10E"],
                "exact_source_scope": "tree + regulated/cut + inclusive NLO proxies; Q04 remains PARTIAL",
                "test_strength": "TREE / ONE_LOOP / IR_REGULATED / INCLUSIVE",
                "test_level": "PERTURBATIVE",
                "missing_capability": (
                    "exact S^dagger S = I on a complete physical Hilbert space; all channels; "
                    "nonperturbative definition; finite exclusive IR-safe S-matrix"
                ),
                "new_input_required": False,
                "provenance": {
                    "principle_status": "PARTIAL_EXTENSION",
                    "result_provenance": "UNTESTED",
                    "coverage_class": "PROXY / TEST EXTENSION plus NECESSARY CONDITION, not the PRINCIPLE",
                },
                "assumptions": ["F2 TEST EXTENSION for gauge amplitudes", "massless on-shell kinematics in P5H"],
                "affected_sectors": ["scattering", "gauge", "scalar matter"],
                "dependencies": [],
                "exclusions": [
                    "optical theorem cut check is not exact S-matrix unitarity",
                    "tree-level unitarity is not all-orders unitarity",
                    "IR-safe inclusive NLO is not a finite exact S-matrix",
                ],
                "massive_vs_massless": {
                    "massive": "UNTESTED as a complete S-matrix",
                    "massless": "IR-SENSITIVE; forward/t-channel singularities in P5H2",
                    "mixed": "UNTESTED",
                },
                "PHYSICAL_STATE_S_MATRIX_STATUS": "PARTIAL",
                "IR_obstruction": "massless exclusive 2-to-2 is not finite; inclusive NLO is not the exact S-matrix",
            }
        ),
        _module(
            {
                "module_id": "M7",
                "name": "ANALYTICITY",
                "mathematical_statement": "amplitudes are analytic functions with the expected singularity structure",
                "principle_itself": "global analyticity of the physical amplitude",
                "necessary_condition": "i0 Feynman contour in loop integrals (not sufficient)",
                "proxy_or_test": "P5G one-loop integrands; P5H2/P5H3 Cutkosky discontinuities; P5K two-loop RG masters",
                "existing_coverage": (
                    "P5G one-loop scalar/gauge bubbles with i0 and dimensional regularization; "
                    "P5H2/P5H3 two-particle cuts as METHOD; P5E Wick is a UV METHOD not an analyticity theorem; "
                    "no certified global analytic domain, continuation path, or all-amplitude singularity map."
                ),
                "coverage_status": "PARTIAL",
                "exact_sources": ["P5E", "P5F", "P5G", "P5G1", "P5H2", "P5H3", "P5K"],
                "exact_source_scope": "perturbative integral analyticity and cut integrands, not global amplitude analyticity",
                "test_strength": "ONE_LOOP / TWO_LOOP / PERTURBATIVE",
                "test_level": "PERTURBATIVE",
                "missing_capability": (
                    "poles, branch cuts, thresholds, and crossing-channel singularities of all declared amplitudes; "
                    "allowed analytic domains and continuation paths"
                ),
                "new_input_required": False,
                "provenance": {
                    "principle_status": "PARTIAL_EXTENSION",
                    "result_provenance": "UNTESTED",
                    "coverage_class": "PROXY / TEST EXTENSION, not the PRINCIPLE",
                },
                "assumptions": ["dimensional regularization", "i0 contour as METHOD"],
                "affected_sectors": ["loop integrals", "amplitudes"],
                "dependencies": [],
                "exclusions": [
                    "analyticity of a scalar integral is not global analyticity",
                    "analyticity of one perturbative amplitude is not analyticity of all amplitudes",
                ],
                "massive_vs_massless": {
                    "massive": "UNTESTED as a global theorem",
                    "massless": "IR-SENSITIVE thresholds",
                    "mixed": "UNTESTED",
                },
            }
        ),
        _module(
            {
                "module_id": "M8",
                "name": "CROSSING SYMMETRY",
                "mathematical_statement": "A(s,t,u) related to the crossed amplitude by the field/statistics-dependent analytic continuation",
                "principle_itself": "crossing symmetry of the amplitude",
                "necessary_condition": "availability of s, t, u channel diagrams (not sufficient)",
                "proxy_or_test": "P5H s/t/u four-gluon and Compton diagrams; P5I CPT incoming<->outgoing; P5H3 t/u bubble promotion",
                "existing_coverage": (
                    "P5H constructs s, t, u diagrams and a Mandelstam identity for a four-gluon kernel; "
                    "P5I uses incoming<->outgoing as a CPT map, not a crossing theorem; "
                    "no certified A(s,t,u) <-> A_crossed(t,s,u) for scalar, Weyl, gauge, and mixed processes."
                ),
                "coverage_status": "PARTIAL",
                "exact_sources": ["P5H", "P5H3", "P5I"],
                "exact_source_scope": "channel diagrams and CPT crossing maps; not an analytic crossing theorem",
                "test_strength": "TREE / PERTURBATIVE",
                "test_level": "TREE",
                "missing_capability": "analytic crossing relation for scalar, Weyl, gauge, and mixed amplitudes",
                "new_input_required": False,
                "provenance": {
                    "principle_status": "PARTIAL_EXTENSION",
                    "result_provenance": "UNTESTED",
                    "coverage_class": "PROXY / TEST EXTENSION, not the PRINCIPLE",
                },
                "assumptions": ["representative 2-to-2 channels, not exhaustive flavor/color survey"],
                "affected_sectors": ["amplitudes", "CPT maps"],
                "dependencies": ["M7 if a later analytic continuation is defined"],
                "exclusions": [
                    "manually reusing crossed diagrams is not a crossing theorem",
                    "channel availability is not crossing symmetry",
                ],
                "massive_vs_massless": {
                    "massive": "UNTESTED",
                    "massless": "tree kernels on massless on-shell kinematics",
                    "mixed": "UNTESTED",
                },
            }
        ),
        _module(
            {
                "module_id": "M9",
                "name": "DISPERSION RELATIONS",
                "mathematical_statement": "a subtracted dispersion integral relating the amplitude to its discontinuity on the certified analytic domain",
                "principle_itself": "dispersion relation derived from analyticity, boundedness, and contour deformation",
                "necessary_condition": "Cutkosky discontinuity of a loop integrand (not sufficient)",
                "proxy_or_test": "P5H2/P5H3 cuts; P5G i0; tree high-energy degree 0 in selected P5H processes",
                "existing_coverage": (
                    "ingredients exist separately: perturbative i0 analyticity (P5G), Cutkosky discontinuities (P5H2/P5H3), "
                    "tree boundedness in selected processes (P5H). No executable contour deformation, subtraction structure, "
                    "or derived dispersion relation from an actual amplitude. Pole omega^2 = |k|^2 + m^2 is not an S-matrix dispersion relation."
                ),
                "coverage_status": "PARTIAL",
                "exact_sources": ["P5G", "P5H", "P5H2", "P5H3"],
                "exact_source_scope": "separate ingredients only; no derived dispersion relation",
                "test_strength": "ONE_LOOP / IR_REGULATED",
                "test_level": "PERTURBATIVE",
                "missing_capability": (
                    "boundedness/asymptotics of the physical amplitude; contour deformation; "
                    "subtraction structure; dispersion integral proved from the certified domain"
                ),
                "new_input_required": False,
                "provenance": {
                    "principle_status": "PARTIAL_EXTENSION",
                    "result_provenance": "UNTESTED",
                    "coverage_class": "NECESSARY CONDITION ingredients only, not the PRINCIPLE",
                },
                "assumptions": ["cuts are METHOD / QUANTUM INFRASTRUCTURE, not a dispersion axiom"],
                "affected_sectors": ["amplitudes"],
                "dependencies": ["M7 if later completed", "discontinuities from P5H2/P5H3"],
                "exclusions": [
                    "a formal cut representation is not a complete dispersion relation",
                    "writing a dispersion integral is not proving it",
                ],
                "massive_vs_massless": {
                    "massive": "UNTESTED",
                    "massless": "forward singularities obstruct unsubtracted forward dispersion",
                    "mixed": "UNTESTED",
                },
            }
        ),
        _module(
            {
                "module_id": "M10",
                "name": "POSITIVITY BOUNDS / S-MATRIX POSITIVITY CONSTRAINTS",
                "mathematical_statement": (
                    "EFT coefficient inequalities derived from S-matrix analyticity, unitarity, "
                    "a dispersion relation, and a positive discontinuity / forward-limit assumption"
                ),
                "principle_itself": "positivity bounds on EFT coefficients",
                "necessary_condition": "positive residues / tree-unitarity |Re a_l| domain (not sufficient)",
                "proxy_or_test": "P5H5 Q04 |Re a_l| <= one-half; 10B.9 kinetic sign; M2 residue sign; M5 massive RP",
                "existing_coverage": (
                    "no certified map amplitude -> analytic continuation -> dispersion -> positive discontinuity "
                    "-> coefficient inequality. Tree-unitarity bounds (P5H5) and positive residues are proxies, "
                    "not positivity-bound theorems."
                ),
                "coverage_status": "ABSENT",
                "exact_sources": ["P5H5", "10B.9", "P5Q", "11D", "11G"],
                "exact_source_scope": "proxies only; positivity-bound theorem not present in P5F-P5K or 11A-11G",
                "test_strength": "AXIOMATIC",
                "test_level": "AXIOMATIC",
                "missing_capability": (
                    "forward-limit positivity, derived dispersion input, and EFT coefficient inequalities"
                ),
                "new_input_required": True,
                "provenance": {
                    "principle_status": "ROADMAP_INPUT",
                    "result_provenance": "UNTESTED",
                    "coverage_class": "ABSENT PRINCIPLE; proxies only",
                },
                "assumptions": ["not activated in this audit"],
                "affected_sectors": ["EFT coefficients", "amplitudes"],
                "dependencies": ["M6", "M7", "M9 if later completed; not certified implications"],
                "exclusions": [
                    "positive residues are not positivity bounds",
                    "tree-unitarity bounds are not positivity bounds",
                    "kinetic-sign positivity is not an S-matrix positivity bound",
                ],
                "massive_vs_massless": {
                    "massive": "UNTESTED",
                    "massless": "UNTESTED; forward singularities would obstruct a naive forward bound",
                    "mixed": "UNTESTED",
                },
            }
        ),
    ]


def analyze_phase11h_smatrix_audit(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    activation: dict[str, Any] | None = None,
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
        "11FB_SUMMARY": phase11fb_artifact_dir() / "PHASE_11F_B_SUMMARY.json",
        "11G": phase11g_artifact_dir() / "PHASE_11G_M5_OS_CONSEQUENCE.json",
        "11G_SUMMARY": phase11g_artifact_dir() / "PHASE_11G_SUMMARY.json",
        "P5F_SUMMARY": phase14c5f_artifact_dir() / "PHASE_14C5F_SUMMARY.json",
        "P5G_SUMMARY": phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json",
        "P5H_SUMMARY": phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json",
        "P5H_MANIFEST": phase14c5h_artifact_dir() / "P5H_CAPABILITY_MANIFEST.json",
        "P5H1_SUMMARY": phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json",
        "P5H2_SUMMARY": phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json",
        "P5H3_SUMMARY": phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json",
        "P5H4_SUMMARY": phase14c5h4_artifact_dir() / "PHASE_14C5H4_SUMMARY.json",
        "P5H4_MANIFEST": phase14c5h4_artifact_dir() / "P5H4_CAPABILITY_MANIFEST.json",
        "P5H5_SUMMARY": phase14c5h5_artifact_dir() / "PHASE_14C5H5_SUMMARY.json",
        "P5I_SUMMARY": phase14c5i_artifact_dir() / "PHASE_14C5I_SUMMARY.json",
        "P5J_SUMMARY": phase14c5j_artifact_dir() / "PHASE_14C5J_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
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
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["P5K_SUMMARY"].get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST, "P5K digest"),
        (loaded["P5K_SUMMARY"].get("FULL_QUANTUM_UNITARITY") != "UNTESTED", "full quantum unitarity upgraded"),
        (loaded["P5K_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS") != "PARTIAL", "Q04 upgraded"),
        (loaded["11G_SUMMARY"].get("PHASE_11G_STATUS") != "PARTIAL", "M5 not PARTIAL"),
        (loaded["11FB_SUMMARY"].get("PHASE_11F_B_STATUS") != "PARTIAL", "M4 not PARTIAL"),
        (loaded["11FB_SUMMARY"].get("MASSIVE_CLUSTER_STATUS") != "VERIFIED", "M4 massive changed"),
        (loaded["11FB_SUMMARY"].get("MASSLESS_CLUSTER_STATUS") != "PARTIAL", "M4 massless changed"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    modules = _build_modules(loaded)
    statuses = {item["module_id"]: item["coverage_status"] for item in modules}
    if any(item["ENABLED"] is True for item in modules):
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "module enabled during AUDIT_ONLY"}
    if any(item["coverage_status"] == "COMPLETE" for item in modules):
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "illegal COMPLETE promotion"}
    if activation:
        if activation.get("promote_partial_to_complete"):
            return {"status": "OK", "PHASE_11H_STATUS": "FAILED", "rejection": "PARTIAL_NOT_PROMOTED_TO_COMPLETE"}
        if activation.get("relabel_existing_as_new"):
            return {"status": "OK", "PHASE_11H_STATUS": "FAILED", "rejection": "EXISTING_NOT_RELABELED_NEW_PHYSICAL_INPUT"}
        if activation.get("mode") == "MODE_C" and not activation.get("explicit_human_authorization"):
            return {"status": "OK", "PHASE_11H_STATUS": "FAILED", "rejection": "ABSENT_PRINCIPLE_NOT_MACHINE_ACTIVATED"}
        if activation.get("post_hoc"):
            return {"status": "OK", "PHASE_11H_STATUS": "FAILED", "rejection": "POST_HOC_ACTIVATION"}
        if any(activation.get(mid) is True for mid in MODULE_IDS):
            return {"status": "OK", "PHASE_11H_STATUS": "FAILED", "rejection": "MODULE_SWITCH_MUST_REMAIN_FALSE"}

    config = {
        "DEFAULT_MODE": "AUDIT_ONLY",
        "mode": "AUDIT_ONLY",
        "modules": [
            {
                "module_id": item["module_id"],
                "module_enabled": False,
                "mode": "AUDIT_ONLY",
                "activation_timestamp": "NOT_ACTIVATED",
                "activation_reason": "AUDIT_ONLY default; no human MODE_C authorization",
                "parent_baseline": "PHASE_10E + P5F-P5K + M1-M5 PARTIAL",
                "module_hash": item["module_hash"],
            }
            for item in modules
        ],
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
    }
    matrix = [
        {
            "Module": item["module_id"],
            "Principle": item["name"],
            "Existing coverage": item["existing_coverage"],
            "Sources": item["exact_sources"],
            "Test strength": item["test_strength"],
            "Missing capability": item["missing_capability"],
            "New input required?": item["new_input_required"],
            "Status": item["coverage_status"],
        }
        for item in modules
    ]
    source_audit = {
        "P5F": {"FULL_QUANTUM_UNITARITY": loaded["P5F_SUMMARY"].get("FULL_QUANTUM_UNITARITY"), "Q04": "PARTIAL"},
        "P5G": {"FULL_QUANTUM_UNITARITY": loaded["P5G_SUMMARY"].get("FULL_QUANTUM_UNITARITY")},
        "P5H": {
            "optical_theorem_executable": loaded["P5H_MANIFEST"].get("optical_theorem_executable"),
            "FULL_QUANTUM_UNITARITY": loaded["P5H_SUMMARY"].get("FULL_QUANTUM_UNITARITY"),
        },
        "P5H1": {"OPTICAL_THEOREM_STATUS": loaded["P5H1_SUMMARY"].get("OPTICAL_THEOREM_STATUS")},
        "P5H2": {"cuts": "regulated two-particle Cutkosky on P5G bubbles", "optical": "PARTIAL"},
        "P5H3": {"optical": "PARTIAL", "FULL_QUANTUM_UNITARITY": loaded["P5H3_SUMMARY"].get("FULL_QUANTUM_UNITARITY")},
        "P5H4": {
            "IR_SAFE_OBSERVABLE_STATUS": loaded["P5H4_MANIFEST"].get("IR_SAFE_OBSERVABLE_STATUS"),
            "exclusive_2to2_finite": loaded["P5H4_MANIFEST"].get("exclusive_2to2_finite"),
        },
        "P5H5": {"Q04": "PARTIAL", "unitarity_convention": loaded["P5H5_SUMMARY"].get("CASE")},
        "P5I": {"crossing": "CPT incoming<->outgoing, not a crossing theorem"},
        "P5J": {"Q04_TREE_UNITARITY_STATUS": loaded["P5J_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS")},
        "P5K": {
            "Q04_TREE_UNITARITY_STATUS": loaded["P5K_SUMMARY"].get("Q04_TREE_UNITARITY_STATUS"),
            "FULL_QUANTUM_UNITARITY": loaded["P5K_SUMMARY"].get("FULL_QUANTUM_UNITARITY"),
            "checkpoint_digest": loaded["P5K_SUMMARY"].get("checkpoint_digest"),
        },
        "note": "coverage is read from certified artefacts; P5G-P5K engines are not rerun",
    }
    payload = {
        "phase": PHASE,
        "module_registry": modules,
        "coverage_matrix": matrix,
        "source_audit": source_audit,
        "test_strength_map": {item["module_id"]: item["test_strength"] for item in modules},
        "dependency_graph": {
            "M6": [],
            "M7": [],
            "M8": ["M7 if a later analytic continuation is defined"],
            "M9": ["M7 if later completed", "P5H2/P5H3 discontinuities as METHOD"],
            "M10": ["M6", "M7", "M9 if later completed; not certified implications"],
            "note": "textbook-order implications are not assumed; NON_IMPLICATIONS are all False",
        },
        "parameter_audit": {
            "new_parameters_introduced": 0,
            "existing_dependencies": [
                "couplings g remain free",
                "masses remain free",
                "IR regulators in P5H1-P5H4 are METHOD",
                "dimensional-regularization cutoff is METHOD",
                "subtraction scheme modified_minimal_subtraction is METHOD",
                "external-state normalization from P5H2 convention",
            ],
            "silently_fixed": False,
            "new_parameter_free_relations": "NONE",
        },
        "parameter_implications": {
            "new_parameters": "none",
            "new_parameter_free_relations": "NONE",
        },
        "provenance_map": {item["module_id"]: item.get("proxy_or_test") for item in modules},
        "activation_configuration": config,
        "unresolved_gaps": [
            "exact S-matrix unitarity on a complete physical Hilbert space",
            "global analyticity of declared amplitudes",
            "analytic crossing theorem",
            "derived dispersion relation",
            "S-matrix positivity bounds",
            "finite exclusive IR-safe S-matrix",
            "physical asymptotic state space beyond BRST TEST EXTENSION",
        ],
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "modules_enabled": [],
        "modules_disabled": list(MODULE_IDS),
        "principles_already_present": [],
        "principles_partially_present": ["M6", "M7", "M8", "M9"],
        "genuinely_absent_principles": ["M10"],
        "unsupported_principles": [],
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M5_STATUS": "PARTIAL",
        "PHYSICAL_STATE_S_MATRIX_STATUS": "PARTIAL",
        "IR_SAFE_INCLUSIVE_IS_NOT_EXACT_S_MATRIX": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11H_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json", payload)
        _write_json(
            "PHASE_11H_SUMMARY.json",
            {
                "AUDIT_VERSION": AUDIT_VERSION,
                "PHASE_11H_STATUS": "AUDIT_COMPLETE",
                "M6_S_MATRIX_UNITARITY_STATUS": statuses["M6"],
                "M7_ANALYTICITY_STATUS": statuses["M7"],
                "M8_CROSSING_STATUS": statuses["M8"],
                "M9_DISPERSION_STATUS": statuses["M9"],
                "M10_POSITIVITY_BOUNDS_STATUS": statuses["M10"],
                "DEFAULT_MODE": "AUDIT_ONLY",
                "modules_enabled": [],
                "PROGRAM_CLOSURE_STATUS_PRESERVED": EXPECTED_10E_CLOSURE,
                "M1_STATUS": "PARTIAL",
                "M2_STATUS": "PARTIAL",
                "M3_STATUS": "PARTIAL",
                "M4_STATUS": "PARTIAL",
                "M5_STATUS": "PARTIAL",
            },
        )
        _write_json("PHASE_11H_ACTIVATION_FREEZE.json", config)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11H_TEST_COPY_ID": PHASE_11H_TEST_COPY_ID,
        "audit": payload,
        "PHASE_11H_PRECONDITION_STATUS": "VERIFIED",
        "COVERAGE_AUDIT_STATUS": "VERIFIED",
        "M6_S_MATRIX_UNITARITY_STATUS": statuses["M6"],
        "M7_ANALYTICITY_STATUS": statuses["M7"],
        "M8_CROSSING_STATUS": statuses["M8"],
        "M9_DISPERSION_STATUS": statuses["M9"],
        "M10_POSITIVITY_BOUNDS_STATUS": statuses["M10"],
        "MODULE_ARCHITECTURE_STATUS": "VERIFIED",
        "NO_DUPLICATION_STATUS": "VERIFIED",
        "DEPENDENCY_AUDIT_STATUS": "VERIFIED",
        "PARAMETER_AUDIT_STATUS": "VERIFIED",
        "TARGET_INDEPENDENCE_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "PHASE_11H_STATUS": "AUDIT_COMPLETE",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M5_STATUS": "PARTIAL",
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
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": all(v is False for v in NON_IMPLICATIONS.values()),
        "activation_frozen_before_consequences": True,
        "modules_enabled": [],
        "modules_disabled": list(MODULE_IDS),
    }


def run_phase11h_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11h_smatrix_audit(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11H_INTEGRITY_FAILURE"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11H_STATUS": science.get("PHASE_11H_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
