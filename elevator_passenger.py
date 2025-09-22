import pygame
import random
import math
from constants import *

class ElevatorPassenger:
    """Represents a person inside the elevator"""
    def __init__(self, destination_floor, color, radius, speed):
        self.destination_floor = destination_floor
        self.color = color
        self.radius = radius
        self.speed = speed
        self.alpha = 255  # For fading effect when exiting
        self.x = 0  # Will be set when streaming out
        self.y = 0  # Will be set when streaming out
        self.streaming_out = False
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.bob_speed = random.uniform(0.05, 0.15)
        
    def start_streaming_out(self, elevator_center_x, floor_y):
        """Start the passenger streaming out of the elevator"""
        self.streaming_out = True
        self.x = float(elevator_center_x)
        self.y = float(floor_y)
        
    def update(self):
        """Update passenger position when streaming out"""
        if self.streaming_out:
            # Move left and fade away
            self.x -= STREAM_OUT_SPEED
            self.alpha = max(0, self.alpha - FADE_SPEED)
            self.bob_offset += self.bob_speed
            
    def draw(self, screen):
        """Draw the passenger (only when streaming out)"""
        if self.streaming_out and self.alpha > 0:
            # Create surface with alpha for fading
            temp_surface = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            
            # Add bobbing motion
            bob_y = self.y + math.sin(self.bob_offset) * 1.5
            
            # Draw with fade effect
            faded_color = (*self.color, self.alpha)
            pygame.draw.circle(temp_surface, faded_color, 
                             (self.radius + 2, self.radius + 2), self.radius)
            
            # Draw face with same alpha
            face_color = (*BLACK, self.alpha)
            pygame.draw.circle(temp_surface, face_color, 
                             (self.radius, self.radius), 1)
            pygame.draw.circle(temp_surface, face_color, 
                             (self.radius + 4, self.radius), 1)
            
            screen.blit(temp_surface, (int(self.x - self.radius - 2), int(bob_y - self.radius - 2)))
            
    def is_off_screen(self):
        """Check if passenger has moved off screen - let them travel further"""
        return self.x < -150 or self.alpha <= 0  # Changed from -50 to -150