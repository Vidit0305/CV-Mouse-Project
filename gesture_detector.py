"""
gesture_detector.py — Gesture classification from hand landmarks.

Gesture mappings:
  - MOVE:        Index finger up, others down → cursor movement
  - LEFT_CLICK:  Fist (all four fingers curled down)
  - RIGHT_CLICK: Open palm (all four fingers extended)
  - SCROLL_UP:   Index + middle up, moving upward
  - SCROLL_DOWN: Index + middle up, moving downward
  - NONE:        No recognized gesture
"""

import time
import math
from collections import deque
from utils import (
    is_finger_up,
    INDEX_TIP, INDEX_PIP,
    MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP,
    RING_TIP, RING_PIP,
    PINKY_TIP, PINKY_PIP,
    THUMB_TIP, THUMB_IP,
    CLICK_COOLDOWN,
    SCROLL_THRESHOLD,
)


class GestureDetector:
    """
    Classifies hand gestures from landmark positions.

    Supported gestures:
        - MOVE:        Index finger up, others curled → cursor movement
        - LEFT_CLICK:  Fist (all four fingers curled) — like pressing/grabbing
        - RIGHT_CLICK: Open palm (all four fingers extended) — deliberate spread
        - SCROLL_UP:   Index + middle up, moving upward
        - SCROLL_DOWN: Index + middle up, moving downward
        - NONE:        No recognized gesture
    """

    # Gesture name constants
    MOVE = "Move Cursor"
    LEFT_CLICK = "Left Click"
    RIGHT_CLICK = "Right Click"
    SCROLL_UP = "Scroll Up"
    SCROLL_DOWN = "Scroll Down"
    NONE = "None"

    def __init__(self):
        self.last_left_click_time = 0
        self.last_right_click_time = 0
        self.click_cooldown = CLICK_COOLDOWN
        self.right_click_cooldown = CLICK_COOLDOWN * 1.2  # Slightly longer for palm

        # Scroll history for direction detection
        self.scroll_history = deque(maxlen=8)
        self.scroll_threshold = SCROLL_THRESHOLD

        self.current_gesture = self.NONE
        self.left_click_triggered = False
        self.right_click_triggered = False
        self.scroll_direction = 0  # +1 up, -1 down, 0 none

        # Previous frame finger state (for edge detection)
        self._prev_fingers_up = -1  # -1 = no previous state

    def detect(self, landmarks):
        """
        Detect the current gesture from hand landmarks.

        Args:
            landmarks: List of 21 (x, y) pixel coordinate tuples.

        Returns:
            str: Name of the detected gesture.
        """
        if landmarks is None:
            self.current_gesture = self.NONE
            self.left_click_triggered = False
            self.right_click_triggered = False
            self.scroll_direction = 0
            self.scroll_history.clear()
            self._prev_fingers_up = -1
            return self.NONE

        now = time.time()

        # Reset per-frame triggers
        self.left_click_triggered = False
        self.right_click_triggered = False
        self.scroll_direction = 0

        # ── Finger states ──────────────────────────────────────
        index_up = is_finger_up(landmarks, INDEX_TIP, INDEX_PIP)
        middle_up = is_finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP)
        ring_up = is_finger_up(landmarks, RING_TIP, RING_PIP)
        pinky_up = is_finger_up(landmarks, PINKY_TIP, PINKY_PIP)

        # Relaxed middle finger check: compare tip vs MCP (knuckle) instead
        # of PIP — much more forgiving for slightly bent middle fingers.
        middle_up_relaxed = is_finger_up(landmarks, MIDDLE_TIP, MIDDLE_MCP)

        # Count extended fingers (excluding thumb for reliability)
        fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

        # ── Priority 1: Left Click — Fist (0 fingers up) ─────
        if fingers_up == 0:
            if (now - self.last_left_click_time) > self.click_cooldown:
                # Only trigger if we were previously in a different state
                # (prevents repeated clicks while holding fist)
                if self._prev_fingers_up > 0:
                    self.left_click_triggered = True
                    self.last_left_click_time = now
            self._prev_fingers_up = fingers_up
            self.scroll_history.clear()
            self.current_gesture = self.LEFT_CLICK
            return self.LEFT_CLICK

        # ── Priority 2: Right Click — Open Palm (4 fingers up) ─
        if fingers_up == 4:
            if (now - self.last_right_click_time) > self.right_click_cooldown:
                if self._prev_fingers_up < 4 and self._prev_fingers_up >= 0:
                    self.right_click_triggered = True
                    self.last_right_click_time = now
            self._prev_fingers_up = fingers_up
            self.scroll_history.clear()
            self.current_gesture = self.RIGHT_CLICK
            return self.RIGHT_CLICK

        # ── Priority 3: Scroll (index + middle up, ring + pinky down) ──
        # Uses relaxed middle finger check (tip vs MCP knuckle) so a slightly
        # bent middle finger still triggers scroll.
        if index_up and middle_up_relaxed and not ring_up and not pinky_up:
            # Track vertical position of midpoint between index and middle tips
            mid_y = (landmarks[INDEX_TIP][1] + landmarks[MIDDLE_TIP][1]) * 0.5
            self.scroll_history.append(mid_y)

            hist_len = len(self.scroll_history)
            if hist_len >= 4:
                hist = self.scroll_history
                recent_avg = (hist[-1] + hist[-2] + hist[-3]) / 3.0
                older_avg = (hist[0] + hist[1] + hist[2]) / 3.0
                delta = recent_avg - older_avg

                if delta < -self.scroll_threshold:
                    self.scroll_direction = 1  # Moving up → scroll up
                    self._prev_fingers_up = fingers_up
                    self.current_gesture = self.SCROLL_UP
                    return self.SCROLL_UP
                elif delta > self.scroll_threshold:
                    self.scroll_direction = -1  # Moving down → scroll down
                    self._prev_fingers_up = fingers_up
                    self.current_gesture = self.SCROLL_DOWN
                    return self.SCROLL_DOWN

            self._prev_fingers_up = fingers_up
            self.current_gesture = self.MOVE
            return self.MOVE

        # ── Priority 4: Move Cursor (index finger up) ────────
        if index_up:
            self.scroll_history.clear()
            self._prev_fingers_up = fingers_up
            self.current_gesture = self.MOVE
            return self.MOVE

        # ── No gesture recognized ─────────────────────────────
        self.scroll_history.clear()
        self._prev_fingers_up = fingers_up
        self.current_gesture = self.NONE
        return self.NONE

    def get_current_gesture(self):
        """Return the name of the last detected gesture."""
        return self.current_gesture

    def was_left_click(self):
        """Return True if a left click was triggered this frame."""
        return self.left_click_triggered

    def was_right_click(self):
        """Return True if a right click was triggered this frame."""
        return self.right_click_triggered

    def get_scroll_direction(self):
        """Return scroll direction: +1 (up), -1 (down), or 0 (none)."""
        return self.scroll_direction

    def set_click_threshold(self, value):
        """Update the click distance threshold (kept for API compatibility)."""
        pass  # No distance threshold needed for fist/palm gestures

    def set_cooldown(self, value):
        """Update the click cooldown."""
        self.click_cooldown = value
