# renderer.py - Updated rendering system with proper ellipse segments
import pygame
import math
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
        ground_x, ground_y = camera.world_to_screen(-WIDTH * 2, GROUND_SCREEN_Y)
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
        
        # Draw neck with LOD optimization and segment types
        self._draw_neck_optimized(character, camera, performance_manager)
    
    def _draw_torso(self, torso_pos, camera):
        """Draw character torso"""
        screen_x, screen_y = camera.world_to_screen(torso_pos[0], torso_pos[1])
        radius = max(1, int(TORSO_RADIUS * camera.zoom))
        
        pygame.draw.circle(self.screen, TORSO_COLOR, 
                         (int(screen_x), int(screen_y)), radius)
    
    def _draw_neck_optimized(self, character, camera, performance_manager):
        """Draw neck segments with LOD optimization and proper ellipse handling"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        segments = character.neck_segments
        segments_to_draw = self._get_segments_to_draw(segments, lod)
        
        for i, segment in segments_to_draw:
            if i == len(segments) - 1:
                # Draw head
                self._draw_head(segment, camera)
            else:
                # Draw neck segment based on type
                if segment.type == 'ellipse':
                    self._draw_ellipse_segment(segment, camera)
                else:
                    self._draw_regular_segment(segment, camera, i, len(segments))
    
    def _draw_head(self, segment, camera):
        """Draw the head segment"""
        screen_x, screen_y = camera.world_to_screen(segment.position[0], segment.position[1])
        head_radius = max(1, int(HEAD_RADIUS * camera.zoom))
        if self._is_circle_visible(screen_x, screen_y, head_radius):
            pygame.draw.circle(self.screen, HEAD_COLOR, 
                             (int(screen_x), int(screen_y)), head_radius)
    
    def _draw_regular_segment(self, segment, camera, segment_index, total_segments):
        """Draw a regular circular neck segment"""
        screen_x, screen_y = camera.world_to_screen(segment.position[0], segment.position[1])
        
        # Taper the neck (smaller towards the head)
        taper_factor = 1 - segment_index / max(1, total_segments) * 0.4
        radius = max(1, int(NECK_RADIUS * camera.zoom * taper_factor))
        
        # Boost radius for extreme zooms
        if camera.zoom < 0.02:
            radius = max(radius, 8)
        
        if self._is_circle_visible(screen_x, screen_y, radius):
            pygame.draw.circle(self.screen, NECK_COLOR, 
                             (int(screen_x), int(screen_y)), radius)
    
    def _draw_ellipse_segment(self, segment, camera):
        """Draw an elliptical consolidated segment that connects properly in the chain"""
        # Get the connection point position (where this segment connects in the physics chain)
        screen_x, screen_y = camera.world_to_screen(segment.position[0], segment.position[1])
        
        # Calculate dimensions based on actual chain length
        base_radius = NECK_RADIUS * camera.zoom
        
        # Width increases with consolidation level for visual distinction
        width_multiplier = 1.4 + 0.3 * segment.consolidation_level
        width = max(6, int(base_radius * width_multiplier))
        
        # Height represents the actual chain length this segment covers
        if hasattr(segment, 'chain_length'):
            actual_length = segment.chain_length
        else:
            actual_length = segment.height_multiplier * SEGMENT_LENGTH
            
        # Make the ellipse tall enough to visually represent the space it fills
        height = max(12, int(actual_length * camera.zoom * 0.8))  # 80% of actual length for visual clarity
        
        # Boost size for extreme zooms
        if camera.zoom < 0.02:
            width = max(width, 10 + segment.consolidation_level * 3)
            height = max(height, int(actual_length * 0.2))  # Ensure visibility at extreme zoom
        
        # Don't draw if too small or off screen
        if width < 2 or height < 2:
            return
            
        margin = max(width, height) + 10
        if (screen_x < -margin or screen_x > WIDTH + margin or 
            screen_y < -margin or screen_y > HEIGHT + margin):
            return
        
        # Position ellipse based on whether this is the bottom segment
        if hasattr(segment, 'is_bottom_segment') and segment.is_bottom_segment:
            # For bottom segments, the ellipse extends DOWNWARD from the physics connection point
            # The physics connection point is at the top of the ellipse
            ellipse_rect = pygame.Rect(
                int(screen_x - width/2), 
                int(screen_y),  # Top of ellipse at connection point
                width, 
                height
            )
        else:
            # For other segments, the ellipse extends DOWNWARD from the physics connection point
            # The physics connection point is at the top of the ellipse
            ellipse_rect = pygame.Rect(
                int(screen_x - width/2), 
                int(screen_y - base_radius * camera.zoom),  # Top of ellipse at connection point
                width, 
                height
            )
        
        # Get color based on consolidation level
        color = self._get_ellipse_color(segment.consolidation_level)
        pygame.draw.ellipse(self.screen, color, ellipse_rect)

    
    def _get_ellipse_color(self, consolidation_level):
        """Get color for ellipse based on consolidation level"""
        return (
            min(255, NECK_COLOR[0] + 30 + consolidation_level * 20),
            min(255, NECK_COLOR[1] + 15 + consolidation_level * 10), 
            max(0, NECK_COLOR[2] - consolidation_level * 15)
        )
    
    def _get_segments_to_draw(self, segments, lod):
        """Get optimized list of segments to draw based on LOD"""
        max_segments = lod['max_segments']
        total_segments = len(segments)
        
        if max_segments == -1 or total_segments <= max_segments:
            return list(enumerate(segments))
        
        # Sample segments evenly
        segments_to_draw = []
        step = total_segments / max_segments
        
        for i in range(max_segments):
            segment_index = int(i * step)
            if segment_index < len(segments):
                segments_to_draw.append((segment_index, segments[segment_index]))
        
        # Always include the head
        if segments_to_draw and segments_to_draw[-1][0] != total_segments - 1:
            segments_to_draw.append((total_segments - 1, segments[-1]))
        
        return segments_to_draw
    
    def draw_ui(self, character, camera, performance_manager):
        """Draw UI information with consolidation stats"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        
        # Get consolidation statistics
        consolidation_stats = character.get_consolidation_stats()
        display_segments = character.get_neck_segment_count()
        actual_length = character.get_total_neck_length()
        equivalent_segments = character.get_neck_segment_count_for_zoom()
        
        info_lines = [
            f"Zoom: {camera.zoom:.3f}x",
            f"Display: {display_segments} segments",
            f"Actual Length: {equivalent_segments} segments",
            f"LOD: {lod['name']}",
            f"Physics Skip: {lod['physics_skip']}",
            ""
        ]
        
        # Add consolidation stats
        for stat_name, value in consolidation_stats.items():
            if stat_name != "Total Length":  # We show this above now
                info_lines.append(f"{stat_name}: {value}")
        
        info_lines.extend(["", "Hold SPACE to grow neck"])
        
        y_pos = 10
        for line in info_lines:
            if line:  # Skip empty lines for spacing
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