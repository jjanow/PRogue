from ecs.world import World
from ecs.components import AI, Position, Velocity

class AISystem:
    """Very simple AI that moves entities towards the closest player."""

    def __init__(self, player_entity):
        self.player_entity = player_entity

    def update(self, world: World):
        player_pos = world.get_entity_components(self.player_entity).get(Position)
        if not player_pos:
            return
        for ent, ai in world.get_component(AI):
            pos = world.get_entity_components(ent).get(Position)
            vel = world.get_entity_components(ent).get(Velocity)
            if not pos:
                continue
            if vel is None:
                vel = Velocity(0, 0)
                world.add_component(ent, vel)
            dx = 1 if player_pos.x > pos.x else -1 if player_pos.x < pos.x else 0
            dy = 1 if player_pos.y > pos.y else -1 if player_pos.y < pos.y else 0
            vel.dx = dx
            vel.dy = dy
