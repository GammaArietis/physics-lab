"""Phase 12A kernel tests. Infrastructure and regression only."""

from __future__ import annotations

from pathlib import Path

from physics_lab.theory_kernel.engine import (
    HumanInputBoundary,
    ResourceBound,
    admit_theory,
    default_bounds,
    run_bounded_smoke,
    run_job,
    search_manifest,
)
from physics_lab.theory_kernel.epistemic import (
    KERNEL_VERSION,
    AuthorizationError,
    AuthorizationLedger,
    ProvenanceError,
    ProvenanceLedger,
    TargetAccessError,
    request_experimental_catalog,
    request_numerical_target,
)
from physics_lab.theory_kernel.equivalence import certify_rule, same_output_is_not_equivalence
from physics_lab.theory_kernel.ir import TheoryObject
from physics_lab.theory_kernel.phase12a import run_phase_12a, snapshot_existing_phases
from physics_lab.theory_kernel.reconstruction import reconstruct_laboratory
from physics_lab.theory_kernel.registries import ObligationStore, merge_symbols, proof_obligation
from physics_lab.theory_kernel.transformations import GrammarBoundary, declare_application

KERNEL = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "theory_kernel"
BANNED = ("1/137", "alpha_em", "interestingness")


def _manifest(seed: int = 0) -> dict:
    return search_manifest(
        run_id="phase12a-smoke",
        seed=seed,
        bounds=default_bounds(),
        enabled_transformations=["ADD_FIELD"],
        timestamp="PHASE_12A",
        policy="deterministic lexicographic",
        code_version=KERNEL_VERSION,
        test_version="phase12a-tests-v1",
    )


def test_theory_ir_and_hash_are_deterministic() -> None:
    lab = reconstruct_laboratory()
    theory = lab["objects"]["theory.4c"]
    again = TheoryObject(theory.document())
    assert theory.canonical() == again.canonical()
    assert theory.content_hash == again.content_hash


def test_child_does_not_mutate_parent() -> None:
    parent = reconstruct_laboratory()["objects"]["theory.scalar.canonical"]
    before = parent.canonical()
    job = run_job(
        parent=parent,
        transformation_id="ADD_FIELD",
        child_id="theory.scalar.canonical.child",
        meaning="infrastructure copy check",
        provenance="KERNEL_DECLARATION",
        seed=0,
        bounds=default_bounds(),
        generated_so_far=0,
        updates={"validation_state": "FORMALIZED"},
    )
    assert parent.canonical() == before
    assert job.child.content_hash != parent.content_hash
    assert job.payload["parent_hash"] == parent.content_hash


def test_reconstructed_provenance_is_preserved() -> None:
    lab = reconstruct_laboratory()
    ledger = lab["provenance"]
    assert isinstance(ledger, ProvenanceLedger)
    susy = lab["objects"]["theory.11s.susy"].document()["provenance"]
    assert susy[0]["provenance"] == "ASSUMED"
    try:
        ledger.promote_to_derived("theory.11s.susy:susy_test_extension")
    except ProvenanceError:
        return
    raise AssertionError("provenance was promoted")


def test_mediation_branches_and_order_parameters_stay_independent() -> None:
    lab = reconstruct_laboratory()
    branches = [
        "theory.11v.gravity_mediation",
        "theory.11x.gauge_mediation",
        "theory.11y.anomaly_mediation",
        "theory.11z.modulus_mediation",
        "theory.11aa.direct_mediation",
    ]
    registries = []
    for theory_id in branches:
        document = lab["objects"][theory_id].document()
        assert document["parent_theory_id"] == "theory.11t.susy_breaking"
        registries.append({item["parameter_id"] for item in document["parameter_registry"]})
    assert all(not left & right for index, left in enumerate(registries) for right in registries[index + 1 :])
    symbols = {
        theory_id: {item["symbol"] for item in lab["objects"][theory_id].document()["parameter_registry"]}
        for theory_id in branches
    }
    assert "F_X" in symbols["theory.11v.gravity_mediation"]
    assert "F_phi" in symbols["theory.11y.anomaly_mediation"]
    assert "F_T" in symbols["theory.11z.modulus_mediation"]
    assert "F_phi" not in symbols["theory.11v.gravity_mediation"]
    assert "F_X" not in symbols["theory.11y.anomaly_mediation"]
    assert lab["facts"]["identities"]["F_X_not_F_phi"] is True
    assert lab["facts"]["identities"]["F_X_not_F_T"] is True
    assert lab["facts"]["identities"]["F_T_not_F_phi"] is True
    left = lab["objects"]["theory.11v.gravity_mediation"].document()["parameter_registry"][0]
    right = lab["objects"]["theory.11x.gauge_mediation"].document()["parameter_registry"][0]
    try:
        merge_symbols(left, right)
    except Exception:
        return
    raise AssertionError("branch symbols were merged")


