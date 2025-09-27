from constants import *
import pygame
import os

class DialogueManager:
    def __init__(self):
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Load sound effects
        try:
            self.click_small_sound = pygame.mixer.Sound(os.path.join("assets/sound", "CLICK_SMALL.ogg"))
        except pygame.error as e:
            print(f"Could not load CLICK_SMALL.ogg: {e}")
            self.click_small_sound = None
        
        # Load dialogue images (you'll need to replace these with your actual image paths)
        self.dialogue_sets = {
            STARTING_HEIGHT: [  # Initial height dialogue set
                "assets/images/dialogue1/dialogue1.png",
                "assets/images/dialogue1/dialogue2.png", 
                "assets/images/dialogue1/dialogue3.png"
            ],
            40: [  # Height 40 dialogue set
                "assets/images/dialogue2/dialogue1.png",
                "assets/images/dialogue2/dialogue2.png",
            ]
        }
        
        # Load all dialogue images
        self.loaded_dialogues = {}
        self.dialogue_widths = {}  # Store widths for centering
        for height, dialogue_paths in self.dialogue_sets.items():
            self.loaded_dialogues[height] = []
            self.dialogue_widths[height] = []
            for path in dialogue_paths:
                try:
                    # Try to load the image, use placeholder if file doesn't exist
                    img = pygame.image.load(path).convert_alpha()
                    self.loaded_dialogues[height].append(img)
                    self.dialogue_widths[height].append(img.get_width())
                except pygame.error:
                    # Create a placeholder dialogue box if image doesn't exist
                    placeholder = self.create_placeholder_dialogue(f"Dialogue {len(self.loaded_dialogues[height]) + 1}")
                    self.loaded_dialogues[height].append(placeholder)
                    self.dialogue_widths[height].append(placeholder.get_width())
        
        self.current_dialogues = []
        self.current_dialogue_widths = []
        self.current_dialogue_index = 0
        self.dialogue_active = False
        self.triggered_heights = set()  # Track which heights have already triggered
        
        # Fade system
        self.fade_out = False
        self.fade_in = False
        self.fade_alpha = 255
        self.fade_speed = 5  # How fast to fade (higher = faster)
        
        # Position for dialogue box (centered on x-axis)
        self.dialogue_y = 500
    
    def create_placeholder_dialogue(self, text):
        """Create a placeholder dialogue box with text"""
        width, height = 300, 100
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw dialogue box background
        pygame.draw.rect(surface, (0, 0, 0, 180), (0, 0, width, height))
        pygame.draw.rect(surface, (255, 255, 255), (0, 0, width, height), 3)
        
        # Draw text
        font = pygame.font.SysFont("Arial", 16)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(width//2, height//2))
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def trigger_dialogue(self, height):
        """Check if dialogue should be triggered at current height"""
        # Check each dialogue trigger height
        for trigger_height in self.dialogue_sets.keys():
            # Trigger if we're at or past the trigger height and haven't triggered it yet
            if height >= trigger_height and trigger_height not in self.triggered_heights:
                self.triggered_heights.add(trigger_height)
                self.start_dialogue_set(trigger_height)
                break  # Only trigger one set at a time
    
    def start_dialogue_set(self, height):
        """Start a new dialogue set"""
        if height in self.loaded_dialogues and self.loaded_dialogues[height]:
            self.current_dialogues = self.loaded_dialogues[height].copy()
            self.current_dialogue_widths = self.dialogue_widths[height].copy()
            self.current_dialogue_index = 0
            self.dialogue_active = True
            self.fade_out = False
            self.fade_in = True
            self.fade_alpha = 0  # Start invisible for fade in
    
    def advance_dialogue(self):
        """Advance to next dialogue or start fade out"""
        if not self.dialogue_active or self.fade_in:  # Don't advance while fading in
            return
        
        # Play sound effect when advancing dialogue
        if self.click_small_sound:
            try:
                self.click_small_sound.play()
            except pygame.error as e:
                print(f"Could not play click_small sound: {e}")
        
        self.current_dialogue_index += 1
        
        # If we've reached the end of current dialogue set, start fade out
        if self.current_dialogue_index >= len(self.current_dialogues):
            self.fade_out = True
        # Normal switch between dialogues - no fade
    
    def update(self):
        """Update dialogue state, handle fade in/out"""
        if self.fade_in:
            # Fade in
            self.fade_alpha += self.fade_speed
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fade_in = False
        elif self.fade_out:
            # Fade out
            self.fade_alpha -= self.fade_speed
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.dialogue_active = False
                self.fade_out = False
                self.current_dialogues = []
                self.current_dialogue_widths = []
                self.current_dialogue_index = 0
    
    def draw(self, screen):
        """Draw current dialogue box"""
        if self.dialogue_active and self.current_dialogues:
            if self.fade_out:
                # Show the last dialogue during fade out
                dialogue_index = len(self.current_dialogues) - 1
            else:
                dialogue_index = self.current_dialogue_index
                
            current_dialogue = self.current_dialogues[dialogue_index]
            dialogue_width = self.current_dialogue_widths[dialogue_index]
            
            # Center the dialogue horizontally
            dialogue_x = (SCREEN_WIDTH - dialogue_width) // 2
            
            # Apply fade effect only when fading in or fading out
            if (self.fade_in or self.fade_out) and self.fade_alpha < 255:
                # Create a temporary surface with the desired alpha
                temp_surface = pygame.Surface(current_dialogue.get_size(), pygame.SRCALPHA)
                temp_surface.blit(current_dialogue, (0, 0))
                temp_surface.set_alpha(self.fade_alpha)
                screen.blit(temp_surface, (dialogue_x, self.dialogue_y))
            else:
                # No fade needed, draw normally
                screen.blit(current_dialogue, (dialogue_x, self.dialogue_y))
    
    def is_active(self):
        return self.dialogue_active