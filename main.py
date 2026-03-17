import pygame
import random
import math

pygame.init()

width = 800 
height = 800

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("N Body Star Cluster")

clock = pygame.time.Clock()

stars = []

for i in range(50):
    x = random.uniform(100, 700)
    y = random.uniform(100, 700)
    vx = random.uniform(-0.1, 0.1)
    vy = random.uniform(-0.1, 0.1)
    mass = random.uniform(1, 3)
    stars.append([x,y,vx,vy,mass])

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0,0,0))
    for star in stars:
        for other in stars:
            
            dx = other[0] - star[0]
            dy = other[1] - star[1]

            distance = math.sqrt((dx**2) + (dy**2))
            distance = max(distance, 5)

            nx = dx/distance
            ny = dy/distance

            ax = 0.5 * other[4]/distance**2 * nx
            ay = 0.5 * other[4]/distance**2 * ny

            star[2] += ax
            star[3] += ay

        star[0] += star[2]
        star[1] += star[3]
        pygame.draw.circle(screen, (255,255,255), (int(star[0]), int(star[1])), 2)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
