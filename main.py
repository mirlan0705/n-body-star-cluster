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

G = 0.5

class QuadNode:
    def __init__(self, cx, cy, size):
        self.cx = cx
        self.cy = cy
        self.size = size
        self.com_x = 0
        self.com_y = 0
        self.mass = 0
        self.divided = False
        self.children = [None, None, None, None]
        self.body = None
    
    def _quadrant(self, star):
        if star[0] < self.cx and star[1] < self.cy:
            return 0
        if star[0] >= self.cx and star[1] < self.cy:
            return 1
        if star[0] < self.cx and star[1] >= self.cy:
            return 2
        else:
            return 3
        
    def insert(self, star):
        if self.mass == 0:
            self.com_x = star[0]
            self.com_y = star[1]
            self.mass = star[4]
        else:
            total = self.mass + star[4]
            self.com_x = (self.com_x * self.mass + star[0] * star[4]) / total
            self.com_y = (self.com_y * self.mass + star[1] * star[4]) / total
            self.mass = total
        if not self.divided and self.body is None:
            self.body = star
            return
        if not self.divided and self.body is not None:
            half = self.size/2
            self.children[0] = QuadNode(self.cx - half, self.cy - half, half) #NW
            self.children[1] = QuadNode(self.cx + half, self.cy - half, half) #NE
            self.children[2] = QuadNode(self.cx - half, self.cy + half, half) #SW
            self.children[3] = QuadNode(self.cx + half, self.cy + half, half) #SE
            self.divided = True
            self.children[self._quadrant(self.body)].insert(self.body)
            self.body = None
            self.children[self._quadrant(star)].insert(star)
            return
        if self.divided:
            self.children[self._quadrant(star)].insert(star)
    def calculate_force(self, star, G, theta, softening):
        if self.mass == 0:
            return 0, 0
        if not self.divided and self.body is star:
            return 0, 0
        dx = self.com_x - star[0]
        dy = self.com_y - star[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if self.size / dist < theta:
            force = G * self.mass / (dist*dist + softening)
            ax = force * dx / dist
            ay = force * dy / dist
            return ax, ay
        ax = 0
        ay = 0
        for child in self.children:
            if child is not None:
                fx, fy = child.calculate_force(star, G, theta, softening)
                ax += fx
                ay += fy
        return ax, ay
    def draw(self, surface, cam_x, cam_y, zoom, width, height):
        x = int((self.cx - self.size - cam_x) * zoom + width / 2)
        y = int((self.cy - self.size - cam_y) * zoom + height / 2)
        s = int(self.size * 2 * zoom)
        pygame.draw.rect(surface, (0, 60, 30), (x, y, s, s), 1)
        if self.divided:
            for child in self.children:
                if child is not None:
                    child.draw(surface, cam_x, cam_y, zoom, width, height)
        
zoom = 1.0
cam_x = 400
cam_y = 400
panning = False
pan_start = (0,0)
cam_start = (0,0)
frames = []
stars = []
recording = False

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
show_tree = False

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
            if event.key == pygame.K_q:
                show_tree = not show_tree
            if event.key == pygame.K_r:
                recording = not recording
            if event.key == pygame.K_s:
                frames[0].save("simulation.gif", save_all=True, append_images=frames[1:], duration = 33, loop = 0)


    screen.fill((0,0,0))
    
    all_x = [s[0] for s in stars]
    all_y = [s[1] for s in stars]
    cx = (max(all_x) + min(all_x)) / 2
    cy = (max(all_y) + min(all_y)) / 2
    size = max(max(all_x) - min(all_x), max(all_y) - min(all_y)) / 2 + 100
    root = QuadNode(cx, cy, size)
    for s in stars:
        root.insert(s)
    if show_tree:
            root.draw(screen, cam_x, cam_y, zoom, width, height)

    
    for star in stars:
        ax, ay = root.calculate_force(star, G, 0.5, 50)
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

    screen.blit(font.render(f"FPS: {int(clock.get_fps())}  Stars: {len(stars)}", True, (255,255,255)), (10, 10))
    screen.blit(font.render("Q: toggle quadtree", True, (100, 100, 100)), (10, 30))
    if recording:
        frame = pygame.surfarray.array3d(screen)
        frame = frame.transpose([1, 0, 2])
        frames.append(Image.fromarray(frame))
    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()