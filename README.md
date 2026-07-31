# 🎓 BTIS3053 - AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

> **ETHICS & LEGAL NOTICE**  
> *"This software is developed strictly for university educational purposes. Mandatory Human Review is required before exporting final videos. Ensure full compliance with Malaysia Personal Data Protection Act (PDPA) 2010."*

---

## 📌 Project Overview

This application is designed for the **BTIS3053 Social & Professional Issues university project**. It provides a **Semi-Automated AI-Assisted Multi-Camera Video Editing Pipeline** to automate the synchronization, selection, and rendering of kindergarten graduation ceremony footage recorded from up to 4 camera angles, reducing manual editing effort for teachers while upholding children's privacy and data protection rights.

---

## ⚖️ Ethics, Privacy & Legal Compliance Declarations

### 1. Children's Privacy & Parental Consent
- Filming minors requires signed parental/guardian consent prior to recording.
- All video assets are processed strictly **locally on authorized educational hardware** and are never uploaded to third-party public clouds or unverified online servers.

### 2. Malaysia Personal Data Protection Act (PDPA) 2010 (Act 709) Compliance
- Identifiable video footage containing faces, voices, school uniforms, or names of minors constitutes sensitive personal data.
- Data processing complies with lawful consent rules, with access restricted strictly to course evaluators and authorized school staff. Local storage is deleted after course grading.

### 3. AI Responsibility & "Semi-Automated" System Scope
- The system operates strictly as a **Semi-Automated Assistant**.
- AI algorithms perform candidate camera selection, but **Mandatory Human Review** is enforced. Teachers can override, reorder, or delete cuts prior to final rendering.

### 4. Copyright & Open-Source Software Licensing
- Built using open-source libraries: **PySide6** (LGPLv3), **MoviePy** (MIT), **OpenCV** (Apache 2.0), **NumPy/SciPy** (BSD).
- Audio and title font assets rely exclusively on open-source or royalty-free licenses.

---

## 🛠️ Architecture & Multi-Modal AI Pipeline

```
┌─────────────────┐    ┌──────────────────────────┐    ┌─────────────────────────┐
│ 4 Camera Feeds  │ ──►│ Audio Sync (FFT Correlation)│ ──►│ Master Alignment        │
└─────────────────┘    └──────────────────────────┘    └─────────────────────────┘
                                                                    │
┌─────────────────┐    ┌──────────────────────────┐                 ▼
│ Rendered MP4    │ ◄──│ Human Review GUI Window  │ ◄── ┌─────────────────────────┐
└─────────────────┘    └──────────────────────────┘     │ Multi-Modal AI Selection│
                                                        │ (Motion + Loudness +    │
                                                        │  programme.csv Events)  │
                                                        └─────────────────────────┘
```

### Key Modules:
- `synchronization/`: Computes sub-second time offsets via audio cross-correlation (`Camera1: 0ms`, `Camera2: +800ms`, etc.).
- `selection/`: Multi-Modal AI Engine combining OpenCV optical frame differencing ($70\%$) with audio RMS energy loudness ($30\%$) and applause peak detection.
- `programme.py`: Parses ceremony schedules (`assets/programme.csv`) to attach event titles (*"Opening Speech"*, *"Dance Performance"*, *"Diploma Presentation"*) to AI decision reasons.
- `edl/`: EDL manager supporting dual JSON (`output.json`) and Excel-compatible CSV (`output.csv`) export/import.
- `subtitle/`: Pillow-based graphics engine with automatic **Chinese CJK font fallback** (`msyh.ttc` / `simhei.ttf`) and **OpenAI Whisper AI** speech-to-text captions (`whisper_transcriber.py`) for automated Chinese/English speech transcription.
- `renderer/`: MoviePy multi-track composition engine with cut/crossfade transitions and low-resource Fast Draft Mode (`480p @ 15fps`).
- `ui/`: PySide6 dark mode GUI featuring a visual multi-track timeline painter, table editor, and **embedded real-time Video Cut Preview Player** (`VideoPreviewWidget`).


---

## 📊 University Assignment Marking Rubric Mapping (100 Marks Target)

