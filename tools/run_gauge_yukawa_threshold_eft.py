"""Run the W14 target-blind threshold-resolved gauge--Yukawa EFT campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.gauge_yukawa_threshold_eft import run_threshold_campaign, write_threshold_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--activation", type=Path, default=root / "schemas/examples/gauge_yukawa_threshold_eft_activation.json")
    parser.add_argument("--output", type=Path, default=root / "docs/validation/gauge_yukawa_threshold_eft_2026-11-16.json")
    args = parser.parse_args()
    activation = json.loads(args.activation.read_text(encoding="utf-8"))
    report = run_threshold_campaign(activation)
    destination = write_threshold_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={destination.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
