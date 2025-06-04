from dataclasses import dataclass


@dataclass
class Position:
    """Grid position component."""
    x: int
    y: int
