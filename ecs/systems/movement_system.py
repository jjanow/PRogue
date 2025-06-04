from ecs.world import World
from ecs.components import Position, Velocity

class MovementSystem:
    """Apply Velocity components to Position components."""

    def __init__(self, game_map):
        self.game_map = game_map

    def is_blocked(self, x, y):
        if 0 <= y < len(self.game_map) and 0 <= x < len(self.game_map[0]):
            return self.game_map[y][x] == '#'
        return True

    def update(self, world: World):
        for ent, vel in world.get_component(Velocity):
            pos = world.get_entity_components(ent).get(Position)
            if not pos:
                continue
            new_x = pos.x + vel.dx
            new_y = pos.y + vel.dy
            if not self.is_blocked(new_x, new_y):
                pos.x = new_x
                pos.y = new_y
            vel.dx = 0
            vel.dy = 0
