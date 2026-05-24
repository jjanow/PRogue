from __future__ import annotations

import curses
import json
import os
from dataclasses import dataclass, field

# Named special keys that can be referenced in keybindings.json
_NAMED_KEYS: dict[str, int] = {
    "KEY_UP":    curses.KEY_UP,
    "KEY_DOWN":  curses.KEY_DOWN,
    "KEY_LEFT":  curses.KEY_LEFT,
    "KEY_RIGHT": curses.KEY_RIGHT,
    "KEY_HOME":  curses.KEY_HOME,
    "KEY_END":   curses.KEY_END,
    "KEY_NPAGE": curses.KEY_NPAGE,
    "KEY_PPAGE": curses.KEY_PPAGE,
    "KEY_A1":    curses.KEY_A1,
    "KEY_A3":    curses.KEY_A3,
    "KEY_C1":    curses.KEY_C1,
    "KEY_C3":    curses.KEY_C3,
    "KEY_B2":    curses.KEY_B2,
    "CTRL_W":    23,
    "ENTER":     10,
    "BACKSPACE": 8,
    "DEL":       127,
}

_DEFAULTS: dict[str, list[str]] = {
    "move_n":        ["k", "8", "KEY_UP"],
    "move_s":        ["j", "2", "KEY_DOWN"],
    "move_w":        ["h", "4", "KEY_LEFT"],
    "move_e":        ["l", "6", "KEY_RIGHT"],
    "move_nw":       ["y", "7", "KEY_HOME", "KEY_A1"],
    "move_ne":       ["u", "9", "KEY_PPAGE", "KEY_A3"],
    "move_sw":       ["b", "1", "KEY_END", "KEY_C1"],
    "move_se":       ["n", "3", "KEY_NPAGE", "KEY_C3"],
    "wait":          ["5", "KEY_B2"],
    "inventory":     ["i"],
    "pickup":        [","],
    "stairs_down":   [">"],
    "stairs_up":     ["<"],
    "walk_mode":     ["w"],
    "auto_explore":  ["0"],
    "options":       ["="],
    "help":          ["?"],
    "character_stats": ["@"],
    "combat_stats":  ["CTRL_W"],
    "quit":          ["Q"],
    "debug":         ["!"],
    "open_door":     ["o"],
    "close_door":    ["c"],
    "rest":          ["r"],
}


def _empty_frozenset() -> frozenset[int]:
    return frozenset()


@dataclass
class Keybindings:
    move_n: frozenset[int] = field(default_factory=_empty_frozenset)
    move_s: frozenset[int] = field(default_factory=_empty_frozenset)
    move_w: frozenset[int] = field(default_factory=_empty_frozenset)
    move_e: frozenset[int] = field(default_factory=_empty_frozenset)
    move_nw: frozenset[int] = field(default_factory=_empty_frozenset)
    move_ne: frozenset[int] = field(default_factory=_empty_frozenset)
    move_sw: frozenset[int] = field(default_factory=_empty_frozenset)
    move_se: frozenset[int] = field(default_factory=_empty_frozenset)
    wait: frozenset[int] = field(default_factory=_empty_frozenset)
    inventory: frozenset[int] = field(default_factory=_empty_frozenset)
    pickup: frozenset[int] = field(default_factory=_empty_frozenset)
    stairs_down: frozenset[int] = field(default_factory=_empty_frozenset)
    stairs_up: frozenset[int] = field(default_factory=_empty_frozenset)
    walk_mode: frozenset[int] = field(default_factory=_empty_frozenset)
    auto_explore: frozenset[int] = field(default_factory=_empty_frozenset)
    options: frozenset[int] = field(default_factory=_empty_frozenset)
    help: frozenset[int] = field(default_factory=_empty_frozenset)
    character_stats: frozenset[int] = field(default_factory=_empty_frozenset)
    combat_stats: frozenset[int] = field(default_factory=_empty_frozenset)
    quit: frozenset[int] = field(default_factory=_empty_frozenset)
    debug: frozenset[int] = field(default_factory=_empty_frozenset)
    open_door: frozenset[int] = field(default_factory=_empty_frozenset)
    close_door: frozenset[int] = field(default_factory=_empty_frozenset)
    rest: frozenset[int] = field(default_factory=_empty_frozenset)


def _parse_key(s: str) -> int:
    """Convert a key string from JSON to an integer key code."""
    if not isinstance(s, str):  # type: ignore[unnecessary-isinstance]
        raise ValueError(f"Key entry must be a string, got {type(s).__name__!r}: {s!r}")
    if s in _NAMED_KEYS:
        return _NAMED_KEYS[s]
    if len(s) == 1:
        return ord(s)
    raise ValueError(
        f"Unknown key name {s!r}. Use a single character or one of: "
        + ", ".join(sorted(_NAMED_KEYS))
    )


def _build_keybindings(raw: dict[str, list[str]]) -> Keybindings:
    """Build a Keybindings instance from a dict of action -> list[str]."""
    merged: dict[str, list[str]] = dict(_DEFAULTS)
    merged.update(raw)
    kwargs: dict[str, frozenset[int]] = {}
    for action in _DEFAULTS:
        key_strings = merged.get(action, _DEFAULTS[action])
        if not isinstance(key_strings, list):  # type: ignore[unnecessary-isinstance]
            raise ValueError(f"Binding for {action!r} must be a list, got {type(key_strings).__name__!r}")
        codes: frozenset[int] = frozenset(_parse_key(s) for s in key_strings)
        kwargs[action] = codes

    # Detect keys assigned to more than one action
    seen: dict[int, str] = {}  # key_code -> first action name
    conflicts: list[str] = []
    for action, codes in kwargs.items():
        for code in codes:
            if code in seen:
                label = repr(chr(code)) if 32 <= code < 127 else f"code {code}"
                conflicts.append(f"{label} is bound to both {seen[code]!r} and {action!r}")
            else:
                seen[code] = action
    if conflicts:
        raise ValueError("Duplicate key bindings detected:\n" + "\n".join(f"  {c}" for c in conflicts))

    return Keybindings(**kwargs)


def load_keybindings(path: str | None = None) -> Keybindings:
    """Load keybindings from a JSON file, falling back to built-in defaults."""
    if path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, '..', 'data', 'keybindings.json')

    if not os.path.exists(path):
        return _build_keybindings({})

    with open(path, 'r') as f:
        raw: object = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("keybindings.json must contain a JSON object")

    # raw is dict[str, list[str]] after validation
    return _build_keybindings(raw)  # type: ignore[arg-type]
