import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deadshot Clone")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Target settings
target_radius = 30
target_x = random.randint(target_radius, WIDTH - target_radius)
target_y = random.randint(target_radius, HEIGHT - target_radius)
target_speed = 3

# Score
score = 0
font = pygame.font.SysFont(None, 40)

# Clock
clock = pygame.time.Clock()

def draw_target(x, y):
    pygame.draw.circle(screen, RED, (x, y), target_radius)

def display_score(score):
    text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def move_target(x, y):
    x += random.choice([-1, 1]) * target_speed
    y += random.choice([-1, 1]) * target_speed

    # Keep within bounds
    x = max(target_radius, min(WIDTH - target_radius, x))
    y = max(target_radius, min(HEIGHT - target_radius, y))
    return x, y

# Game loop
running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Check for mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            distance = ((mouse_x - target_x)**2 + (mouse_y - target_y)**2) ** 0.5
            if distance < target_radius:
                score += 1
                target_x = random.randint(target_radius, WIDTH - target_radius)
                target_y = random.randint(target_radius, HEIGHT - target_radius)

    # Move and draw target
    target_x, target_y = move_target(target_x, target_y)
    draw_target(target_x, target_y)
    display_score(score)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
