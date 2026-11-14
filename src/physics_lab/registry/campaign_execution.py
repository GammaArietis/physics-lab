"""Explicit execution of audited candidate pilot campaigns."""

from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing as mp
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from physics_lab.registry.campaign import (
    DEFAULT_CAMPAIGN_MANIFEST_PATH,
    audit_campaign_readiness,
    load_campaign_manifest,
)
from physics_lab.registry.reference_pipeline import run_reference_pipeline
from physics_lab.registry.harmonic_oscillator_pipeline import run_harmonic_oscillator_pipeline
from physics_lab.registry.free_scalar_field_pipeline import run_free_scalar_field_pipeline
from physics_lab.registry.particle_in_box_pipeline import run_particle_in_box_pipeline
from physics_lab.registry.theory_candidate import load_theory_candidate


CAMPAIGN_ACTIVATION_VERSION = "campaign-activation-v1"
CAMPAIGN_EXECUTION_VERSION = "campaign-execution-v1"
DEFAULT_CAMPAIGN_ACTIVATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "campaign_activation_pilot.json"
)


class CampaignActivationError(ValueError):
    """Raised when explicit pilot authorization is invalid."""


class CampaignExecutionError(RuntimeError):
    """Raised when an authorized pilot cannot execute safely."""


def _portable_relative(path: str | None, label: str, *, allow_null: bool = False) -> str | None:
    if path is None and allow_null:
        return None
    if not isinstance(path, str) or not path or path.startswith("/") or ":\\" in path or ":/" in path:
        raise CampaignActivationError(f"{label} must be a relative path")
    if ".." in Path(path).parts:
        raise CampaignActivationError(f"{label} cannot escape the repository")
    return path


