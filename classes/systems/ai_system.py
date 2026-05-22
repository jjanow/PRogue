class AISystem:
    def run_action(self, enemy, game):
        if (game.distance(enemy, game.player) <= 1 and
                game.has_line_of_sight(enemy.x, enemy.y, game.player.x, game.player.y)):
            defeated = game.combat_system.combat(enemy, game.player, game.messages)
            if defeated:
                game.handle_player_death()
        else:
            next_pos = game.get_flow_next_step(enemy)
            if next_pos:
                if game.map[next_pos[1]][next_pos[0]] == '+':
                    game.map[next_pos[1]][next_pos[0]] = '/'
                    game.invalidate_flow_field()
                else:
                    enemy.x, enemy.y = next_pos
