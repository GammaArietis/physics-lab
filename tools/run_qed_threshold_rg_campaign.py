"""Run the broad target-blind one-loop QED threshold campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.search.qed_threshold_rg_campaign import (
    run_qed_threshold_rg_campaign,
    write_qed_threshold_rg_report,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation_path = root / "schemas/examples/qed_threshold_rg_campaign_activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8"))
    if activation["status"] != "AUTHORIZED" or activation["human_confirmation"] is not True:
        raise RuntimeError("the QED threshold campaign requires an explicit authorized activation")

    report = run_qed_threshold_rg_campaign(
        initial_alpha_values=activation["initial_alpha_values"],
        log_scale_offsets=activation["log_scale_offsets"],
        schedules=activation["threshold_schedules"],
        initial_fermion_flavours=activation["initial_fermion_flavours"],
    )
    report["activation_id"] = activation["activation_id"]
    report["activation_path"] = str(activation_path.relative_to(root))
    output = root / "docs/validation/qed_threshold_rg_campaign_2026-11-15.json"
    write_qed_threshold_rg_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"report_path={output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