def validate_campaign_activation(activation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and detach the explicit human pilot authorization."""
    if not isinstance(activation, Mapping):
        raise CampaignActivationError("campaign activation must be an object")
    record = copy.deepcopy(dict(activation))
    required = {
        "schema_version",
        "activation_id",
        "campaign_id",
        "manifest_path",
        "authorization",
        "execution_status",
        "checkpoint_path",
        "report_path",
        "activated_at",
        "completed_at",
    }
    missing = sorted(required - record.keys())
    if missing:
        raise CampaignActivationError(f"activation is missing fields: {', '.join(missing)}")
    if record["schema_version"] != CAMPAIGN_ACTIVATION_VERSION:
        raise CampaignActivationError("unsupported campaign activation schema version")
    for field in ("activation_id", "campaign_id"):
        if not isinstance(record[field], str) or len(record[field]) < 3:
            raise CampaignActivationError(f"activation {field} is invalid")
    _portable_relative(record["manifest_path"], "manifest_path")
    _portable_relative(record["checkpoint_path"], "checkpoint_path")
    _portable_relative(record["report_path"], "report_path", allow_null=True)
    if record["execution_status"] not in {"NOT_RUN", "COMPLETE", "FAILED"}:
        raise CampaignActivationError("invalid pilot activation execution_status")
    if record["execution_status"] in {"COMPLETE", "FAILED"}:
        if record["report_path"] is None or record["completed_at"] is None:
            raise CampaignActivationError("completed activation needs report_path and completed_at")
    auth = record["authorization"]
    if not isinstance(auth, Mapping):
        raise CampaignActivationError("activation authorization must be an object")
    required_auth = {
        "status",
        "authorization_ref",
        "human_confirmation",
        "selection_mode",
        "ranking",
        "search_status",
        "finite_bounds",
        "empirical_comparison",
        "external_data_used",
    }
    if not required_auth.issubset(auth):
        raise CampaignActivationError("activation authorization is incomplete")
    if auth["status"] != "AUTHORIZED" or not auth["authorization_ref"]:
        raise CampaignActivationError("pilot requires an explicit authorization_ref")
    if auth["human_confirmation"] is not True:
        raise CampaignActivationError("pilot requires human_confirmation=true")
    if auth["selection_mode"] != "NO_AUTO_SELECTION" or auth["ranking"] != "DISABLED":
        raise CampaignActivationError("pilot cannot select or rank candidates automatically")
    if auth["search_status"] != "NOT_ACTIVATED" or auth["finite_bounds"] != "NOT_AUTHORIZED":
        raise CampaignActivationError("pilot search and finite bounds must remain closed")
    if auth["empirical_comparison"] != "NOT_AUTHORIZED" or auth["external_data_used"] is not False:
        raise CampaignActivationError("pilot empirical comparison and external data must remain closed")
    return record


def load_campaign_activation(path: str | Path = DEFAULT_CAMPAIGN_ACTIVATION_PATH) -> dict[str, Any]:
    """Load the explicit pilot authorization from JSON."""
    activation_path = Path(path)
    try:
        payload = json.loads(activation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignActivationError(f"cannot load campaign activation from {activation_path}: {exc}") from exc
    return validate_campaign_activation(payload)


def _pilot_worker(candidate_path: str, result_queue: Any) -> None:
    _candidate_worker(candidate_path, result_queue)


def _candidate_worker(candidate_path: str, result_queue: Any) -> None:
    try:
        candidate = load_theory_candidate(candidate_path)
        pipeline_ref = candidate["registration"].get("pipeline_ref")
        if pipeline_ref == "circle-reference-v1":
            report = run_reference_pipeline(candidate_path=candidate_path)
        elif pipeline_ref == "quantum-harmonic-oscillator-v1":
            report = run_harmonic_oscillator_pipeline(candidate_path=candidate_path)
        elif pipeline_ref == "free-scalar-field-v1":
            report = run_free_scalar_field_pipeline(candidate_path=candidate_path)
        elif pipeline_ref == "particle-in-box-v1":
            report = run_particle_in_box_pipeline(candidate_path=candidate_path)
        else:
            raise CampaignExecutionError(
                f"no campaign runner is registered for pipeline_ref={pipeline_ref!r}"
            )
        result_queue.put({"status": "PASS", "report": report})
    except BaseException as exc:  # noqa: BLE001 - serialize candidate failure for the campaign report
        result_queue.put({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})


def _execute_candidate(
    candidate_path: Path,
    timeout_seconds: float,
    *,
    start_method: str | None = None,
) -> dict[str, Any]:
    # Use the platform default: fork on the current Linux runner and spawn on
    # macOS/Windows. The worker is a module-level function, so both modes are
    # supported without sharing model state with the parent process.
    context = mp.get_context(start_method) if start_method is not None else mp.get_context()
    result_queue = context.Queue()
    process = context.Process(target=_pilot_worker, args=(str(candidate_path), result_queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        result_queue.close()
        return {"status": "FAIL", "error": "CampaignTimeout: per-candidate timeout exceeded"}
    try:
        return result_queue.get(timeout=2)
    except queue.Empty:
        return {"status": "FAIL", "error": f"CampaignWorkerExit: exit_code={process.exitcode}"}
    finally:
        result_queue.close()


def run_pilot_campaign(
    activation: Mapping[str, Any] | None = None,
    *,
    activation_path: str | Path = DEFAULT_CAMPAIGN_ACTIVATION_PATH,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute the explicitly authorized one-candidate pilot."""
    authorization = load_campaign_activation(activation_path) if activation is None else validate_campaign_activation(activation)
    if authorization["execution_status"] != "NOT_RUN":
        raise CampaignActivationError("pilot activation has already been closed")
    root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
    manifest_path = (root / authorization["manifest_path"]).resolve()
    try:
        manifest_path.relative_to(root)
    except ValueError as exc:
        raise CampaignExecutionError("manifest_path escapes the repository") from exc
    manifest = load_campaign_manifest(manifest_path)
    if manifest["campaign_id"] != authorization["campaign_id"]:
        raise CampaignExecutionError("activation and manifest campaign_id do not match")
    readiness = audit_campaign_readiness(manifest=manifest, repository_root=root)
    if readiness["status"] != "READY_FOR_PILOT":
        raise CampaignExecutionError("campaign readiness audit did not pass")
    if len(manifest["candidate_refs"]) != 1 or manifest["execution"]["max_candidates"] != 1:
        raise CampaignExecutionError("pilot executor accepts exactly one candidate")

    ref = manifest["candidate_refs"][0]
    candidate_path = (root / ref["record_path"]).resolve()
    before = load_theory_candidate(candidate_path)
    result = _execute_candidate(candidate_path, float(manifest["execution"]["per_candidate_timeout_seconds"]))
    after = load_theory_candidate(candidate_path)
    unchanged = before == after
    candidate_result: dict[str, Any] = {
        "candidate_id": ref["candidate_id"],
        "status": result["status"],
        "record_path": ref["record_path"],
        "record_unchanged": unchanged,
    }
    if result["status"] == "PASS":
        pipeline_report = result["report"]
        candidate_report_path = Path(manifest["execution"]["report_directory"]) / f"{ref['candidate_id']}.json"
        candidate_result.update(
            {
                "pipeline_status": pipeline_report["pipeline_status"],
                "candidate_report_path": str(candidate_report_path),
                "controls": pipeline_report["controls"],
            }
        )
    else:
        candidate_report_path = None
        candidate_result["error"] = result["error"]
    if not unchanged:
        raise CampaignExecutionError("candidate record changed during pilot execution")

    checkpoint_path = root / manifest["execution"]["checkpoint_path"]
    report_directory = root / manifest["execution"]["report_directory"]
    report_directory.mkdir(parents=True, exist_ok=True)
    if result["status"] == "PASS":
        (report_directory / f"{ref['candidate_id']}.json").write_text(
            json.dumps(result["report"], indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    status = "COMPLETE" if result["status"] == "PASS" else "FAILED"
    checkpoint = {
        "execution_version": CAMPAIGN_EXECUTION_VERSION,
        "campaign_id": manifest["campaign_id"],
        "activation_id": authorization["activation_id"],
        "execution_status": status,
        "completed_candidate_ids": [ref["candidate_id"]] if status == "COMPLETE" else [],
        "failed_candidate_ids": [] if status == "COMPLETE" else [ref["candidate_id"]],
        "candidate_results": [candidate_result],
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path = report_directory / "campaign_report.json"
    report = {
        "execution_version": CAMPAIGN_EXECUTION_VERSION,
        "campaign_id": manifest["campaign_id"],
        "activation_id": authorization["activation_id"],
        "execution_status": status,
        "candidate_count": 1,
        "candidate_results": [candidate_result],
        "checkpoint_path": manifest["execution"]["checkpoint_path"],
        "report_path": str(Path(manifest["execution"]["report_directory"]) / "campaign_report.json"),
        "controls": {
            "explicit_authorization": True,
            "no_auto_selection": True,
            "no_ranking": True,
            "no_search": True,
            "no_finite_bounds": True,
            "no_empirical_comparison": True,
            "no_external_data": True,
            "candidate_records_unchanged": unchanged,
            "checkpoint_written": checkpoint_path.exists(),
            "execution_isolated": True,
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_campaign_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_multi_candidate_campaign(
    activation: Mapping[str, Any] | None = None,
    *,
    activation_path: str | Path = DEFAULT_CAMPAIGN_ACTIVATION_PATH,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute an explicitly authorized, bounded multi-candidate pilot.

    This runner exercises parallel execution, per-candidate isolation,
    checkpointing and resume without selecting, ranking, fitting or comparing
    candidates against external data.  Each candidate is dispatched through
    the explicit ``registration.pipeline_ref`` binding in its record.
    """
    authorization = load_campaign_activation(activation_path) if activation is None else validate_campaign_activation(activation)
    if authorization["execution_status"] != "NOT_RUN":
        raise CampaignActivationError("multi-candidate activation has already been closed")
    root = Path(repository_root).resolve() if repository_root is not None else Path(__file__).resolve().parents[3]
    manifest_path = (root / authorization["manifest_path"]).resolve()
    try:
        manifest_path.relative_to(root)
    except ValueError as exc:
        raise CampaignExecutionError("manifest_path escapes the repository") from exc
    manifest = load_campaign_manifest(manifest_path)
    if manifest["campaign_id"] != authorization["campaign_id"]:
        raise CampaignExecutionError("activation and manifest campaign_id do not match")
    if len(manifest["candidate_refs"]) < 2:
        raise CampaignExecutionError("multi-candidate pilot requires at least two candidates")
    if manifest["execution"]["max_candidates"] != len(manifest["candidate_refs"]):
        raise CampaignExecutionError("multi-candidate pilot must bound exactly the registered candidates")
    readiness = audit_campaign_readiness(manifest=manifest, repository_root=root)
    if readiness["status"] != "READY_FOR_PILOT":
        raise CampaignExecutionError("campaign readiness audit did not pass")

    execution = manifest["execution"]
    report_directory = root / execution["report_directory"]
    checkpoint_path = root / execution["checkpoint_path"]
    refs = manifest["candidate_refs"]
    candidates: dict[str, dict[str, Any]] = {}
    candidate_paths: dict[str, Path] = {}
    candidate_digests: dict[str, str] = {}
    for ref in refs:
        candidate_path = (root / ref["record_path"]).resolve()
        try:
            candidate_path.relative_to(root)
        except ValueError as exc:
            raise CampaignExecutionError("candidate record escapes the repository") from exc
        candidate = load_theory_candidate(candidate_path)
        if candidate["candidate_id"] != ref["candidate_id"]:
            raise CampaignExecutionError(f"candidate reference mismatch for {ref['candidate_id']!r}")
        candidates[ref["candidate_id"]] = candidate
        candidate_paths[ref["candidate_id"]] = candidate_path
        candidate_digests[ref["candidate_id"]] = _canonical_digest(candidate)

    previous: dict[str, Any] = {}
    if execution["resume"] and checkpoint_path.exists():
        try:
            previous = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CampaignExecutionError(f"cannot resume from checkpoint: {exc}") from exc
        if previous.get("campaign_id") != manifest["campaign_id"] or previous.get("activation_id") != authorization["activation_id"]:
            raise CampaignExecutionError("checkpoint does not belong to this campaign activation")

    results_by_id: dict[str, dict[str, Any]] = {
        item["candidate_id"]: item
        for item in previous.get("candidate_results", [])
        if isinstance(item, Mapping) and isinstance(item.get("candidate_id"), str)
    }
    first_by_key: dict[str, str] = {}
    duplicate_policy = manifest["deduplication"]["on_duplicate"]
    dedup_key = manifest["deduplication"]["key"]
    for ref in refs:
        candidate_id = ref["candidate_id"]
        key_value = candidate_id if dedup_key == "candidate_id" else candidate_digests[candidate_id]
        if dedup_key == "canonical_action_digest":
            key_value = _canonical_digest(candidates[candidate_id]["action"])
        if key_value in first_by_key:
            if duplicate_policy == "STOP":
                raise CampaignExecutionError(f"duplicate candidate detected for {candidate_id!r}")
            results_by_id[candidate_id] = {
                "candidate_id": candidate_id,
                "status": "DUPLICATE",
                "record_path": ref["record_path"],
                "record_unchanged": True,
                "duplicate_of": first_by_key[key_value],
            }
        else:
            first_by_key[key_value] = candidate_id

    pending = [
        ref for ref in refs
        if ref["candidate_id"] not in results_by_id
        or results_by_id[ref["candidate_id"]].get("status") == "FAIL"
    ]
    timeout_seconds = float(execution["per_candidate_timeout_seconds"])

    def write_checkpoint(status: str) -> None:
        ordered = [results_by_id[ref["candidate_id"]] for ref in refs if ref["candidate_id"] in results_by_id]
        checkpoint = {
            "execution_version": CAMPAIGN_EXECUTION_VERSION,
            "campaign_id": manifest["campaign_id"],
            "activation_id": authorization["activation_id"],
            "execution_status": status,
            "completed_candidate_ids": [item["candidate_id"] for item in ordered if item.get("status") in {"PASS", "DUPLICATE"}],
            "failed_candidate_ids": [item["candidate_id"] for item in ordered if item.get("status") == "FAIL"],
            "candidate_results": ordered,
        }
        _write_campaign_json(checkpoint_path, checkpoint)

    def execute_ref(ref: Mapping[str, Any]) -> dict[str, Any]:
        candidate_id = ref["candidate_id"]
        before = candidates[candidate_id]
        result = _execute_candidate(
            candidate_paths[candidate_id],
            timeout_seconds,
            start_method="spawn",
        )
        after = load_theory_candidate(candidate_paths[candidate_id])
        unchanged = before == after
        item: dict[str, Any] = {
            "candidate_id": candidate_id,
            "status": result["status"],
            "record_path": ref["record_path"],
            "record_unchanged": unchanged,
        }
        if not unchanged:
            item["status"] = "FAIL"
            item["error"] = "candidate record changed during execution"
        elif result["status"] == "PASS":
            pipeline_report = result["report"]
            candidate_report_path = Path(execution["report_directory"]) / f"{candidate_id}.json"
            item.update(
                {
                    "pipeline_status": pipeline_report["pipeline_status"],
                    "candidate_report_path": str(candidate_report_path),
                    "controls": pipeline_report["controls"],
                }
            )
            _write_campaign_json(report_directory / f"{candidate_id}.json", pipeline_report)
        else:
            item["error"] = result["error"]
        return item

    write_checkpoint("RUNNING")
    with ThreadPoolExecutor(max_workers=int(execution["parallelism"])) as pool:
        futures = {pool.submit(execute_ref, ref): ref for ref in pending}
        for future in as_completed(futures):
            item = future.result()
            results_by_id[item["candidate_id"]] = item
            write_checkpoint("RUNNING")

    ordered_results = [results_by_id[ref["candidate_id"]] for ref in refs]
    failed = [item for item in ordered_results if item.get("status") == "FAIL"]
    max_failures = int(manifest["failure_policy"]["max_failures"])
    status = "COMPLETE" if len(failed) <= max_failures else "FAILED"
    write_checkpoint(status)
    report = {
        "execution_version": CAMPAIGN_EXECUTION_VERSION,
        "campaign_id": manifest["campaign_id"],
        "activation_id": authorization["activation_id"],
        "execution_status": status,
        "candidate_count": len(refs),
        "executed_candidate_count": len(pending),
        "candidate_results": ordered_results,
        "checkpoint_path": execution["checkpoint_path"],
        "report_path": str(Path(execution["report_directory"]) / "campaign_report.json"),
        "controls": {
            "explicit_authorization": True,
            "no_auto_selection": True,
            "no_ranking": True,
            "no_search": True,
            "no_finite_bounds": True,
            "no_empirical_comparison": True,
            "no_external_data": True,
            "candidate_records_unchanged": all(item.get("record_unchanged") is True for item in ordered_results),
            "checkpoint_written": checkpoint_path.exists(),
            "execution_isolated": True,
            "failure_isolation": manifest["failure_policy"]["mode"] == "ISOLATE_AND_CONTINUE",
            "deduplication_applied": dedup_key in {"candidate_id", "canonical_record_digest", "canonical_action_digest"},
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
    }
    _write_campaign_json(report_directory / "campaign_report.json", report)
    return report


def write_completed_activation(
    path: str | Path,
    activation: Mapping[str, Any],
    report: Mapping[str, Any],
    *,
    completed_at: str | None = None,
) -> Path:
    """Persist the activation record after a completed pilot."""
    record = validate_campaign_activation(activation)
    if report.get("execution_status") not in {"COMPLETE", "FAILED"}:
        raise CampaignExecutionError("cannot close activation from an unfinished report")
    record["execution_status"] = report["execution_status"]
    record["report_path"] = report.get("report_path")
    record["completed_at"] = completed_at or datetime.now().astimezone().isoformat(timespec="seconds")
    output_path = Path(path)
    output_path.write_text(
        json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "CAMPAIGN_ACTIVATION_VERSION",
    "CAMPAIGN_EXECUTION_VERSION",
    "CampaignActivationError",
    "CampaignExecutionError",
    "DEFAULT_CAMPAIGN_ACTIVATION_PATH",
    "load_campaign_activation",
    "run_multi_candidate_campaign",
    "run_pilot_campaign",
    "validate_campaign_activation",
    "write_completed_activation",
]
