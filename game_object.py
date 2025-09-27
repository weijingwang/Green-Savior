import pygame, random, os
from constants import *
from utils import world_to_screen_x, incremental_add


class ObjectManager:
    def __init__(self):
        self.objects = pygame.sprite.Group()
        self.rightmost_spawned = 0.0
        self.leftmost_spawned = 0.0
        self.object_configs = [
            ('mouse', MOUSE_HEIGHT, 0.4),
            ('car', CAR_HEIGHT, 0.3),
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


class GameObject(pygame.sprite.Sprite):
    def __init__(self, image_path, height_meters, pixels_per_meter, ground_y):
        """
        GameObject class as a pygame Sprite.
        """
        super().__init__()
        self.image_orig = pygame.image.load(image_path).convert_alpha()
        self.orig_w, self.orig_h = self.image_orig.get_size() # pixels
        self.height_meters = height_meters
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        self.image_scaled = None
        self.rect = None
        self.alpha = 255  # For fading
        self.to_kill = False  # Flag to remove sprite
        self.update_scale(self.pixels_per_meter, self.ground_y)

    def update_scale(self, pixels_per_meter, ground_y):
        """Scale image based on height in meters."""
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        current_height_pixels = self.height_meters * pixels_per_meter
        scale_factor = current_height_pixels / self.orig_h
        new_w = int(self.orig_w * scale_factor)
        new_h = int(self.orig_h * scale_factor)
        
        # If scaled height is too small, mark for fading/removal
        if new_h < HEIGHT_TO_REMOVE_OBJECT:
            self.to_kill = True
            self.fade_out()
            return
        
        self.image_scaled = pygame.transform.scale(self.image_orig, (new_w, new_h))
        self.image_scaled.set_alpha(self.alpha)
        self.rect = self.image_scaled.get_rect()
        self.rect.bottom = ground_y

    def fade_out(self, fade_speed=5):
        """Gradually fade out the sprite."""
        if self.alpha > 0:
            self.alpha -= fade_speed
            self.alpha = max(self.alpha, 0)
            if self.image_scaled:
                self.image_scaled.set_alpha(self.alpha)
        else:
            self.kill()  # Remove from all sprite groups

    def update(self):
        """Call every frame to update the sprite."""
        if self.to_kill:
            self.fade_out()

    def draw(self, screen, x_position):
        """Draw the sprite at a given x-position."""
        if self.rect and self.image_scaled:
            self.rect.x = x_position
            pygame.draw.rect(screen, (255, 0, 255), self.rect, 2)  # 2 = line thickness
            screen.blit(self.image_scaled, self.rect)
