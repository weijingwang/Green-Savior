# config.py - Fixed configuration with single ground constant
import pygame

# Display Settings
WIDTH, HEIGHT = 1280, 720
FPS = 60
BG_COLOR = (30, 30, 30)

# Character Settings
TORSO_RADIUS = 35
NECK_RADIUS = 20
HEAD_RADIUS = 28
SEGMENT_LENGTH = 18
INITIAL_NECK_SEGMENTS = 5
MAX_NECK_SEGMENTS = 500
NECK_TO_CONSOLIDATE = 5
UNTOUCHED_NECK_SEGMENTS = 10

# Colors
TORSO_COLOR = (160, 60, 60)
NECK_COLOR = (220, 220, 140)
HEAD_COLOR = (200, 240, 100)
BUILDING_COLOR = (40, 40, 70)
WINDOW_COLOR = (230, 230, 120)
SPOT_COLOR = (200, 50, 50)

# Performance Settings
MIN_ZOOM = 0.0005

# Environment Settings
GROUND_SCREEN_Y = 600  # Ground always appears at screen Y = 600

BUILDING_SPEED = 2
SPOT_SPAWN_CHANCE = 0.01
MIN_SPOT_DISTANCE = 100

pygame.font.init()