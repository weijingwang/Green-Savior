import pygame
import sys
import math
from config import *
from camera import Camera
from character import Character
from environment import Environment
from renderer import Renderer

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Long Neck Zombie")
        self.clock = pygame.time.Clock()
        
        # Initialize game components
        self.camera = Camera()
        self.character = Character()
        self.environment = Environment()
        self.renderer = Renderer(self.screen)
        
        self.running = True
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self):
        """Update game state"""
        # Check if we need to zoom out
        if self.character.check_head_bounds(self.camera):
            self.camera.zoom_out()
        
        # Get mouse position in world coordinates
        mx, my = pygame.mouse.get_pos()
        world_mx, world_my = self.camera.screen_to_world(mx, my)
        
        # Update character
        torso_x, torso_y = self.character.update(world_mx, world_my, self.camera)
        
        # Update camera to follow character
        self.camera.update_position(torso_x, torso_y)
        
        # Update environment
        self.environment.update(self.camera)
        
        # Check collisions with red spots
        if self.character.neck_positions:
            head_x, head_y = self.character.neck_positions[-1]
            self.environment.check_spot_collisions(head_x, head_y, self.character)
    
    def render(self):
        """Render everything to screen"""
        self.renderer.clear()
        
        # Draw environment
        for building in self.environment.buildings:
            self.renderer.draw_building(building, self.camera)
        
        self.renderer.draw_ground(self.camera)
        
        for spot in self.environment.red_spots:
            self.renderer.draw_red_spot(spot, self.camera)
        
        # Draw character
        if self.character.neck_positions:
            torso_x = self.character.base_x + math.sin(self.character.walk_timer * 0.5) * 15
            torso_y = self.character.base_y
            step_phase = (math.sin(self.character.walk_timer) + 1) / 2
            
            if step_phase > 0.3:
                torso_y = self.character.base_y - step_phase * 20
            else:
                torso_y = self.character.base_y - 14 + (math.sin(self.character.walk_timer * 12) * 6)
            
            self.renderer.draw_character(self.character, torso_x, torso_y, self.camera)
        
        # Draw UI
        self.renderer.draw_ui(self.character, self.camera)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()