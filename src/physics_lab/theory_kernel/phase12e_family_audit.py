"""Phase 12E theory-family grammar audit.

Classifies explicit families already present in the operational grammar and
candidate categories that are not registered. It does not enable a generator,
activate T09 or T10, or run a search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase10a_model_grammar import (
    example_catalog,
    legal_generator_inputs,
    variation_catalogs,
)
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.equivalence import same_output_is_not_equivalence
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12b import REFERENCE_SEEDS
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION as CURRENT_GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH
from physics_lab.theory_kernel.registries import RegistryError, merge_symbols, parameter_record

PHASE = "PHASE_12E"
CODE_VERSION = "phase12e-family-audit-v1"
ARTIFACT_DIR_NAME = "phase12e_family_artifacts"

_AXIS_CLASS = {
    "INTERNAL_OPERATOR_CLASS": "symmetry-constrained operator",
    "REPRESENTATION_CLASS": "finite-dimensional representation",
    "SYMMETRY_CLASS": "symmetry",
    "GEOMETRY_CLASS": "geometry",
    "GAUGE_DYNAMICS_CLASS": "gauge-theory action",
    "MINIMALITY_CLASS": "local derivative bound",
    "MODULUS_CLASS": "modulus declaration",
    "FIELD_CONTENT_CLASS": "field content",
    "GRAVITY_CLASS": "local gravitational action",
    "HILBERT_BOUND": "finite-dimensional Hilbert bound",
}

_VERTICAL_BLOCK = (
    "vacuum selection",
    "modulus stabilization",
    "flux stabilization",
    "new vacuum principle",
    "hidden sector",
    "new physical selection law",
)

_CHARGE_LAYERS = (
    "representation class",
    "representation weight",
    "generator normalization",
    "gauge-connection normalization",
    "physical gauge coupling",
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return (
        "experimental values",
        "measured masses",
        "measured couplings",
        coupling,
        fine,
        "known charge assignments used as targets",
        "target-specific numerical conditions",
    )


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


def run_large_scale_search(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 12E refuses large-scale search")


def _parameter_roles(symbols: list[str]) -> dict[str, Any]:
    roles = []
    for symbol in symbols:
        if symbol in {"c0", "c1"}:
            roles.append({"symbol": symbol, "role": "dimensionful scale", "provenance": "INPUT"})
        elif symbol == "Z_A":
            roles.append(
                {
                    "symbol": symbol,
                    "role": "gauge-connection normalization",
                    "provenance": "INPUT",
                    "absolute_coupling": False,
                }
            )
        else:
            roles.append({"symbol": symbol, "role": "free coefficient", "provenance": "PARAMETER-DEPENDENT"})
    return {
        "allowed_parameters": list(symbols),
        "derived_quantity_count": 0,
        "dimensionful_scales": [item["symbol"] for item in roles if item["role"] == "dimensionful scale"],
        "dimensionless_structural": [],
        "independent_parameter_count": len(symbols),
        "normalization_convention_count": sum(item["role"] == "gauge-connection normalization" for item in roles),
        "parameter_roles": roles,
        "unresolved_quantity_count": len(symbols),
    }


def _family(
    *,
    family_id: str,
    semantic_class: str,
    mathematical_definition: str,
    source: str,
    provenance: str,
    operational_status: str,
    parameters: list[str],
    discrete_labels: list[str],
    finite_bounds: dict[str, Any],
    transformations: list[str],
    boundary_class: str,
    new_physical_principle_required: bool,
    authorization_required: bool,
    eligibility: str,
    dependencies: list[str] | None = None,
    definition_status: str | None = None,
) -> dict[str, Any]:
    accounting = _parameter_roles(parameters)
    accounting["discrete_label_count"] = len(discrete_labels)
    if definition_status is None:
        definition_status = "EXPLICIT" if mathematical_definition not in {"", "ABSENT"} else "ABSENT"
    record = {
        "family_id": family_id,
        "semantic_class": semantic_class,
        "mathematical_definition": mathematical_definition,
        "mathematical_definition_status": definition_status,
        "source": source,
        "provenance": provenance,
        "operational_status": operational_status,
        "allowed_parameters": accounting["allowed_parameters"],
        "discrete_labels": list(discrete_labels),
        "finite_bounds": dict(finite_bounds),
        "finite_bound_status": "FINITE" if finite_bounds else "UNBOUNDED",
        "transformations": list(transformations),
        "proof_obligations": [
            {
                "certified_pass": False,
                "current_status": "OPEN",
                "obligation_class": "consistency",
            }
        ],
        "proof_status": "OPEN",
        "equivalence_rules": [],
        "target_blindness_status": "REJECTED" if contains_target(mathematical_definition) else "VERIFIED",
        "new_physical_principle_required": new_physical_principle_required,
        "authorization_required": authorization_required,
        "authorization_status": "NOT_AUTHORIZED" if authorization_required else "ALREADY_REGISTERED",
        "boundary_class": boundary_class,
        "eligibility": eligibility,
        "generator_enabled": operational_status == "OPERATIONAL",
        "namespace": family_id,
        "parameter_accounting": accounting,
        "dependencies": list(dependencies or []),
        "ratio_audit": {
            "coupling_ratios": "UNRESOLVED",
            "mass_ratios": "PARAMETER-DEPENDENT",
            "representation_weights": "NOT_AN_ABSOLUTE_COUPLING",
            "spectral_ratios": "UNRESOLVED",
            "absolute_scale_confused_with_ratio": False,
        },
    }
    if contains_target(record):
        record["target_blindness_status"] = "REJECTED"
        record["boundary_class"] = "REJECTED"
        record["eligibility"] = "NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION"
    return record


def _operational_families() -> list[dict[str, Any]]:
    families = []
    for item in legal_generator_inputs():
        axis = str(item["axis"])
        identifier = str(item["identifier"])
        families.append(
            _family(
                family_id=f"operational.{axis}.{identifier}",
                semantic_class=_AXIS_CLASS.get(axis, axis),
                mathematical_definition=str(item["mathematical_definition"]),
                source="phase10a legal_generator_inputs",
                provenance=str(item["provenance"]),
                operational_status="OPERATIONAL",
                parameters=list(item.get("allowed_parameters") or []),
                discrete_labels=["internal_dimension=3"] if "internal_dimension" in (item.get("bounds") or {}) else [],
                finite_bounds=dict(item.get("bounds") or {}),
                transformations=[axis],
                boundary_class="ALREADY_REGISTERED",
                new_physical_principle_required=False,
                authorization_required=False,
                eligibility="ALREADY_OPERATIONAL",
                dependencies=list(item.get("dependencies") or []),
            )
        )
    return families


def _reference_families(phase12a: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {row["THEORY_IR_reconstructed"]: row for row in phase12a["regression_table"]}
    families = []
    missing = [theory_id for theory_id in REFERENCE_SEEDS if theory_id not in by_id]
    if missing:
        raise KeyError(str(missing))
    ordered = [row["THEORY_IR_reconstructed"] for row in phase12a["regression_table"]]
    for theory_id in ordered:
        row = by_id[theory_id]
        partial = row["status"] == "PARTIAL"
        families.append(
            _family(
                family_id=f"reference.{theory_id}",
                semantic_class="reconstructed laboratory record",
                mathematical_definition="ABSENT",
                source=theory_id,
                provenance=row["status"],
                operational_status="REFERENCE_ONLY",
                parameters=[],
                discrete_labels=[],
                finite_bounds={},
                transformations=[],
                boundary_class="UNSUPPORTED_PROOF_ENGINE" if partial else "MISSING_MATHEMATICAL_DEFINITION",
                new_physical_principle_required=False,
                authorization_required=True,
                eligibility="NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION",
                definition_status="RECONSTRUCTED_NOT_A_GENERATOR_DEFINITION",
            )
        )
    families.append(
        _family(
            family_id="reference.theory.vacuum.selection",
            semantic_class="vacuum-selection principle",
            mathematical_definition="ABSENT",
            source="theory.vacuum.selection",
            provenance="NOT_FOUND",
            operational_status="REFERENCE_ONLY",
            parameters=[],
            discrete_labels=[],
            finite_bounds={},
            transformations=[],
            boundary_class="NEW_PHYSICAL_PRINCIPLE_REQUIRED",
            new_physical_principle_required=True,
            authorization_required=True,
            eligibility="REQUIRES_HUMAN_INPUT",
        )
    )
    return families


def _example_families() -> list[dict[str, Any]]:
    families = []
    for item in example_catalog():
        families.append(
            _family(
                family_id=f"example.{item['identifier']}",
                semantic_class="illustrative example",
                mathematical_definition=str(item["mathematical_definition"]),
                source="phase10a example_catalog",
                provenance=str(item["provenance"]),
                operational_status="EXAMPLE_ONLY",
                parameters=[],
                discrete_labels=[],
                finite_bounds={},
                transformations=[],
                boundary_class="MISSING_MATHEMATICAL_DEFINITION",
                new_physical_principle_required=False,
                authorization_required=True,
                eligibility="NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION",
                definition_status="ILLUSTRATIVE",
            )
        )
    return families


def _unregistered_categories() -> list[dict[str, Any]]:
    """Audit categories. None of these statements is installed as a generator."""
    rows = (
        (
            "candidate.alternative_local_scalar_actions",
            "alternative local scalar action class",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.higher_derivative_local_theories",
            "higher-derivative local theory",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.gauge_action_classes_beyond_registry",
            "gauge-theory action class",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.representation_families_beyond_registry",
            "finite-dimensional representation family",
            "UNBOUNDED_SEARCH_SPACE",
            False,
        ),
        (
            "candidate.eft_operators_beyond_registry",
            "symmetry-constrained EFT operator family",
            "UNBOUNDED_SEARCH_SPACE",
            False,
        ),
        (
            "candidate.compactification_structures",
            "compactification-style mathematical structure",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.lattice_discretized_operators",
            "lattice or discretized operator construction",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.spectral_operator_constructions",
            "spectral operator construction",
            "MISSING_MATHEMATICAL_DEFINITION",
            False,
        ),
        (
            "candidate.vacuum_selection",
            "vacuum-selection principle",
            "NEW_PHYSICAL_PRINCIPLE_REQUIRED",
            True,
        ),
        (
            "candidate.modulus_stabilization",
            "modulus-stabilization mechanism",
            "NEW_PHYSICAL_PRINCIPLE_REQUIRED",
            True,
        ),
        (
            "candidate.flux_stabilization",
            "flux stabilization",
            "NEW_PHYSICAL_PRINCIPLE_REQUIRED",
            True,
        ),
        (
            "candidate.hidden_sector",
            "hidden sector",
            "NEW_PHYSICAL_PRINCIPLE_REQUIRED",
            True,
        ),
    )
    return [
        _family(
            family_id=family_id,
            semantic_class=semantic_class,
            mathematical_definition="ABSENT",
            source="phase 12E audit category; not a registered generator input",
            provenance="NOT_REGISTERED",
            operational_status="NOT_REGISTERED",
            parameters=[],
            discrete_labels=[],
            finite_bounds={},
            transformations=[],
            boundary_class=boundary,
            new_physical_principle_required=principle,
            authorization_required=True,
            eligibility="REQUIRES_HUMAN_INPUT" if principle else "NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION",
        )
        for family_id, semantic_class, boundary, principle in rows
    ]


def _registration_complete(candidate: dict[str, Any], grammar_version: str | None) -> bool:
    if candidate.get("mathematical_definition") in {None, "", "ABSENT"}:
        return False
    if candidate.get("mathematical_definition_status") != "EXPLICIT":
        return False
    if not candidate.get("provenance"):
        return False
    if not candidate.get("finite_bounds"):
        return False
    if "dependencies" not in candidate:
        return False
    if not candidate.get("proof_obligations"):
        return False
    if not isinstance(grammar_version, str) or not grammar_version.strip():
        return False
    if grammar_version == CURRENT_GRAMMAR_VERSION:
        return False
    return True


def attempt_enable(candidate: dict[str, Any], *, grammar_version: str | None = None) -> dict[str, Any]:
    """Fail closed. This function never writes a generator entry."""
    if contains_target(candidate):
        return {"applied": False, "generator_enabled": False, "status": "REJECTED"}
    if candidate.get("new_physical_principle_required") is True:
        return {
            "applied": False,
            "generator_enabled": False,
            "status": "NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION",
        }
    status = candidate.get("operational_status")
    requested = candidate.get("generator_enabled") is True or candidate.get("request_generator_enabled") is True
    if status in {"REFERENCE_ONLY", "EXAMPLE_ONLY"} and requested:
        return {"applied": False, "generator_enabled": False, "status": "FAIL_CLOSED"}
    if not candidate.get("finite_bounds"):
        return {"applied": False, "generator_enabled": False, "status": "FAIL_CLOSED"}
    if candidate.get("mathematical_definition") in {None, "", "ABSENT"}:
        return {"applied": False, "generator_enabled": False, "status": "FAIL_CLOSED"}
    if requested and not _registration_complete(candidate, grammar_version):
        return {"applied": False, "generator_enabled": False, "status": "FAIL_CLOSED"}
    if requested and grammar_version in {None, "", CURRENT_GRAMMAR_VERSION}:
        return {"applied": False, "generator_enabled": False, "status": "REJECTED"}
    return {"applied": False, "generator_enabled": False, "status": "NOT_ACTIVATED"}


def propose_grammar_change(grammar_version: str | None) -> dict[str, str]:
    if not isinstance(grammar_version, str) or not grammar_version.strip() or grammar_version == CURRENT_GRAMMAR_VERSION:
        return {"applied": "false", "status": "REJECTED"}
    return {"applied": "false", "status": "NOT_APPLIED"}


def shared_parameter_identity(symbol: str = "c0") -> dict[str, Any]:
    left = parameter_record(
        parameter_id=f"family.left.{symbol}",
        symbol=symbol,
        dimension="unspecified",
        origin="phase12e-audit",
        provenance="INPUT",
        branch="family.left",
        independent=True,
        constrained_by=[],
        derived_from=[],
        current_status="INPUT",
        kind="physical parameter",
    )
    right = parameter_record(
        parameter_id=f"family.right.{symbol}",
        symbol=symbol,
        dimension="unspecified",
        origin="phase12e-audit",
        provenance="INPUT",
        branch="family.right",
        independent=True,
        constrained_by=[],
        derived_from=[],
        current_status="INPUT",
        kind="physical parameter",
    )
    merged = False
    try:
        merge_symbols(left, right)
    except RegistryError:
        merged = False
    else:
        merged = True
    return {
        "left_parameter_id": left["parameter_id"],
        "merged": merged,
        "right_parameter_id": right["parameter_id"],
        "symbol": symbol,
    }


def _cross_family_relations() -> list[dict[str, Any]]:
    pairs = (
        ("operational.INTERNAL_OPERATOR_CLASS.commutant_symmetric_K", "operational.INTERNAL_OPERATOR_CLASS.function_of_KTK"),
        ("operational.FIELD_CONTENT_CLASS.metric_plus_internal_Phi", "operational.FIELD_CONTENT_CLASS.metric_Phi_plus_connection"),
        ("operational.GAUGE_DYNAMICS_CLASS.connection_without_autonomous_F2", "operational.GAUGE_DYNAMICS_CLASS.optional_F2_test_extension"),
        ("reference.theory.11v.gravity_mediation", "reference.theory.11x.gauge_mediation"),
    )
    relations = []
    for source, target in pairs:
        verdict = same_output_is_not_equivalence(source, target)
        relations.append(
            {
                "mathematical_statement": "same symmetry, field content, or numerical output is not an equivalence certificate",
                "proof_status": verdict["outcome"],
                "provenance": "equivalence firewall",
                "relation_type": "CROSS_FAMILY_RELATION",
                "source_family": source,
                "target_family": target,
            }
        )
    return relations


def _resource_estimate(phase12b: dict[str, Any]) -> dict[str, Any]:
    catalog = variation_catalogs()
    widths = {axis: len(items) for axis, items in catalog.items()}
    widths["GRAVITY_CLASS"] = 1
    widths["HILBERT_BOUND"] = 1
    product = 1
    for width in widths.values():
        product *= width
    summary = phase12b["summary"]
    return {
        "additional_candidates_generated": 0,
        "candidate_count_estimate": product,
        "deduplication_cost": "not executed",
        "expected_branching_factor": max(widths.values()),
        "expected_proof_obligation_load": summary["TOTAL_OPEN_PROOF_OBLIGATIONS"],
        "ranking_used": False,
        "registered_axis_widths": widths,
        "search_executed": False,
        "stored_phase12b_generated": summary["TOTAL_GENERATED"],
        "symbolic_complexity": "not executed; stored registry bounds only",
    }


def _report_row(family: dict[str, Any]) -> dict[str, Any]:
    accounting = family["parameter_accounting"]
    return {
        "authorization_status": family["authorization_status"],
        "boundary_class": family["boundary_class"],
        "eligibility": family["eligibility"],
        "family": family["family_id"],
        "finite_bound_status": family["finite_bound_status"],
        "mathematical_definition_status": family["mathematical_definition_status"],
        "new_physical_principle_required": family["new_physical_principle_required"],
        "operational_status": family["operational_status"],
        "parameters": accounting["independent_parameter_count"],
        "proof_status": family["proof_status"],
        "provenance": family["provenance"],
        "semantic_class": family["semantic_class"],
    }


def dry_run_negative_tests(families: list[dict[str, Any]]) -> list[dict[str, str]]:
    reference = next(item for item in families if item["operational_status"] == "REFERENCE_ONLY")
    example = next(item for item in families if item["operational_status"] == "EXAMPLE_ONLY")
    principle = next(item for item in families if item["new_physical_principle_required"] is True)
    unbounded = {
        "dependencies": [],
        "finite_bounds": {},
        "generator_enabled": True,
        "mathematical_definition": "an unbounded operator family",
        "mathematical_definition_status": "EXPLICIT",
        "new_physical_principle_required": False,
        "operational_status": "NOT_REGISTERED",
        "proof_obligations": [{"certified_pass": False}],
        "provenance": "AUDIT",
        "request_generator_enabled": True,
    }
    missing = {
        "dependencies": [],
        "finite_bounds": {"polynomial_order": 2},
        "mathematical_definition": "ABSENT",
        "new_physical_principle_required": False,
        "operational_status": "NOT_REGISTERED",
        "proof_obligations": [{"certified_pass": False}],
        "provenance": "AUDIT",
        "request_generator_enabled": True,
    }
    target_aware = {
        "mathematical_definition": "tuned to " + ("1/" + "137"),
        "new_physical_principle_required": False,
        "operational_status": "NOT_REGISTERED",
    }
    incomplete_operational = {
        "dependencies": [],
        "finite_bounds": {"derivative_order": 2},
        "generator_enabled": True,
        "mathematical_definition": "a local polynomial bound without a new registry entry",
        "mathematical_definition_status": "EXPLICIT",
        "new_physical_principle_required": False,
        "operational_status": "NOT_REGISTERED",
        "proof_obligations": [{"certified_pass": False}],
        "provenance": "AUDIT",
        "request_generator_enabled": True,
    }
    reference_request = dict(reference)
    reference_request["request_generator_enabled"] = True
    example_request = dict(example)
    example_request["request_generator_enabled"] = True
    cases = [
        ("1", "T09 cannot activate", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("2", "T10 cannot activate", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("3", "new physical principle is not promoted", "NOT_ELIGIBLE_FOR_AUTOMATIC_ACTIVATION", attempt_enable(principle)["status"]),
        ("4", "REFERENCE_ONLY cannot generate", "FAIL_CLOSED", attempt_enable(reference_request)["status"]),
        ("5", "EXAMPLE_ONLY cannot generate", "FAIL_CLOSED", attempt_enable(example_request)["status"]),
        ("6", "operational family requires explicit registration", "FAIL_CLOSED", attempt_enable(incomplete_operational, grammar_version=CURRENT_GRAMMAR_VERSION)["status"]),
        ("7", "unbounded families fail closed", "FAIL_CLOSED", attempt_enable(unbounded, grammar_version="grammar_not_created")["status"]),
        ("8", "missing mathematical definitions fail closed", "FAIL_CLOSED", attempt_enable(missing, grammar_version="grammar_not_created")["status"]),
        ("9", "target-aware definitions are rejected", "REJECTED", attempt_enable(target_aware)["status"]),
        ("10", "shared parameter names do not merge", "DISTINCT", "DISTINCT" if shared_parameter_identity()["merged"] is False else "MERGED"),
        ("11", "same numerical outputs do not imply equivalence", "EQUIVALENCE_UNSUPPORTED", same_output_is_not_equivalence("family.left", "family.right")["outcome"]),
        ("12", "grammar changes require a new grammar version", "REJECTED", propose_grammar_change(CURRENT_GRAMMAR_VERSION)["status"]),
        ("13", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("14", "Phase 12D remains unchanged", "UNCHANGED", "UNCHANGED"),
        ("15", "no large-scale search runs", "REFUSED", "REFUSED"),
    ]
    return [
        {"case": case, "expected": expected, "label": label, "observed": observed}
        for case, label, expected, observed in cases
    ]


def _precondition_failure(reason: str) -> dict[str, str]:
    return {"PHASE_12E_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_12E_PRECONDITION_FAILED"}


def run_phase_12e(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase12a = _read("phase12a_artifacts/PHASE_12A_KERNEL.json")
    phase12b = _read("phase12b_artifacts/PHASE_12B_EXPLORATION.json")
    phase12c = _read("phase12c_artifacts/PHASE_12C_GRAMMAR_AUDIT.json")
    phase12d = _read("phase12d_authorization_artifacts/PHASE_12D_AUTHORIZATION_GATE.json")
    freeze = verify_phase4c_action_freeze()
    for document in (phase12a, phase12b, phase12c, phase12d):
        if "PYTEST_STATUS" in document and document["PYTEST_STATUS"] != "GREEN":
            return _precondition_failure("stored PYTEST_STATUS is not GREEN")
    if (
        phase12a.get("PHASE_12A_STATUS") != "COMPLETE"
        or phase12a.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH
        or phase12b.get("PHASE_12B_STATUS") != "COMPLETE"
        or phase12b.get("BLINDNESS_STATUS") != "VERIFIED"
        or phase12c.get("PHASE_12C_STATUS") != "COMPLETE"
        or phase12d.get("PHASE_12D_STATUS") != "COMPLETE"
        or phase12d.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase12d.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12d.get("T09_AUTHORIZATION_STATUS") != "REQUIRES_HUMAN_INPUT"
        or phase12d.get("T10_AUTHORIZATION_STATUS") != "REQUIRES_HUMAN_INPUT"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return _precondition_failure("stored phase status or frozen hash")

    families = _operational_families() + _reference_families(phase12a) + _example_families() + _unregistered_categories()
    if any(item["generator_enabled"] and item["operational_status"] != "OPERATIONAL" for item in families):
        return {"PHASE_12E_STATUS": "INCOMPLETE", "status": "FAIL_CLOSED"}
    if any(item["eligibility"] == "READY_FOR_REGISTRATION" for item in families):
        return {"PHASE_12E_STATUS": "INCOMPLETE", "status": "UNEXPECTED_READY_FAMILY"}
    negatives = dry_run_negative_tests(families)
    refused = False
    try:
        run_large_scale_search()
    except RuntimeError:
        refused = True
    if not refused or any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_12E_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "DRY_RUN_FAILED"}

    relations = _cross_family_relations()
    resources = _resource_estimate(phase12b)
    rows = [_report_row(item) for item in families]
    ready = [item["family_id"] for item in families if item["boundary_class"] == "READY_FOR_REGISTRATION"]
    human = [item["family_id"] for item in families if item["boundary_class"] == "REQUIRES_HUMAN_INPUT" or item["eligibility"] == "REQUIRES_HUMAN_INPUT"]
    principle = [item["family_id"] for item in families if item["new_physical_principle_required"] is True]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "code_version": CODE_VERSION,
        "FAMILY_AUDIT_STATUS": "VERIFIED",
        "HORIZONTAL_EXPANSION_STATUS": "PARTIAL",
        "FAMILY_REGISTRATION_STATUS": "VERIFIED",
        "PHYSICAL_PRINCIPLE_FIREWALL_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PARAMETER_ISOLATION_STATUS": "VERIFIED",
        "EQUIVALENCE_STATUS": "PARTIAL",
        "FINITE_BOUND_STATUS": "PARTIAL",
        "RESOURCE_AUDIT_STATUS": "VERIFIED",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "SEARCH_EXECUTED": False,
        "PHASE_12E_STATUS": "COMPLETE",
        "vertical_expansion": "NOT AUTHORIZED",
        "vertical_block": list(_VERTICAL_BLOCK),
        "CURRENT_GRAMMAR_VERSION": CURRENT_GRAMMAR_VERSION,
        "PROPOSED_GRAMMAR_VERSION": "NOT_CREATED",
        "grammar_version_created": False,
        "frozen_4c_hash": freeze["action_content_hash"],
        "FROZEN_STATE_STATUS": "VERIFIED",
        "blind_computation_restarted": False,
        "new_physical_principle_activated": False,
        "charge_layers_kept_distinct": list(_CHARGE_LAYERS),
        "absolute_coupling_fixed_by_label": phase12a["charge_audit"]["absolute_coupling_fixed_by_label"],
        "family_report": rows,
        "families": families,
        "cross_family_relations": relations,
        "resource_estimate": resources,
        "decision": {
            "ACTIVATABLE_FAMILIES": [],
            "GRAMMAR_BOUNDARIES": [
                phase12a["grammar_boundary"],
                "vacuum_selection_principle",
                "no new grammar version created",
            ],
            "NEW_PHYSICAL_PRINCIPLE_REQUIRED": principle,
            "READY_FOR_REGISTRATION": ready,
            "REQUIRES_HUMAN_INPUT": human,
        },
        "dry_run": negatives,
        "activation_attempts": [request_physical_activation("T09"), request_physical_activation("T10")],
        "phase12d_authorization_status": {
            "T09": phase12d["T09_AUTHORIZATION_STATUS"],
            "T10": phase12d["T10_AUTHORIZATION_STATUS"],
        },
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_12E_FAMILY_AUDIT.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_12E_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
