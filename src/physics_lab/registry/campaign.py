"""Readiness contracts for bounded theory campaigns.

This module validates a campaign plan and audits its candidate references. It
does not execute candidates, select theories, rank results, or activate any
search or empirical comparison gate.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping

from physics_lab.registry.theory_candidate import load_theory_candidate


CAMPAIGN_MANIFEST_VERSION = "campaign-manifest-v1"
CAMPAIGN_READINESS_VERSION = "campaign-readiness-v1"
DEFAULT_CAMPAIGN_MANIFEST_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "campaign_manifest_pilot.json"
)

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
_RELATIVE_PATH_PATTERN = re.compile(r"^(?!/)(?![A-Za-z]:[\\/])[^\x00]+$")


class CampaignManifestError(ValueError):
    """Raised when a campaign manifest violates the campaign contract."""


class CampaignReadinessError(RuntimeError):
    """Raised when a readiness audit cannot be completed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignManifestError(message)


def _portable_relative(path: Any, label: str) -> str:
    _require(isinstance(path, str) and bool(path), f"{label} must be a non-empty path")
    _require(_RELATIVE_PATH_PATTERN.fullmatch(path) is not None, f"{label} must be relative")
    parts = Path(path).parts
    _require(".." not in parts, f"{label} cannot escape the repository")
    return path


