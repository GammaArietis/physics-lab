"""Internal spectrum checks."""

from __future__ import annotations

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_spectrum(model: Model, result: ModelResult) -> CheckResult:
    states = result.spectrum.states
    if not states:
        return CheckResult(
            name="Internal spectrum",
            status=CheckStatus.FAIL,
            message="No eigenstates were produced.",
        )

    quantized = all("n" in s.quantum_numbers for s in states)
    derived = result.metadata.get("n_origin") == "derived from PBC"
    details = {
        "n_states": len(states),
        "method": result.spectrum.method,
        "integer_n": quantized,
        "n_origin": result.metadata.get("n_origin"),
    }
    message = f"{len(states)} states via {result.spectrum.method}."
    if derived:
        message += " n ∈ Z derived from χ(ξ+2πR)=χ(ξ)."
    if quantized:
        ns = sorted(int(s.quantum_numbers["n"]) for s in states)
        expected = list(range(min(ns), max(ns) + 1))
        if ns == expected:
            message += " Display window is a consecutive integer lattice."
        else:
            message += f" Quantum numbers n={ns}."
    return CheckResult(
        name="Internal spectrum",
        status=CheckStatus.PASS,
        message=message,
        details=details,
    )
