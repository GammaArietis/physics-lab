"""Reports for the S¹ vs S¹+C3 internal-structure experiment.

No overall score.  No claim that one model is better.  Fractional
numerical structure, if present, is not automatically electric charge.
"""

from __future__ import annotations

from collections import defaultdict

from physics_lab.core.model import Model
from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner, table


def format_fractional_spectrum_report(result: ModelResult) -> str:
    data = result.metadata.get("c3_fractional_spectrum")
    if not data:
        return ""
    op_rows = []
    for op in data.get("operators", []):
        herm = "YES" if op.get("hermitian") else "NO"
        uniq = "YES" if op.get("unique") else "NO"
        op_rows.append(
            [
                op.get("name"),
                herm,
                op.get("spectrum_kind"),
                ", ".join(str(v) for v in op.get("spectrum_values", [])),
                op.get("provenance"),
                uniq,
            ]
        )
    algebra = data.get("projector_algebra", {})
    lines = [
        banner("C3 FRACTIONAL SPECTRUM TEST", width=44),
        "",
        "S¹ integer spectrum:",
        data.get("integer_spectrum", ""),
        "",
        "C3 phases:",
        "   " + ", ".join(str(p) for p in data.get("c3_phases", [])),
        "   (eigenvalues of the unitary T, not of a Hermitian observable)",
        "",
        "C3 sectors:",
        data.get("c3_sectors", ""),
        "",
        "Projectors:",
        data.get("projector_formula", ""),
        f"   P_r P_s = δ_rs P_r: {'YES' if algebra.get('idempotent_orthogonal') else 'FAIL'}",
        f"   Σ_r P_r = I: {'YES' if algebra.get('resolution_of_identity') else 'FAIL'}",
        "   Spectrum of each P_r: {0, 1}",
        "",
        "Natural Hermitian observables:",
        table(
            ["operator", "Hermitian", "spectrum kind", "values", "provenance", "unique"],
            op_rows,
            widths=[22, 10, 18, 28, 28, 8],
        ),
        "",
        "A. integer spectrum  —  n ∈ Z from J and S¹.",
        "B. fractional phases —  exp(2π i r/3) from T.  Not Hermitian eigenvalues.",
        "C. fractional eigenvalues —  Hermitian spectrum in Q.",
        "   A, B, C are not equivalent.",
        "",
        "Uniqueness probes (ASSUMED families, not selected by the structure):",
        *[f"   {line}" for line in data.get("family_example_spectra", [])],
        "",
        "Fractional eigenvalues:",
        data.get("fractional_eigenvalues", "UNTESTED"),
        "",
        "Unique derivation:",
        data.get("unique_derivation", "UNTESTED"),
        "",
        "Free normalization:",
        data.get("free_normalization", "UNTESTED"),
        "",
        "Interpretation as electric charge:",
        data.get("charge_interpretation", "UNTESTED"),
        "",
        data.get("conclusion", ""),
        "",
        "=" * 44,
    ]
    return "\n".join(lines)


def _n_list(result: ModelResult) -> list[int]:
    return [int(s.quantum_numbers["n"]) for s in result.spectrum.states if "n" in s.quantum_numbers]


def _unique_lambdas(result: ModelResult) -> list[float]:
    values = []
    seen: set[float] = set()
    for state in result.spectrum.states:
        val = round(state.eigenvalue.numeric(), 12)
        if val not in seen:
            seen.add(val)
            values.append(state.eigenvalue.numeric())
    return values


def _degeneracy_pattern(result: ModelResult) -> dict[str, int]:
    buckets: dict[float, list[int]] = defaultdict(list)
    for state in result.spectrum.states:
        if "n" not in state.quantum_numbers:
            continue
        n = int(state.quantum_numbers["n"])
        buckets[round(state.eigenvalue.numeric(), 12)].append(n)
    return {str(sorted(members)): len(members) for members in buckets.values()}


def _format_signed_ints(values: list[int]) -> str:
    positives = sorted({abs(v) for v in values if v != 0})
    parts = []
    if 0 in values:
        parts.append("0")
    for v in positives:
        if v in values and -v in values:
            parts.append(f"±{v}")
        elif v in values:
            parts.append(str(v))
        elif -v in values:
            parts.append(str(-v))
    return "\n   ".join(parts)


