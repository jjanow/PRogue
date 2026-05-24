from __future__ import annotations
import random
from collections import Counter
from typing import Any, Optional
from classes.item import Equipment, Item
from classes.item_loader import (
    all_consumables,
    all_equipment,
    all_materials,
)
from classes.ecs import (
    BoostEffect,
    EquipmentSlot,
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


def _make_equipment_slots() -> dict[str, EquipmentSlot]:
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
    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        name: str,
        health: float,
        damage: float,
        defense: float,
    ) -> None:
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

    def get_component(self, comp_type: Any) -> Any:
        for v in vars(self).values():
            if isinstance(v, comp_type):
                return v
        return None

    # ------------------------------------------------------------------
    # Property delegates — keep every existing attribute access working
    # ------------------------------------------------------------------

    @property
    def x(self) -> int: return self.position.x
    @x.setter
    def x(self, v: int) -> None: self.position.x = v

    @property
    def y(self) -> int: return self.position.y
    @y.setter
    def y(self, v: int) -> None: self.position.y = v

    @property
    def char(self) -> str: return self.renderable.char
    @char.setter
    def char(self, v: str) -> None: self.renderable.char = v

    @property
    def health(self) -> float: return self.health_comp.health
    @health.setter
    def health(self, v: float) -> None: self.health_comp.health = v

    @property
    def max_health(self) -> float: return self.health_comp.max_health
    @max_health.setter
    def max_health(self, v: float) -> None: self.health_comp.max_health = v

    @property
    def speed(self) -> int: return self.energy_comp.speed
    @speed.setter
    def speed(self, v: int) -> None: self.energy_comp.speed = v

    @property
    def strength(self) -> int: return self.stats.strength
    @strength.setter
    def strength(self, v: int) -> None: self.stats.strength = v

    @property
    def dexterity(self) -> int: return self.stats.dexterity
    @dexterity.setter
    def dexterity(self, v: int) -> None: self.stats.dexterity = v

    @property
    def constitution(self) -> int: return self.stats.constitution
    @constitution.setter
    def constitution(self, v: int) -> None: self.stats.constitution = v

    @property
    def intelligence(self) -> int: return self.stats.intelligence
    @intelligence.setter
    def intelligence(self, v: int) -> None: self.stats.intelligence = v

    @property
    def willpower(self) -> int: return self.stats.willpower
    @willpower.setter
    def willpower(self, v: int) -> None: self.stats.willpower = v

    @property
    def charisma(self) -> int: return self.stats.charisma
    @charisma.setter
    def charisma(self, v: int) -> None: self.stats.charisma = v

    @property
    def appearance(self) -> int: return self.stats.appearance
    @appearance.setter
    def appearance(self, v: int) -> None: self.stats.appearance = v

    @property
    def perception(self) -> int: return self.stats.perception
    @perception.setter
    def perception(self, v: int) -> None: self.stats.perception = v

    @property
    def level(self) -> int: return self.stats.level
    @level.setter
    def level(self, v: int) -> None: self.stats.level = v

    @property
    def xp(self) -> int: return self.stats.xp
    @xp.setter
    def xp(self, v: int) -> None: self.stats.xp = v

    @property
    def xp_to_next_level(self) -> int: return self.stats.xp_to_next_level
    @xp_to_next_level.setter
    def xp_to_next_level(self, v: int) -> None: self.stats.xp_to_next_level = v

    @property
    def base_damage(self) -> float: return self.combat_stats.base_damage
    @base_damage.setter
    def base_damage(self, v: float) -> None: self.combat_stats.base_damage = v

    @property
    def base_defense(self) -> float: return self.combat_stats.base_defense
    @base_defense.setter
    def base_defense(self, v: float) -> None: self.combat_stats.base_defense = v

    @property
    def inventory(self) -> Counter[Any]: return self.inventory_comp.items
    @inventory.setter
    def inventory(self, v: Counter[Any]) -> None: self.inventory_comp.items = v

    @property
    def equipment(self) -> dict[str, Any]: return self.equipment_comp.slots
    @equipment.setter
    def equipment(self, v: dict[str, Any]) -> None: self.equipment_comp.slots = v

    @property
    def mana(self) -> float: return self.mana_comp.mana
    @mana.setter
    def mana(self, v: float) -> None: self.mana_comp.mana = v

    @property
    def max_mana(self) -> float: return self.mana_comp.max_mana
    @max_mana.setter
    def max_mana(self, v: float) -> None: self.mana_comp.max_mana = v

    @property
    def psi(self) -> float: return self.mana_comp.psi
    @psi.setter
    def psi(self, v: float) -> None: self.mana_comp.psi = v

    @property
    def max_psi(self) -> float: return self.mana_comp.max_psi
    @max_psi.setter
    def max_psi(self, v: float) -> None: self.mana_comp.max_psi = v

    @property
    def name(self) -> str: return self.char_info.name
    @name.setter
    def name(self, v: str) -> None: self.char_info.name = v

    @property
    def race(self) -> str: return self.char_info.race
    @race.setter
    def race(self, v: str) -> None: self.char_info.race = v

    @property
    def gender(self) -> str: return self.char_info.gender
    @gender.setter
    def gender(self, v: str) -> None: self.char_info.gender = v

    @property
    def sex(self) -> str: return self.char_info.sex
    @sex.setter
    def sex(self, v: str) -> None: self.char_info.sex = v

    @property
    def deity(self) -> str: return self.char_info.deity
    @deity.setter
    def deity(self, v: str) -> None: self.char_info.deity = v

    @property
    def birth(self) -> str: return self.char_info.birth
    @birth.setter
    def birth(self, v: str) -> None: self.char_info.birth = v

    @property
    def month(self) -> str: return self.char_info.month
    @month.setter
    def month(self, v: str) -> None: self.char_info.month = v

    @property
    def day(self) -> str: return self.char_info.day
    @day.setter
    def day(self, v: str) -> None: self.char_info.day = v

    @property
    def age(self) -> int: return self.char_info.age
    @age.setter
    def age(self, v: int) -> None: self.char_info.age = v

    @property
    def money(self) -> int: return self.money_comp.money
    @money.setter
    def money(self, v: int) -> None: self.money_comp.money = v

    @property
    def xp_reward(self) -> int: return self.loot_comp.xp_reward
    @xp_reward.setter
    def xp_reward(self, v: int) -> None: self.loot_comp.xp_reward = v

    @property
    def gold_reward(self) -> int: return self.loot_comp.gold_reward
    @gold_reward.setter
    def gold_reward(self, v: int) -> None: self.loot_comp.gold_reward = v

    @property
    def loot(self) -> list[Any]: return self.loot_comp.loot
    @loot.setter
    def loot(self, v: list[Any]) -> None: self.loot_comp.loot = v

    @property
    def temporary_boosts(self) -> dict[str, BoostEffect]: return self.status_comp.boosts
    @temporary_boosts.setter
    def temporary_boosts(self, v: dict[str, BoostEffect]) -> None: self.status_comp.boosts = v

    @property
    def poisoned(self) -> bool: return self.status_comp.poisoned
    @poisoned.setter
    def poisoned(self, v: bool) -> None: self.status_comp.poisoned = v

    @property
    def hunger(self) -> int: return self.status_comp.hunger
    @hunger.setter
    def hunger(self, v: int) -> None: self.status_comp.hunger = v

    # ------------------------------------------------------------------
    # Computed combat properties
    # ------------------------------------------------------------------

    @property
    def damage(self) -> float:
        """Total damage output including stat and level bonuses."""
        weapon: Optional[Equipment] = next(
            (slot['item'] for slot in self.equipment.values() if slot['name'] in ['weapon', 'missile weapon']),
            None,
        )
        weapon_bonus = weapon.damage_bonus if weapon else 0
        strength_bonus = self.get_stat('strength') * 0.5
        level_bonus = self.level * 0.5
        total_damage = self.base_damage + weapon_bonus + strength_bonus + level_bonus
        return round(total_damage, 1)

    @property
    def defense(self) -> float:
        """Total defense score including stat and level bonuses."""
        armor_bonus: float = sum(
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
    def armor(self) -> int:
        """Total damage absorption from equipped armor (AC)."""
        return sum(
            (getattr(slot['item'], 'ac', 0) or 0)
            for slot in self.equipment.values()
            if slot['item']
        )

    # ------------------------------------------------------------------
    # Combat breakdown helpers
    # ------------------------------------------------------------------

    def damage_breakdown(self) -> list[tuple[str, float]]:
        components: list[tuple[str, float]] = [("Base damage", self.base_damage)]
        weapon: Optional[Equipment] = next(
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
                    w_min: int = weapon.damage.get("min", 0)
                    w_max: int = weapon.damage.get("max", 0)
                    avg: float = (w_min + w_max) / 2
                else:
                    avg = float(weapon.damage)
                components.append((f"{weapon.name} base", avg))
            if weapon.damage_bonus:
                components.append((f"{weapon.name} bonus", weapon.damage_bonus))
        strength = self.get_stat("strength")
        components.append((f"Strength {strength}", strength * 0.5))
        components.append((f"Level {self.level}", self.level * 0.5))
        return components

    def defense_breakdown(self) -> list[tuple[str, float]]:
        components: list[tuple[str, float]] = [("Base defense", self.base_defense)]
        for slot in self.equipment.values():
            item: Optional[Equipment] = slot.get("item")
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

    def equip(self, item: Equipment, slot_key: str) -> str:
        slot = self.equipment[slot_key]
        if item.slot == slot['name']:
            old_item: Optional[Equipment] = slot['item']
            slot['item'] = item
            if old_item:
                self.add_item(old_item)
            if item in self.inventory:
                self.remove_item(item)
            return f"Equipped {item.name} in {slot['name']} slot"
        return f"Cannot equip {item.name} in {slot['name']} slot"

    def use_item(self, item: Item) -> str:
        if item in self.inventory:
            if isinstance(item, Equipment):
                for slot_key, slot in self.equipment.items():
                    if slot['name'] == item.slot:
                        return self.equip(item, slot_key)
                return f"No suitable slot found for {item.name}"
            else:
                if item.effect is None:
                    return f"Cannot use {item.name}: no effect."
                effect_result: str = item.effect(self)
                self.remove_item(item)
                return effect_result
        return f"You don't have {item.name}"

    def add_item(self, item: Item) -> None:
        existing_item = next((i for i in self.inventory if i.name == item.name), None)
        if existing_item:
            self.inventory[existing_item] += 1
        else:
            self.inventory[item] = 1

    def remove_item(self, item: Item) -> bool:
        existing_item = next((i for i in self.inventory if i.name == item.name), None)
        if existing_item and self.inventory[existing_item] > 0:
            self.inventory[existing_item] -= 1
            if self.inventory[existing_item] == 0:
                del self.inventory[existing_item]
            return True
        return False

    def get_inventory_items(self) -> list[tuple[Item, int]]:
        return list(self.inventory.items())

    def equip_item(self, item: Equipment) -> str:
        for _slot_key, slot in self.equipment.items():
            if slot['name'] == item.slot:
                if slot['item']:
                    self.add_item(slot['item'])
                slot['item'] = item
                self.remove_item(item)
                return f"Equipped {item.name} in {slot['name']} slot."
        return f"No suitable slot found for {item.name}."

    def unequip_item(self, slot_key: str) -> str:
        slot = self.equipment.get(slot_key)
        if slot and slot['item']:
            self.add_item(slot['item'])
            slot['item'] = None
            return f"Unequipped item from {slot['name']} slot."
        return "No item to unequip in this slot."

    def get_equipped_items(self) -> dict[str, Equipment]:
        return {key: slot['item'] for key, slot in self.equipment.items() if slot['item']}

    # ------------------------------------------------------------------
    # Progression
    # ------------------------------------------------------------------

    def gain_xp(self, amount: int) -> None:
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self) -> None:
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

    def heal(self, amount: float) -> str:
        prev_health = self.health
        self.health = min(self.max_health, self.health + amount)
        gained = self.health - prev_health
        if gained > 0:
            return f"You healed for {gained} HP."
        return "You're already at full health."

    def take_damage(self, amount: float) -> str:
        self.health = max(0, self.health - amount)
        return f"You take {amount} damage."

    def restore_mana(self, amount: float) -> str:
        prev_mana = self.mana
        self.mana = min(self.max_mana, self.mana + amount)
        gained = self.mana - prev_mana
        if gained > 0:
            return f"You restored {gained} mana."
        return "Your mana is already full."

    def apply_item_effect(self, item: Item) -> None:
        if item.effect == 'heal':
            self.heal(item.value or 0)
        elif item.effect == 'restore_mana':
            self.restore_mana(item.value or 0)
        elif item.effect == 'boost_strength':
            self.apply_temporary_boost('strength', item.value or 0, item.duration or 0)
        elif item.effect == 'boost_dexterity':
            self.apply_temporary_boost('dexterity', item.value or 0, item.duration or 0)

    def apply_temporary_boost(self, stat: str, value: Any, duration: Any) -> str:
        self.status_comp.boosts[stat] = {'value': value, 'duration': duration}
        return f"Your {stat.capitalize()} increases by {value} for {duration} turns."

    def update_temporary_boosts(self) -> list[str]:
        messages: list[str] = []
        for stat, boost in list(self.status_comp.boosts.items()):
            boost['duration'] -= 1
            if boost['duration'] <= 0:
                del self.status_comp.boosts[stat]
                messages.append(f"Your {stat.capitalize()} boost wears off.")
        return messages

    def get_stat(self, stat: str) -> float:
        base_value: int = getattr(self, stat)
        boosts = self.status_comp.boosts
        if stat in boosts:
            return base_value + boosts[stat]['value']
        return base_value

    def cure_poison(self) -> str:
        if self.status_comp.poisoned:
            self.status_comp.poisoned = False
            return "You feel the poison leave your body."
        return "You are not poisoned."

    def satiate(self, amount: float) -> str:
        self.status_comp.hunger = max(0, self.status_comp.hunger - int(amount))
        return f"You feel less hungry. (-{amount} hunger)"

    def identify_item(self) -> str:
        return "You identify an item in your inventory."

    def detect_magic(self) -> str:
        return "You sense magical auras in the area."

    def cast_light(self) -> str:
        return "The area is illuminated with magical light."

    # ------------------------------------------------------------------
    # Player initialisation
    # ------------------------------------------------------------------

    def initialize_player(self) -> None:
        health_potion = next((item for item in all_consumables if item.name == "Health Potion"), None)
        if health_potion:
            self.add_item(health_potion)
            self.add_item(health_potion)

        dagger_base: Optional[Equipment] = next((item for item in all_equipment if item.name == "Dagger"), None)
        robe_base: Optional[Equipment] = next((item for item in all_equipment if item.name == "Robe"), None)
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
