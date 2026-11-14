# Known-physics free real scalar field

This is the second controlled known-physics baseline, opened only after the
quantum harmonic oscillator and the historical test-isolation gate were closed.
It is a free real Klein-Gordon field on a `1+1`-dimensional periodic cylinder,
not yet a claim about the full interacting Standard Model or about higher-
dimensional phenomenology.

## Evidence

- Candidate record: [`theory_candidate_free_scalar_field.json`](../schemas/examples/theory_candidate_free_scalar_field.json)
- Model: [`free_scalar_field_model.py`](../src/physics_lab/models/examples/free_scalar_field_model.py)
- Pipeline: [`free_scalar_field_pipeline.py`](../src/physics_lab/registry/free_scalar_field_pipeline.py)
- Regression tests: [`test_free_scalar_field_pipeline.py`](../tests/test_free_scalar_field_pipeline.py)
- Test-isolation fixture: [`conftest.py`](../tests/conftest.py)
- Completed activation: [`campaign_activation_free_scalar_field_completed.json`](../schemas/examples/campaign_activation_free_scalar_field_completed.json)
- Campaign report: [`campaign_report.json`](validation/campaign_reports/free-scalar-field-baseline/campaign_report.json)
- Checkpoint: [`free-scalar-field-baseline.json`](validation/campaign_checkpoints/free-scalar-field-baseline.json)
- Analysis record: [`FREE_SCALAR_FIELD_BASELINE_ANALYSIS_2026-11-14.json`](validation/FREE_SCALAR_FIELD_BASELINE_ANALYSIS_2026-11-14.json)

## Closed internal chain

The action is

```text
S = integral dt dx [phidot^2/2 - (dphidx)^2/2 - mu^2*phi^2/2]
```

The executable derivation checks:

```text
action
  -> Klein-Gordon equation: (d_t^2 - d_x^2 + mu^2) phi = 0
  -> canonical momentum: pi = d_t phi
  -> Hamiltonian density: [pi^2 + (dphidx)^2 + mu^2*phi^2]/2
  -> field quantization: [phi(t,x),pi(t,y)] = i*hbar*delta(x-y)
  -> periodic modes: k_n = 2*pi*n/L
  -> dispersion: omega_n^2 = mu^2 + k_n^2
  -> Fock vacuum: all occupations n_k = 0
  -> ratio: (omega_n^2-omega_0^2)/(omega_1^2-omega_0^2) = n^2
```

The report displays non-negative modes `n = 0,...,4`; this is a report window,
not a search bound. Negative Fourier modes have the same frequency and are
related by the reality condition of the field.

## What passed

The authorized one-candidate pilot completed with an unchanged candidate record
and all nine model checks true: Euler-Lagrange equation, Legendre transform,
periodic mode basis, canonical field commutator, dispersion relation, positive
frequencies, Fock-vacuum ground-state condition, normal-ordered vacuum energy
and parameter-free dispersion ratio.

The field-quantization boundary is explicit. The normal-ordered Fock vacuum is
assigned energy zero, while the unnormal-ordered continuum zero-point sum is
not assigned a finite value. This prevents a finite display window from being
mistaken for a renormalized vacuum-energy calculation.

## Scope and non-claims

`mu`, `L` and `hbar` remain explicit positive inputs. No experimental datum,
fit, calibration, parameter update, selection or ranking enters the baseline.
The result is an internal mathematical reproduction and is not empirical
validation. A real comparison dataset and target-blind authorization remain
separate future gates. Higher-dimensional extension, stress-energy
renormalization and interactions are open questions, not silently assumed.

## Reproduce

```bash
PYTHONPATH=src uv run --with pytest python -m pytest -q tests/test_free_scalar_field_pipeline.py
PYTHONPATH=src uv run python - <<'PY'
from physics_lab.registry import run_free_scalar_field_pipeline
report = run_free_scalar_field_pipeline(
    candidate_path="schemas/examples/theory_candidate_free_scalar_field.json"
)
assert report["pipeline_status"] == "COMPLETE"
assert all(report["checks"].values())
print(report["derivation"]["parameter_free_ratio"])
PY
```
