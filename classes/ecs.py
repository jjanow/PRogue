from dataclasses import dataclass, field
from collections import Counter
from typing import Dict, List

# Energy required for any entity to take one action.
ACTION_COST = 100


@dataclass
class PositionComponent:
    x: int
    y: int


@dataclass
class RenderableComponent:
    char: str


@dataclass
class HealthComponent:
    health: float
    max_health: float


@dataclass
class EnergyComponent:
    energy: float = 0.0
    speed: int = 100


@dataclass
class StatsComponent:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    willpower: int = 10
    charisma: int = 10
    appearance: int = 10
    perception: int = 10
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100


@dataclass
class CombatStatsComponent:
    base_damage: float = 0.0
    base_defense: float = 0.0


@dataclass
class InventoryComponent:
    items: Counter = field(default_factory=Counter)


@dataclass
class EquipmentComponent:
    slots: Dict = field(default_factory=dict)


@dataclass
class ManaComponent:
    mana: float = 10.0
    max_mana: float = 10.0
    psi: float = 10.0
    max_psi: float = 10.0


@dataclass
class CharacterInfoComponent:
    name: str = ""
    race: str = ""
    gender: str = ""
    sex: str = ""
    deity: str = "None"
    birth: str = "Unknown"
    month: str = "Unknown"
    day: str = "Unknown"
    age: int = 0


@dataclass
class MoneyComponent:
    money: int = 0


@dataclass
class PlayerTagComponent:
    pass


@dataclass
class AITagComponent:
    behavior: str = "basic"


@dataclass
class LootComponent:
    xp_reward: int = 0
    gold_reward: int = 0
    loot: List = field(default_factory=list)


@dataclass
class StatusEffectsComponent:
    boosts: Dict = field(default_factory=dict)
    poisoned: bool = False
    hunger: int = 0
