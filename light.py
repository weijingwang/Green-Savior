import pygame
import random
import math
from constants import *

class LightManager:
    def __init__(self):
        self.lights = pygame.sprite.Group()
        self.last_spawned_x = 0.0
        
        # Define different types of lights with their properties
        # (min_height, max_height, base_size, color, spawn_probability)
        self.light_types = [
            # Individual lights - increased probabilities
            (0.1, 2.0, 8, (255, 255, 100), 0.4),      # Small yellow lights
            (1.0, 10.0, 12, (100, 255, 255), 0.3),    # Medium cyan lights  
            (5.0, 50.0, 16, (255, 150, 255), 0.25),   # Large purple lights
            (20.0, 200.0, 20, (255, 100, 100), 0.2),  # Very large red lights
            (100.0, 1000.0, 24, (100, 255, 100), 0.15), # Huge green lights
        ]
        
        # Cluster configurations (min_lights, max_lights, spread_distance)
        self.cluster_configs = [
            (4, 8, 1.5),   # Small tight clusters
            (6, 12, 2.5),  # Medium clusters
            (8, 18, 3.5),  # Large clusters
            (12, 25, 4.5), # Very large clusters
        ]

    def should_spawn_light(self, light_height, current_player_height):
        """
        Determine if a light should be spawned based on player height.
        More lenient than objects - spawn lights within a wider range.
        """
        min_height = current_player_height / 50.0  # Much smaller minimum
        max_height = current_player_height * 10.0  # Much larger maximum
        
        return min_height <= light_height <= max_height

    def get_light_size_for_height(self, height_meters, base_size, pixels_per_meter):
        """Calculate light size based on its height in meters"""
        # Size scales with height, but also with zoom level
        height_scale = math.log10(max(0.1, height_meters)) + 1  # Order of magnitude scaling
        zoom_scale = pixels_per_meter / 100.0  # Scale with zoom
        
        final_size = int(base_size * height_scale * zoom_scale)
        return max(4, min(final_size, 100))  # Clamp between 4 and 100 pixels

    def get_spawn_height_range(self, current_player_height, screen_height):
        """Get the Y range where lights can spawn based on player height"""
        # Lights can spawn from ground level to several times the player's height
        min_y_world = 0  # Ground level
        max_y_world = current_player_height * 3.0  # Up to 3x player height
        
        return min_y_world, max_y_world

    def world_y_to_screen_y(self, world_y, pixels_per_meter, ground_y):
        """Convert world Y coordinate to screen Y coordinate"""
        return int(ground_y - (world_y * pixels_per_meter))

    def create_light_cluster(self, center_x, center_y_world, light_type_data, pixels_per_meter, ground_y):
        """Create a cluster of lights around a center position"""
        min_height, max_height, base_size, color, _ = light_type_data
        cluster_config = random.choice(self.cluster_configs)
        min_lights, max_lights, spread_distance = cluster_config
        
        num_lights = random.randint(min_lights, max_lights)
        
        for _ in range(num_lights):
            # Random position within cluster spread
            offset_x = random.uniform(-spread_distance, spread_distance)
            offset_y = random.uniform(-spread_distance/2, spread_distance/2)
            
            light_x = center_x + offset_x
            light_y_world = max(0, center_y_world + offset_y)  # Don't go below ground
            
            # Random height within the type's range
            light_height = random.uniform(min_height, max_height)
            
            self.create_single_light(light_x, light_y_world, light_height, base_size, 
                                   color, pixels_per_meter, ground_y)

    def create_single_light(self, world_x, world_y, height_meters, base_size, color, pixels_per_meter, ground_y):
        """Create a single light"""
        try:
            light = Light(
                world_x=world_x,
                world_y=world_y,
                height_meters=height_meters,
                base_size=base_size,
                color=color,
                pixels_per_meter=pixels_per_meter,
                ground_y=ground_y
            )
            
            if light.radius > 0:  # Only add if it has a valid size
                self.lights.add(light)
                
        except Exception as e:
            print(f"Error creating light: {e}")

    def spawn_lights_ahead(self, world_x, pixels_per_meter, current_player_height, ground_y):
        """Spawn lights ahead of the player"""
        # Similar bounds calculation as objects
        spawn_x_world = world_x + (SCREEN_WIDTH - SCREEN_CENTER_X) / pixels_per_meter
        spawn_buffer = 100 / pixels_per_meter
        spawn_end = spawn_x_world + spawn_buffer
        
        # Get height range for spawning
        min_y_world, max_y_world = self.get_spawn_height_range(current_player_height, SCREEN_HEIGHT)
        
        # Start spawning from last position
        current_spawn_x = max(self.last_spawned_x, world_x)
        
        while current_spawn_x < spawn_end:
            # Filter light types that are appropriate for current player height
            valid_light_types = []
            for light_type in self.light_types:
                min_height, max_height, base_size, color, probability = light_type
                avg_height = (min_height + max_height) / 2
                if self.should_spawn_light(avg_height, current_player_height):
                    valid_light_types.append(light_type)
            
            if not valid_light_types:
                current_spawn_x += 5.0  # Skip ahead if no valid lights
                continue
            
            # Choose a light type based on probability
            rand = random.random()
            cumulative = 0
            chosen_type = None
            total_prob = sum(lt[4] for lt in valid_light_types)
            
            for light_type in valid_light_types:
                cumulative += light_type[4] / total_prob
                if rand <= cumulative:
                    chosen_type = light_type
                    break
            
            if chosen_type is None:
                chosen_type = valid_light_types[0]
            
            min_height, max_height, base_size, color, _ = chosen_type
            
            # Random Y position within range
            spawn_y_world = random.uniform(min_y_world, max_y_world)
            
            # Decide whether to spawn a cluster or single light
            if random.random() < 0.65:  # 65% chance for cluster (much higher)
                self.create_light_cluster(current_spawn_x, spawn_y_world, chosen_type, pixels_per_meter, ground_y)
                current_spawn_x += random.uniform(2.0, 4.0)  # Much smaller gap after cluster
            else:
                # Single light
                light_height = random.uniform(min_height, max_height)
                self.create_single_light(current_spawn_x, spawn_y_world, light_height, 
                                       base_size, color, pixels_per_meter, ground_y)
                current_spawn_x += random.uniform(0.5, 2.0)  # Much smaller gap for single lights
            
            self.last_spawned_x = current_spawn_x

    def check_collisions(self, player_head_rect, player, current_height, speed_x):
        """
        Check for collisions between player head and lights
        Returns updated current_height and speed_x
        """
        for light in list(self.lights):
            if light.rect.colliderect(player_head_rect) and not light.is_fading:
                # Start fading the light
                light.start_fade()
                
                # Print order of magnitude
                order_of_magnitude = int(math.log10(max(0.1, light.height_meters)))
                print(f"Collected light at height {light.height_meters:.2f}m (Order of magnitude: 10^{order_of_magnitude})")
                
                # Add the player growth mechanics from main.py
                player.add_segment()
                current_height += PLANT_SEGMENT_HEIGHT
                
                # Calculate speed increment for this single segment
                speed_increment = (0.4 * PLANT_SEGMENT_HEIGHT / FPS) * (1 / (1 + SPEED_FALLOFF_PARAM * current_height))
                speed_x += speed_increment
        
        return current_height, speed_x

    def update(self, world_x, pixels_per_meter, current_player_height, ground_y, player_head_rect, player, current_height, speed_x):
        """Update all lights and handle spawning"""
        # Spawn new lights
        self.spawn_lights_ahead(world_x, pixels_per_meter, current_player_height, ground_y)
        
        # Update existing lights
        for light in list(self.lights):
            if not self.should_spawn_light(light.height_meters, current_player_height):
                light.kill()
                continue
                
            light.update(world_x, pixels_per_meter, ground_y)
            
        # Check collisions and get updated values
        updated_height, updated_speed = self.check_collisions(player_head_rect, player, current_height, speed_x)
        
        # Cleanup off-screen lights
        self.cleanup_offscreen_lights(world_x, pixels_per_meter)
        
        return updated_height, updated_speed

    def cleanup_offscreen_lights(self, world_x, pixels_per_meter):
        """Remove lights that have moved off screen"""
        kill_x_world = world_x + (0 - SCREEN_CENTER_X) / pixels_per_meter - 50 / pixels_per_meter
        
        for light in list(self.lights):
            if light.world_x < kill_x_world:
                light.kill()

    def draw_all(self, screen, world_x, pixels_per_meter, ground_y):
        """Draw all visible lights"""
        drawn_count = 0
        
        for light in list(self.lights):
            # Update screen position
            screen_x = int(SCREEN_CENTER_X + (light.world_x - world_x) * pixels_per_meter)
            screen_y = self.world_y_to_screen_y(light.world_y, pixels_per_meter, ground_y)
            
            # Only draw if on screen
            if -light.radius <= screen_x <= SCREEN_WIDTH + light.radius and -light.radius <= screen_y <= SCREEN_HEIGHT + light.radius:
                light.draw(screen, screen_x, screen_y)
                drawn_count += 1
        
        print(f"Total lights: {len(self.lights)}, Drawn: {drawn_count}, Last spawned at: {self.last_spawned_x:.1f}")


