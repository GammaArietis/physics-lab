# W16 — Target-blind W15 → SMDR matching

## Purpose

W16 connects the W15 gauge–Yukawa precision-control output to the official
SMDR executable. It is a deliberately bounded projection, not a claim that
SMDR implements the complete BSM model.

The chain is:

`W15 UV→IR running → declared thresholds → convention map → target-blind SMDR input → pole observables`

The W15 state is

`(g1, g2, g3, yt, yS, lambda_h, lambda_s, lambda_hs)`.

The pure-SM SMDR call receives only the low-energy SM projection:

| W15 quantity | SMDR input | Rule |
|---|---|---|
| `g1` | `gp` | `gp = sqrt(3/5) g1` |
| `g2`, `g3`, `yt` | same | direct convention match |
| absent `yb` | `yb` | explicit neutral control `0` |
| `lambda_h` | `lambda_4` | `lambda_4 = lambda_h / 2` |
| `yS`, `lambda_s`, `lambda_hs` | none | recorded as omitted BSM sector |

No pole mass, coupling, fit target, hadronic correction, ranking, or automatic
selection is supplied. W15 thresholds are represented by the piecewise
low-energy state before SMDR is called. Finite BSM threshold corrections and
new-sector contributions to the SMDR self-energies are not included.

## Reproduced run

The archived report is
[`docs/validation/gauge_yukawa_smdr_matching_2026-11-16.json`](validation/gauge_yukawa_smdr_matching_2026-11-16.json).
It used the official SMDR repository at commit
`5c4dd92c918cadb7f91ad3795694f8398b5c287a` and `calc_all` from that build.
The run processed all five W15 candidates in source order:

* four candidates returned `SMDR_COMPLETE`;
* the exactly-zero-gauge control returned `BACKEND_FAILURE` after the
  declared timeout. This is retained as a per-candidate backend limitation,
  not silently removed from the campaign.

For the four successful projections, SMDR returned diagnostic pole outputs
around `Mt = 8.70 GeV`, `Mh = 24.26 GeV`, `MZ = 2.64 GeV`, `MW = 2.46 GeV`
and `1/alpha ≈ 240,973`. These values are not experimental predictions: the
W15 states were intentionally weak-coupling controls and the pure-SM backend
was given no measured targets. SMDR emitted its own warnings that the supplied
couplings were unusually small; those warnings are preserved in each result.

## Interpretation and next gate

W16 closes the executable projection gate and demonstrates that the W15 output
can be consumed by a real running-to-pole backend without hidden fitting. It
does **not** close full BSM physical matching. The next scientifically
meaningful extension is a BSM-aware matching layer that adds finite threshold
corrections and the singlet/vector-like contributions consistently, or a
published full-BSM backend whose conventions can be reproduced independently.

The result therefore supports a reproducible negative/diagnostic conclusion:
the present W15 trajectories do not land in the SM-like infrared regime under
this declared projection. It does not identify a new physical theory.

## Literature and software anchors

* [Official SMDR repository](https://github.com/davidgrobertson/SMDR)
* [Official SMDR documentation](https://davidgrobertson.github.io/SMDR/)
* [Martin and Robertson, arXiv:1907.02500](https://arxiv.org/abs/1907.02500)
* [Luo and Xiao, two-loop SM RGEs, hep-ph/0207271](https://arxiv.org/abs/hep-ph/0207271)
* [Luo, Wang and Xiao, general gauge-theory RGEs, hep-ph/0211440](https://arxiv.org/abs/hep-ph/0211440)

These references support the backend and RGE conventions. They do not turn the
low-energy pure-SM projection into a published full BSM calculation.
