"""
main.py — Entry point for the Virtual Mouse application.

Launches fullscreen webcam, auto-starts camera, and runs the processing loop.
Press ESC or close the window to exit.
"""

import sys
import tkinter as tk
import cv2

from hand_tracker import HandTracker
from gesture_detector import GestureDetector
from mouse_controller import MouseController
from ui import VirtualMouseUI
from utils import FPSCounter, CAMERA_WIDTH, CAMERA_HEIGHT


class VirtualMouseApp:
    """
    Main application class that orchestrates all modules.
    Auto-starts camera on launch. ESC to exit.
    """

    def __init__(self):
        # ── Tkinter root window ──────────────────────────────
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.bind("<Escape>", lambda e: self.on_exit())

        # ── Modules ──────────────────────────────────────────
        self.hand_tracker = HandTracker()
        self.gesture_detector = GestureDetector()
        self.mouse_controller = MouseController()
        self.fps_counter = FPSCounter()

        # ── UI ───────────────────────────────────────────────
        self.ui = VirtualMouseUI(self.root)

        # ── Camera ───────────────────────────────────────────
        self.cap = None
        self.camera_active = False
        self.update_id = None

        # ── Performance: cache last gesture to reduce jitter ──
        self._last_gesture = GestureDetector.NONE
        self._last_landmarks = None

        # Auto-start camera after UI is ready
        self.root.after(500, self.start_camera)

    def start_camera(self):
        """Open the webcam and start processing frames."""
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                self.ui.show_camera_error()
                return

            self.camera_active = True
            self.ui.update_camera_button(True)
            self.mouse_controller.reset_smoother()
            self.process_frame()

        except Exception as e:
            print(f"Camera error: {e}")
            self.ui.show_camera_error()

    def stop_camera(self):
        """Stop the camera and release resources."""
        self.camera_active = False
        if self.update_id is not None:
            self.root.after_cancel(self.update_id)
            self.update_id = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.ui.update_camera_button(False)
        self.mouse_controller.reset_smoother()

    def process_frame(self):
        """
        Main processing loop — called via Tkinter's after().

        Pipeline:
          1. Capture frame
          2. Detect hand landmarks
          3. Classify gesture
          4. Execute mouse action
          5. Draw overlays + update display
        """
        if not self.camera_active or self.cap is None:
            return

        ret, frame = self.cap.read()

        if not ret:
            self.ui.show_camera_error()
            self.stop_camera()
            return

        # Flip horizontally for mirror experience
        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]

        # ── 1. Detect hand landmarks ─────────────────────────
        landmarks = self.hand_tracker.process_frame(frame)
        hand_detected = self.hand_tracker.is_hand_detected()

        # ── 2. Classify gesture ──────────────────────────────
        gesture = self.gesture_detector.detect(landmarks)

        # ── 3. Execute mouse actions ─────────────────────────
        if gesture == GestureDetector.MOVE:
            self.mouse_controller.move_cursor(landmarks, frame_w, frame_h)
        elif gesture == GestureDetector.LEFT_CLICK:
            if self.gesture_detector.was_left_click():
                self.mouse_controller.left_click()
        elif gesture == GestureDetector.RIGHT_CLICK:
            if self.gesture_detector.was_right_click():
                self.mouse_controller.right_click()
        elif gesture in (GestureDetector.SCROLL_UP, GestureDetector.SCROLL_DOWN):
            self.mouse_controller.scroll(self.gesture_detector.get_scroll_direction())

        # ── 4. Draw overlays (FPS, gesture, guide) ───────────
        fps = self.fps_counter.tick()
        frame = self.ui.draw_overlays(frame, landmarks, gesture,
                                      self.gesture_detector, fps=fps)

        # ── 5. Update display ────────────────────────────────
        self.ui.update_frame(frame)

        # ── Schedule next frame (run as fast as possible) ─────
        self.update_id = self.root.after(1, self.process_frame)

    def on_exit(self):
        """Clean up and exit."""
        self.stop_camera()
        self.hand_tracker.release()
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


def main():
    """Application entry point."""
    app = VirtualMouseApp()
    app.run()


if __name__ == "__main__":
    main()
