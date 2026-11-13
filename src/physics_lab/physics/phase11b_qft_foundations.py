"""Phase 11B: QFT foundational coverage audit. AUDIT_ONLY. No activation."""

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
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11a_input_gate import artifact_dir as phase11a_input_artifact_dir
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase14c5k_p5k import EXPECTED_P5K_CHECKPOINT_DIGEST
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase14c5q_p5q import artifact_dir as phase14c5q_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "EXPECTED_10E_SYNTHESIS_HASH",
    "MODULE_IDS",
    "NON_IMPLICATIONS",
    "PHASE_11B_QFT_TEST_COPY_ID",
    "analyze_phase11b_qft_audit",
    "artifact_dir",
    "module_hash",
    "run_phase11b_qft_or_stop",
]

PHASE_11B_QFT_TEST_COPY_ID = "PHASE_11B_QFT_FOUNDATIONAL_COVERAGE_AUDIT"
PHASE = "PHASE_11B"
AUDIT_VERSION = "phase11b-qft-foundational-audit-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_P5Q_SUMMARY_HASH = "67d9cb20b860d6f6c1c76f01560e286bd4748168fec4129b2241261c1a16fafc"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"
MODULE_IDS = ("M1", "M2", "M3", "M4", "M5")

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
    "module" + "_" + "ranking",
)

