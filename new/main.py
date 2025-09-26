# main.py

import pygame, os
from constants import *
from utils import Animator

pygame.mixer.init()
pygame.init()
pygame.font.init()
pygame.display.set_caption("Player Class Example")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

import os
import pygame

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




player = Player(SCREEN_CENTER_X, GROUND_Y)

running = True
current_height = STARTING_HEIGHT
speed_x = STARTING_SPEED
world_x = 0 # where you currently are in the world in meters

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # check key hold state outside event loop
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]: # [TODO] for increase neck segments by 1
        current_height += PLANT_SEGMENT_HEIGHT
        speed_x = (0.4 * current_height / FPS) * (1 / (1 + SPEED_FALLOFF_PARAM * current_height))
        print(current_height, "meters")

    player.update()

    screen.fill((50, 100, 255))
    pygame.draw.rect(screen,(100, 200, 100),  # color (greenish example)
        pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
    )
    player.draw(screen)

    # UI
    height_text = font.render(f"Height: {current_height:.2f} m", True, (255, 255, 255))
    world_x_text = font.render(f"World_x: {world_x:.2f} m", True, (255, 255, 255))
    speed_x_text = font.render(f"speed_x: {speed_x*FPS:.2f} m/s", True, (255, 255, 255))
    screen.blit(height_text, (10, 10))  # top-left corner
    screen.blit(world_x_text, (10, 40))  # top-left corner
    screen.blit(speed_x_text, (10, 70))  # top-left corner



    pygame.display.flip()

    world_x += STARTING_SPEED

    clock.tick(60)
    print(f"FPS: {clock.get_fps():.2f}")
