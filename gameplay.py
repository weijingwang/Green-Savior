import pygame
import os
from constants import *
from player import Player
from game_object import ObjectManager
from utils import world_to_screen_x, incremental_add
from light import LightManager
from dialogue import DialogueManager

class Gameplay:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        
        # Load images
        self.sky_img = pygame.image.load(os.path.join("assets/images", "sky.png")).convert_alpha()
        self.ground_img = pygame.image.load(os.path.join("assets/images", "ground.png")).convert_alpha()
        self.ground_width = self.ground_img.get_width()
        
        # Game components
        self.player = None
        self.object_manager = None
        self.light_manager = None
        self.dialogue_manager = None
        
        # Game state variables
        self.current_height = 0
        self.current_height_pixels = 0
        self.speed_x = 0
        self.world_x = 0
        self.space_pressed = False
        
        # Win condition variables
        self.fading_to_win = False
        self.fade_alpha = 0
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_speed = 3
        
        # Initialize game
        self.reset()
    
    def reset(self):
        """Reset all game variables for a new game"""
        self.player = Player(SCREEN_CENTER_X, GROUND_Y)
        self.object_manager = ObjectManager()
        self.light_manager = LightManager()
        self.dialogue_manager = DialogueManager()
        
        self.current_height = STARTING_HEIGHT
        self.current_height_pixels = INITIAL_SEGMENTS * INITIAL_PIXELS_PER_METER * PLANT_SEGMENT_HEIGHT
        self.speed_x = STARTING_SPEED
        self.world_x = 0
        self.space_pressed = False
        
        # Reset win condition
        self.fading_to_win = False
        self.fade_alpha = 0
    
    def handle_event(self, event):
        """Handle input events. Returns True if should transition to ending."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.space_pressed:
                self.space_pressed = True
                
                # Check if dialogue is active
                if self.dialogue_manager.is_active():
                    self.dialogue_manager.advance_dialogue()
            
            elif event.key == pygame.K_RETURN:
                # Check win condition
                if self.current_height > 40:
                    self.fading_to_win = True
                    
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.space_pressed = False
        
        return False
    
    def update(self):
        """Update gameplay. Returns True when should transition to ending."""
        # Handle fade to win
        if self.fading_to_win:
            self.fade_alpha += self.fade_speed
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                return True  # Transition to ending
        
        # Regular game updates
        self.current_height_pixels = self.player.segment_count * (self.player.pixels_per_meter * PLANT_SEGMENT_HEIGHT)
        
        self.player.target_pixels_per_meter = (GROUND_Y - MAX_PLANT_Y) / (self.player.segment_count * PLANT_SEGMENT_HEIGHT)
        self.player.pixels_per_meter = incremental_add(self.player.pixels_per_meter, self.player.target_pixels_per_meter)
        
        self.player.update()
        self.player.update_scale(self.player.pixels_per_meter)
        
        self.object_manager.update_spawning(self.world_x, self.player.pixels_per_meter, self.current_height)
        
        self.current_height, self.speed_x = self.light_manager.update(
            self.world_x, self.player.pixels_per_meter, self.current_height, 
            GROUND_Y, self.player.head_rect, self.player, self.current_height, self.speed_x
        )
        
        self.dialogue_manager.trigger_dialogue(self.current_height)
        self.dialogue_manager.update()
        
        self.world_x += self.speed_x
        
        return False
    
    def draw(self):
        """Draw the gameplay"""
        # Draw background
        self.screen.fill((169, 173, 159))  # day sky
        self.screen.blit(self.sky_img, (0, 0))
        
        # Calculate ground scroll offset
        ground_pixels_per_meter = 50
        ground_scroll_offset = int((self.world_x * ground_pixels_per_meter) % self.ground_width)
        
        # Draw ground tiles
        ground_x = -ground_scroll_offset
        while ground_x < SCREEN_WIDTH:
            self.screen.blit(self.ground_img, (ground_x, GROUND_Y))
            ground_x += self.ground_width
        
        # Draw all objects
        self.object_manager.draw_all(self.screen, self.world_x, self.player.pixels_per_meter)
        self.light_manager.draw_all(self.screen, self.world_x, self.player.pixels_per_meter, GROUND_Y)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw dialogue
        self.dialogue_manager.draw(self.screen)
        
        # UI
        height_text = self.font.render(f"Height: {self.current_height:.2f} m", True, (255, 255, 255))
        world_x_text = self.font.render(f"World_x: {self.world_x:.2f} m", True, (255, 255, 255))
        speed_x_text = self.font.render(f"speed_x: {self.speed_x*FPS:.2f} m/s", True, (255, 255, 255))
        pixels_per_meter_text = self.font.render(f"pixels/m: {self.player.pixels_per_meter:.2f}", True, (255, 255, 255))
        
        self.screen.blit(height_text, (10, 10))
        self.screen.blit(world_x_text, (10, 40))
        self.screen.blit(speed_x_text, (10, 70))
        self.screen.blit(pixels_per_meter_text, (10, 100))
        
        # Show win condition hint
        if self.current_height > 35:  # Show hint when close to winning
            win_text = self.font.render("Press ENTER when height > 40m to reach the sky!", True, (255, 255, 0))
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(win_text, win_rect)
        
        # Draw fade overlay if fading to win
        if self.fading_to_win and self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))