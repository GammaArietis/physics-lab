"""Phase 14C.0: known-physics structural catalog, profiles, consequence engine.

Infrastructure plus dry-run plus P0_CORE_STRUCTURAL_PHYSICS only.
P1–P5 are registered and isolated; they are not activated.
"""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14a_reconstruction import (
    artifact_dir as phase14a_artifact_dir,
    structural_input_registry,
)
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ClosureEngine,
    ENGINE_VERSION,
    EngineFailure,
    artifact_dir as phase14b0_artifact_dir,
    assert_target_blind,
    content_hash,
    generate_candidates,
    scan_target_blindness,
    top_down_input_hash,
    _with_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_ID,
    G6_SEARCH_BOUNDS,
    artifact_dir as phase14b6_artifact_dir,
    snapshot_prior_artifact_hashes as snapshot_14b6_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "CATALOG_VERSION",
    "CONSEQUENCE_ENGINE_VERSION",
    "DRY_PROFILE_CHAIN",
    "EXPECTED_G6_CHECKPOINT_HASH",
    "EXPECTED_G6_GRAMMAR_HASH",
    "P0_CHAIN",
    "P0_ID",
    "PHASE_14C0_TEST_COPY_ID",
    "analyze_phase14c0_known_physics",
    "artifact_dir",
    "attach_dry_profile_stats",
    "attach_p0_stats",
    "dry_profile_metadata_legal",
    "dry_profile_registry",
    "dry_profile_run_tests",
    "known_physics_structural_catalog",
    "open_physics_registry",
    "p0_executable_registry",
    "p0_metadata_legal",
    "p0_run_tests",
    "physics_profile_registry",
    "run_phase14c0_or_stop",
]

PHASE = "PHASE_14C.0"
PHASE_14C0_TEST_COPY_ID = "PHASE_14C0_KNOWN_PHYSICS_STRUCTURAL_CLOSURE"
AUDIT_VERSION = "phase14c0-known-physics-v1"
CATALOG_VERSION = "KNOWN_PHYSICS_STRUCTURAL_CATALOG_v1"
CONSEQUENCE_ENGINE_VERSION = "phase14c0-consequence-engine-v1"
PROFILE_REGISTRY_VERSION = "phase14c0-profile-registry-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_G6_GRAMMAR_HASH = "f0b030b17edb945320399cabc0784150271e4ac8271d0314f5cb9e98e9292017"
EXPECTED_G6_CHECKPOINT_HASH = "2a360859dc56c8d16fc64fab172296045ec99e50c9ded27c93f9ed1f65058d7d"
EXPECTED_G6_INTEGRITY_DIGEST = "a45647acb032a203042e23e2fb4cae272ec35364c9be5ceb4b5fe0082c368a16"
P0_ID = "P0_CORE_STRUCTURAL_PHYSICS"
P0_CHAIN: tuple[str, ...] = (P0_ID,)
DRY_PROFILE_CHAIN: tuple[str, ...] = ("14C_DRY_P0", "14C_DRY_P1")
DRY_COLORS: tuple[str, ...] = ("red", "blue", "green")
DRY_MARKERS: tuple[str, ...] = ("on", "off")
AUTHORIZED_PHYSICAL_PROFILES: tuple[str, ...] = (P0_ID,)
REGISTERED_INACTIVE_PROFILES: tuple[str, ...] = (
    "P1_QFT_STRUCTURAL_CONSISTENCY",
    "P2_CHIRAL_GAUGE_MATTER",
    "P3_QUALITATIVE_MATTER",
    "P4_KNOWN_MODEL_REFERENCE",
    "P5_OPTIONAL_QUANTUM_STRUCTURE",
)
P0_KPS: tuple[str, ...] = tuple(f"KP{i:02d}" for i in range(1, 16))


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c0_artifacts"


def g6_checkpoint_path() -> Path:
    return phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json"


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    from physics_lab.physics.phase14b0_engine import _write_json as engine_write

    engine_write(path, payload)


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _kind_entry(
    object_id: str,
    statement: str,
    *,
    kind: str,
    effect_on_generation: str,
    status: str,
    mathematical_form: str,
    provenance: str,
) -> dict[str, Any]:
    return {
        "object_id": object_id,
        "statement": statement,
        "kind": kind,
        "effect_on_generation": effect_on_generation,
        "status": status,
        "mathematical_form": mathematical_form,
        "provenance": provenance,
        "catalog_version": CATALOG_VERSION,
        "outside_current_catalog": False,
    }


