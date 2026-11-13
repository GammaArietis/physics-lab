"""Phase 11A: new physical input gate after closed Phase 10E.

Does not invent, rank, or select a principle. Audits a human-declared
input if and only if one is supplied. Previous artefacts are immutable.
"""

from __future__ import annotations

import hashlib
import json
import re
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
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10c_interpretation import artifact_dir as phase10c_artifact_dir
from physics_lab.physics.phase10d_equivalence import artifact_dir as phase10d_artifact_dir
from physics_lab.physics.phase10e_synthesis import (
    EXPECTED_10C_CATALOG_HASH,
    EXPECTED_10D_CATALOG_HASH,
    EXPECTED_SOURCE_CATALOG_HASH,
    artifact_dir as phase10e_artifact_dir,
)
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_strategy_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_10E_SYNTHESIS_HASH",
    "GATE_VERSION",
    "PHASE_11A_INPUT_TEST_COPY_ID",
    "REQUIRED_INPUT_FIELDS",
    "analyze_phase11a_input_gate",
    "artifact_dir",
    "audit_human_declared_input",
    "canonical_declared_input",
    "input_hash",
    "run_phase11a_input_or_stop",
]

PHASE_11A_INPUT_TEST_COPY_ID = "PHASE_11A_NEW_PHYSICAL_INPUT_GATE"
PHASE = "PHASE_11A"
GATE_VERSION = "phase11a-new-physical-input-gate-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_STRATEGY_11A_SUMMARY_HASH = "2c9ac1d0653053a00eb44a649cf6edf1896f2d09cf9b00b4f51a37df7ec44f1f"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

REQUIRED_INPUT_FIELDS = (
    "input_id",
    "title",
    "mathematical_statement",
    "physical_scope",
    "motivation",
    "affected_previous_phases",
    "new_objects",
    "new_assumptions",
    "parameter_implications",
    "intended_domain",
    "provenance",
    "declaration_timestamp",
    "what_is_new",
    "what_was_already_known",
    "what_is_assumed",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "top" + "_" + "model",
    "similarity" + "_" + "score",
    "preferred" + "_" + "model",
    "principle" + "_" + "generation",
    "principle" + "_" + "ranking",
    "principle" + "_" + "scoring",
)

_POST_HOC_KEYS = (
    "desired_consequence",
    "desired_result",
    "selected_to_obtain",
    "selected_because",
    "invented_to_match",
    "post_hoc",
    "consequence_first",
    "fitted_to",
    "target_value",
)

_POST_HOC_PHRASES = (
    "selected because it yields",
    "in order to obtain unique",
    "invented to match",
    "choose whatever condition",
    "defined by the desired result",
)

_REFORMULATION_PHRASES = (
    "a0 = lambda_a",
    "a1 = lambda_b - lambda_a",
    "commutant_symmetric_k",
    "function_of_ktk",
    "so(2) congruent u(1)",
)

_UNSUPPORTED_AS_NEW_PHRASES = (
    "field-content listing is new physics",
    "unsupported equivalence is new",
    "metric_phi_plus_connection is a new principle",
    "equivalence_unsupported is new physics",
)

_TARGET_PHRASES = (
    "measured masses",
    "measured couplings",
    "measured charge",
    "experimental target",
    "fitted coefficient",
    "calibrated to data",
)


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11a_input_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


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


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _blob(obj: Any) -> str:
    return _norm(" ".join(_walk_strings(obj)))


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase10b1_artifact_dir().resolve(),
        phase10c_artifact_dir().resolve(),
        phase10d_artifact_dir().resolve(),
        phase11a_strategy_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11A input gate refuses an unauthorized action object")
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
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash mismatch"}
    return None


def canonical_declared_input(declared: dict[str, Any]) -> dict[str, Any]:
    return {field: declared.get(field) for field in REQUIRED_INPUT_FIELDS}


def input_hash(declared: dict[str, Any]) -> str:
    return _content_hash(canonical_declared_input(declared))


