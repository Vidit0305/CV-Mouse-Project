<![CDATA[<div align="center">

# 🖱️ AI Virtual Mouse — Hand Gesture Control

### ✨ Made by **Vidit Sharma** ✨

> Control your computer's mouse cursor using just your hand — no physical mouse needed.  
> Powered by **AI, Computer Vision & MediaPipe Hand Tracking**.

---

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-00897B?style=for-the-badge&logo=google&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## 📖 Overview

**AI Virtual Mouse** is a real-time computer vision application that lets you control your system's mouse cursor using natural hand gestures captured through a webcam. It uses **Google MediaPipe's Hand Landmarker** model to detect 21 hand landmarks in real time, classifies hand gestures (fist, open palm, pointing, two-finger scroll), and maps them to mouse actions like cursor movement, left/right click, and scrolling.

### 🎯 Key Highlights

- **Touchless Control** — Move, click, and scroll without touching any device
- **Real-Time Processing** — Optimized for 25–40+ FPS on standard hardware
- **Intuitive Gestures** — Natural hand movements mapped to familiar mouse actions
- **Fullscreen Webcam UI** — Immersive display with lightweight HUD overlays
- **Performance-First Design** — Low-resolution capture, EMA smoothing, temporal tracking, and zero-copy pipeline

---

## 🏗️ Architecture

The application follows a **modular pipeline architecture** with five clearly separated concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VirtualMouseApp (main.py)                    │
│                     Orchestrates the full pipeline                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
  ┌──────────────┐   ┌──────────────────┐   ┌────────────────┐
  │ HandTracker  │   │ GestureDetector  │   │MouseController │
  │              │   │                  │   │                │
  │ MediaPipe    │──▶│ Finger State     │──▶│ PyAutoGUI      │
  │ Hand         │   │ Classification   │   │ Cursor/Click   │
  │ Landmarker   │   │ + Edge Detection │   │ + Scroll       │
  └──────────────┘   └──────────────────┘   └────────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  VirtualMouseUI  │
                    │                  │
                    │  Tkinter Window  │
                    │  + OpenCV HUD    │
                    │  Overlays        │
                    └──────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │     utils.py     │
                    │                  │
                    │  Constants,      │
                    │  FPSCounter,     │
                    │  CursorSmoother, │
                    │  Coordinate      │
                    │  Mapping         │
                    └──────────────────┘
```

### 🔄 Frame Processing Pipeline

Each frame goes through the following stages:

```
Webcam Capture → Flip (Mirror) → MediaPipe Hand Detection → Gesture Classification
        │                                                          │
        │              ┌───────────────────────────────────────────┘
        │              ▼
        │     Mouse Action Execution (Move / Click / Scroll)
        │              │
        ▼              ▼
   Draw HUD Overlays (FPS, Gesture, Click Flash, Scroll Indicator)
        │
        ▼
   Display on Tkinter Canvas (Resized to window)
```

---

## 🧠 How It Works

| Stage | Module | Description |
|:------|:-------|:------------|
| **1. Capture** | `main.py` | Captures frames from webcam at 320×240 resolution for maximum FPS |
| **2. Detection** | `hand_tracker.py` | Runs MediaPipe Hand Landmarker in `VIDEO` mode for temporal tracking across frames (faster than per-frame `IMAGE` mode) |
| **3. Classification** | `gesture_detector.py` | Analyzes finger states (up/down) to classify gestures using edge detection to prevent repeated triggers |
| **4. Execution** | `mouse_controller.py` | Maps index finger position to screen coordinates, applies EMA smoothing, and executes mouse actions via PyAutoGUI |
| **5. Display** | `ui.py` | Renders fullscreen webcam feed with OpenCV-drawn HUD overlays (FPS badge, gesture status, click/scroll indicators) |

---

## ✋ Gesture Mappings

| Gesture | Hand Pose | Action | Visual Feedback |
|:--------|:----------|:-------|:----------------|
| **Move Cursor** | ☝️ Index finger up, others curled | Moves the system cursor | Green cursor dot on fingertip |
| **Left Click** | ✊ Fist (all fingers curled) | Single left click | Red flash burst at wrist |
| **Right Click** | 🖐️ Open palm (all fingers extended) | Single right click | Cyan flash burst at wrist |
| **Scroll Up** | ✌️ Index + middle up, move hand upward | Scrolls page up | Blue rings on fingertips + "SCROLL UP" label |
| **Scroll Down** | ✌️ Index + middle up, move hand downward | Scrolls page down | Blue rings on fingertips + "SCROLL DOWN" label |

> **Edge Detection**: Clicks only trigger on gesture *transitions* (e.g., open → fist), not while holding a pose. A cooldown timer prevents accidental double-clicks.

---

## 🗂️ Project Structure

```
AI-Mouse-Vidit/
│
├── main.py                  # 🚀 Entry point — orchestrates all modules
│                            #    Auto-starts camera, runs Tkinter main loop
│
├── hand_tracker.py          # 🖐️ Hand detection & landmark extraction
│                            #    MediaPipe Hand Landmarker (VIDEO mode)
│                            #    Draws landmarks & connections on frame
│
├── gesture_detector.py      # 🧠 Gesture classification engine
│                            #    Finger state analysis, edge detection
│                            #    Scroll direction via movement history
│
├── mouse_controller.py      # 🖱️ System mouse control
│                            #    PyAutoGUI cursor movement, clicks, scroll
│                            #    EMA-smoothed cursor for jitter-free movement
│
├── ui.py                    # 🎨 Fullscreen webcam UI
│                            #    Tkinter window + OpenCV HUD overlays
│                            #    FPS badge, gesture status, click/scroll visuals
│
├── utils.py                 # ⚙️ Shared constants, helpers & utilities
│                            #    FPSCounter, CursorSmoother, coordinate mapping
│                            #    Colors, thresholds, landmark IDs
│
├── requirements.txt         # 📦 Python dependencies
│
└── assets/
    └── hand_landmarker.task # 🤖 MediaPipe hand landmark model (float16)
```

---

## 📋 File Descriptions

### `main.py` — Application Entry Point
- Initializes all modules (`HandTracker`, `GestureDetector`, `MouseController`, `VirtualMouseUI`)
- Auto-starts the webcam camera on launch
- Runs the **frame processing loop** via Tkinter's `after()` scheduler (non-blocking)
- Handles graceful cleanup on ESC key or window close

### `hand_tracker.py` — Hand Detection & Landmarks
- Wraps **MediaPipe Hand Landmarker** (Tasks API) for hand detection
- Operates in **VIDEO running mode** — uses temporal tracking across frames for significantly faster inference than per-frame IMAGE mode
- Extracts **21 landmark pixel coordinates** from detected hands
- Draws landmark points (green) and skeletal connections (blue) on the frame
- Requires the `hand_landmarker.task` model file in `assets/`

### `gesture_detector.py` — Gesture Classification
- Classifies gestures from finger states: **Move**, **Left Click** (fist), **Right Click** (palm), **Scroll Up/Down**
- Uses **edge detection** — clicks fire only on state *transitions*, not while holding
- Implements **cooldown timers** to prevent accidental repeated clicks
- Tracks **scroll history** (deque of Y-positions) to detect vertical hand movement direction

### `mouse_controller.py` — Mouse Control
- Maps index finger camera coordinates → screen coordinates using ROI (Region of Interest) mapping
- Applies **Exponential Moving Average (EMA)** smoothing for jitter-free cursor movement
- Executes left click, right click, and scroll via **PyAutoGUI**
- Includes PyAutoGUI **failsafe** (move cursor to screen corner to abort)

### `ui.py` — User Interface
- **Fullscreen webcam display** using Tkinter — camera feed fills the entire window
- All status info rendered as **lightweight OpenCV overlays** directly on the frame:
  - **FPS badge** (top-left) — color-coded: green ≥25, orange ≥15, red <15
  - **Gesture status** (below FPS) — shows hand detection state and current gesture
  - **Click flash** — red/cyan burst animation at wrist on click (300ms duration)
  - **Scroll indicator** — blue rings and directional label on scroll gesture
- Optimized rendering: color-convert on small frame *before* upscaling

### `utils.py` — Constants & Utilities
- **Screen/Camera configuration**: resolution, ROI boundaries, sensitivity
- **FPSCounter**: rolling-average FPS using `deque` for O(1) operations
- **CursorSmoother**: EMA filter for smooth cursor movement
- **Coordinate mapping**: camera-to-screen mapping with ROI clamping
- **Finger detection**: `is_finger_up()` helper using landmark Y-comparison
- **Color constants**: dark theme (Tkinter) + BGR drawing colors (OpenCV)
- **MediaPipe landmark IDs**: named constants for all 21 hand landmarks

---

## 🛠️ Languages & Technologies

| Technology | Purpose |
|:-----------|:--------|
| **Python 3.10+** | Core programming language |
| **OpenCV** (`opencv-python ≥4.8.0`) | Webcam capture, frame processing, drawing overlays |
| **MediaPipe** (`mediapipe ≥0.10.0`) | AI hand landmark detection (21-point model) |
| **PyAutoGUI** (`pyautogui ≥0.9.54`) | System-level mouse cursor control |
| **NumPy** (`numpy ≥1.24.0`) | Array operations for frame manipulation |
| **Pillow** (`Pillow ≥10.0.0`) | Image format conversion (OpenCV → Tkinter) |
| **Tkinter** (built-in) | GUI framework for the application window |

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10** or higher
- **Webcam** (built-in or external)
- **Windows OS** (tested; may work on macOS/Linux with minor adjustments)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/AI-Mouse-Vidit.git
   cd AI-Mouse-Vidit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download the MediaPipe model** (if not already present in `assets/`)
   ```bash
   # The hand_landmarker.task file should be in assets/
   # Download from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Exit**: Press `ESC` or close the window.

---

## ⚡ Performance Optimizations

| Optimization | Impact |
|:-------------|:-------|
| **320×240 camera resolution** | 4× fewer pixels vs 640×480 → faster MediaPipe inference |
| **VIDEO running mode** | Temporal tracking — skips full re-detection between frames |
| **EMA cursor smoothing** | Eliminates jitter without adding latency |
| **`math.hypot`** | ~40% faster than manual `sqrt(dx² + dy²)` |
| **Scalar `min`/`max`** | Avoids NumPy array overhead in coordinate mapping |
| **`deque` with `maxlen`** | O(1) append/eviction for FPS counter and scroll history |
| **Color-convert before upscale** | Converts 320×240 frame, then resizes — much cheaper |
| **`INTER_NEAREST` resize** | Fastest interpolation for display upscaling |
| **`cv2.CAP_PROP_BUFFERSIZE=1`** | Minimizes webcam frame latency |

---

## 🎮 Usage Tips

- **Comfortable Range**: Keep your hand within the center 80% of the camera frame (ROI mapping handles this automatically)
- **Good Lighting**: Ensure your hand is well-lit for reliable detection
- **Distance**: Hold your hand about 30–60 cm from the webcam
- **Failsafe**: Move your physical mouse to any screen corner to immediately abort
- **Gestures**: Make deliberate, clean gestures — transition smoothly between poses

---

## 📐 Configuration

Key parameters can be adjusted in `utils.py`:

| Parameter | Default | Description |
|:----------|:--------|:------------|
| `CAMERA_WIDTH` | 320 | Camera capture width (lower = faster) |
| `CAMERA_HEIGHT` | 240 | Camera capture height |
| `CLICK_COOLDOWN` | 0.4s | Minimum time between consecutive clicks |
| `SCROLL_THRESHOLD` | 8px | Vertical movement required to trigger scroll |
| `SCROLL_SPEED` | 5 | Scroll amount per detected scroll gesture |
| `SMOOTHING_FACTOR` | 0.7 | EMA cursor smoothing (higher = more responsive) |
| `SENSITIVITY` | 1.5 | Mouse speed multiplier |
| `ROI_LEFT/TOP/RIGHT/BOTTOM` | 0.1–0.9 | Camera frame region mapped to full screen |

---

## 🧩 Extending the Project

The modular architecture makes it easy to extend:

- **Add new gestures**: Implement detection logic in `gesture_detector.py` and corresponding actions in `mouse_controller.py`
- **Custom UI overlays**: Add drawing methods in `ui.py`
- **Multi-hand support**: Increase `max_hands` in `hand_tracker.py` and handle multiple landmark sets
- **Drag & drop**: Track fist-hold duration in `gesture_detector.py` and use `pyautogui.mouseDown()`/`mouseUp()`

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

### 🙌 Made with ❤️ by **Vidit Sharma**

*AI Virtual Mouse — Turning hand gestures into seamless computer control.*

---

**© 2026 Vidit Sharma. All Rights Reserved.**

</div>
]]>
