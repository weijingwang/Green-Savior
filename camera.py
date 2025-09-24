# camera.py - Simplified camera system
from config import WIDTH, HEIGHT, MIN_ZOOM, SEGMENT_LENGTH, TORSO_RADIUS, HEAD_RADIUS, GROUND_Y

class Camera:
    """Handles camera position and zoom with world-screen coordinate conversion"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.zoom_smoothing = 0.05  # How quickly zoom changes
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom + WIDTH // 2
        screen_y = (world_y - self.y) * self.zoom + HEIGHT // 2
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - WIDTH // 2) / self.zoom + self.x
        world_y = (screen_y - HEIGHT // 2) / self.zoom + self.y
        return world_x, world_y
    
    def follow_target(self, target_x, target_y):
        """Update camera to follow target position"""
        self.x = target_x
        self.y = target_y
    
    def set_zoom_for_segment_count(self, neck_segment_count):
        """Set zoom based purely on number of neck segments"""
        # Calculate maximum possible neck extension (straight up)
        max_neck_length = neck_segment_count * SEGMENT_LENGTH
        
        # Calculate world height needed to show:
        # - Ground level (GROUND_Y = 100)
        # - Character at ground level (torso at y=0, so torso bottom at TORSO_RADIUS above ground)
        # - Full neck extension upward from torso
        # - Head radius at the top
        # - Safety margin so neck never hits top edge
        
        character_base_y = 0  # Character's base position
        torso_top = character_base_y - TORSO_RADIUS
        max_head_y = torso_top - max_neck_length - HEAD_RADIUS
        
        # Total world height from ground to highest possible head position
        world_height_needed = GROUND_Y - max_head_y
        
        # Add 30% safety margin so neck never reaches screen edge
        safety_margin = 1.3
        world_height_needed *= safety_margin
        
        # Calculate zoom to fit this height on screen
        required_zoom = HEIGHT / world_height_needed
        
        # Clamp to minimum zoom
        self.target_zoom = max(MIN_ZOOM, required_zoom)
    
    def update_zoom_smoothly(self):
        """Smoothly interpolate zoom towards target"""
        zoom_diff = self.target_zoom - self.zoom
        self.zoom += zoom_diff * self.zoom_smoothing
        
        # Snap to target if very close to avoid endless tiny adjustments
        if abs(zoom_diff) < 0.0001:
            self.zoom = self.target_zoom