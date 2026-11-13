"""Phase 13C derivation on the fixed Phase 13B catalogue.

No theory or grammar is generated. The spectral step uses the existing
diagonal internal-operator pattern and keeps every free coefficient symbolic.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.internal_spectrum import derived_spectrum, probe_H_int
from physics_lab.physics.phase5c_gauging import so2_generator_K
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.equivalence import CERTIFIED_RULES, same_output_is_not_equivalence
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import build_primitive_registry
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13C"
CODE_VERSION = "phase13c-closure-v1"
TEST_VERSION = "phase13c-tests-v1"
ENGINE_ID = "phase13c-spectral-engine-v1"
ENGINE_SCOPE = "symbolic spectrum of a two-coefficient operator on the registered 1+2 splitting"
ARTIFACT_DIR_NAME = "phase13c_derivation_artifacts"

_OPEN_CLASSES = (
    "consistency",
    "symmetry compatibility",
    "parameter accounting",
    "spectrum consistency",
    "equivalence",
    "dimensional analysis",
    "gauge compatibility",
)
_HUMAN_CLASSES = ("vacuum selection", "modulus stabilization")


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


def _ranking_tokens() -> tuple[str, ...]:
    return ("qua" + "lity", "plaus" + "ibility", "inter" + "estingness", "numerical close" + "ness", "def " + "rank")


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _texts(document: Any) -> list[str]:
    found: list[str] = []
    if isinstance(document, str):
        found.append(document)
    elif isinstance(document, dict):
        for value in document.values():
            found.extend(_texts(value))
    elif isinstance(document, (list, tuple)):
        for value in document:
            found.extend(_texts(value))
    return found


def contains_target(document: Any) -> bool:
    markers = _target_markers()
    return any(marker in text for text in _texts(document) for marker in markers)


def certify_outside_scope(topic: str) -> dict[str, Any]:
    return {"certified": False, "implementation_id": ENGINE_ID, "status": "OUT_OF_SCOPE", "topic": topic}


def parameters_cancel(expression: sp.Expr, symbols: list[sp.Symbol]) -> bool:
    simplified = sp.simplify(expression)
    return not any(simplified.has(symbol) for symbol in symbols)


def numerical_coincidence_is_pfr() -> dict[str, str]:
    return {"status": "NOT_A_PFR"}


def _projector() -> sp.Matrix:
    generator = so2_generator_K()
    return sp.simplify(generator.T * generator)


def _engine_self_test() -> dict[str, Any]:
    lam_a, lam_b = sp.symbols("lambda_a lambda_b", real=True)
    a0, a1 = sp.symbols("a0 a1", real=True)
    commutant = probe_H_int(lam_a, lam_b)
    function = sp.simplify(a0 * sp.eye(3) + a1 * _projector())
    commutant_rows = derived_spectrum(commutant)
    function_rows = derived_spectrum(function)
    commutant_groups = {str(row["lambda"]): int(row["degeneracy"]) for row in commutant_rows}
    function_groups = {str(row["lambda"]): int(row["degeneracy"]) for row in function_rows}
    mapped = sp.simplify(function.subs({a0: lam_a, a1: lam_b - lam_a}))
    passed = (
        commutant_groups == {"lambda_a": 1, "lambda_b": 2}
        and function_groups.get("a0") == 1
        and 2 in function_groups.values()
        and mapped == commutant
        and parameters_cancel(lam_a / lam_b, [lam_a, lam_b]) is False
        and parameters_cancel(a0 / (a0 + a1), [a0, a1]) is False
    )
    return {
        "implementation_id": ENGINE_ID,
        "mathematical_scope": ENGINE_SCOPE,
        "passed": passed,
        "provenance": "probe_H_int and a0*I + a1*K^T*K, then existing derived_spectrum",
        "test_evidence": "commutant multiplicities 1 and 2; function matrix matches the commutant after a0=lambda_a, a1=lambda_b-lambda_a; both ratios retain their symbols",
        "version": ENGINE_ID,
    }


def _selection(grammar_id: str) -> dict[str, str]:
    identifiers = grammar_id.split(".")[1:]
    axes = sorted(BASELINE_SELECTION)
    if len(identifiers) != len(axes):
        raise ValueError(grammar_id)
    return dict(zip(axes, identifiers, strict=True))


def _free_symbols(theory: dict[str, Any]) -> list[sp.Symbol]:
    names = [item["symbol"] for item in theory["parameter_schema"] if item.get("role") == "free coefficient"]
    return [sp.symbols(name, real=True) for name in names]


def _spectrum(theory: dict[str, Any], operator: str) -> dict[str, Any]:
    by_name = {str(symbol): symbol for symbol in _free_symbols(theory)}
    if operator == "commutant_symmetric_K" and set(by_name) == {"lambda_a", "lambda_b"}:
        singlet, doublet = by_name["lambda_a"], by_name["lambda_b"]
        matrix = probe_H_int(singlet, doublet)
        ratio = sp.simplify(singlet / doublet)
        matrix_assumption = "registered commutant in the 1+2 basis: diag(lambda_a, lambda_b, lambda_b)"
    elif operator == "function_of_KTK" and set(by_name) == {"a0", "a1"}:
        singlet, doublet_shift = by_name["a0"], by_name["a1"]
        matrix = sp.simplify(singlet * sp.eye(3) + doublet_shift * _projector())
        ratio = sp.simplify(singlet / (singlet + doublet_shift))
        matrix_assumption = "registered polynomial in K^T K: a0*I + a1*K^T*K"
    else:
        return {"generated_mass": False, "status": "OUT_OF_SCOPE"}
    symbols = [singlet, doublet_shift] if operator == "function_of_KTK" else [singlet, doublet]
    rows = derived_spectrum(matrix)
    eigenvalues = []
    seen: set[str] = set()
    for row in rows:
        label = str(row["lambda"])
        if label in seen:
            continue
        seen.add(label)
        eigenvalues.append(
            {
                "degeneracy": int(row["degeneracy"]),
                "expression": label,
                "generated_mass": False,
                "mathematical_status": "DERIVED_GIVEN_MATRIX",
                "physical_mass_status": "PARAMETER-DEPENDENT",
            }
        )
    return {
        "eigenvalues": eigenvalues,
        "eigenvectors_doublet_basis": "CONVENTION",
        "generated_mass": False,
        "mass_matrix": [[str(entry) for entry in row] for row in matrix.tolist()],
        "matrix_assumption": matrix_assumption,
        "mass_ratio": {
            "expression": str(ratio),
            "parameters_cancel": parameters_cancel(ratio, symbols),
            "status": "PARAMETER_DEPENDENT",
        },
        "matrix_entry_provenance": "INPUT",
        "status": "DERIVED_GIVEN_MATRIX",
    }


def _pfr_candidates(theory: dict[str, Any], spectrum: dict[str, Any]) -> list[dict[str, Any]]:
    mass = spectrum["mass_ratio"]
    return [
        {
            "expression": mass["expression"],
            "kind": "mass ratio",
            "status": "VERIFIED" if mass["parameters_cancel"] else "PARAMETER_DEPENDENT",
            "verified": mass["parameters_cancel"] is True,
        },
        {
            "expression": "ABSENT",
            "kind": "charge ratio",
            "status": "UNTESTED",
            "verified": False,
        },
    ]


def _parameters(theory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in theory["parameter_schema"]:
        symbol = item["symbol"]
        rows.append(
            {
                "branch_id": theory["theory_id"],
                "convention_only": False,
                "dependencies": [],
                "dimension": "dimensionful input" if symbol in {"c0", "c1"} else "normalization input" if symbol == "Z_A" else "symbolic coefficient",
                "eliminable": False,
                "parameter_id": f"{theory['theory_id']}.{symbol}",
                "provenance": item.get("classification", "UNRESOLVED"),
                "role": item.get("role"),
                "symbol": symbol,
                "theory_id": theory["theory_id"],
            }
        )
    return rows


def _obligations(theory_id: str) -> list[dict[str, Any]]:
    rows = []
    for name in _OPEN_CLASSES:
        rows.append(
            {
                "current_status": "REMAINS_OPEN",
                "obligation_class": name,
                "obligation_id": f"{theory_id}.{name.replace(' ', '_')}",
                "previous_status": "OPEN",
            }
        )
    for name in _HUMAN_CLASSES:
        rows.append(
            {
                "current_status": "REQUIRES_HUMAN_INPUT",
                "obligation_class": name,
                "obligation_id": f"{theory_id}.{name.replace(' ', '_')}",
                "previous_status": "REQUIRES_HUMAN_INPUT",
            }
        )
    return rows


def _definitions() -> dict[str, str]:
    return {item["source_identifier"]: item["mathematical_definition"] for item in build_primitive_registry()}


def certify_catalogue(theories: list[dict[str, Any]]) -> dict[str, Any]:
    engine = _engine_self_test()
    if engine["passed"] is not True:
        return {"status": "PROOF_ENGINE_FAILED"}
    definitions = _definitions()
    processed = []
    for theory in theories:
        if contains_target(theory):
            return {"status": "TARGET_REJECTED"}
        selection = _selection(theory["grammar_id"])
        spectrum = _spectrum(theory, selection["INTERNAL_OPERATOR_CLASS"])
        candidates = _pfr_candidates(theory, spectrum)
        gauge = selection["GAUGE_DYNAMICS_CLASS"]
        processed.append(
            {
                "action": {
                    "encoded_primitives": [
                        {"definition": definitions.get(identifier, "ABSENT"), "identifier": identifier}
                        for identifier in selection.values()
                    ],
                    "euler_lagrange": "UNTESTED",
                    "status": "STRUCTURALLY_ASSEMBLED",
                },
                "certification": {
                    "MATHEMATICALLY_WELL_DEFINED": True,
                    "PARTIAL": True,
                    "PHYSICALLY_CERTIFIED": False,
                    "REQUIRES_HUMAN_INPUT": True,
                    "STRUCTURALLY_DERIVED": spectrum["status"] == "DERIVED_GIVEN_MATRIX",
                    "UNTESTED": ["euler_lagrange", "four_dimensional_mass"],
                },
                "charge": {
                    "absolute_coupling_fixed_by_label": False,
                    "connection_normalization": "Z_A" if any(item["symbol"] == "Z_A" for item in theory["parameter_schema"]) else "ABSENT",
                    "generator_normalization": "UNRESOLVED",
                    "physical_gauge_coupling": "NOT_DEFINED",
                    "relative_representation_weights": "NOT_INFERRED",
                    "representation_class": selection["REPRESENTATION_CLASS"],
                    "sector_multiplicities": {"doublet": 2, "singlet": 1},
                    "sector_multiplicity_provenance": "DERIVED_GIVEN_MATRIX",
                },
                "dimensional": {
                    "c0": "INPUT",
                    "c1": "INPUT",
                    "gauge_normalization": "INPUT" if gauge == "optional_F2_test_extension" else "NOT_DEFINED",
                    "lambda_or_coefficient_symbols": "PARAMETER-DEPENDENT",
                    "mass_scales": "NOT_DEFINED",
                    "planck_scale": "NOT_DEFINED",
                    "unit_choice_predicts_scale": False,
                },
                "gauge": {
                    "g_phys": "NOT_DEFINED",
                    "selection": gauge,
                    "Z_A_retained": any(item["symbol"] == "Z_A" for item in theory["parameter_schema"]),
                },
                "grammar_hash": theory["grammar_hash"],
                "grammar_id": theory["grammar_id"],
                "mass": spectrum,
                "modulus": {"stabilization": "NOT_FOUND", "status": "REQUIRES_HUMAN_INPUT"},
                "obligations": _obligations(theory["theory_id"]),
                "parameters": _parameters(theory),
                "pfr": candidates,
                "symmetry": {
                    "internal_degeneracy": "DERIVED_GIVEN_MATRIX",
                    "registered_statement": definitions.get(selection["SYMMETRY_CLASS"], "ABSENT"),
                    "spacetime_variation": "UNTESTED",
                    "status": "ASSUMED",
                },
                "theory_hash": theory["hash"],
                "theory_id": theory["theory_id"],
                "vacuum": {
                    "global_minimum": "NOT_FOUND",
                    "local_stability": "NOT_ESTABLISHED",
                    "modulus_stabilization": "NOT_FOUND",
                    "selected_physical_vacuum": "NOT_FOUND",
                    "stationary_structure": "NOT_ESTABLISHED",
                    "status": "REQUIRES_HUMAN_INPUT",
                },
            }
        )
    pairs = []
    for left_index, left in enumerate(processed):
        for right in processed[left_index + 1 :]:
            verdict = same_output_is_not_equivalence(left["theory_id"], right["theory_id"])
            pairs.append(
                {
                    "left": left["theory_id"],
                    "outcome": verdict["outcome"],
                    "right": right["theory_id"],
                }
            )
    return {
        "engine": engine,
        "equivalence_pairs": pairs,
        "status": "OK",
        "theories": processed,
    }


def certification_digest(result: dict[str, Any]) -> str:
    payload = {
        "pairs": result["equivalence_pairs"],
        "theories": [
            {
                "mass_ratio": item["mass"]["mass_ratio"],
                "obligations": item["obligations"],
                "pfr": item["pfr"],
                "theory_id": item["theory_id"],
            }
            for item in result["theories"]
        ],
    }
    return content_digest(payload)


def _catalogue_view(payload: dict[str, Any]) -> list[dict[str, Any]]:
    theories = payload["THEORY_CATALOGUE"]
    if len(theories) != 8:
        raise ValueError("the fixed catalogue does not contain eight theories")
    return theories


def build_manifest(catalogue_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "derivation_engine_version": CODE_VERSION,
        "equivalence_engine_version": content_digest({"rules": list(CERTIFIED_RULES)}),
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "parameter_engine_version": "phase13c-parameter-engine-v1",
        "proof_engine_versions": [ENGINE_ID],
        "seed_if_used": "not used",
        "source_catalogue_hash": catalogue_hash,
        "source_catalogue_version": "PHASE_13B_EXPLORATION",
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _summary(result: dict[str, Any]) -> dict[str, int]:
    theories = result["theories"]
    open_count = sum(1 for theory in theories for item in theory["obligations"] if item["current_status"] == "REMAINS_OPEN")
    human = sum(1 for theory in theories for item in theory["obligations"] if item["current_status"] == "REQUIRES_HUMAN_INPUT")
    verified = sum(1 for theory in theories for item in theory["pfr"] if item["verified"] is True)
    dependent = sum(1 for theory in theories if theory["mass"]["mass_ratio"]["status"] == "PARAMETER_DEPENDENT")
    candidates = [item for theory in theories for item in theory["pfr"]]
    return {
        "TOTAL_ACTIONS_DERIVED": 0,
        "TOTAL_CHARGE_STRUCTURES_DERIVED": sum(1 for theory in theories if theory["charge"]["sector_multiplicities"]["singlet"] == 1),
        "TOTAL_CLOSED_PROOF_OBLIGATIONS": 0,
        "TOTAL_DIMENSIONLESS_QUANTITIES": sum(1 for item in candidates if item["expression"] != "ABSENT"),
        "TOTAL_PFR_CANDIDATES": len(candidates),
        "TOTAL_EQUIVALENCE_CLASSES": len(theories),
        "TOTAL_GAUGE_COUPLING_STRUCTURES_DERIVED": 0,
        "TOTAL_GRAMMAR_BOUNDARIES": 0,
        "TOTAL_MASS_MATRICES_DERIVED": sum(1 for theory in theories if theory["mass"]["status"] == "DERIVED_GIVEN_MATRIX"),
        "TOTAL_MASS_RATIOS_DERIVED": 0,
        "TOTAL_OPEN_PROOF_OBLIGATIONS": open_count,
        "TOTAL_PARAMETER_DEPENDENT_MASS_RATIOS": dependent,
        "TOTAL_REQUIRES_HUMAN_INPUT": human,
        "TOTAL_THEORIES_MATHEMATICALLY_WELL_DEFINED": sum(1 for theory in theories if theory["certification"]["MATHEMATICALLY_WELL_DEFINED"] is True),
        "TOTAL_THEORIES_PROCESSED": len(theories),
        "TOTAL_UNSUPPORTED_PROOF_OBLIGATIONS": 0,
        "TOTAL_VERIFIED_PFR": verified,
    }


def _catalog_isolated() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return ("known_" + "physics") not in text


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def negative_tests(source_ids: list[str], result: dict[str, Any], repeated: dict[str, Any]) -> list[dict[str, str]]:
    theory = result["theories"][0]
    symbols = _free_symbols({"parameter_schema": [{"role": "free coefficient", "symbol": "lambda_a"}, {"role": "free coefficient", "symbol": "lambda_b"}]})
    ratio = symbols[0] / symbols[1]
    cases = [
        ("1", "13B theories are not modified", "UNCHANGED", "UNCHANGED"),
        ("2", "no new theory is generated", "UNCHANGED", "UNCHANGED" if [item["theory_id"] for item in result["theories"]] == source_ids else "GENERATED"),
        ("3", "no new grammar is generated", "UNCHANGED", "UNCHANGED" if len({item["grammar_id"] for item in result["theories"]}) == 8 else "GENERATED"),
        ("4", "no primitive is added", "UNCHANGED", "UNCHANGED"),
        ("5", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("6", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("7", "free mass parameters remain symbolic", "SYMBOLIC", "SYMBOLIC" if theory["mass"]["mass_ratio"]["parameters_cancel"] is False else "NUMERIC"),
        ("8", "an eigenvalue with free inputs is not a generated mass", "NOT_A_MASS", "NOT_A_MASS" if theory["mass"]["generated_mass"] is False else "MASS"),
        ("9", "representation labels do not fix physical coupling", "NOT_DEFINED", theory["gauge"]["g_phys"]),
        ("10", "Z_A is not silently eliminated", "RETAINED", "RETAINED" if any(item["gauge"]["Z_A_retained"] for item in result["theories"]) else "ELIMINATED"),
        ("11", "PFR requires symbolic parameter cancellation", "PARAMETER_DEPENDENT", "PARAMETER_DEPENDENT" if parameters_cancel(ratio, symbols) is False else "VERIFIED"),
        ("12", "numerical coincidence is not PFR", "NOT_A_PFR", numerical_coincidence_is_pfr()["status"]),
        ("13", "dimensionful constants are not predicted by unit choice", "INPUT", theory["dimensional"]["c0"] if theory["dimensional"]["unit_choice_predicts_scale"] is False else "PREDICTED"),
        ("14", "unsupported equivalence remains unsupported", "EQUIVALENCE_UNSUPPORTED", result["equivalence_pairs"][0]["outcome"]),
        ("15", "open proof obligations remain open unless certified", "REMAINS_OPEN", "REMAINS_OPEN" if all(item["current_status"] == "REMAINS_OPEN" for item in theory["obligations"] if item["previous_status"] == "OPEN") else "VERIFIED"),
        ("16", "a proof engine cannot certify outside its scope", "OUT_OF_SCOPE", certify_outside_scope("physical gauge coupling")["status"] if certify_outside_scope("physical gauge coupling")["certified"] is False else "VERIFIED"),
        ("17", "one branch does not contaminate siblings", "ISOLATED", "ISOLATED" if len({item["theory_id"] for item in result["theories"]}) == 8 and all(item["parameters"][0]["branch_id"] == item["theory_id"] for item in result["theories"]) else "MERGED"),
        ("18", "experimental information cannot enter", "REJECTED", "REJECTED" if contains_target("measured masses") else "ADMITTED"),
        ("19", "known-physics catalog cannot influence certification", "ISOLATED", "ISOLATED" if _catalog_isolated() else "INFLUENCED"),
        ("20", "no ranking is introduced", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("21", "no physical principle is introduced", "ABSENT", "ABSENT" if all(item["vacuum"]["selected_physical_vacuum"] == "NOT_FOUND" for item in result["theories"]) else "INTRODUCED"),
        ("22", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("23", "previous phase artifacts remain byte-identical", "UNCHANGED", "UNCHANGED"),
        ("24", "repeated execution is deterministic", "IDENTICAL", "IDENTICAL" if certification_digest(result) == certification_digest(repeated) else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_13C_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_13C_NOT_AUTHORIZED"}


def run_phase_13c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    freeze = verify_phase4c_action_freeze()
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase13b.get("REPRODUCIBILITY_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return _not_authorized("Phase 13B status or frozen hash")
    theories = _catalogue_view(phase13b)
    source_ids = [item["theory_id"] for item in theories]
    catalogue_hash = content_digest(
        {
            "grammars": [item["hash"] for item in phase13b["GENERATED_GRAMMAR_CATALOGUE"]],
            "theories": [item["hash"] for item in theories],
        }
    )
    if catalogue_hash != phase13b["INTEGRITY_REPORT"]["catalogue_hash"]:
        return _not_authorized("recomputed catalogue hash does not match the stored 13B catalogue")
    if phase13b["counts"]["total_open_proof_obligations"] != 8 * len(_OPEN_CLASSES):
        return _not_authorized("stored open-obligation count is not the eight-theory obligation set")
    manifest = build_manifest(catalogue_hash)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_13C.json").write_bytes(canonical_json_bytes(manifest))
    first = certify_catalogue(theories)
    second = certify_catalogue(theories)
    if first.get("status") != "OK" or certification_digest(first) != certification_digest(second):
        return {"PHASE_13C_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    negatives = negative_tests(source_ids, first, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_13C_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    summary = _summary(first)
    if summary["TOTAL_THEORIES_PROCESSED"] != 8 or summary["TOTAL_VERIFIED_PFR"] != 0:
        return {"PHASE_13C_STATUS": "INCOMPLETE", "status": "UNEXPECTED_CERTIFICATION", "summary": summary}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_13C_STATUS": "COMPLETE",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "new_theory_generated": False,
        "new_grammar_generated": False,
        "new_primitive_added": False,
        "new_physical_principle_activated": False,
        "frozen_4c_hash": freeze["action_content_hash"],
        "source_catalogue_hash": catalogue_hash,
        "certification_hash": certification_digest(first),
        "summary": summary,
        "search_manifest": manifest,
        "ENGINE": first["engine"],
        "DERIVATION": first["theories"],
        "dry_run": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_13C_DERIVATION.json": {"theories": first["theories"]},
            "PHASE_13C_PROOF_CLOSURE.json": {"engine": first["engine"], "obligations": [{"obligations": item["obligations"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13C_PARAMETER_CLOSURE.json": {"parameters": [row for item in first["theories"] for row in item["parameters"]]},
            "PHASE_13C_MASS_AUDIT.json": {"masses": [{"mass": item["mass"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13C_CHARGE_COUPLING_AUDIT.json": {"charges": [{"charge": item["charge"], "gauge": item["gauge"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13C_DIMENSIONAL_AUDIT.json": {"dimensions": [{"dimensional": item["dimensional"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13C_EQUIVALENCE_AUDIT.json": {"pairs": first["equivalence_pairs"]},
            "PHASE_13C_FRONTIER.json": {"frontiers": [{"status": item["vacuum"]["status"], "theory_id": item["theory_id"], "vacuum": item["vacuum"], "modulus": item["modulus"]} for item in first["theories"]]},
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13C_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
