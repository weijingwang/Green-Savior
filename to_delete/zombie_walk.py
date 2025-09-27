import pygame
import sys
import math
import random

# --- Config ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Sizes
TORSO_RADIUS = 35
NECK_RADIUS = 20
HEAD_RADIUS = 28
SEGMENT_LENGTH = 18
NECK_SEGMENTS = 100

# Floor
FLOOR_Y = HEIGHT // 2 + 100

# Colors
BG_COLOR = (30, 30, 30)
TORSO_COLOR = (160, 60, 60)
NECK_COLOR = (220, 220, 140)
HEAD_COLOR = (200, 240, 100)
BUILDING_COLOR = (40, 40, 70)
WINDOW_COLOR = (230, 230, 120)
WINDOW_DARK = (30, 30, 40)
SPOT_COLOR = (200, 50, 50)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Building parameters
BUILDING_SPEED = 2
BUILDINGS = []

# Red spots
RED_SPOTS = []
SPOT_SPAWN_CHANCE = 0.01
MIN_SPOT_DISTANCE = 100

# Walking animation timer
walk_timer = 0

# Zoom
zoom_factor = 1.0

# Neck positions
base_x, base_y = WIDTH // 2, HEIGHT // 2
neck_positions = [(base_x, base_y - (i + 1) * SEGMENT_LENGTH) for i in range(NECK_SEGMENTS)]

