import os
import json
import random
from classes.item import Item, Equipment
from classes.item_loader import all_items, materials_by_type, all_materials

class MonsterTemplate:
    def __init__(self, name, xp, gold, items, challenge_rating, archetype):
        self.name = name
        self.xp = xp
        self.gold = gold
        self.item_names = items
        self.challenge_rating = challenge_rating
        self.archetype = archetype

    def create_loot(self):
        loot = []
        for item_name in self.item_names:
            template = next((i for i in all_items if i.name == item_name), None)
            if template:
                if isinstance(template, Equipment):
                    mats = materials_by_type.get(template.material_type, all_materials)
                    mat = random.choice(mats)
                    loot_item = Equipment(
                        f"{mat.name} {template.name}",
                        template.slot,
                        template.body_part,
                        mat.power,
                        damage=template.damage,
                        ac=template.ac,
                        accuracy_bonus=template.accuracy_bonus,
                        weight=template.weight,
                        material_type=template.material_type,
                    )
                else:
                    loot_item = Item(
                        template.name,
                        template.effect,
                        duration=getattr(template, 'duration', None),
                        value=getattr(template, 'value', None),
                        weight=template.weight,
                        effect_type=getattr(template, 'effect_type', None),
                    )
            else:
                # Generic placeholder item
                loot_item = Item(item_name, lambda e: None)
            loot.append(loot_item)
        return loot

def load_monsters():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    monsters_dir = os.path.join(script_dir, '..', 'data', 'monsters')
    templates = []
    for fname in os.listdir(monsters_dir):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(monsters_dir, fname), 'r') as f:
            data = json.load(f)
        for m in data:
            templates.append(
                MonsterTemplate(
                    m['name'],
                    m.get('xp', 0),
                    m.get('gold', 0),
                    m.get('items', []),
                    m.get('challenge_rating', 1),
                    m.get('archetype', 'unknown'),
                )
            )
    return templates

all_monsters = load_monsters()
