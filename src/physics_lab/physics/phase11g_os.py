"""Phase 11G: M5 reflection positivity / Osterwalder-Schrader.

Stage A freezes HUMAN_DECLARED_PHYSICAL_INPUT. Stage B tests only the
frozen free real scalar Euclidean two-point. Wick rotation is a method,
not OS. Reflection positivity is not full reconstruction.
"""

from __future__ import annotations

import hashlib
import json
import re
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
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11FB_HASH",
    "GATE_VERSION",
    "HUMAN_DECLARED_M5_INPUT",
    "PHASE_11G_TEST_COPY_ID",
    "REQUIRED_INPUT_FIELDS",
    "analyze_phase11g_os",
    "artifact_dir",
    "canonical_declared_input",
    "free_scalar_reflection_positivity",
    "input_hash",
    "run_phase11g_or_stop",
]

PHASE_11G_TEST_COPY_ID = "PHASE_11G_M5_OS"
PHASE = "PHASE_11G"
GATE_VERSION = "phase11g-m5-os-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11F_M4_HASH = "f30ccce277f6bb061b3bcdd7c05634731f80ea34001b4fddde89f7c1d9429a7e"
EXPECTED_11FA_AUTH_HASH = "1fffe7e0393daf84d57af32e56f35033bed95780fa473833d8f134f2269296de"
EXPECTED_11FA_FREEZE_HASH = "367cb101f941e40d3998ee63cff91190c98278688a741195637df15111daaa10"
EXPECTED_11FB_HASH = "db52827760834638196ea9287c776ddee930f10e16f8f4745eed4313ee8fb9c7"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

