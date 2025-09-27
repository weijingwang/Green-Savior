import pygame, os
from constants import *
from title_screen import TitleScreen
from slideshow import Slideshow  
from gameplay import Gameplay
from win_screen import WinScreen

class GameState:
    TITLE = "title"
    INTRO_SLIDESHOW = "intro_slideshow"
    GAME = "game"
    ENDING_SLIDESHOW = "ending_slideshow"
    WIN = "win"

class Game:
    def __init__(self):
        pygame.mixer.init()
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Pyweek 40")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        
        # Load music files
        self.title_music = "assets/sound/last_moment.ogg"
        self.game_music = "assets/sound/fallen_city.ogg"
        self.ending_music = "assets/sound/end.ogg"
        
        # Track current music state
        self.current_music = None
        
        # Game state
        self.state = GameState.TITLE
        self.running = True
        
        # Define slide data
        self.intro_slides_data = [
            {"text": "In my old age I see clearly the wasteland we have created... a world run on greed", "image": "intro/intro1.png", "duration": 4},
            {"text": "We chased power and profits...until the earth was stripped bare", "image": "intro/intro2.png", "duration": 4},
            {"text": "I hold the last green, you will become our messiah", "image": "intro/intro3.png", "duration": 4},
            {"text": "may this green savior forgive my sins", "image": "intro/intro4.png", "duration": 4},
            {"text": "*drops", "image": "intro/intro5.png", "duration": 4},
            {"text": "This is but a small redemption...", "image": "intro/intro6.png", "duration": 4}
        ]
        
        self.ending_slides_data = [
            {"text": "", "image": "end/end1.jpg", "duration": 4},
            {"text": "", "image": "end/end2.jpg", "duration": 4},
            {"text": "", "image": "end/end3.jpg", "duration": 4},
            {"text": "", "image": "end/end4.jpg", "duration": 4},
            {"text": "", "image": "end/end5.jpg", "duration": 4},
            {"text": "", "image": "end/end6.jpg", "duration": 4},
        ]
        
        # Initialize game components
        self.title_screen = TitleScreen(self.screen, self.font, self.title_font)
        self.intro_slideshow = Slideshow(self.screen, self.font, self.subtitle_font, self.intro_slides_data, is_ending=False)
        self.gameplay = Gameplay(self.screen, self.font)
        self.ending_slideshow = Slideshow(self.screen, self.font, self.subtitle_font, self.ending_slides_data, is_ending=True)
        self.win_screen = WinScreen(self.screen, self.font, self.title_font, self.subtitle_font)
        
        # Start title music
        self.play_music(self.title_music, 0.3, loops=-1)
        
    def play_music(self, music_file, volume, loops=0):
        """Play music with specified volume and loop settings"""
        if self.current_music != music_file:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops)
                self.current_music = music_file
                print(f"Playing music: {music_file} at volume {volume}")
            except pygame.error as e:
                print(f"Could not load music {music_file}: {e}")
                
    def handle_events(self):
        """Handle input events based on current state"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                # Pass event to current state handler
                if self.state == GameState.TITLE:
                    if self.title_screen.handle_event(event):
                        pass  # Title screen handles its own transitions
                        
                elif self.state == GameState.INTRO_SLIDESHOW:
                    if self.intro_slideshow.handle_event(event):
                        self.state = GameState.GAME
                        
                elif self.state == GameState.GAME:
                    if self.gameplay.handle_event(event):
                        pass  # Gameplay handles its own transitions
                        
                elif self.state == GameState.ENDING_SLIDESHOW:
                    if self.ending_slideshow.handle_event(event):
                        self.state = GameState.WIN
                        
                elif self.state == GameState.WIN:
                    if self.win_screen.handle_event(event):
                        # Return to title
                        self.reset_to_title()
    
    def update(self):
        """Update current state"""
        if self.state == GameState.TITLE:
            if self.title_screen.update():
                # Title fade complete, go to intro slideshow
                self.state = GameState.INTRO_SLIDESHOW
                self.intro_slideshow.reset()
                
        elif self.state == GameState.INTRO_SLIDESHOW:
            if self.intro_slideshow.update():
                # Intro slideshow complete, go to game
                self.state = GameState.GAME
                self.gameplay.reset()
                # Start game music
                self.play_music(self.game_music, 0.4, loops=-1)
                
        elif self.state == GameState.GAME:
            if self.gameplay.update():
                # Game wants to transition to ending
                self.state = GameState.ENDING_SLIDESHOW
                self.ending_slideshow.reset()
                # Start ending music
                self.play_music(self.ending_music, 0.5, loops=0)
                
        elif self.state == GameState.ENDING_SLIDESHOW:
            if self.ending_slideshow.update():
                # Ending slideshow complete, go to win screen
                self.state = GameState.WIN
                # Don't change music - let ending music continue playing
                
        elif self.state == GameState.WIN:
            self.win_screen.update()
    
    def reset_to_title(self):
        """Reset everything and return to title screen"""
        self.state = GameState.TITLE
        self.title_screen.reset()
        self.intro_slideshow.reset()
        self.gameplay.reset()
        self.ending_slideshow.reset()
        # Resume title music
        self.play_music(self.title_music, 0.3, loops=-1)
    
    def draw(self):
        """Draw current state"""
        if self.state == GameState.TITLE:
            self.title_screen.draw()
        elif self.state == GameState.INTRO_SLIDESHOW:
            self.intro_slideshow.draw()
        elif self.state == GameState.GAME:
            self.gameplay.draw()
        elif self.state == GameState.ENDING_SLIDESHOW:
            self.ending_slideshow.draw()
        elif self.state == GameState.WIN:
            self.win_screen.draw()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            
            if self.state == GameState.GAME:
                fps = self.clock.get_fps()
                print(f"FPS: {fps:.3f}")
            
            self.clock.tick(60)
        
        pygame.mixer.music.stop()  # Stop music when quitting
        pygame.quit()

# Create and run the game
if __name__ == "__main__":
    game = Game()
    game.run()