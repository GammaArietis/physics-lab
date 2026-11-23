"""Run the W19 one-loop OS/MSbar mixed BSM pole-sector closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.gauge_yukawa_bsm_on_shell import run_on_shell_campaign, write_on_shell_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--w17-report",
        type=Path,
        default=root / "docs/validation/gauge_yukawa_bsm_threshold_matching_2026-11-16.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "docs/validation/gauge_yukawa_bsm_on_shell_2026-11-23.json",
    )
    parser.add_argument("--scale-gev", type=float, default=91.1876)
    parser.add_argument("--vev-gev", type=float, default=246.21965)
    args = parser.parse_args()
    report = run_on_shell_campaign(
        json.loads(args.w17_report.read_text(encoding="utf-8")),
        scale_gev=args.scale_gev,
        vev_gev=args.vev_gev,
    )
    destination = write_on_shell_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    try:
        display_path = destination.resolve().relative_to(root)
    except ValueError:
        display_path = destination.resolve()
    print(f"report_path={display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
