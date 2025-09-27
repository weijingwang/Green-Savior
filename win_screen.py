import pygame
from constants import *

class WinScreen:
    def __init__(self, screen, font, title_font, subtitle_font):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.subtitle_font = subtitle_font
    
    def handle_event(self, event):
        """Handle input events. Returns True if should return to title."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return True
        return False
    
    def update(self):
        """Update win screen (no updates needed)"""
        pass
    
    def draw(self):
        """Draw the win screen"""
        self.screen.fill((0, 0, 0))  # Black background
        
        victory_text = self.title_font.render("VICTORY!", True, (255, 215, 0))
        final_text = self.font.render("The plant has reached the sky!", True, (255, 255, 255))
        restart_text = self.subtitle_font.render("Press ENTER to return to title", True, (150, 150, 150))
        
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
        final_rect = final_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        
        self.screen.blit(victory_text, victory_rect)
        self.screen.blit(final_text, final_rect)
        self.screen.blit(restart_text, restart_rect)