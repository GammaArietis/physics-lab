"""Validator checks for Phase 4C internal Hilbert spectrum plus gravity."""

from __future__ import annotations

from pathlib import Path

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.internal_spectrum import (
    MOSTLY_MINUS,
    analyze_internal_spectrum,
    derived_spectrum,
    inner_product,
    orthonormality,
    probe_H_int,
    probe_operator_symbols,
    standard_onb,
)
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("internal_spectrum_test"))


def _data(result: ModelResult) -> dict:
    return result.metadata.get("internal_spectrum_analysis") or {}


def check_isp_eigenvalues(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: eigenvalues",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    lam_a, lam_b = probe_operator_symbols()
    spec = derived_spectrum(probe_H_int(lam_a, lam_b))
    values = [item["lambda"] for item in spec]
    if len(spec) != 3 or values.count(lam_a) != 1 or values.count(lam_b) != 2:
        return CheckResult(
            name="Internal spectrum: eigenvalues",
            status=CheckStatus.FAIL,
            message="Probe spectrum is not {lam_a} union {lam_b, lam_b}.",
        )
    data = _data(result)
    if "DERIVED GIVEN H_int" not in str(data.get("eigenvalues")):
        return CheckResult(
            name="Internal spectrum: eigenvalues",
            status=CheckStatus.FAIL,
            message="lambda_n provenance missing.",
        )
    return CheckResult(
        name="Internal spectrum: eigenvalues",
        status=CheckStatus.PASS,
        message="lambda_n are DERIVED GIVEN the INPUT operator H_int.",
    )


def check_isp_orthonormal(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: orthonormality",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    if data.get("orthonormal") is not True:
        return CheckResult(
            name="Internal spectrum: orthonormality",
            status=CheckStatus.FAIL,
            message="Standard ONB failed.",
        )
    lam_a, lam_b = probe_operator_symbols()
    spec = derived_spectrum(probe_H_int(lam_a, lam_b))
    if not orthonormality([item["xi"] for item in spec]):
        return CheckResult(
            name="Internal spectrum: orthonormality",
            status=CheckStatus.FAIL,
            message="Eigenbasis is not orthonormal.",
        )
    return CheckResult(
        name="Internal spectrum: orthonormality",
        status=CheckStatus.PASS,
        message="Internal eigenbasis is orthonormal.",
    )


def check_isp_decomposition(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: mode decomposition",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    if "psi_n(x) xi_n" not in str(data.get("mode_expansion")):
        return CheckResult(
            name="Internal spectrum: mode decomposition",
            status=CheckStatus.FAIL,
            message="Mode expansion missing.",
        )
    if data.get("not_extra_dimension") is not True:
        return CheckResult(
            name="Internal spectrum: mode decomposition",
            status=CheckStatus.FAIL,
            message="Internal space was treated as an extra dimension.",
        )
    # Parseval on a generic vector.
    coeffs = list(probe_operator_symbols()) + [probe_operator_symbols()[0]]
    vec = coeffs[0] * standard_onb(3)[0] + coeffs[1] * standard_onb(3)[1] + coeffs[0] * standard_onb(3)[2]
    rec = sum((inner_product(e, vec) * e for e in standard_onb(3)), start=standard_onb(3)[0] * 0)
    if rec != vec:
        return CheckResult(
            name="Internal spectrum: mode decomposition",
            status=CheckStatus.FAIL,
            message="ONB reconstruction failed.",
        )
    return CheckResult(
        name="Internal spectrum: mode decomposition",
        status=CheckStatus.PASS,
        message="Phi = sum psi_n xi_n on a finite internal Hilbert space, not an extra dimension.",
    )


def check_isp_lambda_mass(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: lambda vs m_n2",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    if data.get("m_n2_equals_lambda_claimed") is not False:
        return CheckResult(
            name="Internal spectrum: lambda vs m_n2",
            status=CheckStatus.FAIL,
            message="m_n^2 = lambda_n was claimed as derived.",
        )
    if data.get("lambda_determines_m2_I", {}).get("follows") != "NO":
        return CheckResult(
            name="Internal spectrum: lambda vs m_n2",
            status=CheckStatus.FAIL,
            message="Branch I still tied m_n2 to lambda_n.",
        )
    mI = {str(r["m_n2"]) for r in data.get("effective_masses_I") or []}
    if len(mI) != 1:
        return CheckResult(
            name="Internal spectrum: lambda vs m_n2",
            status=CheckStatus.FAIL,
            message="Branch I masses were not mode-independent.",
        )
    if data.get("massive_modes", {}).get("m_equals_lambda") is not False:
        return CheckResult(
            name="Internal spectrum: lambda vs m_n2",
            status=CheckStatus.FAIL,
            message="INPUT probe forced m_n2 = lambda.",
        )
    return CheckResult(
        name="Internal spectrum: lambda vs m_n2",
        status=CheckStatus.PASS,
        message="m_n^2 = lambda_n is not derived. Branch I independent of lambda; branch II proportional with INPUT prefactor.",
    )


def check_isp_stress(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: T and conservation",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    if "DERIVED FROM ACTION" not in str(data.get("stress_energy")):
        return CheckResult(
            name="Internal spectrum: T and conservation",
            status=CheckStatus.FAIL,
            message="T^{(n)} was not derived from the action.",
        )
    if data.get("conservation_1p1_check") is not True:
        return CheckResult(
            name="Internal spectrum: T and conservation",
            status=CheckStatus.FAIL,
            message="On-shell conservation failed.",
        )
    if "2 c1 G" not in str(data.get("metric_field_equation")):
        return CheckResult(
            name="Internal spectrum: T and conservation",
            status=CheckStatus.FAIL,
            message="Metric EOM missing.",
        )
    return CheckResult(
        name="Internal spectrum: T and conservation",
        status=CheckStatus.PASS,
        message="T^{(n)} from delta S_n / delta g. Conservation on shell. Gravity sector unchanged.",
    )


def check_isp_modes(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    ml = data.get("massless_modes") or {}
    mv = data.get("massive_modes") or {}
    if ml.get("classification") != "massless linearized mode" or ml.get("m_n2") != 0:
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.FAIL,
            message="Massless probe failed.",
        )
    if ml.get("T00_wave_zero") is not False:
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.FAIL,
            message="Massless mode was given T=0.",
        )
    if mv.get("classification") != "massive linearized mode":
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.FAIL,
            message="Massive probe failed.",
        )
    if mv.get("T00_wave_zero") is not False:
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.FAIL,
            message="Massive mode was given T=0.",
        )
    if "Do not identify h with m_n^2" not in str(data.get("weak_field")):
        return CheckResult(
            name="Internal spectrum: massless / massive probes",
            status=CheckStatus.FAIL,
            message="Weak-field sourcing statement missing.",
        )
    return CheckResult(
        name="Internal spectrum: massless / massive probes",
        status=CheckStatus.PASS,
        message="Zero rest-mass parameter is not zero energy-momentum. Massive T sources h, not m_n2 itself.",
    )


def check_isp_basis(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: basis invariance / degeneracy",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    inv = data.get("basis_invariance") or {}
    if not (
        inv.get("U_orthogonal")
        and inv.get("spectrum_invariant")
        and inv.get("total_quadratic_form_invariant")
        and inv.get("rotated_basis_orthonormal")
    ):
        return CheckResult(
            name="Internal spectrum: basis invariance / degeneracy",
            status=CheckStatus.FAIL,
            message="Orthogonal invariance failed.",
        )
    if not (data.get("degeneracy") or {}).get("has_degeneracy"):
        return CheckResult(
            name="Internal spectrum: basis invariance / degeneracy",
            status=CheckStatus.FAIL,
            message="Degenerate subspace was not tested.",
        )
    return CheckResult(
        name="Internal spectrum: basis invariance / degeneracy",
        status=CheckStatus.PASS,
        message="Spectrum and total T are U-invariant. No preferred basis in a degenerate eigenspace.",
    )


def check_isp_uniqueness(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    data = _data(result)
    if data.get("common_spectral_origin_mode") != "YES":
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="Mode-level common origin was not YES.",
        )
    if data.get("common_spectral_origin_eigenvalue") != "NO":
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="Eigenvalue-only origin was claimed.",
        )
    if data.get("parameter_free_relation") != "NO" or data.get("unique_relation") != "NO":
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="A unique/parameter-free relation was claimed.",
        )
    if data.get("more_than_many_scalars") != "NO":
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="The tower was claimed to be more than many scalars plus gravity.",
        )
    if "does not yet produce new predictive gravitational structure" not in str(data.get("conclusion")):
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="Stop-criterion conclusion missing.",
        )
    other = analyze_internal_spectrum(signature=MOSTLY_MINUS)
    if other["parameter_free_relation"] != "NO" or other["common_spectral_origin_mode"] != "YES":
        return CheckResult(
            name="Internal spectrum: uniqueness / origin",
            status=CheckStatus.FAIL,
            message="Classification changed with signature.",
        )
    return CheckResult(
        name="Internal spectrum: uniqueness / origin",
        status=CheckStatus.PASS,
        message="Mode common origin YES; parameter-free map NO; still many scalars plus gravity.",
    )


