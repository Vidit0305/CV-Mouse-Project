"""
ui.py — Fullscreen webcam UI for the Virtual Mouse application.

Minimal HUD: FPS overlay (top-left), gesture guide (top-right),
current gesture badge (bottom-center). No side panels.
"""

import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
import time

from utils import (
    COLOR_BG_DARK,
    CV_GREEN, CV_RED, CV_BLUE, CV_CYAN, CV_WHITE,
    INDEX_TIP, MIDDLE_TIP, THUMB_TIP,
    CAMERA_WIDTH, CAMERA_HEIGHT,
)
from gesture_detector import GestureDetector


class VirtualMouseUI:
    """
    Fullscreen webcam UI — the camera feed fills the entire window.
    All status info is rendered as lightweight OpenCV overlays on the frame.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Mouse — AI Hand Gesture Control")
        self.root.configure(bg="#000000")

        # Start at a comfortable default size (user can resize freely)
        self.root.geometry("800x600")
        self.root.minsize(320, 240)

        # State
        self.camera_active = False
        self.click_flash_time = 0
        self.click_flash_type = None

        # Track display size
        self.display_width = CAMERA_WIDTH
        self.display_height = CAMERA_HEIGHT

        # Debounce resize
        self._resize_timer = None

        # ── Build minimal UI: just a webcam label ─────────
        self.webcam_label = tk.Label(self.root, bg="#000000")
        self.webcam_label.pack(fill=tk.BOTH, expand=True)

        # Show placeholder
        self._show_placeholder()

        # Bind resize
        self.root.bind("<Configure>", self._on_resize)

        # ── Hidden buttons (for main.py compatibility) ─────
        # These exist but aren't displayed — main.py auto-starts camera
        self.camera_btn = tk.Button(self.root)
        self.reset_btn = tk.Button(self.root)
        self.exit_btn = tk.Button(self.root)

    # ─── Resize Handling ──────────────────────────────────────────

    def _on_resize(self, event=None):
        """Debounced resize handler."""
        if self._resize_timer is not None:
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(100, self._do_resize)

    def _do_resize(self):
        """Compute new display dimensions — stretch to fill entire window."""
        self._resize_timer = None
        try:
            win_w = self.root.winfo_width()
            win_h = self.root.winfo_height()

            if win_w > 10 and win_h > 10:
                # Fill entire window (no aspect ratio lock)
                self.display_width = max(320, win_w)
                self.display_height = max(240, win_h)
        except Exception:
            pass

    # ─── Placeholder ──────────────────────────────────────────────

    def _show_placeholder(self):
        """Show a placeholder when camera is not active."""
        placeholder = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
        placeholder[:] = (15, 15, 15)

        text = "Starting Camera..."
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
        cx = (CAMERA_WIDTH - tw) // 2
        cy = (CAMERA_HEIGHT + th) // 2
        cv2.putText(placeholder, text, (cx, cy), font, 0.8, (100, 100, 100), 2)

        self._update_frame_display(placeholder)

    # ─── Overlay Drawing ─────────────────────────────────────────

    def draw_overlays(self, frame, landmarks, gesture, gesture_detector, fps=0):
        """
        Draw all HUD overlays directly on the webcam frame.

        Args:
            frame: BGR OpenCV image.
            landmarks: List of 21 (x, y) coordinates, or None.
            gesture: Current gesture name string.
            gesture_detector: GestureDetector instance.
            fps: Current FPS value.
        """
        now = time.time()
        h, w = frame.shape[:2]

        # ── Draw hand interaction visuals ─────────────────
        if landmarks is not None:
            ix, iy = landmarks[INDEX_TIP]

            # Green cursor dot on index finger
            cv2.circle(frame, (ix, iy), 12, CV_GREEN, 2, cv2.LINE_AA)
            cv2.circle(frame, (ix, iy), 5, CV_GREEN, -1, cv2.LINE_AA)

            # Left click flash (red burst)
            if gesture_detector.was_left_click():
                self.click_flash_time = now
                self.click_flash_type = "left"

            # Right click flash (cyan burst)
            if gesture_detector.was_right_click():
                self.click_flash_time = now
                self.click_flash_type = "right"

            # Draw click flash (persists for 300ms)
            if (now - self.click_flash_time) < 0.3 and self.click_flash_type:
                flash_color = CV_RED if self.click_flash_type == "left" else CV_CYAN
                # Flash at center of hand (wrist area)
                cx = landmarks[0][0]
                cy_flash = landmarks[0][1]
                cv2.circle(frame, (cx, cy_flash), 30, flash_color, 3, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy_flash), 15, flash_color, -1, cv2.LINE_AA)

                click_text = "LEFT CLICK!" if self.click_flash_type == "left" else "RIGHT CLICK!"
                self._draw_text_with_bg(frame, click_text, (cx - 55, cy_flash - 40),
                                        0.55, flash_color, 2)

            # Scroll indicator
            if gesture in (GestureDetector.SCROLL_UP, GestureDetector.SCROLL_DOWN):
                mx, my = landmarks[MIDDLE_TIP]
                cv2.circle(frame, (ix, iy), 14, CV_BLUE, 3, cv2.LINE_AA)
                cv2.circle(frame, (mx, my), 14, CV_BLUE, 3, cv2.LINE_AA)
                arrow = "^ SCROLL UP" if gesture == GestureDetector.SCROLL_UP else "v SCROLL DOWN"
                mid_x = (ix + mx) // 2 - 50
                mid_y = min(iy, my) - 25
                self._draw_text_with_bg(frame, arrow, (mid_x, mid_y), 0.5, CV_BLUE, 2)

            # Fist indicator
            if gesture == GestureDetector.LEFT_CLICK:
                cv2.circle(frame, (ix, iy), 20, CV_RED, 3, cv2.LINE_AA)

            # Palm indicator
            if gesture == GestureDetector.RIGHT_CLICK:
                cv2.circle(frame, (ix, iy), 20, CV_CYAN, 3, cv2.LINE_AA)

        # ── FPS Badge (top-left) ──────────────────────────
        self._draw_fps_badge(frame, fps)

        # ── Current Gesture Badge (top-left, below FPS) ───
        self._draw_gesture_badge(frame, gesture, landmarks is not None)

        return frame

    def _draw_fps_badge(self, frame, fps):
        """Draw FPS counter with dark background — top-left."""
        fps_text = f"FPS: {int(fps)}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(fps_text, font, scale, thickness)

        # Background
        pad = 6
        x, y = 10, 10
        cv2.rectangle(frame, (x, y), (x + tw + pad * 2, y + th + pad * 2),
                      (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + tw + pad * 2, y + th + pad * 2),
                      (60, 60, 60), 1)

        # Text color based on FPS
        if fps >= 25:
            color = (0, 230, 118)  # Green
        elif fps >= 15:
            color = (0, 200, 255)  # Orange
        else:
            color = (68, 23, 255)  # Red

        cv2.putText(frame, fps_text, (x + pad, y + th + pad),
                    font, scale, color, thickness, cv2.LINE_AA)

    def _draw_gesture_badge(self, frame, gesture, hand_detected):
        """Draw current gesture name — top-left, below FPS."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1

        # Hand status
        if hand_detected:
            status = f"Hand: Detected | {gesture}"
            color = CV_GREEN
        else:
            status = "Hand: Not Detected"
            color = (100, 100, 100)

        (tw, th), _ = cv2.getTextSize(status, font, scale, thickness)
        pad = 5
        x, y = 10, 42
        cv2.rectangle(frame, (x, y), (x + tw + pad * 2, y + th + pad * 2),
                      (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + tw + pad * 2, y + th + pad * 2),
                      (40, 40, 40), 1)
        cv2.putText(frame, status, (x + pad, y + th + pad),
                    font, scale, color, thickness, cv2.LINE_AA)

    def _draw_gesture_guide(self, frame, frame_w):
        """Draw a compact gesture guide — top-right corner."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.4
        thickness = 1
        line_height = 18

        guide_lines = [
            ("CONTROLS", CV_WHITE),
            ("Point Finger = Move", CV_GREEN),
            ("Close Fist = Left Click", (68, 23, 255)),
            ("Open Palm = Right Click", CV_CYAN),
            ("Two Fingers = Scroll", (255, 121, 41)),
        ]

        # Calculate box dimensions
        max_tw = 0
        for text, _ in guide_lines:
            (tw, _), _ = cv2.getTextSize(text, font, scale, thickness)
            max_tw = max(max_tw, tw)

        pad = 8
        box_w = max_tw + pad * 2
        box_h = len(guide_lines) * line_height + pad * 2
        x = frame_w - box_w - 10
        y = 10

        # Background
        cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (50, 50, 50), 1)

        # Draw lines
        for i, (text, color) in enumerate(guide_lines):
            text_y = y + pad + 12 + i * line_height
            cv2.putText(frame, text, (x + pad, text_y),
                        font, scale, color, thickness, cv2.LINE_AA)

    def _draw_text_with_bg(self, frame, text, pos, scale, color, thickness):
        """Draw text with a dark semi-transparent background."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        x, y = pos
        pad = 4
        cv2.rectangle(frame, (x - pad, y - th - pad), (x + tw + pad, y + pad),
                      (0, 0, 0), -1)
        cv2.putText(frame, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

    # ─── Frame Display ────────────────────────────────────────────

    def update_frame(self, frame):
        """Update the webcam display with a new frame."""
        self._update_frame_display(frame)

    def _update_frame_display(self, frame):
        """Convert BGR frame to Tkinter-compatible, scale, and display.

        Optimization: color-convert on the small camera frame BEFORE
        resizing — much cheaper than converting the large display frame.
        """
        display_w = max(320, self.display_width)
        display_h = max(240, self.display_height)

        # Convert color on small frame first (640x480), then upscale
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(frame_rgb, (display_w, display_h),
                             interpolation=cv2.INTER_NEAREST)
        img = Image.fromarray(resized)
        imgtk = ImageTk.PhotoImage(image=img)
        self.webcam_label.imgtk = imgtk
        self.webcam_label.configure(image=imgtk)

    # ─── Stats Update (no-op in fullscreen mode — drawn as overlays) ──

    def update_stats(self, fps, gesture, hand_detected, left_clicks,
                     right_clicks, scroll_dir):
        """No-op: stats are drawn as overlays in draw_overlays()."""
        pass

    def update_camera_button(self, is_active):
        """Update internal camera state."""
        self.camera_active = is_active

    def show_camera_error(self):
        """Display a camera error on the webcam feed."""
        error_frame = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
        error_frame[:] = (15, 15, 15)

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Camera Error"
        (tw, th), _ = cv2.getTextSize(text, font, 1.0, 2)
        cx = (CAMERA_WIDTH - tw) // 2
        cy = (CAMERA_HEIGHT + th) // 2 - 20
        cv2.putText(error_frame, text, (cx, cy), font, 1.0, (0, 0, 255), 2)

        sub_text = "Could not access the webcam"
        (tw2, _), _ = cv2.getTextSize(sub_text, font, 0.5, 1)
        cx2 = (CAMERA_WIDTH - tw2) // 2
        cv2.putText(error_frame, sub_text, (cx2, cy + 35), font, 0.5,
                    (100, 100, 255), 1)

        self._update_frame_display(error_frame)

    def get_sensitivity(self):
        """Return default sensitivity."""
        return 1.5

    def get_threshold(self):
        """Return default threshold (not used with new gestures)."""
        return 25