def format_exploration_report(model: Model, result: ModelResult) -> str:
    meta = result.metadata
    cubed = meta.get("c3_cubed_identity")
    cubed_text = "identity" if cubed else "FAIL"
    residue = meta.get("c3_residue_form")
    sectors = meta.get("c3_sectors")
    if residue:
        sector_text = "r = 0, 1, 2 with n = 3m + r\n   DERIVED FROM C3 SYMMETRY"
    elif sectors is None:
        sector_text = "FAIL/UNTESTED — C3 sectors were not computed."
    else:
        sector_text = f"FAIL/UNTESTED — observed labels {sectors}; residue form did not hold."

    fractional = meta.get("fractional_numerical_structure", "UNTESTED")
    frac_source = meta.get("fractional_structure_source", "")
    n_values = _n_list(result)
    deg = _degeneracy_pattern(result)
    deg_lines = ", ".join(f"{k} (g={g})" for k, g in deg.items())

    assumptions = [
        "H = p_ξ² on S¹ (MODEL ASSUMPTION).",
        "m² = C λ (ASSUMED). Mass mechanism unchanged.",
        "Plane-wave ansatz χ = exp(i k ξ) on the covering coordinate.",
        "C3 means the cyclic group of order 3; the generator is θ → θ + 2π/3.",
        "No charge operator. q = n/3 and q = r/3 are not defined.",
    ]
    free = [
        f"{p.name} = {p.value}  [{p.provenance.value}]"
        for p in result.parameters
        if p.is_free()
    ]
    derived = [
        "θ ~ θ + 2π  (S¹ identification).",
        "n ∈ Z from χ(θ+2π)=χ(θ) on plane waves.",
        "T χ_n = exp(2π i n / 3) χ_n.",
        f"T³ = {cubed_text}.",
        "C3 character sectors from matching T-phases to cube roots of unity."
        + (" Residue form n=3m+r follows." if residue else ""),
        "λ_n = (n ħ / R)² given H (same as S¹).",
    ]
    untested = [
        "That a C3 sector is an electric charge.",
        "That n/3 or r/3 is a physical charge quantum number.",
        "Any identification with quarks, QED, or α.",
        "Gravity, Higgs, and full QED (not implemented).",
    ]

    rows = []
    for state in result.spectrum.states:
        qn = state.quantum_numbers
        rows.append(
            [
                state.label,
                qn.get("n"),
                state.eigenvalue.numeric(),
                qn.get("c3_phase"),
                qn.get("c3_sector"),
                qn.get("degeneracy"),
                qn.get("c3_angle_over_2pi"),
                state.eigenvalue.provenance.value,
            ]
        )

    lines = [
        banner("INTERNAL STRUCTURE EXPLORATION", width=44),
        "",
        "Geometry:",
        "S¹",
        "",
        "Additional symmetry:",
        "C3",
        "",
        "Boundary condition:",
        "χ(θ+2π)=χ(θ)",
        "",
        "Derived integer quantization:",
        "n ∈ Z",
        "",
        "C3 transformation:",
        "T: θ → θ + 2π/3",
        "T χ_n(θ) = χ_n(θ + 2π/3) = exp(2π i n / 3) χ_n(θ)",
        "The phase depends on n.  It is not inserted as a charge.",
        "",
        "C3^3:",
        cubed_text,
        "",
        "Symmetry sectors:",
        sector_text,
        "",
        "Degeneracies:",
        deg_lines or "none recorded",
        "",
        "normalized spectrum (n, display window):",
        "   " + _format_signed_ints(n_values),
        "",
        "Hamiltonian eigenvalues λ_n (given H = p², ASSUMED):",
        "   " + ", ".join(f"{v:.8g}" for v in _unique_lambdas(result)),
        "",
        "C3 phases (distinct):",
        "   " + ", ".join(str(p) for p in meta.get("c3_distinct_phases", [])),
        "",
        "Observed fractional numerical structure:",
        fractional,
        "",
        "IMPORTANT:",
        '"fractional numerical structure" NON significa automaticamente fractional charge.',
        "",
        f"source = {'derived' if fractional == 'PRESENT' else 'none'}",
        frac_source,
        "",
        "State table",
        "-----------",
        table(
            ["state", "n", "eigenvalue", "C3 phase", "C3 sector", "degeneracy", "angle/2π", "λ origin"],
            rows,
            widths=[8, 6, 12, 22, 10, 11, 10, 10],
        ),
        "",
        "ASSUMPTIONS",
        *["  - " + a for a in assumptions],
        "",
        "FREE PARAMETERS",
        *(["  - " + a for a in free] if free else ["  (none)"]),
        "",
        "DERIVED RESULTS",
        *["  - " + a for a in derived],
        "",
        "UNTESTED INTERPRETATIONS",
        *["  - " + a for a in untested],
        "",
        "=" * 44,
    ]
    return "\n".join(lines)


