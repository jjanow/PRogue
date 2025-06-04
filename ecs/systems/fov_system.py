from typing import List
from ecs.world import World
from ecs.components import FieldOfView, Position

class FOVSystem:
    """Simple square field-of-view calculation."""

    def update(self, world: World):
        for ent, fov in world.get_component(FieldOfView):
            pos = world.get_entity_components(ent).get(Position)
            if not pos:
                continue
            radius = fov.radius
            height = len(fov.visible)
            width = len(fov.visible[0]) if fov.visible else 0
            for y in range(height):
                for x in range(width):
                    fov.visible[y][x] = False
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x = pos.x + dx
                    y = pos.y + dy
                    if 0 <= y < height and 0 <= x < width:
                        fov.visible[y][x] = True
                        fov.explored[y][x] = True
