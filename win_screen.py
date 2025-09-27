import pygame
import os
from constants import *

class WinScreen:
    def __init__(self, screen, font, title_font, subtitle_font):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.subtitle_font = subtitle_font
        
        # Load background image
        try:
            self.background_img = pygame.image.load(os.path.join("assets/images/end", "end8.jpg")).convert_alpha()
            # Scale to screen size if needed
            self.background_img = pygame.transform.scale(self.background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background_img_text = pygame.image.load(os.path.join("assets/images/end", "end8_text.png")).convert_alpha()

        except pygame.error as e:
            print(f"Could not load end8.jpg: {e}")
            self.background_img = None
        
        # Fade variables for smooth appearance
        self.fade_alpha = 0
        self.fade_speed = 2
        self.max_alpha = 255
        
        # Text positioning
        self.title_text = "Victory!"
        self.subtitle_text = "Press SPACE to return to title"
        
        # Create text surfaces
        # self.title_surface = self.title_font.render(self.title_text, True, (255, 255, 255))
        # self.subtitle_surface = self.subtitle_font.render(self.subtitle_text, True, (255, 255, 255))
        
        # # Calculate text positions
        # self.title_x = (SCREEN_WIDTH - self.title_surface.get_width()) // 2
        # self.title_y = SCREEN_HEIGHT // 2 - 100
        
        # self.subtitle_x = (SCREEN_WIDTH - self.subtitle_surface.get_width()) // 2
        # self.subtitle_y = SCREEN_HEIGHT // 2 + 50
    
    def handle_event(self, event):
        """Handle input events. Returns True if should return to title."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return True
        return False
    
    def update(self):
        """Update win screen animations"""
        # Fade in effect
        if self.fade_alpha < self.max_alpha:
            self.fade_alpha += self.fade_speed
            if self.fade_alpha > self.max_alpha:
                self.fade_alpha = self.max_alpha
    
    def reset(self):
        """Reset win screen state"""
        self.fade_alpha = 0
    
    def draw(self):
        """Draw the win screen"""
        # Draw background
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))
            self.screen.blit(self.background_img_text, (0, 0))

        else:
            # Fallback to black background if image fails to load
            self.screen.fill((0, 0, 0))
        
        # Apply fade effect to text
        # if self.fade_alpha > 0:
            # Create temporary surfaces with alpha for fade effect
            # title_surface = self.title_surface.copy()
            # subtitle_surface = self.subtitle_surface.copy()
            
            # title_surface.set_alpha(self.fade_alpha)
            # subtitle_surface.set_alpha(self.fade_alpha)
            
            # # Draw text
            # self.screen.blit(title_surface, (self.title_x, self.title_y))
            # self.screen.blit(subtitle_surface, (self.subtitle_x, self.subtitle_y))