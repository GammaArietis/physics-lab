# Physics Model Laboratory

Python laboratory for exploring candidate structures of fundamental physics
while keeping derivation, assumption, calibration and experiment separate.

The project is not currently a completed theory. Its latest historical report
is the Phase 17 TIER 1 structural search with Phase 18A-18D used to catalogue
the missing dynamical formalization. A post-v23 Phase 18E closure audit is
stored in the repository, but it did not select a theory or activate a search.

Read [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) for the synchronized
state, [`docs/AUDIT_BASELINE_2026-11-13.md`](docs/AUDIT_BASELINE_2026-11-13.md)
for the audit findings, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for
the repository map.
The cleanup also found one historical v23 PDF hash mismatch documented in
[`docs/INTEGRITY_AUDIT.md`](docs/INTEGRITY_AUDIT.md).

The program does **not** try to prove a theory.  It does **not** fit
parameters to experiment unless you say so explicitly.  It exists to
answer one question, over and over:

> Does this result emerge from the structure, or did I insert it?

Typical workflow:

```
internal structure → quantum states → candidate mass / charge / interaction
```

That chain is treated as a **hypothesis to be tested**, not as an axiom.

---

## Scientific rules

Every quantity carries a **provenance**:

| Provenance     | Meaning                                              |
|----------------|------------------------------------------------------|
| `DERIVED`      | obtained mathematically from the model's assumptions |
| `ASSUMED`      | introduced explicitly as a hypothesis                |
| `CALIBRATED`   | chosen using an experimental datum                   |
| `INPUT`        | free parameter supplied by the user                  |
| `EXPERIMENTAL` | experimental datum used **only** in the final comparison |

Consequences, enforced in code:

* `EXPERIMENTAL` values cannot be read while a model is being solved.
* A number inserted as `INPUT` / `ASSUMED` / `CALIBRATED` can never be
  reclassified as `DERIVED`.
* If `q/e = 1/3` appears without `1/3` being a parameter, it may be
  reported as derived.  If you set `charge_fraction = 1/3`, the report
  says `NOT A PREDICTION`.
* Setting `alpha_inv = 137.036` produces a warning: alpha is **not** a
  prediction of the model.
* Reports never hide free parameters behind a lone float.  If
  `q_n = n * hbar * kappa / R`, that formula is printed, with `kappa`
  and `R` marked `[FREE]`.
* There is **no overall score**.  Each condition is `PASS`, `FAIL`,
  `UNTESTED`, `ASSUMED`, or `CALIBRATED`.

---

## Install

Python 3.11+ required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Or:

```bash
pip install -r requirements.txt
pip install -e .
```

---

## Command line

```bash
python -m physics_lab validate examples/circle.yaml
python -m physics_lab audit examples/circle.yaml
python -m physics_lab spectrum examples/circle.yaml

python -m physics_lab validate examples/c3.yaml
```

YAML is optional.  Any model can be built in Python:

```python
from physics_lab.models.examples.circle_model import build_circle_model
from physics_lab import validate

report = validate(build_circle_model(radius=1.0, kappa=1.0))
print(report.text)
```

---

## First model: the circle

Internal coordinate with identification

```
xi ~ xi + 2 pi R
```

Analytic eigenfunctions

```
chi_n(xi) = exp(i n xi / R),   n ∈ ℤ
```

and momentum

```
p_xi = -i ħ d/dξ
p_xi chi_n = (n ħ / R) chi_n          # DERIVED
```

Mass is **not** claimed as known physics:

```
m_n² = C * λ_n                        # ASSUMED
```

Charge from `Q = κ p_ξ`:

```
q_n = n ħ κ / R
q_n ∝ n                               # DERIVED
absolute normalization                # FREE (κ, R)
```

The laboratory will **not** insert `1/3` in order to obtain fractional
charges.  A separate test only inspects the spectrum after the fact.

---

## Second model: C3 potential

```
θ ~ θ + 2π
V(θ) = V0 (1 − cos(3θ))
```

Automatically reported:

```
C3 symmetry: DERIVED
Three sectors r = 0, 1, 2: DERIVED
Charge fractions 1/3: NOT YET DERIVED
```

`q = n/3` is a possibility to test, not a hard-coded conclusion.

---

## Tests

```bash
pytest
```

The suite checks periodicity, momentum eigenvalues, integer `n`, C3
sectors, massless/massive modes, provenance, the ban on labelling an
inserted parameter as `DERIVED`, and the wall between `EXPERIMENTAL`
and model derivation.

---

## Layout

```
src/physics_lab/
  core/          models, parameters and provenance firewall
  geometry/      geometric structures and symmetries
  dynamics/      Hamiltonian, Lagrangian and eigenproblem primitives
  physics/       physical constructions, phase engines and stored artifacts
  theory_kernel/ grammar, closure, enumeration and frontier phases
  models/        YAML loader and executable examples
  reporting/     reports and scorecards
  validation/    validation runners

tests/            automated tests
examples/         YAML inputs and model examples
docs/             current status, architecture and preserved history
```

Experimental constants live in `physics/constants.py` and are imported
only at comparison time.  Model files do not import them.

---

## What this MVP does not do

* No GUI, no machine learning, no automatic fitting of 1/137.
* No search over the space of models.
* Interference is implemented as a separate module and is not wired
  into the circle/C3 prototypes (`UNTESTED` on their scorecards).
* Alpha is compared only if a model actually produces `alpha`; the
  circle and C3 examples do not.

The point of the laboratory is to fail fast, preserve provenance and make
scientific uncertainty explicit.
