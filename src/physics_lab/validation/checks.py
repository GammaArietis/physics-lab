"""Check statuses.  There is no overall score."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNTESTED = "UNTESTED"
    ASSUMED = "ASSUMED"
    CALIBRATED = "CALIBRATED"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
