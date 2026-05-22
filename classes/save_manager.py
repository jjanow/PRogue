import json
import os
import pickle
import base64
import time
import zlib
from datetime import datetime
from pathlib import Path
from classes.map_generator import MapGenerator


SAVE_VERSION = '2.0'


class SaveManager:
    def __init__(self, save_dir="saves"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.max_slots = 10
        
    def get_save_info(self, slot):
        """Get information about a save slot."""
        save_file = self.save_dir / f"save_{slot}.json"
        if save_file.exists():
            try:
                with open(save_file, 'r') as f:
                    data = json.load(f)
                return {
                    'slot': slot,
                    'exists': True,
                    'character_name': data.get('character_name', 'Unknown'),
                    'level': data.get('dungeon_level', 1),
                    'player_level': data.get('player_level', 1),
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'playtime': data.get('playtime', 0)
                }
            except Exception:
                return {'slot': slot, 'exists': False}
        return {'slot': slot, 'exists': False}
    
    def get_all_save_info(self):
        """Get information about all save slots."""
        saves = []
        for slot in range(1, self.max_slots + 1):
            saves.append(self.get_save_info(slot))
        return saves
    
    def _compress_data(self, data):
        """Compress data using zlib and encode as base64."""
        json_str = json.dumps(data, separators=(',', ':'))
        compressed = zlib.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('ascii')
    
    def _decompress_data(self, compressed_data):
        """Decompress data from base64 encoded zlib compressed data."""
        compressed = base64.b64decode(compressed_data.encode('ascii'))
        json_str = zlib.decompress(compressed).decode('utf-8')
        return json.loads(json_str)
    
    def _serialize_map(self, map_data):
        """Serialize map as a compact string format."""
        if not map_data:
            return ""
        
        # Convert 2D array to a single string with newlines
        map_str = '\n'.join(''.join(row) for row in map_data)
        return map_str
    
    def _deserialize_map(self, map_str):
        """Deserialize map from compact string format."""
        if not map_str:
            return []
        
        # Convert string back to 2D array
        rows = map_str.split('\n')
        return [list(row) for row in rows]
    
    def _serialize_2d_array(self, array_2d):
        """Serialize 2D boolean arrays (like visible, explored) as compact format."""
        if not array_2d:
            return ""
        
        # Convert boolean 2D array to a compact string
        # Use '1' for True, '0' for False, with newlines separating rows
        result = []
        for row in array_2d:
            row_str = ''.join('1' if cell else '0' for cell in row)
            result.append(row_str)
        return '\n'.join(result)
    
    def _deserialize_2d_array(self, array_str, width, height):
        """Deserialize 2D boolean array from compact string format."""
        if not array_str:
            return [[False for _ in range(width)] for _ in range(height)]
        
        rows = array_str.split('\n')
        result = []
        for row in rows:
            if len(row) != width:
                # Pad or truncate row to match width
                row = row[:width] + '0' * (width - len(row))
            result.append([cell == '1' for cell in row])
        
        # Ensure we have the right number of rows
        while len(result) < height:
            result.append([False] * width)
        result = result[:height]
        
        return result
    
    def save_game(self, game, slot):
        """Save the current game state to a slot."""
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")
        
        # Create save data with compact format
        save_data = {
            'version': SAVE_VERSION,
            'character_name': game.player.name,
            'player_level': game.player.level,
            'dungeon_level': game.dungeon_level,
            'timestamp': datetime.now().isoformat(),
            'playtime': time.time() - getattr(game, 'start_time', time.time()),
            'map_dimensions': {
                'width': game.width,
                'height': game.height
            },
            
            # Player data
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
                'equipment': self._serialize_equipment(game.player.equipment)
            },
            
            # Game state data with compact format
            'game_state': {
                'map': self._serialize_map(game.map),
                'rooms': game._serialize_rooms(game.rooms),
                'items': self._serialize_items(game.items),
                'enemies': self._serialize_enemies(game.enemies),
                'visible': self._serialize_2d_array(game.visible),
                'explored': self._serialize_2d_array(game.explored),
                'stairs_x': game.stairs_x,
                'stairs_y': game.stairs_y,
                'stairs_up_x': game.stairs_up_x,
                'stairs_up_y': game.stairs_up_y,
                'turn_count': game.turn_count,
                'last_spawn_turn': game.last_spawn_turn,
                'messages': game.messages[-10:],  # Keep last 10 messages
                'time': getattr(game, 'time', 0)
            }
        }
        
        # Save to file
        save_file = self.save_dir / f"save_{slot}.json"
        with open(save_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return True
    
    def load_game(self, game, slot):
        """Load a game state from a slot."""
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")
        
        save_file = self.save_dir / f"save_{slot}.json"
        if not save_file.exists():
            raise FileNotFoundError(f"Save slot {slot} does not exist")
        
        with open(save_file, 'r') as f:
            save_data = json.load(f)
        
        version = save_data.get('version', '1.0')

        # Restore player data
        player_data = save_data['player']
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
        
        # Restore inventory and equipment
        game.player.inventory = self._deserialize_inventory(player_data['inventory'])
        game.player.equipment = self._deserialize_equipment(player_data['equipment'])
        
        # Restore game state
        game_state = save_data['game_state']
        
        if version == SAVE_VERSION:
            game.map = self._deserialize_map(game_state['map'])
            game.rooms = game._deserialize_rooms(game_state['rooms'])
            game.items = self._deserialize_items(game_state['items'])
            game.enemies = self._deserialize_enemies(game_state['enemies'])
            
            # Get dimensions for 2D arrays
            dimensions = save_data.get('map_dimensions', {})
            width = dimensions.get('width', len(game.map[0]) if game.map else 0)
            height = dimensions.get('height', len(game.map) if game.map else 0)
            
            game.visible = self._deserialize_2d_array(game_state['visible'], width, height)
            game.explored = self._deserialize_2d_array(game_state['explored'], width, height)
        else:
            # Legacy format
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
        game.time = game_state.get('time', 0)
        
        # Update game dimensions
        game.height = len(game.map)
        game.width = len(game.map[0]) if game.map else 0

        # Ensure the game has a MapGenerator instance that matches the loaded map
        if not hasattr(game, 'map_generator') or game.map_generator is None:
            game.map_generator = MapGenerator(game.height, game.width, game.screen_height, game.screen_width)
        else:
            # Keep the existing generator but sync its dimensions
            game.map_generator.height = game.height
            game.map_generator.width = game.width

        # Update FOV
        game.update_fov()
        
        return True
    
    def delete_save(self, slot):
        """Delete a save slot."""
        if slot < 1 or slot > self.max_slots:
            raise ValueError(f"Invalid save slot: {slot}. Must be between 1 and {self.max_slots}")
        
        save_file = self.save_dir / f"save_{slot}.json"
        if save_file.exists():
            save_file.unlink()
            return True
        return False
    
    def _serialize_inventory(self, inventory):
        """Serialize player inventory for saving."""
        serialized = []
        for item, count in inventory.items():
            if hasattr(item, 'to_dict'):
                item_data = item.to_dict()
                item_data['count'] = count
                serialized.append(item_data)
        return serialized
    
    def _deserialize_inventory(self, serialized_inventory):
        """Deserialize player inventory from save data."""
        from collections import Counter
        from classes.item import Item, Equipment
        
        inventory = Counter()
        for item_data in serialized_inventory:
            count = item_data.get('count', 1)
            if item_data.get('slot'):
                item = Equipment.from_dict(item_data)
            else:
                item = Item.from_dict(item_data)
            inventory[item] = count
        return inventory
    
    def _serialize_equipment(self, equipment):
        """Serialize player equipment for saving."""
        serialized = {}
        for slot_key, slot_data in equipment.items():
            serialized[slot_key] = {
                'name': slot_data['name'],
                'item': slot_data['item'].to_dict() if slot_data['item'] else None
            }
        return serialized
    
    def _deserialize_equipment(self, serialized_equipment):
        """Deserialize player equipment from save data."""
        from classes.item import Equipment
        
        equipment = {}
        for slot_key, slot_data in serialized_equipment.items():
            equipment[slot_key] = {
                'name': slot_data['name'],
                'item': Equipment.from_dict(slot_data['item']) if slot_data['item'] else None
            }
        return equipment
    
    def _serialize_items(self, items):
        """Serialize game items for saving."""
        serialized = []
        for item in items:
            if hasattr(item, 'to_dict'):
                serialized.append(item.to_dict())
        return serialized
    
    def _deserialize_items(self, serialized_items):
        """Deserialize game items from save data."""
        from classes.item import Item, Equipment
        
        items = []
        for item_data in serialized_items:
            if item_data.get('slot'):
                item = Equipment.from_dict(item_data)
            else:
                item = Item.from_dict(item_data)
            item.x = item_data['x']
            item.y = item_data['y']
            items.append(item)
        return items
    
    def _serialize_enemies(self, enemies):
        """Serialize enemies for saving."""
        serialized = []
        for enemy in enemies:
            enemy_data = {
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
                'equipment': self._serialize_equipment(enemy.equipment)
            }
            serialized.append(enemy_data)
        return serialized
    
    def _deserialize_enemies(self, serialized_enemies):
        """Deserialize enemies from save data."""
        from classes.entity import Entity
        
        enemies = []
        for enemy_data in serialized_enemies:
            enemy = Entity(
                enemy_data['x'],
                enemy_data['y'],
                enemy_data['char'],
                enemy_data['name'],
                enemy_data['max_health'],
                enemy_data['base_damage'],
                enemy_data['base_defense']
            )
            
            _skip = {'x', 'y', 'char', 'name', 'max_health', 'base_damage', 'base_defense', 'inventory', 'equipment'}
            for key, value in enemy_data.items():
                if key not in _skip:
                    setattr(enemy, key, value)
            enemy.inventory = self._deserialize_inventory(enemy_data['inventory'])
            enemy.equipment = self._deserialize_equipment(enemy_data['equipment'])
            
            enemies.append(enemy)
        return enemies 