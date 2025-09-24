# renderer.py - Streamlined rendering system with optimized performance
import pygame
import math
from config import *

class Renderer:
    """Optimized renderer with consolidated drawing methods"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 28)
        
        # Cache frequently used values
        self._screen_bounds = (-50, -50, WIDTH + 50, HEIGHT + 50)  # With margin
        self._ellipse_colors = {}  # Cache colors by consolidation level
    
    def clear_screen(self):
        """Clear screen with background color"""
        self.screen.fill(BG_COLOR)
    
    def draw_ground(self, camera):
        """Draw the ground plane"""
        _, ground_y = camera.world_to_screen(0, GROUND_SCREEN_Y)
        if 0 < ground_y < HEIGHT:
            pygame.draw.rect(self.screen, (20, 20, 50), 
                           (0, ground_y, WIDTH, HEIGHT - ground_y))
    
    def draw_building(self, building, camera):
        """Draw building with optimized window rendering"""
        screen_x, screen_y = camera.world_to_screen(building.x, building.y)
        screen_w = building.width * camera.zoom
        screen_h = building.height * camera.zoom
        
        # Quick visibility check
        if not self._is_visible(screen_x, screen_y, screen_w, screen_h):
            return
        
        # Draw building body
        rect = pygame.Rect(screen_x, screen_y, screen_w, screen_h)
        pygame.draw.rect(self.screen, BUILDING_COLOR, rect)
        
        # Draw windows with smart scaling
        self._draw_windows(building, screen_x, screen_y, camera)
    
    def _draw_windows(self, building, screen_x, screen_y, camera):
        """Optimized window drawing with smart density reduction"""
        windows = building.windows
        window_w = max(1, windows['window_w'] * camera.zoom)
        window_h = max(1, windows['window_h'] * camera.zoom)
        
        # Smart skip factor based on zoom - fewer windows at extreme zoom
        skip_factor = max(1, int(1 / max(camera.zoom, 0.001) / 50))
        
        for r in range(0, windows['rows'], skip_factor):
            for c in range(0, windows['cols'], skip_factor):
                if windows['pattern'][r][c]:
                    wx = screen_x + 10 * camera.zoom + c * (window_w * 1.5)
                    wy = screen_y + 10 * camera.zoom + r * (window_h * 1.5)
                    
                    pygame.draw.rect(self.screen, WINDOW_COLOR, 
                                   (int(wx), int(wy), int(window_w), int(window_h)))
    
    def draw_spot(self, spot, camera):
        """Draw collectible spot"""
        screen_x, screen_y = camera.world_to_screen(spot.x, spot.y)
        radius = max(1, int(spot.radius * camera.zoom))
        
        if self._is_point_visible(screen_x, screen_y, radius):
            pygame.draw.circle(self.screen, SPOT_COLOR, 
                             (int(screen_x), int(screen_y)), radius)
    
    def draw_character(self, character, camera, performance_manager):
        """Draw character with optimized neck rendering"""
        torso_pos = character._cached_torso_pos or character._get_torso_position()
        
        # Draw torso
        screen_x, screen_y = camera.world_to_screen(torso_pos[0], torso_pos[1])
        radius = max(1, int(TORSO_RADIUS * camera.zoom))
        pygame.draw.circle(self.screen, TORSO_COLOR, (int(screen_x), int(screen_y)), radius)
        
        # Draw neck with simplified LOD
        self._draw_neck_smart(character, camera, performance_manager)
    
    def _draw_neck_smart(self, character, camera, performance_manager):
        """Streamlined neck drawing with smart level filtering"""
        segments = character.neck_segments
        if not segments:
            return
        
        # Get LOD settings
        lod = performance_manager.get_lod_settings(camera.zoom)
        max_segments = lod['max_segments']
        
        # Smart filtering: Show top 3 consolidation levels only
        level_counts = {}
        for seg in segments[:-1]:  # Exclude head
            level = seg.consolidation_level if seg.type == 'ellipse' else 0
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Get top 3 levels by count (most numerous levels)
        top_levels = sorted(level_counts.keys(), key=lambda x: level_counts[x], reverse=True)[:3]
        
        # Filter and sample segments
        filtered_segments = []
        for i, seg in enumerate(segments):
            is_head = (i == len(segments) - 1)
            seg_level = seg.consolidation_level if seg.type == 'ellipse' else 0
            
            if is_head or seg_level in top_levels:
                filtered_segments.append((i, seg, is_head))
        
        # Apply max_segments limit if needed
        if max_segments != -1 and len(filtered_segments) > max_segments:
            # Keep head and sample the rest
            head_item = filtered_segments[-1] if filtered_segments[-1][2] else None
            body_items = [item for item in filtered_segments if not item[2]]
            
            # Sample body segments
            step = len(body_items) / (max_segments - (1 if head_item else 0))
            sampled_body = []
            for i in range(max_segments - (1 if head_item else 0)):
                idx = int(i * step)
                if idx < len(body_items):
                    sampled_body.append(body_items[idx])
            
            filtered_segments = sampled_body + ([head_item] if head_item else [])
        
        # Draw filtered segments
        for original_i, segment, is_head in filtered_segments:
            if is_head:
                self._draw_head(segment, camera)
            else:
                self._draw_segment(segment, camera, original_i, len(segments))
    
    def _draw_segment(self, segment, camera, segment_index, total_segments):
        """Draw neck segment - regular or ellipse"""
        screen_x, screen_y = camera.world_to_screen(segment.position[0], segment.position[1])
        
        if segment.type == 'ellipse':
            self._draw_ellipse_segment(segment, screen_x, screen_y, camera)
        else:
            # Regular segment with taper
            taper = 1 - segment_index / max(1, total_segments) * 0.4
            radius = max(1, int(NECK_RADIUS * camera.zoom * taper))
            
            if self._is_point_visible(screen_x, screen_y, radius):
                pygame.draw.circle(self.screen, NECK_COLOR, 
                                 (int(screen_x), int(screen_y)), radius)
    
    def _draw_ellipse_segment(self, segment, screen_x, screen_y, camera):
        """Draw ellipse segment with smart scaling"""
        # Calculate dimensions
        base_radius = NECK_RADIUS * camera.zoom
        width_mult = 1.4 + 0.3 * segment.consolidation_level
        width = max(2, int(base_radius * width_mult))
        
        # Height from actual chain length
        actual_length = getattr(segment, 'chain_length', segment.height_multiplier * SEGMENT_LENGTH)
        height = max(3, int(actual_length * camera.zoom * 0.8))
        
        # Smart scaling for extreme zoom
        if camera.zoom < 0.05:
            scale_factor = 1.0 + (0.05 - camera.zoom) / 0.049 * 2.0
            width = max(width, int(width * scale_factor))
            height = max(height, int(height * scale_factor * 0.5))
        
        # Skip if too small or not visible
        margin = max(width, height) + 20
        if (width < 1 or height < 1 or 
            screen_x < -margin or screen_x > WIDTH + margin or 
            screen_y < -margin or screen_y > HEIGHT + margin):
            return
        
        # Position ellipse (bottom segments extend downward)
        is_bottom = getattr(segment, 'is_bottom_segment', False)
        if is_bottom:
            ellipse_rect = pygame.Rect(int(screen_x - width/2), int(screen_y), width, height)
        else:
            ellipse_rect = pygame.Rect(int(screen_x - width/2), int(screen_y - height/2), width, height)
        
        # Draw ellipse with cached color
        color = self._get_cached_ellipse_color(segment.consolidation_level)
        pygame.draw.ellipse(self.screen, color, ellipse_rect)
    
    def _draw_head(self, segment, camera):
        """Draw head segment"""
        screen_x, screen_y = camera.world_to_screen(segment.position[0], segment.position[1])
        radius = max(1, int(HEAD_RADIUS * camera.zoom))
        
        if self._is_point_visible(screen_x, screen_y, radius):
            pygame.draw.circle(self.screen, HEAD_COLOR, 
                             (int(screen_x), int(screen_y)), radius)
    
    def _get_cached_ellipse_color(self, level):
        """Get cached ellipse color by consolidation level"""
        if level not in self._ellipse_colors:
            self._ellipse_colors[level] = (
                min(255, NECK_COLOR[0] + 30 + level * 20),
                min(255, NECK_COLOR[1] + 15 + level * 10), 
                max(0, NECK_COLOR[2] - level * 15)
            )
        return self._ellipse_colors[level]
    
    def draw_ui(self, character, camera, performance_manager):
        """Streamlined UI with essential information"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        stats = character.get_consolidation_stats()
        
        # Get top levels for display
        level_counts = {}
        for seg in character.neck_segments[:-1]:
            level = seg.consolidation_level if seg.type == 'ellipse' else 0
            level_counts[level] = level_counts.get(level, 0) + 1
        
        top_levels = sorted(level_counts.keys(), key=lambda x: level_counts[x], reverse=True)[:3]
        
        # Essential info only
        info_lines = [
            f"Zoom: {camera.zoom:.3f}x",
            f"Segments: {character.get_neck_segment_count()}",
            f"Length: {character.get_neck_segment_count_for_zoom()}",
            f"LOD: {lod['name']} | Levels: {top_levels}",
            "",
            "Consolidation:",
        ]
        
        # Show consolidation stats with render status
        for stat_name, value in stats.items():
            if stat_name == "Total Length":
                continue
            
            # Mark rendered levels
            marker = ""
            if "L" in stat_name:
                try:
                    level = int(stat_name.split("L")[1].split()[0])
                    marker = " ✓" if level in top_levels else " ✗"
                except:
                    pass
            elif "Regular" in stat_name:
                marker = " ✓" if 0 in top_levels else " ✗"
            
            info_lines.append(f"  {stat_name}: {value}{marker}")
        
        info_lines.extend(["", "Hold SPACE to grow neck"])
        
        # Draw info
        y_pos = 10
        for line in info_lines:
            if line:
                text_surface = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(text_surface, (10, y_pos))
            y_pos += 22  # Tighter spacing
    
    def _is_visible(self, x, y, w, h):
        """Fast visibility check for rectangles"""
        return not (x + w < -50 or x > WIDTH + 50 or y + h < -50 or y > HEIGHT + 50)
    
    def _is_point_visible(self, x, y, radius):
        """Fast visibility check for circles"""
        margin = radius + 20
        return not (x < -margin or x > WIDTH + margin or y < -margin or y > HEIGHT + margin)