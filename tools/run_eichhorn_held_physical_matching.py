"""Run and archive the dimensionful Eichhorn--Held matching campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.eichhorn_held_physical_matching import (
    run_physical_matching_campaign,
    write_physical_matching_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-neighborhood", action="store_true")
    parser.add_argument("--steps-per-unit", type=int, default=6)
    parser.add_argument("--no-experimental-comparison", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = run_physical_matching_campaign(
        include_neighborhood=args.include_neighborhood,
        compare_experiment=not args.no_experimental_comparison,
        steps_per_unit=args.steps_per_unit,
    )
    summary = dict(report)
    summary.pop("cases", None)
    compact_preview = []
    for case in report["cases"][:3]:
        preview = dict(case)
        preview.pop("ew_points", None)
        preview.pop("low_probe_points", None)
        compact_preview.append(preview)
    summary["case_preview"] = compact_preview
    comparison = dict(report["experimental_comparison"])
    comparisons = comparison.pop("comparisons", [])
    comparison["comparison_summary"] = {}
    for field in ("top_pull_using_control_conversion", "higgs_pull_using_tree_control"):
        values = [item[field] for item in comparisons if item.get(field) is not None]
        comparison["comparison_summary"][field] = {
            "count": len(comparisons),
            "finite_count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "mean": sum(values) / len(values) if values else None,
        }
    summary["experimental_comparison"] = comparison
    summary_path = write_physical_matching_report(
        root / "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_summary.json",
        summary,
    )
    archive_path = write_physical_matching_report(
        root / "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15.json.gz",
        report,
        gzip_full=True,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"summary_path={summary_path.relative_to(root)}")
    print(f"archive_path={archive_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
