import pygame
import random
import math
import sys

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 5000, 5000  # Bigger world

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Subnarica - Open World")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# Colors
WHITE = (255, 255, 255)
RED = (200, 30, 30)
GREEN = (30, 200, 30)
BLUE = (30, 30, 200)
GRAY = (100, 100, 100)
YELLOW = (230, 230, 50)
SHELTER_COLOR = (139, 69, 19)  # Brownish for shelter
DESTROYED_COLOR = (80, 80, 80)  # Dark gray for destroyed structures

# Player
player = pygame.Rect(400, 300, 40, 40)
player_speed = 5

# Camera
camera = pygame.Rect(0, 0, WIDTH, HEIGHT)

# World elements
materials = []
destroyed_structures = []
shelters = []

# Inventory and crafting
inventory = {}
crafted_items = []
recipes = {
    'knife': {'metal': 2, 'wood': 3},
    'oxygen_tank': {'metal': 5, 'glass': 3},
    'healing_pack': {'herbs': 3, 'cloth': 2},
    'shelter': {'metal': 10, 'wood': 15}
}

# Objectives
objectives = ["Craft a knife", "Build a shelter"]
objective_status = [False, False]

# Player stats
max_oxygen = 100
oxygen = max_oxygen
max_health = 100
health = max_health

# Enemy
enemies = []
enemy_spawn_rate = 0.003  # Spawn chance per frame
enemy_speed = 2

# Boss
boss = {
    'rect': pygame.Rect(0, 0, 80, 80),
    'speed': 1.5,
    'health': 20,
    'active': False
}

# Attack cooldowns
attack_cooldown = 300  # ms between player attacks
last_attack_time = 0

# Oxygen depletion timer
oxygen_depletion_interval = 2000  # 2 seconds
last_oxygen_depletion = 0

# Material spawn timer
material_spawn_interval = 4000
last_material_spawn = 0

# Show overlays
show_inventory = False
show_recipes = False

# Death flag
dead = False

# Shelter state - track if player is inside a shelter
inside_shelter = False
current_shelter = None

def enemy_chase(enemy_rect, target_rect, speed):
    dx = target_rect.centerx - enemy_rect.centerx
    dy = target_rect.centery - enemy_rect.centery
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    dx, dy = dx / dist, dy / dist
    enemy_rect.x += dx * speed
    enemy_rect.y += dy * speed

def boss_chase(boss_rect, target_rect, speed):
    dx = target_rect.centerx - boss_rect.centerx
    dy = target_rect.centery - boss_rect.centery
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    dx, dy = dx / dist, dy / dist
    boss_rect.x += dx * speed
    boss_rect.y += dy * speed

def spawn_material():
    mat_types = ['metal', 'wood', 'glass', 'herbs', 'cloth']
    mtype = random.choice(mat_types)
    x = random.randint(0, WORLD_WIDTH-20)
    y = random.randint(0, WORLD_HEIGHT-20)
    materials.append({'type': mtype, 'rect': pygame.Rect(x, y, 20, 20)})

def spawn_destroyed_structure():
    x = random.randint(0, WORLD_WIDTH - 60)
    y = random.randint(0, WORLD_HEIGHT - 60)
    rect = pygame.Rect(x, y, 60, 60)
    destroyed_structures.append(rect)

