import math
from config import *

class Character:
    def __init__(self):
        self.base_x = 0
        self.base_y = 0
        self.neck_positions = [(self.base_x, self.base_y - (i + 1) * SEGMENT_LENGTH) 
                              for i in range(NECK_SEGMENTS)]
        self.walk_timer = 0
        self.physics_frame_counter = 0
    
    def update(self, target_x, target_y, camera):
        """Update character position and neck physics"""
        # Update walk animation
        self.walk_timer += 0.05
        step_phase = (math.sin(self.walk_timer) + 1) / 2
        
        # Calculate torso position with jerky zombie walk
        if step_phase > 0.3:
            torso_y = self.base_y - step_phase * 20
        else:
            torso_y = self.base_y - 14 + (math.sin(self.walk_timer * 12) * 6)
        
        torso_x = self.base_x + math.sin(self.walk_timer * 0.5) * 15
        
        # Update neck physics
        self.neck_positions = self._update_neck_optimized(
            (torso_x, torso_y), (target_x, target_y), camera
        )
        
        return torso_x, torso_y
    
    def _update_neck_optimized(self, base, target, camera):
        """Optimized neck physics with LOD"""
        lod = camera.get_current_lod()
        physics_skip = lod["physics_skip"]
        
        self.physics_frame_counter += 1
        
        # Skip physics updates for performance
        if self.physics_frame_counter % physics_skip != 0:
            return self.neck_positions
        
        # Use different physics based on segment count and zoom
        segment_count = len(self.neck_positions)
        
        # Keep responsive physics longer, but optimize for high segment counts
        if segment_count > 200 or camera.zoom_factor < 0.01:
            return self._update_neck_simplified(base, target)
        elif segment_count > 150:
            return self._update_neck_medium(base, target)
        else:
            return self._update_neck_regular(base, target)
    
    def _update_neck_simplified(self, base, target):
        """Ultra-simplified neck physics for extreme zooms"""
        points = self.neck_positions[:]
        points[0] = (base[0], base[1] - TORSO_RADIUS)
        
        total_segments = len(points)
        for i in range(10, total_segments, 10):
            progress = i / total_segments
            x = base[0] + (target[0] - base[0]) * progress
            y = base[1] + (target[1] - base[1]) * progress
            
            if y > 100:  # Ground collision
                y = 100
            points[i] = (x, y)
        
        # Always update head
        if total_segments > 0:
            head_x, head_y = target
            if head_y > 100:
                head_y = 100
            points[-1] = (head_x, head_y)
        
        return points
    
    def _update_neck_medium(self, base, target, stiffness=0.25):
        """Medium optimization neck physics for moderate segment counts"""
        points = self.neck_positions[:]
        points[0] = (base[0], base[1] - TORSO_RADIUS)
        
        # Update every other segment for performance, but keep accuracy
        for i in range(2, len(points), 2):  # Skip every other segment
            # Calculate direction to target
            dx = target[0] - points[i-2][0]
            dy = target[1] - points[i-2][1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 0.0001
            
            dx /= dist
            dy /= dist
            desired_x = points[i-2][0] + dx * (SEGMENT_LENGTH * 2)  # Double length since skipping
            desired_y = points[i-2][1] + dy * (SEGMENT_LENGTH * 2)
            
            # Apply stiffness
            x = points[i][0] * (1 - stiffness) + desired_x * stiffness
            y = points[i][1] * (1 - stiffness) + desired_y * stiffness
            
            # Ground collision
            if y > 100:
                y = 100
            points[i] = (x, y)
            
            # Interpolate the skipped segment
            if i > 0:
                points[i-1] = ((points[i-2][0] + points[i][0]) / 2, 
                              (points[i-2][1] + points[i][1]) / 2)
        
        # Always update head properly
        if len(points) > 2:
            head_x, head_y = target
            if head_y > 100:
                head_y = 100
            points[-1] = (head_x, head_y)
        
        return points

    def _update_neck_regular(self, base, target, stiffness=0.15):
        """Regular neck physics for normal zooms"""
        points = self.neck_positions[:]
        points[0] = (base[0], base[1] - TORSO_RADIUS)
        
        for i in range(1, len(points)):
            # Calculate direction to target
            dx = target[0] - points[i-1][0]
            dy = target[1] - points[i-1][1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 0.0001
            
            dx /= dist
            dy /= dist
            desired_x = points[i-1][0] + dx * SEGMENT_LENGTH
            desired_y = points[i-1][1] + dy * SEGMENT_LENGTH
            
            # Apply stiffness
            x = points[i][0] * (1 - stiffness) + desired_x * stiffness
            y = points[i][1] * (1 - stiffness) + desired_y * stiffness
            
            # Maintain segment length
            dx = x - points[i-1][0]
            dy = y - points[i-1][1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 0.0001
            
            dx /= dist
            dy /= dist
            px = points[i-1][0] + dx * SEGMENT_LENGTH
            py = points[i-1][1] + dy * SEGMENT_LENGTH
            
            # Ground collision
            if py > 100:
                py = 100
            points[i] = (px, py)
        
        return points
    
    def check_head_bounds(self, camera):
        """Check if head is hitting screen edges"""
        if not self.neck_positions:
            return False
        
        head_pos = self.neck_positions[-1]
        screen_x, screen_y = camera.world_to_screen(head_pos[0], head_pos[1])
        
        head_screen_radius = HEAD_RADIUS * camera.zoom_factor
        margin = head_screen_radius + 10
        
        return (screen_x < margin or screen_x > WIDTH - margin or screen_y < margin)
    
    def add_segment(self):
        """Add a new neck segment"""
        if len(self.neck_positions) < 500:  # Increased max segments for more scaling
            self.neck_positions.insert(-1, self.neck_positions[-2])