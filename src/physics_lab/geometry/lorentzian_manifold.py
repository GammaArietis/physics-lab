"""4D Lorentzian manifold with a dynamical metric.  Signature is CONVENTION."""

from __future__ import annotations

from physics_lab.geometry.geometry import Geometry
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag


class LorentzianManifold(Geometry):
    def __init__(self, signature: str = MOSTLY_PLUS) -> None:
        self.signature = signature
        super().__init__(
            name="LorentzianManifold",
            coordinates=("t", "x", "y", "z"),
            periodic=False,
            description=self.domain_description(),
            metadata={
                "signature": signature,
                "dimension": 4,
                "metric_status": "DYNAMICAL FIELD",
                "eta_reference": eta_diag(signature),
            },
        )

    def period(self) -> None:
        return None

    def domain_description(self) -> str:
        label = "(-,+,+,+)" if self.signature == MOSTLY_PLUS else "(+,-,-,-)"
        return (
            f"4D Lorentzian manifold, signature {label} CONVENTION. "
            "g_{mu nu} is a dynamical field."
        )
