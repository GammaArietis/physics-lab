"""Run the bounded fourteen-candidate known-physics campaign."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.registry import run_multi_candidate_campaign, write_completed_activation


ACTIVATION_RELATIVE_PATH = "schemas/examples/campaign_activation_known_physics_fourteen.json"
COMPLETED_ACTIVATION_RELATIVE_PATH = "schemas/examples/campaign_activation_known_physics_fourteen_completed.json"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    activation = json.loads((root / ACTIVATION_RELATIVE_PATH).read_text(encoding="utf-8"))
    report = run_multi_candidate_campaign(activation=activation, repository_root=root)
    print(json.dumps(report, indent=2, sort_keys=True))
    write_completed_activation(root / COMPLETED_ACTIVATION_RELATIVE_PATH, activation, report)
    return 0 if report["execution_status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
