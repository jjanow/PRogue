from __future__ import annotations
import os

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
import random
from typing import Any

# Windows compatibility: use msvcrt for single key input
if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios

# Reduce the delay for detecting an isolated ESC key press.
os.environ.setdefault("ESCDELAY", "25")

# Add the current directory to Python path to find the 'classes' package
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from classes.game import Game
from classes.item import Equipment
from classes.race_loader import Race, all_races
from classes.save_manager import SaveManager, SaveInfo
from curses import KEY_NPAGE, KEY_PPAGE


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_single_key() -> str:
    """Wait for a single keypress and return the pressed character."""
    if os.name == 'nt':
        ch = msvcrt.getch()
        if ch in b"\x00\xe0":
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


def choose_option_single_click(prompt: str, options: list[str]) -> str:
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


def point_buy_curses(
    stdscr: curses.window,
    stats: dict[str, int],
    race_bonuses: dict[str, int],
    total_points: int = 20,
) -> dict[str, int]:
    curses.curs_set(0)
    attributes: list[str] = list(stats.keys())
    selected = 0
    remaining = total_points
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Point Buy - Arrows adjust, Enter to accept")
        for idx, attr in enumerate(attributes):
            marker = "->" if idx == selected else "  "
            base: int = stats[attr]
            bonus: int = race_bonuses.get(attr, 0)
            total: int = max(1, base + bonus)
            stdscr.addstr(idx + 2, 0,
                          f"{marker} {attr.title():<12}: {base:2d} {bonus:+2d} = {total:2d}")
        stdscr.addstr(len(attributes) + 3, 0, f"Remaining Points: {remaining:2d}")
        stdscr.refresh()
        key: int = stdscr.getch()
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


def character_creation_cli() -> dict[str, Any]:
    """Simple command line character creation before launching curses."""
    clear_screen()
    print("=== Character Creation ===")
    name = input("Name: ")
    clear_screen()
    gender = input("Gender: ")
    clear_screen()
    sex_options = ["Male", "Female", "Other"]
    sex = choose_option_single_click("Choose Sex:", sex_options)
    clear_screen()

    race_name = choose_option_single_click(
        "Choose Race:", [r.name for r in all_races]
    )
    race: Race = next(r for r in all_races if r.name == race_name)
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

    stats: dict[str, int] = {}
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

        for attr in attributes:
            stats[attr] = max(1, stats[attr] + race.bonuses.get(attr, 0))

    return {
        "name": name,
        "gender": gender,
        "sex": sex,
        "race": race.name,
        "stats": stats,
    }


