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

Press `0` on the number pad to auto-explore the dungeon. Exploration will pause
whenever you spot a monster so you can react.

While in the dungeon, press `i` to open your inventory. Press the letter
corresponding to an equipment item to wear or wield it. Any item already in that
slot will be returned to your pack automatically.
=======

### Note on Escape Key Responsiveness

By default, `curses` waits up to a second to decide whether an `ESC` press is
part of a special key sequence. To make exiting menus feel snappier, PRogue sets
the delay to 25&nbsp;ms. If you wish to change this value, set the `ESCDELAY`
environment variable before launching the game.
