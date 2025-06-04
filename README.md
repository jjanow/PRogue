# PRogue

## Overview

PRogue is a traditional roguelike game. This project is in its very early stages and is under active development. The game aims to explore classic roguelike mechanics with a focus on procedural generation and turn-based gameplay.

## Features

- Procedurally generated dungeons
- Basic movement and combat mechanics
- Diagonal movement using the number pad (1,3,7,9)
- Randomly generated enemies and items

## Getting Started

To run the game, ensure you have Python installed, then execute the following command:

```bash
python pRoguelike.py
```

Make sure to run the game in a terminal that supports `curses`.
Use the arrow keys or the number pad for movement. Diagonal steps are mapped to
`1`, `3`, `7`, and `9` on the number pad. Press `Q` during play to begin the
quit process.
While in the dungeon, press `i` to open your inventory. Press the letter
corresponding to an equipment item to wear or wield it. Any item already in that
slot will be returned to your pack automatically.
