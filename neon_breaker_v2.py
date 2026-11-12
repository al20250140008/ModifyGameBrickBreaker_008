import math
import os
import random
import sys
import time
from array import array

import pygame

try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except Exception:
    pass
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON BREAKER: DESCENT")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("consolas", 22, bold=True)
BIG = pygame.font.SysFont("consolas", 64, bold=True)
SMALL = pygame.font.SysFont("consolas", 16, bold=True)

BG = (8, 8, 20)
CYAN, MAGENTA, YELLOW = (0, 240, 255), (255, 0, 200), (255, 220, 40)
ORANGE, GREEN, WHITE = (255, 110, 30), (80, 255, 130), (240, 240, 255)
HP_COLORS = {1: CYAN, 2: MAGENTA, 3: YELLOW}

PADDLE_Y = HEIGHT - 50
glow_cache = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


