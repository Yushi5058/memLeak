# Screen settings
DEBUG = False  # Opt-in per-frame physics trace on stdout
INTERNAL_WIDTH = 320
INTERNAL_HEIGHT = 180
SCALE = 3
SCREEN_WIDTH = INTERNAL_WIDTH * SCALE  # 960
SCREEN_HEIGHT = INTERNAL_HEIGHT * SCALE  # 540
FPS = 60
MAX_DT = 0.05  # Longest physics step; tunnelling observed at dt >= 0.2

# Physics
GRAVITY = 980.0  # pixels / second^2
MOVE_SPEED = 110.0  # horizontal speed in pixels / second
JUMP_STRENGTH = -320.0  # initial upward velocity on jump

# Palette (Retro / Terminal vibe)
BG_COLOR = (18, 16, 26)  # Deep night / void purple
GROUND_COLOR = (45, 48, 64)  # Cold stone
PLAYER_COLOR = (50, 205, 50)  # Terminal neon green

# Colors & Level objects
HAZARD_COLOR = (230, 40, 60)  # Glitch red
TARGET_COLOR = (80, 220, 240)  # Anomaly cyan
TEXT_COLOR = (240, 240, 240)
DIM_COLOR = (104, 104, 124)  # Locked or unavailable menu entries
EARNED_TILE_COLOR = (24, 52, 34)  # Achievement row backing, already earned
LOCKED_TILE_COLOR = (46, 26, 36)  # Achievement row backing, still locked

# Falling hazard spawner
FALLING_HAZARD_WIDTH = 10
FALLING_HAZARD_HEIGHT = 14
FALLING_HAZARD_SPEED_MIN = 70.0  # px/sec at chamber start
FALLING_HAZARD_SPEED_MAX = 190.0  # px/sec once fully ramped
SPAWN_INTERVAL_MAX = 2.5  # seconds between spawns at chamber start
SPAWN_INTERVAL_MIN = 0.8  # seconds between spawns once fully ramped
RAMP_SECONDS = 60.0  # seconds to reach the hardest spawn rate

# Audio
VOLUME_STEPS = 5

# Time cost per discrete action
STEP_COST = 0.5  # Drained once whenever a direction key is pressed
JUMP_COST = 2.0  # Drained once when jump is pressed
