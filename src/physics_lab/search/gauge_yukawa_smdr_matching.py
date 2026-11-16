"""W16 target-blind matching of W15 IR states to the official SMDR backend.

W15 evolves an extended gauge--Yukawa theory.  SMDR, by design, evaluates
pure-Standard-Model running-to-pole observables.  This adapter therefore
performs a declared low-energy projection: W15 thresholds are already applied,
the SM gauge/Yukawa/Higgs entries are converted to SMDR conventions, and the
new singlet/vector-like sector is recorded as omitted from the pure-SM call.

The result is a diagnostic bridge, not a BSM pole-matching claim.  It never
fits, ranks, selects, or compares against experimental targets.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from physics_lab.search.smdr_backend import (
    ELECTROWEAK_VEV_GEV,
    SMDR_BRIDGE_VERSION,
    SMDRBackendError,
    run_smdr_calc_all,
    target_blind_input_text,
)


SMDR_MATCHING_VERSION = "gauge-yukawa-smdr-matching-v1"
SMDR_OFFICIAL_REPOSITORY = "https://github.com/davidgrobertson/SMDR"
SMDR_KNOWN_COMMIT = "5c4dd92c918cadb7f91ad3795694f8398b5c287a"


class SMDRMatchingError(ValueError):
    """Raised for malformed W15 states or matching activations."""


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise SMDRMatchingError(f"{name} must be finite")
    return result


def _w15_threshold_summary(candidate: Mapping[str, Any]) -> dict[str, Any]:
    segments = candidate.get("segments", [])
    if not isinstance(segments, list):
        raise SMDRMatchingError("W15 candidate segments must be a list")
    active = []
    for segment in segments:
        if not isinstance(segment, Mapping):
            raise SMDRMatchingError("W15 threshold segment must be an object")
        active.append(
            {
                "high_scale_gev": segment.get("high_scale_gev"),
                "low_scale_gev": segment.get("low_scale_gev"),
                "active_multiplicities": dict(segment.get("active_multiplicities", {})),
            }
        )
    return {
        "w15_segments_count": len(active),
        "w15_segments": active,
        "thresholds_applied_before_smdr": bool(active),
        "finite_bsm_threshold_corrections_in_smdr": False,
    }


def w15_state_to_smdr_input(
    state: Sequence[float],
    *,
    scale_gev: float,
    vev_gev: float = ELECTROWEAK_VEV_GEV,
    delta_alpha_hadronic: float = 0.0,
    candidate: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Convert the W15 eight-state convention into a target-blind SMDR input.

    W15 stores ``(g1,g2,g3,yt,yS,lambda_h,lambda_s,lambda_hs)`` with GUT-
    normalized ``g1`` and conventional SM Higgs quartic ``lambda_h``.  SMDR's
    bridge accepts ``(g1,g2,g3,yt,yb,lambda_4)`` where
    ``gY=sqrt(3/5) g1`` and ``lambda_SM=2 lambda_4``.  Therefore
    ``lambda_4=lambda_h/2`` and the absent bottom Yukawa is explicitly set to
    zero.  ``yS``, ``lambda_s`` and ``lambda_hs`` are not silently mapped into
    a pure-SM calculation; they are recorded as an external BSM sector.
    """

    if len(state) != 8:
        raise SMDRMatchingError("W15 state must contain eight couplings")
    values = tuple(_finite(value, f"w15_state[{index}]") for index, value in enumerate(state))
    g1, g2, g3, yt, y_s, lambda_h, lambda_s, lambda_hs = values
    input_text = target_blind_input_text(
        (g1, g2, g3, yt, 0.0, lambda_h / 2.0),
        scale_gev=scale_gev,
        vev_gev=vev_gev,
        delta_alpha_hadronic=delta_alpha_hadronic,
    )
    metadata: dict[str, Any] = {
        "w15_state_order": ["g1", "g2", "g3", "yt", "yS", "lambda_h", "lambda_s", "lambda_hs"],
        "smdr_bridge_order": ["g1", "g2", "g3", "yt", "yb", "lambda_4"],
        "g1_to_smdr_hypercharge": "gp = sqrt(3/5) * g1",
        "lambda_h_to_smdr_lambda4": "lambda_4 = lambda_h / 2",
        "yb_control_value": 0.0,
        "delta_alpha_hadronic_control_value": float(delta_alpha_hadronic),
        "scale_gev": float(scale_gev),
        "vev_gev": float(vev_gev),
        "pole_targets_supplied": False,
        "experimental_data_used": False,
        "external_bsm_sector": ["yS", "lambda_s", "lambda_hs"],
        "external_bsm_sector_values": {
            "yS": y_s,
            "lambda_s": lambda_s,
            "lambda_hs": lambda_hs,
        },
        "new_sector_omitted_from_pure_smdr": True,
    }
    if candidate is not None:
        metadata["thresholds"] = _w15_threshold_summary(candidate)
    return input_text, metadata


