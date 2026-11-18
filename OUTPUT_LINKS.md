# PolyGen – Output Links & Access Directory
## Week 1 & Week 2: Online & 100% Offline Access

This document contains all active access links, offline URLs, and desktop output directories for **PolyGen: Generative Text-to-3D Asset Pipeline**.

---

## 🌐 1. Online / Standard Mode Links (When Dev Servers Are Running)

When running the standard development environment via `start_polygen.bat` or `npm run dev`:

| Resource | Direct Link | Purpose |
| :--- | :--- | :--- |
| **PolyGen 3D Studio (Dashboard)** | **[http://localhost:5173](http://localhost:5173)** | Full interactive Web Studio with Week 2 texture generation, UV unwrap & 3D viewer |
| **Alternative Frontend IP** | **[http://127.0.0.1:5173](http://127.0.0.1:5173)** | Direct loopback IP address for frontend |
| **FastAPI Swagger API Explorer** | **[http://localhost:8000/docs](http://localhost:8000/docs)** | Interactive Swagger UI to test Week 1 & Week 2 endpoints |
| **ReDoc API Documentation** | **[http://localhost:8000/redoc](http://localhost:8000/redoc)** | Clean REST reference documentation |
| **Backend Health & Diagnostics** | **[http://localhost:8000/api/health](http://localhost:8000/api/health)** | Server status, model storage counts, xatlas & texture providers |
| **Asset Generation History** | **[http://localhost:8000/api/history](http://localhost:8000/api/history)** | JSON listing of all generated models, UV meshes & textures |

---

## 📴 2. 100% Offline Mode Links (When the Internet is NOT Working)

**PolyGen does not require an active internet connection or Wi-Fi.** All procedural 3D math, xatlas UV unwrapping, PBR texture synthesis, and Three.js WebGL rendering run completely on your local computer.

### How to Open Offline:
1. Double-click **[`start_offline.bat`](./start_offline.bat)** in your project folder.
2. It automatically starts the local backend and opens the single-port self-contained studio:

| Offline Resource | Direct Offline URL | Notes |
| :--- | :--- | :--- |
| **Offline 3D Web Studio** | **[http://127.0.0.1:8000](http://127.0.0.1:8000)** | Serves compiled React + Three.js app directly from FastAPI without Node.js or internet |
| **Offline API Docs (Swagger)** | **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** | Test full pipeline endpoints completely offline |
| **Offline Health Check** | **[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)** | Verify local xatlas and offline procedural texture synthesizer |

*(Note: `127.0.0.1` is the internal Windows loopback adapter; it never connects to the internet).*

---

## 💾 3. Where Week 2 Outputs Are Saved on Your Desktop

All generated files are automatically written to the **[`outputs/`](./outputs/)** folder in your project on the Desktop:

📂 **Base Folder**: `c:\Users\USER\OneDrive\Desktop\PolyGen Generative Text-to-3D Asset Pipeline\outputs\`

| Folder | What is Stored Inside | File Extensions |
| :--- | :--- | :--- |
| **[`outputs/models/`](./outputs/models/)** | Week 1 raw generated 3D meshes | `.obj`, `.mtl` |
| **[`outputs/textures/`](./outputs/textures/)** | Week 2 generated 1024×1024 texture maps & ControlNet depth maps | `.png` |
| **[`outputs/processed/`](./outputs/processed/)** | Week 2 automatically UV-unwrapped meshes with texture bindings | `.obj`, `.mtl` |

### Quick Ways to Open the Output Folder:
- **In Windows Explorer**: Double-click **[`open_outputs_folder.bat`](./open_outputs_folder.bat)**.
- **In the Web Studio**: Click the **"Open Outputs Folder"** button in the top navigation bar or the model details card.

---

## 🔌 4. Week 2 API Endpoints Summary

### Full Pipeline (Week 2 Recommended):
- **Generate Complete Textured Asset**:  
  `POST http://localhost:8000/api/generate-full-asset`  
  *Payload:* `{"prompt": "A rusty medieval broadsword with a glowing blue sapphire in the hilt.", "style": "realistic"}`  
  *Generates 3D mesh -> renders depth map -> synthesizes texture -> UV unwraps via xatlas -> saves textured asset.*

### Modular Endpoints:
- **Generate Texture Only**:  
  `POST http://localhost:8000/api/generate-texture`  
  *Payload:* `{"prompt": "A rusty medieval broadsword with a glowing blue sapphire in the hilt."}`

- **Process Mesh & UV Unwrap Only**:  
  `POST http://localhost:8000/api/process-mesh`  
  *Payload:* `{"mesh_filename": "polygen_model_123.obj", "texture_filename": "texture_123.png"}`

- **Fetch / Download Textures**:  
  `GET http://localhost:8000/api/textures/{filename.png}`  
  *(Add `?download=true` for direct browser file download).*

- **Fetch / Download UV-Unwrapped Processed Meshes**:  
  `GET http://localhost:8000/api/processed/{filename.obj}`  
  *(Add `?download=true` for direct browser file download).*

- **Week 1 Mesh Only (Preserved)**:  
  `POST http://localhost:8000/api/generate`  
  `GET http://localhost:8000/api/models/{filename.obj}`

---

## ⚡ 5. Desktop 1-Click Shortcut Launchers

1. **[`open_polygen.html`](./open_polygen.html)**: Clickable offline HTML launchpad with direct links to both online and offline modes.
2. **[`Open_PolyGen.url`](./Open_PolyGen.url)**: Windows desktop internet shortcut. Double-click to open `http://localhost:5173`.
3. **[`start_polygen.bat`](./start_polygen.bat)**: Double-click to launch backend + frontend in standard mode.
4. **[`start_offline.bat`](./start_offline.bat)**: Double-click to run 100% offline (no internet needed).
5. **[`open_outputs_folder.bat`](./open_outputs_folder.bat)**: Double-click to open your Desktop `outputs/` folder in Windows File Explorer.
