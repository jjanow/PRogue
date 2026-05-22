# PRogue

## Overview

PRogue is a traditional roguelike game written in Python using the `curses` library for terminal rendering. The game features procedurally generated dungeons, turn-based combat, a deep equipment and materials system, and multi-level dungeon crawling. It is under active development.

---

## Getting Started

Ensure Python 3 is installed. On **Windows**, install the optional `windows-curses` package first. On **macOS** and **Linux** the standard `curses` module is already included:

```bash
pip install windows-curses
```

Launch the game:

```bash
python pRoguelike.py
```

Run the game in a terminal that supports `curses` and is at least 80 columns wide.

### Running the tests

The test suite requires `pytest`:

```bash
pip install pytest
pytest
```

`pytest.ini` configures `testpaths = tests`, so running `pytest` from the repo root is sufficient. To see verbose output or run a single file:

```bash
pytest -v
pytest tests/test_combat_system.py
```

---

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / Numpad 2,4,6,8 | Move cardinal directions |
| Numpad 1,3,7,9 | Move diagonally |
| `5` / Numpad center | Wait one turn |
| `,` | Pick up item on the ground |
| `>` / `<` | Descend / ascend a staircase |
| `0` | Auto-explore the dungeon |
| `w` | Walk to the nearest staircase |
| `i` | Open the inventory / equipment screen |
| `d` | Open the drop interface |
| `@` | View character sheet |
| `Ctrl+W` | View detailed combat stats (damage and armor breakdown) |
| `=` | Open the options menu |
| `?` | View the in-game help menu |
| `S` | Save/load menu |
| `Q` | Quit the game |

In the inventory screen, press the letter shown next to an item to equip or use it. Use `+`/`.`/PgDn and `-`/`,`/PgUp to page through a long inventory list. Press `ESC` to close any menu.

---

## Game Mechanics

### Character Creation

Before entering the dungeon, you create a character through a series of pre-game menus:

1. **Name and gender** — free-text input.
2. **Race** — choose from six races, each with unique stat bonuses and penalties (see Races section).
3. **Stat generation** — choose between:
   - **Random roll** — each of the eight stats is rolled 1–20, then racial bonuses are applied. You can reroll as many times as you want.
   - **Point buy** — start with all stats at 10 and 20 points to distribute (max 20 per stat). Racial bonuses are applied after you accept.

Your character starts with a Bronze Dagger equipped in the weapon slot, a Cloth Robe in the armor slot, and two Health Potions in their inventory.

### Character Stats

Every entity in the game (players and monsters) has eight primary stats:

| Stat | Effect |
|------|--------|
| **Strength** | Each point adds 0.5 to damage output |
| **Dexterity** | Each point adds 0.3 to defense |
| **Constitution** | Each point adds 0.2 to defense; starting max HP = 50 + constitution × 5 |
| **Intelligence** | Currently tracked; reserved for future magic systems |
| **Willpower** | Currently tracked; reserved for future systems |
| **Charisma** | Currently tracked; reserved for future systems |
| **Appearance** | Currently tracked; reserved for future systems |
| **Perception** | Currently tracked; reserved for future systems |

The status bar at the bottom of the screen shows your current HP, total damage, total defense, character level, XP, and dungeon level.

### Combat

Combat is turn-based and uses a probabilistic hit system:

