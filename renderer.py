# renderer.py - Optimized rendering system using top-3 segment system
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
    
    def _load_plant_images(self):
        """Load plant head images with fallback to colored circles"""
        images = {}
        try:
            print("player loaded!")
            images['head'] = pygame.image.load('assets/images/player/head.png')
            images['leafL'] = pygame.image.load('assets/images/player/leafL.png') 
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
            self._draw_active_segment_2point(segment, camera, i)
        
        # Draw plant head structure
        if len(plant_head_segments) == 5:
            self._draw_plant_head_structure(plant_head_segments, camera)

    def _draw_active_segment_2point(self, segment, camera, segment_index):
        """Draw active segment with enhanced visibility for large consolidated segments"""
        # Convert world positions to screen positions
        start_screen = camera.world_to_screen(segment.start_pos[0], segment.start_pos[1])
        end_screen = camera.world_to_screen(segment.end_pos[0], segment.end_pos[1])
        
        # Quick visibility check
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        if segment.type == 'ellipse':
            # Enhanced ellipse rendering for large consolidated segments
            self._draw_enhanced_ellipse_segment(segment, start_screen, end_screen, camera)
        else:
            # Enhanced regular segment rendering
            self._draw_enhanced_regular_segment(segment, start_screen, end_screen, camera)
    
    def _draw_enhanced_regular_segment(self, segment, start_screen, end_screen, camera):
        """Draw regular segment with thickness proportional to height it represents"""
        # Calculate thickness based on how much this segment represents
        base_thickness = NECK_RADIUS * camera.zoom
        height_multiplier = min(segment.height / 10.0, 3.0)  # Cap the multiplier
        thickness = max(2, int(base_thickness * (1 + height_multiplier * 0.5)))
        
        # Draw as thick line (capsule) with enhanced visibility
        if thickness > 1:
            self._draw_thick_line(start_screen, end_screen, thickness, NECK_COLOR)
            
            # Add outline for very large segments
            if segment.height > 50:
                outline_color = (
                    max(0, NECK_COLOR[0] - 40),
                    max(0, NECK_COLOR[1] - 40),
                    max(0, NECK_COLOR[2] - 40)
                )
                self._draw_thick_line(start_screen, end_screen, thickness + 2, outline_color)
                self._draw_thick_line(start_screen, end_screen, thickness, NECK_COLOR)
        else:
            # Fallback to thin line
            pygame.draw.line(self.screen, NECK_COLOR, start_screen, end_screen, 1)
    
    def _draw_enhanced_ellipse_segment(self, segment, start_screen, end_screen, camera):
        """Draw enhanced ellipse segment with size proportional to consolidation"""
        # Calculate center, length, and angle
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        
        # Calculate screen-space dimensions
        length_screen = math.hypot(end_screen[0] - start_screen[0], end_screen[1] - start_screen[1])
        
        # Enhanced size calculation based on both level and height
        base_size = NECK_RADIUS * camera.zoom
        level_mult = 1.4 + 0.4 * segment.consolidation_level
        height_mult = min(segment.height / 20.0, 2.0)  # Cap height influence
        
        # Height (perpendicular to segment) - enhanced for visibility
        height_screen = max(6, int(base_size * level_mult * (1 + height_mult * 0.3) * 2))
        
        # Width (along segment direction)
        width_screen = max(int(length_screen), int(segment.chain_length * camera.zoom))
        
        # Get rotation angle
        angle = math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0])
        
        # Enhanced color based on consolidation level and size
        color = self._get_enhanced_ellipse_color(segment.consolidation_level, segment.height)
        
        # Draw rotated ellipse with enhanced appearance
        self._draw_enhanced_rotated_ellipse((center_x, center_y), width_screen, height_screen, angle, color, segment)
        
        # Draw connection indicators for very large segments
        if camera.zoom > 0.02 or segment.height > 100:
            connection_radius = max(2, int(3 * camera.zoom))
            connection_color = (255, 255, 255) if segment.height > 100 else (200, 200, 200)
            pygame.draw.circle(self.screen, connection_color, (int(start_screen[0]), int(start_screen[1])), connection_radius)
            pygame.draw.circle(self.screen, connection_color, (int(end_screen[0]), int(end_screen[1])), connection_radius)
    
    def _draw_enhanced_rotated_ellipse(self, center, width, height, angle, color, segment):
        """Draw enhanced ellipse with visual indicators for massive segments"""
        # Create ellipse points
        points = []
        num_points = max(16, min(32, int(width + height) // 4))  # More points for smoother large joints
        
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            
            # Ellipse coordinates
            x_local = (width / 2) * math.cos(theta)
            y_local = (height / 2) * math.sin(theta)
            
            # Rotate point by segment angle
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x_rotated = x_local * cos_a - y_local * sin_a
            y_rotated = x_local * sin_a + y_local * cos_a
            
            # Translate to center
            points.append((center[0] + x_rotated, center[1] + y_rotated))
        
        if len(points) >= 3:
            # Draw filled ellipse
            pygame.draw.polygon(self.screen, color, points)
            
            # Enhanced outline for large segments
            outline_thickness = 1
            if segment.height > 50:
                outline_thickness = 2
            elif segment.height > 200:
                outline_thickness = 3
                
            if width > 10:  # Only for larger joints
                outline_color = (
                    max(0, color[0] - 40),
                    max(0, color[1] - 40), 
                    max(0, color[2] - 40)
                )
                pygame.draw.polygon(self.screen, outline_color, points, outline_thickness)
                
            # Add inner highlight for mega-segments
            if segment.height > 500:
                inner_points = []
                scale_factor = 0.7
                for i in range(num_points):
                    theta = 2 * math.pi * i / num_points
                    x_local = (width / 2 * scale_factor) * math.cos(theta)
                    y_local = (height / 2 * scale_factor) * math.sin(theta)
                    
                    cos_a, sin_a = math.cos(angle), math.sin(angle)
                    x_rotated = x_local * cos_a - y_local * sin_a
                    y_rotated = x_local * sin_a + y_local * cos_a
                    
                    inner_points.append((center[0] + x_rotated, center[1] + y_rotated))
                
                highlight_color = (
                    min(255, color[0] + 30),
                    min(255, color[1] + 30),
                    min(255, color[2] + 30)
                )
                pygame.draw.polygon(self.screen, highlight_color, inner_points)
    
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
    
    def _draw_head_2point(self, segment, camera):
        """Draw head segment using 2-point system with enhanced size for large segments"""
        # Head uses center position
        center_screen = camera.world_to_screen(segment.position[0], segment.position[1])
        base_radius = HEAD_RADIUS * camera.zoom
        
        # Scale head size slightly based on neck complexity
        size_mult = min(1 + segment.height / 100.0, 1.5)  # Cap at 1.5x
        radius = max(2, int(base_radius * size_mult))
        
        if self._is_point_visible(center_screen[0], center_screen[1], radius):
            # Enhanced head color for very large necks
            head_color = HEAD_COLOR
            if segment.height > 200:
                head_color = (
                    min(255, HEAD_COLOR[0] + 20),
                    min(255, HEAD_COLOR[1] + 30),
                    HEAD_COLOR[2]
                )
            
            pygame.draw.circle(self.screen, head_color, 
                             (int(center_screen[0]), int(center_screen[1])), radius)
            
            # Add outline for very large heads
            if segment.height > 100:
                outline_color = (
                    max(0, head_color[0] - 50),
                    max(0, head_color[1] - 50),
                    max(0, head_color[2] - 30)
                )
                pygame.draw.circle(self.screen, outline_color, 
                                 (int(center_screen[0]), int(center_screen[1])), radius, 2)
    
    def _get_enhanced_ellipse_color(self, level, height):
        """Get enhanced ellipse color based on both level and height"""
        cache_key = (level, min(height // 50, 10))  # Group heights by 50s
        
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
                # Highlight performance info in green
                color = (255, 255, 255)
                if "Performance Gain" in line or "Active Segments" in line:
                    color = (100, 255, 100)
                elif "TOP-3 OPTIMIZATION" in line:
                    color = (255, 200, 100)
                
                text_surface = self.font.render(line, True, color)
                self.screen.blit(text_surface, (10, y_pos))
            y_pos += 22
    
    def _is_visible(self, x, y, w, h):
        """Fast visibility check for rectangles"""
        return not (x + w < -50 or x > WIDTH + 50 or y + h < -50 or y > HEIGHT + 50)
    
    def _is_point_visible(self, x, y, radius):
        """Fast visibility check for circles"""
        margin = radius + 20
        return not (x < -margin or x > WIDTH + margin or y < -margin or y > HEIGHT + margin)
    
    def _draw_plant_head_structure(self, plant_segments, camera):
        """Draw the 5-part plant head: left_leaf - left_joint - head - right_joint - right_leaf"""
        left_leaf, left_joint, head, right_joint, right_leaf = plant_segments
        
        # Draw joints (ellipses)
        self._draw_plant_joint(left_joint, camera, "left")
        self._draw_plant_joint(right_joint, camera, "right")
        
        # Draw leaves (enhanced ellipses with leaf-like appearance)
        self._draw_plant_leaf(left_leaf, camera, "left")
        self._draw_plant_leaf(right_leaf, camera, "right")
        
        # Draw head (special circular head with plant-like features)
        self._draw_plant_head_center(head, camera)
    
    def _draw_plant_joint(self, joint_segment, camera, side):
        """Draw plant joint as a more visible connecting ellipse"""
        start_screen = camera.world_to_screen(joint_segment.start_pos[0], joint_segment.start_pos[1])
        end_screen = camera.world_to_screen(joint_segment.end_pos[0], joint_segment.end_pos[1])
        
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        # Make joints more visible - larger size
        base_size = max(NECK_RADIUS * camera.zoom, 4)  # Minimum visible size
        joint_width = max(6, int(base_size * 1.2))  # Wider
        joint_height = max(4, int(base_size * 0.8))  # Taller
        
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        angle = math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0])
        
        # Enhanced joint color for visibility
        joint_color = (
            min(255, NECK_COLOR[0] + 40),
            min(255, NECK_COLOR[1] + 50),
            max(0, NECK_COLOR[2] - 10)
        )
        
        # Draw joint with outline for definition
        self._draw_rotated_ellipse_simple((center_x, center_y), joint_width, joint_height, angle, joint_color)
        
        # Add outline for better visibility
        if joint_width > 8:
            outline_color = (
                max(0, joint_color[0] - 60),
                max(0, joint_color[1] - 40),
                joint_color[2]
            )
            self._draw_rotated_ellipse_outline((center_x, center_y), joint_width, joint_height, angle, outline_color)
    
    def _draw_rotated_ellipse_outline(self, center, width, height, angle, color):
        """Draw outline of rotated ellipse"""
        points = []
        num_points = max(12, min(20, int(width + height) // 2))
        
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            
            x_local = (width / 2) * math.cos(theta)
            y_local = (height / 2) * math.sin(theta)
            
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x_rotated = x_local * cos_a - y_local * sin_a
            y_rotated = x_local * sin_a + y_local * cos_a
            
            points.append((center[0] + x_rotated, center[1] + y_rotated))
        
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, color, points, 2)  # Outline thickness = 2
    
    def _draw_plant_leaf(self, leaf_segment, camera, side):
        """Draw plant leaf using appropriate image (leafL.png or leafR.png)"""
        start_screen = camera.world_to_screen(leaf_segment.start_pos[0], leaf_segment.start_pos[1])
        end_screen = camera.world_to_screen(leaf_segment.end_pos[0], leaf_segment.end_pos[1])
        
        if not self._is_line_visible(start_screen, end_screen):
            return
        
        # Get leaf image
        leaf_image_key = 'leafL' if side == 'left' else 'leafR'
        leaf_image = self.plant_images[leaf_image_key]
        
        # Calculate leaf position and rotation
        center_x = (start_screen[0] + end_screen[0]) / 2
        center_y = (start_screen[1] + end_screen[1]) / 2
        angle_deg = math.degrees(math.atan2(end_screen[1] - start_screen[1], end_screen[0] - start_screen[0]))
        
        # Calculate leaf size based on segment length and camera zoom
        length_screen = math.hypot(end_screen[0] - start_screen[0], end_screen[1] - start_screen[1])
        
        # Scale leaf image - slower scaling to stay visible
        scale_factor = max(0.3, min(2.0, length_screen / 30.0))  # Keeps leaves visible at all zoom levels
        new_width = max(16, int(leaf_image.get_width() * scale_factor * camera.zoom * 2))  # Extra scaling for visibility
        new_height = max(8, int(leaf_image.get_height() * scale_factor * camera.zoom * 2))
        
        # Scale and rotate image
        scaled_leaf = pygame.transform.scale(leaf_image, (new_width, new_height))
        rotated_leaf = pygame.transform.rotate(scaled_leaf, angle_deg)
        
        # Draw leaf image centered on position
        leaf_rect = rotated_leaf.get_rect(center=(int(center_x), int(center_y)))
        self.screen.blit(rotated_leaf, leaf_rect)
    
    def _draw_plant_head_center(self, head_segment, camera):
        """Draw the central plant head using head.png with very slow scaling"""
        center_screen = camera.world_to_screen(head_segment.position[0], head_segment.position[1])
        
        # Much slower scaling - head should always be clearly visible
        base_size = 32  # Base pixel size
        # Very gentle scaling that keeps head visible even at extreme zoom levels
        scale_factor = max(0.4, min(3.0, 0.5 + camera.zoom * 0.5))  # Much slower scaling curve
        
        new_size = max(12, int(base_size * scale_factor))  # Minimum 12px, maximum based on scale
        
        if not self._is_point_visible(center_screen[0], center_screen[1], new_size//2):
            return
        
        # Get and scale head image
        head_image = self.plant_images['head']
        scaled_head = pygame.transform.scale(head_image, (new_size, new_size))
        
        # Draw head image centered
        head_rect = scaled_head.get_rect(center=(int(center_screen[0]), int(center_screen[1])))
        self.screen.blit(scaled_head, head_rect)
    
    def _draw_rotated_ellipse_simple(self, center, width, height, angle, color):
        """Simple rotated ellipse for joints"""
        points = []
        num_points = max(8, min(16, int(width + height) // 2))
        
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            
            x_local = (width / 2) * math.cos(theta)
            y_local = (height / 2) * math.sin(theta)
            
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x_rotated = x_local * cos_a - y_local * sin_a
            y_rotated = x_local * sin_a + y_local * cos_a
            
            points.append((center[0] + x_rotated, center[1] + y_rotated))
        
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, color, points)
