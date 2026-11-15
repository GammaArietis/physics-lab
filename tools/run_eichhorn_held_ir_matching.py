"""Run and archive the target-blind Eichhorn--Held UV-to-IR campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.eichhorn_held_ir_matching import (
    run_ir_matching_campaign,
    write_ir_matching_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = run_ir_matching_campaign()
    path = write_ir_matching_report(
        root / "docs/validation/eichhorn_held_ir_matching_campaign_2026-11-15.json",
        report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
