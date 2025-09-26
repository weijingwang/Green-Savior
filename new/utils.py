# utils.py

import pygame

class Animator:
    def __init__(self, image_paths, scale=(64, 64), frame_duration=5):
        """
        image_paths: list of file paths to frames
        scale: (width, height) to scale images
        frame_duration: how many ticks each frame lasts
        """
        self.frames = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), scale) 
                       for p in image_paths]
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.counter = 0

    def get_image(self):
        """Return the current frame image, advancing animation as needed."""
        self.counter += 1
        if self.counter >= self.frame_duration:
            self.counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        return self.frames[self.current_frame]
