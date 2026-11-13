# Phase 14L–14N performance audit

## Current result

The full test collection contains 1,486 tests. After separating parent-phase
verification from child-phase replay, the complete suite reaches 100% with
exit code 0 in the isolated environment. The 14L symbolic replay remains the
expensive part; 14M and 14N now verify their committed parent artifacts and
run their own audits without recursively replaying the whole chain.

The bottleneck was profiled in Phase 14L. The dominant stack is:

```text
phase14l._pack
  → phase5c_gauging._inner
    → sympy.simplify
      → trigsimp / symbolic ordering
```

The expensive case is the symmetry-breaking comparison, where transformed
fields introduce trigonometric expressions into repeated bilinear
contractions.

## Safe changes retained

`phase5c_gauging._is_zero` now checks, in order:

1. structural zero;
2. structural zero after expansion;
3. the original full `sympy.simplify` fallback.

This preserves the previous mathematical decision procedure while avoiding
expensive simplification for expressions already in canonical zero form.
The focused Phase 5C, Phase 14E, Phase 14K, and Phase 18E tests pass with the
change.

The new `verify_stored_phase_14l`, `verify_stored_phase_14m`, and
`verify_stored_phase_14n` functions validate manifests, parent hashes,
semantic records, provenance, and required action metadata without claiming
that an independent symbolic replay occurred. Their explicit result field is
`independent_replay = NOT_PERFORMED`.

## Experiments rejected

The following approaches were tested only in disposable copies and were not
kept:

- caching the complete audit result, because it weakens the independent
  repeated-evaluation check;
- replacing bilinear contractions with unsimplified raw products, because
  expression size and memory use became unsafe;
- memoizing large symbolic matrix contents, because key construction and
  memory growth became worse than the original calculation.

## Remaining optimization plan

The next deeper optimization must preserve two separate guarantees:

- the derivation must remain mathematically identical;
- repeatability must still be checked independently.

The appropriate design is therefore:

1. introduce a canonical, immutable symbolic intermediate representation at
   the Phase 14J boundary;
2. derive the Phase 14L–14N expressions once from that representation;
3. validate the stored expressions with a lightweight exact checker;
4. run an independent replay in a separate process or dedicated exhaustive
   CI job;
5. compare canonical digests and all negative tests before accepting the
   optimized path.

No new theory search, parameter fit, vacuum choice, or experimental input is
activated by this performance work.

## Verification result

- Full suite: 1,486 tests collected, 100% completion, exit code 0.
- Phase 14K–14N chain: completed successfully after parent-artifact reuse.
- Fast stored-artifact checks: 3 tests included in the full suite, all passing.
- Remaining warning: pytest reports a non-blocking compatibility warning from
  the installed `anyio` plugin.
