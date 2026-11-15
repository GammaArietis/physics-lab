"""Replay every eligible W11 state through the official SMDR executable.

The runner is intentionally a batch executor, not a search or selection
mechanism. It preserves archive order, records every eligible result, writes
non-eligible source cases as explicit records, and can resume from a
compressed JSONL output after interruption.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from physics_lab.search.smdr_backend import (
    SMDR_BRIDGE_VERSION,
    run_smdr_calc_all,
    target_blind_input_text,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz"
DEFAULT_OUTPUT = ROOT / "docs/validation/smdr_full_batch_replay_2026-11-15.jsonl.gz"
DEFAULT_CHECKPOINT = ROOT / "docs/validation/smdr_full_batch_replay_2026-11-15.checkpoint.json"
DEFAULT_SUMMARY = ROOT / "docs/validation/smdr_full_batch_replay_2026-11-15.summary.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_archive(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        report = json.load(handle)
    if not isinstance(report.get("cases"), list):
        raise ValueError("source archive does not contain a cases list")
    return report


def _read_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            case_id = record.get("case_id")
            if case_id:
                records[str(case_id)] = record
    return records


def _write_checkpoint(
    path: Path,
    *,
    status: str,
    source_archive_sha256: str,
    output_path: Path,
    expected_count: int,
    records: Mapping[str, Mapping[str, Any]],
    workers: int,
) -> None:
    counts: dict[str, int] = {}
    for record in records.values():
        key = str(record.get("replay_status", "UNKNOWN"))
        counts[key] = counts.get(key, 0) + 1
    checkpoint = {
        "checkpoint_version": "smdr-full-batch-v1",
        "updated_at_utc": _utc_now(),
        "status": status,
        "source_archive_sha256": source_archive_sha256,
        "output_path": str(output_path),
        "expected_count": expected_count,
        "processed_count": len(records),
        "status_counts": counts,
        "workers": workers,
        "controls": {
            "archive_order_preserved": True,
            "all_negative_results_retained": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "no_fitting": True,
            "target_blind_generation": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _source_record(index: int, case: Mapping[str, Any]) -> dict[str, Any] | None:
    case_id = str(case["case_id"])
    if case.get("status") == "COMPLETE" and case.get("ew_state") and case.get("electroweak_observables"):
        return None
    return {
        "case_index": index,
        "case_id": case_id,
        "replay_status": "NOT_ELIGIBLE",
        "source_status": case.get("status"),
        "source_error": case.get("error"),
        "reason": "no complete electroweak W11 state available for SMDR input",
    }


def _replay_worker(payload: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(payload["case_id"])
    try:
        input_text = target_blind_input_text(
            payload["ew_state"],
            scale_gev=float(payload["evaluation_scale_gev"]),
        )
        result = run_smdr_calc_all(
            payload["smdr_root"],
            input_text=input_text,
            timeout_seconds=int(payload["timeout_seconds"]),
        )
        return {
            "case_index": payload["case_index"],
            "case_id": case_id,
            "replay_status": "COMPLETE",
            "source_status": payload["source_status"],
            "backend_version": result["parsed"].get("version"),
            "parsed": result["parsed"],
            "input_sha256": result.get("input_sha256"),
            "warning_tail": result.get("stderr", "")[-2000:],
            "target_blind_input": True,
        }
    except Exception as exc:  # retain failures as data and continue the batch
        return {
            "case_index": payload["case_index"],
            "case_id": case_id,
            "replay_status": "BACKEND_FAILURE",
            "source_status": payload.get("source_status"),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "target_blind_input": True,
        }


def _write_record(handle, record: Mapping[str, Any]) -> None:
    handle.write(json.dumps(dict(record), sort_keys=True, ensure_ascii=False) + "\n")
    handle.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smdr-root", required=True, help="built official SMDR repository root")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--workers", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--checkpoint-every", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None, help="explicit smoke limit; omit for full replay")
    parser.add_argument("--case-id", action="append", default=[], help="explicit case id; repeat to replay selected cases")
    parser.add_argument("--resume", action="store_true", help="resume an existing JSONL.GZ output")
    args = parser.parse_args()

    if args.workers < 1 or args.workers > 32:
        parser.error("--workers must be in [1, 32]")
    if args.timeout_seconds < 1 or args.checkpoint_every < 1:
        parser.error("timeout and checkpoint interval must be positive")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    archive = args.archive.expanduser().resolve()
    output = args.output.expanduser().resolve()
    checkpoint = args.checkpoint.expanduser().resolve()
    summary_path = args.summary.expanduser().resolve()
    smdr_root = Path(args.smdr_root).expanduser().resolve()
    if not archive.is_file():
        parser.error(f"archive not found: {archive}")
    if output.exists() and not args.resume:
        parser.error(f"output exists; use --resume or choose another path: {output}")

    source = _load_archive(archive)
    source_cases = list(source["cases"])
    source_hash = _sha256(archive)
    requested = set(args.case_id)
    if requested:
        unknown = requested - {str(case["case_id"]) for case in source_cases}
        if unknown:
            parser.error(f"unknown case id(s): {sorted(unknown)}")
        selected = [case for case in source_cases if str(case["case_id"]) in requested]
    else:
        selected = source_cases
    if args.limit is not None:
        selected = selected[: args.limit]

    records = _read_records(output) if args.resume else {}
    selected_ids = {str(case["case_id"]) for case in selected}
    records = {case_id: record for case_id, record in records.items() if case_id in selected_ids}
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "at" if args.resume and output.exists() else "wt"
    started = time.monotonic()
    replay_payloads: list[dict[str, Any]] = []
    with gzip.open(output, mode, encoding="utf-8") as handle:
        if not args.resume:
            for index, case in enumerate(selected):
                record = _source_record(index, case)
                if record is not None:
                    _write_record(handle, record)
                    records[record["case_id"]] = record
        for index, case in enumerate(selected):
            case_id = str(case["case_id"])
            if case_id in records:
                continue
            if _source_record(index, case) is not None:
                continue
            replay_payloads.append(
                {
                    "case_index": index,
                    "case_id": case_id,
                    "source_status": case.get("status"),
                    "ew_state": case["ew_state"],
                    "evaluation_scale_gev": (case.get("electroweak_observables") or {}).get("evaluation_scale_gev", 246.21965),
                    "smdr_root": str(smdr_root),
                    "timeout_seconds": args.timeout_seconds,
                }
            )

        _write_checkpoint(
            checkpoint,
            status="RUNNING",
            source_archive_sha256=source_hash,
            output_path=output,
            expected_count=len(selected),
            records=records,
            workers=args.workers,
        )
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(_replay_worker, payload) for payload in replay_payloads]
            for completed_index, future in enumerate(as_completed(futures), start=1):
                record = future.result()
                _write_record(handle, record)
                records[str(record["case_id"])] = record
                if completed_index % args.checkpoint_every == 0:
                    _write_checkpoint(
                        checkpoint,
                        status="RUNNING",
                        source_archive_sha256=source_hash,
                        output_path=output,
                        expected_count=len(selected),
                        records=records,
                        workers=args.workers,
                    )

    status_counts: dict[str, int] = {}
    for record in records.values():
        status = str(record.get("replay_status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1
    complete = len(records) == len(selected)
    _write_checkpoint(
        checkpoint,
        status="COMPLETE" if complete else "PARTIAL",
        source_archive_sha256=source_hash,
        output_path=output,
        expected_count=len(selected),
        records=records,
        workers=args.workers,
    )
    summary = {
        "campaign_id": "smdr-full-batch-replay-2026-11-15",
        "bridge_version": SMDR_BRIDGE_VERSION,
        "execution_status": "COMPLETE" if complete else "PARTIAL",
        "source_archive": str(archive),
        "source_archive_sha256": source_hash,
        "source_case_count": len(source_cases),
        "selected_case_count": len(selected),
        "replay_submitted_count": len(replay_payloads),
        "processed_count": len(records),
        "status_counts": status_counts,
        "elapsed_seconds": time.monotonic() - started,
        "workers": args.workers,
        "resume": args.resume,
        "limit": args.limit,
        "explicit_case_ids": list(args.case_id),
        "output": str(output),
        "checkpoint": str(checkpoint),
        "controls": {
            "all_selected_cases_retained": True,
            "archive_order_preserved_in_source_index": True,
            "target_blind_generation": True,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "resume_supported": True,
        },
        "interpretation": "SMDR per-state backend replay only; no candidate is promoted by this campaign.",
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"summary_path={summary_path}")
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
