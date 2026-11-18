"""
PolyGen - FastAPI Backend Application
Handles API requests for Text-to-3D model generation, texture generation,
automatic UV unwrapping, model file serving, history listing, and health checks.
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
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from generate_3d import generate_3d_model, MODELS_DIR, OUTPUTS_DIR, BACKEND_MODELS_DIR
from texture_generator import generate_texture, TEXTURES_DIR
from mesh_processor import process_and_unwrap_mesh, PROCESSED_DIR, XATLAS_AVAILABLE

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("polygen.api")

app = FastAPI(
    title="PolyGen - Generative Text-to-3D Asset Pipeline",
    description="API for converting textual descriptions into fully textured, UV-unwrapped 3D assets.",
    version="2.0.0"
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
    file_path: Optional[str] = None
    output_directory: Optional[str] = None
    file_size: int
    metadata: ModelMetadata


class GenerateTextureRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="Description of the texture to generate")
    model_id: Optional[str] = Field(None, description="Model identifier for naming")
    mesh_filename: Optional[str] = Field(None, description="Optional OBJ filename to extract depth guidance")
    resolution: Optional[int] = Field(1024, description="Resolution (default 1024)")


class ProcessMeshRequest(BaseModel):
    mesh_filename: str = Field(..., description="Name of the OBJ file in outputs/models or outputs/")
    texture_filename: Optional[str] = Field(None, description="Name of the texture file to bind in MTL")
    material_name: Optional[str] = Field("PolyGenMaterial", description="Material name")


class FullAssetRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="Prompt for 3D model, UVs, and texture")
    style: Optional[str] = Field("realistic", description="Art style")
    provider: Optional[str] = Field("auto", description="3D Model generation provider")


# =====================================================================
# Static File Mounting & UI Route
# =====================================================================

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.get("/")
def root():
    """Serves the built React frontend or API overview JSON."""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "PolyGen Generative Text-to-3D Asset Pipeline",
        "version": "2.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "generate_3d": "POST /api/generate",
            "generate_texture": "POST /api/generate-texture",
            "process_mesh": "POST /api/process-mesh",
            "generate_full_asset": "POST /api/generate-full-asset",
            "models": "GET /api/models/{filename}",
            "textures": "GET /api/textures/{filename}",
            "processed": "GET /api/processed/{filename}",
            "history": "GET /api/history",
            "health": "GET /api/health",
            "open_folder": "POST /api/open-folder"
        }
    }


@app.post("/api/open-folder")
def open_output_folder():
    """Opens the local outputs folder directly in Windows File Explorer."""
    import subprocess
    try:
        os.startfile(str(OUTPUTS_DIR))
    except Exception:
        subprocess.Popen(["explorer.exe", str(OUTPUTS_DIR)])
    return {
        "success": True, 
        "message": "Opened outputs folder in File Explorer",
        "folder_path": str(OUTPUTS_DIR)
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend status and provider readiness."""
    meshy_ready = bool(os.getenv("MESHY_API_KEY"))
    tripo_ready = bool(os.getenv("TRIPO_API_KEY"))
    stability_ready = bool(os.getenv("STABILITY_API_KEY"))
    hf_ready = bool(os.getenv("HUGGINGFACE_API_KEY"))

    total_models = len(list(MODELS_DIR.glob("*.obj"))) + len(list(OUTPUTS_DIR.glob("*.obj")))
    total_textures = len(list(TEXTURES_DIR.glob("*.png")))
    total_processed = len(list(PROCESSED_DIR.glob("*.obj")))

    return {
        "status": "healthy",
        "service": "polygen-backend",
        "version": "2.0.0",
        "storage_stats": {
            "models_count": total_models,
            "textures_count": total_textures,
            "processed_count": total_processed
        },
        "providers": {
            "3d_mesh_generator": {
                "local_semantic_ai": "active",
                "meshy_api": "active" if meshy_ready else "not_configured",
                "tripo_api": "active" if tripo_ready else "not_configured"
            },
            "texture_generator": {
                "stability_ai_api": "active" if stability_ready else "not_configured",
                "huggingface_api": "active" if hf_ready else "not_configured",
                "semantic_procedural_synthesizer": "active (offline fallback ready)"
            },
            "mesh_processor": {
                "trimesh": "active",
                "xatlas_uv_unwrapping": "active" if XATLAS_AVAILABLE else "cylindrical_projection_fallback"
            }
        },
        "timestamp": time.time()
    }