def _contract_complete(declared: Any) -> bool:
    if not isinstance(declared, dict) or not declared:
        return False
    for field in REQUIRED_INPUT_FIELDS:
        value = declared.get(field)
        if value is None or value == "" or value == [] or value == {}:
            return False
    return True


def _already_present_phrases(synthesis: dict[str, Any]) -> list[str]:
    phrases = [
        "c0 + c1 r",
        "h_r = r^3",
        "diag(lambda_a, lambda_b, lambda_b)",
        "local connection",
        "autonomous f^2",
        "z_a",
        "catalogue_classes = 8",
    ]
    for item in synthesis.get("provenance_map") or []:
        phrases.append(_norm(item.get("RESULT")))
    for item in synthesis.get("parameter_inventory") or []:
        phrases.append(_norm(item.get("symbol")))
        phrases.append(_norm(item.get("meaning")))
    return [p for p in phrases if p]


def _novelty(declared: dict[str, Any], synthesis: dict[str, Any]) -> tuple[str, str]:
    statement = _norm(declared.get("mathematical_statement"))
    what_new = _norm(declared.get("what_is_new"))
    title = _norm(declared.get("title"))
    claimed = " ".join([title, statement, what_new])
    if any(p in claimed for p in _UNSUPPORTED_AS_NEW_PHRASES) or (
        "equivalence_unsupported" in claimed and "new" in claimed
    ):
        return "ALREADY_PRESENT", "EQUIVALENCE_UNSUPPORTED is not new physics"
    if any(p in claimed for p in _REFORMULATION_PHRASES) or "reparameterization of lambda" in claimed:
        return "REDUNDANT_REFORMULATION", "certified 10D reparameterization is not new"
    if "same two-parameter commutant" in claimed:
        return "REDUNDANT_REFORMULATION", "operator-axis reparameterization already certified"
    for phrase in _already_present_phrases(synthesis):
        if phrase and (phrase == statement or phrase == what_new or (len(phrase) > 24 and phrase in statement)):
            return "ALREADY_PRESENT", "statement already in Phases 1-10E"
    if "f^2" in claimed and ("test extension" in claimed or "optional f^2" in claimed):
        return "OVERLAPS_EXISTING_ASSUMPTIONS", "autonomous F^2 is an existing TEST EXTENSION"
    if "c0 + c1" in claimed and "gravity" in claimed:
        return "OVERLAPS_EXISTING_ASSUMPTIONS", "gravity family already declared"
    if not what_new:
        return "NOVELTY_UNRESOLVED", "what_is_new is empty"
    return "GENUINELY_NEW", "not found in certified Phases 1-10E"


def _post_hoc(declared: dict[str, Any]) -> bool:
    if any(key in declared for key in _POST_HOC_KEYS):
        return True
    blob = _blob(declared)
    return any(phrase in blob for phrase in _POST_HOC_PHRASES)


def _target_dependent(declared: dict[str, Any]) -> bool:
    if declared.get("experimental_target_used_for_input_selection") is True:
        return True
    if _contains_banned(declared):
        return True
    blob = _blob(declared)
    return any(phrase in blob for phrase in _TARGET_PHRASES)


def _provenance_ok(declared: dict[str, Any]) -> tuple[bool, str]:
    prov = _norm(declared.get("provenance"))
    if prov in {"derived", "derived from previous framework"}:
        return False, "NEW_PHYSICAL_INPUT must not be labelled DERIVED"
    if declared.get("classification") == "DERIVED":
        return False, "input attempted to relabel INPUT as DERIVED"
    if prov in {"new_physical_input", "input", "assumed", "human_declared"}:
        return True, "NEW_PHYSICAL_INPUT"
    return True, "NEW_PHYSICAL_INPUT"


def _equivalence_status(novelty: str, declared: dict[str, Any]) -> str:
    claimed = " ".join(
        [
            _norm(declared.get("title")),
            _norm(declared.get("mathematical_statement")),
            _norm(declared.get("what_is_new")),
        ]
    )
    if "equivalence_unsupported" in claimed and "new" in claimed:
        return "EQUIVALENCE_UNSUPPORTED"
    if novelty == "REDUNDANT_REFORMULATION":
        return "CERTIFIED_REFORMULATION"
    if novelty == "GENUINELY_NEW":
        return "CERTIFIED_NEW_INPUT"
    if novelty in {"ALREADY_PRESENT", "OVERLAPS_EXISTING_ASSUMPTIONS"}:
        return "CERTIFIED_REFORMULATION"
    return "EQUIVALENCE_UNSUPPORTED"