def check_isp_ratio_audit(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    audit = (_data(result).get("spectral_ratio_audit") or {})
    scale = audit.get("scale") or {}
    tblock = audit.get("T_block") or {}
    br_I = audit.get("branch_I") or {}
    if audit.get("branch_II_ratio_holds") is not True:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Branch II mass-ratio identity failed.",
        )
    if audit.get("branch_II_ratio_provenance") != "DERIVED GIVEN ASSUMPTION":
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Mass-ratio provenance was not DERIVED GIVEN ASSUMPTION.",
        )
    if audit.get("promoted_to_full_theory_prediction") is not False:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="The ratio was promoted to a full-theory prediction.",
        )
    if audit.get("not_absolute_mass_prediction") is not True:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Mass ratios were treated as absolute mass predictions.",
        )
    if not (
        scale.get("all_m2_scale_with_c_H")
        and scale.get("all_m2_scale_with_Z_inverse")
        and scale.get("ratios_invariant_under_c_H")
        and scale.get("ratios_invariant_under_Z")
    ):
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="c_H/Z rescaling identities failed.",
        )
    if audit.get("degeneracy_masses_equal") is not True:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Degenerate eigenvalues did not share m_n^2 on Branch II.",
        )
    if tblock.get("block_sum_invariant") is not True or tblock.get("individual_T_basis_dependent") is not True:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Degenerate T block invariance failed.",
        )
    if audit.get("zero_mode_m2") != 0 or audit.get("zero_mode_T00_zero") is not False:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Zero-mode audit failed (m_n^2 or T_00).",
        )
    if br_I.get("mode_independent") is not True or br_I.get("equals_lambda_ratio") is not False:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="Branch I was claimed to depend nontrivially on lambda_n.",
        )
    if audit.get("new_physical_assumption") is not False:
        return CheckResult(
            name="Internal spectrum: ratio audit",
            status=CheckStatus.FAIL,
            message="A new physical assumption was introduced.",
        )
    return CheckResult(
        name="Internal spectrum: ratio audit",
        status=CheckStatus.PASS,
        message="Branch II mass ratios equal lambda ratios under the assumed linear H_int coupling. Not promoted to a full-theory prediction.",
    )


