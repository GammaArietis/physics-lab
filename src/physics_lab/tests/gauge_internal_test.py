"""Validator checks for Phase 5A internal generator and gauge coupling."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.core.model import Model
from physics_lab.core.provenance import Provenance, derivation_is_active
from physics_lab.core.result import ModelResult
from physics_lab.physics.gauge_internal import (
    MOSTLY_MINUS,
    analyze_gauge_internal,
    candidate_ZA_from_trace,
    commutes,
    degeneracy_of_J,
    firewall_derived_with_free_coefficient,
    g_phys,
    hand_inserted_J_normalization,
    is_hermitian,
    j_spectrum,
    probe_H_int,
    probe_J_commuting,
    probe_J_degenerate,
    probe_J_noncommuting,
    probe_J_symbols,
    probe_operator_symbols,
    rescale_A_g_ZA,
    tr_J2,
)
from physics_lab.physics.internal_spectrum import degenerate_subspace_rotation, spectrum_invariant_under_U
from physics_lab.validation.checks import CheckResult, CheckStatus


def _phase(result: ModelResult) -> bool:
    return bool(result.metadata.get("gauge_internal_test"))


def _data(result: ModelResult) -> dict:
    return result.metadata.get("gauge_internal_analysis") or {}


def check_gi5_hermitian(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: Hermiticity",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    q_a, q_b, q_c = probe_J_symbols()
    mix = sp.symbols("j_mix", real=True)
    # Generic diagonal Hermitian is Hermitian as a complex matrix, but is NOT
    # accepted as a real U(1) generator. Physical J = -i K is Hermitian on H_C.
    from physics_lab.physics.gauge_representation import (
        J_from_K,
        canonical_K,
        is_hermitian as rep_hermitian,
        scale_symbol,
    )

    J_phys = J_from_K(canonical_K(scale_symbol()))
    ok = (
        is_hermitian(probe_J_commuting(q_a, q_b, q_c))
        and is_hermitian(probe_J_degenerate(q_a, q_b))
        and is_hermitian(probe_J_noncommuting(q_a, q_b, q_c, mix))
        and rep_hermitian(J_phys)
    )
    data = _data(result)
    if not ok or data.get("J_hermitian") is not True:
        return CheckResult(
            name="Gauge internal: Hermiticity",
            status=CheckStatus.FAIL,
            message="J probes are not Hermitian.",
        )
    if "DERIVED GIVEN" not in str(data.get("J_hermitian_provenance")):
        return CheckResult(
            name="Gauge internal: Hermiticity",
            status=CheckStatus.FAIL,
            message="Hermiticity of J = -i K was not labelled DERIVED GIVEN K.",
        )
    return CheckResult(
        name="Gauge internal: Hermiticity",
        status=CheckStatus.PASS,
        message="J = -i K is Hermitian on H_C. Derived from K^T = -K, not a generic Hermitian on R^3.",
    )


def check_gi5_eigenvalues(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: eigenvalues",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    from physics_lab.physics.gauge_representation import (
        J_from_K,
        canonical_K,
        complex_eigenvalues_of_J,
        scale_symbol,
    )

    spec = complex_eigenvalues_of_J(J_from_K(canonical_K(scale_symbol())))
    labels = {str(v) for v in spec}
    if labels != {"0", "q", "-q"}:
        return CheckResult(
            name="Gauge internal: eigenvalues",
            status=CheckStatus.FAIL,
            message="Physical spectrum is not {0, +q, -q}.",
        )
    data = _data(result)
    if data.get("q_n_provenance") != "DERIVED GIVEN REPRESENTATION":
        return CheckResult(
            name="Gauge internal: eigenvalues",
            status=CheckStatus.FAIL,
            message="q_n provenance missing.",
        )
    if "DERIVED GIVEN K" not in str(data.get("J_status")):
        return CheckResult(
            name="Gauge internal: eigenvalues",
            status=CheckStatus.FAIL,
            message="J was not obtained from K.",
        )
    return CheckResult(
        name="Gauge internal: eigenvalues",
        status=CheckStatus.PASS,
        message="Spectrum of J = -i K is {0, +q, -q}, DERIVED GIVEN the real U(1) representation. q is FREE.",
    )


def check_gi5_basis(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: basis invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    from physics_lab.physics.gauge_representation import J_from_K, aligned_K, canonical_K, scale_symbol

    q = scale_symbol()
    J = J_from_K(canonical_K(q))
    J_al = J_from_K(aligned_K(q))
    U = degenerate_subspace_rotation(sp.symbols("th", real=True))
    data = _data(result)
    if (
        not spectrum_invariant_under_U(J, U)
        or not spectrum_invariant_under_U(J_al, U)
        or data.get("J_spectrum_invariant") is not True
        or data.get("tr_J2_basis_invariant") is not True
    ):
        return CheckResult(
            name="Gauge internal: basis invariance",
            status=CheckStatus.FAIL,
            message="Spectrum or Tr(J^2) failed basis invariance.",
        )
    return CheckResult(
        name="Gauge internal: basis invariance",
        status=CheckStatus.PASS,
        message="The 1 oplus 2 class and the {0,+q,-q} multiset are invariant under allowed orthogonal conjugations.",
    )


def check_gi5_degeneracy(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: degeneracy",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    deg = data.get("degeneracy") or {}
    if "CONVENTION" not in str(deg.get("individual_labels")):
        return CheckResult(
            name="Gauge internal: degeneracy",
            status=CheckStatus.FAIL,
            message="Degenerate labels were treated as physical.",
        )
    if deg.get("has_degeneracy") is not False:
        return CheckResult(
            name="Gauge internal: degeneracy",
            status=CheckStatus.FAIL,
            message="The {0,+q,-q} complex spectrum was treated as degenerate.",
        )
    return CheckResult(
        name="Gauge internal: degeneracy",
        status=CheckStatus.PASS,
        message="The real 2-plane is a representation sector. After complexification, +/- q are 1D; the ONB in the 2-plane is CONVENTION.",
    )


def check_gi5_commutator(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: commutator",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    from physics_lab.physics.gauge_representation import aligned_K, canonical_K, commutes as k_commutes, scale_symbol

    lam_a, lam_b = probe_operator_symbols()
    H = probe_H_int(lam_a, lam_b)
    q = scale_symbol()
    data = _data(result)
    if k_commutes(H, canonical_K(q)):
        return CheckResult(
            name="Gauge internal: commutator",
            status=CheckStatus.FAIL,
            message="Canonical K was forced to commute with H_int.",
        )
    if not k_commutes(H, aligned_K(q)):
        return CheckResult(
            name="Gauge internal: commutator",
            status=CheckStatus.FAIL,
            message="Aligned K should commute with H_int.",
        )
    if data.get("H_int_K_commute_canonical") is not False or data.get("H_int_K_commute_aligned") is not True:
        return CheckResult(
            name="Gauge internal: commutator",
            status=CheckStatus.FAIL,
            message="Commutator record does not match the probes.",
        )
    if "ADDITIONAL ASSUMPTION" not in str(data.get("simultaneous_eigenstates")):
        return CheckResult(
            name="Gauge internal: commutator",
            status=CheckStatus.FAIL,
            message="Commutation was not labelled as an additional assumption.",
        )
    return CheckResult(
        name="Gauge internal: commutator",
        status=CheckStatus.PASS,
        message="[H_int, K]=0 is not automatic. Alignment with the degenerate 2-plane is ADDITIONAL ASSUMPTION / INPUT.",
    )


def check_gi5_gauge(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    gauging = data.get("gauging") or {}
    cov = data.get("gauge_covariance") or {}
    if gauging.get("law_provenance") != "CONVENTION":
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.FAIL,
            message="Gauge law was not labelled CONVENTION.",
        )
    if "1/g" in str(gauging.get("D_mu")) or "1/g" in str(gauging.get("A_prime")):
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.FAIL,
            message="The unused 1/g convention was mixed in.",
        )
    if cov.get("holds") is not True or data.get("matrix_covariance") is not True:
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.FAIL,
            message="D_mu covariance failed.",
        )
    if data.get("F_invariant") is not True:
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.FAIL,
            message="F_mu_nu invariance failed.",
        )
    if data.get("provenance", {}).get("D_covariance") != "DERIVED":
        return CheckResult(
            name="Gauge internal: gauge covariance",
            status=CheckStatus.FAIL,
            message="Covariance provenance is not DERIVED.",
        )
    return CheckResult(
        name="Gauge internal: gauge covariance",
        status=CheckStatus.PASS,
        message="Fixed convention: Psi' = exp[-i g ga J] Psi, A' = A + d ga. Covariance and F invariance hold.",
    )


def check_gi5_rescaling(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: field rescaling",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    g, Z_A = sp.symbols("g Z_A", real=True, positive=True)
    ok2 = rescale_A_g_ZA(g, Z_A, sp.Integer(2))["invariant"]
    ok7 = rescale_A_g_ZA(g, Z_A, sp.Integer(7))["invariant"]
    data = _data(result)
    if not ok2 or not ok7 or data.get("A_rescaling_invariant") is not True:
        return CheckResult(
            name="Gauge internal: field rescaling",
            status=CheckStatus.FAIL,
            message="A, g, Z_A rescaling failed.",
        )
    if data.get("J_rescaling", {}).get("gJ_invariant") is not True:
        return CheckResult(
            name="Gauge internal: field rescaling",
            status=CheckStatus.FAIL,
            message="g J invariance under J -> a J failed.",
        )
    if data.get("J_rescaling", {}).get("J_normalization_fixed_by_4C") is not False:
        return CheckResult(
            name="Gauge internal: field rescaling",
            status=CheckStatus.FAIL,
            message="J normalization was claimed fixed by 4C.",
        )
    return CheckResult(
        name="Gauge internal: field rescaling",
        status=CheckStatus.PASS,
        message="A -> a A, g -> g/a, Z_A -> Z_A/a^2 and J -> a J, g -> g/a leave the physical combinations invariant.",
    )


def check_gi5_canonical(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: canonical kinetic",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    if data.get("canonical_kinetic") is not True:
        return CheckResult(
            name="Gauge internal: canonical kinetic",
            status=CheckStatus.FAIL,
            message="Canonical identity -Z_A/4 F^2 = -1/4 F_c^2 failed.",
        )
    if data.get("Z_A") != "INPUT":
        return CheckResult(
            name="Gauge internal: canonical kinetic",
            status=CheckStatus.FAIL,
            message="Z_A is not INPUT.",
        )
    return CheckResult(
        name="Gauge internal: canonical kinetic",
        status=CheckStatus.PASS,
        message="A_c = sqrt(Z_A) A puts S_A in canonical form. Z_A remains INPUT.",
    )


def check_gi5_gphys(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: g_phys invariance",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    g, Z_A = sp.symbols("g Z_A", real=True, positive=True)
    combo = g_phys(g, Z_A)
    data = _data(result)
    if sp.simplify(combo - g / sp.sqrt(Z_A)) != 0:
        return CheckResult(
            name="Gauge internal: g_phys invariance",
            status=CheckStatus.FAIL,
            message="g_phys is not g/sqrt(Z_A).",
        )
    if data.get("g_phys_derived") is not False or data.get("g_phys_provenance") != "PARAMETER-DEPENDENT":
        return CheckResult(
            name="Gauge internal: g_phys invariance",
            status=CheckStatus.FAIL,
            message="g_phys was mislabelled as derived.",
        )
    return CheckResult(
        name="Gauge internal: g_phys invariance",
        status=CheckStatus.PASS,
        message="g_phys = g/sqrt(Z_A) is invariant under the field rescaling and remains PARAMETER-DEPENDENT.",
    )


def check_gi5_invariants(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    from physics_lab.physics.gauge_representation import J_from_K, canonical_K, scale_symbol

    J = J_from_K(canonical_K(scale_symbol()))
    C = sp.symbols("C", real=True, positive=True)
    cand = candidate_ZA_from_trace(J, C)
    data = _data(result)
    if cand.get("Z_A_derived") is not False or cand.get("overall_coefficient_free") is not True:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Tr(J^2) candidate was treated as a derived Z_A.",
        )
    if cand.get("normalization_invariant") is not False:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Tr(J^2) was labelled generator-normalization invariant.",
        )
    if data.get("tr_J2_normalization_invariant") is not False:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Analysis claimed Tr(J^2) is invariant under J -> a J.",
        )
    if data.get("ZA_candidate_Q_rep", {}).get("Z_A_derived") is not False:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Tr(Q_rep^2) was used to derive Z_A.",
        )
    if data.get("ZA_candidate_Q_rep", {}).get("overall_coefficient_free") is not True:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="C in C * Tr(Q_rep^2) was not left free.",
        )
    if data.get("ZA_candidate", {}).get("Z_A_derived") is not False:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Analysis labelled Z_A derived from Tr(J^2).",
        )
    if data.get("ZA_candidate_spectral_sum", {}).get("equals_C_tr_J2") is not True:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Spectral sum is not Tr(J^2).",
        )
    if tr_J2(J) == 0:
        return CheckResult(
            name="Gauge internal: internal invariants",
            status=CheckStatus.FAIL,
            message="Tr(J^2) vanished identically on the symbolic probe.",
        )
    return CheckResult(
        name="Gauge internal: internal invariants",
        status=CheckStatus.PASS,
        message="Tr(J^2) is basis invariant, not normalization invariant. Tr(Q_rep^2)=g^2 Tr(J^2) does not fix Z_A.",
    )


def check_gi5_provenance(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: provenance labels",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    prov = data.get("provenance") or {}
    expected = {
        "K": "INPUT / ASSUMED",
        "J": "DERIVED GIVEN K and complexification",
        "q": "FREE / INPUT",
        "q_n": "DERIVED GIVEN REPRESENTATION",
        "g": "INPUT",
        "Z_A": "INPUT",
        "g_phys": "PARAMETER-DEPENDENT",
        "gauge_law": "CONVENTION",
        "D_covariance": "DERIVED",
        "F_invariance": "DERIVED",
        "complexification": "ASSUMPTION / CONVENTION",
    }
    hits = [k for k, v in expected.items() if prov.get(k) != v]
    if data.get("unique_generator") != "NO" or data.get("Z_A_derived") is not False:
        hits.append("unique generator or Z_A derived")
    if data.get("generic_diagonal_accepted") is not False:
        hits.append("generic diagonal accepted")
    if data.get("predictivity") != "NO":
        hits.append("predictivity")
    if hits:
        return CheckResult(
            name="Gauge internal: provenance labels",
            status=CheckStatus.FAIL,
            message="Mislabelled: " + ", ".join(hits),
        )
    return CheckResult(
        name="Gauge internal: provenance labels",
        status=CheckStatus.PASS,
        message="K and q INPUT; J DERIVED GIVEN K; relative {0,+q,-q} DERIVED GIVEN REPRESENTATION; g_phys PARAMETER-DEPENDENT.",
    )


def check_gi5_firewall(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    if firewall_derived_with_free_coefficient("DERIVED", True) is not True:
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Free coefficient labelled DERIVED was not detected.",
        )
    if firewall_derived_with_free_coefficient("PARAMETER-DEPENDENT", True) is not False:
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Legal PARAMETER-DEPENDENT label was rejected.",
        )
    if data.get("illegal_derived_ZA") is not True:
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Analysis did not flag an illegal DERIVED Z_A.",
        )
    if "CONVENTION" not in str(hand_inserted_J_normalization(unit_trace_imposed=True)):
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Hand-inserted J normalization was not flagged.",
        )
    if data.get("unit_trace_is_derived") is not False:
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Unit-trace J was labelled DERIVED.",
        )
    experimental = [p.name for p in result.parameters if p.provenance is Provenance.EXPERIMENTAL]
    if experimental or derivation_is_active():
        return CheckResult(
            name="Gauge internal: provenance firewall",
            status=CheckStatus.FAIL,
            message="Experimental leak or live derivation context.",
        )
    return CheckResult(
        name="Gauge internal: provenance firewall",
        status=CheckStatus.PASS,
        message="Labelling Z_A or a hand-inserted J normalization as DERIVED is detected and rejected.",
    )


def check_gi5_gravity(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    if data.get("gravity_changed") != "NO":
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.FAIL,
            message="Gravity family was changed.",
        )
    if data.get("c0") != "INPUT / FREE" or data.get("c1") != "INPUT / FREE":
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.FAIL,
            message="c0 or c1 not free.",
        )
    if data.get("c1_identified_with_ZA") is not False:
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.FAIL,
            message="c1 was identified with Z_A.",
        )
    if data.get("maxwell_wave_conservation") is not True:
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.FAIL,
            message="Gauge T conservation on a Maxwell wave failed.",
        )
    other = analyze_gauge_internal(signature=MOSTLY_MINUS)
    if other.get("gravity_changed") != "NO" or other.get("maxwell_wave_conservation") is not True:
        return CheckResult(
            name="Gauge internal: gravity",
            status=CheckStatus.FAIL,
            message="Mostly-minus gravity consistency failed.",
        )
    return CheckResult(
        name="Gauge internal: gravity",
        status=CheckStatus.PASS,
        message="S_gravity unchanged. T_gauge from S_A is conserved on EOM. c1 is not Z_A.",
    )


def check_gi5_banned(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: banned tokens",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    root = Path(__file__).resolve().parents[1]
    files = [
        root / "physics" / "gauge_internal.py",
        root / "physics" / "gauge_representation.py",
        root / "physics" / "gauge_compactness.py",
        root / "models" / "examples" / "gauge_internal_model.py",
        root / "reporting" / "gauge_internal_report.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
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
    if data.get("experimental_constants") is not False:
        hits.append("experimental constants used")
    if data.get("searched_familiar_values") is not False:
        hits.append("familiar values searched")
    if data.get("chi_not") != "extra dimension":
        hits.append("extra-dimension denial missing")
    if hits:
        return CheckResult(
            name="Gauge internal: banned tokens",
            status=CheckStatus.FAIL,
            message="; ".join(hits),
        )
    return CheckResult(
        name="Gauge internal: banned tokens",
        status=CheckStatus.PASS,
        message="No inverse-coupling hunt, no experimental constants, no extra dimension.",
    )


def check_gi5_representation(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    audit = data.get("representation_audit") or {}
    reality = audit.get("reality") or {}
    if reality.get("genuinely_real") != "YES" or reality.get("implicitly_complex") != "NO":
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="Internal space was not treated as genuinely real.",
        )
    if reality.get("complexification_provenance") != (
        "ASSUMPTION / CONVENTION (not part of the 4C definition)"
    ):
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="Complexification was not labelled ASSUMPTION / CONVENTION.",
        )
    if audit.get("charpoly_1plus2") is not True:
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="1 oplus 2 was not derived from the antisymmetric charpoly.",
        )
    if audit.get("spectrum_labels") != "{0, +q, -q}":
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="Spectrum labels missing.",
        )
    if audit.get("q") != "FREE / INPUT":
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="q was not left FREE.",
        )
    if sp.simplify(audit.get("ratio_plus_over_minus") + 1) != 0:
        return CheckResult(
            name="Gauge internal: real representation",
            status=CheckStatus.FAIL,
            message="(+q)/(-q) was not derived.",
        )
    return CheckResult(
        name="Gauge internal: real representation",
        status=CheckStatus.PASS,
        message="Real 3D U(1) forces 1 oplus 2. After complexification, J has spectrum {0,+q,-q} with q FREE.",
    )


def check_gi5_negative_diagonal(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: reject generic diagonal",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    from physics_lab.physics.gauge_representation import generic_diagonal_J, rejects_generic_diagonal_as_real_u1

    qa, qb, qc = sp.symbols("q_a q_b q_c", real=True)
    report = rejects_generic_diagonal_as_real_u1(generic_diagonal_J(qa, qb, qc))
    data = _data(result)
    if report.get("accepted") is not False or data.get("generic_diagonal_accepted") is not False:
        return CheckResult(
            name="Gauge internal: reject generic diagonal",
            status=CheckStatus.FAIL,
            message="Generic diag(q_a, q_b, q_c) was accepted as a real U(1) on R^3.",
        )
    if report.get("manufactures_independent_spectrum") is not True:
        return CheckResult(
            name="Gauge internal: reject generic diagonal",
            status=CheckStatus.FAIL,
            message="Independent-spectrum manufacture was not flagged.",
        )
    return CheckResult(
        name="Gauge internal: reject generic diagonal",
        status=CheckStatus.PASS,
        message="Generic Hermitian diagonal J is rejected as a faithful real U(1) on R^3.",
    )


def check_gi5_compactness(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    compact = (_data(result).get("compactness_audit") or {})
    mp = compact.get("mapping") or {}
    if mp.get("mapping_holds") is not True or mp.get("J_equals_minus_i_K") is not True:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Pinned U = exp(-i ga Q_rep) algebra failed.",
        )
    if mp.get("physically_distinct") is not False:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="The two formulations were treated as physically distinct.",
        )
    if mp.get("g_absorbed_into_period") is not False:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="g was described as absorbed into the group parameter.",
        )
    if compact.get("equivalent_parameterizations") is not True:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Generator normalizations were not identified as equivalent parameterizations.",
        )
    probes = (compact.get("real") or {}).get("probes") or {}
    if probes.get("w_1") is not True or probes.get("w_2") is not True or probes.get("w_half") is not False:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Real exp(2 pi K)=I probes failed.",
        )
    if compact.get("real", {}).get("w_fixed_to_preferred_integer") is not False:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="w was normalized by hand.",
        )
    if compact.get("real", {}).get("w_inferred_integer_from_pinned") is not False:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Pinned compactness was used to infer w in Z.",
        )
    if "ADDITIONAL ASSUMPTION" not in str((compact.get("real") or {}).get("faithfulness")):
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Faithfulness was not labelled an additional assumption.",
        )
    mapping_text = str(mp.get("mapping")) + str((_data(result).get("answers_5a1") or {}).get("2_mapping"))
    if "Q_rep = g J" not in mapping_text:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Pinned mapping does not state Q_rep = g J.",
        )
    if "just absorbed" in mapping_text:
        return CheckResult(
            name="Gauge internal: compactness mapping",
            status=CheckStatus.FAIL,
            message="Forbidden absorption wording remains in the mapping.",
        )
    return CheckResult(
        name="Gauge internal: compactness mapping",
        status=CheckStatus.PASS,
        message="Pinned Q_rep = g J. Compactness constrains spectrum(Q_rep), not g or J separately.",
    )


def check_gi5_no_double_count(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    compact = (_data(result).get("compactness_audit") or {})
    if compact.get("double_count_illegal") is not True:
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Counting both q_n in Z and g q_n in Z as independent was not flagged.",
        )
    if compact.get("rescaling", {}).get("gJ_invariant") is not True:
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="gJ invariance under J -> a J, g -> g/a failed.",
        )
    if compact.get("g_phys_derived") is not False or compact.get("Z_A_derived") is not False:
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Compactness was used to label g_phys or Z_A derived.",
        )
    if compact.get("new_physical_prediction") is not False:
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Normalization equivalence was counted as a new prediction.",
        )
    if compact.get("compactness_fixes", {}).get("g_phys") != "NO":
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Compactness was claimed to fix g_phys.",
        )
    if compact.get("compactness_fixes", {}).get("q_n") != "NO (not in the pinned convention)":
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Pinned compactness was claimed to fix q_n.",
        )
    if compact.get("compactness_fixes", {}).get("g") != "NO":
        return CheckResult(
            name="Gauge internal: no double-count",
            status=CheckStatus.FAIL,
            message="Pinned compactness was claimed to fix g.",
        )
    return CheckResult(
        name="Gauge internal: no double-count",
        status=CheckStatus.PASS,
        message="q_n and g q_n are not independent compactness data. Compactness does not fix g_phys or Z_A.",
    )


def check_gi5_u1_lock(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: U(1) lock",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    compact = data.get("compactness_audit") or {}
    lock = data.get("locked_u1_convention") or compact.get("locked_u1_convention") or {}
    probes = compact.get("lock_tests") or {}
    real = compact.get("real") or {}
    gauging = data.get("gauging") or {}
    status = compact.get("final_status") or {}
    name = "Gauge internal: U(1) lock"

    if data.get("PINNED_Q_REP") != "g J" or lock.get("Q_rep") != "g J":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Pinned Q_rep is not g J.")
    if gauging.get("Q_rep") != "g J":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Gauge convention missing Q_rep = g J.")
    if probes.get("two_pi_periodicity_gw_integer") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="2 pi periodicity of pinned U failed.")
    if probes.get("Q_rep_equals_gJ") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Q_rep = g J failed.")
    if probes.get("spectrum_Q_rep_in_Z_when_gw_integer") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="spectrum(Q_rep) subset Z failed.")
    if probes.get("Q_rep_invariant_under_rescaling") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Q_rep is not invariant under J -> a J, g -> g/a.")
    dist = probes.get("qn_vs_gqn_vs_gphys_qn") or {}
    if dist.get("distinct_when_ZA_not_one") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="g q_n was conflated with g_phys q_n.")
    if (probes.get("canonical_field") or {}).get("A_c") != "sqrt(Z_A) A":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Canonical A_c = sqrt(Z_A) A is missing.")
    if probes.get("reject_compactness_implies_g_integer") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Failed to reject compactness => g integer.")
    if probes.get("reject_compactness_implies_qn_integer") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Failed to reject compactness => q_n integer when Q_rep = g J.")
    if real.get("do_not_infer_w_in_Z") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Pinned convention inferred w in Z.")
    required_prov = (
        "provenance_Q_rep",
        "provenance_compactness",
        "provenance_g",
        "provenance_J_scale",
        "provenance_qn",
        "provenance_gqn",
        "provenance_g_phys",
        "provenance_ZA",
    )
    missing = [k for k in required_prov if not lock.get(k)]
    if missing:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Missing provenance: " + ", ".join(missing))
    if data.get("provenance", {}).get("Q_rep") != "CONVENTION / DEFINITION of normalized representation":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Analysis provenance missing Q_rep DEFINITION.")
    if data.get("provenance", {}).get("compactness_of_Q_rep") != "DERIVED GIVEN compact U(1)":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Compactness of Q_rep provenance is wrong.")
    if data.get("provenance", {}).get("g_phys") != "PARAMETER-DEPENDENT":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="g_phys provenance is not PARAMETER-DEPENDENT.")
    if lock.get("group_parameter") != "alpha" or lock.get("local_gauge_parameter") != "alpha(x)":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="alpha was not set as the canonical 2 pi-periodic group parameter.")
    if lock.get("alpha_definition") != "canonical 2 pi-periodic group parameter":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="alpha was not defined as the canonical group parameter.")
    if real.get("simultaneous_w_in_Z_and_gw_in_Z") is not False:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="w in Z and g w in Z were imposed on the same w.")
    if gauging.get("g_absorbed_into_ga") != "NO":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="g was absorbed into alpha.")
    if lock.get("do_not_conflate") is None or "representation weight" not in str(lock.get("do_not_conflate")):
        return CheckResult(name=name, status=CheckStatus.FAIL, message="g q_n vs g_phys q_n distinction is missing.")
    if status.get("NEW_MECHANISM") != "NO":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Lock introduced a new mechanism.")
    if status.get("GRAVITY") != "UNCHANGED":
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Gravity was changed.")
    if compact.get("choice_map", {}).get("g_absorbed_into_period") is not False:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="choice_map still absorbs g into the period.")
    if data.get("degenerate_subspace_does_not_select_U1") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="lam_b degeneracy was used to select a U(1).")
    return CheckResult(
        name=name,
        status=CheckStatus.PASS,
        message="Locked: U(alpha)=exp(-i alpha Q_rep) with Q_rep = g J; g q_n is the representation weight; g_phys q_n is the canonical interaction.",
    )


def check_gi5_false_inferences(model: Model, result: ModelResult) -> CheckResult:
    if not _phase(result):
        return CheckResult(
            name="Gauge internal: rejected false inferences",
            status=CheckStatus.UNTESTED,
            message="This check applies to Phase 5A.",
        )
    data = _data(result)
    rejected = data.get("rejected_false_inferences") or {}
    bv = data.get("basis_versus_normalization") or {}
    name = "Gauge internal: rejected false inferences"
    expected_false = (
        "compactness_implies_g_fixed",
        "compactness_implies_qn_fixed",
        "compactness_implies_g_phys_fixed",
        "Tr_J2_implies_ZA_without_free_coefficient",
        "faithfulness_implies_unit_normalization",
        "basis_invariance_implies_normalization_invariance",
        "gqn_is_canonical_physical_coupling",
    )
    bad = [k for k in expected_false if rejected.get(k) is not False]
    if bad:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="False inferences not rejected: " + ", ".join(bad))
    if bv.get("gJ_invariant_under_normalization") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="gJ failed to stay invariant under J -> a J, g -> g/a.")
    if bv.get("gJ_matrix_equal_under_basis") is not False:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Basis conjugation was conflated with gJ invariance.")
    if bv.get("Tr_J2_basis_invariant") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Tr(J^2) lost basis invariance.")
    if bv.get("Tr_J2_normalization_invariant") is not False:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Tr(J^2) was treated as normalization invariant.")
    if bv.get("Tr_Q_rep2_equals_g2_Tr_J2") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Tr(Q_rep^2) is not g^2 Tr(J^2).")
    if bv.get("Z_A_from_Tr_J2_without_free_C") is not False:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Z_A was inferred from Tr(J^2) without free C.")
    if data.get("commutant", {}).get("degenerate_subspace_does_not_select_U1") is not True:
        return CheckResult(name=name, status=CheckStatus.FAIL, message="Degenerate subspace silently selected a U(1).")
    return CheckResult(
        name=name,
        status=CheckStatus.PASS,
        message="Rejected: compactness fixing g, q_n, or g_phys; Tr(J^2)=>Z_A; faithfulness=>|n|=1; basis=>normalization; g q_n as canonical coupling.",
    )
