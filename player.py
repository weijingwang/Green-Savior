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
        self.mass = self.calculate_mass()  # Constant mass for all segments
    
    def update_scale(self, new_pixels_per_meter):
        """Update segment properties when scale changes - MUCH more gradual scaling"""
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
    
    def calculate_thickness(self):
        """Calculate thickness with EXTREMELY gradual scaling"""
        # Make scaling almost imperceptible - use power of 0.1 instead of 0.5
        scale_factor = (self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.1
        base_thickness = 20 * scale_factor  # Very gradual scaling
        level_multiplier = 1.5 ** self.level  # Much more gradual level scaling
        return max(3, int(base_thickness * level_multiplier))  # Minimum thickness of 3
    
    def calculate_mass(self):
        """Constant mass for maximum performance"""
        return 0.1  # Completely constant mass

class Player:
    def __init__(self, x, y, image_folder="assets/images/player"):
        """
        Enhanced Player class with minimal scaling for maximum performance
        """
        self.x, self.y = x, y

        self.pixels_per_meter = INITIAL_PIXELS_PER_METER
        self.target_pixels_per_meter = INITIAL_PIXELS_PER_METER      
        
        # Initialize segments early so they're available for size calculations
        self.segments = []
        self.segment_count = INITIAL_SEGMENTS  # Initialize early for size calculations
        
        # Define perfect default sizes (current sizes are perfect)
        self.perfect_base_size = self.pixels_per_meter * PLANT_BASE_SIZE
        self.perfect_head_width = int(self.pixels_per_meter * PLANT_HEAD_W + 27)
        self.perfect_head_height = int(self.pixels_per_meter * PLANT_HEAD_H + 10)
        
        # Plant base setup - starts at 2x perfect size, shrinks to perfect
        base_paths = [os.path.join(image_folder, f"base/base{i}.png") for i in range(1, 19)]
        base_size = self.calculate_base_size()
        self.animator = Animator(base_paths, scale=(base_size, base_size), frame_duration=5)
        self.base_image = self.animator.get_image((base_size, base_size))
        self.base_rect = self.base_image.get_rect(center=(x, y))
        
        # Plant head setup - starts at 2x perfect size, shrinks to perfect
        self.og_head_image = pygame.image.load(
            os.path.join(image_folder, "head.png")
        ).convert_alpha()
        self.og_head_rect = self.og_head_image.get_rect()

        head_width, head_height = self.calculate_head_size()
        self.head_image = pygame.transform.scale(self.og_head_image, (head_width, head_height))
        
        # Physics properties - MINIMAL scaling for maximum performance
        self.base_gravity = 0.1
        self.base_mouse_strength = 2.0
        self.constraint_iterations = 2  # Keep low for performance
        self.damping = 0.998  # Slightly more damping for stability
        
        # Initialize with level 0 segments
        self.constraint_iterations = 2  # Keep low for performance
        self.damping = 0.998  # Slightly more damping for stability
        
        # Calculate initial base connection point - segments start 50 pixels below the top of base
        self.base_connection_offset = 50
        
        # Create initial segments
        self._initialize_segments()
        
        # Head setup
        self.head_rect = self.head_image.get_rect()
        self.update_head_position()
        print(self.head_rect)
    
    def calculate_shrink_factor(self):
        """Calculate shrink factor based on segment count - starts at 1.0 (2x size) and shrinks to 0.0 (perfect size)"""
        # Use segment count to determine shrinkage - more segments = smaller head/base
        # Start shrinking after a few segments, reach perfect size around 20-30 segments
        max_shrink_segments = 25  # At this many segments, reach perfect (current) size
        
        # Safely get segment count - use stored count or actual segments length
        current_count = self.segment_count if hasattr(self, 'segment_count') else len(self.segments)
        shrink_progress = min(current_count / max_shrink_segments, 1.0)
        
        # Smooth shrinkage curve - starts fast, slows down as it approaches perfect size
        shrink_factor = 1.0 - (shrink_progress ** 0.7)  # Starts at 1.0, goes to 0.0
        return shrink_factor
    
    def calculate_base_size(self):
        """Calculate base size - starts at 2x perfect, shrinks to perfect"""
        shrink_factor = self.calculate_shrink_factor()
        # shrink_factor: 1.0 = double size, 0.0 = perfect size
        size = self.perfect_base_size * (1.0 + shrink_factor)  # 1.0 to 2.0 range
        return int(size)
    
    def calculate_head_size(self):
        """Calculate head size - starts at 2x perfect, shrinks to perfect"""
        shrink_factor = self.calculate_shrink_factor()
        # shrink_factor: 1.0 = double size, 0.0 = perfect size
        width = self.perfect_head_width * (1.0 + shrink_factor)  # 1.0 to 2.0 range
        height = self.perfect_head_height * (1.0 + shrink_factor)
        return int(width), int(height)
        """Initialize segments with proper connection to base"""
        start_x = self.base_rect.centerx
        start_y = self.base_rect.top + self.base_connection_offset
        
        self.base_position = Vector2(start_x, start_y)
        
    def _initialize_segments(self):
        """Initialize segments with proper connection to base"""
        start_x = self.base_rect.centerx
        start_y = self.base_rect.top + self.base_connection_offset
        
        self.base_position = Vector2(start_x, start_y)
        
        for i in range(INITIAL_SEGMENTS):
            position = Vector2(start_x, start_y - i * (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT))
            segment = VineSegment(position, level=0, pixels_per_meter=self.pixels_per_meter)
            self.segments.append(segment)
    
    def update_scale(self, new_pixels_per_meter):
        """Update scaling with EXTREMELY gradual changes"""
        old_pixels_per_meter = self.pixels_per_meter
        scale_ratio = new_pixels_per_meter / old_pixels_per_meter
        
        # Update player's pixels_per_meter
        self.pixels_per_meter = new_pixels_per_meter
        
        # Scale player position
        self.x *= scale_ratio
        self.y *= scale_ratio
        
        # Base connection offset stays constant
        self.base_connection_offset = 50
        
        # Update base rect and position
        self.base_rect = self.base_image.get_rect(center=(self.x, self.y))
        new_base_x = self.base_rect.centerx
        new_base_y = self.base_rect.top + self.base_connection_offset
        
        # Calculate position offset
        old_base_position = Vector2(self.base_position)
        new_base_position = Vector2(new_base_x, new_base_y)
        position_offset = new_base_position - old_base_position * scale_ratio
        
        # Update all segments
        for segment in self.segments:
            segment.update_scale(new_pixels_per_meter)
            segment.position += position_offset
            segment.old_position += position_offset
        
        # Update base position
        self.base_position = new_base_position
        
        # MINIMAL physics scaling for maximum performance
        self.gravity = self.base_gravity * ((new_pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.2)
        self.mouse_strength = self.base_mouse_strength * ((new_pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.2)
        
        # Ensure first segment connection
        if self.segments:
            self.segments[0].position = Vector2(self.base_position)
            self.segments[0].old_position = Vector2(self.base_position)
        
        # Update base size based on segment count
        new_base_size = self.calculate_base_size()
        if abs(new_base_size - self.base_rect.width) > 1:  # Only update if significant change
            base_paths = [os.path.join("assets/images/player", f"base/base{i}.png") for i in range(1, 19)]
            self.animator = Animator(base_paths, scale=(new_base_size, new_base_size), frame_duration=5)
            self.animator.change_scale = True
    
    @property
    def gravity(self):
        return self.base_gravity * ((self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.2)

    @gravity.setter
    def gravity(self, value):
        self.pixels_per_meter = ((value / self.base_gravity) ** 5.0) * INITIAL_PIXELS_PER_METER

    @property
    def mouse_strength(self):
        return self.base_mouse_strength * ((self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.2)

    @mouse_strength.setter
    def mouse_strength(self, value):
        self.pixels_per_meter = ((value / self.base_mouse_strength) ** 5.0) * INITIAL_PIXELS_PER_METER

    def can_consolidate_at_level(self, level):
        """Check if we can consolidate segments at a specific level"""
        level_segments = [s for s in self.segments if s.level == level]
        
        if len(level_segments) < CONSOLIDATION_SEGMENTS + BUFFER_SEGMENTS:
            return False
        
        return True
    
    def consolidate_segments(self):
        """Perform consolidation starting from the base"""
        max_level = max(s.level for s in self.segments) if self.segments else 0
        
        for level in range(max_level + 1):
            while self.can_consolidate_at_level(level):
                self._consolidate_level(level)
    
    def _consolidate_level(self, level):
        """Consolidate segments at a specific level"""
        level_segments = []
        level_indices = []
        
        for i, s in enumerate(self.segments):
            if s.level == level:
                level_segments.append(s)
                level_indices.append(i)
        
        if len(level_segments) < CONSOLIDATION_SEGMENTS + BUFFER_SEGMENTS:
            return
        
        segments_to_consolidate = []
        indices_to_remove = []
        
        consecutive_count = 0
        start_found = False
        
        for i, (segment, original_index) in enumerate(zip(level_segments, level_indices)):
            if not start_found:
                if consecutive_count == 0:
                    segments_to_consolidate = [segment]
                    indices_to_remove = [original_index]
                    consecutive_count = 1
                    start_found = True
                    continue
            
            if len(indices_to_remove) > 0 and original_index == indices_to_remove[-1] + 1:
                segments_to_consolidate.append(segment)
                indices_to_remove.append(original_index)
                consecutive_count += 1
                
                if consecutive_count >= CONSOLIDATION_SEGMENTS:
                    break
            else:
                if consecutive_count < CONSOLIDATION_SEGMENTS:
                    segments_to_consolidate = [segment]
                    indices_to_remove = [original_index]
                    consecutive_count = 1
        
        if len(segments_to_consolidate) < CONSOLIDATION_SEGMENTS:
            return
        
        segments_to_consolidate = segments_to_consolidate[:CONSOLIDATION_SEGMENTS]
        indices_to_remove = indices_to_remove[:CONSOLIDATION_SEGMENTS]
        
        base_segment = segments_to_consolidate[0]
        total_length = sum(s.length for s in segments_to_consolidate)
        
        new_segment = VineSegment(
            base_segment.position,
            level=level + 1,
            consolidated_count=sum(s.consolidated_count for s in segments_to_consolidate),
            pixels_per_meter=self.pixels_per_meter
        )
        new_segment.old_position = Vector2(base_segment.old_position)
        new_segment.length = total_length
        
        for index in sorted(indices_to_remove, reverse=True):
            self.segments.pop(index)
        
        insert_position = min(indices_to_remove)
        self.segments.insert(insert_position, new_segment)
        
        self._update_segment_chain()
    
    def _update_segment_chain(self):
        """Update segment chain to maintain proper spacing"""
        if not self.segments:
            return
        
        self.segments[0].position = Vector2(self.base_position)
        self.segments[0].old_position = Vector2(self.base_position)
        
        for i in range(1, len(self.segments)):
            prev_segment = self.segments[i - 1]
            current_segment = self.segments[i]
            
            direction = current_segment.position - prev_segment.position
            if direction.length() > 0:
                direction = direction.normalize()
            else:
                direction = Vector2(0, -1)
            
            desired_distance = prev_segment.length
            current_segment.position = prev_segment.position + direction * desired_distance
    
    def add_segment(self):
        """Add a new level 0 segment at the tip"""
        if len(self.segments) < MAX_SEGS_TO_HAVE:
            if self.segments:
                last_segment = self.segments[-1]
                direction = Vector2(0, -1)
                if len(self.segments) > 1:
                    direction = (last_segment.position - self.segments[-2].position).normalize()
                
                new_position = last_segment.position + direction * (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT)
            else:
                new_position = Vector2(self.base_position.x, self.base_position.y - (self.pixels_per_meter * PLANT_SEGMENT_HEIGHT))
            
            new_segment = VineSegment(new_position, level=0, pixels_per_meter=self.pixels_per_meter)
            self.segments.append(new_segment)
            
            levels = np.array([s.level for s in self.segments], dtype=int)
            pattern = "".join(map(str, levels))
            self.segment_count = np.sum(CONSOLIDATION_SEGMENTS ** levels)

            print(f"Segments: {len(self.segments)}, Pattern: {pattern}", "Count:", self.segment_count)

            self.consolidate_segments()
            
            pattern_after = "".join(str(s.level) for s in self.segments)
            print(f"After consolidation - Segments: {len(self.segments)}, Pattern: {pattern_after}")
            print("---")
    
    def update_physics(self):
        """Optimized physics update with constant mass behavior"""
        # Apply forces to all segments except the base
        for i in range(1, len(self.segments)):
            segment = self.segments[i]
            
            current_pos = Vector2(segment.position)
            
            # Calculate velocity (Verlet integration)
            velocity = segment.position - segment.old_position
            
            # Apply uniform damping
            velocity *= self.damping
            
            # Apply uniform gravity (very minimal scaling)
            velocity.y += self.gravity
            
            # Apply mouse force to last segment only
            if i == len(self.segments) - 1:
                mouse_pos = Vector2(pygame.mouse.get_pos())
                to_mouse = mouse_pos - segment.position
                # Strong, uniform mouse force
                mouse_acceleration = to_mouse * self.mouse_strength * 0.04
                velocity += mouse_acceleration
            
            # Uniform velocity limits (minimal scaling)
            max_velocity = 30.0 * ((self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.1)
            if velocity.length() > max_velocity:
                velocity = velocity.normalize() * max_velocity
            
            # Update positions
            segment.old_position = current_pos
            segment.position += velocity
    
    def apply_constraints(self):
        """Apply distance constraints with equal treatment"""
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
                        # Equal distribution
                        current.position -= correction * 0.5
                        next_segment.position += correction * 0.5
            
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
                        # Equal distribution
                        current.position += correction * 0.5
                        next_segment.position -= correction * 0.5
        
        self.apply_ground_collision()
    
    def apply_ground_collision(self):
        """Prevent segments from going through ground"""
        for segment in self.segments:
            if segment.position.y > GROUND_Y:
                segment.position.y = GROUND_Y
                segment.old_position.y = min(segment.old_position.y, GROUND_Y)
    
    def update_head_position(self):
        """Update head position and size based on segment count"""
        # Update head size based on segment count
        head_width, head_height = self.calculate_head_size()
        if abs(head_width - self.head_rect.width) > 1:  # Only update if significant change
            self.head_image = pygame.transform.scale(self.og_head_image, (head_width, head_height))
            self.head_rect = self.head_image.get_rect()

        if self.segments:
            last_segment = self.segments[-1]
            self.head_rect = self.head_image.get_rect(midbottom=(int(last_segment.position.x), int(last_segment.position.y)))

    def update_base_position(self):
        """Update base position and size based on segment count"""
        # Update base size based on segment count
        new_base_size = self.calculate_base_size()
        current_base_size = self.base_rect.width
        
        if abs(new_base_size - current_base_size) > 1:  # Only update if significant change
            # Create new animator with updated size
            base_paths = [os.path.join("assets/images/player", f"base/base{i}.png") for i in range(1, 19)]
            self.animator = Animator(base_paths, scale=(new_base_size, new_base_size), frame_duration=5)
            self.animator.change_scale = True
        
        # Get the updated base image
        self.base_image = self.animator.get_image((new_base_size, new_base_size))
        self.base_rect = self.base_image.get_rect(center=(self.x, self.y))

        # Calculate new base connection point - 50 pixels below top of base
        new_base = Vector2(self.base_rect.centerx, self.base_rect.top + self.base_connection_offset)
        
        # Only update segment positions if there's actually a change
        if self.base_position.distance_to(new_base) > 0.1:  # Small threshold to avoid micro-movements
            offset = new_base - self.base_position
            
            # Move all segments by offset
            for segment in self.segments:
                segment.position += offset
                segment.old_position += offset
            
            self.base_position = new_base
    
    def update(self):
        # Update base position and size (this handles both size changes and animation)
        self.update_base_position()
        
        # Update physics
        self.update_physics()
        
        # Apply constraints
        self.apply_constraints()
        
        # Update head position and size
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
                    (75, 125, 69),   # Level 1: Medium Sea Green  
                    (70, 101, 59),   # Level 2: Darker Green
                    (66, 78, 50),    # Level 3: Very Dark Green
                    (62, 54, 40),    # Level 4: Extra Dark Green
                ]
                color = colors[min(current.level, len(colors) - 1)]
                
                pygame.draw.line(surface, color, start_pos, end_pos, current.thickness)
        
        # Draw segment joints with level indicators - MINIMAL scaling
        for i, segment in enumerate(self.segments):
            # Use extremely gradual scaling for joint size
            scale_factor = (self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.1  # Almost no scaling
            joint_size = max(3, int(segment.thickness // 2 * scale_factor))
            
            joint_colors = [(20, 80, 20), (40, 100, 40), (60, 120, 60), (80, 140, 80), (100, 160, 100)]
            joint_color = joint_colors[min(segment.level, len(joint_colors) - 1)]
            
            pygame.draw.circle(surface, joint_color, 
                             (int(segment.position.x), int(segment.position.y)), joint_size)
            
            # Draw level number for debugging with minimal font scaling
            if segment.level > 0:
                font_scale_factor = (self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.1  # Almost no scaling
                font_size = max(16, int(20 * font_scale_factor))
                font = pygame.font.Font(None, font_size)
                text = font.render(str(segment.level), True, (255, 255, 255))
                surface.blit(text, (int(segment.position.x) - 5, int(segment.position.y) - 10))

        # Draw base on top of segments
        surface.blit(self.base_image, self.base_rect)

        # Draw head on top of everything
        surface.blit(self.head_image, self.head_rect)
    
    def draw_debug_info(self, surface):
        """Draw debug information with minimal scaling"""
        y_offset = 10
        # Minimal font scaling
        font_scale_factor = (self.pixels_per_meter / INITIAL_PIXELS_PER_METER) ** 0.1  # Almost no scaling
        font_size = max(20, int(24 * font_scale_factor))
        font = pygame.font.Font(None, font_size)
        
        # Show segment pattern
        pattern = ""
        for segment in self.segments:
            pattern += str(segment.level)
        
        text = font.render(f"Pattern: {pattern}", True, (255, 255, 255))
        surface.blit(text, (10, y_offset))
        y_offset += int(25 * font_scale_factor)
        
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
            y_offset += int(25 * font_scale_factor)