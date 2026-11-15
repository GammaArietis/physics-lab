"""Run the literature-anchored coupled gauge-Yukawa/Abelian RG campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.gauge_yukawa_em_rg import (
    run_gauge_yukawa_em_campaign,
    write_gauge_yukawa_em_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation_path = root / "schemas/examples/gauge_yukawa_em_rg_activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    if activation["status"] != "AUTHORIZED" or activation["human_confirmation"] is not True:
        raise RuntimeError("the coupled RG campaign requires an explicit authorized activation")

    report = run_gauge_yukawa_em_campaign(
        epsilon_values=activation["epsilon_values"],
        alpha_em_values=activation["alpha_em_values"],
        log_scale_offsets=activation["log_scale_offsets"],
    )
    report["activation_id"] = activation["activation_id"]
    report["activation_path"] = str(activation_path.relative_to(root))
    output = root / "docs/validation/gauge_yukawa_em_rg_campaign_2026-11-15.json"
    write_gauge_yukawa_em_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
