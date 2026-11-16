"""Run the target-blind W11 IR/EFT rescue audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from physics_lab.search.w11_ir_eft_rescue import run_ir_eft_rescue_campaign, write_ir_eft_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz",
    )
    parser.add_argument("--full-output", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = run_ir_eft_rescue_campaign(archive_path=args.archive)
    summary = dict(report)
    records = summary.pop("records")
    summary["record_preview"] = records[:3]
    summary_path = write_ir_eft_report(
        root / "docs/validation/w11_ir_eft_rescue_audit_2026-11-16_summary.json",
        summary,
    )
    if args.full_output:
        full_path = write_ir_eft_report(
            root / "docs/validation/w11_ir_eft_rescue_audit_2026-11-16.json.gz",
            report,
            gzip_full=True,
        )
        print(f"full_report_path={full_path.relative_to(root)}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"summary_path={summary_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
