import random
from person import Person
from constants import *

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