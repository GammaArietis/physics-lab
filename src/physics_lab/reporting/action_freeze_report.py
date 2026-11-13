"""Phase 5B.0 report: action serializer contract and Phase 4C freeze."""

from __future__ import annotations

from physics_lab.core.result import ModelResult
from physics_lab.reporting.formatting import banner


def format_action_freeze_report(result: ModelResult) -> str:
    data = result.metadata.get("action_freeze")
    if not data:
        return ""
    verified = (
        data.get("serializer_status") == "VERIFIED"
        and data.get("freeze_status") == "VERIFIED"
    )
    lines = [
        banner("PHASE 5B.0 — ACTION SERIALIZER CONTRACT", width=52),
        "",
        "ACTION_SERIALIZER_CONTRACT:",
        f"    {data.get('serializer_schema')}",
        "",
        "ACTION_CONTENT_HASH:",
        f"    {data.get('fingerprint')}",
        "",
        "SERIALIZER_STATUS:",
        f"    {data.get('serializer_status')}",
        "",
        "FREEZE_STATUS:",
        f"    {data.get('freeze_status')}",
        "",
        "unsupported_equivalences:",
        f"    {data.get('unsupported_equivalences')}",
        "",
        f"freeze_id: {data.get('freeze_id')}",
        f"freeze_provenance: {data.get('freeze_provenance')}",
        f"scientifically_verified: {verified}",
        "",
        "The fingerprint is SHA-256 of the canonical action JSON.",
        "It is not defined by this report.",
        "The serializer identifies action content. It is not a theorem prover.",
    ]
    return "\n".join(lines)
