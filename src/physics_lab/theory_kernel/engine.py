"""Bounded recursive engine, jobs, frontier, and search policy.

Phase 12A exposes the machinery. It does not enumerate a theory space.
"""

from __future__ import annotations

from typing import Any, Mapping

from physics_lab.theory_kernel.epistemic import (
    GRAMMAR_ID,
    GRAMMAR_VERSION,
    KERNEL_VERSION,
    AuditLog,
    EpistemicError,
    freeze_document,
)
from physics_lab.theory_kernel.ir import TheoryObject
from physics_lab.theory_kernel.registries import ObligationStore, proof_obligation
from physics_lab.theory_kernel.policy import TRAVERSAL_POLICIES
from physics_lab.theory_kernel.transformations import (
    GrammarBoundary,
    UnsupportedTransformation,
    apply_declared,
    declare_application,
)

PHASE_12A_OBJECT_CAP = 4


class ResourceBound(EpistemicError):
    status = "RESOURCE_BOUND_REACHED"


class HumanInputBoundary(EpistemicError):
    status = "REQUIRES_HUMAN_INPUT"


def default_bounds() -> dict[str, int]:
    return {
        "max_branch_depth": 2,
        "max_derivative_order": 2,
        "max_field_count": 4,
        "max_generated_objects": PHASE_12A_OBJECT_CAP,
        "max_memory": 1,
        "max_operator_count": 8,
        "max_runtime": 1,
    }


def search_manifest(
    *,
    run_id: str,
    seed: int,
    bounds: Mapping[str, int],
    enabled_transformations: list[str],
    timestamp: str,
    policy: str,
    code_version: str,
    test_version: str,
) -> dict[str, Any]:
    if policy not in TRAVERSAL_POLICIES:
        raise EpistemicError(f"unknown traversal policy {policy}")
    return freeze_document(
        {
            "bounds": dict(bounds),
            "code_version": code_version,
            "enabled_transformations": list(enabled_transformations),
            "grammar_version": GRAMMAR_VERSION,
            "kernel_version": KERNEL_VERSION,
            "policy": policy,
            "seed": seed,
            "test_version": test_version,
            "timestamp": timestamp,
            "SEARCH_RUN_ID": run_id,
        }
    )


class TheoryFrontier:
    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def add(self, entry: Mapping[str, Any]) -> None:
        stored = freeze_document(dict(entry))
        self._entries[stored["theory_id"]] = stored

    def entries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))


class JobResult:
    def __init__(self, payload: Mapping[str, Any], child: TheoryObject) -> None:
        self.payload = freeze_document(dict(payload))
        self.child = child


def extend_theory(
    parent: TheoryObject,
    *,
    transformation_id: str,
    child_id: str,
    meaning: str,
    provenance: str,
    updates: Mapping[str, Any] | None = None,
    new_assumptions: list[dict[str, Any]] | None = None,
    new_parameters: list[dict[str, Any]] | None = None,
) -> TheoryObject:
    """Return a child. The parent bytes stay as they were."""
    parent_bytes = parent.canonical()
    parent_hash = parent.content_hash
    application = declare_application(
        transformation_id,
        parent_state=parent.validation_state,
        mathematical_meaning=meaning,
        provenance=provenance,
        new_assumptions=list(new_assumptions or []),
        new_parameters=list(new_parameters or []),
        changed_components=list((updates or {}).keys()) or ["infrastructure"],
    )
    child_doc = apply_declared(parent.document(), application, dict(updates or {}))
    child_doc["theory_id"] = child_id
    child_doc["grammar_id"] = GRAMMAR_ID
    child_doc["grammar_version"] = GRAMMAR_VERSION
    child = TheoryObject(child_doc)
    if parent.canonical() != parent_bytes or parent.content_hash != parent_hash:
        raise EpistemicError("parent mutated")
    return child


def run_job(
    *,
    parent: TheoryObject,
    transformation_id: str,
    child_id: str,
    meaning: str,
    provenance: str,
    seed: int,
    bounds: Mapping[str, int],
    generated_so_far: int,
    updates: Mapping[str, Any] | None = None,
    new_assumptions: list[dict[str, Any]] | None = None,
    new_parameters: list[dict[str, Any]] | None = None,
) -> JobResult:
    """Produce a child. The parent object is not written."""
    parent_hash = parent.content_hash
    parent_bytes = parent.canonical()
    if generated_so_far >= int(bounds["max_generated_objects"]):
        raise ResourceBound("max_generated_objects")
    if len(parent.document().get("transformation_history") or []) >= int(bounds["max_branch_depth"]):
        raise ResourceBound("max_branch_depth")
    if parent.validation_state == "REQUIRES_HUMAN_INPUT":
        raise HumanInputBoundary(parent.theory_id)
    child = extend_theory(
        parent,
        transformation_id=transformation_id,
        child_id=child_id,
        meaning=meaning,
        provenance=provenance,
        updates=updates,
        new_assumptions=new_assumptions,
        new_parameters=new_parameters,
    )
    if parent.canonical() != parent_bytes or parent.content_hash != parent_hash:
        raise EpistemicError("parent mutated")
    log = AuditLog()
    log.record(
        "job",
        {
            "child_id": child.theory_id,
            "output_hash": child.content_hash,
            "parent_id": parent.theory_id,
            "seed": seed,
            "transformation": transformation_id,
        },
    )
    return JobResult(
        {
            "audit_log": list(log.events()),
            "output_hash": child.content_hash,
            "output_theory_id": child.theory_id,
            "parent_hash": parent_hash,
            "proof_obligations": child.document()["proof_obligations"],
            "result_artifact": "JOB_OUTPUT",
            "seed": seed,
        },
        child,
    )


