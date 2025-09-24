# physics.py - Fixed physics system with ground collision
import math
from config import SEGMENT_LENGTH, HEAD_RADIUS, NECK_RADIUS

class NeckPhysics:
    """Handles neck segment physics with different complexity levels"""
    
    def __init__(self):
        self.stiffness = 0.15
    
    def update_segments(self, segments, base_pos, target_pos, ground_y, complexity='normal'):
        """Update neck segments based on complexity level with ground collision"""
        if complexity == 'simple':
            return self._update_simple(segments, base_pos, target_pos, ground_y)
        elif complexity == 'medium':
            return self._update_medium(segments, base_pos, target_pos, ground_y)
        else:
            return self._update_normal(segments, base_pos, target_pos, ground_y)
    
    def _update_simple(self, segments, base_pos, target_pos, ground_y):
        """Ultra-simplified physics for extreme zoom levels"""
        new_segments = segments[:]
        new_segments[0] = base_pos
        
        # Only update every 10th segment
        total = len(segments)
        for i in range(10, total, 10):
            progress = i / total
            x = base_pos[0] + (target_pos[0] - base_pos[0]) * progress
            y = base_pos[1] + (target_pos[1] - base_pos[1]) * progress
            
            # Apply ground collision
            y = self._apply_ground_collision(x, y, ground_y, HEAD_RADIUS if i == total-1 else NECK_RADIUS)
            new_segments[i] = (x, y)
        
        # Always update head with collision
        head_x, head_y = target_pos
        head_y = self._apply_ground_collision(head_x, head_y, ground_y, HEAD_RADIUS)
        new_segments[-1] = (head_x, head_y)
        
        return new_segments
    
    def _update_medium(self, segments, base_pos, target_pos, ground_y):
        """Medium complexity physics - skip every other segment"""
        new_segments = segments[:]
        new_segments[0] = base_pos
        
        for i in range(2, len(segments), 2):
            direction = self._get_direction(segments[i-2], target_pos)
            desired_pos = self._move_towards(segments[i-2], direction, SEGMENT_LENGTH * 2)
            
            # Apply stiffness
            new_x = segments[i][0] * (1 - self.stiffness) + desired_pos[0] * self.stiffness
            new_y = segments[i][1] * (1 - self.stiffness) + desired_pos[1] * self.stiffness
            
            # Apply ground collision
            radius = HEAD_RADIUS if i == len(segments)-1 else NECK_RADIUS
            new_y = self._apply_ground_collision(new_x, new_y, ground_y, radius)
            new_segments[i] = (new_x, new_y)
            
            # Interpolate skipped segment with collision check
            if i > 0:
                prev_pos = new_segments[i-2]
                curr_pos = new_segments[i]
                interp_x = (prev_pos[0] + curr_pos[0]) / 2
                interp_y = (prev_pos[1] + curr_pos[1]) / 2
                interp_y = self._apply_ground_collision(interp_x, interp_y, ground_y, NECK_RADIUS)
                new_segments[i-1] = (interp_x, interp_y)
        
        # Update head with collision
        head_x, head_y = target_pos
        head_y = self._apply_ground_collision(head_x, head_y, ground_y, HEAD_RADIUS)
        new_segments[-1] = (head_x, head_y)
        
        return new_segments
    
    def _update_normal(self, segments, base_pos, target_pos, ground_y):
        """Full complexity physics for normal zoom levels"""
        new_segments = segments[:]
        new_segments[0] = base_pos
        
        for i in range(1, len(segments)):
            direction = self._get_direction(segments[i-1], target_pos)
            desired_pos = self._move_towards(segments[i-1], direction, SEGMENT_LENGTH)
            
            # Apply stiffness
            new_x = segments[i][0] * (1 - self.stiffness) + desired_pos[0] * self.stiffness
            new_y = segments[i][1] * (1 - self.stiffness) + desired_pos[1] * self.stiffness
            
            # Maintain segment length constraint
            constrained_pos = self._constrain_length(segments[i-1], (new_x, new_y), SEGMENT_LENGTH)
            
            # Apply ground collision
            radius = HEAD_RADIUS if i == len(segments)-1 else NECK_RADIUS
            final_y = self._apply_ground_collision(constrained_pos[0], constrained_pos[1], ground_y, radius)
            new_segments[i] = (constrained_pos[0], final_y)
        
        return new_segments
    
    def _apply_ground_collision(self, x, y, ground_y, radius):
        """Prevent segments from going below ground level"""
        min_y = ground_y - radius
        return min(y, min_y)
    
    def _get_direction(self, from_pos, to_pos):
        """Get normalized direction vector"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        distance = math.hypot(dx, dy)
        
        if distance == 0:
            return (0, 0)
        
        return (dx / distance, dy / distance)
    
    def _move_towards(self, pos, direction, distance):
        """Move position in direction by distance"""
        return (
            pos[0] + direction[0] * distance,
            pos[1] + direction[1] * distance
        )
    
    def _constrain_length(self, anchor_pos, target_pos, max_length):
        """Constrain target position to be exactly max_length from anchor"""
        direction = self._get_direction(anchor_pos, target_pos)
        return self._move_towards(anchor_pos, direction, max_length)