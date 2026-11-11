# PolyGen – Output Links & Access Directory

This document contains all active access links for the **PolyGen** 3D generation studio, backend endpoints, and API documentation.

---

## 🚀 Live Application Links

| Resource | Direct Link | Description |
| :--- | :--- | :--- |
| **PolyGen 3D Studio (Dashboard)** | **[http://localhost:5173](http://localhost:5173)** | Main Web Application with prompt input, 3D viewport, lighting & controls |
| **Alternative Frontend IP** | **[http://127.0.0.1:5173](http://127.0.0.1:5173)** | Direct local loopback address for the frontend |
| **FastAPI Swagger Docs** | **[http://localhost:8000/docs](http://localhost:8000/docs)** | Interactive API documentation (test `POST /api/generate` in browser) |
| **ReDoc API Documentation** | **[http://localhost:8000/redoc](http://localhost:8000/redoc)** | Clean reference API documentation |
| **Backend Health Check** | **[http://localhost:8000/api/health](http://localhost:8000/api/health)** | Server status, model store count, and active provider info |
| **Generation History API** | **[http://localhost:8000/api/history](http://localhost:8000/api/history)** | JSON list of recently generated 3D OBJ models |

---

## ⚡ 1-Click Launchers

You can also launch and open PolyGen using these files in the workspace:

1. **[`Open_PolyGen.url`](./Open_PolyGen.url)**: Windows Internet Shortcut. Double-click to instantly open the 3D Studio in your default browser.
2. **[`open_polygen.html`](./open_polygen.html)**: Clickable offline HTML launcher.
3. **[`start_polygen.bat`](./start_polygen.bat)**: Double-click to launch both Backend and Frontend servers simultaneously in separate console windows.

---

## 📦 API Endpoints Summary

- **Generate 3D Model**:  
  `POST http://localhost:8000/api/generate`  
  Payload: `{"prompt": "medieval sword", "style": "low-poly"}`

- **Fetch OBJ File**:  
  `GET http://localhost:8000/api/models/{filename}`

- **Download OBJ File Directly**:  
  `GET http://localhost:8000/api/models/{filename}?download=true`

