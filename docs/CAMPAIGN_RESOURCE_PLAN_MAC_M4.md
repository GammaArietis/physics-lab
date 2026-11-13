# Resource plan for wider campaigns on MacBook Air M4, 24 GB

The MacBook Air can be used as the local execution host for wider campaigns,
but its parallelism should be measured rather than inferred from core count.
The first target profile is conservative:

- reserve roughly 8 GB for macOS and interactive work;
- start with `parallelism: 4` and increase only after memory-pressure checks;
- keep per-candidate processes isolated and use the platform default process
  start method (`spawn` on macOS);
- write one report and one checkpoint result per candidate instead of keeping a
  large batch in memory;
- retain resumability so an interrupted run does not restart completed
  candidates;
- do not activate empirical comparison or parameter fitting in the resource
  campaign.

Before a wide run, measure a short multi-candidate pilot on the actual Mac:
peak resident memory per worker, total memory pressure, wall-clock time,
failure rate, checkpoint throughput and duplicate rate. The resulting values
should determine the next manifest's `parallelism`, timeout and candidate
batch size. Until that measurement exists, the current pilot is not evidence
that a wide campaign is safe to launch.