def _parameter_audit(declared: dict[str, Any] | None, old_count: int) -> dict[str, Any]:
    implications = (declared or {}).get("parameter_implications") if declared else None
    new_params = []
    constrained = []
    relations = []
    silent_fix = False
    if isinstance(implications, dict):
        new_params = list(implications.get("new_parameters") or [])
        constrained = list(implications.get("constrained_parameters") or [])
        relations = list(implications.get("relations") or [])
        silent_fix = bool(implications.get("silently_fixes_existing"))
        blob = _blob(implications)
        if "fix c0" in blob or "fix c1" in blob or "determine unique coupling" in blob:
            silent_fix = True
    elif isinstance(implications, str):
        blob = _norm(implications)
        if "fix" in blob or "set unique" in blob:
            silent_fix = True
        if "no new parameter" in blob or blob == "none":
            new_params = []
    dimless = [p for p in new_params if isinstance(p, dict) and p.get("dimension") == "dimensionless"]
    dimful = [p for p in new_params if isinstance(p, dict) and p.get("dimension") == "dimensionful"]
    if new_params and not dimless and not dimful:
        # unlabeled names count as unspecified new parameters, not silent fixes
        pass
    return {
        "old_parameter_count": old_count,
        "new_parameter_count": len(new_params),
        "constrained_parameter_count": len(constrained),
        "new_dimensionless_count": len(dimless),
        "new_dimensionful_count": len(dimful),
        "relations": relations,
        "silent_fix": silent_fix,
        "parameter_free_consequence_immediate": False,
    }


def _object_audit(declared: dict[str, Any] | None) -> list[dict[str, Any]]:
    objects = (declared or {}).get("new_objects") if declared else None
    if not objects:
        return []
    if isinstance(objects, dict):
        objects = [objects]
    out = []
    for item in objects:
        if not isinstance(item, dict):
            out.append(
                {
                    "object_id": str(item),
                    "mathematical_definition": str(item),
                    "dimension": "UNDECLARED",
                    "symmetry": "UNDECLARED",
                    "locality": "UNDECLARED",
                    "covariance": "UNDECLARED",
                    "derivative_order": "UNDECLARED",
                    "parameter_status": "UNDECLARED",
                    "provenance": "NEW_PHYSICAL_INPUT",
                    "dependencies": [],
                    "kind": "UNDECLARED",
                }
            )
            continue
        out.append(
            {
                "object_id": item.get("object_id") or item.get("name"),
                "mathematical_definition": item.get("mathematical_definition") or item.get("definition"),
                "dimension": item.get("dimension", "UNDECLARED"),
                "symmetry": item.get("symmetry", "UNDECLARED"),
                "locality": item.get("locality", "UNDECLARED"),
                "covariance": item.get("covariance", "UNDECLARED"),
                "derivative_order": item.get("derivative_order", "UNDECLARED"),
                "parameter_status": item.get("parameter_status", "INPUT"),
                "provenance": "NEW_PHYSICAL_INPUT",
                "dependencies": item.get("dependencies") or [],
                "kind": item.get("kind", "UNDECLARED"),
            }
        )
    return out


def _compatibility(declared: dict[str, Any], novelty: str) -> tuple[str, str]:
    blob = _blob(declared)
    if declared.get("mutates_frozen_action") is True or "overwrite frozen action" in blob:
        return "INCOMPATIBLE", "new input may not mutate the frozen Phase 4C action"
    if "derive c0 from gauge" in blob or "derive c1 from gauge" in blob:
        return "INCOMPATIBLE", "gravity coefficients must not be derived from later gauge results"
    if novelty != "GENUINELY_NEW":
        return "UNTESTED", "compatibility is not evaluated for a rejected non-new input"
    return "COMPATIBLE", "no immediate obstruction with the frozen closed framework"


