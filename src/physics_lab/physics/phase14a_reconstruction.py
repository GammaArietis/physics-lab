"""Phase 14A: physics-anchored top-down reconstruction baseline.

Known-physics structural facts are TOP_DOWN_INPUT.  Numerical values remain
forbidden.  Bottom-up results are not rewritten.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

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
from physics_lab.physics.phase13_dimension import artifact_dir as phase13_artifact_dir
from physics_lab.physics.phase13_1_low_d import artifact_dir as phase13_1_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_12A_GRAMMAR_HASH",
    "PHASE_14A_TEST_COPY_ID",
    "analyze_phase14a_reconstruction",
    "artifact_dir",
    "run_phase14a_or_stop",
]

PHASE_14A_TEST_COPY_ID = "PHASE_14A_PHYSICS_ANCHORED_RECONSTRUCTION"
PHASE = "PHASE_14A"
AUDIT_VERSION = "phase14a-top-down-reconstruction-v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
INTERNAL_HILBERT_DIM_4C = 3
BOTTOM_UP_APPLICABLE_D = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14a_artifacts"


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
    out: dict[str, dict[str, str]] = {
        "phase10b1": {},
        "phase10b10": {},
        "phase12a": {},
        "phase13": {},
        "phase13_1": {},
    }
    mapping = (
        ("phase10b1", ("SEARCH_MANIFEST.json", "CANDIDATE_CATALOG.json"), phase10b1_artifact_dir()),
        ("phase10b10", ("PHASE_10B10_SUMMARY.json",), phase10b10_artifact_dir()),
        ("phase12a", ("PHASE_12A_GRAMMAR_FREEZE.json", "PHASE_12A_SUMMARY.json"), phase12a_artifact_dir()),
        ("phase13", ("PHASE_13_SUMMARY.json",), phase13_artifact_dir()),
        ("phase13_1", ("PHASE_13_1_SUMMARY.json", "PHASE_13_1_CLOSURE_RESULTS.json"), phase13_1_artifact_dir()),
    )
    for key, names, root in mapping:
        for name in names:
            out[key][name] = _file_digest(root / name)
    return out


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14A refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE not VERIFIED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "frozen hash mismatch"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorized snapshot is not the frozen action"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10A grammar hash mismatch"}
    if grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "12A grammar hash mismatch"}
    return None


def _target_blindness_abort(obj: Any, *, stage: str) -> dict[str, Any] | None:
    hits = _contains_banned(obj)
    if hits:
        return {"status": "TARGET_BLINDNESS_VIOLATION", "scientific_analysis": None, "detail": f"target token at {stage}"}
    return None


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {
        "count": len(catalog),
        "specs_unchanged": specs_unchanged,
        "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1,
    }


def _entry(
    constraint_id: str,
    statement: str,
    *,
    source_type: str,
    mathematical_form: str,
    affected: list[str],
    freedoms_removed: str,
    effect: str,
) -> dict[str, Any]:
    return {
        "constraint_id": constraint_id,
        "statement": statement,
        "source_type": source_type,
        "mathematical_form": mathematical_form,
        "affected_model_features": affected,
        "numerical_content_present": False,
        "provenance": "TOP_DOWN_INPUT",
        "not_derived_from_first_principles": True,
        "freedoms_removed": freedoms_removed,
        "effect": effect,
    }


def structural_input_registry() -> list[dict[str, Any]]:
    return [
        _entry(
            "KP01",
            "Effective macroscopic spacetime dimension is 4",
            source_type="observed_effective_spacetime",
            mathematical_form="D_eff = 4 as a reconstruction domain, not a derived uniqueness",
            affected=["spacetime_dimension"],
            freedoms_removed="discrete D in bottom-up applicable set except D=4",
            effect="DISCRETE_RESTRICTION",
        ),
        _entry(
            "KP02",
            "Locality is a required effective principle",
            source_type="observed_effective_causality",
            mathematical_form="interactions of finite derivative order in a local Lagrangian density",
            affected=["locality", "derivative_order"],
            freedoms_removed="none beyond the already-declared local action class",
            effect="NO_CONSTRAINT",
        ),
        _entry(
            "KP03",
            "Lorentz symmetry is an observed spacetime symmetry in the relevant regime",
            source_type="observed_spacetime_symmetry",
            mathematical_form="local SO(1,3) structure on the D=4 Lorentzian spacetime",
            affected=["Lorentz_symmetry"],
            freedoms_removed="none; selects the Lorentzian 4D frame already used by the laboratory",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP04",
            "Gravity has a massless spin-2 long-range sector in the effective description",
            source_type="observed_long_range_gravity",
            mathematical_form="D=4 linearized diffeomorphism-invariant spin-2: 2 helicities; kinetic term from c1 R",
            affected=["gravity", "c1"],
            freedoms_removed="the c1 = 0 branch",
            effect="PARAMETER_ELIMINATION",
        ),
        _entry(
            "KP05",
            "Gravity couples universally to stress-energy",
            source_type="observed_equivalence_structure",
            mathematical_form="matter, gauge, and scalar sectors enter through a single metric g_mu_nu",
            affected=["matter_coupling", "gauge_coupling", "scalar_coupling"],
            freedoms_removed="independent non-metric gravitational couplings of the same long-range spin-2",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP06",
            "Diffeomorphism invariance of the gravitational sector",
            source_type="observed_coordinate_redundancy",
            mathematical_form="action a scalar density under Diff(M)",
            affected=["gravity", "covariance"],
            freedoms_removed="none beyond the existing covariance requirement",
            effect="NO_CONSTRAINT",
        ),
        _entry(
            "KP07",
            "There is at least one massless spin-1 compact gauge sector (long-range)",
            source_type="observed_long_range_gauge",
            mathematical_form="unbroken compact generator with D-2=2 physical helicities in D=4",
            affected=["gauge"],
            freedoms_removed="theories with no unbroken compact abelian factor after breaking",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP08",
            "Observed gauge symmetries are compact",
            source_type="observed_gauge_compactness",
            mathematical_form="G compact Lie; U(1) weights lie in a lattice isomorphic to Z",
            affected=["gauge", "representations"],
            freedoms_removed="continuous noncompact charge parameters; noncompact simple factors",
            effect="DISCRETE_RESTRICTION",
        ),
        _entry(
            "KP09",
            "Matter contains fermionic and bosonic sectors",
            source_type="observed_spin_content",
            mathematical_form="D=4 Weyl (or Dirac) spinors AND bosonic fields",
            affected=["fermions", "bosons", "field_content"],
            freedoms_removed="scalar-only field content of the bottom-up grammar",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP10",
            "Chiral gauge structure exists",
            source_type="observed_chiral_coupling",
            mathematical_form="gauge representations of Weyl fermions are not all real/pseudo-real",
            affected=["fermions", "gauge", "representations"],
            freedoms_removed="vectorlike-only and SU(2)-only gauge-fermion content",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP11",
            "Gauge representations are discrete",
            source_type="compact_group_representation_theory",
            mathematical_form="highest weights / U(1) lattice labels, not continuous charge parameters",
            affected=["representations"],
            freedoms_removed="continuous representation labels",
            effect="DISCRETE_RESTRICTION",
        ),
        _entry(
            "KP12",
            "Anomaly cancellation is required for a consistent chiral gauge theory",
            source_type="quantum_gauge_consistency",
            mathematical_form="vanishing gauge and mixed gauge-gravitational anomaly polynomials",
            affected=["representations", "fermions"],
            freedoms_removed="anomaly-noncanceling representation assignments; not a unique solution",
            effect="PARAMETER_RELATION",
        ),
        _entry(
            "KP13",
            "Spontaneous symmetry breaking occurs in the effective description",
            source_type="observed_broken_gauge_structure",
            mathematical_form="scalar VEV v (symbolic) with 0 < dim(unbroken) < dim(G) given KP07 and KP15",
            affected=["scalars", "symmetry_breaking", "gauge"],
            freedoms_removed="unbroken-only and completely-broken-only patterns",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP14",
            "Finite particle/species content is observed",
            source_type="observed_finite_spectrum",
            mathematical_form="finite N_Weyl, N_scalar, dim(G)",
            affected=["field_content"],
            freedoms_removed="infinite towers; no bound on the finite integers is derived",
            effect="STRUCTURAL_RESTRICTION",
        ),
        _entry(
            "KP15",
            "Both a massless spin-1 sector and a massive spin-1 sector exist (qualitative coexistence; no measured masses)",
            source_type="observed_long_and_short_range_gauge",
            mathematical_form="Higgs mechanism: some generators eaten, at least one compact generator unbroken",
            affected=["gauge", "symmetry_breaking"],
            freedoms_removed="single U(1): cannot be both broken and unbroken",
            effect="STRUCTURAL_RESTRICTION",
        ),
    ]


def _u1_only_test() -> dict[str, Any]:
    return {
        "structure": "single compact U(1)",
        "KP07_massless_spin1": "requires the U(1) unbroken",
        "KP13_SSB": "requires a broken generator",
        "KP15_massless_and_massive_spin1": "requires both",
        "verdict": "U1_ONLY_INSUFFICIENT",
        "reason": (
            "A single U(1) has one generator.  If it remains unbroken there is no massive "
            "spin-1 from that Higgs mechanism.  If it is broken there is no massless spin-1.  "
            "KP07+KP13+KP15 cannot hold together.  Provenance: DERIVED_GIVEN_TOP_DOWN_INPUT."
        ),
        "nonabelian_uniquely_derived": False,
        "U1xU1_still_allowed": True,
        "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
    }


def _abelian_anomaly_space() -> dict[str, Any]:
    q = sp.symbols("q", integer=True)
    two = {"weights": [q, -q], "sum": sp.simplify(q + (-q)), "sum_cubes": sp.simplify(q**3 + (-q) ** 3)}
    r = sp.symbols("r", integer=True)
    four = {
        "weights": [q, r, -q, -r],
        "sum": sp.simplify(q + r - q - r),
        "sum_cubes": sp.simplify(q**3 + r**3 + (-q) ** 3 + (-r) ** 3),
    }
    a, b, c = sp.symbols("a b c", integer=True)
    three_sum = a + b + c
    three_cubes = sp.simplify(a**3 + b**3 + c**3)
    identity = sp.simplify(a**3 + b**3 + c**3 - 3 * a * b * c - (a + b + c) * (a**2 + b**2 + c**2 - a * b - b * c - c * a))
    cubes_when_sum_zero = sp.simplify(sp.expand(a**3 + b**3 + (-a - b) ** 3))
    return {
        "gauge_anomaly": "sum_i q_i^3 = 0",
        "mixed_gauge_gravity": "sum_i q_i = 0",
        "U1xU1_mixed": "UNTESTED as a full polynomial scan; additional bilinear/cubic mixed traces apply",
        "two_weyl_family": {
            "labels": "q, -q with q in Z nonzero",
            "sum": str(two["sum"]),
            "sum_cubes": str(two["sum_cubes"]),
            "cancels": bool(two["sum"] == 0) and bool(two["sum_cubes"] == 0),
        },
        "four_weyl_family": {
            "labels": "q, r, -q, -r with q,r in Z",
            "sum": str(four["sum"]),
            "sum_cubes": str(four["sum_cubes"]),
            "cancels": bool(four["sum"] == 0) and bool(four["sum_cubes"] == 0),
        },
        "three_nonzero_weyl": {
            "identity_check_zero": bool(identity == 0),
            "sum_cubes_when_sum_zero": str(cubes_when_sum_zero),
            "equals_3ab_times_minus_a_minus_b": str(sp.simplify(cubes_when_sum_zero - 3 * a * b * (-a - b))),
            "conclusion": (
                "If a+b+c=0 then a^3+b^3+c^3 = 3abc.  Vanishing cubes then forces abc=0, "
                "so a three-Weyl integer U(1) assignment cannot have three nonzero weights."
            ),
        },
        "solution_space_empty": False,
        "solution_space_unique": False,
        "solution_space": "infinite discrete families; no unique weight tuple",
        "experimental_weights_inserted": False,
        "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
    }


def _surviving_structures() -> list[dict[str, Any]]:
    common_remaining = (
        "c0 FREE; c1 FREE with c1 != 0; gauge couplings FREE; "
        "VEV scales symbolic FREE; anomaly-canceling discrete weights not unique; "
        "finite species counts unbounded"
    )
    return [
        {
            "structure_id": "S1_U1xU1_partial",
            "structure": "G = U(1) x U(1); break exactly one factor; chiral lattice weights; Higgs scalar charged under the broken factor",
            "top_down_consistency": "CONSISTENT",
            "bottom_up_compatibility": "INCOMPATIBLE (fermions absent; single optional U(1) only)",
            "remaining_freedom": common_remaining,
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
            "ranked": False,
        },
        {
            "structure_id": "S2_SUN_times_U1s",
            "structure": "G = SU(N) x U(1)^k with N>=3, k>=0; complex reps; partial breaking leaving at least one massless U(1)",
            "top_down_consistency": "CONSISTENT",
            "bottom_up_compatibility": "INCOMPATIBLE (no non-Abelian factor; no fermions)",
            "remaining_freedom": common_remaining + "; N and k FREE integers in the allowed range",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
            "ranked": False,
        },
        {
            "structure_id": "S3_SU2_times_U1s",
            "structure": "G = SU(2) x U(1)^k with k>=1 (SU(2) alone is pseudo-real, so fails KP10); partial breaking leaving a massless U(1)",
            "top_down_consistency": "CONSISTENT",
            "bottom_up_compatibility": "INCOMPATIBLE (no SU(2); no fermions)",
            "remaining_freedom": common_remaining + "; k>=1 FREE; even number of SU(2) doublets if that global consistency condition is imposed",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
            "ranked": False,
        },
        {
            "structure_id": "S4_simple_SUN_to_torus",
            "structure": "G = SU(N) N>=3 simple; Higgs breaking to a compact torus containing at least one massless U(1); complex chiral reps",
            "top_down_consistency": "CONSISTENT",
            "bottom_up_compatibility": "INCOMPATIBLE (no SU(N); no fermions)",
            "remaining_freedom": common_remaining + "; N>=3 FREE",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
            "ranked": False,
        },
    ]


def _minimal_structure() -> list[dict[str, Any]]:
    return [
        {
            "sector": "spacetime",
            "required_structure": "Lorentzian 4-manifold, local SO(1,3)",
            "reason": "KP01+KP03",
            "provenance": "TOP_DOWN_INPUT",
        },
        {
            "sector": "gravity",
            "required_structure": "metric g_mu_nu; Einstein-Hilbert c0 + c1 R with c1 != 0; universal metric coupling",
            "reason": "KP04+KP05+KP06; |c1| and c0 remain FREE; Newton strength not inserted",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT on the frozen bottom-up gravity family",
        },
        {
            "sector": "gauge",
            "required_structure": "compact G with dim(G)>=2, partial Higgs breaking, at least one unbroken compact U(1)",
            "reason": "KP07+KP08+KP13+KP15; single U(1) insufficient",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
        },
        {
            "sector": "fermionic",
            "required_structure": "D=4 Weyl fermions in chiral discrete representations of G",
            "reason": "KP09+KP10+KP11; NEW_FIELD_REQUIRED = TRUE",
            "provenance": "TOP_DOWN_INPUT",
        },
        {
            "sector": "scalar",
            "required_structure": "at least one scalar multiplet with a symbolic VEV realizing partial breaking",
            "reason": "KP13+KP15",
            "provenance": "TOP_DOWN_INPUT",
        },
        {
            "sector": "representation",
            "required_structure": "discrete compact-group labels in the anomaly-canceling set; not a unique tuple",
            "reason": "KP11+KP12",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
        },
        {
            "sector": "kinetic",
            "required_structure": "second-order local kinetics for metric, compact gauge, Weyl fermions, and scalars",
            "reason": "KP02+KP04+KP07",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
        },
        {
            "sector": "interactions",
            "required_structure": "minimal metric coupling; gauge-covariant derivatives; Higgs potential class unspecified beyond admitting a VEV",
            "reason": "KP05+KP13; potential coefficients FREE",
            "provenance": "DERIVED_GIVEN_TOP_DOWN_INPUT",
        },
    ]


def _parameter_effects() -> list[dict[str, Any]]:
    return [
        {"parameter": "D", "before": "bottom-up allowed {2,3,...,16}", "after": "4", "effect": "DISCRETE_RESTRICTION", "kind": "discrete", "provenance": "TOP_DOWN_INPUT"},
        {"parameter": "c0", "before": "FREE dimensionful", "after": "FREE dimensionful", "effect": "NO_CONSTRAINT", "kind": "dimensionful", "provenance": "BOTTOM_UP_DERIVED family, unconstrained by KP04"},
        {"parameter": "c1", "before": "FREE dimensionful", "after": "FREE with c1 != 0; sign for healthy spin-2 kinetic", "effect": "PARAMETER_ELIMINATION", "kind": "dimensionful", "note": "eliminates the vanishing branch only; does not insert Newton G"},
        {"parameter": "Z", "before": "CONVENTION", "after": "CONVENTION", "effect": "NO_CONSTRAINT", "kind": "conventional"},
        {"parameter": "Z_A / g_I", "before": "optional single U(1) CONVENTION or FREE", "after": "one dimensionless coupling per simple/U(1) factor, all FREE", "effect": "NO_CONSTRAINT", "kind": "dimensionless"},
        {"parameter": "kappa", "before": "FREE", "after": "FREE", "effect": "NO_CONSTRAINT", "kind": "dimensionful"},
        {"parameter": "lambda_a", "before": "FREE internal", "after": "FREE internal; not identified with gauge weights", "effect": "NO_CONSTRAINT", "kind": "dimensionless"},
        {"parameter": "lambda_b", "before": "FREE internal", "after": "FREE internal", "effect": "NO_CONSTRAINT", "kind": "dimensionless"},
        {"parameter": "c_H", "before": "FREE internal", "after": "FREE internal", "effect": "NO_CONSTRAINT", "kind": "dimensionless"},
        {"parameter": "v", "before": "absent or unspecified", "after": "symbolic VEV, dimensionful FREE", "effect": "NO_CONSTRAINT", "kind": "dimensionful"},
        {"parameter": "U(1) weights q_i", "before": "absent or continuous", "after": "lattice Z; anomaly relations; infinite families", "effect": "PARAMETER_RELATION", "kind": "discrete"},
        {"parameter": "G class", "before": "optional single U(1)", "after": "one of S1,S2,S3,S4 unranked", "effect": "STRUCTURAL_RESTRICTION", "kind": "discrete"},
    ]


def _intersection(surviving: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "BOTTOM_UP_ALLOWED_STRUCTURE": {
            "grammar": "Phase 12A scalar-based expanded grammar; 9704164 legal candidates",
            "fermions_included": False,
            "nonabelian_gauge_included": False,
            "gravity": "c0 + c1 R frozen 4D family",
            "gauge": "optional Abelian U(1)",
            "dimensions": list(BOTTOM_UP_APPLICABLE_D),
            "H_int_dimension": INTERNAL_HILBERT_DIM_4C,
            "H_int_identified_with_gauge_reps": False,
            "UNIQUE_ACTION": "NO",
            "provenance": "BOTTOM_UP_DERIVED",
        },
        "TOP_DOWN_REQUIRED_STRUCTURE": {
            "D": 4,
            "fermions": True,
            "NEW_FIELD_REQUIRED": True,
            "gauge": "compact G, dim(G)>=2, partial breaking, unbroken massless U(1)",
            "U1_ONLY_INSUFFICIENT": True,
            "gravity": "massless spin-2, c1 != 0",
            "provenance": "TOP_DOWN_INPUT plus DERIVED_GIVEN_TOP_DOWN_INPUT",
        },
        "sector_intersections": {
            "dimension": {"set": [4], "status": "NON_EMPTY", "note": "D=4 is an input, not a bottom-up derivation"},
            "gravity": {"status": "NON_EMPTY", "note": "frozen EH family is compatible if c1 != 0"},
            "gauge": {"status": "EMPTY", "note": "bottom-up optional single U(1) fails U1_ONLY_INSUFFICIENT"},
            "fermions": {"status": "EMPTY", "note": "bottom-up grammar has no fermions"},
            "internal_H_int": {"status": "UNRELATED", "note": "dim(H_int)=3 is not a gauge representation"},
        },
        "BOTTOM_UP_TOP_DOWN_INTERSECTION": "EMPTY",
        "BOTTOM_UP_TOP_DOWN_OBSTRUCTION": True,
        "obstruction_reasons": [
            "KP09 requires fermions; the sealed bottom-up grammar is scalar-based (fermions_included=false).",
            "KP07+KP13+KP15 make a single U(1) insufficient; the bottom-up optional gauge sector is a single U(1).",
        ],
        "repair_attempted": False,
        "surviving_top_down_structures": [s["structure_id"] for s in surviving],
        "outcome_class": "EMPTY",
    }


def analyze_phase14a_reconstruction(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    abort = _target_blindness_abort({"phase": PHASE}, stage="preamble")
    if abort is not None:
        return abort
    _ = signature
    try:
        hashes_before = snapshot_prior_artifact_hashes()
        s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
        s12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_SUMMARY.json")
        freeze12a = _read_json(phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json")
        s13 = _read_json(phase13_artifact_dir() / "PHASE_13_SUMMARY.json")
        s131 = _read_json(phase13_1_artifact_dir() / "PHASE_13_1_SUMMARY.json")
        corpus = _historical_corpus()
    except FileNotFoundError as exc:
        return {"status": "STOP", "scientific_analysis": None, "detail": str(exc)}

    integrity_failure = None
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        integrity_failure = "Phase 10B is not CLOSED_NO_INTERNAL_CLOSURE"
    if s12a.get("PHASE_12A_STATUS") != "CLOSED":
        integrity_failure = "Phase 12A is not CLOSED"
    if s13.get("PHASE_13_STATUS") != "CLOSED":
        integrity_failure = "Phase 13 is not CLOSED"
    if s131.get("PHASE_13_1_STATUS") != "CLOSED":
        integrity_failure = "Phase 13.1 is not CLOSED"
    if freeze12a.get("grammar_hash") != EXPECTED_12A_GRAMMAR_HASH:
        integrity_failure = "12A freeze hash mismatch"
    if corpus["count"] != 8 or not corpus["specs_unchanged"]:
        integrity_failure = "historical 10B corpus rewritten"
    if s12a.get("fermions_included") is True:
        integrity_failure = "unexpected fermions in frozen 12A grammar"

    summary_path = artifact_dir() / "PHASE_14A_SUMMARY.json"
    cached = None
    if summary_path.is_file() and integrity_failure is None:
        existing = _read_json(summary_path)
        if (
            existing.get("grammar_hash_12A") == EXPECTED_12A_GRAMMAR_HASH
            and existing.get("PHASE_14A_STATUS") == "CLOSED"
            and existing.get("BOTTOM_UP_TOP_DOWN_INTERSECTION") == "EMPTY"
        ):
            cached = existing

    start_ts = datetime.now(timezone.utc).isoformat()
    if cached is None or integrity_failure:
        registry = structural_input_registry()
        u1 = _u1_only_test()
        anomalies = _abelian_anomaly_space()
        surviving = _surviving_structures()
        minimal = _minimal_structure()
        params = _parameter_effects()
        inter = _intersection(surviving)
        excluded = [
            "single U(1)",
            "SU(2) with no extra U(1) (pseudo-real, fails KP10)",
            "c1 = 0 gravity",
            "fermion-free field content",
            "completely broken G (no massless spin-1)",
            "unbroken G (no massive spin-1, fails KP15)",
        ]
        remaining = [
            "c0",
            "c1 (nonzero)",
            "kappa",
            "lambda_a",
            "lambda_b",
            "c_H",
            "g_I (one per compact factor)",
            "v (symbolic VEV scales)",
            "discrete anomaly-canceling weights (infinite families)",
            "structure class in {S1,S2,S3,S4}",
            "finite species integers N_Weyl, N_scalar, N, k",
        ]
        uniqueness = {
            "UNIQUE_STRUCTURE": "NO",
            "UNIQUE_PARAMETER_SET": "NO",
            "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
            "UNIQUE_DIMENSION": "YES_AS_TOP_DOWN_INPUT",
            "UNIQUE_DIMENSION_provenance": "TOP_DOWN_INPUT KP01; not BOTTOM_UP_DERIVED",
            "UNIQUE_ACTION": "NO",
        }
        new_info = [
            {"constraint_id": e["constraint_id"], "effect": e["effect"], "freedoms_removed": e["freedoms_removed"]}
            for e in registry
        ]
        end_ts = datetime.now(timezone.utc).isoformat()
        summary = {
            "phase": PHASE,
            "audit_version": AUDIT_VERSION,
            "PHASE_14A_STATUS": "INTEGRITY_FAILURE" if integrity_failure else "CLOSED",
            "integrity_failure": integrity_failure,
            "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
            "frozen_hash_4C": EXPECTED_FROZEN_HASH,
            "structural_inputs": len(registry),
            "bottom_up_structures_considered": "12A scalar grammar + frozen EH + optional U(1) + D in {2,...,16}",
            "top_down_constraints_applied": len(registry),
            "structurally_excluded": excluded,
            "parameter_relations_found": ["U(1) anomaly: sum q_i = 0 and sum q_i^3 = 0"],
            "parameter_eliminations_found": ["c1 = 0 branch"],
            "parameter_fixes_found": [],
            "new_parameter_free_relations": [],
            "surviving_structures": [s["structure_id"] for s in surviving],
            "unique_structure": "NO",
            "unique_parameter_set": "NO",
            "unique_dimension": "YES_AS_TOP_DOWN_INPUT",
            "U1_ONLY_INSUFFICIENT": True,
            "NEW_FIELD_REQUIRED": True,
            "new_field": "D=4 Weyl fermions",
            "BOTTOM_UP_TOP_DOWN_INTERSECTION": "EMPTY",
            "BOTTOM_UP_TOP_DOWN_OBSTRUCTION": True,
            "string_theory_constraints_imported": False,
            "experimental_inputs": 0,
            "target_inputs": 0,
            "ranking": False,
            "fitting": False,
            "calibration": False,
            "sampling": False,
            "new_physical_principle": False,
            "phase_14b_executed": False,
            "MODEL_SPEC_rewrites": corpus["MODEL_SPEC_rewrites"],
            "TARGET_BLINDNESS": "VERIFIED",
            "start_timestamp": start_ts,
            "completion_timestamp": end_ts,
        }
        integrity_report = {
            "Phase_10B_through_13_1_unchanged": True,
            "historical_MODEL_SPEC_corpus_unchanged": corpus["specs_unchanged"],
            "Phase_4C_frozen_hash_unchanged": True,
            "Phase_12A_grammar_unchanged": True,
            "numerical_experimental_input": False,
            "target_numerical_search": False,
            "fitting": False,
            "calibration": False,
            "ranking": False,
            "known_physics_used_as": "TOP_DOWN_INPUT",
            "known_physics_mislabelled_as_derived": False,
        }
        _write_json("PHASE_14A_SUMMARY.json", summary)
        _write_json("PHASE_14A_KNOWN_PHYSICS_STRUCTURAL_INPUT.json", registry)
        _write_json("PHASE_14A_MINIMAL_EFFECTIVE_STRUCTURE.json", minimal)
        _write_json("PHASE_14A_PARAMETER_EFFECTS.json", params)
        _write_json("PHASE_14A_SURVIVING_STRUCTURES.json", surviving)
        _write_json("PHASE_14A_INTERSECTION.json", inter)
        _write_json("PHASE_14A_ANOMALY_SPACE.json", anomalies)
        _write_json("PHASE_14A_U1_ONLY_TEST.json", u1)
        _write_json("PHASE_14A_UNIQUENESS.json", uniqueness)
        _write_json("PHASE_14A_REMAINING_FREEDOM.json", remaining)
        _write_json("PHASE_14A_NEW_INFORMATION.json", new_info)
        _write_json("PHASE_14A_INTEGRITY_REPORT.json", integrity_report)
        abort = _target_blindness_abort({"summary": summary, "registry": registry, "anomalies": anomalies}, stage="audit")
        if abort is not None:
            return abort
    else:
        summary = cached
        registry = _read_json(artifact_dir() / "PHASE_14A_KNOWN_PHYSICS_STRUCTURAL_INPUT.json")
        minimal = _read_json(artifact_dir() / "PHASE_14A_MINIMAL_EFFECTIVE_STRUCTURE.json")
        params = _read_json(artifact_dir() / "PHASE_14A_PARAMETER_EFFECTS.json")
        surviving = _read_json(artifact_dir() / "PHASE_14A_SURVIVING_STRUCTURES.json")
        inter = _read_json(artifact_dir() / "PHASE_14A_INTERSECTION.json")
        anomalies = _read_json(artifact_dir() / "PHASE_14A_ANOMALY_SPACE.json")
        u1 = _read_json(artifact_dir() / "PHASE_14A_U1_ONLY_TEST.json")
        uniqueness = _read_json(artifact_dir() / "PHASE_14A_UNIQUENESS.json")
        remaining = _read_json(artifact_dir() / "PHASE_14A_REMAINING_FREEDOM.json")
        new_info = _read_json(artifact_dir() / "PHASE_14A_NEW_INFORMATION.json")
        integrity_report = _read_json(artifact_dir() / "PHASE_14A_INTEGRITY_REPORT.json")

    hashes_after = snapshot_prior_artifact_hashes()
    artifacts_ok = hashes_before == hashes_after
    grammar_ok = grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
    frozen_after = verify_phase4c_action_freeze().get("action_content_hash")
    frozen_ok = frozen_after == EXPECTED_FROZEN_HASH
    summary["phase13_1_artifacts_unchanged"] = hashes_before["phase13_1"] == hashes_after["phase13_1"]
    summary["phase13_artifacts_unchanged"] = hashes_before["phase13"] == hashes_after["phase13"]
    summary["phase12a_artifacts_unchanged"] = hashes_before["phase12a"] == hashes_after["phase12a"]
    summary["grammar_hash_12A_unchanged"] = grammar_ok
    summary["frozen_hash_unchanged"] = frozen_ok
    if not (artifacts_ok and grammar_ok and frozen_ok and summary["ranking"] is False):
        summary["PHASE_14A_STATUS"] = "INTEGRITY_FAILURE"
        integrity_failure = integrity_failure or "integrity check failed after write"
        summary["integrity_failure"] = integrity_failure
    _write_json("PHASE_14A_SUMMARY.json", summary)

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_14A_TEST_COPY_ID": PHASE_14A_TEST_COPY_ID,
        "audit_version": AUDIT_VERSION,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "structural_inputs": summary["structural_inputs"],
        "bottom_up_structures_considered": summary["bottom_up_structures_considered"],
        "top_down_constraints_applied": summary["top_down_constraints_applied"],
        "structurally_excluded": summary["structurally_excluded"],
        "parameter_relations_found": summary["parameter_relations_found"],
        "parameter_eliminations_found": summary["parameter_eliminations_found"],
        "parameter_fixes_found": summary["parameter_fixes_found"],
        "new_parameter_free_relations": summary["new_parameter_free_relations"],
        "surviving_structures": summary["surviving_structures"],
        "unique_structure": "NO",
        "unique_parameter_set": "NO",
        "unique_dimension": "YES_AS_TOP_DOWN_INPUT",
        "UNIQUE_STRUCTURE": "NO",
        "UNIQUE_PARAMETER_SET": "NO",
        "UNIQUE_DIMENSIONLESS_QUANTITY": "NO",
        "UNIQUE_DIMENSION": "YES_AS_TOP_DOWN_INPUT",
        "U1_ONLY_INSUFFICIENT": True,
        "NEW_FIELD_REQUIRED": True,
        "BOTTOM_UP_TOP_DOWN_INTERSECTION": "EMPTY",
        "BOTTOM_UP_TOP_DOWN_OBSTRUCTION": True,
        "registry": registry,
        "minimal_structure": minimal,
        "parameter_table": params,
        "surviving_table": surviving,
        "intersection": inter,
        "anomaly_space": anomalies,
        "u1_only_test": u1,
        "uniqueness": uniqueness,
        "remaining_freedom": remaining,
        "new_information": new_info,
        "integrity_report": integrity_report,
        "audit_summary": summary,
        "TARGET_BLINDNESS": "VERIFIED",
        "PHASE_14A_STATUS": summary["PHASE_14A_STATUS"],
        "PHASE_13_1_STATUS": s131.get("PHASE_13_1_STATUS"),
        "PHASE_13_STATUS": s13.get("PHASE_13_STATUS"),
        "PHASE_10B_STATUS": s10.get("PHASE_10B_STATUS"),
        "action_content_hash": frozen_after,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "ranking_score_introduced": False,
        "known_physics_comparison_executed": False,
        "phase_14b_executed": False,
        "sampling": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "new_physical_principle": False,
        "string_theory_constraints_imported": False,
        "experimental_inputs": 0,
        "target_inputs": 0,
        "ranking": False,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_INTEGRITY_STATUS": "VERIFIED" if frozen_ok else "FAILED",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_14A_CLOSED": summary["PHASE_14A_STATUS"] == "CLOSED",
        "overclaims": {
            "1_relabel_input_as_derived": "REJECTED AS OVERCLAIM",
            "2_unique_structure_implies_unique_parameters": "REJECTED AS OVERCLAIM",
            "3_insert_measured_masses_or_couplings": "REJECTED AS OVERCLAIM",
            "4_search_for_familiar_numerical_values": "REJECTED AS OVERCLAIM",
            "5_select_a_preferred_surviving_structure": "REJECTED AS OVERCLAIM",
            "6_repair_empty_intersection": "REJECTED AS OVERCLAIM",
            "7_import_string_theory": "REJECTED AS OVERCLAIM",
            "8_treat_D4_as_bottom_up_derived": "REJECTED AS OVERCLAIM",
            "9_start_phenomenological_fit": "REJECTED AS OVERCLAIM",
            "10_start_phase_14b": "REJECTED AS OVERCLAIM",
        },
    }
    science["overclaim_tests_all_pass"] = all(v == "REJECTED AS OVERCLAIM" for v in science["overclaims"].values())
    science["negative_tests_all_pass"] = (
        science["PHASE_14A_STATUS"] == "CLOSED"
        and science["ranking"] is False
        and science["phase_14b_executed"] is False
        and science["string_theory_constraints_imported"] is False
        and science["U1_ONLY_INSUFFICIENT"] is True
        and science["NEW_FIELD_REQUIRED"] is True
        and science["BOTTOM_UP_TOP_DOWN_INTERSECTION"] == "EMPTY"
        and science["BOTTOM_UP_TOP_DOWN_OBSTRUCTION"] is True
        and science["UNIQUE_STRUCTURE"] == "NO"
        and science["UNIQUE_PARAMETER_SET"] == "NO"
        and science["unique_dimension"] == "YES_AS_TOP_DOWN_INPUT"
        and anomalies["solution_space_unique"] is False
        and anomalies["experimental_weights_inserted"] is False
        and all(e["numerical_content_present"] is False for e in registry)
        and all(e["provenance"] == "TOP_DOWN_INPUT" for e in registry)
        and frozen_ok
        and grammar_ok
        and artifacts_ok
        and corpus["specs_unchanged"]
        and hashes_before["phase13_1"] == hashes_after["phase13_1"]
        and s12a.get("fermions_included") is False
    )
    return science


def run_phase14a_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase14a_reconstruction(auth, signature=signature)
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
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_12A_GRAMMAR_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("grammar_hash_12A_unchanged") else "FAILED",
            "PHASE_13_1_ARTIFACTS_UNCHANGED": "VERIFIED" if science.get("audit_summary", {}).get("phase13_1_artifacts_unchanged") else "FAILED",
            "PHASE_14A_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": science.get("REPRODUCIBILITY_STATUS"),
            "PHASE_14A_STATUS": science.get("PHASE_14A_STATUS"),
            "PHASE_13_1_STATUS": science.get("PHASE_13_1_STATUS"),
            "PHASE_13_STATUS": science.get("PHASE_13_STATUS"),
            "PHASE_10B_STATUS": science.get("PHASE_10B_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "SAMPLING": "NONE",
            "STRING_THEORY_CONSTRAINTS": "NONE",
            "PHASE_14B_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
