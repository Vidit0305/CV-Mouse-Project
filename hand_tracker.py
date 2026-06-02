"""
hand_tracker.py — Hand detection and landmark extraction using MediaPipe Tasks API.

Performance optimizations:
  - Uses VIDEO running mode (tracks across frames instead of re-detecting every frame)
  - Lower detection confidence since re-detection is rare in tracking mode
"""

import os
import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)
from utils import get_landmark_pixel_coords

# Path to the hand landmarker model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "assets", "hand_landmarker.task")


class HandTracker:
    """
    Detects a single hand in webcam frames using MediaPipe Hand Landmarker (Tasks API).
    Extracts 21 landmark positions and draws them on the frame.

    Uses VIDEO running mode for temporal tracking — much faster than per-frame IMAGE mode.
    """

    def __init__(self, max_hands=1, detection_confidence=0.4, tracking_confidence=0.4):
        # Validate model file exists
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Hand landmarker model not found at: {MODEL_PATH}\n"
                "Download it from: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )

        # VIDEO mode: enables temporal tracking across frames (much faster than IMAGE)
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=tracking_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

        self.landmarks = None
        self.hand_detected = False

        # Monotonically increasing timestamp for VIDEO mode (milliseconds)
        self._timestamp_ms = int(time.time() * 1000)

        # Drawing colors (BGR)
        self.landmark_color = (0, 230, 118)   # Green
        self.connection_color = (41, 121, 255) # Blue

        # MediaPipe hand connections for drawing
        self.hand_connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),      # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16), # Ring
            (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
            (5, 9), (9, 13), (13, 17),             # Palm
        ]

    def process_frame(self, frame):
        """
        Process a BGR frame and detect hand landmarks using VIDEO mode.

        Args:
            frame: BGR image from OpenCV.

        Returns:
            landmarks_list: List of (x, y) pixel coordinates for 21 landmarks,
                            or None if no hand detected.
        """
        frame_h, frame_w = frame.shape[:2]

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Use real timestamps (VIDEO mode requires monotonically increasing timestamps)
        current_ms = int(time.time() * 1000)
        self._timestamp_ms = max(self._timestamp_ms + 1, current_ms)

        # Detect hand landmarks using VIDEO mode (leverages temporal tracking)
        result = self.landmarker.detect_for_video(mp_image, self._timestamp_ms)

        self.landmarks = None
        self.hand_detected = False

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            hand_landmarks = result.hand_landmarks[0]  # First hand only
            self.hand_detected = True

            # Extract pixel coordinates for each landmark
            self.landmarks = [
                (int(lm.x * frame_w), int(lm.y * frame_h))
                for lm in hand_landmarks
            ]

            # Draw landmarks on the frame
            self._draw_landmarks(frame)

        return self.landmarks

    def _draw_landmarks(self, frame):
        """Draw hand landmarks and connections on the frame with custom styling."""
        if self.landmarks is None:
            return

        landmarks = self.landmarks
        landmark_color = self.landmark_color
        connection_color = self.connection_color
        num_landmarks = len(landmarks)

        # Draw connections first (behind the landmarks) — thin lines for speed
        for start_idx, end_idx in self.hand_connections:
            if start_idx < num_landmarks and end_idx < num_landmarks:
                cv2.line(frame, landmarks[start_idx], landmarks[end_idx],
                         connection_color, 1)

        # Draw landmark points — smaller dots for speed
        for pt in landmarks:
            cv2.circle(frame, pt, 3, landmark_color, -1)

    def is_hand_detected(self):
        """Return whether a hand was detected in the last processed frame."""
        return self.hand_detected

    def get_landmarks(self):
        """Return the current landmark positions."""
        return self.landmarks

    def release(self):
        """Release MediaPipe resources."""
        self.landmarker.close()
