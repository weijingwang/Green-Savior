import pygame

class GameObject:
    def __init__(self, image_path, height_meters, pixels_per_meter, ground_y):
        """
        GameObject class. Takes in image_path, height in meters (Find in constants.py).
        Pixels_per_meter is calculated like plant neck height drawn in pixels / plant neck height meters
        Ground_y is in constants.py and may update based on camera zoom.
        """
        self.image_orig = pygame.image.load(image_path).convert_alpha()
        self.orig_w, self.orig_h = self.image_orig.get_size()
        self.height_meters = height_meters
        self.pixels_per_meter = pixels_per_meter
        self.ground_y = ground_y
        self.image_scaled = None
        self.rect = None
        self.update_scale(self.pixels_per_meter, self.ground_y)

    def update_scale(self, pixels_per_meter, ground_y):
        """Scale image based on plant neck height ratio provided (pixels_per_meter)."""
        current_height_pixels = self.height_meters * pixels_per_meter
        scale_factor = current_height_pixels / self.orig_h
        new_w = int(self.orig_w * scale_factor)
        new_h = int(self.orig_h * scale_factor)
        self.image_scaled = pygame.transform.scale(self.image_orig, (new_w, new_h))
        self.rect = self.image_scaled.get_rect()
        # Align bottom to ground
        self.rect.bottom = ground_y

        # Debug info
        # print(current_height_pixels, self.height_meters, self.orig_w, new_w, scale_factor)

    def draw(self, screen, x_position):
        """Draw the object at a given x-position."""
        self.rect.x = x_position
        screen.blit(self.image_scaled, self.rect)
