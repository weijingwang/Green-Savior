# utils.py

import pygame
from constants import *

def incremental_add(current, target):
    diff = target - current
    if abs(diff) > 0.001:
        return current + diff * 0.05
    return target


def world_to_screen_x(world_pos_meters, pixels_per_meter):
    """Convert world position (in meters) to screen x coordinate"""
    return SCREEN_CENTER_X + (world_pos_meters * pixels_per_meter)

class Animator:
    def __init__(self, image_paths, scale=(64, 64), frame_duration=5):
        """
        image_paths: list of file paths to frames
        scale: (width, height) to scale images
        frame_duration: how many ticks each frame lasts
        """
        self.scale = scale
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.counter = 0
        self.change_scale = False
        
        # Load original images once and store in memory
        self.original_frames = [pygame.image.load(p).convert_alpha() for p in image_paths]
        
        # Create scaled frames from originals
        self.frames = [pygame.transform.scale(original, self.scale) for original in self.original_frames]
    
    def get_image(self, scale=(64, 64)):
        """Return the current frame image, advancing animation as needed."""
        self.change_scale = (scale != self.scale)
        
        if self.change_scale:
            # Scale from original images, not from already-scaled ones
            self.frames = [pygame.transform.scale(original, scale) for original in self.original_frames]
            self.scale = scale  # Update current scale
        
        self.counter += 1
        if self.counter >= self.frame_duration:
            self.counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        
        return self.frames[self.current_frame]