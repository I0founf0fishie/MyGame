import pygame
import sys


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile Animation")

tiles_list = [
    pygame.image.load("cloud_3.png").convert_alpha(),
    pygame.image.load("cloud_3_1.png").convert_alpha(),
    pygame.image.load("cloud_3_2.png").convert_alpha(),
    pygame.image.load("cloud_3_3.png").convert_alpha()
]

current_frame = 0
frame_delay = 500 
last_switch_time = pygame.time.get_ticks()

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    current_time = pygame.time.get_ticks()
    if current_time - last_switch_time >= frame_delay:
        current_frame = (current_frame + 1) % len(tiles_list)
        last_switch_time = current_time

    tile_image = tiles_list[current_frame]

    screen.fill((255, 0, 255))
    screen.blit(tile_image, (0, 0))

    pygame.display.flip()
    clock.tick(60)