# ============================================================
# game/game_engine.py
# Task 2 applied: Perfect Placement bonus + width restoration + popup
# Task 3 applied: Falling off-cut debris animation
# ============================================================
import random
import pygame
from game.block import Block
from game.debris import Debris        # TASK 3

PERFECT_TOLERANCE = 6      # px offset still counted as perfect
PERFECT_BONUS = 2
MAX_BONUS = 10
STREAK_FOR_RESTORE = 2     # perfects in a row before width is restored
WIDTH_RESTORE = 10
POPUP_FRAMES = 60


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    # ------------------------------------------------------------
    # TASK 2 + TASK 3: reset() clears perfect/popup state AND debris
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

        # TASK 3: fresh debris list each round
        self.debris = []

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
    # TASK 2 + TASK 3: drop_block now spawns debris on trim
    # ------------------------------------------------------------
    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        if overlap <= 0:                      # complete miss
            self.game_over = True
            self.perfect_streak = 0
            self.popup_timer = 0
            return

        offset = abs(act.x - top_block.x)

        # ---------------- TASK 2: PERFECT branch ----------------
        if offset <= PERFECT_TOLERANCE:       # snap, no trimming
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

        # ---------------- Normal trim branch ----------------
        else:
            self.perfect_streak = 0
            new_x = left
            new_w = overlap

            # ---- TASK 3: spawn debris for the trimmed-off overhang ----
            # Left overhang (the part of the active block left of new_x)
            if act.x < new_x:
                self.debris.append(Debris(
                    act.x, act.y,
                    new_x - act.x, act.height,
                    act.color, side=-1
                ))

            # Right overhang (the part right of new_x + new_w)
            if act.x + act.width > new_x + new_w:
                self.debris.append(Debris(
                    new_x + new_w, act.y,
                    (act.x + act.width) - (new_x + new_w), act.height,
                    act.color, side=+1
                ))

        new_block = Block(new_x, act.y, new_w, self.block_height,
                          act.color, speed=0)
        self.stack.append(new_block)
        self.score += 1

        # Camera scroll
        if new_block.y < 180:
            shift_amount = self.block_height + 4
            for b in self.stack:
                b.y += shift_amount
            # TASK 3: scroll active debris with the camera too
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
    # TASK 2 + TASK 3: update() ticks popup AND advances debris
    # ------------------------------------------------------------
    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        # TASK 2: popup timer
        if self.popup_timer > 0:
            self.popup_timer -= 1

        # TASK 3: gravity + culling for debris
        for d in self.debris:
            d.update(gravity=0.55, floor=self.height)
        self.debris = [d for d in self.debris if d.alive]

    # ------------------------------------------------------------
    # TASK 2 + TASK 3: render() draws stack, debris, active, popup
    # ------------------------------------------------------------
    def render(self, screen):
        screen.fill((24, 27, 36))

        title_surf = self.font_title.render("Skyscraper Stack", True,
                                            (245, 245, 245))
        screen.blit(title_surf,
                    (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(
            f"Height: {self.score}    Bonus: {self.bonus}",
            True, (255, 220, 80))
        screen.blit(score_surf,
                    (self.width // 2 - score_surf.get_width() // 2, 54))

        # Stack blocks
        for b in self.stack:
            b.render(screen)

        # TASK 3: debris renders behind the active block
        for d in self.debris:
            d.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

            # TASK 2: popup with fade
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
