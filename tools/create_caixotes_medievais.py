"""Build a reusable medieval crate stack prop and export its GLB preview."""
from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def make_material(name, color, metallic=0.0, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def cube(name, loc, dims, mat, bevel=0.008, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Desgaste suave das bordas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def nail(name, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (0.012, 0.006, 0.012)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def make_crate(prefix, cx, cy, bottom, dims, mats):
    width, depth, height = dims
    center_z = bottom + height / 2
    post = 0.082
    rail = 0.075
    made = []
    made.append(cube(f"{prefix} | estrutura interna", (cx, cy, center_z),
                     (width - 2 * post, depth - 2 * post, height - 2 * rail), mats[2], 0.004))

    # Broad vertical boards on the front and back, and narrower boards on the ends.
    inner_w = width - 2 * post
    inner_h = height - 2 * rail
    n_front = 5
    board_w = inner_w / n_front
    for side_y in (-1, 1):
        face_y = cy + side_y * (depth / 2 - 0.012)
        for i in range(n_front):
            x = cx - inner_w / 2 + (i + 0.5) * board_w
            mat = mats[(i + int(bottom * 10)) % 2]
            made.append(cube(f"{prefix} | tábua frontal {side_y} {i+1}",
                             (x, face_y, center_z), (board_w - 0.008, 0.035, inner_h), mat, 0.004))

    inner_d = depth - 2 * post
    n_side = 4
    board_d = inner_d / n_side
    for side_x in (-1, 1):
        face_x = cx + side_x * (width / 2 - 0.012)
        for i in range(n_side):
            y = cy - inner_d / 2 + (i + 0.5) * board_d
            mat = mats[(i + 1) % 2]
            made.append(cube(f"{prefix} | tábua lateral {side_x} {i+1}",
                             (face_x, y, center_z), (0.035, board_d - 0.008, inner_h), mat, 0.004))

    # Heavy corner posts and perimeter rails make the construction legible at game scale.
    for sx in (-1, 1):
        for sy in (-1, 1):
            made.append(cube(f"{prefix} | montante {sx} {sy}",
                             (cx + sx * (width / 2 - post / 2), cy + sy * (depth / 2 - post / 2), center_z),
                             (post, post, height), mats[1], 0.008))
    for z in (bottom + rail / 2, bottom + height - rail / 2):
        for sy in (-1, 1):
            made.append(cube(f"{prefix} | travessa longa {z} {sy}",
                             (cx, cy + sy * (depth / 2 - 0.027), z),
                             (width - post, 0.055, rail), mats[1], 0.007))
        for sx in (-1, 1):
            made.append(cube(f"{prefix} | travessa lateral {z} {sx}",
                             (cx + sx * (width / 2 - 0.027), cy, z),
                             (0.055, depth - post, rail), mats[1], 0.007))

    # Closed lid with separated boards.
    top_z = bottom + height - 0.012
    for i in range(5):
        y = cy - depth * 0.38 + i * (depth * 0.19)
        made.append(cube(f"{prefix} | tampa {i+1}", (cx, y, top_z),
                         (width - 0.10, depth * 0.17, 0.035), mats[(i + 1) % 2], 0.004))

    # Diagonal braces on the two camera-facing sides.
    front_y = cy - depth / 2 - 0.024
    brace_len = math.sqrt((width * 0.62) ** 2 + (height * 0.57) ** 2)
    brace_angle = -math.atan2(height * 0.57, width * 0.62)
    made.append(cube(f"{prefix} | travessa diagonal frontal", (cx, front_y, center_z),
                     (brace_len, 0.048, 0.070), mats[1], 0.006, (0, brace_angle, 0)))
    side_x = cx + width / 2 + 0.024
    side_len = math.sqrt((depth * 0.64) ** 2 + (height * 0.55) ** 2)
    side_angle = math.atan2(height * 0.55, depth * 0.64)
    made.append(cube(f"{prefix} | travessa diagonal lateral", (side_x, cy, center_z),
                     (0.048, side_len, 0.070), mats[1], 0.006, (side_angle, 0, 0)))

    # Visible dark iron pegs along the front and right braces/rails.
    for z in (bottom + rail * 0.50, bottom + height - rail * 0.50):
        for sx in (-1, 1):
            made.append(nail(f"{prefix} | prego frontal",
                             (cx + sx * (width / 2 - post / 2), front_y - 0.018, z), mats[3]))
    for z in (bottom + rail * 0.50, bottom + height - rail * 0.50):
        for sy in (-1, 1):
            made.append(nail(f"{prefix} | prego lateral",
                             (side_x + 0.018, cy + sy * (depth / 2 - post / 2), z), mats[3]))
    return made


def setup_camera_and_lights():
    bpy.ops.object.camera_add(location=(2.65, -4.0, 2.55))
    camera = bpy.context.object
    camera.name = "Camera | miniatura isometrica"
    target = Vector((0, 0, 0.67))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.35
    bpy.context.scene.camera = camera

    for name, loc, power, size in (
        ("Luz principal", (1.5, -3.0, 4.0), 90, 3.0),
        ("Luz de preenchimento", (-3.0, -1.0, 2.4), 48, 3.0),
        ("Luz de recorte", (1.0, 2.5, 3.0), 72, 2.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (Vector((0, 0, 0.65)) - light.location).to_track_quat("-Z", "Y").to_euler()


def main():
    clear_scene()
    wood_a = make_material("Carvalho | mel envelhecido", (0.34, 0.16, 0.055))
    wood_b = make_material("Carvalho | tábuas claras", (0.46, 0.245, 0.09))
    wood_dark = make_material("Madeira | sombra entre tábuas", (0.18, 0.075, 0.025))
    iron = make_material("Ferro escurecido", (0.075, 0.08, 0.078), metallic=0.72, roughness=0.48)
    mats = (wood_a, wood_b, wood_dark, iron)

    all_prop = []
    crate_dims = (0.70, 0.64, 0.60)
    all_prop += make_crate("Caixote inferior esquerdo", -0.36, 0.0, 0.0, crate_dims, mats)
    all_prop += make_crate("Caixote inferior direito", 0.36, 0.0, 0.0, crate_dims, mats)
    all_prop += make_crate("Caixote superior", 0.0, 0.0, 0.60, crate_dims, mats)
    setup_camera_and_lights()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.world.color = (0.055, 0.055, 0.055)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(OUT / "caixotes_medievais_preview.png")
    bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "caixotes_medievais.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in all_prop:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = all_prop[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / "caixotes_medievais.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    print(f"EXPORTED crates={len(all_prop)} bounds=1.42x0.64x1.20")


if __name__ == "__main__":
    main()
