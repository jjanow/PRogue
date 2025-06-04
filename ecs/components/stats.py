from dataclasses import dataclass


@dataclass
class Stats:
    """Core statistics component."""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    willpower: int = 10
    charisma: int = 10
    appearance: int = 10
    perception: int = 10
