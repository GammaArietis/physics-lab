"""Finite dimension scan around the Wyler type-IV domain construction.

The scan keeps physical spacetime dimension d=4 fixed and varies only the
abstract complex dimension n of a type-IV (Lie-ball) domain.  The n-dependent
formula is an explicit mathematical extrapolation of the Wyler volume
combination; only n=5 is the historical anchor.  No result for n != 5 is
presented as a physical derivation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


WYLER_DIMENSION_SCAN_VERSION = "wyler-dimension-scan-v1"
DEFAULT_ABSTRACT_DIMENSIONS = tuple(range(3, 10))
PHYSICAL_SPACETIME_DIMENSION = 4


class WylerDimensionScanError(ValueError):
    """Raised when a dimension-scan input is invalid."""


def _lie_ball_volume(n: int) -> float:
    """Euclidean volume of the unit type-IV Lie ball in C^n."""
    return math.pi**n / (2 ** (n - 1) * math.factorial(n))


def _sphere_volume(n: int) -> float:
    """Volume of the unit (n-1)-sphere."""
    return 2 * math.pi ** (n / 2) / math.gamma(n / 2)


def _shilov_boundary_volume(n: int) -> float:
    """Volume under the explicit product/quotient metric convention.

    The distinguished boundary is represented as
    (S^1 x S^(n-1))/Z_2, so its volume is pi times the volume of S^(n-1).
    This metric convention is recorded as an assumption, not hidden in the
    numerical result.
    """
    return math.pi * _sphere_volume(n)


def _wyler_form_extrapolation(n: int) -> float:
    """Apply the historical Wyler volume combination at abstract dimension n."""
    domain = _lie_ball_volume(n)
    boundary = _shilov_boundary_volume(n)
    sphere = _sphere_volume(n)
    return 8 * math.pi * domain ** 0.25 / (boundary * sphere)


def _validate_dimensions(dimensions: Sequence[int]) -> list[int]:
    values = sorted(set(dimensions))
    if not values or any(not isinstance(n, int) or n < 3 or n > 32 for n in values):
        raise WylerDimensionScanError("abstract dimensions must be bounded integers in [3, 32]")
    return values


def run_wyler_dimension_scan(
    *,
    target_alpha_inverse: float,
    dimensions: Sequence[int] = DEFAULT_ABSTRACT_DIMENSIONS,
) -> dict[str, Any]:
    """Run the finite abstract-dimension scan and compare after generation."""
    if not math.isfinite(target_alpha_inverse) or target_alpha_inverse <= 0:
        raise WylerDimensionScanError("target_alpha_inverse must be a positive finite number")
    values = _validate_dimensions(dimensions)

    candidates: list[dict[str, Any]] = []
    for n in values:
        domain = _lie_ball_volume(n)
        sphere = _sphere_volume(n)
        boundary = _shilov_boundary_volume(n)
        alpha = _wyler_form_extrapolation(n)
        candidates.append(
            {
                "candidate_id": f"wyler-type-iv-dimension-n{n}",
                "abstract_domain_dimension": n,
                "physical_spacetime_dimension": PHYSICAL_SPACETIME_DIMENSION,
                "status": "HISTORICAL_ANCHOR_REPRODUCED" if n == 5 else "MATHEMATICAL_EXTRAPOLATION",
                "physical_status": "OPEN" if n == 5 else "NOT_DERIVED",
                "volumes": {
                    "D_n": domain,
                    "Q_n": boundary,
                    "S_(n-1)": sphere,
                },
                "volume_formulas": {
                    "D_n": "pi^n/(2^(n-1)*n!)",
                    "S_(n-1)": "2*pi^(n/2)/Gamma(n/2)",
                    "Q_n": "pi*S_(n-1) under (S^1 x S^(n-1))/Z2 product metric",
                },
                "wyler_form": "8*pi*V(D_n)^(1/4)/(V(Q_n)*V(S_(n-1)))",
                "alpha": alpha,
                "alpha_inverse": 1 / alpha,
                "target_alpha_inverse": target_alpha_inverse,
                "relative_error_ppm": (1 / alpha - target_alpha_inverse) / target_alpha_inverse * 1_000_000,
                "comparison_status": "COMPLETE",
                "continuous_fit_parameters": [],
            }
        )

    return {
        "search_version": WYLER_DIMENSION_SCAN_VERSION,
        "search_id": "wyler-type-iv-abstract-dimension-scan",
        "stage": "W2A_DIMENSION_SCAN",
        "execution_status": "COMPLETE",
        "authorization": {
            "search_status": "AUTHORIZED",
            "finite_bounds": "AUTHORIZED",
            "comparison_status": "AUTHORIZED_AFTER_GENERATION",
            "target_blind_generation": True,
            "fitting": "DISABLED",
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
        },
        "dimensions": {
            "abstract_domain_dimensions": values,
            "physical_spacetime_dimension": PHYSICAL_SPACETIME_DIMENSION,
            "physical_dimension_scan": "NOT_PERFORMED",
            "reason": "Keep d=4 so the QED coupling remains dimensionless and comparable to alpha.",
        },
        "target": {
            "alpha_inverse": target_alpha_inverse,
            "source_id": "codata-2022-alpha-inverse",
            "source_uri": "https://physics.nist.gov/cuu/pdf/JPCRD2022CODATA.pdf",
            "role": "post_generation_comparison_only",
        },
        "assumptions": {
            "domain_family": "Cartan type-IV / Lie ball",
            "boundary_identification": "(S^1 x S^(n-1))/Z2",
            "boundary_metric": "product metric convention",
            "wyler_prefactor_and_exponent": "held fixed from n=5 historical form",
            "physical_interpretation": "not established by this scan",
        },
        "controls": {
            "finite_dimension_bound": True,
            "physical_spacetime_dimension_fixed_to_four": True,
            "no_continuous_fit": True,
            "target_blind_generation": True,
            "comparison_after_generation": True,
            "all_dimensions_recorded": True,
            "no_auto_selection": True,
            "no_ranking": True,
            "n5_anchor_present_once": sum(item["abstract_domain_dimension"] == 5 for item in candidates) == 1,
            "extrapolation_label_explicit": all(
                item["status"] in {"HISTORICAL_ANCHOR_REPRODUCED", "MATHEMATICAL_EXTRAPOLATION"}
                for item in candidates
            ),
        },
        "candidates": candidates,
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "DERIVE_WYLER_MEASURE_AND_U1_ACTION_OR_KEEP_SCAN_AS_MATHEMATICAL_ONLY",
    }


def write_wyler_dimension_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
