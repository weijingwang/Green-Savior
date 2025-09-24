# renderer.py - Enhanced rendering system with 2-point segment support
import pygame
import math
from config import *

class Renderer:
    """Enhanced renderer with 2-point segment rendering for proper connectivity"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 28)
        
        # Cache frequently used values
        self._screen_bounds = (-50, -50, WIDTH + 50, HEIGHT + 50)
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
        
        # Smart skip factor based on zoom
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
        """Draw character with enhanced 2-point neck rendering"""
        torso_pos = character._cached_torso_pos or character._get_torso_position()
        
        # Draw torso
        screen_x, screen_y = camera.world_to_screen(torso_pos[0], torso_pos[1])
        radius = max(1, int(TORSO_RADIUS * camera.zoom))
        pygame.draw.circle(self.screen, TORSO_COLOR, (int(screen_x), int(screen_y)), radius)
        
        # Draw neck with enhanced 2-point rendering
        self._draw_neck_2point(character, camera, performance_manager)
    
    def _draw_neck_2point(self, character, camera, performance_manager):
        """Enhanced neck drawing with proper 2-point connectivity"""
        segments = character.neck_segments
        if not segments:
            return
        
        # Get LOD settings
        lod = performance_manager.get_lod_settings(camera.zoom)
        max_segments = lod['max_segments']
        
        # Smart filtering for performance
        filtered_segments = self._filter_segments_for_lod(segments, max_segments)
        
        # Draw each filtered segment with proper connectivity
        for i, (original_i, segment, is_head) in enumerate(filtered_segments):
            if is_head:
                self._draw_head_2point(segment, camera)
            else:
                self._draw_segment_2point(segment, camera, original_i, len(segments))
    
    def _filter_segments_for_lod(self, segments, max_segments):
        """Filter segments for LOD while maintaining connectivity"""
        if max_segments == -1:
            # No limit - show all segments
            filtered = [(i, seg, i == len(segments)-1) for i, seg in enumerate(segments)]
        else:
            # Apply LOD filtering
            # Always keep head
            head = (len(segments)-1, segments[-1], True)
            body_segments = [(i, seg, False) for i, seg in enumerate(segments[:-1])]
            
            if len(body_segments) <= max_segments - 1:
                # Can show all body segments
                filtered = body_segments + [head]
            else:
                # Sample body segments to fit limit
                step = len(body_segments) / (max_segments - 1)
                sampled_body = []
                for i in range(max_segments - 1):
                    idx = int(i * step)
                    if idx < len(body_segments):
                        sampled_body.append(body_segments[idx])
                
                filtered = sampled_body + [head]
        
        return filtered
    
    def _draw_segment_2point(self, segment, camera, segment_index, total_segments):
        """Draw neck segment using 2-point system for proper connectivity"""
        # Convert world positions to screen positions
        start_screen = camera.world_to_screen(segment.start_pos[0], segment.start_pos[1])
        end_screen = camera.world_to_screen(segment.end_pos[0], segment.end_pos[1])
        
        # Quick visibility check
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        if segment.type == 'ellipse':
            self._draw_ellipse_segment_2point(segment, start_screen, end_screen, camera)
        else:
            self._draw_regular_segment_2point(segment, start_screen, end_screen, camera, segment_index, total_segments)
    
    def _draw_regular_segment_2point(self, segment, start_screen, end_screen, camera, segment_index, total_segments):
        """Draw regular segment as connected capsule"""
        # Calculate thickness with taper
        taper = 1 - segment_index / max(1, total_segments) * 0.4
        thickness = max(1, int(NECK_RADIUS * camera.zoom * taper))
        
        # Draw as thick line (capsule)
        if thickness > 1:
            self._draw_thick_line(start_screen, end_screen, thickness, NECK_COLOR)
        else:
            # Fallback to thin line
            pygame.draw.line(self.screen, NECK_COLOR, start_screen, end_screen, 1)
    
    def _draw_ellipse_segment_2point(self, segment, start_screen, end_screen, camera):
        """Draw ellipse segment as vertical joint along the segment direction"""
        # Calculate center, length, and angle
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        
        # Calculate screen-space dimensions - VERTICAL ellipse (joint-like)
        length_screen = math.hypot(end_screen[0] - start_screen[0], end_screen[1] - start_screen[1])
        
        # Height (perpendicular to segment) gets bigger with consolidation level - NOW VERTICAL
        height_mult = 1.4 + 0.3 * segment.consolidation_level
        height_screen = max(4, int(NECK_RADIUS * camera.zoom * height_mult * 2))  # Taller for vertical joint
        
        # Width (along segment direction) uses actual segment length - NOW HORIZONTAL
        width_screen = max(int(length_screen), int(segment.chain_length * camera.zoom))

        # Get rotation angle - ellipse should be oriented along the segment
        angle = math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0])
        
        # Draw rotated ellipse - height is along the segment direction, width is perpendicular
        color = self._get_cached_ellipse_color(segment.consolidation_level)
        self._draw_rotated_ellipse((center_x, center_y), width_screen, height_screen, angle, color)
        
        # Draw subtle connection indicators at close zoom
        if camera.zoom > 0.05:
            connection_radius = max(1, int(2 * camera.zoom))
            pygame.draw.circle(self.screen, (200, 200, 200), (int(start_screen[0]), int(start_screen[1])), connection_radius)
            pygame.draw.circle(self.screen, (200, 200, 200), (int(end_screen[0]), int(end_screen[1])), connection_radius)
    
    def _draw_thick_line(self, start_pos, end_pos, thickness, color):
        """Draw thick line as a series of circles (capsule shape)"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # Draw line body
        if thickness > 2:
            # Calculate perpendicular offset for rectangle
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.hypot(dx, dy)
            
            if length > 0:
                # Normalize and get perpendicular
                norm_x, norm_y = dx/length, dy/length
                perp_x, perp_y = -norm_y, norm_x
                
                # Calculate rectangle corners
                half_thickness = thickness / 2
                corners = [
                    (start_x + perp_x * half_thickness, start_y + perp_y * half_thickness),
                    (start_x - perp_x * half_thickness, start_y - perp_y * half_thickness),
                    (end_x - perp_x * half_thickness, end_y - perp_y * half_thickness),
                    (end_x + perp_x * half_thickness, end_y + perp_y * half_thickness)
                ]
                
                # Draw rectangle
                pygame.draw.polygon(self.screen, color, corners)
        
        # Draw end caps
        radius = thickness // 2
        if radius > 0:
            pygame.draw.circle(self.screen, color, (int(start_x), int(start_y)), radius)
            pygame.draw.circle(self.screen, color, (int(end_x), int(end_y)), radius)
    
    def _draw_rotated_ellipse(self, center, width, height, angle, color):
        """Draw rotated ellipse as vertical joint with proper proportions"""
        # Create ellipse points - height is along the rotation axis (segment direction)
        points = []
        num_points = max(12, min(24, int(width + height) // 6))  # More points for smoother joints
        
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            
            # Ellipse coordinates: width = perpendicular to segment, height = along segment
            x_local = (width / 2) * math.cos(theta)  # Perpendicular spread
            y_local = (height / 2) * math.sin(theta)  # Along segment length
            
            # Rotate point by segment angle
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x_rotated = x_local * cos_a - y_local * sin_a
            y_rotated = x_local * sin_a + y_local * cos_a
            
            # Translate to center
            points.append((center[0] + x_rotated, center[1] + y_rotated))
        
        if len(points) >= 3:
            # Draw filled ellipse
            pygame.draw.polygon(self.screen, color, points)
            
            # Add subtle outline for joint definition
            if width > 8:  # Only for larger joints
                outline_color = (
                    max(0, color[0] - 30),
                    max(0, color[1] - 30), 
                    max(0, color[2] - 30)
                )
                pygame.draw.polygon(self.screen, outline_color, points, 1)
    
    def _draw_head_2point(self, segment, camera):
        """Draw head segment using 2-point system"""
        # Head uses center position
        center_screen = camera.world_to_screen(segment.position[0], segment.position[1])
        radius = max(1, int(HEAD_RADIUS * camera.zoom))
        
        if self._is_point_visible(center_screen[0], center_screen[1], radius):
            pygame.draw.circle(self.screen, HEAD_COLOR, 
                             (int(center_screen[0]), int(center_screen[1])), radius)
    
    def _get_cached_ellipse_color(self, level):
        """Get cached ellipse color by consolidation level"""
        if level not in self._ellipse_colors:
            self._ellipse_colors[level] = (
                min(255, NECK_COLOR[0] + 30 + level * 20),
                min(255, NECK_COLOR[1] + 15 + level * 10), 
                max(0, NECK_COLOR[2] - level * 15)
            )
        return self._ellipse_colors[level]
    
    def _is_line_visible(self, start_pos, end_pos):
        """Check if line segment is visible on screen"""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Rough bounding box check with margin
        margin = 50
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return not (max_x < -margin or min_x > WIDTH + margin or 
                   max_y < -margin or min_y > HEIGHT + margin)
    
    def draw_ui(self, character, camera, performance_manager):
        """Enhanced UI with 2-point segment information"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        stats = character.get_consolidation_stats()
        
        # Calculate connectivity info
        total_length = sum(seg.get_length() for seg in character.neck_segments)
        avg_angle = sum(abs(seg.get_angle()) for seg in character.neck_segments) / len(character.neck_segments)
        
        # Essential info
        info_lines = [
            f"Zoom: {camera.zoom:.3f}x",
            f"Segments: {character.get_neck_segment_count()}",
            f"Total Length: {total_length:.1f}",
            f"Avg Angle: {math.degrees(avg_angle):.1f}Â°",
            f"LOD: {lod['name']}",
            "",
            "2-Point Connectivity:",
        ]
        
        # Show consolidation stats
        for stat_name, value in stats.items():
            if stat_name == "Total Length":
                continue
            info_lines.append(f"  {stat_name}: {value}")
        
        info_lines.extend(["", "Hold SPACE to grow neck"])
        
        # Draw info
        y_pos = 10
        for line in info_lines:
            if line:
                text_surface = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(text_surface, (10, y_pos))
            y_pos += 22
    
    def _is_visible(self, x, y, w, h):
        """Fast visibility check for rectangles"""
        return not (x + w < -50 or x > WIDTH + 50 or y + h < -50 or y > HEIGHT + 50)
    
    def _is_point_visible(self, x, y, radius):
        """Fast visibility check for circles"""
        margin = radius + 20
        return not (x < -margin or x > WIDTH + margin or y < -margin or y > HEIGHT + margin)