def check_isp_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "internal_spectrum.py",
        root / "models" / "examples" / "internal_spectrum_model.py",
        root / "reporting" / "internal_spectrum_report.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha",
        "char" + "ge",
        "electr" + "ic",
        "Hig" + "gs",
        "6." + "674",
        "from physics_lab.physics." + "constants",
    )
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{token} in {path.name}")
    data = _data(result)
    if data.get("chi_not") != "extra dimension":
        hits.append("extra-dimension denial missing")
    if data.get("interpretation") != "UNTESTED":
        hits.append("interpretation assigned")
    if data.get("c0") != "INPUT / FREE" or data.get("c1") != "INPUT / FREE":
        hits.append("c0 or c1 not free")
    if hits:
        return CheckResult(
            name="Internal spectrum: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Internal spectrum: banned tokens",
        status=CheckStatus.PASS,
        message="No banned coupling tokens. Internal space is not an extra dimension.",
    )


def check_isp_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Internal spectrum: experimental firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 4C.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental:
        return CheckResult(
            name="Internal spectrum: experimental firewall",
            status=CheckStatus.FAIL,
            message="EXPERIMENTAL parameters present.",
        )
    if derivation_is_active():
        return CheckResult(
            name="Internal spectrum: experimental firewall",
            status=CheckStatus.FAIL,
            message="Derivation context still active after solve.",
        )
    data = _data(result)
    if data.get("newton_G_used_to_fix_c1") is not False:
        return CheckResult(
            name="Internal spectrum: experimental firewall",
            status=CheckStatus.FAIL,
            message="c1 was fixed using newton_G.",
        )
    if data.get("G") != "FREE / PARAMETERIZATION only":
        return CheckResult(
            name="Internal spectrum: experimental firewall",
            status=CheckStatus.FAIL,
            message="G was not left as parameterization.",
        )
    return CheckResult(
        name="Internal spectrum: experimental firewall",
        status=CheckStatus.PASS,
        message="No experimental data. c0, c1, H_int parameters remain INPUT / FREE.",
    )
