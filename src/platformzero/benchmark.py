"""CPU throughput benchmark: actual physics ticks and environment decisions."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import multiprocessing
import os
import platform
from pathlib import Path
import hashlib
import statistics
import time

from .core import Action, ENGINE, World, digest, integer
from .env import HeadlessEnv
from .levels import load_example


def worker_job(config):
    mode, level_name, steps, warmup, frame_skip, worker_index = config
    level = load_example(level_name)
    # A deterministic, low-overhead action stream. No policy/model/renderer costs.
    actions = [Action(move=1 if i % 24 < 16 else -1,
                      jump=i % 31 < 12, dash=1 if i % 97 == 0 else 0) for i in range(256)]
    indices = [(a.move + 1, int(a.jump), a.dash) for a in actions]
    world = World(level); env = HeadlessEnv(level, frame_skip=frame_skip, seed=worker_index)
    env.reset()
    physics = decisions = resets = 0

    def advance(index):
        nonlocal world, physics, decisions, resets
        if mode == "physics":
            if world.status != "playing":
                world = World(level); resets += 1
            before = world.frames
            world.tick(actions[index % 256])
            physics += world.frames - before
        else:
            if env.world.status != "playing":
                env.reset(); resets += 1
            *_, info = env.step(indices[index % 256])
            physics += info["physics_frames_delta"]
            decisions += 1

    for i in range(warmup):
        advance(i)
    warmup_physics = physics
    physics = decisions = resets = 0
    start = time.perf_counter()
    for i in range(steps):
        advance(i)
    elapsed = time.perf_counter() - start
    return {"worker_index": worker_index, "physics_frames": physics,
            "decisions": decisions, "episode_resets": resets,
            "warmup_physics_frames_excluded": warmup_physics,
            "sampling_seconds": elapsed}


def run_benchmark(*, mode="env", level="two_gaps", steps=100000,
                  workers=1, warmup=1000, repeats=3, frame_skip=4):
    if mode not in ("physics", "env"):
        raise ValueError("mode must be physics or env")
    integer(steps, "steps", 1, 1000000000)
    integer(workers, "workers", 1, 64)
    integer(warmup, "warmup", 0, 10000000)
    integer(repeats, "repeats", 1, 100)
    integer(frame_skip, "frame_skip", 1, 8)
    load_example(level)
    trials = []
    for repeat in range(repeats):
        jobs = [(mode, level, steps, warmup, frame_skip, i) for i in range(workers)]
        begin = time.perf_counter()
        if workers == 1:
            rows = [worker_job(jobs[0])]
        else:
            # spawn works identically on Windows and Linux; no inherited game/UI state.
            with ProcessPoolExecutor(max_workers=workers,
                                     mp_context=multiprocessing.get_context("spawn")) as pool:
                rows = list(pool.map(worker_job, jobs))
        wall = time.perf_counter() - begin
        frames = sum(r["physics_frames"] for r in rows)
        decisions = sum(r["decisions"] for r in rows)
        trials.append({"repeat": repeat, "workers": rows,
                       "actual_physics_frames": frames, "actual_decisions": decisions,
                       "wall_seconds_including_startup_warmup": wall,
                       "physics_frames_per_second_end_to_end": frames / wall,
                       "decisions_per_second_end_to_end": decisions / wall,
                       "single_worker_sampling_physics_fps": frames / rows[0]["sampling_seconds"] if workers == 1 else None})
    from . import __version__
    source = Path(__file__).parent
    return {"schema": "platformzero-benchmark-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "package_version": __version__, "engine": ENGINE,
            "source_SHA256": {name: hashlib.sha256((source/name).read_bytes()).hexdigest()
                              for name in ("core.py","env.py","levels.py","benchmark.py")},
            "level_SHA256": digest(load_example(level).to_dict()),
            "hardware": {"platform": platform.platform(), "machine": platform.machine(),
                         "processor": platform.processor(), "logical_cpus": os.cpu_count(),
                         "python": platform.python_version()},
            "config": {"mode": mode, "level": level, "steps_per_worker": steps,
                       "workers": workers, "warmup_steps_per_worker": warmup,
                       "repeats": repeats, "frame_skip": frame_skip},
            "scope": "Synthetic CPU simulation only. No rendering, models, gradients or game process. Observations included only in env mode. Reset costs included. Warmup actual frames reported separately. Multiworker end-to-end includes process startup/warmup/shutdown; not a steady-state-only claim.",
            "median_physics_fps_end_to_end": statistics.median(r["physics_frames_per_second_end_to_end"] for r in trials),
            "median_decisions_per_second_end_to_end": statistics.median(r["decisions_per_second_end_to_end"] for r in trials),
            "trials": trials}
