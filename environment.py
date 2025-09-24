import random
import math
from config import *

class Building:
    def __init__(self, x):
        self.x = x
        self.width = random.randint(int(WIDTH * 1.5), int(WIDTH * 3))
        self.height = random.randint(int(HEIGHT * 0.6), int(HEIGHT * 0.95))
        self.y = 100 - self.height
        
        # Window configuration
        self.window_w = max(30, self.width // 15)
        self.window_h = max(50, self.height // 20)
        self.spacing_x = self.window_w // 2
        self.spacing_y = self.window_h // 2
        
        self.cols = max(1, self.width // (self.window_w + self.spacing_x))
        self.rows = max(1, self.height // (self.window_h + self.spacing_y))
        
        # Generate random window lighting
        self.windows = []
        for r in range(self.rows):
            row = [random.random() > 0.35 for c in range(self.cols)]
            self.windows.append(row)
    
    def update(self):
        """Update building position"""
        self.x -= BUILDING_SPEED
    
    def is_offscreen(self, camera):
        """Check if building is completely offscreen"""
        return self.x + self.width < camera.x - WIDTH // camera.zoom_factor

class RedSpot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.timer = 0.0
    
    def update(self):
        """Update spot position"""
        self.x -= BUILDING_SPEED
    
    def is_offscreen(self, camera):
        """Check if spot is offscreen"""
        return self.x + self.radius < camera.x - WIDTH // camera.zoom_factor
    
    def check_collision(self, head_x, head_y):
        """Check collision with character head"""
        dist = math.hypot(head_x - self.x, head_y - self.y)
        return dist < HEAD_RADIUS + self.radius

class Environment:
    def __init__(self):
        self.buildings = []
        self.red_spots = []
        self._spawn_initial_buildings()
    
    def _spawn_initial_buildings(self):
        """Spawn initial set of buildings"""
        x_pos = 0
        while x_pos < WIDTH * 2:
            building = Building(x_pos)
            self.buildings.append(building)
            x_pos += building.width + 200
    
    def update(self, camera):
        """Update all environment objects"""
        # Update buildings
        for building in self.buildings:
            building.update()
        
        # Remove offscreen buildings and spawn new ones
        self.buildings = [b for b in self.buildings if not b.is_offscreen(camera)]
        
        if self.buildings:
            last_building = self.buildings[-1]
            if last_building.x + last_building.width < camera.x + WIDTH // camera.zoom_factor:
                new_x = last_building.x + last_building.width + 200
                self.buildings.append(Building(new_x))
        
        # Spawn red spots randomly
        if random.random() < SPOT_SPAWN_CHANCE:
            self._spawn_red_spot()
        
        # Update red spots
        for spot in self.red_spots:
            spot.update()
        
        # Remove offscreen spots
        self.red_spots = [s for s in self.red_spots if not s.is_offscreen(camera)]
    
    def _spawn_red_spot(self):
        """Spawn a new red spot if conditions are met"""
        x = 400 + random.randint(100, 400)
        y = random.randint(-50, 50)
        
        # Check minimum distance from existing spots
        for spot in self.red_spots:
            if abs(spot.x - x) < MIN_SPOT_DISTANCE:
                return
        
        self.red_spots.append(RedSpot(x, y))
    
    def check_spot_collisions(self, head_x, head_y, character):
        """Check collisions between head and red spots"""
        for spot in self.red_spots:
            if spot.check_collision(head_x, head_y):
                spot.timer += 1 / FPS
                if spot.timer >= 1.0:
                    character.add_segment()
                    spot.timer = 0.0
            else:
                spot.timer = 0.0