def test_kernel_has_no_target_access_or_resemblance_filter() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in KERNEL.glob("*.py"))
    for token in BANNED:
        assert token not in source
    try:
        request_experimental_catalog()
    except TargetAccessError:
        pass
    else:
        raise AssertionError("catalog request was accepted")
    try:
        request_numerical_target()
    except TargetAccessError:
        pass
    else:
        raise AssertionError("numerical target request was accepted")


def test_unsupported_equivalence_is_rejected() -> None:
    outcome = same_output_is_not_equivalence("theory.11v.gravity_mediation", "theory.11y.anomaly_mediation")
    assert outcome["outcome"] == "EQUIVALENCE_UNSUPPORTED"
    empty = certify_rule(rule_id="total derivative", certificate="", scope="missing certificate")
    assert empty["outcome"] == "EQUIVALENCE_UNSUPPORTED"


def test_partial_results_open_obligations_and_cannot_become_assumptions() -> None:
    lab = reconstruct_laboratory()
    store: ObligationStore = lab["obligations"]
    opened = [item for item in store.items() if item["current_status"] == "OPEN"]
    assert opened
    assert all(item["current_status"] != "FALSE" for item in store.items())
    try:
        store.convert_open_to_assumption(opened[0]["obligation_id"])
    except Exception:
        pass
    else:
        raise AssertionError("open obligation became an assumption")


def test_human_input_boundary_stops_extension() -> None:
    vacuum = reconstruct_laboratory()["objects"]["theory.vacuum.selection"]
    assert vacuum.validation_state == "REQUIRES_HUMAN_INPUT"
    values = {item["id"]: item["value"] for item in vacuum.document()["constraints"]}
    assert values["VACUUM_SELECTION"] == "NOT_FOUND"
    try:
        run_job(
            parent=vacuum,
            transformation_id="ADD_CONSTRAINT",
            child_id="theory.vacuum.selection.child",
            meaning="blocked",
            provenance="KERNEL_DECLARATION",
            seed=0,
            bounds=default_bounds(),
            generated_so_far=0,
        )
    except HumanInputBoundary:
        return
    raise AssertionError("human-input theory was extended")


def test_vacuum_and_pfr_and_parameters_stay_at_the_certified_boundary() -> None:
    lab = reconstruct_laboratory()
    constraints = {
        item["id"]: item["value"]
        for item in lab["objects"]["theory.vacuum.selection"].document()["constraints"]
    }
    assert constraints["VACUUM_SELECTION"] == "NOT_FOUND"
    assert constraints["global_minimum"] == "ABSENT"
    assert constraints["modulus_stabilization"] == "NOT_FOUND"
    assert constraints["stationary_point"] != constraints["selected_physical_vacuum"]
    assert lab["facts"]["pfr_count"] == 0
    origins = {
        item["origin"]
        for obj in lab["objects"].values()
        for item in obj.document()["parameter_registry"]
    }
    assert origins == {"preserved-record"}


