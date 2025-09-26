# player.py
import pygame, os
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

        # Plant head (static image for now) [TODO]
        self.head_image = pygame.image.load(
            os.path.join(image_folder, "head.png")
            ).convert_alpha()
        self.head_image = pygame.transform.scale(self.head_image, PLANT_HEAD_SIZE)
        self.head_rect = self.head_image.get_rect(midbottom=self.base_rect.midtop)  # attach above base

        # Neck placeholder (will be IK later) [TODO]
        self.neck_points = []  # placeholder for joint positions

    def update(self):
        # Update base animation
        self.base_image = self.animator.get_image()

        # Update head position (follows base for now) [TODO]
        self.head_rect.midbottom = self.base_rect.midtop  

        # Neck IK update will go here later [TODO]
        # self.neck_points = calculate_neck_positions(...)

    def draw(self, surface):
        # Draw base
        surface.blit(self.base_image, self.base_rect)

        # Placeholder for neck (draw simple line for now)
        if self.neck_points:
            pygame.draw.lines(surface, (200, 200, 200), False, self.neck_points, 4)

        # Draw head
        surface.blit(self.head_image, self.head_rect)