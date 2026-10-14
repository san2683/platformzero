# Measured headless throughput — v0.1.0

Measured sequentially on 2026-10-14, Windows 11, Python 3.12.6, AMD Ryzen 7 8845H (8 cores / 16 logical CPUs). No game, renderer, GPU, model or optimizer was used. Numbers are three-repeat medians on the original `two_gaps` example, not a promise for other geometry or hardware.

| Path | Processes | Measured work per repeat | Actual physics frames/s | Decisions/s |
|---|---:|---|---:|---:|
| Direct physics ticks | 1 | 200,000 physical frames | 285,780 | N/A |
| Environment with observation/reset | 1 | 100,000 decisions / 393,762 frames | 231,662 | 58,833 |
| Environment with observation/reset | 4 | 400,000 decisions / 1,575,048 frames | 336,336 | 85,416 |

These are **end-to-end batch** rates. Denominator includes map/env initialization, warmup and, for four processes, spawn/startup, IPC and shutdown. Warmup frames are separately reported and excluded from the throughput numerator. Worker-local sampling durations are also present; do not use their sum as a parallel wall-clock denominator. Short batches show substantial Windows spawn overhead and are not linear-scaling evidence.

Each worker uses the same precomputed deterministic action stream, without policy inference or random generation overhead in the measured loop. Terminal episodes are reset and that cost is included. At frame_skip=4 some final actions use fewer frames; the table counts literal `physics_frames_delta`, not decisions multiplied by four. Environment observations are lightweight state telemetry; no camera/terrain encoding is included.

## Reproduce

```sh
python -m pip install .
python -m platformzero benchmark --mode physics --steps 200000 --workers 1 --warmup 2000 --repeats 3 --output physics.json
python -m platformzero benchmark --mode env --steps 100000 --workers 1 --warmup 2000 --repeats 3 --output env1.json
python -m platformzero benchmark --mode env --steps 100000 --workers 4 --warmup 2000 --repeats 3 --output env4.json
```

Raw results, including individual timings, resets, actual counters and hardware identifier:

- [Physics, one process](benchmarks/physics-1worker-windows-py312.json)
- [Environment, one process](benchmarks/env-1worker-windows-py312.json)
- [Environment, four processes](benchmarks/env-4workers-windows-py312.json)

The benchmark does not establish compatibility with commercial game physics, learned skill quality or cross-game zero-shot performance.
