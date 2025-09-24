# character.py - Streamlined character system with optimized consolidation
import math
from config import *
from physics import NeckPhysics

class NeckSegment:
    """Simplified neck segment with consolidated properties"""
    
    def __init__(self, position, height=1, level=0, is_bottom=False):
        self.position = position  # (x, y)
        self.height = height  # How many base segments this represents
        self.level = level  # Consolidation level (0=regular, 1+=ellipse)
        self.is_bottom = is_bottom
        self.chain_length = height * SEGMENT_LENGTH
        
        # Maintain compatibility with existing renderer
        self.type = 'ellipse' if level > 0 else 'regular'
        self.height_multiplier = height  # Alias for compatibility
        self.consolidation_level = level  # Alias for compatibility
    
    @property
    def is_ellipse(self):
        return self.level > 0
    
    def get_radius(self):
        if self.is_ellipse:
            return NECK_RADIUS * (1.2 + 0.3 * self.level)
        return NECK_RADIUS
    
    def get_width_multiplier(self):
        if self.is_ellipse:
            return 1.4 + 0.2 * self.level
        return 1.0

class Character:
    """Optimized character with simplified physics and consolidation"""
    
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
        """Create initial neck segments"""
        segments = []
        base_y = self.y - TORSO_RADIUS
        
        for i in range(INITIAL_NECK_SEGMENTS):
            y = base_y - (i + 1) * SEGMENT_LENGTH
            segment = NeckSegment((self.x, y), 1, 0, i == 0)
            segments.append(segment)
        
        return segments
    
    def update(self, target_x, target_y, performance_manager, ground_world_y):
        """Optimized update with cached calculations"""
        self.walk_timer += 0.05
        self._cache_timer += 1
        
        # Update growth cooldown
        if self.growth_cooldown > 0:
            self.growth_cooldown -= 1
        
        # Cache torso position for multiple uses
        if self._cache_timer % 2 == 0 or self._cached_torso_pos is None:
            self._cached_torso_pos = self._get_torso_position()
        
        # Simplified physics update
        if performance_manager.should_update_physics(1.0):
            self._update_neck_physics(target_x, target_y, ground_world_y)
        
        return self._cached_torso_pos
    
    def _update_neck_physics(self, target_x, target_y, ground_world_y):
        """Streamlined physics calculation with proper bottom segment handling"""
        if not self.neck_segments:
            return
        
        # Handle bottom segment as fixed extension of torso (no physics)
        torso_top = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS)
        
        if self.neck_segments[0].is_bottom and self.neck_segments[0].is_ellipse:
            # Bottom segment is a consolidated ellipse - position it as fixed extension
            bottom_segment = self.neck_segments[0]
            bottom_end_y = torso_top[1] - bottom_segment.chain_length
            bottom_segment.position = (torso_top[0], bottom_end_y)
            
            # Physics chain starts from the END of the bottom segment
            current_pos = (torso_top[0], bottom_end_y)
            physics_start_index = 1
        else:
            # No consolidated bottom segment, physics starts from torso
            current_pos = torso_top
            physics_start_index = 0
        
        # Apply physics to remaining segments
        for i in range(physics_start_index, len(self.neck_segments)):
            segment = self.neck_segments[i]
            
            if i == physics_start_index and physics_start_index == 0:
                # First segment when no bottom consolidation - just position it
                segment.position = current_pos
                current_pos = (current_pos[0], current_pos[1] - segment.chain_length)
                continue
            
            # Calculate desired position toward target
            direction = self._get_direction_to_target(current_pos, (target_x, target_y))
            desired_pos = (
                current_pos[0] + direction[0] * segment.chain_length,
                current_pos[1] + direction[1] * segment.chain_length
            )
            
            # Apply stiffness and constraint
            old_pos = segment.position
            stiffness = 0.15
            new_pos = (
                old_pos[0] * (1 - stiffness) + desired_pos[0] * stiffness,
                old_pos[1] * (1 - stiffness) + desired_pos[1] * stiffness
            )
            
            # Maintain chain length and apply ground collision
            constrained_pos = self._constrain_to_chain_length(current_pos, new_pos, segment.chain_length)
            final_pos = self._apply_ground_collision(constrained_pos, ground_world_y, segment.get_radius())
            
            segment.position = final_pos
            current_pos = final_pos
    
    def _get_direction_to_target(self, from_pos, target_pos):
        """Get normalized direction vector"""
        dx = target_pos[0] - from_pos[0]
        dy = target_pos[1] - from_pos[1]
        distance = math.hypot(dx, dy)
        
        if distance < 0.001:  # Avoid division by zero
            return (0, -1)  # Default upward direction
        
        return (dx / distance, dy / distance)
    
    def _constrain_to_chain_length(self, anchor_pos, target_pos, chain_length):
        """Constrain position to exact chain length"""
        direction = self._get_direction_to_target(anchor_pos, target_pos)
        return (
            anchor_pos[0] + direction[0] * chain_length,
            anchor_pos[1] + direction[1] * chain_length
        )
    
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
        """Add segment and consolidate when needed"""
        if len(self.neck_segments) >= MAX_NECK_SEGMENTS or self.growth_cooldown > 0:
            return
        
        self.growth_cooldown = 3
        
        # Add new segment before head
        if len(self.neck_segments) > 1:
            head_pos = self.neck_segments[-1].position
            neck_pos = self.neck_segments[-2].position
            new_segment = NeckSegment(neck_pos, 1, 0, False)
            self.neck_segments.insert(-1, new_segment)
        else:
            base_y = self.y - TORSO_RADIUS - SEGMENT_LENGTH
            new_segment = NeckSegment((self.x, base_y), 1, 0, True)
            self.neck_segments.append(new_segment)
        
        # Check for consolidation
        self._maybe_consolidate()
    
    def _maybe_consolidate(self):
        """Simplified consolidation logic"""
        if len(self.neck_segments) < 11:  # Need minimum segments
            return
        
        # Keep head separate
        head = self.neck_segments[-1]
        body_segments = self.neck_segments[:-1]
        
        # Count segments by level
        level_counts = {}
        for seg in body_segments:
            level_counts[seg.level] = level_counts.get(seg.level, 0) + 1
        
        # Find level that needs consolidation (has 10+ segments)
        consolidation_level = None
        for level, count in level_counts.items():
            if count >= 10:
                consolidation_level = level
                break
        
        if consolidation_level is not None:
            self._consolidate_level(consolidation_level)
    
    def _consolidate_level(self, level):
        """Consolidate 5 segments of given level into next level with proper bottom segment handling"""
        head = self.neck_segments[-1]
        body_segments = self.neck_segments[:-1]
        
        new_segments = []
        i = 0
        
        while i < len(body_segments):
            segment = body_segments[i]
            
            if segment.level == level:
                # Try to collect 5 segments of this level
                group = []
                j = i
                while j < len(body_segments) and len(group) < 5 and body_segments[j].level == level:
                    group.append(body_segments[j])
                    j += 1
                
                if len(group) == 5:
                    # Consolidate these 5 segments
                    total_height = sum(seg.height for seg in group)
                    is_bottom = (i == 0)  # First segment in neck becomes bottom
                    
                    # Position the consolidated segment
                    if is_bottom:
                        # Bottom segment: position it as fixed extension from torso
                        # Don't use current position, calculate from torso
                        torso_top_y = self.y - TORSO_RADIUS
                        position = (group[0].position[0], torso_top_y - total_height * SEGMENT_LENGTH)
                    else:
                        # Regular consolidation: use first segment's position
                        position = group[0].position
                    
                    consolidated = NeckSegment(position, total_height, level + 1, is_bottom)
                    
                    # Mark as bottom segment if consolidating the first segments
                    if is_bottom:
                        consolidated.is_bottom_segment = True  # Extra flag for renderer compatibility
                    
                    new_segments.append(consolidated)
                    i = j
                else:
                    # Can't consolidate, keep original
                    new_segments.append(segment)
                    i += 1
            else:
                new_segments.append(segment)
                i += 1
        
        # Update segments
        self.neck_segments = new_segments + [head]
    
    # Simplified getter methods
    def get_neck_segment_count(self):
        return len(self.neck_segments)
    
    def get_total_neck_length(self):
        return sum(seg.chain_length for seg in self.neck_segments)
    
    def get_neck_segment_count_for_zoom(self):
        return int(self.get_total_neck_length() / SEGMENT_LENGTH)
    
    def get_segment_info_for_rendering(self):
        """Simplified rendering info"""
        info = []
        for seg in self.neck_segments:
            seg_type = f'ellipse_L{seg.level}' if seg.is_ellipse else 'regular'
            info.append((seg.position, seg_type, seg.get_radius()))
        return info
    
    def get_consolidation_stats(self):
        """Simple stats for debugging"""
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
        return stats