"""Phase 5B.0 pre-analysis gate.  Does not construct candidate symmetries."""

from __future__ import annotations

from typing import Any

from physics_lab.physics.phase4c_action_freeze import (
    ANALYSIS_AUTHORIZED,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    require_phase4c_action_freeze,
    verify_phase4c_action_freeze,
)

__all__ = [
    "ANALYSIS_AUTHORIZED",
    "FreezeIntegrityError",
    "Phase5B0Authorization",
    "UnauthorizedAnalysisError",
    "authorize_phase5b0_analysis",
    "require_phase4c_action_freeze",
    "run_phase5b0_or_stop",
    "verify_phase4c_action_freeze",
]


def run_phase5b0_or_stop(*, root=None) -> dict[str, Any]:
    """Authorize, then analyze.  On gate failure return integrity state only."""
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {
            "status": "STOP",
            "integrity": exc.payload,
            "scientific_analysis": None,
        }
    from physics_lab.physics.phase5b0_symmetry import analyze_frozen_action_symmetry

    science = analyze_frozen_action_symmetry(auth)
    if science.get("status") == "ANALYSIS_INVALIDATED_BY_ACTION_CHANGE":
        return {
            "status": "STOP",
            "integrity": science,
            "scientific_analysis": None,
        }
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "freeze_id": auth.freeze_id,
            "serializer_schema": auth.serializer_schema,
            "action_content_hash": auth.action_content_hash,
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "ACTION_INTEGRITY": science.get("action_integrity"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
