"""Minkowski spacetime as a background geometry.  Signature is a CONVENTION."""

from __future__ import annotations

from physics_lab.geometry.geometry import Geometry
from physics_lab.physics.spacetime import MOSTLY_MINUS, MOSTLY_PLUS, eta_diag


class MinkowskiGeometry(Geometry):
    def __init__(self, signature: str = MOSTLY_PLUS) -> None:
        self.signature = signature
        super().__init__(
            name="Minkowski",
            coordinates=("t", "x", "y", "z"),
            periodic=False,
            description=self.domain_description(),
            metadata={"signature": signature, "eta": eta_diag(signature)},
        )

    def period(self) -> None:
        return None

    def domain_description(self) -> str:
        e = eta_diag(self.signature)
        label = "(-,+,+,+)" if self.signature == MOSTLY_PLUS else "(+,-,-,-)"
        if self.signature not in (MOSTLY_PLUS, MOSTLY_MINUS):
            label = "Euclidean"
        return f"Minkowski R^{{1,3}}, eta=diag{e} {label}. Signature is CONVENTION."