def test_grammar_boundary_and_authorization_refusal() -> None:
    try:
        declare_application(
            "ADD_HIDDEN_SECTOR",
            parent_state="FORMALIZED",
            mathematical_meaning="undefined",
            provenance="KERNEL_DECLARATION",
            new_assumptions=[],
            new_parameters=[],
            changed_components=[],
        )
    except GrammarBoundary as exc:
        assert exc.status == "GRAMMAR_BOUNDARY_REACHED"
    else:
        raise AssertionError("unknown transformation was accepted")
    ledger = AuthorizationLedger()
    try:
        ledger.issue_new_physical_input()
    except AuthorizationError:
        return
    raise AssertionError("a new physical authorization was issued")


def test_bounded_smoke_terminates_and_is_reproducible() -> None:
    first = run_bounded_smoke(_manifest())
    second = run_bounded_smoke(_manifest())
    assert first == second
    assert first["stop"] == "DEPTH_REACHED"
    assert len(first["output_ids"]) <= 4


def test_repeated_theory_and_resource_bound() -> None:
    theory = reconstruct_laboratory()["objects"]["theory.4c"]
    visited: set[str] = set()
    assert admit_theory(visited, theory) == "ADMITTED"
    assert admit_theory(visited, TheoryObject(theory.document())) == "REPEATED_THEORY"
    try:
        run_job(
            parent=theory,
            transformation_id="ADD_FIELD",
            child_id="theory.4c.over_bound",
            meaning="bound",
            provenance="KERNEL_DECLARATION",
            seed=1,
            bounds={**default_bounds(), "max_generated_objects": 1},
            generated_so_far=1,
        )
    except ResourceBound as exc:
        assert exc.status == "RESOURCE_BOUND_REACHED"
    else:
        raise AssertionError("resource bound was ignored")


def test_phase12a_regression_does_not_change_existing_phases() -> None:
    before = snapshot_existing_phases()
    result = run_phase_12a(write_artifacts=True)
    after = snapshot_existing_phases()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_12A_STATUS"] == "COMPLETE"
    assert result["PHASE_12A_STOPPED"] is True
    assert result["THEORY_KERNEL_STATUS"] == "READY"
    assert result["THEORY_IR_STATUS"] == "VERIFIED"
    assert result["THEORY_HASH_STATUS"] == "VERIFIED"
    assert result["PROVENANCE_STATUS"] == "VERIFIED"
    assert result["AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["PARAMETER_REGISTRY_STATUS"] == "VERIFIED"
    assert result["DERIVED_QUANTITY_STATUS"] == "VERIFIED"
    assert result["PROOF_OBLIGATION_STATUS"] == "VERIFIED"
    assert result["EQUIVALENCE_ENGINE_STATUS"] == "VERIFIED"
    assert result["HUMAN_INPUT_FRONTIER_STATUS"] == "VERIFIED"
    assert result["RECURSIVE_ENGINE_STATUS"] == "READY"
    assert result["FRONTIER_STATUS"] == "READY"
    assert result["RESOURCE_BOUND_STATUS"] == "VERIFIED"
    assert result["TERMINATION_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["REGRESSION_RECONSTRUCTION_STATUS"] == "VERIFIED"
    assert result["EXISTING_THEORY_REPRODUCTION_STATUS"] == "VERIFIED"
    assert result["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["PFR_STATUS"] == "PRESERVED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["large_scale_scan"] is False
    assert result["experimental_data_used"] is False
    assert result["ranking_used"] is False
    assert len(result["questions"]) == 23
    labels = {row["existing_structure"] for row in result["regression_table"]}
    for required in ("Phase 4C", "Phase 5B.0", "Phase 5C", "Phase 5D", "Phase 11S", "Phase 11V", "Phase 11AA"):
        assert required in labels
    quantities = {row["quantity"] for row in result["parameter_report"]}
    for name in ("c0", "c1", "lam_a", "F_X", "F_phi", "F_T", "<T>", "W", "K", "Z_A", "g", "xi"):
        assert name in quantities
    assert proof_obligation(
        obligation_id="sample.open",
        theory_id="theory.4c",
        missing_statement="sample",
        dependencies=[],
        allowed_methods=[],
        forbidden_inputs=[],
        current_status="OPEN",
    )["current_status"] == "OPEN"
