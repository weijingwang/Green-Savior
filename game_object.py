import pygame, random, os
from constants import *

# print(1/player.pixels_per_meter * world_x + SCREEN_CENTER_X) # This gets the screen center


class ObjectManager:
    def __init__(self):
        self.objects = pygame.sprite.Group()
        self.last_spawned_x = 0.0        
        # Cache for scaled images - key: (obj_type, scale_factor), value: scaled_surface
        self.scaled_image_cache = {}
        # Cache for original images - key: obj_type, value: original_surface
        self.original_image_cache = {}

        # Define object layers for a proper city
        self.ground_objects = [
            ('cockroach', COCKROACH_HEIGHT, 0.15),
            ('mouse', MOUSE_HEIGHT, 0.10),
            ('person', PERSON_HEIGHT, 0.034),
            ('person2', PERSON_HEIGHT*0.75, 0.034),
            ('human3', PERSON_HEIGHT*0.5, 0.034),
            ('human2', PERSON_HEIGHT*0.5, 0.034),
            ('human1', PERSON_HEIGHT*0.25, 0.034),
            ('bear', 0.6, 0.1),
            ('car1', CAR_HEIGHT, 0.16),  # cars are very common in cities
            ('car2', CAR_HEIGHT, 0.16),  # cars are very common in cities
            ('car3', CAR_HEIGHT*0.8, 0.16),  # cars are very common in cities

        ]

        # Common short buildings (2–4 stories)
        self.short_buildings = [
            ('buildings/1.png', BUILDING1_HEIGHT, 1.0/7),
            ('buildings/2.png', BUILDING2_HEIGHT, 1.0/7),
            ('buildings/3.png', BUILDING3_HEIGHT, 1.0/7),
            ('buildings/4.png', BUILDING4_HEIGHT, 1.0/7),
            ('buildings/5.png', BUILDING5_HEIGHT, 1.0/7),
            ('buildings/6.png', BUILDING6_HEIGHT, 1.0/7),
            ('buildings/7.png', BUILDING7_HEIGHT, 1.0/7),
        ]

        # Medium towers (6–12 stories)
        self.medium_buildings = [
            ('buildings/8.png', BUILDING8_HEIGHT, 1.0/7),
            ('buildings/9.png', BUILDING9_HEIGHT, 1.0/7),
            ('buildings/10.png', BUILDING10_HEIGHT, 1.0/7),
            ('buildings/11.png', BUILDING11_HEIGHT, 1.0/7),
            ('buildings/12.png', BUILDING12_HEIGHT, 1.0/7),
            ('buildings/13.png', BUILDING13_HEIGHT, 1.0/7),
            ('buildings/14.png', BUILDING14_HEIGHT, 1.0/7),
        ]

        # Skyscrapers (20+ stories)
        self.tall_buildings = [
            ('buildings/15.png', BUILDING15_HEIGHT, 0.5),
            ('buildings/16.png', BUILDING16_HEIGHT, 0.5),
        ]


    def get_scaled_spawn_distance(self, obj_type, obj_height, pixels_per_meter):
        """Scale spawn distance based on object height and type - buildings are more dense"""
        # Different spacing for different object types
        if obj_type.startswith('buildings/'):
            # Buildings in cities are very close together
            base_distance = obj_height * 0.2  # Much smaller base distance for buildings
            padding = obj_height * 0.1  # Minimal padding between buildings
            min_distance = 0.1  # 10cm minimum for buildings (very tight)
            max_distance = 5.0   # 5m maximum for buildings
        else:
            # Ground objects (people, cars, etc.) need more space to move around
            base_distance = obj_height * 0.4  # Moderate spacing for ground objects
            padding = obj_height * 0.2  # Some padding for movement
            min_distance = 0.3  # 30cm minimum spacing
            max_distance = 8.0  # 8m maximum spacing
        
        distance = base_distance + padding
        return max(min_distance, min(distance, max_distance))

    def get_or_load_original_image(self, obj_type):
        """Get original image from cache or load it"""
        if obj_type in self.original_image_cache:
            return self.original_image_cache[obj_type]
            
        # Handle building images vs regular object images
        if obj_type.startswith('buildings/'):
            image_path = os.path.join("assets/images", obj_type)
        else:
            image_path = os.path.join("assets/images/objects", f"{obj_type}.png")
            
        image = pygame.image.load(image_path).convert_alpha()
        self.original_image_cache[obj_type] = image
        return image
            

    def get_or_create_scaled_image(self, obj_type, height_meters, pixels_per_meter):
        """Get scaled image from cache or create it"""
        # Round scale factor to reduce cache size and improve hit rate
        target_height_pixels = height_meters * pixels_per_meter
        scale_factor = target_height_pixels
        
        cache_key = (obj_type, scale_factor)
        
        if cache_key in self.scaled_image_cache:
            return self.scaled_image_cache[cache_key]
        
        # Create new scaled image
        original = self.get_or_load_original_image(obj_type)
        if original is None:
            return None
            
        orig_w, orig_h = original.get_size()
        if orig_h == 0:
            return None
            
        scale_ratio = scale_factor / orig_h
        new_w = max(1, int(orig_w * scale_ratio))
        new_h = max(1, int(scale_factor))
        
        scaled_image = pygame.transform.scale(original, (new_w, new_h))
        
        # Cache the scaled image
        self.scaled_image_cache[cache_key] = scaled_image
        
        # Limit cache size to prevent memory issues
        if len(self.scaled_image_cache) > 200:
            # Remove oldest entries (simple cleanup)
            keys_to_remove = list(self.scaled_image_cache.keys())[:50]
            for key in keys_to_remove:
                del self.scaled_image_cache[key]
        
        return scaled_image

    def should_spawn_object(self, object_height, current_height):
        """
        Determine if an object should be spawned based on size relative to current height.
        Only spawn if object height is between 1/10th and 2x the current height.
        """
        min_height = current_height / 20.0
        max_height = current_height * 3.0
        
        return min_height <= object_height <= max_height

    def filter_objects_by_size(self, object_list, current_height):
        """Filter a list of objects to only include those within the size range"""
        filtered_objects = []
        total_probability = 0
        
        for obj_type, height, probability in object_list:
            if self.should_spawn_object(height, current_height):
                filtered_objects.append((obj_type, height, probability))
                total_probability += probability
        
        # Normalize probabilities if we have valid objects
        if filtered_objects and total_probability > 0:
            normalized_objects = []
            for obj_type, height, probability in filtered_objects:
                normalized_prob = probability / total_probability
                normalized_objects.append((obj_type, height, normalized_prob))
            return normalized_objects
        
        return []

    def get_spawn_bounds(self, world_x, pixels_per_meter):
        """Get the world coordinates where objects should spawn and be killed"""
        # Convert screen coordinates to world coordinates
        # Objects spawn at right edge (SCREEN_WIDTH) and are killed at left edge (0)
        
        # Right edge spawn position in world coordinates
        spawn_x_world = world_x + (SCREEN_WIDTH - SCREEN_CENTER_X) / pixels_per_meter
        
        # Left edge kill position in world coordinates  
        kill_x_world = world_x + (0 - SCREEN_CENTER_X) / pixels_per_meter
        
        # Add some buffer for smooth spawning/despawning
        spawn_buffer = 50 / pixels_per_meter  # 50 pixels buffer
        
        return kill_x_world - spawn_buffer, spawn_x_world + spawn_buffer

    def select_object_from_list(self, object_list):
        """Select an object from a weighted list"""
        if not object_list:
            return None, None
            
        rand = random.random()
        cumulative = 0
        
        for obj_type, height, probability in object_list:
            cumulative += probability
            if rand <= cumulative:
                return obj_type, height
        
        # Fallback to first item if probabilities don't add up perfectly
        return object_list[0][0], object_list[0][1]

    def get_appropriate_buildings(self, current_height):
        """Get the right building layer based on player height"""
        if current_height < 5:  # When you're small (under 5m), see short buildings
            return self.short_buildings
        elif current_height < 20:  # Medium height (5-20m), see medium buildings
            return self.medium_buildings  
        elif current_height < 100:  # Tall (20-100m), see skyscrapers
            return self.tall_buildings
        else:  # Very tall (100m+), see super buildings (you might need to add this)
            return self.tall_buildings  # Fallback to tall buildings

    def spawn_objects_ahead(self, world_x, pixels_per_meter, current_height):
        """Spawn objects ahead of the player with proper spacing - dense buildings like a city"""
        kill_x_world, spawn_x_world = self.get_spawn_bounds(world_x, pixels_per_meter)
        
        # Get appropriate objects for current height
        building_list = self.get_appropriate_buildings(current_height)
        filtered_buildings = self.filter_objects_by_size(building_list, current_height)
        filtered_ground_objects = self.filter_objects_by_size(self.ground_objects, current_height)
        
        # Start spawning from last spawned position or current spawn bound
        spawn_start = max(self.last_spawned_x, world_x)
        current_spawn_x = spawn_start
        
        # Spawn objects until we reach the spawn boundary
        while current_spawn_x < spawn_x_world:
            # Prioritize buildings for city density - 70% buildings, 30% ground objects
            if filtered_buildings and (not filtered_ground_objects or random.random() < 0.7):
                # Spawn a building
                obj_type, obj_height = self.select_object_from_list(filtered_buildings)
            elif filtered_ground_objects:
                # Spawn a ground object
                obj_type, obj_height = self.select_object_from_list(filtered_ground_objects)
            else:
                # No valid objects, skip ahead
                current_spawn_x += 2.0
                self.last_spawned_x = current_spawn_x
                continue
            
            if obj_type and obj_height:
                # Create the object
                self.create_object(obj_type, obj_height, current_spawn_x, pixels_per_meter)
                
                # Calculate spacing based on this object's type and size
                spawn_distance = self.get_scaled_spawn_distance(obj_type, obj_height, pixels_per_meter)
                
                # Move to next spawn position
                current_spawn_x += spawn_distance
                self.last_spawned_x = current_spawn_x
            else:
                # Fallback spacing if object selection fails
                current_spawn_x += 1.0
                self.last_spawned_x = current_spawn_x

    def create_object(self, obj_type, height, world_pos, pixels_per_meter):
        """Create a single object"""
        try:
            print(f"Creating {obj_type} at world position {world_pos:.2f}")

            obj = GameObject(
                obj_type=obj_type,
                height_meters=height,
                pixels_per_meter=pixels_per_meter,
                ground_y=GROUND_Y,
                object_manager=self  # Pass reference to self for image caching
            )

            # If GameObject failed to initialize properly, don't add it
            if getattr(obj, "to_kill", False):
                print(f"Not adding {obj_type} at {world_pos:.2f} (marked to_kill immediately)")
                return

            if getattr(obj, "rect", None) is None or getattr(obj, "image_scaled", None) is None:
                print(f"Not adding {obj_type} at {world_pos:.2f} (missing rect/image_scaled)")
                return

            # attach world pos and type, then add to group
            obj.world_pos = world_pos
            obj.obj_type = obj_type
            self.objects.add(obj)

        except Exception as e:
            print(f"Error creating object {obj_type}: {e}")

    def update_spawning(self, world_x, pixels_per_meter, current_height):
        """Main spawning update function"""
        # Spawn objects ahead of player
        self.spawn_objects_ahead(world_x, pixels_per_meter, current_height)

        # Update scales for all objects and remove those that are now out of size range
        for obj in list(self.objects):
            obj_height = getattr(obj, "height_meters", 0)
            
            # Check if existing object is still within size range
            if not self.should_spawn_object(obj_height, current_height):
                print(f"Removing {getattr(obj, 'obj_type', '?')} (height {obj_height:.2f}m out of range for current height {current_height:.2f}m)")
                obj.kill()
                continue
                
            obj.update_scale(pixels_per_meter, GROUND_Y)
            
            # Handle fading objects
            obj.update()

        # Cleanup objects that have moved off screen
        self.cleanup_offscreen_objects(world_x, pixels_per_meter)

    def cleanup_offscreen_objects(self, world_x, pixels_per_meter):
        """Remove objects when their right edge has moved past the left edge of the screen"""
        kill_x_world, _ = self.get_spawn_bounds(world_x, pixels_per_meter)
        
        for obj in list(self.objects):
            world_pos = getattr(obj, "world_pos", None)
            if world_pos is None:
                continue
            
            # Calculate the object's width in world coordinates
            obj_width_pixels = getattr(obj.rect, "width", 0) if hasattr(obj, "rect") and obj.rect else 0
            obj_width_world = obj_width_pixels / pixels_per_meter
            
            # Calculate the right edge of the object in world coordinates
            obj_right_edge_world = world_pos + obj_width_world
            
            # Kill objects only when their right edge has moved past the left screen edge
            if obj_right_edge_world < kill_x_world:
                print(f"Killing object {getattr(obj, 'obj_type', '?')} at {world_pos:.2f} (right edge {obj_right_edge_world:.2f} past left edge {kill_x_world:.2f})")
                obj.kill()

    def draw_all(self, screen, world_x, pixels_per_meter):
        """Draw all visible objects, moving them according to world_x. Smaller objects drawn in front."""
        drawn_count = 0
        visible_objects = []
        
        # First pass: collect all visible objects and calculate screen positions
        for obj in list(self.objects):
            # skip incomplete objects
            if getattr(obj, "rect", None) is None or getattr(obj, "image_scaled", None) is None:
                obj.kill()
                continue

            world_pos = getattr(obj, "world_pos", None)
            if world_pos is None:
                continue

            # Convert world position to screen X relative to the player (center)
            screen_x = int(SCREEN_CENTER_X + (world_pos - world_x) * pixels_per_meter)

            # Set the sprite rect x so subsequent code sees the correct position
            obj.rect.x = screen_x

            # Simple culling: only collect if it overlaps the screen horizontally
            if -obj.rect.width <= screen_x <= SCREEN_WIDTH:
                visible_objects.append((obj, screen_x))
        
        # Sort objects by height (largest to smallest) so smaller objects draw on top
        visible_objects.sort(key=lambda item: getattr(item[0], "height_meters", 0), reverse=True)
        
        # Second pass: draw objects in sorted order (tallest first, shortest last = on top)
        for obj, screen_x in visible_objects:
            # pygame.draw.rect(screen, (255, 0, 255), obj.rect, 1)  # thinner debug outline
            screen.blit(obj.image_scaled, obj.rect)
            drawn_count += 1
        
        # Debug info
        kill_x, spawn_x = self.get_spawn_bounds(world_x, pixels_per_meter)
        print(f"Total objects: {len(self.objects)}, Drawn: {drawn_count}, Last spawned at: {self.last_spawned_x:.1f}, Kill bound: {kill_x:.1f}, Spawn bound: {spawn_x:.1f}, Cache size: {len(self.scaled_image_cache)}")


