# AGENT.md

# BTIS3053 - AI Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

## Project Overview

This project is a **Software Engineering university assignment**, NOT a commercial video editor.

The objective is to build a **semi-automated AI-assisted multi-camera video editing pipeline** that helps teachers edit kindergarten graduation videos.

The system MUST reduce manual editing while ensuring:

- Human review
- Children's privacy
- PDPA compliance
- Copyright awareness
- AI responsibility
- Open-source licensing awareness

This project is NOT expected to build Adobe Premiere.

Only implement enough features to satisfy the assignment requirements.

---

# Assignment Goals

Input

Camera1.mp4
Camera2.mp4
Camera3.mp4
Camera4.mp4

↓

Synchronize videos

↓

Generate timeline

↓

Select camera

↓

Generate EDL (JSON)

↓

Render final video

↓

Human review

↓

Export MP4

---

# Required Features

## 1. Video Import

Support importing

- mp4
- mov (optional)

UI

```
Import Videos

[ Camera 1 ]
[ Camera 2 ]
[ Camera 3 ]
[ Camera 4 ]
```

Store metadata

- filename
- fps
- resolution
- duration

---

## 2. Synchronization

Choose ONE synchronization method.

Recommended:

Audio clap synchronization using:

Python

audalign

or

FFmpeg offset

Output

```
Camera1 offset : 0 ms
Camera2 offset : +840 ms
Camera3 offset : -520 ms
Camera4 offset : +120 ms
```

Generate synchronized timeline.

---

## 3. Timeline Creation

Create one master timeline.

Every camera should align onto one shared timeline.

Example

```
0 -------------------------- 120 sec

Cam1
======================

Cam2
   ====================

Cam3
=========================

Cam4
      ===================
```

---

## 4. Camera Selection

Implement ONE automation strategy.

Recommended:

Rule-based camera selection.

Example rules

IF

motion is highest

↓

use that camera

OR

speaker closest to center

↓

select camera

OR

manual selection

The assignment only requires ONE automation method.

Do NOT implement machine learning unless necessary.

---

## 5. Segment Detection

Split timeline into scenes.

Example

```
0-15 sec

15-30 sec

30-48 sec

48-70 sec

...
```

Each segment must record

start

end

camera

reason

---

## 6. Editing Decision List (EDL)

Generate JSON.

Example

```json
[
    {
        "start": "00:00:00",
        "end": "00:00:10",
        "camera": "Camera1",
        "transition": "cut",
        "reason": "Front speaker visible"
    },
    {
        "start": "00:00:10",
        "end": "00:00:22",
        "camera": "Camera3",
        "transition": "fade",
        "reason": "Audience reaction"
    }
]
```

This is REQUIRED.

---

## 7. Video Rendering

Read the EDL.

Render automatically using

MoviePy

or

FFmpeg

Produce

Final.mp4

Length

60~180 seconds

Must include

- opening title
- closing credits
- subtitles OR lower-third
- transitions
- at least 2 camera angles
- at least 3 camera switches

---

## 8. Human Review

Before rendering

Display generated EDL

Allow user to

Edit

Delete

Change camera

Change transition

Never claim full automation.

Always state

"Semi-Automated"

---

# Recommended Tech Stack

Language

Python 3.12+

GUI

PySide6

Video

MoviePy

FFmpeg

Synchronization

audalign

OpenCV (optional)

Data

JSON

CSV

Logging

Python logging

Packaging

PyInstaller

---

# Folder Structure

```
project/

│

├── main.py

├── config.py

├── requirements.txt

├── README.md

├── AGENT.md

│

├── assets/

│   ├── intro.mp4

│   ├── outro.mp4

│   └── music/

│

├── videos/

│   ├── cam1.mp4

│   ├── cam2.mp4

│   ├── cam3.mp4

│   └── cam4.mp4

│

├── edl/

│   └── output.json

│

├── output/

│   └── final.mp4

│

├── synchronization/

│   ├── audio_sync.py

│   └── timeline.py

│

├── selection/

│   ├── rules.py

│   ├── motion.py

│   └── camera_selector.py

│

├── renderer/

│   ├── moviepy_renderer.py

│   └── ffmpeg_renderer.py

│

├── subtitle/

│   └── subtitle_generator.py

│

├── ui/

│   ├── main_window.py

│   ├── review_window.py

│   └── timeline_widget.py

│

└── tests/
```

---

# Code Modules

## synchronization/

Responsible for

- loading videos
- audio sync
- offsets
- master timeline

---

## selection/

Responsible for

camera decision

Returns

```
Camera2

Camera1

Camera3

...
```

---

## renderer/

Read JSON EDL

Generate final MP4

---

## ui/

Human review

Buttons

Import

Synchronize

Generate EDL

Review

Render

Export

---

# UI Workflow

```
Import Videos

↓

Synchronize

↓

Generate Timeline

↓

Generate EDL

↓

Human Review

↓

Render

↓

Export MP4
```

---

# Minimum Assignment Requirements

Must satisfy ALL

✅ 2+ camera angles

✅ 3+ camera switches

✅ opening title

✅ ending credits

✅ subtitle or lower-third

✅ transition

✅ JSON EDL

✅ MP4 output

✅ 60–180 sec

---

# Ethics Requirements (Documentation)

The report must discuss:

- Children's privacy
- Parents' consent
- Malaysia PDPA 2010
- Copyright
- AI responsibility
- Human review
- Software licensing

The software should include a README stating:

"This prototype is intended for educational purposes only.
Human review is mandatory before exporting the final video."

---

# AI Rules

Never describe the system as

❌ Fully Automatic

Always use

✅ Semi-Automated

Always allow manual override.

---

# Git Rules

Use feature branches

```
feature/synchronization

feature/renderer

feature/ui

feature/edl
```

Meaningful commits only.

Example

```
Add MoviePy renderer

Implement audio synchronization

Generate JSON EDL

Create review interface

Add timeline visualization
```

---

# Performance Goals

Must run on

Windows 10

Windows 11

CPU only

No GPU required.

---

# Deliverables

Generate

- README.md
- requirements.txt
- JSON EDL
- Final MP4
- Screenshots
- GitHub repository

---

# Out of Scope

Do NOT build:

- Face recognition
- AI person identification
- Cloud processing
- Live streaming
- Commercial editing software
- Full Adobe Premiere clone
- Deep learning camera selection

Keep the project simple, modular, maintainable, and focused on fulfilling the university assignment requirements.