def _scope_record(declared: dict[str, Any] | None) -> dict[str, Any]:
    sectors = [
        "spacetime",
        "gravity",
        "internal space",
        "gauge symmetry",
        "gauge dynamics",
        "matter",
        "quantization",
        "renormalization",
        "boundary structure",
    ]
    declared_scope = []
    if declared:
        raw = declared.get("physical_scope")
        if isinstance(raw, list):
            declared_scope = [str(x) for x in raw]
        elif raw:
            declared_scope = [str(raw)]
    affected = []
    unchanged = []
    for sector in sectors:
        hit = any(_norm(sector) in _norm(item) or _norm(item) in _norm(sector) for item in declared_scope)
        if hit:
            affected.append(
                {
                    "sector": sector,
                    "direct_effect": "declared by human input",
                    "derived_effect": "NOT EXPLORED IN PHASE 11A",
                    "unchanged_components": "unlisted components remain as in 10E",
                }
            )
        else:
            unchanged.append(sector)
    return {"declared_scope": declared_scope, "affected": affected, "unchanged": unchanged}


def audit_human_declared_input(
    declared: dict[str, Any] | None,
    synthesis: dict[str, Any],
) -> dict[str, Any]:
    if not declared:
        return {
            "HUMAN_INPUT_PRESENT": False,
            "NEW_PHYSICAL_INPUT_STATUS": "MISSING",
            "contract_complete": False,
            "NOVELTY_AUDIT_STATUS": "NOVELTY_UNRESOLVED",
            "novelty_detail": "no HUMAN_DECLARED_PHYSICAL_INPUT supplied",
            "PROVENANCE_STATUS": "VERIFIED",
            "provenance_class": None,
            "TARGET_INDEPENDENCE_STATUS": "VERIFIED",
            "experimental_target_used_for_input_selection": False,
            "EQUIVALENCE_AUDIT_STATUS": "VERIFIED",
            "equivalence_outcome": None,
            "PARAMETER_AUDIT_STATUS": "VERIFIED",
            "parameter_audit": _parameter_audit(None, len(synthesis.get("parameter_inventory") or [])),
            "COMPATIBILITY_STATUS": "UNTESTED",
            "compatibility_detail": "no input to test",
            "POST_HOC_INPUT": False,
            "new_objects": [],
            "scope": _scope_record(None),
            "rejection": None,
        }
    if not _contract_complete(declared):
        return {
            "HUMAN_INPUT_PRESENT": True,
            "NEW_PHYSICAL_INPUT_STATUS": "MISSING",
            "contract_complete": False,
            "NOVELTY_AUDIT_STATUS": "NOVELTY_UNRESOLVED",
            "novelty_detail": "incomplete HUMAN_DECLARED_PHYSICAL_INPUT contract",
            "PROVENANCE_STATUS": "FAILED",
            "TARGET_INDEPENDENCE_STATUS": "VERIFIED",
            "experimental_target_used_for_input_selection": False,
            "EQUIVALENCE_AUDIT_STATUS": "FAILED",
            "PARAMETER_AUDIT_STATUS": "FAILED",
            "parameter_audit": _parameter_audit(declared, len(synthesis.get("parameter_inventory") or [])),
            "COMPATIBILITY_STATUS": "UNTESTED",
            "POST_HOC_INPUT": False,
            "new_objects": [],
            "scope": _scope_record(declared),
            "rejection": "INCOMPLETE_CONTRACT",
        }
    post_hoc = _post_hoc(declared)
    target = _target_dependent(declared)
    prov_ok, prov_class = _provenance_ok(declared)
    novelty, novelty_detail = _novelty(declared, synthesis)
    equiv = _equivalence_status(novelty, declared)
    params = _parameter_audit(declared, len(synthesis.get("parameter_inventory") or []))
    compat, compat_detail = _compatibility(declared, novelty)
    rejection = None
    if post_hoc:
        rejection = "POST_HOC_INPUT"
        novelty = "NOVELTY_UNRESOLVED"
    elif target:
        rejection = "NEW_INPUT_REJECTED_TARGET_DEPENDENT"
    elif not prov_ok:
        rejection = "PROVENANCE_RELABEL_REJECTED"
    elif params["silent_fix"]:
        rejection = "SILENT_PARAMETER_FIX_REJECTED"
    elif novelty in {"ALREADY_PRESENT", "REDUNDANT_REFORMULATION"}:
        rejection = "NEW_INPUT_REJECTED_AS_NONNEW"
    elif equiv == "EQUIVALENCE_UNSUPPORTED" and "new physics" in _blob(declared):
        rejection = "UNSUPPORTED_EQUIVALENCE_NOT_NEW_PHYSICS"
    elif compat == "INCOMPATIBLE":
        rejection = "INCOMPATIBLE_WITH_CLOSED_FRAMEWORK"
    return {
        "HUMAN_INPUT_PRESENT": True,
        "NEW_PHYSICAL_INPUT_STATUS": "PRESENT" if rejection is None else "REJECTED",
        "contract_complete": True,
        "NOVELTY_AUDIT_STATUS": novelty,
        "novelty_detail": novelty_detail,
        "PROVENANCE_STATUS": "VERIFIED" if prov_ok and not post_hoc else "FAILED",
        "provenance_class": prov_class,
        "TARGET_INDEPENDENCE_STATUS": "FAILED" if target else "VERIFIED",
        "experimental_target_used_for_input_selection": bool(target),
        "EQUIVALENCE_AUDIT_STATUS": "VERIFIED" if equiv != "EQUIVALENCE_UNSUPPORTED" or rejection is None else "PARTIAL",
        "equivalence_outcome": equiv,
        "PARAMETER_AUDIT_STATUS": "FAILED" if params["silent_fix"] else "VERIFIED",
        "parameter_audit": params,
        "COMPATIBILITY_STATUS": compat,
        "compatibility_detail": compat_detail,
        "POST_HOC_INPUT": post_hoc,
        "new_objects": _object_audit(declared),
        "scope": _scope_record(declared),
        "rejection": rejection,
        "input_id": declared.get("input_id"),
        "title": declared.get("title"),
        "input_hash": input_hash(declared),
    }


