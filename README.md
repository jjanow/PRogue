# PRogue

## Overview

PRogue is a traditional roguelike game. This project is in its very early stages and is under active development. The game aims to explore classic roguelike mechanics with a focus on procedural generation and turn-based gameplay.

## Features

- Procedurally generated dungeons
- Turn-based combat with random enemies and loot
- Diagonal movement using the number pad (1,3,7,9)
- Auto-explore and walk-to-stairs commands
- Inventory and equipment management screens
- In-game help and options menus

## Getting Started

To run the game, ensure you have Python installed.

On **Windows**, install the optional `windows-curses` package first. On macOS and Linux the standard `curses` module is already included:

```bash
pip install windows-curses
```

Then execute the following command to start the game:

```bash
python pRoguelike.py
```

Make sure to run the game in a terminal that supports `curses`.

- Move with the arrow keys or number pad. Diagonals use `1`, `3`, `7`, and `9`.
- `,` picks up an item on the ground.
- `>` and `<` take you down or up a staircase.
- Press `5` (or the keypad center) to wait a turn.
- Press `0` to auto-explore the dungeon. Use `w` to walk to the nearest stairs.
- Open the inventory with `i` and press the shown letter to equip or use an item. Drop items with `d`.
- View your character sheet with `@`.
- Open the options menu with `=` to adjust auto-walk speed and ESC key delay.
- Press `?` to view this command list at any time.
- Press `Q` to quit the game.
