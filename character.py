# character.py - Enhanced character system with 2-point segments for proper connectivity
import math
from config import *
from physics import NeckPhysics

class NeckSegment:
    """Enhanced neck segment with start/end points for proper connectivity"""
    
    def __init__(self, start_pos, end_pos, height=1, level=0, is_bottom=False):
        self.start_pos = start_pos  # (x, y) - connection point to previous segment
        self.end_pos = end_pos      # (x, y) - connection point to next segment
        self.height = height        # How many base segments this represents
        self.level = level          # Consolidation level (0=regular, 1+=ellipse)
        self.is_bottom = is_bottom
        self.chain_length = height * SEGMENT_LENGTH
        
        # Maintain compatibility with existing renderer
        self.type = 'ellipse' if level > 0 else 'regular'
        self.height_multiplier = height  # Alias for compatibility
        self.consolidation_level = level  # Alias for compatibility
    
    @property
    def position(self):
        """Center position for backward compatibility"""
        return (
            (self.start_pos[0] + self.end_pos[0]) / 2,
            (self.start_pos[1] + self.end_pos[1]) / 2
        )
    
    @position.setter
    def position(self, pos):
        """Set position by moving both endpoints to maintain length/angle"""
        current_center = self.position
        dx = pos[0] - current_center[0]
        dy = pos[1] - current_center[1]
        
        self.start_pos = (self.start_pos[0] + dx, self.start_pos[1] + dy)
        self.end_pos = (self.end_pos[0] + dx, self.end_pos[1] + dy)
    
    @property
    def is_ellipse(self):
        return self.level > 0
    
    def get_length(self):
        """Get actual distance between start and end points"""
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        return math.hypot(dx, dy)
    
    def get_angle(self):
        """Get rotation angle in radians"""
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        return math.atan2(dy, dx)
    
    def get_radius(self):
        if self.is_ellipse:
            return NECK_RADIUS * (1.2 + 0.3 * self.level)
        return NECK_RADIUS
    
    def get_width_multiplier(self):
        if self.is_ellipse:
            return 1.4 + 0.2 * self.level
        return 1.0
    
    def set_from_start_and_direction(self, start_pos, direction, length):
        """Set segment from start point, direction vector, and length"""
        self.start_pos = start_pos
        self.end_pos = (
            start_pos[0] + direction[0] * length,
            start_pos[1] + direction[1] * length
        )
    
    def connect_to_previous(self, prev_segment_end):
        """Connect this segment's start to previous segment's end"""
        # Maintain current length and angle, just move start point
        current_length = self.get_length()
        current_angle = self.get_angle()
        
        self.start_pos = prev_segment_end
        self.end_pos = (
            prev_segment_end[0] + math.cos(current_angle) * current_length,
            prev_segment_end[1] + math.sin(current_angle) * current_length
        )

