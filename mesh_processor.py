"""
PolyGen - Mesh Processing & Automatic UV Unwrapping Module
Week 2: Uses Trimesh and xatlas to load generated OBJ meshes, validate topology,
automatically generate UV coordinates, and prepare textured 3D assets.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import trimesh

# Try importing xatlas for parameterization / UV unwrapping
try:
    import xatlas
    XATLAS_AVAILABLE = True
except ImportError:
    XATLAS_AVAILABLE = False

logger = logging.getLogger("polygen.mesh_processor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Default directory structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"
TEXTURES_DIR = OUTPUTS_DIR / "textures"
PROCESSED_DIR = OUTPUTS_DIR / "processed"

for d in [MODELS_DIR, TEXTURES_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class MeshValidationError(Exception):
    """Raised when a 3D mesh fails geometry or topology validation."""
    pass


# =====================================================================
# Mesh Validation Functions
# =====================================================================

def validate_mesh(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """
    Validates a loaded 3D mesh against geometric and topological criteria.

    Args:
        mesh: trimesh.Trimesh object

    Returns:
        Dict with validation metrics (watertight, vertex count, face count, volume, bounds)

    Raises:
        MeshValidationError if mesh has 0 vertices or degenerate geometry.
    """
    if mesh is None or len(mesh.vertices) == 0:
        raise MeshValidationError("Mesh contains zero vertices.")

    if len(mesh.faces) == 0:
        raise MeshValidationError("Mesh contains zero faces.")

    # Remove unreferenced vertices and degenerate faces
    non_degenerate = mesh.nondegenerate_faces()
    degenerate_count = len(mesh.faces) - np.count_nonzero(non_degenerate)

    # Check for NaN / Inf in vertices
    if not np.all(np.isfinite(mesh.vertices)):
        raise MeshValidationError("Mesh vertices contain non-finite numbers (NaN or Inf).")

    bounds_min = mesh.bounds[0].tolist()
    bounds_max = mesh.bounds[1].tolist()
    extents = (mesh.bounds[1] - mesh.bounds[0]).tolist()

    report = {
        "is_valid": bool(len(mesh.vertices) > 0 and len(mesh.faces) > 0),
        "is_watertight": bool(mesh.is_watertight),
        "is_winding_consistent": bool(mesh.is_winding_consistent),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
        "degenerate_faces": int(degenerate_count),
        "euler_number": int(mesh.euler_number),
        "bounds": {
            "min": [round(x, 4) for x in bounds_min],
            "max": [round(x, 4) for x in bounds_max],
            "extents": [round(x, 4) for x in extents],
        },
        "has_existing_uvs": bool(
            hasattr(mesh.visual, "uv") and mesh.visual.uv is not None and len(mesh.visual.uv) > 0
        ),
    }

    logger.info(
        f"Mesh validation: {report['vertex_count']} verts, {report['face_count']} faces, "
        f"watertight={report['is_watertight']}, existing_uvs={report['has_existing_uvs']}"
    )
    return report


# =====================================================================
# Automatic UV Unwrapping Algorithms
# =====================================================================

def unwrap_mesh_with_xatlas(mesh: trimesh.Trimesh) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes optimal, non-overlapping UV texture coordinates using xatlas.

    Args:
        mesh: trimesh.Trimesh object

    Returns:
        Tuple of (new_vertices, new_faces, uv_coordinates)
    """
    if not XATLAS_AVAILABLE:
        raise RuntimeError("xatlas is not installed in the environment.")

    vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)

    # Parametrize and unwrap mesh using xatlas
    atlas = xatlas.Atlas()
    atlas.add_mesh(vertices, faces)
    atlas.generate()

    # Retrieve unwrapped mesh components
    # xatlas returns tuple per mesh: (vmapping, new_indices, new_uvs)
    mesh_data = atlas[0]
    new_indices = mesh_data[1]
    new_uvs = mesh_data[2]
    vertex_remap = mesh_data[0]

    # Reconstruct vertex array matching new unwrapped topology
    unwrapped_vertices = vertices[vertex_remap]
    unwrapped_faces = new_indices.reshape(-1, 3)

    return unwrapped_vertices, unwrapped_faces, new_uvs


