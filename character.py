# character.py - Character system with fixed bottom segment positioning
import math
from config import *
from physics import NeckPhysics

class NeckSegment:
    """Represents a single neck segment, either regular or consolidated ellipse"""
    
    def __init__(self, position, segment_type='regular', height_multiplier=1, consolidation_level=0, is_bottom_segment=False):
        self.position = position  # (x, y)
        self.type = segment_type  # 'regular' or 'ellipse'
        self.height_multiplier = height_multiplier  # How many regular segments this represents
        self.consolidation_level = consolidation_level  # Level of consolidation (0=regular, 1=first ellipse, 2=super ellipse, etc.)
        self.is_bottom_segment = is_bottom_segment  # Whether this is the bottom-most segment in the neck
        
        # For ellipses, store start and end positions for proper orientation
        self.start_pos = None
        self.end_pos = None
    
    def get_radius(self):
        """Get the radius for rendering this segment"""
        if self.type == 'ellipse':
            # Radius increases with consolidation level
            base_radius = NECK_RADIUS * (1.2 + 0.3 * self.consolidation_level)
            return base_radius
        return NECK_RADIUS
    
    def get_height(self):
        """Get the height of this segment"""
        return SEGMENT_LENGTH * self.height_multiplier
    
    def get_width_multiplier(self):
        """Get width multiplier for ellipse rendering - slightly wider each level"""
        if self.type == 'ellipse':
            return 1.4 + 0.2 * self.consolidation_level  # Slightly wider for higher levels
        return 1.0
    
    def get_length_in_pixels(self, camera):
        """Get the actual length this segment should occupy in pixels"""
        if self.type == 'ellipse' and self.start_pos and self.end_pos:
            # Calculate actual distance between start and end points
            dx = self.end_pos[0] - self.start_pos[0]
            dy = self.end_pos[1] - self.start_pos[1]
            actual_length = math.hypot(dx, dy)
            return actual_length * camera.zoom
        elif self.type == 'ellipse':
            # Fallback: proportional to segments it represents
            return self.height_multiplier * SEGMENT_LENGTH * camera.zoom
        return SEGMENT_LENGTH * camera.zoom
    
    def get_angle(self):
        """Get the angle of orientation for ellipse segments"""
        if self.type == 'ellipse' and self.start_pos and self.end_pos:
            dx = self.end_pos[0] - self.start_pos[0]
            dy = self.end_pos[1] - self.start_pos[1]
            return math.atan2(dy, dx)
        return 0  # Regular segments don't have orientation

