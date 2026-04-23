import pygame
import random
import math

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

# ── Barnes-Hut quadtree ────────────────────────────────────────────────────

class QuadNode:
    __slots__ = ['cx','cy','half','com_x','com_y','mass','body','children']
    def __init__(self, cx, cy, half):
        self.cx = cx; self.cy = cy; self.half = half
        self.com_x = 0.0; self.com_y = 0.0; self.mass = 0.0
        self.body = None
        self.children = [None, None, None, None]

    def is_leaf(self):
        return not any(self.children)

    def _quad(self, x, y):
        return (2 if y >= self.cy else 0) | (1 if x >= self.cx else 0)

    def _child(self, q):
        h = self.half * 0.5
        ox = h if (q & 1) else -h
        oy = h if (q & 2) else -h
        return QuadNode(self.cx + ox, self.cy + oy, h)

    def insert(self, stars, idx):
        x, y, m = stars[idx][0], stars[idx][1], stars[idx][4]
        nm = self.mass + m
        self.com_x = (self.com_x * self.mass + x * m) / nm
        self.com_y = (self.com_y * self.mass + y * m) / nm
        self.mass = nm
        if self.is_leaf() and self.body is None:
            self.body = idx; return
        if self.half < 0.5:
            return
        if not self.is_leaf():
            q = self._quad(x, y)
            if not self.children[q]: self.children[q] = self._child(q)
            self.children[q].insert(stars, idx); return
        old = self.body; self.body = None
        qo = self._quad(stars[old][0], stars[old][1])
        if not self.children[qo]: self.children[qo] = self._child(qo)
        self.children[qo].insert(stars, old)
        qn = self._quad(x, y)
        if not self.children[qn]: self.children[qn] = self._child(qn)
        self.children[qn].insert(stars, idx)


def _accel(node, stars, idx):
    if node is None or node.mass == 0: return 0.0, 0.0
    x, y = stars[idx][0], stars[idx][1]
    if node.is_leaf():
        if node.body == idx: return 0.0, 0.0
        dx, dy = node.com_x - x, node.com_y - y
        d2 = dx*dx + dy*dy
        if d2 < 1: return 0.0, 0.0
        d = math.sqrt(d2)
        f = 0.5 * node.mass / (d2 + 50)
        return f*dx/d, f*dy/d
    dx, dy = node.com_x - x, node.com_y - y
    d2 = dx*dx + dy*dy
    if d2 < 0.001:
        ax = ay = 0.0
        for c in node.children:
            fx, fy = _accel(c, stars, idx); ax += fx; ay += fy
        return ax, ay
    d = math.sqrt(d2)
    if (node.half * 2) / d < 0.5:
        f = 0.5 * node.mass / (d2 + 50)
        return f*dx/d, f*dy/d
    ax = ay = 0.0
    for c in node.children:
        fx, fy = _accel(c, stars, idx); ax += fx; ay += fy
    return ax, ay


def compute_forces(stars):
    root = QuadNode(400, 400, 3000)
    for i in range(len(stars)):
        root.insert(stars, i)
    return [_accel(root, stars, i) for i in range(len(stars))]


def potential_energy(stars):
    pe = 0.0
    for i in range(len(stars)):
        for j in range(i+1, len(stars)):
            dx, dy = stars[j][0]-stars[i][0], stars[j][1]-stars[i][1]
            pe -= 0.5 * stars[i][4] * stars[j][4] / math.sqrt(dx*dx + dy*dy + 50)
    return pe


def do_merges(stars):
    merged = [False] * len(stars)
    result = []
    for i in range(len(stars)):
        if merged[i]:
            continue
        for j in range(i+1, len(stars)):
            if merged[j]:
                continue
            dx = stars[j][0] - stars[i][0]
            dy = stars[j][1] - stars[i][1]
            if dx*dx + dy*dy < 25:   # merge radius = 5px
                mi, mj = stars[i][4], stars[j][4]
                mt = mi + mj
                stars[i][0] = (stars[i][0]*mi + stars[j][0]*mj) / mt
                stars[i][1] = (stars[i][1]*mi + stars[j][1]*mj) / mt
                stars[i][2] = (stars[i][2]*mi + stars[j][2]*mj) / mt
                stars[i][3] = (stars[i][3]*mi + stars[j][3]*mj) / mt
                stars[i][4] = mt
                stars[i][5] = []   # clear trail on merge
                merged[j] = True
        result.append(stars[i])
    return result

