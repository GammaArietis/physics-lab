# SMDR full batch replay

This runner replays every case in the W11 v2 archive through the official
SMDR executable. It is a backend campaign, not a theory search: archive order
is preserved, every result is retained, failed/non-eligible source cases are
recorded, and no fitting, ranking or promotion is performed.

## Mac execution

From the repository root, after building the official SMDR checkout with
`make smdr && make apps`:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD/src"

python tools/run_smdr_full_batch_replay.py \
  --smdr-root /absolute/path/to/SMDR \
  --workers 8
```

The output is resumable. If the process is interrupted, rerun the same
command with `--resume`:

```bash
python tools/run_smdr_full_batch_replay.py \
  --smdr-root /absolute/path/to/SMDR \
  --workers 8 \
  --resume
```

The runner writes:

- `docs/validation/smdr_full_batch_replay_2026-11-15.jsonl.gz`: one record per
  selected case;
- `docs/validation/smdr_full_batch_replay_2026-11-15.checkpoint.json`: atomic
  progress checkpoint;
- `docs/validation/smdr_full_batch_replay_2026-11-15.summary.json`: final
  aggregate and controls.

## Smoke run

Before committing to the full run, an explicit two-case smoke test can be
used:

```bash
python tools/run_smdr_full_batch_replay.py \
  --smdr-root /absolute/path/to/SMDR \
  --workers 2 \
  --limit 2 \
  --output /tmp/smdr-smoke.jsonl.gz \
  --checkpoint /tmp/smdr-smoke.checkpoint.json \
  --summary /tmp/smdr-smoke.summary.json
```

The smoke limit is a diagnostic execution control, not a representative
scientific sample and must not be used for selection.

## Expected cost

The validated ordinary single-case execution took roughly 2.7 seconds in the
audit environment. The full archive contains 28,692 source cases, of which
the completed W11 electroweak states are the replayable subset. The archive
also contains 1,404 complete states with all three gauge couplings numerically
zero; a two-case smoke test showed that these pathological inputs can take
roughly 30 seconds each and may return no headline observables. They remain
in the record as `BACKEND_FAILURE` rather than being silently removed.

The optimistic serial estimate is therefore about 20--22 hours for ordinary
states and potentially about 30 hours including the pathological subset. With
eight workers, a practical wall-time estimate is a few hours, subject to
thermal throttling and process overhead on the Mac. The estimate is only a
scheduling estimate, not a physical result.

## Interpretation boundary

SMDR evaluates the supplied state. It does not repair a candidate whose
couplings run to the wrong infrared regime. A complete batch can therefore
produce a well-populated negative result: successful backend evaluations may
still fail to reproduce known physics. The campaign must be read together
with the W11 matching report and the SMDR backend closeout.
