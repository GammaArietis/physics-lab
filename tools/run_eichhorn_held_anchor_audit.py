"""Run and archive the versioned Eichhorn--Held anchor audit."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.eichhorn_held_anchor_audit import (
    run_anchor_audit,
    write_anchor_audit_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = run_anchor_audit()
    path = write_anchor_audit_report(
        root / "docs/validation/eichhorn_held_anchor_audit_2026-11-15.json",
        report,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
