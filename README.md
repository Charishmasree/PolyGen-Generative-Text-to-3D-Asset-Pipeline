# PolyGen: Generative Text-to-3D Asset Pipeline

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?style=flat&logo=react)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/3D_Engine-Three.js_/_R3F-black.svg?style=flat&logo=three.js)](https://threejs.org/)
[![UV Unwrapping](https://img.shields.io/badge/UV_Engine-xatlas_&_Trimesh-blueviolet.svg?style=flat)]()
[![Texture Generation](https://img.shields.io/badge/Texture_AI-Stable_Diffusion_/_ControlNet-magenta.svg?style=flat)]()
[![Status](https://img.shields.io/badge/Milestones-Week_1_&_Week_2_Complete-success.svg?style=flat)]()

**PolyGen** is an end-to-end generative AI pipeline designed to convert natural language text prompts into textured, UV-unwrapped 3D mesh assets exported in industry-standard Wavefront OBJ format and rendered in a real-time web-based 3D viewport.

This repository contains the complete implementation for **Week 1 (Environment Setup & Text-to-3D Generation)** and **Week 2 (Texture Generation and Automatic UV Mesh Processing)**.

---

## 🎯 Milestones & Implemented Features

### Week 1: Environment Setup & Text-to-3D Generation
- [x] **FastAPI Backend Server**: Input validation, routing, model serving, and health checks.
- [x] **Dual 3D Engine**: Built-in Semantic Procedural AI engine (zero paid keys needed) + Cloud API hooks (Meshy, Tripo3D).
- [x] **Geometry Pipeline**: Generates vertices, computed smooth surface normals, and exports Wavefront `.obj` files.
- [x] **React + Three.js 3D Viewport**: OrbitControls (rotate, zoom, pan), lighting rig, turntable auto-rotation, and wireframe toggle.
- [x] **Offline Support**: 100% offline generation with zero internet dependency via `start_offline.bat`.

### Week 2: Texture Generation & Mesh Processing
- [x] **Texture Generation Module (`backend/texture_generator.py`)**:
  - Accepts the same text prompt used for 3D model generation (e.g. *"A rusty medieval broadsword with a glowing blue sapphire in the hilt."*).
  - Integrates Stable Diffusion pipelines with depth-map / ControlNet conditioning.
  - Supports multiple generation backends: Stability AI SDXL API, Hugging Face Inference API, Local PyTorch Diffusers + ControlNet (with CUDA GPU), and a prompt-guided semantic procedural PBR texture synthesizer for offline/CPU environments.
  - Automatically renders orthographic depth maps from 3D meshes for ControlNet structure guidance.
  - Exports crisp 1024×1024 PNG texture maps to `outputs/textures/`.
- [x] **Mesh Processing & Automatic UV Unwrapping (`backend/mesh_processor.py`)**:
  - Loads and validates generated OBJ meshes using `trimesh` (watertightness, degenerate faces, vertex counts, euler numbers).
  - Automatically unwraps 3D meshes into non-overlapping 2D UV texture atlases using **`xatlas`** parameterization.
  - Re-computes smooth vertex normals and formats face indices (`f v/vt/vn`).
  - Automatically creates companion `.mtl` material files referencing the generated texture (`map_Kd`).
  - Preserves original raw meshes in `outputs/models/` and saves processed assets in `outputs/processed/`.
- [x] **Integrated End-to-End Pipeline**:
  - `POST /api/generate-full-asset`: Orchestrates 3D mesh generation -> depth-map rendering -> texture synthesis -> UV unwrapping -> textured asset assembly in one seamless call.
  - Interactive Web Studio displays the live textured mesh in the 3D viewport with texture map preview and one-click download buttons.

---

## 🏗️ Architecture & Pipeline Overview

```
                               ┌─────────────────────────────────┐
                               │       User Natural Prompt       │
                               │ "A rusty medieval broadsword    │
                               │  with a glowing blue sapphire"  │
                               └────────────────┬────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │      PolyGen Web Studio (React + Three.js)    │
                        │ - Pipeline Mode Toggle (Full Asset vs Mesh)   │
                        │ - Real-time 3D Viewport with PBR Texture Map  │
                        └───────────────────────┬───────────────────────┘
                                                │ POST /api/generate-full-asset
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │          FastAPI Orchestration API            │
                        └──────────┬────────────────────────────┬───────┘
                                   │                            │
                                   ▼                            ▼
                 ┌──────────────────────────────────┐ ┌──────────────────────────────────┐
                 │ Stage 1: Text-to-3D Generator    │ │ Stage 2: ControlNet Guidance     │
                 │ - Procedural / Cloud 3D Engine   │ │ - Orthographic depth rendering   │
                 │ - Saves raw OBJ to:              │ │ - Saves depth guidance to:       │
                 │   outputs/models/<id>.obj        │ │   outputs/textures/<id>_depth.png│
                 └─────────────────┬────────────────┘ └─────────────────┬────────────────┘
                                   │                                    │
                                   └─────────────────┬──────────────────┘
                                                     │
                                                     ▼
                                   ┌──────────────────────────────────┐
                                   │ Stage 3: Texture Generation      │
                                   │ - Stable Diffusion / ControlNet  │
                                   │ - Multi-tier: Stability API / HF │
                                   │   Local Diffusers / Semantic PBR │
                                   │ - Saves 1024x1024 PNG to:        │
                                   │   outputs/textures/<id>_tex.png  │
                                   └─────────────────┬────────────────┘
                                                     │
                                                     ▼
                                   ┌──────────────────────────────────┐
                                   │ Stage 4: Mesh Processing & UVs   │
                                   │ - Trimesh topology validation    │
                                   │ - xatlas UV atlas parameterize   │
                                   │ - Links texture in companion MTL │
                                   │ - Saves textured asset to:       │
                                   │   outputs/processed/<id>_proc.obj│
                                   └─────────────────┬────────────────┘
                                                     │
                                                     ▼
                        ┌───────────────────────────────────────────────┐
                        │         Real-Time 3D WebGL Viewport           │
                        │ - PBR Material with diffuse texture mapping   │
                        │ - Direct OBJ & PNG Texture Download           │
                        └───────────────────────────────────────────────┘
```

---

## 📁 Repository & Output Structure

```text
PolyGen/
├── backend/
│   ├── generate_3d.py         # Week 1: 3D Mesh procedural & cloud generation
│   ├── texture_generator.py   # Week 2: Stable Diffusion & texture generation
│   ├── mesh_processor.py      # Week 2: Trimesh validation & xatlas UV unwrapping
│   ├── main.py                # FastAPI REST API endpoints & static server
│   ├── requirements.txt       # Python dependencies (trimesh, xatlas, pillow, etc.)
│   ├── test_api.py            # Week 1 automated regression test suite
│   ├── test_week2.py          # Week 2 automated test suite (6 test cases)
│   └── .env.example           # Environment template for cloud API keys
├── frontend/
│   ├── index.html             # HTML5 entrypoint
│   ├── package.json           # React 18, Three.js, R3F dependencies
│   ├── vite.config.js         # Vite configuration with API reverse proxy
│   └── src/
│       ├── main.jsx           # React mounting root
│       ├── App.jsx            # Studio UI, pipeline mode toggle & texture preview
│       ├── index.css          # Design system & dark cyberpunk theme
│       └── components/
│           └── ModelViewer.jsx # Three.js Canvas, OrbitControls & TextureLoader
├── outputs/                   # Desktop Output Storage
│   ├── models/                # Week 1 raw generated .obj models
│   ├── textures/              # Week 2 generated 1024x1024 PNG texture maps & depth maps
│   └── processed/             # Week 2 UV-unwrapped textured .obj and .mtl assets
├── start_polygen.bat          # 1-Click launcher for both backend & frontend
├── start_offline.bat          # 1-Click launcher for 100% offline mode
├── open_outputs_folder.bat    # 1-Click Windows Explorer shortcut to outputs/
└── README.md                  # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python**: Version 3.10+ (tested with Python 3.12)
- **Node.js**: Version 18+ (tested with Node.js v24)
- **Operating System**: Windows, macOS, or Linux

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
# source venv/bin/activate

# Install all dependencies (including Trimesh, xatlas, Pillow, Scipy)
pip install -r requirements.txt
```

### 3. Optional AI & GPU Credentials Setup
Copy `.env.example` to `.env` in the `backend/` directory:
```bash
cp .env.example .env
```

| Environment Variable | Description |
| :--- | :--- |
| `STABILITY_API_KEY` | *(Optional)* Stability AI API key for cloud SDXL text-to-texture |
| `HUGGINGFACE_API_KEY` | *(Optional)* HuggingFace API key for hosted Stable Diffusion |
| `SD_WEBUI_URL` | *(Optional)* URL to local Automatic1111/ComfyUI API (e.g. `http://127.0.0.1:7860`) |
| `MESHY_API_KEY` | *(Optional)* Meshy API key for cloud 3D generation |
| `TRIPO_API_KEY` | *(Optional)* Tripo3D API key for cloud 3D generation |

> **Offline / Zero-Credential Guarantee:** If no API keys or NVIDIA CUDA GPUs are present, PolyGen will **never crash** or pretend that external models ran. It transparently utilizes its built-in semantic procedural PBR texture synthesizer and `xatlas` UV engine, with clear status reporting.

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🚀 Running the Project

### Option A: Standard Development Mode (Hot Reloading)
Double-click **[`start_polygen.bat`](./start_polygen.bat)**, or run:
```powershell
# Terminal 1 (Backend):
cd backend
.\venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 (Frontend):
cd frontend
npm run dev
```
- Web Application: **[http://localhost:5173](http://localhost:5173)**
- Interactive API Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Option B: 100% Offline Mode (No Internet Needed)
Double-click **[`start_offline.bat`](./start_offline.bat)**:
- Starts the local server and opens **[http://127.0.0.1:8000](http://127.0.0.1:8000)** with zero network or internet connection required.
- All models, textures, and processed assets are saved directly to `outputs/` on your Desktop.

---

## 🔌 Week 2 API Documentation

### 1. `POST /api/generate-full-asset`
Complete end-to-end pipeline: Generates 3D mesh, renders depth map, synthesizes texture, automatically UV-unwraps mesh with `xatlas`, and binds texture in `.mtl`.

**Request:**
```json
{
  "prompt": "A rusty medieval broadsword with a glowing blue sapphire in the hilt.",
  "style": "realistic",
  "provider": "auto"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "model_id": "polygen_a_rusty_medieval_broadsw_eb67917b",
  "prompt": "A rusty medieval broadsword with a glowing blue sapphire in the hilt.",
  "pipeline_stages": {
    "3d_generation": {
      "filename": "polygen_a_rusty_medieval_broadsw_eb67917b.obj",
      "url": "/api/models/polygen_a_rusty_medieval_broadsw_eb67917b.obj",
      "vertex_count": 129,
      "provider": "polygen-semantic-ai"
    },
    "texture_generation": {
      "filename": "polygen_a_rusty_medieval_broadsw_eb67917b_texture.png",
      "url": "/api/textures/polygen_a_rusty_medieval_broadsw_eb67917b_texture.png",
      "provider": "semantic_procedural_synthesizer",
      "is_ai_fallback": true,
      "status_message": "Stable Diffusion API key / CUDA GPU not detected. Synthesized high-resolution semantic procedural PBR texture from prompt keywords.",
      "depth_guidance_used": true
    },
    "mesh_processing": {
      "filename": "polygen_a_rusty_medieval_broadsw_eb67917b_processed.obj",
      "url": "/api/processed/polygen_a_rusty_medieval_broadsw_eb67917b_processed.obj",
      "unwrapping_method": "xatlas_parameterization",
      "processed_vertices": 226,
      "processed_uvs": 226
    }
  },
  "final_asset": {
    "obj_filename": "polygen_a_rusty_medieval_broadsw_eb67917b_processed.obj",
    "obj_url": "/api/processed/polygen_a_rusty_medieval_broadsw_eb67917b_processed.obj",
    "texture_filename": "polygen_a_rusty_medieval_broadsw_eb67917b_texture.png",
    "texture_url": "/api/textures/polygen_a_rusty_medieval_broadsw_eb67917b_texture.png",
    "mtl_filename": "polygen_a_rusty_medieval_broadsw_eb67917b_processed.mtl",
    "mtl_url": "/api/processed/polygen_a_rusty_medieval_broadsw_eb67917b_processed.mtl"
  },
  "total_pipeline_time_ms": 348.2
}
```

### 2. `POST /api/generate-texture`
Generates a standalone 1024×1024 PNG texture map from a text description and optional mesh for depth conditioning.

### 3. `POST /api/process-mesh`
Validates an existing raw OBJ mesh, computes automatic UV atlas coordinates using `xatlas`, and outputs processed files to `outputs/processed/`.

### 4. `GET /api/textures/{filename}`
Streams generated PNG texture files with caching and download support.

### 5. `GET /api/processed/{filename}`
Streams UV-unwrapped OBJ and MTL files for direct 3D WebGL viewing or Blender/Unity import.

---

## 🧪 Automated Test Suite

Run both test suites to verify full functionality:

```bash
cd backend
python test_week2.py
```

**Week 2 Test Output:**
```text
===================================================================
      PolyGen Week 2 Test Suite: Textures & UV Processing
===================================================================

[TEST 1/6] Generating Base 3D Mesh...
 -> Generated: polygen_a_rusty_medieval_broadsw_eb67917b.obj (129 verts, 204 faces)
 [PASS] Base 3D mesh generation verified.

[TEST 2/6] Rendering ControlNet Depth Map Guidance from Mesh...
 -> Depth map generated: polygen_a_rusty_medieval_broadsw_eb67917b_depth_test.png (512x512 grayscale)
 [PASS] ControlNet depth-map guidance verified.

[TEST 3/6] Generating Texture from Prompt...
 -> Texture created: test_polygen_a_rusty_medieval_broadsw_eb67917b_texture.png (1024x1024 PNG)
 -> Provider: semantic_procedural_synthesizer
 -> Depth Guidance Used: True
 -> Status Message: Stable Diffusion API key / CUDA GPU not detected. Synthesized high-resolution semantic procedural PBR texture from prompt keywords.
 [PASS] Texture generation verified.

[TEST 4/6] Processing Mesh & Automatic UV Unwrapping...
 -> Unwrapped Mesh: polygen_a_rusty_medieval_broadsw_eb67917b_processed.obj
 -> Method: xatlas_parameterization
 -> UV Count: 226
 -> Watertight: False
 -> Linked Texture: True
 [PASS] UV unwrapping and mesh processing verified.

[TEST 5/6] Testing Error Handling for Missing / Invalid Inputs...
 -> Correctly raised FileNotFoundError for missing input mesh.
 -> Correctly raised ValueError for non-OBJ input.
 -> Correctly raised ValueError for whitespace texture prompt.
 [PASS] All error handling checks passed.

[TEST 6/6] Validating Processed Textured Asset Compatibility...
 -> Reloaded mesh verified: 226 vertices, 204 faces, 226 UVs
 [PASS] Asset compatibility verified.

===================================================================
  >>> ALL WEEK 2 TESTS PASSED SUCCESSFULLY (6/6)! <<<
===================================================================
```

---

## 👥 Contributors

- **PolyGen Team** – Week 2: Texture Generation & Mesh Processing Pipeline
