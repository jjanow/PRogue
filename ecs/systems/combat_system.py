import random
import math
from ecs.world import World
from ecs.components import Fighter, Position

class CombatSystem:
    """Handle combat between entities with Fighter components."""

    def attack(self, attacker, defender, messages):
        base_damage = attacker.damage
        attack_score = attacker.damage
        defense_score = defender.defense
        diff = attack_score - defense_score
        hit_chance = 1 / (1 + math.exp(-diff / 5))
        if random.random() < hit_chance:
            dmg = max(1, int(base_damage + random.randint(-2, 2)))
            defender.health -= dmg
            messages.append(f"{attacker.name} hits {defender.name} for {dmg} damage.")
            return defender.health <= 0
        else:
            messages.append(f"{attacker.name} misses {defender.name}.")
            return False

    def update(self, world: World, messages):
        # Example: when two fighters share same Position
        fighters = list(world.get_component(Fighter))
        for i, (ent_a, fighter_a) in enumerate(fighters):
            pos_a = world.get_entity_components(ent_a).get(Position)
            for ent_b, fighter_b in fighters[i+1:]:
                pos_b = world.get_entity_components(ent_b).get(Position)
                if pos_a and pos_b and pos_a.x == pos_b.x and pos_a.y == pos_b.y:
                    defeated = self.attack(fighter_a, fighter_b, messages)
                    if defeated:
                        world.remove_component(ent_b, Fighter)
