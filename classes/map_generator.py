import random

class MapGenerator:
    def __init__(self, height, width, screen_height, screen_width):
        self.height = min(max(10, height), screen_height - 5)  # Ensure minimum height of 10 and max height of screen height minus 5
        self.width = min(max(20, width), screen_width - 5)  # Ensure minimum width of 20 and max width of screen width minus 5

    def generate(self):
        # Existing map generation logic
        self.map, self.rooms = self._generate_map_and_rooms()
        
        # Ensure the bottom row is always a wall
        for x in range(self.width):
            self.map[self.height - 1][x] = '#'
        
        return self.map, self.rooms

    def _generate_map_and_rooms(self):
        self.map = [['#' for _ in range(self.width)] for _ in range(self.height)]
        rooms = []
        max_rooms = min(10, (self.height * self.width) // 100)  # Adjust max rooms based on map size
        
        for _ in range(max_rooms):
            room_height = max(3, min(5, random.randint(3, self.height // 3)))
            room_width = max(5, min(7, random.randint(5, self.width // 3)))
            
            # Ensure there's space for the room
            if self.height - room_height - 1 <= 1 or self.width - room_width - 1 <= 1:
                continue
            
            x = random.randint(1, self.width - room_width - 1)
            y = random.randint(1, self.height - room_height - 1)
            
            # Check if the room overlaps with any existing room
            if not any(self.rooms_overlap(x, y, room_width, room_height, r) for r in rooms):
                self.create_room(x, y, room_width, room_height)
                rooms.append((x, y, room_width, room_height))
        
        # Connect rooms
        for i in range(len(rooms) - 1):
            self.create_corridor(rooms[i], rooms[i+1])

        return self.map, rooms

    def create_room(self, x, y, w, h):
        for i in range(y, y + h):
            for j in range(x, x + w):
                self.map[i][j] = '.'

    def create_corridor(self, room1, room2):
        x1, y1 = room1[0] + room1[2] // 2, room1[1] + room1[3] // 2
        x2, y2 = room2[0] + room2[2] // 2, room2[1] + room2[3] // 2
        
        if random.random() < 0.5:
            self.create_h_tunnel(x1, x2, y1)
            self.create_v_tunnel(y1, y2, x2)
        else:
            self.create_v_tunnel(y1, y2, x1)
            self.create_h_tunnel(x1, x2, y2)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.map[y][x] = '.'

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.map[y][x] = '.'

    def rooms_overlap(self, x, y, w, h, room):
        return (x < room[0] + room[2] and x + w > room[0] and
                y < room[1] + room[3] and y + h > room[1])

    def generate_level(self, player):
        self.map, self.rooms = self.generate()
        
        # Ensure the bottom row is always a wall
        for x in range(self.width):
            self.map[self.height - 1][x] = '#'
        
        # Place stairs up (entry point)
        entry_room = self.rooms[0]
        stairs_up_x = entry_room[0] + entry_room[2] // 2
        stairs_up_y = entry_room[1] + entry_room[3] // 2
        self.map[stairs_up_y][stairs_up_x] = '<'
        
        # Place stairs down (exit to next level)
        exit_room = self.rooms[-1]
        stairs_x = exit_room[0] + exit_room[2] // 2
        stairs_y = exit_room[1] + exit_room[3] // 2
        self.map[stairs_y][stairs_x] = '>'
        
        # Place player at the up stairs
        player.x, player.y = stairs_up_x, stairs_up_y
        
        return self.map, self.rooms, stairs_up_x, stairs_up_y, stairs_x, stairs_y