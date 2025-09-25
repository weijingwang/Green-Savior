# environment.py - Enhanced environment with infinite scaling collectible spots
import random
import math
import os
import pygame
from config import *

class Building:
    """A building in the scrolling environment - positioned on ground"""
    
    def __init__(self, x_position, ground_world_y):
        self.x = x_position
        self.width = random.randint(int(SCREEN_WIDTH * 1.5), int(SCREEN_WIDTH * 3))
        self.height = random.randint(int(SCREEN_HEIGHT * 0.6), int(SCREEN_HEIGHT * 0.95))
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
    """Infinitely scaling collectible spots that grow with camera zoom"""
    
    def __init__(self, x, y, base_altitude_tier=0, zoom_level=1.0):
        self.x = x
        self.y = y  # World Y position
        self.base_altitude_tier = base_altitude_tier  # Base tier (0-4)
        self.zoom_level = zoom_level  # Current zoom when created
        
        # Calculate effective tier based on zoom
        self.effective_tier = self._calculate_effective_tier()
        
        # For backward compatibility with renderer
        self.altitude_tier = self.base_altitude_tier
        
        # Scale properties based on effective tier
        self.base_radius = 12
        self.radius = self._calculate_radius()
        self.growth_multiplier = self._calculate_growth_multiplier()
        self.collection_time = self._calculate_collection_time()
        
        self.collection_timer = 0.0
        self.pulse_timer = 0.0  # For visual pulsing effect
    
    def _calculate_effective_tier(self):
        """Calculate effective tier based on base tier and zoom level"""
        # Smaller zoom = bigger character = higher effective tier for rewards
        # Use inverse relationship: as zoom gets smaller, effective tier increases
        zoom_multiplier = 1.0 / max(0.1, self.zoom_level)  # Prevent division by zero
        return self.base_altitude_tier + math.log2(zoom_multiplier)
    
    def _calculate_radius(self):
        """Calculate spot radius based on effective tier and zoom"""
        # Base size scales inversely with zoom (smaller zoom = bigger character = bigger spots)
        character_scale = 1.0 / max(0.1, self.zoom_level)
        base_size_for_scale = self.base_radius * character_scale
        
        # Tier multiplier for additional size based on altitude tier
        tier_multiplier = 1.0 + (self.base_altitude_tier * 0.4)  # 40% size increase per tier
        
        return int(base_size_for_scale * tier_multiplier)
    
    def _calculate_growth_multiplier(self):
        """Calculate segments provided - scales with character size (inverse zoom)"""
        # Base segments scale with how "big" the character is (smaller zoom = bigger character)
        character_scale = 1.0 / max(0.1, self.zoom_level)
        base_segments = max(1, int(character_scale))
        
        # Tier bonus - higher tiers give exponentially more
        tier_bonus = int(math.pow(1.8, self.base_altitude_tier))
        
        return base_segments * tier_bonus
    
    def _calculate_collection_time(self):
        """Collection time stays consistent regardless of scale"""
        # Time decreases slightly with higher tiers but stays reasonable
        base_time = 1.0
        tier_reduction = min(0.8, self.effective_tier * 0.1)  # Max 80% reduction
        return max(0.2, base_time - tier_reduction)  # Never less than 0.2 seconds
    
    def update_for_zoom(self, new_zoom_level):
        """Update spot properties when zoom changes"""
        self.zoom_level = new_zoom_level
        self.effective_tier = self._calculate_effective_tier()
        self.radius = self._calculate_radius()
        self.growth_multiplier = self._calculate_growth_multiplier()
        self.collection_time = self._calculate_collection_time()
        # Update altitude_tier for renderer compatibility
        self.altitude_tier = int(self.effective_tier)
    
    def get_color(self):
        """Get spot color based on effective tier - FIXED VERSION"""
        # Color intensity increases with effective tier
        tier_clamped = max(0, min(self.effective_tier, 10))  # Clamp between 0 and 10
        
        # Progress through color spectrum as tier increases
        if tier_clamped <= 1:
            # Red to orange-red
            red = int(200 + (55 * tier_clamped))
            green = int(50 + (30 * tier_clamped))
            blue = 50
        elif tier_clamped <= 3:
            # Orange-red to bright orange
            progress = (tier_clamped - 1) / 2
            red = 255
            green = int(80 + (70 * progress))
            blue = 50
        elif tier_clamped <= 5:
            # Orange to yellow-orange
            progress = (tier_clamped - 3) / 2
            red = 255
            green = int(150 + (50 * progress))
            blue = int(50 + (50 * progress))
        elif tier_clamped <= 7:
            # Yellow-orange to bright yellow
            progress = (tier_clamped - 5) / 2
            red = 255
            green = int(200 + (55 * progress))
            blue = int(100 + (100 * progress))
        else:
            # Bright yellow to white-hot
            progress = min(1.0, (tier_clamped - 7) / 3)
            red = 255
            green = 255
            blue = int(200 + (55 * progress))
        
        # Ensure all values are integers and within valid range [0, 255]
        red = max(0, min(255, int(red)))
        green = max(0, min(255, int(green)))
        blue = max(0, min(255, int(blue)))
        
        return (red, green, blue)
    
    def update(self):
        """Move spot left and update pulse animation"""
        self.x -= BUILDING_SPEED
        self.pulse_timer += 0.1
    
    def get_visual_radius(self):
        """Get radius with pulsing effect - more dramatic for higher tiers"""
        pulse_intensity = 0.3 + min(0.4, self.base_altitude_tier * 0.08)  # More pulse for higher tiers
        pulse_factor = 1.0 + pulse_intensity * math.sin(self.pulse_timer)
        return max(1, int(self.radius * pulse_factor))  # Ensure minimum size of 1
    
    def is_offscreen(self, camera_x, screen_width):
        """Check if spot is offscreen"""
        return self.x + self.radius < camera_x - screen_width
    
    def check_collision(self, head_x, head_y):
        """Check if head is colliding with this spot"""
        distance = math.hypot(head_x - self.x, head_y - self.y)
        # Scale HEAD_RADIUS with character size for consistent collision detection
        scaled_head_radius = HEAD_RADIUS / max(0.1, self.zoom_level)
        return distance < scaled_head_radius + self.radius
    
    def get_tier_display(self):
        """Get display string for this spot's tier"""
        return f"T{self.effective_tier:.1f}"


