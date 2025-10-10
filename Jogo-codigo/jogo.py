# main.py
import pygame
import os
import sys
from pathlib import Path

pygame.init()
pygame.mixer.init()

# ---------- Config ----------
WIDTH, HEIGHT = 900, 600
FPS = 60

# Player settings
PLAYER_SPEED = 4.5
JUMP_POWER = -10
GRAVITY = 0.5
PLAYER_MAX_HEALTH = 100
FISH_DAMAGE = 8
ULT_DAMAGE = 35
ULT_CHARGE_PER_HIT = 33  # ~3 hits to full (3*33 = 99)
FISH_SPEED = 8
ULT_SPEED = 6

# Controls
P1_KEYS = {"left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w, "shoot": pygame.K_f, "ult": pygame.K_g}
P2_KEYS = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "shoot": pygame.K_k, "ult": pygame.K_l}

# Paths (tries multiple possibilities)
ASSET_DIRS = [
    Path("assets"),
    Path("jogo-pinguim/assets"),
    Path("jogo-pinguim_extracted/jogo-pinguim/assets"),
    Path("/mnt/data/jogo-pinguim/assets"),
    Path("/mnt/data/jogo-pinguim_extracted/jogo-pinguim/assets"),
    Path(__file__).parent / "assets",          # dentro de Jogo-codigo/assets
    Path(__file__).parent.parent / "assets",  
]

def find_asset(subpath_candidates):
    for base in ASSET_DIRS:
        if not base.exists():
            continue
        for cand in subpath_candidates:
            p = base / cand
            if p.exists():
                return p
    return None

# Attempt to find images
bg_path = find_asset(["extras/fundo.png", "extras/background.png", "fundo.png"])
p_idle_path = find_asset(["Parado/p-parado.png", "Parado/p-parado2.png", "Parado/p-parado.png"])
p_walk_path = find_asset(["Andando/p-andando.png", "Andando/p-andando2.png"])
p_jump_path = find_asset(["Pulando/p-pulando.png"])
p_die_path = find_asset(["Morrendo/p-morrendo.png"])
fish_path = find_asset(["extras/peixe.png", "extras/peixe.png.png", "peixe.png", "peixe.png.png"])
ult_img_path = find_asset(["extras/ult-pinguim.png", "ult-pinguim.png", "extras/ult-pinguim.png.png"])

# Fallback checks
if not p_idle_path:
    print("Aviso: não encontrei sprite de pinguim parado (Parado/p-parado.png). O jogo pode não mostrar o sprite.")
if not fish_path:
    print("Aviso: não encontrei peixe (projétil). Verifique assets/extras/peixe.png")
if not ult_img_path:
    print("Aviso: não encontrei ult-pinguim (assets/extras/ult-pinguim.png) — ult ainda funciona sem imagem.")

# Utility: load image safe
def load_img(path, colorkey=None, scale=None):
    try:
        surf = pygame.image.load(str(path)).convert_alpha()
        if scale:
            surf = pygame.transform.scale(surf, scale)
        if colorkey is not None:
            surf.set_colorkey(colorkey)
        return surf
    except Exception as e:
        print(f"Erro ao carregar {path}: {e}")
        return pygame.Surface((32,32), pygame.SRCALPHA)

# Tint / recolor function (applies multiplicative tint)
def tint_surface(surf, tint_color):
    """Return a tinted copy of surf. tint_color is (r,g,b)."""
    tinted = surf.copy()
    arr = pygame.surfarray.pixels3d(tinted)
    # Multiply color
    r_mult = tint_color[0] / 255.0
    g_mult = tint_color[1] / 255.0
    b_mult = tint_color[2] / 255.0
    arr[..., 0] = (arr[..., 0].astype(float) * r_mult).astype(arr.dtype)
    arr[..., 1] = (arr[..., 1].astype(float) * g_mult).astype(arr.dtype)
    arr[..., 2] = (arr[..., 2].astype(float) * b_mult).astype(arr.dtype)
    del arr
    return tinted

# ---------- Setup window ----------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pinguim PVP")
clock = pygame.time.Clock()

# Load background
if bg_path:
    background = load_img(bg_path, scale=(WIDTH, HEIGHT))
else:
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((25, 100, 200))

# Load pinguim sprites (we'll use single images for simplicity)
p_idle = load_img(p_idle_path) if p_idle_path else pygame.Surface((48,48), pygame.SRCALPHA)
p_walk = load_img(p_walk_path) if p_walk_path else p_idle
p_jump = load_img(p_jump_path) if p_jump_path else p_idle
p_die = load_img(p_die_path) if p_die_path else p_idle

# Load projectiles
fish_img = load_img(fish_path) if fish_path else pygame.Surface((20,12), pygame.SRCALPHA)
ult_img = load_img(ult_img_path) if ult_img_path else None