def create_building(x):
    width = random.randint(int(WIDTH * 1.5), int(WIDTH * 3))
    height = random.randint(int(HEIGHT * 0.6), int(HEIGHT * 0.95))
    y = FLOOR_Y - height

    # Windows scaled to building
    window_w = max(30, width // 15)
    window_h = max(50, height // 20)
    spacing_x = window_w // 2
    spacing_y = window_h // 2

    cols = max(1, width // (window_w + spacing_x))
    rows = max(1, height // (window_h + spacing_y))

    windows = []
    for r in range(rows):
        row = []
        for c in range(cols):
            lit = (random.random() > 0.35)
            row.append(lit)
        windows.append(row)

    return {
        "x": x, "y": y, "w": width, "h": height,
        "window_w": window_w, "window_h": window_h,
        "spacing_x": spacing_x, "spacing_y": spacing_y,
        "rows": rows, "cols": cols, "windows": windows
    }

def draw_building(building, surface):
    pygame.draw.rect(surface, BUILDING_COLOR, (building["x"], building["y"], building["w"], building["h"]))
    for r in range(building["rows"]):
        for c in range(building["cols"]):
            if building["windows"][r][c]:
                wx = building["x"] + 10 + c * (building["window_w"] + building["spacing_x"])
                wy = building["y"] + 10 + r * (building["window_h"] + building["spacing_y"])
                pygame.draw.rect(surface, WINDOW_COLOR, (wx, wy, building["window_w"], building["window_h"]))

def spawn_red_spot():
    x = WIDTH + random.randint(100, 400)
    y = random.randint(50, FLOOR_Y - 50)
    r = 12
    for s in RED_SPOTS:
        if abs(s["x"] - x) < MIN_SPOT_DISTANCE:
            return None
    return {"x": x, "y": y, "r": r, "timer": 0.0}

def update_neck(base, target, segments, length, stiffness=0.15):
    points = segments[:]
    points[0] = (base[0], base[1] - TORSO_RADIUS)
    for i in range(1, len(points)):
        dx = target[0] - points[i-1][0]
        dy = target[1] - points[i-1][1]
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.0001
        dx /= dist; dy /= dist
        desired_x = points[i-1][0] + dx * length
        desired_y = points[i-1][1] + dy * length
        x = points[i][0] * (1 - stiffness) + desired_x * stiffness
        y = points[i][1] * (1 - stiffness) + desired_y * stiffness
        dx = x - points[i-1][0]; dy = y - points[i-1][1]
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.0001
        dx /= dist; dy /= dist
        px = points[i-1][0] + dx * length
        py = points[i-1][1] + dy * length
        if py > FLOOR_Y: py = FLOOR_Y
        points[i] = (px, py)
    return points

# Initial buildings
x_pos = 0
while x_pos < WIDTH * 2:
    b = create_building(x_pos)
    BUILDINGS.append(b)
    x_pos += b["w"] + 200

# Main loop
while True:
    dt = clock.tick(FPS)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Scroll buildings
    for b in BUILDINGS:
        b["x"] -= BUILDING_SPEED
    if BUILDINGS and BUILDINGS[0]["x"] + BUILDINGS[0]["w"] < 0:
        BUILDINGS.pop(0)
    if BUILDINGS and BUILDINGS[-1]["x"] + BUILDINGS[-1]["w"] < WIDTH:
        BUILDINGS.append(create_building(BUILDINGS[-1]["x"] + BUILDINGS[-1]["w"] + 200))

    # Spawn red spots
    if random.random() < SPOT_SPAWN_CHANCE:
        s = spawn_red_spot()
        if s: RED_SPOTS.append(s)

    # Scroll red spots
    for s in RED_SPOTS:
        s["x"] -= BUILDING_SPEED
    RED_SPOTS = [s for s in RED_SPOTS if s["x"] + s["r"] > 0]

    # Walking animation
    walk_timer += 0.05
    step_phase = (math.sin(walk_timer)+1)/2
    if step_phase>0.3: torso_y = base_y - step_phase*20
    else: torso_y = base_y - 14 + math.sin(walk_timer*12)*6
    torso_x = base_x + math.sin(walk_timer*0.5)*15

    # Mouse and zoom
    mx, my = pygame.mouse.get_pos()
    if my < HEIGHT*0.2:
        neck_dx = mx - base_x
        neck_dy = my - base_y
        target_dist = math.hypot(neck_dx, neck_dy)
        max_dist = SEGMENT_LENGTH*len(neck_positions)
        needed_zoom = max(0.5, min(zoom_factor, max_dist/(target_dist+1)))
        zoom_factor = needed_zoom  # permanent shrink

    neck_positions = update_neck((torso_x, torso_y), (mx, my), neck_positions, SEGMENT_LENGTH)

    # Check collisions with red spots
    head_x, head_y = neck_positions[-1]
    for s in RED_SPOTS:
        dist = math.hypot(head_x - s["x"], head_y - s["y"])
        if dist < HEAD_RADIUS + s["r"]:
            s["timer"] += dt
            if s["timer"] >= 1.0 and len(neck_positions) < 300:
                neck_positions.insert(-1, neck_positions[-2])
                s["timer"] = 0.0
        else:
            s["timer"] = 0.0

    # Draw to world surface
    world = pygame.Surface((WIDTH, HEIGHT))
    world.fill(BG_COLOR)
    for b in BUILDINGS: draw_building(b, world)
    pygame.draw.rect(world, (20,20,50), (0,FLOOR_Y,WIDTH,HEIGHT-FLOOR_Y))
    for s in RED_SPOTS: pygame.draw.circle(world, SPOT_COLOR, (int(s["x"]), int(s["y"])), s["r"])
    pygame.draw.circle(world, TORSO_COLOR, (int(torso_x), int(torso_y)), TORSO_RADIUS)
    for i, p in enumerate(neck_positions):
        py = min(p[1], FLOOR_Y)
        if i==len(neck_positions)-1:
            pygame.draw.circle(world, HEAD_COLOR, (int(p[0]), int(py)), HEAD_RADIUS)
        else:
            radius = int(NECK_RADIUS*(1 - i/max(1,len(neck_positions))*0.4))
            pygame.draw.circle(world, NECK_COLOR, (int(p[0]), int(py)), radius)

    # Scale world with permanent zoom
    scaled = pygame.transform.smoothscale(world, (int(WIDTH*zoom_factor), int(HEIGHT*zoom_factor)))
    offset_x = (WIDTH - scaled.get_width())//2
    offset_y = (HEIGHT - scaled.get_height())//2
    screen.fill(BG_COLOR)
    screen.blit(scaled, (offset_x, offset_y))

    pygame.display.flip()
