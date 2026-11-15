"""Run the W8 Standard Model, gravity and U(1)-mixing broad campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.sm_gravity_mixing_rg import (
    run_sm_gravity_mixing_campaign,
    write_sm_gravity_mixing_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation_path = root / "schemas/examples/sm_gravity_mixing_rg_activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    if activation["status"] != "AUTHORIZED" or activation["human_confirmation"] is not True:
        raise RuntimeError("the W8 campaign requires an explicit authorized activation")

    report = run_sm_gravity_mixing_campaign(
        sm_initial_states=activation["sm_initial_states"],
        gravity_coefficients=activation["gravity_coefficients"],
        gravity_initial_g1_values=activation["gravity_initial_g1_values"],
        mixing_matrices=activation["mixing_matrices"],
        mixing_initial_states=activation["mixing_initial_states"],
        log_scale_offsets=activation["log_scale_offsets"],
    )
    report["activation_id"] = activation["activation_id"]
    report["activation_path"] = str(activation_path.relative_to(root))
    output = root / "docs/validation/sm_gravity_mixing_rg_campaign_2026-11-15.json"
    write_sm_gravity_mixing_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
