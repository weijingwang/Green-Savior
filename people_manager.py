import random
from person import Person
from elevator_passenger import ElevatorPassenger
from constants import *

class PeopleManager:
    def __init__(self):
        # Dictionary to store people by floor for easy queue management
        self.people_by_floor = {i: [] for i in range(NUM_FLOORS)}
        self.all_people = []  # Keep all people for drawing and cleanup
        self.elevator_passengers = []  # People inside the elevator
        self.exiting_passengers = []  # People streaming out of elevator
        self.spawn_timer = 0
        self.spawn_interval = random.randint(15, 45)  # Faster spawning (0.25-0.75 seconds at 60fps)
        self.center_line_x = WIDTH // 2
        
        # Track destination floor counts for bar graph
        self.destination_counts = [0] * NUM_FLOORS
        
        # Exit timing control
        self.exit_timer = 0
        self.exit_interval = 20  # Frames between each person exiting (slower than boarding)
        
    def update_destination_counts(self):
        """Update the count of elevator passengers wanting to go to each floor"""
        # Reset counts
        self.destination_counts = [0] * NUM_FLOORS
        
        # Only count elevator passengers' destinations (not waiting people)
        for passenger in self.elevator_passengers:
            if 0 <= passenger.destination_floor < NUM_FLOORS:
                self.destination_counts[passenger.destination_floor] += 1
        
    def get_destination_counts(self):
        """Get the array of destination counts for the bar graph"""
        return self.destination_counts
        
    def update(self, elevator, game=None):
        # Spawn new people
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_person()
            self.spawn_timer = 0
            self.spawn_interval = random.randint(15, 45)  # Reset with faster random interval
        
        # Handle people streaming into elevator
        self.handle_elevator_boarding(elevator, game)
        
        # Handle people streaming out of elevator  
        self.handle_elevator_exiting(elevator, game)
        
        # Update existing people
        people_to_remove = []
        for person in self.all_people[:]:  # Use slice to avoid modification issues
            reached_elevator = person.update()
            if reached_elevator:
                # Person has reached elevator, convert to passenger
                passenger = ElevatorPassenger(
                    person.destination_floor,
                    person.color,
                    person.radius,
                    person.speed
                )
                self.elevator_passengers.append(passenger)
                people_to_remove.append(person)
                
                # Play enter sound when person actually enters elevator
                if game and game.sound_enter:
                    game.sound_enter.play()
        
        # Remove people who entered elevator
        for person in people_to_remove:
            if person in self.all_people:
                self.all_people.remove(person)
            if person.floor in self.people_by_floor and person in self.people_by_floor[person.floor]:
                self.people_by_floor[person.floor].remove(person)
                # Only update queue positions for people who are NOT currently streaming in
                for i, remaining_person in enumerate(self.people_by_floor[person.floor]):
                    if not remaining_person.streaming_in:
                        remaining_person.update_queue_position(i)
        
        # Update exiting passengers
        self.update_exiting_passengers()
            
        # Only do cleanup occasionally and be very conservative
        if self.spawn_timer % 60 == 0:  # Only check every second
            self.cleanup_distant_people()
            
        # Update destination counts for bar graph
        self.update_destination_counts()
    
    def handle_elevator_boarding(self, elevator, game=None):
        """Handle people streaming into elevator when it arrives at their floor"""
        # Check each floor to see if elevator is on it
        for floor in range(NUM_FLOORS):
            if elevator.is_on_floor(floor) and floor in self.people_by_floor:
                floor_people = self.people_by_floor[floor]
                if len(floor_people) > 0:
                    elevator_center_x = elevator.get_center_x()
                    
                    # Only start streaming the FIRST person in line who isn't already streaming
                    for person in floor_people:
                        if person.waiting and not person.streaming_in:
                            person.start_streaming_in(elevator_center_x)
                            # Note: Enter sound is now played when person actually reaches elevator
                            # in the main update loop, not when they start streaming
                            break  # Only start one person at a time
    
    def handle_elevator_exiting(self, elevator, game=None):
        """Handle passengers exiting when elevator stops at their destination"""
        if not elevator.is_stopped_for_exit():
            self.exit_timer = 0  # Reset timer if elevator is moving
            return
        
        # Increment exit timer
        self.exit_timer += 1
        
        # Only allow one person to start exiting every exit_interval frames
        if self.exit_timer < self.exit_interval:
            return
            
        passengers_to_remove = []
        
        # Find the FIRST passenger who needs to exit at this floor and isn't already streaming
        for passenger in self.elevator_passengers:
            if elevator.is_on_floor(passenger.destination_floor) and not passenger.streaming_out:
                # Start streaming out to the LEFT side
                floor_height = RECT_HEIGHT / NUM_FLOORS
                floor_y = RECT_Y + passenger.destination_floor * floor_height + floor_height * 0.7
                passenger.start_streaming_out(elevator.get_center_x(), floor_y)
                self.exiting_passengers.append(passenger)
                passengers_to_remove.append(passenger)
                
                # Play exit sound
                if game and game.sound_exit:
                    game.sound_exit.play()
                
                # Reset timer for next passenger
                self.exit_timer = 0
                break  # Only start one passenger at a time
        
        # Remove passengers who started exiting from elevator
        for passenger in passengers_to_remove:
            if passenger in self.elevator_passengers:
                self.elevator_passengers.remove(passenger)
    
    def update_exiting_passengers(self):
        """Update passengers who are streaming out and fading"""
        remaining_passengers = []
        for passenger in self.exiting_passengers:
            passenger.update()
            if not passenger.is_off_screen():
                remaining_passengers.append(passenger)
        self.exiting_passengers = remaining_passengers
    
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
        """Remove people from the front of the queue on a specific floor (legacy method)"""
        # This method is no longer needed since people stream automatically
        pass
    
    def get_floor_queue_size(self, floor):
        """Get the number of people waiting on a specific floor"""
        if floor < 0 or floor >= NUM_FLOORS:
            return 0
        return len(self.people_by_floor[floor])
    
    def get_elevator_passenger_count(self):
        """Get the number of people inside the elevator"""
        return len(self.elevator_passengers)
    
    def draw(self, screen):
        # Draw people waiting and streaming in
        for person in self.all_people:
            person.draw(screen)
        
        # Draw people exiting elevator (streaming to the left)
        for passenger in self.exiting_passengers:
            passenger.draw(screen)
    
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
        
        # Also cleanup exiting passengers who have traveled far enough
        remaining_passengers = []
        for passenger in self.exiting_passengers:
            # Let them travel further before removing (was -50, now -150)
            if passenger.x > -150 and passenger.alpha > 0:
                remaining_passengers.append(passenger)
        self.exiting_passengers = remaining_passengers