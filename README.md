# Spinepose PRO v2.0 🧬

**Zero-Latency. Offline-First. AI-Powered.**

Spinepose PRO is a next-generation biomechanics analysis platform designed for both clinical and athletic performance. By running entirely on the edge (localized inference), it delivers real-time spinal health metrics without the need for cloud connectivity or expensive hardware.

---

## 🚀 Key Features

### 1. Zero-Latency Hybrid Engine
*   **Local Inference:** Powered by a custom `HybridEngine` combining YOLOv8 (Object Detection) and MediaPipe (Pose Estimation).
*   **Offline Capability:** Fully functional without an internet connection. All assets (fonts, icons, models) are served locally.

### 2. "Cyber-Medical" Interface
*   **Bento Grid Layout:** A modular, high-density dashboard inspired by modern data visualization trends.
*   **Glassmorphism:** Sleek, translucent panels with a Deep Space Blue & Neon Cyan aesthetic.
*   **Control Dock:** A centralized "cockpit" control bar for easy access to all modes.

### 3. Dual-Domain RAG System
The system features a Retrieval-Augmented Generation (RAG) backend that contextualizes live data against a curated Knowledge Base:
*   **🏥 Medical Mode:** Compares user posture against X-ray standards (Scoliosis, Kyphosis).
*   **🏃 Sports Mode:** Analyzes athletic form (Golf Swing, Squat, Running) against pro-athlete benchmarks.

---

## 🏗️ Technical Architecture

### 1. Hybrid Engine (Local Inference)
The core of Spinepose PRO is the `HybridEngine` (located in `spine_engine/core/session.py`). It orchestrates a two-stage pipeline:
*   **Stage 1: YOLOv8 Nano:** Instantly detects humans in the frame, cropping the region of interest (ROI) to maximize accuracy.
*   **Stage 2: MediaPipe Pose:** Runs high-fidelity landmark extraction (33 keypoints) on the cropped ROI.
*   **Optimization:** This handoff ensures that the heavier pose model only processes relevant pixels, maintaining 30+ FPS on consumer hardware.

### 2. Biomechanics Geometry
Raw keypoints are transformed into clinical metrics using vector mathematics (`spine_engine/analysis/geometry.py`):
*   **Cobb Angle:** Calculated using the arctangent of vectors between the shoulder girdle (Acromion) and pelvic girdle (Iliac Crest).
*   **Lumbar Flexion:** Measures the relative angle between the thoracic spine vector and the femur.
*   **Head Drop:** Tracks the tragus (ear) position relative to the C7 vertebrae benchmark.

### 3. RAG Knowledge System
We built a custom lightweight RAG (Retrieval-Augmented Generation) system:
*   **Ingestion:** Python scripts (`tools/ingest_*.py`) scrape and normalize reference images from open medical and sports repositories.
*   **Indexing:** Images are tagged with metadata (`domain`, `activity`, `condition`) and stored in a local JSONL database (`spine_db/index.jsonl`).
*   **Retrieval:** The backend queries this index in <5ms to fetch context-aware comparison overlays (e.g., showing a "Pro Golf Swing" overlay when the user enters Sports Mode).

### 4. Zero-Latency Frontend
The UI avoids heavy frameworks (React/Angular) in favor of Vanilla JS and CSS3 Variables for maximum performance:
*   **Rendering:** Video frames are streamed via WebSocket as binary blobs, rendering directly to an HTML5 Canvas.
*   **Styling:** "Bento Grid" layout uses CSS Grid with fallback flexbox, ensuring responsiveness without layout shift.

---

## 🛠️ Installation

### Prerequisites
*   Python 3.9+
*   Webcam

### Setup
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/MohithS04/Software-Spinepose.git
    cd "Software Spinepose"
    ```
2. Create and Activate Virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   # Note: On Windows, use: .venv\Scripts\activate
   ```
3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**
    ```bash
    python server.py
    ```
    *The application will launch at `http://localhost:8000`*

---

## 🎮 Usage Guide

### The Dashboard
Upon launching, you will see the **Spinepose PRO Dashboard**.

1.  **Select Mode:**
    *   Click **Medical** for clinical posture analysis.
    *   Click **Sports** for athletic form tracking.
2.  **Start Analysis:**
    *   Press the large Cyan **START LIVE ANALYSIS** button in the dock.
3.  **Control Dock Tools:**
    *   📁 **Upload:** Analyze pre-recorded videos or images.
    *   🎥 **Camera:** Toggle the live feed view.
    *   📷 **Save:** Take a high-res screenshot of the analysis.
    *   🔴 **REC:** Record the current session to the RAG database.

### Public Access (Tunneling)
To share your local instance publicly:
```bash
npx localtunnel --port 8000
```
**Active Public Link:** [https://tame-swans-exist.loca.lt](https://tame-swans-exist.loca.lt)
*(Note: Link active only while local server is running)*

---

## 🤖 Credits & Attribution
**Lead Architect & Co-Developer:** [Gemini 2.0](https://deepmind.google/technologies/gemini/)

*   **Code Generation:** 90%+ of the backend logic and CSS styling.
*   **Architecture:** Design of the Offline-First RAG system and Hybrid Engine.
*   **UI/UX:** Concept and implementation of the "Cyber-Medical" Bento Grid.

---
*Built for the Future of Digital Health.*