def _backend_commit(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _binary_sha256(root: Path) -> str | None:
    binary = root / "calc_all"
    if not binary.is_file():
        return None
    digest = hashlib.sha256()
    with binary.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_smdr_for_w15_candidate(
    candidate: Mapping[str, Any],
    *,
    smdr_root: str | Path,
    timeout_seconds: int = 120,
    scale_gev: float = 91.1876,
    vev_gev: float = ELECTROWEAK_VEV_GEV,
    delta_alpha_hadronic: float = 0.0,
) -> dict[str, Any]:
    """Run one W15 IR state through SMDR and classify backend failures."""

    candidate_id = str(candidate.get("candidate_id", "unnamed"))
    w15_status = str(candidate.get("status", "UNKNOWN"))
    state = candidate.get("final_state")
    if not isinstance(state, list):
        return {
            "candidate_id": candidate_id,
            "w15_status": w15_status,
            "status": "NOT_ELIGIBLE",
            "error_type": "MissingFinalState",
            "error": "W15 candidate has no final_state list",
            "target_blind_input": True,
        }
    if w15_status not in {"COMPLETE", "ZERO_PROTECTED"}:
        return {
            "candidate_id": candidate_id,
            "w15_status": w15_status,
            "status": "NOT_ELIGIBLE",
            "error_type": "W15StatusNotEligible",
            "error": f"W15 status {w15_status} is not eligible for SMDR projection",
            "target_blind_input": True,
        }
    try:
        input_text, mapping = w15_state_to_smdr_input(
            state,
            scale_gev=scale_gev,
            vev_gev=vev_gev,
            delta_alpha_hadronic=delta_alpha_hadronic,
            candidate=candidate,
        )
        backend = run_smdr_calc_all(smdr_root, input_text=input_text, timeout_seconds=timeout_seconds)
    except (SMDRBackendError, SMDRMatchingError) as exc:
        return {
            "candidate_id": candidate_id,
            "w15_status": w15_status,
            "status": "BACKEND_FAILURE" if isinstance(exc, SMDRBackendError) else "MATCHING_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "mapping": mapping if "mapping" in locals() else None,
            "target_blind_input": True,
            "pole_comparison": "NOT_AUTHORIZED",
        }
    return {
        "candidate_id": candidate_id,
        "w15_status": w15_status,
        "status": "SMDR_COMPLETE",
        "target_blind_input": True,
        "pole_comparison": "NOT_AUTHORIZED",
        "mapping": mapping,
        "backend": {
            "bridge_version": SMDR_BRIDGE_VERSION,
            "parsed": backend["parsed"],
            "input_sha256": backend.get("input_sha256"),
            "target_blind_input": backend.get("target_blind_input"),
            "stderr": backend.get("stderr", ""),
        },
    }


def run_smdr_matching_campaign(
    precision_report: Mapping[str, Any],
    *,
    smdr_root: str | Path,
    timeout_seconds: int = 120,
    scale_gev: float | None = None,
    vev_gev: float = ELECTROWEAK_VEV_GEV,
    delta_alpha_hadronic: float = 0.0,
    candidate_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Project every selected W15 candidate through SMDR, preserving order."""

    candidates = precision_report.get("candidate_results")
    if not isinstance(candidates, list) or not candidates:
        raise SMDRMatchingError("precision report requires candidate_results")
    selected = set(candidate_ids) if candidate_ids else None
    chosen = [item for item in candidates if selected is None or item.get("candidate_id") in selected]
    if selected is not None and len(chosen) != len(selected):
        missing = sorted(selected - {str(item.get("candidate_id")) for item in chosen})
        raise SMDRMatchingError(f"unknown W15 candidate ids: {missing}")
    root = Path(smdr_root).expanduser().resolve()
    effective_scale = float(scale_gev if scale_gev is not None else precision_report.get("scope", {}).get("ir_scale_gev", 91.1876))
    results = [
        run_smdr_for_w15_candidate(
            item,
            smdr_root=root,
            timeout_seconds=timeout_seconds,
            scale_gev=effective_scale,
            vev_gev=vev_gev,
            delta_alpha_hadronic=delta_alpha_hadronic,
        )
        for item in chosen
    ]
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    source_json = json.dumps(precision_report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "campaign_id": "w16-gauge-yukawa-smdr-matching-2026-11-16",
        "matching_version": SMDR_MATCHING_VERSION,
        "execution_status": "COMPLETE",
        "source": {
            "w15_pipeline_version": precision_report.get("pipeline_version"),
            "w15_candidate_count": len(candidates),
            "selected_candidate_count": len(chosen),
            "selected_candidate_ids": [str(item.get("candidate_id")) for item in chosen],
            "w15_report_sha256_canonical_json": hashlib.sha256(source_json).hexdigest(),
        },
        "backend": {
            "name": "SMDR",
            "official_repository": SMDR_OFFICIAL_REPOSITORY,
            "known_reference_commit": SMDR_KNOWN_COMMIT,
            "resolved_commit": _backend_commit(root),
            "calc_all_sha256": _binary_sha256(root),
            "scale_gev": effective_scale,
            "vev_gev": float(vev_gev),
            "timeout_seconds": int(timeout_seconds),
        },
        "scope": {
            "thresholds_applied_before_smdr": True,
            "pure_smdr_standard_model_projection": True,
            "finite_bsm_threshold_corrections_included": False,
            "new_singlet_and_vectorlike_sector_included_in_smdr": False,
            "pole_observables_are_diagnostic": True,
        },
        "scan": {"selected_case_count": len(chosen), "status_counts": counts},
        "controls": {
            "all_selected_candidates_retained": True,
            "candidate_order_preserved": True,
            "target_blind_generation": True,
            "pole_observables_generated": any(item["status"] == "SMDR_COMPLETE" for item in results),
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "new_bsm_sector_omitted_from_pure_smdr": True,
            "thresholds_applied_before_smdr": True,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": (
            "W16 target-blind projection of W15 IR states through the pure-SM SMDR backend. "
            "Pole outputs do not constitute a full BSM matching result because finite BSM "
            "threshold corrections and new-sector contributions are outside this SMDR call."
        ),
    }


def write_smdr_matching_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "SMDR_KNOWN_COMMIT",
    "SMDR_MATCHING_VERSION",
    "SMDR_OFFICIAL_REPOSITORY",
    "SMDRMatchingError",
    "run_smdr_for_w15_candidate",
    "run_smdr_matching_campaign",
    "w15_state_to_smdr_input",
    "write_smdr_matching_report",
]
