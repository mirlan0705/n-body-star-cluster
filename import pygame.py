import pygame
import random
import math
from PIL import Image

pygame.init()

width = 800
height = 800

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("N Body Star Cluster")

clock = pygame.time.Clock()


zoom = 1.0
cam_x = 400
cam_y = 400
panning = False
pan_start = (0,0)
cam_start = (0,0)

stars = []

for i in range(500):
    x = random.uniform(100, 700)
    y = random.uniform(100, 700)
    vx = random.uniform(-0.05, 0.05)
    vy = random.uniform(-0.05, 0.05)
    mass = random.uniform(1, 3)
    stars.append([x,y,vx,vy,mass, []])

def star_color(mass):
    if mass < 2:
        return(150, 180, 255)
    elif mass < 3.5:
        return (255, 255, 200)
    else:
        return (255, 100, 60)

font = pygame.font.SysFont("monospace", 14)
recording = False
frames = []

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            else:
                zoom *= 0.9
        if event.type == pygame.MOUSEBUTTONDOWN:
            panning = True
            pan_start = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONUP:
            panning = False
        if event.type == pygame.MOUSEMOTION:
            if panning:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                cam_x -= (mouse_x - pan_start[0]) / zoom
                cam_y -= (mouse_y - pan_start[1]) / zoom
                pan_start = (mouse_x, mouse_y)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                recording = not recording
            if event.key == pygame.K_s:
                if frames:
                    frames[0].save("brute_force.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)
    screen.fill((0,0,0))
    
    for star in stars:
        for other in stars:    
            if star == other:
                continue

            dx = other[0] - star[0]
            dy = other[1] - star[1]
            distance = math.sqrt(dx**2 + dy**2)
            force = 0.5 * other[4] / (distance**2+50)
            ax = force * dx/distance
            ay = force * dy/distance

            star[2] += ax
            star[3] += ay

        star[0] += star[2]
        star[1] += star[3]

        star[5].append((star[0], star[1]))

        if len(star[5]) > 100:
            star[5].pop(0)
        
        for j in range(1, len(star[5])):
            opacity = int(255 * j / len(star[5]))
            trail_color = (
                int(star_color(star[4])[0] * opacity / 255),
                int(star_color(star[4])[1] * opacity / 255),
                int(star_color(star[4])[2] * opacity / 255)
            )
            tx1 = (star[5][j-1][0] - cam_x) * zoom + width / 2
            ty1 = (star[5][j-1][1] - cam_y) * zoom + height / 2
            tx2 = (star[5][j][0] - cam_x) * zoom + width / 2
            ty2 = (star[5][j][1] - cam_y) * zoom + height / 2
            pygame.draw.line(screen, trail_color, (int(tx1), int(ty1)), (int(tx2), int(ty2)), 1)

        screen_x = (star[0] - cam_x) * zoom + width / 2
        screen_y = (star[1] - cam_y) * zoom + height / 2
        pygame.draw.circle(screen, (star_color(star[4])), (int(screen_x), int(screen_y)), max(2, int(star[4])))

    screen.blit(font.render(f"FPS: {int(clock.get_fps())}  Stars: {len(stars)}  BRUTE FORCE O(n²)", True, (255, 255, 255)), (10, 10))
    if recording:
        screen.blit(font.render("● REC", True, (255, 0, 0)), (10, 30))
        frame = pygame.surfarray.array3d(screen)
        frame = frame.transpose([1, 0, 2])
        frames.append(Image.fromarray(frame))

    pygame.display.flip()

    clock.tick(60)
pygame.quit()