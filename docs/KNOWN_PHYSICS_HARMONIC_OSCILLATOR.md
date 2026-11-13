# Known-physics quantum harmonic oscillator

This is the first concrete physical candidate registered after the laboratory
infrastructure pilots. It is a controlled reproduction of the one-dimensional
quantum harmonic oscillator, not a new theory claim and not an empirical test.

## Evidence

- Candidate record: [`theory_candidate_quantum_harmonic_oscillator.json`](../schemas/examples/theory_candidate_quantum_harmonic_oscillator.json)
- Model: [`harmonic_oscillator_model.py`](../src/physics_lab/models/examples/harmonic_oscillator_model.py)
- Pipeline: [`harmonic_oscillator_pipeline.py`](../src/physics_lab/registry/harmonic_oscillator_pipeline.py)
- Regression tests: [`test_harmonic_oscillator_pipeline.py`](../tests/test_harmonic_oscillator_pipeline.py)
- Manifest: [`campaign_manifest_harmonic_oscillator_baseline.json`](../schemas/examples/campaign_manifest_harmonic_oscillator_baseline.json)
- Completed activation: [`campaign_activation_harmonic_oscillator_completed.json`](../schemas/examples/campaign_activation_harmonic_oscillator_completed.json)
- Campaign report: [`campaign_report.json`](validation/campaign_reports/harmonic-oscillator-baseline/campaign_report.json)
- Checkpoint: [`harmonic-oscillator-baseline.json`](validation/campaign_checkpoints/harmonic-oscillator-baseline.json)
- Analysis record: [`HARMONIC_OSCILLATOR_BASELINE_ANALYSIS_2026-11-13.json`](validation/HARMONIC_OSCILLATOR_BASELINE_ANALYSIS_2026-11-13.json)

## Closed internal chain

The registered action is

```text
S = integral dt [m*xdot^2/2 - m*omega^2*x^2/2]
```

The executable derivation checks the following chain:

```text
action
  -> Euler-Lagrange equation: m*(xddot + omega^2*x) = 0
  -> canonical momentum: p = m*xdot
  -> Legendre transform: H = p^2/(2*m) + m*omega^2*x^2/2
  -> canonical quantization: [x,p] = i*hbar
  -> exact spectrum: E_n = hbar*omega*(n + 1/2), n in N_0
  -> vacuum: n=0, global minimum of the exact spectrum
  -> gap ratio: (E_n-E_0)/(E_1-E_0) = n
```

The displayed levels `n = 0,...,4` are only a report window. The analytic
spectrum is defined for all non-negative integer `n`; the display cutoff is
not a search bound.

## What passed

The single-candidate campaign completed with an unchanged candidate record and
all eight model checks true:

- Euler-Lagrange equation;
- Legendre transform;
- canonical commutator declaration;
- spectrum formula;
- ground-state vacuum selection;
- positive excitation gaps;
- equal level spacing;
- parameter-free gap ratio.

The report contains 15 derived observable rows for the display window: five
energy levels, five gaps and five dimensionless gap ratios. The ratio has no
free dependencies, while the dimensionful energies retain the explicit
`hbar` and `omega` inputs as they should.

## Scope and non-claims

The candidate keeps `m`, `omega` and `hbar` as explicit positive inputs. No
experimental value enters the derivation, no parameter is fitted or updated,
and no search or ranking is active. This is quantum mechanics, not field
quantization; `field_quantization_status` is therefore `NOT_APPLICABLE`.

The internal result is `COMPLETE` and is sufficient to open the next controlled
baseline, the free scalar field. It is not yet an empirical validation: the
comparison gate remains closed until a separate immutable dataset and an
explicit target-blind authorization are registered.

## Reproduce

```bash
PYTHONPATH=src uv run --with pytest python -m pytest -q tests/test_harmonic_oscillator_pipeline.py
PYTHONPATH=src uv run python - <<'PY'
from physics_lab.registry import run_harmonic_oscillator_pipeline
report = run_harmonic_oscillator_pipeline(
    candidate_path="schemas/examples/theory_candidate_quantum_harmonic_oscillator.json"
)
assert report["pipeline_status"] == "COMPLETE"
assert all(report["checks"].values())
print(report["derivation"]["gap_ratio"])
PY
```
