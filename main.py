# main.py - Entry point
#!/usr/bin/env python3
"""
Long Neck Zombie Game - Refactored Version
A physics-based game with simplified, readable code structure.
"""

from game import Game

if __name__ == "__main__":
    game = Game()
    game.run()