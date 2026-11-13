# Contributing to the laboratory

This project is both software and a scientific provenance record. A change is
acceptable only when its computational effect and its scientific status are
clear.

## Non-negotiable rules

1. Do not overwrite historical reports or sealed phase artifacts.
2. Do not label an assumed, calibrated or experimental value as derived.
3. Do not activate a search, action, vacuum or new physical input implicitly.
4. Keep code changes separate from scientific conclusions in commits.
5. Update tests and the current-status document when a phase status changes.
6. Record hashes and authorization identifiers for new phase artifacts.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

The virtual environment is local and must not be committed. The repository
expects Python 3.11 or newer as declared in `pyproject.toml`.

Some historical phase tests intentionally exercise artifact materialization.
Run them in a disposable checkout or verify `git status` and artifact hashes
afterward. A test run must never be used as evidence that a scientific record
was intentionally updated.

## Phase work

Before implementing a new phase, document its input boundary, authorization
boundary, output artifacts and stopping conditions. A phase may report
`NOT_STARTED`, `NOT_AUTHORIZED` or `NOT_TESTED`; those are meaningful states,
not failures to hide.

## Public release

The repository has no license file yet. Choose a license before making the
GitHub repository a reusable public project.
