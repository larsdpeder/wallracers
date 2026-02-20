import math
import random
import pygame


class Item:
    def __init__(self, track, waypoint_idx, lane, item_type):
        self.track = track
        self.waypoint_idx = waypoint_idx
        self.lane = lane
        self.item_type = item_type
        self.active = True
        self.respawn_timer = 0.0
        pos = track.lanes[lane][waypoint_idx]
        self.pos = (pos[0], pos[1])
        self.radius = 16

    def update(self, dt):
        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.active = True

    def check_collision(self, car):
        if not self.active:
            return False
        if math.hypot(car.pos[0] - self.pos[0], car.pos[1] - self.pos[1]) < self.radius + 20:
            self._apply(car)
            if self.item_type != "boost_pad":
                self.active = False
                self.respawn_timer = 5.0
            return True
        return False

    def _apply(self, car):
        if self.item_type == "boost_pad":
            car.boost_timer = max(car.boost_timer, 0.5)
        elif self.item_type == "boost_pickup":
            car.boost_charges = min(car.boost_charges + 1, 3)
        elif self.item_type == "oil_slick":
            if car.has_shield:
                car.has_shield = False
            else:
                car.slow_timer = 2.0
        elif self.item_type == "mystery_box":
            effect = random.choice(["shield", "speed_burst", "boost_pickup"])
            if effect == "shield":
                car.has_shield = True
            elif effect == "speed_burst":
                car.boost_timer = max(car.boost_timer, 1.5)
            elif effect == "boost_pickup":
                car.boost_charges = min(car.boost_charges + 1, 3)

    def render(self, surface):
        if not self.active:
            return
        x, y = int(self.pos[0]), int(self.pos[1])
        if self.item_type == "boost_pad":
            # Glowing arrows on track
            glow = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 200, 50, 40), (16, 16), 14)
            surface.blit(glow, (x - 16, y - 16))
            pygame.draw.polygon(surface, (255, 200, 50), [
                (x, y - 12), (x - 9, y + 5), (x + 9, y + 5)])
            pygame.draw.polygon(surface, (255, 240, 130), [
                (x, y - 6), (x - 5, y + 2), (x + 5, y + 2)])
        elif self.item_type == "boost_pickup":
            # Lightning bolt with glow
            glow = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow, (50, 120, 255, 50), (18, 18), 16)
            surface.blit(glow, (x - 18, y - 18))
            pygame.draw.polygon(surface, (80, 170, 255), [
                (x - 3, y - 13), (x + 7, y - 2), (x + 1, y - 2),
                (x + 3, y + 13), (x - 7, y + 2), (x - 1, y + 2)])
            pygame.draw.polygon(surface, (160, 210, 255), [
                (x - 1, y - 9), (x + 4, y - 2), (x + 1, y - 2),
                (x + 1, y + 9), (x - 4, y + 2), (x - 1, y + 2)])
        elif self.item_type == "oil_slick":
            # Dark iridescent puddle
            pygame.draw.ellipse(surface, (30, 20, 15), (x - 16, y - 10, 32, 20))
            pygame.draw.ellipse(surface, (50, 35, 25), (x - 11, y - 7, 22, 14))
            pygame.draw.ellipse(surface, (40, 50, 60), (x - 5, y - 3, 10, 6))
        elif self.item_type == "mystery_box":
            # Spinning/glowing mystery box
            glow = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 80, 255, 45), (18, 18), 16)
            surface.blit(glow, (x - 18, y - 18))
            pygame.draw.rect(surface, (200, 60, 200), (x - 11, y - 11, 22, 22), border_radius=4)
            pygame.draw.rect(surface, (255, 120, 255), (x - 9, y - 9, 18, 18), border_radius=3)
            pygame.draw.rect(surface, (220, 80, 220), (x - 9, y - 9, 18, 18), 2, border_radius=3)
            font = pygame.font.Font(None, 22)
            txt = font.render("?", True, (255, 255, 255))
            surface.blit(txt, txt.get_rect(center=(x, y)))


def create_track_items(track):
    items = []
    n = track.num_waypoints
    spacing = n // 14
    for i in range(3):
        idx = int(n * (i + 0.5) / 3)
        items.append(Item(track, idx, 1, "boost_pad"))
    for i in range(5):
        idx = (spacing * (i * 3 + 1)) % n
        items.append(Item(track, idx, random.choice([0, 1, 2]), "boost_pickup"))
    for i in range(4):
        idx = (spacing * (i * 3 + 2)) % n
        items.append(Item(track, idx, random.choice([0, 2]), "oil_slick"))
    for i in range(3):
        idx = (spacing * (i * 4 + 3)) % n
        items.append(Item(track, idx, random.choice([0, 1, 2]), "mystery_box"))
    return items
