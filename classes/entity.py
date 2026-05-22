import random
from collections import Counter
from classes.item import Equipment
from classes.item_loader import (
    all_consumables,
    all_equipment,
    all_materials,
)
from classes.ecs import (
    PositionComponent,
    RenderableComponent,
    HealthComponent,
    EnergyComponent,
    StatsComponent,
    CombatStatsComponent,
    InventoryComponent,
    EquipmentComponent,
    ManaComponent,
    CharacterInfoComponent,
    MoneyComponent,
    LootComponent,
    StatusEffectsComponent,
)


def _make_equipment_slots():
    return {
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


class Entity:
    def __init__(self, x, y, char, name, health, damage, defense):
        # --- Components (all data lives here) ---
        self.position = PositionComponent(x, y)
        self.renderable = RenderableComponent(char)
        self.health_comp = HealthComponent(float(health), float(health))
        self.energy_comp = EnergyComponent()
        self.stats = StatsComponent()
        self.combat_stats = CombatStatsComponent(float(damage), float(defense))
        self.inventory_comp = InventoryComponent()
        self.equipment_comp = EquipmentComponent(slots=_make_equipment_slots())
        self.mana_comp = ManaComponent()
        self.char_info = CharacterInfoComponent(name=name)
        self.money_comp = MoneyComponent()
        self.loot_comp = LootComponent()
        self.status_comp = StatusEffectsComponent()

    def get_component(self, comp_type):
        for v in vars(self).values():
            if isinstance(v, comp_type):
                return v
        return None

    # ------------------------------------------------------------------
    # Property delegates — keep every existing attribute access working
    # ------------------------------------------------------------------

    @property
    def x(self): return self.position.x
    @x.setter
    def x(self, v): self.position.x = v

    @property
    def y(self): return self.position.y
    @y.setter
    def y(self, v): self.position.y = v

    @property
    def char(self): return self.renderable.char
    @char.setter
    def char(self, v): self.renderable.char = v

    @property
    def health(self): return self.health_comp.health
    @health.setter
    def health(self, v): self.health_comp.health = v

    @property
    def max_health(self): return self.health_comp.max_health
    @max_health.setter
    def max_health(self, v): self.health_comp.max_health = v

    @property
    def speed(self): return self.energy_comp.speed
    @speed.setter
    def speed(self, v): self.energy_comp.speed = v

    @property
    def strength(self): return self.stats.strength
    @strength.setter
    def strength(self, v): self.stats.strength = v

    @property
    def dexterity(self): return self.stats.dexterity
    @dexterity.setter
    def dexterity(self, v): self.stats.dexterity = v

    @property
    def constitution(self): return self.stats.constitution
    @constitution.setter
    def constitution(self, v): self.stats.constitution = v

    @property
    def intelligence(self): return self.stats.intelligence
    @intelligence.setter
    def intelligence(self, v): self.stats.intelligence = v

    @property
    def willpower(self): return self.stats.willpower
    @willpower.setter
    def willpower(self, v): self.stats.willpower = v

    @property
    def charisma(self): return self.stats.charisma
    @charisma.setter
    def charisma(self, v): self.stats.charisma = v

    @property
    def appearance(self): return self.stats.appearance
    @appearance.setter
    def appearance(self, v): self.stats.appearance = v

    @property
    def perception(self): return self.stats.perception
    @perception.setter
    def perception(self, v): self.stats.perception = v

    @property
    def level(self): return self.stats.level
    @level.setter
    def level(self, v): self.stats.level = v

    @property
    def xp(self): return self.stats.xp
    @xp.setter
    def xp(self, v): self.stats.xp = v

    @property
    def xp_to_next_level(self): return self.stats.xp_to_next_level
    @xp_to_next_level.setter
    def xp_to_next_level(self, v): self.stats.xp_to_next_level = v

    @property
    def base_damage(self): return self.combat_stats.base_damage
    @base_damage.setter
    def base_damage(self, v): self.combat_stats.base_damage = v

    @property
    def base_defense(self): return self.combat_stats.base_defense
    @base_defense.setter
    def base_defense(self, v): self.combat_stats.base_defense = v

    @property
    def inventory(self): return self.inventory_comp.items
    @inventory.setter
    def inventory(self, v): self.inventory_comp.items = v

    @property
    def equipment(self): return self.equipment_comp.slots
    @equipment.setter
    def equipment(self, v): self.equipment_comp.slots = v

    @property
    def mana(self): return self.mana_comp.mana
    @mana.setter
    def mana(self, v): self.mana_comp.mana = v

    @property
    def max_mana(self): return self.mana_comp.max_mana
    @max_mana.setter
    def max_mana(self, v): self.mana_comp.max_mana = v

    @property
    def psi(self): return self.mana_comp.psi
    @psi.setter
    def psi(self, v): self.mana_comp.psi = v

    @property
    def max_psi(self): return self.mana_comp.max_psi
    @max_psi.setter
    def max_psi(self, v): self.mana_comp.max_psi = v

    @property
    def name(self): return self.char_info.name
    @name.setter
    def name(self, v): self.char_info.name = v

    @property
    def race(self): return self.char_info.race
    @race.setter
    def race(self, v): self.char_info.race = v

    @property
    def gender(self): return self.char_info.gender
    @gender.setter
    def gender(self, v): self.char_info.gender = v

    @property
    def sex(self): return self.char_info.sex
    @sex.setter
    def sex(self, v): self.char_info.sex = v

    @property
    def deity(self): return self.char_info.deity
    @deity.setter
    def deity(self, v): self.char_info.deity = v

    @property
    def birth(self): return self.char_info.birth
    @birth.setter
    def birth(self, v): self.char_info.birth = v

    @property
    def month(self): return self.char_info.month
    @month.setter
    def month(self, v): self.char_info.month = v

    @property
    def day(self): return self.char_info.day
    @day.setter
    def day(self, v): self.char_info.day = v

    @property
    def age(self): return self.char_info.age
    @age.setter
    def age(self, v): self.char_info.age = v

    @property
    def money(self): return self.money_comp.money
    @money.setter
    def money(self, v): self.money_comp.money = v

    @property
    def xp_reward(self): return self.loot_comp.xp_reward
    @xp_reward.setter
    def xp_reward(self, v): self.loot_comp.xp_reward = v

    @property
    def gold_reward(self): return self.loot_comp.gold_reward
    @gold_reward.setter
    def gold_reward(self, v): self.loot_comp.gold_reward = v

    @property
    def loot(self): return self.loot_comp.loot
    @loot.setter
    def loot(self, v): self.loot_comp.loot = v

    @property
    def temporary_boosts(self): return self.status_comp.boosts
    @temporary_boosts.setter
    def temporary_boosts(self, v): self.status_comp.boosts = v

    @property
    def poisoned(self): return self.status_comp.poisoned
    @poisoned.setter
    def poisoned(self, v): self.status_comp.poisoned = v

    @property
    def hunger(self): return self.status_comp.hunger
    @hunger.setter
    def hunger(self, v): self.status_comp.hunger = v

    # ------------------------------------------------------------------
    # Computed combat properties
    # ------------------------------------------------------------------

    @property
    def damage(self):
        """Total damage output including stat and level bonuses."""
        weapon = next(
            (slot['item'] for slot in self.equipment.values() if slot['name'] in ['weapon', 'missile weapon']),
            None,
        )
        weapon_bonus = weapon.damage_bonus if weapon else 0
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

    @property
    def armor(self):
        """Total damage absorption from equipped armor (AC)."""
        return sum(
            (getattr(slot['item'], 'ac', 0) or 0)
            for slot in self.equipment.values()
            if slot['item']
        )

    # ------------------------------------------------------------------
    # Combat breakdown helpers
    # ------------------------------------------------------------------

    def damage_breakdown(self):
        components = [("Base damage", self.base_damage)]
        weapon = next(
            (
                slot["item"]
                for slot in self.equipment.values()
                if slot["name"] in ["weapon", "missile weapon"]
            ),
            None,
        )
        if weapon:
            if weapon.damage is not None:
                if isinstance(weapon.damage, dict):
                    w_min = weapon.damage.get("min", 0)
                    w_max = weapon.damage.get("max", 0)
                    avg = (w_min + w_max) / 2
                else:
                    avg = weapon.damage
                components.append((f"{weapon.name} base", avg))
            if weapon.damage_bonus:
                components.append((f"{weapon.name} bonus", weapon.damage_bonus))
        strength = self.get_stat("strength")
        components.append((f"Strength {strength}", strength * 0.5))
        components.append((f"Level {self.level}", self.level * 0.5))
        return components

    def defense_breakdown(self):
        components = [("Base defense", self.base_defense)]
        for slot in self.equipment.values():
            item = slot.get("item")
            if item:
                if item.defense_bonus:
                    components.append((item.name, item.defense_bonus))
                if getattr(item, 'ac', 0):
                    components.append((f"{item.name} AC", item.ac))
        dexterity = self.get_stat("dexterity")
        constitution = self.get_stat("constitution")
        components.append((f"Dexterity {dexterity}", dexterity * 0.3))
        components.append((f"Constitution {constitution}", constitution * 0.2))
        components.append((f"Level {self.level}", self.level * 0.5))
        return components

    # ------------------------------------------------------------------
    # Inventory / equipment management
    # ------------------------------------------------------------------

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
                for slot_key, slot in self.equipment.items():
                    if slot['name'] == item.slot:
                        return self.equip(item, slot_key)
                return f"No suitable slot found for {item.name}"
            else:
                effect_result = item.effect(self)
                self.remove_item(item)
                return effect_result
        return f"You don't have {item.name}"

    def add_item(self, item):
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

    def equip_item(self, item):
        for slot_key, slot in self.equipment.items():
            if slot['name'] == item.slot:
                if slot['item']:
                    self.add_item(slot['item'])
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

    # ------------------------------------------------------------------
    # Progression
    # ------------------------------------------------------------------

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
        stat_names = [
            'strength', 'dexterity', 'constitution', 'intelligence',
            'willpower', 'charisma', 'appearance', 'perception',
        ]
        for stat in stat_names:
            setattr(self, stat, getattr(self, stat) + random.randint(1, 2))
        self.speed += random.randint(1, 2)

    # ------------------------------------------------------------------
    # Health / mana / status
    # ------------------------------------------------------------------

    def heal(self, amount):
        prev_health = self.health
        self.health = min(self.max_health, self.health + amount)
        gained = self.health - prev_health
        if gained > 0:
            return f"You healed for {gained} HP."
        return "You're already at full health."

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return f"You take {amount} damage."

    def restore_mana(self, amount):
        prev_mana = self.mana
        self.mana = min(self.max_mana, self.mana + amount)
        gained = self.mana - prev_mana
        if gained > 0:
            return f"You restored {gained} mana."
        return "Your mana is already full."

    def apply_item_effect(self, item):
        if item.effect == 'heal':
            self.heal(item.value)
        elif item.effect == 'restore_mana':
            self.restore_mana(item.value)
        elif item.effect == 'boost_strength':
            self.apply_temporary_boost('strength', item.value, item.duration)
        elif item.effect == 'boost_dexterity':
            self.apply_temporary_boost('dexterity', item.value, item.duration)

    def apply_temporary_boost(self, stat, value, duration):
        self.status_comp.boosts[stat] = {'value': value, 'duration': duration}
        return f"Your {stat.capitalize()} increases by {value} for {duration} turns."

    def update_temporary_boosts(self):
        messages = []
        for stat, boost in list(self.status_comp.boosts.items()):
            boost['duration'] -= 1
            if boost['duration'] <= 0:
                del self.status_comp.boosts[stat]
                messages.append(f"Your {stat.capitalize()} boost wears off.")
        return messages

    def get_stat(self, stat):
        base_value = getattr(self, stat)
        boosts = self.status_comp.boosts
        if stat in boosts:
            return base_value + boosts[stat]['value']
        return base_value

    def cure_poison(self):
        if self.status_comp.poisoned:
            self.status_comp.poisoned = False
            return "You feel the poison leave your body."
        return "You are not poisoned."

    def satiate(self, amount):
        self.status_comp.hunger = max(0, self.status_comp.hunger - amount)
        return f"You feel less hungry. (-{amount} hunger)"

    def identify_item(self):
        return "You identify an item in your inventory."

    def detect_magic(self):
        return "You sense magical auras in the area."

    def cast_light(self):
        return "The area is illuminated with magical light."

    # ------------------------------------------------------------------
    # Player initialisation
    # ------------------------------------------------------------------

    def initialize_player(self):
        health_potion = next((item for item in all_consumables if item.name == "Health Potion"), None)
        if health_potion:
            self.add_item(health_potion)
            self.add_item(health_potion)

        dagger_base = next((item for item in all_equipment if item.name == "Dagger"), None)
        robe_base = next((item for item in all_equipment if item.name == "Robe"), None)
        starter_mat = next((m for m in all_materials if m.power == 1), all_materials[0])

        if dagger_base:
            dagger = Equipment(
                f"{starter_mat.name} {dagger_base.name}",
                dagger_base.slot,
                dagger_base.body_part,
                starter_mat.power,
                damage=dagger_base.damage,
                ac=dagger_base.ac,
                accuracy_bonus=dagger_base.accuracy_bonus,
                weight=dagger_base.weight,
                material_type=starter_mat.name,
                gold_value=dagger_base.gold_value * starter_mat.value_multiplier,
            )
            self.equip(dagger, 'a')

        if robe_base:
            robe = Equipment(
                f"{starter_mat.name} {robe_base.name}",
                robe_base.slot,
                robe_base.body_part,
                starter_mat.power,
                damage=robe_base.damage,
                ac=robe_base.ac,
                weight=robe_base.weight,
                material_type=starter_mat.name,
                gold_value=robe_base.gold_value * starter_mat.value_multiplier,
            )
            self.equip(robe, 'f')
