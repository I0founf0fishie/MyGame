import math
import os
import random
import sys
from dataclasses import dataclass
from typing import List, Optional
import pygame
# ---------------------------
# Константы
# ---------------------------
GAME_W = 960
GAME_H = 540
GROUND_Y = GAME_H - 40
GRAVITY = 0.7
JUMP_VELOCITY = -14
PLAYER_X = 140
PLAYER_W = 80
PLAYER_H = 80
BASE_SPEED = 4.0
NUM_LAYERS = 5
LAYER_TOP_Y = 110
LAYER_BOTTOM_Y = GROUND_Y - 70
LAYER_GAP = (LAYER_BOTTOM_Y - LAYER_TOP_Y) / (NUM_LAYERS - 1)
LAYER_YS = [LAYER_BOTTOM_Y - i * LAYER_GAP for i in range(NUM_LAYERS)]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR_CANDIDATES = [
    BASE_DIR,
    os.path.join(BASE_DIR, "assets"),
    os.path.join(BASE_DIR, "dream_assets"),
]
@dataclass

class Cloud:
    x: float
    y: float
    w: float
    h: float
    kind: str  # normal | storm | sugar
    hit: bool
    layer: int
    storm_anim_time: float = -1.0
@dataclass

class Star:
    x: float
    y: float
    size: float
    hit: bool
@dataclass

class Player:
    x: float
    y: float
    vy: float
    on_cloud: Optional[Cloud]
    on_ground: bool

def jump_airtime(delta_up: float) -> float:
    a = 0.5 * GRAVITY
    b = JUMP_VELOCITY
    c = delta_up
    disc = b * b - 4 * a * c
    if disc < 0:
        return 0.0
    return (-b + math.sqrt(disc)) / (2 * a)

def find_asset_path(name: str) -> Optional[str]:
    for base in ASSET_DIR_CANDIDATES:
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return None


