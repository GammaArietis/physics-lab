# W14 — Threshold-resolved IR/EFT extension

## Purpose

W14 continues the W13 gauge–Yukawa vector-like extension without opening a
new geometric search. Every present vector-like multiplet receives an
explicit mass threshold. The one-loop gauge coefficients are recomputed from
the representation data above and below each threshold, and the dimensionless
coupling state is matched continuously at the declared scale.

The executable chain is:

`activation → action with masses → active representations → piecewise running → IR observables`

## Result

The registered five-candidate campaign contains four nonzero branches and one
exact-zero gauge control:

* `4 COMPLETE`;
* `1 ZERO_PROTECTED`;
* all five records retained;
* no fitting, ranking, automatic selection or alpha target;
* no finite threshold corrections or two-loop/NNLO precision matching claim.

The zero branch remains zero because perturbative gauge beta functions are
multiplicative in the gauge coupling. Thresholds change the coefficient of
the flow but do not create an additive seed.

## Interpretation

This is a stronger IR control than W13 because decoupling scales are explicit
and the representation content changes along the trajectory. It is still not
a precision phenomenology result: finite matching corrections, full
two-loop gauge–Yukawa–scalar beta functions, pole conversion and experimental
constraints remain outside scope.

The masses in the activation are declared theoretical scan inputs. They are
not fitted to measured masses and no candidate is promoted by its IR value.

## Literature position

Vector-like matter in gauge–Yukawa theories and interacting ultraviolet fixed
points are established research directions. W14 uses that literature as a
model-building anchor, while implementing a deliberately transparent
one-loop threshold control rather than claiming to reproduce the complete
multi-loop calculations:

* [Litim–Sannino, *Asymptotic safety guaranteed*](https://arxiv.org/abs/1406.2337)
* [Mann et al., *Asymptotically Safe Standard Model via Vector-Like Fermions*](https://arxiv.org/abs/1707.02942)

