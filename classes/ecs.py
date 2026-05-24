from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from classes.item import Item, Equipment

# Energy required for any entity to take one action.
ACTION_COST = 100


class EquipmentSlot(TypedDict):
    name: str
    item: Optional[Equipment]


class BoostEffect(TypedDict):
    value: float
    duration: int


def _empty_counter() -> Counter[Item]:
    return Counter()


def _empty_equipment_slots() -> dict[str, EquipmentSlot]:
    return {}


def _empty_loot() -> list[Item]:
    return []


def _empty_boosts() -> dict[str, BoostEffect]:
    return {}


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
    items: Counter[Item] = field(default_factory=_empty_counter)


@dataclass
class EquipmentComponent:
    slots: dict[str, EquipmentSlot] = field(default_factory=_empty_equipment_slots)


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
    loot: list[Item] = field(default_factory=_empty_loot)


@dataclass
class StatusEffectsComponent:
    boosts: dict[str, BoostEffect] = field(default_factory=_empty_boosts)
    poisoned: bool = False
    hunger: int = 0


@dataclass
class AIStateComponent:
    state: str = "idle"  # "asleep" | "idle" | "alert"
    wander_dx: int = 0
    wander_dy: int = 0
    wander_turns_left: int = 0
