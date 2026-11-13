"""Phase 11AJ.1: containment audit for universal modulus-gauge weights.

T07 did not reduce the parameter count. This module asks whether a
universal f_a(T) or a fixed modular weight is already derived.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase5d_gauge_dynamics import phase5d_scope_summary
from physics_lab.physics.phase9_internal_gap import _bianchi_coverage
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import artifact_dir as phase11ae4_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import run_phase_11AE_4_synthesis
from physics_lab.physics.phase11ai2_ft_identification import (
    F_T_IdentificationAuthorization,
    run_phase_11AI_2_execution,
)
from physics_lab.physics.phase11ai2_ft_identification import artifact_dir as phase11ai2_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import modulus_mediation_identities

__all__ = [
    "CLOSURE_TARGET",
    "T07_STATUS",
    "run_containment_audit_T08",
]

PHASE = "PHASE_11AJ.1"
T07_STATUS = "FAILED_NO_PARAMETER_REDUCTION"
CLOSURE_TARGET = "UNIVERSAL_WEIGHTS_DERIVED"
_WEIGHT_IDS = ("f_a", "f1", "f2", "n_i", "Z_A")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11aj_artifacts"


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _fixes_weight_to_a_number(text: str) -> bool:
    """A differential equation that still contains the symbol does not fix it."""
    if text.count("=") != 1:
        return False
    if any(token in text for token in ("nabla", "D_mu", "partial", "G_mu")):
        return False
    left, right = [part.strip() for part in text.split("=")]
    for token in ("Z_A", "f_a", "n_i", "f1"):
        if token in left and _is_plain_number(right):
            return True
        if token in right and _is_plain_number(left):
            return True
    return False


def _is_plain_number(text: str) -> bool:
    try:
        value = sp.sympify(text)
    except (sp.SympifyError, TypeError, ValueError):
        return False
    return bool(value.is_number)


def _weights_are_universal() -> dict[str, Any]:
    modulus = sp.symbols("T")
    first = sp.Function("f1")
    second = sp.Function("f2")
    weight = sp.symbols("n_i")
    normalization = sp.symbols("Z_A")
    return {
        "f1_equals_f2": bool(first(modulus).equals(second(modulus))),
        "modular_weight_is_number": bool(weight.is_number),
        "Z_A_is_number": bool(normalization.is_number),
    }


def _scan(vacuum: dict[str, Any]) -> list[dict[str, Any]]:
    scope = phase5d_scope_summary()
    identities = modulus_mediation_identities()
    algebraic = _weights_are_universal()
    out_of_scope = scope["out_of_scope"]
    gauge_probe = _probe(
        "gauge_phase_5d",
        algebraic["f1_equals_f2"] or algebraic["Z_A_is_number"],
        {
            "tests_only": scope["tests_only"],
            "numerical_Z_A_is_out_of_scope": "forcing any numerical value for Z_A" in out_of_scope,
            "beta_functions_out_of_scope": "beta functions" in out_of_scope,
            "f1_equals_f2": algebraic["f1_equals_f2"],
            "f_a_not_assumed_universal": identities["f_a_not_assumed_universal"],
            "Z_A_is_number": algebraic["Z_A_is_number"],
        },
    )

    document = phase4c_action_document()
    parameters = {row["id"]: row for row in document["parameters"]}
    present_weights = [name for name in _WEIGHT_IDS if name in parameters]
    lam_a = parameters["lam_a"]
    lam_b = parameters["lam_b"]
    surviving = vacuum["synthesis"]["surviving_class"]
    class_text = json.dumps(surviving)
    class_fixes = any(token in class_text for token in ("f_a", "n_i", "Z_A"))
    structural_weights = [
        name
        for name in present_weights
        if parameters[name].get("symbolic") is False and parameters[name].get("value_is_structural") is True
    ]
    spectrum_probe = _probe(
        "internal_spectrum_and_z2_moduli",
        algebraic["modular_weight_is_number"] or bool(structural_weights) or class_fixes,
        {
            "weight_parameters_in_freeze": present_weights,
            "no_T_in_freeze": identities["no_T_in_freeze"],
            "lam_a_provenance": lam_a["provenance"],
            "lam_b_provenance": lam_b["provenance"],
            "lam_a_symbolic": lam_a["symbolic"],
            "modular_weights_not_fixed": identities["modular_weights_not_fixed"],
            "modular_weight_is_number": algebraic["modular_weight_is_number"],
            "symmetry": vacuum["synthesis"]["symmetry"],
            "surviving_class": surviving,
            "class_fixes_gauge_weight": class_fixes,
        },
    )

    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    derived_rows = [row for row in rows if str(row.get("provenance", "")).startswith("DERIVED")]
    named = [
        str(row.get("EOM", ""))
        for row in derived_rows
        if any(token in str(row.get("EOM", "")) for token in ("f_a", "f1", "n_i", "Z_A"))
    ]
    fixed = [text for text in named if _fixes_weight_to_a_number(text)]
    bianchi = _bianchi_coverage()
    eom_probe = _probe(
        "eom_4d",
        bool(fixed),
        {
            "derived_row_count": len(derived_rows),
            "equations_naming_weights": named,
            "weights_fixed_to_a_number": fixed,
            "bianchi_new_parameter_relation": bianchi["new_parameter_relation"],
            "bianchi_constrains_lambda_or_Z_A": bianchi["constrains_c0_c1_Z_lambda_ZA"],
        },
    )
    return [gauge_probe, spectrum_probe, eom_probe]


def run_containment_audit_T08(
    closure_target: str | None = None,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan for a derived universal gauge or modular weight.

    UNIVERSAL_WEIGHTS_DERIVED is logged before the scan.
    """
    if closure_target is not None and closure_target != CLOSURE_TARGET:
        return {
            "status": "CLOSURE_CRITERION_REFUSED",
            "PHASE": PHASE,
            "topic": "T08: universal f_a(T) / fixed weights",
            "rule": "Target-Blind rule",
            "scanned": False,
            "provenance_log": [
                {
                    "entry": "Pre-Execution Closure Criterion",
                    "rule": "Target-Blind rule",
                    "closure_target": None,
                    "accepted": False,
                    "logged_before_logical_execution": True,
                    "post_hoc_validation": False,
                }
            ],
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    prior = run_phase_11AI_2_execution(F_T_IdentificationAuthorization(), write_artifacts=False)
    if prior.get("observed") != "RELATION_NOT_DERIVED" or prior.get("parameter_free_relation") is not False:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Phase 11AI.2 did not leave T07 without a parameter reduction",
            "scanned": False,
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    if prior.get("T06_STATUS") != "FAILED_NO_PARAMETER_REDUCTION":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "T06 is not archived as a failed parameter reduction",
            "scanned": False,
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    t07_entry = {
        "entry": "T07 status",
        "T07_STATUS": T07_STATUS,
        "previous_phase": "PHASE_11AI.2",
        "previous_observed": prior["observed"],
        "T06_STATUS": prior["T06_STATUS"],
        "previous_record_modified": False,
        "logged_before_t08_scan": True,
    }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "accepted": True,
    }
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [t07_entry, closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11AE4": phase11ae4_artifact_dir() / "PHASE_11AE4_SYNTHESIS.json",
        "11AI2": phase11ai2_artifact_dir() / "PHASE_11AI2_EXECUTION.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    decision = json.loads(parents["11AD"].read_text(encoding="utf-8")).get("decision_map") or {}
    if decision.get("T08") != "REQUIRES_EXPLICIT_ASSUMPTION":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [t07_entry, closure_entry],
            "detail": "parent T08 decision",
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    vacuum = run_phase_11AE_4_synthesis(write_artifacts=False)
    if vacuum.get("PROGRAM_CLOSURE_STATUS") != "CLOSED_UNDER_DECLARED_SCOPE" or vacuum.get("synthesis", {}).get("symmetry") != "Z_2":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Z_2 moduli class is not the closed Phase 11AE.4 record",
            "scanned": False,
            "provenance_log": [t07_entry, closure_entry],
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    probes = _scan(vacuum)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "detail": "parent artifact mutated",
            "scanned": False,
            "new_parameter_count": 0,
            "T08_activated": False,
        }
    found = any(item["found"] for item in probes)
    provenance_log = [t07_entry, closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "topic": "T08: universal f_a(T) / fixed weights",
        "T07_STATUS": T07_STATUS,
        "T06_STATUS": prior["T06_STATUS"],
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "UNIVERSAL_WEIGHTS_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T08_activated": False,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AJ_T08_CONTAINMENT.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11ae4_artifact_dir().resolve(),
            phase11ai2_artifact_dir().resolve(),
            phase10b8_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            canonical_json_bytes(
                {
                    "T07_STATUS": T07_STATUS,
                    "topic": payload["topic"],
                    "Provenance": payload["Provenance"],
                    "log": provenance_log,
                }
            )
            + b"\n"
        )
    return payload
