from __future__ import annotations

import random
import math
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from classes.entity import Entity

from classes.item import Equipment, Item


class CombatSystem:
    @staticmethod
    def combat(attacker: Entity, defender: Entity, messages: list[str]) -> bool:
        weapon: Optional[Equipment] = next(
            (
                slot['item']
                for slot in attacker.equipment.values()
                if slot['name'] in ['weapon', 'missile weapon']
            ),
            None,
        )
        accuracy_bonus: float = weapon.accuracy_bonus if weapon else 0

        # Determine base weapon damage
        if weapon and weapon.damage is not None:
            if isinstance(weapon.damage, dict):
                damage_dict: dict[str, int] = weapon.damage  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                w_min = damage_dict.get('min', 0)
                w_max = damage_dict.get('max', 0)
                weapon_damage: float = random.randint(w_min, w_max)
            else:
                weapon_damage = weapon.damage
        else:
            weapon_damage = random.randint(1, 3)

        # Strength and other bonuses directly affect raw damage
        raw_damage: float = (
            weapon_damage
            + attacker.base_damage
            + (weapon.damage_bonus if weapon else 0)
            + attacker.get_stat('strength') * 0.5
            + attacker.level * 0.5
        )
        raw_damage += random.randint(-2, 2)
        raw_damage = max(1, int(raw_damage))

        # Calculate attack and defense scores
        attack_score = attacker.damage + accuracy_bonus
        defense_score = defender.defense

        # Logistic function converts score difference into win probability
        diff = attack_score - defense_score
        hit_chance = 1 / (1 + math.exp(-diff / 5))

        if random.random() < hit_chance:
            absorbed = defender.armor
            damage = max(1, int(raw_damage) - absorbed)
            defender.health -= damage
            msg = f"{attacker.name} hits {defender.name} for {damage} damage"
            if absorbed:
                msg += f" ({absorbed} absorbed)"
            messages.append(msg + ".")

            if defender.health <= 0:
                messages.append(f"{defender.name} is defeated!")
                return True  # Enemy defeated
        else:
            messages.append(f"{attacker.name} misses {defender.name}.")

        return False  # Enemy not defeated

    def create_random_item(self) -> Item | Equipment:
        from classes.item_loader import all_consumables, all_equipment
        # Exclude misc items from random drops - they should only drop from monsters
        ground_loot_pool: list[Item | Equipment] = all_consumables + all_equipment
        return random.choice(ground_loot_pool)

    def player_attack_enemy(self, player: Entity, enemy: Entity, messages: list[str]) -> list[Item | Equipment]:
        """Handle rewards when the player defeats an enemy."""
        messages.append(f"You defeated {enemy.name}!")

        xp: int = getattr(enemy, 'xp_reward', 20 + enemy.level * 5)
        player.gain_xp(xp)
        messages.append(f"You gain {xp} XP.")

        gold: int = getattr(enemy, 'gold_reward', 0)
        if gold:
            player.money += gold
            messages.append(f"You collect {gold} gold.")

        drops: list[Item | Equipment] = []
        loot: list[Item | Equipment] = getattr(enemy, 'loot', [])
        for item in loot:
            if random.random() < 0.05:
                item.x, item.y = enemy.x, enemy.y
                drops.append(item)

        # Fallback random drop if no predefined loot
        if not drops and random.random() < 0.05:
            loot_item = self.create_random_item()
            loot_item.x, loot_item.y = enemy.x, enemy.y
            drops.append(loot_item)

        return drops
