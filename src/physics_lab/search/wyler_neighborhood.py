"""Reproduce Wyler's anchor and run a declared normalization stress test.

The historical Wyler expression is evaluated exactly as a reference anchor.
The surrounding variants are deliberately labelled stress tests, not physical
theories: they vary discrete normalization ingredients before any comparison
is made, and they are never selected or ranked automatically.  A physical
candidate still needs an explicit Maxwell/QED action and a derivation of the
normalization.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping


WYLER_SEARCH_VERSION = "wyler-neighborhood-search-v1"
WYLER_VOLUMES = {
    "D5": "pi^5/(2^4*5!)",
    "Q5": "8*pi^3/3",
    "S4": "8*pi^2/3",
}


class WylerNeighborhoodError(ValueError):
    """Raised when a Wyler neighborhood input is invalid."""


def _volumes() -> dict[str, float]:
    pi = math.pi
    return {
        "D5": pi**5 / (2**4 * math.factorial(5)),
        "Q5": 8 * pi**3 / 3,
        "S4": 8 * pi**2 / 3,
    }


def _alpha_from_components(*, spin_multiplicity: int, phase_factor: float, domain_exponent: float) -> float:
    volumes = _volumes()
    return (
        spin_multiplicity
        * phase_factor
        * volumes["D5"] ** domain_exponent
        / (volumes["Q5"] * volumes["S4"])
    )


def wyler_anchor() -> dict[str, Any]:
    """Return the historical Wyler formula without fitting any quantity."""
    alpha = _alpha_from_components(
        spin_multiplicity=4,
        phase_factor=2 * math.pi,
        domain_exponent=0.25,
    )
    return {
        "candidate_id": "wyler-anchor",
        "status": "REFERENCE_ANCHOR",
        "physical_status": "OPEN",
        "formula": "9/(16*pi^3)*(pi/5!)^(1/4)",
        "equivalent_formula": "9/(8*pi^4)*(pi^5/(2^4*5!))^(1/4)",
        "volumes": WYLER_VOLUMES,
        "components": {
            "spin_multiplicity": 4,
            "phase_factor": "2*pi",
            "domain_exponent": "1/4",
        },
        "alpha": alpha,
        "alpha_inverse": 1 / alpha,
        "free_continuous_parameters": [],
        "comparison_role": "historical_anchor_only",
    }


def _variant_id(spin_multiplicity: int, phase_factor_label: str, domain_exponent: float) -> str:
    exponent_label = str(domain_exponent).replace(".", "p")
    return f"wyler-stress-spin{spin_multiplicity}-{phase_factor_label}-power{exponent_label}"


def _build_variants() -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    phase_factors = [(1.0, "one"), (2 * math.pi, "two-pi")]
    for spin_multiplicity in (1, 2, 4):
        for phase_factor, phase_label in phase_factors:
            for domain_exponent in (0.125, 0.25, 0.5):
                candidate_id = _variant_id(spin_multiplicity, phase_label, domain_exponent)
                is_anchor = (
                    spin_multiplicity == 4
                    and phase_label == "two-pi"
                    and domain_exponent == 0.25
                )
                variants.append(
                    {
                        "candidate_id": candidate_id,
                        "status": "REFERENCE_ANCHOR" if is_anchor else "NORMALIZATION_STRESS_TEST",
                        "physical_status": "OPEN" if is_anchor else "NOT_ADMISSIBLE_WITHOUT_DERIVATION",
                        "formula": "spin_factor*phase_factor*V(D5)^p/(V(Q5)*V(S4))",
                        "volumes": WYLER_VOLUMES,
                        "components": {
                            "spin_multiplicity": spin_multiplicity,
                            "phase_factor": phase_label,
                            "domain_exponent": domain_exponent,
                        },
                        "alpha": _alpha_from_components(
                            spin_multiplicity=spin_multiplicity,
                            phase_factor=phase_factor,
                            domain_exponent=domain_exponent,
                        ),
                        "free_continuous_parameters": [],
                        "comparison_role": "post_generation_diagnostic",
                    }
                )
    return variants


def run_wyler_neighborhood_pilot(*, target_alpha_inverse: float) -> dict[str, Any]:
    """Evaluate the pre-registered neighborhood and compare after generation."""
    if not math.isfinite(target_alpha_inverse) or target_alpha_inverse <= 0:
        raise WylerNeighborhoodError("target_alpha_inverse must be a positive finite number")

    # Generation is complete before target_alpha_inverse is read by the
    # comparison loop.  This separation is recorded in the report.
    variants = _build_variants()
    anchor = wyler_anchor()
    anchor_ids = [item["candidate_id"] for item in variants if item["status"] == "REFERENCE_ANCHOR"]
    if anchor_ids != ["wyler-stress-spin4-two-pi-power0p25"]:
        raise WylerNeighborhoodError("the exact anchor must occur once in the pre-registered neighborhood")

    for item in variants:
        item["alpha_inverse"] = 1 / item["alpha"]
        item["target_alpha_inverse"] = target_alpha_inverse
        item["relative_error_ppm"] = (
            (item["alpha_inverse"] - target_alpha_inverse) / target_alpha_inverse * 1_000_000
        )
        item["comparison_status"] = "COMPLETE"

    return {
        "search_version": WYLER_SEARCH_VERSION,
        "search_id": "wyler-neighborhood-stage1",
        "stage": "W0_ANCHOR_PLUS_W1_NORMALIZATION_STRESS_TEST",
        "execution_status": "COMPLETE",
        "grammar": {
            "spin_multiplicity": [1, 2, 4],
            "phase_factor": ["one", "two-pi"],
            "domain_exponent": [0.125, 0.25, 0.5],
            "candidate_count": len(variants),
        },
        "authorization": {
            "search_status": "AUTHORIZED",
            "finite_bounds": "AUTHORIZED",
            "comparison_status": "AUTHORIZED_AFTER_GENERATION",
            "fitting": "DISABLED",
            "external_target_used": True,
            "target_blind_generation": True,
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
        },
        "target": {
            "alpha_inverse": target_alpha_inverse,
            "source_id": "codata-2022-alpha-inverse",
            "source_uri": "https://physics.nist.gov/cuu/pdf/JPCRD2022CODATA.pdf",
            "role": "post_generation_comparison_only",
        },
        "controls": {
            "anchor_reproduced": True,
            "finite_grammar": True,
            "no_continuous_fit": True,
            "target_blind_generation": True,
            "comparison_after_generation": True,
            "no_auto_selection": True,
            "no_ranking": True,
            "all_variants_recorded": True,
            "physical_admissibility_not_claimed": True,
        },
        "anchor": anchor,
        "variants": variants,
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "DERIVE_U1_MAXWELL_QED_NORMALIZATION_OR_REJECT_AS_NUMEROLOGY",
    }


def write_wyler_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
