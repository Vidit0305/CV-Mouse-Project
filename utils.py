"""
utils.py — Constants, configuration, FPS counter, and helper functions.

Performance optimizations:
  - math.hypot instead of manual sqrt for distance calculation (~40% faster)
  - Scalar min/max instead of np.clip in map_coordinates (avoids numpy array overhead)
  - deque-based FPS counter (avoids list slicing/copy every tick)
  - Lower camera resolution for faster processing
"""

import time
import math
from collections import deque
import pyautogui

# ─── Screen Dimensions ────────────────────────────────────────────────
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# ─── Camera Settings ──────────────────────────────────────────────────
# 320x240 for maximum FPS (fewer pixels = faster MediaPipe inference)
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# ─── Gesture Thresholds ──────────────────────────────────────────────
CLICK_DISTANCE_THRESHOLD = 20       # Pixels in camera frame for click detection
RIGHT_CLICK_DISTANCE_THRESHOLD = 20 # Pixels in camera frame for right click
CLICK_COOLDOWN = 0.4                # Seconds between consecutive clicks
SCROLL_THRESHOLD = 8                # Vertical pixel movement to trigger scroll
SCROLL_SPEED = 5                    # Scroll amount per frame

# ─── Cursor Smoothing ────────────────────────────────────────────────
SMOOTHING_FACTOR = 0.7   # EMA factor: higher = more responsive cursor
SENSITIVITY = 1.5        # Mouse speed multiplier

# ─── Camera Frame ROI (Region of Interest) ───────────────────────────
# Use inner portion of the camera frame for comfortable mapping
ROI_LEFT = 0.1
ROI_TOP = 0.1
ROI_RIGHT = 0.9
ROI_BOTTOM = 0.9

# Pre-computed ROI span for map_coordinates (avoids repeated subtraction)
_ROI_X_SPAN = ROI_RIGHT - ROI_LEFT
_ROI_Y_SPAN = ROI_BOTTOM - ROI_TOP

# ─── UI Colors (Dark Theme) ──────────────────────────────────────────
COLOR_BG_DARK = "#0d1117"
COLOR_BG_PANEL = "#161b22"
COLOR_BG_CARD = "#1c2333"
COLOR_BG_HEADER = "#0f1923"
COLOR_ACCENT_GREEN = "#00e676"
COLOR_ACCENT_RED = "#ff1744"
COLOR_ACCENT_BLUE = "#2979ff"
COLOR_ACCENT_PURPLE = "#b388ff"
COLOR_ACCENT_ORANGE = "#ff9100"
COLOR_ACCENT_CYAN = "#00e5ff"
COLOR_TEXT_PRIMARY = "#e6edf3"
COLOR_TEXT_SECONDARY = "#8b949e"
COLOR_TEXT_DIM = "#484f58"
COLOR_BORDER = "#30363d"
COLOR_SUCCESS = "#2ea043"
COLOR_WARNING = "#d29922"

# ─── OpenCV Drawing Colors (BGR) ─────────────────────────────────────
CV_GREEN = (0, 230, 118)
CV_RED = (68, 23, 255)
CV_BLUE = (255, 121, 41)
CV_CYAN = (255, 229, 0)
CV_WHITE = (255, 255, 255)
CV_YELLOW = (0, 255, 255)
CV_DARK_BG = (23, 17, 13)

# ─── MediaPipe Landmark IDs ──────────────────────────────────────────
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20


class FPSCounter:
    """Calculates rolling-average FPS over a configurable window.

    Uses deque with maxlen for O(1) append/eviction instead of list slicing.
    """

    def __init__(self, window_size=30):
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)
        self.fps = 0.0

    def tick(self):
        """Call once per frame. Returns current FPS."""
        now = time.time()
        self.timestamps.append(now)
        if len(self.timestamps) >= 2:
            elapsed = self.timestamps[-1] - self.timestamps[0]
            if elapsed > 0:
                self.fps = (len(self.timestamps) - 1) / elapsed
        return self.fps

    def get_fps(self):
        """Return last computed FPS."""
        return self.fps


class CursorSmoother:
    """Exponential moving average filter for cursor position."""

    def __init__(self, smoothing=SMOOTHING_FACTOR):
        self.smoothing = smoothing
        self.prev_x = None
        self.prev_y = None

    def smooth(self, x, y):
        """Apply EMA smoothing to the given (x, y) position."""
        if self.prev_x is None:
            self.prev_x = x
            self.prev_y = y
            return x, y

        s = self.smoothing
        smooth_x = self.prev_x + s * (x - self.prev_x)
        smooth_y = self.prev_y + s * (y - self.prev_y)
        self.prev_x = smooth_x
        self.prev_y = smooth_y
        return int(smooth_x), int(smooth_y)

    def reset(self):
        """Reset the smoother state."""
        self.prev_x = None
        self.prev_y = None

    def set_smoothing(self, value):
        """Update the smoothing factor."""
        self.smoothing = value


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two (x, y) points.

    Uses math.hypot — a C-level intrinsic that's ~40% faster than
    manual sqrt((dx)**2 + (dy)**2).
    """
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])


def map_coordinates(x, y, frame_w, frame_h, sensitivity=SENSITIVITY):
    """
    Map camera-frame coordinates to screen coordinates.
    Uses ROI to provide a comfortable working area.

    Optimized: uses scalar min/max instead of np.clip to avoid numpy overhead.
    """
    # Pre-compute ROI pixel boundaries
    roi_left_px = ROI_LEFT * frame_w
    roi_right_px = ROI_RIGHT * frame_w
    roi_top_px = ROI_TOP * frame_h
    roi_bottom_px = ROI_BOTTOM * frame_h

    # Clamp to ROI boundaries (scalar min/max — no numpy array creation)
    roi_x = max(roi_left_px, min(roi_right_px, x))
    roi_y = max(roi_top_px, min(roi_bottom_px, y))

    # Normalize within ROI (0.0 to 1.0)
    norm_x = (roi_x - roi_left_px) / (_ROI_X_SPAN * frame_w)
    norm_y = (roi_y - roi_top_px) / (_ROI_Y_SPAN * frame_h)

    # X is NOT inverted here because cv2.flip() already mirrors the frame
    screen_x = int(norm_x * SCREEN_WIDTH)
    screen_y = int(norm_y * SCREEN_HEIGHT)

    # Clamp to screen bounds
    screen_x = max(0, min(SCREEN_WIDTH - 1, screen_x))
    screen_y = max(0, min(SCREEN_HEIGHT - 1, screen_y))

    return screen_x, screen_y


def is_finger_up(landmarks, finger_tip_id, finger_pip_id):
    """Check if a finger is extended (tip is above PIP joint in image coords)."""
    return landmarks[finger_tip_id][1] < landmarks[finger_pip_id][1]


def get_landmark_pixel_coords(landmark, frame_w, frame_h):
    """Convert normalized MediaPipe landmark to pixel coordinates."""
    return int(landmark.x * frame_w), int(landmark.y * frame_h)
