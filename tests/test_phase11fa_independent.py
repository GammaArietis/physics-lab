"""Independent Phase 11F-A: freeze identity, 11F blocked artefact unchanged."""

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
from physics_lab.physics.phase11fa_m4_authorization import (
    EXPECTED_11F_M4_HASH,
    HUMAN_DECLARED_M4_INPUT,
    analyze_phase11fa_m4_authorization,
    input_hash,
)


def test_independent_authorization_freeze_and_parent_identity():
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
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_audit = audit.read_bytes()
    before_m1 = m1.read_bytes()
    before_m2 = m2.read_bytes()
    before_m3 = m3.read_bytes()
    before_blocked = blocked.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11fa_m4_authorization(auth, declared_input=HUMAN_DECLARED_M4_INPUT)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert audit.read_bytes() == before_audit
    assert m1.read_bytes() == before_m1
    assert m2.read_bytes() == before_m2
    assert m3.read_bytes() == before_m3
    assert blocked.read_bytes() == before_blocked
    assert sci["status"] == "OK"
    assert sci["PHASE_11F_A_STATUS"] == "AUTHORIZED"
    assert sci["M4_AUTHORIZATION_STATUS"] == "VERIFIED"
    assert sci["INPUT_FREEZE_STATUS"] == "VERIFIED"
    assert sci["M4_CONSEQUENCE_TEST_STATUS"] == "NOT_STARTED"
    assert sci["input_hash"] == input_hash(HUMAN_DECLARED_M4_INPUT)
    assert sci["baseline_hashes"]["phase11f_m4_hash"] == EXPECTED_11F_M4_HASH
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M5_ENABLED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11fa_m4_authorization.py",
        root / "models" / "examples" / "phase11fa_model.py",
        root / "reporting" / "phase11fa_report.py",
        root / "tests" / "phase11fa_test.py",
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
        assert "free" + "_scalar_cluster" not in text
        assert "analyze_phase11e" + "_vacuum" not in text
