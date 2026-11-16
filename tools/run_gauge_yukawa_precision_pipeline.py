"""Run the W15 target-blind gauge--Yukawa precision-control campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.gauge_yukawa_precision_pipeline import run_precision_campaign, write_precision_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--activation", type=Path, default=root / "schemas/examples/gauge_yukawa_precision_activation.json")
    parser.add_argument("--output", type=Path, default=root / "docs/validation/gauge_yukawa_precision_pipeline_2026-11-16.json")
    args = parser.parse_args()
    activation = json.loads(args.activation.read_text(encoding="utf-8"))
    report = run_precision_campaign(activation)
    destination = write_precision_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={destination.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
