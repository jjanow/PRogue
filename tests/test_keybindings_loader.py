"""Tests for keybindings_loader.py — loading, parsing, and overrides."""
import curses
import json
import os
import pytest

from classes.keybindings_loader import (
    Keybindings,
    _DEFAULTS,
    _NAMED_KEYS,
    _parse_key,
    load_keybindings,
)


# ---------------------------------------------------------------------------
# _parse_key
# ---------------------------------------------------------------------------

class TestParseKey:
    def test_single_char_returns_ordinal(self):
        assert _parse_key("k") == ord("k")

    def test_comma(self):
        assert _parse_key(",") == ord(",")

    def test_uppercase(self):
        assert _parse_key("Q") == ord("Q")

    def test_named_key_up(self):
        assert _parse_key("KEY_UP") == curses.KEY_UP

    def test_named_ctrl_w(self):
        assert _parse_key("CTRL_W") == 23

    def test_all_named_keys_resolve(self):
        for name, code in _NAMED_KEYS.items():
            assert _parse_key(name) == code

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown key name"):
            _parse_key("NOT_A_KEY")

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="must be a string"):
            _parse_key(65)

    def test_multi_char_non_named_raises(self):
        with pytest.raises(ValueError, match="Unknown key name"):
            _parse_key("kk")


# ---------------------------------------------------------------------------
# load_keybindings — real data file
# ---------------------------------------------------------------------------

class TestLoadKeybindingsFromFile:
    def test_returns_keybindings_instance(self):
        kb = load_keybindings()
        assert isinstance(kb, Keybindings)

    def test_all_actions_populated(self):
        kb = load_keybindings()
        for action in _DEFAULTS:
            keys = getattr(kb, action)
            assert isinstance(keys, frozenset), f"{action} is not a frozenset"
            assert len(keys) > 0, f"{action} has no keys bound"

    def test_default_movement_contains_expected_keys(self):
        kb = load_keybindings()
        assert ord("k") in kb.move_n
        assert curses.KEY_UP in kb.move_n
        assert ord("j") in kb.move_s
        assert curses.KEY_DOWN in kb.move_s
        assert ord("h") in kb.move_w
        assert ord("l") in kb.move_e

    def test_default_diagonal_keys(self):
        kb = load_keybindings()
        assert ord("y") in kb.move_nw
        assert curses.KEY_HOME in kb.move_nw
        assert ord("u") in kb.move_ne
        assert ord("b") in kb.move_sw
        assert ord("n") in kb.move_se

    def test_default_action_keys(self):
        kb = load_keybindings()
        assert ord("i") in kb.inventory
        assert ord(",") in kb.pickup
        assert ord(">") in kb.stairs_down
        assert ord("<") in kb.stairs_up
        assert ord("w") in kb.walk_mode
        assert ord("0") in kb.auto_explore
        assert ord("=") in kb.options
        assert ord("?") in kb.help
        assert ord("@") in kb.character_stats
        assert 23 in kb.combat_stats       # CTRL_W
        assert ord("Q") in kb.quit
        assert ord("!") in kb.debug

    def test_wait_contains_numpad_5_and_b2(self):
        kb = load_keybindings()
        assert ord("5") in kb.wait
        assert curses.KEY_B2 in kb.wait


# ---------------------------------------------------------------------------
# load_keybindings — missing file falls back to defaults
# ---------------------------------------------------------------------------

class TestLoadKeybindingsMissingFile:
    def test_missing_file_returns_defaults(self, tmp_path):
        kb = load_keybindings(path=str(tmp_path / "nonexistent.json"))
        assert ord("k") in kb.move_n
        assert ord("i") in kb.inventory

    def test_missing_file_all_actions_populated(self, tmp_path):
        kb = load_keybindings(path=str(tmp_path / "nonexistent.json"))
        for action in _DEFAULTS:
            assert len(getattr(kb, action)) > 0


# ---------------------------------------------------------------------------
# load_keybindings — custom file overrides
# ---------------------------------------------------------------------------

