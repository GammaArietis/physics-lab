"""Run the explicitly authorized Wyler anchor and neighborhood pilot."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search import run_wyler_neighborhood_pilot, write_wyler_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation = json.loads(
        (root / "schemas/examples/wyler_neighborhood_activation.json").read_text(encoding="utf-8")
    )
    report = run_wyler_neighborhood_pilot(
        target_alpha_inverse=float(activation["target"]["alpha_inverse"])
    )
    output = root / "docs" / "validation" / "wyler_neighborhood_stage1_2026-11-14.json"
    write_wyler_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
