import json
import os
from classes.item import Item, Equipment

class Material:
    def __init__(self, name, power):
        self.name = name
        self.power = power
        # Higher tier materials are worth more
        self.value_multiplier = power


def load_materials():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    materials_dir = os.path.join(script_dir, '..', 'data', 'materials')
    materials_by_type = {}
    all_materials = []

    for fname in os.listdir(materials_dir):
        if not fname.endswith('.json'):
            continue
        category = os.path.splitext(fname)[0]
        path = os.path.join(materials_dir, fname)
        with open(path, 'r') as file:
            material_data = json.load(file)
        mats = [Material(m['name'], m['power']) for m in material_data]
        materials_by_type[category] = mats
        all_materials.extend(mats)

    return materials_by_type, all_materials

def load_items():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    items_dir = os.path.join(script_dir, '..', 'data', 'items')

    consumables_path = os.path.join(items_dir, 'consumables.json')
    with open(consumables_path, 'r') as file:
        consumable_data = json.load(file)

    materials_by_type, all_materials = load_materials()

    consumables = []
    for item_data in consumable_data:
        effect = create_effect(item_data['effect'], item_data['value'])
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


    equipment = []
    misc_items = []
    for fname in os.listdir(items_dir):
        if not fname.endswith('.json') or fname == 'consumables.json':
            continue
        path = os.path.join(items_dir, fname)
        with open(path, 'r') as file:
            items = json.load(file)
        for item_data in items:
            accuracy = item_data.get('accuracy', 0)
            material_type = item_data.get('material_type')
            if 'slot' in item_data:
                item = Equipment(
                    item_data['name'],
                    item_data['slot'],
                    item_data.get('body_part', 'unknown'),
                    0,
                    damage=item_data.get('damage'),
                    ac=item_data.get('ac'),
                    accuracy_bonus=accuracy,
                    weight=item_data.get('weight', 1),
                    material_type=material_type,
                    gold_value=item_data.get('gold', 50),
                )
                equipment.append(item)
            else:
                item = Item(
                    item_data['name'],
                    lambda e: None,
                    weight=item_data.get('weight', 1),
                    gold_value=item_data.get('gold', 0),
                    material_type=material_type,
                )
                misc_items.append(item)

    all_items = consumables + equipment + misc_items
    return consumables, equipment, misc_items, materials_by_type, all_materials, all_items

def create_effect(effect_type, value):
    if effect_type == 'heal':
        return lambda e: e.heal(value)
    elif effect_type == 'restore_mana':
        return lambda e: e.restore_mana(value)
    elif effect_type == 'boost_strength':
        return lambda e: e.apply_temporary_boost('strength', value, 50)  # 50 turns duration
    elif effect_type == 'boost_dexterity':
        return lambda e: e.apply_temporary_boost('dexterity', value, 50)  # 50 turns duration
    elif effect_type in ('poison', 'damage'):
        return lambda e: e.take_damage(value)
    else:
        return lambda e: None  # Null effect if not recognized

(
    all_consumables,
    all_equipment,
    all_misc,
    materials_by_type,
    all_materials,
    all_items,
) = load_items()
