from __future__ import annotations
import json
import os
from typing import Any, Callable, Optional, TYPE_CHECKING
from classes.item import Item, Equipment

if TYPE_CHECKING:
    from classes.entity import Entity


class Material:
    def __init__(self, name: str, power: float) -> None:
        self.name = name
        self.power = power
        # Higher tier materials are worth more
        self.value_multiplier: float = power


def load_materials() -> list[Material]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    materials_path = os.path.join(script_dir, '..', 'data', 'materials', 'materials.json')
    with open(materials_path, 'r') as f:
        material_data: list[dict[str, Any]] = json.load(f)
    return [Material(m['name'], m['power']) for m in material_data]


def load_items() -> tuple[
    list[Item],
    list[Equipment],
    list[Item],
    list[Material],
    list[Item | Equipment],
]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    items_dir = os.path.join(script_dir, '..', 'data', 'items')

    consumables_path = os.path.join(items_dir, 'consumables.json')
    with open(consumables_path, 'r') as file:
        consumable_data: list[dict[str, Any]] = json.load(file)

    all_mats = load_materials()

    consumables: list[Item] = []
    for item_data in consumable_data:
        effect = create_effect(item_data['effect'], item_data['value'], item_data.get('duration', None))
        item = Item(
            item_data['name'],
            effect,
            item_data.get('duration', None),
            value=item_data.get('value'),
            weight=item_data.get('weight', 1),
            effect_type=item_data.get('effect'),
            gold_value=item_data.get('gold', 10),
            material_type=item_data.get('material_type'),
        )
        consumables.append(item)

    equipment: list[Equipment] = []
    misc_items: list[Item] = []
    for fname in os.listdir(items_dir):
        if not fname.endswith('.json') or fname == 'consumables.json':
            continue
        path = os.path.join(items_dir, fname)
        with open(path, 'r') as file:
            items: list[dict[str, Any]] = json.load(file)
        for item_data in items:
            accuracy: float = item_data.get('accuracy', 0)
            material_type: Optional[str] = item_data.get('material_type')
            # Check for either 'slot' or 'type' field to determine if it's equipment
            slot: Optional[str] = item_data.get('slot') or item_data.get('type')
            if slot:
                eq = Equipment(
                    item_data['name'],
                    slot,
                    item_data.get('body_part', 'unknown'),
                    0,
                    damage=item_data.get('damage'),
                    ac=item_data.get('ac'),
                    accuracy_bonus=accuracy,
                    weight=item_data.get('weight', 1),
                    material_type=material_type,
                    gold_value=item_data.get('gold', 50),
                )
                equipment.append(eq)
            else:
                no_effect: Callable[[Entity], None] = lambda e: None
                misc = Item(
                    item_data['name'],
                    no_effect,
                    weight=item_data.get('weight', 1),
                    gold_value=item_data.get('gold', 0),
                    material_type=material_type,
                )
                misc_items.append(misc)

    all_items: list[Item | Equipment] = consumables + equipment + misc_items  # type: ignore[assignment]
    return consumables, equipment, misc_items, all_mats, all_items


def create_effect(
    effect_type: str,
    value: Any,
    duration: Any,
) -> Callable[[Entity], Any]:
    fn: Callable[[Entity], Any]
    if effect_type == 'heal':
        fn = lambda e: e.heal(value)
    elif effect_type == 'restore_mana':
        fn = lambda e: e.restore_mana(value)
    elif effect_type == 'boost_strength':
        fn = lambda e: e.apply_temporary_boost('strength', value, duration)
    elif effect_type == 'boost_dexterity':
        fn = lambda e: e.apply_temporary_boost('dexterity', value, duration)
    elif effect_type == 'boost_constitution':
        fn = lambda e: e.apply_temporary_boost('constitution', value, duration)
    elif effect_type == 'boost_intelligence':
        fn = lambda e: e.apply_temporary_boost('intelligence', value, duration)
    elif effect_type == 'boost_speed':
        fn = lambda e: e.apply_temporary_boost('speed', value, duration)
    elif effect_type == 'boost_charisma':
        fn = lambda e: e.apply_temporary_boost('charisma', value, duration)
    elif effect_type == 'cure_poison':
        fn = lambda e: e.cure_poison()
    elif effect_type == 'satiate':
        fn = lambda e: e.satiate(value)
    elif effect_type == 'identify':
        fn = lambda e: e.identify_item()
    elif effect_type == 'detect_magic':
        fn = lambda e: e.detect_magic()
    elif effect_type == 'light':
        fn = lambda e: e.cast_light()
    elif effect_type in ('poison', 'damage'):
        fn = lambda e: e.take_damage(value)
    else:
        fn = lambda e: f"Unknown effect: {effect_type}"
    return fn


(
    all_consumables,
    all_equipment,
    all_misc,
    all_materials,
    all_items,
) = load_items()
