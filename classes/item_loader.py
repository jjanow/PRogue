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
            # Check for either 'slot' or 'type' field to determine if it's equipment
            slot = item_data.get('slot') or item_data.get('type')
            if slot:
                item = Equipment(
                    item_data['name'],
                    slot,  # Use the slot/type as the equipment slot
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

def create_effect(effect_type, value, duration):
    if effect_type == 'heal':
        return lambda e: e.heal(value)
    elif effect_type == 'restore_mana':
        return lambda e: e.restore_mana(value)
    elif effect_type == 'boost_strength':
        return lambda e: e.apply_temporary_boost('strength', value, duration)
    elif effect_type == 'boost_dexterity':
        return lambda e: e.apply_temporary_boost('dexterity', value, duration)
    elif effect_type == 'boost_constitution':
        return lambda e: e.apply_temporary_boost('constitution', value, duration)
    elif effect_type == 'boost_intelligence':
        return lambda e: e.apply_temporary_boost('intelligence', value, duration)
    elif effect_type == 'boost_speed':
        return lambda e: e.apply_temporary_boost('speed', value, duration)
    elif effect_type == 'boost_charisma':
        return lambda e: e.apply_temporary_boost('charisma', value, duration)
    elif effect_type == 'cure_poison':
        return lambda e: e.cure_poison()
    elif effect_type == 'satiate':
        return lambda e: e.satiate(value)
    elif effect_type == 'identify':
        return lambda e: e.identify_item()
    elif effect_type == 'detect_magic':
        return lambda e: e.detect_magic()
    elif effect_type == 'light':
        return lambda e: e.cast_light()
    elif effect_type in ('poison', 'damage'):
        return lambda e: e.take_damage(value)
    else:
        return lambda e: f"Unknown effect: {effect_type}"

def get_effect_function(effect_name):
    """Get an effect function by name for loading saved items."""
    # For now, return a simple lambda that does nothing
    # In a full implementation, you might want to store effect parameters
    # and recreate the full effect function
    if effect_name == 'heal':
        return lambda e: e.heal(10)  # Default heal value
    elif effect_name == 'restore_mana':
        return lambda e: e.restore_mana(10)  # Default mana value
    elif effect_name == 'cure_poison':
        return lambda e: e.cure_poison()
    elif effect_name == 'identify':
        return lambda e: e.identify_item()
    elif effect_name == 'detect_magic':
        return lambda e: e.detect_magic()
    elif effect_name == 'light':
        return lambda e: e.cast_light()
    else:
        return lambda e: f"Unknown effect: {effect_name}"

(
    all_consumables,
    all_equipment,
    all_misc,
    materials_by_type,
    all_materials,
    all_items,
) = load_items()