# ──────────────────────────────────────────────────────────────────────────

NUM_STARS = 300
DISK_RADIUS = 200
total_mass_est = NUM_STARS * 2.0

stars = []

for i in range(NUM_STARS):
    r = math.sqrt(random.uniform(0, 1)) * DISK_RADIUS
    angle = random.uniform(0, 2 * math.pi)
    x = 400 + r * math.cos(angle)
    y = 400 + r * math.sin(angle)
    vx = random.uniform(-0.05, 0.05)
    vy = random.uniform(-0.05, 0.05)
    mass = random.uniform(1, 3)
    # Add circular orbital velocity so the cluster spins
    v_circ = math.sqrt(0.5 * total_mass_est * r / (DISK_RADIUS**2 + 1))
    vx += -v_circ * math.sin(angle)
    vy +=  v_circ * math.cos(angle)
    stars.append([x,y,vx,vy,mass, []])

def star_color(mass):
    if mass < 2:
        return (150, 180, 255)   # blue-white
    elif mass < 3.5:
        return (255, 255, 200)   # yellow-white
    elif mass < 10:
        return (255, 180, 80)    # orange: merged star
    else:
        return (255, 80, 40)     # red giant: very massive

# Leapfrog initialisation: compute starting accelerations
accels = compute_forces(stars)

font = pygame.font.SysFont("monospace", 13)
pe_cache = 0.0
energy_0 = None
frame = 0

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
    screen.fill((0,0,0))

    # Leapfrog KDK: half kick → drift → new forces → half kick
    for i, star in enumerate(stars):
        star[2] += accels[i][0] * 0.5
        star[3] += accels[i][1] * 0.5

    for star in stars:
        star[0] += star[2]
        star[1] += star[3]

    accels = compute_forces(stars)

    for i, star in enumerate(stars):
        star[2] += accels[i][0] * 0.5
        star[3] += accels[i][1] * 0.5

    # Mergers (every 5 frames)
    if frame % 5 == 0:
        stars = do_merges(stars)
        accels = accels[:len(stars)]

    # Energy (PE is O(n²) so only every 30 frames)
    if frame % 30 == 0:
        pe_cache = potential_energy(stars)
    ke = sum(0.5 * s[4] * (s[2]*s[2] + s[3]*s[3]) for s in stars)
    total_energy = ke + pe_cache
    if energy_0 is None and frame == 30:
        energy_0 = total_energy

    for star in stars:
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
            pygame.draw.line(screen, trail_color, (tx1, ty1), (tx2, ty2), 1)

        screen_x = (star[0] - cam_x) * zoom + width / 2
        screen_y = (star[1] - cam_y) * zoom + height / 2
        radius = max(2, int(math.log1p(star[4]) * 1.5))
        pygame.draw.circle(screen, (star_color(star[4])), (int(screen_x), int(screen_y)), radius)

    # HUD
    hud = [
        f"FPS:   {clock.get_fps():.0f}",
        f"Stars: {len(stars)}",
        f"KE:    {ke:,.0f}",
        f"PE:    {pe_cache:,.0f}",
        f"E:     {total_energy:,.0f}",
    ]
    if energy_0:
        hud.append(f"dE:    {abs((total_energy - energy_0) / energy_0) * 100:.3f}%")
    hud += ["", "Barnes-Hut  O(n log n)", "Leapfrog integrator"]
    for i, line in enumerate(hud):
        screen.blit(font.render(line, True, (160, 160, 160)), (10, 10 + i * 17))

    pygame.display.flip()

    clock.tick(60)
    frame += 1

pygame.quit()