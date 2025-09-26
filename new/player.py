# player.py
import pygame, os, math
from pygame.math import Vector2
from constants import *
from utils import Animator

class Player:
    def __init__(self, x, y, image_folder="assets/images/player"):
        """
        Player class
        x, y position and image folder for assets
        """
        # Plant base
        base_paths = [os.path.join(image_folder, f"base/base{i}.png") for i in range(1, 19)]
        self.animator = Animator(base_paths, scale=PLANT_BASE_SIZE, frame_duration=5)
        self.base_image = self.animator.get_image()
        self.base_rect = self.base_image.get_rect(center=(x, y))
        
        # Plant head (static image for now)
        self.head_image = pygame.image.load(
            os.path.join(image_folder, "head.png")
        ).convert_alpha()
        self.head_image = pygame.transform.scale(self.head_image, PLANT_HEAD_SIZE)
        
        # Chain-like neck system
        self.segment_count = 5
        self.segment_length = 30
        
        # Chain physics properties
        self.gravity = 0.2  # Downward force
        self.mouse_strength = 0.1  # How strongly mouse pulls the head
        self.constraint_iterations = 3  # How many times to enforce constraints
        
        # Initialize neck segments
        self.neck_points = []
        self.old_neck_points = []  # For Verlet integration
        self.segment_lengths = []
        
        # Start neck from inside the base (50 pixels down from top)
        start_x = self.base_rect.centerx
        start_y = self.base_rect.top + 50
        
        # Initialize neck points in a straight line upward
        for i in range(self.segment_count + 1):
            point = Vector2(start_x, start_y - i * self.segment_length)
            self.neck_points.append(point)
            self.old_neck_points.append(Vector2(point))  # Copy for Verlet
        
        # Store segment lengths
        for i in range(self.segment_count):
            self.segment_lengths.append(self.segment_length)
        
        # Head position
        self.head_rect = self.head_image.get_rect()
        self.update_head_position()
        
        self.base_position = Vector2(start_x, start_y)
    
    def update_head_position(self):
        """Update head position based on last neck joint"""
        if self.neck_points:
            self.head_rect.midbottom = (int(self.neck_points[-1].x), int(self.neck_points[-1].y))
    
    def update_chain_physics(self):
        """Update chain using Verlet integration - simple and stable"""
        # Apply forces to all points except the base (index 0)
        for i in range(1, len(self.neck_points)):
            # Store current position
            current_pos = Vector2(self.neck_points[i])
            
            # Calculate velocity from position history (Verlet integration)
            velocity = self.neck_points[i] - self.old_neck_points[i]
            
            # Apply gravity
            velocity.y += self.gravity
            
            # Apply mouse force to head segment only
            if i == len(self.neck_points) - 1:  # Last segment (head)
                mouse_pos = Vector2(pygame.mouse.get_pos())
                to_mouse = mouse_pos - self.neck_points[i]
                # Apply mouse force
                velocity += to_mouse * self.mouse_strength
            
            # Store old position
            self.old_neck_points[i] = current_pos
            
            # Update position
            self.neck_points[i] += velocity
    
    def apply_distance_constraints(self):
        """Maintain fixed distances between chain segments"""
        for iteration in range(self.constraint_iterations):
            # Forward pass: from base to head
            for i in range(len(self.neck_points) - 1):
                # Vector from current point to next point
                segment = self.neck_points[i + 1] - self.neck_points[i]
                distance = segment.length()
                target_distance = self.segment_lengths[i]
                
                if distance > 0:  # Avoid division by zero
                    # Calculate correction
                    difference = target_distance - distance
                    correction = segment.normalize() * (difference * 0.5)
                    
                    # Apply correction (both points move toward each other)
                    if i == 0:  # Base point - don't move it
                        self.neck_points[i + 1] += correction * 2
                    else:
                        self.neck_points[i] -= correction
                        self.neck_points[i + 1] += correction
            
            # Backward pass: from head to base
            for i in range(len(self.neck_points) - 2, -1, -1):
                # Vector from next point to current point
                segment = self.neck_points[i] - self.neck_points[i + 1]
                distance = segment.length()
                target_distance = self.segment_lengths[i]
                
                if distance > 0:  # Avoid division by zero
                    # Calculate correction
                    difference = target_distance - distance
                    correction = segment.normalize() * (difference * 0.5)
                    
                    # Apply correction
                    if i == 0:  # Base point - don't move it
                        self.neck_points[i + 1] -= correction * 2
                    else:
                        self.neck_points[i] += correction
                        self.neck_points[i + 1] -= correction
        
        # Apply ground collision constraints
        self.apply_ground_collision()
    
    def update_neck_base_position(self):
        """Update the base of the neck to follow the plant base"""
        new_base = Vector2(self.base_rect.centerx, self.base_rect.top + 50)
        offset = new_base - self.neck_points[0]
        
        # Move all neck points by the offset
        for i in range(len(self.neck_points)):
            self.neck_points[i] += offset
            self.old_neck_points[i] += offset
        
        self.base_position = new_base
    
    def apply_ground_collision(self):
        """Prevent neck segments and head from passing through the ground"""
        for i in range(len(self.neck_points)):
            # If any point is below ground level, push it back up
            if self.neck_points[i].y > GROUND_Y:
                # Set to ground level
                self.neck_points[i].y = GROUND_Y
                
                # Stop downward movement by resetting old position
                if i < len(self.old_neck_points):
                    self.old_neck_points[i].y = min(self.old_neck_points[i].y, GROUND_Y)
    
    def add_neck_segment(self):
        """Add a new segment to the neck"""
        if len(self.neck_points) < 15:
            # Calculate direction for new segment
            if len(self.neck_points) > 1:
                direction = (self.neck_points[-1] - self.neck_points[-2])
                if direction.length() > 0:
                    direction = direction.normalize() * self.segment_length
                else:
                    direction = Vector2(0, -self.segment_length)
            else:
                direction = Vector2(0, -self.segment_length)
            
            # Add new point
            new_point = self.neck_points[-1] + direction
            self.neck_points.append(new_point)
            self.old_neck_points.append(Vector2(new_point))
            
            # Add segment length
            self.segment_lengths.append(self.segment_length)
            
            self.segment_count += 1
    
    def update(self):
        # Update base animation
        self.base_image = self.animator.get_image()
        
        # Update neck base position to follow the plant base
        self.update_neck_base_position()
        
        # Update chain physics
        self.update_chain_physics()
        
        # Apply distance constraints to maintain chain structure
        self.apply_distance_constraints()
        
        # Update head position
        self.update_head_position()
    
    def draw(self, surface):
        # Draw neck segments with varying thickness
        if len(self.neck_points) > 1:
            for i in range(len(self.neck_points) - 1):
                start_pos = (int(self.neck_points[i].x), int(self.neck_points[i].y))
                end_pos = (int(self.neck_points[i + 1].x), int(self.neck_points[i + 1].y))
                
                # Thickness decreases toward the head
                thickness = max(4, 12 - i)
                pygame.draw.line(surface, (34, 139, 34), start_pos, end_pos, thickness)
        
        # Draw neck joints
        for i, point in enumerate(self.neck_points):
            joint_size = max(2, 5 - i // 2)
            pygame.draw.circle(surface, (20, 80, 20), (int(point.x), int(point.y)), joint_size)

        # Draw base
        surface.blit(self.base_image, self.base_rect)

        # Draw head
        surface.blit(self.head_image, self.head_rect)