def load_image(name: str, alpha: bool = True):
    path = find_asset_path(name)
    if not path:
        print("[WARN] Не найден ассет:", name)
        return None
    img = pygame.image.load(path)
    return img.convert_alpha() if alpha else img.convert()
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Sheep and Dream — Овечка и Сон")
        self.screen = pygame.display.set_mode((GAME_W, GAME_H))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 44, bold=True)
        self.font_mid = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.images = {
            "bg": load_image("background.png", alpha=False),
            "sheep_idle": load_image("sheep_1.png"),
            "sheep_push": load_image("sheep_2-1.png"),
            "sheep_jump": load_image("sheep_2-2.png"),
            "cloud_normal": load_image("cloud_1.png"),
            "cloud_storm": load_image("cloud_3.png"),
            "cloud_storm_1": load_image("cloud_3_1.png"),
            "cloud_storm_2": load_image("cloud_3_2.png"),
            "cloud_storm_3": load_image("cloud_3_3.png"),
            "cloud_sugar": load_image("cloud_2.png"),
            "star": load_image("star_1.png"),
            "heart": load_image("heart.png"),
        }
        self.started = False
        self.paused = False
        self.game_over = False
        self.reset()

    def reset(self):
        self.player = Player(
            x=PLAYER_X, y=GROUND_Y - PLAYER_H, vy=0.0, on_cloud=None, on_ground=True
        )
        self.clouds: List[Cloud] = []
        self.stars: List[Star] = []
        self.bg_x = 0.0
        self.score = 0
        self.lives = 3
        self.speed = BASE_SPEED
        self.score_acc = 0.0
        self.invuln = 0.0
        self.push_timer = 0.0
        self.last_column_right_x = 0.0
        self.last_column_layers = [0]
        self.last_column_hazard = False
        self.finished = False
        self.spawn_initial()

    def rand(self, a: float, b: float) -> float:
        return random.uniform(a, b)
    
    def pick_safe_kind(self) -> str:
        if self.lives < 3 and random.random() < 0.25:
            return "sugar"
        return "normal"
    
    def spawn_initial(self):
        start_layer_y = LAYER_YS[0]
        start_cloud = Cloud(
            x=80, y=start_layer_y, w=220, h=60, kind="normal", hit=True, layer=0, storm_anim_time=-1.0
        )
        self.clouds.append(start_cloud)
        self.player.y = start_cloud.y + 10 - PLAYER_H
        self.player.on_cloud = start_cloud
        self.player.on_ground = False
        self.last_column_right_x = 80 + 220
        self.last_column_layers = [0]
        safety = 0
        while self.last_column_right_x < GAME_W + 400 and safety < 50:
            self.spawn_next_column()
            safety += 1

    def spawn_next_column(self):
        prev_layers = self.last_column_layers
        mandatory_max_layer = min(NUM_LAYERS - 1, min(prev_layers) + 1)
        reachable_layers = list(range(mandatory_max_layer + 1))
        allow_hazard = not self.last_column_hazard
        r = random.random()
        hazard_type = "none"
        if allow_hazard:
            if r < 0.18:
                hazard_type = "storm"
            elif r < 0.3:
                hazard_type = "star"
        placements = []
        if hazard_type == "storm":
            storm_layer = random.choice(reachable_layers)
            alt = [l for l in reachable_layers if l != storm_layer]
            safe_layer = random.choice(alt) if alt else min(NUM_LAYERS - 1, storm_layer + 1)
            placements.append((storm_layer, "storm"))
            placements.append((safe_layer, self.pick_safe_kind()))
        else:
            num_clouds = 1 if random.random() < 0.6 else 2
            chosen = {random.choice(reachable_layers)}
            while len(chosen) < num_clouds:
                chosen.add(random.randint(0, NUM_LAYERS - 1))
            for layer in chosen:
                placements.append((layer, self.pick_safe_kind()))
        layers = [p[0] for p in placements]
        tightest_reach = float("inf")
        for pl in prev_layers:
            best_for_pl = 0.0
            for tl in layers:
                if tl > pl + 1:
                    continue
                delta_up = LAYER_YS[pl] - LAYER_YS[tl]
                at = jump_airtime(delta_up)
                if at > best_for_pl:
                    best_for_pl = at
            if best_for_pl == 0:
                continue
            tightest_reach = min(tightest_reach, best_for_pl)
        if not math.isfinite(tightest_reach):
            tightest_reach = 0.0
        reach = tightest_reach * self.speed * 0.65
        min_gap = 80
        max_gap = max(min_gap + 30, reach)
        gap = self.rand(min_gap, max_gap)
        col_x = self.last_column_right_x + gap
        w = 180
        h = 60
        rightmost = col_x
        for layer, kind in placements:
            jitter = self.rand(-20, 20)
            x = col_x + jitter
            self.clouds.append(
                Cloud(
                    x=x,
                    y=LAYER_YS[layer],
                    w=w,
                    h=h,
                    kind=kind,
                    hit=False,
                    layer=layer,
                    storm_anim_time=-1.0,
                )
            )
            rightmost = max(rightmost, x + w)
        if hazard_type == "star":
            # удаляем облака текущей колонки и собираем колонку заново под звезду
            for _ in range(len(placements)):
                self.clouds.pop()
            star_slot = random.randint(0, NUM_LAYERS - 1)
            mode = random.choice(["above", "level", "below"])
            if mode == "above":
                star_y = LAYER_YS[star_slot] - self.rand(35, 55)
            elif mode == "level":
                star_y = LAYER_YS[star_slot] - self.rand(5, 20)
            else:
                star_y = LAYER_YS[star_slot] + self.rand(25, 45)
            h_pos = random.random()
            if h_pos < 0.33:
                star_x_offset = self.rand(-30, 10)
            elif h_pos < 0.66:
                star_x_offset = self.rand(40, 80)
            else:
                star_x_offset = self.rand(90, 130)

            def layer_is_safe(L: int) -> bool:
                player_top = LAYER_YS[L] + 10 - PLAYER_H
                player_bot = LAYER_YS[L] + 10
                return player_bot <= star_y - 5 or player_top >= star_y + 55
            candidates = [l for l in reachable_layers if layer_is_safe(l)]
            if candidates:
                safe_bypass_layer = random.choice(candidates)
            else:
                fallback = [l for l in reachable_layers if l != star_slot]
                safe_bypass_layer = random.choice(fallback) if fallback else reachable_layers[0]
            slot_cloud_safe = layer_is_safe(star_slot)
            star_clouds = [(safe_bypass_layer, self.pick_safe_kind())]
            if slot_cloud_safe and star_slot != safe_bypass_layer and random.random() < 0.5:
                star_clouds.append((star_slot, self.pick_safe_kind()))
            rightmost = col_x
            for layer, kind in star_clouds:
                jitter = self.rand(-20, 20)
                x = col_x + jitter
                self.clouds.append(
                    Cloud(
                        x=x,
                        y=LAYER_YS[layer],
                        w=w,
                        h=h,
                        kind=kind,
                        hit=False,
                        layer=layer,
                        storm_anim_time=-1.0,
                    )
                )
                rightmost = max(rightmost, x + w)
            self.stars.append(Star(x=col_x + star_x_offset, y=star_y, size=50, hit=False))
            self.last_column_layers = [c[0] for c in star_clouds]
        else:
            self.last_column_layers = layers
        self.last_column_right_x = rightmost
        self.last_column_hazard = hazard_type != "none"

    def jump(self):
        if self.finished:
            return
        if self.player.on_ground or self.player.on_cloud:
            self.player.vy = JUMP_VELOCITY
            self.push_timer = 0.3
            self.player.on_ground = False
            self.player.on_cloud = None

    def lose_life(self):
        if self.invuln > 0:
            return
        self.lives -= 1
        self.invuln = 1.2
        if self.lives <= 0:
            self.lives = 0
            self.finished = True
            self.game_over = True
    def gain_life(self):
        if self.lives < 3:
            self.lives += 1

    def update(self, dt: float):
        if self.finished:
            return
        self.score_acc += dt * 10
        self.score = int(self.score_acc)
        tier = self.score // 250
        self.speed = BASE_SPEED + tier * 0.6
        if self.invuln > 0:
            self.invuln -= dt
        if self.push_timer > 0:
            self.push_timer = max(0.0, self.push_timer - dt)
        self.bg_x -= self.speed * 0.3
        if self.bg_x <= -GAME_W:
            self.bg_x += GAME_W
        for c in self.clouds:
            c.x -= self.speed
            if c.kind == "storm" and c.storm_anim_time >= 0:
                c.storm_anim_time += dt
        for s in self.stars:
            s.x -= self.speed
        self.last_column_right_x -= self.speed
        self.clouds = [c for c in self.clouds if c.x + c.w > -50]
        self.stars = [s for s in self.stars if s.x + s.size > -50]
        safety = 0
        while self.last_column_right_x < GAME_W + 400 and safety < 10:
            self.spawn_next_column()
            safety += 1
        p = self.player
        p.vy += GRAVITY
        p.y += p.vy
        landed = False
        if p.vy >= 0:
            for c in self.clouds:
                px1 = p.x + 10
                px2 = p.x + PLAYER_W - 10
                cx1 = c.x
                cx2 = c.x + c.w
                overlap = px2 > cx1 and px1 < cx2
                cloud_top = c.y + 10
                prev_bottom = p.y - p.vy + PLAYER_H
                curr_bottom = p.y + PLAYER_H
                if overlap and prev_bottom <= cloud_top <= curr_bottom:
                    p.y = cloud_top - PLAYER_H
                    p.vy = 0
                    p.on_cloud = c
                    p.on_ground = False
                    landed = True
                    if not c.hit:
                        c.hit = True
                        if c.kind == "storm":
                            c.storm_anim_time = 0.0
                            self.lose_life()
                        elif c.kind == "sugar":
                            self.gain_life()
                    break
        if not landed:
            p.on_cloud = None
            if p.y + PLAYER_H >= GROUND_Y:
                self.lose_life()
                if not self.finished:
                    p.y = -PLAYER_H
                    p.vy = 0
        else:
            c = p.on_cloud
            if c and (p.x + 10 > c.x + c.w or p.x + PLAYER_W - 10 < c.x):
                p.on_cloud = None
        for s in self.stars:
            if s.hit:
                continue
            sx1, sy1 = s.x + 8, s.y + 8
            sx2, sy2 = s.x + s.size - 8, s.y + s.size - 8
            px1, py1 = p.x + 12, p.y + 12
            px2, py2 = p.x + PLAYER_W - 12, p.y + PLAYER_H - 12
            if px2 > sx1 and px1 < sx2 and py2 > sy1 and py1 < sy2:
                s.hit = True
                self.lose_life()

    def draw_bg(self):
        bg = self.images["bg"]
        if bg:
            bg_scaled = pygame.transform.smoothscale(bg, (GAME_W, GAME_H))
            self.screen.blit(bg_scaled, (self.bg_x, 0))
            self.screen.blit(bg_scaled, (self.bg_x + GAME_W, 0))
        else:
            self.screen.fill((59, 130, 246))

    def draw_cloud(self, c: Cloud):
        if c.kind == "normal":
            key = "cloud_normal"
        elif c.kind == "storm":
            if c.storm_anim_time < 0:
                key = "cloud_storm"
            elif c.storm_anim_time < 0.2:
                key = "cloud_storm"
            elif c.storm_anim_time < 0.4:
                key = "cloud_storm_1"
            elif c.storm_anim_time < 0.6:
                key = "cloud_storm_2"
            else:
                key = "cloud_storm_3"
        else:
            key = "cloud_sugar"
        img = self.images[key]
        rect = pygame.Rect(int(c.x), int(c.y - 20), int(c.w), int(c.h + 40))
        if img:
            scaled = pygame.transform.smoothscale(img, (rect.w, rect.h))
            self.screen.blit(scaled, rect.topleft)
        else:
            color = (255, 255, 255) if c.kind == "normal" else (60, 60, 70) if c.kind == "storm" else (255, 170, 220)
            pygame.draw.ellipse(self.screen, color, rect)

    def draw_star(self, s: Star):
        if s.hit:
            return
        rect = pygame.Rect(int(s.x), int(s.y), int(s.size), int(s.size))
        img = self.images["star"]
        if img:
            scaled = pygame.transform.smoothscale(img, (rect.w, rect.h))
            self.screen.blit(scaled, rect.topleft)
        else:
            pygame.draw.circle(self.screen, (255, 230, 80), rect.center, rect.w // 2)

    def draw_player(self):
        flicker = self.invuln > 0 and int(self.invuln * 20) % 2 == 0
        if flicker:
            return
        rect = pygame.Rect(int(self.player.x), int(self.player.y), PLAYER_W, PLAYER_H)
        visual_scale = 1.12
        draw_w = int(PLAYER_W * visual_scale)
        draw_h = int(PLAYER_H * visual_scale)
        draw_x = rect.centerx - draw_w // 2
        draw_y = rect.bottom - draw_h
        draw_rect = pygame.Rect(draw_x, draw_y, draw_w, draw_h)
        if self.push_timer > 0:
            img = self.images["sheep_push"]
        elif self.player.on_cloud is None:
            img = self.images["sheep_jump"]
        else:
            img = self.images["sheep_idle"]
        if img:
            scaled = pygame.transform.smoothscale(img, (draw_rect.w, draw_rect.h))
            self.screen.blit(scaled, draw_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (245, 245, 245), draw_rect, border_radius=12)

    def draw_hud(self):
        # жизни
        for i in range(3):
            x = 18 + i * 34
            y = 14
            if self.images["heart"]:
                heart = pygame.transform.smoothscale(self.images["heart"], (26, 26))
                if i >= self.lives:
                    heart.set_alpha(80)
                self.screen.blit(heart, (x, y))
            else:
                color = (255, 80, 120) if i < self.lives else (90, 90, 100)
                pygame.draw.circle(self.screen, color, (x + 13, y + 13), 11)
        score_surf = self.font_mid.render(str(self.score), True, (255, 255, 255))
        speed_surf = self.font_small.render("x{:.1f}".format(self.speed), True, (255, 255, 255))
        self.screen.blit(score_surf, (GAME_W // 2 - score_surf.get_width() // 2, 12))
        self.screen.blit(speed_surf, (GAME_W - speed_surf.get_width() - 20, 18))

    def draw_overlay_text(self, lines):
        # затемнение
        shade = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        self.screen.blit(shade, (0, 0))
        y = GAME_H // 2 - 70
        for txt, kind in lines:
            font = self.font_big if kind == "big" else self.font_mid if kind == "mid" else self.font_small
            surf = font.render(txt, True, (255, 255, 255))
            self.screen.blit(surf, (GAME_W // 2 - surf.get_width() // 2, y))
            y += surf.get_height() + 14

    def draw(self):
        self.draw_bg()
        for c in self.clouds:
            self.draw_cloud(c)
        for s in self.stars:
            self.draw_star(s)
        self.draw_player()
        self.draw_hud()
        if not self.started:
            self.draw_overlay_text([
                ("Старт — Space для прыжка", "mid"),
                ("Esc / P — пауза", "small"),
            ])
        elif self.paused and not self.game_over:
            self.draw_overlay_text([
                ("Пауза", "big"),
                ("Space — прыжок, Esc/P — продолжить", "small"),
                ("R — начать заново", "small"),
            ])
        elif self.game_over:
            self.draw_overlay_text([
                ("Конец игры", "big"),
                ("Очки: {}".format(self.score), "mid"),
                ("R — играть снова", "small"),
            ])
        pygame.display.flip()
        
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    if not self.started:
                        self.started = True
                    elif not self.paused:
                        self.jump()
                elif e.key in (pygame.K_ESCAPE, pygame.K_p):
                    if self.started and not self.game_over:
                        self.paused = not self.paused
                elif e.key == pygame.K_r:
                    self.started = True
                    self.paused = False
                    self.game_over = False
                    self.reset()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.started and not self.paused:
                    self.jump()

    def run(self):
        while True:
            dt = min(0.05, self.clock.tick(60) / 1000.0)
            self.handle_events()
            if self.started and not self.paused and not self.game_over:
                self.update(dt)
            # синхронизация флага game_over с состоянием
            if self.finished:
                self.game_over = True
            self.draw()
if __name__ == "__main__":
    Game().run()