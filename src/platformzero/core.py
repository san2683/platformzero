"""Synthetic fixed-step physics adapted from the project's generic core.

Units: metres/seconds; y points down. This is not Celeste physics.
No game assets, rendering, learning framework, or native-game bridge is used.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math

DT = 1 / 60
ENGINE = "platformzero-synthetic-v1"
DIRECTIONS = ((0, 0), (1, 0), (1, -1), (0, -1), (-1, -1),
              (-1, 0), (-1, 1), (0, 1), (1, 1))


def number(value, name, low=None, high=None):
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number")
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f"{name} outside allowed range")
    return value


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def boolean(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be boolean")
    return value


def exact_keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name}: missing or unknown fields")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Action:
    move: int = 0
    jump: bool = False
    dash: int = 0

    def __post_init__(self):
        integer(self.move, "move", -1, 1)
        boolean(self.jump, "jump")
        integer(self.dash, "dash", 0, 8)

    @classmethod
    def from_indices(cls, values):
        if not isinstance(values, (tuple, list)) or len(values) != 3:
            raise ValueError("Action indices must be [horizontal 0..2, jump 0..1, dash 0..8]")
        move, jump, dash = values
        return cls(integer(move, "horizontal", 0, 2) - 1,
                   bool(integer(jump, "jump index", 0, 1)), integer(dash, "dash", 0, 8))


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def __post_init__(self):
        for name in ("x", "y", "w", "h"):
            number(getattr(self, name), name, -1e6, 1e6)
        if self.w <= 0 or self.h <= 0:
            raise ValueError("Rectangle dimensions must be positive")


@dataclass(frozen=True)
class Rules:
    gravity: float = 24.0
    speed: float = 6.0
    jump_speed: float = 10.0
    jumps: int = 1
    dash: bool = True
    dash_speed: float = 16.0
    dash_duration: float = 0.15
    variable_jump: bool = True
    jump_cut: float = 0.45

    def __post_init__(self):
        for name, low, high in (("gravity", 1, 50), ("speed", 1, 20),
                               ("jump_speed", 1, 20), ("dash_speed", 1, 30),
                               ("dash_duration", .05, .5), ("jump_cut", .1, 1)):
            number(getattr(self, name), name, low, high)
        integer(self.jumps, "jumps", 1, 2)
        boolean(self.dash, "dash"); boolean(self.variable_jump, "variable_jump")


@dataclass(frozen=True)
class Level:
    name: str
    width: float
    height: float
    platforms: tuple[Rect, ...]
    hazards: tuple[Rect, ...]
    spawn: tuple[float, float]
    goal: Rect
    rules: Rules = Rules()

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or len(self.name) > 128:
            raise ValueError("Level name must be a nonempty string <=128 characters")
        number(self.width, "width", 1, 1e5); number(self.height, "height", 1, 1e5)
        if not isinstance(self.rules, Rules) or not isinstance(self.goal, Rect):
            raise ValueError("Level requires Rules and Rect objects")
        for key in ("platforms", "hazards"):
            values = tuple(getattr(self, key))
            if len(values) > 2000 or any(not isinstance(v, Rect) for v in values):
                raise ValueError("Invalid geometry")
            object.__setattr__(self, key, values)
        if not isinstance(self.spawn, (tuple, list)) or len(self.spawn) != 2:
            raise ValueError("spawn must be [x,y]")
        for rect in self.platforms + self.hazards + (self.goal,):
            if rect.x < 0 or rect.y < 0 or rect.x + rect.w > self.width + 1e-9 or rect.y + rect.h > self.height + 1e-9:
                raise ValueError("Geometry must be within level bounds")
        object.__setattr__(self, "spawn", tuple(self.spawn))
        x, y = self.spawn
        number(x, "spawn x", 0, self.width - .55)
        number(y, "spawn y", 0, self.height - .8)
        player = Rect(x, y, .55, .8)
        if any(overlaps(player, r) for r in self.platforms + self.hazards):
            raise ValueError("spawn intersects solid or hazard")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        exact_keys(value, ("name", "width", "height", "platforms", "hazards", "spawn", "goal", "rules"), "level")
        if not isinstance(value["rules"], dict):
            raise ValueError("rules must be a mapping")
        try:
            return cls(value["name"], value["width"], value["height"],
                       tuple(Rect(**r) for r in value["platforms"]),
                       tuple(Rect(**r) for r in value["hazards"]),
                       tuple(value["spawn"]), Rect(**value["goal"]), Rules(**value["rules"]))
        except (TypeError, KeyError) as exc:
            raise ValueError("Invalid level fields") from exc


def overlaps(a, b):
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y


class World:
    player_w = .55
    player_h = .8

    def __init__(self, level, max_frames=1800):
        if not isinstance(level, Level):
            raise ValueError("level must be a Level")
        self.level = level
        self.max_frames = integer(max_frames, "max_frames", 1, 10000000)
        self.x, self.y = level.spawn
        self.vx = self.vy = 0.0
        self.grounded = self.supported()
        self.jumps_left = level.rules.jumps if self.grounded else level.rules.jumps - 1
        self.dash_ready = level.rules.dash
        self.dash_frames = 0
        self.jump_held = self.dash_held = self.jump_active = False
        self.frames = 0
        self.max_x = self.x
        self.total_reward = self.last_reward = 0.0
        self.status = "playing"
        self.last_terms = {}
        self.last_action = Action()

    @property
    def player(self):
        return Rect(self.x, self.y, self.player_w, self.player_h)

    def supported(self):
        return self.vy >= 0 and any(
            abs(self.y + self.player_h - p.y) < 1e-6
            and self.x < p.x + p.w and self.x + self.player_w > p.x
            for p in self.level.platforms)

    def touches(self, rect):
        # Geometry is validated once at load time; no per-substep Rect allocation.
        return (self.x < rect.x + rect.w and self.x + self.player_w > rect.x
                and self.y < rect.y + rect.h and self.y + self.player_h > rect.y)

    def tick(self, action):
        if not isinstance(action, Action):
            raise ValueError("tick requires a semantic Action")
        if self.status != "playing":
            return 0.0
        rules = self.level.rules
        self.frames += 1
        jump_edge = action.jump and not self.jump_held
        jump_release = self.jump_held and not action.jump
        dash_edge = bool(action.dash) and not self.dash_held
        was_grounded = self.grounded
        self.jump_held, self.dash_held = action.jump, bool(action.dash)
        self.last_action = action
        if dash_edge and self.dash_ready:
            self.jump_active = False
            dx, dy = DIRECTIONS[action.dash]
            norm = math.hypot(dx, dy)
            self.vx, self.vy = rules.dash_speed * dx / norm, rules.dash_speed * dy / norm
            self.dash_frames = round(rules.dash_duration / DT)
            self.dash_ready = False
        if not self.dash_frames:
            self.vx = action.move * rules.speed
            if jump_edge and self.jumps_left > 0:
                self.vy = -rules.jump_speed
                self.jumps_left -= 1
                self.jump_active = True
            if rules.variable_jump and jump_release and self.jump_active and self.vy < 0:
                self.vy *= rules.jump_cut
                self.jump_active = False
            self.vy = min(self.vy + rules.gravity * DT, 20.0)
        else:
            self.dash_frames -= 1
        count = max(1, math.ceil(max(abs(self.vx * DT), abs(self.vy * DT)) / .1))
        landed = False
        for _ in range(count):
            old_x = self.x
            self.x = max(0.0, min(self.x + self.vx * DT / count, self.level.width - self.player_w))
            for rect in self.level.platforms:
                if self.touches(rect):
                    self.x = rect.x - self.player_w if self.x > old_x else rect.x + rect.w
                    self.vx = 0.0
            old_y = self.y
            self.y += self.vy * DT / count
            for rect in self.level.platforms:
                if self.touches(rect):
                    if self.vy >= 0 and old_y + self.player_h <= rect.y + 1e-6:
                        self.y = rect.y - self.player_h
                        landed = True
                    elif self.vy < 0:
                        self.y = rect.y + rect.h
                    self.vy = 0.0
            if any(self.touches(hazard) for hazard in self.level.hazards):
                self.status = "dead"
                break
        self.grounded = landed or self.supported()
        if self.grounded:
            self.jumps_left = rules.jumps
            if not was_grounded:
                self.dash_ready = rules.dash
            self.jump_active = False
        elif self.jumps_left == rules.jumps:
            self.jumps_left -= 1
        if self.vy >= 0:
            self.jump_active = False
        if self.y > self.level.height:
            self.status = "dead"
        if self.status == "playing" and self.touches(self.level.goal):
            self.status = "success"
        if self.status == "playing" and self.frames >= self.max_frames:
            self.status = "timeout"
        progress = max(0.0, self.x - self.max_x) / self.level.width
        self.max_x = max(self.max_x, self.x)
        self.last_terms = {"progress": progress, "time": -.001,
                           "success": 10.0 if self.status == "success" else 0.0,
                           "death": -2.0 if self.status == "dead" else 0.0}
        self.last_reward = sum(self.last_terms.values())
        self.total_reward += self.last_reward
        return self.last_reward

    def get_state(self):
        dynamic = {name: getattr(self, name) for name in (
            "x", "y", "vx", "vy", "grounded", "jumps_left", "dash_ready", "dash_frames",
            "jump_held", "dash_held", "jump_active", "frames", "max_x", "total_reward",
            "last_reward", "status")}
        dynamic["last_terms"] = dict(self.last_terms)
        dynamic["last_action"] = asdict(self.last_action)
        level = self.level.to_dict()
        return {"schema": 1, "engine": ENGINE, "level": level, "level_sha256": digest(level),
                "max_frames": self.max_frames, "dynamic": dynamic}

    @classmethod
    def from_state(cls, state):
        exact_keys(state, ("schema", "engine", "level", "level_sha256", "max_frames", "dynamic"), "world state")
        if type(state["schema"]) is not int or state["schema"] != 1 or state["engine"] != ENGINE:
            raise ValueError("Incompatible world state version")
        level = Level.from_dict(state["level"])
        if digest(level.to_dict()) != state["level_sha256"]:
            raise ValueError("Level fingerprint mismatch")
        result = cls(level, state["max_frames"])
        fields = result.get_state()["dynamic"]
        d = state["dynamic"]
        exact_keys(d, fields, "dynamic state")
        for name in ("x", "y", "vx", "vy", "max_x", "total_reward", "last_reward"):
            number(d[name], name)
        number(d["x"], "x", 0, level.width - cls.player_w)
        number(d["max_x"], "max_x", d["x"], level.width)
        for name in ("grounded", "dash_ready", "jump_held", "dash_held", "jump_active"):
            boolean(d[name], name)
        integer(d["frames"], "frames", 0, result.max_frames)
        integer(d["jumps_left"], "jumps_left", 0, level.rules.jumps)
        integer(d["dash_frames"], "dash_frames", 0, round(level.rules.dash_duration / DT))
        if d["status"] not in ("playing", "dead", "success", "timeout"):
            raise ValueError("Invalid status")
        if (d["status"] == "playing" and d["frames"] >= result.max_frames
                or d["status"] == "timeout" and d["frames"] != result.max_frames):
            raise ValueError("Inconsistent terminal/frame state")
        if not isinstance(d["last_terms"], dict) or set(d["last_terms"]) not in (set(), {"progress", "time", "success", "death"}):
            raise ValueError("Invalid reward terms")
        for value in d["last_terms"].values():
            number(value, "reward term")
        if sum(d["last_terms"].values()) != d["last_reward"]:
            raise ValueError("Reward sum mismatch")
        exact_keys(d["last_action"], ("move", "jump", "dash"), "last action")
        action = Action(**d["last_action"])
        if d["jump_held"] != action.jump or d["dash_held"] != bool(action.dash):
            raise ValueError("Button-history mismatch")
        for key in fields:
            if key not in ("last_action", "last_terms"):
                setattr(result, key, d[key])
        result.last_terms = dict(d["last_terms"])
        result.last_action = action
        return result
