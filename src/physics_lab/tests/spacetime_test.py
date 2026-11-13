"""Validator checks for spacetime Phase 3 and signature consistency."""

from __future__ import annotations

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.spacetime import (
    EUCLIDEAN,
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    X_homogeneous_spatial,
    adapted_canonical_matches_hyperbolic,
    analyze_spacetime,
    boost_preserves_X,
    canonical_prefactor,
    classify_m2,
    eta_diag,
    field_redefinition_Z,
    hamiltonian_density_from_F,
    mixed_convention_hamiltonian_coeff,
    volume_element,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("spacetime_test"))


def check_st_lorentz(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: Lorentz scalars / boost",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    if not boost_preserves_X():
        return CheckResult(
            name="Spacetime: Lorentz scalars / boost",
            status=CheckStatus.FAIL,
            message="X is not invariant under a 1+1 boost.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    if data.get("F_linear_in_X") != "NOT DERIVED":
        return CheckResult(
            name="Spacetime: Lorentz scalars / boost",
            status=CheckStatus.FAIL,
            message="Linear F(X) was claimed to be derived.",
        )
    return CheckResult(
        name="Spacetime: Lorentz scalars / boost",
        status=CheckStatus.PASS,
        message="X is a Lorentz scalar. L=F(phi,X) is allowed. Linear F is NOT DERIVED.",
    )


def check_st_signature(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: signature contraction X",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    Xp = X_homogeneous_spatial(MOSTLY_PLUS, phidot, gradsq)
    Xm = X_homogeneous_spatial(MOSTLY_MINUS, phidot, gradsq)
    if sp.simplify(Xp - (-(phidot**2) + gradsq)) != 0:
        return CheckResult(
            name="Spacetime: signature contraction X",
            status=CheckStatus.FAIL,
            message="mostly_plus X mismatch.",
        )
    if sp.simplify(Xm - (phidot**2 - gradsq)) != 0:
        return CheckResult(
            name="Spacetime: signature contraction X",
            status=CheckStatus.FAIL,
            message="mostly_minus X mismatch.",
        )
    if sp.simplify(Xp + Xm) != 0:
        return CheckResult(
            name="Spacetime: signature contraction X",
            status=CheckStatus.FAIL,
            message="eta -> -eta should send X -> -X.",
        )
    return CheckResult(
        name="Spacetime: signature contraction X",
        status=CheckStatus.PASS,
        message="X matches both Lorentzian signatures and flips under eta -> -eta.",
    )


def check_st_hamiltonian(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: Hamiltonian kinetic sign",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    phidot, gradsq = sp.symbols("phidot gradsq", real=True)
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        X = X_homogeneous_spatial(sig, phidot, gradsq)
        F = canonical_prefactor(sig) * X
        H = hamiltonian_density_from_F(F, X, phidot)
        coeff = sp.expand(H.subs(gradsq, 0)).coeff(phidot, 2)
        if sp.simplify(coeff - sp.Rational(1, 2)) != 0:
            return CheckResult(
                name="Spacetime: Hamiltonian kinetic sign",
                status=CheckStatus.FAIL,
                message=f"Adapted canonical L does not give +1/2 phidot^2 in H for {sig}.",
            )
    data = result.metadata.get("spacetime_analysis") or {}
    if (data.get("signature_audit") or {}).get("signature_consistency") != "PASS":
        return CheckResult(
            name="Spacetime: Hamiltonian kinetic sign",
            status=CheckStatus.FAIL,
            message="Signature audit did not PASS.",
        )
    return CheckResult(
        name="Spacetime: Hamiltonian kinetic sign",
        status=CheckStatus.PASS,
        message="Ghost-free is Hamiltonian positivity of (d_t phi)^2, given signature and adapted L.",
    )


def check_st_propagator(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: propagator / dispersion",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    if not adapted_canonical_matches_hyperbolic():
        return CheckResult(
            name="Spacetime: propagator / dispersion",
            status=CheckStatus.FAIL,
            message="Adapted canonical L is not hyperbolic in both signatures.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    audit = data.get("signature_audit") or {}
    if audit.get("propagator_consistency") != "PASS":
        return CheckResult(
            name="Spacetime: propagator / dispersion",
            status=CheckStatus.FAIL,
            message="Propagator consistency is not PASS.",
        )
    if "omega^2 = |k|^2 + m2" not in str(audit.get("dispersion_relation", "")):
        return CheckResult(
            name="Spacetime: propagator / dispersion",
            status=CheckStatus.FAIL,
            message="Dispersion relation missing.",
        )
    return CheckResult(
        name="Spacetime: propagator / dispersion",
        status=CheckStatus.PASS,
        message="Adapted Klein-Gordon operator is hyperbolic. Not a unitarity proof.",
    )


def check_st_locality(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: locality vs derivative order",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    note = str(data.get("locality_vs_order", ""))
    if "point" not in note.lower():
        return CheckResult(
            name="Spacetime: locality vs derivative order",
            status=CheckStatus.FAIL,
            message="Locality was not distinguished from derivative order.",
        )
    if (data.get("examples") or {}).get("L4", {}).get("local", "").startswith("YES") is False:
        return CheckResult(
            name="Spacetime: locality vs derivative order",
            status=CheckStatus.FAIL,
            message="L4 must remain local even though it is higher-order.",
        )
    return CheckResult(
        name="Spacetime: locality vs derivative order",
        status=CheckStatus.PASS,
        message="L1-L5 are local. L4 is local and higher-order.",
    )


def check_st_canonicalization(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: field redefinition",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    info = field_redefinition_Z()
    if "CONVENTION" not in info["status"]:
        return CheckResult(
            name="Spacetime: field redefinition",
            status=CheckStatus.FAIL,
            message="Canonicalization was not marked as a convention.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    if (data.get("examples") or {}).get("L2", {}).get("canonicalizable") == "YES":
        return CheckResult(
            name="Spacetime: field redefinition",
            status=CheckStatus.FAIL,
            message="Nonlinear X^2 must survive a field redefinition of phi.",
        )
    return CheckResult(
        name="Spacetime: field redefinition",
        status=CheckStatus.PASS,
        message="Z(phi) X is a chart choice. Nonlinear F(X) is not removed.",
    )


def check_st_dimensional(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: dimensional / no-scale",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    ns = data.get("no_scale") or {}
    if ns.get("unique_action") != "NO":
        return CheckResult(
            name="Spacetime: dimensional / no-scale",
            status=CheckStatus.FAIL,
            message="No-scale branch claimed a unique action.",
        )
    dim = data.get("dimensional_table") or []
    joined = " ".join(str(c) for row in dim for c in row)
    if "lam" not in joined or "c_box" not in joined:
        return CheckResult(
            name="Spacetime: dimensional / no-scale",
            status=CheckStatus.FAIL,
            message="Dimensionful couplings were not listed.",
        )
    return CheckResult(
        name="Spacetime: dimensional / no-scale",
        status=CheckStatus.PASS,
        message="No-scale leftover is still a free f. Unique action remains NO.",
    )


def check_st_mixed_convention(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: mixed-convention trap",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    plus = mixed_convention_hamiltonian_coeff(MOSTLY_PLUS)
    minus = mixed_convention_hamiltonian_coeff(MOSTLY_MINUS)
    if sp.simplify(plus - sp.Rational(1, 2)) != 0:
        return CheckResult(
            name="Spacetime: mixed-convention trap",
            status=CheckStatus.FAIL,
            message="Unadapted F=-X/2 should be ghost-free in mostly_plus.",
        )
    if sp.simplify(minus + sp.Rational(1, 2)) != 0:
        return CheckResult(
            name="Spacetime: mixed-convention trap",
            status=CheckStatus.FAIL,
            message="Unadapted F=-X/2 on mostly_minus must flip the Hamiltonian sign.",
        )
    return CheckResult(
        name="Spacetime: mixed-convention trap",
        status=CheckStatus.PASS,
        message="Keeping F=-X/2 while flipping eta is a mix error, not a new theory.",
    )


def check_st_euclidean(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: Euclidean branch",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    if volume_element(EUCLIDEAN) != "sqrt(g)":
        return CheckResult(
            name="Spacetime: Euclidean branch",
            status=CheckStatus.FAIL,
            message="Euclidean volume element should be sqrt(g).",
        )
    if eta_diag(EUCLIDEAN) == eta_diag(MOSTLY_PLUS) or eta_diag(EUCLIDEAN) == eta_diag(MOSTLY_MINUS):
        return CheckResult(
            name="Spacetime: Euclidean branch",
            status=CheckStatus.FAIL,
            message="Euclidean metric collapsed onto a Lorentzian signature.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    if "separate" not in str(data.get("euclidean_branch", "")).lower():
        return CheckResult(
            name="Spacetime: Euclidean branch",
            status=CheckStatus.FAIL,
            message="Euclidean was not kept as a separate branch.",
        )
    return CheckResult(
        name="Spacetime: Euclidean branch",
        status=CheckStatus.PASS,
        message="Euclidean is a separate formulation, not a Lorentzian signature.",
    )


def check_st_banned_tokens(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "spacetime.py",
        root / "geometry" / "minkowski.py",
        root / "models" / "examples" / "spacetime_model.py",
        root / "reporting" / "spacetime_report.py",
        root / "tests" / "spacetime_test.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha",
        "char" + "ge",
        "electr" + "ic",
        "ma" + "ss",
    )
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    if hits:
        return CheckResult(
            name="Spacetime: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Spacetime: banned tokens",
        status=CheckStatus.PASS,
        message="No banned tokens in Phase 3 sources.",
    )


def check_st_eom_ostro(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    ex = data.get("examples") or {}
    if (ex.get("L2") or {}).get("eom_order") != 2:
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L2 must remain second order.",
        )
    if (ex.get("L4") or {}).get("ostrogradsky") != "Ostrogradsky applicable":
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L4 should trigger Ostrogradsky applicable.",
        )
    if "degeneracy" not in str((ex.get("L5") or {}).get("ostrogradsky", "")).lower() and (
        "avoided" not in str((ex.get("L5") or {}).get("ostrogradsky", "")).lower()
    ):
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L5 should avoid Ostrogradsky by degeneracy.",
        )
    l5 = ex.get("L5") or {}
    if l5.get("higher_derivative_in_L") != "YES":
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L5 must remain higher-derivative in L.",
        )
    if l5.get("hessian_degenerate") != "YES" or l5.get("eom_higher_order") != "NO":
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L5 Hessian/EOM classification failed the explicit identities.",
        )
    if l5.get("ostrogradsky_instability") != "NO":
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L5 Ostrogradsky instability is not NO after the identities.",
        )
    if not l5.get("ibp_holds") or not l5.get("equivalent_el_match"):
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="L5 IBP or equivalent-EL identity failed.",
        )
    data_fd = result.metadata.get("spacetime_analysis") or {}
    if (data_fd.get("first_derivative_class") or {}).get("status") != "COMPLETE AT FIRST-DERIVATIVE SCALAR LEVEL":
        return CheckResult(
            name="Spacetime: EOM order and Ostrogradsky",
            status=CheckStatus.FAIL,
            message="First-derivative Lorentz class is not complete.",
        )
    return CheckResult(
        name="Spacetime: EOM order and Ostrogradsky",
        status=CheckStatus.PASS,
        message="L2: second-order non-quadratic. L4: Ostrogradsky. L5: degenerate, second-order EOM.",
    )



def check_st_covariance(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    plus = volume_element(MOSTLY_PLUS)
    minus = volume_element(MOSTLY_MINUS)
    if plus != "sqrt(-g)" or minus != "sqrt(-g)":
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="Lorentzian volume element should be sqrt(-g) in both signatures.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    curved = data.get("curved") or {}
    if curved.get("Einstein_equations") != "NOT ASSUMED":
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="Einstein equations were not kept out of this branch.",
        )
    if curved.get("dynamical_metric") != "NO":
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="A dynamical metric was introduced.",
        )
    if curved.get("dynamical_gravity") != "NOT YET TESTED":
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="Dynamical gravity was not left untested.",
        )
    if curved.get("delta_S_delta_g") != "NON USATO COME EQUAZIONE DINAMICA":
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="delta S / delta g was used as a dynamical equation.",
        )
    if "generally covariant matter theory on a fixed background" not in str(curved.get("label", "")):
        return CheckResult(
            name="Spacetime: general covariance branch",
            status=CheckStatus.FAIL,
            message="Covariance was not labelled as a matter theory on a fixed background.",
        )
    return CheckResult(
        name="Spacetime: general covariance branch",
        status=CheckStatus.PASS,
        message="Generally covariant matter theory on a fixed background. Not dynamical gravity.",
    )


def check_st_unique(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: uniqueness",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    if data.get("unique_action") != "NO" or data.get("unique_kinetic_structure") != "NO":
        return CheckResult(
            name="Spacetime: uniqueness",
            status=CheckStatus.FAIL,
            message="Uniqueness was claimed.",
        )
    if data.get("canonical_kinetic_term") != "NOT SELECTED":
        return CheckResult(
            name="Spacetime: uniqueness",
            status=CheckStatus.FAIL,
            message="Canonical kinetic term was selected.",
        )
    if data.get("quantum_unitarity") != "UNTESTED":
        return CheckResult(
            name="Spacetime: uniqueness",
            status=CheckStatus.FAIL,
            message="Quantum unitarity was not left UNTESTED.",
        )
    return CheckResult(
        name="Spacetime: uniqueness",
        status=CheckStatus.PASS,
        message="unique action NO. quadratic kinetic NOT SELECTED. Quantum unitarity UNTESTED.",
    )


def check_st_cross_signature(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: cross-signature equivalence",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    a = analyze_spacetime(signature=MOSTLY_PLUS)
    b = analyze_spacetime(signature=MOSTLY_MINUS)
    if a["unique_action"] != b["unique_action"]:
        return CheckResult(
            name="Spacetime: cross-signature equivalence",
            status=CheckStatus.FAIL,
            message="Uniqueness classification changed with signature.",
        )
    if a["examples"]["L1"]["classical_ghost"] != b["examples"]["L1"]["classical_ghost"]:
        return CheckResult(
            name="Spacetime: cross-signature equivalence",
            status=CheckStatus.FAIL,
            message="Adapted L1 ghost classification differs across signatures.",
        )
    if classify_m2(1) != "ordinary_m2" or classify_m2(-1) != "tachyonic_m2":
        return CheckResult(
            name="Spacetime: cross-signature equivalence",
            status=CheckStatus.FAIL,
            message="m2 classification mismatch.",
        )
    if eta_diag(MOSTLY_PLUS) == eta_diag(MOSTLY_MINUS):
        return CheckResult(
            name="Spacetime: cross-signature equivalence",
            status=CheckStatus.FAIL,
            message="The two signatures collapsed.",
        )
    return CheckResult(
        name="Spacetime: cross-signature equivalence",
        status=CheckStatus.PASS,
        message="Adapted actions keep the same physical classification across signatures.",
    )


def check_st_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Spacetime: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to spacetime Phase 3.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Spacetime: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Spacetime: experimental firewall",
            status=CheckStatus.FAIL,
            message="DerivationContext still active after solve.",
        )
    data = result.metadata.get("spacetime_analysis") or {}
    if data.get("interpretation") != "UNTESTED":
        return CheckResult(
            name="Spacetime: experimental firewall",
            status=CheckStatus.FAIL,
            message="An external interpretation was assigned.",
        )
    return CheckResult(
        name="Spacetime: experimental firewall",
        status=CheckStatus.PASS,
        message="No EXPERIMENTAL values. Interpretation UNTESTED.",
    )
