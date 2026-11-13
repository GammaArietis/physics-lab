"""Phase 11 final closure.

The report records the outcomes already obtained. It does not rewrite them.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ae4_degenerate_vacuum import run_phase_11AE_4_synthesis
from physics_lab.physics.phase11aj2_universal_weights import (
    UniversalWeightsAuthorization,
    run_phase_11AJ_2_execution,
)
from physics_lab.physics.phase11aj_universal_weights import run_containment_audit_T08
from physics_lab.physics.phase11ak_uv_completion import (
    UVCompletionAuthorization,
    run_phase_11AK_2_execution,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "PHASE",
    "PROGRAM_STATUS",
    "run_phase_11_synthesis",
]

PHASE = "PHASE_11_FINAL_CLOSURE"
PROGRAM_STATUS = "PHASE_11_CLOSED_UNDER_DECLARED_SCOPE"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11_final_artifacts"


def _laboratory_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def _topic(outcome: str, observed: str, detail: str) -> dict[str, str]:
    return {"outcome": outcome, "observed": observed, "detail": detail}


def run_phase_11_synthesis(*, signature: str = MOSTLY_PLUS, write_artifacts: bool = False) -> dict[str, Any]:
    """Aggregate Phase 11 and seal the laboratory hash of that record."""
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    vacuum = run_phase_11AE_4_synthesis(write_artifacts=False, signature=signature)
    weights_audit = run_containment_audit_T08(write_artifacts=False)
    weights = run_phase_11AJ_2_execution(UniversalWeightsAuthorization(), write_artifacts=False, signature=signature)
    ultraviolet = run_phase_11AK_2_execution(UVCompletionAuthorization(), write_artifacts=False, signature=signature)
    document_after = canonical_json_bytes(phase4c_action_document())
    if document_after != document_before:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "frozen action mutated",
            "new_parameter_count": 0,
            "frozen_action_modified": True,
        }
    t10_ok = (
        vacuum.get("status") == "OK"
        and vacuum.get("synthesis", {}).get("moduli_fixed_at_finite_value") is True
        and vacuum.get("synthesis", {}).get("t10_solution_count") == 4
    )
    t09_ok = (
        vacuum.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE"
        and vacuum.get("T09_STATUS") == "CLOSED"
        and vacuum.get("synthesis", {}).get("symmetry") == "Z_2"
        and vacuum.get("synthesis", {}).get("mixed_tachyonic_states_eliminated") is True
    )
    t06_ok = weights_audit.get("T06_STATUS") == "FAILED_NO_PARAMETER_REDUCTION"
    t07_ok = weights_audit.get("T07_STATUS") == "FAILED_NO_PARAMETER_REDUCTION"
    t08_ok = weights.get("observed") == "RELATION_NOT_DERIVED" and weights.get("parameter_free_relation") is False
    if not all((t10_ok, t09_ok, t06_ok, t07_ok, t08_ok)) or ultraviolet.get("status") != "OK":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "a Phase 11 record does not match its stored outcome",
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    t12_failed = ultraviolet.get("observed") == "RELATION_NOT_DERIVED"
    t12_success = ultraviolet.get("PROGRAM_CLOSURE_STATUS") == "CLOSED_UNDER_DECLARED_SCOPE"
    if t12_failed:
        t12 = _topic("FAILED", "RELATION_NOT_DERIVED", "Nessuna riduzione dei parametri.")
    elif t12_success:
        t12 = _topic("SUCCESS", "NEW_PARAMETER_FREE_RELATION", "Il cutoff UV elimina gradi di libertà parametrici.")
    else:
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "T12 outcome is not a recorded execution status",
            "new_parameter_count": 0,
            "frozen_action_modified": False,
        }
    topics = {
        "T10": _topic("SUCCESS", "MODULI_FIXED_AT_FINITE_VALUE", "Stabilizzati a valori finiti su dominî discreti."),
        "T09": _topic("SUCCESS", "DEGENERATE_CLASS", "Selezionata classe degenere Z_2, stati tachionici eliminati."),
        "T06": _topic("FAILED", "FAILED_NO_PARAMETER_REDUCTION", "Nessuna riduzione dei parametri."),
        "T07": _topic("FAILED", "FAILED_NO_PARAMETER_REDUCTION", "Nessuna riduzione dei parametri."),
        "T08": _topic("FAILED", "RELATION_NOT_DERIVED", "Nessuna riduzione dei parametri."),
        "T12": t12,
    }
    sealed = {
        "PHASE": PHASE,
        "action_content_hash": digest,
        "topics": topics,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
    }
    laboratory_hash = _laboratory_hash(sealed)
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "PROGRAM_CLOSURE_STATUS": PROGRAM_STATUS,
        "action_content_hash": digest,
        "laboratory_hash": laboratory_hash,
        "topics": topics,
        "T12_observed": ultraviolet["observed"],
        "frozen_action_modified": False,
        "new_parameter_count": 0,
        "provenance_log": [
            {"entry": "Phase 11 final synthesis", "PHASE": PHASE, "topics": list(topics)},
            {
                "entry": "laboratory hash",
                "laboratory_hash": laboratory_hash,
                "action_content_hash": digest,
                "frozen_hash_unchanged": True,
            },
        ],
    }
    if write_artifacts:
        destination = artifact_dir()
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_11_FINAL_CLOSURE.json").write_bytes(canonical_json_bytes(payload) + b"\n")
        (destination / "LABORATORY_STATE.json").write_bytes(
            canonical_json_bytes(
                {
                    "PROGRAM_CLOSURE_STATUS": PROGRAM_STATUS,
                    "laboratory_hash": laboratory_hash,
                    "action_content_hash": digest,
                    "topics": topics,
                }
            )
            + b"\n"
        )
    return payload
