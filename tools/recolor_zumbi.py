"""Recolor the zombie miniature and split its generic material by body area."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    # Paleta observada na referência: pele cinza-oliva morta, sobretudo azul
    # gasto, calça marrom-grafite e base de terra/pedra. As variações evitam o
    # aspecto de miniatura de plástico de uma única cor.
    "zumbi_pele": ((0.130, 0.145, 0.112), 0.0, 0.84),
    "zumbi_pele_suja": ((0.062, 0.078, 0.052), 0.0, 0.92),
    "zumbi_pele_ferida": ((0.170, 0.040, 0.024), 0.0, 0.88),
    "zumbi_casaco": ((0.030, 0.055, 0.065), 0.0, 0.88),
    "zumbi_casaco_gasto": ((0.072, 0.095, 0.096), 0.0, 0.90),
    "zumbi_casaco_sombra": ((0.012, 0.020, 0.024), 0.0, 0.94),
    "zumbi_calca": ((0.060, 0.047, 0.033), 0.0, 0.91),
    "zumbi_calca_suja": ((0.024, 0.019, 0.014), 0.0, 0.96),
    "zumbi_cabelo": ((0.010, 0.008, 0.006), 0.0, 0.98),
    "zumbi_base": ((0.052, 0.039, 0.025), 0.0, 0.98),
    "zumbi_pedra": ((0.098, 0.078, 0.052), 0.0, 0.97),
}


def load(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    return meshes


def set_material(mat, color, metallic, roughness):
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    # GLB de origem traz multiplicadores de cor ligados ao shader; eles
    # anulavam a paleta mesmo após alterar o valor-base. Para uma miniatura
    # consistente no Three.js, a cor PBR final fica explícita e sem links.
    for socket_name in ("Base Color", "Metallic", "Roughness"):
        for link in list(bsdf.inputs[socket_name].links):
            mat.node_tree.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness


def ensure_materials():
    materials = {}
    for name, settings in PALETTE.items():
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        set_material(mat, *settings)
        materials[name] = mat
    return materials


def patch_noise(center, scale=9.0):
    """Stable coarse variation mask: grouped patches, never salt-and-pepper."""
    x, y, z = (round(component * scale) / scale for component in center)
    return (x * 17.0 + y * 31.0 + z * 47.0) % 1.0


def classify_face(center):
    """Recover the miniature's readable areas from its assembled silhouette."""
    x, y, z = center
    radius = (x * x + y * y) ** 0.5
    if z < -0.805 and radius > 0.45:
        return "zumbi_base"
    if z > 0.78:
        return "zumbi_cabelo"
    if z > 0.63 or (z > 0.54 and abs(x) < 0.25 and y < -0.05):
        return "zumbi_pele"  # face and neck, excluding the coat's shoulders
    if z < -0.69 and radius < 0.57:
        return "zumbi_pele"  # bare feet emerging from torn trousers
    if abs(x) > 0.49 and z < 0.34:
        return "zumbi_pele"  # outstretched forearms and hands
    if z < -0.33:
        return "zumbi_calca"
    return "zumbi_casaco"


def recolor(meshes):
    materials = ensure_materials()
    variants_by_role = {
        "zumbi_pele": ("zumbi_pele", "zumbi_pele_suja", "zumbi_pele_ferida"),
        "zumbi_casaco": ("zumbi_casaco", "zumbi_casaco_gasto", "zumbi_casaco_sombra"),
        "zumbi_calca": ("zumbi_calca", "zumbi_calca_suja"),
        "zumbi_cabelo": ("zumbi_cabelo",),
        "zumbi_base": ("zumbi_base", "zumbi_pedra"),
    }
    for obj in meshes:
        # Os nomes das submalhas não representam fielmente toda a anatomia.
        # A classificação espacial mantém pele exposta, roupas e pedestal
        # coerentes mesmo quando uma peça cruza mais de uma dessas regiões.
        slot_names = [name for values in variants_by_role.values() for name in values]
        obj.data.materials.clear()
        for name in slot_names:
            obj.data.materials.append(materials[name])
        slots = {name: index for index, name in enumerate(slot_names)}
        for poly in obj.data.polygons:
            center = obj.matrix_world @ poly.center
            role = classify_face(center)
            amount = patch_noise(center)
            poly.use_smooth = role != "zumbi_base"
            if role == "zumbi_pele":
                name = "zumbi_pele_ferida" if amount > 0.985 else "zumbi_pele_suja" if amount > 0.83 else "zumbi_pele"
            elif role == "zumbi_casaco":
                name = "zumbi_casaco_sombra" if amount > 0.93 else "zumbi_casaco_gasto" if amount > 0.80 else "zumbi_casaco"
            elif role == "zumbi_calca":
                name = "zumbi_calca_suja" if amount > 0.82 else "zumbi_calca"
            elif role == "zumbi_base":
                name = "zumbi_pedra" if amount > 0.80 else "zumbi_base"
            else:
                name = "zumbi_cabelo"
            poly.material_index = slots[name]
        obj["palette_reference"] = "assets/pawns/monstros/zumbi/zumbi.png"
        obj["palette_adjustment"] = "gray-green skin with grime and wounds; worn blue-gray coat; dirty brown-charcoal trousers; earthy stone base"
    return sorted(materials)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(meshes):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return mn, mx


def save_asset(blend_path: Path, glb_path: Path):
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.parent.mkdir(parents=True, exist_ok=True)
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


def make_preview(meshes, output: Path):
    mn, mx = bounds(meshes)
    center = (mn + mx) * 0.5
    height = max(mx.z - mn.z, 0.001)

    bpy.ops.object.camera_add(
        location=(height * 1.55, -height * 2.15, center.z + height * 0.82)
    )
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + height * 0.40))
    camera.data.lens = 58
    bpy.context.scene.camera = camera

    for location, energy, size in [
        ((height * 2.0, -height * 3.0, center.z + height * 2.8), 980, height * 1.8),
        ((-height * 2.0, -height * 1.0, center.z + height * 1.3), 360, height * 1.6),
        ((height * 0.4, height * 2.2, center.z + height * 1.8), 520, height * 1.5),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + height * 0.38))

    bpy.ops.mesh.primitive_plane_add(
        size=height * 8.0, location=(center.x, center.y, mn.z - height * 0.035)
    )
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Preview floor")
    floor_mat.use_nodes = True
    floor_bsdf = floor_mat.node_tree.nodes["Principled BSDF"]
    floor_bsdf.inputs["Base Color"].default_value = (0.012, 0.012, 0.015, 1.0)
    floor_bsdf.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Zombie preview world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.006, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.13
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--keep-materials", action="store_true")
    cli = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(cli)

    meshes = load(args.input)
    if args.keep_materials:
        print("materials_preserved")
    else:
        print("materials_created", recolor(meshes))
    save_asset(args.out_blend, args.out_glb)
    make_preview(meshes, args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