class EnvironmentalObject:
    """Objects that sit on the ground with their bottoms aligned to GROUND_Y"""
    
    def __init__(self, x_position, ground_world_y, object_type, image=None):
        self.x = x_position
        self.ground_world_y = ground_world_y
        self.object_type = object_type
        self.image = image
        
        # Calculate position so bottom sits on ground
        if self.image:
            self.width = self.image.get_width()
            self.height = self.image.get_height()
            # Y position is top of object, with bottom at ground level
            self.y = self.ground_world_y - self.height
        else:
            # Fallback dimensions
            self.width = 50
            self.height = 80
            self.y = self.ground_world_y - self.height
        
        # Add some random properties
        self.scale_factor = random.uniform(0.8, 1.2)
        self.flip = random.choice([False, True])
    
    def update(self):
        """Move object left"""
        self.x -= BUILDING_SPEED
    
    def is_offscreen(self, camera_x, screen_width):
        """Check if object is offscreen"""
        return self.x + self.width < camera_x - screen_width


class Environment:
    """Enhanced environment with infinitely scaling spots"""
    
    def __init__(self):
        self.buildings = []
        self.spots = []
        self.objects = []  # Environmental objects
        # Ground is always at world Y = 0 (constant)
        self.ground_world_y = 0
        
        # Load environmental object images
        self.object_images = self._load_object_images()
        self.object_types = list(self.object_images.keys()) if self.object_images else ['tree', 'rock', 'bush']
        
        # Dynamic altitude tiers based on zoom level
        self.base_altitude_tiers = [
            (0, -50),      # Tier 0: Ground level
            (-100, -200),  # Tier 1: Low altitude
            (-250, -400),  # Tier 2: Medium altitude
            (-450, -600),  # Tier 3: High altitude  
            (-650, -1000)  # Tier 4: Extreme altitude
        ]
    
    def get_altitude_tiers_for_zoom(self, zoom_level):
        """Generate altitude tiers relative to current viewport scale"""
        # Calculate the world height that's visible on screen
        visible_world_height = GROUND_SCREEN_Y / zoom_level  # Height from ground to top of screen in world units
        
        # Create tiers that span the full visible height plus extra above
        tier_height = visible_world_height / 3  # Each tier is 1/3 of visible height
        
        scaled_tiers = []
        
        # Tier 0: Bottom third of screen (lowest rewards)
        tier0_bottom = -visible_world_height * 0.33
        tier0_top = 0  # Ground level
        scaled_tiers.append((tier0_bottom, tier0_top))
        
        # Tier 1: Middle third of screen (normal rewards)
        tier1_bottom = -visible_world_height * 0.66
        tier1_top = -visible_world_height * 0.33
        scaled_tiers.append((tier1_bottom, tier1_top))
        
        # Tier 2: Top third of screen (higher rewards)
        tier2_bottom = -visible_world_height
        tier2_top = -visible_world_height * 0.66
        scaled_tiers.append((tier2_bottom, tier2_top))
        
        # Tier 3: Just above screen (premium rewards)
        tier3_bottom = -visible_world_height * 1.5
        tier3_top = -visible_world_height
        scaled_tiers.append((tier3_bottom, tier3_top))
        
        # Tier 4: High above screen (maximum rewards)
        tier4_bottom = -visible_world_height * 2.5
        tier4_top = -visible_world_height * 1.5
        scaled_tiers.append((tier4_bottom, tier4_top))
        
        # Add additional extreme tiers for very small zoom (large character)
        if zoom_level < 0.5:  # When zoomed way out
            num_extra_tiers = max(3, int(5 / zoom_level) - 5)
            for i in range(num_extra_tiers):
                tier_bottom = -visible_world_height * (3.5 + i * 2)
                tier_top = -visible_world_height * (2.5 + i * 2)
                scaled_tiers.append((tier_bottom, tier_top))
        
        return scaled_tiers
    
    def _load_object_images(self):
        """Load environmental object images from directory"""
        images = {}
        objects_dir = 'assets/images/objects'
        
        if not os.path.exists(objects_dir):
            print(f"Objects directory not found: {objects_dir}")
            return images
        
        try:
            for filename in os.listdir(objects_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    try:
                        image_path = os.path.join(objects_dir, filename)
                        image = pygame.image.load(image_path)
                        images[name] = image
                        print(f"Loaded object: {name}")
                    except Exception as e:
                        print(f"Failed to load {filename}: {e}")
        except Exception as e:
            print(f"Error reading objects directory: {e}")
        
        return images
    
    def _spawn_initial_buildings(self):
        """Create initial set of buildings on ground"""
        self.buildings = []  # Clear existing buildings
        x_pos = 0
        while x_pos < SCREEN_WIDTH * 2:
            # Buildings sit on ground (world Y = 0)
            building = Building(x_pos, self.ground_world_y)
            self.buildings.append(building)
            x_pos += building.width + 200
    
    def spawn_initial_spots(self, camera):
        """Spawn initial spots around the starting area including behind the player"""
        world_viewport_width = SCREEN_WIDTH / camera.zoom
        world_viewport_height = GROUND_SCREEN_Y / camera.zoom
        
        # Spawn spots in a wide area around the starting position
        start_x = camera.x - world_viewport_width * 2  # Start 2 screen widths behind
        end_x = camera.x + world_viewport_width * 3    # End 3 screen widths ahead
        
        # Calculate how many spots to spawn based on area
        area_width = end_x - start_x
        spots_to_spawn = int(area_width / (world_viewport_width * 0.3))  # One spot per 30% of screen width
        
        altitude_tiers = self.get_altitude_tiers_for_zoom(camera.zoom)
        available_tiers = len(altitude_tiers)
        
        for _ in range(spots_to_spawn):
            # Random position across the entire spawn area
            new_x = random.uniform(start_x, end_x)
            
            # Select tier with same weights as normal spawning
            if available_tiers <= 5:
                tier_weights = [0.35, 0.30, 0.20, 0.10, 0.05][:available_tiers]
            else:
                tier_weights = []
                for i in range(available_tiers):
                    if i == 0:
                        tier_weights.append(0.25)
                    elif i <= 2:
                        tier_weights.append(0.25)
                    elif i <= 4:
                        tier_weights.append(0.15)
                    else:
                        tier_weights.append(0.05)
            
            total_weight = sum(tier_weights)
            tier_weights = [w / total_weight for w in tier_weights]
            tier = random.choices(range(available_tiers), weights=tier_weights)[0]
            
            # Generate Y position for this tier
            if tier < len(altitude_tiers):
                min_y, max_y = altitude_tiers[tier]
                min_y_int = int(min_y)
                max_y_int = int(max_y)
                lower_bound = min(min_y_int, max_y_int)
                upper_bound = max(min_y_int, max_y_int)
                new_y = random.randint(lower_bound, upper_bound)
            else:
                fallback_min = int(-world_viewport_height * 2)
                fallback_max = int(-world_viewport_height * 1.5)
                new_y = random.randint(fallback_max, fallback_min)
            
            # Check for minimum distance from other spots
            min_distance = (SCREEN_WIDTH * 0.05) / camera.zoom
            too_close = False
            for spot in self.spots:
                if abs(spot.x - new_x) < min_distance and abs(spot.y - new_y) < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                self.spots.append(CollectibleSpot(new_x, new_y, tier, camera.zoom))
    
    def initialize_starting_content(self, camera):
        """Initialize spots and buildings for game start"""
        if not hasattr(self, '_initialized'):
            self._spawn_initial_buildings()
            self.spawn_initial_spots(camera)
            self._initialized = True
    
    def update(self, camera):
        """Update all environment objects with zoom-aware scaling"""
        # Initialize starting content on first update
        self.initialize_starting_content(camera)
        
        # Update existing spots for current zoom level
        for spot in self.spots:
            spot.update_for_zoom(camera.zoom)
        
        self._update_buildings(camera)
        self._update_spots(camera)
        self._update_objects(camera)
        self._spawn_new_content(camera)
    
    def _update_buildings(self, camera):
        """Update building positions and remove offscreen ones"""
        for building in self.buildings:
            building.update()
        
        screen_width = SCREEN_WIDTH // camera.zoom
        self.buildings = [b for b in self.buildings 
                         if not b.is_offscreen(camera.x, screen_width)]
    
    def _update_spots(self, camera):
        """Update spot positions and remove offscreen ones"""
        for spot in self.spots:
            spot.update()
        
        screen_width = SCREEN_WIDTH // camera.zoom
        self.spots = [s for s in self.spots 
                     if not s.is_offscreen(camera.x, screen_width)]
    
    def _update_objects(self, camera):
        """Update environmental objects"""
        for obj in self.objects:
            obj.update()
        
        screen_width = SCREEN_WIDTH // camera.zoom
        self.objects = [obj for obj in self.objects 
                       if not obj.is_offscreen(camera.x, screen_width)]
    
    def _spawn_new_content(self, camera):
        """Spawn new buildings, spots, and objects as needed"""
        # Spawn new buildings
        if self.buildings:
            last_building = self.buildings[-1]
            screen_width = SCREEN_WIDTH // camera.zoom
            if last_building.x + last_building.width < camera.x + screen_width:
                new_x = last_building.x + last_building.width + 200
                # Buildings always sit on ground (world Y = 0)
                self.buildings.append(Building(new_x, self.ground_world_y))
        
        # Spawn new spots with higher frequency for denser placement
        spot_spawn_frequency = SPOT_SPAWN_CHANCE * 3.0  # 3x more frequent spawning
        if random.random() < spot_spawn_frequency:
            self._try_spawn_scaled_spot(camera)
        
        # Spawn environmental objects occasionally
        if random.random() < OBJECT_SPAWN_CHANCE:
            self._try_spawn_object(camera)
    
    def _try_spawn_scaled_spot(self, camera):
        """Spawn spots scaled appropriately for current zoom level"""
        # Spawn distance should be relative to world scale
        world_viewport_width = SCREEN_WIDTH / camera.zoom
        
        # Multiple spawn attempts for denser placement
        for _ in range(3):  # Try to spawn 3 spots per call
            spawn_distance = world_viewport_width * random.uniform(0.3, 1.2)  # Spawn closer and further
            new_x = camera.x + spawn_distance
            
            # Get altitude tiers for current zoom (these are properly scaled to viewport)
            altitude_tiers = self.get_altitude_tiers_for_zoom(camera.zoom)
            
            # All altitude tiers are always available
            available_tiers = len(altitude_tiers)
            
            # Weight distribution: favor middle tiers for balanced gameplay
            if available_tiers <= 5:
                tier_weights = [0.35, 0.30, 0.20, 0.10, 0.05][:available_tiers]
            else:
                # For many tiers, distribute weights
                tier_weights = []
                for i in range(available_tiers):
                    if i == 0:
                        tier_weights.append(0.25)  # Bottom tier - common
                    elif i <= 2:
                        tier_weights.append(0.25)  # Middle tiers - common
                    elif i <= 4:
                        tier_weights.append(0.15)  # Higher tiers - less common
                    else:
                        tier_weights.append(0.05)  # Extreme tiers - rare
            
            # Normalize weights
            total_weight = sum(tier_weights)
            tier_weights = [w / total_weight for w in tier_weights]
            
            # Select altitude tier
            tier = random.choices(range(available_tiers), weights=tier_weights)[0]
            
            if tier < len(altitude_tiers):
                min_y, max_y = altitude_tiers[tier]
                # Convert to integers and ensure proper order for randint
                min_y_int = int(min_y)
                max_y_int = int(max_y)
                lower_bound = min(min_y_int, max_y_int)
                upper_bound = max(min_y_int, max_y_int)
                new_y = random.randint(lower_bound, upper_bound)
            else:
                # Fallback for edge cases
                visible_height = GROUND_SCREEN_Y / camera.zoom
                fallback_min = int(-visible_height * 2)
                fallback_max = int(-visible_height * 1.5)
                new_y = random.randint(fallback_max, fallback_min)
            
            # Check minimum distance from existing spots (reduced for denser placement)
            min_distance = (SCREEN_WIDTH * 0.05) / camera.zoom  # Reduced from 10% to 5% for denser spacing
            too_close = False
            for spot in self.spots:
                if abs(spot.x - new_x) < min_distance and abs(spot.y - new_y) < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                self.spots.append(CollectibleSpot(new_x, new_y, tier, camera.zoom))
    
    def _try_spawn_object(self, camera):
        """Spawn environmental objects on the ground"""
        new_x = camera.x + random.randint(300, 800)
        
        # Check minimum distance from other objects
        for obj in self.objects:
            if abs(obj.x - new_x) < 100:
                return
        
        # Select random object type
        if self.object_types:
            object_type = random.choice(self.object_types)
            image = self.object_images.get(object_type)
        else:
            object_type = 'fallback'
            image = None
        
        self.objects.append(EnvironmentalObject(new_x, self.ground_world_y, object_type, image))
    
    def check_spot_collections(self, head_x, head_y, character):
        """Enhanced spot collection with infinite scaling rewards"""
        spots_to_remove = []
        
        for spot in self.spots:
            if spot.check_collision(head_x, head_y):
                spot.collection_timer += 1 / FPS
                if spot.collection_timer >= spot.collection_time:
                    # Add multiple segments based on spot's scaling
                    segments_to_add = spot.growth_multiplier
                    for _ in range(segments_to_add):
                        character.add_neck_segment()
                    spots_to_remove.append(spot)
                    
                    # Enhanced feedback for high-tier spots
                    print(f"Collected {spot.get_tier_display()} spot! +{segments_to_add} segments (zoom: {spot.zoom_level:.1f})")
            else:
                spot.collection_timer = 0.0
        
        # Remove collected spots
        for spot in spots_to_remove:
            self.spots.remove(spot)