# =====================================================================
# Week 1 Endpoints (Preserved & Enhanced)
# =====================================================================

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
    Checks outputs/models/, outputs/, and backend/models/.
    """
    safe_filename = Path(filename).name
    if not (safe_filename.endswith(".obj") or safe_filename.endswith(".mtl")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .obj and .mtl files are accessible.")

    # Search potential storage locations
    candidates = [
        MODELS_DIR / safe_filename,
        OUTPUTS_DIR / safe_filename,
        BACKEND_MODELS_DIR / safe_filename
    ]
    file_path = next((p for p in candidates if p.exists() and p.is_file()), None)

    if not file_path:
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


# =====================================================================
# Week 2 Endpoints: Texture Generation & Mesh Processing
# =====================================================================

@app.post("/api/generate-texture")
def api_generate_texture(req: GenerateTextureRequest):
    """
    Generate a texture image from a prompt (and optional mesh depth map guidance).
    Saves in outputs/textures/ and returns metadata.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Texture prompt cannot be empty.")

    mesh_path = None
    if req.mesh_filename:
        safe_name = Path(req.mesh_filename).name
        candidates = [MODELS_DIR / safe_name, OUTPUTS_DIR / safe_name, PROCESSED_DIR / safe_name]
        mesh_path = next((str(p) for p in candidates if p.exists()), None)

    try:
        logger.info(f"Generating texture for prompt: '{clean_prompt}'")
        res = generate_texture(
            prompt=clean_prompt,
            model_id=req.model_id,
            mesh_path=mesh_path,
            resolution=req.resolution or 1024
        )
        return res
    except Exception as e:
        logger.exception(f"Texture generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate texture: {str(e)}")


@app.post("/api/process-mesh")
def api_process_mesh(req: ProcessMeshRequest):
    """
    Loads an existing OBJ mesh, validates topology, generates automatic UVs via xatlas,
    links texture map into companion MTL, and saves processed asset in outputs/processed/.
    """
    safe_mesh_name = Path(req.mesh_filename).name
    candidates = [
        MODELS_DIR / safe_mesh_name,
        OUTPUTS_DIR / safe_mesh_name,
        BACKEND_MODELS_DIR / safe_mesh_name
    ]
    mesh_path = next((p for p in candidates if p.exists() and p.is_file()), None)

    if not mesh_path:
        raise HTTPException(status_code=404, detail=f"Mesh file '{safe_mesh_name}' not found.")

    texture_rel = None
    if req.texture_filename:
        safe_tex = Path(req.texture_filename).name
        texture_rel = f"../textures/{safe_tex}"

    try:
        logger.info(f"Processing mesh and generating UVs for: {safe_mesh_name}")
        res = process_and_unwrap_mesh(
            input_obj_path=str(mesh_path),
            texture_relative_path=texture_rel,
            material_name=req.material_name or "PolyGenMaterial"
        )
        res["processed_model_url"] = f"/api/processed/{res['filename']}"
        res["download_url"] = f"/api/processed/{res['filename']}?download=true"
        return res
    except Exception as e:
        logger.exception(f"Mesh processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process mesh: {str(e)}")


