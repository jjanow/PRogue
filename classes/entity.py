import random
from collections import Counter
from classes.item import Equipment, Item
from classes.item_loader import (
    all_consumables,
    all_equipment,
    materials_by_type,
    all_materials,
)


class Entity:
    def __init__(self, x, y, char, name, health, damage, defense):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.max_health = health
        self.health = health
        self.base_damage = damage
        self.base_defense = defense
        self.inventory = Counter()
        self.equipment = {
            'a': {'name': 'weapon', 'item': None},
            'b': {'name': 'missile weapon', 'item': None},
            'c': {'name': 'helmet', 'item': None},
            'd': {'name': 'amulet', 'item': None},
            'e': {'name': 'shield', 'item': None},
            'f': {'name': 'armor', 'item': None},
            'g': {'name': 'cloak', 'item': None},
            'h': {'name': 'girdle', 'item': None},
            'i': {'name': 'gauntlets', 'item': None},
            'j': {'name': 'boots', 'item': None},
            'k': {'name': 'ring (right)', 'item': None},
            'l': {'name': 'ring (left)', 'item': None},
            'm': {'name': 'bracers', 'item': None},
        }
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100        
        self.strength = 10
        self.dexterity = 10
        self.constitution = 10
        self.intelligence = 10
        self.willpower = 10
        self.charisma = 10
        self.appearance = 10
        self.perception = 10
        self.speed = 100
        self.max_mana = 10
        self.mana = 10
        self.max_psi = 10
        self.psi = 10        
        self.money = 0
        self.deity = "None"
        self.birth = "Unknown"
        self.month = "Unknown"
        self.day = "Unknown"
        self.age = 0
        self.gender = ""
        self.sex = ""
        self.race = ""
    
    @property
    def damage(self):
        """Total damage output including stat and level bonuses."""
        weapon = next(
            (slot['item'] for slot in self.equipment.values() if slot['name'] in ['weapon', 'missile weapon']),
            None,
        )
        weapon_bonus = weapon.damage_bonus if weapon else 0

        # Every point of strength increases damage. Levels give a small bonus
        strength_bonus = self.get_stat('strength') * 0.5
        level_bonus = self.level * 0.5

        total_damage = self.base_damage + weapon_bonus + strength_bonus + level_bonus
        return round(total_damage, 1)

    @property
    def defense(self):
        """Total defense score including stat and level bonuses."""
        armor_bonus = sum(
            slot['item'].defense_bonus
            for slot in self.equipment.values()
            if slot['item']
        )

        # Every point of dexterity/constitution increases defense
        dexterity_bonus = self.get_stat('dexterity') * 0.3
        constitution_bonus = self.get_stat('constitution') * 0.2
        level_bonus = self.level * 0.5

        total_defense = (
            self.base_defense
            + armor_bonus
            + dexterity_bonus
            + constitution_bonus
            + level_bonus
        )
        return round(total_defense, 1)

    def equip(self, item, slot_key):
        slot = self.equipment[slot_key]
        if isinstance(item, Equipment) and item.slot == slot['name']:
            old_item = slot['item']
            slot['item'] = item
            if old_item:
                self.add_item(old_item)
            if item in self.inventory:
                self.remove_item(item)
            return f"Equipped {item.name} in {slot['name']} slot"
        return f"Cannot equip {item.name} in {slot['name']} slot"

    def use_item(self, item):
        if item in self.inventory:
            if isinstance(item, Equipment):
                return self.equip(item)
            else:
                effect_result = item.effect(self)
                self.remove_item(item)
                return effect_result
        return f"You don't have {item.name}"

    def add_item(self, item):
        # Check if an item with the same name already exists
        existing_item = next((i for i in self.inventory if i.name == item.name), None)
        if existing_item:
            self.inventory[existing_item] += 1
        else:
            self.inventory[item] = 1

    def remove_item(self, item):
        existing_item = next((i for i in self.inventory if i.name == item.name), None)
        if existing_item and self.inventory[existing_item] > 0:
            self.inventory[existing_item] -= 1
            if self.inventory[existing_item] == 0:
                del self.inventory[existing_item]
            return True
        return False

    def get_inventory_items(self):
        return list(self.inventory.items())

    def move(self, dx, dy, game):
        speed_multiplier = 1
        boots = self.equipment['j']['item']
        if boots and boots.name == "Boots of Speed":
            speed_multiplier = 1.5
        
        moves = int(self.speed * speed_multiplier / 100)
        for _ in range(moves):
            new_x, new_y = self.x + dx, self.y + dy
            if game.is_valid_move(new_x, new_y):
                self.x, self.y = new_x, new_y
            else:
                break
        return True

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        self.max_health += 10
        self.health = self.max_health
        
        # Increase stats randomly
        stats = ['strength', 'dexterity', 'constitution', 'intelligence', 'willpower', 'charisma', 'appearance', 'perception']
        for stat in stats:
            setattr(self, stat, getattr(self, stat) + random.randint(1, 2))
        
        self.speed += random.randint(1, 2)

    def initialize_player(self):
        # Add two healing potions to the player's inventory
        health_potion = next((item for item in all_consumables if item.name == "Health Potion"), None)
        if health_potion:
            self.add_item(health_potion)
            self.add_item(health_potion)

        # Equip the player with a basic dagger and robe
        dagger_base = next((item for item in all_equipment if item.name == "Dagger"), None)
        robe_base = next((item for item in all_equipment if item.name == "Robe"), None)
        bronze = next((m for m in materials_by_type.get('weapons', []) if m.name == "Bronze"), None)
        cloth = next((m for m in materials_by_type.get('cloth', []) if m.name == "Cloth"), None)

        if dagger_base and bronze:
            dagger = Equipment(
                f"{bronze.name} {dagger_base.name}",
                dagger_base.slot,
                dagger_base.body_part,
                bronze.power,
                damage=dagger_base.damage,
                ac=dagger_base.ac,
                accuracy_bonus=dagger_base.accuracy_bonus,
                weight=dagger_base.weight,
                material_type=dagger_base.material_type,
            )
            self.equip(dagger, 'a')  # 'a' is the weapon slot

        if robe_base and cloth:
            robe = Equipment(
                f"{cloth.name} {robe_base.name}",
                robe_base.slot,
                robe_base.body_part,
                cloth.power,
                damage=robe_base.damage,
                ac=robe_base.ac,
                weight=robe_base.weight,
                material_type=robe_base.material_type,
            )
            self.equip(robe, 'f')  # 'f' is the armor slot

    def heal(self, amount):
        """Heal the entity by the given amount and report the actual gain."""
        prev_health = self.health
        self.health = min(self.max_health, self.health + amount)
        gained = self.health - prev_health
        if gained > 0:
            return f"You healed for {gained} HP."
        return "You're already at full health."

    def apply_item_effect(self, item):
        if item.effect == 'heal':
            self.heal(item.value)
        elif item.effect == 'restore_mana':
            self.restore_mana(item.value)
        elif item.effect == 'boost_strength':
            self.apply_temporary_boost('strength', item.value, item.duration)
        elif item.effect == 'boost_dexterity':
            self.apply_temporary_boost('dexterity', item.value, item.duration)
        # Add more effects as needed

    def apply_temporary_boost(self, stat, value, duration):
        if not hasattr(self, 'temporary_boosts'):
            self.temporary_boosts = {}
        self.temporary_boosts[stat] = {'value': value, 'duration': duration}
        stat_name = stat.capitalize()
        return f"Your {stat_name} increases by {value} for {duration} turns."

    def update_temporary_boosts(self):
        messages = []
        if hasattr(self, 'temporary_boosts'):
            for stat, boost in list(self.temporary_boosts.items()):
                boost['duration'] -= 1
                if boost['duration'] <= 0:
                    del self.temporary_boosts[stat]
                    messages.append(f"Your {stat.capitalize()} boost wears off.")
        return messages

    def get_stat(self, stat):
        base_value = getattr(self, stat)
        if hasattr(self, 'temporary_boosts') and stat in self.temporary_boosts:
            return base_value + self.temporary_boosts[stat]['value']
        return base_value

    def restore_mana(self, amount):
        """Restore mana and report the actual amount recovered."""
        prev_mana = self.mana
        self.mana = min(self.max_mana, self.mana + amount)
        gained = self.mana - prev_mana
        if gained > 0:
            return f"You restored {gained} mana."
        return "Your mana is already full."

    def equip_item(self, item):
        for slot_key, slot in self.equipment.items():
            if slot['name'] == item.slot:
                if slot['item']:
                    self.add_item(slot['item'])  # Add currently equipped item back to inventory
                slot['item'] = item
                self.remove_item(item)
                return f"Equipped {item.name} in {slot['name']} slot."
        return f"No suitable slot found for {item.name}."

    def unequip_item(self, slot_key):
        slot = self.equipment.get(slot_key)
        if slot and slot['item']:
            self.add_item(slot['item'])
            slot['item'] = None
            return f"Unequipped item from {slot['name']} slot."
        return "No item to unequip in this slot."

    def get_equipped_items(self):
        return {key: slot['item'] for key, slot in self.equipment.items() if slot['item']}
