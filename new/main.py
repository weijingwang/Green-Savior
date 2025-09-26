# main.py
import pygame, os
from constants import *
from player import Player
from game_object import GameObject
from utils import world_to_screen_x

pygame.mixer.init()
pygame.init()
pygame.font.init()
pygame.display.set_caption("Pyweek 40")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

player = Player(SCREEN_CENTER_X, GROUND_Y)

running = True
current_height = STARTING_HEIGHT # meters
current_height_pixels = 320 #player.length # pixels
speed_x = STARTING_SPEED # meters/60s
world_x = 0 # where you currently are in the world in meters
pixels_per_meter = current_height_pixels / current_height

# Track space key press to avoid continuous addition
space_pressed = False


# Define object positions in world coordinates (meters from player)
OBJECT_WORLD_POSITIONS = {
    'mouse': -2.0,      # 2 meters to the left of player
    'car': 0.5,         # 0.5 meters to the right of player
    'boonies': 1.5,     # 1.5 meters to the right of player
    'gun': 2.5          # 2.5 meters to the right of player
}

mouse_obj = GameObject(
    image_path=os.path.join("assets/images/objects", "mouse.png"),
    height_meters=MOUSE_HEIGHT,
    pixels_per_meter=pixels_per_meter,
    ground_y=GROUND_Y
)

car_obj = GameObject(
    image_path=os.path.join("assets/images/objects", "car.png"),
    height_meters=CAR_HEIGHT,
    pixels_per_meter=pixels_per_meter,
    ground_y=GROUND_Y
)

boonies_obj = GameObject(
    image_path=os.path.join("assets/images/objects", "boonies.png"),
    height_meters=BOONIES_HEIGHT,
    pixels_per_meter=pixels_per_meter,
    ground_y=GROUND_Y
)

gun_obj = GameObject(
    image_path=os.path.join("assets/images/objects", "gun_building.png"),
    height_meters=GUN_BUILDING_HEIGHT,
    pixels_per_meter=pixels_per_meter,
    ground_y=GROUND_Y
)

mouse_x, car_x, boonies_x, gun_x = OBJECT_WORLD_POSITIONS['mouse'], OBJECT_WORLD_POSITIONS['car'], OBJECT_WORLD_POSITIONS['boonies'], OBJECT_WORLD_POSITIONS['gun']

while running:
    print(player.segment_count)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not space_pressed:
                space_pressed = True
                # Add neck segment
                player.add_segment()
                current_height += PLANT_SEGMENT_HEIGHT
                speed_x = (0.4 * current_height / FPS) * (1 / (1 + SPEED_FALLOFF_PARAM * current_height))
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_pressed = False

    # Update pixels_per_meter based on current height
    pixels_per_meter = current_height_pixels / current_height

    player.update()
    mouse_obj.update_scale(pixels_per_meter, GROUND_Y)
    car_obj.update_scale(pixels_per_meter, GROUND_Y)
    # boonies_obj.update_scale(pixels_per_meter, GROUND_Y)
    # gun_obj.update_scale(pixels_per_meter, GROUND_Y)

    screen.fill((169, 173, 159)) # day sky
    pygame.draw.rect(screen,(69, 65, 52),  # ground color
        pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
    )

    # Draw objects using world coordinates converted to screen coordinates
    # gun_screen_x = world_to_screen_x(gun_x, pixels_per_meter)
    # boonies_screen_x = world_to_screen_x(boonies_x, pixels_per_meter)
    car_screen_x = world_to_screen_x(car_x, pixels_per_meter)
    mouse_screen_x = world_to_screen_x(mouse_x, pixels_per_meter)

    # Only draw objects that are visible on screen
    # if 0 <= gun_screen_x <= SCREEN_WIDTH:
    #     gun_obj.draw(screen, gun_screen_x)
    # if 0 <= boonies_screen_x <= SCREEN_WIDTH:
    #     boonies_obj.draw(screen, boonies_screen_x)
    if 0 <= car_screen_x <= SCREEN_WIDTH:
        car_obj.draw(screen, car_screen_x)
    if 0 <= mouse_screen_x <= SCREEN_WIDTH:
        mouse_obj.draw(screen, mouse_screen_x)

    player.draw(screen)

    # UI
    height_text = font.render(f"Height: {current_height:.2f} m", True, (255, 255, 255))
    world_x_text = font.render(f"World_x: {world_x:.2f} m", True, (255, 255, 255))
    speed_x_text = font.render(f"speed_x: {speed_x*FPS:.2f} m/s", True, (255, 255, 255))
    pixels_per_meter_text = font.render(f"pixels/m: {pixels_per_meter:.2f}", True, (255, 255, 255))
    # segments_text = font.render(f"Neck segments: {player.segment_count}", True, (255, 255, 255))
    
    screen.blit(height_text, (10, 10))
    screen.blit(world_x_text, (10, 40))
    screen.blit(speed_x_text, (10, 70))
    screen.blit(pixels_per_meter_text, (10, 100))
    # screen.blit(segments_text, (10, 130))

    pygame.display.flip()

    world_x += STARTING_SPEED 

    # Update object positions relative to moving plant
    mouse_x, car_x, boonies_x, gun_x = OBJECT_WORLD_POSITIONS['mouse']-world_x, OBJECT_WORLD_POSITIONS['car']-world_x, OBJECT_WORLD_POSITIONS['boonies']-world_x, OBJECT_WORLD_POSITIONS['gun']-world_x

    clock.tick(60)