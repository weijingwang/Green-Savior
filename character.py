# character.py - Fixed character system with ground collision support
import math
from config import *
from physics import NeckPhysics

class Character:
    """Main character with physics-based neck"""
    
    def __init__(self):
        self.x = 0
        self.y = 0  # Character torso at ground level (world Y = 0)
        self.neck_segments = self._create_initial_segments()
        self.walk_timer = 0
        self.physics = NeckPhysics()
    
    def _create_initial_segments(self):
        """Create initial neck segments starting from torso"""
        segments = []
        # Start from top of torso (torso center is at ground level)
        base_y = self.y - TORSO_RADIUS
        for i in range(INITIAL_NECK_SEGMENTS):
            y = base_y - (i + 1) * SEGMENT_LENGTH
            segments.append((self.x, y))
        return segments
    
    def update(self, target_x, target_y, performance_manager, ground_world_y):
        """Update character position and neck physics with ground collision"""
        self.walk_timer += 0.05
        
        # Calculate torso position with walking animation
        torso_pos = self._get_torso_position()
        
        # Update neck physics if performance allows
        if performance_manager.should_update_physics(1.0):
            complexity = self._get_physics_complexity(len(self.neck_segments))
            base_pos = (torso_pos[0], torso_pos[1] - TORSO_RADIUS)
            
            self.neck_segments = self.physics.update_segments(
                self.neck_segments, base_pos, (target_x, target_y), 
                ground_world_y, complexity
            )
        
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
        """Add a new neck segment when collecting spots"""
        if len(self.neck_segments) < MAX_NECK_SEGMENTS:
            # Insert new segment before the head
            self.neck_segments.insert(-1, self.neck_segments[-2])