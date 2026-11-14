# Wyler dimension scan protocol

Status: `W2A_COMPLETE` after explicit authorization on 14 November 2026.

## Question

Does the numerical proximity of the Wyler expression depend uniquely on the
abstract dimension `n=5`, or does a nearby dimension produce comparable
values?

## Separation of dimensions

The scan varies the abstract complex dimension `n` of a Cartan type-IV domain
(Lie ball). It keeps physical spacetime dimension fixed at `d=4`. This is
essential: changing `d` would change the physical theory and the mass
dimension of the gauge coupling, so it would not be a direct comparison with
the four-dimensional fine-structure constant.

## Mathematical convention

For `n=3,...,9` the pilot uses the explicit unit-volume conventions:

```text
V(D_n)       = pi^n / (2^(n-1) n!)
V(S^(n-1))   = 2 pi^(n/2) / Gamma(n/2)
V(Q_n)       = pi V(S^(n-1))
```

The last equation corresponds to the stated product/quotient convention
`Q_n = (S^1 x S^(n-1))/Z_2`. It is recorded as a metric assumption rather
than hidden in the code.

The historical Wyler combination is then extrapolated diagnostically as:

```text
alpha_n = 8*pi*V(D_n)^(1/4) / (V(Q_n)*V(S^(n-1)))
```

Only `n=5` is the historical Wyler anchor. Every other dimension is labelled
`MATHEMATICAL_EXTRAPOLATION`, not a physical derivation.

## Interpretation rules

- The target is read only after all dimensions are generated.
- No continuous fit or per-dimension normalization is allowed.
- All dimensions are retained; no closest-value selection or ranking occurs.
- A close value at `n != 5` would show numerical sensitivity, not a theory.
- A unique `n=5` proximity would be an interesting mathematical clue, not a
  proof of QED.
- The next physical gate remains a derivation of the measure, the U(1) action,
  and the coupling normalization.
