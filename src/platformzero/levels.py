"""Load authored synthetic JSON geometry, never commercial game maps."""
from importlib.resources import files
import json
from pathlib import Path

from .core import Level, exact_keys

EXAMPLES = ("runway", "two_gaps", "steps_and_spikes")


def example_names():
    return EXAMPLES


def parse_level(text):
    value = json.loads(text)
    exact_keys(value, ("schema", "authorship", "level"), "map")
    if value["schema"] != "platformzero-map-v1":
        raise ValueError("Unsupported map schema")
    if not isinstance(value["authorship"], str) or not 1 <= len(value["authorship"]) <= 256:
        raise ValueError("Map requires an authorship string")
    return Level.from_dict(value["level"])


def load_example(name="two_gaps"):
    if name not in EXAMPLES:
        raise ValueError(f"Unknown example {name!r}; choose from {EXAMPLES}")
    return parse_level(files("platformzero").joinpath("maps").joinpath(name + ".json").read_text(encoding="utf-8"))


def load_level(path):
    """Read this project's small JSON schema; no .bin/native-game importer."""
    p = Path(path)
    if p.suffix.lower() != ".json" or p.stat().st_size > 1000000:
        raise ValueError("Expected a PlatformZero JSON map <=1 MB")
    return parse_level(p.read_text(encoding="utf-8"))
