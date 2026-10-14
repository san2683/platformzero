"""A dependency-free, headless synthetic platformer backend."""
from .core import Action, DT, Level, Rect, Rules, World
from .env import HeadlessEnv
from .levels import example_names, load_example, load_level

__version__ = "0.1.0"
__all__ = ["Action", "DT", "Level", "Rect", "Rules", "World", "HeadlessEnv",
           "example_names", "load_example", "load_level"]
