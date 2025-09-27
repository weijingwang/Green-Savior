import pygame, os
from constants import *
from player import Player
from game_object import ObjectManager
from utils import world_to_screen_x, incremental_add

pygame.mixer.init()
pygame.init()
pygame.font.init()
pygame.display.set_caption("Pyweek 40")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

sky_img = pygame.image.load(os.path.join("assets/images", "sky.png")).convert_alpha()
ground_img = pygame.image.load(os.path.join("assets/images", "ground.png")).convert_alpha()

# Get ground image width for looping calculation
ground_width = ground_img.get_width()

player = Player(SCREEN_CENTER_X, GROUND_Y)

# Create object manager
object_manager = ObjectManager()

running = True
current_height = STARTING_HEIGHT # meters
current_height_pixels = INITIAL_SEGMENTS * INITIAL_PIXELS_PER_METER * PLANT_SEGMENT_HEIGHT # pixels
speed_x = STARTING_SPEED # meters/60s
world_x = 0 # where you currently are in the world in meters

# Track space key press to avoid continuous addition
space_pressed = False

while running:
    print(1/player.pixels_per_meter * world_x + SCREEN_CENTER_X) # This gets the screen center
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not space_pressed:
                space_pressed = True
                # Add neck segment
                player.add_segment()
                current_height += PLANT_SEGMENT_HEIGHT
                
                # Calculate speed increment for this single segment
                speed_increment = (0.4 * PLANT_SEGMENT_HEIGHT / FPS) * (1 / (1 + SPEED_FALLOFF_PARAM * current_height))
                speed_x += speed_increment
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_pressed = False

    # Update height in pixels for zoom
    current_height_pixels = player.segment_count * (player.pixels_per_meter * PLANT_SEGMENT_HEIGHT) # pixels

    # Update pixels_per_meter based on current height
    player.target_pixels_per_meter = (GROUND_Y - MAX_PLANT_Y) / (player.segment_count * PLANT_SEGMENT_HEIGHT)
    player.pixels_per_meter = incremental_add(player.pixels_per_meter, player.target_pixels_per_meter)

    player.update()
    player.update_scale(player.pixels_per_meter)

    # Update object spawning - NOW PASSING CURRENT HEIGHT
    object_manager.update_spawning(world_x, player.pixels_per_meter, current_height)

    # Draw background
    screen.fill((169, 173, 159)) # day sky
    screen.blit(sky_img, (0, 0))
    
    # Calculate ground scroll offset based on world_x at a fixed pixel rate
    # Use a consistent pixels per meter for ground scrolling to avoid zoom stuttering
    ground_pixels_per_meter = 50  # Fixed rate for consistent ground scrolling
    ground_scroll_offset = int((world_x * ground_pixels_per_meter) % ground_width)
    
    # Draw ground tiles to fill the screen width, accounting for scroll offset
    ground_x = -ground_scroll_offset
    while ground_x < SCREEN_WIDTH:
        screen.blit(ground_img, (ground_x, GROUND_Y))
        ground_x += ground_width

    # Draw all objects
    object_manager.draw_all(screen, world_x, player.pixels_per_meter)

    # Draw player
    player.draw(screen)

    # UI
    height_text = font.render(f"Height: {current_height:.2f} m", True, (255, 255, 255))
    world_x_text = font.render(f"World_x: {world_x:.2f} m", True, (255, 255, 255))
    speed_x_text = font.render(f"speed_x: {speed_x*FPS:.2f} m/s", True, (255, 255, 255))
    pixels_per_meter_text = font.render(f"pixels/m: {player.pixels_per_meter:.2f}", True, (255, 255, 255))
    
    screen.blit(height_text, (10, 10))
    screen.blit(world_x_text, (10, 40))
    screen.blit(speed_x_text, (10, 70))
    screen.blit(pixels_per_meter_text, (10, 100))

    pygame.display.flip()

    world_x += speed_x 

    clock.tick(60)