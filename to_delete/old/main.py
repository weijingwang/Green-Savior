import pygame
from elevator_game import ElevatorGame

def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    try:
        game = ElevatorGame()
        game.run()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()