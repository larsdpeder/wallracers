import math
import pygame

LANE_WIDTH = 40
TRACK_WIDTH = LANE_WIDTH * 3 + 20
NUM_WAYPOINTS = 600

TRACKS = {
    "Monaco": {
        "controls": [
            (960, 860), (1200, 870), (1400, 830), (1550, 720),
            (1620, 550), (1600, 380), (1500, 250), (1350, 180),
            (1200, 170), (1100, 230), (1080, 340), (1150, 430),
            (1100, 520), (950, 500), (780, 470), (620, 490),
            (480, 550), (400, 660), (380, 780), (430, 870),
            (600, 890), (780, 875),
        ],
        "color": (255, 200, 50),
        "bg": (26, 26, 46),
        "tarmac": (55, 55, 65),
    },
    "Monza": {
        "controls": [
            (400, 800), (700, 820), (1050, 830), (1400, 810),
            (1600, 750), (1680, 620), (1620, 500), (1450, 480),
            (1350, 520), (1250, 480), (1150, 440), (1050, 480),
            (900, 460), (700, 430), (500, 400), (350, 350),
            (280, 280), (320, 200), (450, 180), (650, 200),
            (850, 240), (1050, 260), (1250, 240), (1400, 200),
            (1500, 250), (1480, 350), (1350, 380), (1100, 360),
            (800, 340), (550, 360), (350, 440), (300, 560),
            (310, 680), (350, 770),
        ],
        "color": (50, 200, 50),
        "bg": (20, 35, 20),
        "tarmac": (50, 55, 50),
    },
    "Spa": {
        "controls": [
            (500, 850), (750, 860), (1000, 840), (1200, 780),
            (1350, 680), (1400, 550), (1380, 420), (1450, 300),
            (1550, 220), (1650, 180), (1700, 250), (1680, 380),
            (1600, 480), (1500, 550), (1400, 640), (1250, 700),
            (1100, 680), (1000, 600), (900, 500), (800, 380),
            (700, 300), (580, 260), (450, 280), (350, 340),
            (300, 440), (320, 560), (380, 680), (430, 780),
        ],
        "color": (255, 100, 100),
        "bg": (30, 26, 20),
        "tarmac": (60, 55, 50),
    },
    "Silverstone": {
        "controls": [
            (700, 850), (950, 870), (1200, 850), (1400, 790),
            (1550, 700), (1620, 570), (1600, 440), (1500, 340),
            (1380, 280), (1250, 250), (1100, 260), (980, 310),
            (880, 380), (800, 320), (700, 250), (580, 220),
            (450, 240), (350, 310), (310, 420), (340, 540),
            (400, 630), (350, 720), (320, 800), (400, 860),
            (550, 870),
        ],
        "color": (100, 150, 255),
        "bg": (20, 25, 35),
        "tarmac": (50, 52, 60),
    },
    "Suzuka": {
        "controls": [
            (960, 880), (1200, 870), (1400, 820), (1530, 720),
            (1580, 580), (1550, 440), (1450, 340), (1300, 280),
            (1150, 260), (1050, 300), (980, 380), (920, 460),
            (840, 400), (760, 320), (660, 260), (540, 230),
            (420, 260), (340, 340), (310, 450), (340, 570),
            (420, 660), (530, 720), (650, 750), (780, 770),
            (880, 810), (900, 860),
        ],
        "color": (255, 150, 200),
        "bg": (30, 20, 28),
        "tarmac": (58, 50, 55),
    },
}

TRACK_NAMES = list(TRACKS.keys())


