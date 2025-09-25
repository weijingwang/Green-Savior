# game.py - Enhanced plant growing game with altitude spots and environmental objects
import pygame, sys
from config import *
from camera import Camera
from character import Character
from environment import Environment
from renderer import Renderer
from performance import PerformanceManager

class Game:
    """Enhanced game class with altitude-based collectibles and environmental objects"""
    
    def __init__(self):
        pygame.mixer.pre_init()
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Plant Skyscraper City - Enhanced Edition")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize game systems
        self.camera = Camera()
        self.character = Character()
        self.environment = Environment()
        self.renderer = Renderer(self.screen)
        self.performance_manager = PerformanceManager()
        
        # Set initial zoom with simple 3x headroom based on actual length
        initial_length = self.character.get_total_neck_length()
        initial_segment_equiv = int(initial_length / SEGMENT_LENGTH)
        self.camera.set_zoom_for_segment_count(initial_segment_equiv)
        self.camera.zoom = self.camera.target_zoom  # Start at target zoom
        
        # Game statistics
        self.stats = {
            'spots_collected': 0,
            'segments_gained': 0,
            'highest_altitude': 0,
            'objects_seen': set()
        }
        
        self.running = True
    
    def run(self):
        """Main game loop"""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)
        
        self._cleanup()
    
    def _handle_events(self):
        """Process input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._reset_game()
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()
        
        # Handle space bar for neck growth (DEBUG: remove when game is complete)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.character.add_neck_segment()
            self.stats['segments_gained'] += 1
    
    def _reset_game(self):
        """Reset the game to initial state"""
        self.__init__()
        print("Game reset!")
    
    def _toggle_fullscreen(self):
        """Toggle between windowed and fullscreen mode"""
        pygame.display.toggle_fullscreen()
    
    def _update(self):
        """Update all game systems"""
        # Get mouse target position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        target_x, target_y = self.camera.screen_to_world(mouse_x, mouse_y)
        
        # Update character with ground collision (ground is always at world Y = 0)
        torso_pos = self.character.update(target_x, target_y, self.performance_manager, 
                                         self.camera.ground_world_y)
        
        # Update camera to follow character (only horizontally)
        self.camera.follow_target(torso_pos[0], torso_pos[1])
        
        # Zoom based on actual neck length, not display segment count
        equivalent_segment_count = self.character.get_neck_segment_count_for_zoom()
        self.camera.set_zoom_for_segment_count(equivalent_segment_count)
        self.camera.update_zoom_smoothly()
        
        # Update environment
        self.environment.update(self.camera)
        
        # Handle spot collections with enhanced feedback
        self._handle_spot_collections()
        
        # Update statistics
        self._update_statistics(torso_pos)
    
    def _handle_spot_collections(self):
        """Enhanced spot collection handling with statistics tracking"""
        # Find the head segment (should be the middle segment of the plant head structure)
        active_segments = self.character.get_neck_segments_for_rendering()
        if len(active_segments) >= 3:
            head_segment = active_segments[-3]  # Head is 3rd from end in plant structure
            head_pos = head_segment.position
            
            # Store spots before collection for statistics
            spots_before = len(self.environment.spots)
            
            # Check collections
            self.environment.check_spot_collections(
                head_pos[0], head_pos[1], self.character
            )
            
            # Update statistics if spots were collected
            spots_after = len(self.environment.spots)
            if spots_after < spots_before:
                collected_count = spots_before - spots_after
                self.stats['spots_collected'] += collected_count
                
                # Track highest altitude reached (negative Y = higher altitude)
                current_altitude = abs(min(0, head_pos[1]))  # Convert to positive altitude
                if current_altitude > self.stats['highest_altitude']:
                    self.stats['highest_altitude'] = current_altitude
    
    def _update_statistics(self, torso_pos):
        """Update game statistics"""
        # Track unique objects seen (for exploration encouragement)
        for obj in self.environment.objects:
            # Check if object is within "seeing" distance
            distance = abs(obj.x - torso_pos[0])
            if distance < 200:  # Within sight range
                self.stats['objects_seen'].add(obj.object_type)
    
    def _render(self):
        """Enhanced rendering with all new elements"""
        self.renderer.clear_screen()
        
        # Draw environment in proper depth order
        # 1. Buildings (background)
        for building in self.environment.buildings:
            self.renderer.draw_building(building, self.camera)
        
        # 2. Ground plane
        self.renderer.draw_ground(self.camera)
        
        # 3. Environmental objects (on ground, behind character)
        for obj in self.environment.objects:
            self.renderer.draw_object(obj, self.camera)
        
        # 4. Collectible spots (can be at any altitude)
        for spot in self.environment.spots:
            self.renderer.draw_spot(spot, self.camera)
        
        # 5. Character (foreground)
        self.renderer.draw_character(self.character, self.camera, self.performance_manager)
        
        # 6. UI and statistics
        self.renderer.draw_ui(self.character, self.camera, self.performance_manager)
        
        pygame.display.flip()
    
    def _cleanup(self):
        """Clean up resources"""
        pygame.quit()
        sys.exit()