class Light(pygame.sprite.Sprite):
    def __init__(self, world_x, world_y, height_meters, base_size, color, pixels_per_meter, ground_y):
        super().__init__()
        
        self.world_x = world_x
        self.world_y = world_y
        self.height_meters = height_meters
        self.base_size = base_size
        self.color = color
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        
        self.alpha = 255
        self.is_fading = False
        self.fade_speed = 8
        self.glow_offset = 0  # For pulsing effect
        
        # Calculate initial size and create rect
        self.update_size()
        
    def update_size(self):
        """Update the light's size based on current zoom level"""
        # Calculate size based on height and zoom
        height_scale = math.log10(max(0.1, self.height_meters)) + 1
        zoom_scale = self.pixels_per_meter / 100.0
        
        self.radius = max(2, int(self.base_size * height_scale * zoom_scale * 0.5))
        
        # Create rect for collision detection
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
    
    def start_fade(self):
        """Start fading the light"""
        self.is_fading = True
    
    def update(self, world_x, pixels_per_meter, ground_y):
        """Update the light each frame"""
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        
        # Update size based on new zoom level
        self.update_size()
        
        # Update screen position for collision rect
        screen_x = int(SCREEN_CENTER_X + (self.world_x - world_x) * pixels_per_meter)
        screen_y = int(ground_y - (self.world_y * pixels_per_meter))
        self.rect.center = (screen_x, screen_y)
        
        # Handle fading
        if self.is_fading:
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.kill()
        else:
            # Pulsing glow effect
            self.glow_offset += 0.1
    
    def draw(self, screen, screen_x, screen_y):
        """Draw the light with a glowing effect"""
        if self.alpha <= 0:
            return
            
        # Create a pulsing effect
        pulse = math.sin(self.glow_offset) * 0.2 + 1.0
        current_radius = int(self.radius * pulse)
        
        # Create color with alpha
        color_with_alpha = (*self.color, self.alpha)
        
        # Draw multiple circles for glow effect
        glow_layers = 3
        for i in range(glow_layers):
            layer_radius = current_radius + (glow_layers - i) * 2
            layer_alpha = (self.alpha // glow_layers) // (i + 1)
            
            if layer_alpha > 0:
                # Create a surface for the glow layer
                glow_surf = pygame.Surface((layer_radius * 2, layer_radius * 2), pygame.SRCALPHA)
                glow_color = (*self.color, layer_alpha)
                pygame.draw.circle(glow_surf, glow_color, (layer_radius, layer_radius), layer_radius)
                
                # Blit the glow layer
                screen.blit(glow_surf, (screen_x - layer_radius, screen_y - layer_radius))
        
        # Draw the core light
        if self.alpha > 0:
            core_surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
            core_color = (min(255, self.color[0] + 50), min(255, self.color[1] + 50), min(255, self.color[2] + 50), self.alpha)
            pygame.draw.circle(core_surf, core_color, (current_radius, current_radius), current_radius)
            screen.blit(core_surf, (screen_x - current_radius, screen_y - current_radius))