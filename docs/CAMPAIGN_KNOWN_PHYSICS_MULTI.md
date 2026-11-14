# Bounded known-physics multi-candidate campaign

This campaign runs the two executable known-physics baselines already closed
internally by the laboratory:

- \`known-physics-quantum-harmonic-oscillator\`;
- \`known-physics-free-real-scalar-field\`.

It is a reproducibility and pipeline campaign, not a search over speculative
theories. It does not compare candidates with external data, fit parameters,
rank candidates, select a theory, activate finite bounds, or use the H₂
scope-control dataset.

The Mac resource benchmark with 64 controlled variants remains a separate
infrastructure result. It must not be interpreted as a 64-theory physical
campaign.

## Run on the Mac

From the repository root:

\`\`\`bash
git pull --ff-only origin optimize/phase14l-14n
source .venv/bin/activate
export PYTHONPATH="$PWD/src"

python tools/run_known_physics_multi_campaign.py
\`\`\`

Use the checked-in launcher rather than a \`python - <<'PY'\` heredoc. macOS
uses multiprocessing \`spawn\`; a heredoc has the synthetic path
\`<stdin>\`, so worker processes cannot reconstruct the parent program. The
previous failed run is resumable: the existing checkpoint records isolated
failures and the launcher will retry them.

The expected first gate is:

- \`execution_status: COMPLETE\`;
- both candidates \`PASS\`;
- \`record_unchanged: true\` for both;
- all campaign controls true;
- \`selection.performed: false\`;
- \`selection.ranking_performed: false\`.

The execution writes only campaign evidence under:

- \`docs/validation/campaign_checkpoints/known-physics-multi-baselines.json\`;
- \`docs/validation/campaign_reports/known-physics-multi-baselines/\`.

It also writes
\`schemas/examples/campaign_activation_known_physics_multi_completed.json\`
after the run. After inspecting the JSON report, commit the generated
evidence and the completed activation record. Do not edit the original
\`NOT_RUN\` activation record: it is the pre-execution authorization.
