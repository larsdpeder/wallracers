import pygame
import numpy as np
import threading
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# How much of the center of the frame to crop for scanning
CROP_RATIO = 0.45


class Scanner:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.processing = False
        self.result_ready = False
        self.result_sprite = None
        self.snapshot_surf = None
        self._thread = None

    def open(self):
        if not HAS_CV2:
            return False
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = None
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return True

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_preview_surface(self, target_size=(640, 480)):
        if not self.cap:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        self.frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, target_size)
        h, w = rgb.shape[:2]
        cx, cy = w // 2, h // 2
        box_w = int(w * CROP_RATIO / 2)
        box_h = int(h * CROP_RATIO / 2)
        cv2.rectangle(rgb, (cx - box_w, cy - box_h), (cx + box_w, cy + box_h), (255, 255, 100), 2)
        # Corner markers for better framing
        corner_len = 20
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            x0 = cx + dx * box_w
            y0 = cy + dy * box_h
            cv2.line(rgb, (x0, y0), (x0 - dx * corner_len, y0), (255, 255, 100), 3)
            cv2.line(rgb, (x0, y0), (x0, y0 - dy * corner_len), (255, 255, 100), 3)
        cv2.putText(rgb, "Hold car in frame", (cx - 90, cy - box_h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 100), 2)
        # Arrow showing which way the front of the car should point (down)
        arrow_x = cx + box_w + 18
        arrow_top = cy - 30
        arrow_bot = cy + 30
        cv2.arrowedLine(rgb, (arrow_x, arrow_top), (arrow_x, arrow_bot),
                        (255, 255, 100), 2, tipLength=0.3)
        cv2.putText(rgb, "FRONT", (arrow_x - 22, arrow_bot + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 100), 1)
        return pygame.image.frombuffer(rgb.tobytes(), target_size, "RGB")

    def start_capture(self):
        if self.frame is None or self.processing:
            return False
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (640, 480))
        self.snapshot_surf = pygame.image.frombuffer(rgb.tobytes(), (640, 480), "RGB")
        self.processing = True
        self.result_ready = False
        self.result_sprite = None
        frame_copy = self.frame.copy()
        self._thread = threading.Thread(target=self._process_frame, args=(frame_copy,), daemon=True)
        self._thread.start()
        return True

    def _process_frame(self, frame):
        try:
            # Crop to center region so the car fills the frame
            cropped = _crop_center(frame, CROP_RATIO)
            sprite = None
            if HAS_REMBG:
                sprite = _capture_rembg(cropped, 64)
            # Fallback: contrast-based detection (colored object on white/light background)
            if sprite is None:
                sprite = _capture_contrast(cropped, 64)
            self.result_sprite = sprite
        except Exception:
            self.result_sprite = None
        self.result_ready = True
        self.processing = False

    def collect_result(self):
        if self.result_ready:
            self.result_ready = False
            sprite = self.result_sprite
            self.result_sprite = None
            self.snapshot_surf = None
            return True, sprite
        return False, None


def _crop_center(frame, ratio):
    h, w = frame.shape[:2]
    cw, ch = int(w * ratio), int(h * ratio)
    x0 = (w - cw) // 2
    y0 = (h - ch) // 2
    return frame[y0:y0 + ch, x0:x0 + cw].copy()


def _capture_rembg(frame, size):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)
    result = rembg_remove(pil_img)
    rgba = np.array(result)
    alpha = rgba[:, :, 3]
    # Use a low threshold — rembg can be conservative
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)
    if not rows.any() or not cols.any():
        return None
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    # Check if the detected region is meaningful (not just noise)
    region_h = rmax - rmin
    region_w = cmax - cmin
    if region_h < 20 or region_w < 20:
        return None
    pad = 8
    rmin = max(0, rmin - pad)
    rmax = min(rgba.shape[0], rmax + pad)
    cmin = max(0, cmin - pad)
    cmax = min(rgba.shape[1], cmax + pad)
    cropped = rgba[rmin:rmax, cmin:cmax]
    return _square_and_resize(cropped, size)


def _capture_contrast(frame, size):
    """Detect colored object on a light background using saturation + edges."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Detect the light/white background (high value, low saturation)
    bg_mask = cv2.inRange(hsv, np.array([0, 0, 170]), np.array([180, 60, 255]))
    # Also detect very bright areas
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    # Combine: background is white/bright
    combined_bg = cv2.bitwise_or(bg_mask, bright_mask)
    # Invert to get foreground (the car)
    fg_mask = cv2.bitwise_not(combined_bg)
    # Clean up
    kernel = np.ones((7, 7), np.uint8)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    # Also add edges to catch detail
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
    fg_mask = cv2.bitwise_or(fg_mask, edges)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    # Find largest contour
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 300:
        return None
    # Create tight mask from contour
    clean_mask = np.zeros(fg_mask.shape, dtype=np.uint8)
    cv2.drawContours(clean_mask, [largest], -1, 255, -1)
    # Slight expand to catch edges
    clean_mask = cv2.dilate(clean_mask, np.ones((5, 5), np.uint8))
    x, y, w, h = cv2.boundingRect(largest)
    pad = 10
    x = max(0, x - pad)
    y = max(0, y - pad)
    w = min(frame.shape[1] - x, w + pad * 2)
    h = min(frame.shape[0] - y, h + pad * 2)
    car_bgr = frame[y:y + h, x:x + w]
    car_mask = clean_mask[y:y + h, x:x + w]
    car_rgba = cv2.cvtColor(car_bgr, cv2.COLOR_BGR2BGRA)
    car_rgba[:, :, 3] = car_mask
    rgb = cv2.cvtColor(car_rgba[:, :, :3], cv2.COLOR_BGR2RGB)
    rgba = np.dstack((rgb, car_rgba[:, :, 3]))
    return _square_and_resize(rgba, size)


def _square_and_resize(rgba, size):
    """Pad to square and resize to target size."""
    h, w = rgba.shape[:2]
    max_dim = max(h, w)
    square = np.zeros((max_dim, max_dim, 4), dtype=np.uint8)
    y_off = (max_dim - h) // 2
    x_off = (max_dim - w) // 2
    square[y_off:y_off + h, x_off:x_off + w] = rgba
    square_img = Image.fromarray(square)
    square_img = square_img.resize((size, size), Image.LANCZOS)
    final = np.array(square_img)
    return _numpy_rgba_to_surface(final, size)


def _numpy_rgba_to_surface(rgba, size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    arr = pygame.surfarray.pixels3d(surf)
    alpha = pygame.surfarray.pixels_alpha(surf)
    arr[:] = np.transpose(rgba[:, :, :3], (1, 0, 2))
    alpha[:] = np.transpose(rgba[:, :, 3])
    del arr, alpha
    return surf
