class AISystem:
    def run_action(self, enemy, game):
        if (game.distance(enemy, game.player) <= 1 and
                game.has_line_of_sight(enemy.x, enemy.y, game.player.x, game.player.y)):
            defeated = game.combat_system.combat(enemy, game.player, game.messages)
            if defeated:
                game.handle_player_death()
        else:
            path = game.find_path(enemy, game.player, consider_enemies=True)
            if path and len(path) > 1:
                next_pos = path[1]
                enemy.x, enemy.y = next_pos