def draw_gradient_background(screen, t):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(0 + 40 * ratio)
        g = int(50 + 100 * ratio)
        b = int(80 + 120 * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

def draw_underwater_light(screen, t):
    alpha = int((math.sin(t * 0.002) + 1) / 2 * 100 + 50)
    light = pygame.Surface((WIDTH, HEIGHT // 4), pygame.SRCALPHA)
    for y in range(HEIGHT // 4):
        pygame.draw.line(light, (255, 255, 255, max(0, alpha - y*2)), (0, y), (WIDTH, y))
    screen.blit(light, (0, 0))

def draw_shadow(screen, rect, camera):
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 90))
    screen.blit(shadow, (rect.x - camera.x + 5, rect.y - camera.y + 5))

def draw_inventory_overlay(screen):
    overlay = pygame.Surface((300, 400))
    overlay.fill((30, 30, 30))
    overlay.set_alpha(230)
    screen.blit(overlay, (WIDTH//2 - 150, HEIGHT//2 - 200))
    y = HEIGHT//2 - 180
    x = WIDTH//2 - 130
    screen.blit(font.render("Inventory:", True, WHITE), (x, y))
    y += 30
    if not inventory:
        screen.blit(font.render("Empty", True, WHITE), (x, y))
    else:
        for mat, count in inventory.items():
            screen.blit(font.render(f"{mat}: {count}", True, WHITE), (x, y))
            y += 25

def draw_recipe_overlay(screen):
    overlay = pygame.Surface((400, 300))
    overlay.fill((50, 50, 50))
    overlay.set_alpha(240)
    screen.blit(overlay, (WIDTH//2 - 200, HEIGHT//2 - 150))
    y = HEIGHT//2 - 130
    x = WIDTH//2 - 180
    screen.blit(font.render("Crafting Recipes:", True, WHITE), (x, y))
    y += 30
    for item, reqs in recipes.items():
        reqs_str = ", ".join(f"{mat} x{count}" for mat, count in reqs.items())
        screen.blit(font.render(f"{item}: {reqs_str}", True, WHITE), (x, y))
        y += 25

def draw_death_screen():
    screen.fill((0, 0, 0))
    text1 = font.render("You Died!", True, RED)
    text2 = font.render("Press R to Restart or Q to Quit", True, WHITE)
    screen.blit(text1, (WIDTH//2 - text1.get_width()//2, HEIGHT//2 - 40))
    screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2 + 10))
    pygame.display.flip()

# Initial spawn of structures and materials
for _ in range(15):
    spawn_destroyed_structure()
for _ in range(20):
    spawn_material()

# Main loop
running = True
while running:
    dt = clock.tick(60)
    seconds_passed = dt / 1000.0
    time_now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if dead:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Restart game (simple reset)
                    player.x, player.y = 400, 300
                    oxygen = max_oxygen
                    health = max_health
                    enemies.clear()
                    materials.clear()
                    destroyed_structures.clear()
                    shelters.clear()
                    inventory.clear()
                    crafted_items.clear()
                    objective_status[:] = [False] * len(objective_status)
                    objectives[:] = ["Craft a knife", "Build a shelter"]
                    boss['active'] = False
                    boss['health'] = 20
                    dead = False
                if event.key == pygame.K_q:
                    running = False

    if dead:
        draw_death_screen()
        continue

    keys = pygame.key.get_pressed()

    # Toggle inventory and recipes overlay
    if keys[pygame.K_e]:
        show_inventory = not show_inventory
        pygame.time.wait(200)
    if keys[pygame.K_r]:
        show_recipes = not show_recipes
        pygame.time.wait(200)

    # --- MOVEMENT ---
    dx = dy = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += player_speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= player_speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += player_speed

    # Move player and collision check
    new_player = player.move(dx, dy)

    blocked = False
    # Blocked by destroyed structures and shelters if outside shelter
    for wall in destroyed_structures:
        if new_player.colliderect(wall):
            blocked = True
            break
    # If outside shelter, block shelter walls
    if not inside_shelter:
        for sh in shelters:
            if new_player.colliderect(sh):
                blocked = True
                break
    # If inside shelter, allow movement only inside current shelter rect
    else:
        if not current_shelter or not new_player.colliderect(current_shelter):
            blocked = True

    # Keep player inside world bounds
    if new_player.left < 0 or new_player.right > WORLD_WIDTH or new_player.top < 0 or new_player.bottom > WORLD_HEIGHT:
        blocked = True

    if not blocked:
        player = new_player

    # --- ENTER/EXIT SHELTER (SPACE) ---
    if keys[pygame.K_SPACE]:
        # Check if player is near any shelter (within 50 px)
        if inside_shelter:
            # Exit shelter
            inside_shelter = False
            current_shelter = None
        else:
            for sh in shelters:
                dist = math.hypot(player.centerx - sh.centerx, player.centery - sh.centery)
                if dist < 50:
                    inside_shelter = True
                    current_shelter = sh
                    break
        pygame.time.wait(300)  # Debounce space press

    # --- CAMERA ---
    camera.x = player.x - WIDTH // 2
    camera.y = player.y - HEIGHT // 2
    camera.x = max(0, min(camera.x, WORLD_WIDTH - WIDTH))
    camera.y = max(0, min(camera.y, WORLD_HEIGHT - HEIGHT))

    # --- SPAWN MATERIALS ---
    if time_now - last_material_spawn > material_spawn_interval:
        spawn_material()
        last_material_spawn = time_now

    # --- SPAWN ENEMIES ---
    if random.random() < enemy_spawn_rate:
        ex = random.randint(0, WORLD_WIDTH-40)
        ey = random.randint(0, WORLD_HEIGHT-40)
        enemies.append({'rect': pygame.Rect(ex, ey, 40, 40), 'speed': enemy_speed, 'health': 3})

    # --- PICKUP MATERIALS ---
    for mat in materials[:]:
        if player.colliderect(mat['rect']):
            inventory[mat['type']] = inventory.get(mat['type'], 0) + 1
            materials.remove(mat)

    # --- CRAFTING ---
    craft_keys = {
        pygame.K_1: 'knife',
        pygame.K_2: 'oxygen_tank',
        pygame.K_3: 'healing_pack',
        pygame.K_4: 'shelter'
    }
    for key, item in craft_keys.items():
        if keys[key]:
            can_craft = True
            for mat, count in recipes[item].items():
                if inventory.get(mat, 0) < count:
                    can_craft = False
                    break
            if can_craft:
                for mat, count in recipes[item].items():
                    inventory[mat] -= count
                    if inventory[mat] == 0:
                        del inventory[mat]
                crafted_items.append(item)
                if item == 'oxygen_tank':
                    max_oxygen += 50  # Increase max oxygen
                    oxygen = max_oxygen
                if item == 'healing_pack':
                    health = min(max_health, health + 30)
                if item == 'shelter':
                    # Place shelter at player position
                    shelter_rect = pygame.Rect(player.x - 30, player.y - 30, 100, 100)
                    shelters.append(shelter_rect)
                    # Add a destroyed structure inside shelter so walls block outside
                    destroyed_structures.append(shelter_rect)
                    objective_status[1] = True
                if item == 'knife':
                    objective_status[0] = True
                pygame.time.wait(300)  # Debounce

    # --- OXYGEN DEPLETION ---
    if not inside_shelter and time_now - last_oxygen_depletion > oxygen_depletion_interval:
        oxygen -= 5
        oxygen = max(0, oxygen)
        last_oxygen_depletion = time_now
    if oxygen == 0:
        health -= 1
        if health <= 0:
            dead = True

    # --- ENEMY AI ---
    for enemy in enemies[:]:
        dist = math.hypot(player.centerx - enemy['rect'].centerx, player.centery - enemy['rect'].centery)
        if dist < 250:
            enemy_chase(enemy['rect'], player, enemy['speed'])

    # --- ENEMY ATTACK ---
    # Attack cooldown for enemies (1 sec per hit)
    for enemy in enemies[:]:
        dist = math.hypot(player.centerx - enemy['rect'].centerx, player.centery - enemy['rect'].centery)
        if dist < 50:
            if not hasattr(enemy, 'last_attack'):
                enemy['last_attack'] = 0
            if time_now - enemy['last_attack'] > 1000:  # 1 second cooldown
                health -= 10
                enemy['last_attack'] = time_now
                if health <= 0:
                    dead = True

    # --- PLAYER ATTACK (Q key) ---
    if keys[pygame.K_q]:
        if time_now - last_attack_time > attack_cooldown:
            # Attack enemy in range (50 px)
            for enemy in enemies[:]:
                dist = math.hypot(player.centerx - enemy['rect'].centerx, player.centery - enemy['rect'].centery)
                if dist < 50:
                    enemy['health'] -= 1
                    if enemy['health'] <= 0:
                        enemies.remove(enemy)
                    break
            last_attack_time = time_now

    # --- OBJECTIVES CHECK ---
    if all(objective_status) and not boss['active']:
        boss['active'] = True
        boss['rect'].x = random.randint(0, WORLD_WIDTH - boss['rect'].width)
        boss['rect'].y = random.randint(0, WORLD_HEIGHT - boss['rect'].height)

    # --- BOSS AI ---
    if boss['active']:
        boss_chase(boss['rect'], player, boss['speed'])
        dist = math.hypot(player.centerx - boss['rect'].centerx, player.centery - boss['rect'].centery)
        if dist < 80:
            if not hasattr(boss, 'last_attack'):
                boss['last_attack'] = 0
            if time_now - boss['last_attack'] > 1500:
                health -= 20
                boss['last_attack'] = time_now
                if health <= 0:
                    dead = True
        # Player can attack boss as well
        if keys[pygame.K_q]:
            if time_now - last_attack_time > attack_cooldown:
                if dist < 80:
                    boss['health'] -= 1
                    if boss['health'] <= 0:
                        boss['active'] = False
                        objectives.append("Boss Defeated! Game Complete!")
                last_attack_time = time_now

    # --- DRAWING ---
    draw_gradient_background(screen, time_now)
    draw_underwater_light(screen, time_now)

    # Draw materials
    for mat in materials:
        color = {
            'metal': GRAY,
            'wood': (160, 82, 45),
            'glass': (135, 206, 235),
            'herbs': (34, 139, 34),
            'cloth': (220, 220, 220)
        }.get(mat['type'], WHITE)
        pygame.draw.rect(screen, color, pygame.Rect(mat['rect'].x - camera.x, mat['rect'].y - camera.y, 20, 20))

    # Draw destroyed structures
    for struct in destroyed_structures:
        pygame.draw.rect(screen, DESTROYED_COLOR, pygame.Rect(struct.x - camera.x, struct.y - camera.y, struct.width, struct.height))

    # Draw shelters with different color
    for sh in shelters:
        pygame.draw.rect(screen, SHELTER_COLOR, pygame.Rect(sh.x - camera.x, sh.y - camera.y, sh.width, sh.height))

    # Draw enemies
    for enemy in enemies:
        pygame.draw.rect(screen, RED, pygame.Rect(enemy['rect'].x - camera.x, enemy['rect'].y - camera.y, enemy['rect'].width, enemy['rect'].height))

    # Draw boss
    if boss['active']:
        pygame.draw.rect(screen, YELLOW, pygame.Rect(boss['rect'].x - camera.x, boss['rect'].y - camera.y, boss['rect'].width, boss['rect'].height))

    # Draw player
    pygame.draw.rect(screen, BLUE, pygame.Rect(player.x - camera.x, player.y - camera.y, player.width, player.height))

    # Draw health and oxygen bars
    pygame.draw.rect(screen, RED, (20, 20, 200, 20))
    pygame.draw.rect(screen, GREEN, (20, 20, 200 * (health / max_health), 20))
    screen.blit(font.render("HP", True, WHITE), (225, 20))

    pygame.draw.rect(screen, GRAY, (20, 50, 200, 20))
    pygame.draw.rect(screen, BLUE, (20, 50, 200 * (oxygen / max_oxygen), 20))
    screen.blit(font.render("Oxygen", True, WHITE), (225, 50))

    # Draw objectives
    y_obj = 90
    for i, obj in enumerate(objectives):
        color = GREEN if (i < len(objective_status) and objective_status[i]) else WHITE
        screen.blit(font.render(f"Objective: {obj}", True, color), (20, y_obj))
        if i < len(objective_status) and objective_status[i]:
            screen.blit(font.render("✓", True, GREEN), (180, y_obj))
        y_obj += 25

    # Show inventory or recipes overlay
    if show_inventory:
        draw_inventory_overlay(screen)
    if show_recipes:
        draw_recipe_overlay(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