def compare_s1_and_s1_c3(model_a: Model, result_a: ModelResult, model_b: Model, result_b: ModelResult) -> str:
    """Report only observable mathematical differences.  No score."""
    n_a = _n_list(result_a)
    n_b = _n_list(result_b)
    lam_a = [round(v, 12) for v in _unique_lambdas(result_a)]
    lam_b = [round(v, 12) for v in _unique_lambdas(result_b)]
    deg_a = _degeneracy_pattern(result_a)
    deg_b = _degeneracy_pattern(result_b)
    keys_a = sorted({k for s in result_a.spectrum.states for k in s.quantum_numbers})
    keys_b = sorted({k for s in result_b.spectrum.states for k in s.quantum_numbers})
    new_keys = [k for k in keys_b if k not in keys_a]
    same_n = n_a == n_b
    same_lam = lam_a == lam_b
    same_deg = deg_a == deg_b

    differences: list[str] = []
    if not same_n:
        differences.append(f"allowed n differ: A={n_a}  B={n_b}")
    if not same_lam:
        differences.append("Hamiltonian eigenvalue pattern differs.")
    if not same_deg:
        differences.append("λ-degeneracy pattern differs.")
    if new_keys:
        differences.append("B has additional state labels: " + ", ".join(new_keys))
    if "C3" in result_b.symmetries and "C3" not in result_a.symmetries:
        differences.append("B has a C3 action and character sectors; A does not.")
    if not differences:
        differences.append("No mathematical difference recorded in the compared fields.")

    charges_a = any(row.charge is not None for row in result_a.mass_charge_table)
    charges_b = any(row.charge is not None for row in result_b.mass_charge_table)

    lines = [
        banner("MODEL COMPARISON", width=44),
        "",
        "MODEL A:",
        "S¹",
        f"name: {result_a.name}",
        "",
        "MODEL B:",
        "S¹ + C3",
        f"name: {result_b.name}",
        "",
        "allowed states (n):",
        f"  A: {_format_signed_ints(n_a)}",
        f"  B: {_format_signed_ints(n_b)}",
        f"  same lattice in the display window: {'YES' if same_n else 'NO'}",
        "",
        "symmetry classes:",
        f"  A: {', '.join(result_a.symmetries) or '(none extra)'}",
        f"  B: {', '.join(result_b.symmetries) or '(none extra)'}",
        f"  B C3 sectors: {result_b.metadata.get('c3_sectors')}",
        "",
        "degeneracies of λ (from H = p²):",
        f"  A: {deg_a}",
        f"  B: {deg_b}",
        f"  same: {'YES' if same_deg else 'NO'}",
        "",
        "eigenvalue pattern:",
        f"  A unique λ: {lam_a}",
        f"  B unique λ: {lam_b}",
        f"  same: {'YES' if same_lam else 'NO'}",
        "",
        "charge operator:",
        f"  A assigned: {'YES' if charges_a else 'NO'}",
        f"  B assigned: {'YES' if charges_b else 'NO'}",
        "",
        "Observable mathematical differences:",
        *("  - " + d for d in differences),
        "",
        "No model is scored.  Neither model is declared better.",
        "=" * 44,
    ]
    return "\n".join(lines)


def new_properties_from_c3(result_s1: ModelResult, result_s1_c3: ModelResult) -> list[str]:
    """Facts present in S¹+C3 and absent from S¹."""
    props: list[str] = []
    if result_s1_c3.metadata.get("c3_cubed_identity"):
        props.append("A verified C3 action T: θ → θ+2π/3 with T³ = identity.")
    if result_s1_c3.metadata.get("c3_residue_form"):
        props.append(
            "States classified by C3 characters; n = 3m+r follows from matching "
            "T-phases to cube roots of unity."
        )
    phases = result_s1_c3.metadata.get("c3_distinct_phases") or []
    if phases:
        props.append(f"C3 transformation phases: {phases}.")
    if result_s1_c3.metadata.get("fractional_numerical_structure") == "PRESENT":
        props.append(
            "A fractional numerical structure appears in the C3 transformation "
            "data (phase angles n/3, cube roots of unity), not in a charge operator."
        )
    lam_same = [round(v, 12) for v in _unique_lambdas(result_s1)] == [
        round(v, 12) for v in _unique_lambdas(result_s1_c3)
    ]
    if lam_same:
        props.append(
            "The Hamiltonian spectrum {λ_n} is unchanged: C3 was added as a "
            "discrete map on existing S¹ states, not as a new H."
        )
    return props