# Scale sprites reasonably
PLAYER_SCALED = (64, 64)
p_idle = pygame.transform.scale(p_idle, PLAYER_SCALED)
p_walk = pygame.transform.scale(p_walk, PLAYER_SCALED)
p_jump = pygame.transform.scale(p_jump, PLAYER_SCALED)
p_die = pygame.transform.scale(p_die, PLAYER_SCALED)
fish_img = pygame.transform.scale(fish_img, (50, 50))
if ult_img:
    ult_img = pygame.transform.scale(ult_img, (80, 80))

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, controls, color_tint=(255,255,255)):
        super().__init__()
        self.controls = controls
        self.image = p_idle.copy()
        if color_tint != (255,255,255):
            self.image = tint_surface(self.image, color_tint)
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing_right = True
        self.health = PLAYER_MAX_HEALTH
        self.ult_charge = 0
        self.alive = True
        self.color_tint = color_tint

    def update(self, keys):
        if not self.alive:
            return
        left = keys[self.controls["left"]]
        right = keys[self.controls["right"]]
        up = keys[self.controls["up"]]
        self.vx = 0
        if left and not right:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        elif right and not left:
            self.vx = PLAYER_SPEED
            self.facing_right = True

        # Jump
        if up and self.on_ground:
            self.vy = JUMP_POWER
            self.on_ground = False

        # Apply physics
        self.vy += GRAVITY
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Keep inside screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

        # Simple floor collision
        if self.rect.bottom >= HEIGHT - 40:
            self.rect.bottom = HEIGHT - 40
            self.vy = 0
            self.on_ground = True

        # Update image based on state
        if not self.on_ground:
            img = p_jump
        elif self.vx != 0:
            img = p_walk
        else:
            img = p_idle
        # Apply tint if necessary
        self.image = img.copy()
        if self.color_tint != (255,255,255):
            self.image = tint_surface(self.image, self.color_tint)
        if self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def give_ult_charge(self, amount):
        self.ult_charge = min(100, self.ult_charge + amount)

    def reset(self, x, y):
        self.rect.midbottom = (x,y)
        self.vx = self.vy = 0
        self.on_ground = False
        self.facing_right = True
        self.health = PLAYER_MAX_HEALTH
        self.ult_charge = 0
        self.alive = True

# Projectile classes
class FishProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_right, owner):
        super().__init__()
        self.image = fish_img.copy()

        if dir_right:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect(center=(x,y))
        self.vx = FISH_SPEED if dir_right else -FISH_SPEED
        self.owner = owner

    def update(self):
        self.rect.x += self.vx
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class UltProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_right, owner):
        super().__init__()
        if ult_img:
            self.image = ult_img.copy()
            if not dir_right:
                self.image = pygame.transform.flip(self.image, True, False)
        else:
            # fallback rect
            self.image = pygame.Surface((50,50), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255,255,255), (25,25), 25)
        self.rect = self.image.get_rect(center=(x,y))
        self.vx = ULT_SPEED if dir_right else -ULT_SPEED
        self.owner = owner

    def update(self):
        self.rect.x += self.vx
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

# Create players
p1 = Player(150, HEIGHT-40, P1_KEYS, color_tint=(200,220,255))  # slightly bluish (original)
p2 = Player(WIDTH-150, HEIGHT-40, P2_KEYS, color_tint=(255,200,200))  # reddish tint for distinction

players = pygame.sprite.Group(p1, p2)
fish_group = pygame.sprite.Group()
ult_group = pygame.sprite.Group()

# HUD draw
font = pygame.font.SysFont(None, 22)
big_font = pygame.font.SysFont(None, 48)

def draw_hud():
    # P1 HUD
    bar_w = 220
    x1 = 20
    y1 = 15
    pygame.draw.rect(screen, (30,30,30), (x1-2,y1-2,bar_w+4,34))
    pygame.draw.rect(screen, (120,0,0), (x1, y1, bar_w, 12))
    health_ratio = p1.health / PLAYER_MAX_HEALTH
    pygame.draw.rect(screen, (0,200,0), (x1, y1, bar_w * health_ratio, 12))
    screen.blit(font.render("P1 HP", True, (255,255,255)), (x1, y1+14))
    # Ult bar
    pygame.draw.rect(screen, (60,60,60), (x1, y1+32, bar_w, 12))
    pygame.draw.rect(screen, (0,120,255), (x1, y1+32, bar_w * (p1.ult_charge/100), 12))
    screen.blit(font.render("P1 ULT", True, (255,255,255)), (x1, y1+46))

    # P2 HUD (right)
    x2 = WIDTH - 20 - bar_w
    pygame.draw.rect(screen, (30,30,30), (x2-2,y1-2,bar_w+4,34))
    pygame.draw.rect(screen, (120,0,0), (x2, y1, bar_w, 12))
    health_ratio2 = p2.health / PLAYER_MAX_HEALTH
    pygame.draw.rect(screen, (0,200,0), (x2, y1, bar_w * health_ratio2, 12))
    screen.blit(font.render("P2 HP", True, (255,255,255)), (x2, y1+14))
    pygame.draw.rect(screen, (60,60,60), (x2, y1+32, bar_w, 12))
    pygame.draw.rect(screen, (0,120,255), (x2, y1+32, bar_w * (p2.ult_charge/100), 12))
    screen.blit(font.render("P2 ULT", True, (255,255,255)), (x2, y1+46))

