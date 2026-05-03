import pygame
import sys
import heapq
import random
import math
from collections import deque

# ─── Constants ───────────────────────────────────────────────────────────────
CELL      = 24
COLS, ROWS = 28, 31
W, H       = COLS * CELL, ROWS * CELL + 60   # extra 60px for HUD
FPS        = 60

# Colors
BLACK   = (0,   0,   0  )
BLUE    = (33,  33,  255)
YELLOW  = (255, 255, 0  )
WHITE   = (255, 255, 255)
RED     = (255, 0,   0  )
PINK    = (255, 184, 255)
CYAN    = (0,   255, 255)
ORANGE  = (255, 184, 82 )
SCARED  = (33,  33,  255)
SCARED2 = (255, 255, 255)
DARK_BG = (10,  10,  30 )
PELLET_C= (255, 220, 180)
DOT_C   = (220, 160, 120)

# ─── Classic Pac-Man maze (0=dot, 1=wall, 2=power, 3=empty/ghost-house) ─────
MAZE_TEMPLATE = [
    "1111111111111111111111111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1222222222222222222222222221",
    "1211112112111111112112111121",
    "1211112112111111112112111121",
    "1222222112222112222112222221",
    "1111112111110001111011111111",
    "1111112111110001111011111111",
    "1111112112333333333211111111",
    "1111112112300000332111111111",
    "0000002002300000332000000000",
    "1111112112333333332111111111",
    "1111112112000000002111111111",
    "1111112112000000002111111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1222112222222002222222112221",
    "1112112112111111112112112111",
    "1112112112111111112112112111",
    "1222222112222112222112222221",
    "1211111111112112111111111121",
    "1211111111112112111111111121",
    "1222222222222222222222222221",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1222222222222112222222222221",
    "1111111111111111111111111111",
]

def build_maze():
    grid = []
    for row_str in MAZE_TEMPLATE:
        row = []
        for ch in row_str:
            row.append(int(ch))
        grid.append(row)
    return grid

# ─── A* pathfinding ──────────────────────────────────────────────────────────
def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def astar(grid, start, goal):
    """Returns next step (col,row) towards goal, or None."""
    rows, cols = len(grid), len(grid[0])
    open_heap = []
    heapq.heappush(open_heap, (0, start))
    came_from = {start: None}
    g_cost = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            # reconstruct first step
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path[1] if len(path) > 1 else None

        cx, cy = current
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = cx+dx, cy+dy
            if 0 <= nx < cols and 0 <= ny < rows and grid[ny][nx] != 1:
                new_g = g_cost[current] + 1
                nb = (nx, ny)
                if nb not in g_cost or new_g < g_cost[nb]:
                    g_cost[nb] = new_g
                    f = new_g + heuristic(nb, goal)
                    heapq.heappush(open_heap, (f, nb))
                    came_from[nb] = current
    return None

# ─── Ghost ───────────────────────────────────────────────────────────────────
GHOST_COLORS = [RED, PINK, CYAN, ORANGE]
GHOST_NAMES  = ["Blinky","Pinky","Inky","Clyde"]

