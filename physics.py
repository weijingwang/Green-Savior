def update_segments(self, segments, base_pos, target_pos, ground_y, complexity='normal'):
        """Update neck segments based on complexity level with ground collision"""
        if complexity == 'simple':
            return self._update_simple(segments, base_pos, target_pos, ground_y)
        elif complexity == 'medium':
            return self._update_medium(segments, base_pos, target_pos, ground_y)
        else:
            return self._update_normal(segments, base_pos, target_pos, ground_y)# physics.py - Fixed physics system with ellipse chain length support
import math
from config import SEGMENT_LENGTH, HEAD_RADIUS, NECK_RADIUS

class NeckPhysics:
    """Handles neck segment physics with ellipse chain length awareness"""
    
    def __init__(self):
        self.stiffness = 0.15
    
    def update_segments_with_objects(self, segments, base_pos, target_pos, ground_y, complexity='normal'):
        """Update neck segments working with segment objects directly"""
        if complexity == 'simple':
            return self._update_simple_objects(segments, base_pos, target_pos, ground_y)
        elif complexity == 'medium':
            return self._update_medium_objects(segments, base_pos, target_pos, ground_y)
        else:
            return self._update_normal_objects(segments, base_pos, target_pos, ground_y)
    
    def _update_normal_objects(self, segments, base_pos, target_pos, ground_y):
        """Physics that respects ellipse chain lengths working with segment objects"""
        # Create new segment list with updated positions
        new_segments = [seg for seg in segments]  # Copy the list
        
        # Update first segment position
        new_segments[0].position = base_pos
        current_pos = base_pos
        
        for i in range(1, len(segments)):
            current_segment = segments[i]
            
            # Calculate the chain length for this segment
            if hasattr(current_segment, 'chain_length'):
                chain_length = current_segment.chain_length
            else:
                chain_length = SEGMENT_LENGTH
            
            # Get direction toward target
            direction = self._get_direction(current_pos, target_pos)
            desired_pos = self._move_towards(current_pos, direction, chain_length)
            
            # Apply stiffness
            old_pos = current_segment.position
            new_x = old_pos[0] * (1 - self.stiffness) + desired_pos[0] * self.stiffness
            new_y = old_pos[1] * (1 - self.stiffness) + desired_pos[1] * self.stiffness
            
            # Maintain proper chain length constraint
            constrained_pos = self._constrain_length(current_pos, (new_x, new_y), chain_length)
            
            # Apply ground collision
            radius = HEAD_RADIUS if i == len(segments)-1 else NECK_RADIUS
            final_y = self._apply_ground_collision(constrained_pos[0], constrained_pos[1], ground_y, radius)
            
            new_segments[i].position = (constrained_pos[0], final_y)
            current_pos = new_segments[i].position
        
        return new_segments
    
    def _update_simple_objects(self, segments, base_pos, target_pos, ground_y):
        """Simplified physics working with segment objects"""
        new_segments = [seg for seg in segments]  # Copy the list
        new_segments[0].position = base_pos
        
        # Calculate total chain length
        total_length = 0
        for seg in segments:
            if hasattr(seg, 'chain_length'):
                total_length += seg.chain_length
            else:
                total_length += SEGMENT_LENGTH
        
        # Update positions based on progress along total length
        current_length = 0
        
        for i in range(1, len(segments)):
            if hasattr(segments[i], 'chain_length'):
                seg_length = segments[i].chain_length
            else:
                seg_length = SEGMENT_LENGTH
                
            current_length += seg_length
            
            # Update position based on progress along total length
            if i % 10 == 0 or i == len(segments) - 1:  # Update every 10th or the head
                progress = current_length / total_length if total_length > 0 else 0
                x = base_pos[0] + (target_pos[0] - base_pos[0]) * progress
                y = base_pos[1] + (target_pos[1] - base_pos[1]) * progress
                
                # Apply ground collision
                radius = HEAD_RADIUS if i == len(segments)-1 else NECK_RADIUS
                y = self._apply_ground_collision(x, y, ground_y, radius)
                new_segments[i].position = (x, y)
            else:
                # Keep existing position for non-updated segments
                pass  # Position stays the same
        
        return new_segments
    
    def _update_medium_objects(self, segments, base_pos, target_pos, ground_y):
        """Medium complexity physics with segment objects"""
        new_segments = [seg for seg in segments]  # Copy the list
        new_segments[0].position = base_pos
        current_pos = base_pos
        
        for i in range(1, len(segments)):
            current_segment = segments[i]
            
            # Get chain length for this segment
            if hasattr(current_segment, 'chain_length'):
                chain_length = current_segment.chain_length
            else:
                chain_length = SEGMENT_LENGTH
            
            # Update this segment
            direction = self._get_direction(current_pos, target_pos)
            desired_pos = self._move_towards(current_pos, direction, chain_length)
            
            # Apply stiffness
            old_pos = current_segment.position
            new_x = old_pos[0] * (1 - self.stiffness) + desired_pos[0] * self.stiffness
            new_y = old_pos[1] * (1 - self.stiffness) + desired_pos[1] * self.stiffness
            
            # Maintain chain length
            constrained_pos = self._constrain_length(current_pos, (new_x, new_y), chain_length)
            
            # Apply ground collision
            radius = HEAD_RADIUS if i == len(segments)-1 else NECK_RADIUS
            final_y = self._apply_ground_collision(constrained_pos[0], constrained_pos[1], ground_y, radius)
            new_segments[i].position = (constrained_pos[0], final_y)
            
            current_pos = new_segments[i].position
        
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