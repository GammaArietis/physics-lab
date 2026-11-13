"""Phase 18D audits formalization and does not authorize a search."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18c_authorization_design import UNRESOLVED
from physics_lab.theory_kernel.phase18d_formalization_audit import (
    ARTIFACT_DIR_NAME,
    assign_coefficient,
    authorize_search,
    execute_search,
    run_phase_18d,
    select_action,
    select_theory,
    select_vacuum,
)

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"
STATES = {"FORMALIZATION_COMPLETE", "FORMALIZATION_PARTIAL", "FORMALIZATION_UNRESOLVED", "NOT_YET_SPECIFIABLE"}


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase18d_audits_formalization_without_authorizing_search() -> None:
    before = _prior()
    audit = (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes()
    proposal = (PHYSICS / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json").read_bytes()
    design = (PHYSICS / "phase18c_authorization_artifacts" / "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json").read_bytes()
    result = run_phase_18d(write_artifacts=True)
    repeated = run_phase_18d(write_artifacts=True)
    assert before == _prior()
    assert (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes() == audit
    assert (PHYSICS / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json").read_bytes() == proposal
    assert (PHYSICS / "phase18c_authorization_artifacts" / "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json").read_bytes() == design
    assert result["status"] == "OK"
    assert result["PHASE18D_STATUS"] == "COMPLETE"
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["SEARCH_ACTIVE"] is False
    assert result["ACTION_SELECTED"] is False
    assert result["VACUUM_SELECTED"] is False
    assert result["NEW_PHYSICAL_INPUT_ACTIVATED"] is False
    assert result["NUMERICAL_BOUNDS_INTRODUCED"] is False
    assert result["THEORY_SELECTED"] is False
    assert result["BOUND_AUTHORIZATION_STATUS"] == "NOT_AUTHORIZED"
    assert result["execution_status"] == "NOT_EXECUTED"
    records = result["formulation_records"]
    assert len(records) == 47
    assert len({item["FORMULATION_ID"] for item in records}) == 47
    assert all(item["FORMALIZATION_STATUS"] in STATES for item in records)
    assert all(item["BOUND_STATUS"] == "BOUND_MISSING" for item in records)
    assert all(item["READY_FOR_FINITE_BOUNDING"] is False for item in records)
    assert all(item["search_authorization"] == "NOT_AUTHORIZED" for item in records)
    assert all(item["numerical_value"] == "NOT_INTRODUCED" for item in records)
    assert all(item["copied_from_phase17c"] is False for item in records)
    assert all(isinstance(item["REQUIRES_NEW_PHYSICAL_INPUT"], dict) for item in records)
    assert all(item["REQUIRES_NEW_PHYSICAL_INPUT"]["empirical_constant_count"] == "NOT_DECIDED" for item in records)
    assert all(item["REQUIRES_NEW_PHYSICAL_INPUT"]["activated"] is False for item in records)
    assert result["selected_formulation"] == "NONE"
    assert result["equivalence_firewall"]["unresolved_ids"] == list(UNRESOLVED)
    assert result["equivalence_firewall"]["resolved_count"] == 0
    assert result["classification_counts"]["FORMALIZATION_COMPLETE"] == 0
    assert sum(result["classification_counts"].values()) == 47
    assert sum(row["formulation_count"] for row in result["class_summary"]) == 47
    assert all(row["ready_for_finite_bounding"] == 0 for row in result["class_summary"])
    finite = next(item for item in records if item["FORMULATION_ID"] == "g17b1.finite_algebra__not_yet_specifiable__0")
    assert finite["FINITE_ALGEBRA"]["multiplication_presentation_defined"] is False
    assert finite["FINITE_ALGEBRA"]["algebra_selected"] is False
    assert finite["OBSTACLE"]["E_BOUNDED_SEARCH_ONLY"] is False
    assert finite["OBSTACLE"]["primary"] == "A_MISSING_MATHEMATICAL_DEFINITION"
    rejoined = {
        "g17b1.weyl__other_formal_dynamics__1": "law for the length connection",
        "g17b1.projective__other_formal_dynamics__0": "law on unparameterized paths",
        "g17b1.riemann_cartan__constrained_action__1": "which structural relations are dynamical constraints",
        "g17b1.affine__other_formal_dynamics__0": "law for the affine connection",
        "g17b1.metric_affine__constrained_action__1": "constraint functional",
    }
    by_id = {item["FORMULATION_ID"]: item for item in records}
    for identifier, phrase in rejoined.items():
        assert by_id[identifier]["missing_phrase_storage"] == "CHARACTER_SEQUENCE_REJOINED"
        assert phrase in [item["item"] for item in by_id[identifier]["DATA_MISSING"]]
        assert "l" not in [item["item"] for item in by_id[identifier]["DATA_MISSING"]]
    others = [item for item in records if item["DYNAMICAL_CLASS"] == "OTHER_FORMAL_DYNAMICS"]
    assert others and all(item["DYNAMICAL_CLASS_RESOLUTION"] == "DYNAMICAL_CLASS_UNRESOLVED" for item in others)
    text = json.dumps(result)
    assert ("1/" + "137") not in text
    assert ("alp" + "ha_em") not in text
    assert result["VACUUM_SELECTION"] == "NOT_INSERTED"
    assert result["bound_firewall"]["numerical_values_introduced"] is False
    assert result["bound_firewall"]["copied_from_phase17c"] is False
    assert execute_search() == "NOT_PERFORMED"
    assert authorize_search() == "NOT_AUTHORIZED"
    assert select_theory() == "NOT_PERFORMED"
    assert select_action() == "NOT_PERFORMED"
    assert assign_coefficient() == "NOT_PERFORMED"
    assert select_vacuum() == "NOT_PERFORMED"
    assert repeated["audit_hash"] == result["audit_hash"]
    assert result["HISTORICAL_ARTIFACTS_MODIFIED"] is False
