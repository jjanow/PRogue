import random

class CombatSystem:
    @staticmethod
    def combat(attacker, defender, messages):
        base_damage = attacker.damage
        attack_roll = random.randint(1, 20) + max(0, (attacker.strength - 10) // 2)
        defense_value = 10 + defender.defense + max(0, (defender.dexterity - 10) // 2)

        if attack_roll >= defense_value:
            damage = max(1, base_damage + random.randint(-2, 2))
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
        defeated = self.combat(player, enemy, messages)
        if defeated:
            messages.append(f"You defeated {enemy.name}!")
            player.gain_xp(20 + enemy.level * 5)
            
            # 5% chance to drop a random item
            if random.random() < 0.05:
                dropped_item = self.create_random_item()
                dropped_item.x, dropped_item.y = enemy.x, enemy.y
                return dropped_item
        return None