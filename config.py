# config.py - Enhanced configuration with altitude-based features

# Display Settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
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
SPOT_SPAWN_CHANCE = 0.015  # Slightly increased for altitude variety
MIN_SPOT_DISTANCE = 100

# New: Environmental Objects
OBJECT_SPAWN_CHANCE = 0.005  # Less frequent than spots
OBJECT_TYPES = ['tree', 'rock', 'bush', 'flower', 'mushroom', 'crystal', 'statue']

# Altitude-based spot scaling
ALTITUDE_TIERS = {
    0: {'name': 'Ground', 'multiplier': 1, 'color': (200, 50, 50), 'time': 1.0},
    1: {'name': 'Low', 'multiplier': 2, 'color': (255, 80, 50), 'time': 0.8},
    2: {'name': 'Medium', 'multiplier': 3, 'color': (255, 150, 50), 'time': 0.6},
    3: {'name': 'High', 'multiplier': 5, 'color': (255, 200, 50), 'time': 0.4},
    4: {'name': 'Extreme', 'multiplier': 8, 'color': (255, 255, 100), 'time': 0.2}
}