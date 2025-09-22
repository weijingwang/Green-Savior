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
        
    def update(self, target_y):
        """Update elevator position based on target position"""
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
    
    def get_current_floor(self):
        """Get the current floor number (0-indexed)"""
        nearest_floor = round((RECT_Y + RECT_HEIGHT - self.height - self.y) / self.floor_height)
        return min(max(nearest_floor, 0), NUM_FLOORS - 1)
    
    def draw(self, screen):
        """Draw the elevator"""
        smooth_y = round(self.y)  # Round to nearest pixel for drawing
        pygame.draw.rect(screen, BLACK, (self.x, smooth_y, self.width, self.height))