def draw(stdscr: curses.window, game: Game) -> None:
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    for y, row in enumerate(game.map):
        for x, cell in enumerate(row):
            stdscr.addch(y, x, cell)

    icon_map: dict[str, str] = {
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
        stdscr.addch(item.y, item.x, ch)  # type: ignore[arg-type]

    for enemy in game.enemies:
        stdscr.addch(enemy.y, enemy.x, enemy.char)

    stdscr.addch(game.player.y, game.player.x, game.player.char)

    stdscr.addstr(
        height - 3,
        0,
        f"Health: {game.player.health}/{game.player.max_health} | Damage: {game.player.damage:.1f} | Defense: {game.player.defense:.1f}",
    )
    stdscr.addstr(height - 2, 0, f"Level: {game.player.level} | XP: {game.player.xp}/{game.player.xp_to_next_level} | Dungeon Level: {game.dungeon_level}")

    inv_str = ", ".join(item.name for item in game.player.inventory)
    stdscr.addstr(height - 1, 0, f"Inventory: {inv_str[:width-12]}")

    for i, message in enumerate(game.messages[-3:]):
        stdscr.addstr(height - 1 + i, 0, str(message)[:width])

    stdscr.refresh()


def _run_main_loop(stdscr: curses.window, game: Game) -> None:
    """Run the main game loop."""
    while True:
        if game.character_stats_mode:
            game.renderer.draw_character_stats_screen(stdscr)
        elif game.combat_stats_mode:
            game.renderer.draw_combat_stats_screen(stdscr)
        elif game.inventory_mode:
            game.renderer.draw_inventory(stdscr)
        elif game.backpack_mode:
            game.renderer.draw_backpack(stdscr)
        elif game.drop_mode:
            game.renderer.draw_drop_interface(stdscr)
        elif game.options_mode:
            game.renderer.draw_options_menu(stdscr)
        elif game.save_load_menu_mode:
            game.renderer.draw_save_load_menu(stdscr)
        elif game.help_mode:
            game.renderer.draw_help_menu(stdscr)
        elif game.debug_mode:
            game.renderer.draw_debug_menu(stdscr)
        elif game.save_mode:
            game.renderer.draw_save_screen(stdscr)
        elif game.load_mode:
            game.renderer.draw_load_screen(stdscr)
        elif game.delete_mode:
            game.renderer.draw_delete_screen(stdscr)
        else:
            game.renderer.draw(stdscr)

        if game.quit:
            break

        key: int = stdscr.getch()
        if game.debug_mode and key == 27:
            game.debug_mode = False
        elif game.inventory_mode:
            if key in (ord('+'), ord('.'), KEY_NPAGE):
                game.inventory_page = min(
                    game.inventory_page + 1,
                    (len(game.player.inventory) - 1) // game.items_per_page,
                )
            elif key in (ord('-'), ord(','), KEY_PPAGE):
                game.inventory_page = max(0, game.inventory_page - 1)
            elif game.handle_input(key):
                break
        elif game.handle_input(key):
            break

        if game.quit:
            break

    if game.game_over:
        game.renderer.draw(stdscr)
        stdscr.nodelay(False)
        while True:
            key = stdscr.getch()
            if key in (10, 13):
                break


def main(stdscr: curses.window, char_data: dict[str, Any]) -> None:
    curses.start_color()
    if hasattr(curses, "set_escdelay"):
        curses.set_escdelay(25)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(9, curses.COLOR_CYAN, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx()
    game = Game(height - 3, width, stdscr)
    game.player.name = char_data.get("name", game.player.name)
    game.player.gender = char_data.get("gender", "")
    game.player.sex = char_data.get("sex", "")
    game.player.race = char_data.get("race", "")
    for stat, value in char_data.get("stats", {}).items():
        if hasattr(game.player, stat):
            setattr(game.player, stat, value)

    game.player.max_health = 50 + game.player.constitution * 5
    game.player.health = game.player.max_health

    _run_main_loop(stdscr, game)


if __name__ == "__main__":
    def show_intro_menu() -> str:
        """Show the main intro menu with options to create, load, or manage saves."""
        while True:
            clear_screen()
            print("=== PRogue - A Python Roguelike ===")
            print()
            print("Choose an option:")
            print("  1) Create New Character")
            print("  2) Load Existing Save")
            print("  3) Manage Save Games")
            print("  4) Quit")
            print("  5) Quick Start (Random Character)")
            print()

            choice = get_single_key()

            if choice == "1":
                return "create"
            elif choice == "2":
                return "load"
            elif choice == "3":
                return "manage"
            elif choice == "4":
                return "quit"
            elif choice == "5":
                return "random"

    def generate_random_character() -> dict[str, Any]:
        """Generate a fully randomized character without any prompts."""
        _first_names: list[str] = [
            "Aric", "Bran", "Cael", "Dorn", "Eryn", "Fael", "Gorn", "Hael",
            "Idris", "Jorn", "Kael", "Lorn", "Mira", "Nael", "Oren", "Pell",
            "Rael", "Sera", "Tael", "Urik", "Vael", "Wren", "Xael", "Yorn",
            "Zael", "Aldric", "Brynn", "Caius", "Delia", "Eamon",
        ]
        _sex_options: list[str] = ["Male", "Female", "Other"]
        _attributes: list[str] = [
            "strength", "dexterity", "constitution", "intelligence",
            "willpower", "charisma", "appearance", "perception",
        ]

        name = random.choice(_first_names)
        sex = random.choice(_sex_options)
        gender = sex
        race: Race = random.choice(all_races)

        base_stats: dict[str, int] = {attr: random.randint(1, 20) for attr in _attributes}
        stats: dict[str, int] = {
            attr: max(1, base_stats[attr] + race.bonuses.get(attr, 0))
            for attr in _attributes
        }

        return {
            "name": name,
            "gender": gender,
            "sex": sex,
            "race": race.name,
            "stats": stats,
        }

    def show_load_menu() -> int | None:
        """Show menu to select a save slot to load."""
        save_manager = SaveManager()
        saves = save_manager.get_all_save_info()

        while True:
            clear_screen()
            print("=== Load Game ===")
            print()

            available_saves: list[SaveInfo] = []
            for save in saves:
                if save['exists']:
                    available_saves.append(save)
                    print(f"  {save['slot']}) {save['character_name']} - Level {save['player_level']} (Dungeon {save['level']})")
                    print(f"      Last played: {save['timestamp']}")
                    print()

            if not available_saves:
                print("  No save games found.")
                print()
                print("Press any key to return to main menu...")
                get_single_key()
                return None

            print("  0) Return to main menu")
            print()
            print("Select a save slot to load:")

            choice = get_single_key()
            if choice == "0":
                return None

            if choice.isdigit():
                slot = int(choice)
                if 1 <= slot <= 10:
                    save_info = save_manager.get_save_info(slot)
                    if save_info['exists']:
                        return slot

            print("Invalid selection. Press any key to continue...")
            get_single_key()

    def show_manage_menu() -> None:
        """Show menu to manage save games (delete, view details)."""
        save_manager = SaveManager()

        while True:
            saves = save_manager.get_all_save_info()
            clear_screen()
            print("=== Manage Save Games ===")
            print()

            for save in saves:
                if save['exists']:
                    print(f"  {save['slot']}) {save['character_name']} - Level {save['player_level']} (Dungeon {save['level']})")
                    print(f"      Last played: {save['timestamp']}")
                    print(f"      Playtime: {save['playtime']} seconds")
                    print()
                else:
                    print(f"  {save['slot']}) Empty slot")
                    print()

            print("Options:")
            print("  d) Delete a save game")
            print("  0) Return to main menu")
            print()

            choice = get_single_key().lower()

            if choice == "0":
                return
            elif choice == "d":
                show_delete_menu(save_manager, saves)

    def show_delete_menu(save_manager: SaveManager, saves: list[SaveInfo]) -> None:
        """Show menu to delete a save game."""
        while True:
            clear_screen()
            print("=== Delete Save Game ===")
            print()

            existing_saves = [save for save in saves if save['exists']]

            if not existing_saves:
                print("No save games to delete.")
                print()
                print("Press any key to continue...")
                get_single_key()
                return

            for save in existing_saves:
                print(f"  {save['slot']}) {save['character_name']} - Level {save['player_level']}")

            print()
            print("  0) Cancel")
            print()
            print("Select a save to delete:")

            choice = get_single_key()
            if choice == "0":
                return

            if choice.isdigit():
                slot = int(choice)
                if 1 <= slot <= 10:
                    save_info = save_manager.get_save_info(slot)
                    if save_info['exists']:
                        clear_screen()
                        print(f"Are you sure you want to delete {save_info['character_name']}?")
                        print("This action cannot be undone!")
                        print()
                        print("  y) Yes, delete")
                        print("  n) No, cancel")
                        print()

                        confirm = get_single_key().lower()
                        if confirm == "y":
                            try:
                                save_manager.delete_save(slot)
                                print("Save game deleted successfully!")
                            except Exception as e:
                                print(f"Error deleting save: {e}")
                            print()
                            print("Press any key to continue...")
                            get_single_key()
                        return

            print("Invalid selection. Press any key to continue...")
            get_single_key()

    def load_existing_game(slot: int) -> None:
        """Load an existing game from a save slot."""
        def run_loaded_game(stdscr: curses.window) -> None:
            curses.start_color()
            if hasattr(curses, "set_escdelay"):
                curses.set_escdelay(25)
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

            height, width = stdscr.getmaxyx()
            game = Game.create_minimal(height - 3, width, stdscr)

            save_manager = SaveManager()
            try:
                save_manager.load_game(game, slot)
                game.save_slot = slot
                _run_main_loop(stdscr, game)
            except Exception as e:
                stdscr.clear()
                stdscr.addstr(0, 0, f"Error loading save: {e}")
                stdscr.addstr(2, 0, "Press any key to return to main menu...")
                stdscr.refresh()
                stdscr.getch()

        wrapper(run_loaded_game)

    # Main program loop
    while True:
        choice = show_intro_menu()

        if choice == "random":
            char_data = generate_random_character()
            print(f"Starting as {char_data['name']} the {char_data['race']}...")

            def run(stdscr: curses.window) -> None:
                main(stdscr, char_data)

            wrapper(run)
            print("Thanks for playing!")
            break

        elif choice == "create":
            char_data = character_creation_cli()

            def run(stdscr: curses.window) -> None:
                main(stdscr, char_data)

            wrapper(run)
            print("Thanks for playing!")
            break

        elif choice == "load":
            slot = show_load_menu()
            if slot is not None:
                load_existing_game(slot)

        elif choice == "manage":
            show_manage_menu()

        elif choice == "quit":
            print("Thanks for playing!")
            break
