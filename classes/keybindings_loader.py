import curses
import json
import os
from dataclasses import dataclass, field

# Named special keys that can be referenced in keybindings.json
_NAMED_KEYS = {
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

_DEFAULTS = {
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


@dataclass
class Keybindings:
    move_n: frozenset = field(default_factory=frozenset)
    move_s: frozenset = field(default_factory=frozenset)
    move_w: frozenset = field(default_factory=frozenset)
    move_e: frozenset = field(default_factory=frozenset)
    move_nw: frozenset = field(default_factory=frozenset)
    move_ne: frozenset = field(default_factory=frozenset)
    move_sw: frozenset = field(default_factory=frozenset)
    move_se: frozenset = field(default_factory=frozenset)
    wait: frozenset = field(default_factory=frozenset)
    inventory: frozenset = field(default_factory=frozenset)
    pickup: frozenset = field(default_factory=frozenset)
    stairs_down: frozenset = field(default_factory=frozenset)
    stairs_up: frozenset = field(default_factory=frozenset)
    walk_mode: frozenset = field(default_factory=frozenset)
    auto_explore: frozenset = field(default_factory=frozenset)
    options: frozenset = field(default_factory=frozenset)
    help: frozenset = field(default_factory=frozenset)
    character_stats: frozenset = field(default_factory=frozenset)
    combat_stats: frozenset = field(default_factory=frozenset)
    quit: frozenset = field(default_factory=frozenset)
    debug: frozenset = field(default_factory=frozenset)
    open_door: frozenset = field(default_factory=frozenset)
    close_door: frozenset = field(default_factory=frozenset)
    rest: frozenset = field(default_factory=frozenset)


def _parse_key(s):
    """Convert a key string from JSON to an integer key code."""
    if not isinstance(s, str):
        raise ValueError(f"Key entry must be a string, got {type(s).__name__!r}: {s!r}")
    if s in _NAMED_KEYS:
        return _NAMED_KEYS[s]
    if len(s) == 1:
        return ord(s)
    raise ValueError(
        f"Unknown key name {s!r}. Use a single character or one of: "
        + ", ".join(sorted(_NAMED_KEYS))
    )


def _build_keybindings(raw):
    """Build a Keybindings instance from a dict of action -> list[str]."""
    merged = dict(_DEFAULTS)
    merged.update(raw)
    kwargs = {}
    for action in _DEFAULTS:
        key_strings = merged.get(action, _DEFAULTS[action])
        if not isinstance(key_strings, list):
            raise ValueError(f"Binding for {action!r} must be a list, got {type(key_strings).__name__!r}")
        codes = frozenset(_parse_key(s) for s in key_strings)
        kwargs[action] = codes

    # Detect keys assigned to more than one action
    seen = {}  # key_code -> first action name
    conflicts = []
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


def load_keybindings(path=None):
    """Load keybindings from a JSON file, falling back to built-in defaults."""
    if path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, '..', 'data', 'keybindings.json')

    if not os.path.exists(path):
        return _build_keybindings({})

    with open(path, 'r') as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("keybindings.json must contain a JSON object")

    return _build_keybindings(raw)
