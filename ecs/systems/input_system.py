from typing import List
import curses
from ecs.world import World
from ecs.components import PlayerInput, Position, Velocity

class InputSystem:
    """Process keyboard input for entities with PlayerInput components."""

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def update(self, world: World, key: int):
        for ent, _ in world.get_component(PlayerInput):
            pos = world.get_entity_components(ent).get(Position)
            if not pos:
                continue
            vel = world.get_entity_components(ent).get(Velocity)
            if vel is None:
                vel = Velocity(0, 0)
                world.add_component(ent, vel)

            movement_keys = {
                ord('8'): (0, -1), ord('k'): (0, -1), curses.KEY_UP: (0, -1),
                ord('2'): (0, 1), ord('j'): (0, 1), curses.KEY_DOWN: (0, 1),
                ord('4'): (-1, 0), ord('h'): (-1, 0), curses.KEY_LEFT: (-1, 0),
                ord('6'): (1, 0), ord('l'): (1, 0), curses.KEY_RIGHT: (1, 0),
                ord('7'): (-1, -1), ord('y'): (-1, -1), curses.KEY_HOME: (-1, -1),
                ord('9'): (1, -1), ord('u'): (1, -1), curses.KEY_PPAGE: (1, -1),
                ord('1'): (-1, 1), ord('b'): (-1, 1), curses.KEY_END: (-1, 1),
                ord('3'): (1, 1), ord('n'): (1, 1), curses.KEY_NPAGE: (1, 1),
            }

            if key in movement_keys:
                dx, dy = movement_keys[key]
                vel.dx = dx
                vel.dy = dy
            elif key in [ord('5'), curses.KEY_B2]:
                vel.dx = 0
                vel.dy = 0
            else:
                vel.dx = 0
                vel.dy = 0
