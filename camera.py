# camera.py - Fixed camera system with ground always at fixed screen position
from config import WIDTH, HEIGHT, MIN_ZOOM, SEGMENT_LENGTH, TORSO_RADIUS, HEAD_RADIUS, GROUND_SCREEN_Y

class Camera:
    """Handles camera position and zoom with ground always at screen Y = 600"""
    
    def __init__(self):
        self.x = 0
        self.y = 0  # Camera world Y position
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.zoom_smoothing = 0.05
        
        # Fixed ground world Y coordinate - never changes
        self.ground_world_y = 0
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates with fixed ground"""
        screen_x = (world_x - self.x) * self.zoom + WIDTH // 2
        # Fixed ground positioning: ground_world_y always maps to GROUND_SCREEN_Y
        screen_y = (world_y - self.ground_world_y) * self.zoom + GROUND_SCREEN_Y
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - WIDTH // 2) / self.zoom + self.x
        world_y = (screen_y - GROUND_SCREEN_Y) / self.zoom + self.ground_world_y
        return world_x, world_y
    
    def follow_target(self, target_x, target_y):
        """Update camera to follow target position - only follow horizontally"""
        self.x = target_x
        # Don't change ground_world_y - it stays constant at 0
        # Camera Y position stays at 0 to keep ground at screen Y = 600
        self.y = 0
    
    def set_zoom_for_segment_count(self, neck_segment_count):
        """Calculate zoom to fit neck with headroom"""
        # Calculate maximum neck extension upward from torso
        max_neck_length = neck_segment_count * SEGMENT_LENGTH
        
        # Total vertical space needed from ground level up
        # Character torso center is at ground level (world Y = 0)
        # Neck extends max_neck_length above torso center
        # Head adds HEAD_RADIUS above that
        total_height_above_ground = max_neck_length + HEAD_RADIUS
        
        # Add generous headroom (2x) for better gameplay visibility
        world_height_needed = total_height_above_ground * 2.0
        
        # Available screen space above ground (from ground at Y=600 up to top)
        available_screen_height = GROUND_SCREEN_Y  # 600 pixels
        
        # Calculate zoom to fit this on screen
        required_zoom = available_screen_height / world_height_needed
        
        # Clamp to minimum zoom
        self.target_zoom = max(MIN_ZOOM, required_zoom)
    
    def update_zoom_smoothly(self):
        """Smoothly interpolate zoom towards target"""
        zoom_diff = self.target_zoom - self.zoom
        self.zoom += zoom_diff * self.zoom_smoothing
        
        # Snap to target if very close
        if abs(zoom_diff) < 0.0001:
            self.zoom = self.target_zoom