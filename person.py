import pygame
import random
import math
from constants import *

class Person:
    def __init__(self, floor, spawn_x, queue_position):
        self.floor = floor  # Which floor they're on (0-20)
        self.destination_floor = random.randint(0, NUM_FLOORS - 1)  # Where they want to go
        # Make sure they don't want to go to their current floor
        while self.destination_floor == self.floor:
            self.destination_floor = random.randint(0, NUM_FLOORS - 1)
            
        self.x = spawn_x
        self.floor_height = RECT_HEIGHT / NUM_FLOORS
        self.y = RECT_Y + floor * self.floor_height + self.floor_height * 0.7  # Stand on floor
        self.queue_position = queue_position  # Position in line (0 = front)
        self.target_x = self.calculate_target_x()  # Calculate position in line
        self.speed = random.uniform(2.0, 3.0)  # Slightly faster walking speed
        self.color = random.choice([GREEN, YELLOW, PURPLE, RED])
        self.radius = random.randint(4, 7)
        self.waiting = False  # True when they reach their position in line
        self.streaming_in = False  # True when streaming into elevator
        self.bob_offset = random.uniform(0, math.pi * 2)  # For bobbing animation
        self.bob_speed = random.uniform(0.05, 0.15)
        self.alpha = 255  # For fading effect when entering elevator
        
    def calculate_target_x(self):
        # Line up horizontally to the right of the elevator
        # Each person takes up about 18 pixels of horizontal space
        person_spacing = 18
        base_x = RECT_X + RECT_WIDTH + 15  # Start 15 pixels to the right of elevator
        return base_x + (self.queue_position * person_spacing)
        
    def update_queue_position(self, new_position):
        """Update this person's position in the queue"""
        # Don't update position if currently streaming into elevator
        if self.streaming_in:
            return
            
        old_position = self.queue_position
        self.queue_position = new_position
        new_target = self.calculate_target_x()
        
        # Only update if the position actually changed
        if old_position != new_position:
            self.target_x = new_target
            # If they were already waiting, they need to move to their new position
            if self.waiting and abs(self.x - new_target) > 2.0:
                self.waiting = False
    
    def start_streaming_in(self, elevator_center_x):
        """Start streaming into the elevator"""
        self.streaming_in = True
        self.target_x = elevator_center_x
        self.waiting = False
        
    def update(self):
        if self.streaming_in:
            # Stream toward elevator center (no fading - they will become passengers)
            distance_to_elevator = abs(self.x - self.target_x)
            if distance_to_elevator > 3.0:
                if self.x > self.target_x:
                    self.x -= STREAM_IN_SPEED
                elif self.x < self.target_x:
                    self.x += STREAM_IN_SPEED
                return False  # Still streaming
            else:
                return True  # Reached elevator center, convert to passenger
                
        elif not self.waiting:
            # Move toward their position in line
            distance_to_target = abs(self.x - self.target_x)
            if distance_to_target > 2.0:  # Threshold to reduce jittering
                if self.x > self.target_x:
                    self.x -= min(self.speed, distance_to_target * 0.3)  # Slow down as we get closer
                elif self.x < self.target_x:
                    self.x += min(self.speed, distance_to_target * 0.3)  # Slow down as we get closer
            else:
                self.x = self.target_x
                self.waiting = True
        
        # Add subtle bobbing animation when waiting
        if self.waiting:
            self.bob_offset += self.bob_speed
            
        return False  # Not ready to be removed
            
    def draw(self, screen):
        draw_y = self.y
        if self.waiting or self.streaming_in:
            # Add bobbing when waiting or streaming
            draw_y += math.sin(self.bob_offset) * 1.5
        
        # Normal drawing (no fading when entering - they become passengers)
        pygame.draw.circle(screen, self.color, (int(self.x), int(draw_y)), self.radius)
        # Add a simple face
        pygame.draw.circle(screen, BLACK, (int(self.x - 2), int(draw_y - 2)), 1)
        pygame.draw.circle(screen, BLACK, (int(self.x + 2), int(draw_y - 2)), 1)