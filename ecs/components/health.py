from dataclasses import dataclass


@dataclass
class Health:
    """Hit point tracking component."""
    current: int
    maximum: int
