import pygame, os, random
from constants import *
from player import Player
from game_object import GameObject
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

class ObjectManager:
    def __init__(self):
        self.objects = pygame.sprite.Group()
        self.rightmost_spawned = 0.0
        self.leftmost_spawned = 0.0
        self.object_configs = [
            ('mouse', MOUSE_HEIGHT, 0.4),
            ('car', CAR_HEIGHT, 0.3),
            ('boonies', BOONIES_HEIGHT, 0.2),
            ('gun', GUN_BUILDING_HEIGHT, 0.1),
        ]

    def get_visible_range(self, world_x, pixels_per_meter):
        screen_meters = SCREEN_WIDTH / pixels_per_meter
        buffer = screen_meters * 0.5
        return world_x - buffer, world_x + screen_meters + buffer

    def spawn_object(self, world_pos, pixels_per_meter):
        rand = random.random()
        cumulative = 0
        selected_obj = None
        for obj_type, height, probability in self.object_configs:
            cumulative += probability
            if rand <= cumulative:
                selected_obj = (obj_type, height)
                break

        if not selected_obj:
            return

        obj_type, height = selected_obj
        try:
            image_path = os.path.join(
                "assets/images/objects",
                f"{obj_type}.png" if obj_type != 'gun' else "gun_building.png"
            )
            print(f"Creating {obj_type} at world position {world_pos:.2f}")

            obj = GameObject(
                image_path=image_path,
                height_meters=height,
                pixels_per_meter=pixels_per_meter,
                ground_y=GROUND_Y
            )

            # If GameObject immediately marked itself to_kill or failed to set rect/image, don't add it.
            if getattr(obj, "to_kill", False):
                print(f"Not adding {obj_type} at {world_pos:.2f} (marked to_kill immediately)")
                # let obj fall out of scope so Python can collect it
                return

            if getattr(obj, "rect", None) is None or getattr(obj, "image_scaled", None) is None:
                print(f"Not adding {obj_type} at {world_pos:.2f} (missing rect/image_scaled)")
                return

            # attach world pos and type, then add to group
            obj.world_pos = world_pos
            obj.obj_type = obj_type
            self.objects.add(obj)
            print(f"Successfully created {obj_type}, total objects: {len(self.objects)}")

        except Exception as e:
            print(f"Error creating object {obj_type}: {e}")

    def update_spawning(self, world_x, pixels_per_meter):
        left_visible, right_visible = self.get_visible_range(world_x, pixels_per_meter)

        # Spawn to the right
        spawn_count = 0
        while self.rightmost_spawned < right_visible and spawn_count < 10:
            self.spawn_object(self.rightmost_spawned, pixels_per_meter)
            self.rightmost_spawned += random.uniform(2.0, 5.0)
            spawn_count += 1

        # Spawn to the left
        spawn_count = 0
        while self.leftmost_spawned > left_visible and spawn_count < 10:
            self.spawn_object(self.leftmost_spawned, pixels_per_meter)
            self.leftmost_spawned -= random.uniform(2.0, 5.0)
            spawn_count += 1

        # Update scales (snapshot the group so objects can kill() themselves inside update_scale)
        for obj in list(self.objects):
            obj.update_scale(pixels_per_meter, GROUND_Y)
            # keep the standard pygame.Sprite image reference in sync if needed
            if getattr(obj, "image_scaled", None):
                obj.image = obj.image_scaled

        # Cleanup distant objects
        self.cleanup_distant(world_x, pixels_per_meter)

    def cleanup_distant(self, world_x, pixels_per_meter):
        cleanup_distance = (SCREEN_WIDTH / pixels_per_meter) * 2
        for obj in list(self.objects):
            world_pos = getattr(obj, "world_pos", None)
            if world_pos is None:
                continue
            if abs(world_pos - world_x) > cleanup_distance:
                print(f"Killing object {getattr(obj, 'obj_type', '?')} at {world_pos:.2f} (too far)")
                obj.kill()

    def draw_all(self, screen, world_x, pixels_per_meter):
        """Draw all visible objects, moving them according to world_x."""
        for obj in list(self.objects):
            # skip incomplete objects
            if getattr(obj, "rect", None) is None or getattr(obj, "image_scaled", None) is None:
                obj.kill()
                continue

            world_pos = getattr(obj, "world_pos", None)
            if world_pos is None:
                continue

            # Convert world position to screen X relative to the player (center)
            screen_x = int(SCREEN_CENTER_X + (world_pos - world_x) * pixels_per_meter)

            # Set the sprite rect x so subsequent code sees the correct position
            obj.rect.x = screen_x

            # Simple culling: only draw if it overlaps the screen horizontally
            if -obj.rect.width <= screen_x <= SCREEN_WIDTH:
                pygame.draw.rect(screen, (255, 0, 255), obj.rect, 2)
                screen.blit(obj.image_scaled, obj.rect)


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
    print(player.pixels_per_meter, player.target_pixels_per_meter)
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

    # Update height in pixels for zoom
    current_height_pixels = player.segment_count * (player.pixels_per_meter * PLANT_SEGMENT_HEIGHT) # pixels

    # Update pixels_per_meter based on current height
    player.target_pixels_per_meter = (GROUND_Y - MAX_PLANT_Y) / (player.segment_count * PLANT_SEGMENT_HEIGHT)
    player.pixels_per_meter = incremental_add(player.pixels_per_meter, player.target_pixels_per_meter)

    player.update()
    player.update_scale(player.pixels_per_meter)

    # Update object spawning
    object_manager.update_spawning(world_x, player.pixels_per_meter)

    # Draw background
    screen.fill((169, 173, 159)) # day sky
    screen.blit(sky_img, (0, 0))
    screen.blit(ground_img, (0, GROUND_Y))

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