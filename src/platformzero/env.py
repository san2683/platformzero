"""Minimal five-value environment API without Gymnasium/NumPy dependencies."""
import random

from .core import Action, DT, World, exact_keys, integer
from .levels import load_example


def tuple_tree(value):
    return tuple(tuple_tree(v) for v in value) if isinstance(value, (tuple, list)) else value


class HeadlessEnv:
    action_shape = (3, 2, 9)
    observation_schema = "platformzero-state-v1"

    def __init__(self, level=None, *, frame_skip=4, max_frames=1800, seed=0):
        self.level = load_example() if level is None else level
        self.frame_skip = integer(frame_skip, "frame_skip", 1, 8)
        self.max_frames = integer(max_frames, "max_frames", 1, 10000000)
        integer(seed, "seed", 0, 2**32 - 1)
        self.rng = random.Random(seed)
        self.world = None

    def reset(self, *, seed=None):
        if seed is not None:
            self.rng = random.Random(integer(seed, "seed", 0, 2**32 - 1))
        self.world = World(self.level, self.max_frames)
        return self.observe(), self.info()

    def sample_action(self):
        return (self.rng.randrange(3), self.rng.randrange(2), self.rng.randrange(9))

    def step(self, action):
        if self.world is None or self.world.status != "playing":
            raise RuntimeError("reset() before stepping or after an episode ends")
        semantic = action if isinstance(action, Action) else Action.from_indices(action)
        reward = 0.0; terms = {}; start = self.world.frames
        for _ in range(self.frame_skip):
            reward += self.world.tick(semantic)
            for key, value in self.world.last_terms.items():
                terms[key] = terms.get(key, 0.0) + value
            if self.world.status != "playing":
                break
        info = self.info()
        info.update(physics_frames_delta=self.world.frames - start, reward_terms=terms)
        return (self.observe(), reward, self.world.status in ("dead", "success"),
                self.world.status == "timeout", info)

    def observe(self):
        if self.world is None:
            raise RuntimeError("reset() first")
        w = self.world
        return {"position": (w.x, w.y), "velocity": (w.vx, w.vy),
                "grounded": w.grounded, "jumps_left": w.jumps_left,
                "dash_ready": w.dash_ready, "dash_frames": w.dash_frames,
                "jump_held": w.jump_held, "dash_held": w.dash_held,
                "frames_remaining": w.max_frames - w.frames}

    def info(self):
        if self.world is None:
            raise RuntimeError("reset() first")
        w = self.world
        return {"level": w.level.name, "observation_schema": self.observation_schema,
                "status": w.status, "is_success": w.status == "success",
                "physics_frames": w.frames, "simulated_seconds": w.frames * DT,
                "episode_return": w.total_reward}

    def get_state(self):
        if self.world is None:
            raise RuntimeError("reset() first")
        return {"schema": "platformzero-env-state-v1", "frame_skip": self.frame_skip,
                "world": self.world.get_state(), "sampler_rng": self.rng.getstate()}

    def set_state(self, state):
        """Validate and install atomically; input can come from JSON round-trip."""
        exact_keys(state, ("schema", "frame_skip", "world", "sampler_rng"), "env state")
        if state["schema"] != "platformzero-env-state-v1":
            raise ValueError("Incompatible env state version")
        frame_skip = integer(state["frame_skip"], "frame_skip", 1, 8)
        world = World.from_state(state["world"])
        rng = random.Random()
        try:
            rng.setstate(tuple_tree(state["sampler_rng"]))
        except (TypeError, ValueError, OverflowError, IndexError) as exc:
            raise ValueError("Invalid sampler RNG state") from exc
        self.frame_skip, self.world, self.rng = frame_skip, world, rng
        self.level, self.max_frames = world.level, world.max_frames
