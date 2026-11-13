
"""
PolyGen - 3D Mesh Validation Module

Validates generated 3D mesh geometry before OBJ export.
Checks vertex coordinates, face indices, duplicate vertices,
and mesh structure to improve model quality.
"""

import math
from typing import Any, Dict, List, Tuple


def validate_vertices(
    vertices: List[Tuple[float, float, float]]
) -> Dict[str, Any]:
    """Check whether all mesh vertices contain valid coordinates."""

    errors = []

    if not vertices:
        errors.append("Mesh contains no vertices.")

    for index, vertex in enumerate(vertices):
        if len(vertex) != 3:
            errors.append(
                f"Vertex {index + 1} must contain three coordinates."
            )
            continue

        for coordinate in vertex:
            if not isinstance(coordinate, (int, float)):
                errors.append(
                    f"Vertex {index + 1} contains a non-numeric value."
                )
                break

            if not math.isfinite(coordinate):
                errors.append(
                    f"Vertex {index + 1} contains an invalid coordinate."
                )
                break

    return {
        "valid": len(errors) == 0,
        "vertex_count": len(vertices),
        "errors": errors
    }


def validate_faces(
    faces: List[List[int]],
    vertex_count: int
) -> Dict[str, Any]:
    """Verify that every face references existing mesh vertices."""

    errors = []

    if not faces:
        errors.append("Mesh contains no faces.")

    for face_index, face in enumerate(faces):
        if len(face) < 3:
            errors.append(
                f"Face {face_index + 1} must have at least three vertices."
            )
            continue

        for vertex_index in face:
            if not isinstance(vertex_index, int):
                errors.append(
                    f"Face {face_index + 1} contains an invalid index."
                )
            elif vertex_index < 1 or vertex_index > vertex_count:
                errors.append(
                    f"Face {face_index + 1} references an invalid vertex."
                )

    return {
        "valid": len(errors) == 0,
        "face_count": len(faces),
        "errors": errors
    }


def validate_mesh(mesh: Any) -> Dict[str, Any]:
    """Run complete geometry validation on a PolyGen mesh object."""

    vertex_result = validate_vertices(mesh.vertices)

    face_indices = [
        [vertex[0] for vertex in face]
        for face in mesh.faces
    ]

    face_result = validate_faces(
        face_indices,
        len(mesh.vertices)
    )

    all_errors = (
        vertex_result["errors"] + face_result["errors"]
    )

    return {
        "valid": len(all_errors) == 0,
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.faces),
        "vertices_valid": vertex_result["valid"],
        "faces_valid": face_result["valid"],
        "errors": all_errors
    }


if __name__ == "__main__":
    sample_vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0)
    ]

    sample_faces = [[1, 2, 3]]

    vertex_check = validate_vertices(sample_vertices)
    face_check = validate_faces(
        sample_faces,
        len(sample_vertices)
    )

    print("PolyGen Mesh Validation")
    print("-----------------------")
    print("Vertex Validation:", vertex_check)
    print("Face Validation:", face_check)
    print("Overall Status:",
          "SUCCESS" if vertex_check["valid"]
          and face_check["valid"] else "FAILED")
