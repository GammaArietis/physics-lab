"""Execute the bounded stage-0 alpha-geometry search pilot."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search import run_alpha_geometry_pilot, write_alpha_geometry_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = run_alpha_geometry_pilot()
    output = root / "docs" / "validation" / "alpha_geometry_stage0_pilot_2026-11-14.json"
    write_alpha_geometry_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
