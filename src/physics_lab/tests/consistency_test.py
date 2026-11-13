"""Mathematical consistency of a solved model."""

from __future__ import annotations

import numpy as np

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.validation.checks import CheckResult, CheckStatus


def check_consistency(model: Model, result: ModelResult) -> CheckResult:
    problems: list[str] = []
    values = result.spectrum.eigenvalues()
    if values.size == 0:
        problems.append("empty spectrum")
    if np.any(~np.isfinite(values)):
        problems.append("non-finite eigenvalues")

    matrix = getattr(model.dynamics, "matrix", None)
    if matrix is not None:
        hermitian = bool(np.allclose(matrix, np.asarray(matrix).conj().T))
        if not hermitian:
            problems.append("Hamiltonian matrix is not Hermitian")

    checks = result.metadata.get("momentum_eigenfunction_checks")
    if checks:
        failed = [c for c in checks if not c.get("holds")]
        if failed:
            problems.append(f"{len(failed)} momentum eigenfunction identities failed")

    if result.metadata.get("momentum_identity_verified") is False:
        problems.append("analytic momentum identity p_xi chi_n = n*hbar/R chi_n failed")

    if result.metadata.get("n_origin") == "derived from PBC":
        if result.metadata.get("half_integer_rejected") is False:
            problems.append("candidate n=1/2 was not rejected by the PBC")
        kq = result.metadata.get("k_quantization")
        if kq is not None and not getattr(kq, "integer_n_derived", False):
            problems.append("PBC did not derive n ∈ Z")

    if problems:
        return CheckResult(
            name="Mathematical consistency",
            status=CheckStatus.FAIL,
            message="; ".join(problems),
        )
    return CheckResult(
        name="Mathematical consistency",
        status=CheckStatus.PASS,
        message="Finite spectrum; analytic identities hold where checked.",
    )
