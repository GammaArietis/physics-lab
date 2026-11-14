"""Run the bounded abstract-dimension scan around the Wyler construction."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search import run_wyler_dimension_scan, write_wyler_dimension_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation = json.loads(
        (root / "schemas/examples/wyler_dimension_scan_activation.json").read_text(encoding="utf-8")
    )
    report = run_wyler_dimension_scan(
        target_alpha_inverse=float(activation["target"]["alpha_inverse"]),
        dimensions=activation["dimensions"]["abstract_domain_dimensions"],
    )
    output = root / "docs" / "validation" / "wyler_dimension_scan_2026-11-14.json"
    write_wyler_dimension_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
