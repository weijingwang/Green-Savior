# character.py - Enhanced character system with top-3 segment optimization
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
    """Enhanced character with top-3 segment optimization for massive scale performance"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.neck_segments = self._create_initial_segments()
        self.walk_timer = 0
        self.growth_cooldown = 0
        
        # Top-3 optimization system
        self.active_segments = []  # Only the top 3 largest segments + head
        self.total_represented_height = 0  # Total height represented by all segments
        self._segment_cache_dirty = True
        
        # Physics optimization - cache frequently used values
        self._cached_torso_pos = None
        self._cache_timer = 0
    
    def _create_initial_segments(self):
        """Create initial neck segments with proper 2-point connectivity and plant head"""
        segments = []
        torso_top = (self.x, self.y - TORSO_RADIUS)
        current_end = torso_top
        
        # Create neck segments (excluding head)
        for i in range(INITIAL_NECK_SEGMENTS - 1):  # -1 because we'll add plant head separately
            start_pos = current_end
            end_pos = (self.x, current_end[1] - SEGMENT_LENGTH)
            
            segment = NeckSegment(start_pos, end_pos, 1, 0, i == 0)
            segments.append(segment)
            current_end = end_pos
        
        # Add plant head structure: left_leaf - left_joint - head - right_joint - right_leaf
        self._add_plant_head_structure(segments, current_end)
        
        self._segment_cache_dirty = True
        return segments
    
    def _add_plant_head_structure(self, segments, neck_end_pos):
        """Add the 5-part plant head structure"""
        # Determine the ellipse level to use (max_level - 1, or create level 1 if max is 0)
        body_segments = segments  # All current segments are body segments
        max_level = max(seg.level for seg in body_segments) if body_segments else 0
        leaf_level = max(1, max_level - 1) if max_level > 0 else 1
        
        # Plant head dimensions
        leaf_length = SEGMENT_LENGTH * 1.5  # Leaves are a bit longer
        joint_length = SEGMENT_LENGTH * 0.8  # Joints are shorter
        head_radius = HEAD_RADIUS
        
        # Calculate positions for the plant head structure
        head_center = (neck_end_pos[0], neck_end_pos[1] - head_radius)
        
        # Left leaf (angled outward)
        left_angle = math.radians(135)  # 45 degrees up and left
        left_leaf_start = (head_center[0] - joint_length/2 * math.cos(math.radians(90)), 
                          head_center[1] - joint_length/2 * math.sin(math.radians(90)))
        left_leaf_end = (left_leaf_start[0] + leaf_length * math.cos(left_angle),
                        left_leaf_start[1] + leaf_length * math.sin(left_angle))
        
        # Left joint (connecting neck to head)
        left_joint_start = neck_end_pos
        left_joint_end = left_leaf_start
        
        # Right joint (connecting head to right leaf) 
        right_joint_start = (head_center[0] + joint_length/2 * math.cos(math.radians(90)), 
                           head_center[1] - joint_length/2 * math.sin(math.radians(90)))
        right_joint_end = head_center
        
        # Right leaf (angled outward)
        right_angle = math.radians(45)  # 45 degrees up and right
        right_leaf_start = right_joint_start
        right_leaf_end = (right_leaf_start[0] + leaf_length * math.cos(right_angle),
                         right_leaf_start[1] + leaf_length * math.sin(right_angle))
        
        # Create the 5 segments: left_leaf, left_joint, head, right_joint, right_leaf
        # Left leaf (ellipse)
        left_leaf = NeckSegment(left_leaf_start, left_leaf_end, 
                               height=leaf_level * NECK_TO_CONSOLIDATE, 
                               level=leaf_level, is_bottom=False)
        segments.append(left_leaf)
        
        # Left joint (ellipse)
        left_joint = NeckSegment(left_joint_start, left_joint_end,
                                height=leaf_level * NECK_TO_CONSOLIDATE,
                                level=leaf_level, is_bottom=False)
        segments.append(left_joint)
        
        # Head (special head segment)
        head = NeckSegment(head_center, head_center, 1, -1, False)  # level -1 for special head
        head.type = 'head'
        segments.append(head)
        
        # Right joint (ellipse) 
        right_joint = NeckSegment(right_joint_end, right_joint_start,
                                 height=leaf_level * NECK_TO_CONSOLIDATE,
                                 level=leaf_level, is_bottom=False)
        segments.append(right_joint)
        
        # Right leaf (ellipse)
        right_leaf = NeckSegment(right_leaf_start, right_leaf_end,
                                height=leaf_level * NECK_TO_CONSOLIDATE,
                                level=leaf_level, is_bottom=False)
        segments.append(right_leaf)
    
    def _update_active_segments(self):
        """Update active segments using top-3 level system, always including plant head structure"""
        if not self._segment_cache_dirty:
            return
        
        if not self.neck_segments:
            self.active_segments = []
            self.total_represented_height = 0
            return
        
        # Plant head structure: always include the last 5 segments (leaves + joints + head)
        plant_head_segments = self.neck_segments[-5:] if len(self.neck_segments) >= 5 else self.neck_segments
        neck_body_segments = self.neck_segments[:-5] if len(self.neck_segments) >= 5 else []
        
        if not neck_body_segments:
            self.active_segments = plant_head_segments
            self.total_represented_height = sum(seg.height for seg in self.neck_segments)
            return
        
        # Find the maximum level present in neck body segments (excluding plant head)
        max_level = max(seg.level for seg in neck_body_segments)
        
        # Calculate the cutoff: only render levels >= (max_level - 2)
        min_active_level = max(0, max_level - 2)
        
        # Collect neck body segments with level >= min_active_level
        active_neck_segments = [seg for seg in neck_body_segments if seg.level >= min_active_level]
        
        # Combine active neck + plant head structure
        self.active_segments = active_neck_segments + plant_head_segments
        
        # Calculate total height represented by all segments
        self.total_represented_height = sum(seg.height for seg in self.neck_segments)
        
        # Ensure connectivity (but respect plant head structure)
        self._ensure_active_segment_connectivity_with_plant_head()
        
        self._segment_cache_dirty = False
    
    def _ensure_active_segment_connectivity_with_plant_head(self):
        """Ensure connectivity while preserving plant head structure"""
        if len(self.active_segments) < 6:  # Need at least 1 neck + 5 plant head segments
            return
        
        # Split into neck segments and plant head segments
        neck_segments = self.active_segments[:-5]
        plant_head_segments = self.active_segments[-5:]
        
        # Handle neck connectivity
        if neck_segments:
            torso_top = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS) if self._cached_torso_pos else (self.x, self.y - TORSO_RADIUS)
            current_end = torso_top
            
            for segment in neck_segments:
                segment.start_pos = current_end
                # Maintain segment's direction and length
                current_length = segment.chain_length
                current_angle = segment.get_angle()
                segment.end_pos = (
                    current_end[0] + math.cos(current_angle) * current_length,
                    current_end[1] + math.sin(current_angle) * current_length
                )
                current_end = segment.end_pos
            
            # Connect plant head to neck
            neck_end = current_end
        else:
            # No neck segments, connect directly to torso
            neck_end = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS) if self._cached_torso_pos else (self.x, self.y - TORSO_RADIUS)
        
        # Update plant head positions (but maintain their relative structure)
        self._update_plant_head_positions(plant_head_segments, neck_end)
    
    def _update_plant_head_positions(self, plant_head_segments, neck_end_pos):
        """Update plant head segment positions while maintaining structure"""
        if len(plant_head_segments) != 5:
            return
        
        left_leaf, left_joint, head, right_joint, right_leaf = plant_head_segments
        
        # Plant head dimensions (scale with environment but slower)
        base_leaf_length = SEGMENT_LENGTH * 1.5
        base_joint_length = SEGMENT_LENGTH * 0.8
        
        # Calculate head center position
        head_center = (neck_end_pos[0], neck_end_pos[1] - HEAD_RADIUS)
        
        # Update head position
        head.start_pos = head_center
        head.end_pos = head_center
        
        # Update joints and leaves with slight sway based on movement
        sway_angle = math.sin(self.walk_timer * 2) * 0.3  # Gentle sway
        
        # Left side
        left_joint.start_pos = neck_end_pos
        left_joint_end = (head_center[0] - base_joint_length/2, head_center[1])
        left_joint.end_pos = left_joint_end
        
        # Left leaf with sway
        left_angle = math.radians(135) + sway_angle
        left_leaf.start_pos = left_joint_end
        left_leaf.end_pos = (
            left_joint_end[0] + base_leaf_length * math.cos(left_angle),
            left_joint_end[1] + base_leaf_length * math.sin(left_angle)
        )
        
        # Right side  
        right_joint_start = (head_center[0] + base_joint_length/2, head_center[1])
        right_joint.start_pos = head_center
        right_joint.end_pos = right_joint_start
        
        # Right leaf with opposite sway
        right_angle = math.radians(45) - sway_angle
        right_leaf.start_pos = right_joint_start
        right_leaf.end_pos = (
            right_joint_start[0] + base_leaf_length * math.cos(right_angle),
            right_joint_start[1] + base_leaf_length * math.sin(right_angle)
        )
    
    def _ensure_active_segment_connectivity(self):
        """Ensure active segments are properly connected by adjusting positions"""
        if len(self.active_segments) < 2:
            return
        
        # Start from torso
        torso_top = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS) if self._cached_torso_pos else (self.x, self.y - TORSO_RADIUS)
        current_end = torso_top
        
        for i, segment in enumerate(self.active_segments):
            segment.start_pos = current_end
            
            # Maintain the segment's current direction and chain length
            current_length = segment.chain_length
            current_angle = segment.get_angle()
            
            # Update end position
            segment.end_pos = (
                current_end[0] + math.cos(current_angle) * current_length,
                current_end[1] + math.sin(current_angle) * current_length
            )
            
            current_end = segment.end_pos
    
    def update(self, target_x, target_y, performance_manager, ground_world_y):
        """Enhanced update with top-3 optimization"""
        self.walk_timer += 0.05
        self._cache_timer += 1
        
        # Update growth cooldown
        if self.growth_cooldown > 0:
            self.growth_cooldown -= 1
        
        # Cache torso position for multiple uses
        if self._cache_timer % 2 == 0 or self._cached_torso_pos is None:
            self._cached_torso_pos = self._get_torso_position()
        
        # Update active segments (only when needed)
        self._update_active_segments()
        
        # Enhanced physics update ONLY on active segments
        if performance_manager.should_update_physics(1.0):
            self._update_active_physics_2point(target_x, target_y, ground_world_y)
        
        return self._cached_torso_pos
    
    def _update_active_physics_2point(self, target_x, target_y, ground_world_y):
        """Physics update for active segments including plant head structure"""
        if not self.active_segments:
            return
        
        # Split active segments into neck and plant head
        if len(self.active_segments) >= 5:
            neck_segments = self.active_segments[:-5]  # All except last 5
            plant_head_segments = self.active_segments[-5:]  # Last 5 are plant head
        else:
            neck_segments = []
            plant_head_segments = self.active_segments
        
        # Start from torso top
        torso_top = (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS)
        
        # Update neck segments with normal physics
        current_start = torso_top
        
        for i, segment in enumerate(neck_segments):
            # Calculate desired direction toward target (neck follows mouse)
            direction = self._get_direction_to_target(current_start, (target_x, target_y))
            
            # Calculate desired end position
            desired_end = (
                current_start[0] + direction[0] * segment.chain_length,
                current_start[1] + direction[1] * segment.chain_length
            )
            
            # Apply physics with stiffness
            segment_weight = segment.height
            weight_factor = 1.0 / (1.0 + segment_weight * 0.05)
            stiffness = 0.15 * weight_factor
            
            old_end = segment.end_pos
            new_end = (
                old_end[0] * (1 - stiffness) + desired_end[0] * stiffness,
                old_end[1] * (1 - stiffness) + desired_end[1] * stiffness
            )
            
            # Maintain chain length
            actual_direction = self._get_direction_to_target(current_start, new_end)
            constrained_end = (
                current_start[0] + actual_direction[0] * segment.chain_length,
                current_start[1] + actual_direction[1] * segment.chain_length
            )
            
            # Apply ground collision
            final_end = self._apply_ground_collision(constrained_end, ground_world_y, segment.get_radius())
            
            # Update segment
            segment.start_pos = current_start
            segment.end_pos = final_end
            current_start = final_end
        
        # Update plant head with special physics
        if len(plant_head_segments) == 5:
            neck_end = current_start
            self._update_plant_head_physics(plant_head_segments, neck_end, target_x, target_y, ground_world_y)
    
    def _update_plant_head_physics(self, plant_segments, neck_end, target_x, target_y, ground_world_y):
        """Special physics for plant head - head follows target, leaves sway"""
        left_leaf, left_joint, head, right_joint, right_leaf = plant_segments
        
        # Calculate head target position (follows mouse but with some offset)
        head_direction = self._get_direction_to_target(neck_end, (target_x, target_y))
        head_distance = HEAD_RADIUS * 2  # Keep head close to neck end
        
        desired_head_pos = (
            neck_end[0] + head_direction[0] * head_distance,
            neck_end[1] + head_direction[1] * head_distance
        )
        
        # Apply physics to head position with gentle movement
        current_head_pos = head.position
        stiffness = 0.08  # Gentler movement for head
        new_head_pos = (
            current_head_pos[0] * (1 - stiffness) + desired_head_pos[0] * stiffness,
            current_head_pos[1] * (1 - stiffness) + desired_head_pos[1] * stiffness
        )
        
        # Apply ground collision to head
        final_head_pos = self._apply_ground_collision(new_head_pos, ground_world_y, HEAD_RADIUS)
        
        # Update head
        head.start_pos = final_head_pos
        head.end_pos = final_head_pos
        
        # Update plant structure around the head
        self._update_plant_head_positions(plant_segments, neck_end)
        
        # Add some physics-based sway to leaves based on movement
        movement_sway = (target_x - neck_end[0]) * 0.001  # Small sway based on horizontal movement
        
        # Apply sway to leaf positions
        sway_intensity = 0.3 + abs(movement_sway) * 2
        left_sway = math.sin(self.walk_timer * 2 + movement_sway) * sway_intensity
        right_sway = math.sin(self.walk_timer * 2 - movement_sway) * sway_intensity
        
        # Update left leaf with sway
        left_joint_end = left_joint.end_pos
        base_left_angle = math.radians(135)
        left_angle = base_left_angle + left_sway * 0.5
        leaf_length = SEGMENT_LENGTH * 1.5
        
        left_leaf.end_pos = (
            left_joint_end[0] + leaf_length * math.cos(left_angle),
            left_joint_end[1] + leaf_length * math.sin(left_angle)
        )
        
        # Update right leaf with opposite sway  
        right_joint_end = right_joint.end_pos
        base_right_angle = math.radians(45)
        right_angle = base_right_angle - right_sway * 0.5
        
        right_leaf.end_pos = (
            right_joint_end[0] + leaf_length * math.cos(right_angle),
            right_joint_end[1] + leaf_length * math.sin(right_angle)
        )
    
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
        """Add segment while preserving plant head structure"""
        if len(self.neck_segments) >= MAX_NECK_SEGMENTS or self.growth_cooldown > 0:
            return
        
        self.growth_cooldown = 3
        
        # With plant head structure, we need to insert new segments before the plant head
        if len(self.neck_segments) >= 6:  # Need at least 1 neck segment + 5 plant head segments
            # Remove plant head structure temporarily
            plant_head_segments = self.neck_segments[-5:]
            neck_segments = self.neck_segments[:-5]
            
            # Add new segment to neck
            if neck_segments:
                last_neck_segment = neck_segments[-1]
                new_start = last_neck_segment.end_pos
                # Point toward where plant head connects
                direction = self._get_direction_to_target(new_start, plant_head_segments[1].start_pos)  # left_joint start
                new_end = (
                    new_start[0] + direction[0] * SEGMENT_LENGTH,
                    new_start[1] + direction[1] * SEGMENT_LENGTH
                )
                new_segment = NeckSegment(new_start, new_end, 1, 0, False)
                neck_segments.append(new_segment)
            else:
                # First neck segment
                torso_top = (self.x, self.y - TORSO_RADIUS)
                new_end = (self.x, torso_top[1] - SEGMENT_LENGTH)
                new_segment = NeckSegment(torso_top, new_end, 1, 0, True)
                neck_segments.append(new_segment)
            
            # Reconnect plant head to new neck end
            new_neck_end = neck_segments[-1].end_pos
            self._reconnect_plant_head_to_neck(plant_head_segments, new_neck_end)
            
            # Rebuild segments list
            self.neck_segments = neck_segments + plant_head_segments
        else:
            # Not enough segments yet, add normally but maintain plant structure
            torso_top = (self.x, self.y - TORSO_RADIUS) if self._cached_torso_pos is None else (self._cached_torso_pos[0], self._cached_torso_pos[1] - TORSO_RADIUS)
            new_end = (torso_top[0], torso_top[1] - SEGMENT_LENGTH)
            new_segment = NeckSegment(torso_top, new_end, 1, 0, len(self.neck_segments) == 0)
            
            if len(self.neck_segments) >= 5:
                # Insert before plant head
                self.neck_segments.insert(-5, new_segment)
            else:
                # Still building initial structure
                self.neck_segments.insert(-1 if self.neck_segments else 0, new_segment)
        
        # Mark cache as dirty
        self._segment_cache_dirty = True
        
        # Check for consolidation (but protect plant head)
        self._maybe_consolidate_with_plant_head()
    
    def _reconnect_plant_head_to_neck(self, plant_head_segments, neck_end):
        """Reconnect plant head structure to new neck end position"""
        if len(plant_head_segments) != 5:
            return
        
        left_leaf, left_joint, head, right_joint, right_leaf = plant_head_segments
        
        # Update left joint to connect to neck
        left_joint.start_pos = neck_end
        
        # Maintain relative positions but adjust to new connection point
        head_center = (neck_end[0], neck_end[1] - HEAD_RADIUS * 1.5)
        joint_length = SEGMENT_LENGTH * 0.8
        
        # Update positions
        left_joint.end_pos = (head_center[0] - joint_length/2, head_center[1])
        head.start_pos = head_center
        head.end_pos = head_center
        right_joint.start_pos = head_center
        right_joint.end_pos = (head_center[0] + joint_length/2, head_center[1])
        
        # Update leaf positions
        leaf_length = SEGMENT_LENGTH * 1.5
        left_angle = math.radians(135)
        right_angle = math.radians(45)
        
        left_leaf.start_pos = left_joint.end_pos
        left_leaf.end_pos = (
            left_leaf.start_pos[0] + leaf_length * math.cos(left_angle),
            left_leaf.start_pos[1] + leaf_length * math.sin(left_angle)
        )
        
        right_leaf.start_pos = right_joint.end_pos
        right_leaf.end_pos = (
            right_leaf.start_pos[0] + leaf_length * math.cos(right_angle),
            right_leaf.start_pos[1] + leaf_length * math.sin(right_angle)
        )
    
    def _maybe_consolidate_with_plant_head(self):
        """Consolidation logic that protects the plant head structure"""
        # Need enough segments for consolidation + plant head protection
        min_segments = NECK_TO_CONSOLIDATE + UNTOUCHED_NECK_SEGMENTS + 5 + 1  # +5 for plant head
        if len(self.neck_segments) < min_segments:
            return
        
        # Separate plant head from consolidation
        plant_head_segments = self.neck_segments[-5:]
        neck_body_segments = self.neck_segments[:-5]
        
        # Keep some untouched neck segments before plant head
        untouched_segments = neck_body_segments[-(UNTOUCHED_NECK_SEGMENTS):]
        consolidatable_segments = neck_body_segments[:-(UNTOUCHED_NECK_SEGMENTS)]
        
        if len(consolidatable_segments) < NECK_TO_CONSOLIDATE:
            return
        
        # Find consolidation opportunities
        level_counts = {}
        level_segments = {}
        
        for seg in consolidatable_segments:
            level = seg.level
            if level not in level_counts:
                level_counts[level] = 0
                level_segments[level] = []
            level_counts[level] += 1
            level_segments[level].append(seg)
        
        # Find the lowest level with enough segments
        consolidation_level = None
        for level in sorted(level_counts.keys()):
            if level_counts[level] >= NECK_TO_CONSOLIDATE:
                consolidation_level = level
                break
        
        if consolidation_level is not None:
            self._consolidate_level_with_plant_head(consolidation_level, consolidatable_segments, 
                                                   untouched_segments, plant_head_segments)
    
    def _consolidate_level_with_plant_head(self, level, consolidatable_segments, untouched_segments, plant_head_segments):
        """Consolidate segments while preserving plant head"""
        new_consolidatable = []
        segments_to_consolidate = []
        
        # Collect segments for consolidation
        for seg in consolidatable_segments:
            if seg.level == level and len(segments_to_consolidate) < NECK_TO_CONSOLIDATE:
                segments_to_consolidate.append(seg)
            else:
                new_consolidatable.append(seg)
        
        # Consolidate if we have enough
        if len(segments_to_consolidate) == NECK_TO_CONSOLIDATE:
            total_height = sum(seg.height for seg in segments_to_consolidate)
            start_pos = segments_to_consolidate[0].start_pos
            end_pos = segments_to_consolidate[-1].end_pos
            is_bottom = (segments_to_consolidate[0] == consolidatable_segments[0])
            
            consolidated = NeckSegment(start_pos, end_pos, total_height, level + 1, is_bottom)
            new_consolidatable.append(consolidated)
        else:
            new_consolidatable.extend(segments_to_consolidate)
        
        # Rebuild segments: consolidated + untouched + plant head
        all_new_segments = new_consolidatable + untouched_segments
        self._ensure_connectivity(all_new_segments)
        
        # Update segments list
        self.neck_segments = all_new_segments + plant_head_segments
        
        # Mark cache dirty and check for more consolidation
        self._segment_cache_dirty = True
        self._maybe_consolidate_with_plant_head()
    
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
            # Mark cache as dirty after consolidation
            self._segment_cache_dirty = True
    
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
    
    # Modified getter methods to use active segments for rendering
    def get_neck_segments_for_rendering(self):
        """Get only active segments for rendering - massive performance boost"""
        self._update_active_segments()
        return self.active_segments
    
    def get_neck_segment_count(self):
        """Get count of ALL segments (for UI display)"""
        return len(self.neck_segments)
    
    def get_active_segment_count(self):
        """Get count of active segments"""
        self._update_active_segments()
        return len(self.active_segments)
    
    def get_total_neck_length(self):
        """Get total length using represented height (not just active segments)"""
        return self.total_represented_height * SEGMENT_LENGTH
    
    def get_neck_segment_count_for_zoom(self):
        """Use total represented height for zoom calculation"""
        self._update_active_segments()  # Ensure total_represented_height is current
        return self.total_represented_height
    
    def get_segment_info_for_rendering(self):
        """Enhanced rendering info with 2-point data - only for active segments"""
        self._update_active_segments()
        info = []
        for seg in self.active_segments:
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
        """Enhanced stats showing level-based filtering system"""
        stats = {}
        total_height = 0
        
        # Group all segments by level for comprehensive stats
        all_levels = {}
        active_levels = {}
        
        self._update_active_segments()
        active_set = set(self.active_segments)
        
        # Find max level and calculate active range
        body_segments = [seg for seg in self.neck_segments if seg != self.neck_segments[-1]]
        max_level = max(seg.level for seg in body_segments) if body_segments else 0
        min_active_level = max(0, max_level - 2)
        
        # Analyze all segments
        for seg in self.neck_segments:
            level_key = f"Level {seg.level}"
            if seg.is_ellipse:
                level_key += f" (×{seg.height})"
            
            # Count totals
            all_levels[level_key] = all_levels.get(level_key, 0) + 1
            total_height += seg.height
            
            # Count actives
            if seg in active_set:
                active_levels[level_key] = active_levels.get(level_key, 0) + 1
        
        # Display format showing level-based filtering
        stats[f"MAX LEVEL: {max_level}"] = f"Rendering L{max_level} to L{min_active_level}"
        stats[""] = ""  # Spacer
        
        # Show each level with active status
        for level in sorted(all_levels.keys(), key=lambda x: int(x.split()[1]), reverse=True):
            active_count = active_levels.get(level, 0)
            total_count = all_levels[level]
            level_num = int(level.split()[1])
            
            if level_num >= min_active_level:
                stats[f"✓ {level}"] = f"{active_count}/{total_count} ACTIVE"
            else:
                stats[f"✗ {level}"] = f"0/{total_count} skipped"
        
        # Add summary info
        stats["  "] = ""  # Spacer
        stats["Active Segments"] = f"{len(self.active_segments)}/{len(self.neck_segments)}"
        stats["Performance Gain"] = f"{len(self.neck_segments) - len(self.active_segments)} segments skipped"
        stats["Total Height"] = total_height
        
        return stats