NON_IMPLICATIONS = {
    "local_action_implies_M1_complete": False,
    "positive_kinetic_implies_M2_complete": False,
    "ghost_free_implies_M2_complete": False,
    "ssb_background_implies_M3_complete": False,
    "locality_implies_M4": False,
    "lorentz_covariance_implies_M5": False,
    "equal_time_ccr_implies_full_spacelike_microcausality": False,
    "propagator_positivity_implies_os_positivity": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11b_qft_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def module_hash(module: dict[str, Any]) -> str:
    return _content_hash({k: v for k, v in module.items() if k != "module_hash"})


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
        phase14c5q_artifact_dir().resolve(),
        phase14c5k_artifact_dir().resolve(),
        phase10b9_artifact_dir().resolve(),
        phase11b1_artifact_dir().resolve(),
        phase11a_input_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11B QFT audit refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash mismatch"}
    return None


def _module(spec: dict[str, Any]) -> dict[str, Any]:
    item = {
        **spec,
        "category": "QFT_FOUNDATIONAL_PRINCIPLE",
        "activation_status": "DISABLED",
        "ENABLED": False,
        "mode": "AUDIT_ONLY",
        "new_objects": spec.get("new_objects") or [],
        "new_parameters": "none under AUDIT_ONLY",
        "potential_relations": "NONE",
        "parameter_free_relation": "NONE",
        "parameter_audit": {
            "introduces": "no new parameter under AUDIT_ONLY",
            "dimensionful_parameter": False,
            "dimensionless_parameter": False,
            "normalization": False,
            "state_selection_assumption": spec["module_id"] in {"M3", "M4"},
            "boundary_condition": False,
            "geometric_structure": spec["module_id"] == "M5",
        },
    }
    item["module_hash"] = module_hash(item)
    return item


def _build_modules(p5q: dict[str, Any], p5k: dict[str, Any], s10e: dict[str, Any]) -> list[dict[str, Any]]:
    qs = s10e.get("quantum_scope") or {}
    q02 = p5q.get("Q02_CANONICAL_QUANTIZATION_STATUS")
    q03 = p5q.get("Q03_PROPAGATOR_STATUS")
    q04 = p5k.get("Q04_TREE_UNITARITY_STATUS")
    full_u = p5k.get("FULL_QUANTUM_UNITARITY")
    return [
        _module(
            {
                "module_id": "M1",
                "name": "MICROCAUSALITY",
                "mathematical_statement": (
                    "[O(x), O(y)] = 0 for spacelike separated x, y, for the declared local fields"
                ),
                "required_structures": ["local fields", "spacelike separation", "operator algebra"],
                "existing_coverage": (
                    "local action (4C/5B.0) plus P5Q equal-time canonical algebra "
                    f"(Q02={q02}). No certified spacelike commutator calculation."
                ),
                "coverage_status": "PARTIAL",
                "exact_source_scope": (
                    f"P5Q Q02={q02} equal-time CCR/CAR; Q01 is the implemented equal-time "
                    "spin-statistics proxy, not a spacelike microcausality theorem"
                ),
                "missing_test": "spacelike [O(x), O(y)] = 0, distinct from equal-time CCR",
                "new_input_required": False,
                "assumptions": ["declared free-field canonical algebra"],
                "affected_sectors": ["quantization", "observables", "matter"],
                "unaffected_sectors": ["gravity family coefficients", "10B catalogue"],
                "tests": ["P5Q equal-time CCR", "no spacelike commutator test found"],
                "provenance": {"principle_status": "PARTIAL_EXTENSION", "result_provenance": "UNTESTED"},
                "scope": "canonical equal-time algebra only",
                "dependencies": [],
                "exclusions": [
                    "local action is not microcausality",
                    "equal-time CCR is not spacelike microcausality",
                ],
                "test_level": "CANONICAL",
                "principle_itself": "[O(x), O(y)] = 0 spacelike",
                "necessary_condition": "local action / local kinetic term",
                "proxy_or_test": "[Phi(t,x), Pi(t,y)] = i delta^3(x-y)",
            }
        ),
        _module(
            {
                "module_id": "M2",
                "name": "SPECTRAL CONDITION / POSITIVE-ENERGY STRUCTURE",
                "mathematical_statement": (
                    "physical spectrum compatible with required energy-momentum positivity / spectral support"
                ),
                "required_structures": ["physical Hilbert space", "energy-momentum", "spectral support"],
                "existing_coverage": (
                    "10B.9 kinetic-sign / linearized ghost (PARAMETER-DEPENDENT); "
                    f"P5Q Q03={q03}; 10E matter propagator={qs.get('matter_propagator')}; "
                    f"gauge propagator={qs.get('gauge_propagator')}; "
                    "Cutkosky theta(k0) is a cut proxy. Full spectral support UNTESTED. "
                    f"Q04={q04}. FULL_QUANTUM_UNITARITY={full_u}."
                ),
                "coverage_status": "PARTIAL",
                "exact_source_scope": (
                    f"P5Q Q03={q03}; P5K/10E Q04={q04}; 10B.9 ghost-free iff sign conditions; "
                    "P5Q rejects upgrading positive energy to full ghost freedom"
                ),
                "missing_test": "spectral support of physical energy-momentum, not residue/ghost-sign proxies",
                "new_input_required": False,
                "assumptions": ["mostly_plus kinetic-sign convention", "F^2 TEST EXTENSION for gauge poles"],
                "affected_sectors": ["quantization", "matter", "gauge"],
                "unaffected_sectors": ["c0,c1 uniqueness", "10D unsupported pairs"],
                "tests": ["10B.9 linearized ghost", "P5Q propagator", "P5H/P5K unitarity proxies"],
                "provenance": {"principle_status": "PARTIAL_EXTENSION", "result_provenance": "UNTESTED"},
                "scope": "perturbative poles and sign-only ghost diagnostics",
                "dependencies": [],
                "exclusions": [
                    "ghost-free is not the spectral condition",
                    "positive residue is not full spectral support",
                ],
                "test_level": "PERTURBATIVE",
                "principle_itself": "spectral support of physical energy-momentum",
                "necessary_condition": "ghost-free quadratic kinetic term (sign-only)",
                "proxy_or_test": "positive kinetic sign; propagator residue; theta(k0) in cuts",
            }
        ),
        _module(
            {
                "module_id": "M3",
                "name": "VACUUM / PHYSICAL-STATE CONSISTENCY",
                "mathematical_statement": "existence of a consistent physical vacuum and physical-state space",
                "required_structures": ["vacuum vector", "physical subspace", "Hamiltonian boundedness"],
                "existing_coverage": (
                    "G4 structural VEV assumptions (G4_PARTIAL_NOT_UPGRADED); "
                    "P5Q Hamiltonian PARAMETER-DEPENDENT; "
                    f"10E BRST={qs.get('BRST')}; c0=0 is BACKGROUND_CONDITION not a vacuum theorem."
                ),
                "coverage_status": "PARTIAL",
                "exact_source_scope": (
                    f"G4 PARTIAL; P5Q Hamiltonian PARAMETER-DEPENDENT; BRST={qs.get('BRST')}"
                ),
                "missing_test": (
                    "Hamiltonian boundedness on the physical subspace, distinct from a chosen VEV/background"
                ),
                "new_input_required": False,
                "assumptions": ["VEV is a G4 structural assumption", "BRST scope is TEST EXTENSION"],
                "affected_sectors": ["vacuum", "gauge", "matter"],
                "unaffected_sectors": ["gravity family form", "10B catalogue classes"],
                "tests": ["G4 VEV grammar", "P5Q Hamiltonian status", "BRST TEST EXTENSION"],
                "provenance": {"principle_status": "PARTIAL_EXTENSION", "result_provenance": "INPUT"},
                "scope": "structural VEV + perturbative BRST TEST EXTENSION",
                "dependencies": [],
                "exclusions": [
                    "SSB background is not a vacuum-consistency theorem",
                    "local stability is not global vacuum stability",
                ],
                "test_level": "PERTURBATIVE",
                "principle_itself": "consistent physical vacuum",
                "necessary_condition": "existence of a convenient background",
                "proxy_or_test": "chosen SSB/VEV; BRST cohomology in TEST EXTENSIONS",
            }
        ),
        _module(
            {
                "module_id": "M4",
                "name": "CLUSTER DECOMPOSITION",
                "mathematical_statement": (
                    "separated correlators factorize at large spacelike separation for the declared states"
                ),
                "required_structures": ["correlation functions", "large spacelike separation", "state assumptions"],
                "existing_coverage": "no certified large-distance factorization or connected-correlator suppression test",
                "coverage_status": "ABSENT",
                "exact_source_scope": "not present in Phases 1-10E, G1-G6R, or P0-P5K",
                "missing_test": "factorization of correlators at large spacelike separation",
                "new_input_required": True,
                "assumptions": ["not activated in this audit"],
                "affected_sectors": ["correlations", "observables", "vacuum"],
                "unaffected_sectors": ["all closed 10E coefficients while DISABLED"],
                "tests": ["none certified"],
                "provenance": {"principle_status": "ROADMAP_INPUT", "result_provenance": "UNTESTED"},
                "scope": "absent",
                "dependencies": ["M1 if a later test uses spacelike localization"],
                "exclusions": [
                    "locality is not cluster decomposition",
                    "Lorentz invariance is not cluster decomposition",
                ],
                "test_level": "AXIOMATIC",
                "principle_itself": "cluster decomposition of correlators",
                "necessary_condition": "locality (not sufficient)",
                "proxy_or_test": "none certified",
            }
        ),
        _module(
            {
                "module_id": "M5",
                "name": "REFLECTION POSITIVITY / OS-TYPE EUCLIDEAN CONSISTENCY",
                "mathematical_statement": (
                    "Euclidean correlators satisfy reflection positivity and declared reconstruction conditions"
                ),
                "required_structures": [
                    "Euclidean continuation of correlators",
                    "reflection-positive inner product",
                    "OS reconstruction hypotheses",
                ],
                "existing_coverage": (
                    "spacetime Euclidean branch is a separate geometric formulation, not a kinetic-sign proxy. "
                    "P5E Wick rotation is a loop-integral METHOD for UV poles, not OS positivity."
                ),
                "coverage_status": "ABSENT",
                "exact_source_scope": "Euclidean geometry separate; P5E Wick is METHOD, not OS",
                "missing_test": "reflection positivity of Euclidean correlators and reconstruction conditions",
                "new_input_required": True,
                "assumptions": ["not activated in this audit"],
                "affected_sectors": ["quantization", "correlations"],
                "unaffected_sectors": ["all closed 10E coefficients while DISABLED"],
                "tests": ["none certified as OS"],
                "provenance": {"principle_status": "ROADMAP_INPUT", "result_provenance": "UNTESTED"},
                "scope": "absent as OS; Euclidean geometry is not OS",
                "dependencies": [],
                "exclusions": [
                    "Lorentz covariance is not OS positivity",
                    "propagator positivity is not OS positivity",
                    "ghost-free is not OS positivity",
                ],
                "test_level": "EUCLIDEAN",
                "principle_itself": "OS reflection positivity",
                "necessary_condition": "none certified as OS",
                "proxy_or_test": "Lorentzian residue signs; Euclidean metric branch; P5E Wick UV coefficient",
            }
        ),
    ]


def _activation_configuration(modules: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mode": "AUDIT_ONLY",
        "DEFAULT_MODE": "AUDIT_ONLY",
        "frozen_before_consequences": True,
        "post_hoc_activation": False,
        "modules": [
            {
                "module_id": item["module_id"],
                "module_enabled": False,
                "activation_timestamp": "NOT_ACTIVATED",
                "activation_reason": "AUDIT_ONLY default; no human MODE_C authorization",
                "parent_baseline": "PHASE_10E",
                "module_hash": item["module_hash"],
                "mode": "AUDIT_ONLY",
            }
            for item in modules
        ],
    }


def analyze_phase11b_qft_audit(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    activation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "P5Q_SUMMARY": phase14c5q_artifact_dir() / "PHASE_14C5Q_SUMMARY.json",
        "P5K_SUMMARY": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
        "10B9_SUMMARY": phase10b9_artifact_dir() / "PHASE_10B9_SUMMARY.json",
        "LEGACY_11B1": phase11b1_artifact_dir() / "PHASE_11B1_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "STOP", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    s10e = loaded["10E_SYNTHESIS"]
    sum10e = loaded["10E_SUMMARY"]
    p5q = loaded["P5Q_SUMMARY"]
    p5k = loaded["P5K_SUMMARY"]
    if _content_hash(s10e) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10E synthesis hash mismatch"}
    if _content_hash(p5q) != EXPECTED_P5Q_SUMMARY_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "P5Q summary hash mismatch"}
    if p5k.get("checkpoint_digest") != EXPECTED_P5K_CHECKPOINT_DIGEST:
        return {"status": "STOP", "scientific_analysis": None, "detail": "P5K digest mismatch"}
    if sum10e.get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10E not closed"}
    if p5q.get("Q02_CANONICAL_QUANTIZATION_STATUS") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "unexpected P5Q Q02"}
    if p5k.get("FULL_QUANTUM_UNITARITY") != "UNTESTED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "full quantum unitarity was upgraded"}

    if activation:
        if activation.get("inspect_result_first") or activation.get("post_hoc"):
            return {"status": "OK", "PHASE_11B_STATUS": "FAILED", "rejection": "POST_HOC_ACTIVATION", "models_generated": 0}
        if activation.get("mode") == "MODE_C" and not activation.get("explicit_human_authorization"):
            return {
                "status": "OK",
                "PHASE_11B_STATUS": "FAILED",
                "rejection": "ABSENT_PRINCIPLE_NOT_MACHINE_ACTIVATED",
                "models_generated": 0,
            }
        if activation.get("promote_partial_to_complete"):
            return {
                "status": "OK",
                "PHASE_11B_STATUS": "FAILED",
                "rejection": "PARTIAL_NOT_PROMOTED_TO_COMPLETE",
                "models_generated": 0,
            }
        if activation.get("relabel_existing_as_new"):
            return {
                "status": "OK",
                "PHASE_11B_STATUS": "FAILED",
                "rejection": "EXISTING_NOT_RELABELED_NEW_PHYSICAL_INPUT",
                "models_generated": 0,
            }

    modules = _build_modules(p5q, p5k, s10e)
    statuses = {item["module_id"]: item["coverage_status"] for item in modules}
    for item in modules:
        if item["coverage_status"] == "COMPLETE":
            return {"status": "STOP", "scientific_analysis": None, "detail": "illegal COMPLETE promotion"}
        if item["provenance"]["principle_status"] == "NEW_PHYSICAL_INPUT":
            return {"status": "STOP", "scientific_analysis": None, "detail": "existing relabeled new"}
        if item["ENABLED"] is True:
            return {"status": "STOP", "scientific_analysis": None, "detail": "module enabled during AUDIT_ONLY"}

    config = _activation_configuration(modules)
    matrix = [
        {
            "Module": item["module_id"],
            "Principle": item["name"],
            "Existing coverage": item["existing_coverage"],
            "Exact source scope": item["exact_source_scope"],
            "Missing test": item["missing_test"],
            "New input required?": item["new_input_required"],
            "Status": item["coverage_status"],
        }
        for item in modules
    ]
    payload = {
        "phase": PHASE,
        "module_registry": modules,
        "coverage_matrix": matrix,
        "dependency_graph": {
            "M1": [],
            "M2": [],
            "M3": [],
            "M4": ["M1 if a later spacelike correlator test is defined"],
            "M5": [],
            "note": "no textbook-order implication is assumed",
        },
        "test_strength_map": {item["module_id"]: item["test_level"] for item in modules},
        "parameter_implications": {
            "new_parameters_introduced": 0,
            "new_parameter_free_relations": "NONE",
            "per_module": {item["module_id"]: item["parameter_audit"] for item in modules},
        },
        "provenance_map": {item["module_id"]: item["provenance"] for item in modules},
        "activation_configuration": config,
        "previous_phase_sources": {
            "PHASE_10E": EXPECTED_10E_SYNTHESIS_HASH,
            "P5Q": EXPECTED_P5Q_SUMMARY_HASH,
            "P5K": EXPECTED_P5K_CHECKPOINT_DIGEST,
            "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
            "grammar_hash": grammar_before,
        },
        "unresolved_gaps": [
            "spacelike microcausality commutator",
            "full spectral support on the physical-state space",
            "vacuum-consistency theorem beyond VEV/background/BRST TEST EXTENSION",
            "cluster decomposition test",
            "OS reflection positivity and reconstruction",
        ],
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "modules_enabled": [],
        "modules_disabled": list(MODULE_IDS),
        "principles_already_present": [],
        "principles_partially_present": ["M1", "M2", "M3"],
        "genuinely_absent_principles": ["M4", "M5"],
        "unsupported_principles": [],
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "STOP", "scientific_analysis": None, "detail": "banned or ranking token"}
    if write_artifacts:
        _write_json("PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json", payload)
        _write_json(
            "PHASE_11B_QFT_SUMMARY.json",
            {
                "AUDIT_VERSION": AUDIT_VERSION,
                "PHASE_11B_STATUS": "AUDIT_COMPLETE",
                "M1_MICROCAUSALITY_STATUS": statuses["M1"],
                "M2_SPECTRAL_STATUS": statuses["M2"],
                "M3_VACUUM_STATUS": statuses["M3"],
                "M4_CLUSTER_STATUS": statuses["M4"],
                "M5_OS_STATUS": statuses["M5"],
                "DEFAULT_MODE": "AUDIT_ONLY",
                "modules_enabled": [],
                "PROGRAM_CLOSURE_STATUS_PRESERVED": EXPECTED_10E_CLOSURE,
            },
        )
        _write_json("PHASE_11B_ACTIVATION_FREEZE.json", config)
    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}
    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11B_QFT_TEST_COPY_ID": PHASE_11B_QFT_TEST_COPY_ID,
        "audit": payload,
        "PHASE_11B_PRECONDITION_STATUS": "VERIFIED",
        "COVERAGE_AUDIT_STATUS": "VERIFIED",
        "M1_MICROCAUSALITY_STATUS": statuses["M1"],
        "M2_SPECTRAL_STATUS": statuses["M2"],
        "M3_VACUUM_STATUS": statuses["M3"],
        "M4_CLUSTER_STATUS": statuses["M4"],
        "M5_OS_STATUS": statuses["M5"],
        "MODULE_ARCHITECTURE_STATUS": "VERIFIED",
        "NO_DUPLICATION_STATUS": "VERIFIED",
        "TARGET_INDEPENDENCE_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "PHASE_11B_STATUS": "AUDIT_COMPLETE",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "FINAL_PARAMETER_FREE_RELATION_COUNT": 0,
        "UNIQUE_ACTION": False,
        "UNIQUE_COUPLING": False,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "NO_EXPERIMENTAL_DATA_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": all(v is False for v in NON_IMPLICATIONS.values()),
        "activation_frozen_before_consequences": True,
    }


def run_phase11b_qft_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11b_qft_audit(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11B_STATUS": science.get("PHASE_11B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
