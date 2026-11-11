# PolyGen: AI-Powered Text-to-3D Model Generation

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?style=flat&logo=react)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/3D_Engine-Three.js_/_R3F-black.svg?style=flat&logo=three.js)](https://threejs.org/)
[![Wavefront OBJ](https://img.shields.io/badge/Export_Format-Wavefront_OBJ-orange.svg?style=flat)]()
[![Status](https://img.shields.io/badge/Milestone-Week_1_Complete-success.svg?style=flat)]()

**PolyGen** is an end-to-end generative AI pipeline designed to convert natural language text prompts into interactive 3D mesh assets exported in industry-standard Wavefront OBJ format and rendered in a real-time web-based 3D viewport.

This repository contains the complete **Week 1 Implementation: Environment Setup and Text-to-3D Generation Pipeline**.

---

## 🎯 Week 1 Milestone Objectives

- [x] **Backend Infrastructure (Python + FastAPI)**:
  - Text prompt reception, preprocessing, and input validation.
  - Hybrid Text-to-3D generation engine supporting both:
    1. Built-in **PolyGen Procedural & Semantic AI Engine** for instant offline generation without paid keys.
    2. Cloud Text-to-3D API integrations (**Meshy API** and **Tripo3D API**) via optional `.env` credentials.
  - Geometry synthesis with vertex calculations, smooth normal computations, bounding box normalization, and Wavefront `.obj` export.
  - RESTful API endpoints for generation, model serving, history listing, and health checks.
  - Directory traversal protection and robust error handling.
- [x] **Frontend Studio (React + Three.js + React Three Fiber)**:
  - Sleek modern dark-theme dashboard with prompt input, character count, and preset suggestions.
  - Real-time 3D viewport using `@react-three/fiber` and `@react-three/drei`.
  - Interactive camera controls: orbit rotation, smooth zoom, pan, and reset.
  - Studio lighting rig (key light, fill light, hemisphere light, ground grid).
  - Multi-material shading modes (Clay Studio, Chrome Metal, Stylized Purple, Normal Map, Wireframe).
  - One-click Wavefront OBJ direct download.
  - Loading states, error alerts, and live mesh geometry statistics (vertices, faces, dimensions).

---

## 🏗️ Architecture & Pipeline Overview

```
                          ┌───────────────────────────┐
                          │   User Natural Prompt     │
                          │   "low-poly wooden chair" │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │       PolyGen React Studio (Vite)       │
                   │   - Prompt Input & Preset Chips         │
                   │   - Art Style & Provider Selection      │
                   └────────────────────┬────────────────────┘
                                        │ HTTP POST /api/generate
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │         FastAPI Backend Server          │
                   │   - Input sanitization & validation     │
                   │   - Provider routing & fallbacks        │
                   └────────────────────┬────────────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 │                                             │
                 ▼                                             ▼
  ┌─────────────────────────────┐               ┌─────────────────────────────┐
  │ Built-in Semantic AI Engine │               │   Cloud Text-to-3D APIs     │
  │ - Keyword & intent parsing  │               │   (Optional Meshy / Tripo)  │
  │ - Parametric mesh synthesis │               │   - Polled task pipeline    │
  │ - Normal generation & bounds│               │   - Cloud mesh fetching     │
  └──────────────┬──────────────┘               └──────────────┬──────────────┘
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │         Wavefront OBJ Exporter          │
                   │   - Standard `v`, `vn`, `vt`, `f` lines │
                   │   - Saved to `backend/models/*.obj`     │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │    WebGL 3D Viewport (Three.js / R3F)   │
                   │   - OrbitControls (rotate/pan/zoom)     │
                   │   - Dynamic Shading & Wireframe modes   │
                   │   - Direct OBJ Download                 │
                   └─────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
PolyGen/
├── backend/
│   ├── generate_3d.py       # Core Text-to-3D geometry synthesis & OBJ exporter
│   ├── main.py              # FastAPI application, endpoints & CORS middleware
│   ├── requirements.txt     # Python backend dependencies
│   ├── test_api.py          # Automated backend test suite
│   ├── .env.example         # Template for optional external API keys
│   └── models/              # Storage directory for generated .obj files
├── frontend/
│   ├── index.html           # HTML5 entrypoint
│   ├── package.json         # React & Three.js dependencies
│   ├── vite.config.js       # Vite build configuration with API reverse proxy
│   └── src/
│       ├── main.jsx         # React application root
│       ├── App.jsx          # Studio layout, state management & API integration
│       ├── index.css        # Cyberpunk/dark-studio UI design system
│       └── components/
│           └── ModelViewer.jsx  # Three.js Canvas, OrbitControls & OBJ loader
└── README.md                # Project documentation
```

---

## ⚙️ Prerequisites

- **Python**: Version 3.10+ (tested with Python 3.12)
- **Node.js**: Version 18+ (tested with Node.js v24)
- **Operating System**: Windows, macOS, or Linux

---

## 🚀 Quick Start Guide

### Step 1: Backend Setup (Python + FastAPI)

1. Open a terminal in the project root directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* Configure Cloud Text-to-3D API keys:
   Copy `.env.example` to `.env` and insert your keys if you wish to use Meshy or Tripo3D:
   ```bash
   cp .env.example .env
   ```
   > **Note:** If no API key is configured, PolyGen will automatically use its built-in offline Semantic AI engine.

5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will be live at `http://localhost:8000` (Interactive docs at `http://localhost:8000/docs`).

---

### Step 2: Frontend Setup (React + Three.js)

1. In a second terminal window, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 🔌 API Endpoint Documentation

### 1. `POST /api/generate`
Generates a new 3D model from a user-supplied text prompt and art style.

**Request Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "prompt": "a low-poly medieval broadsword with golden hilt",
  "style": "low-poly",
  "provider": "auto"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "model_id": "polygen_a_low_poly_medieval_br_f085ddba",
  "prompt": "a low-poly medieval broadsword with golden hilt",
  "style": "low-poly",
  "filename": "polygen_a_low_poly_medieval_br_f085ddba.obj",
  "model_url": "/api/models/polygen_a_low_poly_medieval_br_f085ddba.obj",
  "download_url": "/api/models/polygen_a_low_poly_medieval_br_f085ddba.obj?download=true",
  "file_size": 15469,
  "metadata": {
    "vertex_count": 129,
    "face_count": 204,
    "dimensions": {
      "min": [-0.275, 0.0, -0.04],
      "max": [0.275, 2.0, 0.04],
      "width": 0.55,
      "height": 2.0,
      "depth": 0.08
    },
    "provider": "polygen-semantic-ai",
    "generation_time_ms": 42.38
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "futuristic spaceship", "style": "low-poly"}'
```

---

### 2. `GET /api/models/{filename}`
Streams the generated `.obj` model file. Used directly by Three.js `OBJLoader` or browser downloads.

**Query Parameters:**
- `download=true` *(optional)*: Sets `Content-Disposition: attachment` to trigger browser file save.

**cURL Example:**
```bash
curl -O http://localhost:8000/api/models/polygen_a_low_poly_medieval_br_f085ddba.obj
```

---

### 3. `GET /api/history`
Returns recently generated models stored on the server.

**Response (200 OK):**
```json
{
  "count": 5,
  "models": [
    {
      "model_id": "polygen_ancient_broadsword_f085ddba",
      "filename": "polygen_ancient_broadsword_f085ddba.obj",
      "model_url": "/api/models/polygen_ancient_broadsword_f085ddba.obj",
      "download_url": "/api/models/polygen_ancient_broadsword_f085ddba.obj?download=true",
      "file_size": 15469,
      "created_at": 1794299768.0
    }
  ]
}
```

---

### 4. `GET /api/health`
Health check endpoint reporting backend server status, model storage counts, and provider availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "polygen-backend",
  "models_in_store": 6,
  "providers": {
    "local_semantic_ai": "active",
    "meshy_api": "not_configured (API key missing)",
    "tripo_api": "not_configured (API key DIC missing)"
  },
  "timestamp": 1794299326.64
}
```

---

## 🎨 Supported Categories & Suggested Prompts

PolyGen's built-in synthesis engine recognizes diverse semantic categories and generates clean manifold 3D meshes:

| Category | Example Prompts | Geometric Features |
|---|---|---|
| **Weapons & Armor** | `"medieval broadsword"`, `"ornate battle shield"` | Pommel, wrapped hilt, crossguard, tapered blade with fuller, curved heater shield with center boss |
| **Furniture** | `"low-poly wooden chair"`, `"dining table"` | Beveled seat, 4 tapered cylindrical legs, curved backrest with uprights and slats |
| **Vehicles** | `"cyberpunk flying car"`, `"futuristic spaceship"` | Slanted chassis, cockpit canopy, 4 wheels/tires, swept delta wings, twin engine nacelles |
| **Aeronautics** | `"space rocket"`, `"apollo booster"` | Cylindrical stage body, aerodynamic nosecone, 4 delta stabilizer fins, engine nozzle |
| **Architecture** | `"cozy cottage house"`, `"medieval tower"` | Foundation walls, pitched gable roof, stone chimney, door recess |
| **Nature** | `"pine tree"`, `"forest plant"` | Organic tapered trunk, layered 3-tier conical foliage canopy |
| **Everyday Objects** | `"ceramic coffee mug"`, `"glazed donut"` | Cylindrical body with torus handle, wavy surface torus |
| **Crystals & Gems** | `"faceted diamond gemstone"`, `"magic crystal"` | Multi-faceted brilliant-cut bipyramid with crown and pavilion |
| **Arbitrary Prompts** | *"Any creative prompt"* | Parametric harmonic surface synthesis driven by prompt seed |

---

## 🖥️ 3D Viewport Controls & Features

- **Interactive OrbitControls**:
  - **Left Click + Drag**: Orbit / Rotate model in 3D space.
  - **Right Click + Drag**: Pan camera horizontally and vertically.
  - **Scroll Wheel**: Smooth zoom in / zoom out with clamped min/max distance.
- **Floating Studio Toolbar**:
  - **Rotate**: Toggle automated smooth 360° turntable rotation.
  - **Wireframe**: Toggle geometric wireframe overlay to inspect mesh topology.
  - **Grid**: Toggle spatial ground grid for scale reference.
  - **Material Selector**:
    - `Clay Studio`: Neutral matte studio shading with soft highlights.
    - `Chrome Metal`: Highly reflective metallic PBR shading.
    - `Stylized Purple`: High-contrast game-asset shading.
    - `Normal Map`: Visualizes geometric surface normal vectors in RGB.
  - **Reset**: Instantly restores default camera position and perspective.
- **Export**: One-click download button to save the current asset as a standard `.obj` file.

---

## 🧪 Testing

Run the automated backend test suite to verify all endpoints, validation logic, and geometry generation:

```bash
cd backend
python test_api.py
```

Expected output:
```text
========================================
 Running PolyGen Backend Test Suite
========================================
[PASS] 1. Health check endpoint
[PASS] 2. Generation (chair) -> polygen_a_low_poly_wooden_chair_e437c5ac.obj (156 verts, 264 faces)
[PASS] 3. Generation (crystal) -> polygen_futuristic_neon_cyber_cr_1c216df5.obj (18 verts)
[PASS] 4. Blank prompt validation correctly caught (HTTP 400)
[PASS] 5. Short prompt validation correctly caught (HTTP 400)
[PASS] 6. Model file retrieval -> 15469 bytes
[PASS] 7. Directory traversal defense verified
[PASS] 8. History listing -> 5 models found
========================================
 ALL BACKEND TESTS PASSED (8/8)!
========================================
```

---

## 👥 Contributors

- **PolyGen Team** – Week 1: Environment Setup and Text-to-3D Generation Pipeline