class Character:
    """Enhanced character with 2-point segment physics and rendering"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.neck_segments = self._create_initial_segments()
        self.walk_timer = 0
        self.growth_cooldown = 0
        
        # Physics optimization - cache frequently used values
        self._cached_torso_pos = None
        self._cache_timer = 0
    
    def _create_initial_segments(self):
        """Create initial neck segments with proper 2-point connectivity"""
        segments = []
        torso_top = (self.x, self.y - TORSO_RADIUS)
        current_end = torso_top
        
        for i in range(INITIAL_NECK_SEGMENTS):
            start_pos = current_end
            end_pos = (self.x, current_end[1] - SEGMENT_LENGTH)
            
            segment = NeckSegment(start_pos, end_pos, 1, 0, i == 0)
            segments.append(segment)
            current_end = end_pos
        
        return segments
    
    def update(self, target_x, target_y, performance_manager, ground_world_y):
        """Enhanced update with 2-point physics"""
        self.walk_timer += 0.05
        self._cache_timer += 1
        
        # Update growth cooldown
        if self.growth_cooldown > 0:
            self.growth_cooldown -= 1
        
        # Cache torso position for multiple uses
        if self._cache_timer % 2 == 0 or self._cached_torso_pos is None:
            self._cached_torso_pos = self._get_torso_position()
        
        # Enhanced physics update with 2-point system
        if performance_manager.should_update_physics(1.0):
            self._update_neck_physics_2point(target_x, target_y, ground_world_y)
        
        return self._cached_torso_pos
    
    def _update_neck_physics_2point(self, target_x, target_y, ground_world_y):
        """Enhanced physics with proper 2-point connectivity"""
        if not self.neck_segments:
            return
        
        # Start from torso top
        torso_top = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS)
        
        # Update each segment maintaining connectivity
        current_start = torso_top
        
        for i, segment in enumerate(self.neck_segments):
            is_head = (i == len(self.neck_segments) - 1)
            
            # Calculate desired direction toward target
            if is_head:
                # Head segment points directly toward target
                target_pos = (target_x, target_y)
            else:
                # Body segments use a mix of target direction and chain following
                target_pos = (target_x, target_y)
            
            direction = self._get_direction_to_target(current_start, target_pos)
            
            # Calculate desired end position
            desired_end = (
                current_start[0] + direction[0] * segment.chain_length,
                current_start[1] + direction[1] * segment.chain_length
            )
            
            # Apply physics with stiffness based on segment weight (larger segments move slower)
            segment_weight = segment.height
            weight_factor = 1.0 / (1.0 + segment_weight * 0.05)  # Heavier segments have more inertia
            stiffness = 0.15 * weight_factor
            
            old_end = segment.end_pos
            new_end = (
                old_end[0] * (1 - stiffness) + desired_end[0] * stiffness,
                old_end[1] * (1 - stiffness) + desired_end[1] * stiffness
            )
            
            # Maintain proper chain length
            actual_direction = self._get_direction_to_target(current_start, new_end)
            constrained_end = (
                current_start[0] + actual_direction[0] * segment.chain_length,
                current_start[1] + actual_direction[1] * segment.chain_length
            )
            
            # Apply ground collision to end point
            final_end = self._apply_ground_collision(constrained_end, ground_world_y, segment.get_radius())
            
            # Update segment with connected points
            segment.start_pos = current_start
            segment.end_pos = final_end
            
            # Next segment starts where this one ends
            current_start = final_end
    
    def _get_direction_to_target(self, from_pos, target_pos):
        """Get normalized direction vector"""
        dx = target_pos[0] - from_pos[0]
        dy = target_pos[1] - from_pos[1]
        distance = math.hypot(dx, dy)
        
        if distance < 0.001:  # Avoid division by zero
            return (0, -1)  # Default upward direction
        
        return (dx / distance, dy / distance)
    
    def _apply_ground_collision(self, pos, ground_y, radius):
        """Simple ground collision"""
        min_y = ground_y - radius
        return (pos[0], min(pos[1], min_y))
    
    def _get_torso_position(self):
        """Calculate torso position with walking animation"""
        step_phase = (math.sin(self.walk_timer) + 1) / 2
        
        # Simplified walking animation
        if step_phase > 0.3:
            torso_y = self.y - step_phase * 20
        else:
            torso_y = self.y - 14 + math.sin(self.walk_timer * 12) * 6
        
        torso_x = self.x + math.sin(self.walk_timer * 0.5) * 15
        return (torso_x, torso_y)
    
    def add_neck_segment(self):
        """Add segment with proper 2-point connectivity"""
        if len(self.neck_segments) >= MAX_NECK_SEGMENTS or self.growth_cooldown > 0:
            return
        
        self.growth_cooldown = 3
        
        # Add new segment before head, maintaining connectivity
        if len(self.neck_segments) > 1:
            # Insert before head
            head_segment = self.neck_segments[-1]
            prev_segment = self.neck_segments[-2]
            
            # New segment starts where prev ends, ends where head starts
            new_start = prev_segment.end_pos
            new_end = head_segment.start_pos
            new_segment = NeckSegment(new_start, new_end, 1, 0, False)
            
            # Adjust to proper length
            direction = self._get_direction_to_target(new_start, new_end)
            proper_end = (
                new_start[0] + direction[0] * SEGMENT_LENGTH,
                new_start[1] + direction[1] * SEGMENT_LENGTH
            )
            new_segment.end_pos = proper_end
            
            # Update head to connect properly
            head_segment.start_pos = proper_end
            
            self.neck_segments.insert(-1, new_segment)
        else:
            # First segment after torso
            torso_top = (self.x, self.y - TORSO_RADIUS)
            new_end = (self.x, torso_top[1] - SEGMENT_LENGTH)
            new_segment = NeckSegment(torso_top, new_end, 1, 0, True)
            self.neck_segments.append(new_segment)
        
        # Check for consolidation
        self._maybe_consolidate()
    
    def _maybe_consolidate(self):
        """Fixed consolidation logic with proper untouched segments"""
        # Need at least NECK_TO_CONSOLIDATE + UNTOUCHED_NECK_SEGMENTS + 1 (head) total segments
        min_segments = NECK_TO_CONSOLIDATE + UNTOUCHED_NECK_SEGMENTS + 1
        if len(self.neck_segments) < min_segments:
            return
        
        # Keep head separate and ensure UNTOUCHED_NECK_SEGMENTS remain untouched
        head = self.neck_segments[-1]
        untouched_segments = self.neck_segments[-(UNTOUCHED_NECK_SEGMENTS + 1):-1]  # Exclude head
        consolidatable_segments = self.neck_segments[:-(UNTOUCHED_NECK_SEGMENTS + 1)]
        
        if len(consolidatable_segments) < NECK_TO_CONSOLIDATE:
            return
        
        # Find the lowest level that has at least NECK_TO_CONSOLIDATE segments
        level_counts = {}
        level_segments = {}
        
        for seg in consolidatable_segments:
            level = seg.level
            if level not in level_counts:
                level_counts[level] = 0
                level_segments[level] = []
            level_counts[level] += 1
            level_segments[level].append(seg)
        
        # Find the lowest level with enough segments to consolidate
        consolidation_level = None
        for level in sorted(level_counts.keys()):
            if level_counts[level] >= NECK_TO_CONSOLIDATE:
                consolidation_level = level
                break
        
        if consolidation_level is not None:
            self._consolidate_level_2point(consolidation_level, consolidatable_segments, untouched_segments, head)
    
    def _consolidate_level_2point(self, level, consolidatable_segments, untouched_segments, head):
        """Enhanced consolidation maintaining 2-point connectivity and untouched segments"""
        new_consolidatable = []
        segments_to_consolidate = []
        
        # Collect segments by level
        for seg in consolidatable_segments:
            if seg.level == level and len(segments_to_consolidate) < NECK_TO_CONSOLIDATE:
                segments_to_consolidate.append(seg)
            else:
                new_consolidatable.append(seg)
        
        # Only consolidate if we have exactly NECK_TO_CONSOLIDATE segments of this level
        if len(segments_to_consolidate) == NECK_TO_CONSOLIDATE:
            # Create consolidated segment
            total_height = sum(seg.height for seg in segments_to_consolidate)
            start_pos = segments_to_consolidate[0].start_pos
            end_pos = segments_to_consolidate[-1].end_pos
            is_bottom = (segments_to_consolidate[0] == consolidatable_segments[0])
            
            consolidated = NeckSegment(start_pos, end_pos, total_height, level + 1, is_bottom)
            new_consolidatable.append(consolidated)
        else:
            # Can't consolidate, keep original segments
            new_consolidatable.extend(segments_to_consolidate)
        
        # Ensure proper connectivity in new segment list
        all_new_segments = new_consolidatable + untouched_segments
        self._ensure_connectivity(all_new_segments)
        
        # Update segments (consolidatable + untouched + head)
        self.neck_segments = all_new_segments + [head]
        
        # Check if we can consolidate again (recursive consolidation)
        self._maybe_consolidate()
    
    def _ensure_connectivity(self, segments):
        """Ensure all segments are properly connected"""
        for i in range(1, len(segments)):
            prev_segment = segments[i-1]
            current_segment = segments[i]
            current_segment.start_pos = prev_segment.end_pos
    
    # Getter methods remain the same
    def get_neck_segment_count(self):
        return len(self.neck_segments)
    
    def get_total_neck_length(self):
        return sum(seg.chain_length for seg in self.neck_segments)
    
    def get_neck_segment_count_for_zoom(self):
        return int(self.get_total_neck_length() / SEGMENT_LENGTH)
    
    def get_segment_info_for_rendering(self):
        """Enhanced rendering info with 2-point data"""
        info = []
        for seg in self.neck_segments:
            seg_type = f'ellipse_L{seg.level}' if seg.is_ellipse else 'regular'
            info.append({
                'start': seg.start_pos,
                'end': seg.end_pos,
                'center': seg.position,
                'type': seg_type,
                'radius': seg.get_radius(),
                'angle': seg.get_angle(),
                'length': seg.get_length()
            })
        return info
    
    def get_consolidation_stats(self):
        """Enhanced stats with connectivity info"""
        stats = {}
        total_height = 0
        
        for seg in self.neck_segments:
            if seg.is_ellipse:
                key = f"Ellipse L{seg.level} (×{seg.height})"
            else:
                key = "Regular (L0)"
            
            stats[key] = stats.get(key, 0) + 1
            total_height += seg.height
        
        stats["Total Length"] = total_height
        stats["Avg Segment Length"] = f"{sum(seg.get_length() for seg in self.neck_segments) / len(self.neck_segments):.1f}"
        return stats