class Track:
    def __init__(self, name=None, control_points=None):
        if name and name in TRACKS:
            cfg = TRACKS[name]
            controls = cfg["controls"]
            self.color = cfg["color"]
            self.bg_color = cfg["bg"]
            self.tarmac_color = cfg["tarmac"]
            self.name = name
        else:
            controls = control_points or TRACKS["Monaco"]["controls"]
            self.color = (255, 200, 50)
            self.bg_color = (26, 26, 46)
            self.tarmac_color = (55, 55, 65)
            self.name = name or "Monaco"
        smooth = _chaikin(controls, iterations=5)
        self.centerline = _evenly_space(smooth, NUM_WAYPOINTS)
        self.normals = _compute_normals(self.centerline)
        self.lanes = [
            _offset_lane(self.centerline, self.normals, -LANE_WIDTH),
            list(self.centerline),
            _offset_lane(self.centerline, self.normals, LANE_WIDTH),
        ]
        self.num_waypoints = len(self.centerline)
        self.start_index = 0
        self._surface = None

    def render(self, surface):
        if self._surface is None:
            self._build_surface(surface.get_size())
        surface.blit(self._surface, (0, 0))

    def _build_surface(self, size):
        self._surface = pygame.Surface(size)
        self._surface.fill(self.bg_color)
        half = int(TRACK_WIDTH // 2)
        # Layer 1: Grass/runoff area (wide green border)
        grass_color = (35, 85, 35)
        for i in range(self.num_waypoints):
            pos = (int(self.centerline[i][0]), int(self.centerline[i][1]))
            pygame.draw.circle(self._surface, grass_color, pos, half + 25)
        # Layer 2: Gravel trap (sandy border)
        gravel = (120, 110, 80)
        for i in range(self.num_waypoints):
            pos = (int(self.centerline[i][0]), int(self.centerline[i][1]))
            pygame.draw.circle(self._surface, gravel, pos, half + 12)
        # Layer 3: Kerb — alternating red/white
        for i in range(self.num_waypoints):
            pos = (int(self.centerline[i][0]), int(self.centerline[i][1]))
            color = (210, 40, 40) if (i // 5) % 2 == 0 else (240, 240, 240)
            pygame.draw.circle(self._surface, color, pos, half + 5)
        # Layer 4: Track tarmac
        for i in range(self.num_waypoints):
            pos = (int(self.centerline[i][0]), int(self.centerline[i][1]))
            pygame.draw.circle(self._surface, self.tarmac_color, pos, half)
        # Layer 5: Subtle tarmac texture — darker center strip
        dark_tarmac = tuple(max(0, c - 8) for c in self.tarmac_color)
        for i in range(self.num_waypoints):
            pos = (int(self.centerline[i][0]), int(self.centerline[i][1]))
            pygame.draw.circle(self._surface, dark_tarmac, pos, 15)
        # Lane markings — dashed white lines
        for lane in [self.lanes[0], self.lanes[2]]:
            for i in range(0, self.num_waypoints, 12):
                if (i // 12) % 2 == 0:
                    j = min(i + 6, self.num_waypoints - 1)
                    pygame.draw.line(
                        self._surface, (200, 200, 200),
                        (int(lane[i][0]), int(lane[i][1])),
                        (int(lane[j][0]), int(lane[j][1])), 2,
                    )
        # Start/finish: checkered pattern
        si = self.start_index
        left = self.lanes[0][si]
        right = self.lanes[2][si]
        dx = right[0] - left[0]
        dy = right[1] - left[1]
        length = math.hypot(dx, dy)
        nx, ny = dx / length, dy / length
        # Direction along track
        si2 = (si + 3) % self.num_waypoints
        tx = self.centerline[si2][0] - self.centerline[si][0]
        ty = self.centerline[si2][1] - self.centerline[si][1]
        tlen = math.hypot(tx, ty) or 1
        tx, ty = tx / tlen, ty / tlen
        sq = 8
        for row in range(-2, 3):
            for col in range(int(length / sq) + 1):
                cx = left[0] + nx * col * sq + tx * row * sq
                cy = left[1] + ny * col * sq + ty * row * sq
                color = (255, 255, 255) if (row + col) % 2 == 0 else (20, 20, 20)
                pygame.draw.rect(self._surface, color,
                                 (int(cx - sq / 2), int(cy - sq / 2), sq, sq))


    def render_mini(self, size=(280, 160)):
        surf = pygame.Surface(size)
        surf.fill(self.bg_color)
        if not self.centerline:
            return surf
        xs = [p[0] for p in self.centerline]
        ys = [p[1] for p in self.centerline]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x or 1
        h = max_y - min_y or 1
        margin = 15
        sx = (size[0] - margin * 2) / w
        sy = (size[1] - margin * 2) / h
        s = min(sx, sy)
        ox = margin + (size[0] - margin * 2 - w * s) / 2
        oy = margin + (size[1] - margin * 2 - h * s) / 2
        pts = [(int(ox + (p[0] - min_x) * s), int(oy + (p[1] - min_y) * s)) for p in self.centerline]
        pygame.draw.lines(surf, self.tarmac_color, True, pts, 8)
        pygame.draw.lines(surf, self.color, True, pts, 2)
        return surf


def _chaikin(points, iterations):
    pts = list(points)
    for _ in range(iterations):
        new = []
        for i in range(len(pts)):
            p0 = pts[i]
            p1 = pts[(i + 1) % len(pts)]
            new.append((0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1]))
            new.append((0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1]))
        pts = new
    return pts


def _evenly_space(points, n):
    dists = [0.0]
    for i in range(1, len(points)):
        d = math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
        dists.append(dists[-1] + d)
    total = dists[-1]
    result = []
    pi = 0
    for i in range(n):
        target = (i / n) * total
        while pi < len(dists) - 2 and dists[pi + 1] < target:
            pi += 1
        seg = dists[pi + 1] - dists[pi]
        frac = (target - dists[pi]) / seg if seg > 0.001 else 0
        x = points[pi][0] + frac * (points[pi + 1][0] - points[pi][0])
        y = points[pi][1] + frac * (points[pi + 1][1] - points[pi][1])
        result.append((x, y))
    return result


def _compute_normals(centerline):
    normals = []
    n = len(centerline)
    for i in range(n):
        p0 = centerline[i]
        p1 = centerline[(i + 1) % n]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy) or 1
        normals.append((-dy / length, dx / length))
    return normals


def _offset_lane(centerline, normals, offset):
    return [
        (c[0] + n[0] * offset, c[1] + n[1] * offset)
        for c, n in zip(centerline, normals)
    ]
