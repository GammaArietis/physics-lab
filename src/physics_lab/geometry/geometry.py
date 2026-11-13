"""Abstract internal geometry.

The core model does not assume a circle.  Concrete geometries implement
this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Geometry(ABC):
    name: str
    coordinates: tuple[str, ...]
    periodic: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def period(self) -> float | None:
        """Fundamental period of the coordinate, if periodic."""

    @abstractmethod
    def domain_description(self) -> str:
        """Human-readable domain, including identifications."""

    def identifications(self) -> list[str]:
        return []