def run_bounded_smoke(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Tiny deterministic recursion used only to test termination."""
    bounds = dict(manifest["bounds"])
    if int(bounds["max_generated_objects"]) > PHASE_12A_OBJECT_CAP:
        raise ResourceBound("phase 12A refuses a large object bound")
    root_doc = {
        "action": [],
        "assumptions": [{"id": "smoke", "provenance": "KERNEL_DECLARATION", "statement": "no physical content"}],
        "boundary_data": [],
        "constraints": [],
        "derived_quantities": [],
        "equivalence_metadata": [],
        "field_domains": [{"field": "s0", "domain": "toy"}],
        "fields": [{"id": "s0", "type": "toy_symbol"}],
        "grammar_id": GRAMMAR_ID,
        "grammar_version": GRAMMAR_VERSION,
        "operators": [],
        "parameter_registry": [],
        "parent_theory_id": None,
        "proof_obligations": [],
        "provenance": [{"id": "smoke", "provenance": "KERNEL_DECLARATION"}],
        "representations": [],
        "symmetries": [],
        "theory_id": "toy.kernel.smoke",
        "transformation_history": [],
        "validation_state": "FORMALIZED",
    }
    current = TheoryObject(root_doc)
    visited = {current.content_hash}
    produced = [current.theory_id]
    hashes = [current.content_hash]
    obligations = ObligationStore()
    seed = int(manifest["seed"])
    depth = 0
    generated = 0
    stop = "COMPLETED"
    while depth < int(bounds["max_branch_depth"]):
        child_id = f"toy.kernel.smoke.{seed}.{depth}"
        try:
            job = run_job(
                parent=current,
                transformation_id="ADD_FIELD",
                child_id=child_id,
                meaning="infrastructure field token",
                provenance="KERNEL_DECLARATION",
                seed=seed,
                bounds=bounds,
                generated_so_far=generated,
                updates={
                    "fields": list(current.document()["fields"]) + [{"id": f"s{depth + 1}", "type": "toy_symbol"}],
                    "validation_state": "FORMALIZED",
                },
            )
        except ResourceBound:
            stop = "RESOURCE_BOUND_REACHED"
            break
        except (GrammarBoundary, UnsupportedTransformation, HumanInputBoundary) as exc:
            stop = getattr(exc, "status", "STOPPED")
            break
        generated += 1
        child = job.child
        if child.content_hash in visited:
            stop = "REPEATED_THEORY"
            break
        visited.add(child.content_hash)
        produced.append(child.theory_id)
        hashes.append(child.content_hash)
        current = child
        depth += 1
    else:
        stop = "DEPTH_REACHED"
    frontier = TheoryFrontier()
    frontier.add(
        {
            "available_extensions": ["ADD_FIELD"] if stop == "DEPTH_REACHED" else [],
            "content_hash": current.content_hash,
            "exploration_status": stop,
            "human_input_required": False,
            "theory_id": current.theory_id,
            "unresolved_obligations": [],
        }
    )
    return freeze_document(
        {
            "hashes": hashes,
            "manifest_seed": seed,
            "obligations": [dict(item) for item in obligations.items()],
            "output_ids": produced,
            "stop": stop,
            "visited_count": len(visited),
        }
    )


def admit_theory(visited: set[str], theory: TheoryObject) -> str:
    """A content hash already seen is not explored again."""
    if theory.content_hash in visited:
        return "REPEATED_THEORY"
    visited.add(theory.content_hash)
    return "ADMITTED"


def obligation_from_partial(theory_id: str, statement: str) -> dict[str, Any]:
    return proof_obligation(
        obligation_id="obl." + theory_id,
        theory_id=theory_id,
        missing_statement=statement,
        dependencies = [],
        allowed_methods=["existing certified record"],
        forbidden_inputs=["experimental catalog", "new assumption"],
        current_status="OPEN",
    )


def human_input_record(*, theory_id: str, obligation_id: str, missing: str, reason: str) -> dict[str, Any]:
    return freeze_document(
        {
            "blocked_obligation": obligation_id,
            "exact_missing": missing,
            "reason": reason,
            "status": "REQUIRES_HUMAN_INPUT",
            "theory_id": theory_id,
        }
    )
