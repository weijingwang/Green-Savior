import pygame
from config import *

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 28)
    
    def clear(self):
        """Clear screen with background color"""
        self.screen.fill(BG_COLOR)
    
    def draw_ground(self, camera):
        """Draw the ground plane"""
        ground_screen_x, ground_screen_y = camera.world_to_screen(-WIDTH * 2, 100)
        if 0 < ground_screen_y < HEIGHT:
            pygame.draw.rect(self.screen, (20, 20, 50), 
                           (0, ground_screen_y, WIDTH, HEIGHT - ground_screen_y))
    
    def draw_building(self, building, camera):
        """Draw a single building with windows"""
        screen_x, screen_y = camera.world_to_screen(building.x, building.y)
        screen_w = building.width * camera.zoom_factor
        screen_h = building.height * camera.zoom_factor
        
        # Only draw if visible
        if not (screen_x + screen_w > 0 and screen_x < WIDTH and 
                screen_y + screen_h > 0 and screen_y < HEIGHT):
            return
        
        # Draw building
        rect = pygame.Rect(screen_x, screen_y, screen_w, screen_h)
        pygame.draw.rect(self.screen, BUILDING_COLOR, rect)
        
        # Draw windows
        window_w = building.window_w * camera.zoom_factor
        window_h = building.window_h * camera.zoom_factor
        spacing_x = building.spacing_x * camera.zoom_factor
        spacing_y = building.spacing_y * camera.zoom_factor
        
        for r in range(building.rows):
            for c in range(building.cols):
                if building.windows[r][c]:
                    wx = screen_x + 10 * camera.zoom_factor + c * (window_w + spacing_x)
                    wy = screen_y + 10 * camera.zoom_factor + r * (window_h + spacing_y)
                    
                    if (wx + window_w < screen_x + screen_w and 
                        wy + window_h < screen_y + screen_h and
                        window_w > 1 and window_h > 1):
                        pygame.draw.rect(self.screen, WINDOW_COLOR, 
                                       (wx, wy, window_w, window_h))
    
    def draw_red_spot(self, spot, camera):
        """Draw a red spot"""
        screen_x, screen_y = camera.world_to_screen(spot.x, spot.y)
        screen_radius = max(1, int(spot.radius * camera.zoom_factor))
        
        if (screen_x + screen_radius > 0 and screen_x - screen_radius < WIDTH and
            screen_y + screen_radius > 0 and screen_y - screen_radius < HEIGHT):
            pygame.draw.circle(self.screen, SPOT_COLOR, 
                             (int(screen_x), int(screen_y)), screen_radius)
    
    def draw_character(self, character, torso_x, torso_y, camera):
        """Draw the character with optimized neck rendering"""
        # Draw torso
        torso_screen_x, torso_screen_y = camera.world_to_screen(torso_x, torso_y)
        torso_radius = max(1, int(TORSO_RADIUS * camera.zoom_factor))
        pygame.draw.circle(self.screen, TORSO_COLOR, 
                         (int(torso_screen_x), int(torso_screen_y)), torso_radius)
        
        # Get visible neck segments with LOD
        visible_segments = self._get_visible_neck_segments(character, camera)
        
        # Draw neck segments
        for i, pos in visible_segments:
            screen_x, screen_y = camera.world_to_screen(pos[0], pos[1])
            
            if i == len(character.neck_positions) - 1:
                # Draw head
                head_radius = max(1, int(HEAD_RADIUS * camera.zoom_factor))
                if self._should_draw_segment(screen_x, screen_y, head_radius):
                    pygame.draw.circle(self.screen, HEAD_COLOR, 
                                     (int(screen_x), int(screen_y)), head_radius)
            else:
                # Draw neck segment
                base_radius = NECK_RADIUS * (1 - i / max(1, len(character.neck_positions)) * 0.4)
                radius = max(1, int(base_radius * camera.zoom_factor))
                
                # Dynamic thickness for extreme zooms
                if camera.zoom_factor < 0.1:
                    radius = max(radius, 4)
                elif camera.zoom_factor < 0.05:
                    radius = max(radius, 6)
                elif camera.zoom_factor < 0.02:
                    radius = max(radius, 8)
                
                if self._should_draw_segment(screen_x, screen_y, radius):
                    pygame.draw.circle(self.screen, NECK_COLOR, 
                                     (int(screen_x), int(screen_y)), radius)
    
    def _get_visible_neck_segments(self, character, camera):
        """Get optimized list of neck segments to draw"""
        lod = camera.get_current_lod()
        total_segments = len(character.neck_positions)
        max_segments = lod["segments"]
        
        if max_segments == -1 or total_segments <= max_segments:
            return list(enumerate(character.neck_positions))
        
        # Ultra-low detail: key segments only
        if max_segments <= 8:
            indices = [0]  # First segment
            if max_segments > 2:
                for i in range(1, max_segments - 1):
                    idx = int((i / (max_segments - 1)) * (total_segments - 1))
                    indices.append(idx)
            indices.append(total_segments - 1)  # Head
            return [(i, character.neck_positions[i]) for i in indices]
        
        # Regular LOD: skip segments mathematically
        skip_ratio = max(1, total_segments // max_segments)
        visible_segments = []
        
        for i in range(0, total_segments, skip_ratio):
            visible_segments.append((i, character.neck_positions[i]))
        
        # Always include head
        if visible_segments[-1][0] != total_segments - 1:
            visible_segments.append((total_segments - 1, character.neck_positions[-1]))
        
        return visible_segments
    
    def _should_draw_segment(self, screen_x, screen_y, radius):
        """Check if segment should be drawn based on size and bounds"""
        if radius < SEGMENT_CULL_RADIUS:
            return False
        
        margin = radius + 10
        return not (screen_x < -margin or screen_x > WIDTH + margin or 
                   screen_y < -margin or screen_y > HEIGHT + margin)
    
    def draw_ui(self, character, camera):
        """Draw UI information"""
        lod = camera.get_current_lod()
        visible_count = len(self._get_visible_neck_segments(character, camera))
        
        info_texts = [
            f"Zoom: {camera.zoom_factor:.3f}x",
            f"Total Segments: {len(character.neck_positions)}",
            f"Visible: {visible_count}",
            f"LOD: {lod['name']}",
            f"Physics Skip: {lod['physics_skip']}"
        ]
        
        y_offset = 10
        for text in info_texts:
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25