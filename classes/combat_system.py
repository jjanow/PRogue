import random
import math

class CombatSystem:
    @staticmethod
    def combat(attacker, defender, messages):
        weapon = next(
            (
                slot['item']
                for slot in attacker.equipment.values()
                if slot['name'] in ['weapon', 'missile weapon']
            ),
            None,
        )
        accuracy_bonus = weapon.accuracy_bonus if weapon else 0

        # Determine base weapon damage
        if weapon and weapon.damage is not None:
            if isinstance(weapon.damage, dict):
                w_min = weapon.damage.get('min', 0)
                w_max = weapon.damage.get('max', 0)
                weapon_damage = random.randint(w_min, w_max)
            else:
                weapon_damage = weapon.damage
        else:
            weapon_damage = random.randint(1, 3)

        # Strength and other bonuses directly affect raw damage
        raw_damage = (
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
            damage = max(1, raw_damage - absorbed)
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

    def create_random_item(self):
        from classes.item_loader import all_items
        import random
        return random.choice(all_items)

    def player_attack_enemy(self, player, enemy, messages):
        """Handle rewards when the player defeats an enemy."""
        messages.append(f"You defeated {enemy.name}!")

        xp = getattr(enemy, 'xp_reward', 20 + enemy.level * 5)
        player.gain_xp(xp)
        messages.append(f"You gain {xp} XP.")

        gold = getattr(enemy, 'gold_reward', 0)
        if gold:
            player.money += gold
            messages.append(f"You collect {gold} gold.")

        drops = []
        for item in getattr(enemy, 'loot', []):
            if random.random() < 0.05:
                item.x, item.y = enemy.x, enemy.y
                drops.append(item)

        # Fallback random drop if no predefined loot
        if not drops and random.random() < 0.05:
            loot = self.create_random_item()
            loot.x, loot.y = enemy.x, enemy.y
            drops.append(loot)

        return drops
