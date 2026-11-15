"""Run and archive the Eichhorn--Held full gravity--matter reproduction."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.eichhorn_held_asymptotic_safety import (
    run_eichhorn_held_campaign,
    write_eichhorn_held_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = run_eichhorn_held_campaign()
    path = write_eichhorn_held_report(
        root / "docs/validation/eichhorn_held_asymptotic_safety_campaign_2026-11-15.json",
        report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
