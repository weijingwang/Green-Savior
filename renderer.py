# renderer.py - Optimized rendering system with fixed scaling and reduced code duplication
import pygame
import math
from config import *

class Renderer:
    """Optimized renderer that only processes active segments for massive performance gains"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 28)
        
        # Cache frequently used values
        self._screen_bounds = (-50, -50, WIDTH + 50, HEIGHT + 50)
        self._ellipse_colors = {}  # Cache colors by consolidation level
        
        # Load plant images
        self.plant_images = self._load_plant_images()
        
        # Fixed scaling constants to prevent startup scaling issues
        self.LEAF_BASE_SIZE = 25  # Fixed base size for leaves
        self.HEAD_BASE_SIZE = 15  # Fixed base size for head
        self.MIN_SCALE = 3.0      # Minimum scale factor
        self.MAX_SCALE = 6.0      # Maximum scale factor
    
    def _load_plant_images(self):
        """Load plant head images with fallback to colored circles"""
        images = {}
        try:
            print("player loaded!")
            images['head'] = pygame.image.load('assets/images/player/head.png')
            images['leafL'] = pygame.image.load('assets/images/player/leafR.png') 
            images['leafR'] = pygame.image.load('assets/images/player/leafR.png')
        except:
            # Create fallback colored surfaces if images don't exist
            head_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(head_surf, (150, 200, 80), (16, 16), 16)
            images['head'] = head_surf
            
            leaf_surf = pygame.Surface((40, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf_surf, (100, 180, 60), (0, 0, 40, 20))
            images['leafL'] = leaf_surf
            images['leafR'] = leaf_surf
        
        return images
    
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
        """Draw character with optimized rendering using only active segments"""
        torso_pos = character._cached_torso_pos or character._get_torso_position()
        
        # Draw torso
        screen_x, screen_y = camera.world_to_screen(torso_pos[0], torso_pos[1])
        radius = max(1, int(TORSO_RADIUS * camera.zoom))
        pygame.draw.circle(self.screen, TORSO_COLOR, (int(screen_x), int(screen_y)), radius)
        
        # Draw neck with ONLY active segments - massive performance boost
        self._draw_neck_optimized(character, camera, performance_manager)

    def _draw_neck_optimized(self, character, camera, performance_manager):
        """Optimized neck drawing with plant head structure"""
        # Get only active segments
        active_segments = character.get_neck_segments_for_rendering()
        
        if not active_segments:
            return
        
        # Split into neck segments and plant head structure
        if len(active_segments) >= 5:
            neck_segments = active_segments[:-5]  # Neck body segments
            plant_head_segments = active_segments[-5:]  # Last 5: plant head structure
        else:
            neck_segments = []
            plant_head_segments = active_segments
        
        # Draw neck segments
        for i, segment in enumerate(neck_segments):
            self._draw_active_segment(segment, camera)
        
        # Draw plant head structure
        if len(plant_head_segments) == 5:
            self._draw_plant_head_structure(plant_head_segments, camera)

    def _draw_active_segment(self, segment, camera):
        """Draw active segment with enhanced visibility"""
        # Convert world positions to screen positions
        start_screen = camera.world_to_screen(segment.start_pos[0], segment.start_pos[1])
        end_screen = camera.world_to_screen(segment.end_pos[0], segment.end_pos[1])
        
        # Quick visibility check
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        if segment.type == 'ellipse':
            self._draw_ellipse_segment(segment, start_screen, end_screen, camera)
        else:
            self._draw_regular_segment(segment, start_screen, end_screen, camera)
    
    def _draw_regular_segment(self, segment, start_screen, end_screen, camera):
        """Draw regular segment with thickness proportional to height it represents"""
        # Calculate thickness based on how much this segment represents
        base_thickness = NECK_RADIUS * camera.zoom
        height_multiplier = min(segment.height / 10.0, 3.0)  # Cap the multiplier
        thickness = max(2, int(base_thickness * (1 + height_multiplier * 0.5)))
        
        # Draw as thick line with enhanced visibility for large segments
        if segment.height > 50:
            # Add outline for very large segments
            outline_color = self._darken_color(NECK_COLOR, 40)
            self._draw_thick_line(start_screen, end_screen, thickness + 2, outline_color)
        
        self._draw_thick_line(start_screen, end_screen, thickness, NECK_COLOR)
    
    def _draw_ellipse_segment(self, segment, start_screen, end_screen, camera):
        """Draw enhanced ellipse segment with size proportional to consolidation"""
        # Calculate center, length, and angle
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        
        # Calculate screen-space dimensions
        length_screen = math.hypot(end_screen[0] - start_screen[0], end_screen[1] - start_screen[1])
        
        # Enhanced size calculation
        base_size = NECK_RADIUS * camera.zoom
        level_mult = 1.4 + 0.4 * segment.consolidation_level
        height_mult = min(segment.height / 20.0, 2.0)
        
        height_screen = max(6, int(base_size * level_mult * (1 + height_mult * 0.3) * 2))
        width_screen = max(int(length_screen), int(segment.chain_length * camera.zoom))
        
        angle = math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0])
        color = self._get_enhanced_ellipse_color(segment.consolidation_level, segment.height)
        
        # Draw ellipse with outline for large segments
        self._draw_rotated_ellipse((center_x, center_y), width_screen, height_screen, angle, color)
        
        if segment.height > 50:
            outline_color = self._darken_color(color, 40)
            self._draw_rotated_ellipse_outline((center_x, center_y), width_screen, height_screen, angle, outline_color)
        
        # Draw connection indicators for very large segments
        if camera.zoom > 0.02 or segment.height > 100:
            connection_radius = max(2, int(3 * camera.zoom))
            connection_color = (255, 255, 255) if segment.height > 100 else (200, 200, 200)
            pygame.draw.circle(self.screen, connection_color, (int(start_screen[0]), int(start_screen[1])), connection_radius)
            pygame.draw.circle(self.screen, connection_color, (int(end_screen[0]), int(end_screen[1])), connection_radius)
    
    def _draw_thick_line(self, start_pos, end_pos, thickness, color):
        """Draw thick line as a capsule shape"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        if thickness <= 2:
            pygame.draw.line(self.screen, color, start_pos, end_pos, max(1, thickness))
            return
        
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
            
            pygame.draw.polygon(self.screen, color, corners)
        
        # Draw end caps
        radius = thickness // 2
        if radius > 0:
            pygame.draw.circle(self.screen, color, (int(start_x), int(start_y)), radius)
            pygame.draw.circle(self.screen, color, (int(end_x), int(end_y)), radius)
    
    def _draw_plant_head_structure(self, plant_segments, camera):
        """Draw the 5-part plant head: left_leaf - left_joint - head - right_joint - right_leaf"""
        left_leaf, left_joint, head, right_joint, right_leaf = plant_segments
        
        # Draw joints first (behind leaves)
        self._draw_plant_joint(left_joint, camera)
        self._draw_plant_joint(right_joint, camera)
        
        # Draw leaves
        self._draw_plant_leaf(left_leaf, camera, "left")
        self._draw_plant_leaf(right_leaf, camera, "right")
        
        # Draw head (on top)
        self._draw_plant_head_center(head, camera)
    
    def _draw_plant_joint(self, joint_segment, camera):
        """Draw plant joint as a connecting ellipse"""
        start_screen = camera.world_to_screen(joint_segment.start_pos[0], joint_segment.start_pos[1])
        end_screen = camera.world_to_screen(joint_segment.end_pos[0], joint_segment.end_pos[1])
        
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        # Calculate joint dimensions
        base_size = max(NECK_RADIUS * camera.zoom, 4)
        joint_width = max(6, int(base_size * 1.2))
        joint_height = max(4, int(base_size * 0.8))
        
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        angle = math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0])
        
        # Enhanced joint color
        joint_color = (
            min(255, NECK_COLOR[0] + 40),
            min(255, NECK_COLOR[1] + 50),
            max(0, NECK_COLOR[2] - 10)
        )
        
        self._draw_rotated_ellipse((center_x, center_y), joint_width, joint_height, angle, joint_color)
        
        # Add outline for better visibility
        if joint_width > 8:
            outline_color = self._darken_color(joint_color, 60)
            self._draw_rotated_ellipse_outline((center_x, center_y), joint_width, joint_height, angle, outline_color)
    
    def _draw_plant_leaf(self, leaf_segment, camera, side):
        """Draw plant leaf using appropriate image with FIXED scaling"""
        start_screen = camera.world_to_screen(leaf_segment.start_pos[0], leaf_segment.start_pos[1])
        end_screen = camera.world_to_screen(leaf_segment.end_pos[0], leaf_segment.end_pos[1])
        
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        # Get leaf image
        leaf_image_key = 'leafL' if side == 'left' else 'leafR'
        leaf_image = self.plant_images[leaf_image_key]
        
        # Calculate position and rotation
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        angle_deg = math.degrees(math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0]))
        
        # FIXED scaling to prevent startup issues
        zoom_factor = max(0.1, min(2.0, camera.zoom))  # Clamp zoom to reasonable range
        scale_factor = self.MIN_SCALE + (self.MAX_SCALE - self.MIN_SCALE) * min(zoom_factor, 1.0)
        
        # Calculate final size
        final_width = max(8, int(self.LEAF_BASE_SIZE * scale_factor))
        final_height = max(4, int(self.LEAF_BASE_SIZE * scale_factor * 0.5))
        
        # Scale and rotate image
        scaled_leaf = pygame.transform.scale(leaf_image, (final_width, final_height))
        rotated_leaf = pygame.transform.rotate(scaled_leaf, angle_deg)
        
        # Draw leaf image centered on position
        leaf_rect = rotated_leaf.get_rect(center=(int(center_x), int(center_y)))
        self.screen.blit(rotated_leaf, leaf_rect)
    
    def _draw_plant_head_center(self, head_segment, camera):
        """Draw the central plant head with FIXED scaling"""
        center_screen = camera.world_to_screen(head_segment.position[0], head_segment.position[1])
        
        # FIXED scaling to prevent startup issues
        zoom_factor = max(0.1, min(2.0, camera.zoom))  # Clamp zoom
        scale_factor = self.MIN_SCALE + (self.MAX_SCALE - self.MIN_SCALE) * min(zoom_factor * 0.8, 1.0)
        
        # Calculate final size
        final_size = max(10, int(self.HEAD_BASE_SIZE * scale_factor))
        
        if not self._is_point_visible(center_screen[0], center_screen[1], final_size//2):
            return
        
        # Get and scale head image
        head_image = self.plant_images['head']
        scaled_head = pygame.transform.scale(head_image, (final_size, final_size))
        
        # Draw head image centered
        head_rect = scaled_head.get_rect(center=(int(center_screen[0]), int(center_screen[1])))
        self.screen.blit(scaled_head, head_rect)
    
    def _draw_rotated_ellipse(self, center, width, height, angle, color):
        """Draw filled rotated ellipse"""
        points = self._get_ellipse_points(center, width, height, angle)
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, color, points)
    
    def _draw_rotated_ellipse_outline(self, center, width, height, angle, color, thickness=2):
        """Draw outline of rotated ellipse"""
        points = self._get_ellipse_points(center, width, height, angle)
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, color, points, thickness)
    
    def _get_ellipse_points(self, center, width, height, angle):
        """Generate points for rotated ellipse"""
        points = []
        num_points = max(8, min(20, int(width + height) // 4))
        
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            
            x_local = (width / 2) * math.cos(theta)
            y_local = (height / 2) * math.sin(theta)
            
            x_rotated = x_local * cos_a - y_local * sin_a
            y_rotated = x_local * sin_a + y_local * cos_a
            
            points.append((center[0] + x_rotated, center[1] + y_rotated))
        
        return points
    
    def _get_enhanced_ellipse_color(self, level, height):
        """Get enhanced ellipse color based on both level and height"""
        cache_key = (level, min(height // 50, 10))
        
        if cache_key not in self._ellipse_colors:
            base_color = NECK_COLOR
            level_intensity = min(level * 25, 100)
            height_intensity = min(height // 20, 50)
            
            self._ellipse_colors[cache_key] = (
                min(255, base_color[0] + level_intensity + height_intensity // 2),
                min(255, base_color[1] + level_intensity // 2 + height_intensity // 3), 
                max(0, base_color[2] - level_intensity // 2)
            )
        
        return self._ellipse_colors[cache_key]
    
    def _darken_color(self, color, amount):
        """Darken a color by the specified amount"""
        return (
            max(0, color[0] - amount),
            max(0, color[1] - amount),
            max(0, color[2] - amount)
        )
    
    def _is_line_visible(self, start_pos, end_pos):
        """Check if line segment is visible on screen"""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        margin = 50
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        return not (max_x < -margin or min_x > WIDTH + margin or 
                   max_y < -margin or min_y > HEIGHT + margin)
    
    def _is_visible(self, x, y, w, h):
        """Fast visibility check for rectangles"""
        return not (x + w < -50 or x > WIDTH + 50 or y + h < -50 or y > HEIGHT + 50)
    
    def _is_point_visible(self, x, y, radius):
        """Fast visibility check for circles"""
        margin = radius + 20
        return not (x < -margin or x > WIDTH + margin or y < -margin or y > HEIGHT + margin)
    
    def draw_ui(self, character, camera, performance_manager):
        """Enhanced UI showing optimization information"""
        lod = performance_manager.get_lod_settings(camera.zoom)
        stats = character.get_consolidation_stats()
        
        # Calculate connectivity info for active segments only
        active_segments = character.get_neck_segments_for_rendering()
        if active_segments:
            total_length = sum(seg.get_length() for seg in active_segments)
            avg_angle = sum(abs(seg.get_angle()) for seg in active_segments) / len(active_segments)
        else:
            total_length = 0
            avg_angle = 0
        
        # Essential info with optimization data
        info_lines = [
            f"Zoom: {camera.zoom:.3f}x",
            f"Active Segments: {character.get_active_segment_count()}/{character.get_neck_segment_count()}",
            f"Total Length: {character.get_total_neck_length():.1f}",
            f"Active Length: {total_length:.1f}",
            f"Avg Angle: {math.degrees(avg_angle):.1f}°",
            f"LOD: {lod['name']}",
            "",
            "TOP-3 OPTIMIZATION:",
        ]
        
        # Show consolidation stats
        for stat_name, value in stats.items():
            if stat_name == "Total Length":
                continue
            info_lines.append(f"  {stat_name}: {value}")
        
        info_lines.extend(["", "Hold SPACE to grow neck"])
        
        # Draw info with performance highlights
        y_pos = 10
        for line in info_lines:
            if line:
                # Highlight performance info in different colors
                color = (255, 255, 255)
                if "Performance Gain" in line or "Active Segments" in line:
                    color = (100, 255, 100)
                elif "TOP-3 OPTIMIZATION" in line:
                    color = (255, 200, 100)
                
                text_surface = self.font.render(line, True, color)
                self.screen.blit(text_surface, (10, y_pos))
            y_pos += 22