from ecs.systems.input_system import InputSystem
from ecs.world import World

class InputHandler(InputSystem):
    """Wrapper to use the ECS InputSystem with the existing Game."""

    def __init__(self, game):
        self.game = game
        self.world: World = getattr(game, 'world', World())
        if not hasattr(game, 'world'):
            game.world = self.world
        super().__init__(game.stdscr)

    def handle_input(self, key):
        self.update(self.world, key)
        return False
