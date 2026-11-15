"""Run and archive the W10 correlated gravity--matter campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.gravity_matter_single_truncation_rg import (
    run_gravity_matter_single_truncation_campaign,
    write_gravity_matter_single_truncation_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = run_gravity_matter_single_truncation_campaign()
    path = write_gravity_matter_single_truncation_report(
        root / "docs/validation/gravity_matter_single_truncation_rg_campaign_2026-11-15.json",
        report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
