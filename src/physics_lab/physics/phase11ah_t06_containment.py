"""Phase 11AH.1: containment audit for T06, F proportional to Phi.

The scan reads the recorded equations, the Z_2 moduli class, Bianchi
identities, and the frozen field definitions. It does not add a relation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import phase4c_action_document, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase5c_gauging import _field_strength_invariant
from physics_lab.physics.phase9_internal_gap import _bianchi_coverage
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import synthesis_identities
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import artifact_dir as phase11ae4_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import run_phase_11AE_4_synthesis
from physics_lab.physics.phase11o_gravity_matter import artifact_dir as phase11o_artifact_dir

__all__ = [
    "CLOSURE_TARGET",
    "run_containment_audit_T06",
]

PHASE = "PHASE_11AH.1"
CLOSURE_TARGET = "PROPORTIONALITY_DERIVED"


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ah_artifacts"


def _probe(name: str, found: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe": name,
        "found": found,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "evidence": evidence,
        "closure_target_used_as_filter": False,
    }


def _forced_proportion(left: Any, right: Any) -> bool:
    """True only when left and right are the same up to one field-independent factor."""
    factor = sp.symbols("k")
    solved = sp.solve(sp.Eq(left, factor * right), factor)
    if len(solved) != 1:
        return False
    value = sp.simplify(solved[0])
    if value == 0 or value.free_symbols:
        return False
    return bool(sp.simplify(left - value * right) == 0)


def _mentions_both(text: str) -> bool:
    lowered = text.lower()
    has_f = "f_mu" in lowered or "f^{" in lowered or "f_x" in lowered or "f_phi" in lowered
    has_target = "phi" in lowered or "lam_a" in lowered or "lam_b" in lowered or "lambda" in lowered
    return has_f and has_target


def _algebraic_proportion(text: str) -> bool:
    """A differential equation is not an algebraic identification."""
    if text.count("=") != 1:
        return False
    if any(token in text for token in ("D_mu", "nabla", "partial", "G_mu")):
        return False
    left, right = text.split("=")
    return _mentions_both(left + " " + right) and (
        ("Phi" in left and "F" in right) or ("Phi" in right and "F" in left)
    )


def _scan(vacuum: dict[str, Any]) -> list[dict[str, Any]]:
    rows = json.loads((phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json").read_text(encoding="utf-8"))
    derived_rows = [row for row in rows if str(row.get("provenance", "")).startswith("DERIVED")]
    linked = [row["EOM"] for row in derived_rows if _mentions_both(str(row.get("EOM", "")))]
    eom_probe = _probe(
        "eom_4d",
        any(_algebraic_proportion(text) for text in linked),
        {
            "derived_row_count": len(derived_rows),
            "equations_linking_F_and_Phi": linked,
            "phi_equation": "Z D_mu D^mu Phi = (c_H H_int + kappa I) Phi",
            "gauge_equation_present": any("F^{" in str(row.get("EOM", "")) for row in derived_rows),
        },
    )

    surviving = vacuum["synthesis"]["surviving_class"]
    moduli_text = json.dumps(surviving)
    moduli_probe = _probe(
        "z2_moduli",
        _mentions_both(moduli_text),
        {
            "symmetry": vacuum["synthesis"]["symmetry"],
            "V_adm": vacuum["synthesis"]["V_adm"],
            "surviving_class": surviving,
            "class_mentions_F": "F" in moduli_text,
        },
    )

    bianchi = _bianchi_coverage()
    gravity = json.loads(
        (phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json").read_text(encoding="utf-8")
    )["bianchi_analysis"]
    bianchi_text = " ".join(str(value) for value in {**bianchi, **gravity}.values())
    bianchi_probe = _probe(
        "bianchi_identity",
        bool(bianchi.get("new_parameter_relation")) and _mentions_both(bianchi_text),
        {
            "bianchi_holds_identically": bianchi["bianchi_holds_identically"],
            "new_parameter_relation": bianchi["new_parameter_relation"],
            "geometric_identity": gravity.get("geometric_identity"),
            "constrains_lambda": bianchi["constrains_c0_c1_Z_lambda_ZA"],
        },
    )

    document = phase4c_action_document()
    strength = _field_strength_invariant()
    identities = synthesis_identities()
    t, x = sp.symbols("t x", real=True)
    connection_1 = sp.Function("Aconn1")(t, x)
    connection_0 = sp.Function("Aconn0")(t, x)
    phi = sp.Function("Phi")(t, x)
    curvature = sp.diff(connection_1, t) - sp.diff(connection_0, x)
    order_x, order_phi, lam_a, lam_b = sp.symbols("F_X F_phi lam_a lam_b")
    forced = any(
        _forced_proportion(left, right)
        for left, right in (
            (curvature, phi),
            (order_x, order_phi),
            (order_x, lam_a),
            (order_x, lam_b),
            (order_phi, lam_a),
            (order_phi, lam_b),
        )
    )
    definition_probe = _probe(
        "field_definitions",
        forced,
        {
            "frozen_field_ids": [field["id"] for field in document["fields"]],
            "F_definition": strength["definition"],
            "F_invariant_as_curvature": strength["invariant"],
            "F_X_not_F_phi": identities["F_X_not_F_phi"],
            "lam_a_provenance": "INPUT",
            "lam_b_provenance": "INPUT",
            "proportion_forced_by_definitions": forced,
        },
    )
    return [eom_probe, moduli_probe, bianchi_probe, definition_probe]


def run_containment_audit_T06(
    closure_target: str | None = None,
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    """Scan for a frozen derivation of F proportional to Phi.

    PROPORTIONALITY_DERIVED is logged before the scan.
    """
    if closure_target is not None and closure_target != CLOSURE_TARGET:
        return {
            "status": "CLOSURE_CRITERION_REFUSED",
            "PHASE": PHASE,
            "topic": "T06: F proportional to Phi",
            "rule": "Target-Blind rule",
            "scanned": False,
            "provenance_log": [
                {
                    "entry": "Pre-Execution Closure Criterion",
                    "rule": "Target-Blind rule",
                    "closure_target": None,
                    "accepted": False,
                    "logged_before_logical_execution": True,
                    "post_hoc_validation": False,
                }
            ],
            "new_parameter_count": 0,
            "T06_activated": False,
        }
    closure_entry = {
        "entry": "Pre-Execution Closure Criterion",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "logged_before_logical_execution": True,
        "post_hoc_validation": False,
        "accepted": True,
    }
    verification = verify_phase4c_action_freeze()
    digest = verification.get("action_content_hash")
    if verification.get("status") != "VERIFIED" or digest != EXPECTED_FROZEN_HASH:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [closure_entry],
            "detail": "frozen 4C hash",
            "new_parameter_count": 0,
            "T06_activated": False,
        }
    parents = {
        "11AD": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
        "EOM": phase10b8_artifact_dir() / "EOM_FIELD_TABLE.json",
        "11O": phase11o_artifact_dir() / "PHASE_11O_GRAVITY_MATTER.json",
        "11AE4": phase11ae4_artifact_dir() / "PHASE_11AE4_SYNTHESIS.json",
    }
    before = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    decision = json.loads(parents["11AD"].read_text(encoding="utf-8")).get("decision_map") or {}
    if decision.get("T06") != "REQUIRES_EXPLICIT_ASSUMPTION":
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "scanned": False,
            "provenance_log": [closure_entry],
            "detail": "parent T06 decision",
            "new_parameter_count": 0,
            "T06_activated": False,
        }
    document_before = canonical_json_bytes(phase4c_action_document())
    vacuum = run_phase_11AE_4_synthesis(write_artifacts=False)
    if vacuum.get("PROGRAM_CLOSURE_STATUS") != "CLOSED_UNDER_DECLARED_SCOPE" or vacuum.get("synthesis", {}).get("symmetry") != "Z_2":
        return {
            "status": "STOP",
            "PHASE": PHASE,
            "detail": "Z_2 moduli class is not the closed Phase 11AE.4 record",
            "scanned": False,
            "provenance_log": [closure_entry],
            "new_parameter_count": 0,
            "T06_activated": False,
        }
    probes = _scan(vacuum)
    document_after = canonical_json_bytes(phase4c_action_document())
    after = {name: path.read_bytes() for name, path in parents.items() if path.is_file()}
    if document_after != document_before or after != before:
        return {
            "status": "CONTAINMENT_AUDIT_INTEGRITY_FAILURE",
            "PHASE": PHASE,
            "detail": "parent artifact mutated",
            "scanned": False,
            "new_parameter_count": 0,
            "T06_activated": False,
        }
    found = any(item["found"] for item in probes)
    provenance_log = [closure_entry, *probes]
    payload = {
        "status": "OK",
        "PHASE": PHASE,
        "topic": "T06: F proportional to Phi",
        "rule": "Target-Blind rule",
        "closure_target": CLOSURE_TARGET,
        "closure_target_used_as_filter": False,
        "scanned": True,
        "action_content_hash": digest,
        "probes": probes,
        "provenance_log": provenance_log,
        "Provenance": "DERIVED" if found else "NOT_FOUND",
        "PROPORTIONALITY_STATUS": "DERIVED" if found else "NOT_FOUND",
        "T06_activated": False,
        "new_parameter_count": 0,
        "frozen_action_modified": False,
        "definitions_modified": False,
    }
    if write_artifacts:
        destination = artifact_dir() / "PHASE_11AH_T06_CONTAINMENT.json"
        forbidden = (
            phase11ad_artifact_dir().resolve(),
            phase11ae4_artifact_dir().resolve(),
            phase10b8_artifact_dir().resolve(),
            phase11o_artifact_dir().resolve(),
        )
        if any(destination.resolve().is_relative_to(root) for root in forbidden):
            raise RuntimeError("FEEDBACK_LOOP_DETECTED")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            canonical_json_bytes(
                {
                    "topic": payload["topic"],
                    "Provenance": payload["Provenance"],
                    "log": provenance_log,
                }
            )
            + b"\n"
        )
    return payload
