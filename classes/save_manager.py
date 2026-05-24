from __future__ import annotations
import json
import base64
import time
import zlib
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from classes.item import Item, Equipment
from classes.map_generator import MapGenerator

if TYPE_CHECKING:
    from classes.entity import Entity
    from classes.ecs import EquipmentSlot

SAVE_VERSION = '2.0'

SaveInfo = dict[str, str | int | bool | float]


class SaveManager:
    def __init__(self, save_dir: str = "saves") -> None:
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.max_slots = 10

    def get_save_info(self, slot: int) -> SaveInfo:
        save_file = self.save_dir / f"save_{slot}.json"
        if save_file.exists():
            try:
                with open(save_file, 'r') as f:
                    data: dict[str, Any] = json.load(f)
                return {
                    'slot': slot,
                    'exists': True,
                    'character_name': data.get('character_name', 'Unknown'),
                    'level': data.get('dungeon_level', 1),
                    'player_level': data.get('player_level', 1),
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'playtime': data.get('playtime', 0),
                }
            except Exception:
                return {'slot': slot, 'exists': False}
        return {'slot': slot, 'exists': False}

    def get_all_save_info(self) -> list[SaveInfo]:
        saves: list[SaveInfo] = []
        for slot in range(1, self.max_slots + 1):
            saves.append(self.get_save_info(slot))
        return saves

    def _compress_data(self, data: object) -> str:
        json_str = json.dumps(data, separators=(',', ':'))
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('ascii')

    def _decompress_data(self, compressed_data: str) -> Any:
        compressed = base64.b64decode(compressed_data.encode('ascii'))
        json_str = zlib.decompress(compressed).decode('utf-8')
        return json.loads(json_str)

    def _serialize_map(self, map_data: list[list[str]]) -> str:
        if not map_data:
            return ""
        return '\n'.join(''.join(row) for row in map_data)

    def _deserialize_map(self, map_str: str) -> list[list[str]]:
        if not map_str:
            return []
        rows = map_str.split('\n')
        return [list(row) for row in rows]

    def _serialize_2d_array(self, array_2d: list[list[bool]]) -> str:
        if not array_2d:
            return ""
        result: list[str] = []
        for row in array_2d:
            result.append(''.join('1' if cell else '0' for cell in row))
        return '\n'.join(result)

    def _deserialize_2d_array(self, array_str: str, width: int, height: int) -> list[list[bool]]:
        if not array_str:
            return [[False for _ in range(width)] for _ in range(height)]
        rows = array_str.split('\n')
        result: list[list[bool]] = []
        for row in rows:
            if len(row) != width:
                row = row[:width] + '0' * (width - len(row))
            result.append([cell == '1' for cell in row])
        while len(result) < height:
            result.append([False] * width)
        return result[:height]

    def save_game(self, game: Any, slot: int) -> bool:
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")

        save_data: dict[str, Any] = {
            'version': SAVE_VERSION,
            'character_name': game.player.name,
            'player_level': game.player.level,
            'dungeon_level': game.dungeon_level,
            'in_town': game.in_town,
            'allow_enemy_spawning': game.allow_enemy_spawning,
            'timestamp': datetime.now().isoformat(),
            'playtime': time.time() - getattr(game, 'start_time', time.time()),
            'map_dimensions': {
                'width': game.width,
                'height': game.height,
            },
            'player': {
                'x': game.player.x,
                'y': game.player.y,
                'char': game.player.char,
                'name': game.player.name,
                'max_health': game.player.max_health,
                'health': game.player.health,
                'base_damage': game.player.base_damage,
                'base_defense': game.player.base_defense,
                'level': game.player.level,
                'xp': game.player.xp,
                'xp_to_next_level': game.player.xp_to_next_level,
                'strength': game.player.strength,
                'dexterity': game.player.dexterity,
                'constitution': game.player.constitution,
                'intelligence': game.player.intelligence,
                'willpower': game.player.willpower,
                'charisma': game.player.charisma,
                'appearance': game.player.appearance,
                'perception': game.player.perception,
                'speed': game.player.speed,
                'max_mana': game.player.max_mana,
                'mana': game.player.mana,
                'max_psi': game.player.max_psi,
                'psi': game.player.psi,
                'money': game.player.money,
                'deity': game.player.deity,
                'birth': game.player.birth,
                'month': game.player.month,
                'day': game.player.day,
                'age': game.player.age,
                'gender': game.player.gender,
                'sex': game.player.sex,
                'race': game.player.race,
                'inventory': self._serialize_inventory(game.player.inventory),
                'equipment': self._serialize_equipment(game.player.equipment),
            },
            'game_state': {
                'map': self._serialize_map(game.map),
                'rooms': game._serialize_rooms(game.rooms),
                'items': self._serialize_items(game.items),
                'enemies': self._serialize_enemies(game.enemies),
                'visible': self._serialize_2d_array(game.visible),
                'explored': self._serialize_2d_array(game.explored),
                'town_explored': self._serialize_2d_array(
                    game._town_explored) if game._town_explored else None,
                'town_items': self._serialize_items(game._town_items),
                'stairs_x': game.stairs_x,
                'stairs_y': game.stairs_y,
                'stairs_up_x': game.stairs_up_x,
                'stairs_up_y': game.stairs_up_y,
                'turn_count': game.turn_count,
                'last_spawn_turn': game.last_spawn_turn,
                'messages': game.messages[-10:],
                'time': getattr(game, 'time', 0),
            },
        }

        save_file = self.save_dir / f"save_{slot}.json"
        with open(save_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        return True

    def load_game(self, game: Any, slot: int) -> bool:
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")

        save_file = self.save_dir / f"save_{slot}.json"
        if not save_file.exists():
            raise FileNotFoundError(f"Save slot {slot} does not exist")

        with open(save_file, 'r') as f:
            save_data: dict[str, Any] = json.load(f)

        version: str = save_data.get('version', '1.0')

        player_data: dict[str, Any] = save_data['player']
        game.player.x = player_data['x']
        game.player.y = player_data['y']
        game.player.char = player_data['char']
        game.player.name = player_data['name']
        game.player.max_health = player_data['max_health']
        game.player.health = player_data['health']
        game.player.base_damage = player_data['base_damage']
        game.player.base_defense = player_data['base_defense']
        game.player.level = player_data['level']
        game.player.xp = player_data['xp']
        game.player.xp_to_next_level = player_data['xp_to_next_level']
        game.player.strength = player_data['strength']
        game.player.dexterity = player_data['dexterity']
        game.player.constitution = player_data['constitution']
        game.player.intelligence = player_data['intelligence']
        game.player.willpower = player_data['willpower']
        game.player.charisma = player_data['charisma']
        game.player.appearance = player_data['appearance']
        game.player.perception = player_data['perception']
        game.player.speed = player_data['speed']
        game.player.max_mana = player_data['max_mana']
        game.player.mana = player_data['mana']
        game.player.max_psi = player_data['max_psi']
        game.player.psi = player_data['psi']
        game.player.money = player_data['money']
        game.player.deity = player_data['deity']
        game.player.birth = player_data['birth']
        game.player.month = player_data['month']
        game.player.day = player_data['day']
        game.player.age = player_data['age']
        game.player.gender = player_data['gender']
        game.player.sex = player_data['sex']
        game.player.race = player_data['race']

        game.player.inventory = self._deserialize_inventory(player_data['inventory'])
        game.player.equipment = self._deserialize_equipment(player_data['equipment'])

        game_state: dict[str, Any] = save_data['game_state']

        if version == SAVE_VERSION:
            game.map = self._deserialize_map(game_state['map'])
            game.rooms = game._deserialize_rooms(game_state['rooms'])
            game.items = self._deserialize_items(game_state['items'])
            game.enemies = self._deserialize_enemies(game_state['enemies'])

            dimensions: dict[str, Any] = save_data.get('map_dimensions', {})
            width: int = dimensions.get('width', len(game.map[0]) if game.map else 0)
            height: int = dimensions.get('height', len(game.map) if game.map else 0)

            game.visible = self._deserialize_2d_array(game_state['visible'], width, height)
            game.explored = self._deserialize_2d_array(game_state['explored'], width, height)
        else:
            game.map = game_state['map']
            game.rooms = game._deserialize_rooms(game_state['rooms'])
            game.items = self._deserialize_items(game_state['items'])
            game.enemies = self._deserialize_enemies(game_state['enemies'])
            game.visible = game_state['visible']
            game.explored = game_state['explored']

        game.stairs_x = game_state['stairs_x']
        game.stairs_y = game_state['stairs_y']
        game.stairs_up_x = game_state['stairs_up_x']
        game.stairs_up_y = game_state['stairs_up_y']
        game.turn_count = game_state['turn_count']
        game.last_spawn_turn = game_state['last_spawn_turn']
        game.messages = game_state['messages']
        game.dungeon_level = save_data['dungeon_level']
        game.in_town = save_data.get('in_town', False)
        game.allow_enemy_spawning = save_data.get('allow_enemy_spawning', True)
        game.time = game_state.get('time', 0)

        raw_town_exp: str | None = game_state.get('town_explored')
        if raw_town_exp:
            te_rows = raw_town_exp.split('\n')
            te_h = len(te_rows)
            te_w = len(te_rows[0]) if te_rows else 0
            game._town_explored = self._deserialize_2d_array(raw_town_exp, te_w, te_h)
        else:
            game._town_explored = None
        game._town_items = self._deserialize_items(game_state.get('town_items', []))

        game.height = len(game.map)
        game.width = len(game.map[0]) if game.map else 0

        if not hasattr(game, 'map_generator') or game.map_generator is None:
            game.map_generator = MapGenerator(game.height, game.width, game.screen_height, game.screen_width)
        else:
            game.map_generator.height = game.height
            game.map_generator.width = game.width

        game.update_fov()
        return True

    def delete_save(self, slot: int) -> bool:
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")
        save_file = self.save_dir / f"save_{slot}.json"
        if save_file.exists():
            save_file.unlink()
            return True
        return False

    def _serialize_inventory(self, inventory: Counter[Item]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item, count in inventory.items():
            item_data = item.to_dict()
            item_data['count'] = count
            serialized.append(item_data)
        return serialized

    def _deserialize_inventory(self, serialized_inventory: list[dict[str, Any]]) -> Counter[Item]:
        inventory: Counter[Item] = Counter()
        for item_data in serialized_inventory:
            count: int = item_data.get('count', 1)
            if item_data.get('slot'):
                item: Item = Equipment.from_dict(item_data)
            else:
                item = Item.from_dict(item_data)
            inventory[item] = count
        return inventory

    def _serialize_equipment(self, equipment: dict[str, EquipmentSlot]) -> dict[str, dict[str, Any]]:
        serialized: dict[str, dict[str, Any]] = {}
        for slot_key, slot_data in equipment.items():
            serialized[slot_key] = {
                'name': slot_data['name'],
                'item': slot_data['item'].to_dict() if slot_data['item'] else None,
            }
        return serialized

    def _deserialize_equipment(self, serialized_equipment: dict[str, dict[str, Any]]) -> dict[str, EquipmentSlot]:
        from classes.ecs import EquipmentSlot as ES
        equipment: dict[str, EquipmentSlot] = {}
        for slot_key, slot_data in serialized_equipment.items():
            eq_item = Equipment.from_dict(slot_data['item']) if slot_data['item'] else None
            equipment[slot_key] = ES(name=slot_data['name'], item=eq_item)
        return equipment

    def _serialize_items(self, items: list[Item]) -> list[dict[str, Any]]:
        return [item.to_dict() for item in items]

    def _deserialize_items(self, serialized_items: list[dict[str, Any]]) -> list[Item]:
        items: list[Item] = []
        for item_data in serialized_items:
            if item_data.get('slot'):
                item: Item = Equipment.from_dict(item_data)
            else:
                item = Item.from_dict(item_data)
            item.x = item_data['x']
            item.y = item_data['y']
            items.append(item)
        return items

    def _serialize_enemies(self, enemies: list[Entity]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for enemy in enemies:
            enemy_data: dict[str, Any] = {
                'x': enemy.x,
                'y': enemy.y,
                'char': enemy.char,
                'name': enemy.name,
                'max_health': enemy.max_health,
                'health': enemy.health,
                'base_damage': enemy.base_damage,
                'base_defense': enemy.base_defense,
                'level': enemy.level,
                'xp': enemy.xp,
                'xp_to_next_level': enemy.xp_to_next_level,
                'strength': enemy.strength,
                'dexterity': enemy.dexterity,
                'constitution': enemy.constitution,
                'intelligence': enemy.intelligence,
                'willpower': enemy.willpower,
                'charisma': enemy.charisma,
                'appearance': enemy.appearance,
                'perception': enemy.perception,
                'speed': enemy.speed,
                'max_mana': enemy.max_mana,
                'mana': enemy.mana,
                'max_psi': enemy.max_psi,
                'psi': enemy.psi,
                'money': enemy.money,
                'deity': enemy.deity,
                'birth': enemy.birth,
                'month': enemy.month,
                'day': enemy.day,
                'age': enemy.age,
                'gender': enemy.gender,
                'sex': enemy.sex,
                'race': enemy.race,
                'xp_reward': enemy.xp_reward,
                'gold_reward': enemy.gold_reward,
                'inventory': self._serialize_inventory(enemy.inventory),
                'equipment': self._serialize_equipment(enemy.equipment),
            }
            serialized.append(enemy_data)
        return serialized

    def _deserialize_enemies(self, serialized_enemies: list[dict[str, Any]]) -> list[Entity]:
        from classes.entity import Entity

        enemies: list[Entity] = []
        for enemy_data in serialized_enemies:
            enemy = Entity(
                enemy_data['x'],
                enemy_data['y'],
                enemy_data['char'],
                enemy_data['name'],
                enemy_data['max_health'],
                enemy_data['base_damage'],
                enemy_data['base_defense'],
            )
            skip = {'x', 'y', 'char', 'name', 'max_health', 'base_damage', 'base_defense', 'inventory', 'equipment'}
            for key, value in enemy_data.items():
                if key not in skip:
                    setattr(enemy, key, value)
            enemy.inventory = self._deserialize_inventory(enemy_data['inventory'])
            enemy.equipment = self._deserialize_equipment(enemy_data['equipment'])
            enemies.append(enemy)
        return enemies
