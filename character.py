# character.py - Character system with segment consolidation
import math
from config import *
from physics import NeckPhysics

class NeckSegment:
    """Represents a single neck segment, either regular or consolidated ellipse"""
    
    def __init__(self, position, segment_type='regular', height_multiplier=1):
        self.position = position  # (x, y)
        self.type = segment_type  # 'regular' or 'ellipse'
        self.height_multiplier = height_multiplier  # How many regular segments this represents
    
    def get_radius(self):
        """Get the radius for rendering this segment"""
        if self.type == 'ellipse':
            return NECK_RADIUS * 1.2  # Slightly larger for ellipses
        return NECK_RADIUS
    
    def get_height(self):
        """Get the height of this segment"""
        return SEGMENT_LENGTH * self.height_multiplier

class Character:
    """Main character with physics-based neck and segment consolidation"""
    
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
            segment = NeckSegment((self.x, y), 'regular', 1)
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
            
            # Convert segments to positions for physics
            positions = [seg.position for seg in self.neck_segments]
            
            updated_positions = self.physics.update_segments(
                positions, base_pos, (target_x, target_y), 
                ground_world_y, complexity
            )
            
            # Update segment positions
            for i, pos in enumerate(updated_positions):
                if i < len(self.neck_segments):
                    self.neck_segments[i].position = pos
        
        return torso_pos
    
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
    
    def add_neck_segment(self):
        """Add a new neck segment when space is held, with consolidation logic"""
        if (len(self.neck_segments) < MAX_NECK_SEGMENTS and 
            self.growth_cooldown <= 0):
            
            # Add cooldown to prevent too rapid growth
            self.growth_cooldown = 3  # 3 frames between additions
            
            # Insert new regular segment before the head
            if len(self.neck_segments) > 1:
                head_pos = self.neck_segments[-1].position
                neck_pos = self.neck_segments[-2].position
                new_segment = NeckSegment(neck_pos, 'regular', 1)
                self.neck_segments.insert(-1, new_segment)
            else:
                # First segment case
                base_y = self.y - TORSO_RADIUS - SEGMENT_LENGTH
                new_segment = NeckSegment((self.x, base_y), 'regular', 1)
                self.neck_segments.append(new_segment)
            
            # Check if we need to consolidate segments
            if len(self.neck_segments) >= 20:
                self._consolidate_segments()
    
    def _consolidate_segments(self):
        """Consolidate bottom segments into ellipses to maintain performance"""
        total_segments = len(self.neck_segments)
        
        # Count current ellipses
        ellipse_count = sum(1 for seg in self.neck_segments if seg.type == 'ellipse')
        max_ellipses = int(total_segments * 0.25)  # 25% max ellipses
        
        # Only consolidate if we have room for more ellipses
        if ellipse_count < max_ellipses:
            # Find consolidation candidates (bottom 5 regular segments)
            regular_indices = []
            for i, seg in enumerate(self.neck_segments):
                if seg.type == 'regular':
                    regular_indices.append(i)
                if len(regular_indices) >= 5:
                    break
            
            if len(regular_indices) >= 5:
                # Take the first 5 regular segments (bottom ones)
                consolidate_indices = regular_indices[:5]
                
                # Calculate the consolidated position (middle of the 5 segments)
                positions = [self.neck_segments[i].position for i in consolidate_indices]
                avg_x = sum(pos[0] for pos in positions) / 5
                avg_y = sum(pos[1] for pos in positions) / 5
                
                # Create new ellipse segment representing 5 regular segments
                ellipse_segment = NeckSegment((avg_x, avg_y), 'ellipse', 5)
                
                # Remove the 5 regular segments and insert the ellipse
                # Remove in reverse order to maintain indices
                for i in reversed(consolidate_indices):
                    del self.neck_segments[i]
                
                # Insert ellipse at the bottom position
                self.neck_segments.insert(consolidate_indices[0], ellipse_segment)
    
    def get_segment_info_for_rendering(self):
        """Get segment information for the renderer"""
        return [(seg.position, seg.type, seg.get_radius()) for seg in self.neck_segments]