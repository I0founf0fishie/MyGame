import pygame
import sys


tiles_list = [
    0,0,600,600],

SCREEN_WIDTH = 1200  
SCREEN_HEIGHT = 1200




pygame.init() 


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Tile from Tileset")

tileset1 = pygame.image.load("cloud_1.png").convert_alpha()

tileset2 = pygame.image.load("cloud_2.png").convert_alpha()

tileset3 = pygame.image.load("cloud_3.png").convert_alpha()

tileset4 = pygame.image.load("star_1.png").convert_alpha()




tile_rect = pygame.Rect(
    tiles_list[0][0], 
    tiles_list[0][1], 
    tiles_list[0][2],            
    tiles_list[0][3]            
)



tile_image1 = tileset1.subsurface(tile_rect)

tile_image2 = tileset2.subsurface(tile_rect)

tile_image3 = tileset3.subsurface(tile_rect)

tile_image4 = tileset4.subsurface(tile_rect)

clock = pygame.time.Clock()   

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()  
            sys.exit()    
    
    screen.fill((255, 0, 255))


    screen.blit(tile_image1, (0, 0))
    screen.blit(tile_image2, (550, 70))
    screen.blit(tile_image3, (0, 600))
    screen.blit(tile_image4, (600, 600))

    pygame.display.flip()

   
    clock.tick(60)