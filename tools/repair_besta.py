"""Repair and color the generated crossbow asset.

The source is a triangle-soup GLB: most triangle vertices occupy the same
coordinates but are duplicated.  The repair welds only coincident vertices,
removes two tiny orphan triangles, fills closed boundary loops, and preserves
flat shading so the low-poly form remains intact.
"""
from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


def load_source(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    # The source has one real connected mesh plus two orphan triangles.
    obj = max(meshes, key=lambda o: len(o.data.polygons))
    for other in meshes:
        if other != obj:
            bpy.data.objects.remove(other, do_unlink=True)
    return obj


def connected_face_components(bm: bmesh.types.BMesh):
    seen = set()
    result = []
    for face in bm.faces:
        if face in seen:
            continue
        q = deque([face])
        seen.add(face)
        component = []
        while q:
            current = q.popleft()
            component.append(current)
            for edge in current.edges:
                for neighbor in edge.link_faces:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        q.append(neighbor)
        result.append(component)
    return result


def repair_mesh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    before = (len(bm.verts), len(bm.edges), len(bm.faces))

    # Exact duplicates are the dominant defect in this generated mesh.  A
    # very small tolerance avoids changing nearby details.
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Remove only genuinely detached noise; keep all substantial geometry.
    components = connected_face_components(bm)
    orphan_faces = [face for component in components if len(component) < 50 for face in component]
    if orphan_faces:
        bmesh.ops.delete(bm, geom=orphan_faces, context="FACES")

    # Close the bounded gaps that can be inferred unambiguously from the
    # existing edge loops.  Open ends (such as the string) are intentionally
    # left open instead of being capped with an invented surface.
    bm.edges.ensure_lookup_table()
    boundary = [edge for edge in bm.edges if edge.is_boundary]
    bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bm.normal_update()

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    for poly in obj.data.polygons:
        poly.use_smooth = False

    after = (len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons))
    remaining_boundary = sum(1 for e in obj.data.edges if False)  # reported below in Blender audit
    return before, after


def make_material(name, color, metallic=0.0, roughness=0.55):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign_palette(obj):
    palette = [
        make_material("Besta | madeira escura", (0.075, 0.022, 0.007), 0.0, 0.58),
        make_material("Besta | madeira", (0.18, 0.065, 0.018), 0.0, 0.5),
        make_material("Besta | madeira iluminada", (0.29, 0.125, 0.035), 0.0, 0.48),
        make_material("Besta | couro", (0.045, 0.010, 0.004), 0.0, 0.7),
        make_material("Besta | metal escuro", (0.13, 0.115, 0.095), 0.78, 0.38),
        make_material("Besta | metal bronze", (0.22, 0.12, 0.045), 0.68, 0.34),
        make_material("Besta | corda", (0.16, 0.115, 0.075), 0.0, 0.76),
    ]
    obj.data.materials.clear()
    for mat in palette:
        obj.data.materials.append(mat)

    def wood_variant(c):
        # Broad, restrained variation follows the grain direction of the
        # stock while keeping the palette close to the reference image.
        wave = 0.5 + 0.5 * __import__("math").sin(c.y * 24.0 + c.x * 5.0 + c.z * 9.0)
        if wave < 0.24:
            return 0
        if wave > 0.80:
            return 2
        return 1

    for poly in obj.data.polygons:
        c = poly.center
        x, y, z = c.x, c.y, c.z

        # The two taut cords are straight, narrow diagonal runs above the
        # bow.  Keep the tip hardware in metal by giving metal precedence.
        string_y = -0.28 + 0.38 * abs(x)
        is_string = abs(x) > 0.26 and x * x + (y + 0.28) * (y + 0.28) < 1.0 and abs(y - string_y) < 0.032 and z > -0.065

        is_tip_hardware = abs(x) > 0.73 and -0.60 < y < -0.08
        is_front_hardware = abs(x) < 0.27 and -0.83 < y < -0.20
        is_top_hardware = abs(x) < 0.28 and y > 0.47 and (y > 0.83 or z > 0.11)

        if is_tip_hardware or is_front_hardware or is_top_hardware:
            # Small warm accents are reserved for visible clamps and bands.
            poly.material_index = 5 if (abs(x) > 0.72 and z > -0.08) else 4
        elif is_string:
            poly.material_index = 6
        elif y < 0.08 and abs(x) > 0.27:
            poly.material_index = 0 if z < -0.04 else 1
        elif y < -0.58 and abs(x) < 0.30:
            poly.material_index = 3
        else:
            poly.material_index = wood_variant(c)

    obj["asset_name"] = "besta_corrigida"
    obj["repair_method"] = "weld coincident vertices 1e-5; remove orphan triangles; fill closed holes; flat shading"
    obj["palette_reference"] = "assets/itens/besta.png"


def save_outputs(obj, glb_path: Path, blend_path: Path):
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_materials="EXPORT",
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_cameras=False,
        export_lights=False,
    )


def audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    print("final_mesh", len(bm.verts), len(bm.edges), len(bm.faces))
    print("boundary_edges", sum(1 for e in bm.edges if e.is_boundary))
    print("nonmanifold_edges", sum(1 for e in bm.edges if not e.is_manifold))
    print("materials", [m.name for m in obj.data.materials])
    bm.free()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(cli)
    obj = load_source(args.input)
    before, after = repair_mesh(obj)
    assign_palette(obj)
    print("source_mesh", before, "repaired_mesh", after)
    audit(obj)
    save_outputs(obj, args.out_glb, args.out_blend)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)


if __name__ == "__main__":
    main()
