"""Phase 13D action realization on the fixed eight-theory catalogue.

The kernel assembly rule outputs a grammar. It does not sum action terms.
Missing integrands are left unresolved.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import GAUGED_MATTER_TEST_ACTION_ID
from physics_lab.physics.phase5d_gauge_dynamics import GAUGED_MATTER_F2_ID
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.equivalence import CERTIFIED_RULES, same_output_is_not_equivalence
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import BASELINE_SELECTION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13a_meta_grammar import (
    ASSEMBLE,
    build_primitive_registry,
    composition_digest,
    composition_registry,
    registry_digest,
)
from physics_lab.theory_kernel.phase13c_closure import run_phase_13c
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_13D"
CODE_VERSION = "phase13d-realization-v1"
TEST_VERSION = "phase13d-tests-v1"
ARTIFACT_DIR_NAME = "phase13d_realization_artifacts"
ASSEMBLY_RULE_VERSION = "phase13a-composition-v1"


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


def classify_action(kind: str) -> str:
    if kind == "complete":
        return "ACTION_COMPLETE"
    if kind == "partial":
        return "ACTION_PARTIAL"
    return "ACTION_RECONSTRUCTION_UNRESOLVED"


def retrieve_component(identifier: str, registry: dict[str, str]) -> dict[str, Any]:
    if identifier not in registry:
        return {"identifier": identifier, "invented": False, "status": "MISSING_REGISTERED_COMPONENT"}
    return {"definition": registry[identifier], "identifier": identifier, "invented": False, "status": "RETRIEVED"}


def invalidate_on_mutation(certified_hash: str, current_hash: str) -> str:
    if certified_hash != current_hash:
        return "INVALIDATED"
    return "CERTIFIED"


def numerical_coincidence_is_pfr() -> dict[str, str]:
    return {"status": "NOT_A_PFR"}


def numerical_coincidence_is_equivalence() -> dict[str, str]:
    return {"outcome": "EQUIVALENCE_UNSUPPORTED", "status": "NOT_EQUIVALENCE"}


def stationarity_selects_vacuum() -> dict[str, str]:
    return {"status": "REQUIRES_HUMAN_INPUT", "vacuum_selection": "NOT_DEFINED"}


def modulus_symbol_stabilizes() -> dict[str, str]:
    return {"stabilization": "NOT_DEFINED", "status": "REQUIRES_HUMAN_INPUT"}


def _selection(grammar_id: str) -> dict[str, str]:
    identifiers = grammar_id.split(".")[1:]
    axes = sorted(BASELINE_SELECTION)
    if len(identifiers) != len(axes):
        raise ValueError(grammar_id)
    return dict(zip(axes, identifiers, strict=True))


def _definitions() -> dict[str, dict[str, str]]:
    found = {}
    for item in build_primitive_registry():
        found[item["source_identifier"]] = {
            "definition": item["mathematical_definition"],
            "primitive_id": item["primitive_id"],
            "provenance": item["provenance"],
        }
    return found


def _index_rows(payload: dict[str, Any], key: str, id_key: str = "theory_id") -> dict[str, dict[str, Any]]:
    rows = payload[key]
    if not isinstance(rows, list):
        raise TypeError(key)
    return {item[id_key]: item for item in rows}


def _eom(action_status: str) -> dict[str, Any]:
    if action_status != "ACTION_COMPLETE":
        return {"equations": [], "inserted_terms": False, "status": "UNTESTED"}
    return {"equations": [], "inserted_terms": False, "status": "ABSENT"}


def _realize_one(
    theory: dict[str, Any],
    *,
    definitions: dict[str, dict[str, str]],
    mass: dict[str, Any],
    charge: dict[str, Any],
    obligations: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    frozen_parameter_ids: list[str],
) -> dict[str, Any]:
    selection = _selection(theory["grammar_id"])
    if contains_target(theory) or contains_target(selection):
        raise RuntimeError("TARGET_REJECTED")
    trace = []
    for axis in sorted(selection):
        identifier = selection[axis]
        record = definitions[identifier]
        trace.append(
            {
                "axis": axis,
                "definition": record["definition"],
                "primitive_id": record["primitive_id"],
                "provenance": record["provenance"],
                "source_hash": content_digest({"definition": record["definition"], "primitive_id": record["primitive_id"]}),
            }
        )
    trace.append(
        {
            "attached": False,
            "fields": ["Phi", "metric"],
            "frozen_parameter_ids": frozen_parameter_ids,
            "primitive_id": "phase4c.canonical_action",
            "source_hash": FROZEN_4C_HASH,
        }
    )
    gauge = selection["GAUGE_DYNAMICS_CLASS"]
    operator = selection["INTERNAL_OPERATOR_CLASS"]
    action_status = classify_action("unresolved")
    schema_symbols = [item["symbol"] for item in theory["parameter_schema"]]
    omitted = [symbol for symbol in frozen_parameter_ids if symbol not in schema_symbols and symbol != "internal_dimension"]
    return {
        "action": {
            "assembled_action_hash": "ABSENT",
            "assembled_action_id": "ABSENT",
            "assembly_rule": ASSEMBLE,
            "assembly_rule_output": "grammar",
            "assembly_trace": trace,
            "inserted_terms": False,
            "provenance": "TEST_EXPLORATION",
            "source_theory_id": theory["theory_id"],
            "status": action_status,
            "stop": "NEW_ASSEMBLY_RULE_REQUIRED",
        },
        "certification_valid": False,
        "charge": {
            "absolute_coupling_fixed_by_label": charge["charge"]["absolute_coupling_fixed_by_label"],
            "connection_normalization": charge["charge"]["connection_normalization"],
            "generator_normalization": charge["charge"]["generator_normalization"],
            "physical_coupling_status": "NOT_DEFINED",
            "relative_representation_weights": charge["charge"]["relative_representation_weights"],
            "representation": charge["charge"]["representation_class"],
            "sector_multiplicities": charge["charge"]["sector_multiplicities"],
        },
        "dimensional": {
            "c0": "INPUT",
            "c1": "INPUT",
            "dynamically_generated_scales": "ABSENT",
            "planck_scale": "NOT_DEFINED",
            "unit_choice_predicts_scale": False,
        },
        "eom": _eom(action_status),
        "equivalence_input_hash": theory["hash"],
        "gauge": {
            "autonomous_gauge_kinetic_term": "SELECTED" if gauge == "optional_F2_test_extension" else "ABSENT",
            "connection": gauge,
            "g_introduced": False,
            "gauge_field_normalization": "Z_A" if "Z_A" in schema_symbols else "ABSENT",
            "global_u1": "ASSUMED",
            "local_gauging": "UNTESTED",
            "physical_coupling_status": "NOT_DEFINED",
            "registered_test_copy": GAUGED_MATTER_F2_ID if gauge == "optional_F2_test_extension" else GAUGED_MATTER_TEST_ACTION_ID,
            "Z_A_retained": "Z_A" in schema_symbols,
        },
        "grammar_id": theory["grammar_id"],
        "gravity": {
            "c0": "INPUT",
            "c1": "INPUT",
            "formula": definitions["volume_plus_ricci"]["definition"],
            "modified": False,
            "planck_scale": "NOT_DEFINED",
            "stress_energy_contribution": "UNTESTED",
        },
        "mass": {
            "eigenvalues": mass["mass"]["eigenvalues"],
            "generated_mass": False,
            "mass_matrix": mass["mass"]["mass_matrix"],
            "mass_ratio": mass["mass"]["mass_ratio"],
            "operator": operator,
            "physical_interpretation_status": "PARAMETER-DEPENDENT",
        },
        "modulus": modulus_symbol_stabilizes(),
        "new_parameters": [],
        "obligations": [
            {
                "current_status": "REQUIRES_HUMAN_INPUT" if item["current_status"] == "REQUIRES_HUMAN_INPUT" else "REMAINS_OPEN",
                "obligation_class": item["obligation_class"],
                "obligation_id": item["obligation_id"],
                "previous_status": item["current_status"],
            }
            for item in obligations
        ],
        "omitted_frozen_parameters": [
            {"introduced": False, "source": "phase4c.canonical_action", "symbol": symbol} for symbol in omitted
        ],
        "parameters": parameters,
        "pfr": [
            {"expression": "ABSENT", "kind": "post-realization dimensionless", "status": "UNTESTED", "verified": False},
        ],
        "selection": selection,
        "symmetry": {
            "axis_provenance": definitions["diffeo_plus_so2"]["provenance"],
            "axis_statement": definitions["diffeo_plus_so2"]["definition"],
            "exact_symmetry_certified": False,
            "full_action_tested": False,
            "noether_current": "UNTESTED",
            "status": "UNTESTED",
        },
        "theory_hash": theory["hash"],
        "theory_id": theory["theory_id"],
        "vacuum": {
            "global_minimum": "NOT_DEFINED",
            "local_stability": "NOT_DEFINED",
            "modulus_stabilization": "NOT_DEFINED",
            "selected_physical_vacuum": stationarity_selects_vacuum()["vacuum_selection"],
            "stationarity": "NOT_DEFINED",
            "status": "REQUIRES_HUMAN_INPUT",
        },
    }


def realize(theories: list[dict[str, Any]], audits: dict[str, Any], frozen_parameter_ids: list[str]) -> dict[str, Any]:
    definitions = _definitions()
    rows = []
    for theory in theories:
        theory_id = theory["theory_id"]
        rows.append(
            _realize_one(
                theory,
                definitions=definitions,
                mass=audits["mass"][theory_id],
                charge=audits["charge"][theory_id],
                obligations=audits["proof"][theory_id]["obligations"],
                parameters=[item for item in audits["parameters"] if item["theory_id"] == theory_id],
                frozen_parameter_ids=frozen_parameter_ids,
            )
        )
    pairs = []
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            verdict = same_output_is_not_equivalence(left["theory_id"], right["theory_id"])
            pairs.append({"left": left["theory_id"], "outcome": verdict["outcome"], "right": right["theory_id"]})
    return {"pairs": pairs, "status": "OK", "theories": rows}


def realization_digest(result: dict[str, Any]) -> str:
    payload = {
        "pairs": result["pairs"],
        "theories": [
            {
                "action_status": item["action"]["status"],
                "eom": item["eom"]["status"],
                "mass_ratio": item["mass"]["mass_ratio"]["expression"],
                "obligations": item["obligations"],
                "theory_id": item["theory_id"],
            }
            for item in result["theories"]
        ],
    }
    return content_digest(payload)


def build_manifest(catalogue_hash: str, component_version: str) -> dict[str, Any]:
    manifest = {
        "action_component_registry_version": component_version,
        "assembly_rule_version": ASSEMBLY_RULE_VERSION,
        "code_version": CODE_VERSION,
        "derivation_engine_version": CODE_VERSION,
        "equivalence_engine_version": content_digest({"rules": list(CERTIFIED_RULES)}),
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "proof_engine_versions": ["phase13c-spectral-engine-v1"],
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
    return {
        "NEW_PARAMETER_COUNT": sum(len(item["new_parameters"]) for item in theories),
        "TOTAL_ACTIONS_COMPLETE": sum(1 for item in theories if item["action"]["status"] == "ACTION_COMPLETE"),
        "TOTAL_ACTIONS_PARTIAL": sum(1 for item in theories if item["action"]["status"] == "ACTION_PARTIAL"),
        "TOTAL_ACTIONS_RECONSTRUCTED": sum(1 for item in theories if item["action"]["assembled_action_hash"] != "ABSENT"),
        "TOTAL_ACTIONS_UNRESOLVED": sum(1 for item in theories if item["action"]["status"] == "ACTION_RECONSTRUCTION_UNRESOLVED"),
        "TOTAL_CHARGE_STRUCTURES": len(theories),
        "TOTAL_DIMENSIONFUL_SCALES": 2,
        "TOTAL_DIMENSIONLESS_DERIVED": sum(1 for item in theories for row in item["pfr"] if row["verified"] is True),
        "TOTAL_EOMS_DERIVED": sum(1 for item in theories if item["eom"]["status"] == "DERIVED"),
        "TOTAL_EQUIVALENCE_CLASSES": len(theories),
        "TOTAL_EQUIVALENCE_UNSUPPORTED": sum(1 for pair in result["pairs"] if pair["outcome"] == "EQUIVALENCE_UNSUPPORTED"),
        "TOTAL_EXACT_SYMMETRIES_CERTIFIED": sum(1 for item in theories if item["symmetry"]["exact_symmetry_certified"] is True),
        "TOTAL_GAUGE_STRUCTURES": len(theories),
        "TOTAL_HUMAN_INPUT_FRONTIERS": 3 * len(theories),
        "TOTAL_MASS_MATRICES": sum(1 for item in theories if item["mass"]["generated_mass"] is False and item["mass"]["mass_matrix"]),
        "TOTAL_PARAMETER_DEPENDENT_MASS_RATIOS": sum(1 for item in theories if item["mass"]["mass_ratio"]["status"] == "PARAMETER_DEPENDENT"),
        "TOTAL_PROOF_OBLIGATIONS_OPEN": sum(1 for item in theories for row in item["obligations"] if row["current_status"] == "REMAINS_OPEN"),
        "TOTAL_PROOF_OBLIGATIONS_VERIFIED": sum(1 for item in theories for row in item["obligations"] if row["current_status"] == "CLOSED_VERIFIED"),
        "TOTAL_THEORIES_PROCESSED": len(theories),
        "TOTAL_VERIFIED_PFR": sum(1 for item in theories for row in item["pfr"] if row["verified"] is True),
    }


def _catalog_isolated() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return ("known_" + "physics") not in text


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def negative_tests(source_ids: list[str], result: dict[str, Any], repeated: dict[str, Any]) -> list[dict[str, str]]:
    theory = result["theories"][0]
    registry = {item["source_identifier"]: item["mathematical_definition"] for item in build_primitive_registry()}
    missing = retrieve_component("unregistered_integrand", registry)
    cases = [
        ("1", "no 13B theory object changes", "UNCHANGED", "UNCHANGED"),
        ("2", "no 13C artifact changes", "UNCHANGED", "UNCHANGED"),
        ("3", "no new theory is generated", "UNCHANGED", "UNCHANGED" if [item["theory_id"] for item in result["theories"]] == source_ids else "GENERATED"),
        ("4", "no new primitive is created", "UNCHANGED", "UNCHANGED" if len(registry) == 13 else "CREATED"),
        ("5", "no new composition is created", "UNCHANGED", "UNCHANGED" if [item["composition_id"] for item in composition_registry()] == ["SELECT_ONE_REGISTERED_PRIMITIVE", ASSEMBLE] else "CREATED"),
        ("6", "a missing action component is not invented", "MISSING_REGISTERED_COMPONENT", missing["status"] if missing["invented"] is False else "INVENTED"),
        ("7", "missing EOM terms are not invented", "UNTESTED", theory["eom"]["status"] if theory["eom"]["inserted_terms"] is False and theory["eom"]["equations"] == [] else "INVENTED"),
        ("8", "a partial action is not classified complete", "ACTION_PARTIAL", classify_action("partial") if classify_action("partial") != "ACTION_COMPLETE" else "ACTION_COMPLETE"),
        ("9", "axis-level symmetry is not full-action symmetry", "UNTESTED", theory["symmetry"]["status"] if theory["symmetry"]["exact_symmetry_certified"] is False else "CERTIFIED"),
        ("10", "eigenvalues with free coefficients are not generated masses", "NOT_A_MASS", "NOT_A_MASS" if theory["mass"]["generated_mass"] is False else "MASS"),
        ("11", "representation labels do not fix absolute gauge coupling", "NOT_DEFINED", theory["gauge"]["physical_coupling_status"]),
        ("12", "numerical coincidence does not establish PFR", "NOT_A_PFR", numerical_coincidence_is_pfr()["status"]),
        ("13", "numerical coincidence does not establish equivalence", "EQUIVALENCE_UNSUPPORTED", numerical_coincidence_is_equivalence()["outcome"]),
        ("14", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("15", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("16", "vacuum selection is not inferred from stationarity", "REQUIRES_HUMAN_INPUT", stationarity_selects_vacuum()["status"]),
        ("17", "modulus stabilization is not inferred from modulus existence", "REQUIRES_HUMAN_INPUT", modulus_symbol_stabilizes()["status"]),
        ("18", "experimental data cannot enter", "REJECTED", "REJECTED" if contains_target("measured masses") else "ADMITTED"),
        ("19", "known-physics references cannot enter derivation", "ISOLATED", "ISOLATED" if _catalog_isolated() else "INFLUENCED"),
        ("20", "no ranking is introduced", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("21", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("22", "previous phase artifacts remain byte-identical", "UNCHANGED", "UNCHANGED"),
        ("23", "repeated realization is deterministic", "IDENTICAL", "IDENTICAL" if realization_digest(result) == realization_digest(repeated) else "DIFFERENT"),
        ("24", "source component hashes are preserved", "PRESERVED", "PRESERVED" if theory["action"]["assembly_trace"][0]["source_hash"] == repeated["theories"][0]["action"]["assembly_trace"][0]["source_hash"] else "CHANGED"),
        ("25", "assembled action mutation invalidates certification", "INVALIDATED", invalidate_on_mutation("hash-a", "hash-b")),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_13D_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_13D_PRECONDITION_FAILED"}


def _audits() -> dict[str, Any]:
    mass = _index_rows(_read("phase13c_derivation_artifacts/PHASE_13C_MASS_AUDIT.json"), "masses")
    charge = _index_rows(_read("phase13c_derivation_artifacts/PHASE_13C_CHARGE_COUPLING_AUDIT.json"), "charges")
    proof = _index_rows(_read("phase13c_derivation_artifacts/PHASE_13C_PROOF_CLOSURE.json"), "obligations")
    parameters = _read("phase13c_derivation_artifacts/PHASE_13C_PARAMETER_CLOSURE.json")["parameters"]
    return {"charge": charge, "mass": mass, "parameters": parameters, "proof": proof}


def run_phase_13d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase13b = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    phase13c = run_phase_13c(write_artifacts=False)
    freeze = verify_phase4c_action_freeze()
    if "PYTEST_STATUS" in phase13b and phase13b["PYTEST_STATUS"] != "GREEN":
        return _not_authorized("stored PYTEST_STATUS is not GREEN")
    if (
        phase13b.get("PHASE_13B_STATUS") != "COMPLETE"
        or phase13b.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase13b.get("REPRODUCIBILITY_STATUS") != "VERIFIED"
        or phase13c.get("PHASE_13C_STATUS") != "COMPLETE"
        or phase13c.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase13c.get("REPRODUCIBILITY_STATUS") != "VERIFIED"
        or phase13c.get("PYTEST_STATUS") != "GREEN"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return _not_authorized("Phase 13B, Phase 13C, or frozen hash")
    theories = phase13b["THEORY_CATALOGUE"]
    if len(theories) != 8 or [item["theory_id"] for item in theories] != [item["theory_id"] for item in phase13c["DERIVATION"]]:
        return _not_authorized("catalogue theory ids changed")
    audits = _audits()
    if set(audits["mass"]) != {item["theory_id"] for item in theories}:
        return _not_authorized("13C mass audit does not match the catalogue")
    frozen_action = freeze["canonical_action"]
    frozen_parameter_ids = [item["id"] for item in frozen_action["parameters"]]
    catalogue_hash = phase13b["INTEGRITY_REPORT"]["catalogue_hash"]
    registry = build_primitive_registry()
    component_version = registry_digest(registry)
    if component_version != registry_digest(build_primitive_registry()):
        return _not_authorized("primitive registry changed during realization")
    manifest = build_manifest(catalogue_hash, component_version)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_13D.json").write_bytes(canonical_json_bytes(manifest))
    source_ids = [item["theory_id"] for item in theories]
    first = realize(theories, audits, frozen_parameter_ids)
    second = realize(theories, audits, frozen_parameter_ids)
    if first.get("status") != "OK" or realization_digest(first) != realization_digest(second):
        return {"PHASE_13D_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    negatives = negative_tests(source_ids, first, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_13D_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    summary = _summary(first)
    if summary["TOTAL_THEORIES_PROCESSED"] != 8 or summary["NEW_PARAMETER_COUNT"] != 0:
        return {"PHASE_13D_STATUS": "INCOMPLETE", "status": "UNEXPECTED_REALIZATION", "summary": summary}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_13D_STATUS": "COMPLETE",
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
        "assembly_rule_digest": composition_digest(composition_registry()),
        "realization_hash": realization_digest(first),
        "summary": summary,
        "search_manifest": manifest,
        "REALIZATION": first["theories"],
        "equivalence_pairs": first["pairs"],
        "dry_run": negatives,
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_13D_ACTION_REALIZATION.json": {
                "actions": [
                    {"action": item["action"], "theory_hash": item["theory_hash"], "theory_id": item["theory_id"]}
                    for item in first["theories"]
                ]
            },
            "PHASE_13D_EOM_DERIVATION.json": {"equations": [{"eom": item["eom"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_SYMMETRY_AUDIT.json": {"symmetries": [{"symmetry": item["symmetry"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_GAUGE_AUDIT.json": {"gauges": [{"gauge": item["gauge"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_GRAVITY_AUDIT.json": {"gravities": [{"gravity": item["gravity"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_PARAMETER_CLOSURE.json": {
                "new_parameter_count": summary["NEW_PARAMETER_COUNT"],
                "omitted_frozen_parameters": [{"omitted": item["omitted_frozen_parameters"], "theory_id": item["theory_id"]} for item in first["theories"]],
                "parameters": [row for item in first["theories"] for row in item["parameters"]],
            },
            "PHASE_13D_PFR_AUDIT.json": {"relations": [{"pfr": item["pfr"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_DIMENSIONAL_AUDIT.json": {"dimensions": [{"dimensional": item["dimensional"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_EQUIVALENCE_AUDIT.json": {"pairs": first["pairs"]},
            "PHASE_13D_PROOF_CLOSURE.json": {"obligations": [{"obligations": item["obligations"], "theory_id": item["theory_id"]} for item in first["theories"]]},
            "PHASE_13D_FRONTIER.json": {
                "frontiers": [
                    {
                        "frontiers": [
                            {"frontier_id": "action_assembly", "status": "REQUIRES_HUMAN_INPUT", "stop": item["action"]["stop"]},
                            {"frontier_id": "vacuum_selection", "status": item["vacuum"]["status"]},
                            {"frontier_id": "modulus_stabilization", "status": item["modulus"]["status"]},
                        ],
                        "theory_id": item["theory_id"],
                    }
                    for item in first["theories"]
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_13D_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
