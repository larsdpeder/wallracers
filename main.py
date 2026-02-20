import os
import pygame
import sys
from enum import Enum

from controls import PLAYER_KEYS, SCAN_KEY, WIDTH, HEIGHT, FPS
from track import Track, TRACK_NAMES
from car import Car, PLAYER_COLORS
from scanner import Scanner
from items import create_track_items
from race import RaceManager
from hud import HUD
from sounds import SoundManager
from effects import ParticleSystem


class State(Enum):
    PLAYER_SELECT = 0
    SCANNING = 1
    PROCESSING = 2
    TRACK_SELECT = 3
    COUNTDOWN = 4
    RACING = 5
    FINISH = 6


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Wall Racers")
        self.clock = pygame.time.Clock()
        self.sfx = SoundManager()
        self.sfx.init()
        self.state = State.PLAYER_SELECT
        self.hud = HUD()
        self.scanner = Scanner()
        self.particles = ParticleSystem()
        self.cars = []
        self.items = []
        self.race = None
        self.track = None
        self.car_sprites = {}
        self.scan_player = 0
        self.countdown_timer = 0.0
        self.countdown_value = 3
        self.preview_surf = None
        self.num_players = 2
        self.all_tracks = [Track(name) for name in TRACK_NAMES]
        self.selected_track_idx = 0
        self.honk_timers = {}
        self.finish_fireworks_timer = 0.0

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._quit()
                    elif event.key == pygame.K_F12:
                        self._screenshot()
                    else:
                        self._handle_key(event.key)
            self._update(dt)
            self._render()
            pygame.display.flip()

    def _screenshot(self):
        shots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(shots_dir, exist_ok=True)
        existing = [f for f in os.listdir(shots_dir) if f.endswith(".png")]
        num = len(existing) + 1
        path = os.path.join(shots_dir, f"screenshot_{num:03d}.png")
        pygame.image.save(self.screen, path)

    def _quit(self):
        self.scanner.close()
        pygame.quit()
        sys.exit()

    def _handle_key(self, key):
        if self.state == State.PLAYER_SELECT:
            if key in (pygame.K_LEFT, pygame.K_a):
                self.num_players = max(1, self.num_players - 1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.num_players = min(4, self.num_players + 1)
            elif key == SCAN_KEY:
                self.scan_player = 0
                self.car_sprites.clear()
                self.state = State.SCANNING
                self.scanner.open()

        elif self.state == State.SCANNING:
            if key == SCAN_KEY:
                if self.scanner.start_capture():
                    self.sfx.play("pickup")
                    self.state = State.PROCESSING

        elif self.state == State.TRACK_SELECT:
            if key in (pygame.K_LEFT, pygame.K_a):
                self.selected_track_idx = (self.selected_track_idx - 1) % len(self.all_tracks)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_track_idx = (self.selected_track_idx + 1) % len(self.all_tracks)
            elif key == SCAN_KEY:
                self._start_race()

        elif self.state == State.RACING:
            for pid in range(self.num_players):
                keys = PLAYER_KEYS[pid]
                if key == keys["lane"]:
                    self.cars[pid].switch_lane()
                    self.sfx.play("lane_switch")
                elif key == keys["boost"]:
                    if self.cars[pid].activate_boost():
                        self.sfx.play("boost")
                        self.sfx.play("engine_rev")
                elif key == keys["honk"]:
                    self._honk(pid)

        elif self.state == State.FINISH:
            if key == SCAN_KEY:
                self.state = State.PLAYER_SELECT

    def _honk(self, pid):
        self.sfx.play(f"honk_{pid}")
        self.honk_timers[pid] = 0.5

    def _start_race(self):
        self.track = self.all_tracks[self.selected_track_idx]
        self.track._surface = None
        self.cars = []
        for i in range(self.num_players):
            sprite = self.car_sprites.get(i)
            self.cars.append(Car(i, self.track, sprite))
        self.items = create_track_items(self.track)
        self.race = RaceManager(self.cars, self.track)
        self.honk_timers.clear()
        self.particles = ParticleSystem()
        self.state = State.COUNTDOWN
        self.countdown_timer = 0.0
        self.countdown_value = 3
        self.finish_fireworks_timer = 0.0

    def _update(self, dt):
        for pid in list(self.honk_timers):
            self.honk_timers[pid] -= dt
            if self.honk_timers[pid] <= 0:
                del self.honk_timers[pid]

        self.particles.update(dt)

        if self.state == State.SCANNING:
            self.preview_surf = self.scanner.get_preview_surface()

        elif self.state == State.PROCESSING:
            done, sprite = self.scanner.collect_result()
            if done:
                if sprite:
                    self.car_sprites[self.scan_player] = sprite
                self.scan_player += 1
                if self.scan_player >= self.num_players:
                    self.scanner.close()
                    self.state = State.TRACK_SELECT
                else:
                    self.state = State.SCANNING

        elif self.state == State.COUNTDOWN:
            self.countdown_timer += dt
            if self.countdown_timer >= 1.0:
                self.countdown_timer -= 1.0
                self.countdown_value -= 1
                if self.countdown_value > 0:
                    self.sfx.play("countdown")
                elif self.countdown_value == 0:
                    self.sfx.play("go")
                elif self.countdown_value < 0:
                    self.state = State.RACING
                    self.race.started = True
                    self.sfx.start_engine()

        elif self.state == State.RACING:
            for car in self.cars:
                car.update(dt)
                if car.boost_timer > 0:
                    self.particles.emit_boost(car.pos[0], car.pos[1], car.angle)
            for item in self.items:
                item.update(dt)
                for car in self.cars:
                    if item.check_collision(car):
                        if item.item_type in ("boost_pickup", "mystery_box"):
                            self.sfx.play("pickup")
                            self.particles.emit_pickup(
                                item.pos[0], item.pos[1],
                                (80, 170, 255) if item.item_type == "boost_pickup" else (255, 120, 255),
                            )
                        elif item.item_type == "oil_slick":
                            self.sfx.play("oil")
                            self.particles.emit_oil_hit(car.pos[0], car.pos[1])
            self.race.update(dt)
            if self.race.is_finished():
                self.sfx.stop_engine()
                self.sfx.play("finish")
                winner = self.race.get_winner()
                if winner:
                    self.particles.emit_finish(winner.pos[0], winner.pos[1])
                self.state = State.FINISH

        elif self.state == State.FINISH:
            self.finish_fireworks_timer += dt
            if self.finish_fireworks_timer > 0.4:
                self.finish_fireworks_timer = 0.0
                import random
                self.particles.emit_finish(
                    random.randint(WIDTH // 4, WIDTH * 3 // 4),
                    random.randint(HEIGHT // 4, HEIGHT // 2),
                )

    def _render(self):
        self.screen.fill((26, 26, 46))

        if self.state == State.PLAYER_SELECT:
            self.hud.render_player_select(self.screen, self.num_players)

        elif self.state == State.SCANNING:
            self.hud.render_scanning(self.screen, self.scan_player, self.preview_surf)

        elif self.state == State.PROCESSING:
            self.hud.render_processing(self.screen, self.scan_player, self.scanner.snapshot_surf)

        elif self.state == State.TRACK_SELECT:
            self.hud.render_track_select(self.screen, self.all_tracks, self.selected_track_idx)

        elif self.state == State.COUNTDOWN:
            self.track.render(self.screen)
            for item in self.items:
                item.render(self.screen)
            for car in self.cars:
                car.render(self.screen)
            self.hud.render_countdown(self.screen, self.countdown_value)

        elif self.state == State.RACING:
            self.track.render(self.screen)
            for item in self.items:
                item.render(self.screen)
            for car in self.cars:
                car.render(self.screen)
            self.particles.render(self.screen)
            self._render_honks()
            self.hud.render_race(self.screen, self.race)

        elif self.state == State.FINISH:
            self.track.render(self.screen)
            for car in self.cars:
                car.render(self.screen)
            self.particles.render(self.screen)
            self.hud.render_finish(self.screen, self.race)

    def _render_honks(self):
        for pid, timer in self.honk_timers.items():
            if pid < len(self.cars):
                car = self.cars[pid]
                color = PLAYER_COLORS[pid % 4]
                cx, cy = int(car.pos[0]), int(car.pos[1])
                # Expanding ring with fade
                progress = 1.0 - (timer / 0.5)
                radius = int(25 + progress * 35)
                alpha = int(200 * (timer / 0.5))
                ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring, (*color, alpha), (radius + 2, radius + 2), radius, 3)
                self.screen.blit(ring, (cx - radius - 2, cy - radius - 2))
                if timer > 0.2:
                    font = pygame.font.Font(None, 28)
                    txt = font.render("HONK!", True, color)
                    self.screen.blit(txt, txt.get_rect(center=(cx, cy - 45)))


if __name__ == "__main__":
    Game().run()
