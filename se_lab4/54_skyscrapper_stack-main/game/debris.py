# ============================================================
# game/debris.py
# TASK 3: Falling, rotating off-cut debris animation
# ============================================================
import pygame


class Debris:
    def __init__(self, x, y, width, height, color, side):
        """
        side: -1 = overhang fell off the LEFT of the new block
              +1 = overhang fell off the RIGHT of the new block
        """
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.color = color
        self.vy = 0.0
        self.vx = side * 1.5     # horizontal drift in the fall direction
        self.angle = 0.0
        self.spin = side * 4.0   # degrees per frame
        self.alive = True

    def update(self, gravity=0.55, floor=None):
        self.vy += gravity
        self.y += self.vy
        self.x += self.vx
        self.angle += self.spin

        # Kill debris once it has fallen well below the screen
        if floor is not None and self.y > floor + 200:
            self.alive = False

    def render(self, surface):
        w = max(1, int(self.width))
        h = max(1, int(self.height))

        # Draw the debris rect on its own surface so we can rotate it
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, w, h), border_radius=4)
        pygame.draw.rect(surf, (245, 245, 250), (0, 0, w, h),
                         width=2, border_radius=4)

        rotated = pygame.transform.rotate(surf, self.angle)
        rect = rotated.get_rect(
            center=(int(self.x + w / 2), int(self.y + h / 2)))
        surface.blit(rotated, rect)
