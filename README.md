# PlatformZero

**跑酷平台搭建器：独立、无渲染的二维平台模拟环境，用于快速并行采样。**

A headless 2D platformer simulation backend for reproducible sampling. **v0.1.0 is installable and runnable** with Python 3.10+ and no runtime dependencies. The shipped backend uses original synthetic maps and simplified physics; it does not import Celeste maps, require a game installation, or claim Celeste physics parity.

## Install and sample

From this checkout:

```sh
python -m pip install .
python -m platformzero sample --level two_gaps --episodes 20 --seed 42
```

Or install this GitHub version directly (Git required):

```sh
python -m pip install "git+https://github.com/san2683/platformzero.git@v0.1.0"
platformzero sample --level runway --policy right --episodes 3
```

This does not imply a PyPI publication. `random` samples legal actions; `right` is a minimal scripted example for the flat runway, not a trained Bot.

## What ships

- Fixed 60 Hz CPU physics with axis-separated collision substeps.
- Edge-triggered jumping, optional double jump, jump release shortening, eight-direction dash, static solids/hazards and goal/death/timeout handling.
- Three bundled **original** JSON maps: `runway`, `two_gaps`, `steps_and_spikes`.
- A five-value headless environment API, actual-frame accounting and a seeded action sampler.
- Versioned JSON-safe state capture/restore including velocities, resources, held-button history, reward state, immutable level fingerprint and sampler RNG.
- Sequential and spawned multiprocessing throughput benchmarks, tests and Windows/Linux CI configuration.

No renderer, display server, commercial maps/assets, Celeste importer, game DLLs, model checkpoints or training framework are included. Moving platforms, wall climbing, coyote time, native-game replication and a PPO trainer are **not implemented in v0.1.0**.

## Python API

```python
from platformzero import HeadlessEnv, load_example

env = HeadlessEnv(load_example("two_gaps"), frame_skip=4, seed=42)
observation, info = env.reset()
while True:
    observation, reward, terminated, truncated, info = env.step(env.sample_action())
    # May be <4 on the final decision. Count actual frames, not decisions * 4.
    actual_frames = info["physics_frames_delta"]
    if terminated or truncated:
        break
```

`env.step()` accepts either `Action(move=-1/0/1, jump=False/True, dash=0..8)` or the factorized indices `[horizontal 0..2, jump 0..1, dash 0..8]` (54 joint actions). See [API and physics contract](docs/API.md) for direction indices, observations and supported behavior. This interface is separate from any research model's contract.

## Capture and restore

```python
import json

saved = json.loads(json.dumps(env.get_state()))
clone = HeadlessEnv()
clone.set_state(saved)
# Same subsequent action stream => same states, rewards and terminal decisions.
```

Run the round-trip example and installed-package tests:

```sh
python examples/restore.py
python -m unittest discover -s tests -v
```

Snapshots include the environment's action-sampler RNG, not an external policy's state. Invalid restores are rejected before changing the environment. Deterministic continuation is tested on the same runtime; cross-version/platform floating-point parity is not promised.

## Throughput

```sh
platformzero benchmark --mode physics --steps 200000 --workers 1 --repeats 3
platformzero benchmark --mode env --steps 100000 --workers 4 --repeats 3
```

Physics mode measures ticks only. Environment mode includes observations, rewards and terminal/reset handling. Both report **actual physics frames** separately from decisions. End-to-end time includes warmup and, with multiple workers, process startup and shutdown. See the [measured benchmark report](docs/BENCHMARKS.md) and raw JSON results; these are local CPU measurements, not GPU training or native-game performance claims.

## Source, license and release scope

The published synthetic backend, examples and tooling use the [MIT license](LICENSE). Its generic physics core was extracted and revised from this project's authored synthetic environment, with source hashes and modifications recorded in [released-file provenance](provenance/RELEASED_FILES.json).

Commercial-game-specific research modules remain outside this package. References in [source provenance](provenance/UPSTREAM.md) do not mean those implementations have been shipped or licensed by this release. See [license policy](LICENSE_POLICY.md), [release plan](docs/RELEASE_PLAN.md) and [working-name review](docs/NAME_REVIEW.md).
