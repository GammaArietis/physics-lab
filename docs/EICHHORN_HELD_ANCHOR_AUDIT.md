# Eichhorn--Held fixed-point anchor audit

## Purpose

The W11 reproduction initially implemented the final printed
Einstein--Hilbert gravity--matter equations and found a direct numerical
mismatch: the final paper quotes

\[
(G_N^*,\Lambda^*)=(3.29,-4.51),
\]

but the first laboratory transcription produced a different non-Gaussian
zero. This document records the broader audit and the correction.

## What was tested

The audit evaluates, without fitting or selecting:

1. the arXiv v1/v2 gravitational equations and their quoted
   \((4.1,-9.9)\) anchor;
2. the final arXiv v3 equations and their quoted \((3.29,-4.51)\) anchor;
3. the source field counts \((N_S,N_V,N_W)=(4,12,45)\);
4. a pre-registered 27-case diagnostic grid covering scalar, vector and
   fermion bookkeeping alternatives;
5. all distinct roots found from a fixed, declared seed set, including the
   Gaussian branch.

The count grid is not a search for the nearest published number. Every case,
residual and root is retained in the machine-readable report.

## Results

For the exact source counts:

| Source equations | Quoted anchor | Residual at quoted anchor | Root obtained from printed equations |
|---|---:|---:|---:|
| arXiv v1/v2 | \((4.1,-9.9)\) | \((-0.11277453,\;0.32810074)\) | \((4.04205888,-9.74596892)\) |
| arXiv v3 final | \((3.29,-4.51)\) | \((0.00874978,\;-0.00309505)\) | \((3.29450944,-4.51398683)\) |

The v1/v2 anchor is numerically close to a root of its own printed system,
although the rounded pair is not an exact zero. For v3, the exact root rounds
to the published anchor at two decimal places. The final discrepancy was
therefore not a literature inconsistency.

The important source-level fact is that v1/v2 and v3 are materially different
systems. In the final version, the matter-counting structure in the
\(\beta_\Lambda\) bracket and the sign/constant terms in \(f_{G_N}\) change,
and the quoted anchor changes at the same time. Therefore the v3 number cannot
be validated by silently applying the v1/v2 equations, nor can the v1/v2
equations be treated as an earlier rounding of v3.

## Interpretation

The immediate discrepancy is resolved as a laboratory transcription error.
The v3 source equation is

\[
7-\frac{3}{2(3-4\Lambda)},
\]

where the first implementation had incorrectly encoded

\[
\frac{3}{7-2(3-4\Lambda)}.
\]

After correction, the exact root is
\((3.2945094357,-4.5139868308)\), which is the quoted \((3.29,-4.51)\)
at the displayed precision. No field count, regulator parameter or physical
target was changed. The version comparison remains useful as provenance: v1/v2
and v3 are materially different source submissions and must remain separately
audited.

No value of \(\alpha\), measured mass, or empirical dataset entered this
audit. No root was promoted, ranked or selected.

## Reproduction

```bash
export PYTHONPATH="$PWD/src"
pytest -q tests/test_eichhorn_held_anchor_audit.py
python tools/run_eichhorn_held_anchor_audit.py
```

Machine-readable result:
`docs/validation/eichhorn_held_anchor_audit_2026-11-15.json`.

## Primary bibliography

- A. Eichhorn and A. Held, *Top mass from asymptotic safety*,
  arXiv:1707.01107, versions v1, v2 and v3; Phys. Lett. B 777, 217--221
  (2018), DOI [10.1016/j.physletb.2017.12.040](https://doi.org/10.1016/j.physletb.2017.12.040).
- M. Donà, A. Eichhorn and R. Percacci, *Matter matters in asymptotically
  safe quantum gravity*, Phys. Rev. D 89, 084035 (2014), DOI
  [10.1103/PhysRevD.89.084035](https://doi.org/10.1103/PhysRevD.89.084035).
- A. Eichhorn and S. Lippoldt, *Quantum gravity and Standard-Model-like
  fermions*, Phys. Lett. B 767, 142--146 (2017), DOI
  [10.1016/j.physletb.2017.01.064](https://doi.org/10.1016/j.physletb.2017.01.064).