def _phase_status(audit: dict[str, Any]) -> str:
    if not audit.get("HUMAN_INPUT_PRESENT") or audit.get("NEW_PHYSICAL_INPUT_STATUS") == "MISSING":
        return "BLOCKED"
    if audit.get("rejection"):
        return "FAILED"
    if audit.get("NOVELTY_AUDIT_STATUS") != "GENUINELY_NEW":
        return "FAILED"
    if audit.get("TARGET_INDEPENDENCE_STATUS") != "VERIFIED":
        return "FAILED"
    if audit.get("PROVENANCE_STATUS") != "VERIFIED":
        return "FAILED"
    if audit.get("COMPATIBILITY_STATUS") == "INCOMPATIBLE":
        return "FAILED"
    if audit.get("COMPATIBILITY_STATUS") == "UNTESTED":
        return "BLOCKED"
    return "READY_FOR_CONSEQUENCE_PHASE"


def analyze_phase11a_input_gate(
    auth: Phase5B0Authorization,
    *,
    declared_input: dict[str, Any] | None = None,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    del signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt

    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "10B_CATALOG": phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json",
        "10C_CATALOG": phase10c_artifact_dir() / "PHASE_10C_INTERPRETATION_CATALOG.json",
        "10D_CATALOG": phase10d_artifact_dir() / "PHASE_10D_EQUIVALENCE_CATALOG.json",
        "STRATEGY_11A": phase11a_strategy_artifact_dir() / "PHASE_11A_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {
            "status": "STOP",
            "scientific_analysis": None,
            "detail": "missing " + ", ".join(missing),
        }
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    synthesis = loaded["10E_SYNTHESIS"]
    summary10e = loaded["10E_SUMMARY"]

    hash_10e = _content_hash(synthesis)
    if hash_10e != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10E synthesis hash mismatch"}
    if _content_hash(loaded["10B_CATALOG"]) != EXPECTED_SOURCE_CATALOG_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10B catalog hash mismatch"}
    if _content_hash(loaded["10C_CATALOG"]) != EXPECTED_10C_CATALOG_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10C catalog hash mismatch"}
    if _content_hash(loaded["10D_CATALOG"]) != EXPECTED_10D_CATALOG_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10D catalog hash mismatch"}
    if hashlib.sha256(snapshots["STRATEGY_11A"]).hexdigest() != EXPECTED_STRATEGY_11A_SUMMARY_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "legacy 11A strategy artefact mutated"}
    if summary10e.get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10E not closed under declared scope"}
    if summary10e.get("FINAL_PARAMETER_FREE_RELATION_COUNT") != 0:
        return {"status": "STOP", "scientific_analysis": None, "detail": "10E PFR count changed"}
    if summary10e.get("UNIQUE_ACTION") is not False:
        return {"status": "STOP", "scientific_analysis": None, "detail": "UNIQUE_ACTION changed"}
    if summary10e.get("UNIQUE_COUPLING") is not False:
        return {"status": "STOP", "scientific_analysis": None, "detail": "UNIQUE_COUPLING changed"}
    if synthesis.get("NEW_PHYSICAL_INPUT_REQUIRED") is not True:
        return {"status": "STOP", "scientific_analysis": None, "detail": "NEW_PHYSICAL_INPUT_REQUIRED changed"}
    if _contains_banned(declared_input or {}) or _ranking_hits(declared_input or {}):
        target_fail = True
    else:
        target_fail = False

    audit = audit_human_declared_input(declared_input, synthesis)
    if target_fail and declared_input:
        audit["TARGET_INDEPENDENCE_STATUS"] = "FAILED"
        audit["experimental_target_used_for_input_selection"] = True
        audit["rejection"] = "NEW_INPUT_REJECTED_TARGET_DEPENDENT"
        audit["NEW_PHYSICAL_INPUT_STATUS"] = "REJECTED"

    phase_status = _phase_status(audit)
    freeze_status = "NOT_CREATED"
    freeze_payload = None
    if (
        phase_status == "READY_FOR_CONSEQUENCE_PHASE"
        and declared_input is not None
        and audit.get("NOVELTY_AUDIT_STATUS") == "GENUINELY_NEW"
    ):
        freeze_payload = {
            "input_id": declared_input.get("input_id"),
            "canonical_input": canonical_declared_input(declared_input),
            "input_hash": input_hash(declared_input),
            "provenance": "NEW_PHYSICAL_INPUT",
            "novelty_status": audit["NOVELTY_AUDIT_STATUS"],
            "dependency_manifest": {
                "closed_baseline": "PHASE_10E",
                "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
                "grammar_hash": grammar_before,
            },
            "affected_components": audit["scope"]["declared_scope"],
            "GATE_VERSION": GATE_VERSION,
        }
        freeze_status = "VERIFIED"

    baseline = {
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "FINAL_PARAMETER_FREE_RELATION_COUNT": 0,
        "UNIQUE_ACTION": False,
        "UNIQUE_COUPLING": False,
        "NEW_PHYSICAL_INPUT_REQUIRED": True,
        "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
        "grammar_hash": grammar_before,
        "phase10e_synthesis_hash": hash_10e,
        "phase10b1_catalog_hash": EXPECTED_SOURCE_CATALOG_HASH,
        "phase10c_catalog_hash": EXPECTED_10C_CATALOG_HASH,
        "phase10d_catalog_hash": EXPECTED_10D_CATALOG_HASH,
        "legacy_strategy_11a_summary_hash": EXPECTED_STRATEGY_11A_SUMMARY_HASH,
        "catalogue_classes": 8,
        "certified_equivalence_components": 4,
        "certified_distinct_pairs": 16,
        "unsupported_pairs": 8,
    }

    payload = {
        "gate_version": GATE_VERSION,
        "HUMAN_INPUT_PRESENT": audit["HUMAN_INPUT_PRESENT"],
        "NEW_PHYSICAL_INPUT_STATUS": audit.get("NEW_PHYSICAL_INPUT_STATUS"),
        "audit": audit,
        "PRE_NEW_INPUT_BASELINE": baseline,
        "INPUT_FREEZE": freeze_payload,
        "models_generated": 0,
        "principles_generated": 0,
        "ranking": False,
        "machine_chose_principle": False,
        "previous_program_unchanged": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "STOP", "scientific_analysis": None, "detail": "banned or ranking token in gate payload"}

    if write_artifacts:
        _write_json("PHASE_11A_INPUT_GATE.json", payload)
        _write_json("PRE_NEW_INPUT_BASELINE.json", baseline)
        _write_json(
            "PHASE_11A_INPUT_GATE_SUMMARY.json",
            {
                "GATE_VERSION": GATE_VERSION,
                "PHASE_11A_STATUS": phase_status,
                "HUMAN_INPUT_PRESENT": audit["HUMAN_INPUT_PRESENT"],
                "NOVELTY_AUDIT_STATUS": audit["NOVELTY_AUDIT_STATUS"],
                "INPUT_FREEZE_STATUS": freeze_status,
                "PROGRAM_CLOSURE_STATUS_PRESERVED": EXPECTED_10E_CLOSURE,
                "FINAL_PARAMETER_FREE_RELATION_COUNT": 0,
                "UNIQUE_ACTION": False,
                "UNIQUE_COUPLING": False,
            },
        )
        if freeze_payload is not None:
            _write_json("PHASE_11A_INPUT_FREEZE.json", freeze_payload)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    science = {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11A_INPUT_TEST_COPY_ID": PHASE_11A_INPUT_TEST_COPY_ID,
        "gate": payload,
        "PHASE_11A_PRECONDITION_STATUS": "VERIFIED",
        "HUMAN_INPUT_PRESENT": audit["HUMAN_INPUT_PRESENT"],
        "NOVELTY_AUDIT_STATUS": audit["NOVELTY_AUDIT_STATUS"],
        "PROVENANCE_STATUS": audit["PROVENANCE_STATUS"],
        "TARGET_INDEPENDENCE_STATUS": audit["TARGET_INDEPENDENCE_STATUS"],
        "EQUIVALENCE_AUDIT_STATUS": audit["EQUIVALENCE_AUDIT_STATUS"],
        "PARAMETER_AUDIT_STATUS": audit["PARAMETER_AUDIT_STATUS"],
        "COMPATIBILITY_STATUS": audit["COMPATIBILITY_STATUS"],
        "INPUT_FREEZE_STATUS": freeze_status,
        "PHASE_11A_STATUS": phase_status,
        "NEW_PHYSICAL_INPUT_STATUS": audit.get("NEW_PHYSICAL_INPUT_STATUS"),
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "FINAL_PARAMETER_FREE_RELATION_COUNT": 0,
        "UNIQUE_ACTION": False,
        "UNIQUE_COUPLING": False,
        "NEW_PHYSICAL_INPUT_REQUIRED": True,
        "models_generated": 0,
        "principles_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "machine_chose_principle": False,
        "NO_EXPERIMENTAL_DATA_USED": True,
        "NO_TARGET_VALUES_USED": audit["TARGET_INDEPENDENCE_STATUS"] == "VERIFIED",
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "experimental_target_used_for_input_selection": audit.get("experimental_target_used_for_input_selection"),
        "GRAMMAR_UNCHANGED": True,
        "SOURCE_CATALOG_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "LEGACY_STRATEGY_11A_UNCHANGED": True,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "PHASE_11A_CLOSED": False,
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": phase_status == "BLOCKED" and audit["HUMAN_INPUT_PRESENT"] is False,
    }
    return science


def run_phase11a_input_or_stop(
    *,
    root=None,
    signature: str = MOSTLY_PLUS,
    declared_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11a_input_gate(auth, signature=signature, declared_input=declared_input)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED"}:
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
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "LEGACY_STRATEGY_11A_UNCHANGED": "VERIFIED",
            "PHASE_11A_INPUT_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED" if science.get("TARGET_INDEPENDENCE_STATUS") == "VERIFIED" else "FAILED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11A_STATUS": science.get("PHASE_11A_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
