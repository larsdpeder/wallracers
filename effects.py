import pygame
import random
import math


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, vx, vy, life, color, size=3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_boost(self, x, y, angle_deg):
        rad = math.radians(angle_deg + 90)
        for _ in range(3):
            spread = random.uniform(-0.5, 0.5)
            speed = random.uniform(1.5, 3.5)
            vx = math.cos(rad + spread) * speed
            vy = math.sin(rad + spread) * speed
            color = random.choice([
                (255, 200, 50), (255, 150, 30), (255, 100, 20), (255, 255, 100)
            ])
            self.particles.append(Particle(x, y, vx, vy, random.uniform(0.2, 0.5), color, random.randint(2, 5)))

    def emit_oil_hit(self, x, y):
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.3, 0.6),
                random.choice([(60, 40, 20), (80, 60, 30), (40, 30, 15)]),
                random.randint(2, 4),
            ))

    def emit_pickup(self, x, y, color):
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.2, 0.5),
                color,
                random.randint(2, 4),
            ))

    def emit_finish(self, x, y):
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            color = random.choice([
                (255, 215, 0), (255, 255, 255), (255, 100, 100),
                (100, 200, 255), (100, 255, 100),
            ])
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.5, 1.5),
                color,
                random.randint(3, 6),
            ))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx
                p.y += p.vy
                p.vy += 0.5 * dt  # slight gravity
                alive.append(p)
        self.particles = alive

    def render(self, surface):
        for p in self.particles:
            alpha = p.life / p.max_life
            size = max(1, int(p.size * alpha))
            color = tuple(int(c * alpha) for c in p.color)
            pygame.draw.circle(surface, color, (int(p.x), int(p.y)), size)
