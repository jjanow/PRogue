try:
    import curses
    from curses import wrapper
except ImportError as exc:
    if os.name == 'nt':
        raise ImportError(
            "The 'windows-curses' package is required on Windows. Install it with 'pip install windows-curses'."
        ) from exc
    raise
import sys
import os
import random

# Windows compatibility: use msvcrt for single key input
if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios

# Reduce the delay for detecting an isolated ESC key press. The default delay
# can make exiting menus feel sluggish.
os.environ.setdefault("ESCDELAY", "25")

# Add the current directory to Python path to find the 'classes' package
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from classes.game import Game
from classes.item import Equipment
from classes.race_loader import all_races
from curses import KEY_NPAGE, KEY_PPAGE


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_single_key():
    """Wait for a single keypress and return the pressed character."""
    if os.name == 'nt':
        ch = msvcrt.getch()
        if ch in b"\x00\xe0":  # Handle special keys
            ch = msvcrt.getch()
        return ch.decode("utf-8", errors="ignore")
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def choose_option_single_click(prompt, options):
    """Display options and return the selected one using a single key press."""
    while True:
        clear_screen()
        print(prompt)
        for idx, opt in enumerate(options, 1):
            print(f"  {idx}) {opt}")
        ch = get_single_key()
        if ch.isdigit():
            sel = int(ch) - 1
            if 0 <= sel < len(options):
                clear_screen()
                return options[sel]


def point_buy_curses(stdscr, stats, race_bonuses, total_points=20):
    curses.curs_set(0)
    attributes = list(stats.keys())
    selected = 0
    remaining = total_points
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Point Buy - Arrows adjust, Enter to accept")
        for idx, attr in enumerate(attributes):
            marker = "->" if idx == selected else "  "
            base = stats[attr]
            bonus = race_bonuses.get(attr, 0)
            total = max(1, base + bonus)
            stdscr.addstr(idx + 2, 0,
                          f"{marker} {attr.title():<12}: {base:2d} {bonus:+2d} = {total:2d}")
        stdscr.addstr(len(attributes) + 3, 0, f"Remaining Points: {remaining:2d}")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(attributes)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(attributes)
        elif key == curses.KEY_RIGHT:
            if remaining > 0 and stats[attributes[selected]] < 20:
                stats[attributes[selected]] += 1
                remaining -= 1
        elif key == curses.KEY_LEFT:
            if stats[attributes[selected]] > 1:
                stats[attributes[selected]] -= 1
                remaining += 1
        elif key in (10, 13):
            break
    return stats

def character_creation_cli():
    """Simple command line character creation before launching curses."""
    clear_screen()
    print("=== Character Creation ===")
    name = input("Name: ")
    clear_screen()
    gender = input("Gender: ")
    clear_screen()
    # Choose sex using single key input
    sex_options = ["Male", "Female", "Other"]
    sex = choose_option_single_click("Choose Sex:", sex_options)
    clear_screen()

    # Choose race from data file
    race = choose_option_single_click(
        "Choose Race:", [r.name for r in all_races]
    )
    race = next(r for r in all_races if r.name == race)
    clear_screen()

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

    clear_screen()
    print("Choose stat generation:")
    print("  r) Random roll")
    print("  p) Point buy")
    while True:
        method = get_single_key().lower()
        if method in ("r", "p"):
            break
    
    stats = {}
    if method.startswith("r"):
        while True:
            clear_screen()
            base_stats = {attr: random.randint(1, 20) for attr in attributes}
            stats = {}
            print("Rolled stats (base + racial bonus = total):")
            for attr in attributes:
                base = base_stats[attr]
                bonus = race.bonuses.get(attr, 0)
                total = max(1, base + bonus)
                stats[attr] = total
                print(f"  {attr.title():<12}: {base:2d} + {bonus:+2d} = {total:2d}")
            print("Press 'r' to reroll or any other key to accept")
            choice = get_single_key().lower()
            if choice != "r":
                clear_screen()
                break
    else:
        stats = {attr: 10 for attr in attributes}
        stats = wrapper(point_buy_curses, stats, race.bonuses, 20)

        # Apply race bonuses directly without an extra screen
        for attr in attributes:
            stats[attr] = max(1, stats[attr] + race.bonuses.get(attr, 0))

    return {
        "name": name,
        "gender": gender,
        "sex": sex,
        "race": race.name,
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
    # Further reduce the ESC key delay inside curses itself. Not all curses
    # implementations provide ``set_escdelay`` (e.g. ``windows-curses`` on
    # Windows). Guard the call so the game runs everywhere.
    if hasattr(curses, "set_escdelay"):
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

    # Recalculate derived attributes based on stats
    game.player.max_health = 50 + game.player.constitution * 5
    game.player.health = game.player.max_health

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
