# utils.py

import pygame
from constants import *

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
        self.image_paths = image_paths
        self.frames = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), self.scale) 
                       for p in self.image_paths]
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.counter = 0
        self.change_scale = False

    def get_image(self, scale=(64, 64)):
        """Return the current frame image, advancing animation as needed."""
        self.change_scale = (scale != self.scale)
        if (self.change_scale):
            self.frames = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), scale) 
                        for p in self.image_paths]
        self.counter += 1
        if self.counter >= self.frame_duration:
            self.counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        return self.frames[self.current_frame]
