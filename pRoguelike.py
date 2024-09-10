import curses
from curses import wrapper
import sys
import os

# Add the current directory to Python path to find the 'classes' package
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from classes.game import Game
from curses import KEY_NPAGE, KEY_PPAGE

def draw(stdscr, game):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    for y, row in enumerate(game.map):
        for x, cell in enumerate(row):
            stdscr.addch(y, x, cell)

    for item in game.items:
        stdscr.addch(item.y, item.x, item.char)

    for enemy in game.enemies:
        stdscr.addch(enemy.y, enemy.x, enemy.char)

    stdscr.addch(game.player.y, game.player.x, game.player.char)

    # Status bar
    stdscr.addstr(height - 3, 0, f"Health: {game.player.health}/{game.player.max_health} | Damage: {game.player.damage} | Defense: {game.player.defense}")
    stdscr.addstr(height - 2, 0, f"Level: {game.player.level} | XP: {game.player.xp}/{game.player.xp_to_next_level} | Dungeon Level: {game.dungeon_level}")

    # Inventory
    inv_str = ", ".join(item.name for item in game.player.inventory[:5])  # Show only first 5 items
    if len(game.player.inventory) > 5:
        inv_str += "..."
    stdscr.addstr(height - 1, 0, f"Inventory: {inv_str[:width-12]}")  # Truncate if too long

    # Messages
    for i, message in enumerate(game.messages[-3:]):
        if message is not None:
            stdscr.addstr(height - 1 + i, 0, str(message)[:width])  # Convert to string and truncate if too long

    stdscr.refresh()

def main(stdscr):
    # Initialize curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Player
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Monsters
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Items
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Walls
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Doors

    # Initialize game
    height, width = stdscr.getmaxyx()
    game = Game(height - 3, width, stdscr)

    while True:
        if game.character_stats_mode:
            game.renderer.draw_character_stats_screen(stdscr)
        elif game.inventory_mode:
            game.renderer.draw_inventory(stdscr)
        elif game.backpack_mode:
            game.renderer.draw_backpack(stdscr)
        elif game.drop_mode:
            game.renderer.draw_drop_interface(stdscr)
        elif game.debug_mode:
            game.renderer.draw_debug_menu(stdscr)
        else:
            game.renderer.draw(stdscr)

        key = stdscr.getch()
        if game.debug_mode and key == 27:  # ESC key
            game.debug_mode = False
        elif game.inventory_mode:
            if key in (ord('+'), ord('.'), KEY_NPAGE):  # Next page (+ key, . key, or PgDn)
                game.inventory_page = min(game.inventory_page + 1, (len(game.player.inventory) - 1) // game.items_per_page)
            elif key in (ord('-'), ord(','), KEY_PPAGE):  # Previous page (- key, , key, or PgUp)
                game.inventory_page = max(0, game.inventory_page - 1)
            elif game.handle_input(key):
                break
        elif game.handle_input(key):
            break

    curses.endwin()
    print("Thanks for playing!")

if __name__ == "__main__":
    wrapper(main)
