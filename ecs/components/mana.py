from dataclasses import dataclass


@dataclass
class Mana:
    """Mana point tracking component."""
    current: int
    maximum: int
