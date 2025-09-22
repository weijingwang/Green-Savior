import pygame
from constants import *
from elevator import Elevator
from people_manager import PeopleManager

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
        
        # Game objects
        self.elevator = Elevator()
        self.people_manager = PeopleManager()
        
        # Slider state
        self.slider_x = SLIDER_BAR_X
        
        # Game state
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Hide default cursor and use custom one
        pygame.mouse.set_visible(False)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self):
        """Update game logic"""
        # Update mouse/slider position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x < WIDTH // 2:
            mouse_x = WIDTH // 2
        if mouse_x > WIDTH - CURSOR_RADIUS:
            mouse_x = WIDTH - CURSOR_RADIUS
        
        self.slider_x = min(max(mouse_x, SLIDER_BAR_X), SLIDER_BAR_X + SLIDER_BAR_WIDTH)
        
        # Calculate target elevator position based on slider
        t = (self.slider_x - SLIDER_BAR_X) / SLIDER_BAR_WIDTH
        target_y = RECT_Y + (1 - t) * (RECT_HEIGHT - self.elevator.height)
        
        # Update elevator
        self.elevator.update(target_y)
        
        # Update people
        self.people_manager.update()
    
    def draw(self):
        """Draw everything to the screen"""
        # Clear screen and draw background
        self.screen.fill(WHITE)
        self.screen.blit(self.background, (0, 0))
        
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
        
        # Draw slider bar and circle
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
        people_count_text = self.font.render(f"People: {self.people_manager.get_people_count()}", True, BLACK)
        self.screen.blit(people_count_text, (20, 100))
        
        # Current floor queue size
        current_floor_queue = self.people_manager.get_floor_queue_size(current_floor)
        queue_text = self.font.render(f"Floor {current_floor + 1} Queue: {current_floor_queue}", True, PURPLE)
        self.screen.blit(queue_text, (20, 140))
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)