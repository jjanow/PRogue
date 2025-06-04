from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Velocity:
    dx: int
    dy: int

@dataclass
class Renderable:
    char: str
    color: int = 1

@dataclass
class Fighter:
    health: int
    max_health: int
    damage: int
    defense: int

@dataclass
class AI:
    state: str = "idle"

@dataclass
class Item:
    reference: Any

@dataclass
class FieldOfView:
    radius: int
    visible: List[List[bool]] = field(default_factory=list)
    explored: List[List[bool]] = field(default_factory=list)

@dataclass
class PlayerInput:
    pass
