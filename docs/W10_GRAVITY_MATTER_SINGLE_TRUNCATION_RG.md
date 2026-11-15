# W10 — Correlated gravity–matter truncation

## Objective

W9 scanned (f_g), (f_y) and (f_\lambda) as independent controls. W10
closes that gap by evaluating all three from one common set of FRG threshold
integrals and the same fixed point (G_*) of the Einstein–Hilbert Newton
coupling.

The implemented source reproduction is the standard-gravity and unimodular
analysis of de Brito and Eichhorn, *Eur. Phys. J. C* **83**, 161 (2023),
DOI [10.1140/epjc/s10052-023-11172-z](https://doi.org/10.1140/epjc/s10052-023-11172-z).
It contains one Abelian gauge field, one Dirac fermion and one real scalar,
with gauge, Yukawa and scalar-quartic interactions. The regulator interpolation
parameter (a) is evaluated for both Litim and exponential shape functions.

## What is reproduced

The threshold integral is

\[
 I_{\alpha,\beta}[r]=\int_0^\infty\frac{dy}{(4\pi)^2}
 \frac{y^\alpha r'(y)}{(1+r(y))^\beta}.
\]

For standard gravity the correlated coefficients are

\[
\begin{aligned}
 f_g&=\frac{80\pi}{3}(I_{1,2}-2I_{1,3})G_* ,\\
 f_\lambda&=\frac{16\pi}{3}(17I_{1,2}+2I_{1,3})G_* ,\\
 f_y&=\frac{\pi}{6}(220I_{1,2}+88I_{1,3}-135I_{1,5/2})G_* .
\end{aligned}
\]

The unimodular expressions are also implemented from the same publication.
The Einstein–Hilbert Newton flow is evaluated from its published
\(\beta_G\), rather than from an independently chosen (G_*).

In the published vanishing-regulator limit:

| gravity setting | (f_g) | (f_y) | (f_\lambda) |
| --- | ---: | ---: | ---: |
| standard | (10/17) | (-173/272) | (-38/17) |
| unimodular | (12/17) | (-261/136) | (-108/17) |

Both regulators reproduce the same universal-limit values. Finite-(a)
records are retained as scheme diagnostics, not as competing candidates.

## Cosmological-constant audit

The source truncation explicitly omits the cosmological-constant operator. It
therefore does **not** satisfy the stronger request “derive all three
coefficients from one truncation including nonzero Λ”. W10 records this as an
open closure gate and does not introduce an arbitrary (G\Lambda) correction.
The same source notes that nonzero Λ adds further terms and that a negative
cosmological constant can change the sign of the Yukawa contribution, but it
does not provide the numerical Λ-dependent closure used by this campaign.

This is a result, not a crash: the three matter coefficients are now genuinely
correlated in the published Λ=0 truncation, while the Λ-inclusive problem is
shown to remain underdetermined.

The comparative Higgs analysis is Pawlowski, Reichert, Wetterich and Yamada,
*Phys. Rev. D* **99**, 086010 (2019),
DOI [10.1103/PhysRevD.99.086010](https://doi.org/10.1103/PhysRevD.99.086010).
The broader gravity–matter context is de Brito *et al.*, *Phys. Rev. D*
**109**, 055022 (2024),
DOI [10.1103/PhysRevD.109.055022](https://doi.org/10.1103/PhysRevD.109.055022).
Scheme and gauge dependence are explicitly retained as a caveat, following
Riabokon, Schiffer and Wagner, *Phys. Rev. D* **112**, 106003 (2025),
DOI [10.1103/gxm2-trn6](https://doi.org/10.1103/gxm2-trn6).

## Campaign

The default run executes:

- 2 gravity settings: standard and unimodular;
- 2 regulators: Litim and exponential;
- 10 regulator values, including the published (a\to0) limit;
- 40 correlated coefficient slices;
- 114 retained algebraic branches;
- 80 bounded trajectories from two target-blind initial states.

No branch is selected or ranked. No value of α, including (1/137), is used as
an input, target or fit criterion.

The machine-readable result is
`docs/validation/gravity_matter_single_truncation_rg_campaign_2026-11-15.json`.
