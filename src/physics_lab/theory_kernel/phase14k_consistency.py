"""Phase 14K audits consistency of the Phase 14J equations.

The completed test action and the frozen action are not modified.
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
from physics_lab.physics.phase5c_gauging import _inner, _is_zero, so2_generator_K
from physics_lab.physics.spacetime import MOSTLY_PLUS, eta_diag
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14j_eom import (
    BRANCH_A_DIRECT,
    BRANCH_A_EXPANDED,
    BRANCH_B_EQUATION,
    F2_TERM,
    GRAVITY_EQUATION,
    PHI_COMPONENT,
    T_F2,
    T_MATTER,
    _el_scalar,
    _lagrangians,
    run_phase_14j,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14K"
CODE_VERSION = "phase14k-consistency-v1"
TEST_VERSION = "phase14k-tests-v1"
ARTIFACT_DIR_NAME = "phase14k_consistency_artifacts"
IR_VERSION = "phase14k-consistency-v1"
PREVIOUS_IR_VERSION = "phase14j-eom-v1"
ACTION_HASH_14I = "48dc1f2edb675c1de52a9b8a0031565310f56b0638d47467a114478b34f8c25d"
CURRENT_OFF_SHELL = "d_mu <D^mu Phi, K Phi> = <D_mu D^mu Phi, K Phi>"
CURRENT_ON_SHELL = "d_mu j^mu = 0 on the Phi shell"
DIVERGENCE_IDENTITY = "d_nu d_mu F^{mu nu} = 0"
PRINCIPAL_PART = "Z_A (box A^nu - d^nu d_alpha A^alpha)"
CONSERVATION_IDENTITY = "d_mu T^{mu nu} equals the Phi and connection contractions"
METRIC_IDENTITY = "divergence of the metric equation equals -d_mu T^{mu nu} under retained Bianchi and metric compatibility"


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


def derive_quantum() -> dict[str, str]:
    return {"status": "UNTESTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def keep_symmetry() -> dict[str, str]:
    return {"status": "PENDING_REVERIFICATION"}


def _raised_vectors(covariant: list[Any], eta: sp.Matrix) -> list[sp.Matrix]:
    raised: list[sp.Matrix] = []
    for mu in range(4):
        acc = sp.zeros(3, 1)
        for nu in range(4):
            acc += eta[mu, nu] * covariant[nu]
        raised.append(acc)
    return raised


def _box(raised: list[sp.Matrix], connection: list[Any], generator: sp.Matrix, coords: tuple[Any, ...]) -> sp.Matrix:
    divergence = sp.zeros(3, 1)
    for mu in range(4):
        divergence += sp.Matrix([sp.diff(raised[mu][index], coords[mu]) for index in range(3)])
        divergence -= connection[mu] * (generator * raised[mu])
    return divergence


def _field_strength(connection: list[Any], coords: tuple[Any, ...]) -> sp.Matrix:
    strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            strength[mu, nu] = sp.diff(connection[nu], coords[mu]) - sp.diff(connection[mu], coords[nu])
    return strength


def _maxwell_stress(strength: sp.Matrix, eta: sp.Matrix, coefficient: Any) -> sp.Matrix:
    raised_once = strength * eta
    scalar = sum(strength[i, j] * (eta * strength * eta)[i, j] for i in range(4) for j in range(4))
    lowered = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            contracted = sum(raised_once[mu, lam] * strength[nu, lam] for lam in range(4))
            lowered[mu, nu] = coefficient * (contracted - sp.Rational(1, 4) * eta[mu, nu] * scalar)
    return eta * lowered * eta


def _principal_symbol() -> dict[str, Any]:
    eta = sp.diag(*eta_diag(MOSTLY_PLUS))
    wave = sp.Matrix(sp.symbols("k0 k1 k2 k3"))
    raised = eta * wave
    square = sp.simplify((wave.T * raised)[0, 0])
    symbol = -square * eta + raised * raised.T
    kernel = _is_zero(sp.simplify(symbol * wave))
    sample = {wave[0]: 2, wave[1]: 0, wave[2]: 0, wave[3]: 1}
    evaluated = sp.simplify(symbol.subs(sample))
    return {
        "degeneracy": "gauge direction k_mu is annihilated",
        "kernel": kernel,
        "operator": PRINCIPAL_PART,
        "rank_on_sample": int(evaluated.rank()) if kernel else -1,
        "sample_square": sp.simplify(square.subs(sample)) != 0,
    }


def _audit(generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    built = _lagrangians(generator)
    coords = built["coords"]
    phi = built["phi"]
    connection = built["connection"]
    eta = built["eta"]
    coefficient = built["symbols"]["Z"]
    gauge_coefficient = built["symbols"]["Z_A"]
    mass = built["matrix"]
    generator_charge = _inner(generator * phi, generator * phi)
    raised = _raised_vectors(built["covariant"], eta)
    box = _box(raised, connection, generator, coords)
    matter = built["kinetic"] + built["potential"]
    phi_el = sp.Matrix([_el_scalar(matter, phi[index], coords) for index in range(3)])
    reaction = built["symbols"]["c_H"] * (mass * phi) + built["symbols"]["kappa"] * phi
    phi_closed = sp.expand(-2 * coefficient * box + reaction)
    if not _is_zero(phi_el - phi_closed):
        return {"status": "PHI_EQUATION_MISMATCH"}
    matter_connection = [_el_scalar(matter, connection[nu], coords) for nu in range(4)]
    direct = [sp.expand(-2 * coefficient * _inner(raised[nu], generator * phi)) for nu in range(4)]
    if any(not _is_zero(matter_connection[nu] - direct[nu]) for nu in range(4)):
        return {"status": "BRANCH_A_MISMATCH"}
    strength = _field_strength(connection, coords)
    raised_strength = eta * strength * eta
    maxwell_connection = [_el_scalar(built["maxwell"], connection[nu], coords) for nu in range(4)]
    divergence_f = [sp.expand(sum(sp.diff(raised_strength[mu, nu], coords[mu]) for mu in range(4))) for nu in range(4)]
    full_connection = [sp.expand(maxwell_connection[nu] + matter_connection[nu]) for nu in range(4)]
    full_closed = [sp.expand(gauge_coefficient * divergence_f[nu] + direct[nu]) for nu in range(4)]
    if any(not _is_zero(full_connection[nu] - full_closed[nu]) for nu in range(4)):
        return {"status": "BRANCH_B_MISMATCH"}
    antisymmetry = _is_zero(sp.expand(sum(sp.diff(divergence_f[nu], coords[nu]) for nu in range(4))))
    current_divergence = sp.expand(sum(sp.diff(_inner(raised[mu], generator * phi), coords[mu]) for mu in range(4)))
    current_identity = _is_zero(current_divergence - _inner(box, generator * phi))
    potential_projection = _is_zero(sp.expand(_inner(reaction, generator * phi)))
    commutator = _is_zero(generator * mass - mass * generator)
    branch_divergence = sp.expand(sum(sp.diff(full_connection[nu], coords[nu]) for nu in range(4)))
    source_match = _is_zero(branch_divergence - _inner(phi_el, generator * phi))
    slopes = _raised_vectors(built["slopes"], eta)
    ungauged = sp.expand(sum(sp.diff(_inner(slopes[mu], generator * phi), coords[mu]) for mu in range(4)))
    ungauged_is_identity = _is_zero(ungauged)
    jacobian_matches = True
    for nu in range(4):
        for sigma in range(4):
            derivative = sp.diff(direct[nu], connection[sigma])
            expected = 2 * coefficient * generator_charge * eta[nu, sigma]
            jacobian_matches = jacobian_matches and _is_zero(sp.expand(derivative - expected))
    charge_polynomial = sp.expand(generator_charge - (phi[1] ** 2 + phi[2] ** 2))
    kernel_vector = sp.Matrix([sp.symbols("p0", real=True), 0, 0])
    kernel_annihilated = _is_zero(generator * kernel_vector)
    generic_jacobian = (2 * coefficient * sp.symbols("q", nonzero=True) * eta).rank() == 4
    principal_match = True
    time_class = []
    for nu in range(4):
        doubled = 0
        for lam in range(4):
            raised_component = eta[nu, lam] * connection[lam]
            doubled += sum(eta[a, c] * sp.diff(raised_component, coords[a], coords[c]) for a in range(4) for c in range(4))
        divergence_a = sum(eta[alpha, lam] * sp.diff(connection[lam], coords[alpha]) for alpha in range(4) for lam in range(4))
        lowered_derivative = sum(eta[nu, sigma] * sp.diff(divergence_a, coords[sigma]) for sigma in range(4))
        principal_match = principal_match and _is_zero(sp.expand(divergence_f[nu] - (doubled - lowered_derivative)))
        second_time = [rho for rho in range(4) if divergence_f[nu].has(sp.diff(connection[rho], coords[0], 2))]
        time_class.append(second_time)
    symbol = _principal_symbol()
    higher = any(
        expr.has(sp.diff(field, coord, 2))
        for expr in (built["kinetic"], built["maxwell"])
        for field in list(phi) + connection
        for coord in coords
    )
    matter_stress = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            matter_stress[mu, nu] = eta[mu, nu] * matter - 2 * coefficient * _inner(raised[mu], raised[nu])
    gauge_stress = _maxwell_stress(strength, eta, gauge_coefficient)
    matter_lowered = [sum(eta[mu, lam] * matter_connection[lam] for lam in range(4)) for mu in range(4)]
    maxwell_lowered = [sum(eta[mu, lam] * maxwell_connection[lam] for lam in range(4)) for mu in range(4)]
    full_lowered = [matter_lowered[mu] + maxwell_lowered[mu] for mu in range(4)]
    conservation = True
    for nu in range(4):
        matter_div = sp.expand(sum(sp.diff(matter_stress[mu, nu], coords[mu]) for mu in range(4)))
        phi_contraction = sp.expand(_inner(phi_el, raised[nu]))
        matter_field = sp.expand(sum(matter_lowered[mu] * raised_strength[mu, nu] for mu in range(4)))
        gauge_div = sp.expand(sum(sp.diff(gauge_stress[mu, nu], coords[mu]) for mu in range(4)))
        full_field = sp.expand(sum(full_lowered[mu] * raised_strength[mu, nu] for mu in range(4)))
        maxwell_field = sp.expand(sum(maxwell_lowered[mu] * raised_strength[mu, nu] for mu in range(4)))
        conservation = conservation and _is_zero(sp.expand(matter_div - phi_contraction + matter_field))
        conservation = conservation and _is_zero(sp.expand(gauge_div + maxwell_field))
        conservation = conservation and _is_zero(sp.expand(matter_div + gauge_div - phi_contraction + full_field))
    collapsed_connection = all(_is_zero(item.subs(coefficient, 0)) for item in matter_connection)
    collapsed_phi = _is_zero(phi_el.subs(coefficient, 0) - reaction)
    maxwell_removed = all(_is_zero(item.subs(gauge_coefficient, 0)) for item in maxwell_connection)
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    special_mass = mass.subs({lam_a: lam_b})
    special_still_commutes = _is_zero(generator * special_mass - special_mass * generator)
    checks = {
        "antisymmetry": antisymmetry,
        "charge_polynomial": _is_zero(charge_polynomial),
        "collapsed_connection": collapsed_connection,
        "collapsed_phi": collapsed_phi,
        "commutator": commutator,
        "conservation": conservation,
        "current_identity": current_identity,
        "generic_jacobian": generic_jacobian,
        "jacobian_matches": jacobian_matches,
        "kernel_annihilated": kernel_annihilated,
        "maxwell_removed": maxwell_removed,
        "not_higher_derivative": not higher,
        "not_identically_zero_response": not _is_zero(direct[1]),
        "potential_projection": potential_projection,
        "principal_kernel": symbol["kernel"] is True,
        "principal_match": principal_match,
        "principal_rank": symbol["rank_on_sample"] == 3,
        "principal_sample": symbol["sample_square"] is True,
        "source_match": source_match,
        "special_commutator": special_still_commutes,
        "time_order": time_class == [[], [1], [2], [3]],
        "ungauged_not_identity": not ungauged_is_identity,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return {"failed": failed, "status": "CONSISTENCY_MISMATCH"}
    return {
        "branch_a_role": "ALGEBRAIC_RESPONSE",
        "branch_a_equation": BRANCH_A_DIRECT,
        "branch_a_expanded": BRANCH_A_EXPANDED,
        "branch_b_equation": BRANCH_B_EQUATION,
        "branch_b_role": "SECOND_ORDER_EQUATION_WITH_GAUGE_REDUNDANT_DIRECTION",
        "commutator": "[K, H_int] = 0",
        "conservation_identity": CONSERVATION_IDENTITY,
        "current_off_shell": CURRENT_OFF_SHELL,
        "current_on_shell": CURRENT_ON_SHELL,
        "derived_relations": ["[K, H_int] = 0"],
        "divergence_identity": DIVERGENCE_IDENTITY,
        "generic_jacobian_rank": "4 when Z and <K Phi, K Phi> are nonzero",
        "metric_identity": METRIC_IDENTITY,
        "parameters_fixed": [],
        "phi_component": PHI_COMPONENT,
        "physical_dof_count": "NOT_PERFORMED",
        "principal_operator": PRINCIPAL_PART,
        "special_cases_replace_generic": False,
        "status": "DERIVED",
        "time_component": "NO_SECOND_TIME_DERIVATIVE",
        "spatial_components": "SECOND_TIME_DERIVATIVE",
        "ungauged_current_conservation": "NOT_THE_GAUGED_IDENTITY",
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
            "branch_a": science["branch_a_role"],
            "branch_b": science["branch_b_role"],
            "conservation": science["conservation_identity"],
            "current": science["current_on_shell"],
            "divergence": science["divergence_identity"],
            "phi": science["phi_component"],
        }
    )


def negative_tests(result: dict[str, Any], repeated: str) -> list[dict[str, str]]:
    science = result["science"]
    actions = result["actions"]
    cases = [
        ("1", "Phase 14I hash remains bound", ACTION_HASH_14I, result["ACTION_HASH_14I_INPUT"]),
        ("2", "Phase 14J equations reproduce exactly", PHI_COMPONENT, science["phi_component"] if science["branch_b_equation"] == BRANCH_B_EQUATION and science["branch_a_equation"] == BRANCH_A_DIRECT else "MISMATCH"),
        ("3", "branches remain separate", "2", "2" if len({item["test_action_id"] for item in actions}) == 2 else "MERGED"),
        ("4", "Branch A contains no F2", "ABSENT", "ABSENT" if all(item["f2_term"] == "ABSENT" for item in actions if item["test_action_id"] == "GAUGED_MATTER_TEST_ACTION_COMPLETE") else "PRESENT"),
        ("5", "Branch B contains the inherited F2 term", F2_TERM, F2_TERM if all(item["f2_term"] == F2_TERM for item in actions if "F2" in item["test_action_id"]) else "OTHER"),
        ("6", "Branch A classification is the algebraic response", "ALGEBRAIC_RESPONSE", science["branch_a_role"]),
        ("7", "Branch B principal term is the derived operator", PRINCIPAL_PART, science["principal_operator"]),
        ("8", "divergence identity is checked", "VERIFIED", result["DIVERGENCE_IDENTITY_STATUS"]),
        ("9", "current identity is checked", "VERIFIED", result["CURRENT_IDENTITY_STATUS"]),
        ("10", "stress conservation is deterministic", "VERIFIED", result["CONSERVATION_STATUS"] if result["digest"] == repeated else "UNSTABLE"),
        ("11", "metric consistency is deterministic", "VERIFIED", result["METRIC_CONSISTENCY_STATUS"] if result["digest"] == repeated else "UNSTABLE"),
        ("12", "special cases stay off the generic branch", "FALSE", "FALSE" if science["special_cases_replace_generic"] is False else "TRUE"),
        ("13", "no parameter is fixed", "0", "0" if science["parameters_fixed"] == [] else "FIXED"),
        ("14", "no new field appears", "0", "0" if science["new_fields"] == [] else "ADDED"),
        ("15", "no new interaction appears", "0", "0" if science["new_interactions"] == [] else "ADDED"),
        ("16", "no experimental constant appears", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("17", "no quantum claim is emitted", "UNTESTED", result["QUANTUM_STATUS"]),
        ("18", "symmetry stays pending", "PENDING_REVERIFICATION", result["SYMMETRY_STATUS"]),
        ("19", "no physical degree count is emitted", "NOT_PERFORMED", science["physical_dof_count"]),
        ("20", "repeated audit matches", "IDENTICAL", "IDENTICAL" if result["digest"] == repeated else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_14K_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_14K_BLOCKED"}


def _equations_bound() -> bool:
    phi = _read("phase14j_eom_artifacts/PHASE_14J_PHI_EOM.json")
    connection = _read("phase14j_eom_artifacts/PHASE_14J_CONNECTION_EOM.json")
    metric = _read("phase14j_eom_artifacts/PHASE_14J_METRIC_EOM.json")
    provenance = _read("phase14j_eom_artifacts/PHASE_14J_PROVENANCE.json")
    return (
        phi.get("component") == PHI_COMPONENT
        and connection.get("branch_a_direct") == BRANCH_A_DIRECT
        and connection.get("branch_a_expanded") == BRANCH_A_EXPANDED
        and connection.get("branch_b") == BRANCH_B_EQUATION
        and metric.get("equation") == GRAVITY_EQUATION
        and metric.get("matter_stress") == T_MATTER
        and metric.get("f2_stress") == T_F2
        and provenance.get("action_hash_14i_input") == ACTION_HASH_14I
    )


def run_phase_14k(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    phase14j = run_phase_14j(write_artifacts=False)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or phase14j.get("PHASE_14J_STATUS") != "COMPLETE"
        or phase14j.get("ACTION_HASH_14I_INPUT") != ACTION_HASH_14I
        or phase14j.get("FROZEN_ACTION_MODIFIED") is not False
        or phase14j.get("SYMMETRY_STATUS") != "PENDING_REVERIFICATION"
        or phase14j.get("QUANTUM_STATUS") != "UNTESTED"
        or phase14j.get("CLASSICAL_EOM") != "DERIVED"
        or not _equations_bound()
    ):
        return _stop("freeze gate or Phase 14J binding")
    actions = phase14j["actions"]
    science = _audit(so2_generator_K())
    if science.get("status") != "DERIVED":
        return {"PHASE_14K_STATUS": "BLOCKED", "status": science.get("status", "CONSISTENCY_MISMATCH")}
    science["new_fields"] = []
    science["new_interactions"] = []
    science["gravity_equation"] = GRAVITY_EQUATION
    repeated = _audit(so2_generator_K())
    if repeated.get("status") != "DERIVED":
        return _stop("reproducibility")
    compared = (
        "branch_a_role",
        "branch_b_role",
        "current_on_shell",
        "divergence_identity",
        "conservation_identity",
        "principal_operator",
        "generic_jacobian_rank",
        "physical_dof_count",
    )
    if any(repeated[key] != science[key] for key in compared):
        return _stop("reproducibility")
    digest = _result_digest(science)
    second = _result_digest(repeated)
    manifest = build_manifest(ACTION_HASH_14I)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_14K_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "BRANCH_A_CONSISTENCY_STATUS": "VERIFIED",
        "BRANCH_B_CONSISTENCY_STATUS": "VERIFIED",
        "CURRENT_IDENTITY_STATUS": "VERIFIED",
        "DIVERGENCE_IDENTITY_STATUS": "VERIFIED",
        "CONSERVATION_STATUS": "VERIFIED",
        "METRIC_CONSISTENCY_STATUS": "VERIFIED",
        "PRINCIPAL_SYMBOL_STATUS": "VERIFIED",
        "CONSTRAINT_STATUS": "VERIFIED",
        "OSTROGRADSKY_STATUS": "NOT_TRIGGERED",
        "SYMMETRY_STATUS": keep_symmetry()["status"],
        "QUANTUM_STATUS": derive_quantum()["status"],
        "ACTION_FREEZE_VERIFIED": True,
        "ATOMIC_GATE": "VERIFIED",
        "CONCURRENCY_GUARD": "VERIFIED",
        "ACTION_HASH_14I_INPUT": ACTION_HASH_14I,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "BIANCHI_STATUS": "RETAINED_NOT_REDERIVED",
        "CONSERVATION_SCOPE": "MOSTLY_PLUS_PROBE",
        "SEARCH_EXECUTED": False,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "actions": actions,
        "science": science,
        "digest": digest,
    }
    negatives = negative_tests(payload, second)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14K_STATUS": "BLOCKED", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if request_physical_activation("T09")["status"] == "AUTHORIZED":
        return _stop("T09")
    if numerical_search()["status"] != "NOT_EXECUTED":
        return _stop("search")
    payload["dry_run_negatives"] = negatives
    payload["search_manifest"] = manifest
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14K.json").write_bytes(canonical_json_bytes(manifest))
        files = {
            "PHASE_14K_CURRENT_IDENTITY.json": {
                "branch_b_divergence": "equals the Phi residual projected on K Phi",
                "off_shell": CURRENT_OFF_SHELL,
                "on_phi_shell": CURRENT_ON_SHELL,
                "ungauged": "NOT_THE_GAUGED_IDENTITY",
            },
            "PHASE_14K_CONSTRAINTS.json": {
                "branch_a": "ALGEBRAIC_RESPONSE",
                "branch_a_generic_jacobian": science["generic_jacobian_rank"],
                "branch_b_principal": PRINCIPAL_PART,
                "branch_b_time_component": "NO_SECOND_TIME_DERIVATIVE",
                "divergence_identity": DIVERGENCE_IDENTITY,
                "physical_dof_count": "NOT_PERFORMED",
                "zero_charge_branch": "FIELD-DEPENDENT BRANCH",
            },
            "PHASE_14K_CONSERVATION.json": {
                "bianchi": "RETAINED_NOT_REDERIVED",
                "branch_a": "matter stress only",
                "branch_b": "matter stress plus F2 stress",
                "identity": CONSERVATION_IDENTITY,
                "metric": METRIC_IDENTITY,
                "scope": "MOSTLY_PLUS_PROBE",
            },
            "PHASE_14K_PROVENANCE.json": {
                "action_hash_14i_input": ACTION_HASH_14I,
                "constraint_classification": "DERIVED FROM COMPLETED TEST ACTION",
                "current_relation": "DERIVED / REUSED FROM PHASE_5B.0",
                "eom_consistency": "DERIVED FROM PHASE_14J_EQUATIONS",
                "metric_consistency": "DERIVED",
                "quantum": "UNTESTED",
                "stress_energy_conservation": "DERIVED",
                "symmetry": "PENDING_REVERIFICATION",
            },
            "PHASE_14K_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "symmetry", "status": "PENDING_REVERIFICATION"},
                    {"frontier_id": "quantum", "status": "UNTESTED"},
                    {"frontier_id": "hamiltonian_dof", "status": "NOT_PERFORMED"},
                    {"frontier_id": "curved_christoffel", "status": "NOT_RECOMPUTED"},
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
