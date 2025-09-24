from config import WIDTH, HEIGHT, ZOOM_SPEED, MIN_ZOOM

class Camera:
    """Handles camera position and zoom with world-screen coordinate conversion"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
    
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
    
    def zoom_out(self):
        """Gradually zoom out when character grows"""
        self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_SPEED)
