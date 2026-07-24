# BTIS3053 - AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

> **ETHICS & LEGAL NOTICE**  
> *"This prototype is intended for educational purposes only. Human review is mandatory before exporting the final video."*

---

## 📌 Project Overview

This software is developed for the **BTIS3053 Software Engineering university assignment**. It provides a **semi-automated AI-assisted video editing pipeline** designed to reduce manual editing effort for teachers assembling kindergarten graduation videos from up to 4 camera angles.

---

## ⚖️ Ethics, Privacy & Compliance Declaration

### 1. Children's Privacy & Parent Consent
- All video recording of minors requires explicit, signed parental/guardian consent forms prior to filming.
- Video materials are strictly stored locally on authorized educational devices and never uploaded to public clouds.

### 2. Malaysia Personal Data Protection Act (PDPA) 2010 Compliance
- In accordance with **Malaysia PDPA 2010**, personal data (including video recordings and names of minors) is processed under lawful consent.
- Data access is restricted to authorized school staff and university course evaluators.

### 3. AI Responsibility & "Semi-Automated" System Scope
- The system operates **strictly as a Semi-Automated Assistant**.
- Artificial intelligence heuristics perform candidate camera selection, but **Mandatory Human Review** is required before exporting final videos.
- Automated suggestions can be overridden, re-ordered, or deleted in the Human Review interface.

### 4. Copyright & Software Licensing Awareness
- Built using open-source libraries: **PySide6** (LGPLv3), **MoviePy** (MIT), **OpenCV** (Apache 2.0), **NumPy/SciPy** (BSD).
- All title card fonts and background assets use open-source / royalty-free licenses.

---

## 🛠️ Architecture & Features

```
[Import 4 Cameras] ➔ [Audio Sync Cross-Correlation] ➔ [Master Timeline] ➔ [AI Motion & Rule Selection] ➔ [JSON EDL] ➔ [Human Review UI] ➔ [MoviePy Renderer] ➔ [Final MP4]
```

### Key Modules:
- `synchronization/`: Performs sample-accurate audio cross-correlation to compute sub-second time offsets (`Camera1 offset: 0ms`, `Camera2 offset: +800ms`, etc.).
- `selection/`: OpenCV optical motion estimation combined with rule heuristics (highest motion, speaker focus, minimum shot duration).
- `edl/`: Manages JSON Edit Decision List (EDL) specifications.
- `subtitle/`: Generates Opening Title Cards, Lower-Third overlays, and Outro Credits using Pillow.
- `renderer/`: MoviePy multi-track composition engine applying trimming, camera offsets, transitions (cut/fade), and overlays.
- `ui/`: Interactive PySide6 desktop interface with visual multi-track timeline and EDL table editor.

---

## 📋 University Assignment Requirements Checklist

| Requirement | Status | Implementation |
|---|---|---|
| **2+ Camera Angles** | ✅ Satisfied | Uses Camera1, Camera2, Camera3, Camera4 |
| **3+ Camera Switches** | ✅ Satisfied | Minimum 4 cut segments generated in EDL |
| **Opening Title Card** | ✅ Satisfied | "Kindergarten Graduation 2026" full-screen card |
| **Ending Credits Card** | ✅ Satisfied | "Congratulations Graduates!" credits card |
| **Subtitles / Lower-Third**| ✅ Satisfied | Semi-transparent lower-third box with camera angle & AI reason |
| **Transitions** | ✅ Satisfied | Supports Cuts and Fade-in/Fade-out transitions |
| **JSON EDL Export** | ✅ Satisfied | Exported to `edl/output.json` |
| **Final MP4 Output** | ✅ Satisfied | Rendered to `output/final.mp4` (60–180s) |
| **Human Review UI** | ✅ Satisfied | PySide6 interactive EDL table editor |
| **Ethics & Privacy Report**| ✅ Satisfied | Documented in README & GUI header |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Test Videos (Instant Out-of-the-Box Testing)
Generate 4 synchronized sample camera MP4 files with audio sync claps and visual motion graphics:
```bash
python scripts/generate_test_videos.py
```

### 3. Launch PySide6 GUI Application
```bash
python main.py
```

### 4. Headless CLI Pipeline Execution
```bash
python main.py --cli
```

---

## 📁 Directory Structure
```
ai-editor/
├── config.py                 # Global configurations & paths
├── requirements.txt           # Python dependencies
├── main.py                    # Application entry point (GUI/CLI)
├── README.md                  # Project & ethics documentation
├── project.md                 # Assignment specification
│
├── assets/                    # Intro/outro & music assets
├── videos/                    # Source camera MP4 files
├── edl/                       # JSON EDL outputs
├── output/                    # Rendered final MP4 videos
│
├── synchronization/           # Audio sync & master timeline
│   ├── audio_sync.py
│   └── timeline.py
├── selection/                 # Motion analysis & camera selection rules
│   ├── motion.py
│   ├── rules.py
│   └── camera_selector.py
├── edl/                       # EDL JSON manager
│   └── edl_manager.py
├── subtitle/                  # Title cards & lower-third overlays
│   └── subtitle_generator.py
├── renderer/                  # MoviePy video rendering engine
│   └── moviepy_renderer.py
├── ui/                        # PySide6 Desktop GUI components
│   ├── main_window.py
│   ├── review_window.py
│   └── timeline_widget.py
└── scripts/                   # Synthetic test video generator
    └── generate_test_videos.py
```
