import pygame
import os
from constants import *

class TitleScreen:
    def __init__(self, screen, font, title_font):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        
        # Load title image
        self.title_img = pygame.image.load(os.path.join("assets/images", "title.png")).convert_alpha()
        
        # Fade variables
        self.fade_alpha = 0
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_speed = 3
        self.is_fading_out = False
        
    def handle_event(self, event):
        """Handle input events. Returns True if should transition to next state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.is_fading_out:
                # Start fade out
                self.is_fading_out = True
                self.fade_alpha = 0
                return False  # Still transitioning
        return False
    
    def update(self):
        """Update title screen. Returns True when fade out is complete."""
        if self.is_fading_out:
            self.fade_alpha += self.fade_speed
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                return True  # Fade complete
        return False
    
    def reset(self):
        """Reset title screen state"""
        self.fade_alpha = 0
        self.is_fading_out = False
    
    def draw(self):
        """Draw the title screen"""
        self.screen.fill((0, 0, 0))  # Black background
        self.screen.blit(self.title_img, (0, 0))
        
        # Draw fade overlay if fading out
        if self.is_fading_out and self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))