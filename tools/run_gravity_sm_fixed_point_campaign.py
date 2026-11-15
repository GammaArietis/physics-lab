"""Run the W9 gravity-dressed Standard Model fixed-point campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.gravity_sm_fixed_point_rg import (
    run_gravity_sm_fixed_point_campaign,
    write_gravity_sm_fixed_point_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation_path = root / "schemas/examples/gravity_sm_fixed_point_rg_activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    if activation["status"] != "AUTHORIZED" or activation["human_confirmation"] is not True:
        raise RuntimeError("the W9 campaign requires an explicit authorized activation")

    report = run_gravity_sm_fixed_point_campaign(
        f_g_values=activation["f_g_values"],
        f_y_values=activation["f_y_values"],
        f_lambda_values=activation["f_lambda_values"],
        initial_states=activation["initial_states"],
        log_scale_offsets=activation["log_scale_offsets"],
    )
    report["activation_id"] = activation["activation_id"]
    report["activation_path"] = str(activation_path.relative_to(root))
    output = root / "docs/validation/gravity_sm_fixed_point_rg_campaign_2026-11-15.json"
    write_gravity_sm_fixed_point_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