# Shooting cooldowns to avoid spam
COOLDOWN_FRAMES = 10
p1_cd = 0
p2_cd = 0

# Game loop flags
running = True
winner_text = None

def handle_shooting(keys):
    global p1_cd, p2_cd
    # P1 shoot
    if p1.alive:
        if keys[p1.controls["shoot"]] and p1_cd <= 0:
            # spawn fish
            spawn_x = p1.rect.centerx + (p1.rect.width//2 + 10) * (1 if p1.facing_right else -1)
            spawn_y = p1.rect.centery - 6
            fish_group.add(FishProjectile(spawn_x, spawn_y, p1.facing_right, p1))
            p1_cd = COOLDOWN_FRAMES
        if keys[p1.controls["ult"]] and p1.ult_charge >= 100:
            spawn_x = p1.rect.centerx + (p1.rect.width//2 + 20) * (1 if p1.facing_right else -1)
            spawn_y = p1.rect.centery
            ult_group.add(UltProjectile(spawn_x, spawn_y, p1.facing_right, p1))
            p1.ult_charge = 0

    # P2 shoot
    if p2.alive:
        if keys[p2.controls["shoot"]] and p2_cd <= 0:
            spawn_x = p2.rect.centerx + (p2.rect.width//2 + 10) * (1 if p2.facing_right else -1)
            spawn_y = p2.rect.centery - 6
            fish_group.add(FishProjectile(spawn_x, spawn_y, p2.facing_right, p2))
            p2_cd = COOLDOWN_FRAMES
        if keys[p2.controls["ult"]] and p2.ult_charge >= 100:
            spawn_x = p2.rect.centerx + (p2.rect.width//2 + 20) * (1 if p2.facing_right else -1)
            spawn_y = p2.rect.centery
            ult_group.add(UltProjectile(spawn_x, spawn_y, p2.facing_right, p2))
            p2.ult_charge = 0

# Collision handling
def handle_collisions():
    # Fish vs players (but ignore owner)
    for fish in fish_group.sprites():
        hit_players = [pl for pl in players if pl != fish.owner and pl.alive and fish.rect.colliderect(pl.rect)]
        for hit in hit_players:
            hit.take_damage(FISH_DAMAGE)
            fish.owner.give_ult_charge(ULT_CHARGE_PER_HIT)
            fish.kill()

    # Ult vs players
    for ult in ult_group.sprites():
        hit_players = [pl for pl in players if pl != ult.owner and pl.alive and ult.rect.colliderect(pl.rect)]
        for hit in hit_players:
            hit.take_damage(ULT_DAMAGE)
            ult.kill()

def check_winner():
    global winner_text
    if not p1.alive and p2.alive:
        winner_text = "P2 VENCEU!"
    elif not p2.alive and p1.alive:
        winner_text = "P1 VENCEU!"
    elif not p1.alive and not p2.alive:
        winner_text = "EMPATE!"

def reset_game():
    global winner_text, p1_cd, p2_cd
    winner_text = None
    p1.reset(150, HEIGHT-40)
    p2.reset(WIDTH-150, HEIGHT-40)
    fish_group.empty()
    ult_group.empty()
    p1_cd = p2_cd = 0

# Main loop
while running:
    dt = clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if winner_text and event.key == pygame.K_r:
                reset_game()

    # Update players if no winner yet
    if not winner_text:
        players.update(keys)
        # handle shooting input
        handle_shooting(keys)
        # update projectiles
        fish_group.update()
        ult_group.update()
        # collisions
        handle_collisions()
        # check death
        check_winner()
        # cooldowns
        if p1_cd > 0:
            p1_cd -= 1
        if p2_cd > 0:
            p2_cd -= 1

    # Draw
    screen.blit(background, (0,0))
    # ground
    pygame.draw.rect(screen, (40,40,40), (0, HEIGHT-40, WIDTH, 40))
    players.draw(screen)
    fish_group.draw(screen)
    ult_group.draw(screen)
    draw_hud()

    # show instructions bottom
    instr = "P1: WASD mover, F atirar, G ult | P2: Setas mover, K atirar, L ult | R para reiniciar"
    screen.blit(font.render(instr, True, (255,255,255)), (20, HEIGHT-25))

    if winner_text:
        txt_surf = big_font.render(winner_text, True, (255, 230, 0))
        txt_rect = txt_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
        screen.blit(txt_surf, txt_rect)
        sub = font.render("Pressione R para reiniciar", True, (255,255,255))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()

pygame.quit()
sys.exit()