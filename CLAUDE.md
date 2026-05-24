# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python pRoguelike.py
```

Requires a terminal that supports `curses` and is at least 80 columns wide (29+ rows recommended). The dungeon map is a fixed 80×23 grid; the renderer scrolls the viewport when the terminal is smaller. On Windows, `pip install windows-curses` first. There is no linter configured.

## Tests and Documentation Maintenance

Whenever you make changes to the game, you must keep tests and documentation in sync:

### Unit Tests (`tests/`)

- **New function or method**: create a corresponding test in `tests/` (mirror the `classes/` structure, e.g. `tests/test_combat_system.py`). Use the standard `unittest` module — no third-party test framework is installed.
- **Changed behavior**: update any existing tests that cover the modified code so they reflect the new behavior.
- **Deleted code**: remove the corresponding tests so the suite stays green.
- Run the full suite with `python -m pytest tests/` (or `python -m unittest discover tests/` if pytest is unavailable) after every change and fix any failures before finishing.

### Documentation (`CLAUDE.md`)

- **New class or file**: add a row to the "Other Key Classes" table with the file path and its responsibility.
- **Renamed or removed file**: update or delete the corresponding row in that table.
- **New data file or data directory**: add a bullet under "Data Files (`data/`)".
- **New content type** (new monster field, item slot, material category, etc.): update the relevant bullet under "Adding Content".
- **Architectural change** (new system, new ECS component, changes to the `Game` object): update the relevant section ("ECS Architecture" or "Game Object") to reflect the new structure.

Keep documentation edits minimal and factual — describe what exists, not intent or history.

## Architecture

PRogue is a terminal roguelike (Python + `curses`). All game logic lives under `classes/`, and all content data lives under `data/` as JSON files that can be edited without touching Python.

### ECS Architecture

`classes/ecs.py` defines pure-data component `@dataclass`es (`PositionComponent`, `HealthComponent`, `EnergyComponent`, `StatsComponent`, `AIStateComponent`, etc.). `Entity` (`classes/entity.py`) is a plain object that holds instances of every component — it represents both the player and all monsters.

Systems in `classes/systems/` operate on entities each turn:
- **`TurnSystem`** — drives the energy-based turn loop. Each enemy accumulates `speed` energy per tick and acts once per `ACTION_COST` (100) of energy banked. Clears `game.noise_events` at the end of each tick.
- **`AISystem`** — three-state machine per enemy (`AIStateComponent.state`): **asleep** (skip action, wake on nearby noise), **idle** (random wander, become alert on LOS or loud noise), **alert** (A\* pursue and attack player). Enemies spawn asleep with 40 % probability. Becoming alert emits a shout that can chain-wake nearby sleepers.
- **`StatusSystem`** — ticks temporary status effects (attribute boosts, poison, hunger).

### Game Object (`classes/game.py`)

`Game` is the central state container: player, enemies list, items list, map grid, FOV/explored arrays, dungeon level, turn counter, `noise_events` list, and all UI mode flags (`inventory_mode`, `drop_mode`, `save_mode`, etc.). The main loop in `pRoguelike.py` checks these flags each frame to choose which renderer method to call.

`noise_events` is a `list[tuple[int, int, float]]` (x, y, level) that accumulates noise emitted during a player turn. Player movement emits footstep noise (2), doors emit noise (5), and melee combat emits noise (10). The list is cleared by `TurnSystem` after all enemies have acted. Enemy `AISystem` reads this list to decide whether to wake or alert.

After `generate_level`, `Game._generate_random_level` reads `map_generator.room_types` (a `dict[int, RoomType]`) to drive content spawning: monster dens get group-spawned same-type enemies, treasure rooms get pre-filled items, tension rooms get dense enemy fills and trigger a warning message, and special rooms have placeholder feature tiles placed by the generator (`A`=altar, `~`=fountain, `f`=forge, `b`=herb bush, `^`=trap cluster).

### Other Key Classes

| File | Responsibility |
|------|---------------|
| `classes/renderer.py` | All curses drawing — map, HUD, every menu/screen |
| `classes/input_handler.py` | Key-to-action dispatch; delegates to `Game` methods |
| `classes/combat_system.py` | Hit probability (logistic function) and damage calculation |
| `classes/map_generator.py` | BSP dungeon generation (fixed 80×23 map); room content types (`RoomType`, `SpecialFeature`); tile-budget and connectivity validation; viewport scrolling in renderer |
| `classes/item.py` | `Item` and `Equipment` data classes with dict serialization |
| `classes/item_loader.py` | Loads all item JSON; combines templates + materials; builds consumable effect lambdas |
| `classes/monster_loader.py` | Loads monster JSON; builds loot lists |
| `classes/save_manager.py` | JSON save/load/delete (10 slots); compact map serialization |

### Data Files (`data/`)

Content is entirely data-driven:
- `data/monsters/` — five archetype files; monsters have `challenge_rating` used to filter spawns by dungeon depth
- `data/items/` — per-slot equipment templates and consumables
- `data/materials/` — material tiers (`weapons`, `armor`, `cloth`, `jewelry`) combined with item templates at generation time to produce named items like "Steel Longsword"
- `data/races.json` — race stat bonuses applied during character creation
- `data/skills.json` — skill definitions (not yet wired to gameplay)

### Adding Content

New content requires only JSON edits — no Python changes needed:
- **Monster**: add to `data/monsters/<archetype>.json` with `name`, `xp`, `gold`, `challenge_rating`, `archetype`
- **Item**: add to `data/items/<slot>.json` with required stat fields
- **Material**: add to `data/materials/<type>.json` with `name` and `power`
- **Race**: add to `data/races.json` with `name` and `bonuses` dict
