import math
import os
import random
import pygame
import numpy as np

PLAYER_COLORS = [(255, 50, 50), (50, 100, 255), (50, 255, 50), (255, 200, 50)]

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")
_CAR_FILES = ["car_red.png", "car_blue.png", "car_green.png", "car_orange.png"]


class Car:
    def __init__(self, player_id, track, sprite=None):
        self.player_id = player_id
        self.track = track
        self.lane = 1
        self.waypoint_idx = player_id * 20
        self.base_speed = 3.0 + random.uniform(-0.15, 0.15)
        self.speed = self.base_speed
        self.boost_charges = 0
        self.boost_timer = 0.0
        self.slow_timer = 0.0
        self.has_shield = False
        self.lap = 0
        self.finished = False
        self.finish_time = None
        self.sprite = sprite or _default_sprite(player_id)
        pos = track.lanes[self.lane][self.waypoint_idx % track.num_waypoints]
        self.pos = [pos[0], pos[1]]
        self.angle = 0.0

    def update(self, dt):
        if self.finished:
            return
        if self.boost_timer > 0:
            self.boost_timer = max(0, self.boost_timer - dt)
            self.speed = self.base_speed * 2.0
        elif self.slow_timer > 0:
            self.slow_timer = max(0, self.slow_timer - dt)
            self.speed = self.base_speed * 0.5
        else:
            self.speed = self.base_speed

        lane = self.track.lanes[self.lane]
        n = self.track.num_waypoints
        remaining = self.speed * dt * 60

        while remaining > 0.01:
            next_idx = (self.waypoint_idx + 1) % n
            tx, ty = lane[next_idx]
            dx, dy = tx - self.pos[0], ty - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist < 0.01:
                self.waypoint_idx = next_idx
                continue
            if dist <= remaining:
                self.pos[0], self.pos[1] = tx, ty
                old = self.waypoint_idx
                self.waypoint_idx = next_idx
                remaining -= dist
                if next_idx < old:
                    self.lap += 1
            else:
                frac = remaining / dist
                self.pos[0] += dx * frac
                self.pos[1] += dy * frac
                remaining = 0

        nxt = lane[(self.waypoint_idx + 1) % n]
        self.angle = math.degrees(math.atan2(-(nxt[1] - self.pos[1]), nxt[0] - self.pos[0])) - 90

    def switch_lane(self):
        self.lane = (self.lane + 1) % 3

    def activate_boost(self):
        if self.boost_charges > 0 and self.boost_timer <= 0:
            self.boost_charges -= 1
            self.boost_timer = 2.5
            return True
        return False

    def render(self, surface):
        rotated = pygame.transform.rotate(self.sprite, self.angle)
        rect = rotated.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        # Shadow under car
        shadow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 5, 40, 30))
        sh_rot = pygame.transform.rotate(shadow, self.angle)
        sh_rect = sh_rot.get_rect(center=(int(self.pos[0]) + 2, int(self.pos[1]) + 2))
        surface.blit(sh_rot, sh_rect)
        surface.blit(rotated, rect)
        if self.boost_timer > 0:
            # Glowing boost trail
            n = self.track.num_waypoints
            for j in range(1, 6):
                idx = (self.waypoint_idx - j * 3) % n
                pt = self.track.lanes[self.lane][idx]
                alpha = max(0, 200 - j * 40)
                r = max(1, 6 - j)
                glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 200, 50, alpha), (r * 2, r * 2), r * 2)
                surface.blit(glow, (int(pt[0]) - r * 2, int(pt[1]) - r * 2))
        if self.has_shield:
            # Animated shield glow
            glow = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 140, 255, 80), (35, 35), 32)
            pygame.draw.circle(glow, (120, 180, 255, 50), (35, 35), 28)
            surface.blit(glow, (int(self.pos[0]) - 35, int(self.pos[1]) - 35))
            pygame.draw.circle(surface, (150, 200, 255), (int(self.pos[0]), int(self.pos[1])), 30, 2)
        if self.slow_timer > 0:
            # Oil splat visual on car
            glow = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 60, 20, 100), (25, 25), 20)
            surface.blit(glow, (int(self.pos[0]) - 25, int(self.pos[1]) - 25))


def _default_sprite(pid):
    """Load car sprite from assets, fall back to simple drawn sprite."""
    path = os.path.join(_ASSET_DIR, _CAR_FILES[pid % len(_CAR_FILES)])
    if os.path.exists(path):
        try:
            from PIL import Image as PILImage
            pil = PILImage.open(path).convert("RGBA")
            arr = np.array(pil)
            size = arr.shape[0]
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            px = pygame.surfarray.pixels3d(surf)
            al = pygame.surfarray.pixels_alpha(surf)
            px[:] = np.transpose(arr[:, :, :3], (1, 0, 2))
            al[:] = np.transpose(arr[:, :, 3])
            del px, al
            return surf
        except Exception:
            pass
    # Fallback: simple colored car shape
    color = PLAYER_COLORS[pid % 4]
    dark = tuple(max(0, c - 70) for c in color)
    surf = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.polygon(surf, dark, [(16, 6), (32, 6), (30, 18), (18, 18)])
    pygame.draw.rect(surf, color, (11, 16, 26, 14), border_radius=2)
    pygame.draw.polygon(surf, color, [(20, 30), (28, 30), (26, 40), (22, 40)])
    pygame.draw.rect(surf, (190, 190, 190), (9, 42, 30, 3))
    pygame.draw.rect(surf, (190, 190, 190), (8, 3, 32, 3))
    for wx, wy in [(8, 11), (35, 11), (8, 33), (35, 33)]:
        pygame.draw.rect(surf, (20, 20, 20), (wx, wy, 6, 10), border_radius=1)
    return surf
