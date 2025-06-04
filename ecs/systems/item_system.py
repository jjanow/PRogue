from ecs.world import World
from ecs.components import Position, Item

class ItemSystem:
    """Handle pickup of items when occupying the same tile."""

    def __init__(self, inventory):
        self.inventory = inventory

    def update(self, world: World):
        for ent, item_comp in list(world.get_component(Item)):
            pos = world.get_entity_components(ent).get(Position)
            if not pos:
                continue
            # Check if a player occupies this position
            for player_ent, _ in world.get_component(Position):
                if player_ent == ent:
                    continue
                player_pos = world.get_entity_components(player_ent).get(Position)
                if player_pos and player_pos.x == pos.x and player_pos.y == pos.y:
                    self.inventory.append(item_comp.reference)
                    world.remove_component(ent, Item)
                    break
