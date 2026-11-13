"""Independent Phase 5B.0 checks: gate, algebras, Noether, bans."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5b0_symmetry import (
    analyze_frozen_action_symmetry,
    noether_breaking_on_test_copy,
)


def test_independent_algebras_and_noether():
    auth = authorize_phase5b0_analysis()
    sci = analyze_frozen_action_symmetry(auth)
    cur = sci["noether_current"]
    assert sci["action_integrity"] == "VERIFIED"
    assert sci["final_action_hash"] == auth.action_content_hash
    assert sci["levels"]["E_full_frozen_action"] == "so(2)"
    assert sci["levels"]["B_kinetic"] == "so(3)"
    assert sci["finite_SO2_leaves_H_int"] is True
    assert sci["L12_breaks_H_int_form"] is True
    assert cur["on_shell_conservation"] is True
    assert cur["on_shell_conservation_curved"] is True
    assert cur["C"] == 2
    assert cur["kinetic_z_prefactor"] == 1
    assert cur["conservation_law_curved"] == "nabla_mu j^mu = 0"
    assert cur["conservation_law_flat_limit"] == "partial_mu j^mu = 0"
    assert cur["existence_basis_independent"] is True
    assert cur["Q_Noether_identified_as_em"] is False
    assert cur["frozen_action_modified"] is False
    assert sci["phase_5b0_closed"] is True
    assert sci["gravity_changed"] is False
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"
    assert ver["action_content_hash"] == sci["action_content_hash"]


def test_independent_breaking_copy_does_not_touch_freeze():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    k23 = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    diag = noether_breaking_on_test_copy(k23)
    after = freeze_path.read_bytes()
    assert before == after
    assert diag["test_copy_only"] is True
    assert diag["frozen_baseline_modified"] is False
    assert diag["nabla_mu_j_mu_vanishes"] is False


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5b0_symmetry.py",
        root / "physics" / "phase5b0_gate.py",
        root / "models" / "examples" / "phase5b0_model.py",
        root / "reporting" / "phase5b0_report.py",
        root / "physics" / "phase4c_action_freeze.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