def unwrap_mesh_procedural_fallback(mesh: trimesh.Trimesh) -> np.ndarray:
    """
    Generates cylindrical and spherical UV coordinates as a fallback.
    Projects 3D Cartesian coordinates (x, y, z) into 2D UV texture space [0, 1].

    Args:
        mesh: trimesh.Trimesh object

    Returns:
        (N, 2) array of UV coordinates for mesh vertices.
    """
    v = mesh.vertices
    # Center vertices around origin
    center = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    centered_v = v - center

    x = centered_v[:, 0]
    y = centered_v[:, 1]
    z = centered_v[:, 2]

    # Cylindrical parameterization: u from angle in XZ plane, v from normalized Y height
    u = 0.5 + np.arctan2(z, x) / (2.0 * np.pi)
    y_min, y_max = y.min(), y.max()
    y_range = (y_max - y_min) if (y_max - y_min) > 1e-6 else 1.0
    v_coord = (y - y_min) / y_range

    uvs = np.column_stack((np.clip(u, 0.0, 1.0), np.clip(v_coord, 0.0, 1.0)))
    return uvs.astype(np.float32)


# =====================================================================
# Main Mesh Processing Pipeline
# =====================================================================

def process_and_unwrap_mesh(
    input_obj_path: str,
    output_obj_path: Optional[str] = None,
    texture_relative_path: Optional[str] = None,
    material_name: str = "PolyGenMaterial"
) -> Dict[str, Any]:
    """
    Loads an OBJ mesh, validates topology, generates automatic UV coordinates,
    updates material/MTL links, and saves the processed asset in outputs/processed/.

    Args:
        input_obj_path: Path to the raw source .obj file.
        output_obj_path: Destination path for the UV-unwrapped .obj file.
        texture_relative_path: Optional relative path to associated texture map (e.g. "../textures/xyz.png").
        material_name: Name of the material definition.

    Returns:
        Dict with processing metadata, validation report, and saved file paths.
    """
    in_path = Path(input_obj_path).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input mesh file does not exist: {in_path}")

    if not in_path.is_file() or in_path.suffix.lower() != ".obj":
        raise ValueError(f"Input file must be a valid .obj file, got: {in_path.name}")

    logger.info(f"Loading mesh for processing: {in_path.name}")

    # Load mesh via trimesh
    try:
        loaded = trimesh.load(str(in_path), file_type="obj", force="mesh", process=False)
        if isinstance(loaded, trimesh.Scene):
            # If multiple geometries, merge or select primary
            if len(loaded.geometry) == 0:
                raise MeshValidationError("Empty scene loaded from OBJ.")
            mesh = trimesh.util.concatenate(list(loaded.geometry.values()))
        else:
            mesh = loaded
    except Exception as e:
        raise MeshValidationError(f"Trimesh failed to parse OBJ file: {e}")

    # Step 1: Validate mesh
    validation_report = validate_mesh(mesh)

    # Step 2: Automatic UV Unwrapping
    unwrapping_method = "none"
    if XATLAS_AVAILABLE:
        try:
            logger.info("Generating UV atlas via xatlas parameterization...")
            new_verts, new_faces, new_uvs = unwrap_mesh_with_xatlas(mesh)
            # Reconstruct mesh with new parameterization
            processed_mesh = trimesh.Trimesh(
                vertices=new_verts,
                faces=new_faces,
                visual=trimesh.visual.TextureVisuals(uv=new_uvs),
                process=False
            )
            unwrapping_method = "xatlas_parameterization"
        except Exception as e:
            logger.warning(f"xatlas parameterization encountered an issue: {e}. Falling back to cylindrical projection.")
            uvs = unwrap_mesh_procedural_fallback(mesh)
            processed_mesh = mesh.copy()
            processed_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)
            unwrapping_method = "procedural_cylindrical_projection"
    else:
        logger.info("xatlas not available. Using procedural projection for UV unwrapping.")
        uvs = unwrap_mesh_procedural_fallback(mesh)
        processed_mesh = mesh.copy()
        processed_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)
        unwrapping_method = "procedural_cylindrical_projection"

    # Step 3: Compute vertex normals if missing
    if processed_mesh.vertex_normals is None or len(processed_mesh.vertex_normals) == 0:
        processed_mesh.recompute_vertex_normals()

    # Step 4: Determine Output Paths
    if not output_obj_path:
        stem = in_path.stem
        out_name = f"{stem}_processed.obj"
        out_path = PROCESSED_DIR / out_name
    else:
        out_path = Path(output_obj_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

    mtl_filename = f"{out_path.stem}.mtl"
    mtl_path = out_path.parent / mtl_filename

    # Step 5: Write Companion MTL File referencing texture if provided
    with open(mtl_path, "w", encoding="utf-8") as fm:
        fm.write(f"# PolyGen Week 2 Material Definition\n")
        fm.write(f"# Processed Mesh: {out_path.name}\n\n")
        fm.write(f"newmtl {material_name}\n")
        fm.write(f"Ka 0.2000 0.2000 0.2000\n")
        fm.write(f"Kd 0.8500 0.8500 0.8500\n")
        fm.write(f"Ks 0.3500 0.3500 0.3500\n")
        fm.write(f"Ns 60.0000\n")
        fm.write(f"d 1.0000\n")
        fm.write(f"illum 2\n")
        if texture_relative_path:
            fm.write(f"map_Kd {texture_relative_path}\n")

    # Step 6: Export Clean Wavefront OBJ with UV Coordinates and Normals
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# PolyGen Processed & UV-Unwrapped 3D Mesh\n")
        f.write(f"# Source: {in_path.name}\n")
        f.write(f"# Unwrapping Method: {unwrapping_method}\n")
        f.write(f"# Vertices: {len(processed_mesh.vertices)}, Faces: {len(processed_mesh.faces)}\n\n")
        f.write(f"mtllib {mtl_filename}\n")
        f.write(f"o {out_path.stem}\n")
        f.write(f"usemtl {material_name}\n\n")

        # Vertices
        for v in processed_mesh.vertices:
            f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        f.write("\n")

        # Texture Coordinates (UVs)
        uvs = processed_mesh.visual.uv
        if uvs is not None and len(uvs) > 0:
            for uv in uvs:
                f.write(f"vt {uv[0]:.5f} {uv[1]:.5f}\n")
            f.write("\n")

        # Normals
        normals = processed_mesh.vertex_normals
        if normals is not None and len(normals) > 0:
            for vn in normals:
                f.write(f"vn {vn[0]:.4f} {vn[1]:.4f} {vn[2]:.4f}\n")
            f.write("\n")

        # Faces with vertex, UV, and normal indices (1-based)
        has_uv = uvs is not None and len(uvs) > 0
        has_vn = normals is not None and len(normals) > 0

        for face in processed_mesh.faces:
            # 1-based indices
            v1, v2, v3 = face[0] + 1, face[1] + 1, face[2] + 1
            if has_uv and has_vn:
                f.write(f"f {v1}/{v1}/{v1} {v2}/{v2}/{v2} {v3}/{v3}/{v3}\n")
            elif has_uv:
                f.write(f"f {v1}/{v1} {v2}/{v2} {v3}/{v3}\n")
            elif has_vn:
                f.write(f"f {v1}//{v1} {v2}//{v2} {v3}//{v3}\n")
            else:
                f.write(f"f {v1} {v2} {v3}\n")

    logger.info(f"Successfully processed and saved UV-unwrapped mesh to: {out_path.name}")

    return {
        "success": True,
        "original_mesh_path": str(in_path),
        "processed_mesh_path": str(out_path),
        "filename": out_path.name,
        "mtl_path": str(mtl_path),
        "mtl_filename": mtl_filename,
        "unwrapping_method": unwrapping_method,
        "validation": validation_report,
        "processed_stats": {
            "vertex_count": int(len(processed_mesh.vertices)),
            "face_count": int(len(processed_mesh.faces)),
            "uv_count": int(len(uvs)) if uvs is not None else 0,
            "has_texture_linked": bool(texture_relative_path),
        }
    }


if __name__ == "__main__":
    # Test script standalone
    test_files = list(MODELS_DIR.glob("*.obj"))
    if not test_files:
        # Check root outputs/
        test_files = list(OUTPUTS_DIR.glob("*.obj"))

    if test_files:
        sample = test_files[0]
        print(f"Testing mesh_processor on: {sample.name}")
        res = process_and_unwrap_mesh(str(sample))
        print("Success:", res["success"])
        print("Method:", res["unwrapping_method"])
        print("Processed Vertices:", res["processed_stats"]["vertex_count"])
        print("Processed UVs:", res["processed_stats"]["uv_count"])
    else:
        print("No test OBJ files found. Run generate_3d.py first.")
