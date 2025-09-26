# camera.py - Camera system with ground always at fixed screen position
from constants import *
from utils import world_to_screen_x

class Camera:
    """Handles camera position and zoom with ground always at screen Y = GROUND_Y"""
    
    def __init__(self):
        self.x = 0  # Camera world X position meters
        self.y = 0  # Camera world Y position meters
        # self.zoom = 1.0
        # self.target_zoom = 1.0
        self.zoom_smoothing = 0.05
        
        # Initial zoom based on starting segments
        self.pixel_per_meter = INITIAL_PIXELS_PER_METER
        self.old_pixel_per_meter = self.pixel_per_meter

   
    def set_zoom_for_segment_count(self, segment_count):
        """Calculate zoom to fit plant with headroom"""
        # Calculate maximum plant height
        max_plant_height = segment_count * PLANT_SEGMENT_HEIGHT
        
        # Total vertical space needed from ground level up
        # Add headroom for better gameplay visibility
        world_height_needed = max_plant_height * 1.2  # 20% headroom
        
        # Available screen space above ground (from ground up to MAX_PLANT_Y)
        available_screen_height = GROUND_Y - MAX_PLANT_Y
        
        # Calculate zoom to fit this on screen
        required_zoom = available_screen_height / world_height_needed
        
        # Set minimum zoom to prevent it from getting too small
        min_zoom = 0.1
        self.target_zoom = max(min_zoom, required_zoom)
    
    def update_zoom_smoothly(self):
        """Smoothly interpolate zoom towards target"""
        zoom_diff = self.target_zoom - self.zoom
        self.zoom += zoom_diff * self.zoom_smoothing
        
        # Snap to target if very close
        if abs(zoom_diff) < 0.0001:
            self.zoom = self.target_zoom
    
    def get_pixels_per_meter(self):
        """Get current pixels per meter based on zoom"""
        return self.zoom
    
    def get_scale_factor_for_player(self):
        """Get scale factor for player objects that should stay at screen center"""
        # This returns the zoom level for scaling player graphics, but not position
        return self.zoom
    
    def update(self):
        """Update camera each frame"""
        self.update_zoom_smoothly()