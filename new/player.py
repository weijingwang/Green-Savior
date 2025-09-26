import pygame, os
import numpy as np
from pygame.math import Vector2
from constants import *
from utils import Animator

class VineSegment:
    """Represents a segment at any consolidation level"""
    def __init__(self, position, level=0, consolidated_count=1, pixels_per_meter=INITIAL_PIXELS_PER_METER):
        self.position = Vector2(position)
        self.old_position = Vector2(position)
        self.pixels_per_meter = pixels_per_meter
        self.level = level  # 0 = base level, 1 = first consolidation, etc.
        self.consolidated_count = consolidated_count  # How many original segments this represents
        self.length = pixels_per_meter * PLANT_SEGMENT_HEIGHT * consolidated_count  # Scaled length
        self.thickness = self.calculate_thickness()
        self.mass = self.calculate_mass()  # New: mass affects physics
    
    def update_scale(self, new_pixels_per_meter):
        """Update segment properties when scale changes"""
        old_pixels_per_meter = self.pixels_per_meter
        scale_ratio = new_pixels_per_meter / old_pixels_per_meter
        
        # Update pixels_per_meter
        self.pixels_per_meter = new_pixels_per_meter
        
        # Scale positions
        self.position *= scale_ratio
        self.old_position *= scale_ratio
        
        # Recalculate length and thickness with new scale
        self.length = new_pixels_per_meter * PLANT_SEGMENT_HEIGHT * self.consolidated_count
        self.thickness = self.calculate_thickness()
        # Note: mass doesn't change with scale, it's based on level/count only
    
    def calculate_thickness(self):
        """Calculate thickness based on level and current scale"""
        base_thickness = 12 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)  # Scale with pixels_per_meter
        level_multiplier = 1.5 ** self.level  # Thicker for higher levels
        return max(2, int(base_thickness * level_multiplier))  # Minimum thickness of 2
    
    def calculate_mass(self):
        """Calculate mass based on level - higher levels are much heavier"""
        base_mass = 1.0
        # Mass increases exponentially with level (heavier segments move much slower)
        mass_multiplier = 2.5 ** self.level  # Each level is 2.5x heavier
        return base_mass * mass_multiplier * self.consolidated_count

