"""Independent Phase 11F-B: freeze identity, 11F-A and blocked 11F unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import (
    EXPECTED_INPUT_HASH,
    analyze_phase11fb_cluster_consequence,
)


def test_independent_consequence_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    audit = phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json"
    m1 = phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json"
    m2 = phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json"
    m3 = phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json"
    blocked = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "physics_lab"
        / "physics"
        / "phase11f_artifacts"
        / "PHASE_11F_M4_CLUSTER.json"
    )
    authz = phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json"
    m4_freeze = phase11fa_artifact_dir() / "PHASE_11F_M4_INPUT_FREEZE.json"
    before = {
        "freeze": freeze_path.read_bytes(),
        "syn": syn.read_bytes(),
        "audit": audit.read_bytes(),
        "m1": m1.read_bytes(),
        "m2": m2.read_bytes(),
        "m3": m3.read_bytes(),
        "blocked": blocked.read_bytes(),
        "authz": authz.read_bytes(),
        "m4_freeze": m4_freeze.read_bytes(),
    }
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11fb_cluster_consequence(auth)
    assert freeze_path.read_bytes() == before["freeze"]
    assert syn.read_bytes() == before["syn"]
    assert audit.read_bytes() == before["audit"]
    assert m1.read_bytes() == before["m1"]
    assert m2.read_bytes() == before["m2"]
    assert m3.read_bytes() == before["m3"]
    assert blocked.read_bytes() == before["blocked"]
    assert authz.read_bytes() == before["authz"]
    assert m4_freeze.read_bytes() == before["m4_freeze"]
    assert sci["status"] == "OK"
    assert sci["PHASE_11F_B_STATUS"] == "PARTIAL"
    assert sci["input_hash"] == EXPECTED_INPUT_HASH
    assert sci["MASSIVE_CLUSTER_STATUS"] == "VERIFIED"
    assert sci["MASSLESS_CLUSTER_STATUS"] == "PARTIAL"
    assert sci["UNIVERSAL_M4_COMPLETE"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11fb_cluster_consequence.py",
        root / "models" / "examples" / "phase11fb_model.py",
        root / "reporting" / "phase11fb_report.py",
        root / "tests" / "phase11fb_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11f" + "_cluster" not in text
        assert "analyze_phase11fa" + "_m4_authorization" not in text
        assert "analyze_phase11e" + "_vacuum" not in text
