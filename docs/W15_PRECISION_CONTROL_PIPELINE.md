# W15 — Gauge–Yukawa precision-control pipeline

## Scope

W15 closes the next computational gate for the extension

\[
  SU(3)_c\times SU(2)_L\times U(1)_Y
  + S + \text{vector-like Dirac multiplets},
\]

where `S` is a real singlet and the vector-like fermions are introduced in
anomaly-free Dirac pairs. The activation is target-blind: it contains only
declared theoretical seeds, representations, thresholds and couplings. It
does not contain measured masses as fit targets.

The executable chain is:

`activation → action/representations → fixed points → critical exponents →
piecewise UV→IR running → stability/perturbativity observables`

Pole matching through SMDR is deliberately a separate gate and is not run by
this campaign.

## What is implemented

* the standard two-loop Standard Model gauge matrix;
* representation-derived vector-like contributions to the gauge two-loop
  control, with the registered GUT normalization for `U(1)_Y`;
* the W13 reduced Yukawa–scalar matter block at one loop;
* explicit vector-like thresholds and piecewise running;
* target-blind numerical fixed-point search from the declared seed set;
* numerical Jacobian eigenvalues (critical exponents) at every retained fixed
  point;
* vacuum-stability inequalities for the Higgs, singlet and portal quartics;
* perturbativity checks and retention of every candidate without ranking or
  selection.

The campaign result is four `COMPLETE` trajectories and one
`ZERO_PROTECTED` gauge control. The latter is expected: perturbative gauge
beta functions are multiplicative in the gauge coupling, so an exactly zero
gauge seed remains zero unless an additive interaction is introduced.

## Deliberate boundaries

This is not yet a full two-loop BSM calculation. In particular:

* new-sector Yukawa terms in the two-loop gauge beta functions are not
  activated;
* Yukawa, Higgs-quartic, singlet-quartic and portal beta functions use the
  registered reduced one-loop control;
* finite threshold corrections are not claimed;
* `MS\bar` running-to-pole conversion and the `W`, `Z`, top and Higgs pole
  observables are deferred to the external SMDR backend;
* “all fixed points” means all roots found from the declared numerical seed
  set, not a mathematical proof that no root exists outside that search
  domain.

Consequently the report is a reproducible control and screening artifact,
not evidence that the extension reproduces measured Standard Model data or
that it supplies an asymptotically safe UV completion.

## Literature anchors

The two-loop SM gauge/RGE normalization is anchored to the general
renormalization-group literature, including:

* [Luo and Xiao, *Two-loop Renormalization Group Equations in the Standard Model*](https://arxiv.org/abs/hep-ph/0207271)
* [Machacek and Vaughn, general two-loop renormalization-group equations](https://doi.org/10.1016/0550-3213(84)90547-0)
* [Litim and Sannino, *Asymptotic safety guaranteed*](https://arxiv.org/abs/1406.2337)
* [Mann et al., *Asymptotically Safe Standard Model via Vector-Like Fermions*](https://arxiv.org/abs/1707.02942)
* [Martin and Robertson, *Standard Model parameters in the light of two-loop corrections* / SMDR](https://arxiv.org/abs/1907.02500)

These references motivate the model class and normalization. They do not
turn the present reduced implementation into a reproduction of every
published multi-loop result; that distinction is recorded in the activation,
code controls and validation report.
