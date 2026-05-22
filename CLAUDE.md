# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python pRoguelike.py
```

Requires a terminal that supports `curses` and is at least 80 columns wide. On Windows, `pip install windows-curses` first. There is no test suite or linter configured.

## Architecture

PRogue is a terminal roguelike (Python + `curses`). All game logic lives under `classes/`, and all content data lives under `data/` as JSON files that can be edited without touching Python.

### ECS Architecture

`classes/ecs.py` defines pure-data component `@dataclass`es (`PositionComponent`, `HealthComponent`, `EnergyComponent`, `StatsComponent`, etc.). `Entity` (`classes/entity.py`) is a plain object that holds instances of every component — it represents both the player and all monsters.

Systems in `classes/systems/` operate on entities each turn:
- **`TurnSystem`** — drives the energy-based turn loop. Each enemy accumulates `speed` energy per tick and acts once per `ACTION_COST` (100) of energy banked.
- **`AISystem`** — decides enemy action each tick: attack if adjacent+LOS, else A* path toward player.
- **`StatusSystem`** — ticks temporary status effects (attribute boosts, poison, hunger).

### Game Object (`classes/game.py`)

`Game` is the central state container: player, enemies list, items list, map grid, FOV/explored arrays, dungeon level, turn counter, and all UI mode flags (`inventory_mode`, `drop_mode`, `save_mode`, etc.). The main loop in `pRoguelike.py` checks these flags each frame to choose which renderer method to call.

### Other Key Classes

| File | Responsibility |
|------|---------------|
| `classes/renderer.py` | All curses drawing — map, HUD, every menu/screen |
| `classes/input_handler.py` | Key-to-action dispatch; delegates to `Game` methods |
| `classes/combat_system.py` | Hit probability (logistic function) and damage calculation |
| `classes/map_generator.py` | Procedural room + corridor generation; staircase placement |
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
