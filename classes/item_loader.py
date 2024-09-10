import json
import os
from classes.item import Item, Equipment

def load_items():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, '..', 'data', 'items.json')
    
    with open(json_path, 'r') as file:
        data = json.load(file)

    consumables = []
    equipment = []

    for item_data in data['consumables']:
        effect = create_effect(item_data['effect'], item_data['value'])
        item = Item(item_data['name'], item_data['char'], effect, item_data.get('duration', None))
        consumables.append(item)

    for item_data in data['equipment']:
        item = Equipment(item_data['name'], item_data['char'], item_data['slot'], item_data['stat_boost'])
        equipment.append(item)

    all_items = consumables + equipment
    return consumables, equipment, all_items

def create_effect(effect_type, value):
    if effect_type == 'heal':
        return lambda e: e.heal(value)
    elif effect_type == 'restore_mana':
        return lambda e: e.restore_mana(value)
    elif effect_type == 'boost_strength':
        return lambda e: e.apply_temporary_boost('strength', value, 50)  # 50 turns duration
    elif effect_type == 'boost_dexterity':
        return lambda e: e.apply_temporary_boost('dexterity', value, 50)  # 50 turns duration
    else:
        return lambda e: None  # Null effect if not recognized

all_consumables, all_equipment, all_items = load_items()