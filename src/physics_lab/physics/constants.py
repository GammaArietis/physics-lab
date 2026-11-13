"""Experimental reference constants.

These values are EXPERIMENTAL.  They must NOT be imported by model
derivation code.  Use them only in the final comparison stage
(reporting / validator).
"""

from physics_lab.core.parameter import Parameter
from physics_lab.core.provenance import Provenance

# CODATA 2022 inverse fine-structure constant (dimensionless).
# Stored solely as an experimental reference.
ALPHA_INVERSE = Parameter(
    name="alpha_inverse",
    value=137.035999177,
    provenance=Provenance.EXPERIMENTAL,
    description="Inverse fine-structure constant (experimental reference only).",
)

ALPHA = Parameter(
    name="alpha",
    value=1.0 / 137.035999177,
    provenance=Provenance.EXPERIMENTAL,
    description="Fine-structure constant (experimental reference only).",
)


def experimental_names() -> frozenset[str]:
    return frozenset({ALPHA_INVERSE.name, ALPHA.name})
