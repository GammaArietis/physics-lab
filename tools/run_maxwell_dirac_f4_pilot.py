"""Run the structural Maxwell–Dirac F^4 pilot."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.registry.maxwell_dirac_f4_pipeline import run_maxwell_dirac_f4_pipeline, write_maxwell_dirac_f4_report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation = json.loads(
        (root / "schemas/examples/maxwell_dirac_f4_activation.json").read_text(encoding="utf-8")
    )
    report = run_maxwell_dirac_f4_pipeline(
        candidate_path=root / activation["candidate_path"],
    )
    output = root / "docs" / "validation" / "maxwell_dirac_f4_pilot_2026-11-14.json"
    write_maxwell_dirac_f4_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
