"""Cria uma variante ninja da miniatura Kobold, sem alterar o GLB original.

Execute na raiz do projeto:
    "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" \
        --background --python tools/create_kobold_ninja.py
"""
from pathlib import Path
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models3d/monstros/kobold.glb"
OUTPUT = ROOT / "assets/models3d/monstros/kobold_ninja.glb"
BLEND = ROOT / "assets/models3d/monstros/kobold_ninja.blend"
PREVIEW = ROOT / "assets/models3d/monstros/kobold_ninja_preview.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def make_material(name, color, roughness=0.82, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def add_uv_sphere(name, location, scale, material, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def add_jacket(material):
    """Low-poly cloth shell fitted around the Kobold's hunched torso."""
    profile = [
        (-0.34, -0.12, -0.03, 0.19, 0.28),
        (-0.23, -0.14, -0.11, 0.24, 0.33),
        (-0.05, -0.16, -0.17, 0.27, 0.36),
        ( 0.13, -0.19, -0.21, 0.28, 0.34),
        ( 0.27, -0.20, -0.24, 0.25, 0.27),
    ]
    segments = 20
    vertices, faces = [], []
    for z, cx, cy, rx, ry in profile:
        for i in range(segments):
            angle = (2 * math.pi * i) / segments
            vertices.append((cx + rx * math.cos(angle),
                             cy + ry * math.sin(angle), z))
    for ring in range(len(profile) - 1):
        a0, a1 = ring * segments, (ring + 1) * segments
        for i in range(segments):
            n = (i + 1) % segments
            faces.append((a0 + i, a0 + n, a1 + n, a1 + i))
    faces.append(tuple(reversed(range(segments))))
    top = (len(profile) - 1) * segments
    faces.append(tuple(top + i for i in range(segments)))
    mesh = bpy.data.meshes.new("KoboldNinja_TorsoMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    jacket = bpy.data.objects.new("Roupa Ninja - túnica", mesh)
    bpy.context.collection.objects.link(jacket)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return jacket


def add_ribbon(name, points, width, material):
    """Extruded ribbon following a path in the XZ plane."""
    vertices, faces = [], []
    for i, (x, y, z) in enumerate(points):
        if i == 0:
            dx, dz = points[1][0] - x, points[1][2] - z
        elif i == len(points) - 1:
            dx, dz = x - points[i - 1][0], z - points[i - 1][2]
        else:
            dx, dz = points[i + 1][0] - points[i - 1][0], points[i + 1][2] - points[i - 1][2]
        length = max(1e-6, math.hypot(dx, dz))
        ox, oz = (-dz / length) * width / 2, (dx / length) * width / 2
        vertices.extend(((x - ox, y, z - oz), (x + ox, y, z + oz)))
    for i in range(len(points) - 1):
        a = i * 2
        faces.append((a + 2, a + 3, a + 1, a))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    solidify = obj.modifiers.new("espessura do tecido", "SOLIDIFY")
    solidify.thickness = 0.018
    bevel = obj.modifiers.new("borda suave", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    return obj


def add_belt(material):
    curve = bpy.data.curves.new("KoboldNinja_BeltCurve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = 0.027
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    count = 48
    spline.points.add(count - 1)
    cx, cy, z, rx, ry = -0.15, -0.20, -0.20, 0.29, 0.29
    for i, point in enumerate(spline.points):
        angle = 2 * math.pi * i / count
        point.co = (cx + rx * math.cos(angle), cy + ry * math.sin(angle), z, 1)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new("Roupa Ninja - faixa da cintura", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def paint_clothes_on_source(mesh_obj, cloth, trim, mask):
    """Color garment regions on the existing surface to avoid floating shells."""
    mesh = mesh_obj.data
    slots = {}
    for name, material in (("cloth", cloth), ("trim", trim), ("mask", mask)):
        mesh.materials.append(material)
        slots[name] = len(mesh.materials) - 1

    sash_start = Vector((-0.43, 0.18))
    sash_end = Vector((0.08, -0.24))
    sash_vec = sash_end - sash_start
    sash_len2 = max(1e-8, sash_vec.length_squared)
    counts = {key: 0 for key in slots}
    for poly in mesh.polygons:
        p = mesh_obj.matrix_world @ poly.center
        # Ninja jacket overlays the original torso armor, but follows its exact
        # triangles and leaves the Kobold's arms, legs and tail untouched.
        if (-0.36 <= p.z <= 0.22 and -0.47 <= p.x <= 0.31
                and -0.50 <= p.y <= 0.20):
            poly.material_index = slots["cloth"]
            counts["cloth"] += 1
        # A narrow muted-red waist sash wraps around the lower torso.
        if (-0.245 <= p.z <= -0.195 and -0.51 <= p.x <= 0.31
                and -0.62 <= p.y <= 0.25):
            poly.material_index = slots["trim"]
            counts["trim"] += 1
        # The diagonal chest sash follows front-facing torso polygons.
        point = Vector((p.x, p.z))
        t = max(0.0, min(1.0, (point - sash_start).dot(sash_vec) / sash_len2))
        if (point - (sash_start + t * sash_vec)).length < 0.036 and p.y < -0.20:
            poly.material_index = slots["trim"]
            counts["trim"] += 1
        # A cloth face covering and a compact head wrap, painted directly on
        # the model so the eyes, horns and muzzle keep their original shape.
        if (0.335 <= p.z <= 0.455 and -0.38 <= p.x <= 0.10
                and p.y < -0.74):
            poly.material_index = slots["mask"]
            counts["mask"] += 1
        if (0.625 <= p.z <= 0.675 and -0.43 <= p.x <= 0.06
                and p.y < -0.64):
            poly.material_index = slots["trim"]
            counts["trim"] += 1
        if (0.72 <= p.z <= 0.84 and -0.46 <= p.x <= 0.13
                and -0.58 <= p.y <= -0.12):
            poly.material_index = slots["cloth"]
            counts["cloth"] += 1
    print("Faces recolored:", counts)


def configure_preview():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.028, 0.035, 0.05)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.camera = None

    bpy.ops.object.camera_add(location=(3.15, -5.6, 3.1))
    camera = bpy.context.object
    camera.name = "PreviewCamera"
    target = Vector((-0.10, -0.05, -0.03))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.95
    scene.camera = camera

    lights = [
        ((-3.8, -4.8, 5.2), 720, 4.4),
        ((4.0, -1.5, 2.1), 430, 3.2),
        ((-1.0, 3.2, 4.2), 600, 3.5),
    ]
    for location, energy, size in lights:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    source_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not source_meshes:
        raise RuntimeError("O GLB de origem não contém malhas.")
    original = source_meshes[0]
    original.name = "Kobold original"

    cloth = make_material("Ninja - tecido azul-noite", (0.012, 0.026, 0.058), 0.92)
    trim = make_material("Ninja - faixa vinho", (0.085, 0.006, 0.012), 0.88)
    dark = make_material("Ninja - máscara grafite", (0.006, 0.009, 0.015), 0.94)
    paint_clothes_on_source(original, cloth, trim, dark)

    configure_preview()
    # A versão editável mantém as luzes/câmera do preview; o GLB contém só peões.
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == original)
    bpy.context.view_layer.objects.active = original
    bpy.ops.export_scene.gltf(
        filepath=str(OUTPUT), export_format="GLB", use_selection=True,
        export_apply=True, export_materials="EXPORT", export_texcoords=True,
        export_normals=True, export_cameras=False,
        export_lights=False)
    print(f"Exportado: {OUTPUT}")
    print(f"Blend: {BLEND}")
    print(f"Preview: {PREVIEW}")


if __name__ == "__main__":
    main()
