from __future__ import annotations
from typing import Any, Callable, Optional


class Item:
    def __init__(
        self,
        name: str,
        effect: Optional[Callable[..., Any]],
        duration: Optional[int] = None,
        value: Optional[float] = None,
        weight: int = 1,
        effect_type: Optional[str] = None,
        gold_value: float = 0,
        material_type: Optional[str] = None,
    ) -> None:
        self.name = name
        self.effect = effect
        self.duration = duration
        self.value = value
        self.weight = weight
        self.effect_type = effect_type
        self.gold_value = gold_value
        self.material_type = material_type
        self.x: Optional[int] = None
        self.y: Optional[int] = None
        self.quantity = 1
        # Track whether the player has seen this item on the ground. Items should
        # only be visible outside the current field of view after they have been
        # discovered once.
        self.seen = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Item):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'effect': self.effect.__name__ if self.effect else None,
            'duration': self.duration,
            'value': self.value,
            'weight': self.weight,
            'effect_type': self.effect_type,
            'gold_value': self.gold_value,
            'material_type': self.material_type,
            'x': self.x,
            'y': self.y,
            'quantity': self.quantity,
            'seen': self.seen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Item:
        if data.get('effect_type'):
            from classes.item_loader import create_effect
            effect = create_effect(data['effect_type'], data.get('value'), data.get('duration'))
        else:
            effect = None

        item = cls(
            name=data['name'],
            effect=effect,
            duration=data.get('duration'),
            value=data.get('value'),
            weight=data.get('weight', 1),
            effect_type=data.get('effect_type'),
            gold_value=data.get('gold_value', 0),
            material_type=data.get('material_type'),
        )
        item.x = data.get('x')
        item.y = data.get('y')
        item.quantity = data.get('quantity', 1)
        item.seen = data.get('seen', False)
        return item


class Equipment(Item):
    def __init__(
        self,
        name: str,
        slot: str,
        body_part: str,
        stat_boost: float,
        damage: dict[str, int] | int | None = None,
        ac: Optional[int] = None,
        accuracy_bonus: float = 0,
        weight: int = 1,
        material_type: Optional[str] = None,
        gold_value: float = 0,
    ) -> None:
        super().__init__(name, None, None, None, weight, None, gold_value)
        self.slot = slot
        self.body_part = body_part
        self.damage: dict[str, int] | int | None = damage
        self.ac: int = ac if ac is not None else 0
        self.stat_boost = stat_boost

        # Separate bonuses allow items to affect different stats
        if slot in ['weapon', 'missile weapon']:
            self.damage_bonus: float = stat_boost
            self.defense_bonus: float = 0
        else:
            self.damage_bonus = 0
            self.defense_bonus = stat_boost

        self.accuracy_bonus = accuracy_bonus
        self.material_type = material_type

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'slot': self.slot,
            'body_part': self.body_part,
            'damage': self.damage,
            'ac': self.ac,
            'stat_boost': self.stat_boost,
            'damage_bonus': self.damage_bonus,
            'defense_bonus': self.defense_bonus,
            'accuracy_bonus': self.accuracy_bonus,
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Equipment:
        equipment = cls(
            name=data['name'],
            slot=data['slot'],
            body_part=data['body_part'],
            stat_boost=data['stat_boost'],
            damage=data.get('damage'),
            ac=data.get('ac'),
            accuracy_bonus=data.get('accuracy_bonus', 0),
            weight=data.get('weight', 1),
            material_type=data.get('material_type'),
            gold_value=data.get('gold_value', 0),
        )
        equipment.x = data.get('x')
        equipment.y = data.get('y')
        equipment.quantity = data.get('quantity', 1)
        equipment.seen = data.get('seen', False)
        return equipment