class Character:
    """Main character with physics-based neck and recursive segment consolidation"""
    
    def __init__(self):
        self.x = 0
        self.y = 0  # Character torso at ground level (world Y = 0)
        self.neck_segments = self._create_initial_segments()
        self.walk_timer = 0
        self.physics = NeckPhysics()
        self.growth_cooldown = 0  # Prevent too rapid growth
    
    def _create_initial_segments(self):
        """Create initial neck segments starting from torso"""
        segments = []
        # Start from top of torso (torso center is at ground level)
        base_y = self.y - TORSO_RADIUS
        for i in range(INITIAL_NECK_SEGMENTS):
            y = base_y - (i + 1) * SEGMENT_LENGTH
            segment = NeckSegment((self.x, y), 'regular', 1, 0, i == 0)
            segments.append(segment)
        return segments
    
    def update(self, target_x, target_y, performance_manager, ground_world_y):
        """Update character position and neck physics with ground collision"""
        self.walk_timer += 0.05
        
        # Update growth cooldown
        if self.growth_cooldown > 0:
            self.growth_cooldown -= 1
        
        # Calculate torso position with walking animation
        torso_pos = self._get_torso_position()
        
        # Update neck physics if performance allows
        if performance_manager.should_update_physics(1.0):
            complexity = self._get_physics_complexity(len(self.neck_segments))
            base_pos = (torso_pos[0], torso_pos[1] - TORSO_RADIUS)
            
            # Use original physics interface but with custom chain handling
            updated_positions = self._update_physics_with_chain_lengths(
                base_pos, (target_x, target_y), ground_world_y, complexity
            )
            
            # Update segment positions
            for i, pos in enumerate(updated_positions):
                if i < len(self.neck_segments):
                    self.neck_segments[i].position = pos
        
        return torso_pos
    
    def _update_physics_with_chain_lengths(self, base_pos, target_pos, ground_world_y, complexity):
        """Custom physics update that respects chain lengths"""
        positions = []
        current_pos = base_pos
        
        for i, segment in enumerate(self.neck_segments):
            if i == 0:
                # For the first segment, check if it's a bottom ellipse that needs special positioning
                if (segment.type == 'ellipse' and 
                    hasattr(segment, 'is_bottom_segment') and 
                    segment.is_bottom_segment):
                    # Keep the existing position for bottom ellipse segments - don't reset to base_pos
                    positions.append(segment.position)
                    current_pos = segment.position
                else:
                    # Regular first segment sits at base position
                    positions.append(base_pos)
                    current_pos = base_pos
                continue
            
            # Get chain length for this segment
            if hasattr(segment, 'chain_length'):
                chain_length = segment.chain_length
            else:
                chain_length = SEGMENT_LENGTH
            
            # Simple physics with proper chain length
            direction = self._get_direction(current_pos, target_pos)
            desired_pos = self._move_towards(current_pos, direction, chain_length)
            
            # Apply stiffness
            old_pos = segment.position
            stiffness = 0.15
            new_x = old_pos[0] * (1 - stiffness) + desired_pos[0] * stiffness
            new_y = old_pos[1] * (1 - stiffness) + desired_pos[1] * stiffness
            
            # Maintain proper chain length constraint
            constrained_pos = self._constrain_length(current_pos, (new_x, new_y), chain_length)
            
            # Apply ground collision
            radius = HEAD_RADIUS if i == len(self.neck_segments)-1 else NECK_RADIUS
            final_y = self._apply_ground_collision(constrained_pos[0], constrained_pos[1], ground_world_y, radius)
            
            final_pos = (constrained_pos[0], final_y)
            positions.append(final_pos)
            current_pos = final_pos
        
        return positions
    
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
    
    def _apply_ground_collision(self, x, y, ground_y, radius):
        """Prevent segments from going below ground level"""
        min_y = ground_y - radius
        return min(y, min_y)
    
    def _get_torso_position(self):
        """Calculate torso position with walking animation"""
        step_phase = (math.sin(self.walk_timer) + 1) / 2
        
        # Base torso position at ground level
        base_y = self.y
        
        # Jerky zombie walk animation (moving up from ground)
        if step_phase > 0.3:
            torso_y = base_y - step_phase * 20
        else:
            torso_y = base_y - 14 + math.sin(self.walk_timer * 12) * 6
        
        torso_x = self.x + math.sin(self.walk_timer * 0.5) * 15
        
        return (torso_x, torso_y)
    
    def _get_physics_complexity(self, segment_count):
        """Determine physics complexity based on segment count"""
        if segment_count > 200:
            return 'simple'
        elif segment_count > 150:
            return 'medium'
        else:
            return 'normal'
    
    def get_neck_segment_count(self):
        """Get the current number of neck segments"""
        return len(self.neck_segments)
    
    def get_total_neck_length(self):
        """Get the actual total neck length accounting for consolidation"""
        total_length = 0
        for seg in self.neck_segments:
            if hasattr(seg, 'chain_length'):
                total_length += seg.chain_length
            else:
                total_length += SEGMENT_LENGTH
        return total_length
    
    def get_neck_segment_count_for_zoom(self):
        """Get equivalent segment count for zoom calculation (based on actual length)"""
        return int(self.get_total_neck_length() / SEGMENT_LENGTH)
    
    def add_neck_segment(self):
        """Add a new neck segment when space is held, with structured consolidation"""
        if (len(self.neck_segments) < MAX_NECK_SEGMENTS and 
            self.growth_cooldown <= 0):
            
            # Add cooldown to prevent too rapid growth
            self.growth_cooldown = 3  # 3 frames between additions
            
            # Insert new regular segment before the head
            if len(self.neck_segments) > 1:
                head_pos = self.neck_segments[-1].position
                neck_pos = self.neck_segments[-2].position
                new_segment = NeckSegment(neck_pos, 'regular', 1, 0, False)
                self.neck_segments.insert(-1, new_segment)
            else:
                # First segment case
                base_y = self.y - TORSO_RADIUS - SEGMENT_LENGTH
                new_segment = NeckSegment((self.x, base_y), 'regular', 1, 0, True)
                self.neck_segments.append(new_segment)
            
            # Check if we need to consolidate with structured pattern
            self._consolidate_structured()
    
    def _consolidate_structured(self):
        """Structured consolidation maintaining 5 regular segments at top"""
        # Always keep 5 regular segments at the top (plus head)
        # So we need at least 11 segments before first consolidation (5 + 5 to consolidate + 1 head)
        if len(self.neck_segments) < 11:
            return
            
        # Find the consolidation boundary - always keep last 6 segments (5 regular + head)
        consolidation_end = len(self.neck_segments) - 6
        
        # Get segments available for consolidation (excluding the top 5 + head)
        consolidatable_segments = self.neck_segments[:consolidation_end]
        
        if len(consolidatable_segments) < 5:
            return
            
        # Consolidate from bottom up in structured pattern
        self._perform_structured_consolidation(consolidatable_segments, consolidation_end)
    
    def _perform_structured_consolidation(self, segments, end_index):
        """Perform consolidation following the structured pattern with proper base positioning"""
        # Work from bottom (index 0) upward
        i = 0
        new_segments = []
        
        while i < len(segments):
            current_seg = segments[i]
            
            if current_seg.type == 'regular':
                # Try to consolidate 5 regular segments
                if i + 4 < len(segments):
                    # Check if we have 5 consecutive regular segments
                    regular_group = segments[i:i+5]
                    if all(seg.type == 'regular' and seg.consolidation_level == 0 for seg in regular_group):
                        # Mark if this is the bottom-most segment (first in neck)
                        is_bottom = (i == 0)
                        
                        # Consolidate these 5 into a level 1 ellipse
                        consolidated = self._create_consolidated_segment_with_chain(regular_group, 1, is_bottom)
                        new_segments.append(consolidated)
                        i += 5
                        continue
                
                # Can't consolidate, keep as is
                new_segments.append(current_seg)
                i += 1
                
            elif current_seg.type == 'ellipse':
                # Try to consolidate ellipses of the same level
                level = current_seg.consolidation_level
                
                # Look for 5 ellipses of the same level to consolidate
                ellipse_group = []
                j = i
                while (j < len(segments) and 
                       len(ellipse_group) < 5 and
                       segments[j].type == 'ellipse' and
                       segments[j].consolidation_level == level):
                    ellipse_group.append(segments[j])
                    j += 1
                
                if len(ellipse_group) == 5:
                    # Mark if this is the bottom-most segment
                    is_bottom = (i == 0)
                    
                    # Consolidate 5 ellipses into next level
                    consolidated = self._create_consolidated_segment_with_chain(ellipse_group, level + 1, is_bottom)
                    new_segments.append(consolidated)
                    i = j
                else:
                    # Can't consolidate, keep as is
                    new_segments.append(current_seg)
                    i += 1
            else:
                new_segments.append(current_seg)
                i += 1
        
        # Replace the consolidatable part of neck_segments
        self.neck_segments = new_segments + self.neck_segments[end_index:]
    
    def _create_consolidated_segment_with_chain(self, segment_group, new_level, is_bottom_segment):
        """Create a consolidated segment that maintains proper chain positioning above the base"""
        first_segment = segment_group[0]
        
        # Calculate total height multiplier (sum of all segments being consolidated)
        total_height_multiplier = sum(seg.height_multiplier for seg in segment_group)
        ellipse_height = total_height_multiplier * SEGMENT_LENGTH
        
        # For bottom segments, position physics point so ellipse bottom sits on torso top
        if is_bottom_segment:
            # Torso top position
            torso_top_y = self.y - TORSO_RADIUS
            # Physics point (top of ellipse) should be positioned so that when the ellipse
            # extends downward by ellipse_height, its bottom reaches torso_top_y
            # So: physics_position + ellipse_height = torso_top_y
            # Therefore: physics_position = torso_top_y - ellipse_height
            physics_position = (first_segment.position[0], torso_top_y - ellipse_height)
        else:
            # For non-bottom segments, use the first segment's position
            physics_position = first_segment.position
        
        # Create new consolidated segment at the proper position
        consolidated = NeckSegment(
            physics_position,
            'ellipse',
            total_height_multiplier,
            new_level,
            is_bottom_segment
        )
        
        # Store the chain length for physics
        consolidated.chain_length = ellipse_height
        
        return consolidated
    
    def get_segment_info_for_rendering(self):
        """Get segment information for the renderer"""
        info = []
        for seg in self.neck_segments:
            # Include consolidation level in the segment type for rendering
            seg_type = seg.type
            if seg.type == 'ellipse':
                seg_type = f'ellipse_L{seg.consolidation_level}'
            
            info.append((seg.position, seg_type, seg.get_radius()))
        return info
    
    def get_consolidation_stats(self):
        """Get statistics about consolidation levels for debugging"""
        stats = {}
        total_value = 0
        
        for seg in self.neck_segments:
            if seg.type == 'regular':
                key = "Regular (L0)"
            else:
                key = f"Ellipse L{seg.consolidation_level} (×{seg.height_multiplier})"
            
            stats[key] = stats.get(key, 0) + 1
            total_value += seg.height_multiplier
            
        # Add total actual length
        stats["Total Length"] = total_value
        return stats