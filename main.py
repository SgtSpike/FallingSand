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

BACKGROUND_COLOR = (20, 20, 30)

# Colors for each particle type
COLORS = {
    SAND: (194, 178, 128),
    WATER: (50, 100, 200),
    STONE: (80, 80, 80),
    GOLD: (255, 200, 50),
    ANTIGRAV: (240, 240, 255),
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
        gx, gy = self.get_gravity()

        # Check if gravity is significant
        if abs(gx) < 0.01 and abs(gy) < 0.01:
            return  # No significant gravity

        # Process in correct order based on gravity direction
        if gy > 0.01:
            y_range = range(GRID_HEIGHT - 1, -1, -1)
        elif gy < -0.01:
            y_range = range(GRID_HEIGHT)
        else:
            if self.frame_count % 2 == 0:
                y_range = range(GRID_HEIGHT)
            else:
                y_range = range(GRID_HEIGHT - 1, -1, -1)

        if gx > 0.01:
            x_range = range(GRID_WIDTH - 1, -1, -1)
        elif gx < -0.01:
            x_range = range(GRID_WIDTH)
        else:
            if self.frame_count % 2 == 0:
                x_range = range(GRID_WIDTH)
            else:
                x_range = range(GRID_WIDTH - 1, -1, -1)

        for y in y_range:
            for x in x_range:
                p = self.grid[x][y]
                if p == EMPTY or p == STONE:
                    continue

                # Determine movement parameters based on particle type
                if p == ANTIGRAV:
                    # Antigrav moves opposite to gravity
                    pgx, pgy = -gx, -gy
                    steps = 2
                else:
                    pgx, pgy = gx, gy
                    steps = 2 if p == GOLD else 1

                # Calculate movement probabilities based on gravity components
                ax, ay = abs(pgx), abs(pgy)
                total = ax + ay
                if total < 0.01:
                    continue

                # Direction signs
                sx = 1 if pgx > 0 else -1
                sy = 1 if pgy > 0 else -1

                for _ in range(steps):
                    moved = False

                    # Build movement attempts using probability
                    attempts = []

                    # Use random to decide primary movement based on gravity ratio
                    r = random.random() * total
                    if r < ax:
                        # Favor horizontal movement
                        attempts.append((x + sx, y))
                        attempts.append((x + sx, y + sy))
                        attempts.append((x, y + sy))
                    else:
                        # Favor vertical movement
                        attempts.append((x, y + sy))
                        attempts.append((x + sx, y + sy))
                        attempts.append((x + sx, y))

                    # Also try sliding sideways (perpendicular to movement)
                    d = random.choice([-1, 1])
                    if ay > 0.01:
                        attempts.append((x + d, y + sy))
                        attempts.append((x - d, y + sy))
                    if ax > 0.01:
                        attempts.append((x + sx, y + d))
                        attempts.append((x + sx, y - d))

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
                        elif target == ANTIGRAV:
                            # Sand, gold, water cannot move through antigrav
                            continue

                    # Water spreads perpendicular to gravity
                    if not moved and p == WATER:
                        spread = random.choice([-1, 1])
                        for dist in range(1, 4):
                            # Spread perpendicular to gravity direction
                            if ay > ax * 2:
                                # Mostly vertical gravity - spread horizontally
                                wx, wy = x + spread * dist, y
                            elif ax > ay * 2:
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
        names = {SAND: "Sand", WATER: "Water", STONE: "Stone", GOLD: "Gold", ANTIGRAV: "Antigrav"}
        surface.blit(font.render(f"[1-5] Type: {names[self.current_type]}", True, (200, 200, 200)), (10, 10))
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
