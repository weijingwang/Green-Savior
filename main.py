import pygame, os
from constants import *
from player import Player
from game_object import ObjectManager
from utils import world_to_screen_x, incremental_add
from light import LightManager
from dialogue import DialogueManager

class GameState:
    TITLE = "title"
    INTRO = "intro"
    GAME = "game"
    ENDING = "ending"
    WIN = "win"

class Game:
    def __init__(self):
        pygame.mixer.init()
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Pyweek 40")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        
        # Load images
        self.sky_img = pygame.image.load(os.path.join("assets/images", "sky.png")).convert_alpha()
        self.ground_img = pygame.image.load(os.path.join("assets/images", "ground.png")).convert_alpha()
        self.ground_width = self.ground_img.get_width()
        
        # Game state
        self.state = GameState.TITLE
        self.running = True
        
        # Fade variables
        self.fade_alpha = 0
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fading_to_win = False
        self.fade_speed = 3
        
        # Intro slideshow variables
        self.intro_slides = [
            "Long ago, a tiny plant dreamed of touching the sky...",
            "With each stretch upward, it grew closer to its goal...",
            "Help the plant reach for the heavens!",
            "Press SPACE to grow, but beware the dangers above..."
        ]
        self.current_slide = 0
        self.slide_timer = 0
        self.slide_duration = 180  # 3 seconds at 60 FPS
        
        # Ending slideshow variables
        self.ending_slides = [
            "Congratulations! The little plant reached the sky!",
            "Through determination and courage, dreams can come true...",
            "Even the smallest beings can achieve greatness!",
            "Thank you for playing!"
        ]
        
        # Initialize game components
        self.reset_game()
        
    def reset_game(self):
        """Reset all game variables for a new game"""
        self.player = Player(SCREEN_CENTER_X, GROUND_Y)
        self.object_manager = ObjectManager()
        self.light_manager = LightManager()
        self.dialogue_manager = DialogueManager()
        
        self.current_height = STARTING_HEIGHT
        self.current_height_pixels = INITIAL_SEGMENTS * INITIAL_PIXELS_PER_METER * PLANT_SEGMENT_HEIGHT
        self.speed_x = STARTING_SPEED
        self.world_x = 0
        self.space_pressed = False
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.TITLE:
                    if event.key == pygame.K_RETURN:
                        self.state = GameState.INTRO
                        self.current_slide = 0
                        self.slide_timer = 0
                        
                elif self.state == GameState.INTRO:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.next_slide()
                        
                elif self.state == GameState.GAME:
                    if event.key == pygame.K_SPACE and not self.space_pressed:
                        self.space_pressed = True
                        
                        # Check if dialogue is active
                        if self.dialogue_manager.is_active():
                            self.dialogue_manager.advance_dialogue()
                        # else:
                        #     # Normal game behavior: add neck segment
                        #     self.player.add_segment()
                        #     self.current_height += PLANT_SEGMENT_HEIGHT
                        #     
                        #     # Calculate speed increment for this single segment
                        #     speed_increment = (0.4 * PLANT_SEGMENT_HEIGHT / FPS) * (1 / (1 + SPEED_FALLOFF_PARAM * self.current_height))
                        #     self.speed_x += speed_increment
                    
                    elif event.key == pygame.K_RETURN:
                        # Check win condition
                        if self.current_height > 40:
                            self.fading_to_win = True
                            
                elif self.state == GameState.ENDING:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.next_ending_slide()
                        
                elif self.state == GameState.WIN:
                    if event.key == pygame.K_RETURN:
                        # Reset game and go back to title
                        self.reset_game()
                        self.state = GameState.TITLE
                        self.fade_alpha = 0
                        self.fading_to_win = False
                        
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.space_pressed = False
    
    def next_slide(self):
        """Advance to the next intro slide or start the game"""
        self.current_slide += 1
        self.slide_timer = 0
        
        if self.current_slide >= len(self.intro_slides):
            self.state = GameState.GAME
            
    def next_ending_slide(self):
        """Advance to the next ending slide or show final win screen"""
        self.current_slide += 1
        self.slide_timer = 0
        
        if self.current_slide >= len(self.ending_slides):
            self.state = GameState.WIN
    
    def update(self):
        if self.state == GameState.TITLE:
            # No updates needed for title screen
            pass
            
        elif self.state == GameState.INTRO:
            self.slide_timer += 1
            # Auto-advance slides after duration
            if self.slide_timer >= self.slide_duration:
                self.next_slide()
                
        elif self.state == GameState.GAME:
            # Handle fade to win
            if self.fading_to_win:
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    self.state = GameState.ENDING
                    self.current_slide = 0
                    self.slide_timer = 0
                    self.fading_to_win = False
                return
            
            # Regular game updates
            self.current_height_pixels = self.player.segment_count * (self.player.pixels_per_meter * PLANT_SEGMENT_HEIGHT)
            
            self.player.target_pixels_per_meter = (GROUND_Y - MAX_PLANT_Y) / (self.player.segment_count * PLANT_SEGMENT_HEIGHT)
            self.player.pixels_per_meter = incremental_add(self.player.pixels_per_meter, self.player.target_pixels_per_meter)
            
            self.player.update()
            self.player.update_scale(self.player.pixels_per_meter)
            
            self.object_manager.update_spawning(self.world_x, self.player.pixels_per_meter, self.current_height)
            
            self.current_height, self.speed_x = self.light_manager.update(
                self.world_x, self.player.pixels_per_meter, self.current_height, 
                GROUND_Y, self.player.head_rect, self.player, self.current_height, self.speed_x
            )
            
            self.dialogue_manager.trigger_dialogue(self.current_height)
            self.dialogue_manager.update()
            
            self.world_x += self.speed_x
            
        elif self.state == GameState.ENDING:
            self.slide_timer += 1
            # Auto-advance ending slides
            if self.slide_timer >= self.slide_duration:
                self.next_ending_slide()
    
    def draw_title_screen(self):
        self.screen.fill((50, 100, 150))  # Dark blue background
        
        title_text = self.title_font.render("Sky Reach", True, (255, 255, 255))
        subtitle_text = self.subtitle_font.render("A Plant's Journey to the Heavens", True, (200, 200, 200))
        start_text = self.font.render("Press ENTER to Start", True, (255, 255, 255))
        
        # Center the text
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        self.screen.blit(start_text, start_rect)
    
    def draw_intro_slide(self):
        self.screen.fill((20, 30, 50))  # Dark background
        
        if self.current_slide < len(self.intro_slides):
            slide_text = self.intro_slides[self.current_slide]
            
            # Wrap text if it's too long
            words = slide_text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.font.size(test_line)[0] < SCREEN_WIDTH - 100:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Draw each line
            total_height = len(lines) * 40
            start_y = SCREEN_HEIGHT // 2 - total_height // 2
            
            for i, line in enumerate(lines):
                text_surface = self.font.render(line, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, start_y + i * 40))
                self.screen.blit(text_surface, text_rect)
        
        # Show progress
        progress_text = self.subtitle_font.render(f"{self.current_slide + 1} / {len(self.intro_slides)}", True, (150, 150, 150))
        self.screen.blit(progress_text, (10, SCREEN_HEIGHT - 30))
        
        skip_text = self.subtitle_font.render("Press SPACE or ENTER to continue", True, (150, 150, 150))
        skip_rect = skip_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(skip_text, skip_rect)
    
    def draw_game(self):
        # Draw background
        self.screen.fill((169, 173, 159))  # day sky
        self.screen.blit(self.sky_img, (0, 0))
        
        # Calculate ground scroll offset
        ground_pixels_per_meter = 50
        ground_scroll_offset = int((self.world_x * ground_pixels_per_meter) % self.ground_width)
        
        # Draw ground tiles
        ground_x = -ground_scroll_offset
        while ground_x < SCREEN_WIDTH:
            self.screen.blit(self.ground_img, (ground_x, GROUND_Y))
            ground_x += self.ground_width
        
        # Draw all objects
        self.object_manager.draw_all(self.screen, self.world_x, self.player.pixels_per_meter)
        self.light_manager.draw_all(self.screen, self.world_x, self.player.pixels_per_meter, GROUND_Y)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw dialogue
        self.dialogue_manager.draw(self.screen)
        
        # UI
        height_text = self.font.render(f"Height: {self.current_height:.2f} m", True, (255, 255, 255))
        world_x_text = self.font.render(f"World_x: {self.world_x:.2f} m", True, (255, 255, 255))
        speed_x_text = self.font.render(f"speed_x: {self.speed_x*FPS:.2f} m/s", True, (255, 255, 255))
        pixels_per_meter_text = self.font.render(f"pixels/m: {self.player.pixels_per_meter:.2f}", True, (255, 255, 255))
        
        self.screen.blit(height_text, (10, 10))
        self.screen.blit(world_x_text, (10, 40))
        self.screen.blit(speed_x_text, (10, 70))
        self.screen.blit(pixels_per_meter_text, (10, 100))
        
        # Show win condition hint
        if self.current_height > 35:  # Show hint when close to winning
            win_text = self.font.render("Press ENTER when height > 40m to reach the sky!", True, (255, 255, 0))
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(win_text, win_rect)
    
    def draw_ending_slide(self):
        self.screen.fill((10, 10, 30))  # Very dark background
        
        if self.current_slide < len(self.ending_slides):
            slide_text = self.ending_slides[self.current_slide]
            
            # Wrap text
            words = slide_text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.font.size(test_line)[0] < SCREEN_WIDTH - 100:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Draw each line
            total_height = len(lines) * 40
            start_y = SCREEN_HEIGHT // 2 - total_height // 2
            
            for i, line in enumerate(lines):
                text_surface = self.font.render(line, True, (255, 215, 0))  # Golden text
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, start_y + i * 40))
                self.screen.blit(text_surface, text_rect)
        
        # Show progress
        progress_text = self.subtitle_font.render(f"{self.current_slide + 1} / {len(self.ending_slides)}", True, (150, 150, 150))
        self.screen.blit(progress_text, (10, SCREEN_HEIGHT - 30))
        
        skip_text = self.subtitle_font.render("Press SPACE or ENTER to continue", True, (150, 150, 150))
        skip_rect = skip_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(skip_text, skip_rect)
    
    def draw_win_screen(self):
        self.screen.fill((0, 0, 0))  # Black background
        
        victory_text = self.title_font.render("VICTORY!", True, (255, 215, 0))
        final_text = self.font.render("The plant has reached the sky!", True, (255, 255, 255))
        restart_text = self.subtitle_font.render("Press ENTER to return to title", True, (150, 150, 150))
        
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
        final_rect = final_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        
        self.screen.blit(victory_text, victory_rect)
        self.screen.blit(final_text, final_rect)
        self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.INTRO:
            self.draw_intro_slide()
        elif self.state == GameState.GAME:
            self.draw_game()
        elif self.state == GameState.ENDING:
            self.draw_ending_slide()
        elif self.state == GameState.WIN:
            self.draw_win_screen()
        
        # Draw fade overlay during transition
        if self.fading_to_win and self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            
            if self.state == GameState.GAME:
                fps = self.clock.get_fps()
                print(f"FPS: {fps:.3f}")
            
            self.clock.tick(60)
        
        pygame.quit()

# Create and run the game
if __name__ == "__main__":
    game = Game()
    game.run()