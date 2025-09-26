import pygame
from constants import HEIGHT_TO_REMOVE_OBJECT



class GameObject(pygame.sprite.Sprite):
    def __init__(self, image_path, height_meters, pixels_per_meter, ground_y):
        """
        GameObject class as a pygame Sprite.
        """
        super().__init__()
        self.image_orig = pygame.image.load(image_path).convert_alpha()
        self.orig_w, self.orig_h = self.image_orig.get_size()
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

