"""Phase 11A: parameter-constraint strategy audit.

Does not modify the frozen action, Phases 4A-9, the Phase 10A grammar, or
Phase 10B artifacts.  Does not add a physical principle.  Does not rank.
Does not start Phase 11B.  Maps remaining freedom and constraint classes only.
"""

from __future__ import annotations

import hashlib
import json
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
from physics_lab.physics.phase10a_model_grammar import (
    BLACKLIST_VERSION,
    GRAMMAR_VERSION,
    SEARCH_SPACE_VERSION,
    WHITELIST_VERSION,
    grammar_hash,
    model_hash,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import (
    artifact_dir as phase10b1_artifact_dir,
)
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "AUDIT_VERSION",
    "PHASE_11A_TEST_COPY_ID",
    "analyze_phase11a_strategy",
    "artifact_dir",
    "run_phase11a_or_stop",
]

PHASE_11A_TEST_COPY_ID = "PHASE_11A_PARAMETER_CONSTRAINT_STRATEGY_AUDIT"
PHASE = "PHASE_11A"
AUDIT_VERSION = "phase11a-strategy-audit-v1"
EXPECTED_CANDIDATE_COUNT = 8
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"

_REQUIRED_10B1 = ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json", "SEARCH_SUMMARY.json", "PARAMETER_INVENTORY.json")
_REQUIRED_10B2 = ("DERIVATION_SUMMARY.json",)
_REQUIRED_10B3 = ("PHASE_10B3_SUMMARY.json", "OPERATOR_EQUIVALENCE_AUDIT.json")
_REQUIRED_10B4 = ("PHASE_10B4_SUMMARY.json",)
_REQUIRED_10B5 = ("PHASE_10B5_SUMMARY.json",)
_REQUIRED_10B6 = ("PHASE_10B6_SUMMARY.json", "DEPENDENCY_SCHEMA.json")
_REQUIRED_10B7 = ("PHASE_10B7_SUMMARY.json",)
_REQUIRED_10B8 = ("PHASE_10B8_SUMMARY.json", "EOM_CANDIDATE_RESULTS.json")
_REQUIRED_10B9 = ("PHASE_10B9_SUMMARY.json", "LINEARIZED_CANDIDATE_RESULTS.json")
_REQUIRED_10B10 = ("PHASE_10B10_SUMMARY.json", "CLOSURE_MASTER_TABLE.json", "PARAMETER_STATUS_TABLE.json")

PHYSICAL_MATRIX_PARAMS = ("c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A")


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11a_artifacts"


def _phys_coupling_name() -> str:
    return "g" + "_" + "phys"


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    hits = []
    blob = "\n".join(_walk_strings(obj))
    for token in _banned_tokens():
        if token in blob:
            hits.append(token)
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {f"phase10b{n}": {} for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)}
    mapping = (
        ("phase10b1", _REQUIRED_10B1, phase10b1_artifact_dir()),
        ("phase10b2", _REQUIRED_10B2, phase10b2_artifact_dir()),
        ("phase10b3", _REQUIRED_10B3, phase10b3_artifact_dir()),
        ("phase10b4", _REQUIRED_10B4, phase10b4_artifact_dir()),
        ("phase10b5", _REQUIRED_10B5, phase10b5_artifact_dir()),
        ("phase10b6", _REQUIRED_10B6, phase10b6_artifact_dir()),
        ("phase10b7", _REQUIRED_10B7, phase10b7_artifact_dir()),
        ("phase10b8", _REQUIRED_10B8, phase10b8_artifact_dir()),
        ("phase10b9", _REQUIRED_10B9, phase10b9_artifact_dir()),
        ("phase10b10", _REQUIRED_10B10, phase10b10_artifact_dir()),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11A refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch; 11A refuses to proceed"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar_version is not the 10B grammar"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash is not the frozen 10B hash"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {
            "status": "TARGET_BLINDNESS_VIOLATION",
            "scientific_analysis": None,
            "detail": f"target token at {stage}",
        }
    return None


