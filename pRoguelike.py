import curses
from curses import wrapper
import sys
import os
import random

# Reduce the delay for detecting an isolated ESC key press. The default delay
# can make exiting menus feel sluggish.
os.environ.setdefault("ESCDELAY", "25")

# Add the current directory to Python path to find the 'classes' package
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from classes.game import Game
from classes.item import Equipment
from curses import KEY_NPAGE, KEY_PPAGE

def character_creation_cli():
    """Simple command line character creation before launching curses."""
    print("=== Character Creation ===")
    name = input("Name: ")
    gender = input("Gender: ")
    sex = input("Sex: ")
    race = input("Race: ")

    attributes = [
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "willpower",
        "charisma",
        "appearance",
        "perception",
    ]

    method = input(
        "Choose stat generation - random roll (r) or point buy (p): "
    ).strip().lower()

    stats = {}
    if method.startswith("r"):
        while True:
            stats = {attr: random.randint(1, 20) for attr in attributes}
            print("Rolled stats:")
            for attr in attributes:
                print(f"  {attr.title()}: {stats[attr]}")
            choice = input("Press 'r' to reroll or any other key to accept: ").lower()
            if choice != "r":
                break
    else:
        remaining = 20
        stats = {attr: 10 for attr in attributes}
        for attr in attributes:
            while True:
                max_add = min(20 - stats[attr], remaining)
                prompt = f"Add points to {attr.title()} (0-{max_add}, remaining {remaining}): "
                try:
                    add = int(input(prompt))
                except ValueError:
                    print("Please enter a number.")
                    continue
                if 0 <= add <= max_add:
                    stats[attr] += add
                    remaining -= add
                    break
                else:
                    print("Invalid amount.")
        if remaining:
            print(f"{remaining} unspent points will be ignored.")

    return {
        "name": name,
        "gender": gender,
        "sex": sex,
        "race": race,
        "stats": stats,
    }

def draw(stdscr, game):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    for y, row in enumerate(game.map):
        for x, cell in enumerate(row):
            stdscr.addch(y, x, cell)

    icon_map = {
        'weapon': '/',
        'missile weapon': '}',
        'helmet': '^',
        'armor': '[',
        'cloak': 'B',
        'shield': ')',
        'boots': '(',
        'bracers': '|',
        'gauntlets': ']',
        'girdle': ':',
        'amulet': '"',
        'ring (right)': '=',
        'ring (left)': '=',
    }
    for item in game.items:
        if isinstance(item, Equipment):
            ch = icon_map.get(item.slot, '?')
        else:
            ch = '!'
        stdscr.addch(item.y, item.x, ch)

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

def main(stdscr, char_data):
    # Initialize curses
    curses.start_color()
    # Further reduce the ESC key delay inside curses itself
    curses.set_escdelay(25)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Player
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Monsters
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Items
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Walls
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Doors

    # Initialize game
    height, width = stdscr.getmaxyx()
    game = Game(height - 3, width, stdscr)
    # Apply character creation choices
    game.player.name = char_data.get("name", game.player.name)
    game.player.gender = char_data.get("gender", "")
    game.player.sex = char_data.get("sex", "")
    game.player.race = char_data.get("race", "")
    for stat, value in char_data.get("stats", {}).items():
        if hasattr(game.player, stat):
            setattr(game.player, stat, value)

    while True:
        if game.character_stats_mode:
            game.renderer.draw_character_stats_screen(stdscr)
        elif game.inventory_mode:
            game.renderer.draw_inventory(stdscr)
        elif game.backpack_mode:
            game.renderer.draw_backpack(stdscr)
        elif game.drop_mode:
            game.renderer.draw_drop_interface(stdscr)
        elif game.options_mode:
            game.renderer.draw_options_menu(stdscr)
        elif game.help_mode:
            game.renderer.draw_help_menu(stdscr)
        elif game.debug_mode:
            game.renderer.draw_debug_menu(stdscr)
        else:
            game.renderer.draw(stdscr)

        if game.quit:
            break

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

        if game.quit:
            break

    return

if __name__ == "__main__":
    char_data = character_creation_cli()

    def run(stdscr):
        main(stdscr, char_data)

    wrapper(run)
    print("Thanks for playing!")
