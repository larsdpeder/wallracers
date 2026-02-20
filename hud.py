import pygame
from car import PLAYER_COLORS
from controls import PLAYER_KEYS


class HUD:
    def __init__(self):
        self.font_lg = None
        self.font_md = None
        self.font_sm = None
        self.font_xs = None
    def _init(self):
        if self.font_lg is None:
            self.font_lg = pygame.font.Font(None, 96)
            self.font_md = pygame.font.Font(None, 48)
            self.font_sm = pygame.font.Font(None, 32)
            self.font_xs = pygame.font.Font(None, 24)

    def render_race(self, surface, race):
        self._init()
        positions = race.get_positions()
        num = len(race.cars)
        spacing = min(420, (surface.get_width() - 200) // max(num, 1))
        # Top HUD panel
        panel = pygame.Surface((spacing * num + 60, 80), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        surface.blit(panel, (70, 5))
        for car in race.cars:
            color = PLAYER_COLORS[car.player_id % 4]
            pos_num = positions.index(car) + 1
            # Position badge near car
            badge = pygame.Surface((28, 22), pygame.SRCALPHA)
            badge.fill((*color, 180))
            lbl = self.font_xs.render(f"P{pos_num}", True, (255, 255, 255))
            badge.blit(lbl, lbl.get_rect(center=(14, 11)))
            surface.blit(badge, (int(car.pos[0]) + 24, int(car.pos[1]) - 22))
            # Top HUD
            hx = 90 + car.player_id * spacing
            # Player name + position
            pos_color = (255, 215, 0) if pos_num == 1 else color
            txt = self.font_sm.render(f"P{car.player_id+1}", True, pos_color)
            surface.blit(txt, (hx, 12))
            # Lap counter
            lap_display = min(car.lap + 1, 5)
            lap_txt = self.font_xs.render(f"Lap {lap_display}/5", True, (200, 200, 200))
            surface.blit(lap_txt, (hx + 40, 16))
            # Boost charges as filled/empty circles
            for b in range(3):
                bx = hx + b * 22
                by = 45
                if b < car.boost_charges:
                    pygame.draw.circle(surface, (80, 170, 255), (bx + 8, by + 8), 7)
                    pygame.draw.circle(surface, (140, 210, 255), (bx + 8, by + 8), 4)
                else:
                    pygame.draw.circle(surface, (60, 60, 70), (bx + 8, by + 8), 7, 1)
            # Boost active bar
            if car.boost_timer > 0:
                bar_w = int(70 * car.boost_timer / 2.5)
                pygame.draw.rect(surface, (255, 180, 30), (hx, 66, bar_w, 4), border_radius=2)
                pygame.draw.rect(surface, (255, 220, 100), (hx, 66, max(1, bar_w - 2), 2), border_radius=1)

    def render_countdown(self, surface, value):
        self._init()
        text = str(value) if value > 0 else "GO!"
        color = (255, 80, 80) if value > 0 else (80, 255, 80)
        surf = self.font_lg.render(text, True, color)
        rect = surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        shadow = self.font_lg.render(text, True, (0, 0, 0))
        surface.blit(shadow, (rect.x + 3, rect.y + 3))
        surface.blit(surf, rect)

    def render_finish(self, surface, race):
        self._init()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        winner = race.get_winner()
        if winner:
            color = PLAYER_COLORS[winner.player_id % 4]
            txt = self.font_lg.render(f"Player {winner.player_id+1} Wins!", True, color)
            rect = txt.get_rect(center=(surface.get_width() // 2, 180))
            surface.blit(txt, rect)
        cx = surface.get_width() // 2
        podium_x = [cx - 120, cx + 120, cx]
        podium_y = [340, 340, 420]
        podium_h = [180, 140, 100]
        for i, car in enumerate(race.finished_order[:3]):
            if i >= len(podium_x):
                break
            px, py, ph = podium_x[i], podium_y[i], podium_h[i]
            color = PLAYER_COLORS[car.player_id % 4]
            pygame.draw.rect(surface, color, (px - 50, py + 96 - ph, 100, ph))
            sprite = pygame.transform.scale(car.sprite, (80, 80))
            surface.blit(sprite, (px - 40, py))
            pos_txt = self.font_md.render(f"#{i+1}", True, (255, 255, 255))
            surface.blit(pos_txt, pos_txt.get_rect(center=(px, py + 96 + 20)))
        prompt = self.font_md.render("Press SPACE to race again", True, (200, 200, 200))
        surface.blit(prompt, prompt.get_rect(center=(cx, surface.get_height() - 80)))

    def render_track_select(self, surface, tracks, selected_idx):
        self._init()
        cx = surface.get_width() // 2
        title = self.font_lg.render("SELECT TRACK", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(cx, 80)))
        total = len(tracks)
        card_w, card_h = 300, 200
        gap = 30
        total_w = total * card_w + (total - 1) * gap
        start_x = cx - total_w // 2
        for i, track in enumerate(tracks):
            x = start_x + i * (card_w + gap)
            y = 200
            is_sel = i == selected_idx
            border_color = track.color if is_sel else (80, 80, 80)
            pygame.draw.rect(surface, (30, 30, 40), (x, y, card_w, card_h), border_radius=8)
            pygame.draw.rect(surface, border_color, (x, y, card_w, card_h), 3, border_radius=8)
            mini = track.render_mini((card_w - 20, card_h - 50))
            surface.blit(mini, (x + 10, y + 10))
            name_surf = self.font_sm.render(track.name, True, track.color if is_sel else (150, 150, 150))
            surface.blit(name_surf, name_surf.get_rect(center=(x + card_w // 2, y + card_h - 15)))
            if is_sel:
                arrow = self.font_md.render("^", True, track.color)
                surface.blit(arrow, arrow.get_rect(center=(x + card_w // 2, y + card_h + 25)))
        keys_text = "LEFT/RIGHT to browse  |  SPACE to race"
        prompt = self.font_md.render(keys_text, True, (200, 200, 200))
        surface.blit(prompt, prompt.get_rect(center=(cx, surface.get_height() - 80)))

    def render_player_select(self, surface, num_players):
        self._init()
        cx, cy = surface.get_width() // 2, surface.get_height() // 2
        # Game title
        title = self.font_lg.render("WALL RACERS", True, (255, 200, 50))
        surface.blit(title, title.get_rect(center=(cx, cy - 280)))
        # Question
        question = self.font_md.render("How many players?", True, (200, 200, 200))
        surface.blit(question, question.get_rect(center=(cx, cy - 160)))
        # Draw 1-4 as big selectable numbers
        for i in range(1, 5):
            x = cx + (i - 2.5) * 180
            y = cy - 30
            is_sel = i == num_players
            color = PLAYER_COLORS[(i - 1) % 4] if is_sel else (80, 80, 80)
            radius = 65 if is_sel else 55
            if is_sel:
                pygame.draw.circle(surface, color, (int(x), int(y)), radius)
                txt_color = (20, 20, 30)
            else:
                pygame.draw.circle(surface, color, (int(x), int(y)), radius, 3)
                txt_color = color
            num = self.font_lg.render(str(i), True, txt_color)
            surface.blit(num, num.get_rect(center=(int(x), int(y))))
            lbl = self.font_sm.render(f"{'player' if i == 1 else 'players'}", True, color)
            surface.blit(lbl, lbl.get_rect(center=(int(x), int(y) + 90)))
        # Controls preview for selected count
        key_names = {
            pygame.K_q: "Q", pygame.K_w: "W", pygame.K_e: "E",
            pygame.K_t: "T", pygame.K_y: "Y", pygame.K_u: "U",
            pygame.K_i: "I", pygame.K_o: "O", pygame.K_p: "P",
            pygame.K_LEFT: "LEFT", pygame.K_UP: "UP", pygame.K_RIGHT: "RIGHT",
        }
        controls_y = cy + 120
        for i in range(num_players):
            keys = PLAYER_KEYS[i]
            color = PLAYER_COLORS[i % 4]
            ln = key_names.get(keys["lane"], "?")
            bs = key_names.get(keys["boost"], "?")
            hk = key_names.get(keys["honk"], "?")
            txt = self.font_xs.render(f"P{i+1}: {ln} = Lane   {bs} = Boost   {hk} = Honk", True, color)
            surface.blit(txt, txt.get_rect(center=(cx, controls_y + i * 28)))
        prompt = self.font_md.render("LEFT/RIGHT to choose  |  SPACE to start", True, (255, 255, 255))
        surface.blit(prompt, prompt.get_rect(center=(cx, surface.get_height() - 80)))

    def render_processing(self, surface, player_id, snapshot_surf=None):
        self._init()
        cx = surface.get_width() // 2
        color = PLAYER_COLORS[player_id % 4]
        txt = self.font_lg.render(f"Player {player_id+1}", True, color)
        surface.blit(txt, txt.get_rect(center=(cx, 80)))
        # Show frozen snapshot with a "captured" overlay
        if snapshot_surf:
            rect = snapshot_surf.get_rect(center=(cx, surface.get_height() // 2 - 20))
            surface.blit(snapshot_surf, rect)
            # Dim overlay
            dim = pygame.Surface(snapshot_surf.get_size(), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 80))
            surface.blit(dim, rect)
            pygame.draw.rect(surface, color, rect, 3)
        # Spinning dots animation
        import time
        t = time.time()
        dots = "." * (int(t * 3) % 4)
        msg = self.font_md.render(f"Cutting out car{dots}", True, (255, 255, 255))
        surface.blit(msg, msg.get_rect(center=(cx, surface.get_height() - 120)))
        # Spinner
        import math
        spinner_cx, spinner_cy = cx, surface.get_height() - 60
        for i in range(8):
            angle = math.radians(i * 45 + t * 360)
            alpha = int(255 * ((i + int(t * 8)) % 8) / 8)
            sx = spinner_cx + math.cos(angle) * 18
            sy = spinner_cy + math.sin(angle) * 18
            size = 4 if (i + int(t * 8)) % 8 > 4 else 6
            c = tuple(min(255, int(v * alpha / 255)) for v in color)
            pygame.draw.circle(surface, c, (int(sx), int(sy)), size)

    def render_lobby(self, surface, num_players, car_sprites):
        self._init()
        cx, cy = surface.get_width() // 2, surface.get_height() // 2
        title = self.font_lg.render("WALL RACERS", True, (255, 200, 50))
        surface.blit(title, title.get_rect(center=(cx, 180)))
        subtitle = self.font_md.render("Place your car on the mat", True, (180, 180, 180))
        surface.blit(subtitle, subtitle.get_rect(center=(cx, 260)))
        for i in range(num_players):
            x = cx + (i - num_players / 2 + 0.5) * 220
            y = cy + 60
            color = PLAYER_COLORS[i % 4]
            pygame.draw.rect(surface, color, (int(x) - 50, int(y) - 50, 100, 100), 3)
            if i in car_sprites:
                spr = pygame.transform.scale(car_sprites[i], (80, 80))
                surface.blit(spr, (int(x) - 40, int(y) - 40))
            else:
                txt = self.font_md.render("?", True, color)
                surface.blit(txt, txt.get_rect(center=(int(x), int(y))))
            lbl = self.font_sm.render(f"Player {i+1}", True, color)
            surface.blit(lbl, lbl.get_rect(center=(int(x), int(y) + 70)))
        # Controls reference
        key_names = {
            pygame.K_q: "Q", pygame.K_w: "W", pygame.K_e: "E",
            pygame.K_t: "T", pygame.K_y: "Y", pygame.K_u: "U",
            pygame.K_i: "I", pygame.K_o: "O", pygame.K_p: "P",
            pygame.K_LEFT: "LEFT", pygame.K_UP: "UP", pygame.K_RIGHT: "RIGHT",
        }
        cy_controls = cy + 160
        for i in range(num_players):
            keys = PLAYER_KEYS[i]
            color = PLAYER_COLORS[i % 4]
            ln = key_names.get(keys["lane"], "?")
            bs = key_names.get(keys["boost"], "?")
            hk = key_names.get(keys["honk"], "?")
            txt = self.font_xs.render(f"P{i+1}: {ln}=Lane  {bs}=Boost  {hk}=Honk", True, color)
            surface.blit(txt, txt.get_rect(center=(cx, cy_controls + i * 28)))
        prompt = self.font_md.render("Press SPACE to start scanning", True, (255, 255, 255))
        surface.blit(prompt, prompt.get_rect(center=(cx, surface.get_height() - 80)))

    def render_scanning(self, surface, player_id, preview_surf=None):
        self._init()
        cx = surface.get_width() // 2
        color = PLAYER_COLORS[player_id % 4]
        txt = self.font_lg.render(f"Scan Player {player_id+1}'s Car", True, color)
        surface.blit(txt, txt.get_rect(center=(cx, 100)))
        if preview_surf:
            rect = preview_surf.get_rect(center=(cx, surface.get_height() // 2))
            surface.blit(preview_surf, rect)
            pygame.draw.rect(surface, color, rect, 3)
        else:
            msg = self.font_md.render("No webcam — using default car", True, (200, 150, 50))
            surface.blit(msg, msg.get_rect(center=(cx, surface.get_height() // 2)))
        hint = self.font_sm.render("Point nose DOWN  |  Hold car in the yellow box", True, (160, 160, 160))
        surface.blit(hint, hint.get_rect(center=(cx, surface.get_height() - 130)))
        prompt = self.font_md.render("Press SPACE to capture", True, (200, 200, 200))
        surface.blit(prompt, prompt.get_rect(center=(cx, surface.get_height() - 80)))
