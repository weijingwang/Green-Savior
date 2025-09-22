import pygame
import numpy as np
from constants import *
from elevator import Elevator
from people_manager import PeopleManager
import os

class ElevatorGame:
    def __init__(self):
        # Screen setup
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Elevator Simulation")
        
        # Font and background
        self.font = pygame.font.SysFont("Arial", 36, bold=True)
        try:
            self.background = pygame.image.load("gameplay_draft.png").convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            self.background.set_alpha(128)  # 50% opacity
        except pygame.error:
            # If background image not found, use a solid color
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((200, 200, 200))
            self.background.set_alpha(128)

        # IMAGES (maybe change later) ============================
        self.floor_images = []
        for i in range(1, NUM_FLOORS + 1):
            # Adjust for file naming convention
            filename = f"000{i}.png" if i < 10 else f"00{i}.png"
            
            try:
                # Load the image
                img = pygame.image.load(os.path.join("assets/images/player", filename)).convert_alpha()
                
                # Scale proportionally to a height of 100px
                original_width, original_height = img.get_size()
                aspect_ratio = original_width / original_height
                new_width = int(400 * aspect_ratio)
                scaled_img = pygame.transform.scale(img, (new_width, 400))
                
                self.floor_images.append(scaled_img)
            except pygame.error as e:
                print(f"Failed to load image {filename}: {e}")
                self.floor_images.append(None) # Append a placeholder to maintain indexing


        
        # Game objects
        self.elevator = Elevator()
        self.people_manager = PeopleManager()
        
        # Slider state
        self.slider_x = SLIDER_BAR_X
        
        # Game state
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Arrow key controls
        self.key_repeat_timer = 0
        self.key_repeat_delay = 15  # Frames to wait before repeating
        self.target_floor = 0  # Target floor for arrow key control
        self.control_mode = "mouse"  # "mouse" or "keyboard"
        
        # Bar graph settings - align with slider
        self.bar_graph_width = SLIDER_BAR_WIDTH
        self.bar_graph_height = 200
        self.bar_graph_x = SLIDER_BAR_X
        self.bar_graph_y = HEIGHT - self.bar_graph_height - 20
        
        # Hide default cursor and use custom one
        pygame.mouse.set_visible(False)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle control mode
                    if self.control_mode == "mouse":
                        self.control_mode = "keyboard"
                        # Set target floor to match current elevator position
                        current_elevator_floor = self.elevator.get_current_floor()
                        self.target_floor = current_elevator_floor
                    else:
                        self.control_mode = "mouse"
                        # Update slider to match current elevator position
                        current_floor = self.elevator.get_current_floor()
                        t = current_floor / (NUM_FLOORS - 1)
                        self.slider_x = SLIDER_BAR_X + (1 - t) * SLIDER_BAR_WIDTH
                elif event.key == pygame.K_LEFT and self.control_mode == "keyboard":
                    # Move down one floor (floors are numbered 0=top, so increase)
                    self.target_floor = min(NUM_FLOORS - 1, self.target_floor + 1)
                    self.key_repeat_timer = 0
                elif event.key == pygame.K_RIGHT and self.control_mode == "keyboard":
                    # Move up one floor (decrease floor number)
                    self.target_floor = max(0, self.target_floor - 1)
                    self.key_repeat_timer = 0
        
        # Handle key repeat for held keys (only in keyboard mode)
        if self.control_mode == "keyboard":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                self.key_repeat_timer += 1
                if self.key_repeat_timer >= self.key_repeat_delay:
                    if keys[pygame.K_LEFT]:
                        self.target_floor = min(NUM_FLOORS - 1, self.target_floor + 1)
                    elif keys[pygame.K_RIGHT]:
                        self.target_floor = max(0, self.target_floor - 1)
                    self.key_repeat_timer = 0
    
    def update(self):
        """Update game logic"""
        if self.control_mode == "keyboard":
            # Use arrow key target
            t = self.target_floor / (NUM_FLOORS - 1)
            target_y = RECT_Y + t * (RECT_HEIGHT - self.elevator.height)
            # Also update slider to match (visual only)
            self.slider_x = SLIDER_BAR_X + (1 - t) * SLIDER_BAR_WIDTH
        else:
            # Mouse control mode - update mouse/slider position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x < WIDTH // 2:
                mouse_x = WIDTH // 2
            if mouse_x > WIDTH - CURSOR_RADIUS:
                mouse_x = WIDTH - CURSOR_RADIUS
            
            self.slider_x = min(max(mouse_x, SLIDER_BAR_X), SLIDER_BAR_X + SLIDER_BAR_WIDTH)
            
            # Calculate target elevator position based on slider
            t = (self.slider_x - SLIDER_BAR_X) / SLIDER_BAR_WIDTH
            target_y = RECT_Y + (1 - t) * (RECT_HEIGHT - self.elevator.height)
            # Update target floor to match slider - fix the mapping
            self.target_floor = round((1 - t) * (NUM_FLOORS - 1))
        
        # Update elevator
        self.elevator.update(target_y)
        
        # Update people (pass elevator reference for streaming logic)
        self.people_manager.update(self.elevator)
    
    def draw_bar_graph(self):
        """Draw bar graph showing destination floor counts"""
        destination_counts = self.people_manager.get_destination_counts()
        
        # Always draw the graph background and structure
        # Background for bar graph
        graph_rect = pygame.Rect(self.bar_graph_x - 10, self.bar_graph_y - 10, 
                                self.bar_graph_width + 20, self.bar_graph_height + 20)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), graph_rect)
        pygame.draw.rect(self.screen, BLACK, graph_rect, 2)
        
        # Title
        title_font = pygame.font.SysFont("Arial", 18, bold=True)
        title_text = title_font.render("Elevator Passenger Destinations", True, BLACK)
        self.screen.blit(title_text, (self.bar_graph_x, self.bar_graph_y - 30))
        
        # Calculate bar dimensions
        bar_width = self.bar_graph_width / NUM_FLOORS
        
        # Draw bars only if there are passengers
        if destination_counts and any(count > 0 for count in destination_counts):
            max_count = max(destination_counts)
            
            for i, count in enumerate(destination_counts):
                if count > 0:
                    bar_height = (count / max_count) * (self.bar_graph_height - 30)
                    
                    # Calculate bar position to align exactly with slider positions
                    # Use the exact same calculation as the slider
                    floor_t = i / (NUM_FLOORS - 1) if NUM_FLOORS > 1 else 0
                    bar_center_x = self.bar_graph_x + (1 - floor_t) * self.bar_graph_width
                    bar_x = bar_center_x - bar_width // 2
                    bar_y = self.bar_graph_y + self.bar_graph_height - bar_height - 15  # Leave space at bottom
                    
                    # Color coding: use target floor to prevent flickering during bouncing
                    target_floor = self.target_floor
                    bar_color = RED if i == target_floor else GREEN
                    
                    # Draw bar
                    pygame.draw.rect(self.screen, bar_color, 
                                   (bar_x, bar_y, bar_width, bar_height))
                    
                    # Draw count text on top of bar if there's space
                    if bar_height > 20:
                        count_font = pygame.font.SysFont("Arial", 12)
                        count_text = count_font.render(str(count), True, WHITE)
                        text_rect = count_text.get_rect()
                        text_x = bar_x + (bar_width - text_rect.width) // 2
                        text_y = bar_y + 5
                        self.screen.blit(count_text, (text_x, text_y))
        
        # Always draw floor labels on x-axis (every 5th floor to avoid crowding)
        label_font = pygame.font.SysFont("Arial", 10)
        for i in range(0, NUM_FLOORS, 5):
            floor_display_number = NUM_FLOORS - i  # Convert to display numbering (21, 16, 11, 6, 1)
            
            # Calculate label position to align exactly with slider and bar positions
            floor_t = i / (NUM_FLOORS - 1) if NUM_FLOORS > 1 else 0
            label_x = self.bar_graph_x + (1 - floor_t) * self.bar_graph_width - 5
            label_y = self.bar_graph_y + self.bar_graph_height + 5
            
            label_text = label_font.render(str(floor_display_number), True, BLACK)
            self.screen.blit(label_text, (label_x, label_y))
    
    def draw(self):
        """Draw everything to the screen"""
        # Clear screen and draw background
        self.screen.fill(WHITE)
        self.screen.blit(self.background, (0, 0))

        # EDIT LATER MAYBE ===============================================
        # Blit the image for the current target floor
        if 0 <= self.target_floor < len(self.floor_images) and self.floor_images[self.target_floor] is not None:
            # Get the image to blit
            img_to_blit = self.floor_images[self.target_floor]
            img_rect = img_to_blit.get_rect()
            
            # Position the image on the right half of the screen
            # For example, centered vertically on the right side
            img_rect.centerx = (WIDTH // 2) + (WIDTH // 4)
            img_rect.centery = HEIGHT // 2 - 100
            
            # Blit the image to the screen
            self.screen.blit(img_to_blit, img_rect)
        
        # Draw elevator shaft
        pygame.draw.rect(self.screen, BLUE, (RECT_X, RECT_Y, RECT_WIDTH, RECT_HEIGHT))
        
        # Draw floor lines
        floor_height = RECT_HEIGHT / NUM_FLOORS
        for i in range(NUM_FLOORS + 1):  # +1 so we get the top line too
            y = RECT_Y + i * floor_height
            pygame.draw.line(self.screen, WHITE, (RECT_X, y), (RECT_X + RECT_WIDTH, y), 2)
        
        # Draw center line for reference
        pygame.draw.line(self.screen, BLACK, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 1)
        
        # Draw elevator
        self.elevator.draw(self.screen)
        
        # Draw people
        self.people_manager.draw(self.screen)
        
        # Draw bar graph first (so slider appears on top)
        self.draw_bar_graph()
        
        # Draw slider bar and circle on top of graph
        pygame.draw.rect(self.screen, BLACK, (SLIDER_BAR_X, SLIDER_BAR_Y - SLIDER_BAR_HEIGHT // 2,
                        SLIDER_BAR_WIDTH, SLIDER_BAR_HEIGHT))
        pygame.draw.circle(self.screen, RED, (self.slider_x, SLIDER_BAR_Y), SLIDER_RADIUS)
        
        # Draw UI text
        self.draw_ui()
        
        # Draw custom cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.circle(self.screen, BLACK, (mouse_x, mouse_y), CURSOR_RADIUS)
    
    def draw_ui(self):
        """Draw UI elements like text displays"""
        current_floor = self.elevator.get_current_floor()
        
        # Floor display
        floor_text = self.font.render(f"Floor: {current_floor + 1}", True, BLACK)
        self.screen.blit(floor_text, (20, 20))
        
        # FPS display
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, RED)
        self.screen.blit(fps_text, (20, 60))
        
        # People count
        people_count_text = self.font.render(f"Waiting: {self.people_manager.get_people_count()}", True, BLACK)
        self.screen.blit(people_count_text, (20, 100))
        
        # Elevator passengers
        passenger_count_text = self.font.render(f"In Elevator: {self.people_manager.get_elevator_passenger_count()}", True, GREEN)
        self.screen.blit(passenger_count_text, (20, 140))
        
        # Current floor queue size
        current_floor_queue = self.people_manager.get_floor_queue_size(current_floor)
        queue_text = self.font.render(f"Floor {current_floor + 1} Queue: {current_floor_queue}", True, PURPLE)
        self.screen.blit(queue_text, (20, 180))
        
        # Target floor display (for arrow key control)
        target_text = self.font.render(f"Target: Floor {self.target_floor + 1}", True, BLUE)
        self.screen.blit(target_text, (20, 220))
        
        # Controls help and mode display
        if self.control_mode == "keyboard":
            mode_text = self.font.render("KEYBOARD MODE", True, GREEN)
            self.screen.blit(mode_text, (20, 260))
            control_text = pygame.font.SysFont("Arial", 24).render("← Down Floor | → Up Floor | SPACE: Switch to Mouse", True, BLACK)
            self.screen.blit(control_text, (20, 300))
        else:
            mode_text = self.font.render("MOUSE MODE", True, BLUE)
            self.screen.blit(mode_text, (20, 260))
            control_text = pygame.font.SysFont("Arial", 24).render("Drag slider to control | SPACE: Switch to Keyboard", True, BLACK)
            self.screen.blit(control_text, (20, 300))
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)