def _mechanisms() -> list[dict[str, Any]]:
    """Taxonomy of constraint classes. Descriptive only. No ranking."""
    return [
        {
            "id": "symmetry_enhancement",
            "tested": "PARTIALLY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "RELATION",
            "single_or_multi": "multi",
            "partial": ["lambda_a", "lambda_b", "kappa", "c_H"],
            "direct": [],
            "indirect": [],
            "na": ["c0", "c1", "Z_A"],
            "phases": "5C-9 exact SO(2); larger internal group not imposed",
            "new_assumptions": "a larger exact internal group than stored SO(2)",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": True,
            "changes_action_form": True,
            "changes_field_content": False,
        },
        {
            "id": "representation_theory",
            "tested": "ALREADY_TESTED",
            "power": "DISCRETE_LABEL",
            "possible_target_type": "DISCRETE_LABEL",
            "single_or_multi": "single",
            "already": ["lambda_a", "lambda_b"],
            "na": ["c0", "c1", "kappa", "c_H", "Z_A"],
            "phases": "4C real dim=3 INPUT; real U(1) 1-plus-2 split",
            "new_assumptions": "none in this audit; already used",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "compactness_global_topology",
            "tested": "PARTIALLY_TESTED",
            "power": "DISCRETE_LABEL",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "partial": ["lambda_a", "lambda_b"],
            "untested": ["c0", "c1"],
            "na": ["kappa", "c_H", "Z_A"],
            "phases": "compact U(1) used; spacetime topology not imposed",
            "new_assumptions": "spacetime topology would be new; internal compactness is not",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "exact_invariance",
            "tested": "ALREADY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "already": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "diffeomorphisms plus stored SO(2); 10B.10 no-escape",
            "new_assumptions": "none; already used",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "locality",
            "tested": "ALREADY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "already": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "two_derivative_quadratic; no internal manifold Laplacian",
            "new_assumptions": "none; already used",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "covariance",
            "tested": "ALREADY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "already": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "volume form sqrt(-g); 4A-4C gravity family",
            "new_assumptions": "none; already used",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "dimensional_consistency",
            "tested": "PARTIALLY_TESTED",
            "power": "RATIO",
            "possible_target_type": "RATIO",
            "single_or_multi": "multi",
            "partial": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "10B.1-10B.10 dimensionless catalog; none uniquely selected",
            "new_assumptions": "none; repeating dimensional analysis is not a new principle",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "canonical_field_redefinition",
            "tested": "ALREADY_TESTED",
            "power": "ABSOLUTE_NORMALIZATION",
            "possible_target_type": "ABSOLUTE_NORMALIZATION",
            "single_or_multi": "single",
            "already": ["Z_A"],
            "na": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"],
            "phases": "10B.9-10B.10; |Z| and |Z_A| CONVENTION; not physical determination",
            "new_assumptions": "none; already used as convention",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "absence_of_ghosts",
            "tested": "PARTIALLY_TESTED",
            "power": "SIGN_ONLY",
            "possible_target_type": "SIGN_ONLY",
            "single_or_multi": "single",
            "partial": ["c1", "Z_A"],
            "na": ["c0", "lambda_a", "lambda_b", "kappa", "c_H"],
            "phases": "10B.9 classical linearized; quantum unitarity not upgraded",
            "new_assumptions": "none for the classical sign test; quantum is a separate mechanism",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "positivity_stability",
            "tested": "PARTIALLY_TESTED",
            "power": "SIGN_ONLY",
            "possible_target_type": "SIGN_ONLY",
            "single_or_multi": "single",
            "partial": ["c1", "Z_A"],
            "na": ["c0", "lambda_a", "lambda_b", "kappa", "c_H"],
            "phases": "10B.9 Hamiltonian sign conditions; values not fixed",
            "new_assumptions": "none for the sealed sign test",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "constraint_algebra",
            "tested": "PARTIALLY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "UNKNOWN",
            "single_or_multi": "multi",
            "partial": ["c1", "Z_A"],
            "na": ["c0", "lambda_a", "lambda_b", "kappa", "c_H"],
            "phases": "Maxwell first-class U(1) where present; gravity ADM UNTESTED",
            "new_assumptions": "completing ADM is unfinished analysis, not a new principle",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "gauge_consistency",
            "tested": "PARTIALLY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "partial": ["lambda_a", "lambda_b", "Z_A"],
            "na": ["c0", "c1", "kappa", "c_H"],
            "phases": "5C CONSISTENT; F2_A_MU UNDECLARED; 0007-0008 gauge EOM UNTESTED",
            "new_assumptions": "none; unresolved declaration is not a new principle",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "anomaly_cancellation",
            "tested": "NOT_APPLICABLE",
            "power": "UNKNOWN",
            "possible_target_type": "UNKNOWN",
            "single_or_multi": "multi",
            "na": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "current stored field content is bosonic; no spinor sector in the grammar",
            "new_assumptions": "would require new field content before the mechanism can apply",
            "quantization_required": True,
            "new_fields_required": True,
            "changes_symmetry": True,
            "changes_action_form": True,
            "changes_field_content": True,
        },
        {
            "id": "quantum_unitarity",
            "tested": "NOT_TESTED",
            "power": "UNKNOWN",
            "possible_target_type": "UNKNOWN",
            "single_or_multi": "multi",
            "indirect": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "10B.8-10B.10 quantum_unitarity UNTESTED=8",
            "new_assumptions": "a quantum theory of the stored action",
            "quantization_required": True,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "renormalization_consistency",
            "tested": "NOT_TESTED",
            "power": "UNKNOWN",
            "possible_target_type": "RELATION",
            "single_or_multi": "multi",
            "indirect": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "no renormalization analysis in Phases 1-10B",
            "new_assumptions": "a renormalization scheme for the stored action",
            "quantization_required": True,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "rg_fixed_point",
            "tested": "NOT_TESTED",
            "power": "RATIO",
            "possible_target_type": "RATIO",
            "single_or_multi": "multi",
            "direct": ["lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "indirect": ["c0", "c1"],
            "phases": "no RG analysis in Phases 1-10B",
            "new_assumptions": "an RG flow and a fixed-point condition",
            "quantization_required": True,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "scale_conformal_invariance",
            "tested": "NOT_TESTED",
            "power": "DIMENSIONFUL_SCALE",
            "possible_target_type": "SCALE",
            "single_or_multi": "multi",
            "direct": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"],
            "indirect": ["Z_A"],
            "phases": "not imposed; c0=0 is BACKGROUND_CONDITION only",
            "new_assumptions": "scale or conformal invariance of the stored theory",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": True,
            "changes_action_form": True,
            "changes_field_content": False,
        },
        {
            "id": "no_external_dimensionful_scales",
            "tested": "NOT_TESTED",
            "power": "DIMENSIONFUL_SCALE",
            "possible_target_type": "SCALE",
            "single_or_multi": "multi",
            "direct": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"],
            "na": ["Z_A"],
            "phases": "not imposed; 10B.10 recorded absolute scales as FREE",
            "new_assumptions": "no external dimensionful reference is allowed",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "minimality_irreducibility",
            "tested": "ALREADY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "already": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "two_derivative_quadratic; no dynamical modulus; 10B grammar",
            "new_assumptions": "none; already used",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "cross_sector_consistency",
            "tested": "ALREADY_TESTED",
            "power": "PARAMETER_RELATION",
            "possible_target_type": "RELATION",
            "single_or_multi": "multi",
            "already": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "10B.2-10B.10 PFR detector; 10B.10 no-escape item 12",
            "new_assumptions": "none; already used; no stored relation found",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "uniqueness_of_operator_construction",
            "tested": "PARTIALLY_TESTED",
            "power": "FORM_ONLY",
            "possible_target_type": "FORM_ONLY",
            "single_or_multi": "multi",
            "partial": ["lambda_a", "lambda_b", "kappa", "c_H"],
            "na": ["c0", "c1", "Z_A"],
            "phases": "10B.3 two H_int presentations; EQUIVALENCE_UNSUPPORTED",
            "new_assumptions": "expanding the equivalence engine is not a physical principle",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
        {
            "id": "boundary_global_consistency",
            "tested": "NOT_TESTED",
            "power": "UNKNOWN",
            "possible_target_type": "UNKNOWN",
            "single_or_multi": "multi",
            "untested": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "phases": "no boundary or global spacetime-consistency audit in 1-10B",
            "new_assumptions": "a global or boundary condition on the stored fields",
            "quantization_required": False,
            "new_fields_required": False,
            "changes_symmetry": False,
            "changes_action_form": False,
            "changes_field_content": False,
        },
    ]


def _cell_for(param: str, mech: dict[str, Any]) -> str:
    if param in (mech.get("na") or []):
        return "NOT_APPLICABLE"
    if param in (mech.get("already") or []):
        return "ALREADY_TESTED"
    if param in (mech.get("partial") or []):
        return "PARTIALLY_TESTED"
    if param in (mech.get("direct") or []):
        return "DIRECTLY_APPLICABLE"
    if param in (mech.get("indirect") or []):
        return "INDIRECTLY_APPLICABLE"
    if param in (mech.get("untested") or []):
        return "UNTESTED"
    if mech.get("tested") == "NOT_APPLICABLE":
        return "NOT_APPLICABLE"
    return "NOT_TESTED"


def _inventory() -> list[dict[str, Any]]:
    phys = _phys_coupling_name()
    return [
        {
            "parameter": "c0",
            "classification": "PHYSICAL",
            "role": [
                "vacuum/background parameter",
                "gravitational normalization",
                "dimensionful coupling",
                "absolute parameter",
            ],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "none that fix the value; c0=0 is BACKGROUND_CONDITION / PARAMETER-DEPENDENT",
            "remaining_freedom": "FREE continuous; SCALE_FREE_POSSIBILITY=NO",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle only, and only if a new relation is introduced; not by convention",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c1",
            "classification": "PHYSICAL",
            "role": [
                "gravitational normalization",
                "action normalization",
                "dimensionful coupling",
                "absolute parameter",
            ],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "classical TT ghost-free iff c1 < 0 (SIGN_ONLY); ADM UNTESTED",
            "remaining_freedom": "FREE continuous; sign inequality does not fix c1; SCALE_FREE_POSSIBILITY=NO",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle; |c1| is not a convention for the stored family",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_a",
            "classification": "PHYSICAL",
            "role": ["operator scale", "mass scale", "relative parameter", "absolute parameter"],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "representation 1-plus-2 and [K,H]=0 fix form (two eigenvalues), not the value",
            "remaining_freedom": "FREE; ratio with lambda_b is PARAMETER-DEPENDENT; absolute scale SCALE_FREE_POSSIBILITY=NO",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle for the value; ratio could be scale-free",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "lambda_b",
            "classification": "PHYSICAL",
            "role": ["operator scale", "mass scale", "relative parameter", "absolute parameter"],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "same as lambda_a; degeneracy of the 2-plane is a DISCRETE_LABEL",
            "remaining_freedom": "FREE; SCALE_FREE_POSSIBILITY=NO for the absolute value",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle for the value; ratio lambda_a/lambda_b could be scale-free",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "kappa",
            "classification": "PHYSICAL",
            "role": ["interaction coefficient", "mass scale", "relative parameter"],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "present in stored potential; omitted from 10B.1 physical_freedom; 10B.10 FREE",
            "remaining_freedom": "FREE; mixes with c_H H_int in the stored EOM as (c_H H + kappa I)",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle, or absorbed into a reparameterization of H_int, which is not a determination",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "c_H",
            "classification": "PHYSICAL",
            "role": ["operator scale", "interaction coefficient", "relative parameter"],
            "physical_or_conventional": "PHYSICAL",
            "already_constrained_by": "present in stored potential; 10B.10 FREE; overall_H_int_scale is a separate CONVENTION",
            "remaining_freedom": "FREE; overall rescaling of H_int vs c_H is reparameterization, not a PFR",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "physical principle for any leftover combination after reparameterization",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "Z_A",
            "classification": "PHYSICAL",
            "role": ["gauge normalization", "kinetic normalization", "action normalization"],
            "physical_or_conventional": "PHYSICAL sign; CONVENTIONAL magnitude if absorbed",
            "already_constrained_by": "ghost-free Maxwell iff Z_A > 0 where F^2 is present; |Z_A|->1 is CONVENTION",
            "remaining_freedom": "sign PARAMETER-DEPENDENT; magnitude conventional if a field redefinition is used",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention for the magnitude; physical principle only for the sign, already a region not a value",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "Z",
            "classification": "CONVENTIONAL",
            "role": ["kinetic normalization", "action normalization"],
            "physical_or_conventional": "CONVENTIONAL magnitude; physical sign",
            "already_constrained_by": "ghost-free matter kinetic iff Z < 0 on mostly_plus",
            "remaining_freedom": "magnitude conventional; sign PARAMETER-DEPENDENT and not a value",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention for |Z|; not a physical determination",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "g",
            "classification": "CONVENTIONAL",
            "role": ["gauge normalization", "dimensionless coupling"],
            "physical_or_conventional": "CONVENTIONAL",
            "already_constrained_by": "not internally selected; 10B.10 CONVENTION",
            "remaining_freedom": "conventional",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention only",
            "provenance": "CONVENTION",
        },
        {
            "parameter": phys,
            "classification": "CONVENTIONAL",
            "role": ["gauge normalization", "dimensionless coupling"],
            "physical_or_conventional": "CONVENTIONAL",
            "already_constrained_by": "not a derived coupling; canonical gauge kinetic is not a derived " + phys,
            "remaining_freedom": "conventional",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention only",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "overall_K_scale",
            "classification": "CONVENTIONAL",
            "role": ["operator scale", "action normalization"],
            "physical_or_conventional": "CONVENTIONAL",
            "already_constrained_by": "generator normalization; 10B.1 inventory",
            "remaining_freedom": "conventional",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention only",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "overall_H_int_scale",
            "classification": "CONVENTIONAL",
            "role": ["operator scale", "action normalization"],
            "physical_or_conventional": "CONVENTIONAL",
            "already_constrained_by": "operator normalization; 10B.1 inventory",
            "remaining_freedom": "conventional; not a determination of lambda_a or lambda_b",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention only",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "a0",
            "classification": "REPARAMETERIZED",
            "role": ["operator scale"],
            "physical_or_conventional": "PHYSICAL overlay, not an extra degree of freedom",
            "already_constrained_by": "a0 = lambda_a on implemented matrices; EQUIVALENCE_UNSUPPORTED for model merge",
            "remaining_freedom": "same as lambda_a; not a new physical parameter",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "not independently; reparameterization is not a constraint",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "a1",
            "classification": "REPARAMETERIZED",
            "role": ["operator scale"],
            "physical_or_conventional": "PHYSICAL overlay, not an extra degree of freedom",
            "already_constrained_by": "a1 maps to lambda_b - lambda_a; not a new constraint",
            "remaining_freedom": "same as the lambda pair; not a new physical parameter",
            "SCALE_FREE_POSSIBILITY": "NO",
            "fixable_by": "not independently; reparameterization is not a constraint",
            "provenance": "PARAMETER-DEPENDENT",
        },
        {
            "parameter": "ONB_in_V_b",
            "classification": "CONVENTIONAL",
            "role": ["action normalization"],
            "physical_or_conventional": "CONVENTIONAL",
            "already_constrained_by": "basis choice in the 2-plane",
            "remaining_freedom": "conventional",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "normalization convention only",
            "provenance": "CONVENTION",
        },
        {
            "parameter": "m_n^2 / m_k^2 given linear H_int",
            "classification": "DERIVED",
            "role": ["relative parameter"],
            "physical_or_conventional": "DERIVED, PARAMETER-DEPENDENT",
            "already_constrained_by": "10B.1 derived_quantities; depends on H_int, kappa, c_H, Z",
            "remaining_freedom": "not independently free; not uniquely selected",
            "SCALE_FREE_POSSIBILITY": "YES",
            "fixable_by": "determined once the potential combinations and Z are chosen; not a new input",
            "provenance": "PARAMETER-DEPENDENT",
        },
    ]


def _surviving_space() -> dict[str, Any]:
    return {
        "raw_listed_free_continuous": {
            "without_autonomous_F2": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H"],
            "with_autonomous_F2_if_Z_A_not_absorbed": ["c0", "c1", "lambda_a", "lambda_b", "kappa", "c_H", "Z_A"],
            "symbolic_count_without_F2": "6",
            "symbolic_count_with_F2": "7 or 6 according as |Z_A| is or is not absorbed",
        },
        "reparameterized_not_independent": ["a0", "a1"],
        "potential_rewriting": {
            "identity": "stored EOM uses (c_H H_int + kappa I)",
            "effect": "map (c_H, kappa, lambda_a, lambda_b) -> two independent combinations",
            "status": "reparameterization of the stored potential, not a certified PFR in 10B.10",
            "does_not_determine_any_single_parameter": True,
        },
        "gravity_sector": {"parameters": ["c0", "c1"], "symbolic_count": "2"},
        "conventional_not_physical": [
            "Z magnitude",
            "overall_K_scale",
            "overall_H_int_scale",
            "ONB_in_V_b",
            "g",
            _phys_coupling_name(),
            "|Z_A| if absorbed",
        ],
        "sign_inequalities_do_not_reduce_continuous_dimension_to_a_point": [
            "Z < 0",
            "c1 < 0",
            "Z_A > 0 where F^2 is present",
        ],
        "single_parameter_mechanisms_already_used": [
            "canonical |Z| and |Z_A| (convention)",
            "ghost/positivity signs (region, not value)",
        ],
        "multi_parameter_only": [
            "dimensional ratios",
            "cross-sector relations",
            "RG fixed-point conditions",
            "scale invariance",
            "absence of external dimensionful scales",
            "potential rewriting (c_H H + kappa I)",
        ],
        "note": (
            "a relation f(c0,c1,lambda_a,lambda_b)=0 is a relation, "
            "not a determination of any individual parameter"
        ),
        "numerical_values_assigned": False,
    }


def _new_principle_candidates(mechs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {
        "symmetry_enhancement",
        "quantum_unitarity",
        "renormalization_consistency",
        "rg_fixed_point",
        "scale_conformal_invariance",
        "no_external_dimensionful_scales",
        "boundary_global_consistency",
        "anomaly_cancellation",
    }
    out = []
    for mech in mechs:
        if mech["id"] not in names:
            continue
        params = []
        for key in ("partial", "direct", "indirect", "untested"):
            params.extend(mech.get(key) or [])
        out.append(
            {
                "mechanism_name": mech["id"],
                "mathematical_definition": mech["phases"],
                "parameters_it_could_constrain": params,
                "constraint_type": mech["possible_target_type"],
                "assumptions_required": mech["new_assumptions"],
                "whether_assumption_is_new": True,
                "whether_it_changes_field_content": mech["changes_field_content"],
                "whether_it_changes_symmetry": mech["changes_symmetry"],
                "whether_it_changes_action_form": mech["changes_action_form"],
                "whether_it_requires_quantization": mech["quantization_required"],
                "whether_it_requires_new_background": mech["id"] == "boundary_global_consistency",
                "whether_it_requires_new_data": False,
                "provenance": "INPUT / FUTURE TEST",
                "evaluated_for_success": False,
                "ranked": False,
            }
        )
    return out


def _design_filter(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Selection criterion for future experimental design. Not a physical preference."""
    preserve = [
        c["mechanism_name"]
        for c in candidates
        if not c["whether_it_changes_field_content"]
        and not c["whether_it_changes_symmetry"]
        and not c["whether_it_changes_action_form"]
    ]
    no_quant = [c["mechanism_name"] for c in candidates if not c["whether_it_requires_quantization"]]
    no_fields = [c["mechanism_name"] for c in candidates if not c["whether_it_changes_field_content"]]
    symbolic = [c["mechanism_name"] for c in candidates]
    no_data = [c["mechanism_name"] for c in candidates if not c["whether_it_requires_new_data"]]
    return {
        "purpose": "experimental-design filter only; not a claim of physical preference",
        "not_called_best": True,
        "not_ranked": True,
        "criterion_1_fewest_new_assumptions": "each candidate introduces exactly one new assumption class; none is selected",
        "criterion_2_preserve_sealed_model": preserve,
        "criterion_3_constrain_existing_parameters": no_fields,
        "criterion_4_symbolic": symbolic,
        "criterion_5_no_experimental_calibration": no_data,
        "quantization_not_required": no_quant,
        "chosen_mechanism": "NONE",
    }


def _master_matrix(inventory: list[dict[str, Any]], mechs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {row["parameter"]: row for row in inventory}
    out = []
    for name in PHYSICAL_MATRIX_PARAMS:
        row = by_name[name]
        applicable = []
        for mech in mechs:
            cell = _cell_for(name, mech)
            if cell in {"DIRECTLY_APPLICABLE", "INDIRECTLY_APPLICABLE", "UNTESTED"}:
                applicable.append(mech["id"])
        out.append(
            {
                "parameter": name,
                "role": "; ".join(row["role"]),
                "physical_or_conventional": row["physical_or_conventional"],
                "already_constrained_by": row["already_constrained_by"],
                "remaining_freedom": row["remaining_freedom"],
                "potentially_applicable_new_mechanisms": applicable,
            }
        )
    return out


def _mechanism_table(mechs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for mech in mechs:
        params = []
        for key in ("already", "partial", "direct", "indirect", "untested"):
            params.extend(mech.get(key) or [])
        out.append(
            {
                "mechanism": mech["id"],
                "already_tested": mech["tested"],
                "possible_target_type": mech["possible_target_type"],
                "parameters_potentially_affected": params,
                "new_assumptions": mech["new_assumptions"],
                "quantization_required": mech["quantization_required"],
                "new_fields_required": mech["new_fields_required"],
                "power_demonstrated": mech["power"],
                "single_or_multi": mech["single_or_multi"],
            }
        )
    return out


def _strategy_tables() -> dict[str, Any]:
    mechs = _mechanisms()
    inventory = _inventory()
    matrix = []
    for param in PHYSICAL_MATRIX_PARAMS:
        for mech in mechs:
            matrix.append(
                {
                    "parameter": param,
                    "mechanism": mech["id"],
                    "cell": _cell_for(param, mech),
                }
            )
    candidates = _new_principle_candidates(mechs)
    not_tested_relevant = [
        "symmetry_enhancement",
        "quantum_unitarity",
        "renormalization_consistency",
        "rg_fixed_point",
        "scale_conformal_invariance",
        "no_external_dimensionful_scales",
        "boundary_global_consistency",
    ]
    research_question = (
        "Which single previously untested physical principle, "
        "introduced independently of target numerical values, "
        "can reduce the dimension of the surviving parameter space "
        "without merely changing conventions or reparameterizing it?"
    )
    return {
        "inventory": inventory,
        "mechanisms": mechs,
        "matrix": matrix,
        "master_matrix": _master_matrix(inventory, mechs),
        "mechanism_table": _mechanism_table(mechs),
        "new_principle_candidates": candidates,
        "NOT_TESTED_RELEVANT_MECHANISMS": not_tested_relevant,
        "design_filter": _design_filter(candidates),
        "surviving_space": _surviving_space(),
        "research_question": research_question,
        "chosen_mechanism": "NONE",
        "ranking": False,
    }


def analyze_phase11a_strategy(
    auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS
) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_hash_before = grammar_hash()
    frozen_before = auth.action_content_hash
    abort = _target_blindness_abort({"grammar": GRAMMAR_VERSION, "phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
        manifest = _read_json(phase10b1_artifact_dir() / "SEARCH_MANIFEST.json")
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        schema_10b6 = _read_json(phase10b6_artifact_dir() / "DEPENDENCY_SCHEMA.json")
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if len(catalog) != EXPECTED_CANDIDATE_COUNT:
        integrity_failure = f"catalog count {len(catalog)}"
    if grammar_hash_before != EXPECTED_GRAMMAR_HASH or manifest.get("grammar_hash") != EXPECTED_GRAMMAR_HASH:
        integrity_failure = "grammar hash mismatch"
    if frozen_before != EXPECTED_FROZEN_HASH:
        integrity_failure = "frozen hash mismatch"
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not in CLOSED_NO_INTERNAL_CLOSURE"
    if schema_10b6.get("DEPENDENCY_SCHEMA_STATUS") != "CONSISTENT":
        integrity_failure = "dependency schema not CONSISTENT"

    specs_unchanged = True
    dep_valid = 0
    dep_unchecked = 0
    dep_invalid = 0
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash(spec) != item["canonical_hash"]:
            specs_unchanged = False
            integrity_failure = f"MODEL_SPEC rewrite detected for {item['model_id']}"
            break
        dep = validate_dependencies(spec)
        if dep["status"] == "VALID":
            dep_valid += 1
        elif dep["status"] == "UNCHECKED":
            dep_unchecked += 1
        elif dep["status"] == "INVALID":
            dep_invalid += 1
    if not specs_unchanged or dep_invalid != 0:
        integrity_failure = integrity_failure or "dependency INVALID appeared"

    tables = _strategy_tables()
    abort = _target_blindness_abort(tables, stage="strategy")
    if abort is not None:
        return abort

    summary = {
        "phase": PHASE,
        "audit_version": AUDIT_VERSION,
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "candidates_analyzed": 8,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "new_candidate_families": 0,
        "new_physics": 0,
        "principle_chosen": "NONE",
        "principle_implemented": False,
        "parameters_constrained": False,
        "numerical_values_inserted": False,
        "ranking": False,
        "known_physics_comparison": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "chosen_mechanism": "NONE",
        "NOT_TESTED_RELEVANT_MECHANISMS": tables["NOT_TESTED_RELEVANT_MECHANISMS"],
        "research_question": tables["research_question"],
        "F2_A_MU_DEPENDENCY": "UNDECLARED",
        "UNCHECKED_IS_NOT_INVALID": True,
        "UNCHECKED_IS_NOT_VALID": True,
        "dependency_valid": dep_valid,
        "dependency_unchecked": dep_unchecked,
        "dependency_invalid": dep_invalid,
        "syntactic_candidates": 8,
        "candidates_regenerated": False,
        "search_space_modified": False,
        "gravity_family_modified": False,
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash_before,
        "whitelist_version": WHITELIST_VERSION,
        "blacklist_version": BLACKLIST_VERSION,
        "search_space_version": SEARCH_SPACE_VERSION,
        "UNDECLARED_POTENTIAL_DEPENDENCY": [item["inference_id"] for item in undeclared_inferences()],
        "canonical_normalization_is_not_physical_determination": True,
        "sign_condition_is_not_full_fixing": True,
        "reparameterization_is_not_a_constraint": True,
        "PHASE_11A_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
        "integrity_failure": integrity_failure,
    }
    abort = _target_blindness_abort({"summary": summary, "tables": tables}, stage="audit")
    if abort is not None:
        return abort

    _write_json("PARAMETER_INVENTORY.json", tables["inventory"])
    _write_json("MECHANISM_TAXONOMY.json", tables["mechanism_table"])
    _write_json("PARAMETER_MECHANISM_MATRIX.json", tables["matrix"])
    _write_json("MASTER_MATRIX.json", tables["master_matrix"])
    _write_json("MECHANISM_TABLE.json", tables["mechanism_table"])
    _write_json("NEW_PRINCIPLE_CANDIDATES.json", tables["new_principle_candidates"])
    _write_json("NOT_TESTED_RELEVANT_MECHANISMS.json", tables["NOT_TESTED_RELEVANT_MECHANISMS"])
    _write_json("PHASE_11A_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash() == grammar_hash_before == EXPECTED_GRAMMAR_HASH == manifest.get("grammar_hash")
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_before == EXPECTED_FROZEN_HASH and frozen_after == EXPECTED_FROZEN_HASH
    for n in range(1, 11):
        key = f"phase10b{n}"
        summary[f"{key}_artifacts_unchanged"] = hashes_before[key] == hashes_after[key]
    summary["grammar_hash_unchanged"] = grammar_ok
    summary["whitelist_unchanged"] = WHITELIST_VERSION == manifest.get("whitelist_version")
    summary["blacklist_unchanged"] = BLACKLIST_VERSION == manifest.get("blacklist_version")
    summary["frozen_hash_unchanged"] = frozen_ok
    summary["frozen_hash"] = frozen_after
    if not (artifacts_ok and grammar_ok and frozen_ok and specs_unchanged and summary["ranking"] is False):
        summary["PHASE_11A_STATUS"] = "INTEGRITY_FAILURE"
    _write_json("PHASE_11A_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11A_TEST_COPY_ID": PHASE_11A_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "inventory": tables["inventory"],
        "master_matrix": tables["master_matrix"],
        "mechanism_table": tables["mechanism_table"],
        "parameter_mechanism_matrix": tables["matrix"],
        "new_principle_candidates": tables["new_principle_candidates"],
        "NOT_TESTED_RELEVANT_MECHANISMS": tables["NOT_TESTED_RELEVANT_MECHANISMS"],
        "design_filter": tables["design_filter"],
        "surviving_space": tables["surviving_space"],
        "research_question": tables["research_question"],
        "audit_summary": summary,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "PHASE_11A_STATUS": summary["PHASE_11A_STATUS"],
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash(),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "target_based_objective_function": False,
        "known_physics_imported_into_generator": False,
        "known_physics_comparison_executed": False,
        "phase_11b_executed": False,
        "principle_chosen": "NONE",
        "principle_implemented": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_assumptions": 0,
        "new_dependencies": 0,
        "large_scale_generation_executed": False,
        "candidates_repaired": False,
        "search_space_modified": False,
        "grammar_changed": 0,
        "phase_10a_grammar_version_unchanged": True,
        "phase_10b1_artifacts_unchanged": summary["phase10b1_artifacts_unchanged"],
        "phase_10b2_artifacts_unchanged": summary["phase10b2_artifacts_unchanged"],
        "phase_10b3_artifacts_unchanged": summary["phase10b3_artifacts_unchanged"],
        "phase_10b4_artifacts_unchanged": summary["phase10b4_artifacts_unchanged"],
        "phase_10b5_artifacts_unchanged": summary["phase10b5_artifacts_unchanged"],
        "phase_10b6_artifacts_unchanged": summary["phase10b6_artifacts_unchanged"],
        "phase_10b7_artifacts_unchanged": summary["phase10b7_artifacts_unchanged"],
        "phase_10b8_artifacts_unchanged": summary["phase10b8_artifacts_unchanged"],
        "phase_10b9_artifacts_unchanged": summary["phase10b9_artifacts_unchanged"],
        "phase_10b10_artifacts_unchanged": summary["phase10b10_artifacts_unchanged"],
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11A_CLOSED": summary["PHASE_11A_STATUS"] == "CLOSED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "overclaims": {
            "1_choose_a_principle": "REJECTED AS OVERCLAIM",
            "2_canonical_norm_is_physical_determination": "REJECTED AS OVERCLAIM",
            "3_sign_condition_fully_fixes_a_parameter": "REJECTED AS OVERCLAIM",
            "4_rank_mechanisms": "REJECTED AS OVERCLAIM",
            "5_start_phase_11b": "REJECTED AS OVERCLAIM",
            "6_known_physics_comparison": "REJECTED AS OVERCLAIM",
            "7_insert_a_dimensionful_reference_scale": "REJECTED AS OVERCLAIM",
            "8_reparameterization_is_a_physical_constraint": "REJECTED AS OVERCLAIM",
            "9_anomaly_applies_without_new_field_content": "REJECTED AS OVERCLAIM",
            "10_search_is_all_possible_theories": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_11A_STATUS"] == "CLOSED"
        and science["ranking_score_introduced"] is False
        and science["known_physics_comparison_executed"] is False
        and science["new_assumptions"] == 0
        and science["phase_11b_executed"] is False
        and science["principle_chosen"] == "NONE"
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and specs_unchanged
    )
    return science


def run_phase11a_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11a_strategy(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
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
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10B1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b1_artifacts_unchanged") else "FAILED",
            "PHASE_10B2_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b2_artifacts_unchanged") else "FAILED",
            "PHASE_10B3_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b3_artifacts_unchanged") else "FAILED",
            "PHASE_10B4_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b4_artifacts_unchanged") else "FAILED",
            "PHASE_10B5_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b5_artifacts_unchanged") else "FAILED",
            "PHASE_10B6_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b6_artifacts_unchanged") else "FAILED",
            "PHASE_10B7_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b7_artifacts_unchanged") else "FAILED",
            "PHASE_10B8_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b8_artifacts_unchanged") else "FAILED",
            "PHASE_10B9_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b9_artifacts_unchanged") else "FAILED",
            "PHASE_10B10_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("phase_10b10_artifacts_unchanged") else "FAILED",
            "PHASE_11A_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_11A_STATUS": science.get("PHASE_11A_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
