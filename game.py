# game.py - Fixed main game class with proper zoom for consolidated segments
import pygame
import sys
from config import *
from camera import Camera
from character import Character
from environment import Environment
from renderer import Renderer
from performance import PerformanceManager

class Game:
    """Main game class that orchestrates all systems"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Plant neck game")
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
        
        # Handle space bar for neck growth
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.character.add_neck_segment()
    
    def _update(self):
        """Update all game systems"""
        # Get mouse target position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        target_x, target_y = self.camera.screen_to_world(mouse_x, mouse_y)
        
        # Update character with ground collision
        torso_pos = self.character.update(target_x, target_y, self.performance_manager, 
                                         self.camera.ground_world_y)
        
        # Update camera to follow character
        self.camera.follow_target(torso_pos[0], torso_pos[1])
        
        # Zoom based on actual neck length, not display segment count
        equivalent_segment_count = self.character.get_neck_segment_count_for_zoom()
        self.camera.set_zoom_for_segment_count(equivalent_segment_count)
        self.camera.update_zoom_smoothly()
        
        # Update environment
        self.environment.update(self.camera)
        
        # Handle spot collections
        if self.character.neck_segments:
            head_segment = self.character.neck_segments[-1]
            head_pos = head_segment.position
            self.environment.check_spot_collections(
                head_pos[0], head_pos[1], self.character
            )
    
    def _render(self):
        """Render everything to screen"""
        self.renderer.clear_screen()
        
        # Draw environment
        for building in self.environment.buildings:
            self.renderer.draw_building(building, self.camera)
        
        self.renderer.draw_ground(self.camera)
        
        for spot in self.environment.spots:
            self.renderer.draw_spot(spot, self.camera)
        
        # Draw character
        self.renderer.draw_character(self.character, self.camera, self.performance_manager)
        
        # Draw UI
        self.renderer.draw_ui(self.character, self.camera, self.performance_manager)
        
        pygame.display.flip()
    
    def _cleanup(self):
        """Clean up resources"""
        pygame.quit()
        sys.exit()