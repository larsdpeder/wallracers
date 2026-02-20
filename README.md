<img width="2032" height="1220" alt="Screenshot 2026-02-20 at 12 45 25" src="https://github.com/user-attachments/assets/c4d37483-2f8b-40be-be9f-6f7a60d4b022" />


# Wall Racers

A top-down racing game where kids scan their toy cars with a webcam and race them on 5 iconic racing circuits. Built with Pygame — designed to be projected on a wall for group play.

## How It Works

1. **Choose players** (1-4) on the title screen
2. **Scan your car** using the webcam — hold it in the yellow guide box with the nose pointing down, press SPACE to capture
3. **Pick a track** — Monaco, Monza, Spa, Silverstone, or Suzuka
4. **Race!** Cars drive automatically around the track. You control lane switching, boost, and honk

If you skip scanning or don't have a webcam, the game uses built-in car sprites.

## Controls

All players share one keyboard:

| Player | Lane Switch | Boost | Honk |
|--------|-------------|-------|------|
| P1 | Q | W | E |
| P2 | I | O | P |
| P3 | T | Y | U |
| P4 | LEFT | UP | RIGHT |

**General:** SPACE to confirm/advance, ESC to quit, LEFT/RIGHT to navigate menus.

### Gameplay

- **Lane Switch** — Cycles between 3 lanes (inner, middle, outer)
- **Boost** — Uses a boost charge for a speed burst (collect blue lightning pickups to earn charges, max 3)
- **Honk** — Air horn with visual ring effect

### Track Items

- **Boost Pads** (yellow arrows) — Brief speed burst when driven over
- **Boost Pickups** (blue lightning) — Adds a boost charge
- **Oil Slicks** (dark puddles) — Slows you down for 2 seconds (shields block this)
- **Mystery Boxes** (purple ?) — Random effect: shield, speed burst, or boost charge

## Setup

### Requirements

- Python 3.9+
- Webcam (optional, for scanning cars)

### macOS

```bash
# Clone the repo
git clone https://github.com/larsdpeder/wallracers.git
cd wallracers

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

**Note:** On macOS, the game may prompt for camera access when scanning. Allow this in System Settings > Privacy & Security > Camera.

If `rembg` installation fails (it's large), the game still works — it will fall back to contrast-based car detection or use the built-in sprites.

### Windows

```powershell
# Clone the repo
git clone https://github.com/larsdpeder/wallracers.git
cd wallracers

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

**Note:** On Windows, if you get a `pygame` audio error, try installing with:
```powershell
pip install pygame --pre
```

### Minimal Install (no webcam scanning)

If you just want to race without scanning:

```bash
pip install pygame numpy Pillow
python main.py
```

The game uses built-in car sprites automatically when no webcam is available.

## Project Structure

```
wallracers/
  main.py          # Game loop and state machine
  controls.py      # Key bindings and constants
  track.py         # 5 racing circuits with lane generation
  car.py           # Car physics, rendering, sprites
  scanner.py       # Webcam capture and car cutout
  race.py          # Lap tracking, positions, finish
  items.py         # Boost pads, pickups, oil, mystery boxes
  hud.py           # All UI screens and race overlay
  sounds.py        # Synthesized engine and effects
  effects.py       # Particle system (boost flames, fireworks)
  assets/          # Car sprites
  tests/           # Unit tests
```

## Tracks

| Track | Color | Style |
|-------|-------|-------|
| Monaco | Red | Tight street circuit |
| Monza | Green | High-speed oval feel |
| Spa | Blue | Flowing elevation changes |
| Silverstone | White | Fast sweeping corners |
| Suzuka | Purple | Technical figure-8 layout |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Troubleshooting

- **Game window is black/tiny**: The game runs at 1920x1080 fullscreen. Press ESC to quit if your display doesn't support this.
- **No sound**: Make sure your system volume is up. The game generates all sounds programmatically — no audio files needed.
- **Webcam not detected**: The game skips scanning and uses default car sprites. Make sure no other app is using the camera.
- **Car cutout is bad**: Hold the car against a plain white/light background. The yellow guide box on screen shows where to position it. Point the nose downward.
- **`rembg` is slow to install**: It downloads a ~170MB neural network model on first use. If you don't need scanning, skip it with the minimal install above.
