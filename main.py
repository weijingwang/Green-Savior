import pygame
pygame.init()



# Screen setup
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elevator Simulation")


font = pygame.font.SysFont("Arial", 36, bold=True)
background = pygame.image.load("gameplay_draft.png").convert()  # no per-pixel alpha
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background.set_alpha(128)  # 50% opacity (0 = fully transparent, 255 = fully opaque)


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
RED = (255, 50, 50)

# Elevator shaft
rect_width, rect_height = 200, 600
rect_x = (WIDTH // 2 - rect_width) // 4
rect_y = (HEIGHT - rect_height) // 2

# Elevator
elev_width = 40
NUM_FLOORS = 20
elev_height = rect_height // NUM_FLOORS
elev_x = rect_x + (rect_width - elev_width) // 2
elev_y = float(rect_y)  # Use float for sub-pixel precision
elev_speed = 0.0

# Slider
slider_bar_y = HEIGHT // 2 + 150
slider_bar_width = WIDTH // 2 - 120
slider_bar_x = WIDTH // 2 + 80
slider_bar_height = 6
slider_radius = 12
slider_y = slider_bar_y
slider_x = slider_bar_x

pygame.mouse.set_visible(False)
cursor_radius = 8
floor_height = rect_height / NUM_FLOORS

# Motion parameters
MAX_SPEED = 12.0  # Fast but not too crazy
ACCEL = 1.2       # Quick acceleration for responsiveness
DECEL = 1.6       # Gentler braking to allow overshoot
STOP_THRESHOLD = 1.5  # Smaller threshold for precision
OVERSHOOT_FACTOR = 0.15  # Allow 15% overshoot for fun physics

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Draw background
    screen.fill(WHITE)
    screen.blit(background, (0, 0))

    pygame.draw.rect(screen, BLUE, (rect_x, rect_y, rect_width, rect_height))
    
    # Draw floor lines
    for i in range(NUM_FLOORS + 1):  # +1 so we get the top line too
        y = rect_y + i * floor_height
        pygame.draw.line(screen, WHITE, (rect_x, y), (rect_x + rect_width, y), 2)

    # Mouse (slider) position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if mouse_x < WIDTH // 2:
        mouse_x = WIDTH // 2
    if mouse_x > WIDTH - cursor_radius:
        mouse_x = WIDTH - cursor_radius
    
    slider_x = min(max(mouse_x, slider_bar_x), slider_bar_x + slider_bar_width)
    
    # Target elevator Y based on slider
    t = (slider_x - slider_bar_x) / slider_bar_width
    target_y = rect_y + (1 - t) * (rect_height - elev_height)  # Keep as float
    
    # Compute distance to target
    dist = target_y - elev_y
    
    # Stop if close enough to target AND speed is low
    if abs(dist) <= STOP_THRESHOLD and abs(elev_speed) < 0.8:
        elev_speed = 0
        elev_y = target_y  # Snap to exact target
    else:
        # Calculate allowed overshoot distance for more natural motion
        overshoot_distance = floor_height * OVERSHOOT_FACTOR
        
        # Dynamic braking distance - start braking later for overshoot
        base_braking_distance = (elev_speed ** 2) / (2 * DECEL)
        braking_distance = max(base_braking_distance * 0.8, abs(dist) * 0.2)
        
        if abs(dist) <= braking_distance and abs(dist) > STOP_THRESHOLD:
            # Gentler deceleration to allow natural overshoot
            brake_force = DECEL * (0.7 + (braking_distance - abs(dist)) / braking_distance * 0.5)
            if elev_speed > 0:
                elev_speed = max(0, elev_speed - brake_force)
            elif elev_speed < 0:
                elev_speed = min(0, elev_speed + brake_force)
        else:
            # Accelerate toward target with boost for quick direction changes
            direction_change_boost = 1.0
            if (dist > 0 and elev_speed < 0) or (dist < 0 and elev_speed > 0):
                direction_change_boost = 1.5  # Extra responsive when changing direction
            
            if dist > 0:
                elev_speed = min(MAX_SPEED, elev_speed + ACCEL * direction_change_boost)
            elif dist < 0:
                elev_speed = max(-MAX_SPEED, elev_speed - ACCEL * direction_change_boost)
        
        # Update elevator position
        elev_y += elev_speed
        
        # Allow controlled overshoot, but prevent excessive overshoot
        if ((dist > 0 and elev_y > target_y + overshoot_distance and elev_speed > 0) or 
            (dist < 0 and elev_y < target_y - overshoot_distance and elev_speed < 0)):
            # Only stop if we've overshot too much
            elev_speed *= -0.3  # Bounce back with reduced speed
        elif ((dist > 0 and elev_y > target_y and elev_speed > 0) or 
              (dist < 0 and elev_y < target_y and elev_speed < 0)):
            # We're overshooting but within allowed range - just slow down
            elev_speed *= 0.85
    
    # Snap to nearest floor for display
    nearest_floor = round((rect_y + rect_height - elev_height - elev_y) / floor_height)
    current_floor = min(max(nearest_floor, 0), NUM_FLOORS - 1)
    # print(f"Current Floor: {current_floor + 1}")
    
    # Draw elevator with smooth sub-pixel positioning
    smooth_elev_y = round(elev_y)  # Round to nearest pixel for drawing
    pygame.draw.rect(screen, BLACK, (elev_x, smooth_elev_y, elev_width, elev_height))
    
    # Draw slider bar and circle
    pygame.draw.rect(screen, BLACK, (slider_bar_x, slider_bar_y - slider_bar_height // 2,
                     slider_bar_width, slider_bar_height))
    pygame.draw.circle(screen, RED, (slider_x, slider_y), slider_radius)
    
    floor_text = font.render(f"Floor: {current_floor + 1}", True, BLACK)
    screen.blit(floor_text, (20, 20))  # top-left corner
    # --- Draw FPS text ---
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, RED)
    screen.blit(fps_text, (20, 60))  # just below floor text

    # Draw custom cursor
    pygame.draw.circle(screen, BLACK, (mouse_x, mouse_y), cursor_radius)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()