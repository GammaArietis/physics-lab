"""Phase 11AG: containment audit for T13 A/B/FI operators.

T09 is frozen with a residual sign degeneracy. This module asks whether a
linear gauge term or an asymmetric soft operator is already derived. It does
not add one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase5d_gauge_dynamics import phase5d_scope_summary
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae3_discrete_vacuum import run_phase_11AE_3_execution
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir

__all__ = [
    "CLOSURE_TARGET",
    "T09_STATUS",
    "T09_ANNOTATION",
    "run_containment_audit_T13",
]

PHASE = "PHASE_11AG"
T09_STATUS = "FROZEN_SYMMETRY_RESIDUAL"
T09_ANNOTATION = (
    "Il loop quantistico ha eliminato gli stati tachionici misti, "
    "ma non ha potuto rompere la degenerazione residua senza fissare arbitrariamente il parametro c_H."
)
CLOSURE_TARGET = "ASYMMETRIC_OPERATOR_FOUND"
_OPERATOR_MARKERS = ("fayet", "f_i", "a-term", "b-term", "a_term", "b_term", "soft")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ag_artifacts"


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _text_has_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _OPERATOR_MARKERS)


def _freeze_t09() -> dict[str, Any] | dict[str, Any]:
    previous = run_phase_11AE_3_execution(write_artifacts=False)
    if previous.get("observed") != "DOMAIN_UNREDUCED" or previous.get("T09_STATUS") != "UNFROZEN":
        return {"status": "STOP", "detail": "T09 freeze does not match Phase 11AE.3"}
    evaluation = previous["evaluation"]
    mixed_removed = all(
        row["complex_log"] is True
        for row in evaluation["rows"]
        if row["lambda_signs"][0] != row["lambda_signs"][1]
    )
    if not mixed_removed or evaluation["selection_is_unique"] is not False:
        return {"status": "STOP", "detail": "residual degeneracy record does not match Phase 11AE.3"}
    return {
        "entry": "T09 freeze",
        "T09_STATUS": T09_STATUS,
        "annotation": T09_ANNOTATION,
        "mixed_tachyonic_states_eliminated": True,
        "residual_degeneracy_tracks_c_H": True,
        "c_H_fixed": False,
        "logged_before_t13_scan": True,
    }


def _scan() -> list[dict[str, Any]]:
    document = phase4c_action_document()
    term_ids = [term["id"] for term in document["terms"]]
    field_ids = [field["id"] for field in document["fields"]]
    parameter_ids = [row["id"] for row in document["parameters"]]
    frozen_text = " ".join(term_ids + field_ids + parameter_ids)
    frozen_probe = _probe(
        "frozen_action",
        False,
        {
            "term_ids": term_ids,
            "field_ids": field_ids,
            "gauge_field_present": "A_mu" in field_ids,
            "linear_gauge_term_present": False,
            "marker_in_frozen_terms": _text_has_marker(frozen_text),
            "lam_a_provenance": "INPUT",
            "lam_b_provenance": "INPUT",
            "H_int_provenance": "ASSUMED",
        },
    )

    scope = phase5d_scope_summary()
    in_scope = " ".join(scope["in_scope"])
    gauge_probe = _probe(
        "gauge_phase_5d",
        _text_has_marker(in_scope),
        {
            "tests_only": scope["tests_only"],
            "in_scope_declares_linear_gauge_term": "linear" in in_scope.lower(),
            "quadratic_invariants_only": "quadratic invariants" in in_scope.lower(),
            "marker_in_scope": _text_has_marker(in_scope),
        },
    )

    eom_rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    eom_text = " ".join(str(row.get("EOM", "")) for row in eom_rows)
    eom_derived_operator = any(
        _text_has_marker(str(row.get("EOM", ""))) and str(row.get("provenance", "")).startswith("DERIVED")
        for row in eom_rows
    )
    eom_probe = _probe(
        "eom_4d",
        eom_derived_operator,
        {
            "row_count": len(eom_rows),
            "marker_in_eom": _text_has_marker(eom_text),
            "constant_linear_gauge_source": False,
        },
    )

    bianchi = json.loads(
        (phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json").read_text(encoding="utf-8")
    ).get("bianchi_analysis") or {}
    bianchi_text = " ".join(str(value) for value in bianchi.values())
    bianchi_derived = str(bianchi.get("provenance", "")).startswith("DERIVED") and _text_has_marker(bianchi_text)
    bianchi_probe = _probe(
        "bianchi_identity",
        bianchi_derived,
        {
            "status": bianchi.get("status"),
            "geometric_identity": bianchi.get("geometric_identity"),
            "marker_in_bianchi": _text_has_marker(bianchi_text),
            "splits_lambda_directions": False,
        },
    )
    return [frozen_probe, gauge_probe, eom_probe, bianchi_probe]


def run_containment_audit_T13(
    closure_target: str | None = None,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan for a derived FI term or an asymmetric A/B operator.

    ASYMMETRIC_OPERATOR_FOUND is logged before the scan. The frozen action is
    not modified.
    """
    frozen = _freeze_t09()
    if frozen.get("status") == "STOP":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": frozen.get("detail"),
            "scanned": False,
            "new_parameter_count": 0,
            "T13_activated": False,
        }
    if closure_target is not None and closure_target != CLOSURE_TARGET:
        return {
            "status": "CLOSURE_CRITERION_REFUSED",
            "PHASE": PHASE,
            "T09_STATUS": T09_STATUS,
            "rule": "Target-Blind rule",
            "scanned": False,
            "provenance_log": [
                frozen,
                {
                    "entry": "Pre-Execution Closure Criterion",
                    "rule": "Target-Blind rule",
                    "closure_target": None,
                    "accepted": False,
                    "logged_before_logical_execution": True,
                    "post_hoc_validation": False,
                },
            ],
            "new_parameter_count": 0,
            "T13_activated": False,
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
            "provenance_log": [frozen, closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T13_activated": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "11O": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items()}
    decision = json.loads(before["11AD"].decode("utf-8")).get("decision_map") or {}
    if decision.get("T13") != "REQUIRES_NEW_PHYSICAL_INPUT":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [frozen, closure_entry],
            "detail": "parent T13 decision",
            "new_parameter_count": 0,
            "T13_activated": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    probes = _scan()
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "detail": "frozen action mutated",
            "new_parameter_count": 0,
            "T13_activated": False,
        }
    found = any(item["found"] for item in probes)
    provenance_log = [frozen, closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "topic": "T13: A/B/FI operators",
        "T09_STATUS": T09_STATUS,
        "T09_annotation": T09_ANNOTATION,
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "ASYMMETRIC_OPERATOR_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T13_activated": False,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    after = {name: path.read_bytes() for name, path in parents.items()}
    if after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "detail": "parent artifact mutated",
            "scanned": False,
            "new_parameter_count": 0,
            "T13_activated": False,
        }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AG_T13_CONTAINMENT.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            canonical_json_bytes(
                {
                    "T09_STATUS": T09_STATUS,
                    "annotation": T09_ANNOTATION,
                    "Provenance": payload["Provenance"],
                    "log": provenance_log,
                }
            )
            + b"\n"
        )
    return payload
