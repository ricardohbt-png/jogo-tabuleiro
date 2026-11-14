"""Aplica ao GLB do urso esquelético a paleta da referência PNG.

Preserva a malha original e gera uma cópia colorida, um .blend editável e uma
prévia renderizada. Executar com Blender 5.1 em modo background.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector


FALLBACK_BONE_SRGB = (0.40, 0.29, 0.19)
COLOR_ATTRIBUTE = "ReferenceColor"


def srgb_to_linear(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def make_vertex_color_material():
    mat = bpy.data.materials.new("Osso — cores projetadas da referência PNG")
    mat.diffuse_color = (0.48, 0.34, 0.23, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.88
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = COLOR_ATTRIBUTE
    links.new(vertex_color.outputs["Color"], bsdf.inputs["Base Color"])
    eyes = bpy.data.materials.new("Olhos — vermelho incandescente da referência")
    eyes.use_nodes = True
    eye_bsdf = eyes.node_tree.nodes.get("Principled BSDF")
    eye_bsdf.inputs["Base Color"].default_value = (0.65, 0.006, 0.002, 1.0)
    eye_bsdf.inputs["Roughness"].default_value = 0.38
    if "Emission Color" in eye_bsdf.inputs:
        eye_bsdf.inputs["Emission Color"].default_value = (1.0, 0.008, 0.002, 1.0)
        eye_bsdf.inputs["Emission Strength"].default_value = 1.6
    return mat, eyes


def is_eye_socket(center):
    x, y, z = center
    for eye_x in (-0.055, 0.055):
        if (((x - eye_x) / 0.027) ** 2 + ((z - 0.700) / 0.024) ** 2 <= 1.0
                and -0.84 <= y <= -0.76):
            return True
    return False


def load_model(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"O arquivo não contém malhas: {path}")
    return meshes


def recolor(meshes, reference: Path):
    image = bpy.data.images.load(str(reference), check_existing=False)
    width, height = image.size
    rgba = list(image.pixels[:])  # Blender stores image rows from bottom to top.
    def pixel(x, y_top):
        x = max(0, min(width - 1, int(x)))
        y_top = max(0, min(height - 1, int(y_top)))
        index = ((height - 1 - y_top) * width + x) * 4
        return rgba[index:index + 4]

    # Find the PNG's visible silhouette, ignoring transparent antialiasing.
    visible = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixel(x, y)
            if a > 0.45 and max(r, g, b) > 0.045:
                visible.append((x, y))
    if not visible:
        raise RuntimeError(f"A referência não tem pixels visíveis: {reference}")
    x0 = min(x for x, _ in visible)
    x1 = max(x for x, _ in visible)
    y0 = min(y for _, y in visible)
    y1 = max(y for _, y in visible)

    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    min_x, max_x = min(p.x for p in points), max(p.x for p in points)
    min_z, max_z = min(p.z for p in points), max(p.z for p in points)
    fallback = tuple(srgb_to_linear(v) for v in FALLBACK_BONE_SRGB)

    def sample(sx, sy):
        ix, iy = round(sx), round(sy)
        r, g, b, a = pixel(ix, iy)
        if a < 0.18:
            return fallback
        # The PNG already contains bone highlights, warm shadows, and red eyes.
        # Convert its sRGB values for glTF's linear vertex-color channel.
        return tuple(srgb_to_linear(max(0.0, min(1.0, c))) for c in (r, g, b))

    material, eye_material = make_vertex_color_material()
    vertex_count = 0
    colored_vertices = 0
    eye_faces = 0
    for obj in meshes:
        mesh = obj.data
        old = mesh.color_attributes.get(COLOR_ATTRIBUTE)
        if old:
            mesh.color_attributes.remove(old)
        colors = mesh.color_attributes.new(
            name=COLOR_ATTRIBUTE, type="FLOAT_COLOR", domain="POINT")
        mesh.materials.clear()
        mesh.materials.append(material)
        mesh.materials.append(eye_material)
        for poly in mesh.polygons:
            center = obj.matrix_world @ poly.center
            glowing_eye = is_eye_socket(center)
            poly.material_index = 1 if glowing_eye else 0
            eye_faces += int(glowing_eye)
        for vertex in mesh.vertices:
            world = obj.matrix_world @ vertex.co
            normal = (obj.matrix_world.to_3x3() @ vertex.normal).normalized()
            # The reference is a front view; back and side surfaces use the
            # same projected bone colors with a restrained natural darkening.
            facing = max(0.0, -normal.y)
            shade = 0.70 + 0.30 * facing
            u = (world.x - min_x) / max(max_x - min_x, 1e-8)
            v = (world.z - min_z) / max(max_z - min_z, 1e-8)
            sx = x0 + u * (x1 - x0)
            # Na PNG, o crânio está deslocado para a direita em relação
            # ao torso; no GLB ele fica centralizado. Compensa só a cabeça
            # para os olhos e os tons do rosto caírem nos lugares certos.
            head_weight = max(0.0, min(1.0, (world.z - 0.64) / 0.15))
            sx += head_weight * 0.145 * (x1 - x0)
            sy = y1 - v * (y1 - y0)
            # A cabeça 3D é mais alta que a da arte em proporção ao corpo;
            # desloca a amostra para baixo para alinhar olhos e órbitas.
            sy -= head_weight * 0.05 * (y1 - y0)
            color = sample(sx, sy)
            colors.data[vertex.index].color = (*[c * shade for c in color], 1.0)
            colored_vertices += 1
        obj["palette_reference"] = str(reference)
        obj["color_adjustment"] = "front-projected PNG colors with subtle darkening on side and rear faces"
        vertex_count += len(mesh.vertices)
    return {"vertices": vertex_count, "colored_vertices": colored_vertices, "eye_faces": eye_faces,
            "reference_bounds": [x0, y0, x1, y1]}


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
        filepath=str(glb_path), export_format="GLB", export_materials="EXPORT",
        export_apply=True, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )


def make_preview(meshes, output: Path):
    mn, mx = bounds(meshes)
    center = (mn + mx) * 0.5
    height = max(mx.z - mn.z, 0.001)
    bpy.ops.object.camera_add(location=(center.x + height * 0.8,
                                        center.y - height * 2.8,
                                        center.z + height * 0.60))
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + height * 0.05))
    camera.data.lens = 52
    bpy.context.scene.camera = camera
    for location, energy, size in [
        ((height * 2.0, -height * 3.0, center.z + height * 2.4), 800, height * 1.7),
        ((-height * 2.0, -height * 1.0, center.z + height * 1.1), 300, height * 1.8),
        ((height * 0.4, height * 2.2, center.z + height * 1.5), 360, height * 1.6),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + height * 0.32))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = 800
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Esqueleto animal preview")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.18
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    if not args.input.is_file() or not args.reference.is_file():
        raise FileNotFoundError("GLB fonte ou PNG de referência ausente")
    meshes = load_model(args.input)
    counts = recolor(meshes, args.reference)
    save_asset(args.out_blend, args.out_glb)
    make_preview(meshes, args.preview)
    print("materials_face_counts", counts)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
