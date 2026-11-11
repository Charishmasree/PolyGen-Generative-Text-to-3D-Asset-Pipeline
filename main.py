"""
PolyGen - FastAPI Backend Application
Handles API requests for Text-to-3D model generation, model file serving,
history listing, and health checks.
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from generate_3d import generate_3d_model, MODELS_DIR

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("polygen.api")

app = FastAPI(
    title="PolyGen - AI Text-to-3D Generation API",
    description="API for converting textual descriptions into downloadable 3D OBJ models.",
    version="1.0.0"
)

# CORS setup for frontend clients (React Vite on 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# =====================================================================
# Request / Response Schemas
# =====================================================================

class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        example="a low-poly medieval sword with golden hilt",
        description="Text prompt describing the desired 3D model."
    )
    style: Optional[str] = Field("low-poly", description="Target visual style (e.g. low-poly, realistic, stylized)")
    provider: Optional[str] = Field("auto", description="Provider engine: 'auto', 'local', 'meshy', or 'tripo'")


class ModelDimensions(BaseModel):
    width: float
    height: float
    depth: float


class ModelMetadata(BaseModel):
    vertex_count: int
    face_count: int
    dimensions: Dict[str, Any]
    provider: str
    generation_time_ms: float


class GenerateResponse(BaseModel):
    success: bool
    model_id: str
    prompt: str
    style: str
    filename: str
    model_url: str
    download_url: str
    file_size: int
    metadata: ModelMetadata


# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/")
def root():
    return {
        "service": "PolyGen Text-to-3D Generation API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "generate": "POST /api/generate",
            "models": "GET /api/models/{filename}",
            "history": "GET /api/history",
            "health": "GET /api/health"
        }
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend status and provider readiness."""
    meshy_ready = bool(os.getenv("MESHY_API_KEY"))
    tripo_ready = bool(os.getenv("TRIPO_API_KEY"))
    total_models = len(list(MODELS_DIR.glob("*.obj")))

    return {
        "status": "healthy",
        "service": "polygen-backend",
        "models_in_store": total_models,
        "providers": {
            "local_semantic_ai": "active",
            "meshy_api": "active" if meshy_ready else "not_configured (API key missing)",
            "tripo_api": "active" if tripo_ready else "not_configured (API key missing)"
        },
        "timestamp": time.time()
    }


@app.post("/api/generate", response_model=GenerateResponse)
@app.post("/generate", response_model=GenerateResponse)
def generate_model(req: GenerateRequest):
    """
    Generate a 3D model from a user-supplied text prompt.
    Exports in OBJ format and returns access and download URLs.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be blank or contain only whitespace."
        )

    if len(clean_prompt) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt must be at least 2 characters long."
        )

    try:
        logger.info(f"Received generation request: '{clean_prompt}', style='{req.style}', provider='{req.provider}'")
        result = generate_3d_model(
            prompt=clean_prompt,
            style=req.style or "low-poly",
            provider=req.provider or "auto"
        )
        return result
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the 3D model: {str(e)}"
        )


@app.get("/api/models/{filename}")
@app.get("/models/{filename}")
def get_model_file(filename: str, download: bool = Query(False)):
    """
    Serve generated OBJ models for browser 3D viewers (Three.js) or file download.
    Includes path traversal protection.
    """
    # Sanitize filename against directory traversal
    safe_filename = Path(filename).name
    if not (safe_filename.endswith(".obj") or safe_filename.endswith(".mtl")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .obj and .mtl files are accessible.")

    file_path = MODELS_DIR / safe_filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model '{safe_filename}' not found.")

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=3600"
    }

    if download:
        headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'

    return FileResponse(
        path=file_path,
        media_type="text/plain; charset=utf-8",
        headers=headers
    )


@app.get("/api/history")
def list_history(limit: int = Query(20, ge=1, le=100)):
    """
    List recently generated 3D models with metadata.
    """
    files = list(MODELS_DIR.glob("*.obj"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    history = []
    for f in files[:limit]:
        st = f.stat()
        history.append({
            "model_id": f.stem,
            "filename": f.name,
            "model_url": f"/api/models/{f.name}",
            "download_url": f"/api/models/{f.name}?download=true",
            "file_size": st.st_size,
            "created_at": st.st_mtime,
        })

    return {"count": len(history), "models": history}


# =====================================================================
# Server Runner
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

