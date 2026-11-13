"""Internal charge operator and fractional-charge pattern tests.

Charge quantization (q_n proportional to an integer quantum number) can
be DERIVED from an operator such as Q = kappa * p_xi.

The absolute normalization depends on free parameters (kappa, R, ...)
and is therefore NOT a prediction.

Fractional charges such as 1/3 are NEVER inserted into a model in order
to obtain them.  A separate test merely inspects the produced spectrum
to see whether those ratios appear on their own.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

import numpy as np
import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.observable import Observable
from physics_lab.core.parameter import Parameter, ParameterRegistry
from physics_lab.core.provenance import Provenance
from physics_lab.core.result import Quantity, Spectrum, quantity_from_parameters


# Patterns the *test* looks for.  These numbers are not model inputs.
CANDIDATE_CHARGE_FRACTIONS: tuple[Fraction, ...] = (
    Fraction(0, 1),
    Fraction(1, 1),
    Fraction(-1, 1),
    Fraction(1, 3),
    Fraction(-1, 3),
    Fraction(2, 3),
    Fraction(-2, 3),
)


CHARGE_QUANTIZATION_NOTE = (
    "Charge quantization: DERIVED (q_n proportional to n) "
    "if Q is built from the internal momentum. "
    "Absolute charge normalization: FREE PARAMETER."
)


def circle_charge_formula() -> str:
    return "q_n = n * hbar * kappa / R"


def charge_from_momentum(
    n: int,
    hbar: Parameter,
    kappa: Parameter,
    radius: Parameter,
) -> Quantity:
    """q_n = kappa * n * hbar / R  on the circle."""
    value = n * hbar.numeric * kappa.numeric / radius.numeric
    n_sym = sp.symbols("n", integer=True)
    symbolic = n_sym * hbar.symbolic * kappa.symbolic / radius.symbolic
    return quantity_from_parameters(
        name=f"charge[{n}]",
        value=value,
        ingredients=(hbar, kappa, radius),
        formula=circle_charge_formula(),
        symbolic=symbolic.subs(n_sym, n),
        extra_dependencies=("n",),
        state_label=str(n),
        notes=(CHARGE_QUANTIZATION_NOTE,),
    )


@dataclass
class CircleChargeObservable(Observable):
    """Q = kappa * p_xi  evaluated on circle momentum eigenstates."""

    name: str = "charge"
    description: str = "Q = kappa * p_xi"

    def evaluate(self, model: Model, spectrum: Spectrum) -> list[Quantity]:
        for required in ("kappa", "hbar", "R"):
            if required not in model.parameters:
                raise KeyError(
                    f"Circle charge observable requires parameter '{required}'."
                )
            model.parameters.mark_used(required, "charge")
        hbar = model.parameters.get("hbar")
        kappa = model.parameters.get("kappa")
        radius = model.parameters.get("R")
        results: list[Quantity] = []
        for state in spectrum.states:
            n = int(state.quantum_numbers.get("n", state.label))
            results.append(charge_from_momentum(n, hbar, kappa, radius))
        return results


def _parameter_looks_like_third(param: Parameter) -> bool:
    name = param.name.lower()
    if any(token in name for token in ("1/3", "one_third", "third", "fraction")):
        return True
    try:
        return abs(float(param.value) - (1.0 / 3.0)) < 1e-12
    except (TypeError, ValueError):
        return False


def third_was_inserted(parameters: ParameterRegistry | Iterable[Parameter]) -> bool:
    items = parameters.items() if isinstance(parameters, ParameterRegistry) else parameters
    return any(_parameter_looks_like_third(p) for p in items)


@dataclass
class ChargeFractionReport:
    status: str
    found_fractions: tuple[str, ...]
    inserted_one_third: bool
    message: str

    def is_prediction(self) -> bool:
        return self.status == "DERIVED"


def inspect_charge_fractions(
    charges: Iterable[float],
    parameters: ParameterRegistry | Iterable[Parameter],
    *,
    atol: float = 1e-6,
) -> ChargeFractionReport:
    """Observe a charge spectrum; never write 1/3 into the model.

    If the user inserted 1/3 as a parameter, the result is
    NOT A PREDICTION even if the spectrum contains thirds.
    """
    inserted = third_was_inserted(parameters)
    values = [float(c) for c in charges]
    if not values:
        return ChargeFractionReport(
            status="UNTESTED",
            found_fractions=(),
            inserted_one_third=inserted,
            message="No charges to inspect.",
        )

    scale_candidates = [abs(v) for v in values if abs(v) > atol]
    if not scale_candidates:
        ratios = [0.0] * len(values)
        scale = 1.0
    else:
        # Scale so that the smallest positive |q| maps to 1 when possible,
        # otherwise use max |q|.  This is an observational choice of units,
        # not a model input.
        scale = min(scale_candidates)
        ratios = [v / scale for v in values]

    found: list[str] = []
    for frac in CANDIDATE_CHARGE_FRACTIONS:
        target = float(frac)
        if any(abs(r - target) <= atol for r in ratios):
            found.append(str(frac))

    has_thirds = any(f in found for f in ("1/3", "-1/3", "2/3", "-2/3"))

    if inserted:
        return ChargeFractionReport(
            status="NOT A PREDICTION",
            found_fractions=tuple(found),
            inserted_one_third=True,
            message=(
                "A parameter equal to 1/3 (or named as a charge fraction) "
                "was inserted by the user. Fractional charge is therefore "
                "NOT A PREDICTION."
            ),
        )

    if has_thirds:
        return ChargeFractionReport(
            status="CANDIDATE DERIVED",
            found_fractions=tuple(found),
            inserted_one_third=False,
            message=(
                "Charge ratios compatible with {0, ±1/3, ±2/3, ±1} appear "
                "in the spectrum without 1/3 being inserted. "
                "Treat this as a candidate pattern, not as a completed derivation "
                "of quark-like charges."
            ),
        )

    return ChargeFractionReport(
        status="UNTESTED",
        found_fractions=tuple(found),
        inserted_one_third=False,
        message=(
            "No 1/3 charge-ratio pattern was observed in the spectrum. "
            "Integer ratios (if present) are reported separately as "
            "quantization, not as fractional charge."
        ),
    )


def charge_quantization_from_circle(charges: list[Quantity]) -> dict[str, str]:
    """q_n ∝ n is derived; absolute scale is a free parameter."""
    if not charges:
        return {
            "quantization": "UNTESTED",
            "absolute_normalization": "UNTESTED",
        }
    ns = []
    qs = []
    for q in charges:
        try:
            n = int(str(q.state_label))
        except (TypeError, ValueError):
            continue
        ns.append(n)
        qs.append(q.numeric())
    if not ns:
        return {
            "quantization": "UNTESTED",
            "absolute_normalization": "FREE PARAMETER",
        }

    # Check q_n / n constant for n != 0.
    ratios = [qs[i] / ns[i] for i in range(len(ns)) if ns[i] != 0]
    proportional = (
        len(ratios) >= 2 and float(np.max(np.abs(np.array(ratios) - ratios[0]))) < 1e-8
    )
    zeros_ok = all(abs(qs[i]) < 1e-12 for i, n in enumerate(ns) if n == 0)
    quantization = "DERIVED" if proportional and zeros_ok else "FAIL"
    free = any(q.free_dependencies for q in charges)
    return {
        "quantization": quantization,
        "absolute_normalization": "FREE PARAMETER" if free else "DERIVED",
        "formula": circle_charge_formula(),
    }
