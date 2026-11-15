# SMDR backend closeout — 2026-11-15

## Decision

The SMDR integration gate is **CLOSED at the executable-backend level**.
The laboratory can now pass a target-blind MS-bar state from the W11
UV-to-IR matching campaign to the official SMDR executable and retain its
headline pole/EFT observables without fitting, ranking, or selecting a
candidate.

This does **not** claim that the W11 campaign has produced a physical model.
It closes the missing software/validation dependency identified in the
physical-matching report: full Higgs-pole, heavy-particle and low-energy
QCD+QED matching is delegated to the published SMDR implementation.

## Authority and build

- Repository: <https://github.com/davidgrobertson/SMDR>
- Version: SMDR v1.3
- Audited commit: `5c4dd92c918cadb7f91ad3795694f8398b5c287a`
- Build sequence: `make smdr && make apps`
- `calc_all` completed with exit code `0` using the official
  `ReferenceModel.dat`.

The top-level parallel build was not used for the audit because its
application targets can race the static-library target. The sequential
two-command build is the reproducible procedure recorded here.

## Two executions kept separate

### Official reference smoke test

This is only a backend smoke test. It uses SMDR's own `ReferenceModel.dat`,
which contains reference/experimental inputs. It is not part of target-blind
generation.

Parsed headline values:

| quantity | value |
|---|---:|
| SMDR version | 1.3 |
| top complex-pole mass | 172.400000 GeV |
| Higgs complex-pole mass | 125.200000 GeV |
| Z PDG-convention mass | 91.187600 GeV |
| W PDG-convention mass | 80.349183 GeV |
| Sommerfeld alpha inverse | 137.03599918 |
| Fermi constant coefficient | 1.16637820 |

The reference smoke test is evidence that the official executable was built
and can run; it is not a fit or a validation of the W11 candidate ensemble.

### Target-blind W11 case

The declared case is:

`source-neighborhood-0357|transition=-2|loop=one-loop-sm|threshold=no-decoupling`

The bridge converts the W11 conventions explicitly:

- `g1_GUT -> gp = sqrt(3/5) g1`;
- `lambda_SM = 2 lambda_4`;
- lower-family Yukawas set to zero as a declared neutral control;
- `Delta_alpha_had_5_MZ = 0`;
- no pole mass, alpha, or Fermi-constant target is supplied.

SMDR completed this target-blind input with exit code `0`, produced all
required headline observables, and returned:

| quantity | value |
|---|---:|
| top pole control | 48.190341 GeV |
| Higgs pole control | 45.791952 GeV |
| Z pole control | 3.486658 GeV |
| W pole control | 2.758371 GeV |
| Sommerfeld alpha inverse | 67215.03412391 |
| Fermi constant coefficient | 1.15995049 |

These values are intentionally not interpreted as a successful physical
prediction. They show that the candidate reaches the full external backend;
the large displacement from known low-energy values is a negative diagnostic
for this particular target-blind trajectory. SMDR warnings about small
couplings are retained verbatim in the JSON report.

The batch runner applies a stricter rule than the executable exit code alone:
if SMDR exits with code `0` but fails to print one of the six required headline
observables, the case is recorded as `BACKEND_FAILURE`. This occurred in the
smoke run for zero-coupling states and is deliberately not counted as a
successful observable evaluation.

## What is closed and what is not

Closed:

1. official SMDR source and commit are identified;
2. the official executable is built and run;
3. the W11-to-SMDR convention map is explicit and tested;
4. reference input and target-blind input are separated;
5. parsed results and raw output tails are recorded;
6. no automatic fitting, ranking, selection, or experimental comparison is
   performed by the bridge.

Not claimed:

- all 28,692 W11 configurations have not been replayed through SMDR;
- no candidate has been promoted;
- no claim of asymptotic safety, unification, or agreement with experiment is
  made;
- the W11 low-scale diagnostic still uses the stated truncation controls and
  is not a complete EFT replacement for every threshold schedule.

The complete 28,692-case replay remains an optional compute campaign. It is
deliberately not replaced by an unreported sample: a sample could bias the
record and would violate the laboratory's no-selection rule. The audit report
therefore records the exact remaining gate as
`OPTIONAL_BATCH_SMDR_REPLAY_WITH_EXPLICIT_COMPUTE_BUDGET`.

## Primary references

- SMDR repository and implementation: <https://github.com/davidgrobertson/SMDR>
- Martin and Robertson, *Standard Model parameters in the dimensional
  reduction scheme*, arXiv:1907.02500:
  <https://arxiv.org/abs/1907.02500>
- Eichhorn and Held, gravity contributions to Standard Model beta functions:
  <https://doi.org/10.1016/j.physletb.2017.12.040>

The machine-readable evidence is
`docs/validation/smdr_backend_audit_2026-11-15.json`.