class GameObject(pygame.sprite.Sprite):
    def __init__(self, obj_type, height_meters, pixels_per_meter, ground_y, object_manager):
        """
        GameObject class as a pygame Sprite with shared image caching.
        """
        super().__init__()
        
        self.obj_type = obj_type
        self.height_meters = height_meters
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        self.object_manager = object_manager  # Reference to manager for image caching
        
        self.image_scaled = None
        self.rect = None
        self.alpha = 255  # For fading
        self.to_kill = False  # Flag to remove sprite
        
        self.update_scale(self.pixels_per_meter, self.ground_y)

    def update_scale(self, pixels_per_meter, ground_y):
        """Scale image based on height in meters using shared cache."""
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        current_height_pixels = self.height_meters * pixels_per_meter
        
        # If scaled height is too small, start fading but don't kill immediately
        if current_height_pixels < HEIGHT_TO_REMOVE_OBJECT:
            if not self.to_kill:  # Only start fading once
                self.to_kill = True
            # Continue to scale the image even while fading
        
        # Get scaled image from cache
        if current_height_pixels > 0:
            self.image_scaled = self.object_manager.get_or_create_scaled_image(
                self.obj_type, 
                self.height_meters, 
                pixels_per_meter
            )
            
            if self.image_scaled:
                # Apply alpha for fading
                if self.alpha < 255:
                    temp_surface = self.image_scaled.copy()
                    temp_surface.set_alpha(self.alpha)
                    self.image_scaled = temp_surface
                
                self.rect = self.image_scaled.get_rect()
                self.rect.bottom = ground_y

    def fade_out(self, fade_speed=5):
        """Gradually fade out the sprite."""
        if self.alpha > 0:
            self.alpha -= fade_speed
            self.alpha = max(self.alpha, 0)
            # Image alpha will be applied in next update_scale call
        else:
            self.kill()  # Remove from all sprite groups

    def update(self):
        """Call every frame to update the sprite."""
        if self.to_kill:
            self.fade_out()

    def draw(self, screen, x_position):
        """Draw the sprite at a given x-position."""
        if self.rect and self.image_scaled:
            self.rect.x = x_position
            # pygame.draw.rect(screen, (255, 0, 255), self.rect, 2)  # 2 = line thickness
            screen.blit(self.image_scaled, self.rect)