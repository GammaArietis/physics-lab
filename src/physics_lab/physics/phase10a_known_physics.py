"""Isolated known-physics comparison catalog.

MUST NOT be imported by the Phase 10A generator, filters, or ranking.
Downstream interpretation only. No experimental numbers.
"""

from __future__ import annotations

from typing import Any

KNOWN_PHYSICS_CATALOG_VERSION = "phase10a-known-physics-v1"
PARTICIPATES_IN_GENERATION = False
PARTICIPATES_IN_FILTERING = False
PARTICIPATES_IN_RANKING = False

KNOWN_PHYSICS_CATALOG: dict[str, dict[str, Any]] = {
    "klein_gordon": {
        "fingerprint": "real scalar; two-derivative kinetic; optional mass-squared term",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
    "maxwell": {
        "fingerprint": "Abelian two-form kinetic F_mu_nu F^mu_nu; U(1) gauge invariance",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
    "einstein_hilbert": {
        "fingerprint": "volume term plus Ricci scalar; diffeomorphism covariance",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
    "yang_mills": {
        "fingerprint": "non-Abelian two-derivative curvature kinetic term",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
    "qed": {
        "fingerprint": "Maxwell plus minimally coupled charged matter",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
    "kaluza_klein_benchmark": {
        "fingerprint": "product geometry reduction to lower-dimensional gauge structure",
        "use": "downstream comparison only",
        "status": "REFERENCE_ONLY",
        "generator_enabled": False,
        "participates_in_generation": False,
        "participates_in_filtering": False,
        "participates_in_ranking": False,
    },
}
