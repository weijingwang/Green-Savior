import pygame, random, os
from constants import *
from utils import world_to_screen_x, incremental_add


class ObjectManager:
    def __init__(self):
        self.objects = pygame.sprite.Group()
        self.last_spawned_x = 0.0
        self.base_spawn_distance = 0.3  # base spawn distance for small objects
        
        # Cache for scaled images - key: (obj_type, scale_factor), value: scaled_surface
        self.scaled_image_cache = {}
        # Cache for original images - key: obj_type, value: original_surface
        self.original_image_cache = {}


        # Define object layers for a proper city
        self.ground_objects = [
            ('cockroach', COCKROACH_HEIGHT, 0.15),
            ('mouse', MOUSE_HEIGHT, 0.10),
            ('person', PERSON_HEIGHT, 0.25),
            ('car1', CAR_HEIGHT, 0.50),  # cars are very common in cities
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


    def get_scaled_spawn_distance(self, current_height):
        """Scale spawn distance based on current height - bigger objects need more space"""
        # Scale spawn distance proportionally to height, with minimum and maximum bounds
        scale_factor = max(1.0, current_height / 2.0)  # Start scaling at 2m height
        scaled_distance = self.base_spawn_distance * scale_factor
        
        # Set reasonable bounds
        min_distance = 0.3  # 30cm minimum
        max_distance = 50.0  # 50m maximum
        
        return max(min_distance, min(max_distance, scaled_distance))

    def get_or_load_original_image(self, obj_type):
        """Get original image from cache or load it"""
        if obj_type in self.original_image_cache:
            return self.original_image_cache[obj_type]
            
        try:
            # Handle building images vs regular object images
            if obj_type.startswith('buildings/'):
                image_path = os.path.join("assets/images", obj_type)
            elif obj_type == 'gun_building':
                image_path = os.path.join("assets/images/objects", "gun_building.png")
            elif obj_type == 'bone_tower':
                image_path = os.path.join("assets/images/objects", "bone_tower.png")
            elif obj_type == 'skyscraper':
                image_path = os.path.join("assets/images/objects", "skyscraper.png")
            else:
                image_path = os.path.join("assets/images/objects", f"{obj_type}.png")
                
            image = pygame.image.load(image_path).convert_alpha()
            self.original_image_cache[obj_type] = image
            return image
            
        except pygame.error as e:
            print(f"Could not load image {image_path}: {e}")
            # Create a fallback colored rectangle - use estimated height for sizing
            fallback_height = 100  # Default fallback height in pixels
            if 'cockroach' in obj_type or 'mouse' in obj_type:
                fallback_height = 20
            elif 'person' in obj_type or 'car' in obj_type:
                fallback_height = 50
            elif 'building' in obj_type:
                fallback_height = 200
                
            image = pygame.Surface((50, fallback_height))
            # Color code by type
            if 'cockroach' in obj_type or 'mouse' in obj_type:
                image.fill((255, 255, 0))  # Yellow for small creatures
            elif 'person' in obj_type or 'car' in obj_type:
                image.fill((0, 255, 0))    # Green for people/cars
            else:
                image.fill((128, 128, 128))  # Gray for buildings
                
            self.original_image_cache[obj_type] = image
            return image

    def get_or_create_scaled_image(self, obj_type, height_meters, pixels_per_meter):
        """Get scaled image from cache or create it"""
        # Round scale factor to reduce cache size and improve hit rate
        target_height_pixels = height_meters * pixels_per_meter
        scale_factor = round(target_height_pixels / 10) * 10  # Round to nearest 10 pixels
        
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
        min_height = current_height / 10.0
        max_height = current_height * 2.0
        
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

    def get_visible_range(self, world_x, pixels_per_meter):
        screen_meters = SCREEN_WIDTH / pixels_per_meter
        buffer = screen_meters * 1.5  # larger buffer for smoother spawning
        return world_x - buffer, world_x + screen_meters + buffer

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
        else:  # Very tall (100m+), see super buildings
            return self.super_buildings

    def spawn_city_block(self, world_pos, pixels_per_meter, current_height):
        """Spawn a dense city block with multiple objects"""
        spawned_objects = []
        
        # Get appropriate buildings for current height and filter by size
        building_list = self.get_appropriate_buildings(current_height)
        filtered_buildings = self.filter_objects_by_size(building_list, current_height)
        
        # Filter ground objects by size too
        filtered_ground_objects = self.filter_objects_by_size(self.ground_objects, current_height)
        
        # Reduce density for larger objects - fewer buildings when dealing with big objects
        building_density_factor = max(0.3, 2.0 / current_height)  # Less dense for bigger objects
        ground_density_factor = max(0.5, 5.0 / current_height)    # Less dense for bigger objects
        
        # Only spawn buildings if we have valid filtered buildings
        if filtered_buildings:
            base_buildings = 2
            num_buildings = max(1, int(base_buildings * building_density_factor))
            for i in range(num_buildings):
                obj_type, height = self.select_object_from_list(filtered_buildings)
                if obj_type:  # Make sure we got a valid object
                    building_pos = world_pos + random.uniform(-1, 2)
                    spawned_objects.append((obj_type, height, building_pos))
        
        # Only spawn ground objects if we have valid filtered ground objects
        if filtered_ground_objects:
            base_ground_objects = 5
            num_ground_objects = max(1, int(base_ground_objects * ground_density_factor))
            for i in range(num_ground_objects):
                obj_type, height = self.select_object_from_list(filtered_ground_objects)
                if obj_type:  # Make sure we got a valid object
                    obj_pos = world_pos + random.uniform(-1.5, 2.5)
                    spawned_objects.append((obj_type, height, obj_pos))
        
        # Actually create all the objects
        for obj_type, height, pos in spawned_objects:
            self.create_object(obj_type, height, pos, pixels_per_meter)

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
        left_visible, right_visible = self.get_visible_range(world_x, pixels_per_meter)

        # Use scaled spawn distance
        spawn_distance = self.get_scaled_spawn_distance(current_height)

        # Continuous spawning system - spawn ahead of the player
        spawn_ahead_distance = right_visible
        
        # Keep spawning until we've filled the visible area plus buffer
        while self.last_spawned_x < spawn_ahead_distance:
            self.spawn_city_block(self.last_spawned_x, pixels_per_meter, current_height)
            self.last_spawned_x += spawn_distance
        
        # Also spawn behind if we haven't yet (for when player might move backwards)
        spawn_behind_distance = left_visible
        temp_spawn_pos = world_x - 10  # Start spawning from 10 meters behind current position
        
        # Fill in any gaps behind the player
        while temp_spawn_pos > spawn_behind_distance:
            # Check if we already have objects near this position
            has_objects_nearby = any(
                abs(getattr(obj, "world_pos", float('inf')) - temp_spawn_pos) < spawn_distance
                for obj in self.objects
            )
            
            if not has_objects_nearby:
                self.spawn_city_block(temp_spawn_pos, pixels_per_meter, current_height)
            
            temp_spawn_pos -= spawn_distance

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

        # Cleanup distant objects (keep more objects loaded for a fuller world)
        self.cleanup_distant(world_x, pixels_per_meter)

    def cleanup_distant(self, world_x, pixels_per_meter):
        cleanup_distance = (SCREEN_WIDTH / pixels_per_meter) * 4  # Keep objects longer
        for obj in list(self.objects):
            world_pos = getattr(obj, "world_pos", None)
            if world_pos is None:
                continue
            if abs(world_pos - world_x) > cleanup_distance:
                print(f"Killing object {getattr(obj, 'obj_type', '?')} at {world_pos:.2f} (too far)")
                obj.kill()

    def draw_all(self, screen, world_x, pixels_per_meter):
        """Draw all visible objects, moving them according to world_x."""
        drawn_count = 0
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

            # Simple culling: only draw if it overlaps the screen horizontally
            if -obj.rect.width <= screen_x <= SCREEN_WIDTH:
                pygame.draw.rect(screen, (255, 0, 255), obj.rect, 1)  # thinner debug outline
                screen.blit(obj.image_scaled, obj.rect)
                drawn_count += 1
        
        # Debug info
        current_spawn_distance = self.get_scaled_spawn_distance(pixels_per_meter / 100)  # rough estimate
        print(f"Total objects: {len(self.objects)}, Drawn: {drawn_count}, Last spawned at: {self.last_spawned_x:.1f}, Spawn distance: {current_spawn_distance:.1f}m, Cache size: {len(self.scaled_image_cache)}")


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
            pygame.draw.rect(screen, (255, 0, 255), self.rect, 2)  # 2 = line thickness
            screen.blit(self.image_scaled, self.rect)