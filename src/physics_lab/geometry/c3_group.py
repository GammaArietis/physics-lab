"""Internal space = the finite group C3.  No continuous coordinate, no R."""

from __future__ import annotations

from physics_lab.geometry.geometry import Geometry


class C3GroupGeometry(Geometry):
    """The set {e, T, T²} with T³ = I.

    This is not a discretized circle.  There is no radius and no angle θ.
    """

    def __init__(self) -> None:
        super().__init__(
            name="C3",
            coordinates=(),
            periodic=False,
            description=self.domain_description(),
        )

    def period(self) -> None:
        return None

    def domain_description(self) -> str:
        return "internal space = group C3 = {e, T, T^2},  T^3 = I  (no radius, no θ)"

    def identifications(self) -> list[str]:
        return ["T^3 = I"]
