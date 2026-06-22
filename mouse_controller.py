"""
mouse_controller.py — System mouse control via PyAutoGUI + direct Win32 API.

Uses direct Win32 SetCursorPos for cursor movement (faster than PyAutoGUI),
and PyAutoGUI for clicks/scroll (where overhead doesn't matter).
"""

import ctypes
import pyautogui
from utils import (
    map_coordinates,
    CursorSmoother,
    SCROLL_SPEED,
    SENSITIVITY,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    INDEX_TIP,
)

# Safety: allow aborting by moving mouse to screen corner
pyautogui.FAILSAFE = True
# Disable the default pause between PyAutoGUI calls for responsiveness
pyautogui.PAUSE = 0

# Direct Win32 API for cursor movement — ~5-10ms faster than pyautogui.moveTo
_set_cursor_pos = ctypes.windll.user32.SetCursorPos


class MouseController:
    """
    Controls the system mouse cursor using hand landmark positions.
    Handles cursor movement, clicks, and scrolling.
    """

    def __init__(self):
        self.smoother = CursorSmoother()
        self.sensitivity = SENSITIVITY
        self.scroll_speed = SCROLL_SPEED

        # Click counters for the UI
        self.left_click_count = 0
        self.right_click_count = 0
        self.is_active = False

    def move_cursor(self, landmarks, frame_w=CAMERA_WIDTH, frame_h=CAMERA_HEIGHT):
        """
        Move the system cursor based on the index finger tip position.

        Uses direct Win32 SetCursorPos for minimal latency.

        Args:
            landmarks: List of 21 (x, y) landmark coordinates.
            frame_w: Width of the camera frame.
            frame_h: Height of the camera frame.
        """
        if landmarks is None:
            self.is_active = False
            return

        self.is_active = True
        index_x, index_y = landmarks[INDEX_TIP]

        # Map camera coordinates to screen coordinates
        screen_x, screen_y = map_coordinates(
            index_x, index_y, frame_w, frame_h, self.sensitivity
        )

        # Apply smoothing
        smooth_x, smooth_y = self.smoother.smooth(screen_x, screen_y)

        # Move cursor via direct Win32 API (bypasses PyAutoGUI overhead)
        _set_cursor_pos(smooth_x, smooth_y)

    def left_click(self):
        """Perform a left mouse click."""
        try:
            pyautogui.click(_pause=False)
            self.left_click_count += 1
        except pyautogui.FailSafeException:
            pass

    def right_click(self):
        """Perform a right mouse click."""
        try:
            pyautogui.rightClick(_pause=False)
            self.right_click_count += 1
        except pyautogui.FailSafeException:
            pass

    def scroll(self, direction):
        """
        Scroll the mouse wheel.

        Args:
            direction: +1 for scroll up, -1 for scroll down.
        """
        amount = direction * self.scroll_speed
        try:
            pyautogui.scroll(amount, _pause=False)
        except pyautogui.FailSafeException:
            pass

    def set_sensitivity(self, value):
        """Update mouse sensitivity."""
        self.sensitivity = value

    def set_scroll_speed(self, value):
        """Update scroll speed."""
        self.scroll_speed = value

    def get_left_click_count(self):
        """Return the total number of left clicks."""
        return self.left_click_count

    def get_right_click_count(self):
        """Return the total number of right clicks."""
        return self.right_click_count

    def reset_counters(self):
        """Reset click counters."""
        self.left_click_count = 0
        self.right_click_count = 0

    def reset_smoother(self):
        """Reset the cursor smoother."""
        self.smoother.reset()
