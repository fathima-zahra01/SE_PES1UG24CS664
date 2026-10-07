# ============================================================
# game/game_engine.py
# Task 2 applied: Perfect Placement bonus + width restoration + popup
# Task 3 applied: Falling off-cut debris animation
# Task 4 applied: Atmospheric background shifting
# ============================================================
import random
import pygame
from game.block import Block
from game.debris import Debris

PERFECT_TOLERANCE = 6
PERFECT_BONUS = 2
MAX_BONUS = 10
STREAK_FOR_RESTORE = 2
WIDTH_RESTORE = 10
POPUP_FRAMES = 60

# ------------------------------------------------------------
# TASK 4: Atmospheric gradient stop definitions
# Each stop is (top_rgb, bottom_rgb). The tower's height
# (self.score) picks which pair is active and how far we
# interpolate toward the next pair.
# ------------------------------------------------------------
SKY_STOPS = [
    # score threshold, top color, bottom color
    (0,  (18,  22,  40), (55,  70, 110)),   # night / ground
    (6,  (70,  45,  95), (230, 130, 95)),   # dawn
    (14, (45, 120, 190), (185, 220, 255)),  # day
    (26, (150, 80, 140), (250, 170, 95)),   # dusk
    (40, (25,  25,  60), (75,  45, 110)),   # twilight
    (60, (8,    8,  24), (25,  15,  50)),   # deep space
]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        # TASK 4: pre-allocated gradient surface (re-rendered on height change)
        self._sky_surface = None
        self._sky_cache_key = None

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),
            (240, 140, 45),
            (245, 210, 50),
            (60, 195, 110),
            (50, 150, 240),
            (165, 80, 225),
        ]
        return palette[index % len(palette)]

    # ------------------------------------------------------------
    # TASK 2 + 3 + 4: reset()
    # ------------------------------------------------------------
    def reset(self):
        self.score = 0
        self.game_over = False
        self.bonus = 0
        self.perfect_streak = 0
        self.popup_text = ""
        self.popup_timer = 0
        self.popup_x = 0
        self.popup_y = 0

        # TASK 3
        self.debris = []

        # TASK 4: force gradient rebuild on reset
        self._sky_cache_key = None

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width,
                           self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width,
                                  self.block_height, color, speed=speed)

    # ------------------------------------------------------------
    # TASK 2 + 3: drop_block
    # ------------------------------------------------------------
    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        if overlap <= 0:
            self.game_over = True
            self.perfect_streak = 0
            self.popup_timer = 0
            return

        offset = abs(act.x - top_block.x)

        # TASK 2: PERFECT branch
        if offset <= PERFECT_TOLERANCE:
            self.perfect_streak += 1
            new_x = top_block.x
            new_w = top_block.width

            if self.perfect_streak >= STREAK_FOR_RESTORE:
                grow = min(WIDTH_RESTORE, self.base_width - new_w)
                if grow > 0:
                    new_x -= grow / 2
                    new_w += grow
                    new_x = max(20, min(new_x, self.width - 20 - new_w))

            bonus = min(MAX_BONUS, PERFECT_BONUS * self.perfect_streak)
            self.bonus += bonus
            self.popup_text = ("PERFECT!" if self.perfect_streak == 1
                               else f"PERFECT! x{self.perfect_streak}  +{bonus}")
            self.popup_timer = POPUP_FRAMES
        else:
            self.perfect_streak = 0
            new_x = left
            new_w = overlap

            # TASK 3: spawn debris for the trimmed overhang
            if act.x < new_x:
                self.debris.append(Debris(
                    act.x, act.y,
                    new_x - act.x, act.height,
                    act.color, side=-1))
            if act.x + act.width > new_x + new_w:
                self.debris.append(Debris(
                    new_x + new_w, act.y,
                    (act.x + act.width) - (new_x + new_w), act.height,
                    act.color, side=+1))

        new_block = Block(new_x, act.y, new_w, self.block_height,
                          act.color, speed=0)
        self.stack.append(new_block)
        self.score += 1

        if new_block.y < 180:
            shift_amount = self.block_height + 4
            for b in self.stack:
                b.y += shift_amount
            for d in self.debris:
                d.y += shift_amount

        self.popup_x = new_block.x + new_block.width / 2
        self.popup_y = new_block.y - 10

        self.spawn_active_block()

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_r) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    # ------------------------------------------------------------
    # TASK 2 + 3: update()
    # ------------------------------------------------------------
    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        if self.popup_timer > 0:
            self.popup_timer -= 1

        for d in self.debris:
            d.update(gravity=0.55, floor=self.height)
        self.debris = [d for d in self.debris if d.alive]

    # ------------------------------------------------------------
    # TASK 4: atmospheric background helpers
    # ------------------------------------------------------------
    def _sky_targets(self):
        """Return the (top_rgb, bottom_rgb) for the current score."""
        score = self.score
        # Find surrounding stops by threshold
        prev = SKY_STOPS[0]
        for i, stop in enumerate(SKY_STOPS):
            thresh, top, bottom = stop
            if score < thresh:
                # interpolate between prev and this stop
                prev_thresh, prev_top, prev_bottom = prev
                span = max(1, thresh - prev_thresh)
                t = (score - prev_thresh) / span
                t = max(0.0, min(1.0, t))
                top_c = tuple(int(prev_top[k] + (top[k] - prev_top[k]) * t)
                              for k in range(3))
                bot_c = tuple(int(prev_bottom[k] + (bottom[k] - prev_bottom[k]) * t)
                              for k in range(3))
                return top_c, bot_c
            prev = stop
        # Beyond the last stop -> clamp to the last
        return SKY_STOPS[-1][1], SKY_STOPS[-1][2]

    def _build_sky_surface(self, top_color, bottom_color):
        """Draw a vertical gradient onto a new surface."""
        surf = pygame.Surface((self.width, self.height))
        h = self.height
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    def _draw_sky(self, screen):
        """Cache and blit the gradient; rebuild only when it changes."""
        top_c, bot_c = self._sky_targets()
        key = (top_c, bot_c, self.width, self.height)
        if key != self._sky_cache_key:
            self._sky_surface = self._build_sky_surface(top_c, bot_c)
            self._sky_cache_key = key
        screen.blit(self._sky_surface, (0, 0))

    # ------------------------------------------------------------
    # TASK 2 + 3 + 4: render()
    # ------------------------------------------------------------
    def render(self, screen):
        # TASK 4: gradient background replaces the flat fill
        self._draw_sky(screen)

        title_surf = self.font_title.render("Skyscraper Stack", True,
                                            (245, 245, 245))
        screen.blit(title_surf,
                    (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(
            f"Height: {self.score}    Bonus: {self.bonus}",
            True, (255, 220, 80))
        screen.blit(score_surf,
                    (self.width // 2 - score_surf.get_width() // 2, 54))

        for b in self.stack:
            b.render(screen)

        for d in self.debris:
            d.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

            if self.popup_timer > 0 and self.popup_text:
                age = POPUP_FRAMES - self.popup_timer
                alpha = max(0, min(255,
                            int(255 * self.popup_timer / POPUP_FRAMES)))
                surf = self.font_hud.render(self.popup_text, True,
                                            (255, 235, 90))
                surf.set_alpha(alpha)
                screen.blit(surf,
                            (self.popup_x - surf.get_width() // 2,
                             self.popup_y - age * 0.8))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True,
                                             (240, 75, 75))
            screen.blit(over_surf,
                        (self.width // 2 - over_surf.get_width() // 2,
                         self.height // 2 - 40))

            final_surf = self.font_hud.render(
                f"Final Height: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf,
                        (self.width // 2 - final_surf.get_width() // 2,
                         self.height // 2 + 10))

            restart_surf = self.font_hud.render(
                "Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf,
                        (self.width // 2 - restart_surf.get_width() // 2,
                         self.height // 2 + 50))
