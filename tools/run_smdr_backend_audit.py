"""Audit the official SMDR backend and run one declared target-blind case."""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
from pathlib import Path

from physics_lab.search.smdr_backend import (
    SMDR_BRIDGE_VERSION,
    SMDRBackendError,
    run_smdr_calc_all,
    target_blind_input_text,
    write_smdr_report,
)


DECLARED_CASE_ID = "source-neighborhood-0357|transition=-2|loop=one-loop-sm|threshold=no-decoupling"


def _load_declared_case(root: Path) -> dict:
    archive = root / "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz"
    with gzip.open(archive, "rt", encoding="utf-8") as handle:
        report = json.load(handle)
    for case in report["cases"]:
        if case["case_id"] == DECLARED_CASE_ID:
            return case
    raise SMDRBackendError(f"declared case not found: {DECLARED_CASE_ID}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smdr-root", required=True, help="built official SMDR repository root")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    smdr_root = Path(args.smdr_root).expanduser().resolve()
    case = _load_declared_case(root)
    input_text = target_blind_input_text(case["ew_state"])

    git_sha = subprocess.run(
        ["git", "-C", str(smdr_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    reference = run_smdr_calc_all(smdr_root, timeout_seconds=args.timeout_seconds)
    target_blind = run_smdr_calc_all(
        smdr_root,
        input_text=input_text,
        timeout_seconds=args.timeout_seconds,
    )
    report = {
        "bridge_version": SMDR_BRIDGE_VERSION,
        "execution_status": "COMPLETE",
        "backend": {
            "repository": "https://github.com/davidgrobertson/SMDR",
            "git_sha": git_sha,
            "build": "validated externally with make smdr && make apps",
            "official_reference_smoke": reference,
        },
        "target_blind_case": {
            "case_id": DECLARED_CASE_ID,
            "source_report": "docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz",
            "input_convention": "g1_GUT_to_gp, lambda_SM=2*lambda_4, lower-family Yukawas=0, Delta_alpha_had_5=0",
            "result": target_blind,
        },
        "controls": {
            "official_backend_executed": True,
            "target_blind_input_executed": True,
            "reference_model_kept_separate": True,
            "experimental_comparison_performed": False,
            "fit_performed": False,
            "automatic_selection": False,
            "automatic_ranking": False,
        },
        "scope": {
            "full_sm_pole_and_eft_backend_available": True,
            "all_28692_physical_cases_replayed_through_smdr": False,
            "reason": "SMDR is an authoritative per-state backend; the bridge audit validates the executable and one declared target-blind state without treating a computational subsample as a selected physical result.",
        },
        "next_gate": "OPTIONAL_BATCH_SMDR_REPLAY_WITH_EXPLICIT_COMPUTE_BUDGET",
    }
    path = write_smdr_report(root / "docs/validation/smdr_backend_audit_2026-11-15.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"report_path={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
