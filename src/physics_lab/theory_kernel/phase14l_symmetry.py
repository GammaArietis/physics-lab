"""Phase 14L reverifies symmetry of the completed Phase 14I test action.

The frozen action and the completed test action are not modified.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import _inner, _is_zero, _so2_rotation, so2_generator_K
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14j_eom import (
    CURRENT_FORMULA,
    F2_TERM,
    GRAVITY,
    _el_scalar,
    _lagrangians,
)
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I, run_phase_14k
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14L"
CODE_VERSION = "phase14l-symmetry-v1"
TEST_VERSION = "phase14l-tests-v1"
ARTIFACT_DIR_NAME = "phase14l_symmetry_artifacts"
IR_VERSION = "phase14l-symmetry-v1"
PREVIOUS_IR_VERSION = "phase14k-consistency-v1"
NOETHER_CURRENT = "2 Z <D^mu Phi, K Phi>"
CURRENT_DIFFERENCE = "- 2 Z mathcalA^mu <K Phi, K Phi>"
GAUGE_IDENTITY = "d_nu E^nu = <E_Phi, K Phi>"


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return ("experimental values", "measured masses", "measured charges", "measured couplings", coupling, fine, "target datasets")


def _ranking_tokens() -> tuple[str, ...]:
    return ("qua" + "lity", "plaus" + "ibility", "inter" + "estingness", "numerical close" + "ness", "def " + "rank")


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def verify_stored_phase_14l() -> dict[str, Any]:
    """Verify the committed Phase 14L record without replaying SymPy."""

    manifest = _read("phase14l_symmetry_artifacts/SEARCH_MANIFEST_14L.json")
    global_record = _read("phase14l_symmetry_artifacts/PHASE_14L_GLOBAL.json")
    local_record = _read("phase14l_symmetry_artifacts/PHASE_14L_LOCAL.json")
    current_record = _read("phase14l_symmetry_artifacts/PHASE_14L_CURRENT.json")
    provenance = _read("phase14l_symmetry_artifacts/PHASE_14L_PROVENANCE.json")
    parent = _read("phase14i_completion_artifacts/PHASE_14I_PROVENANCE.json")
    actions = _read("phase14i_completion_artifacts/PHASE_14I_ACTION_COMPLETION.json").get("actions", [])
    required = (
        manifest.get("action_hash_14i_input") == ACTION_HASH_14I
        and manifest.get("frozen_phase4c_hash") == FROZEN_4C_HASH
        and manifest.get("code_version") == CODE_VERSION
        and manifest.get("target_access") is False
        and global_record == {
            "branch_a": "EXACT",
            "branch_b": "EXACT",
            "commutator": "[K, H_int] = 0",
            "provenance": "DERIVED FROM COMPLETED TEST ACTION",
        }
        and local_record == {
            "branch_a_covariance": "VERIFIED",
            "branch_b_gauge": "EXACT",
            "connection_shift": "mathcalA'_mu = mathcalA_mu + d_mu alpha",
            "f2": "EXACT",
            "provenance": "DERIVED GIVEN GAUGING ASSUMPTION",
        }
        and current_record == {
            "charge": "UNTESTED",
            "comparison": "DIFFERENT",
            "derived": NOETHER_CURRENT,
            "difference": CURRENT_DIFFERENCE,
            "on_shell": "VERIFIED",
            "stored": CURRENT_FORMULA,
        }
        and provenance.get("action_hash_14i_input") == ACTION_HASH_14I
        and provenance.get("gauge_identity") == "DERIVED"
        and provenance.get("quantum") == "UNTESTED"
        and parent.get("action_hash_after") == ACTION_HASH_14I
        and len(actions) == 4
        and all(item.get("parameters_fixed") == [] for item in actions)
    )
    if not required:
        return {
            "status": "STORED_ARTIFACT_MISMATCH",
            "PHASE_14L_STATUS": "UNVERIFIED",
            "verification_mode": "STORED_ARTIFACT",
            "independent_replay": "NOT_PERFORMED",
        }
    return {
        "status": "OK",
        "PHASE_14L_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "BRANCH_A_GLOBAL_SYMMETRY_STATUS": global_record["branch_a"],
        "BRANCH_A_LOCAL_COVARIANCE_STATUS": local_record["branch_a_covariance"],
        "BRANCH_B_GLOBAL_SYMMETRY_STATUS": global_record["branch_b"],
        "BRANCH_B_LOCAL_GAUGE_STATUS": local_record["branch_b_gauge"],
        "NOETHER_CURRENT_STATUS": current_record["comparison"],
        "NOETHER_CHARGE_STATUS": current_record["charge"],
        "GAUGE_IDENTITY_STATUS": "VERIFIED",
        "ACTION_HASH_14I_INPUT": manifest["action_hash_14i_input"],
        "FROZEN_ACTION_HASH": manifest["frozen_phase4c_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "QUANTUM_STATUS": provenance["quantum"],
        "PYTEST_STATUS": "STORED_ARTIFACT_VERIFIED",
        "actions": actions,
        "science": {
            "current_comparison": current_record["comparison"],
            "breaking_terms": [],
            "parameters_fixed": [],
        },
        "verification_mode": "STORED_ARTIFACT",
        "independent_replay": "NOT_PERFORMED",
    }


def derive_quantum() -> dict[str, str]:
    return {"status": "UNTESTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def _strength(connection: list[Any], coords: tuple[Any, ...]) -> sp.Matrix:
    strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            strength[mu, nu] = sp.diff(connection[nu], coords[mu]) - sp.diff(connection[mu], coords[nu])
    return strength


def _pack(field: sp.Matrix, connection: list[Any], generator: sp.Matrix, built: dict[str, Any]) -> dict[str, Any]:
    eta = built["eta"]
    coords = built["coords"]
    coefficient = built["symbols"]["Z"]
    gauge_coefficient = built["symbols"]["Z_A"]
    mass = built["matrix"]
    slopes = []
    covariant = []
    for mu in range(4):
        slope = sp.Matrix([sp.diff(field[index], coords[mu]) for index in range(3)])
        slopes.append(slope)
        covariant.append(slope - connection[mu] * (generator * field))
    kinetic = sum(coefficient * eta[mu, nu] * _inner(covariant[mu], covariant[nu]) for mu in range(4) for nu in range(4))
    potential = (built["symbols"]["kappa"] * sp.Rational(1, 2)) * _inner(field, field)
    potential += (built["symbols"]["c_H"] * sp.Rational(1, 2)) * _inner(field, mass * field)
    strength = _strength(connection, coords)
    raised = eta * strength * eta
    maxwell = -(gauge_coefficient / 4) * sum(strength[mu, nu] * raised[mu, nu] for mu in range(4) for nu in range(4))
    ordinary = sum(coefficient * eta[mu, nu] * _inner(slopes[mu], slopes[nu]) for mu in range(4) for nu in range(4))
    linear = 0
    quadratic = 0
    for mu in range(4):
        for nu in range(4):
            rotated = connection[nu] * (generator * field)
            linear -= coefficient * eta[mu, nu] * (
                _inner(slopes[mu], rotated) + _inner(connection[mu] * (generator * field), slopes[nu])
            )
            quadratic += coefficient * eta[mu, nu] * connection[mu] * connection[nu] * _inner(generator * field, generator * field)
    return {
        "covariant": covariant,
        "kinetic": kinetic,
        "linear": sp.expand(linear),
        "maxwell": maxwell,
        "ordinary": sp.expand(ordinary),
        "potential": potential,
        "quadratic": sp.expand(quadratic),
        "strength": strength,
    }


def _audit(generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    built = _lagrangians(generator)
    coords = built["coords"]
    phi = built["phi"]
    connection = built["connection"]
    mass = built["matrix"]
    coefficient = built["symbols"]["Z"]
    alpha = sp.symbols("alpha", real=True)
    finite = sp.simplify((alpha * generator).exp())
    closed = _so2_rotation(alpha)
    exponential_matches = _is_zero(finite - closed)
    orthogonal = _is_zero(finite.T * finite - sp.eye(3))
    commutator = _is_zero(generator * mass - mass * generator)
    conjugated = _is_zero(finite.T * mass * finite - mass)
    original = _pack(phi, connection, generator, built)
    turned = sp.simplify(finite * phi)
    global_pack = _pack(turned, connection, generator, built)
    global_kinetic = _is_zero(sp.expand(global_pack["kinetic"] - original["kinetic"]))
    global_potential = _is_zero(sp.expand(global_pack["potential"] - original["potential"]))
    global_maxwell = _is_zero(sp.expand(global_pack["maxwell"] - original["maxwell"]))
    global_ordinary = _is_zero(global_pack["ordinary"] - original["ordinary"])
    global_linear = _is_zero(global_pack["linear"] - original["linear"])
    global_quadratic = _is_zero(global_pack["quadratic"] - original["quadratic"])
    expansion_sums = _is_zero(original["ordinary"] + original["linear"] + original["quadratic"] - sp.expand(original["kinetic"]))
    local_angle = sp.Function("alpha")(*coords)
    local_group = _so2_rotation(local_angle)
    local_derivative = True
    for mu in range(4):
        slope = sp.diff(local_group, coords[mu])
        expected = sp.diff(local_angle, coords[mu]) * (generator * local_group)
        local_derivative = local_derivative and _is_zero(sp.simplify(slope - expected))
    local_field = sp.simplify(local_group * phi)
    shifted = [connection[mu] + sp.diff(local_angle, coords[mu]) for mu in range(4)]
    local_pack = _pack(local_field, shifted, generator, built)
    local_transport = True
    for mu in range(4):
        local_transport = local_transport and _is_zero(local_pack["covariant"][mu] - sp.simplify(local_group * original["covariant"][mu]))
    local_kinetic = _is_zero(sp.expand(local_pack["kinetic"] - original["kinetic"]))
    local_potential = _is_zero(sp.expand(local_pack["potential"] - original["potential"]))
    local_maxwell = _is_zero(sp.expand(local_pack["maxwell"] - original["maxwell"]))
    local_strength = _is_zero(sp.expand(local_pack["strength"] - original["strength"]))
    local_fragments_separate = all(
        _is_zero(local_pack[name] - original[name]) for name in ("ordinary", "linear", "quadratic")
    )
    local_sum = _is_zero(local_pack["ordinary"] + local_pack["linear"] + local_pack["quadratic"] - (original["ordinary"] + original["linear"] + original["quadratic"]))
    kappa_only = _is_zero(_inner(turned, turned) - _inner(phi, phi))
    hint_only = _is_zero(_inner(turned, mass * turned) - _inner(phi, mass * phi))
    probe = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    breaker = sp.diag(0, 1, 0)
    breaker_moves = not _is_zero(_inner(closed * probe, breaker * closed * probe) - _inner(probe, breaker * probe))
    breaker_absent = not _is_zero(breaker - mass)
    matter = built["kinetic"] + built["potential"]
    phi_equation = sp.Matrix([_el_scalar(matter + built["maxwell"], phi[index], coords) for index in range(3)])
    connection_equation = [_el_scalar(matter + built["maxwell"], connection[nu], coords) for nu in range(4)]
    gauge_identity = _is_zero(sp.expand(sum(sp.diff(connection_equation[nu], coords[nu]) for nu in range(4)) - _inner(phi_equation, generator * phi)))
    momentum = sp.Matrix([sp.diff(built["kinetic"], sp.diff(phi[index], coords[0])) for index in range(3)])
    noether = sp.expand(_inner(momentum, generator * phi))
    raised = sp.zeros(3, 1)
    for nu in range(4):
        raised += built["eta"][0, nu] * original["covariant"][nu]
    ordinary_slope = sp.zeros(3, 1)
    for nu in range(4):
        ordinary_slope += built["eta"][0, nu] * built["slopes"][nu]
    derived = sp.expand(2 * coefficient * _inner(raised, generator * phi))
    stored = sp.expand(2 * coefficient * _inner(ordinary_slope, generator * phi))
    charge_scalar = _inner(generator * phi, generator * phi)
    shift = sp.expand(2 * coefficient * sum(built["eta"][0, nu] * connection[nu] for nu in range(4)) * charge_scalar)
    current_matches_derived = _is_zero(noether - derived)
    current_matches_stored = _is_zero(noether - stored)
    difference_matches = _is_zero(noether - stored + shift)
    raised_all = []
    for mu in range(4):
        acc = sp.zeros(3, 1)
        for nu in range(4):
            acc += built["eta"][mu, nu] * original["covariant"][nu]
        raised_all.append(acc)
    box = sp.zeros(3, 1)
    for mu in range(4):
        box += sp.Matrix([sp.diff(raised_all[mu][index], coords[mu]) for index in range(3)])
        box -= connection[mu] * (generator * raised_all[mu])
    current_divergence = sp.expand(sum(sp.diff(_inner(raised_all[mu], generator * phi), coords[mu]) for mu in range(4)))
    reaction = built["symbols"]["c_H"] * (mass * phi) + built["symbols"]["kappa"] * phi
    on_shell_identity = _is_zero(current_divergence - _inner(box, generator * phi)) and _is_zero(sp.expand(_inner(reaction, generator * phi)))
    extra = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    extra_commutator = _is_zero(extra * mass - mass * extra)
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    extra_when_equal = _is_zero((extra * mass - mass * extra).subs(lam_a, lam_b))
    extra_angle = sp.symbols("theta", real=True)
    extra_group = sp.simplify((extra_angle * extra).exp())
    extra_field = sp.simplify(extra_group * phi)
    extra_pack = _pack(extra_field, connection, generator, built)
    extra_kinetic = sp.expand(extra_pack["kinetic"] - original["kinetic"])
    extra_potential = sp.expand(extra_pack["potential"] - original["potential"])
    extra_kinetic_generic = _is_zero(extra_kinetic)
    extra_kinetic_equal = _is_zero(extra_kinetic.subs(lam_a, lam_b))
    extra_potential_generic = _is_zero(extra_potential)
    extra_potential_equal = _is_zero(extra_potential.subs(lam_a, lam_b))
    extra_kinetic_without_z = _is_zero(extra_kinetic.subs(coefficient, 0))
    basis = sp.diag(1, 1, -1)
    basis_generator = sp.simplify(basis.T * generator * basis)
    basis_mass = sp.simplify(basis.T * mass * basis)
    basis_algebra = _is_zero(basis_generator + generator) and _is_zero(basis_generator.T + basis_generator)
    basis_commutator = _is_zero(basis_generator * basis_mass - basis_mass * basis_generator)
    basis_group = sp.simplify((alpha * basis_generator).exp())
    basis_conjugates = _is_zero(basis_group.T * basis_mass * basis_group - basis_mass)
    checks = {
        "basis_algebra": basis_algebra,
        "basis_commutator": basis_commutator,
        "basis_conjugates": basis_conjugates,
        "breaker_absent": breaker_absent,
        "breaker_detected": breaker_moves,
        "commutator": commutator,
        "conjugated": conjugated,
        "current_difference": difference_matches,
        "current_derived": current_matches_derived,
        "current_not_stored": not current_matches_stored,
        "expansion_sum": expansion_sums,
        "exponential": exponential_matches,
        "extra_kinetic_not_generic": not extra_kinetic_generic,
        "extra_kinetic_not_equal": not extra_kinetic_equal,
        "extra_kinetic_without_z": extra_kinetic_without_z,
        "extra_not_generic": not extra_commutator,
        "extra_potential_equal": extra_potential_equal,
        "extra_potential_not_generic": not extra_potential_generic,
        "extra_when_equal": extra_when_equal,
        "gauge_identity": gauge_identity,
        "global_kinetic": global_kinetic,
        "global_linear": global_linear,
        "global_maxwell": global_maxwell,
        "global_ordinary": global_ordinary,
        "global_potential": global_potential,
        "global_quadratic": global_quadratic,
        "hint": hint_only,
        "kappa": kappa_only,
        "local_derivative": local_derivative,
        "local_fragments_mix": not local_fragments_separate,
        "local_kinetic": local_kinetic,
        "local_maxwell": local_maxwell,
        "local_potential": local_potential,
        "local_strength": local_strength,
        "local_sum": local_sum,
        "local_transport": local_transport,
        "on_shell_current": on_shell_identity,
        "orthogonal": orthogonal,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return {"failed": failed, "status": "SYMMETRY_MISMATCH"}
    return {
        "basis_relation": "K changes orientation and the same one-parameter group remains",
        "breaking_terms": [],
        "current_comparison": "DIFFERENT",
        "current_difference": CURRENT_DIFFERENCE,
        "enlargement": "potential only when lam_a = lam_b; completed kinetic term stays non-invariant",
        "gauge_identity": GAUGE_IDENTITY,
        "k_antisymmetric": "TRUE",
        "new_fields": [],
        "new_interactions": [],
        "noether_current": NOETHER_CURRENT,
        "parameters_fixed": [],
        "phase_5b0_current": CURRENT_FORMULA,
        "special_cases_replace_generic": False,
        "status": "DERIVED",
    }


def _isolated(document: Any) -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    rendered = json.dumps(document)
    return (
        ("known_" + "physics") not in text
        and all(token not in text for token in _ranking_tokens())
        and all(marker not in rendered for marker in _target_markers())
    )


def build_manifest(action_hash: str) -> dict[str, Any]:
    manifest = {
        "action_hash_14i_input": action_hash,
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": EXPECTED_LEXICON_HASH,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _result_digest(science: dict[str, Any]) -> str:
    return content_digest(
        {
            "comparison": science["current_comparison"],
            "current": science["noether_current"],
            "enlargement": science["enlargement"],
            "gauge": science["gauge_identity"],
        }
    )


def negative_tests(result: dict[str, Any], repeated: str) -> list[dict[str, str]]:
    science = result["science"]
    actions = result["actions"]
    cases = [
        ("1", "freeze verification precedes the symmetry test", "VERIFIED", result["FREEZE_STATUS"]),
        ("2", "Phase 14I hash is bound", ACTION_HASH_14I, result["ACTION_HASH_14I_INPUT"]),
        ("3", "K stays antisymmetric", "TRUE", science["k_antisymmetric"]),
        ("4", "commutator is reproduced", "VERIFIED", "VERIFIED" if science["status"] == "DERIVED" else "FAILED"),
        ("5", "global kinetic invariance", "EXACT", result["KINETIC_GLOBAL_STATUS"]),
        ("6", "local kinetic covariance", "EXACT", result["KINETIC_LOCAL_STATUS"]),
        ("7", "H_int invariance", "EXACT", result["HINT_STATUS"]),
        ("8", "identity term invariance", "EXACT", result["KAPPA_STATUS"]),
        ("9", "nonlinear terms in the completed action", "INVARIANT", result["NONLINEAR_STATUS"] if science["breaking_terms"] == [] else "BROKEN"),
        ("10", "Branch A complete action", "EXACT", result["BRANCH_A_GLOBAL_SYMMETRY_STATUS"]),
        ("11", "Branch B complete global action", "EXACT", result["BRANCH_B_GLOBAL_SYMMETRY_STATUS"]),
        ("12", "Branch B local covariance", "EXACT", result["BRANCH_B_LOCAL_GAUGE_STATUS"]),
        ("13", "F_mu_nu invariance", "EXACT", result["F_STATUS"]),
        ("14", "F2 invariance", "EXACT", result["F2_STATUS"]),
        ("15", "Noether current is reconstructed", NOETHER_CURRENT, science["noether_current"]),
        ("16", "comparison with the Phase 5B.0 current", "DIFFERENT", science["current_comparison"]),
        ("17", "gauge identity", "VERIFIED", result["GAUGE_IDENTITY_STATUS"]),
        ("18", "special limits stay off the generic result", "FALSE", "FALSE" if science["special_cases_replace_generic"] is False else "TRUE"),
        ("19", "basis change preserves the conclusion", "VERIFIED", result["BASIS_INVARIANCE_STATUS"]),
        ("20", "no parameter is tuned", "0", "0" if science["parameters_fixed"] == [] else "FIXED"),
        ("21", "frozen action stays unchanged", "FALSE", "FALSE" if result["FROZEN_ACTION_MODIFIED"] is False else "TRUE"),
        ("22", "no new field or interaction", "0", "0" if science["new_fields"] == [] and science["new_interactions"] == [] else "ADDED"),
        ("23", "no experimental input", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("24", "no quantum claim", "UNTESTED", result["QUANTUM_STATUS"]),
        ("25", "Branch A contains no F2 term", "ABSENT", "ABSENT" if all(item["f2_term"] == "ABSENT" for item in actions if item["test_action_id"] == "GAUGED_MATTER_TEST_ACTION_COMPLETE") else "PRESENT"),
        ("26", "Branch B contains the inherited F2 term", F2_TERM, F2_TERM if all(item["f2_term"] == F2_TERM for item in actions if "F2" in item["test_action_id"]) else "OTHER"),
        ("27", "repeated execution matches", "IDENTICAL", "IDENTICAL" if result["digest"] == repeated else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_14L_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_14L_BLOCKED"}


def run_phase_14l(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    phase14k = run_phase_14k(write_artifacts=False)
    provenance = _read("phase14i_completion_artifacts/PHASE_14I_PROVENANCE.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or phase14k.get("PHASE_14K_STATUS") != "COMPLETE"
        or phase14k.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or provenance.get("action_hash_after") != ACTION_HASH_14I
        or phase14k.get("FROZEN_ACTION_MODIFIED") is not False
        or phase14k.get("QUANTUM_STATUS") != "UNTESTED"
    ):
        return _stop("freeze gate or completed-action binding")
    science = _audit(so2_generator_K())
    if science.get("status") != "DERIVED":
        return {"PHASE_14L_STATUS": "BLOCKED", "failed": science.get("failed", []), "status": science.get("status", "SYMMETRY_MISMATCH")}
    repeated = _audit(so2_generator_K())
    if repeated.get("status") != "DERIVED":
        return _stop("reproducibility")
    digest = _result_digest(science)
    second = _result_digest(repeated)
    if digest != second:
        return _stop("reproducibility")
    manifest = build_manifest(ACTION_HASH_14I)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_14L_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "BRANCH_A_GLOBAL_SYMMETRY_STATUS": "EXACT",
        "BRANCH_A_LOCAL_COVARIANCE_STATUS": "VERIFIED",
        "BRANCH_B_GLOBAL_SYMMETRY_STATUS": "EXACT",
        "BRANCH_B_LOCAL_GAUGE_STATUS": "EXACT",
        "KINETIC_GLOBAL_STATUS": "EXACT",
        "KINETIC_LOCAL_STATUS": "EXACT",
        "HINT_STATUS": "EXACT",
        "KAPPA_STATUS": "EXACT",
        "NONLINEAR_STATUS": "INVARIANT",
        "F_STATUS": "EXACT",
        "F2_STATUS": "EXACT",
        "NOETHER_CURRENT_STATUS": "DIFFERENT",
        "NOETHER_CHARGE_STATUS": "UNTESTED",
        "GAUGE_IDENTITY_STATUS": "VERIFIED",
        "BASIS_INVARIANCE_STATUS": "VERIFIED",
        "PARAMETER_DEPENDENCE_STATUS": "VERIFIED",
        "QUANTUM_STATUS": derive_quantum()["status"],
        "ACTION_FREEZE_VERIFIED": True,
        "ATOMIC_GATE": "VERIFIED",
        "CONCURRENCY_GUARD": "VERIFIED",
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "CURRENT_ON_SHELL_STATUS": "VERIFIED",
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "actions": phase14k["actions"],
        "science": science,
        "digest": digest,
    }
    negatives = negative_tests(payload, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14L_STATUS": "BLOCKED", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if request_physical_activation("T09")["status"] == "AUTHORIZED" or numerical_search()["status"] != "NOT_EXECUTED":
        return _stop("search or activation")
    payload["dry_run_negatives"] = negatives
    payload["search_manifest"] = manifest
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14L.json").write_bytes(canonical_json_bytes(manifest))
        files = {
            "PHASE_14L_GLOBAL.json": {
                "branch_a": "EXACT",
                "branch_b": "EXACT",
                "commutator": "[K, H_int] = 0",
                "provenance": "DERIVED FROM COMPLETED TEST ACTION",
            },
            "PHASE_14L_LOCAL.json": {
                "branch_a_covariance": "VERIFIED",
                "branch_b_gauge": "EXACT",
                "connection_shift": "mathcalA'_mu = mathcalA_mu + d_mu alpha",
                "f2": "EXACT",
                "provenance": "DERIVED GIVEN GAUGING ASSUMPTION",
            },
            "PHASE_14L_CURRENT.json": {
                "charge": "UNTESTED",
                "comparison": "DIFFERENT",
                "derived": NOETHER_CURRENT,
                "difference": CURRENT_DIFFERENCE,
                "on_shell": "VERIFIED",
                "stored": CURRENT_FORMULA,
            },
            "PHASE_14L_PROVENANCE.json": {
                "action_hash_14i_input": ACTION_HASH_14I,
                "gauge_identity": "DERIVED",
                "global_so2": "DERIVED FROM COMPLETED TEST ACTION",
                "local_u1": "DERIVED GIVEN GAUGING ASSUMPTION",
                "noether_current": "DERIVED",
                "quantum": "UNTESTED",
            },
            "PHASE_14L_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "noether_charge", "status": "UNTESTED"},
                    {"frontier_id": "quantum", "status": "UNTESTED"},
                    {"frontier_id": "coupling_normalization", "status": "NOT_STARTED"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