@app.post("/api/generate-full-asset")
def api_generate_full_asset(req: FullAssetRequest):
    """
    Complete Week 2 End-to-End Pipeline:
    1. Generates 3D model from prompt.
    2. Renders depth map from mesh for ControlNet guidance.
    3. Generates high-res texture using prompt and depth guidance.
    4. Automatically UV-unwraps mesh, binds texture, and saves final textured asset.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        start_time = time.time()
        logger.info(f"=== Starting Full Asset Pipeline for: '{clean_prompt}' ===")

        # Step 1: Generate 3D Model
        model_res = generate_3d_model(prompt=clean_prompt, style=req.style or "realistic", provider=req.provider or "auto")
        model_id = model_res["model_id"]
        raw_mesh_path = model_res["file_path"]

        # Step 2: Generate Texture (with depth guidance from generated mesh)
        tex_res = generate_texture(
            prompt=clean_prompt,
            model_id=model_id,
            mesh_path=raw_mesh_path,
            resolution=1024
        )

        # Step 3: UV Unwrap & Bind Texture in Processed Mesh
        texture_relative = f"../textures/{tex_res['texture_filename']}"
        proc_res = process_and_unwrap_mesh(
            input_obj_path=raw_mesh_path,
            texture_relative_path=texture_relative,
            material_name="PolyGenPBRMaterial"
        )

        total_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "model_id": model_id,
            "prompt": clean_prompt,
            "pipeline_stages": {
                "3d_generation": {
                    "filename": model_res["filename"],
                    "url": model_res["model_url"],
                    "vertex_count": model_res["metadata"]["vertex_count"],
                    "provider": model_res["metadata"]["provider"]
                },
                "texture_generation": {
                    "filename": tex_res["texture_filename"],
                    "url": tex_res["texture_url"],
                    "provider": tex_res["provider"],
                    "is_ai_fallback": tex_res["is_ai_fallback"],
                    "status_message": tex_res["status_message"],
                    "depth_guidance_used": tex_res["depth_guidance_used"],
                },
                "mesh_processing": {
                    "filename": proc_res["filename"],
                    "url": f"/api/processed/{proc_res['filename']}",
                    "download_url": f"/api/processed/{proc_res['filename']}?download=true",
                    "unwrapping_method": proc_res["unwrapping_method"],
                    "processed_vertices": proc_res["processed_stats"]["vertex_count"],
                    "processed_uvs": proc_res["processed_stats"]["uv_count"]
                }
            },
            "final_asset": {
                "obj_filename": proc_res["filename"],
                "obj_url": f"/api/processed/{proc_res['filename']}",
                "obj_download_url": f"/api/processed/{proc_res['filename']}?download=true",
                "texture_filename": tex_res["texture_filename"],
                "texture_url": tex_res["texture_url"],
                "mtl_filename": proc_res["mtl_filename"],
                "mtl_url": f"/api/processed/{proc_res['mtl_filename']}",
            },
            "total_pipeline_time_ms": total_time_ms
        }

    except Exception as e:
        logger.exception(f"Full asset pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/api/textures/{filename}")
def get_texture_file(filename: str, download: bool = Query(False)):
    """Serves generated PNG texture maps from outputs/textures/."""
    safe_filename = Path(filename).name
    if not safe_filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="Only PNG textures are accessible.")

    file_path = TEXTURES_DIR / safe_filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Texture '{safe_filename}' not found.")

    headers = {"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'

    return FileResponse(path=file_path, media_type="image/png", headers=headers)


@app.get("/api/processed/{filename}")
def get_processed_mesh_file(filename: str, download: bool = Query(False)):
    """Serves UV-unwrapped OBJ and MTL files from outputs/processed/."""
    safe_filename = Path(filename).name
    if not (safe_filename.endswith(".obj") or safe_filename.endswith(".mtl")):
        raise HTTPException(status_code=400, detail="Only .obj and .mtl files are accessible.")

    file_path = PROCESSED_DIR / safe_filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Processed model '{safe_filename}' not found.")

    headers = {"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'

    return FileResponse(path=file_path, media_type="text/plain; charset=utf-8", headers=headers)


@app.get("/api/history")
def list_history(limit: int = Query(20, ge=1, le=100)):
    """
    List recently generated 3D models with metadata.
    """
    files = list(MODELS_DIR.glob("*.obj")) + list(PROCESSED_DIR.glob("*.obj"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    history = []
    seen = set()
    for f in files:
        if f.name in seen:
            continue
        seen.add(f.name)
        st = f.stat()
        is_processed = f.parent.name == "processed"
        history.append({
            "model_id": f.stem,
            "filename": f.name,
            "is_processed": is_processed,
            "model_url": f"/api/processed/{f.name}" if is_processed else f"/api/models/{f.name}",
            "download_url": f"/api/processed/{f.name}?download=true" if is_processed else f"/api/models/{f.name}?download=true",
            "file_size": st.st_size,
            "created_at": st.st_mtime,
        })
        if len(history) >= limit:
            break

    return {"count": len(history), "models": history}


# =====================================================================
# Server Runner
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
