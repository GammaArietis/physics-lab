"""Phase 4C: internal Hilbert spectrum plus gravity."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.internal_spectrum_model import build_internal_spectrum_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS, analyze_internal_spectrum
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_spectrum_origin_no_unique_relation_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_internal_spectrum_model(signature=sig).solve()
        data = result.metadata["internal_spectrum_analysis"]
        assert data["common_spectral_origin_mode"] == "YES"
        assert data["common_spectral_origin_eigenvalue"] == "NO"
        assert data["parameter_free_relation"] == "NO"
        assert data["unique_relation"] == "NO"
        assert data["more_than_many_scalars"] == "NO"
        assert data["c0"] == "INPUT / FREE"
        assert data["c1"] == "INPUT / FREE"
        assert data["m_n2_equals_lambda_claimed"] is False
        assert data["not_extra_dimension"] is True
        assert data["orthonormal"] is True
        assert data["spectrum_size"] == 3
        assert data["degeneracy"]["has_degeneracy"] is True
        assert data["massless_modes"]["T00_wave_zero"] is False
        assert data["massive_modes"]["T00_wave_zero"] is False
        assert data["massive_modes"]["m_equals_lambda"] is False
        assert data["conservation_1p1_check"] is True
        assert data["quantum_unitarity"] == "UNTESTED"
        assert "does not yet produce new predictive gravitational structure" in data["conclusion"]
        assert data["answers"]["2_spectrum_determines_m2"].startswith("NO")
        assert data["answers"]["5_parameter_free_relation"].startswith("NO")
        assert data["answers"]["9_more_than_many_scalars"].startswith("NO")
        audit = data["spectral_ratio_audit"]
        assert audit["branch_II_ratio_holds"] is True
        assert audit["branch_II_ratio_provenance"] == "DERIVED GIVEN ASSUMPTION"
        assert audit["promoted_to_full_theory_prediction"] is False
        assert audit["branch_I"]["equals_lambda_ratio"] is False
        assert audit["new_physical_assumption"] is False


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
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
        "from physics_lab.physics." + "constants",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "internal_spectrum.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Internal spectrum: eigenvalues",
        "Internal spectrum: orthonormality",
        "Internal spectrum: mode decomposition",
        "Internal spectrum: lambda vs m_n2",
        "Internal spectrum: T and conservation",
        "Internal spectrum: massless / massive probes",
        "Internal spectrum: basis invariance / degeneracy",
        "Internal spectrum: uniqueness / origin",
        "Internal spectrum: ratio audit",
        "Internal spectrum: banned tokens",
        "Internal spectrum: experimental firewall",
        "Action freeze: verified",
        "Action freeze: determinism",
        "Action freeze: no analysis leakage",
        "Action freeze: banned tokens",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "PHASE 4C — INTERNAL SPECTRUM + GRAVITY" in report.text
    assert "PHASE 4C.1 — INVARIANT SPECTRAL-RATIO AUDIT" in report.text
    assert "ACTION_SERIALIZER_CONTRACT:" in report.text
    assert "phase4c-action-v1" in report.text
    assert "SERIALIZER_STATUS:" in report.text
    assert "FREEZE_STATUS:" in report.text
    analysis = analyze_internal_spectrum(signature=MOSTLY_PLUS)
    assert analysis["parameter_free_relation"] == "NO"
    assert analysis["common_spectral_origin_mode"] == "YES"
