from config import WIDTH, HEIGHT, ZOOM_SPEED, LOD_LEVELS

class Camera:
    def __init__(self):
        self.zoom_factor = 1.0
        self.x = 0
        self.y = 0
    
    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (x - self.x) * self.zoom_factor + WIDTH // 2
        screen_y = (y - self.y) * self.zoom_factor + HEIGHT // 2
        return screen_x, screen_y
    
    def screen_to_world(self, x, y):
        """Convert screen coordinates to world coordinates"""
        world_x = (x - WIDTH // 2) / self.zoom_factor + self.x
        world_y = (y - HEIGHT // 2) / self.zoom_factor + self.y
        return world_x, world_y
    
    def update_position(self, target_x, target_y):
        """Update camera position to follow target"""
        self.x = target_x
        self.y = target_y
    
    def zoom_out(self):
        """Gradually zoom out"""
        self.zoom_factor = max(0.0005, self.zoom_factor - ZOOM_SPEED)  # Much smaller minimum for skyscraper scale
    
    def get_current_lod(self):
        """Get current LOD settings based on zoom level"""
        for threshold in sorted(LOD_LEVELS.keys(), reverse=True):
            if self.zoom_factor >= threshold:
                return LOD_LEVELS[threshold]
        return LOD_LEVELS[0.01]