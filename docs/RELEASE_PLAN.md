# Release plan

## Independent workspace

The preparation checkout is separate from the research workspace. Do not move, rename, clean up or rewrite historical experiments to prepare a public release. Remote inventory is read-only; server capacity rules and training authorization remain outside this release task.

## Shipped v0.1.0 layout

~~~
src/platformzero/
  core.py
  env.py
  levels.py
  cli.py
  benchmark.py
  maps/  # original synthetic JSON, packaged in the wheel
examples/
tests/
docs/
provenance/
~~~

Keep generic interfaces separate from game-specific physics and the native adapter. Copy source only through an explicit, reviewed allowlist. Do not export entire experiment directories or server bundles.

## Existing workspace roles

| Workspace | Contents and role | Release treatment |
|---|---|---|
| Local research | Python source, synthetic environment, native bridge, experiment implementations, reports and reference material | Candidate implementation source; references and evidence stay private |
| Recent training server | Deployed runtime, source transports, recent paired experiments and complete checkpoints | Deployment reference and retained evidence; no bulk export |
| Earlier training server | Historical solver banks, previous encoders, recovery runs and diagnostics | Historical reference; no bulk export |

Exact host/account/path metadata is recorded only in an ignored private inventory. Selected owned-process filters found no matching training commands during the inventory; this is not a claim that the servers have no other processes.

## Acceptance before a runnable simulator release

The initial scaffold has now been followed by a runnable synthetic release. Original authored-map sampling and state recovery are the scope of v0.1.0. Commercial-game adapters and native-game parity remain future work; no Celeste map importer is included.

1. Decide the public name after collision review.
2. Trace each selected file to project-authored work or a specific compatible upstream license; isolate unresolved implementations.
3. Extract the fast simulation backend and its explicit dependencies. For v0.1.0, provide redistributable authored examples only; do not add commercial map import.
4. Remove research-only paths, machine addresses, frozen-run identifiers and hidden fallback dependencies from runtime configuration.
5. Package a single documented install and rollout path. Pin the supported runtime; document platform and numerical differences.
6. Verify action masks, terminal conditions, state/history capture and deterministic restore using bounded authored examples. Do not rerun sealed scientific experiments.
7. Provide a repeatable throughput benchmark with hardware, worker count, simulator frames versus decisions and supported mechanism scope.
8. Audit tracked files, built distributions and Git history for assets, credentials and incompatible sources; preserve required license notices.
9. Only then describe the repository as runnable or ready to publish.

## Scientific claims

Existing room geometry coverage does not imply every game mechanism is implemented. Successful worker startup or checkpoint restoration does not establish skill accumulation. A single paired experiment is not robust evidence of superiority. The existing paired KL result improved measured retention but did not pass the joint old/new skill qualification.

The public documentation must distinguish exact behavior, calibrated approximations, unsupported mechanics and native-game transfer evidence. Existing training uses demonstrations and a pretrained source actor; the name Zero must not imply zero-shot training or learning entirely from scratch.
