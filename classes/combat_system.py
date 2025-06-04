import random
import math

class CombatSystem:
    @staticmethod
    def combat(attacker, defender, messages):
        base_damage = attacker.damage
        weapon = next(
            (slot['item'] for slot in attacker.equipment.values() if slot['name'] in ['weapon', 'missile weapon']),
            None,
        )
        accuracy_bonus = weapon.accuracy_bonus if weapon else 0

        # Calculate attack and defense scores
        attack_score = attacker.damage + accuracy_bonus
        defense_score = defender.defense

        # Logistic function converts score difference into win probability
        diff = attack_score - defense_score
        hit_chance = 1 / (1 + math.exp(-diff / 5))

        if random.random() < hit_chance:
            damage = max(1, int(base_damage + random.randint(-2, 2)))
            defender.health -= damage
            messages.append(f"{attacker.name} hits {defender.name} for {damage} damage.")

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
        player.gain_xp(20 + enemy.level * 5)

        # 5% chance to drop a random item
        if random.random() < 0.05:
            dropped_item = self.create_random_item()
            dropped_item.x, dropped_item.y = enemy.x, enemy.y
            return dropped_item

        return None