class Ghost:
    SCATTER_TARGETS = [(25,1),(2,1),(25,29),(2,29)]

    def __init__(self, idx, start_cell):
        self.idx        = idx
        self.color      = GHOST_COLORS[idx]
        self.name       = GHOST_NAMES[idx]
        self.cell       = list(start_cell)       # [col, row]
        self.pixel      = [start_cell[0]*CELL, start_cell[1]*CELL]
        self.target     = start_cell
        self.speed      = 1.5
        self.scared     = False
        self.scare_timer= 0
        self.dead       = False
        self.moving     = False
        self.direction  = (0, 0)
        self.move_queue = deque()
        self.step_timer = 0
        self.step_delay = 12          # frames between cell steps (lower = faster)
        self.scatter_mode = True
        self.mode_timer   = 0

    def get_target(self, pac_cell, pac_dir, grid):
        if self.dead:
            return (13, 13)        # ghost house
        if self.scared:
            # run away: pick random walkable neighbour far from pac
            cx, cy = self.cell
            candidates = []
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx+dx, cy+dy
                if 0<=nx<COLS and 0<=ny<ROWS and grid[ny][nx]!=1:
                    candidates.append((nx,ny))
            if candidates:
                best = max(candidates, key=lambda c: heuristic(c, pac_cell))
                return best
            return tuple(self.cell)

        # Scatter: each ghost targets a corner
        if self.scatter_mode:
            return Ghost.SCATTER_TARGETS[self.idx]

        # Chase behaviours
        px, py = pac_cell
        if self.idx == 0:   # Blinky - direct chase
            return (px, py)
        elif self.idx == 1: # Pinky - 4 ahead of pac
            dx, dy = pac_dir
            return (px + 4*dx, py + 4*dy)
        elif self.idx == 2: # Inky - complex
            return (px, py)
        else:               # Clyde - chase if far, scatter if close
            if heuristic(tuple(self.cell), pac_cell) > 8:
                return (px, py)
            else:
                return Ghost.SCATTER_TARGETS[self.idx]

    def update(self, pac_cell, pac_dir, grid, dt):
        # Mode switching
        self.mode_timer += 1
        if self.mode_timer < 420:
            self.scatter_mode = True
        elif self.mode_timer < 1220:
            self.scatter_mode = False
        elif self.mode_timer < 1420:
            self.scatter_mode = True
        else:
            self.scatter_mode = False

        if self.scared:
            self.scare_timer -= 1
            if self.scare_timer <= 0:
                self.scared = False

        self.step_timer += 1
        delay = 6 if self.dead else (20 if self.scared else self.step_delay)
        if self.step_timer >= delay:
            self.step_timer = 0
            target = self.get_target(pac_cell, pac_dir, grid)
            # clamp target
            tx = max(0, min(COLS-1, target[0]))
            ty = max(0, min(ROWS-1, target[1]))
            # avoid walls in target
            if grid[ty][tx] == 1:
                tx, ty = pac_cell
            next_cell = astar(grid, tuple(self.cell), (tx, ty))
            if next_cell:
                self.cell = list(next_cell)
                self.pixel = [self.cell[0]*CELL, self.cell[1]*CELL]
            # If arrived at ghost house when dead, revive
            if self.dead and self.cell == [13, 13]:
                self.dead = False

    def frighten(self, duration=300):
        if not self.dead:
            self.scared      = True
            self.scare_timer = duration

    def draw(self, surf, frame):
        px, py = self.pixel[0], self.pixel[1]
        cx, cy = px + CELL//2, py + CELL//2
        r = CELL//2 - 2

        if self.dead:
            # Just eyes
            pygame.draw.circle(surf, WHITE, (cx-4, cy-2), 4)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-2), 4)
            pygame.draw.circle(surf, BLUE,  (cx-4, cy-2), 2)
            pygame.draw.circle(surf, BLUE,  (cx+4, cy-2), 2)
            return

        if self.scared:
            blink = self.scare_timer < 80 and (frame//6)%2==0
            color = SCARED2 if blink else SCARED
        else:
            color = self.color

        # Body
        body_rect = pygame.Rect(px+2, py+r, CELL-4, r)
        pygame.draw.rect(surf, color, body_rect)
        pygame.draw.circle(surf, color, (cx, py+r), r)
        # Skirt wiggles
        skirt_y = py + CELL - 2
        wave = math.sin(frame*0.2)*2
        for i in range(3):
            x0 = px + 2 + i*(CELL-4)//3
            x1 = x0 + (CELL-4)//3
            xm = (x0+x1)//2
            pts = [(x0, skirt_y), (xm, skirt_y - 4 + wave), (x1, skirt_y)]
            pygame.draw.polygon(surf, DARK_BG, pts)

        # Eyes
        if not self.scared:
            pygame.draw.circle(surf, WHITE, (cx-4, cy-3), 4)
            pygame.draw.circle(surf, WHITE, (cx+4, cy-3), 4)
            pygame.draw.circle(surf, BLUE,  (cx-4, cy-3), 2)
            pygame.draw.circle(surf, BLUE,  (cx+4, cy-3), 2)
        else:
            # x eyes
            for ex, ey in [(cx-4, cy-3),(cx+4, cy-3)]:
                pygame.draw.line(surf, WHITE, (ex-2,ey-2),(ex+2,ey+2), 2)
                pygame.draw.line(surf, WHITE, (ex+2,ey-2),(ex-2,ey+2), 2)

# ─── Pacman ──────────────────────────────────────────────────────────────────
class Pacman:
    def __init__(self, cell):
        self.cell      = list(cell)
        self.pixel     = [cell[0]*CELL, cell[1]*CELL]
        self.direction = (1, 0)
        self.next_dir  = (1, 0)
        self.step_timer= 0
        self.step_delay= 8
        self.mouth     = 0
        self.mouth_dir = 1
        self.alive     = True
        self.anim_t    = 0

    def update(self, grid, keys):
        if not self.alive:
            return

        # Queue direction
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.next_dir=(-1,0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.next_dir=(1,0)
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.next_dir=(0,-1)
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.next_dir=(0,1)

        self.step_timer += 1
        if self.step_timer >= self.step_delay:
            self.step_timer = 0
            cx, cy = self.cell
            # Try queued direction first
            nx, ny = cx+self.next_dir[0], cy+self.next_dir[1]
            # wrap tunnel
            nx = nx % COLS
            if grid[ny][nx] != 1:
                self.direction = self.next_dir
            dx, dy = self.direction
            mx, my = cx+dx, cy+dy
            mx = mx % COLS
            if grid[my][mx] != 1:
                self.cell = [mx, my]
                self.pixel = [mx*CELL, my*CELL]

        # Mouth animation
        self.mouth += 4 * self.mouth_dir
        if self.mouth >= 40: self.mouth_dir = -1
        if self.mouth <= 0:  self.mouth_dir = 1

    def draw(self, surf, frame):
        if not self.alive:
            return
        px, py = self.pixel
        cx, cy = px+CELL//2, py+CELL//2
        r = CELL//2 - 2
        angle = math.degrees(math.atan2(-self.direction[1], self.direction[0]))
        start_a = angle + self.mouth
        end_a   = angle - self.mouth
        # Glow effect
        glow_surf = pygame.Surface((CELL*2, CELL*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255,255,0,40), (CELL,CELL), r+6)
        surf.blit(glow_surf, (cx-CELL, cy-CELL))
        # Body
        pygame.draw.circle(surf, YELLOW, (cx,cy), r)
        # Mouth cut
        mouth_pts = [(cx,cy)]
        for a in range(int(start_a), int(end_a)-1, -1):
            rad = math.radians(a)
            mouth_pts.append((cx+int(r*math.cos(rad)), cy-int(r*math.sin(rad))))
        if len(mouth_pts) > 2:
            pygame.draw.polygon(surf, DARK_BG, mouth_pts)
        # Eye
        ex = cx + int((r*0.4)*math.cos(math.radians(angle+70)))
        ey = cy - int((r*0.4)*math.sin(math.radians(angle+70)))
        pygame.draw.circle(surf, DARK_BG, (ex,ey), 2)

# ─── Game ────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("PAC-MAN  ·  A* Ghost AI")
        self.clock  = pygame.font.SysFont(None, 20)
        self.font_big  = pygame.font.SysFont("couriernew", 28, bold=True)
        self.font_med  = pygame.font.SysFont("couriernew", 18)
        self.font_sm   = pygame.font.SysFont("couriernew", 14)
        self.clock_obj = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.grid   = build_maze()
        self.dots   = {}    # (col,row) -> 'dot' or 'power'
        # populate dots
        for r in range(ROWS):
            for c in range(COLS):
                v = self.grid[r][c]
                if v == 0:
                    self.dots[(c,r)] = 'dot'
                elif v == 2:
                    self.dots[(c,r)] = 'power'
                # make walkable
                if v in (0,2):
                    self.grid[r][c] = 0

        # treat ghost house as walkable for ghosts
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == 3:
                    self.grid[r][c] = 0

        self.pac    = Pacman((14, 23))
        # Ghost start positions (inside house area)
        starts = [(13,13),(14,13),(13,14),(14,14)]
        self.ghosts = [Ghost(i, starts[i]) for i in range(4)]
        self.score  = 0
        self.lives  = 3
        self.level  = 1
        self.frame  = 0
        self.state  = 'play'   # 'play','dead','win','gameover'
        self.dead_timer = 0
        self.total_dots = len(self.dots)

    def eat_dots(self):
        cell = tuple(self.pac.cell)
        if cell in self.dots:
            kind = self.dots.pop(cell)
            if kind == 'dot':
                self.score += 10
            else:
                self.score += 50
                for g in self.ghosts:
                    g.frighten(300 + self.level*20)

    def check_collisions(self):
        pcell = tuple(self.pac.cell)
        for g in self.ghosts:
            if tuple(g.cell) == pcell:
                if g.scared:
                    g.dead = True
                    g.scared = False
                    self.score += 200
                elif not g.dead:
                    self.pac.alive = False
                    self.state = 'dead'
                    self.dead_timer = 120

    def draw_maze(self):
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c*CELL, r*CELL
                v = MAZE_TEMPLATE[r][c]
                if v == '1':
                    # Wall with subtle glow
                    rect = pygame.Rect(x+1, y+1, CELL-2, CELL-2)
                    pygame.draw.rect(self.screen, (20,20,80), rect, border_radius=3)
                    pygame.draw.rect(self.screen, BLUE,       rect, 1, border_radius=3)

        # Dots & power pellets
        for (c,r), kind in self.dots.items():
            x, y = c*CELL + CELL//2, r*CELL + CELL//2
            if kind == 'power':
                pulse = int(4 + 3*math.sin(self.frame*0.1))
                pygame.draw.circle(self.screen, PELLET_C, (x,y), pulse)
            else:
                pygame.draw.circle(self.screen, DOT_C, (x,y), 2)

    def draw_hud(self):
        hud_y = ROWS * CELL + 4
        # Background bar
        pygame.draw.rect(self.screen, (20,10,40), (0, ROWS*CELL, W, 60))
        pygame.draw.line(self.screen, BLUE, (0, ROWS*CELL), (W, ROWS*CELL), 1)

        score_surf = self.font_big.render(f"SCORE  {self.score:06d}", True, YELLOW)
        self.screen.blit(score_surf, (10, hud_y+4))

        lvl_surf = self.font_med.render(f"LEVEL {self.level}", True, CYAN)
        self.screen.blit(lvl_surf, (W//2 - lvl_surf.get_width()//2, hud_y+4))

        # Lives (pac icons)
        for i in range(self.lives):
            lx = W - 30 - i*26
            pygame.draw.circle(self.screen, YELLOW, (lx, hud_y+18), 8)
            pygame.draw.polygon(self.screen, DARK_BG, [(lx,hud_y+18),(lx+10,hud_y+12),(lx+10,hud_y+24)])

        # Ghost mode labels
        for i, g in enumerate(self.ghosts):
            mode = "SCARED" if g.scared else ("DEAD" if g.dead else ("SCAT" if g.scatter_mode else "CHASE"))
            c_lbl = SCARED if g.scared else (WHITE if g.dead else (CYAN if g.scatter_mode else g.color))
            lbl = self.font_sm.render(f"{g.name[:4]}:{mode}", True, c_lbl)
            self.screen.blit(lbl, (10 + i*100, hud_y + 32))

    def draw_overlay(self, text, sub=""):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))
        big = self.font_big.render(text, True, YELLOW)
        self.screen.blit(big, (W//2 - big.get_width()//2, H//2 - 30))
        if sub:
            sm = self.font_med.render(sub, True, WHITE)
            self.screen.blit(sm, (W//2 - sm.get_width()//2, H//2 + 10))

    def run(self):
        while True:
            self.frame += 1
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

            # ── Update ──
            if self.state == 'play':
                self.pac.update(self.grid, keys)
                pac_cell  = tuple(self.pac.cell)
                pac_dir   = self.pac.direction
                for g in self.ghosts:
                    g.update(pac_cell, pac_dir, self.grid, 1)
                self.eat_dots()
                self.check_collisions()
                if not self.dots:
                    self.state = 'win'

            elif self.state == 'dead':
                self.dead_timer -= 1
                if self.dead_timer <= 0:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = 'gameover'
                    else:
                        # respawn
                        self.pac    = Pacman((14, 23))
                        starts      = [(13,13),(14,13),(13,14),(14,14)]
                        self.ghosts = [Ghost(i, starts[i]) for i in range(4)]
                        self.state  = 'play'

            elif self.state == 'win':
                pass   # wait for R

            elif self.state == 'gameover':
                pass

            # ── Draw ──
            self.screen.fill(DARK_BG)
            self.draw_maze()
            self.pac.draw(self.screen, self.frame)
            for g in self.ghosts:
                g.draw(self.screen, self.frame)
            self.draw_hud()

            if self.state == 'win':
                self.draw_overlay("YOU WIN!", "Press R to play again")
            elif self.state == 'gameover':
                self.draw_overlay("GAME OVER", "Press R to restart")

            pygame.display.flip()
            self.clock_obj.tick(FPS)

if __name__ == "__main__":
    Game().run()
