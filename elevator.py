import pygame
from constants import *

class Elevator:
    def __init__(self):
        self.width = ELEV_WIDTH
        self.height = RECT_HEIGHT // NUM_FLOORS
        self.x = RECT_X + (RECT_WIDTH - self.width) // 2
        self.y = float(RECT_Y)  # Use float for sub-pixel precision
        self.speed = 0.0
        self.floor_height = RECT_HEIGHT / NUM_FLOORS
        
        # Track elevator state for people management
        self.current_floor = 0
        self.stopped_frames = 0  # How many frames the elevator has been stopped
        self.was_moving = False  # Track if elevator was moving last frame
        
    def update(self, target_y):
        """Update elevator position based on target position"""
        # Store previous position to detect if we're moving
        prev_y = self.y
        
        # Compute distance to target
        dist = target_y - self.y
        
        # Stop if close enough to target AND speed is low
        if abs(dist) <= STOP_THRESHOLD and abs(self.speed) < 0.8:
            self.speed = 0
            self.y = target_y  # Snap to exact target
        else:
            # Calculate allowed overshoot distance for more natural motion
            overshoot_distance = self.floor_height * OVERSHOOT_FACTOR
            
            # Dynamic braking distance - start braking later for overshoot
            base_braking_distance = (self.speed ** 2) / (2 * DECEL)
            braking_distance = max(base_braking_distance * 0.8, abs(dist) * 0.2)
            
            if abs(dist) <= braking_distance and abs(dist) > STOP_THRESHOLD:
                # Gentler deceleration to allow natural overshoot
                brake_force = DECEL * (0.7 + (braking_distance - abs(dist)) / braking_distance * 0.5)
                if self.speed > 0:
                    self.speed = max(0, self.speed - brake_force)
                elif self.speed < 0:
                    self.speed = min(0, self.speed + brake_force)
            else:
                # Accelerate toward target with boost for quick direction changes
                direction_change_boost = 1.0
                if (dist > 0 and self.speed < 0) or (dist < 0 and self.speed > 0):
                    direction_change_boost = 1.5  # Extra responsive when changing direction
                
                if dist > 0:
                    self.speed = min(MAX_SPEED, self.speed + ACCEL * direction_change_boost)
                elif dist < 0:
                    self.speed = max(-MAX_SPEED, self.speed - ACCEL * direction_change_boost)
            
            # Update elevator position
            self.y += self.speed
            
            # Allow controlled overshoot, but prevent excessive overshoot
            if ((dist > 0 and self.y > target_y + overshoot_distance and self.speed > 0) or 
                (dist < 0 and self.y < target_y - overshoot_distance and self.speed < 0)):
                # Only stop if we've overshot too much
                self.speed *= -0.3  # Bounce back with reduced speed
            elif ((dist > 0 and self.y > target_y and self.speed > 0) or 
                  (dist < 0 and self.y < target_y and self.speed < 0)):
                # We're overshooting but within allowed range - just slow down
                self.speed *= 0.85
        
        # Update movement tracking
        is_moving = abs(self.y - prev_y) > 0.1
        
        if not is_moving and not self.was_moving:
            # Elevator has been stopped
            self.stopped_frames += 1
        else:
            # Elevator is moving or just started moving
            self.stopped_frames = 0
            
        self.was_moving = is_moving
        self.current_floor = self.get_current_floor()
    
    def is_moving(self):
        """Check if elevator is currently moving"""
        return abs(self.speed) > 0.1
    
    def get_current_floor(self):
        """Get the current floor number (0-indexed)"""
        # Calculate which floor the elevator center is closest to
        elevator_center_y = self.y + self.height / 2
        
        # Calculate relative position within the shaft
        relative_y = elevator_center_y - RECT_Y
        
        # Calculate floor (floors are numbered from top to bottom, 0 = top floor)
        floor_number = relative_y / self.floor_height
        
        # Round to nearest floor and clamp to valid range
        nearest_floor = round(floor_number)
        return min(max(nearest_floor, 0), NUM_FLOORS - 1)
    
    def is_stopped_for_exit(self):
        """Check if elevator has been stopped long enough for people to exit"""
        return self.stopped_frames >= ELEVATOR_STOP_FRAMES
    
    def is_on_floor(self, floor):
        """Check if elevator is currently on a specific floor and reasonably stationary"""
        if floor < 0 or floor >= NUM_FLOORS:
            return False
            
        # Calculate where the elevator center should be for this floor
        target_floor_y = RECT_Y + floor * self.floor_height + self.floor_height / 2
        elevator_center_y = self.y + self.height / 2
        
        # Check if elevator is close to the floor center (no speed requirement for boarding)
        distance_to_floor_center = abs(elevator_center_y - target_floor_y)
        is_near_floor = distance_to_floor_center < self.floor_height * 0.3  # Within 30% of floor height
        
        return is_near_floor
    
    def get_center_x(self):
        """Get the center x position of the elevator"""
        return self.x + self.width // 2
        
    def draw(self, screen):
        """Draw the elevator"""
        smooth_y = round(self.y)  # Round to nearest pixel for drawing
        pygame.draw.rect(screen, BLACK, (self.x, smooth_y, self.width, self.height))