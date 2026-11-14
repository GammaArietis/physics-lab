# Bounded known-physics multi-candidate campaign

This campaign runs the two executable known-physics baselines already closed
internally by the laboratory:

- `known-physics-quantum-harmonic-oscillator`;
- `known-physics-free-real-scalar-field`.

It is a reproducibility and pipeline campaign, not a search over speculative
theories. It does not compare candidates with external data, fit parameters,
rank candidates, select a theory, activate finite bounds, or use the H₂
scope-control dataset.

The Mac resource benchmark with 64 controlled variants remains a separate
infrastructure result. It must not be interpreted as a 64-theory physical
campaign.

## Run on the Mac

From the repository root:

```bash
git pull --ff-only origin optimize/phase14l-14n
source .venv/bin/activate
export PYTHONPATH="$PWD/src"

python - <<'PY'
import json
from pathlib import Path

from physics_lab.registry import run_multi_candidate_campaign, write_completed_activation

root = Path.cwd()
activation_path = root / "schemas/examples/campaign_activation_known_physics_multi.json"
activation = json.loads(activation_path.read_text(encoding="utf-8"))

report = run_multi_candidate_campaign(
    activation=activation,
    repository_root=root,
)
print(json.dumps(report, indent=2, sort_keys=True))

write_completed_activation(
    root / "schemas/examples/campaign_activation_known_physics_multi_completed.json",
    activation,
    report,
)
PY
```

The expected first gate is:

- `execution_status: COMPLETE`;
- both candidates `PASS`;
- `record_unchanged: true` for both;
- all campaign controls true;
- `selection.performed: false`;
- `selection.ranking_performed: false`.

The execution writes only campaign evidence under:

- `docs/validation/campaign_checkpoints/known-physics-multi-baselines.json`;
- `docs/validation/campaign_reports/known-physics-multi-baselines/`.

After inspecting the JSON report, commit the generated evidence and the
completed activation record. Do not edit the original `NOT_RUN` activation
record: it is the immutable pre-execution authorization.