class Player:
    def __init__(self, x, y, image_folder="assets/images/player"):
        """
        Enhanced Player class with segment consolidation and mass-based physics
        """
        self.x, self.y = x, y

        self.pixels_per_meter = INITIAL_PIXELS_PER_METER

        # Plant base setup (unchanged)
        base_paths = [os.path.join(image_folder, f"base/base{i}.png") for i in range(1, 19)]
        self.animator = Animator(base_paths, scale=(self.pixels_per_meter * PLANT_BASE_SIZE, self.pixels_per_meter * PLANT_BASE_SIZE), frame_duration=5)
        self.base_image = self.animator.get_image((self.pixels_per_meter * PLANT_BASE_SIZE, self.pixels_per_meter * PLANT_BASE_SIZE))
        self.base_rect = self.base_image.get_rect(center=(x, y))
        
        # Plant head setup (unchanged)
        self.head_image = pygame.image.load(
            os.path.join(image_folder, "head.png")
        ).convert_alpha()
        self.head_image = pygame.transform.scale(self.head_image, (self.pixels_per_meter * PLANT_HEAD_W, self.pixels_per_meter * PLANT_HEAD_H))
        
        # Physics properties - these should scale with pixels_per_meter
        self.base_gravity = 0.2
        self.base_mouse_strength = 0.04
        self.constraint_iterations = 3
        self.damping = 0.98  # This doesn't need scaling
        
        # Initialize with level 0 segments
        self.segments = []
        self.segment_count = INITIAL_SEGMENTS
        start_x = self.base_rect.centerx
        start_y = self.base_rect.top + 50
        
        # Create initial segments
        for i in range(INITIAL_SEGMENTS):
            position = Vector2(start_x, start_y - i * (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT))
            segment = VineSegment(position, level=0, pixels_per_meter=self.pixels_per_meter)
            self.segments.append(segment)
        
        # Head setup
        self.head_rect = self.head_image.get_rect()
        self.update_head_position()
        self.base_position = Vector2(start_x, start_y)
    
    def update_scale(self, new_pixels_per_meter):
        """Update all scaling-related properties when pixels_per_meter changes"""
        old_pixels_per_meter = self.pixels_per_meter
        scale_ratio = new_pixels_per_meter / old_pixels_per_meter
        
        # Update player's pixels_per_meter
        self.pixels_per_meter = new_pixels_per_meter
        
        # Scale player position
        self.x *= scale_ratio
        self.y *= scale_ratio
        
        # Scale base position
        self.base_position *= scale_ratio
        
        # Update all segments
        for segment in self.segments:
            segment.update_scale(new_pixels_per_meter)
        
        # Update physics properties that should scale
        self.gravity = self.base_gravity * (new_pixels_per_meter / INITIAL_PIXELS_PER_METER)
        self.mouse_strength = self.base_mouse_strength * (new_pixels_per_meter / INITIAL_PIXELS_PER_METER)
        
        # Update base and head images (these will be handled in the update methods with animator.change_scale)
        # The animator and head image scaling will be handled in update() method
    
    @property
    def gravity(self):
        """Scaled gravity property"""
        return self.base_gravity * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)
    
    @property 
    def mouse_strength(self):
        """Scaled mouse strength property"""
        return self.base_mouse_strength * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)
    
    def can_consolidate_at_level(self, level):
        """Check if we can consolidate segments at a specific level"""
        level_segments = [s for s in self.segments if s.level == level]
        
        # Count segments from the base (oldest first)
        if len(level_segments) < CONSOLIDATION_SEGMENTS + BUFFER_SEGMENTS:
            return False
        
        return True
    
    def consolidate_segments(self):
        """Perform consolidation starting from the base (oldest segments first)"""
        max_level = max(s.level for s in self.segments) if self.segments else 0
        
        # Check each level starting from 0
        for level in range(max_level + 1):
            while self.can_consolidate_at_level(level):
                self._consolidate_level(level)
    
    def _consolidate_level(self, level):
        """Consolidate segments at a specific level"""
        # Get segments at this level, ordered from base to tip
        level_segments = []
        level_indices = []
        
        for i, s in enumerate(self.segments):
            if s.level == level:
                level_segments.append(s)
                level_indices.append(i)
        
        if len(level_segments) < CONSOLIDATION_SEGMENTS + BUFFER_SEGMENTS:
            return
        
        # Find the first contiguous group of CONSOLIDATION_SEGMENTS at this level
        # We need to consolidate from the base (lowest indices first)
        segments_to_consolidate = []
        indices_to_remove = []
        
        # Look for the first contiguous group from the base
        consecutive_count = 0
        start_found = False
        
        for i, (segment, original_index) in enumerate(zip(level_segments, level_indices)):
            if not start_found:
                # Look for start of consolidatable group
                if consecutive_count == 0:
                    segments_to_consolidate = [segment]
                    indices_to_remove = [original_index]
                    consecutive_count = 1
                    start_found = True
                    continue
            
            # Check if this segment is consecutive to the previous one
            if len(indices_to_remove) > 0 and original_index == indices_to_remove[-1] + 1:
                segments_to_consolidate.append(segment)
                indices_to_remove.append(original_index)
                consecutive_count += 1
                
                if consecutive_count >= CONSOLIDATION_SEGMENTS:
                    break
            else:
                # Reset if not consecutive
                if consecutive_count < CONSOLIDATION_SEGMENTS:
                    segments_to_consolidate = [segment]
                    indices_to_remove = [original_index]
                    consecutive_count = 1
        
        # Only consolidate if we have enough consecutive segments
        if len(segments_to_consolidate) < CONSOLIDATION_SEGMENTS:
            return
        
        # Take only the first CONSOLIDATION_SEGMENTS
        segments_to_consolidate = segments_to_consolidate[:CONSOLIDATION_SEGMENTS]
        indices_to_remove = indices_to_remove[:CONSOLIDATION_SEGMENTS]
        
        # Calculate new consolidated segment properties
        base_segment = segments_to_consolidate[0]
        total_length = sum(s.length for s in segments_to_consolidate)
        
        # Create new consolidated segment
        new_segment = VineSegment(
            base_segment.position,
            level=level + 1,
            consolidated_count=sum(s.consolidated_count for s in segments_to_consolidate),
            pixels_per_meter=self.pixels_per_meter
        )
        new_segment.old_position = Vector2(base_segment.old_position)
        new_segment.length = total_length
        
        # Remove old segments (in reverse order to maintain indices)
        for index in sorted(indices_to_remove, reverse=True):
            self.segments.pop(index)
        
        # Insert new segment at the position of the first removed segment
        insert_position = min(indices_to_remove)
        self.segments.insert(insert_position, new_segment)
        
        # Update positions of remaining segments
        self._update_segment_chain()
    
    def _update_segment_chain(self):
        """Update the chain of segments to maintain proper spacing"""
        if not self.segments:
            return
        
        # Ensure base segment is at correct position
        self.segments[0].position = Vector2(self.base_position)
        self.segments[0].old_position = Vector2(self.base_position)
        
        # Update remaining segments to maintain chain structure
        for i in range(1, len(self.segments)):
            prev_segment = self.segments[i - 1]
            current_segment = self.segments[i]
            
            # Calculate desired position based on previous segment
            direction = current_segment.position - prev_segment.position
            if direction.length() > 0:
                direction = direction.normalize()
            else:
                direction = Vector2(0, -1)  # Default upward
            
            desired_distance = prev_segment.length
            current_segment.position = prev_segment.position + direction * desired_distance
    
    def add_segment(self):
        """Add a new level 0 segment at the tip"""
        if len(self.segments) < 20:  # Max segments limit
            # Calculate position for new segment
            if self.segments:
                last_segment = self.segments[-1]
                direction = Vector2(0, -1)  # Default upward
                if len(self.segments) > 1:
                    direction = (last_segment.position - self.segments[-2].position).normalize()
                
                new_position = last_segment.position + direction * (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT)
            else:
                new_position = Vector2(self.base_position.x, self.base_position.y - (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT))
            
            # Create new segment with current scale
            new_segment = VineSegment(new_position, level=0, pixels_per_meter=self.pixels_per_meter)
            self.segments.append(new_segment)
            
            levels = np.array([s.level for s in self.segments], dtype=int)
            pattern = "".join(map(str, levels))
            self.segment_count = np.sum(CONSOLIDATION_SEGMENTS ** levels)

            print(f"Segments: {len(self.segments)}, Pattern: {pattern}", "Count:", self.segment_count)

            # Trigger consolidation check
            self.consolidate_segments()
            
            # Print after consolidation
            pattern_after = "".join(str(s.level) for s in self.segments)
            print(f"After consolidation - Segments: {len(self.segments)}, Pattern: {pattern_after}")
            print("---")
    
    def update_physics(self):
        """Update physics for all segments with mass-based movement"""
        # Apply forces to all segments except the base
        for i in range(1, len(self.segments)):
            segment = self.segments[i]
            
            # Store current position
            current_pos = Vector2(segment.position)
            
            # Calculate velocity (Verlet integration)
            velocity = segment.position - segment.old_position
            
            # Apply damping based on mass (heavier segments are more resistant to movement)
            mass_damping = self.damping ** (1.0 / segment.mass)  # Heavier = more damping
            velocity *= mass_damping
            
            # Apply gravity (F = ma, so acceleration = F/m)
            gravity_acceleration = self.gravity / segment.mass  # Heavier segments fall slower
            velocity.y += gravity_acceleration
            
            # Apply mouse force to last segment (head) - also affected by mass
            if i == len(self.segments) - 1:
                mouse_pos = Vector2(pygame.mouse.get_pos())
                to_mouse = mouse_pos - segment.position
                # Mouse force is reduced by mass (heavier segments respond less to mouse)
                mouse_acceleration = (to_mouse * self.mouse_strength) / segment.mass
                velocity += mouse_acceleration
            
            # Limit velocity to prevent instability (especially important for light segments)
            max_velocity = 10.0 / (segment.mass ** 0.3) * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)
            if velocity.length() > max_velocity:
                velocity = velocity.normalize() * max_velocity
            
            # Update positions
            segment.old_position = current_pos
            segment.position += velocity
    
    def apply_constraints(self):
        """Apply distance constraints between segments with mass consideration"""
        for iteration in range(self.constraint_iterations):
            # Forward pass
            for i in range(len(self.segments) - 1):
                current = self.segments[i]
                next_segment = self.segments[i + 1]
                
                segment_vector = next_segment.position - current.position
                distance = segment_vector.length()
                target_distance = current.length
                
                if distance > 0:
                    difference = target_distance - distance
                    correction = segment_vector.normalize() * (difference * 0.5)
                    
                    if i == 0:  # Base segment - don't move
                        next_segment.position += correction * 2
                    else:
                        # Distribute correction based on mass ratio
                        total_mass = current.mass + next_segment.mass
                        current_weight = next_segment.mass / total_mass  # Heavier segments move less
                        next_weight = current.mass / total_mass
                        
                        current.position -= correction * current_weight
                        next_segment.position += correction * next_weight
            
            # Backward pass
            for i in range(len(self.segments) - 2, -1, -1):
                current = self.segments[i]
                next_segment = self.segments[i + 1]
                
                segment_vector = current.position - next_segment.position
                distance = segment_vector.length()
                target_distance = current.length
                
                if distance > 0:
                    difference = target_distance - distance
                    correction = segment_vector.normalize() * (difference * 0.5)
                    
                    if i == 0:  # Base segment - don't move
                        next_segment.position -= correction * 2
                    else:
                        # Distribute correction based on mass ratio
                        total_mass = current.mass + next_segment.mass
                        current_weight = next_segment.mass / total_mass  # Heavier segments move less
                        next_weight = current.mass / total_mass
                        
                        current.position += correction * current_weight
                        next_segment.position -= correction * next_weight
        
        # Apply ground collision
        self.apply_ground_collision()
    
    def apply_ground_collision(self):
        """Prevent segments from going through ground"""
        for segment in self.segments:
            if segment.position.y > GROUND_Y:
                segment.position.y = GROUND_Y
                segment.old_position.y = min(segment.old_position.y, GROUND_Y)
    
    def update_head_position(self):
        """Update head position based on last segment"""
        if self.animator.change_scale:
            self.head_image = pygame.transform.scale(self.head_image, (self.pixels_per_meter * PLANT_HEAD_W, self.pixels_per_meter * PLANT_HEAD_H))
            self.head_rect = self.head_image.get_rect()

        if self.segments:
            last_segment = self.segments[-1]
            self.head_rect = self.head_image.get_rect(midbottom=(int(last_segment.position.x), int(last_segment.position.y)))

    def update_base_position(self):
        """Update base position and propagate to first segment"""
        self.base_rect = self.base_image.get_rect(center=(self.x, self.y))

        new_base = Vector2(self.base_rect.centerx, self.base_rect.top + 50 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER))
        offset = new_base - self.base_position
        
        # Move all segments by offset
        for segment in self.segments:
            segment.position += offset
            segment.old_position += offset
        
        self.base_position = new_base
    
    def update(self):
        # Update base animation
        self.base_image = self.animator.get_image((self.pixels_per_meter * PLANT_BASE_SIZE, self.pixels_per_meter * PLANT_BASE_SIZE))
        
        # Update base position
        self.update_base_position()
        
        # Update physics
        self.update_physics()
        
        # Apply constraints
        self.apply_constraints()
        
        # Update head position
        self.update_head_position()
        
        # Check for consolidation opportunities
        self.consolidate_segments()
    
    def get_segment_info(self):
        """Debug function to show current segment structure"""
        info = []
        for i, segment in enumerate(self.segments):
            info.append(f"Segment {i}: Level {segment.level}, Count {segment.consolidated_count}, Mass {segment.mass:.2f}")
        return info
    
    def draw(self, surface):
        # Draw segments with level-appropriate styling
        if len(self.segments) > 1:
            for i in range(len(self.segments) - 1):
                current = self.segments[i]
                next_segment = self.segments[i + 1]
                
                start_pos = (int(current.position.x), int(current.position.y))
                end_pos = (int(next_segment.position.x), int(next_segment.position.y))
                
                # Color varies by level
                colors = [
                    (79, 149, 79),   # Level 0: Forest Green
                    (75, 125, 69),  # Level 1: Medium Sea Green  
                    (70, 101, 59),   # Level 2: Darker Green
                    (66, 78, 50),    # Level 3: Very Dark Green
                    (62, 54, 40),    # Level 4: Extra Dark Green
                ]
                color = colors[min(current.level, len(colors) - 1)]
                
                pygame.draw.line(surface, color, start_pos, end_pos, current.thickness)
        
        # Draw segment joints with level indicators
        for i, segment in enumerate(self.segments):
            joint_size = max(2, int(segment.thickness // 2 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)))
            # Color joint based on level
            joint_colors = [(20, 80, 20), (40, 100, 40), (60, 120, 60), (80, 140, 80), (100, 160, 100)]
            joint_color = joint_colors[min(segment.level, len(joint_colors) - 1)]
            
            pygame.draw.circle(surface, joint_color, 
                             (int(segment.position.x), int(segment.position.y)), joint_size)
            
            # Draw level number for debugging (scaled font)
            if segment.level > 0:
                font_size = max(12, int(20 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)))
                font = pygame.font.Font(None, font_size)
                text = font.render(str(segment.level), True, (255, 255, 255))
                surface.blit(text, (int(segment.position.x) - 5, int(segment.position.y) - 10))

        # Draw base scaled in update base scale
        surface.blit(self.base_image, self.base_rect)

        # Draw head
        surface.blit(self.head_image, self.head_rect)
    
    def draw_debug_info(self, surface):
        """Draw debug information about current segment structure"""
        y_offset = 10
        font_size = max(16, int(24 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER)))
        font = pygame.font.Font(None, font_size)
        
        # Show segment pattern
        pattern = ""
        for segment in self.segments:
            pattern += str(segment.level)
        
        text = font.render(f"Pattern: {pattern}", True, (255, 255, 255))
        surface.blit(text, (10, y_offset))
        y_offset += int(25 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER))
        
        # Show segment counts by level
        level_counts = {}
        level_masses = {}
        for segment in self.segments:
            level_counts[segment.level] = level_counts.get(segment.level, 0) + 1
            if segment.level not in level_masses:
                level_masses[segment.level] = segment.mass
        
        for level, count in sorted(level_counts.items()):
            mass = level_masses[level]
            text = font.render(f"Level {level}: {count} segments (mass: {mass:.1f})", True, (255, 255, 255))
            surface.blit(text, (10, y_offset))
            y_offset += int(25 * (self.pixels_per_meter / INITIAL_PIXELS_PER_METER))