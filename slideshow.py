import pygame
import os
from constants import *

class Slideshow:
    def __init__(self, screen, font, subtitle_font, slides_data, is_ending=False):
        self.screen = screen
        self.font = font
        self.subtitle_font = subtitle_font
        self.slides_data = slides_data
        self.is_ending = is_ending
        
        # Slideshow state
        self.current_slide = 0
        self.slide_timer = 0
        self.slide_display_time = 0
        
        # Fade variables - simplified
        self.fade_alpha = 0  # 0 = fully showing current slide, 255 = fully black
        self.fade_speed = 4
        self.is_transitioning = False
        self.current_slide_surface = None
        
        # Slideshow states - simplified
        self.FADE_IN = "fade_in"
        self.DISPLAY = "display"
        self.FADE_OUT = "fade_out"
        self.state = self.FADE_IN
        
        # Load slideshow images
        self.slideshow_images = {}
        for slide in self.slides_data:
            if slide["image"] and slide["image"] not in self.slideshow_images:
                try:
                    # Convert to regular surface for better alpha blending
                    img = pygame.image.load(os.path.join("assets/images", slide["image"])).convert()
                    self.slideshow_images[slide["image"]] = img
                except pygame.error:
                    print(f"Warning: Could not load image {slide['image']}")
                    self.slideshow_images[slide["image"]] = None
        
        # Initialize first slide
        self.reset()
    
    def reset(self):
        """Reset slideshow to beginning"""
        self.current_slide = 0
        self.slide_timer = 0
        self.slide_display_time = 0
        self.fade_alpha = 255  # Start fully black
        self.state = self.FADE_IN
        self.is_transitioning = True
        self.current_slide_surface = self.create_slide_surface(0, show_text=True)
    
    def draw_slide_with_alpha(self, slide_index, alpha, show_text=True):
        """Draw a slide directly to screen with specified alpha"""
        if slide_index < len(self.slides_data):
            slide_data = self.slides_data[slide_index]
            slide_text = slide_data["text"]
            slide_image = slide_data["image"]
            
            # Draw background with alpha
            background_color = (10, 10, 30) if self.is_ending else (20, 30, 50)
            # Create background surface with alpha
            bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            bg_surface.fill(background_color)
            bg_surface.set_alpha(alpha)
            self.screen.blit(bg_surface, (0, 0))
            
            # Draw image if available with alpha
            if slide_image and slide_image in self.slideshow_images and self.slideshow_images[slide_image]:
                img = self.slideshow_images[slide_image].copy()
                img.set_alpha(alpha)
                self.screen.blit(img, (0, 0))
            
            # Only draw text if show_text is True
            if show_text:
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
                
                # Draw each line with alpha
                total_height = len(lines) * 40
                start_y = SCREEN_HEIGHT // 2 - total_height // 2
                
                text_color = (255, 215, 0) if self.is_ending else (255, 255, 255)  # Golden for ending, white for intro
                
                for i, line in enumerate(lines):
                    text_surface = self.font.render(line, True, text_color)
                    text_surface.set_alpha(alpha)
                    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, start_y + i * 40))
                    self.screen.blit(text_surface, text_rect)
                
                # Show progress with alpha
                progress_text = self.subtitle_font.render(f"{slide_index + 1} / {len(self.slides_data)}", True, (150, 150, 150))
                progress_text.set_alpha(alpha)
                self.screen.blit(progress_text, (10, SCREEN_HEIGHT - 30))
                
                skip_text = self.subtitle_font.render("Press SPACE or ENTER to continue", True, (150, 150, 150))
                skip_text.set_alpha(alpha)
                skip_rect = skip_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
                self.screen.blit(skip_text, skip_rect)

    def create_slide_surface(self, slide_index, show_text=True):
        """Create a surface for a specific slide"""
        # Create surface with same pixel format as screen for better blending
        slide_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        
        if slide_index < len(self.slides_data):
            slide_data = self.slides_data[slide_index]
            slide_text = slide_data["text"]
            slide_image = slide_data["image"]
            
            # Fill with background
            if self.is_ending:
                slide_surface.fill((10, 10, 30))  # Very dark background for ending
            else:
                slide_surface.fill((20, 30, 50))  # Dark background for intro
            
            # Draw image if available at 0,0 without scaling
            if slide_image and slide_image in self.slideshow_images and self.slideshow_images[slide_image]:
                img = self.slideshow_images[slide_image]
                slide_surface.blit(img, (0, 0))
            
            # Only draw text if show_text is True
            if show_text:
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
                
                # Draw each line on slide surface
                total_height = len(lines) * 40
                start_y = SCREEN_HEIGHT // 2 - total_height // 2
                
                text_color = (255, 215, 0) if self.is_ending else (255, 255, 255)  # Golden for ending, white for intro
                
                for i, line in enumerate(lines):
                    text_surface = self.font.render(line, True, text_color)
                    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, start_y + i * 40))
                    slide_surface.blit(text_surface, text_rect)
                
                # Show progress on slide surface
                progress_text = self.subtitle_font.render(f"{slide_index + 1} / {len(self.slides_data)}", True, (150, 150, 150))
                slide_surface.blit(progress_text, (10, SCREEN_HEIGHT - 30))
                
                skip_text = self.subtitle_font.render("Press SPACE or ENTER to continue", True, (150, 150, 150))
                skip_rect = skip_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
                slide_surface.blit(skip_text, skip_rect)
        
        return slide_surface
    
    def handle_event(self, event):
        """Handle input events. Returns True if slideshow should end."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.next_slide()
        return False
    
    def next_slide(self):
        """Advance to the next slide. Returns True if slideshow is complete."""
        if self.is_transitioning:
            return False  # Don't allow skipping during transition
            
        # Start fade out to black
        self.state = self.FADE_OUT
        self.is_transitioning = True
        self.fade_alpha = 0  # Start fade out from 0
        return False
    
    def update(self):
        """Update slideshow. Returns True when slideshow is complete."""
        if self.state == self.FADE_IN:
            # Fade in from black to current slide
            self.fade_alpha -= self.fade_speed
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.state = self.DISPLAY
                self.is_transitioning = False
                self.slide_display_time = 0
                
        elif self.state == self.DISPLAY:
            # Display slide normally and check for auto-advance
            if not self.is_transitioning:
                self.slide_display_time += 1
                current_slide_duration = int(self.slides_data[self.current_slide]["duration"] * 60)
                
                if self.slide_display_time >= current_slide_duration:
                    # Auto-advance to next slide
                    self.next_slide()
                    
        elif self.state == self.FADE_OUT:
            # Fade out current slide to black
            self.fade_alpha += self.fade_speed
            print(f"Fade out: fade_alpha = {self.fade_alpha}")  # Debug
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                print(f"Fade out complete, current_slide = {self.current_slide}, total = {len(self.slides_data)}")  # Debug
                
                # Check if this is the last slide
                if self.current_slide >= len(self.slides_data) - 1:
                    # End of slideshow
                    print("End of slideshow")  # Debug
                    return True
                else:
                    # Move to next slide and prepare for fade in
                    print(f"Moving to next slide {self.current_slide + 1}")  # Debug
                    self.current_slide += 1
                    # Create the next slide surface AFTER the screen is black
                    self.current_slide_surface = self.create_slide_surface(self.current_slide, show_text=True)
                    self.state = self.FADE_IN
                    self.is_transitioning = True
                    # fade_alpha stays at 255 for fade in from black
        
        return False
    
    def draw(self):
        """Draw the slideshow"""
        # Fill with black background first
        self.screen.fill((0, 0, 0))
        
        if self.state == self.FADE_IN:
            # Fading in current slide from black
            if self.fade_alpha > 0:
                # Calculate alpha for the entire slide: 0 when fade_alpha=255, 255 when fade_alpha=0
                slide_alpha = 255 - self.fade_alpha
                
                # Draw each component separately with alpha
                self.draw_slide_with_alpha(self.current_slide, slide_alpha, show_text=True)
            elif self.fade_alpha == 0:
                # Fully visible - draw normally
                self.screen.blit(self.current_slide_surface, (0, 0))
                    
        elif self.state == self.DISPLAY:
            # Normal display - just show the current slide
            if self.current_slide_surface:
                self.screen.blit(self.current_slide_surface, (0, 0))
                
        elif self.state == self.FADE_OUT:
            # Fading current slide to black
            print(f"Drawing fade out: fade_alpha = {self.fade_alpha}")  # Debug
            if self.fade_alpha < 255:
                # Calculate alpha for the entire slide: 255 when fade_alpha=0, 0 when fade_alpha=255
                slide_alpha = 255 - self.fade_alpha
                print(f"Drawing with slide_alpha = {slide_alpha}")  # Debug
                
                # Draw the slide with fading alpha
                self.draw_slide_with_alpha(self.current_slide, slide_alpha, show_text=True)
            else:
                print("Fade out complete - black screen")  # Debug
            # When fade_alpha=255, screen stays black