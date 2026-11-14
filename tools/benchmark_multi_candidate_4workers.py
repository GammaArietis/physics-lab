#!/usr/bin/env python3
"""Run a disposable four-worker multi-candidate resource benchmark.

The benchmark creates four explicit variants of the internal circle reference
candidate in a temporary repository root. It exercises the real campaign
runner with macOS-compatible ``spawn`` workers, while leaving the repository's
historical checkpoints and reports untouched.
"""

from __future__ import annotations

import copy
import argparse
from collections import Counter
import json
import os
import resource
import tempfile
import time
from pathlib import Path
from typing import Any

from physics_lab.registry import (
    load_campaign_activation,
    load_campaign_manifest,
    load_theory_candidate,
    run_multi_candidate_campaign,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "schemas/examples/campaign_manifest_multi_candidate_pilot.json"
ACTIVATION_PATH = ROOT / "schemas/examples/campaign_activation_pilot.json"
CANDIDATE_PATH = ROOT / "schemas/examples/theory_candidate_circle_reference.json"
def _max_rss_bytes() -> int:
    """Return the current process maximum RSS in bytes on macOS and Linux."""
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if os.uname().sysname == "Darwin" else value * 1024


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=4,
        help="number of disposable candidate variants to execute (default: 4)",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=4,
        help="number of concurrent candidate workers (default: 4)",
    )
    arguments = parser.parse_args()
    if arguments.candidate_count < 2:
        parser.error("--candidate-count must be at least 2")
    if arguments.parallelism < 1 or arguments.parallelism > arguments.candidate_count:
        parser.error("--parallelism must be between 1 and --candidate-count")
    return arguments


def main() -> int:
    arguments = _arguments()
    manifest = load_campaign_manifest(MANIFEST_PATH)
    base_candidate = load_theory_candidate(CANDIDATE_PATH)
    radii = tuple(float(index) for index in range(1, arguments.candidate_count + 1))

    with tempfile.TemporaryDirectory(prefix="physics-lab-4worker-") as temporary_root:
        root = Path(temporary_root)
        refs: list[dict[str, Any]] = []
        for index, radius in enumerate(radii, start=1):
            candidate = copy.deepcopy(base_candidate)
            candidate_id = f"circle-reference-m4-r{index}"
            candidate["candidate_id"] = candidate_id
            candidate["title"] = f"Disposable four-worker radius-{radius:g} benchmark variant"
            candidate["registration"]["decision_ref"] = f"m4-four-worker-r{index}"
            for parameter in candidate["parameters"]:
                if parameter["id"] == "radius":
                    parameter["value"] = radius
            record_path = f"candidate-{index}.json"
            _write_json(root / record_path, candidate)
            refs.append(
                {
                    "candidate_id": candidate_id,
                    "record_path": record_path,
                    "expected_selected": False,
                    "expected_registration_status": "READY_FOR_DERIVATION",
                }
            )

        manifest["candidate_refs"] = refs
        manifest["execution"]["max_candidates"] = arguments.candidate_count
        manifest["execution"]["parallelism"] = arguments.parallelism
        manifest["execution"]["checkpoint_path"] = "checkpoint.json"
        manifest["execution"]["report_directory"] = "reports"
        manifest["execution"]["resume"] = True
        manifest["failure_policy"]["max_failures"] = 0
        _write_json(root / "manifest.json", manifest)

        activation = load_campaign_activation(ACTIVATION_PATH)
        activation["activation_id"] = (
            f"mac-{arguments.candidate_count}-candidate-"
            f"{arguments.parallelism}-worker-resource-benchmark"
        )
        activation["campaign_id"] = manifest["campaign_id"]
        activation["manifest_path"] = "manifest.json"
        activation["checkpoint_path"] = "checkpoint.json"

        started = time.perf_counter()
        report = run_multi_candidate_campaign(
            activation=activation,
            repository_root=root,
        )
        elapsed = time.perf_counter() - started

    max_rss_bytes = _max_rss_bytes()
    summary = {
        "benchmark": "multi-candidate-resource-benchmark",
        "candidate_count": arguments.candidate_count,
        "parallelism": arguments.parallelism,
        "execution_status": report["execution_status"],
        "candidate_status_counts": dict(
            sorted(Counter(item["status"] for item in report["candidate_results"]).items())
        ),
        "elapsed_seconds": round(elapsed, 6),
        "max_rss_bytes_parent": max_rss_bytes,
        "max_rss_mib_parent": round(max_rss_bytes / (1024 * 1024), 3),
        "controls": report["controls"],
        "selection": report["selection"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["execution_status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
