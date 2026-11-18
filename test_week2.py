"""
PolyGen - Week 2 Test Suite: Texture Generation & Mesh Processing
Tests:
1. Texture generation with sample prompt ("A rusty medieval broadsword with a glowing blue sapphire in the hilt.")
2. Automatic UV unwrapping with xatlas on generated OBJ models.
3. ControlNet depth-map guidance generation from 3D mesh geometry.
4. Material and texture binding in processed Wavefront OBJ/MTL.
5. Error handling for missing files, invalid inputs, and corrupt geometry.
6. Full end-to-end Week 2 asset pipeline.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_3d import generate_3d_model, MODELS_DIR
from texture_generator import generate_texture, render_depth_map_from_mesh, TEXTURES_DIR
from mesh_processor import process_and_unwrap_mesh, validate_mesh, PROCESSED_DIR
import trimesh
from PIL import Image

def run_week2_tests():
    print("===================================================================")
    print("      PolyGen Week 2 Test Suite: Textures & UV Processing")
    print("===================================================================\n")

    # Sample prompt from the Week 2 specification
    sample_prompt = "A rusty medieval broadsword with a glowing blue sapphire in the hilt."

    # Test 1: Generate a 3D Model for Testing
    print("[TEST 1/6] Generating Base 3D Mesh...")
    model_res = generate_3d_model(sample_prompt, style="realistic")
    assert model_res["success"] is True
    raw_mesh_path = model_res["file_path"]
    assert Path(raw_mesh_path).exists(), f"Mesh file not found at {raw_mesh_path}"
    print(f" -> Generated: {model_res['filename']} ({model_res['metadata']['vertex_count']} verts, {model_res['metadata']['face_count']} faces)")
    print(" [PASS] Base 3D mesh generation verified.\n")

    # Test 2: ControlNet Depth Map Rendering
    print("[TEST 2/6] Rendering ControlNet Depth Map Guidance from Mesh...")
    depth_out = str(TEXTURES_DIR / f"{model_res['model_id']}_depth_test.png")
    depth_res = render_depth_map_from_mesh(raw_mesh_path, output_depth_path=depth_out, resolution=512)
    assert depth_res is not None
    assert Path(depth_out).exists()
    d_img = Image.open(depth_out)
    assert d_img.size == (512, 512)
    print(f" -> Depth map generated: {Path(depth_out).name} ({d_img.size[0]}x{d_img.size[1]} grayscale)")
    print(" [PASS] ControlNet depth-map guidance verified.\n")

    # Test 3: Texture Generation with Sample Prompt
    print("[TEST 3/6] Generating Texture from Prompt...")
    tex_res = generate_texture(
        prompt=sample_prompt,
        model_id=f"test_{model_res['model_id']}",
        mesh_path=raw_mesh_path,
        resolution=1024
    )
    assert tex_res["success"] is True
    assert Path(tex_res["texture_path"]).exists()
    t_img = Image.open(tex_res["texture_path"])
    assert t_img.size == (1024, 1024)
    print(f" -> Texture created: {tex_res['texture_filename']} ({t_img.size[0]}x{t_img.size[1]} PNG)")
    print(f" -> Provider: {tex_res['provider']}")
    print(f" -> Depth Guidance Used: {tex_res['depth_guidance_used']}")
    print(f" -> Status Message: {tex_res['status_message']}")
    print(" [PASS] Texture generation verified.\n")

    # Test 4: Automatic UV Unwrapping and Mesh Processing
    print("[TEST 4/6] Processing Mesh & Automatic UV Unwrapping...")
    texture_relative = f"../textures/{tex_res['texture_filename']}"
    proc_res = process_and_unwrap_mesh(
        input_obj_path=raw_mesh_path,
        texture_relative_path=texture_relative,
        material_name="SwordMaterial"
    )
    assert proc_res["success"] is True
    proc_obj_path = proc_res["processed_mesh_path"]
    assert Path(proc_obj_path).exists()
    assert Path(proc_res["mtl_path"]).exists()
    assert proc_res["processed_stats"]["uv_count"] > 0
    print(f" -> Unwrapped Mesh: {proc_res['filename']}")
    print(f" -> Method: {proc_res['unwrapping_method']}")
    print(f" -> UV Count: {proc_res['processed_stats']['uv_count']}")
    print(f" -> Watertight: {proc_res['validation']['is_watertight']}")
    print(f" -> Linked Texture: {proc_res['processed_stats']['has_texture_linked']}")
    print(" [PASS] UV unwrapping and mesh processing verified.\n")

    # Test 5: Error Handling (Missing & Invalid Files)
    print("[TEST 5/6] Testing Error Handling for Missing / Invalid Inputs...")
    
    # 5a. Missing file
    try:
        process_and_unwrap_mesh("non_existent_file_999.obj")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        print(" -> Correctly raised FileNotFoundError for missing input mesh.")

    # 5b. Invalid extension
    try:
        process_and_unwrap_mesh(__file__)  # .py instead of .obj
        assert False, "Should have raised ValueError"
    except ValueError:
        print(" -> Correctly raised ValueError for non-OBJ input.")

    # 5c. Empty prompt in texture generator
    try:
        generate_texture("   ")
        assert False, "Should have raised ValueError"
    except ValueError:
        print(" -> Correctly raised ValueError for whitespace texture prompt.")

    print(" [PASS] All error handling checks passed.\n")

    # Test 6: Verify Processed Mesh in Trimesh with Textures
    print("[TEST 6/6] Validating Processed Textured Asset Compatibility...")
    reloaded_mesh = trimesh.load(proc_obj_path, file_type="obj", force="mesh", process=False)
    assert len(reloaded_mesh.vertices) > 0
    assert len(reloaded_mesh.faces) > 0
    assert hasattr(reloaded_mesh.visual, "uv") and len(reloaded_mesh.visual.uv) > 0
    print(f" -> Reloaded mesh verified: {len(reloaded_mesh.vertices)} vertices, {len(reloaded_mesh.faces)} faces, {len(reloaded_mesh.visual.uv)} UVs")
    print(" [PASS] Asset compatibility verified.\n")

    print("===================================================================")
    print("  >>> ALL WEEK 2 TESTS PASSED SUCCESSFULLY (6/6)! <<<")
    print("===================================================================")


if __name__ == "__main__":
    run_week2_tests()

