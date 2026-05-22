"""Shared fixtures for all test modules."""
import pytest
from unittest.mock import MagicMock

from classes.entity import Entity
from classes.game import Game
from classes.map_generator import MapGenerator


@pytest.fixture
def mock_stdscr():
    mock = MagicMock()
    mock.getmaxyx.return_value = (24, 80)
    return mock


@pytest.fixture
def bare_player():
    """Entity with default stats and no items."""
    return Entity(5, 5, '@', 'TestPlayer', 100, 0, 0)


def _apply_minimal_map(game):
    """Populate a game instance with a deterministic 10×20 map containing one room."""
    h, w = 10, 20
    game.map = [['#'] * w for _ in range(h)]
    for y in range(2, 7):
        for x in range(2, 12):
            game.map[y][x] = '.'
    game.rooms = [(2, 2, 10, 5)]
    game.height = h
    game.width = w
    game.visible = [[False] * w for _ in range(h)]
    game.explored = [[False] * w for _ in range(h)]
    game.stairs_up_x, game.stairs_up_y = 3, 3
    game.stairs_x, game.stairs_y = 10, 4
    game.player.x, game.player.y = 5, 4
    mg = MapGenerator(h, w, 24, 80)
    mg.height = h
    mg.width = w
    game.map_generator = mg


@pytest.fixture
def minimal_game(mock_stdscr):
    """Minimal Game instance with a hand-crafted map — no curses rendering."""
    game = Game.create_minimal(24, 80, mock_stdscr)
    _apply_minimal_map(game)
    return game
