from ecs.systems.rendering_system import RenderingSystem

class Renderer(RenderingSystem):
    """Wrapper around the ECS RenderingSystem for compatibility."""
    def __init__(self, game):
        self.game = game
        super().__init__(game.stdscr, game.map)
