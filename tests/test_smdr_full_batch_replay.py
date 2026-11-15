from __future__ import annotations

import gzip
import json
from pathlib import Path

from tools.run_smdr_full_batch_replay import _read_records, _source_record


def test_non_eligible_case_is_retained_as_data() -> None:
    record = _source_record(3, {"case_id": "failed", "status": "BOUND_REACHED", "error": "bound"})
    assert record is not None
    assert record["replay_status"] == "NOT_ELIGIBLE"
    assert record["source_status"] == "BOUND_REACHED"


def test_jsonl_gzip_records_resume_by_case_id(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"case_id": "a", "replay_status": "COMPLETE"}) + "\n")
    assert _read_records(path)["a"]["replay_status"] == "COMPLETE"