1. **Hit chance** — the game computes an attack score (your total damage + weapon accuracy bonus) and a defense score (target's total defense). The difference is fed into a logistic function to produce a hit probability, so a well-matched fight has roughly a 50% hit rate and a large advantage skews it sharply.
2. **Damage roll** — if the attack hits, raw damage is rolled from the weapon's min/max range, then strength and level bonuses are added, plus a ±2 random variance. Armor Class (AC) from equipped pieces is subtracted last; the minimum dealt is 1.
3. **Defeat** — a defeated enemy drops XP, gold (added instantly), and may drop loot items on the ground (5% chance per loot entry, or a 5% chance of a random item if the monster has no predefined loot).

Enemies move and attack every turn the player takes an action. Enemies path toward the player using A* pathfinding and attack automatically when adjacent.

### Leveling Up

Defeating enemies awards XP equal to the monster's XP value. When accumulated XP reaches the threshold:

- Character level increases by 1.
- XP threshold scales by ×1.5 each level.
- Max HP increases by 10 and health is fully restored.
- All eight stats each increase by 1 or 2 (random).
- Speed increases by 1 or 2 (random).

Every 10 turns the player passively regenerates 1 HP.

### Field of View

The game uses Bresenham line-of-sight tracing. Vision rules differ by location:

- **Inside a room** — you see the entire room and up to 2 tiles into connected corridors.
- **In a corridor** — sight is restricted to a 3-tile radius.

Tiles you have seen before are shown in a dimmed color even when out of sight. Items on the ground are revealed when they enter your field of view and remain visible on explored tiles thereafter.

### Map Generation

Each dungeon level is procedurally generated:

- Up to 10 rectangular rooms are placed randomly, sized 3–5 tiles tall by 5–7 tiles wide, with overlap checks so rooms never intersect.
- Rooms are connected sequentially by L-shaped corridors (horizontal-then-vertical or vertical-then-horizontal, chosen randomly).
- Upstairs (`<`) are placed in the center of the first room; downstairs (`>`) in the center of the last room.
- The player spawns on the upstairs tile.
- Enemies and items are scattered on random floor tiles after generation.

New enemies spawn every 50 turns to keep the dungeon populated. The monster pool narrows each level to creatures whose challenge rating matches the current dungeon depth.

### Enemies and Monster AI

Monsters are selected from a pool filtered by **challenge rating** relative to the current dungeon level: `min_cr = (dungeon_level - 1) × 0.5`, `max_cr = dungeon_level × 0.5 + 0.5`. Their HP, strength, and dexterity all scale with their challenge rating and the dungeon level.

Enemies path toward the player every turn using precomputed BFS paths (one path tree per walkable tile, cached at level generation) with A* as a live fallback. Enemies avoid walking through each other.

Monster categories found in `data/monsters/`:

| File | Contents |
|------|----------|
| `humanoids.json` | Bandit, Goblin, Kobold, Hobgoblin, Orc Warrior, Barbarian Raider, Gnoll, Dark Elf, Troll, Ogre (CR 0.25–4.0) |
| `animals.json` | Wild animals with low to moderate CR |
| `undead.json` | Undead creatures |
| `constructs.json` | Magical constructs |
| `abominations.json` | High-CR aberrations and boss-tier monsters |

### Items and Equipment

Items on the ground are displayed with ASCII icons:

| Icon | Slot |
|------|------|
| `/` | Weapon |
| `}` | Missile weapon |
| `^` | Helmet |
| `[` | Armor |
| `B` | Cloak |
| `)` | Shield |
| `(` | Boots |
| `\|` | Bracers |
| `]` | Gauntlets |
| `:` | Girdle |
| `"` | Amulet |
| `=` | Ring |
| `!` | Consumable (potions, scrolls, food) |

**Equipment slots** — the player has 13 slots labeled `a`–`m`:

| Slot | Type |
|------|------|
| a | Weapon |
| b | Missile weapon |
| c | Helmet |
| d | Amulet |
| e | Shield |
| f | Armor |
| g | Cloak |
| h | Girdle |
| i | Gauntlets |
| j | Boots |
| k | Ring (right) |
| l | Ring (left) |
| m | Bracers |

Weapons contribute a damage bonus and an accuracy bonus. All other armor slots contribute a defense bonus and an Armor Class (AC) value that absorbs flat damage per hit.

**Consumables** include potions (healing, mana, attribute elixirs, antidotes, speed potions), scrolls (Cure Wounds tiers, Restore Mana, Identify, Detect Magic, Light), food (Food Ration, Elven Waybread), and drinks (Dwarven Ale, Wine). Attribute elixirs grant a temporary boost that wears off after a set number of turns.

### Materials System

Equipment items are generated by combining a base item template with a randomly selected material, producing names like "Steel Longsword" or "Mithril Plate". The material determines the item's stat boost power and gold value multiplier.

**Weapon materials** (ascending power):

Bronze → Iron → Steel → Mithril → Adamantine → Obsidian → Dragonbone → Ethereal → Legendary

Separate material tables exist for armor, cloth (robes/cloaks), and jewelry (rings/amulets), each with their own tier progression.

### Races

Six playable races are available, each with stat modifiers applied during character creation:

| Race | Bonuses | Penalties |
|------|---------|-----------|
| Human | None | None |
| Elf | +2 Dex, +2 Perception, +1 Appearance | −2 Con, −1 Str |
| Dwarf | +2 Con, +1 Willpower | −1 Cha, −1 Dex |
| Halfling | +2 Dex, +1 Cha | −1 Str, −1 Con |
| Orc | +2 Str, +1 Con | −2 Cha, −1 Int |
| Gnome | +2 Int, +1 Dex | −1 Str, −1 Con |

### Save System

The game supports up to 10 named save slots stored as JSON files in the `saves/` directory. Saves record the full game state: player stats, inventory, equipment, the dungeon map, explored/visible tile arrays, all floor items, all live enemies, staircase positions, turn count, messages, and playtime. The map and boolean grids are compacted to strings before writing.

From the main menu you can create a new character, load an existing save, or manage saves (view details, delete). Mid-game, press `S` to reach the save/load menu.

### Auto-explore and Auto-walk

- **Auto-explore (`0`)** — the game repeatedly pathfinds to the nearest unexplored tile using a Dijkstra scan of the walkable map, walks there with animation, and stops automatically when a monster enters your field of view or the entire level is explored.
- **Walk to stairs (`w`)** — walks directly to the nearest staircase (upstairs or downstairs) with animation. Any keypress interrupts either auto-movement mode.

---

## File and Folder Structure

```
PRogue/
├── pRoguelike.py          # Entry point: main menu, character creation, curses bootstrap
├── README.md
├── pytest.ini             # Test runner configuration
├── saves/                 # Save game JSON files (save_1.json … save_10.json)
├── tests/                 # Unit tests (291 tests across 10 files)
│   ├── conftest.py
│   ├── test_combat_system.py
│   ├── test_ecs.py
│   ├── test_entity.py
│   ├── test_game.py
│   ├── test_item.py
│   ├── test_item_loader.py
│   ├── test_map_generator.py
│   ├── test_monster_loader.py
│   ├── test_save_manager.py
│   └── test_systems.py
├── classes/               # All game logic (Python package)
│   ├── game.py            # Core game state, turn loop, level generation, pathfinding, FOV
│   ├── entity.py          # Entity class used for both the player and monsters; stat/equipment logic
│   ├── ecs.py             # Pure-data ECS component dataclasses (Position, Health, Energy, Stats, …)
│   ├── combat_system.py   # Hit-chance and damage calculation; XP/gold/loot rewards on kill
│   ├── map_generator.py   # Procedural room and corridor generation; staircase placement
│   ├── renderer.py        # All curses drawing: map, items, enemies, HUD, menus, screens
│   ├── input_handler.py   # Key-to-action dispatch for movement, menus, and game commands
│   ├── item.py            # Item and Equipment data classes; serialization to/from dict
│   ├── item_loader.py     # Loads consumables and equipment from data/; builds effect lambdas
│   ├── monster_loader.py  # Loads monster templates from data/monsters/; creates loot lists
│   ├── race_loader.py     # Loads race definitions and stat bonuses from data/races.json
│   ├── save_manager.py    # JSON save/load/delete for up to 10 slots; compact map serialization
│   ├── systems/           # ECS systems operating on entities each turn
│   │   ├── turn_system.py    # Energy-based turn loop; passive regen; enemy spawning
│   │   ├── ai_system.py      # Enemy AI: A* pathfinding and melee attack logic
│   │   └── status_system.py  # Ticks and expires temporary status effects
│   └── __init__.py
└── data/                  # Game data (JSON); edit these to add content without touching code
    ├── races.json          # Playable races and their stat bonuses
    ├── skills.json         # Skill definitions (stealth, magic schools, weapon types, etc.)
    ├── items/              # Equipment and consumable templates
    │   ├── consumables.json     # Potions, scrolls, food, drinks and their effects/values
    │   ├── weapons.json         # Melee weapon templates (damage ranges, accuracy)
    │   ├── missile_weapons.json # Ranged weapon templates
    │   ├── armor.json           # Body armor templates
    │   ├── helmets.json         # Helmet templates
    │   ├── shields.json         # Shield templates
    │   ├── boots.json           # Boot templates
    │   ├── gauntlets.json       # Gauntlet templates
    │   ├── bracers.json         # Bracer templates
    │   ├── girdles.json         # Girdle templates
    │   ├── cloaks.json          # Cloak templates
    │   ├── rings.json           # Ring templates
    │   ├── amulets.json         # Amulet templates
    │   └── misc.json            # Miscellaneous items (monster drops only, not ground loot)
    ├── materials/          # Material tiers that are combined with item templates
    │   ├── weapons.json         # Bronze → Legendary weapon materials
    │   ├── armor.json           # Armor material tiers
    │   ├── cloth.json           # Cloth/robe material tiers
    │   └── jewelry.json         # Jewelry material tiers
    └── monsters/           # Monster definitions grouped by archetype
        ├── humanoids.json       # Goblins, orcs, trolls, etc. (CR 0.25–4.0)
        ├── animals.json         # Beasts and wildlife
        ├── undead.json          # Skeletons, zombies, liches, etc.
        ├── constructs.json      # Golems and magical constructs
        └── abominations.json    # High-CR aberrations and boss creatures
```

### Adding Content

Because all game data lives in JSON files under `data/`, new content can be added without modifying Python code:

- **New monster**: add an entry to the appropriate file in `data/monsters/` with `name`, `xp`, `gold`, `challenge_rating`, `archetype`, and optionally `items` (a list of item names from `data/items/`).
- **New item**: add an entry to the relevant file in `data/items/` with the required fields (`name`, `slot` or `type`, `body_part`, and stat fields).
- **New material**: add an entry to the appropriate file in `data/materials/` with `name` and `power`.
- **New race**: add an entry to `data/races.json` with `name` and `bonuses` (a dict of stat names to integer offsets).
