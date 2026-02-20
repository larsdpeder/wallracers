import pygame

PLAYER_KEYS = {
    0: {"lane": pygame.K_q, "boost": pygame.K_w, "honk": pygame.K_e},
    1: {"lane": pygame.K_i, "boost": pygame.K_o, "honk": pygame.K_p},
    2: {"lane": pygame.K_t, "boost": pygame.K_y, "honk": pygame.K_u},
    3: {"lane": pygame.K_LEFT, "boost": pygame.K_UP, "honk": pygame.K_RIGHT},
}

SCAN_KEY = pygame.K_SPACE
NUM_PLAYERS = 4
WIDTH, HEIGHT = 1920, 1080
FPS = 60
TOTAL_LAPS = 5