def validate_campaign_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and detach a bounded campaign manifest."""
    if not isinstance(manifest, Mapping):
        raise CampaignManifestError("campaign manifest must be an object")
    record = copy.deepcopy(dict(manifest))
    required = {
        "schema_version",
        "campaign_id",
        "status",
        "candidate_refs",
        "scope",
        "selection_policy",
        "execution",
        "deduplication",
        "failure_policy",
        "authorization",
        "execution_status",
    }
    missing = sorted(required - record.keys())
    _require(not missing, f"campaign manifest is missing fields: {', '.join(missing)}")
    _require(record["schema_version"] == CAMPAIGN_MANIFEST_VERSION, "unsupported campaign manifest schema version")
    _require(isinstance(record["campaign_id"], str) and _ID_PATTERN.fullmatch(record["campaign_id"]) is not None, "campaign_id is not portable")
    _require(record["status"] in {"DRAFT", "PILOT_READY", "RUNNING", "COMPLETE", "BLOCKED", "REJECTED"}, "invalid campaign status")
    _require(record["execution_status"] == "NOT_RUN", "campaign manifest must be audited before execution")

    refs = record["candidate_refs"]
    _require(isinstance(refs, list) and bool(refs), "candidate_refs must be a non-empty list")
    seen_ids: set[str] = set()
    for index, ref in enumerate(refs):
        label = f"candidate_refs[{index}]"
        _require(isinstance(ref, Mapping), f"{label} must be an object")
        for field in ("candidate_id", "record_path", "expected_selected"):
            _require(field in ref, f"{label} is missing {field}")
        candidate_id = ref["candidate_id"]
        _require(isinstance(candidate_id, str) and _ID_PATTERN.fullmatch(candidate_id) is not None, f"{label}.candidate_id is not portable")
        _require(candidate_id not in seen_ids, f"duplicate candidate_id {candidate_id!r}")
        seen_ids.add(candidate_id)
        _require(ref["expected_selected"] is False, f"{label}.expected_selected must be false")
        _portable_relative(ref["record_path"], f"{label}.record_path")

    scope = record["scope"]
    _require(isinstance(scope, Mapping), "scope must be an object")
    _require(scope.get("search_status") == "NOT_ACTIVATED", "campaign search must remain NOT_ACTIVATED")
    _require(scope.get("finite_bounds") == "NOT_AUTHORIZED", "campaign finite bounds must remain NOT_AUTHORIZED")
    _require(scope.get("empirical_comparison") == "NOT_AUTHORIZED", "campaign empirical comparison must remain NOT_AUTHORIZED")
    _require(scope.get("external_data_used") is False, "campaign external_data_used must be false")

    selection = record["selection_policy"]
    _require(isinstance(selection, Mapping), "selection_policy must be an object")
    _require(selection.get("mode") == "NO_AUTO_SELECTION", "automatic selection is forbidden")
    _require(selection.get("ranking") == "DISABLED", "automatic ranking is forbidden")
    _require(selection.get("human_review_required") is True, "human review must be required")

    execution = record["execution"]
    _require(isinstance(execution, Mapping), "execution must be an object")
    max_candidates = execution.get("max_candidates")
    parallelism = execution.get("parallelism")
    timeout = execution.get("per_candidate_timeout_seconds")
    _require(isinstance(max_candidates, int) and not isinstance(max_candidates, bool) and max_candidates >= 1, "max_candidates must be a positive integer")
    _require(isinstance(parallelism, int) and not isinstance(parallelism, bool) and parallelism >= 1, "parallelism must be a positive integer")
    _require(isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and math.isfinite(float(timeout)) and 0 < float(timeout) <= 86400, "per_candidate_timeout_seconds must be in (0, 86400]")
    _portable_relative(execution.get("checkpoint_path"), "execution.checkpoint_path")
    _portable_relative(execution.get("report_directory"), "execution.report_directory")
    _require(execution.get("resume") is True, "campaign execution must be resumable")
    seed = execution.get("deterministic_seed")
    _require(seed is None or (isinstance(seed, int) and not isinstance(seed, bool)), "deterministic_seed must be an integer or null")

    dedup = record["deduplication"]
    _require(isinstance(dedup, Mapping), "deduplication must be an object")
    _require(dedup.get("key") in {"candidate_id", "canonical_record_digest", "canonical_action_digest"}, "invalid deduplication key")
    _require(dedup.get("on_duplicate") in {"RETAIN_FIRST_WITH_LINK", "MERGE_WITH_PROVENANCE", "STOP"}, "invalid duplicate policy")

    failure = record["failure_policy"]
    _require(isinstance(failure, Mapping), "failure_policy must be an object")
    _require(failure.get("mode") == "ISOLATE_AND_CONTINUE", "failure policy must isolate candidates")
    max_failures = failure.get("max_failures")
    _require(isinstance(max_failures, int) and not isinstance(max_failures, bool) and 0 <= max_failures <= max_candidates, "max_failures must be bounded by max_candidates")

    authorization = record["authorization"]
    _require(isinstance(authorization, Mapping), "authorization must be an object")
    _require(authorization.get("status") == "NOT_ACTIVATED", "campaign authorization must remain NOT_ACTIVATED")
    _require(authorization.get("authorization_ref") is None or isinstance(authorization.get("authorization_ref"), str), "authorization_ref must be a string or null")
    return record


def load_campaign_manifest(path: str | Path = DEFAULT_CAMPAIGN_MANIFEST_PATH) -> dict[str, Any]:
    """Load and validate a campaign manifest from JSON."""
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignManifestError(f"cannot load campaign manifest from {manifest_path}: {exc}") from exc
    return validate_campaign_manifest(payload)


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _repository_root(repository_root: str | Path | None) -> Path:
    return Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]


def audit_campaign_readiness(
    manifest: Mapping[str, Any] | None = None,
    *,
    manifest_path: str | Path = DEFAULT_CAMPAIGN_MANIFEST_PATH,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Audit a manifest and its candidate records without executing them."""
    record = load_campaign_manifest(manifest_path) if manifest is None else validate_campaign_manifest(manifest)
    root = _repository_root(repository_root)
    candidate_audits: list[dict[str, Any]] = []
    candidate_checks: list[bool] = []
    for ref in record["candidate_refs"]:
        candidate_path = (root / ref["record_path"]).resolve()
        item: dict[str, Any] = {
            "candidate_id": ref["candidate_id"],
            "record_path": ref["record_path"],
        }
        try:
            candidate_path.relative_to(root)
            candidate = load_theory_candidate(candidate_path)
            id_matches = candidate["candidate_id"] == ref["candidate_id"]
            selected = candidate["registration"]["selected"]
            expected_status = ref.get("expected_registration_status")
            registration_matches = expected_status is None or candidate["registration"]["status"] == expected_status
            scope_closed = (
                candidate["authorization"]["search_status"] == "NOT_ACTIVATED"
                and candidate["authorization"]["finite_bounds"] == "NOT_AUTHORIZED"
                and candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"
                and candidate["authorization"]["external_data_used"] is False
            )
            item.update(
                {
                    "status": "PASS" if id_matches and not selected and registration_matches and scope_closed else "FAIL",
                    "candidate_record_digest": _canonical_digest(candidate),
                    "id_matches": id_matches,
                    "selected": selected,
                    "registration_status": candidate["registration"]["status"],
                    "registration_matches": registration_matches,
                    "scope_closed": scope_closed,
                }
            )
            candidate_checks.append(item["status"] == "PASS")
        except Exception as exc:  # noqa: BLE001 - audit records isolate candidate failures
            item.update({"status": "FAIL", "error": str(exc)})
            candidate_checks.append(False)
        candidate_audits.append(item)

    execution = record["execution"]
    max_candidates = execution["max_candidates"]
    checks = {
        "manifest_scope_closed": True,
        "candidate_refs_unique": len({ref["candidate_id"] for ref in record["candidate_refs"]}) == len(record["candidate_refs"]),
        "candidate_records_valid": bool(candidate_checks) and all(candidate_checks),
        "candidates_unselected": all(item.get("selected") is False for item in candidate_audits if item.get("status") == "PASS"),
        "search_not_activated": record["scope"]["search_status"] == "NOT_ACTIVATED",
        "finite_bounds_not_authorized": record["scope"]["finite_bounds"] == "NOT_AUTHORIZED",
        "empirical_comparison_not_authorized": record["scope"]["empirical_comparison"] == "NOT_AUTHORIZED",
        "external_data_disabled": record["scope"]["external_data_used"] is False,
        "no_auto_selection": record["selection_policy"]["mode"] == "NO_AUTO_SELECTION" and record["selection_policy"]["ranking"] == "DISABLED",
        "human_review_required": record["selection_policy"]["human_review_required"] is True,
        "checkpoint_resumable": bool(execution["checkpoint_path"]) and execution["resume"] is True,
        "parallelism_bounded": 1 <= execution["parallelism"] <= min(max_candidates, len(record["candidate_refs"])),
        "candidate_limit_bounded": max_candidates <= len(record["candidate_refs"]),
        "timeout_bounded": 0 < float(execution["per_candidate_timeout_seconds"]) <= 86400,
        "deduplication_configured": record["deduplication"]["key"] in {"candidate_id", "canonical_record_digest", "canonical_action_digest"},
        "failure_isolation_configured": record["failure_policy"]["mode"] == "ISOLATE_AND_CONTINUE",
        "execution_not_started": record["execution_status"] == "NOT_RUN",
    }
    ready = all(checks.values())
    return {
        "audit_version": CAMPAIGN_READINESS_VERSION,
        "campaign_id": record["campaign_id"],
        "status": "READY_FOR_PILOT" if ready else "NOT_READY",
        "execution_status": "NOT_RUN",
        "candidate_count": len(record["candidate_refs"]),
        "candidate_ids": [ref["candidate_id"] for ref in record["candidate_refs"]],
        "candidate_audits": candidate_audits,
        "checks": checks,
        "controls": {
            "no_candidate_execution": True,
            "no_auto_selection": checks["no_auto_selection"],
            "no_ranking": record["selection_policy"]["ranking"] == "DISABLED",
            "no_external_data": checks["external_data_disabled"],
            "resumable": checks["checkpoint_resumable"],
            "failure_isolation": checks["failure_isolation_configured"],
        },
    }


def write_campaign_readiness_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **audit_kwargs: Any,
) -> Path:
    """Write a deterministic readiness report."""
    output_path = Path(path)
    payload = report or audit_campaign_readiness(**audit_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "CAMPAIGN_MANIFEST_VERSION",
    "CAMPAIGN_READINESS_VERSION",
    "CampaignManifestError",
    "CampaignReadinessError",
    "DEFAULT_CAMPAIGN_MANIFEST_PATH",
    "audit_campaign_readiness",
    "load_campaign_manifest",
    "validate_campaign_manifest",
    "write_campaign_readiness_report",
]
