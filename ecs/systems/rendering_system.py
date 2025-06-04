import curses
from ecs.world import World
from ecs.components import Position, Renderable, FieldOfView

class RenderingSystem:
    """Draw entities and map using curses."""

    def __init__(self, stdscr, game_map):
        self.stdscr = stdscr
        self.game_map = game_map

    def draw_map(self, fov: FieldOfView):
        height = len(self.game_map)
        width = len(self.game_map[0]) if self.game_map else 0
        for y in range(height):
            for x in range(width):
                if not fov.explored[y][x]:
                    self.stdscr.addch(y, x, ' ')
                    continue
                visible = fov.visible[y][x]
                ch = self.game_map[y][x]
                attr = curses.A_NORMAL if visible else curses.A_DIM
                if ch == '#':
                    self.stdscr.addch(y, x, ch, curses.color_pair(5) | attr)
                elif ch == '+':
                    self.stdscr.addch(y, x, ch, curses.color_pair(6) | attr)
                else:
                    self.stdscr.addch(y, x, ch, curses.color_pair(1) | attr)

    def update(self, world: World):
        self.stdscr.clear()
        fov_ent = next(iter(world.get_component(FieldOfView)), (None, None))[0]
        fov = world.get_entity_components(fov_ent).get(FieldOfView) if fov_ent else None
        if fov:
            self.draw_map(fov)
        for ent, rend in world.get_component(Renderable):
            pos = world.get_entity_components(ent).get(Position)
            if not pos:
                continue
            attr = curses.color_pair(rend.color)
            self.stdscr.addch(pos.y, pos.x, rend.char, attr)
        self.stdscr.refresh()
