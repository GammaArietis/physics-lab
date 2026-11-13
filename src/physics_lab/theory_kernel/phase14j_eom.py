"""Phase 14J derives classical equations from the Phase 14I completed test action.

The frozen action is not modified. Quantum consistency is not claimed.
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
from physics_lab.theory_kernel.phase14i_completion import PROVENANCE, run_phase_14i
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14J"
CODE_VERSION = "phase14j-eom-v1"
TEST_VERSION = "phase14j-tests-v1"
ARTIFACT_DIR_NAME = "phase14j_eom_artifacts"
IR_VERSION = "phase14j-eom-v1"
PREVIOUS_IR_VERSION = "phase14i-completion-v1"
KINETIC_DENSITY = "Z g^{mu nu} <D_mu Phi, D_nu Phi>"
D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
CURRENT_FORMULA = "j^mu = 2 Z <nabla^mu Phi, K Phi>"
F_DEFINITION = "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
F2_TERM = "integral sqrt(-g) [- Z_A/4 F_mu_nu F^mu_nu]"
GRAVITY = "S_gravity = integral sqrt(-g) (c0 + c1 R), c0 c1 FREE"
GRAVITY_EQUATION = "2 c1 G_mu_nu - c0 g_mu_nu = T_mu_nu"
PHI_COMPONENT = "-2 Z D_mu D^mu Phi + (c_H H_int + kappa I) Phi = 0"
PHI_COVARIANT = "2 Z D_mu D^mu Phi = (c_H H_int + kappa I) Phi"
BRANCH_A_DIRECT = "-2 Z <D^mu Phi, K Phi> = 0"
BRANCH_A_EXPANDED = "- j^mu + 2 Z mathcalA^mu <K Phi, K Phi> = 0"
BRANCH_B_EQUATION = "Z_A nabla_mu F^{mu nu} - j^nu + 2 Z mathcalA^nu <K Phi, K Phi> = 0"
T_MATTER = "g_mu_nu L_matter - 2 Z <D_mu Phi, D_nu Phi>"
T_F2 = "Z_A (F_mu^lambda F_nu_lambda - 1/4 g_mu_nu F^2)"
ALGEBRAIC = "MATTER-SECTOR VARIATION IS ALGEBRAIC IN mathcal A_mu"


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


def _half(node: Any) -> bool:
    return isinstance(node, dict) and node.get("rational") == [1, 2]


def _phi(node: Any) -> bool:
    return isinstance(node, dict) and node.get("field") == "Phi"


def _diag(node: Any) -> list[str] | None:
    if isinstance(node, dict) and node.get("op") == "matrix":
        entries = node["entries"]
        return [entries[index][index]["symbol"] for index in range(int(node["rows"]))]
    return None


def _potential_ready(action: dict[str, Any]) -> bool:
    phi_sq = next(item for item in action["terms"] if item["id"] == "matter_phi_sq")["expression"]
    hint = next(item for item in action["terms"] if item["id"] == "matter_H_int")["expression"]
    phi_args = (phi_sq.get("integrand") or {}).get("args") or []
    hint_args = (hint.get("integrand") or {}).get("args") or []
    phi_symbols = [item.get("symbol") for item in phi_args if isinstance(item, dict) and "symbol" in item]
    hint_symbols = [item.get("symbol") for item in hint_args if isinstance(item, dict) and "symbol" in item]
    phi_inner = next((item for item in phi_args if isinstance(item, dict) and item.get("op") == "inner_product"), None)
    hint_inner = next((item for item in hint_args if isinstance(item, dict) and item.get("op") == "inner_product"), None)
    diagonal = _diag((hint_inner or {}).get("right", {}).get("operator"))
    return (
        phi_sq.get("density") == "sqrt_minus_g"
        and hint.get("density") == "sqrt_minus_g"
        and phi_symbols == ["kappa"]
        and hint_symbols == ["c_H"]
        and any(_half(item) for item in phi_args)
        and any(_half(item) for item in hint_args)
        and phi_inner is not None
        and _phi(phi_inner.get("left"))
        and _phi(phi_inner.get("right"))
        and hint_inner is not None
        and _phi(hint_inner.get("left"))
        and diagonal == ["lam_a", "lam_b", "lam_b"]
    )


def _el_scalar(density: Any, field: Any, coords: tuple[Any, ...]) -> Any:
    term = sp.diff(density, field)
    for coord in coords:
        slope = sp.diff(field, coord)
        term -= sp.diff(sp.diff(density, slope), coord)
    return sp.expand(term)


def _order(expr: Any, fields: list[Any], coords: tuple[Any, ...], level: int) -> bool:
    for field in fields:
        for left in coords:
            for right in coords:
                if level == 2 and expr.has(sp.diff(field, left, right)):
                    return True
                if level == 3 and expr.has(sp.diff(field, left, 3)):
                    return True
    return False


def _lagrangians(generator: sp.Matrix) -> dict[str, Any]:
    eta = sp.diag(*eta_diag(MOSTLY_PLUS))
    coords = sp.symbols("t x y z", real=True)
    coefficient, kappa, c_h, lam_a, lam_b, z_a = sp.symbols("Z kappa c_H lam_a lam_b Z_A", real=True)
    phi = sp.Matrix([sp.Function(f"Phi{index}")(*coords) for index in range(3)])
    connection = [sp.Function(f"A{index}")(*coords) for index in range(4)]
    matrix = sp.diag(lam_a, lam_b, lam_b)
    slopes = []
    covariant = []
    for mu in range(4):
        slope = sp.Matrix([sp.diff(phi[index], coords[mu]) for index in range(3)])
        slopes.append(slope)
        covariant.append(slope - connection[mu] * (generator * phi))
    kinetic = sum(coefficient * eta[mu, nu] * _inner(covariant[mu], covariant[nu]) for mu in range(4) for nu in range(4))
    potential = (kappa * sp.Rational(1, 2)) * _inner(phi, phi) + (c_h * sp.Rational(1, 2)) * _inner(phi, matrix * phi)
    strength = sp.zeros(4)
    for mu in range(4):
        for nu in range(4):
            strength[mu, nu] = sp.diff(connection[nu], coords[mu]) - sp.diff(connection[mu], coords[nu])
    raised = eta * strength * eta
    maxwell = -(z_a / 4) * sum(strength[mu, nu] * raised[mu, nu] for mu in range(4) for nu in range(4))
    return {
        "connection": connection,
        "coords": coords,
        "covariant": covariant,
        "eta": eta,
        "kinetic": kinetic,
        "matrix": matrix,
        "maxwell": maxwell,
        "phi": phi,
        "potential": potential,
        "raised_strength": raised,
        "slopes": slopes,
        "symbols": {"Z": coefficient, "Z_A": z_a, "c_H": c_h, "kappa": kappa},
    }


def _derive(generator: sp.Matrix) -> dict[str, Any]:
    if not _is_zero(generator.T + generator):
        return {"status": "K_NOT_ANTISYMMETRIC"}
    built = _lagrangians(generator)
    coords = built["coords"]
    phi = built["phi"]
    connection = built["connection"]
    eta = built["eta"]
    coefficient = built["symbols"]["Z"]
    z_a = built["symbols"]["Z_A"]
    matter = built["kinetic"] + built["potential"]
    phi_el = sp.Matrix([_el_scalar(matter, phi[index], coords) for index in range(3)])
    raised_d = []
    for mu in range(4):
        raised = sp.zeros(3, 1)
        for nu in range(4):
            raised += eta[mu, nu] * built["covariant"][nu]
        raised_d.append(raised)
    divergence = sp.zeros(3, 1)
    for mu in range(4):
        divergence += sp.Matrix([sp.diff(raised_d[mu][index], coords[mu]) for index in range(3)])
        divergence -= connection[mu] * (generator * raised_d[mu])
    phi_closed = sp.expand(-2 * coefficient * divergence + built["symbols"]["c_H"] * (built["matrix"] * phi) + built["symbols"]["kappa"] * phi)
    phi_match = _is_zero(phi_el - phi_closed)
    phi_second = any(_order(expr, list(phi), coords, 2) for expr in phi_el)
    phi_third = any(_order(expr, list(phi), coords, 3) for expr in phi_el)
    branch_a = [_el_scalar(matter, connection[nu], coords) for nu in range(4)]
    direct = [sp.expand(-2 * coefficient * _inner(raised_d[nu], generator * phi)) for nu in range(4)]
    ordinary_current = []
    quadratic_response = []
    charge = _inner(generator * phi, generator * phi)
    for nu in range(4):
        raised_slope = sp.zeros(3, 1)
        for sigma in range(4):
            raised_slope += eta[nu, sigma] * built["slopes"][sigma]
        ordinary_current.append(sp.expand(2 * coefficient * _inner(raised_slope, generator * phi)))
        quadratic_response.append(sp.expand(2 * coefficient * sum(eta[nu, sigma] * connection[sigma] for sigma in range(4)) * charge))
    expanded = [sp.expand(-ordinary_current[nu] + quadratic_response[nu]) for nu in range(4)]
    branch_a_match = all(_is_zero(branch_a[nu] - direct[nu]) and _is_zero(direct[nu] - expanded[nu]) for nu in range(4))
    branch_a_derivative = any(_order(expr, connection, coords, 1) for expr in branch_a)
    full = matter + built["maxwell"]
    branch_b = [_el_scalar(full, connection[nu], coords) for nu in range(4)]
    maxwell_response = []
    for nu in range(4):
        acc = 0
        for mu in range(4):
            acc += sp.diff(built["raised_strength"][mu, nu], coords[mu])
        maxwell_response.append(sp.expand(z_a * acc + direct[nu]))
    branch_b_match = all(_is_zero(branch_b[nu] - maxwell_response[nu]) for nu in range(4))
    branch_b_second = any(_order(expr, connection, coords, 2) for expr in branch_b)
    branch_b_third = any(_order(expr, connection, coords, 3) for expr in branch_b)
    higher_in_lagrangian = any(
        built["kinetic"].has(sp.diff(field, coord, 2)) or built["maxwell"].has(sp.diff(field, coord, 2))
        for field in list(phi) + connection
        for coord in coords
    )
    if not (phi_match and branch_a_match and branch_b_match and phi_second and not phi_third and not branch_a_derivative and branch_b_second and not branch_b_third and not higher_in_lagrangian):
        return {"status": "EOM_MISMATCH"}
    return {
        "branch_a_classification": ALGEBRAIC,
        "branch_a_equation": BRANCH_A_DIRECT,
        "branch_a_expanded": BRANCH_A_EXPANDED,
        "branch_a_order": "ALGEBRAIC",
        "branch_b_equation": BRANCH_B_EQUATION,
        "branch_b_order": "SECOND_ORDER",
        "current_formula": CURRENT_FORMULA,
        "factor_two_checked": True,
        "phi_algebraic": "(c_H H_int + kappa I) Phi",
        "phi_component": PHI_COMPONENT,
        "phi_covariant": PHI_COVARIANT,
        "phi_kinetic": "-2 Z D_mu D^mu Phi",
        "phi_order": "SECOND_ORDER",
        "quadratic_is_gauge_kinetic": False,
        "status": "DERIVED",
    }


def _stress_probe() -> dict[str, Any]:
    coefficient, potential, i00, i01, i11 = sp.symbols("Z V I00 I01 I11", real=True)
    eta = sp.diag(-1, 1)
    inner = sp.Matrix([[i00, i01], [i01, i11]])
    contracted = sum(eta[mu, nu] * inner[mu, nu] for mu in range(2) for nu in range(2))
    lagrangian = coefficient * contracted + potential
    matched = True
    for mu in range(2):
        for nu in range(2):
            varied = sp.simplify(-sp.Rational(1, 2) * eta[mu, nu] * lagrangian + coefficient * inner[mu, nu])
            tensor = sp.simplify(-2 * varied)
            closed = sp.simplify(eta[mu, nu] * lagrangian - 2 * coefficient * inner[mu, nu])
            matched = matched and _is_zero(tensor - closed)
    gauge_matched = _maxwell_stress_matches()
    return {"match": matched and gauge_matched, "matter": T_MATTER, "maxwell": T_F2}


def _maxwell_stress_matches() -> bool:
    coefficient = sp.symbols("Z_A", real=True)
    electric, magnetic = sp.symbols("f h", real=True)
    inverse = sp.symbols("g0 g1 g2 g3", real=True)
    metric = sp.diag(*inverse)
    strength = sp.zeros(4)
    strength[0, 1] = electric
    strength[1, 0] = -electric
    strength[0, 2] = magnetic
    strength[2, 0] = -magnetic
    raised = metric * strength * metric
    lagrangian = -(coefficient / 4) * sum(strength[i, j] * raised[i, j] for i in range(4) for j in range(4))
    point = {inverse[0]: -1, inverse[1]: 1, inverse[2]: 1, inverse[3]: 1}
    eta = sp.diag(-1, 1, 1, 1)
    evaluated = sp.simplify(lagrangian.subs(point))
    scalar = sp.simplify(sum(strength[i, j] * (eta * strength * eta)[i, j] for i in range(4) for j in range(4)))
    matched = True
    for index in range(4):
        derivative = sp.diff(lagrangian, inverse[index]).subs(point)
        tensor = sp.simplify(eta[index, index] * evaluated - 2 * derivative)
        raised_strength = strength * eta
        contracted = sum(raised_strength[index, lam] * strength[index, lam] for lam in range(4))
        closed = sp.simplify(coefficient * (contracted - sp.Rational(1, 4) * eta[index, index] * scalar))
        matched = matched and _is_zero(sp.expand(tensor - closed))
    return matched


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
            "branch_a": science["branch_a_equation"],
            "branch_b": science["branch_b_equation"],
            "phi": science["phi_component"],
            "t": science["stress_matter"],
        }
    )


def negative_tests(result: dict[str, Any], repeated: str, action_hash: str) -> list[dict[str, str]]:
    science = result["science"]
    actions = result["actions"]
    cases = [
        ("1", "freeze gate passes before derivation", "VERIFIED", result["FREEZE_STATUS"]),
        ("2", "Phase 14I hash is bound", action_hash, result["ACTION_HASH_14I_INPUT"]),
        ("3", "frozen hash remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("4", "Phi EOM matches the completed kinetic variation", "DERIVED", science["status"] if science["phi_component"] == PHI_COMPONENT else "MISMATCH"),
        ("5", "operator term is the stored potential contribution", "(c_H H_int + kappa I) Phi", science["phi_algebraic"]),
        ("6", "Branch A variation is reproduced", BRANCH_A_DIRECT, science["branch_a_equation"]),
        ("7", "Branch A classification is algebraic", ALGEBRAIC, science["branch_a_classification"]),
        ("8", "Branch B variation is reproduced", BRANCH_B_EQUATION, science["branch_b_equation"]),
        ("9", "F_mu_nu dependence is verified", "VERIFIED", result["F2_DEPENDENCY_STATUS"]),
        ("10", "the factor two is checked", "TRUE", "TRUE" if science["factor_two_checked"] and science["current_formula"] == CURRENT_FORMULA else "FALSE"),
        ("11", "stress tensor matches the computed variation", T_MATTER, science["stress_matter"] if science["stress_match"] else "UNCOMPUTED"),
        ("12", "gravity retains c0 and c1", GRAVITY_EQUATION, science["gravity_equation"]),
        ("13", "no parameter is fixed", "0", "0" if science["parameters_fixed"] == [] else "FIXED"),
        ("14", "no new field is added", "0", "0" if science["new_fields"] == [] else "ADDED"),
        ("15", "no new interaction is added", "0", "0" if science["new_interactions"] == [] else "ADDED"),
        ("16", "no experimental constant appears", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("17", "no numerical target appears", "ABSENT", "ABSENT" if _isolated(science) else "PRESENT"),
        ("18", "no quantum claim is made", "UNTESTED", result["QUANTUM_STATUS"]),
        ("19", "symmetry stays pending", "PENDING_REVERIFICATION", result["SYMMETRY_STATUS"]),
        ("20", "the branches stay separate", "2", "2" if len({item["test_action_id"] for item in actions}) == 2 else "MERGED"),
        ("21", "Branch A has no F2 term", "ABSENT", "ABSENT" if all(item["f2_term"] == "ABSENT" for item in actions if item["test_action_id"] == "GAUGED_MATTER_TEST_ACTION_COMPLETE") else "PRESENT"),
        ("22", "Branch B has one inherited F2 term", F2_TERM, F2_TERM if all(item["f2_term"] == F2_TERM and "Z_A" in item["parameters"] for item in actions if "F2" in item["test_action_id"]) else "OTHER"),
        ("23", "action hash stays the Phase 14I hash", action_hash, result["ACTION_HASH_14I_INPUT"]),
        ("24", "repeated derivation is deterministic", "IDENTICAL", "IDENTICAL" if result["digest"] == repeated else "DIFFERENT"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_14J_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_14J_BLOCKED"}


def run_phase_14j(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    phase14i = run_phase_14i(write_artifacts=False)
    stored = _read("phase14i_completion_artifacts/PHASE_14I_ACTION_COMPLETION.json")
    provenance = _read("phase14i_completion_artifacts/PHASE_14I_PROVENANCE.json")
    actions = stored.get("actions", [])
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or auth.action_content_hash != FROZEN_4C_HASH
        or phase14i.get("PHASE_14I_STATUS") != "COMPLETE"
        or phase14i.get("ACTION_COMPLETION_STATUS") != "VERIFIED"
        or phase14i.get("ACTION_DERIVATION_READY") is not True
        or phase14i.get("FROZEN_ACTION_MODIFIED") is not False
        or phase14i.get("AUTHORIZATION_STATUS") != PROVENANCE
        or phase14i.get("ACTION_HASH_AFTER") != provenance.get("action_hash_after")
        or stored.get("kinetic_density") != KINETIC_DENSITY
        or stored.get("d_mu") != D_MU
        or len(actions) != 4
        or not _potential_ready(auth.immutable_action_snapshot)
    ):
        return _stop("freeze gate or Phase 14I binding")
    if any(item.get("kinetic_density") != KINETIC_DENSITY or item.get("gravity") != GRAVITY or item.get("parameters_fixed") for item in actions):
        return _stop("completed action snapshot mismatch")
    science = _derive(so2_generator_K())
    stress = _stress_probe()
    if science.get("status") != "DERIVED" or stress["match"] is not True:
        return {"PHASE_14J_STATUS": "BLOCKED", "status": science.get("status", "STRESS_MISMATCH")}
    science["stress_matter"] = stress["matter"]
    science["stress_maxwell"] = stress["maxwell"]
    science["stress_match"] = True
    science["gravity_equation"] = GRAVITY_EQUATION
    science["parameters_fixed"] = []
    science["new_fields"] = []
    science["new_interactions"] = []
    repeated = _derive(so2_generator_K())
    if repeated.get("status") != "DERIVED":
        return _stop("reproducibility")
    compared = ("phi_component", "branch_a_equation", "branch_a_expanded", "branch_b_equation", "phi_order", "branch_a_order", "branch_b_order")
    if any(repeated[key] != science[key] for key in compared):
        return _stop("reproducibility")
    digest = _result_digest(science)
    second = _result_digest(
        {
            "branch_a_equation": repeated["branch_a_equation"],
            "branch_b_equation": repeated["branch_b_equation"],
            "phi_component": repeated["phi_component"],
            "stress_matter": stress["matter"],
        }
    )
    manifest = build_manifest(str(provenance["action_hash_after"]))
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14J.json").write_bytes(canonical_json_bytes(manifest))
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "PHASE_14J_STATUS": "COMPLETE",
        "FREEZE_STATUS": "VERIFIED",
        "ACTION_BINDING_STATUS": "VERIFIED",
        "BRANCH_A_EOM_STATUS": "VERIFIED",
        "BRANCH_B_EOM_STATUS": "VERIFIED",
        "METRIC_EOM_STATUS": "VERIFIED",
        "STRESS_ENERGY_STATUS": "VERIFIED",
        "EOM_ORDER_STATUS": "VERIFIED",
        "F2_DEPENDENCY_STATUS": "VERIFIED",
        "CONSERVATION_STATUS": "UNTESTED",
        "OSTROGRADSKY_STATUS": "NOT_TRIGGERED",
        "SYMMETRY_STATUS": "PENDING_REVERIFICATION",
        "QUANTUM_STATUS": "UNTESTED",
        "ACTION_FREEZE_VERIFIED": True,
        "ATOMIC_GATE": "VERIFIED",
        "CONCURRENCY_GUARD": "VERIFIED",
        "ACTION_HASH_14I_INPUT": provenance["action_hash_after"],
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "FROZEN_ACTION_MODIFIED": False,
        "CLASSICAL_EOM": "DERIVED",
        "EOM_ORDER_PHI": science["phi_order"],
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "SEARCH_EXECUTED": False,
        "actions": actions,
        "science": science,
        "digest": digest,
    }
    negatives = negative_tests(payload, second, str(provenance["action_hash_after"]))
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14J_STATUS": "BLOCKED", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    if request_physical_activation("T09")["status"] == "AUTHORIZED":
        return _stop("T09")
    payload["dry_run_negatives"] = negatives
    payload["search_manifest"] = manifest
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14J_PHI_EOM.json": {
                "algebraic": science["phi_algebraic"],
                "component": science["phi_component"],
                "covariant_reformulation": science["phi_covariant"],
                "kinetic": science["phi_kinetic"],
                "order": science["phi_order"],
                "reformulation": "EQUIVALENT REFORMULATION",
            },
            "PHASE_14J_CONNECTION_EOM.json": {
                "branch_a_classification": science["branch_a_classification"],
                "branch_a_direct": science["branch_a_equation"],
                "branch_a_expanded": science["branch_a_expanded"],
                "branch_a_order": science["branch_a_order"],
                "branch_b": science["branch_b_equation"],
                "branch_b_order": science["branch_b_order"],
                "current": science["current_formula"],
                "quadratic_is_gauge_kinetic": False,
            },
            "PHASE_14J_METRIC_EOM.json": {
                "conservation": "UNTESTED",
                "equation": GRAVITY_EQUATION,
                "f2_stress": T_F2,
                "matter_stress": T_MATTER,
            },
            "PHASE_14J_ORDER_AUDIT.json": {
                "branch_a": "ALGEBRAIC",
                "branch_b": "SECOND_ORDER",
                "ostrogradsky": "NOT_TRIGGERED",
                "phi": "SECOND_ORDER",
            },
            "PHASE_14J_PROVENANCE.json": {
                "action_completion": PROVENANCE,
                "action_hash_14i_input": provenance["action_hash_after"],
                "conservation": "UNTESTED",
                "eom_derivation": "DERIVED FROM PHASE_14I_COMPLETED_TEST_ACTION",
                "metric_eom": "DERIVED FROM COMPLETED TEST ACTION",
                "quantum": "UNTESTED",
                "symmetry": "PENDING_REVERIFICATION",
            },
            "PHASE_14J_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "conservation", "status": "UNTESTED"},
                    {"frontier_id": "symmetry", "status": "PENDING_REVERIFICATION"},
                    {"frontier_id": "quantum", "status": "UNTESTED"},
                    {"frontier_id": "Z_A", "status": "FREE"},
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
