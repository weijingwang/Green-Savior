import pygame
import random
import math

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elevator Simulation")

font = pygame.font.SysFont("Arial", 36, bold=True)
background = pygame.image.load("gameplay_draft.png").convert()  # no per-pixel alpha
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background.set_alpha(128)  # 50% opacity (0 = fully transparent, 255 = fully opaque)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
PURPLE = (255, 50, 255)

# Elevator shaft
rect_width, rect_height = 200, 600
rect_x = (WIDTH // 2 - rect_width) // 4
rect_y = (HEIGHT - rect_height) // 2

# Elevator
elev_width = 40
NUM_FLOORS = 21
elev_height = rect_height // NUM_FLOORS
elev_x = rect_x + (rect_width - elev_width) // 2
elev_y = float(rect_y)  # Use float for sub-pixel precision
elev_speed = 0.0

# Slider
slider_bar_y = HEIGHT // 2 + 150
slider_bar_width = WIDTH // 2 - 120
slider_bar_x = WIDTH // 2 + 80
slider_bar_height = 6
slider_radius = 12
slider_y = slider_bar_y
slider_x = slider_bar_x

pygame.mouse.set_visible(False)
cursor_radius = 8
floor_height = rect_height / NUM_FLOORS

# Motion parameters
MAX_SPEED = 12.0  # Fast but not too crazy
ACCEL = 1.2       # Quick acceleration for responsiveness
DECEL = 1.6       # Gentler braking to allow overshoot
STOP_THRESHOLD = 1.5  # Smaller threshold for precision
OVERSHOOT_FACTOR = 0.15  # Allow 15% overshoot for fun physics

class Person:
    def __init__(self, floor, spawn_x, queue_position):
        self.floor = floor  # Which floor they're on (0-20)
        self.x = spawn_x
        self.y = rect_y + floor * floor_height + floor_height * 0.7  # Stand on floor
        self.queue_position = queue_position  # Position in line (0 = front)
        self.target_x = self.calculate_target_x()  # Calculate position in line
        self.speed = random.uniform(2.0, 3.0)  # Slightly faster walking speed
        self.color = random.choice([GREEN, YELLOW, PURPLE, RED])
        self.radius = random.randint(4, 7)
        self.waiting = False  # True when they reach their position in line
        self.bob_offset = random.uniform(0, math.pi * 2)  # For bobbing animation
        self.bob_speed = random.uniform(0.05, 0.15)
        
    def calculate_target_x(self):
        # Line up horizontally to the right of the elevator
        # Each person takes up about 18 pixels of horizontal space (increased from 16)
        person_spacing = 18
        base_x = rect_x + rect_width + 15  # Start 15 pixels to the right of elevator (increased from 10)
        return base_x + (self.queue_position * person_spacing)
        
    def update_queue_position(self, new_position):
        """Update this person's position in the queue"""
        old_position = self.queue_position
        self.queue_position = new_position
        new_target = self.calculate_target_x()
        
        # Only update if the position actually changed
        if old_position != new_position:
            self.target_x = new_target
            # If they were already waiting, they need to move to their new position
            if self.waiting and abs(self.x - new_target) > 2.0:
                self.waiting = False
        
    def update(self):
        if not self.waiting:
            # Move toward their position in line
            distance_to_target = abs(self.x - self.target_x)
            if distance_to_target > 2.0:  # Increased threshold to reduce jittering
                if self.x > self.target_x:
                    self.x -= min(self.speed, distance_to_target * 0.3)  # Slow down as we get closer
                elif self.x < self.target_x:
                    self.x += min(self.speed, distance_to_target * 0.3)  # Slow down as we get closer
            else:
                self.x = self.target_x
                self.waiting = True
        
        # Add subtle bobbing animation when waiting
        if self.waiting:
            self.bob_offset += self.bob_speed
            
    def draw(self, screen):
        draw_y = self.y
        if self.waiting:
            # Add bobbing when waiting
            draw_y += math.sin(self.bob_offset) * 1.5
            
        pygame.draw.circle(screen, self.color, (int(self.x), int(draw_y)), self.radius)
        # Add a simple face
        pygame.draw.circle(screen, BLACK, (int(self.x - 2), int(draw_y - 2)), 1)
        pygame.draw.circle(screen, BLACK, (int(self.x + 2), int(draw_y - 2)), 1)

class PeopleManager:
    def __init__(self):
        # Dictionary to store people by floor for easy queue management
        self.people_by_floor = {i: [] for i in range(NUM_FLOORS)}
        self.all_people = []  # Keep all people for drawing and cleanup
        self.spawn_timer = 0
        self.spawn_interval = random.randint(30, 90)  # Fast spawning (0.5-1.5 seconds at 60fps)
        self.center_line_x = WIDTH // 2
        
    def update(self):
        # Spawn new people
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_person()
            self.spawn_timer = 0
            self.spawn_interval = random.randint(30, 90)  # Reset with random interval
            
        # Update existing people
        for person in self.all_people[:]:  # Use slice to avoid modification issues
            person.update()
            
        # Only do cleanup occasionally and be very conservative
        if self.spawn_timer % 60 == 0:  # Only check every second
            self.cleanup_distant_people()
    
    def spawn_person(self):
        # Randomly choose which floor(s) to spawn on
        num_spawns = random.choices([1, 2, 3], weights=[70, 25, 5])[0]  # Usually 1, sometimes 2-3
        
        for _ in range(num_spawns):
            floor = random.randint(0, NUM_FLOORS - 1)
            
            # Determine this person's position in the queue for their floor
            queue_position = len(self.people_by_floor[floor])
            
            # Spawn from center line with some random offset, but ensure they start moving toward elevator
            spawn_x = self.center_line_x + random.randint(-50, 50)
            # Make sure spawn position is reasonable (not too far left)
            spawn_x = max(spawn_x, 100)  # Don't spawn too close to left edge
            person = Person(floor, spawn_x, queue_position)
            
            # Add to both tracking structures
            self.people_by_floor[floor].append(person)
            self.all_people.append(person)
    
    def remove_people_from_floor(self, floor, count=1):
        """Remove people from the front of the queue on a specific floor"""
        if floor < 0 or floor >= NUM_FLOORS:
            return
            
        removed_count = 0
        floor_people = self.people_by_floor[floor]
        
        # Remove people from the front of the queue
        people_to_remove = []
        for i in range(min(count, len(floor_people))):
            if i < len(floor_people):
                people_to_remove.append(floor_people[i])
        
        # Actually remove them
        for person in people_to_remove:
            if person in floor_people:
                floor_people.remove(person)
            if person in self.all_people:
                self.all_people.remove(person)
            removed_count += 1
        
        # Update queue positions for remaining people on this floor
        for i, person in enumerate(floor_people):
            person.update_queue_position(i)
    
    def get_floor_queue_size(self, floor):
        """Get the number of people waiting on a specific floor"""
        if floor < 0 or floor >= NUM_FLOORS:
            return 0
        return len(self.people_by_floor[floor])
    
    def draw(self, screen):
        for person in self.all_people:
            person.draw(screen)
    
    def get_people_count(self):
        return len(self.all_people)
    def cleanup_distant_people(self):
            """Conservative cleanup of people who are genuinely off-screen"""
            people_to_remove = []
            for person in self.all_people:
                # Only remove people who are VERY far away and clearly not coming back
                if person.x < -200 or person.x > WIDTH + 300:
                    people_to_remove.append(person)
            
            # Remove the flagged people safely
            for person in people_to_remove:
                if person in self.all_people:
                    self.all_people.remove(person)
                # Also remove from floor-specific tracking
                if person.floor in self.people_by_floor and person in self.people_by_floor[person.floor]:
                    self.people_by_floor[person.floor].remove(person)
                    # Update queue positions for remaining people on this floor
                    for i, remaining_person in enumerate(self.people_by_floor[person.floor]):
                        remaining_person.update_queue_position(i)

# Initialize people manager
people_manager = PeopleManager()

clock = pygame.time.Clock()
running = True

# Removed pickup system - just show queueing behavior

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Draw background
    screen.fill(WHITE)
    screen.blit(background, (0, 0))

    pygame.draw.rect(screen, BLUE, (rect_x, rect_y, rect_width, rect_height))
    
    # Draw floor lines
    for i in range(NUM_FLOORS + 1):  # +1 so we get the top line too
        y = rect_y + i * floor_height
        pygame.draw.line(screen, WHITE, (rect_x, y), (rect_x + rect_width, y), 2)

    # Draw center line for reference
    pygame.draw.line(screen, BLACK, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 1)

    # Update and draw people
    people_manager.update()
    people_manager.draw(screen)

    # Mouse (slider) position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if mouse_x < WIDTH // 2:
        mouse_x = WIDTH // 2
    if mouse_x > WIDTH - cursor_radius:
        mouse_x = WIDTH - cursor_radius
    
    slider_x = min(max(mouse_x, slider_bar_x), slider_bar_x + slider_bar_width)
    
    # Target elevator Y based on slider
    t = (slider_x - slider_bar_x) / slider_bar_width
    target_y = rect_y + (1 - t) * (rect_height - elev_height)  # Keep as float
    
    # Compute distance to target
    dist = target_y - elev_y
    
    # Stop if close enough to target AND speed is low
    if abs(dist) <= STOP_THRESHOLD and abs(elev_speed) < 0.8:
        elev_speed = 0
        elev_y = target_y  # Snap to exact target
    else:
        # Calculate allowed overshoot distance for more natural motion
        overshoot_distance = floor_height * OVERSHOOT_FACTOR
        
        # Dynamic braking distance - start braking later for overshoot
        base_braking_distance = (elev_speed ** 2) / (2 * DECEL)
        braking_distance = max(base_braking_distance * 0.8, abs(dist) * 0.2)
        
        if abs(dist) <= braking_distance and abs(dist) > STOP_THRESHOLD:
            # Gentler deceleration to allow natural overshoot
            brake_force = DECEL * (0.7 + (braking_distance - abs(dist)) / braking_distance * 0.5)
            if elev_speed > 0:
                elev_speed = max(0, elev_speed - brake_force)
            elif elev_speed < 0:
                elev_speed = min(0, elev_speed + brake_force)
        else:
            # Accelerate toward target with boost for quick direction changes
            direction_change_boost = 1.0
            if (dist > 0 and elev_speed < 0) or (dist < 0 and elev_speed > 0):
                direction_change_boost = 1.5  # Extra responsive when changing direction
            
            if dist > 0:
                elev_speed = min(MAX_SPEED, elev_speed + ACCEL * direction_change_boost)
            elif dist < 0:
                elev_speed = max(-MAX_SPEED, elev_speed - ACCEL * direction_change_boost)
        
        # Update elevator position
        elev_y += elev_speed
        
        # Allow controlled overshoot, but prevent excessive overshoot
        if ((dist > 0 and elev_y > target_y + overshoot_distance and elev_speed > 0) or 
            (dist < 0 and elev_y < target_y - overshoot_distance and elev_speed < 0)):
            # Only stop if we've overshot too much
            elev_speed *= -0.3  # Bounce back with reduced speed
        elif ((dist > 0 and elev_y > target_y and elev_speed > 0) or 
              (dist < 0 and elev_y < target_y and elev_speed < 0)):
            # We're overshooting but within allowed range - just slow down
            elev_speed *= 0.85
    
    # Snap to nearest floor for display
    nearest_floor = round((rect_y + rect_height - elev_height - elev_y) / floor_height)
    current_floor = min(max(nearest_floor, 0), NUM_FLOORS - 1)
    
    # Draw elevator with smooth sub-pixel positioning
    smooth_elev_y = round(elev_y)  # Round to nearest pixel for drawing
    pygame.draw.rect(screen, BLACK, (elev_x, smooth_elev_y, elev_width, elev_height))
    
    # Draw slider bar and circle
    pygame.draw.rect(screen, BLACK, (slider_bar_x, slider_bar_y - slider_bar_height // 2,
                     slider_bar_width, slider_bar_height))
    pygame.draw.circle(screen, RED, (slider_x, slider_y), slider_radius)
    
    floor_text = font.render(f"Floor: {current_floor + 1}", True, BLACK)
    screen.blit(floor_text, (20, 20))  # top-left corner
    
    # Draw FPS text
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, RED)
    screen.blit(fps_text, (20, 60))  # just below floor text
    
    # Draw people count
    people_count_text = font.render(f"People: {people_manager.get_people_count()}", True, BLACK)
    screen.blit(people_count_text, (20, 100))
    
    # Draw current floor queue size
    current_floor_queue = people_manager.get_floor_queue_size(current_floor)
    queue_text = font.render(f"Floor {current_floor + 1} Queue: {current_floor_queue}", True, PURPLE)
    screen.blit(queue_text, (20, 140))

    # Draw custom cursor
    pygame.draw.circle(screen, BLACK, (mouse_x, mouse_y), cursor_radius)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()