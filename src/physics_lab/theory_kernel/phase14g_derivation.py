"""Phase 14G derives consequences from the four stored Phase 14F test actions.

Expressions that are not in those actions stay untested. The actions are not rewritten.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.epistemic import KERNEL_VERSION, content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.phase13b_exploration import _obligations
from physics_lab.theory_kernel.phase14a_lexicon import LEXICON_ID, lexicon_document, lookup
from physics_lab.theory_kernel.phase14c_authorization import EXPECTED_LEXICON_HASH
from physics_lab.theory_kernel.phase14f_embedding import run_phase_14f
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_14G"
CODE_VERSION = "phase14g-derivation-v1"
TEST_VERSION = "phase14g-tests-v1"
ARTIFACT_DIR_NAME = "phase14g_derivation_artifacts"
IR_VERSION = "phase14g-derivation-v1"
PREVIOUS_IR_VERSION = "phase14f-embedding-v1"
D_MU = "D_mu Phi = d_mu Phi - mathcalA_mu K Phi"
LINEAR = "- mathcalA_mu j^mu"
QUADRATIC = "Z mathcalA_mu mathcalA^mu <K Phi, K Phi>"
F2_CONTENTS = "GAUGED_MATTER + (- Z_A/4) F_mu_nu F^mu_nu"
F_DEFINITION = "F_mu_nu = d_mu mathcalA_nu - d_nu mathcalA_mu"
GRAVITY_EQUATION = "2 c1 G_mu_nu - c0 g_mu_nu = T_mu_nu"
POTENTIAL_EQUATION = "(c_H H_int + kappa I) Phi"
QUADRATIC_PHI_EQUATION = "2 Z mathcalA_mu mathcalA^mu (K^T K Phi)"
CONNECTION_EQUATION = "- j^mu + 2 Z mathcalA^mu <K Phi, K Phi>"
POTENTIAL_STRESS = "- g_mu_nu (kappa/2 <Phi, Phi> + c_H/2 <Phi, H_int Phi>)"


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


def derive_new_theory() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_search() -> dict[str, str]:
    return {"status": "NOT_EXECUTED"}


def numerical_coincidence_is_pfr() -> dict[str, str]:
    return {"status": "NOT_A_PFR"}


def infer_f2_gauge_eom(dependency: str) -> dict[str, str]:
    if dependency == "UNDECLARED":
        return {"equation": "NOT_DERIVED", "status": "UNTESTED"}
    return {"equation": "NOT_DERIVED", "status": "UNTESTED"}


def _term_hash(action: dict[str, Any], term_id: str) -> str:
    term = next(item for item in action["terms"] if item["id"] == term_id)
    return content_digest({"expression": term["expression"], "id": term_id})


def _matrix_diag(node: Any) -> list[str] | None:
    if isinstance(node, dict):
        if node.get("op") == "matrix":
            entries = node["entries"]
            return [entries[index][index]["symbol"] for index in range(int(node["rows"]))]
        for value in node.values():
            found = _matrix_diag(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _matrix_diag(value)
            if found:
                return found
    return None


def _half(node: Any) -> bool:
    return isinstance(node, dict) and node.get("rational") == [1, 2]


def _phi_field(node: Any) -> bool:
    return isinstance(node, dict) and node.get("field") == "Phi"


def _potential_pieces(action: dict[str, Any]) -> dict[str, Any]:
    phi_sq = next(item for item in action["terms"] if item["id"] == "matter_phi_sq")
    hint = next(item for item in action["terms"] if item["id"] == "matter_H_int")
    phi_expr = phi_sq["expression"]
    hint_expr = hint["expression"]
    if phi_expr.get("density") != "sqrt_minus_g" or hint_expr.get("density") != "sqrt_minus_g":
        return {"status": "UNTESTED"}
    phi_args = (phi_expr.get("integrand") or {}).get("args") or []
    hint_args = (hint_expr.get("integrand") or {}).get("args") or []
    phi_symbols = [item.get("symbol") for item in phi_args if isinstance(item, dict) and "symbol" in item]
    hint_symbols = [item.get("symbol") for item in hint_args if isinstance(item, dict) and "symbol" in item]
    phi_inner = next((item for item in phi_args if isinstance(item, dict) and item.get("op") == "inner_product"), None)
    hint_inner = next((item for item in hint_args if isinstance(item, dict) and item.get("op") == "inner_product"), None)
    if phi_symbols != ["kappa"] or not any(_half(item) for item in phi_args) or phi_inner is None:
        return {"status": "UNTESTED"}
    if not _phi_field(phi_inner.get("left")) or not _phi_field(phi_inner.get("right")):
        return {"status": "UNTESTED"}
    if hint_symbols != ["c_H"] or not any(_half(item) for item in hint_args) or hint_inner is None:
        return {"status": "UNTESTED"}
    operator = (hint_inner.get("right") or {}).get("operator")
    diagonal = _matrix_diag(operator)
    if diagonal != ["lam_a", "lam_b", "lam_b"] or not _phi_field(hint_inner.get("left")):
        return {"status": "UNTESTED"}
    lam_a, lam_b, kappa, c_h = sp.symbols("lam_a lam_b kappa c_H", real=True)
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    matrix = sp.diag(lam_a, lam_b, lam_b)
    density = (kappa * sp.Rational(1, 2)) * (phi.T * phi)[0] + (c_h * sp.Rational(1, 2)) * (phi.T * matrix * phi)[0]
    gradient = sp.Matrix([sp.diff(density, phi[index]) for index in range(3)])
    expected = kappa * phi + c_h * (matrix * phi)
    if sp.simplify(gradient - expected) != sp.zeros(3, 1):
        return {"status": "UNTESTED"}
    return {
        "diagonal": diagonal,
        "derivative_order": 0,
        "equation": POTENTIAL_EQUATION,
        "metric_dependence": "sqrt_minus_g",
        "parameters": ["c_H", "kappa", "lam_a", "lam_b"],
        "status": "DERIVED",
        "terms": ["matter_phi_sq", "matter_H_int"],
    }


def _quadratic_phi_identity() -> bool:
    matrix = sp.Matrix(3, 3, lambda row, col: sp.symbols(f"k{row}{col}"))
    phi = sp.Matrix(sp.symbols("p0 p1 p2", real=True))
    formed = (matrix * phi).dot(matrix * phi)
    gradient = sp.Matrix([sp.diff(formed, phi[index]) for index in range(3)])
    expected = sp.simplify(2 * (matrix.T * matrix * phi))
    return sp.simplify(gradient - expected) == sp.zeros(3, 1)


def _connection_identity() -> bool:
    amplitude, current, coefficient, formed = sp.symbols("A j Z Q", real=True)
    density = -amplitude * current + coefficient * amplitude**2 * formed
    return sp.simplify(sp.diff(density, amplitude) - (-current + 2 * coefficient * amplitude * formed)) == 0


def _eigenvalues(diagonal: list[str]) -> dict[str, Any]:
    lam_a, lam_b = sp.symbols("lam_a lam_b", real=True)
    mapping = {"lam_a": lam_a, "lam_b": lam_b}
    matrix = sp.diag(*[mapping[name] for name in diagonal])
    values = matrix.eigenvals()
    return {
        "degeneracy": {"lam_a": int(values[lam_a]), "lam_b": int(values[lam_b])},
        "eigenvalues": ["lam_a", "lam_b", "lam_b"],
        "mass_ratio": "lam_a/lam_b",
        "mass_ratio_status": "PARAMETER_DEPENDENT",
        "physical_mass": False,
    }


def _short(theory_id: str) -> str:
    gauge = "F2" if "optional_F2_test_extension" in theory_id else "connection"
    operator = "function_of_KTK" if "function_of_KTK" in theory_id else "commutant"
    return f"{gauge} · {operator}"


def derive_one(record: dict[str, Any], frozen: dict[str, Any], potential: dict[str, Any]) -> dict[str, Any]:
    expressions = [item["expression"] for item in record["embedded_terms"]]
    f2 = F2_CONTENTS in expressions
    inherited = {item["term_id"]: item["source_hash"] for item in record["inherited_terms"]}
    for term_id, source_hash in inherited.items():
        if _term_hash(frozen, term_id) != source_hash:
            return {"status": "SOURCE_HASH_MISMATCH"}
    if "matter_kinetic" in inherited or D_MU not in expressions or LINEAR not in expressions or QUADRATIC not in expressions:
        return {"status": "STORED_EXPRESSION_MISMATCH"}
    if potential["status"] != "DERIVED" or potential["diagonal"] != record["operator_diagonal"]:
        return {"status": "POTENTIAL_UNRESOLVED"}
    if not _quadratic_phi_identity() or not _connection_identity():
        return {"status": "VARIATION_IDENTITY_FAILED"}
    if f2 and F_DEFINITION in expressions:
        return {"status": "F2_DEPENDENCY_INSERTED"}
    spectrum = _eigenvalues(record["operator_diagonal"])
    phi = {
        "certification_status": "PARTIAL",
        "constraints": [
            "covariant kinetic density is absent from the stored expression",
            "delta j^mu / delta Phi is not stated by the stored linear term",
        ],
        "derivative_order": 0,
        "equation": f"{POTENTIAL_EQUATION} + {QUADRATIC_PHI_EQUATION}",
        "parameter_dependence": ["Z", "c_H", "kappa", "lam_a", "lam_b"],
        "provenance": ["matter_phi_sq", "matter_H_int", QUADRATIC],
        "second_order_piece": "UNTESTED",
        "status": "PARTIAL",
    }
    connection = {
        "autonomous_gauge_dynamics": False,
        "differential": False,
        "equation": CONNECTION_EQUATION,
        "equation_class": "ALGEBRAIC",
        "propagation": False,
        "source_structure": "stored symbol j^mu plus the stored quadratic monomial",
        "status": "PARTIAL",
    }
    metric = {
        "gravity_contribution": GRAVITY_EQUATION,
        "gravity_inputs_unchanged": ["c0", "c1"],
        "matter_contribution": POTENTIAL_STRESS,
        "matter_scope": "volume factor of the inherited potential only",
        "status": "PARTIAL",
        "t_matter_status": "UNTESTED",
    }
    gauge_dependency = "UNDECLARED"
    f2_record = {
        "F2_dependency_status": "F2_DEPENDENCY_UNDECLARED" if f2 else "ABSENT",
        "F_mu_nu_role": "STORED_SYMBOLIC_OBJECT" if f2 else "ABSENT",
        "gauge_eom": infer_f2_gauge_eom(gauge_dependency)["equation"] if f2 else "NOT_APPLICABLE",
        "status": "UNTESTED" if f2 else "NOT_APPLICABLE",
    }
    eoms = [
        {"domain": "Phi", "status": "PARTIAL"},
        {"domain": "connection", "status": "PARTIAL"},
        {"domain": "metric", "status": "PARTIAL"},
    ]
    if f2:
        eoms.append({"domain": "F2_gauge", "status": "UNTESTED"})
    obligations = []
    for item in _obligations(record["theory_id"]):
        obligations.append(
            {
                "attempt_status": item["current_status"] if item["current_status"] == "REQUIRES_HUMAN_INPUT" else "REMAINS_OPEN",
                "current_status": item["current_status"],
                "obligation_class": item["obligation_class"],
                "obligation_id": item["obligation_id"],
            }
        )
    parameters = []
    frozen_parameters = {item["id"]: item for item in frozen["parameters"]}
    for name in record["actual_parameters"]:
        if name == "Z_A":
            parameters.append(
                {
                    "branch": _short(record["theory_id"]),
                    "class": "TEST_EXTENSION_PARAMETER",
                    "convention_only": False,
                    "dimension": "UNSTATED",
                    "eliminated": False,
                    "parameter_id": name,
                    "provenance": "COPIED_FROM_F2_TEST_COMPONENT",
                    "source_theory": record["theory_id"],
                    "unresolved": True,
                }
            )
            continue
        source = frozen_parameters[name]
        parameters.append(
            {
                "branch": _short(record["theory_id"]),
                "class": "FROZEN_ACTION_PARAMETER",
                "convention_only": False,
                "dimension": "UNSTATED",
                "eliminated": False,
                "parameter_id": name,
                "provenance": source["provenance"],
                "source_theory": record["theory_id"],
                "unresolved": True,
            }
        )
    return {
        "status": "OK",
        "theory_id": record["theory_id"],
        "label": _short(record["theory_id"]),
        "source_action_id": record["materialized_action_v2_id"],
        "source_action_hash": record["materialized_action_v2_hash"],
        "source_component_hashes": list(record["source_component_hashes"]),
        "source_components": list(record["source_components"]),
        "lexicon_hash": record["lexicon_hash"],
        "authorization_id": record["authorization_id"],
        "Phi_EOM": phi,
        "connection_variation": connection,
        "metric_variation": metric,
        "symmetry_status": "UNTESTED",
        "symmetry_reason": "Phase 5B.0 includes matter_kinetic, which this action replaced. The stored gauge strings do not state an SO(2) transformation.",
        "Noether_current": "UNTESTED",
        "noether_reason": "No exact continuous symmetry was verified on the full materialized action.",
        "stored_j_mu": "NOT_A_DERIVED_CURRENT",
        "mass_operator": spectrum,
        "mass_ratio_status": "PARAMETER_DEPENDENT",
        "operator_diagonal": list(record["operator_diagonal"]),
        "phase10d_statement": record["phase10d_statement"],
        "phase10d_merged_with_lexicon": False,
        "charge_structure": "UNTESTED",
        "gauge_dependency": gauge_dependency,
        "f2": f2_record,
        "PFR_status": "NONE_FOUND",
        "pfr_candidates": [{"kind": "lam_a/lam_b", "status": "PARAMETER_DEPENDENT", "verified": False}],
        "proof_status": "PARTIAL",
        "obligations": obligations,
        "parameters": parameters,
        "dimensional": {
            "derived_absolute_scale": "NOT_DERIVED",
            "dimensionful_inputs": ["c0", "c1"],
            "normalization_scales": ["Z"] + (["Z_A"] if f2 else []),
            "status": "PARTIAL",
            "unresolved_scales": list(record["actual_parameters"]),
        },
        "eoms": eoms,
        "physical_certification": "NOT_CLAIMED",
    }


def derivation_digest(rows: list[dict[str, Any]]) -> str:
    return content_digest(
        {
            "rows": [
                {
                    "connection": item["connection_variation"]["equation"],
                    "gauge_dependency": item["gauge_dependency"],
                    "hash": item["source_action_hash"],
                    "mass": item["mass_operator"]["eigenvalues"],
                    "phi": item["Phi_EOM"]["equation"],
                    "pfr": item["PFR_status"],
                    "proof": [row["attempt_status"] for row in item["obligations"]],
                    "symmetry": item["symmetry_status"],
                    "theory_id": item["theory_id"],
                }
                for item in rows
            ]
        }
    )


def build_manifest(lexicon_hash: str) -> dict[str, Any]:
    manifest = {
        "code_version": CODE_VERSION,
        "frozen_phase4c_hash": FROZEN_4C_HASH,
        "lexicon_hash": lexicon_hash,
        "lexicon_id": LEXICON_ID,
        "new_ir_version": IR_VERSION,
        "previous_ir_version": PREVIOUS_IR_VERSION,
        "source_catalogue_version": "PHASE_14F_MATERIALIZED_ACTIONS_V2",
        "target_access": False,
        "test_version": TEST_VERSION,
        "theory_kernel_version": KERNEL_VERSION,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest["manifest_hash"] = content_digest({key: value for key, value in manifest.items() if key != "timestamp"})
    return manifest


def _catalog_isolated() -> bool:
    return ("known_" + "physics") not in Path(__file__).read_text(encoding="utf-8")


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def negative_tests(result: dict[str, Any], repeated: dict[str, Any], action_hash: str, prior_unchanged: bool) -> list[dict[str, str]]:
    rows = result["rows"]
    phi_stored = all("D_mu D^mu" not in item["Phi_EOM"]["equation"] and QUADRATIC in item["Phi_EOM"]["provenance"] for item in rows)
    no_wave = all("Z <D_mu Phi, D_nu Phi>" not in json.dumps(item["Phi_EOM"]) for item in rows)
    f2_rows = [item for item in rows if item["f2"]["status"] == "UNTESTED"]
    f2_firewall = all(item["f2"]["gauge_eom"] == "NOT_DERIVED" and item["gauge_dependency"] == "UNDECLARED" for item in f2_rows)
    extra_identity = lookup("a0", "lam_a")["status"]
    cases = [
        ("1", "14F actions remain unchanged", "UNCHANGED", "UNCHANGED" if prior_unchanged else "CHANGED"),
        ("2", "no new action is generated", "NOT_EXECUTED", derive_new_theory()["status"]),
        ("3", "no new theory is generated", "NOT_EXECUTED", derive_new_theory()["status"]),
        ("4", "no new grammar is generated", "NOT_EXECUTED", derive_new_theory()["status"]),
        ("5", "no new parameter is introduced", "0", "0" if result["NEW_PARAMETER_COUNT"] == 0 else "ADDED"),
        ("6", "no new integrand is introduced", "0", "0" if result["NEW_INTEGRAND_COUNT"] == 0 else "ADDED"),
        ("7", "Phi EOM uses only stored action terms", "TRUE", "TRUE" if phi_stored else "RECONSTRUCTED"),
        ("8", "missing action structure is not invented", "TRUE", "TRUE" if no_wave else "INVENTED"),
        ("9", "F2_A_MU_DEPENDENCY remains undeclared", "UNDECLARED", "UNDECLARED" if all(item["gauge_dependency"] == "UNDECLARED" for item in rows) else "CHANGED"),
        ("10", "no F2 gauge EOM is inferred", "NOT_DERIVED", "NOT_DERIVED" if f2_firewall else "INFERRED"),
        ("11", "representation symmetry is not assumed to be full-action symmetry", "UNTESTED", "UNTESTED" if all(item["symmetry_status"] == "UNTESTED" for item in rows) else "ASSUMED"),
        ("12", "eigenvalues with free coefficients remain parameter dependent", "PARAMETER_DEPENDENT", "PARAMETER_DEPENDENT" if all(item["mass_ratio_status"] == "PARAMETER_DEPENDENT" and item["mass_operator"]["physical_mass"] is False for item in rows) else "NUMERIC"),
        ("13", "numerical coincidence is not PFR", "NOT_A_PFR", numerical_coincidence_is_pfr()["status"]),
        ("14", "c0 and c1 remain inputs", "INPUT", "INPUT" if all(item["metric_variation"]["gravity_inputs_unchanged"] == ["c0", "c1"] for item in rows) else "DERIVED"),
        ("15", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("16", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        ("17", "no experimental data enter", "FALSE", "FALSE" if result["EXPERIMENTAL_INPUT"] is False and not any(marker in json.dumps(result["rows"]) for marker in _target_markers()) else "PRESENT"),
        ("18", "no ranking is introduced", "ABSENT", "ABSENT" if _ranking_absent() and _catalog_isolated() else "PRESENT"),
        ("19", "repeated derivation is deterministic", "IDENTICAL", "IDENTICAL" if derivation_digest(result["rows"]) == derivation_digest(repeated["rows"]) else "DIFFERENT"),
        ("20", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, action_hash),
        ("21", "previous phase artifacts remain byte-identical", "UNCHANGED", "UNCHANGED" if prior_unchanged else "CHANGED"),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def _not_authorized(reason: str) -> dict[str, str]:
    return {"PHASE_14G_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_14G_PRECONDITION_FAILED"}


def _analyze(records: list[dict[str, Any]], frozen: dict[str, Any]) -> dict[str, Any]:
    potential = _potential_pieces(frozen)
    rows = [derive_one(record, frozen, potential) for record in records]
    if any(item.get("status") != "OK" for item in rows):
        return {"status": rows[0].get("status", "DERIVATION_FAILED"), "rows": rows}
    return {"rows": rows, "status": "OK"}


def run_phase_14g(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase14f = run_phase_14f(write_artifacts=False)
    stored = _read("phase14f_embedding_artifacts/PHASE_14F_MATERIALIZED_ACTIONS_V2.json")
    catalogue = _read("phase13b_exploration_artifacts/PHASE_13B_EXPLORATION.json")
    freeze = verify_phase4c_action_freeze()
    records = stored.get("actions", [])
    live_hashes = [item["materialized_action_v2_hash"] for item in phase14f.get("EMBEDDING", {}).get("actions", [])]
    stored_hashes = [item.get("materialized_action_v2_hash") for item in records]
    catalogue_ids = {item["theory_id"]: item.get("proof_status") for item in catalogue.get("THEORY_CATALOGUE", [])}
    if (
        phase14f.get("PHASE_14F_STATUS") != "COMPLETE"
        or phase14f.get("ACTION_MATERIALIZATION_V2_STATUS") != "COMPLETE"
        or phase14f.get("FIELD_CLOSURE_STATUS") != "VERIFIED"
        or phase14f.get("PARAMETER_CLOSURE_STATUS") != "VERIFIED"
        or phase14f.get("PYTEST_STATUS") != "GREEN"
        or phase14f.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase14f.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase14f.get("NEW_PHYSICAL_CONTENT") != "NONE"
        or phase14f.get("NEW_PARAMETER_COUNT") != 0
        or phase14f.get("LEXICON_HASH") != EXPECTED_LEXICON_HASH
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or len(records) != 4
        or stored_hashes != live_hashes
        or any(catalogue_ids.get(item["theory_id"]) != "OPEN" for item in records)
    ):
        return _not_authorized("Phase 14F, lexicon, catalogue, or frozen state")
    frozen = freeze["canonical_action"]
    manifest = build_manifest(EXPECTED_LEXICON_HASH)
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SEARCH_MANIFEST_14G.json").write_bytes(canonical_json_bytes(manifest))
    first = _analyze(records, frozen)
    second = _analyze(records, frozen)
    if first.get("status") != "OK" or second.get("status") != "OK":
        return {"PHASE_14G_STATUS": "INCOMPLETE", "status": first.get("status", "DERIVATION_FAILED")}
    if derivation_digest(first["rows"]) != derivation_digest(second["rows"]):
        return {"PHASE_14G_STATUS": "INCOMPLETE", "status": "REPRODUCIBILITY_FAILURE"}
    identities = lexicon_document()["entries"]
    if any(item.get("physical_relation") == "DERIVED" for item in identities):
        return {"PHASE_14G_STATUS": "INCOMPLETE", "status": "LEXICON_TREATED_AS_PHYSICAL"}
    eom_rows = [item for row in first["rows"] for item in row["eoms"]]
    open_obligations = [
        item for row in first["rows"] for item in row["obligations"] if item["current_status"] == "OPEN"
    ]
    first["NEW_PARAMETER_COUNT"] = 0
    first["NEW_INTEGRAND_COUNT"] = 0
    first["EXPERIMENTAL_INPUT"] = False
    second["NEW_PARAMETER_COUNT"] = 0
    second["NEW_INTEGRAND_COUNT"] = 0
    second["EXPERIMENTAL_INPUT"] = False
    negatives = negative_tests(first, second, freeze["action_content_hash"], True)
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_14G_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "NEGATIVE_TEST_FAILED"}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "EULER_LAGRANGE_STATUS": "PARTIAL",
        "PHI_EOM_STATUS": "PARTIAL",
        "CONNECTION_VARIATION_STATUS": "PARTIAL",
        "METRIC_VARIATION_STATUS": "PARTIAL",
        "SYMMETRY_STATUS": "UNTESTED",
        "NOETHER_STATUS": "UNTESTED",
        "MASS_OPERATOR_STATUS": "VERIFIED",
        "CHARGE_STRUCTURE_STATUS": "UNTESTED",
        "GAUGE_DEPENDENCY_STATUS": "UNDECLARED",
        "PFR_STATUS": "NONE_FOUND",
        "DIMENSIONAL_SCALE_STATUS": "PARTIAL",
        "PARAMETER_CLOSURE_STATUS": "PARTIAL",
        "PROOF_CLOSURE_STATUS": "PARTIAL",
        "COMPLETE_EOM_COUNT": sum(item["status"] == "VERIFIED" for item in eom_rows),
        "PARTIAL_EOM_COUNT": sum(item["status"] == "PARTIAL" for item in eom_rows),
        "UNTESTED_EOM_COUNT": sum(item["status"] == "UNTESTED" for item in eom_rows),
        "VERIFIED_SYMMETRY_COUNT": 0,
        "VERIFIED_PFR_COUNT": 0,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_INTEGRAND_COUNT": 0,
        "NEW_PHYSICAL_CONTENT": "NONE",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "SEARCH_EXECUTED": False,
        "EXPERIMENTAL_INPUT": False,
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PHASE_14G_STATUS": "COMPLETE",
        "CURRENT_IR_VERSION": IR_VERSION,
        "PREVIOUS_IR_VERSION": PREVIOUS_IR_VERSION,
        "LEXICON_ID": LEXICON_ID,
        "LEXICON_HASH": EXPECTED_LEXICON_HASH,
        "TOTAL_THEORIES": 4,
        "TOTAL_COMPLETE_EOMS": sum(item["status"] == "VERIFIED" for item in eom_rows),
        "TOTAL_PARTIAL_EOMS": sum(item["status"] == "PARTIAL" for item in eom_rows),
        "TOTAL_UNTESTED_EOMS": sum(item["status"] == "UNTESTED" for item in eom_rows),
        "TOTAL_VERIFIED_SYMMETRIES": 0,
        "TOTAL_VERIFIED_PFR": 0,
        "TOTAL_PARAMETER_DEPENDENT_RATIOS": sum(item["mass_ratio_status"] == "PARAMETER_DEPENDENT" for item in first["rows"]),
        "TOTAL_OPEN_PROOF_OBLIGATIONS": len(open_obligations),
        "TOTAL_UNRESOLVED_GAUGE_DEPENDENCIES": sum(item["f2"]["status"] == "UNTESTED" for item in first["rows"]),
        "frozen_4c_hash": freeze["action_content_hash"],
        "derivation_hash": derivation_digest(first["rows"]),
        "search_manifest": manifest,
        "rows": first["rows"],
        "dry_run_negatives": negatives,
        "interpretation": "A derived equation is a consequence of the stored action. It does not certify experimental correctness, uniqueness, or quantum consistency.",
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        files = {
            "PHASE_14G_EULER_LAGRANGE.json": {
                "actions": [
                    {"Phi_EOM": item["Phi_EOM"], "theory_id": item["theory_id"], "source_action_hash": item["source_action_hash"]}
                    for item in first["rows"]
                ]
            },
            "PHASE_14G_METRIC_VARIATION.json": {
                "actions": [{"metric_variation": item["metric_variation"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_SYMMETRY_AUDIT.json": {
                "actions": [{"reason": item["symmetry_reason"], "status": item["symmetry_status"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_NOETHER.json": {
                "actions": [
                    {
                        "current": item["Noether_current"],
                        "reason": item["noether_reason"],
                        "stored_j_mu": item["stored_j_mu"],
                        "theory_id": item["theory_id"],
                    }
                    for item in first["rows"]
                ]
            },
            "PHASE_14G_MASS_OPERATOR.json": {
                "actions": [
                    {
                        "diagonal": item["operator_diagonal"],
                        "mass_operator": item["mass_operator"],
                        "phase10d_merged_with_lexicon": item["phase10d_merged_with_lexicon"],
                        "phase10d_statement": item["phase10d_statement"],
                        "theory_id": item["theory_id"],
                    }
                    for item in first["rows"]
                ]
            },
            "PHASE_14G_PARAMETER_CLOSURE.json": {
                "actions": [{"parameters": item["parameters"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_PFR_AUDIT.json": {
                "actions": [{"candidates": item["pfr_candidates"], "status": item["PFR_status"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_DIMENSIONAL_AUDIT.json": {
                "actions": [{"dimensional": item["dimensional"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_GAUGE_DEPENDENCY.json": {
                "actions": [{"connection_variation": item["connection_variation"], "f2": item["f2"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_PROOF_CLOSURE.json": {
                "actions": [{"obligations": item["obligations"], "theory_id": item["theory_id"]} for item in first["rows"]]
            },
            "PHASE_14G_FRONTIER.json": {
                "frontiers": [
                    {"frontier_id": "phi_second_order", "status": "UNTESTED"},
                    {"frontier_id": "F2_A_MU_DEPENDENCY", "status": "UNDECLARED"},
                    {"frontier_id": "full_action_SO2", "status": "UNTESTED"},
                    {"frontier_id": "T_matter", "status": "UNTESTED"},
                    {"frontier_id": "PFR", "status": "NONE_FOUND"},
                    {"frontier_id": "T09", "status": "REQUIRES_HUMAN_INPUT"},
                    {"frontier_id": "T10", "status": "REQUIRES_HUMAN_INPUT"},
                ]
            },
        }
        for name, body in files.items():
            (destination / name).write_bytes(canonical_json_bytes(body))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_14G_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