class TestLoadKeybindingsCustomFile:
    def _write(self, tmp_path, data):
        p = tmp_path / "keybindings.json"
        p.write_text(json.dumps(data))
        return str(p)

    def test_override_single_action(self, tmp_path):
        path = self._write(tmp_path, {"inventory": ["z"]})
        kb = load_keybindings(path)
        assert ord("z") in kb.inventory
        assert ord("i") not in kb.inventory  # overridden, not merged

    def test_unmentioned_actions_keep_defaults(self, tmp_path):
        path = self._write(tmp_path, {"quit": ["X"]})
        kb = load_keybindings(path)
        assert ord("X") in kb.quit
        assert ord("k") in kb.move_n   # untouched

    def test_override_movement_keys(self, tmp_path):
        path = self._write(tmp_path, {"move_n": ["t"], "move_s": ["g"]})
        kb = load_keybindings(path)
        assert ord("t") in kb.move_n
        assert ord("k") not in kb.move_n
        assert ord("g") in kb.move_s

    def test_named_key_in_override(self, tmp_path):
        path = self._write(tmp_path, {"wait": ["KEY_B2"]})
        kb = load_keybindings(path)
        assert curses.KEY_B2 in kb.wait

    def test_multiple_keys_per_action(self, tmp_path):
        path = self._write(tmp_path, {"pickup": ["g", "p"]})
        kb = load_keybindings(path)
        assert ord("g") in kb.pickup
        assert ord("p") in kb.pickup

    def test_invalid_key_name_raises(self, tmp_path):
        path = self._write(tmp_path, {"inventory": ["INVALID"]})
        with pytest.raises(ValueError, match="Unknown key name"):
            load_keybindings(path)

    def test_non_list_binding_raises(self, tmp_path):
        path = self._write(tmp_path, {"inventory": "i"})
        with pytest.raises(ValueError, match="must be a list"):
            load_keybindings(path)

    def test_empty_file_object_uses_all_defaults(self, tmp_path):
        path = self._write(tmp_path, {})
        kb = load_keybindings(path)
        assert ord("k") in kb.move_n
        assert ord("i") in kb.inventory


# ---------------------------------------------------------------------------
# Duplicate key detection
# ---------------------------------------------------------------------------

class TestDuplicateDetection:
    def _write(self, tmp_path, data):
        p = tmp_path / "keybindings.json"
        p.write_text(json.dumps(data))
        return str(p)

    def test_duplicate_across_actions_raises(self, tmp_path):
        # Bind "i" to both inventory and pickup — should fail
        path = self._write(tmp_path, {"inventory": ["i"], "pickup": ["i"]})
        with pytest.raises(ValueError, match="Duplicate key bindings"):
            load_keybindings(path)

    def test_duplicate_message_names_both_actions(self, tmp_path):
        path = self._write(tmp_path, {"quit": ["Q"], "debug": ["Q"]})
        with pytest.raises(ValueError, match="'quit'") as exc_info:
            load_keybindings(path)
        assert "debug" in str(exc_info.value)

    def test_duplicate_named_key_raises(self, tmp_path):
        path = self._write(tmp_path, {"move_n": ["KEY_UP"], "move_s": ["KEY_UP"]})
        with pytest.raises(ValueError, match="Duplicate key bindings"):
            load_keybindings(path)

    def test_no_duplicate_in_defaults(self):
        # The built-in defaults must themselves be conflict-free
        kb = load_keybindings()
        assert isinstance(kb, Keybindings)  # would have raised if there were duplicates

    def test_non_printable_code_shown_as_code_number(self, tmp_path):
        # KEY_UP is non-printable; error message should say "code <n>"
        path = self._write(tmp_path, {"move_n": ["KEY_UP"], "move_s": ["KEY_UP"]})
        with pytest.raises(ValueError) as exc_info:
            load_keybindings(path)
        assert "code" in str(exc_info.value)

    def test_printable_char_shown_as_repr(self, tmp_path):
        path = self._write(tmp_path, {"inventory": ["z"], "pickup": ["z"]})
        with pytest.raises(ValueError) as exc_info:
            load_keybindings(path)
        assert "'z'" in str(exc_info.value)
