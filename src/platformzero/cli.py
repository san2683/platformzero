"""Installed headless sampling and benchmark commands."""
import argparse
import json
from pathlib import Path
import time

from . import __version__
from .benchmark import run_benchmark
from .env import HeadlessEnv
from .levels import example_names, load_example


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def nonnegative(value):
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def emit(result, output):
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if output:
        p = Path(output); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


def sample(args):
    env = HeadlessEnv(load_example(args.level), frame_skip=args.frame_skip, seed=args.seed)
    totals = {"physics_frames": 0, "decisions": 0, "success": 0, "dead": 0, "timeout": 0}
    start = time.perf_counter()
    for _ in range(args.episodes):
        env.reset()
        while env.world.status == "playing":
            action = env.sample_action() if args.policy == "random" else (2, 0, 0)
            *_, info = env.step(action)
            totals["physics_frames"] += info["physics_frames_delta"]
            totals["decisions"] += 1
        totals[env.world.status] += 1
    wall = time.perf_counter() - start
    return {"version": __version__, "level": args.level, "seed": args.seed,
            "policy": args.policy, "episodes": args.episodes, "rendering": False,
            "frame_skip": args.frame_skip, "actual": totals, "wall_seconds": wall,
            "physics_frames_per_second": totals["physics_frames"] / wall}


def main(argv=None):
    parser = argparse.ArgumentParser(description="PlatformZero headless synthetic simulator")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    s = commands.add_parser("sample", help="sample complete episodes without rendering")
    s.add_argument("--level", choices=example_names(), default="two_gaps")
    s.add_argument("--episodes", type=positive, default=10)
    s.add_argument("--seed", type=nonnegative, default=0)
    s.add_argument("--policy", choices=("random", "right"), default="random")
    s.add_argument("--frame-skip", type=int, choices=range(1,9), default=4)
    s.add_argument("--output")
    b = commands.add_parser("benchmark", help="measure actual CPU sampling throughput")
    b.add_argument("--mode", choices=("physics", "env"), default="env")
    b.add_argument("--level", choices=example_names(), default="two_gaps")
    b.add_argument("--steps", type=positive, default=100000)
    b.add_argument("--workers", type=positive, default=1)
    b.add_argument("--warmup", type=nonnegative, default=1000)
    b.add_argument("--repeats", type=positive, default=3)
    b.add_argument("--frame-skip", type=int, choices=range(1,9), default=4)
    b.add_argument("--output")
    args = parser.parse_args(argv)
    if args.command == "sample":
        if args.seed >= 2**32:
            parser.error("seed must be <2**32")
        result = sample(args)
    else:
        if args.workers > 64:
            parser.error("workers must be <=64")
        result = run_benchmark(mode=args.mode, level=args.level, steps=args.steps,
                               workers=args.workers, warmup=args.warmup,
                               repeats=args.repeats, frame_skip=args.frame_skip)
    emit(result, args.output)
    return 0
