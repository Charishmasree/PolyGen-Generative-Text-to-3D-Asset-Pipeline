"""
PolyGen API Test Suite
Tests FastAPI endpoints directly and verifies 3D OBJ generation.
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import app, generate_model, GenerateRequest, get_model_file, health_check, list_history
from fastapi import HTTPException

def test_all():
    print("========================================")
    print(" Running PolyGen Backend Test Suite")
    print("========================================")

    # 1. Test Health
    h = health_check()
    assert h["status"] == "healthy", f"Health failed: {h}"
    print("[PASS] 1. Health check endpoint")

    # 2. Test Generate with categorical prompt
    req1 = GenerateRequest(prompt="a low-poly wooden chair", style="low-poly")
    res1 = generate_model(req1)
    assert res1["success"] is True
    assert res1["filename"].endswith(".obj")
    assert res1["metadata"]["vertex_count"] > 0
    print(f"[PASS] 2. Generation (chair) -> {res1['filename']} ({res1['metadata']['vertex_count']} verts, {res1['metadata']['face_count']} faces)")

    # 3. Test Generate with parametric prompt
    req2 = GenerateRequest(prompt="futuristic neon cyber crystal", style="realistic")
    res2 = generate_model(req2)
    assert res2["success"] is True
    assert res2["metadata"]["vertex_count"] > 0
    print(f"[PASS] 3. Generation (crystal) -> {res2['filename']} ({res2['metadata']['vertex_count']} verts)")

    # 4. Test Blank Prompt Validation
    try:
        generate_model(GenerateRequest(prompt="   "))
        assert False, "Should have raised HTTPException for whitespace prompt"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"[PASS] 4. Blank prompt validation correctly caught (HTTP {e.status_code})")

    # 5. Test Short Prompt Validation
    try:
        generate_model(GenerateRequest(prompt="a"))
        assert False, "Should have raised HTTPException for too-short prompt"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"[PASS] 5. Short prompt validation correctly caught (HTTP {e.status_code})")

    # 6. Test Model File Retrieval
    f_res = get_model_file(res1["filename"])
    assert Path(f_res.path).exists()
    assert Path(f_res.path).stat().st_size > 0
    print(f"[PASS] 6. Model file retrieval -> {Path(f_res.path).stat().st_size} bytes")

    # 7. Test Directory Traversal Defense
    try:
        get_model_file("../../secret.txt")
        assert False, "Should have rejected path traversal"
    except HTTPException as e:
        assert e.status_code == 400 or e.status_code == 404
        print(f"[PASS] 7. Directory traversal defense verified")

    # 8. Test History Listing
    hist = list_history(limit=5)
    assert hist["count"] > 0
    print(f"[PASS] 8. History listing -> {hist['count']} models found")

    print("========================================")
    print(" ALL BACKEND TESTS PASSED (8/8)!")
    print("========================================")

if __name__ == "__main__":
    test_all()