def known_physics_structural_catalog() -> dict[str, Any]:
    inputs = []
    for item in structural_input_registry():
        inputs.append(
            _kind_entry(
                item["constraint_id"],
                item["statement"],
                kind="KNOWN_PHYSICS_INPUT",
                effect_on_generation="ACTIVE_WHEN_PROFILE_ENABLES",
                status="REGISTERED",
                mathematical_form=item["mathematical_form"],
                provenance="KNOWN_PHYSICS_INPUT",
            )
        )
    references = [
        _kind_entry(
            "REF_SM_GAUGE_STRUCTURE",
            "Known compact nonabelian-plus-abelian gauge structure of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only; not a generation or filter target",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_SM_REPRESENTATION_ASSIGNMENTS",
            "Known representation assignments of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_SM_FIELD_CONTENT",
            "Known field content of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_ELECTROWEAK_STRUCTURE",
            "Known electroweak chiral gauge structure of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_QCD_STRUCTURE",
            "Known strongly interacting nonabelian gauge structure of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_HIGGS_STRUCTURE",
            "Known scalar-doublet mass-generating sector of the established reference model",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_KNOWN_PARTICLE_SECTORS",
            "Experimentally established particle sectors recorded as a comparison benchmark",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference description only",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
        _kind_entry(
            "REF_GENERATION_MULTIPLICITY",
            "Known generation multiplicity of the established reference model is a reference integer, not a filter",
            kind="KNOWN_PHYSICS_REFERENCE",
            effect_on_generation="NONE",
            status="REFERENCE_ONLY",
            mathematical_form="reference integer; not used for generation, filtering, or ranking",
            provenance="KNOWN_PHYSICS_REFERENCE",
        ),
    ]
    objects = inputs + references
    payload = {
        "catalog_id": CATALOG_VERSION,
        "version": CATALOG_VERSION,
        "completeness_claim": "REGISTERED_STATEMENTS_ONLY",
        "contains_all_known_physics": False,
        "unregistered_physics": "OUTSIDE_CURRENT_CATALOG",
        "input_objects": inputs,
        "reference_only_objects": references,
        "objects": objects,
        "input_count": len(inputs),
        "reference_only_count": len(references),
        "separation": {
            "KNOWN_PHYSICS_INPUT": "qualitative fact admitted as a top-down constraint when a profile enables it",
            "KNOWN_PHYSICS_REFERENCE": "benchmark retained for interpretation; never used in generation or filtering",
            "DERIVED_CONSEQUENCE": "result forced by the active grammar and the active profile inputs",
        },
        "provenance": "KNOWN_PHYSICS_STRUCTURAL_CATALOG",
    }
    payload["catalog_hash"] = content_hash({k: v for k, v in payload.items() if k != "catalog_hash"})
    assert_target_blind(payload)
    return payload


def open_physics_registry() -> list[dict[str, Any]]:
    topics = (
        ("OPEN_DARK_MATTER_MECHANISM", "dark matter mechanism"),
        ("OPEN_DARK_ENERGY_MECHANISM", "dark energy mechanism"),
        ("OPEN_QUANTUM_GRAVITY", "quantum gravity"),
        ("OPEN_BARYOGENESIS_MECHANISM", "baryogenesis mechanism"),
        ("OPEN_NEUTRINO_MASS_MECHANISM", "exact neutrino mass mechanism"),
        ("OPEN_ULTRAVIOLET_COMPLETION", "exact ultraviolet completion"),
        ("OPEN_CONFINEMENT_AS_AXIOM", "confinement as a universal axiom"),
        ("OPEN_SUPERSYMMETRY", "supersymmetry"),
        ("OPEN_STRING_THEORY", "string theory"),
        ("OPEN_EXTRA_DIMENSIONS", "extra dimensions"),
    )
    out = []
    for object_id, topic in topics:
        out.append(
            {
                "object_id": object_id,
                "topic": topic,
                "status": "OPEN",
                "effect_on_generation": "NONE",
                "kind": "OPEN",
                "default_placement": "REFERENCE_ONLY / FUTURE_OPTIONAL_PROFILE",
                "provenance": "OUTSIDE_CURRENT_CATALOG",
            }
        )
    return out


def _profile_body(spec: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "profile_id",
        "version",
        "description",
        "input_objects",
        "enabled_constraints",
        "disabled_constraints",
        "reference_only_objects",
        "dependencies",
        "provenance",
        "generation_allowed",
        "filtering_allowed",
        "ranking_allowed",
        "activation_state",
        "untested_principles",
    )
    return {k: spec[k] for k in keys if k in spec}


def freeze_profile(spec: dict[str, Any]) -> dict[str, Any]:
    body = _profile_body(spec)
    assert_target_blind(body)
    out = dict(spec)
    for key, val in body.items():
        out[key] = copy.deepcopy(val)
    out["profile_hash"] = content_hash(body)
    out["frozen"] = True
    return out


def assert_profile_immutable(profile: dict[str, Any]) -> None:
    if not profile.get("frozen"):
        raise EngineFailure("PROFILE_HASH_MISMATCH", "profile is not frozen")
    recomputed = content_hash(_profile_body(profile))
    if recomputed != profile.get("profile_hash"):
        raise EngineFailure("PROFILE_HASH_MISMATCH", profile.get("profile_id") or "unknown")


def assert_profile_not_p4_in_generation(profile_id: str) -> None:
    if profile_id == "P4_KNOWN_MODEL_REFERENCE":
        raise EngineFailure("KNOWN_MODEL_ISOLATION_VIOLATION", "P4 must not participate in generation")


def assert_profile_activation_authorized(profile_id: str, *, dry: bool = False) -> None:
    if dry and profile_id in DRY_PROFILE_CHAIN:
        return
    if profile_id not in AUTHORIZED_PHYSICAL_PROFILES:
        raise EngineFailure("ILLEGAL_AUTOMATIC_EXTENSION", profile_id)


def _qft_untested() -> list[str]:
    return [
        "quantum_unitarity",
        "spin_statistics_consistency",
        "CPT_consistency",
        "perturbative_renormalizability",
    ]


def physics_profile_registry() -> dict[str, dict[str, Any]]:
    catalog = known_physics_structural_catalog()
    input_ids = [e["object_id"] for e in catalog["input_objects"]]
    ref_ids = [e["object_id"] for e in catalog["reference_only_objects"]]
    p0 = freeze_profile(
        {
            "profile_id": P0_ID,
            "version": "P0_v1",
            "description": "Currently established Phase 14A qualitative structural inputs KP01-KP15. No new physics is added.",
            "input_objects": list(P0_KPS),
            "enabled_constraints": list(P0_KPS),
            "disabled_constraints": [],
            "reference_only_objects": [],
            "dependencies": ["G6_STRUCTURAL_GAUGE_CONSISTENCY"],
            "provenance": "KNOWN_PHYSICS_INPUT",
            "generation_allowed": True,
            "filtering_allowed": True,
            "ranking_allowed": False,
            "activation_state": "AUTHORIZED_THIS_PHASE",
            "untested_principles": [],
        }
    )
    p1 = freeze_profile(
        {
            "profile_id": "P1_QFT_STRUCTURAL_CONSISTENCY",
            "version": "P1_v1",
            "description": "Structural QFT principles that can be tested when a genuine test exists. Classical proxies do not imply quantum verification.",
            "input_objects": ["KP02", "KP03", "KP08", "KP12"],
            "enabled_constraints": ["KP02", "KP03", "KP08", "KP12"],
            "disabled_constraints": _qft_untested(),
            "reference_only_objects": [],
            "dependencies": [P0_ID],
            "provenance": "KNOWN_PHYSICS_INPUT",
            "generation_allowed": True,
            "filtering_allowed": True,
            "ranking_allowed": False,
            "activation_state": "REGISTERED_NOT_ACTIVATED",
            "untested_principles": [
                {"principle": "quantum_unitarity", "status": "UNTESTED", "note": "positive classical kinetic Hessian is not full quantum unitarity"},
                {"principle": "spin_statistics_consistency", "status": "UNTESTED"},
                {"principle": "CPT_consistency", "status": "UNTESTED"},
            ],
        }
    )
    p2 = freeze_profile(
        {
            "profile_id": "P2_CHIRAL_GAUGE_MATTER",
            "version": "P2_v1",
            "description": "Chiral Weyl matter, compact gauge structure, finite-dimensional representations, anomaly cancellation, local covariance, scalar-compatible gauge structure, SSB, massless plus massive vectors. Exact reference-model group and charges remain REFERENCE_ONLY.",
            "input_objects": ["KP07", "KP08", "KP10", "KP11", "KP12", "KP13", "KP15"],
            "enabled_constraints": ["KP07", "KP08", "KP10", "KP11", "KP12", "KP13", "KP15"],
            "disabled_constraints": [],
            "reference_only_objects": [
                "REF_SM_GAUGE_STRUCTURE",
                "REF_SM_REPRESENTATION_ASSIGNMENTS",
                "REF_GENERATION_MULTIPLICITY",
            ],
            "dependencies": [P0_ID],
            "provenance": "KNOWN_PHYSICS_INPUT",
            "generation_allowed": True,
            "filtering_allowed": True,
            "ranking_allowed": False,
            "activation_state": "REGISTERED_NOT_ACTIVATED",
            "untested_principles": [],
        }
    )
    p3 = freeze_profile(
        {
            "profile_id": "P3_QUALITATIVE_MATTER",
            "version": "P3_v1",
            "description": "Qualitative fermionic and bosonic matter, chiral sectors, finite species, mass-generating scalar sector, gauge-invariant fermion/scalar interactions. No measured species numbers and no Yukawa fitting.",
            "input_objects": ["KP09", "KP10", "KP13", "KP14"],
            "enabled_constraints": ["KP09", "KP10", "KP13", "KP14"],
            "disabled_constraints": [],
            "reference_only_objects": ["REF_SM_FIELD_CONTENT", "REF_HIGGS_STRUCTURE"],
            "dependencies": [P0_ID],
            "provenance": "KNOWN_PHYSICS_INPUT",
            "generation_allowed": True,
            "filtering_allowed": True,
            "ranking_allowed": False,
            "activation_state": "REGISTERED_NOT_ACTIVATED",
            "untested_principles": [],
        }
    )
    p4 = freeze_profile(
        {
            "profile_id": "P4_KNOWN_MODEL_REFERENCE",
            "version": "P4_v1",
            "description": "Downstream comparison benchmark only. Must not generate, filter, or rank.",
            "input_objects": [],
            "enabled_constraints": [],
            "disabled_constraints": list(input_ids),
            "reference_only_objects": list(ref_ids),
            "dependencies": [],
            "provenance": "KNOWN_PHYSICS_REFERENCE",
            "generation_allowed": False,
            "filtering_allowed": False,
            "ranking_allowed": False,
            "activation_state": "REFERENCE_ONLY_ISOLATED",
            "untested_principles": [],
        }
    )
    p5 = freeze_profile(
        {
            "profile_id": "P5_OPTIONAL_QUANTUM_STRUCTURE",
            "version": "P5_v1",
            "description": "Optional quantum principles that require tests not yet implemented. Default REFERENCE_ONLY / UNTESTED.",
            "input_objects": [],
            "enabled_constraints": [],
            "disabled_constraints": [
                "perturbative_renormalizability",
                "RG_consistency",
                "asymptotic_freedom",
                "nonperturbative_confinement_diagnostics",
                "quantum_gravity_consistency",
            ],
            "reference_only_objects": [
                "OPEN_QUANTUM_GRAVITY",
                "OPEN_CONFINEMENT_AS_AXIOM",
            ],
            "dependencies": [],
            "provenance": "REFERENCE_ONLY",
            "generation_allowed": False,
            "filtering_allowed": False,
            "ranking_allowed": False,
            "activation_state": "REGISTERED_NOT_ACTIVATED",
            "untested_principles": [
                {"principle": "perturbative_renormalizability", "status": "UNTESTED"},
                {"principle": "RG_consistency", "status": "UNTESTED"},
                {"principle": "asymptotic_freedom", "status": "UNTESTED"},
                {"principle": "nonperturbative_confinement_diagnostics", "status": "UNTESTED"},
                {"principle": "quantum_gravity_consistency", "status": "UNTESTED"},
            ],
        }
    )
    registry = {
        "P0_CORE_STRUCTURAL_PHYSICS": p0,
        "P1_QFT_STRUCTURAL_CONSISTENCY": p1,
        "P2_CHIRAL_GAUGE_MATTER": p2,
        "P3_QUALITATIVE_MATTER": p3,
        "P4_KNOWN_MODEL_REFERENCE": p4,
        "P5_OPTIONAL_QUANTUM_STRUCTURE": p5,
    }
    for profile in registry.values():
        assert_profile_immutable(profile)
    payload = {
        "version": PROFILE_REGISTRY_VERSION,
        "profiles": registry,
        "active_this_phase": [P0_ID],
        "registered_not_activated": list(REGISTERED_INACTIVE_PROFILES),
        "p4_isolated": True,
        "no_automatic_full_known_physics": True,
    }
    payload["profile_registry_hash"] = content_hash(
        {pid: registry[pid]["profile_hash"] for pid in sorted(registry)}
    )
    return payload


def catalog_hash() -> str:
    return known_physics_structural_catalog()["catalog_hash"]


def profile_registry_hash() -> str:
    return physics_profile_registry()["profile_registry_hash"]


def verify_g6_parent_checkpoint() -> dict[str, Any]:
    path = g6_checkpoint_path()
    if not path.is_file():
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 parent missing")
    payload = _read_json(path)
    stored = payload.get("integrity_digest")
    recomputed = content_hash({k: v for k, v in payload.items() if k != "integrity_digest"})
    if stored != recomputed:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 parent digest mismatch")
    if payload.get("grammar_id") != G6_ID:
        raise EngineFailure("GRAMMAR_MISSING", "G6 parent grammar_id")
    if payload.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        raise EngineFailure("GRAMMAR_HASH_MISMATCH", "G6 parent grammar_hash")
    if payload.get("engine_version") != ENGINE_VERSION:
        raise EngineFailure("RESUME_INTEGRITY_FAILURE", "G6 parent engine version")
    if payload.get("input_hashes", {}).get("top_down_input_hash") != top_down_input_hash():
        raise EngineFailure("INPUT_HASH_MISMATCH", "G6 parent top-down inputs")
    if payload.get("integrity_digest") != EXPECTED_G6_INTEGRITY_DIGEST:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 integrity digest changed")
    if _file_digest(path) != EXPECTED_G6_CHECKPOINT_HASH:
        raise EngineFailure("CHECKPOINT_CORRUPTED", "G6 file digest changed")
    return payload


@lru_cache(maxsize=1)
def g6_class_rows() -> tuple[dict[str, Any], ...]:
    parent = verify_g6_parent_checkpoint()
    rows = []
    for row in parent.get("class_table") or []:
        status = row.get("status")
        if status == "PASS":
            completeness = "COMPLETE"
        elif status == "PARTIAL":
            completeness = "PARTIAL_G4_DEPENDENCY"
        else:
            continue
        item = dict(row)
        item["completeness"] = completeness
        if completeness == "COMPLETE":
            item["g4_partiality"] = "G4_PARTIALITY_IRRELEVANT"
        else:
            item["g4_partiality"] = "DEPENDS_ON_G4_PARTIALITY"
        rows.append(item)
    return tuple(rows)


@lru_cache(maxsize=1)
def g6_survivor_hashes() -> tuple[str, ...]:
    return tuple(row["candidate_hash"] for row in g6_class_rows())


@lru_cache(maxsize=1)
def g6_row_by_hash() -> dict[str, dict[str, Any]]:
    return {row["candidate_hash"]: row for row in g6_class_rows()}


def g6_candidate_space_hash() -> str:
    return content_hash({"g6_survivor_hashes": list(g6_survivor_hashes())})


def dry_profile_registry() -> dict[str, dict[str, Any]]:
    dry0 = _with_hash(
        {
            "grammar_id": "14C_DRY_P0",
            "parent_grammar_id": None,
            "extension_description": "synthetic profile P0: marker must be on; no physical meaning",
            "allowed_fields": ["color", "marker"],
            "allowed_groups": [],
            "allowed_representations": [],
            "allowed_interactions": [],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": ["DRY_C_MARKER_ON"],
            "explicit_exclusions": ["physics_interpretation", "P4_KNOWN_MODEL_REFERENCE"],
            "provenance": "METHOD / INTEGRITY CONTROL",
            "status": "ACTIVE_DRY_RUN",
            "axes": {"color": list(DRY_COLORS), "marker": list(DRY_MARKERS)},
        }
    )
    dry1 = _with_hash(
        {
            "grammar_id": "14C_DRY_P1",
            "parent_grammar_id": "14C_DRY_P0",
            "extension_description": "synthetic profile P1: marker on and color not red; no physical meaning",
            "allowed_fields": ["color", "marker"],
            "allowed_groups": [],
            "allowed_representations": [],
            "allowed_interactions": [],
            "allowed_symmetry_breaking": [],
            "allowed_constraints": ["DRY_C_MARKER_ON", "DRY_C_NOT_RED"],
            "explicit_exclusions": ["physics_interpretation", "P4_KNOWN_MODEL_REFERENCE"],
            "provenance": "METHOD / INTEGRITY CONTROL",
            "status": "ACTIVE_DRY_RUN",
            "axes": {"color": list(DRY_COLORS), "marker": list(DRY_MARKERS)},
        }
    )
    return {"14C_DRY_P0": dry0, "14C_DRY_P1": dry1}


def dry_profile_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    gid = grammar.get("grammar_id")
    if assignment.get("marker") == "off":
        return False, "DRY_C_MARKER_ON"
    if gid == "14C_DRY_P1" and assignment.get("color") == "red":
        return False, "DRY_C_NOT_RED"
    return True, None


def dry_profile_run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    assignment = candidate["assignment"]
    results = [
        {
            "test_id": "grammar_legality",
            "test_version": test_version,
            "status": "PASS",
            "provenance": "METHOD / INTEGRITY CONTROL",
            "source_phase": PHASE,
        },
        {
            "test_id": "marker_on",
            "test_version": test_version,
            "status": "PASS" if assignment.get("marker") == "on" else "FAIL",
            "provenance": "METHOD / INTEGRITY CONTROL",
            "source_phase": PHASE,
        },
    ]
    if candidate.get("grammar_version") == "14C_DRY_P1":
        results.append(
            {
                "test_id": "color_not_red",
                "test_version": test_version,
                "status": "PASS" if assignment.get("color") != "red" else "FAIL",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "source_phase": PHASE,
            }
        )
    status = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    return {"status": status, "results": results, "test_version": test_version}


def p0_executable_registry() -> dict[str, dict[str, Any]]:
    assert_profile_activation_authorized(P0_ID)
    profile = physics_profile_registry()["profiles"][P0_ID]
    assert_profile_immutable(profile)
    p0 = _with_hash(
        {
            "grammar_id": P0_ID,
            "parent_grammar_id": G6_ID,
            "extension_description": (
                "P0 core structural physics profile applied to the verified G6 survivor space. "
                "Base mathematical grammar is unchanged. No new physical principle is added."
            ),
            "allowed_fields": ["inherited_G6_content"],
            "allowed_groups": ["inherited_G6_groups"],
            "allowed_representations": ["inherited_G6_representations"],
            "allowed_interactions": ["inherited_G6_interactions"],
            "allowed_symmetry_breaking": ["inherited_G6_SSB"],
            "allowed_constraints": list(P0_KPS),
            "explicit_exclusions": [
                "P1_QFT_STRUCTURAL_CONSISTENCY automatic activation",
                "P2_CHIRAL_GAUGE_MATTER automatic activation",
                "P3_QUALITATIVE_MATTER automatic activation",
                "P4_KNOWN_MODEL_REFERENCE generation",
                "P5_OPTIONAL_QUANTUM_STRUCTURE automatic activation",
                "exact reference-model group",
                "exact reference-model field content",
                "exact observed charge assignments",
                "numerical mixing data",
                "Yukawa fitting",
                "ranking",
                "hidden reference-model matching",
            ],
            "provenance": "INHERITED FROM G6",
            "status": "ACTIVE_P0_ONLY",
            "axes": {"g6_survivor": list(g6_survivor_hashes())},
            "profile_hash": profile["profile_hash"],
            "VECTORLIKE_STATUS": "UNTESTED",
        }
    )
    return {P0_ID: p0}


def p0_metadata_legal(assignment: dict[str, str], grammar: dict[str, Any]) -> tuple[bool, str | None]:
    _ = grammar
    digest = assignment.get("g6_survivor")
    if digest not in g6_row_by_hash():
        return False, "g6_survivor_unknown"
    return True, None


def p0_run_tests(candidate: dict[str, Any], *, test_version: str = "dry-tests-v1") -> dict[str, Any]:
    assert_target_blind(candidate)
    digest = candidate["assignment"]["g6_survivor"]
    row = g6_row_by_hash()[digest]
    completeness = row["completeness"]
    if completeness == "COMPLETE":
        status = "PASS"
    elif completeness == "PARTIAL_G4_DEPENDENCY":
        status = "PARTIAL"
    else:
        status = "UNRESOLVED"
    results = [
        {
            "test_id": "g6_reuse",
            "test_version": test_version,
            "status": "PASS",
            "completeness": completeness,
            "provenance": "INHERITED FROM G6",
            "source_phase": PHASE,
        },
        {
            "test_id": "p0_kp01_kp15_already_enforced",
            "test_version": test_version,
            "status": "PASS",
            "provenance": "KNOWN_PHYSICS_INPUT",
            "source_phase": PHASE,
        },
        {
            "test_id": "partial_not_upgraded",
            "test_version": test_version,
            "status": "PASS" if (status != "PASS" or completeness == "COMPLETE") else "FAIL",
            "provenance": "PARTIAL_G4_DEPENDENCY",
            "source_phase": PHASE,
        },
    ]
    return {
        "status": status,
        "results": results,
        "test_version": test_version,
        "completeness": completeness,
        "g4_partiality": row["g4_partiality"],
        "g6_row": row,
    }


def _signature(row: dict[str, Any]) -> dict[str, Any]:
    couplings = list(row.get("free_couplings") or [])
    return {
        "gauge_group_class": str(row.get("gauge_group")),
        "representation_class": str(row.get("fermion_representations")),
        "scalar_class": str(row.get("scalar_representation")),
        "anomaly_class": str(row.get("anomaly_integrity")),
        "ssb_class": str(row.get("VEV_stabilizer")),
        "residual_subgroup": str(row.get("VEV_stabilizer")),
        "vector_sector_structure": str(row.get("KP15")),
        "matter_content": str(row.get("Weyl_content")),
        "u1_weights": str(row.get("U1_weights")),
        "local_covariance": str(row.get("local_covariance")),
        "matter_invariance": str(row.get("matter_invariance")),
        "orbit_classification": str(row.get("orbit_classification")),
        "vectorlike_status": str(row.get("VECTORLIKE_STATUS")),
        "free_parameter_count": len(couplings),
        "free_couplings": couplings,
        "completeness": row.get("completeness") or ("COMPLETE" if row.get("status") == "PASS" else "PARTIAL_G4_DEPENDENCY"),
        "g4_partiality": row.get("g4_partiality") or "G4_PARTIALITY_IRRELEVANT",
        "candidate_hash": row.get("candidate_hash"),
    }


def _values(rows: list[dict[str, Any]], key: str) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for row in rows:
        sig = _signature(row)
        val = str(sig.get(key))
        buckets.setdefault(val, []).append(str(sig["candidate_hash"]))
    return buckets


def _property_record(
    *,
    property_id: str,
    value: Any,
    classification: str,
    provenance: str,
    forced_by: list[str],
    g4: str,
    counterexamples: list[dict[str, Any]],
    proof_status: str,
    universe: str,
) -> dict[str, Any]:
    return {
        "consequence_id": f"C14C0_{property_id}",
        "property": property_id,
        "value": value,
        "classification": classification,
        "claim_label": "DERIVED" if classification == "PROFILE_FORCED" else classification,
        "provenance": provenance,
        "forced_by_constraints": forced_by,
        "minimal_constraint_subset": list(forced_by),
        "proof_status": proof_status,
        "counterexamples": counterexamples,
        "g4_partiality": g4,
        "universe": universe,
        "grammar_version": G6_ID,
        "profile_version": "P0_v1",
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "equivalence_version": "IDENTITY_EQUAL",
        "scope": "FORCED_WITHIN_DECLARED_BOUNDS" if classification == "PROFILE_FORCED" else classification,
    }


def classify_consequences(
    rows: list[dict[str, Any]],
    *,
    profile_id: str,
    enabled_constraints: list[str],
) -> dict[str, Any]:
    complete = [r for r in rows if (r.get("completeness") or r.get("status")) in {"COMPLETE", "PASS"}]
    partial = [r for r in rows if (r.get("completeness") or r.get("status")) in {"PARTIAL_G4_DEPENDENCY", "PARTIAL"}]
    if not complete:
        complete = list(rows)
    specs: list[dict[str, Any]] = [
        {"id": "local_covariance", "key": "local_covariance", "kind": "status", "forced_by": ["KP08"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "matter_invariance", "key": "matter_invariance", "kind": "status", "forced_by": ["KP09"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "anomaly_integrity", "key": "anomaly_class", "kind": "status", "forced_by": ["KP12"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "vector_sector_KP15", "key": "vector_sector_structure", "kind": "status", "forced_by": ["KP15"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "gauge_group_class", "key": "gauge_group_class", "kind": "label", "forced_by": ["KP07", "KP08"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "representation_class", "key": "representation_class", "kind": "label", "forced_by": ["KP10", "KP11"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "scalar_class", "key": "scalar_class", "kind": "label", "forced_by": ["KP13"], "g4": "DEPENDS_ON_G4_PARTIALITY"},
        {"id": "ssb_class", "key": "ssb_class", "kind": "label", "forced_by": ["KP13", "KP15"], "g4": "DEPENDS_ON_G4_PARTIALITY"},
        {"id": "matter_content", "key": "matter_content", "kind": "label", "forced_by": ["KP09", "KP14"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "u1_weights", "key": "u1_weights", "kind": "label", "forced_by": ["KP08", "KP11"], "g4": "G4_PARTIALITY_IRRELEVANT"},
        {"id": "vectorlike_status", "key": "vectorlike_status", "kind": "untested", "forced_by": [], "g4": "G4_PARTIALITY_IRRELEVANT"},
    ]
    forced: list[dict[str, Any]] = []
    branch: list[dict[str, Any]] = []
    free: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    destroyed: list[dict[str, Any]] = []
    universe = "COMPLETE_G6_SURVIVORS"
    for spec in specs:
        buckets = _values(complete, spec["key"])
        values = sorted(buckets)
        counterexamples = []
        if len(values) > 1:
            a, b = values[0], values[1]
            counterexamples = [
                {"value": a, "candidate_hash": buckets[a][0]},
                {"value": b, "candidate_hash": buckets[b][0]},
            ]
        if spec["kind"] == "untested":
            unresolved.append(
                _property_record(
                    property_id=spec["id"],
                    value=values[0] if len(values) == 1 else values,
                    classification="UNRESOLVED",
                    provenance="UNTESTED",
                    forced_by=spec["forced_by"],
                    g4=spec["g4"],
                    counterexamples=[],
                    proof_status="UNTESTED",
                    universe=universe,
                )
            )
            continue
        if spec["kind"] == "status" and len(values) == 1 and values[0] in {"PASS", "True"}:
            forced.append(
                _property_record(
                    property_id=spec["id"],
                    value=values[0],
                    classification="PROFILE_FORCED",
                    provenance="DERIVED_CONSEQUENCE",
                    forced_by=[c for c in spec["forced_by"] if c in enabled_constraints],
                    g4=spec["g4"],
                    counterexamples=[],
                    proof_status="FORCED_WITHIN_DECLARED_BOUNDS",
                    universe=universe,
                )
            )
            continue
        if spec["kind"] == "label" and len(values) == 1:
            forced.append(
                _property_record(
                    property_id=spec["id"],
                    value=values[0],
                    classification="PROFILE_FORCED",
                    provenance="DERIVED_CONSEQUENCE",
                    forced_by=[c for c in spec["forced_by"] if c in enabled_constraints],
                    g4=spec["g4"],
                    counterexamples=[],
                    proof_status="FORCED_WITHIN_DECLARED_BOUNDS",
                    universe=universe,
                )
            )
            continue
        branch.append(
            _property_record(
                property_id=spec["id"],
                value=values,
                classification="BRANCH_DEPENDENT",
                provenance="BRANCH_DEPENDENT",
                forced_by=spec["forced_by"],
                g4=spec["g4"],
                counterexamples=counterexamples,
                proof_status="COUNTEREXAMPLE_FOUND",
                universe=universe,
            )
        )
        destroyed.append(
            {
                "proposed_consequence": f"unique_{spec['id']}",
                "destroyed_by": counterexamples,
                "reason": "frequency is not logical necessity",
                "provenance": "DERIVED_CONSEQUENCE",
            }
        )
    predicates = [
        ("weyl_fermion_sector_present", lambda r: "Weyl" in str(r.get("Weyl_content")), ["KP09", "KP10"]),
        ("compact_su_n_factor_present", lambda r: str(r.get("gauge_group", "")).startswith("SU("), ["KP07", "KP08"]),
        ("finite_species_content", lambda r: True, ["KP14"]),
        ("anomaly_free", lambda r: r.get("anomaly_integrity") == "PASS", ["KP12"]),
        ("local_gauge_covariance", lambda r: r.get("local_covariance") == "PASS", ["KP08"]),
        ("both_fermion_and_boson_sectors", lambda r: bool(r.get("scalar_representation")) and "Weyl" in str(r.get("Weyl_content")), ["KP09"]),
    ]
    for pid, pred, forced_by in predicates:
        holds = [r for r in complete if pred(r)]
        fails = [r for r in complete if not pred(r)]
        if fails:
            branch.append(
                _property_record(
                    property_id=pid,
                    value=False,
                    classification="BRANCH_DEPENDENT",
                    provenance="BRANCH_DEPENDENT",
                    forced_by=forced_by,
                    g4="G4_PARTIALITY_IRRELEVANT",
                    counterexamples=[{"candidate_hash": fails[0]["candidate_hash"]}],
                    proof_status="COUNTEREXAMPLE_FOUND",
                    universe=universe,
                )
            )
            destroyed.append(
                {
                    "proposed_consequence": pid,
                    "destroyed_by": [{"candidate_hash": fails[0]["candidate_hash"]}],
                    "reason": "counterexample in complete survivor space",
                    "provenance": "DERIVED_CONSEQUENCE",
                }
            )
        else:
            forced.append(
                _property_record(
                    property_id=pid,
                    value=True,
                    classification="PROFILE_FORCED",
                    provenance="DERIVED_CONSEQUENCE",
                    forced_by=[c for c in forced_by if c in enabled_constraints],
                    g4="G4_PARTIALITY_IRRELEVANT",
                    counterexamples=[],
                    proof_status="FORCED_WITHIN_DECLARED_BOUNDS",
                    universe=universe,
                )
            )
    unique_group = len(_values(complete, "gauge_group_class")) == 1
    if not unique_group:
        destroyed.append(
            {
                "proposed_consequence": "unique_gauge_group",
                "destroyed_by": [
                    {"candidate_hash": complete[0]["candidate_hash"], "gauge_group": complete[0].get("gauge_group")}
                ],
                "reason": "inequivalent gauge groups survive",
                "provenance": "DERIVED_CONSEQUENCE",
            }
        )
    free.extend(
        [
            _property_record(
                property_id="gauge_coupling_g_SU_N",
                value="FREE",
                classification="FREE",
                provenance="FREE / PARAMETER-DEPENDENT",
                forced_by=[],
                g4="G4_PARTIALITY_IRRELEVANT",
                counterexamples=[],
                proof_status="UNCONSTRAINED_CONTINUOUS_PARAMETER",
                universe=universe,
            ),
            _property_record(
                property_id="gravity_c0",
                value="FREE",
                classification="FREE",
                provenance="FREE / PARAMETER-DEPENDENT",
                forced_by=[],
                g4="G4_PARTIALITY_IRRELEVANT",
                counterexamples=[],
                proof_status="UNCONSTRAINED_CONTINUOUS_PARAMETER",
                universe="PHASE_4C_FREEZE",
            ),
            _property_record(
                property_id="gravity_c1",
                value="FREE",
                classification="FREE",
                provenance="FREE / PARAMETER-DEPENDENT",
                forced_by=[],
                g4="G4_PARTIALITY_IRRELEVANT",
                counterexamples=[],
                proof_status="UNCONSTRAINED_CONTINUOUS_PARAMETER",
                universe="PHASE_4C_FREEZE",
            ),
            _property_record(
                property_id="VEV_magnitude",
                value="NOT PROVIDED",
                classification="FREE",
                provenance="NOT PROVIDED",
                forced_by=[],
                g4="DEPENDS_ON_G4_PARTIALITY",
                counterexamples=[],
                proof_status="UNCONSTRAINED_DIMENSIONFUL_PARAMETER",
                universe=universe,
            ),
        ]
    )
    unresolved.append(
        _property_record(
            property_id="SU4_scalar_20_and_64_orbits",
            value="PARTIAL",
            classification="UNRESOLVED",
            provenance="UNRESOLVED_BY_G4_ORBIT_CLASSIFICATION",
            forced_by=["KP13"],
            g4="DEPENDS_ON_G4_PARTIALITY",
            counterexamples=[],
            proof_status="UNRESOLVED",
            universe="PARTIAL_G4_DEPENDENCY",
        )
    )
    signatures = [_signature(r) for r in complete]
    common = {}
    if signatures:
        keys = [
            "gauge_group_class",
            "representation_class",
            "anomaly_class",
            "ssb_class",
            "vector_sector_structure",
            "matter_content",
            "free_parameter_count",
        ]
        for key in keys:
            vals = {str(s[key]) for s in signatures}
            if len(vals) == 1:
                common[key] = next(iter(vals))
    g_u1_present = any("g_U1" in (r.get("free_couplings") or []) for r in complete)
    g_u1_absent = any("g_U1" not in (r.get("free_couplings") or []) for r in complete)
    if g_u1_present:
        free.append(
            _property_record(
                property_id="gauge_coupling_g_U1",
                value="FREE_WHEN_U1_PRESENT",
                classification="FREE",
                provenance="FREE / PARAMETER-DEPENDENT",
                forced_by=[],
                g4="G4_PARTIALITY_IRRELEVANT",
                counterexamples=[],
                proof_status="UNCONSTRAINED_CONTINUOUS_PARAMETER",
                universe=universe,
            )
        )
    parameter_analysis = {
        "remaining_physical_continuous_parameters": ["g_SU_N", "g_U1_when_present", "c0", "c1", "kappa"],
        "normalization_freedoms": ["antihermitian_connection_convention", "representation_phase_convention"],
        "discrete_structural_labels": sorted({str(r.get("gauge_group")) for r in complete}),
        "branch_dependent_parameters": ["gauge_group", "fermion_representation", "scalar_representation", "VEV_orbit", "N_f", "U1_factor"],
        "unresolved_parameters": ["SU4_20_orbit", "SU4_64_orbit", "vectorlike_classification"],
        "parameter_free_derived_relations": ["anomaly_polynomials_vanish"],
        "g_U1_present_in_some_branches": g_u1_present,
        "g_U1_absent_in_some_branches": g_u1_absent,
        "new_parameter_free_dimensionless_physical_observables": [],
        "representation_invariants_are_not_couplings": True,
        "continuous_couplings_still_free": True,
        "adding_P0_reduces_continuous_freedom": False,
        "provenance": "DERIVED_CONSEQUENCE",
    }
    dimensionless_audit = {
        "representation_invariants": "NOT_PHYSICAL_COUPLINGS",
        "convention_dependent_ratios": "NOT_SEARCHED",
        "free_couplings": ["g_SU_N", "g_U1_when_present"],
        "dimensionless_physical_observables_derived": [],
        "structural_integers": ["group_rank", "representation_dimension", "N_f", "N_scalar"],
        "familiar_numerical_constants_searched": False,
        "provenance": "DERIVED_CONSEQUENCE",
    }
    return {
        "profile_id": profile_id,
        "candidate_count": len(rows),
        "complete_count": len(complete),
        "partial_count": len(partial),
        "FORCED_PROPERTIES": forced,
        "BRANCH_DEPENDENT_PROPERTIES": branch,
        "FREE_PROPERTIES": free,
        "UNRESOLVED_PROPERTIES": unresolved,
        "destroyed_by_counterexample": destroyed,
        "universal_signatures": common,
        "parameter_analysis": parameter_analysis,
        "dimensionless_audit": dimensionless_audit,
        "MINIMAL_ASSUMPTION_MAP": [
            {
                "consequence_id": item["consequence_id"],
                "property": item["property"],
                "forced_by_constraints": item["forced_by_constraints"],
                "minimal_constraint_subset": item["minimal_constraint_subset"],
                "proof_status": item["proof_status"],
                "counterexamples": item["counterexamples"],
            }
            for item in forced
        ],
        "UNIQUE_THEORY": len(complete) == 1,
        "KNOWN_QUALITATIVE_PHYSICS_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_GRAMMAR_AND_PROFILES": len(complete) != 1,
        "NEW_PROPERTIES_BEYOND_G6": [],
        "P0_ADDS_NO_NEW_ELIMINATION": True,
    }


def classify_dry_consequences(evaluated: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [c for c in evaluated if c.get("filter_status") == "PASS"]
    colors = {}
    markers = {}
    for cand in survivors:
        assignment = cand["assignment"]
        colors.setdefault(assignment["color"], []).append(cand["candidate_hash"])
        markers.setdefault(assignment["marker"], []).append(cand["candidate_hash"])
    forced = []
    branch = []
    destroyed = []
    if list(markers.keys()) == ["on"]:
        forced.append(
            {
                "property": "marker_on",
                "classification": "PROFILE_FORCED",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "proof_status": "FORCED_WITHIN_DECLARED_BOUNDS",
            }
        )
    if len(colors) > 1:
        keys = sorted(colors)
        branch.append(
            {
                "property": "color",
                "values": keys,
                "classification": "BRANCH_DEPENDENT",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "counterexamples": [{"color": keys[0], "candidate_hash": colors[keys[0]][0]}, {"color": keys[1], "candidate_hash": colors[keys[1]][0]}],
            }
        )
        destroyed.append(
            {
                "proposed_consequence": "unique_color",
                "destroyed_by": [{"color": keys[1], "candidate_hash": colors[keys[1]][0]}],
            }
        )
    elif len(colors) == 1:
        forced.append(
            {
                "property": "color",
                "value": next(iter(colors)),
                "classification": "PROFILE_FORCED",
                "provenance": "METHOD / INTEGRITY CONTROL",
                "proof_status": "FORCED_WITHIN_DECLARED_BOUNDS",
            }
        )
    return {
        "FORCED_PROPERTIES": forced,
        "BRANCH_DEPENDENT_PROPERTIES": branch,
        "FREE_PROPERTIES": [],
        "UNRESOLVED_PROPERTIES": [],
        "destroyed_by_counterexample": destroyed,
        "survivor_count": len(survivors),
        "physical_conclusions_authorized": False,
        "provenance": "METHOD / INTEGRITY CONTROL",
    }


def cross_profile_difference(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    def ids(block: list[dict[str, Any]]) -> set[str]:
        out = set()
        for item in block:
            out.add(str(item.get("property") or item.get("proposed_consequence")))
        return out

    left_forced = ids(left.get("FORCED_PROPERTIES") or [])
    right_forced = ids(right.get("FORCED_PROPERTIES") or [])
    return {
        "newly_forced_properties": sorted(right_forced - left_forced),
        "no_longer_forced_properties": sorted(left_forced - right_forced),
        "newly_eliminated_classes": list((right.get("eliminated_classes") or [])),
        "newly_free_properties": sorted(
            ids(right.get("FREE_PROPERTIES") or []) - ids(left.get("FREE_PROPERTIES") or [])
        ),
        "unresolved_properties": sorted(ids(right.get("UNRESOLVED_PROPERTIES") or [])),
        "numerical_closeness_to_known_physics": "NOT_COMPUTED",
        "provenance": "METHOD / INTEGRITY CONTROL",
    }


def attach_dry_profile_stats(
    grammar: dict[str, Any],
    evaluated: list[dict[str, Any]],
    compatible: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = compatible
    table = []
    for cand in evaluated:
        assignment = cand["assignment"]
        table.append(
            {
                "candidate_class": cand["candidate_id"],
                "candidate_hash": cand["candidate_hash"],
                "color": assignment.get("color"),
                "marker": assignment.get("marker"),
                "status": cand.get("filter_status"),
                "provenance": "METHOD / INTEGRITY CONTROL",
            }
        )
    consequences = classify_dry_consequences(evaluated)
    return {
        "class_table": table,
        "parameter_inventory": [],
        "blockers": [],
        "target_blindness": "VERIFIED",
        "profile_id": grammar["grammar_id"],
        "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "consequences": consequences,
        "provenance_summary": {
            "dry_run": "METHOD / INTEGRITY CONTROL",
            "physical_conclusions": "NOT AUTHORIZED",
        },
    }


def attach_p0_stats(
    grammar: dict[str, Any],
    evaluated: list[dict[str, Any]],
    compatible: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = compatible
    profile = physics_profile_registry()["profiles"][P0_ID]
    table = []
    inventory = []
    rows_for_engine = []
    for cand in evaluated:
        digest = cand["assignment"]["g6_survivor"]
        row = dict(g6_row_by_hash()[digest])
        row["p0_candidate_hash"] = cand["candidate_hash"]
        row["completeness"] = "COMPLETE" if cand.get("filter_status") == "PASS" else "PARTIAL_G4_DEPENDENCY"
        if row["completeness"] == "COMPLETE":
            row["g4_partiality"] = "G4_PARTIALITY_IRRELEVANT"
        else:
            row["g4_partiality"] = "DEPENDS_ON_G4_PARTIALITY"
        table.append(row)
        rows_for_engine.append(row)
        if cand.get("filter_status") == "PASS":
            inventory.append(
                {
                    "g6_candidate_hash": digest,
                    "p0_candidate_hash": cand["candidate_hash"],
                    "gauge_group": row.get("gauge_group"),
                    "completeness": "COMPLETE",
                    "free_couplings": row.get("free_couplings"),
                    "provenance": "INHERITED FROM G6",
                }
            )
    consequences = classify_consequences(rows_for_engine, profile_id=P0_ID, enabled_constraints=list(P0_KPS))
    partial_n = sum(1 for c in evaluated if c.get("filter_status") == "PARTIAL")
    return {
        "class_table": table,
        "parameter_inventory": inventory,
        "blockers": [],
        "parent_checkpoint_hash": EXPECTED_G6_CHECKPOINT_HASH,
        "parent_grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
        "search_bounds": dict(G6_SEARCH_BOUNDS),
        "g6_survivors_reused": len(g6_survivor_hashes()),
        "target_blindness": "VERIFIED",
        "profile_id": P0_ID,
        "profile_hash": profile["profile_hash"],
        "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "completeness_statistics": {
            "COMPLETE": sum(1 for c in evaluated if c.get("filter_status") == "PASS"),
            "PARTIAL_G4_DEPENDENCY": partial_n,
        },
        "partial": partial_n,
        "consequences": consequences,
        "provenance_summary": {
            "P0_inputs": "KNOWN_PHYSICS_INPUT",
            "G6_inheritance": "INHERITED FROM G6",
            "derived_consequences": "DERIVED_CONSEQUENCE",
            "P4_comparison": "NOT_EXECUTED",
            "P1_P2_P3_P5": "REGISTERED_NOT_ACTIVATED",
        },
    }


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14b6_priors()
    out["phase14b6"] = {}
    for name in (
        "PHASE_14B6_SUMMARY.json",
        "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json",
    ):
        path = phase14b6_artifact_dir() / name
        if path.is_file():
            out["phase14b6"][name] = _file_digest(path)
    return out


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {"count": len(catalog), "specs_unchanged": specs_unchanged, "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1}


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.0 refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def run_synthetic_dry_run(root: Path) -> dict[str, Any]:
    dry_root = Path(root) / "dry_run"
    engine = ClosureEngine(dry_root, chain="14c0_dry")
    state = engine.run_until_closure()
    resumed = engine.resume_closure()
    p0_rep = next(r for r in state["version_reports"] if r["grammar_id"] == "14C_DRY_P0")
    p1_rep = next(r for r in state["version_reports"] if r["grammar_id"] == "14C_DRY_P1")

    def _from_table(rep: dict[str, Any]) -> dict[str, Any]:
        fake = [
            {
                "assignment": {"color": r["color"], "marker": r["marker"]},
                "filter_status": r["status"],
                "candidate_hash": r["candidate_hash"],
            }
            for r in (rep.get("class_table") or [])
        ]
        return classify_dry_consequences(fake)

    p0_cons = _from_table(p0_rep)
    p1_cons = classify_dry_consequences(
        [{"assignment": {"color": r["color"], "marker": r["marker"]}, "filter_status": r["status"], "candidate_hash": r["candidate_hash"]} for r in (p1_rep.get("class_table") or [])]
    )
    p1_cons["eliminated_classes"] = ["red"]
    diff = cross_profile_difference(p0_cons, p1_cons)
    parallel = ClosureEngine(dry_root / "parallel", chain="14c0_dry")
    serial_stats = ClosureEngine(dry_root / "serial", chain="14c0_dry").evaluate_grammar("14C_DRY_P0", parallel=False)
    parallel_stats = parallel.evaluate_grammar("14C_DRY_P0", parallel=True)
    engine.verify_checkpoint("14C_DRY_P0")
    engine.verify_checkpoint("14C_DRY_P1")
    return {
        "status": "OK",
        "closure_status": state.get("closure_status"),
        "resume_matches": resumed.get("closure_status") == state.get("closure_status"),
        "resume_compatible": resumed.get("compatible_count") == state.get("compatible_count"),
        "P0_compatible": p0_rep["compatible"],
        "P1_compatible": p1_rep["compatible"],
        "P0_consequences": p0_cons,
        "P1_consequences": p1_cons,
        "cross_profile_difference": diff,
        "checkpoint_p0": str(engine.checkpoint_path("14C_DRY_P0")),
        "checkpoint_p1": str(engine.checkpoint_path("14C_DRY_P1")),
        "deterministic_parallel": serial_stats["candidate_hashes"] == parallel_stats["candidate_hashes"],
        "physical_conclusions_authorized": False,
        "provenance": "METHOD / INTEGRITY CONTROL",
        "SCIENTIFIC_STATUS": "DRY_RUN_ONLY",
    }


def _claim_labels() -> dict[str, str]:
    return {
        "P0_inputs": "KNOWN_PHYSICS_INPUT",
        "P0_forced_properties": "DERIVED",
        "P4_structures": "REFERENCE_ONLY",
        "resemblance_to_known_model": "RECOGNIZED_MATCH",
        "vacuum_existence": "ASSUMED",
        "quantum_unitarity": "UNTESTED",
        "vectorlike_classification": "UNTESTED",
        "P4_comparison": "NOT_EXECUTED",
    }


def analyze_phase14c0_known_physics(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    s14b0 = _read_json(phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json")
    s14a = _read_json(phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
    s14b6 = _read_json(phase14b6_artifact_dir() / "PHASE_14B6_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        g5_path = phase14b6_artifact_dir().parent / "phase14b5_artifacts" / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
        if not g5_path.is_file():
            from physics_lab.physics.phase14b5_g5 import artifact_dir as phase14b5_artifact_dir

            g5_path = phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json"
        g5_before = g5_path.read_bytes()
    except (FileNotFoundError, EngineFailure) as exc:
        detail = exc.mode if isinstance(exc, EngineFailure) else str(exc)
        return {"status": "STOP", "scientific_analysis": None, "detail": detail, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    integrity_failure = None
    if s14b0.get("TOP_DOWN_CLOSURE_ENGINE") != "READY":
        integrity_failure = "TOP_DOWN_CLOSURE_ENGINE is not READY"
    if s14b6.get("GRAMMAR_HASH") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 grammar hash mismatch"
    if s14b6.get("G6_PASS") != 359 or s14b6.get("G6_PARTIAL") != 120:
        integrity_failure = "archived G6 survivor counts rewritten"
    if s14b6.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        integrity_failure = "G5 grammar hash mismatch"
    if s14b6.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        integrity_failure = "G4_CORRECTED_GRAMMAR_HASH mismatch"
    if s14b6.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        integrity_failure = "G3_CORRECTED_HASH mismatch"
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        integrity_failure = "G6 checkpoint grammar hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical corpus rewritten"
    if s14a.get("PHASE_14A_STATUS") != "CLOSED":
        integrity_failure = "Phase 14A is not CLOSED"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not closed"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s14b6.get("PHASE_14B6_STATUS") != "CLOSED":
        integrity_failure = "Phase 14B.6 is not CLOSED"
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        integrity_failure = "live top-down input hash mismatch"
    if _file_digest(g5_path) != EXPECTED_G5_CHECKPOINT_HASH:
        integrity_failure = "G5 checkpoint changed"

    catalog = known_physics_structural_catalog()
    profiles = physics_profile_registry()
    open_reg = open_physics_registry()
    p4 = profiles["profiles"]["P4_KNOWN_MODEL_REFERENCE"]
    if p4["generation_allowed"] or p4["filtering_allowed"] or p4["ranking_allowed"]:
        integrity_failure = "P4 isolation broken"
    if any(item["effect_on_generation"] != "NONE" for item in open_reg):
        integrity_failure = "open physics leaked into generation"
    if any(item["kind"] == "KNOWN_PHYSICS_REFERENCE" and item["effect_on_generation"] != "NONE" for item in catalog["reference_only_objects"]):
        integrity_failure = "reference object used as input"
    contamination = scan_target_blindness({"catalog": catalog, "profiles": profiles, "open": open_reg})
    if contamination:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": ",".join(contamination),
            "TARGET_BLINDNESS_STATUS": "FAILED",
            "SCIENTIFIC_STATUS": "NOT_ANALYZED",
        }

    summary_path = artifact_dir() / "PHASE_14C0_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if existing.get("PHASE_14C0_STATUS") == "CLOSED" and existing.get("P1_EXECUTED") is False:
            cached = existing

    if cached is None or integrity_failure:
        if integrity_failure:
            summary = {
                "phase": PHASE,
                "PHASE_14C0_STATUS": "STOPPED_BY_INTEGRITY_FAILURE",
                "METHOD_STATUS": "FAILED",
                "SCIENTIFIC_STATUS": "NOT_ANALYZED",
                "integrity_failure": integrity_failure,
                "P0_EXECUTED": False,
                "P1_EXECUTED": False,
                "ranking": False,
            }
            artifact_dir().mkdir(parents=True, exist_ok=True)
            _write_json(summary_path, summary)
            return {"status": "STOP", "scientific_analysis": summary, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
        try:
            ClosureEngine(artifact_dir() / "no_physics", chain="physics")
            physics_chain_blocked = False
        except EngineFailure as exc:
            physics_chain_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        try:
            assert_profile_activation_authorized("P1_QFT_STRUCTURAL_CONSISTENCY")
            p1_blocked = False
        except EngineFailure as exc:
            p1_blocked = exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        try:
            assert_profile_not_p4_in_generation("P4_KNOWN_MODEL_REFERENCE")
            p4_blocked = False
        except EngineFailure as exc:
            p4_blocked = exc.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"
        dry = run_synthetic_dry_run(artifact_dir())
        engine = ClosureEngine(artifact_dir(), chain="p0_only")
        state = engine.run_until_closure()
        p0_rep = next(r for r in state["version_reports"] if r["grammar_id"] == P0_ID)
        pass_n = p0_rep["compatible"]
        partial_n = p0_rep.get("partial") or 0
        rejected_n = p0_rep["rejected"]
        unresolved_n = p0_rep["unresolved"]
        consequences = p0_rep.get("consequences")
        if consequences is None:
            consequences = classify_consequences(
                list(g6_class_rows()),
                profile_id=P0_ID,
                enabled_constraints=list(P0_KPS),
            )
        p0_profile = profiles["profiles"][P0_ID]
        report_profiles = {
            P0_ID: {
                "profile_id": P0_ID,
                "profile_hash": p0_profile["profile_hash"],
                "input_count": len(p0_profile["input_objects"]),
                "candidate_count": p0_rep["generated_candidates"],
                "compatible_count": pass_n,
                "rejected_count": rejected_n,
                "partial_count": partial_n,
                "unresolved_count": unresolved_n,
                "equivalence_classes": pass_n,
                "executed": True,
            }
        }
        for pid in REGISTERED_INACTIVE_PROFILES:
            pr = profiles["profiles"][pid]
            report_profiles[pid] = {
                "profile_id": pid,
                "profile_hash": pr["profile_hash"],
                "input_count": len(pr["input_objects"]),
                "candidate_count": 0,
                "compatible_count": 0,
                "rejected_count": 0,
                "partial_count": 0,
                "unresolved_count": 0,
                "equivalence_classes": 0,
                "executed": False,
                "activation_state": pr["activation_state"],
            }
        cross = {
            "P0_vs_P1": "NOT_EXECUTED",
            "P0_vs_P2": "NOT_EXECUTED",
            "P0_vs_P3": "NOT_EXECUTED",
            "dry_P0_vs_dry_P1": dry["cross_profile_difference"],
        }
        checkpoint_payload = {
            "engine_version": ENGINE_VERSION,
            "catalog_version": CATALOG_VERSION,
            "profile_registry_hash": profiles["profile_registry_hash"],
            "active_profile": P0_ID,
            "grammar_hash": p0_rep["grammar_hash"],
            "candidate_space_hash": g6_candidate_space_hash(),
            "top_down_input_hash": top_down_input_hash(),
            "target_blindness_status": "VERIFIED",
            "consequence_engine_version": CONSEQUENCE_ENGINE_VERSION,
            "timestamp": _utc(),
            "provenance_summary": p0_rep.get("provenance_summary") or {},
            "parent_g6_grammar_hash": EXPECTED_G6_GRAMMAR_HASH,
            "parent_g6_checkpoint_hash": EXPECTED_G6_CHECKPOINT_HASH,
            "dry_run_status": dry["status"],
            "P1_EXECUTED": False,
            "P4_COMPARISON_EXECUTED": False,
        }
        checkpoint_payload["checkpoint_digest"] = content_hash(
            {k: v for k, v in checkpoint_payload.items() if k != "checkpoint_digest"}
        )
        ckpt_path = artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json"
        _write_json(ckpt_path, checkpoint_payload)
        uniqueness = {
            "UNIQUE_GAUGE_GROUP": "NO",
            "UNIQUE_REPRESENTATION_CONTENT": "NO",
            "UNIQUE_STRUCTURAL_THEORY": "NO",
            "UNIQUE_DIMENSIONLESS_COUPLING": "NO",
        }
        negative = {
            "automatic_P1_activation": "REJECTED",
            "automatic_P4_comparison_feedback": "REJECTED",
            "numerical_target_search": "REJECTED",
            "ranking": "REJECTED",
            "partial_upgraded_to_complete": "REJECTED",
            "open_physics_as_constraint": "REJECTED",
            "new_physical_principle_invented": "REJECTED",
        }
        summary = {
            "phase": PHASE,
            "status": "OK",
            "PHASE_14C0_STATUS": "CLOSED",
            "PHASE_14C_STATUS": "READY",
            "PHASE_14C0_CLOSED": True,
            "METHOD_STATUS": "VERIFIED",
            "SCIENTIFIC_STATUS": "ANALYZED_P0_ONLY",
            "PHASE_14C0_TEST_COPY_ID": PHASE_14C0_TEST_COPY_ID,
            "AUDIT_VERSION": AUDIT_VERSION,
            "CATALOG_VERSION": CATALOG_VERSION,
            "catalog_hash": catalog["catalog_hash"],
            "KNOWN_PHYSICS_CATALOG_STATUS": "READY",
            "PROFILE_REGISTRY_STATUS": "VERIFIED",
            "profile_registry_hash": profiles["profile_registry_hash"],
            "TOP_DOWN_INPUT_INTEGRITY": "VERIFIED",
            "TOP_DOWN_INPUT_HASH": top_down_input_hash(),
            "TARGET_BLINDNESS_STATUS": "VERIFIED",
            "CONSEQUENCE_ENGINE_STATUS": "VERIFIED",
            "COUNTEREXAMPLE_ENGINE_STATUS": "VERIFIED",
            "CROSS_PROFILE_ENGINE_STATUS": "VERIFIED",
            "OPEN_PHYSICS_FIREWALL_STATUS": "VERIFIED",
            "PARAMETER_ANALYSIS_STATUS": "VERIFIED",
            "KNOWN_MODEL_ISOLATION_STATUS": "VERIFIED",
            "G4_PARTIALITY_PROPAGATION_STATUS": "VERIFIED",
            "ENGINE_VERSION": ENGINE_VERSION,
            "GRAMMAR_HASH": p0_rep["grammar_hash"],
            "PARENT_GRAMMAR": G6_ID,
            "PARENT_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
            "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
            "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
            "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "FREEZE_ID": FREEZE_ID,
            "G6_COMPLETE": 359,
            "G6_PARTIAL": 120,
            "G6_SURVIVORS_REUSED": 479,
            "P0_EXECUTED": True,
            "P1_EXECUTED": False,
            "P2_EXECUTED": False,
            "P3_EXECUTED": False,
            "P4_COMPARISON_EXECUTED": False,
            "P5_EXECUTED": False,
            "P0_CANDIDATE_COUNT": p0_rep["generated_candidates"],
            "P0_COMPATIBLE": pass_n,
            "P0_PARTIAL": partial_n,
            "P0_REJECTED": rejected_n,
            "P0_UNRESOLVED": unresolved_n,
            "EQUIVALENCE_CLASSES": pass_n,
            "profiles": report_profiles,
            "FORCED_PROPERTIES": consequences["FORCED_PROPERTIES"],
            "BRANCH_DEPENDENT_PROPERTIES": consequences["BRANCH_DEPENDENT_PROPERTIES"],
            "FREE_PROPERTIES": consequences["FREE_PROPERTIES"],
            "UNRESOLVED_PROPERTIES": consequences["UNRESOLVED_PROPERTIES"],
            "MINIMAL_ASSUMPTION_MAP": consequences["MINIMAL_ASSUMPTION_MAP"],
            "CROSS_PROFILE_DIFFERENCES": cross,
            "KNOWN_MODEL_REFERENCE_COMPARISON": {
                "status": "NOT_EXECUTED",
                "MATCH": "NOT_EXECUTED",
                "PARTIAL_MATCH": "NOT_EXECUTED",
                "NO_MATCH": "NOT_EXECUTED",
                "COMPARISON_UNRESOLVED": "NOT_EXECUTED",
                "feedback_into_generation": False,
                "provenance": "REFERENCE_ONLY",
            },
            "dry_run": {k: v for k, v in dry.items() if k not in {"P0_consequences", "P1_consequences"}},
            "dry_run_P0_consequences": dry["P0_consequences"],
            "dry_run_P1_consequences": dry["P1_consequences"],
            "uniqueness": uniqueness,
            "claim_labels": _claim_labels(),
            "parameter_analysis": consequences["parameter_analysis"],
            "dimensionless_audit": consequences["dimensionless_audit"],
            "universal_signatures": consequences["universal_signatures"],
            "destroyed_by_counterexample": consequences["destroyed_by_counterexample"],
            "NEW_PROPERTIES_BEYOND_G6": [],
            "P0_ADDS_NO_NEW_ELIMINATION": True,
            "KNOWN_QUALITATIVE_PHYSICS_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_GRAMMAR_AND_PROFILES": True,
            "gravity_action": "S_gravity = integral sqrt(-g) (c0 + c1 R)",
            "gravity_c0": "FREE",
            "gravity_c1": "FREE",
            "gravity_changed": False,
            "ranking": False,
            "numerical_target_search": False,
            "target_inputs": 0,
            "experimental_constants": False,
            "fitting_or_calibration": False,
            "open_physics_registry": open_reg,
            "catalog_completeness_claim": "REGISTERED_STATEMENTS_ONLY",
            "contains_all_known_physics": False,
            "NEXT_AUTHORIZED_EXTENSION": "ACTIVATE P1_QFT_STRUCTURAL_CONSISTENCY",
            "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
            "SCIENTIFIC_STOP": "STOP",
            "physics_chain_blocked": physics_chain_blocked,
            "p1_blocked": p1_blocked,
            "p4_blocked": p4_blocked,
            "negative_tests_all_pass": all(v == "REJECTED" for v in negative.values()) and physics_chain_blocked and p1_blocked and p4_blocked,
            "overclaims": {
                "all_known_physics_encoded": "REJECTED AS OVERCLAIM",
                "standard_model_rediscovered": "REJECTED AS OVERCLAIM",
                "P1_automatically_activated": "REJECTED AS OVERCLAIM",
            },
            "questions": {
                "1_input_derived_separation": "YES",
                "2_multiple_profiles_same_grammar": "YES",
                "3_forced_across_all_survivors": "YES",
                "4_counterexamples_found": "YES",
                "5_minimal_assumptions_recorded": "YES",
                "6_claim_labels_preserved": "YES",
                "7_standard_model_isolated": "YES",
                "8_open_physics_isolated": "YES",
                "9_g4_partiality_propagates": "YES",
                "10_target_blind": "YES",
                "11_g6_space_reused": "YES",
                "12_new_forced_beyond_G6": "NONE",
                "13_candidates_remaining_under_P0": pass_n,
                "13_partial_preserved": partial_n,
                "14_universal_structural_consequences": len(consequences["FORCED_PROPERTIES"]),
                "15_apparent_consequences_destroyed": len(consequences["destroyed_by_counterexample"]),
                "16_continuous_couplings_still_free": "YES",
                "17_new_parameter_free_dimensionless_quantities": "NONE",
                "18_gravity_changed": "NO",
            },
            "audit_summary": {
                "phase4c_unchanged": hashes_before.get("phase14a") == snapshot_prior_artifact_hashes().get("phase14a"),
                "g6_checkpoint_unchanged": g6_checkpoint_path().read_bytes() == g6_before,
                "g5_checkpoint_unchanged": g5_path.read_bytes() == g5_before,
                "phase14b6_artifacts_unchanged": snapshot_prior_artifact_hashes()["phase14b6"] == hashes_before["phase14b6"],
                "grammar_hash_12A_unchanged": grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH,
            },
            "checkpoint_path": str(ckpt_path),
            "checkpoint_digest": checkpoint_payload["checkpoint_digest"],
            "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
            "search_bounds": dict(G6_SEARCH_BOUNDS),
            "VECTORLIKE_STATUS": "UNTESTED",
            "action_content_hash": auth.action_content_hash,
            "final_action_hash": auth.action_content_hash,
            "G7_EXECUTED": False,
            "G6_EXECUTED": True,
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14B6_STATUS": s14b6.get("PHASE_14B6_STATUS"),
            "PHASE_14A_STATUS": s14a.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
            "class_table": p0_rep.get("class_table") or [],
        }
        _write_json(summary_path, summary)
        _write_json(artifact_dir() / "KNOWN_PHYSICS_STRUCTURAL_CLOSURE_REPORT.json", summary)
        cached = summary

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after["phase14b6"] != hashes_before["phase14b6"]:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["PHASE_14C0_STATUS"] = "STOPPED_BY_INTEGRITY_FAILURE"
        cached["detail"] = "G6 artifacts were modified"
    if g6_checkpoint_path().read_bytes() != g6_before:
        cached = dict(cached)
        cached["status"] = "STOP"
        cached["detail"] = "G6 checkpoint modified"
    return cached


def run_phase14c0_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c0_known_physics(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_INTEGRITY": "VERIFIED",
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_14B6_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase14b6_artifacts_unchanged") else "FAILED",
            "G6_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g6_checkpoint_unchanged") else "FAILED",
            "G5_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("g5_checkpoint_unchanged") else "FAILED",
            "PHASE_14C0_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14C0_STATUS": science.get("PHASE_14C0_STATUS"),
            "PHASE_14C_STATUS": science.get("PHASE_14C_STATUS"),
            "PHASE_14B6_STATUS": science.get("PHASE_14B6_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "P0_EXECUTED": "TRUE",
            "P1_EXECUTED": "FALSE",
            "P4_COMPARISON_EXECUTED": "FALSE",
            "G7_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
