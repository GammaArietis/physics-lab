from __future__ import annotations

from physics_lab.search.smdr_backend import SMDRBackendError, parse_calc_all_output, target_blind_input_text


def test_target_blind_input_maps_w11_conventions() -> None:
    text = target_blind_input_text((0.02, 0.03, 0.04, 0.5, 0.01, 0.06))
    assert "SMDR_gp_in = 0.015491933384829669" in text
    assert "SMDR_lambda_in = 0.12" in text
    assert "SMDR_Delta_alpha_had_5_MZ_in = 0" in text
    assert "SMDR_Mt_pole" not in text


def test_parse_calc_all_headline_observables() -> None:
    output = """SMDR (Standard Model in Dimensional Regularization) v1.3
Mt = 172.4; Gammat = 1.3;
Mh = 125.2; Gammah = 0.003;
MZ = 91.1; GammaZ = 2.4;
MW = 80.3; GammaW = 2.0;
Sommerfeld fine structure and Fermi constants:
  alpha = 1/137.03599918; GFermi = 1.16637820 10^-5;
"""
    parsed = parse_calc_all_output(output)
    assert parsed["version"] == "1.3"
    assert parsed["top_pole_gev"] == 172.4
    assert parsed["higgs_pole_gev"] == 125.2
    assert parsed["alpha_sommerfeld_inverse"] == 137.03599918


def test_missing_headline_observables_are_not_a_success() -> None:
    error = SMDRBackendError("SMDR exited successfully but did not produce required headline observables")
    assert "required headline observables" in str(error)
