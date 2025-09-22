import pygame
from elevator_game import ElevatorGame

def main():
    pygame.init()
    game = ElevatorGame()
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()