# Configuration settings for the game
import pygame

# --- Display Settings ---
WIDTH, HEIGHT = 800, 600
FPS = 60
BG_COLOR = (30, 30, 30)

# --- Character Sizes ---
TORSO_RADIUS = 35
NECK_RADIUS = 20
HEAD_RADIUS = 28
SEGMENT_LENGTH = 18
NECK_SEGMENTS = 100

# --- World Settings ---
FLOOR_Y = HEIGHT // 2 + 100

# --- Colors ---
TORSO_COLOR = (160, 60, 60)
NECK_COLOR = (220, 220, 140)
HEAD_COLOR = (200, 240, 100)
BUILDING_COLOR = (40, 40, 70)
WINDOW_COLOR = (230, 230, 120)
SPOT_COLOR = (200, 50, 50)

# --- Performance Settings ---
LOD_LEVELS = {
    1.0: {"segments": -1, "physics_skip": 1, "name": "Mouse Size"},
    0.5: {"segments": -1, "physics_skip": 1, "name": "Cat Size"},
    0.2: {"segments": 100, "physics_skip": 1, "name": "Human Size"},
    0.1: {"segments": 80, "physics_skip": 1, "name": "Room Size"},
    0.05: {"segments": 60, "physics_skip": 2, "name": "House Size"},
    0.02: {"segments": 40, "physics_skip": 3, "name": "Building Size"},
    0.01: {"segments": 25, "physics_skip": 5, "name": "Block Size"},
    0.005: {"segments": 15, "physics_skip": 8, "name": "District Size"},
    0.002: {"segments": 10, "physics_skip": 12, "name": "City Size"},
    0.001: {"segments": 6, "physics_skip": 20, "name": "Skyscraper Size"}
}

SEGMENT_CULL_RADIUS = 1
ZOOM_SPEED = 0.0005  # Even slower zoom for more scale levels

# --- Building Settings ---
BUILDING_SPEED = 2

# --- Red Spot Settings ---
SPOT_SPAWN_CHANCE = 0.01
MIN_SPOT_DISTANCE = 100

# Initialize Pygame font (needed for text rendering)
pygame.font.init()