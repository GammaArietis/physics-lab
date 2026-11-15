# Eichhorn--Held: full gravity--matter reproduction

## Objective

This campaign reproduces the published Einstein--Hilbert gravity--matter
truncation used by Eichhorn and Held in *Top mass from asymptotic safety*,
Phys. Lett. B 777, 217--221 (2018), DOI
[10.1016/j.physletb.2017.12.040](https://doi.org/10.1016/j.physletb.2017.12.040).
It extends the laboratory's W9/W10 bookkeeping to the explicit

\[
(G_N,\Lambda,g_1,g_2,g_3,y_t,y_b,\lambda_4)
\]

system printed in the paper. The goal is faithful execution and auditability,
not a fit to the fine-structure constant or to particle masses.

## Implemented equations

The gravitational sector is

\[
\beta_{G_N}=2G_N-G_N^2 f_{G_N}(\Lambda),
\]

\[
\beta_\Lambda=-2\Lambda-\frac{G_N}{2\pi}B(\Lambda)
-G_N\Lambda f_{G_N}(\Lambda),
\]

with the Standard Model field counts \(N_S=4\), \(N_V=12\), and
\(N_W=45\) used by the source. The gauge sector is

\[
\beta_{g_i}=\frac{b_i g_i^3}{16\pi^2}-G_N g_i f_g(\Lambda),
\qquad b_i=\left(\frac{41}{10},-\frac{19}{6},-7\right),
\]

and the matter sector contains the printed one-loop top, bottom and Higgs
quartic beta functions with the common gravitational factors
\(f_y(\Lambda)\) and \(f_{\lambda_4}(\Lambda)\). The three explicit threshold
functions are implemented exactly as printed:

\[
f_g=\frac{5(1-4\Lambda)}{18\pi(1-2\Lambda)^2},
\]

\[
f_y=\frac{96+\Lambda[-235+\Lambda(103+56\Lambda)]}
{12\pi[3+2\Lambda(-5+4\Lambda)]^2},
\]

\[
f_{\lambda_4}=\frac{165-8\Lambda[61+\Lambda(-49+4\Lambda)]}
{6\pi[3+2\Lambda(-5+4\Lambda)]^2}.
\]

Threshold poles are explicitly guarded. No value of \(\alpha\), no measured
mass and no external dataset is used in the computation.

## Reproducibility audit

The paper quotes the gravity fixed point

\[
(G_N^*,\Lambda^*)=(3.29,-4.51).
\]

Evaluating the corrected printed equations with the stated field counts at
that rounded anchor gives

\[
(\beta_{G_N},\beta_\Lambda)\approx(0.00874978,-0.00309505),
\]

so the anchor is a rounded point, not an exact zero. Solving those equations
independently gives

\[
(G_N,\Lambda)=(3.2945094357,-4.5139868308),
\]

with maximum residual below \(10^{-14}\). This rounds exactly to the paper's
reported two-decimal anchor. The original implementation had a transcription
error in the \(\beta_\Lambda\) bracket: it used
\(3/[7-2(3-4\Lambda)]\) instead of the printed
\(7-3/[2(3-4\Lambda)]\). The error is now corrected and covered by the
versioned audit.

## Campaign contents

The default campaign contains 45 \((G_N,\Lambda)\) slices, enumerates all
real matter fixed-point branches found from a deterministic seed set, and
integrates three full eight-dimensional trajectories. The executed local run
produced 780 retained matter branches and three `COMPLETE` trajectories.
Every branch is retained; no automatic ranking or selection is performed.

The source's quoted top-pole and Higgs-mass values are recorded as source
claims only. IR matching, pole-mass conversion and empirical comparison are
not implemented in this campaign.

## Result

The published truncation is now executable and target-blind, including the
nonzero cosmological constant and all three SM gauge couplings. It does not
derive \(1/137\). The independent convention and source audit is recorded in
`docs/EICHHORN_HELD_ANCHOR_AUDIT.md` and confirms the correction. The next
scientific gate is a separate target-blind IR matching layer.

Machine-readable activation:
`schemas/examples/eichhorn_held_asymptotic_safety_activation.json`.

Machine-readable report:
`docs/validation/eichhorn_held_asymptotic_safety_campaign_2026-11-15.json`.
