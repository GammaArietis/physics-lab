"""Run the W16 W15-to-SMDR target-blind matching campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.gauge_yukawa_smdr_matching import (
    run_smdr_matching_campaign,
    write_smdr_matching_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--precision-report",
        type=Path,
        default=root / "docs/validation/gauge_yukawa_precision_pipeline_2026-11-16.json",
    )
    parser.add_argument("--smdr-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "docs/validation/gauge_yukawa_smdr_matching_2026-11-16.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--candidate-id", action="append", default=None)
    args = parser.parse_args()
    precision_report = json.loads(args.precision_report.read_text(encoding="utf-8"))
    report = run_smdr_matching_campaign(
        precision_report,
        smdr_root=args.smdr_root,
        timeout_seconds=args.timeout_seconds,
        candidate_ids=args.candidate_id,
    )
    destination = write_smdr_matching_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    try:
        display_path = destination.resolve().relative_to(root)
    except ValueError:
        display_path = destination.resolve()
    print(f"report_path={display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
