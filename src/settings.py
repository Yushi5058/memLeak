# Screen settings
DEBUG = False  # Opt-in per-frame physics trace on stdout
INTERNAL_WIDTH = 320
INTERNAL_HEIGHT = 180
SCALE = 3
SCREEN_WIDTH = INTERNAL_WIDTH * SCALE  # 960
SCREEN_HEIGHT = INTERNAL_HEIGHT * SCALE  # 540
FPS = 60

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
START_EARTH_YEARS = 500.0  # Starting allocation
DRAIN_RATE = 15.0  # Earth years lost per real second
HAZARD_PENALTY = 50.0  # Penalty on hazard hit

# Time cost per discrete action
STEP_COST = 0.5  # Drained once whenever a direction key is pressed
JUMP_COST = 2.0  # Drained once when jump is pressed
