from classes.ecs import ACTION_COST


class TurnSystem:
    def __init__(self, ai_system, status_system):
        self.ai_system = ai_system
        self.status_system = status_system

    def process(self, game):
        game.enemies = [e for e in game.enemies if e.health > 0]

        # Give every enemy their speed-based energy for this tick.
        for enemy in game.enemies:
            enemy.energy_comp.energy += enemy.energy_comp.speed

        # Each enemy acts as many times as their accumulated energy allows.
        for enemy in game.enemies[:]:
            while enemy.health > 0 and enemy.energy_comp.energy >= ACTION_COST:
                self.ai_system.run_action(enemy, game)
                enemy.energy_comp.energy -= ACTION_COST
                if game.player.health <= 0:
                    return

        game.turn_count += 1

        if game.turn_count % 10 == 0:
            heal_amount = min(game.player.max_health - game.player.health, 1)
            game.player.health += heal_amount
            if heal_amount > 0:
                game.messages.append(f"You feel a bit better. (+{heal_amount} HP)")

        if game.allow_enemy_spawning and game.turn_count - game.last_spawn_turn >= 50:
            game.spawn_enemies(1)
            game.last_spawn_turn = game.turn_count

        for item in game.items:
            if item.x == game.player.x and item.y == game.player.y:
                game.messages.append(f"Floor: {item.name}")

        self.status_system.update(game.player, game.messages)
        game.update_fov()
