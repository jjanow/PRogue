from dataclasses import dataclass


@dataclass
class Renderable:
    """Visual representation component."""
    char: str
    color: int
