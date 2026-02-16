import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1000, 1000
CELL_SIZE = 4
FRAME_MARGIN = 200  # Frame is 200px smaller than window
FRAME_PADDING = 20  # Wooden border thickness
GRID_WIDTH = (WIDTH - FRAME_MARGIN - FRAME_PADDING * 2) // CELL_SIZE
GRID_HEIGHT = (HEIGHT - FRAME_MARGIN - FRAME_PADDING * 2) // CELL_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Falling Sand - Arrow Keys to Rotate Frame")
clock = pygame.time.Clock()

# Particle types
EMPTY = 0
SAND = 1
WATER = 2
STONE = 3
GOLD = 4
ANTIGRAV = 5
BEES = 6
STYROFOAM = 7

BACKGROUND_COLOR = (20, 20, 30)

# Colors for each particle type
COLORS = {
    SAND: (194, 178, 128),
    WATER: (50, 100, 200),
    STONE: (80, 80, 80),
    GOLD: (255, 200, 50),
    ANTIGRAV: (240, 240, 255),
    BEES: (255, 165, 0),
    STYROFOAM: (200, 200, 210),
}


class FallingSand:
    def __init__(self):
        self.grid = [[EMPTY] * GRID_HEIGHT for _ in range(GRID_WIDTH)]
        self.frame_angle = 0.0
        self.target_angle = 0.0
        self.current_type = SAND
        self.brush_size = 3
        self.grid_surface = pygame.Surface((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
        self.frame_count = 0  # Used to alternate scan direction

    def in_bounds(self, x, y):
        return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

    def is_empty(self, x, y):
        return self.in_bounds(x, y) and self.grid[x][y] == EMPTY

    def get_gravity(self):
        return math.sin(self.frame_angle) * 0.5, math.cos(self.frame_angle) * 0.5

    def is_floating_styrofoam(self, x, y, mx, my):
        """Check if styrofoam at (x,y) is floating on water (directly or via other styrofoam)."""
        # Look in the gravity direction (downward) for water support
        cx, cy = x + mx, y + my
        for _ in range(20):
            if not self.in_bounds(cx, cy):
                return False
            cell = self.grid[cx][cy]
            if cell == WATER:
                return True
            if cell == STYROFOAM:
                cx += mx
                cy += my
                continue
            return False
        return False

    def screen_to_grid(self, sx, sy):
        cx, cy = WIDTH // 2, HEIGHT // 2
        dx, dy = sx - cx, sy - cy
        cos_a, sin_a = math.cos(-self.frame_angle), math.sin(-self.frame_angle)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        return int((rx + GRID_WIDTH * CELL_SIZE // 2) // CELL_SIZE), \
               int((ry + GRID_HEIGHT * CELL_SIZE // 2) // CELL_SIZE)

    def spawn(self, sx, sy, ptype):
        gx, gy = self.screen_to_grid(sx, sy)
        for dx in range(-self.brush_size, self.brush_size + 1):
            for dy in range(-self.brush_size, self.brush_size + 1):
                if dx*dx + dy*dy <= self.brush_size * self.brush_size:
                    x, y = gx + dx, gy + dy
                    if self.is_empty(x, y) and random.random() < 0.7:
                        self.grid[x][y] = ptype

    def erase(self, sx, sy):
        gx, gy = self.screen_to_grid(sx, sy)
        for dx in range(-self.brush_size, self.brush_size + 1):
            for dy in range(-self.brush_size, self.brush_size + 1):
                if dx*dx + dy*dy <= self.brush_size * self.brush_size:
                    x, y = gx + dx, gy + dy
                    if self.in_bounds(x, y):
                        self.grid[x][y] = EMPTY

    def update(self):
        self.frame_angle += (self.target_angle - self.frame_angle) * 0.08
        self.frame_count += 1

        # Update bees - random movement biased toward center
        cx, cy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[x][y] != BEES:
                    continue
                # Random direction with slight center bias
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                # Bias toward center
                #if random.random() < 0.05:
                #    dx = 1 if x < cx else -1
                #if random.random() < 0.05:
                #    dy = 1 if y < cy else -1
                nx, ny = x + dx, y + dy
                if self.is_empty(nx, ny):
                    self.grid[nx][ny] = BEES
                    self.grid[x][y] = EMPTY

        gx, gy = self.get_gravity()

        # Determine move direction once for all particles
        mx = 1 if gx > 0.05 else (-1 if gx < -0.05 else 0)
        my = 1 if gy > 0.05 else (-1 if gy < -0.05 else 0)

        if mx == 0 and my == 0:
            return  # No gravity, nothing moves

        # Process in correct order based on gravity direction
        # When gravity points +y (down), process from high y to low y
        # This way, lower particles move first, making room for upper particles
        if my > 0:
            y_range = range(GRID_HEIGHT - 1, -1, -1)
        elif my < 0:
            y_range = range(GRID_HEIGHT)
        else:
            # No vertical gravity - alternate direction each frame
            if self.frame_count % 2 == 0:
                y_range = range(GRID_HEIGHT)
            else:
                y_range = range(GRID_HEIGHT - 1, -1, -1)

        if mx > 0:
            x_range = range(GRID_WIDTH - 1, -1, -1)
        elif mx < 0:
            x_range = range(GRID_WIDTH)
        else:
            # No horizontal gravity - alternate direction each frame
            if self.frame_count % 2 == 0:
                x_range = range(GRID_WIDTH)
            else:
                x_range = range(GRID_WIDTH - 1, -1, -1)

        for y in y_range:
            for x in x_range:
                p = self.grid[x][y]
                if p == EMPTY or p == STONE or p == BEES:
                    continue

                # Styrofoam moves at half speed - skip every other frame
                if p == STYROFOAM and self.frame_count % 2 == 0:
                    continue

                # Determine movement parameters based on particle type
                if p == ANTIGRAV:
                    # Antigrav moves opposite to gravity, very fast
                    pmx, pmy = -mx, -my
                    steps = 2
                else:
                    pmx, pmy = mx, my
                    steps = 2 if p == GOLD else 1

                for _ in range(steps):
                    moved = False

                    # Build list of movement attempts in priority order
                    attempts = []

                    # Primary: move in particle's gravity direction
                    if pmx != 0 and pmy != 0:
                        attempts.append((x + pmx, y + pmy))  # Diagonal
                        # When diagonal blocked, try each axis separately
                        if abs(gy) >= abs(gx):
                            attempts.append((x, y + pmy))  # Vertical first
                            attempts.append((x + pmx, y))  # Then horizontal
                        else:
                            attempts.append((x + pmx, y))  # Horizontal first
                            attempts.append((x, y + pmy))  # Then vertical
                    elif pmy != 0:
                        attempts.append((x, y + pmy))
                    elif pmx != 0:
                        attempts.append((x + pmx, y))

                    # Also try sliding sideways (perpendicular to movement)
                    d = random.choice([-1, 1])
                    if pmy != 0:
                        attempts.append((x + d, y + pmy))
                        attempts.append((x - d, y + pmy))
                    if pmx != 0:
                        attempts.append((x + pmx, y + d))
                        attempts.append((x + pmx, y - d))

                    # Try each movement option
                    for nx, ny in attempts:
                        if not self.in_bounds(nx, ny):
                            continue
                        target = self.grid[nx][ny]
                        if target == EMPTY:
                            self.grid[nx][ny] = p
                            self.grid[x][y] = EMPTY
                            x, y = nx, ny
                            moved = True
                            break
                        elif p == ANTIGRAV:
                            # Antigrav only moves through empty space
                            continue
                        elif target == WATER and p in (SAND, GOLD):
                            chance = 0.3 if p == SAND else 0.5
                            if random.random() < chance:
                                self.grid[nx][ny] = p
                                self.grid[x][y] = WATER
                                x, y = nx, ny
                                moved = True
                                break
                        elif target == STYROFOAM and p == WATER:
                            # Water is denser than styrofoam - swap them
                            if random.random() < 0.3:
                                self.grid[nx][ny] = WATER
                                self.grid[x][y] = STYROFOAM
                                x, y = nx, ny
                                moved = True
                                break
                        elif target == STYROFOAM and p in (SAND, GOLD) and self.is_floating_styrofoam(nx, ny, pmx, pmy):
                            # Sand/gold sink through floating styrofoam
                            chance = 0.3 if p == SAND else 0.5
                            if random.random() < chance:
                                self.grid[nx][ny] = p
                                self.grid[x][y] = STYROFOAM
                                x, y = nx, ny
                                moved = True
                                break
                        elif target == ANTIGRAV:
                            # Sand, gold, water cannot move through antigrav
                            continue

                    # Water spreads perpendicular to gravity
                    if not moved and p == WATER:
                        spread = random.choice([-1, 1])
                        for dist in range(1, 4):
                            # Spread perpendicular to gravity direction
                            if abs(gy) > abs(gx) * 2:
                                # Mostly vertical gravity - spread horizontally
                                wx, wy = x + spread * dist, y
                            elif abs(gx) > abs(gy) * 2:
                                # Mostly horizontal gravity - spread vertically
                                wx, wy = x, y + spread * dist
                            else:
                                # Diagonal gravity - spread in both perpendicular directions
                                if random.random() < 0.5:
                                    wx, wy = x + spread * dist, y - spread * dist
                                else:
                                    wx, wy = x - spread * dist, y + spread * dist
                            if self.is_empty(wx, wy):
                                self.grid[wx][wy] = WATER
                                self.grid[x][y] = EMPTY
                                moved = True
                                break

                    # Styrofoam spreads when floating on water
                    if not moved and p == STYROFOAM and self.is_floating_styrofoam(x, y, pmx, pmy):
                        spread = random.choice([-1, 1])
                        for dist in range(1, 3):
                            if abs(gy) > abs(gx) * 2:
                                wx, wy = x + spread * dist, y
                            elif abs(gx) > abs(gy) * 2:
                                wx, wy = x, y + spread * dist
                            else:
                                if random.random() < 0.5:
                                    wx, wy = x + spread * dist, y - spread * dist
                                else:
                                    wx, wy = x - spread * dist, y + spread * dist
                            if self.is_empty(wx, wy):
                                self.grid[wx][wy] = STYROFOAM
                                self.grid[x][y] = EMPTY
                                moved = True
                                break
                            elif self.in_bounds(wx, wy) and self.grid[wx][wy] != EMPTY:
                                break

                    if not moved:
                        break

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        self.grid_surface.fill(BACKGROUND_COLOR)

        # Draw particles
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                p = self.grid[x][y]
                if p != EMPTY:
                    pygame.draw.rect(self.grid_surface, COLORS[p],
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # Create and rotate frame
        fw = GRID_WIDTH * CELL_SIZE + FRAME_PADDING * 2
        fh = GRID_HEIGHT * CELL_SIZE + FRAME_PADDING * 2
        frame = pygame.Surface((fw, fh), pygame.SRCALPHA)
        pygame.draw.rect(frame, (139, 90, 43), (0, 0, fw, fh))
        pygame.draw.rect(frame, (90, 60, 30), (0, 0, fw, fh), 4)
        pygame.draw.rect(frame, BACKGROUND_COLOR, (FRAME_PADDING, FRAME_PADDING, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
        frame.blit(self.grid_surface, (FRAME_PADDING, FRAME_PADDING))

        rotated = pygame.transform.rotate(frame, -math.degrees(self.frame_angle))
        rect = rotated.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        surface.blit(rotated, rect)

        # UI
        font = pygame.font.Font(None, 24)
        names = {SAND: "Sand", WATER: "Water", STONE: "Stone", GOLD: "Gold", ANTIGRAV: "Antigrav", BEES: "Bees", STYROFOAM: "Styrofoam"}
        surface.blit(font.render(f"[1-7] Type: {names[self.current_type]}  |  Brush: {self.brush_size}", True, (200, 200, 200)), (10, 10))
        surface.blit(font.render(f"FPS: {clock.get_fps():.0f}", True, (200, 200, 200)), (10, 35))
        surface.blit(font.render("Arrows: Rotate | LMB/RMB: Draw/Erase | C: Clear", True, (150, 150, 150)), (10, 60))


def main():
    sim = FallingSand()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    sim.current_type = SAND
                elif event.key == pygame.K_2:
                    sim.current_type = WATER
                elif event.key == pygame.K_3:
                    sim.current_type = STONE
                elif event.key == pygame.K_4:
                    sim.current_type = GOLD
                elif event.key == pygame.K_5:
                    sim.current_type = ANTIGRAV
                elif event.key == pygame.K_6:
                    sim.current_type = BEES
                elif event.key == pygame.K_7:
                    sim.current_type = STYROFOAM
                elif event.key == pygame.K_c:
                    sim.grid = [[EMPTY] * GRID_HEIGHT for _ in range(GRID_WIDTH)]
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEWHEEL:
                sim.brush_size = max(1, min(10, sim.brush_size + event.y))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            sim.target_angle += 0.03
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            sim.target_angle -= 0.03

        mouse = pygame.mouse.get_pressed()
        pos = pygame.mouse.get_pos()
        if mouse[0]:
            sim.spawn(pos[0], pos[1], sim.current_type)
        elif mouse[2]:
            sim.erase(pos[0], pos[1])

        sim.update()
        sim.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()