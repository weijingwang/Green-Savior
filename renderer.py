import pygame
from config import *

class Renderer:
    """Handles all rendering operations"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 28)
    
    def clear_screen(self):
        """Clear screen with background color"""
        self.screen.fill(BG_COLOR)
    
    def draw_ground(self, camera):
        """Draw the ground plane"""
        ground_x, ground_y = camera.world_to_screen(-WIDTH * 2, GROUND_Y)
        if 0 < ground_y < HEIGHT:
            pygame.draw.rect(self.screen, (20, 20, 50), 
                           (0, ground_y, WIDTH, HEIGHT - ground_y))
    
    def draw_building(self, building, camera):
        """Draw a building with windows"""
        screen_x, screen_y = camera.world_to_screen(building.x, building.y)
        screen_w = building.width * camera.zoom
        screen_h = building.height * camera.zoom
        
        # Skip if not visible
        if not self._is_rect_visible(screen_x, screen_y, screen_w, screen_h):
            return
        
        # Draw building body
        rect = pygame.Rect(screen_x, screen_y, screen_w, screen_h)
        pygame.draw.rect(self.screen, BUILDING_COLOR, rect)
        
        # Draw windows
        self._draw_building_windows(building, screen_x, screen_y, camera)
    
    def _draw_building_windows(self, building, screen_x, screen_y, camera):
        """Draw windows on a building"""
        windows = building.windows
        window_w = windows['window_w'] * camera.zoom
        window_h = windows['window_h'] * camera.zoom
        
        if window_w < 1 or window_h < 1:
            return
        
        for r in range(windows['rows']):
            for c in range(windows['cols']):
                if windows['pattern'][r][c]:
                    wx = screen_x + 10 * camera.zoom + c * (window_w * 1.5)
                    wy = screen_y + 10 * camera.zoom + r * (window_h * 1.5)
                    
                    pygame.draw.rect(self.screen, WINDOW_COLOR, 
                                   (wx, wy, window_w, window_h))
    
    def draw_spot(self, spot, camera):
        """Draw a collectible spot"""
        screen_x, screen_y = camera.world_to_screen(spot.x, spot.y)
        radius = max(1, int(spot.radius * camera.zoom))
        
        if self._is_circle_visible(screen_x, screen_y, radius):
            pygame.draw.circle(self.screen, SPOT_COLOR, 
                             (int(screen_x), int(screen_y)), radius)
    
    def draw_character(self, character, camera, performance_manager):
        """Draw the character with optimized neck rendering"""
        torso_pos = character._get_torso_position()
        
        # Draw torso
        self._draw_torso(torso_pos, camera)
        
        # Draw neck with LOD optimization
        self._draw_neck_optimized(character, camera, performance_manager)
    
    def _draw_torso(self, torso_pos, camera):
        """Draw character torso"""
        screen_x, screen_y = camera.world_to_screen(torso_pos[0], torso_pos[1])
        radius = max(1, int(TORSO_RADIUS * camera.zoom))
        
        pygame.draw.circle(self.screen, TORSO_COLOR, 
                         (int(screen_x), int(screen_y)), radius)
    
    def _draw_neck_optimized(self, character, camera, performance_manager):
        """Draw neck segments with LOD optimization"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        segments_to_draw = self._get_segments_to_draw(character.neck_segments, lod)
        
        for i, pos in segments_to_draw:
            screen_x, screen_y = camera.world_to_screen(pos[0], pos[1])
            
            if i == len(character.neck_segments) - 1:
                # Draw head
                radius = max(1, int(HEAD_RADIUS * camera.zoom))
                if self._is_circle_visible(screen_x, screen_y, radius):
                    pygame.draw.circle(self.screen, HEAD_COLOR, 
                                     (int(screen_x), int(screen_y)), radius)
            else:
                # Draw neck segment
                base_radius = NECK_RADIUS * (1 - i / max(1, len(character.neck_segments)) * 0.4)
                radius = max(1, int(base_radius * camera.zoom))
                
                # Boost radius for extreme zooms
                if camera.zoom < 0.02:
                    radius = max(radius, 8)
                
                if self._is_circle_visible(screen_x, screen_y, radius):
                    pygame.draw.circle(self.screen, NECK_COLOR, 
                                     (int(screen_x), int(screen_y)), radius)
    
    def _get_segments_to_draw(self, all_segments, lod):
        """Get optimized list of segments to draw based on LOD"""
        max_segments = lod['max_segments']
        total_segments = len(all_segments)
        
        if max_segments == -1 or total_segments <= max_segments:
            return list(enumerate(all_segments))
        
        # Sample segments evenly
        segments_to_draw = []
        step = total_segments / max_segments
        
        for i in range(max_segments):
            segment_index = int(i * step)
            segments_to_draw.append((segment_index, all_segments[segment_index]))
        
        # Always include the head
        if segments_to_draw[-1][0] != total_segments - 1:
            segments_to_draw.append((total_segments - 1, all_segments[-1]))
        
        return segments_to_draw
    
    def draw_ui(self, character, camera, performance_manager):
        """Draw UI information"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        
        info_lines = [
            f"Zoom: {camera.zoom:.3f}x",
            f"Segments: {len(character.neck_segments)}",
            f"LOD: {lod['name']}",
            f"Physics Skip: {lod['physics_skip']}"
        ]
        
        y_pos = 10
        for line in info_lines:
            text_surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, y_pos))
            y_pos += 25
    
    def _is_rect_visible(self, x, y, w, h):
        """Check if rectangle is visible on screen"""
        return not (x + w < 0 or x > WIDTH or y + h < 0 or y > HEIGHT)
    
    def _is_circle_visible(self, x, y, radius):
        """Check if circle is visible on screen"""
        margin = radius + 10
        return not (x < -margin or x > WIDTH + margin or 
                   y < -margin or y > HEIGHT + margin)
