# environment.py - Fixed environment system with objects properly on ground
import random
import math
from config import *

class Building:
    """A building in the scrolling environment - positioned on ground"""
    
    def __init__(self, x_position, ground_world_y):
        self.x = x_position
        self.width = random.randint(int(WIDTH * 1.5), int(WIDTH * 3))
        self.height = random.randint(int(HEIGHT * 0.6), int(HEIGHT * 0.95))
        # Building bottom sits exactly on ground level (world Y = 0)
        self.y = ground_world_y - self.height  # Top of building is negative Y
        
        # Generate window pattern
        self.windows = self._generate_windows()
    
    def _generate_windows(self):
        """Generate random window lighting pattern"""
        window_w = max(30, self.width // 15)
        window_h = max(50, self.height // 20)
        cols = max(1, self.width // (window_w + window_w // 2))
        rows = max(1, self.height // (window_h + window_h // 2))
        
        windows = []
        for r in range(rows):
            row = [random.random() > 0.35 for c in range(cols)]
            windows.append(row)
        
        return {
            'pattern': windows,
            'window_w': window_w,
            'window_h': window_h,
            'cols': cols,
            'rows': rows
        }
    
    def update(self):
        """Move building left"""
        self.x -= BUILDING_SPEED
    
    def is_offscreen(self, camera_x, screen_width):
        """Check if building is completely offscreen"""
        return self.x + self.width < camera_x - screen_width


class CollectibleSpot:
    """Red collectible spots that make the neck grow - positioned on or above ground"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y  # World Y position
        self.radius = 12
        self.collection_timer = 0.0
    
    def update(self):
        """Move spot left"""
        self.x -= BUILDING_SPEED
    
    def is_offscreen(self, camera_x, screen_width):
        """Check if spot is offscreen"""
        return self.x + self.radius < camera_x - screen_width
    
    def check_collision(self, head_x, head_y):
        """Check if head is colliding with this spot"""
        distance = math.hypot(head_x - self.x, head_y - self.y)
        return distance < HEAD_RADIUS + self.radius


class Environment:
    """Manages buildings and collectible spots"""
    
    def __init__(self):
        self.buildings = []
        self.spots = []
        # Ground is always at world Y = 0 (constant)
        self.ground_world_y = 0
    
    def _spawn_initial_buildings(self):
        """Create initial set of buildings on ground"""
        self.buildings = []  # Clear existing buildings
        x_pos = 0
        while x_pos < WIDTH * 2:
            # Buildings sit on ground (world Y = 0)
            building = Building(x_pos, self.ground_world_y)
            self.buildings.append(building)
            x_pos += building.width + 200
    
    def update(self, camera):
        """Update all environment objects"""
        # Spawn initial buildings if needed
        if not self.buildings:
            self._spawn_initial_buildings()
        
        self._update_buildings(camera)
        self._update_spots(camera)
        self._spawn_new_content(camera)
    
    def _update_buildings(self, camera):
        """Update building positions and remove offscreen ones"""
        for building in self.buildings:
            building.update()
        
        screen_width = WIDTH // camera.zoom
        self.buildings = [b for b in self.buildings 
                         if not b.is_offscreen(camera.x, screen_width)]
    
    def _update_spots(self, camera):
        """Update spot positions and remove offscreen ones"""
        for spot in self.spots:
            spot.update()
        
        screen_width = WIDTH // camera.zoom
        self.spots = [s for s in self.spots 
                     if not s.is_offscreen(camera.x, screen_width)]
    
    def _spawn_new_content(self, camera):
        """Spawn new buildings and spots as needed"""
        # Spawn new buildings
        if self.buildings:
            last_building = self.buildings[-1]
            screen_width = WIDTH // camera.zoom
            if last_building.x + last_building.width < camera.x + screen_width:
                new_x = last_building.x + last_building.width + 200
                # Buildings always sit on ground (world Y = 0)
                self.buildings.append(Building(new_x, self.ground_world_y))
        
        # Spawn new spots randomly
        if random.random() < SPOT_SPAWN_CHANCE:
            self._try_spawn_spot(camera)
    
    def _try_spawn_spot(self, camera):
        """Try to spawn a new spot above ground level"""
        new_x = camera.x + 400 + random.randint(100, 400)
        
        # Spawn spots above ground level (ground is at world Y = 0)
        # Some spots on ground, some floating above for neck to reach
        if random.random() < 0.3:
            # 30% chance: spot on ground level
            new_y = self.ground_world_y - 10  # Slightly above ground surface
        else:
            # 70% chance: spot floating above ground
            new_y = self.ground_world_y - random.randint(50, 300)  # Negative Y = above ground
        
        # Check minimum distance from existing spots
        for spot in self.spots:
            if abs(spot.x - new_x) < MIN_SPOT_DISTANCE:
                return
        
        self.spots.append(CollectibleSpot(new_x, new_y))
    
    def check_spot_collections(self, head_x, head_y, character):
        """Handle spot collection logic"""
        for spot in self.spots:
            if spot.check_collision(head_x, head_y):
                spot.collection_timer += 1 / FPS
                if spot.collection_timer >= 1.0:  # 1 second collection time
                    character.add_neck_segment()
                    spot.collection_timer = 0.0
            else:
                spot.collection_timer = 0.0