| Rubric Criteria | Marks | Implementation Details |
|---|---|---|
| **System Overview & Setup (CLO1)** | 10 Marks | Modular architecture, comprehensive documentation, and complete data flow diagrams. |
| **AI Enhancement & Accuracy** | 15 Marks | **Multi-Modal AI Engine**: Combines visual motion differencing with audio RMS energy & audience applause peak detection. |
| **Low-Resource Optimization (CLO1-2)** | 15 Marks | 320x180 frame downsampling, frame step skipping, and 480p Fast Draft Mode (`--draft`). |
| **Windows Installer Deployment** | 25 Marks | PyInstaller spec (`ai_editor.spec`), automated build script (`scripts/build_exe.py`), batch runner (`build.bat`), and Inno Setup installer (`scripts/setup_installer.iss`). |
| **Ethics, PDPA & Legal (CLO1-3)** | 15 Marks | In-app headers, parental consent declarations, Malaysia PDPA 2010 compliance notes, and open-source license audit. |
| **Human Review & EDL Workflow** | 20 Marks | PySide6 Human Review dialog with **live Video Cut Preview Player**, table editor, dual JSON/CSV export, and `programme.csv` ceremony event integration. |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Test Videos (Instant Offline Testing)
Generate 4 synchronized sample camera MP4 files with audio sync claps and visual graphics:
```bash
python scripts/generate_test_videos.py
```

### 3. Launch PySide6 Desktop GUI Application
```bash
python main.py
```

### 4. Headless CLI Pipeline Execution
```bash
# Master Quality Mode (720p HD @ 30 FPS)
python main.py --cli

# Fast Low-Resource Draft Mode (480p SD @ 15 FPS ~5s render)
python main.py --cli --draft
```

### 5. Build Standalone Windows Executable (.exe)
```bash
# Run automated build script
python scripts/build_exe.py

# OR double-click build.bat in Windows Explorer
```
Output executable bundle is located in `dist/AI_Video_Editor/` and packaged as `dist/BTIS3053_AI_Video_Editor_Windows.zip`.

---

## 📁 Directory Structure
```
ai-editor/
├── config.py                 # Global parameters, draft modes & file paths
├── requirements.txt           # Python dependency specifications
├── main.py                    # Main application entry point (GUI / CLI)
├── ai_editor.spec             # PyInstaller standalone executable specification
├── build.bat                  # 1-click Windows build batch script
├── README.md                  # Comprehensive project & ethics documentation
├── project.md                 # University assignment specification
│
├── assets/                    # Ceremony assets & schedule
│   ├── programme.csv          # Ceremony schedule timestamps & event names
│   └── music/                 # Optional background music tracks
│
├── videos/                    # Source camera MP4 files (Camera1-Camera4)
├── edl/                       # Output EDLs (output.json & output.csv)
├── output/                    # Exported MP4 videos (final.mp4 / final_draft.mp4)
│
├── synchronization/           # Audio sync & master timeline engine
│   ├── audio_sync.py
│   └── timeline.py
├── selection/                 # Multi-Modal AI selection engine
│   ├── motion.py              # OpenCV visual frame differencing
│   ├── audio_analysis.py      # Audio RMS energy & applause peak detection
│   ├── programme.py           # Ceremony event schedule parser
│   ├── rules.py               # Multi-modal heuristic rule engine
│   └── camera_selector.py     # Candidate EDL segment generator
├── edl/                       # EDL JSON & CSV manager
│   └── edl_manager.py
├── subtitle/                  # Title cards & lower-third overlays
│   └── subtitle_generator.py
├── renderer/                  # MoviePy video rendering engine
│   └── moviepy_renderer.py
├── ui/                        # PySide6 Desktop GUI components
│   ├── main_window.py         # Main window & timeline visualizer wrapper
│   ├── review_window.py       # Human Review split-view dialog
│   ├── video_player.py        # Embedded real-time video cut preview player
│   └── timeline_widget.py     # Custom multi-track timeline QPainter
└── scripts/                   # Utility scripts
    ├── generate_test_videos.py # Synthetic 4-camera video generator
    ├── build_exe.py           # Automated PyInstaller packaging script
    └── setup_installer.iss    # Inno Setup Windows installer wizard script
```