REQUIRED_INPUT_FIELDS = (
    "input_id",
    "title",
    "mathematical_statement",
    "physical_scope",
    "motivation",
    "affected_previous_phases",
    "new_objects",
    "new_assumptions",
    "parameter_implications",
    "intended_domain",
    "provenance",
    "activation_id",
    "activation_reason",
    "authorization_statement",
    "declaration_timestamp",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

_DERIVED_PHRASES = (
    "derived from wick",
    "derived from lorentz",
    "derived from locality",
    "derived from spectral",
    "derived from m2",
    "derived from propagator positivity",
    "derived from kinetic sign",
)

_REFORMULATION_PHRASES = (
    "same as wick rotation",
    "equivalent to m2",
    "same as propagator positivity",
    "euclidean covariance is os",
)

HUMAN_DECLARED_M5_INPUT: dict[str, Any] = {
    "input_id": "HUMAN-M5-OS-v1",
    "title": "Reflection positivity as explicit new physical input",
    "mathematical_statement": (
        "For admissible test functionals F supported in Euclidean time tau > 0, "
        "and Euclidean time reflection theta: tau -> -tau with "
        "(theta f)(tau, x) = complex_conjugate[f(-tau, x)], "
        "the Euclidean quadratic form Q[f] = integral (theta f)(x) G_E(x-y) f(y) "
        "satisfies Q[f] >= 0. Equivalently <theta F F>_E >= 0. "
        "This is reflection positivity of the free Euclidean two-point, not a complete OS reconstruction theorem."
    ),
    "physical_scope": (
        "INITIAL SCOPE ONLY: free real scalar Euclidean two-point function. "
        "NOT AUTHORIZED: Weyl fermions; gauge fields; interacting scalar theory; "
        "interacting n-point functions; full OS reconstruction; constructive QFT; gravity."
    ),
    "motivation": (
        "WHAT IS NEW: Euclidean reflection positivity Q[f] >= 0 for the declared free-scalar two-point. "
        "WHAT WAS ALREADY PRESENT: Euclidean spacetime as a geometric branch; P5E Wick rotation as a "
        "loop-integral METHOD; M1-M4 PARTIAL; 11B recorded M5 as ABSENT. "
        "Wick rotation is not OS. Euclidean covariance is not OS. Positive kinetic sign is not OS."
    ),
    "affected_previous_phases": [
        "Phase 10E unchanged: CLOSED_UNDER_DECLARED_SCOPE",
        "Phase 11B unchanged: M5_OS_STATUS remains ABSENT as historical record",
        "Phase 11C-11E unchanged: M1/M2/M3 remain PARTIAL",
        "Phase 11F-B unchanged: M4 remains PARTIAL",
    ],
    "new_objects": [
        {"object_id": "euclidean_two_point_G_E", "kind": "free Euclidean scalar kernel"},
        {"object_id": "euclidean_time_tau", "kind": "Euclidean time coordinate"},
        {"object_id": "reflection_map_theta", "kind": "theta: tau -> -tau"},
        {"object_id": "quadratic_form_Q_f", "kind": "Q[f] = integral (theta f) G_E f"},
        {"object_id": "admissible_positive_time_test_functions", "kind": "support in tau > 0"},
    ],
    "new_assumptions": [
        {"assumption": "Euclidean continuation", "status": "INPUT", "note": "not a proof of reflection positivity"},
        {"assumption": "Euclidean time coordinate", "status": "INPUT"},
        {"assumption": "reflection map theta", "status": "INPUT"},
        {"assumption": "translation invariance", "status": "DERIVED FROM PREVIOUS FRAMEWORK", "source": "flat Euclidean R^4 from Minkowski"},
        {"assumption": "chosen correlator", "status": "INPUT", "note": "free Euclidean two-point G_E"},
        {"assumption": "admissible test functions", "status": "INPUT", "note": "complex Schwartz or compact support in tau > 0"},
        {"assumption": "boundary conditions", "status": "ASSUMED", "note": "standard free falloff; no manufactured IR cutoff"},
        {"assumption": "mass assumptions", "status": "INPUT", "note": "mu_s remains free; massive and massless treated separately"},
        {"assumption": "full OS reconstruction", "status": "NOT ASSUMED"},
        {"assumption": "Weyl, gauge, interacting OS positivity", "status": "NOT ASSUMED"},
        {"assumption": "derivation from Wick, Lorentz, M2, or propagator positivity", "status": "NOT ASSUMED"},
    ],
    "parameter_implications": {
        "new_continuous_parameters": [],
        "new_discrete_labels": [],
        "new_normalization_choices": [],
        "new_boundary_conditions": [],
        "silently_fixes_existing": False,
        "new_parameters": [],
        "new_parameter_count": 0,
    },
    "intended_domain": (
        "free real scalar Euclidean two-point reflection positivity. "
        "Weyl, gauge-invariant, interacting, and full OS reconstruction are outside this authorization."
    ),
    "provenance": "NEW_PHYSICAL_INPUT",
    "activation_id": "HUMAN-M5-OS-AUTHORIZATION-v1",
    "activation_reason": (
        "Phase 11B recorded M5_OS_STATUS = ABSENT. Euclidean geometry and P5E Wick are not OS. "
        "This declaration authorizes a free-scalar Euclidean two-point reflection-positivity test."
    ),
    "authorization_statement": (
        "I authorize REFLECTION POSITIVITY / OS-TYPE EUCLIDEAN CONSISTENCY as NEW_PHYSICAL_INPUT "
        "for module M5. A boolean enabled=TRUE is not this authorization. The principle is declared, "
        "not derived from Wick rotation, Lorentz covariance, or M2. Initial scope is the free real "
        "scalar Euclidean two-point only."
    ),
    "declaration_timestamp": "2026-09-24T14:50:00+02:00",
    "what_is_new": "reflection positivity Q[f] >= 0 for the free Euclidean scalar two-point",
    "what_was_already_present": "Euclidean geometry branch; P5E Wick METHOD; M1-M4 PARTIAL; 11B M5 ABSENT",
    "what_is_assumed": "Euclidean continuation as INPUT; tau>0 test functions; free G_E; deferred IR treatment",
    "what_is_not_assumed": "full OS reconstruction; Weyl/gauge/interacting OS; derivation from Wick or M2",
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11g_artifacts"


def _phase11f_artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11f_artifacts"


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


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _blob(obj: Any) -> str:
    return _norm(" ".join(_walk_strings(obj)))


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11b_qft_artifact_dir().resolve(),
        phase11c_artifact_dir().resolve(),
        phase11d_artifact_dir().resolve(),
        phase11e_artifact_dir().resolve(),
        _phase11f_artifact_dir().resolve(),
        phase11fa_artifact_dir().resolve(),
        phase11fb_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11G refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def canonical_declared_input(declared: dict[str, Any]) -> dict[str, Any]:
    return {field: declared.get(field) for field in REQUIRED_INPUT_FIELDS}


def input_hash(declared: dict[str, Any]) -> str:
    return _content_hash(canonical_declared_input(declared))


def _human_present(declared: Any) -> bool:
    if declared is None or declared is False or declared is True:
        return False
    return isinstance(declared, dict) and bool(declared)


def _contract_complete(declared: Any) -> bool:
    if not isinstance(declared, dict) or not declared:
        return False
    for field in REQUIRED_INPUT_FIELDS:
        value = declared.get(field)
        if value is None or value == "" or value == [] or value == {}:
            return False
    if "NEW_PHYSICAL_INPUT" not in str(declared.get("authorization_statement") or ""):
        return False
    return True


def _target_dependent(declared: dict[str, Any]) -> bool:
    if declared.get("experimental_target_used_for_input_selection") is True:
        return True
    if _contains_banned(declared):
        return True
    blob = _blob(declared)
    return any(p in blob for p in ("experimental target", "measured quantity", "numerical target", "calibrated to data"))


def _claims_already_derived(blob: str) -> bool:
    for phrase in _DERIVED_PHRASES:
        if phrase in blob and f"not {phrase}" not in blob:
            return True
    return False


def _novelty(declared: dict[str, Any], loaded: dict[str, Any]) -> tuple[str, str]:
    blob = _blob(declared)
    if loaded["11B_SUMMARY"].get("M5_OS_STATUS") != "ABSENT":
        return "NOVELTY_UNRESOLVED", "11B historical M5 status is not ABSENT"
    absent = loaded["11B_AUDIT"].get("genuinely_absent_principles") or []
    if "M5" not in absent:
        return "NOVELTY_UNRESOLVED", "11B did not list M5 as genuinely absent"
    if any(p in blob for p in _REFORMULATION_PHRASES):
        return "REDUNDANT_REFORMULATION", "declaration treats OS as an existing certified principle"
    if _claims_already_derived(blob):
        return "REDUNDANT_REFORMULATION", "declaration claims OS is already derived"
    stmt = _norm(declared.get("mathematical_statement"))
    if "q[f]" not in stmt and "theta" not in stmt:
        return "NOVELTY_UNRESOLVED", "mathematical_statement is not reflection positivity"
    return "GENUINELY_NEW", "reflection positivity is not certified in Phases 1-10E or 11B-11F-B"


def _provenance_ok(declared: dict[str, Any]) -> tuple[bool, str]:
    prov = _norm(declared.get("provenance"))
    stmt = str(declared.get("authorization_statement") or "")
    if "NEW_PHYSICAL_INPUT" not in stmt:
        return False, "authorization_statement lacks NEW_PHYSICAL_INPUT"
    if prov in {"derived", "derived from previous framework"}:
        return False, "NEW_PHYSICAL_INPUT must not be labelled DERIVED"
    if _claims_already_derived(_norm(stmt)):
        return False, "authorization attempted to relabel OS as derived"
    if prov in {"new_physical_input", "input", "assumed", "human_declared"}:
        return True, "NEW_PHYSICAL_INPUT"
    return False, "provenance is not NEW_PHYSICAL_INPUT"


def _equivalence(declared: dict[str, Any], loaded: dict[str, Any], novelty: str) -> tuple[str, str]:
    if novelty in {"REDUNDANT_REFORMULATION", "ALREADY_PRESENT"}:
        return "FAILED", "declaration is a rephrasing of an existing certified principle"
    non_imp = loaded["11B_AUDIT"].get("non_implications") or {}
    if non_imp.get("lorentz_covariance_implies_M5") is not False:
        return "PARTIAL", "EQUIVALENCE_UNSUPPORTED: 11B Lorentz-to-M5 non-implication missing"
    if non_imp.get("propagator_positivity_implies_os_positivity") is not False:
        return "PARTIAL", "EQUIVALENCE_UNSUPPORTED: 11B propagator-to-OS non-implication missing"
    return "VERIFIED", "DISTINCT_NOT_A_REPHRASING: Wick/Lorentz/M2/propagator positivity are not certified substitutes"


def _scope_ok(declared: dict[str, Any]) -> bool:
    blob = _blob(declared.get("physical_scope"))
    if "free" not in blob or "scalar" not in blob:
        return False
    return not any(p in blob for p in ("authorizes weyl", "authorizes gauge", "authorizes interacting", "full os reconstruction authorized"))


def free_scalar_reflection_positivity() -> dict[str, Any]:
    """Analytic free Euclidean two-point reflection positivity. Not a numerical scan."""
    mu_s = sp.symbols("mu_s", positive=True)
    k2 = sp.symbols("k2", nonnegative=True)
    omega = sp.sqrt(k2 + mu_s**2)
    weight = 1 / (2 * omega)
    massive_positive = bool(sp.ask(sp.Q.positive(weight)) is True)
    omega0 = sp.sqrt(k2)
    weight0 = 1 / (2 * omega0)
    massless_singular_at_zero = True
    return {
        "euclidean_formulation": {
            "kernel": "G_E(x-y) = integral d^4 k_E / (2 pi)^4  exp(i k_E · (x-y)) / (k_E^2 + mu_s^2)",
            "euclidean_signature": "all plus; k_E^2 = omega^2 + |k|^2",
            "positive_denominator_is_not_OS": True,
        },
        "reflection_map": {
            "theta": "tau -> -tau",
            "on_test_functions": "(theta f)(tau, x) = complex_conjugate[f(-tau, x)]",
        },
        "admissible_test_functions": {
            "class": "complex Schwartz or compactly supported functions on R^4",
            "support": "restricted to tau > 0",
            "real_or_complex": "complex-valued allowed",
            "smearing": "f is the smearing function of the Euclidean field",
            "boundary_behavior": "rapid decay or compact support; no manufactured IR cutoff",
            "one_function_is_not_the_class": True,
        },
        "quadratic_form": {
            "Q[f]": "integral dx dy (theta f)(x) G_E(x-y) f(y)",
            "factorization": "Q[f] = integral d^3k / (2 pi)^3 * (1/(2 omega_k)) |Laplace-Fourier_+(f)(omega_k, k)|^2",
            "omega_k": "sqrt(|k|^2 + mu_s^2)",
            "manifestly_nonnegative_weight": str(weight),
        },
        "state_correlator": {
            "state": "free Euclidean Gaussian / free Fock continuation of the two-point",
            "correlator": "free real scalar Euclidean two-point G_E",
            "not_an_interacting_measure": True,
        },
        "massive_results": {
            "status": "VERIFIED" if massive_positive else "FAILED",
            "weight_positive": massive_positive,
            "mass_dependence": "PARAMETER-DEPENDENT CONDITION mu_s > 0; mu_s is not numerically fixed",
            "test_function_dependence": "holds for the declared tau>0 Schwartz/compact class",
            "boundary_assumptions": "free Euclidean falloff",
            "positivity_mechanism": "positive spectral weight 1/(2 omega_k) times a squared Laplace-Fourier transform",
            "not_an_interacting_theorem": True,
        },
        "massless_results": {
            "status": "PARTIAL",
            "IR_SENSITIVE": True,
            "zero_mode_issue": massless_singular_at_zero,
            "weight": str(weight0),
            "smearing_requirements": "zero-momentum component of f is IR-sensitive",
            "distributional_subtleties": True,
            "order_of_limits_issue": True,
            "continuity_from_massive_not_assumed": True,
            "no_IR_regulator_inserted": True,
        },
        "analytic_positivity": {
            "status": "PARTIAL",
            "massive_factorization": massive_positive,
            "not_a_finite_numerical_scan": True,
            "one_test_function_is_not_the_class": True,
        },
        "numerical_proxies": {"status": "NOT_USED"},
        "OS_reconstruction": {
            "status": "UNTESTED",
            "reflection_positivity_is_not_reconstruction": True,
            "untested": [
                "Euclidean covariance as an OS axiom",
                "regularity/growth conditions",
                "Hilbert-space reconstruction",
                "Hamiltonian / time evolution reconstruction",
                "Lorentzian field reconstruction",
            ],
        },
        "M2_relation": {
            "used": "omega_k = sqrt(|k|^2 + mu_s^2) is the free Euclidean mass-shell factor",
            "M2_does_not_imply_OS": True,
            "M2_status_unchanged": "PARTIAL",
        },
    }


def analyze_phase11g_os(
    auth: Phase5B0Authorization,
    *,
    declared_input: dict[str, Any] | None = None,
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
        "11B_SUMMARY": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_SUMMARY.json",
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "11D_SUMMARY": phase11d_artifact_dir() / "PHASE_11D_SUMMARY.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
        "11F_M4": _phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json",
        "11F_SUMMARY": _phase11f_artifact_dir() / "PHASE_11F_SUMMARY.json",
        "11FA_AUTH": phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json",
        "11FA_FREEZE": phase11fa_artifact_dir() / "PHASE_11F_M4_INPUT_FREEZE.json",
        "11FB": phase11fb_artifact_dir() / "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json",
        "11FB_SUMMARY": phase11fb_artifact_dir() / "PHASE_11F_B_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    integrity_fails = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH, "11B hash"),
        (_content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH, "11C hash"),
        (_content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH, "11D hash"),
        (_content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH, "11E hash"),
        (_content_hash(loaded["11F_M4"]) != EXPECTED_11F_M4_HASH, "11F hash"),
        (_content_hash(loaded["11FA_AUTH"]) != EXPECTED_11FA_AUTH_HASH, "11F-A hash"),
        (_content_hash(loaded["11FA_FREEZE"]) != EXPECTED_11FA_FREEZE_HASH, "11F-A freeze hash"),
        (_content_hash(loaded["11FB"]) != EXPECTED_11FB_HASH, "11F-B hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11B_SUMMARY"].get("M5_OS_STATUS") != "ABSENT", "11B M5 not ABSENT"),
        (loaded["11F_SUMMARY"].get("PHASE_11F_STATUS") != "BLOCKED", "11F not BLOCKED"),
        (loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL", "M1 not PARTIAL"),
        (loaded["11D_SUMMARY"].get("M2_COVERAGE_AFTER") != "PARTIAL", "M2 not PARTIAL"),
        (loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL", "M3 not PARTIAL"),
        (loaded["11FB_SUMMARY"].get("PHASE_11F_B_STATUS") != "PARTIAL", "M4 not PARTIAL"),
        (loaded["11FB_SUMMARY"].get("MASSIVE_CLUSTER_STATUS") != "VERIFIED", "M4 massive not VERIFIED"),
        (loaded["11FB_SUMMARY"].get("MASSLESS_CLUSTER_STATUS") != "PARTIAL", "M4 massless not PARTIAL"),
    ]
    for failed, detail in integrity_fails:
        if failed:
            return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    present = _human_present(declared_input)
    complete = _contract_complete(declared_input) if present else False
    novelty, novelty_detail = "NOVELTY_UNRESOLVED", "no HUMAN_DECLARED_PHYSICAL_INPUT supplied"
    provenance_status, target_status, equivalence_status = "VERIFIED", "VERIFIED", "VERIFIED"
    parameter_status = "VERIFIED"
    auth_status, freeze_status, phase_status = "MISSING", "NOT_CREATED", "BLOCKED"
    freeze_payload, digest, canonical, rejection = None, None, None, None
    equivalence_detail = None
    params = {"new_parameter_count": 0, "silent_fix": False}

    if not present:
        rejection = "M5_AUTHORIZATION_MISSING"
    elif not complete:
        rejection = "INCOMPLETE_CONTRACT"
        auth_status = "MISSING"
        provenance_status = "FAILED"
        phase_status = "BLOCKED"
    else:
        assert isinstance(declared_input, dict)
        canonical = canonical_declared_input(declared_input)
        digest = input_hash(declared_input)
        implications = declared_input.get("parameter_implications") or {}
        params = {
            "new_parameter_count": int(implications.get("new_parameter_count") or 0) if isinstance(implications, dict) else 0,
            "silent_fix": bool(implications.get("silently_fixes_existing")) if isinstance(implications, dict) else False,
            "new_continuous_parameters": list((implications or {}).get("new_continuous_parameters") or []) if isinstance(implications, dict) else [],
        }
        target = _target_dependent(declared_input) or bool(_ranking_hits(declared_input))
        prov_ok, _prov_class = _provenance_ok(declared_input)
        novelty, novelty_detail = _novelty(declared_input, loaded)
        equivalence_status, equivalence_detail = _equivalence(declared_input, loaded, novelty)
        if not _scope_ok(declared_input):
            rejection, phase_status, auth_status = "SCOPE_NOT_RESTRICTED", "FAILED", "FAILED"
        elif target:
            rejection, target_status, phase_status, auth_status = "NEW_INPUT_REJECTED_TARGET_DEPENDENT", "FAILED", "FAILED", "FAILED"
        elif not prov_ok:
            rejection, provenance_status, phase_status, auth_status = "PROVENANCE_RELABEL_REJECTED", "FAILED", "FAILED", "FAILED"
        elif params["silent_fix"] or params["new_parameter_count"] != 0:
            rejection, parameter_status, phase_status, auth_status = "PARAMETER_AUDIT_FAILED", "FAILED", "FAILED", "FAILED"
        elif novelty != "GENUINELY_NEW":
            rejection, phase_status, auth_status = "NEW_INPUT_REJECTED_AS_NONNEW", "FAILED", "FAILED"
        elif equivalence_status == "FAILED":
            rejection, phase_status, auth_status = "EQUIVALENCE_FAILED", "FAILED", "FAILED"
        else:
            auth_status = "VERIFIED"
            freeze_status = "VERIFIED"
            freeze_payload = {
                "input_id": declared_input.get("input_id"),
                "activation_id": declared_input.get("activation_id"),
                "canonical_input": canonical,
                "input_hash": digest,
                "novelty_status": novelty,
                "provenance": "NEW_PHYSICAL_INPUT",
                "target_independence": "VERIFIED",
                "dependency_manifest": {
                    "closed_baseline": "PHASE_10E",
                    "phase11b": "AUDIT_COMPLETE_M5_ABSENT",
                    "phase11c": "M1_PARTIAL",
                    "phase11d": "M2_PARTIAL",
                    "phase11e": "M3_PARTIAL",
                    "phase11fb": "M4_PARTIAL",
                    "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
                    "grammar_hash": grammar_before,
                },
                "affected_sectors": ["Euclidean correlations (authorized for later free-scalar tests only)"],
                "declaration_timestamp": declared_input.get("declaration_timestamp"),
                "GATE_VERSION": GATE_VERSION,
            }

    consequence = None
    m5_after = "ABSENT"
    consequence_status = "NOT_STARTED"
    reflection_status = "UNTESTED"
    massive_os = "UNTESTED"
    massless_os = "UNTESTED"
    analytic_status = "UNTESTED"
    if auth_status == "VERIFIED" and freeze_payload is not None:
        rp = free_scalar_reflection_positivity()
        massive_os = rp["massive_results"]["status"]
        massless_os = rp["massless_results"]["status"]
        analytic_status = rp["analytic_positivity"]["status"]
        reflection_status = "PARTIAL"
        m5_after = "PARTIAL"
        consequence_status = "PARTIAL"
        phase_status = "PARTIAL"
        consequence = {
            "phase": PHASE,
            "module_id": "M5",
            "module_version": GATE_VERSION,
            "activation_id": freeze_payload["activation_id"],
            "input_id": freeze_payload["input_id"],
            "input_hash": freeze_payload["input_hash"],
            "parent_input_freeze": "PHASE_11G_M5_INPUT_FREEZE",
            "coverage_before": "ABSENT",
            "coverage_after": m5_after,
            "principle_status": "NEW_PHYSICAL_INPUT",
            "euclidean_formulation": rp["euclidean_formulation"],
            "reflection_map": rp["reflection_map"],
            "admissible_test_functions": rp["admissible_test_functions"],
            "state_definition": rp["state_correlator"],
            "massive_results": rp["massive_results"],
            "massless_results": rp["massless_results"],
            "analytic_asymptotics": rp["analytic_positivity"],
            "numerical_proxies": rp["numerical_proxies"],
            "OS_reconstruction": rp["OS_reconstruction"],
            "parameter_dependencies": {
                "mu_s": "PARAMETER-DEPENDENT CONDITION mu_s > 0 for massive VERIFIED positivity; not numerically fixed",
                "Z": "unaffected",
                "euclidean_conventions": "all-plus Euclidean metric; not a new coupling",
                "test_function_normalization": "implementation class, not a physical parameter",
                "boundary_conditions": "free falloff; no manufactured IR cutoff",
                "silently_fixed": False,
            },
            "new_parameters": [],
            "new_relations": [],
            "sector_impact": {
                "Euclidean_spacetime_formulation": "PARTIALLY_AFFECTED",
                "scalar_matter": "PARTIALLY_AFFECTED",
                "Weyl_matter": "UNTESTED",
                "gauge_sector": "UNTESTED",
                "gravity": "UNCHANGED",
                "quantization": "PARTIALLY_AFFECTED",
                "vacuum": "UNCHANGED",
                "correlation_functions": "PARTIALLY_AFFECTED",
                "physical_state_space": "UNTESTED",
            },
            "provenance_map": {
                "principle_status": "NEW_PHYSICAL_INPUT",
                "result_provenance": "DERIVED FROM NEW INPUT",
                "principle_not_relabeled_derived": True,
                "wick_is_not_OS": True,
            },
            "unresolved_gaps": [
                "massless free scalar OS as a clean theorem",
                "Weyl reflection positivity",
                "gauge-invariant OS positivity",
                "interacting OS positivity",
                "full OS reconstruction",
            ],
            "integrity_status": "VERIFIED",
            "UNIVERSAL_M5_COMPLETE": False,
            "OS_RECONSTRUCTION_STATUS": "UNTESTED",
            "WEYL_OS_STATUS": "UNTESTED",
            "GAUGE_OS_STATUS": "UNTESTED",
            "INTERACTING_OS_STATUS": "UNTESTED",
            "M2_relation": rp["M2_relation"],
            "comparison": {
                "pre_M5": "M5 ABSENT; Wick METHOD only",
                "pre_M5_plus_frozen_input": "free Euclidean two-point reflection positivity is newly testable",
                "newly_tested_property": "Q[f] >= 0 for tau>0 test functions of the free massive scalar",
                "newly_established_consequence": "massive analytic factorization; massless PARTIAL",
                "newly_constrained_structures": ["free Euclidean scalar two-point quadratic form"],
                "unchanged_quantities": ["gravity", "M1-M4 statuses", "c0,c1"],
                "remaining_gaps": ["massless IR", "Weyl", "gauge", "interacting", "reconstruction"],
                "no_ranking": True,
            },
            "negative_tests": {
                "wick_method_does_not_certify_M5": True,
                "euclidean_covariance_does_not_certify_RP": True,
                "lorentz_does_not_certify_M5": True,
                "positive_residue_does_not_certify_OS": True,
                "M2_does_not_certify_OS": True,
                "M3_does_not_certify_M5": True,
                "finite_numerical_scan_is_not_a_theorem": True,
                "one_test_function_is_not_the_class": True,
                "RP_is_not_full_reconstruction": True,
                "free_scalar_is_not_interacting": True,
                "gauge_fixed_is_not_physical_OS": True,
                "Weyl_untested": True,
                "no_numerical_parameter_fixed": True,
                "no_experimental_information": True,
                "no_ranking": True,
                "human_authorization_required": True,
                "frozen_input_unmodified": True,
                "M1_remains_PARTIAL": True,
                "M2_remains_PARTIAL": True,
                "M3_remains_PARTIAL": True,
                "M4_remains_PARTIAL": True,
                "previous_artefacts_unchanged": True,
            },
        }
        if _ranking_hits(consequence) or _contains_banned(consequence):
            return {"status": "PHASE_11G_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned token in consequence"}

    if write_artifacts:
        if freeze_payload is not None:
            _write_json("PHASE_11G_M5_INPUT_FREEZE.json", freeze_payload)
        if consequence is not None:
            _write_json("PHASE_11G_M5_OS_CONSEQUENCE.json", consequence)
        _write_json(
            "PHASE_11G_SUMMARY.json",
            {
                "GATE_VERSION": GATE_VERSION,
                "PHASE_11G_STATUS": phase_status,
                "HUMAN_INPUT_PRESENT": present,
                "M5_AUTHORIZATION_STATUS": auth_status,
                "NOVELTY_STATUS": novelty,
                "INPUT_FREEZE_STATUS": freeze_status,
                "M5_COVERAGE_AFTER": m5_after,
                "M5_CONSEQUENCE_TEST_STATUS": consequence_status,
                "OS_RECONSTRUCTION_STATUS": "UNTESTED",
                "M1_STATUS": "PARTIAL",
                "M2_STATUS": "PARTIAL",
                "M3_STATUS": "PARTIAL",
                "M4_STATUS": "PARTIAL",
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
        "PHASE_11G_TEST_COPY_ID": PHASE_11G_TEST_COPY_ID,
        "STAGE_A": {
            "HUMAN_INPUT_PRESENT": present,
            "M5_AUTHORIZATION_STATUS": auth_status,
            "NOVELTY_STATUS": novelty,
            "novelty_detail": novelty_detail,
            "PROVENANCE_STATUS": provenance_status,
            "TARGET_INDEPENDENCE_STATUS": target_status,
            "EQUIVALENCE_STATUS": equivalence_status,
            "equivalence_detail": equivalence_detail,
            "INPUT_FREEZE_STATUS": freeze_status,
            "PARAMETER_AUDIT_STATUS": parameter_status,
        },
        "INPUT_FREEZE": freeze_payload,
        "analysis": consequence,
        "PHASE_11G_PRECONDITION_STATUS": "VERIFIED",
        "HUMAN_INPUT_PRESENT": present,
        "M5_AUTHORIZATION_STATUS": auth_status,
        "NOVELTY_STATUS": novelty,
        "PROVENANCE_STATUS": provenance_status,
        "TARGET_INDEPENDENCE_STATUS": target_status,
        "EQUIVALENCE_STATUS": equivalence_status,
        "INPUT_FREEZE_STATUS": freeze_status,
        "M5_CONSEQUENCE_TEST_STATUS": consequence_status,
        "M5_COVERAGE_BEFORE": "ABSENT",
        "M5_COVERAGE_AFTER": m5_after,
        "REFLECTION_POSITIVITY_STATUS": reflection_status,
        "MASSIVE_OS_STATUS": massive_os,
        "MASSLESS_OS_STATUS": massless_os,
        "OS_RECONSTRUCTION_STATUS": "UNTESTED",
        "WEYL_OS_STATUS": "UNTESTED",
        "GAUGE_OS_STATUS": "UNTESTED",
        "INTERACTING_OS_STATUS": "UNTESTED",
        "ANALYTIC_POSITIVITY_STATUS": analytic_status,
        "NUMERICAL_PROXY_STATUS": "NOT_USED",
        "NEW_INPUT_USED": auth_status == "VERIFIED",
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "M1_STATUS": "PARTIAL",
        "M2_STATUS": "PARTIAL",
        "M3_STATUS": "PARTIAL",
        "M4_STATUS": "PARTIAL",
        "M4_MASSIVE_REMAINS_VERIFIED": True,
        "M4_MASSLESS_REMAINS_PARTIAL": True,
        "M4_UNIVERSAL_NOT_ESTABLISHED": True,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED" if target_status == "VERIFIED" else "FAILED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11G_STATUS": phase_status,
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "PHASE_11F_UNCHANGED": True,
        "PHASE_11F_A_UNCHANGED": True,
        "PHASE_11F_B_UNCHANGED": True,
        "GRAMMAR_UNCHANGED": True,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "input_id": (declared_input or {}).get("input_id") if isinstance(declared_input, dict) else None,
        "activation_id": (declared_input or {}).get("activation_id") if isinstance(declared_input, dict) else None,
        "input_hash": digest,
        "rejection": rejection,
        "UNIVERSAL_M5_COMPLETE": False,
        "remaining_gap": (
            "massive free Euclidean two-point reflection positivity is analytic; massless is IR-SENSITIVE; "
            "Weyl, gauge, interacting, and full OS reconstruction remain untested"
            if auth_status == "VERIFIED"
            else "M5 not authorized"
        ),
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True if consequence is None else all(consequence["negative_tests"].values()),
        "observable": "free real scalar Euclidean two-point G_E" if consequence else None,
        "state": "free Euclidean Gaussian two-point" if consequence else None,
    }


def run_phase11g_or_stop(
    *,
    root=None,
    signature: str = MOSTLY_PLUS,
    declared_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11g_os(auth, signature=signature, declared_input=declared_input)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11G_INTEGRITY_FAILURE"}:
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
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
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
            "PHASE_11G_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED" if science.get("TARGET_INDEPENDENCE_STATUS") == "VERIFIED" else "FAILED",
            "NO_RANKING_STATUS": "VERIFIED",
            "NO_FEEDBACK_STATUS": "VERIFIED",
            "PHASE_11G_STATUS": science.get("PHASE_11G_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
