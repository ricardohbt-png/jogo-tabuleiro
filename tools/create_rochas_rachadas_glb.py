"""Gera a miniatura 1x1 de rochas rachadas em PNG e GLB."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "rochas_rachadas"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in list(collection):
            if data.users == 0:
                collection.remove(data)


def stone_material(name, color, roughness=0.92):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    nodes, links = material.node_tree.nodes, material.node_tree.links
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 31
    noise.inputs["Detail"].default_value = 3
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.018
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_rock(name, center, radii, materials, rng, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1,
                                          location=center)
    obj = bpy.context.object
    obj.name = name
    rx, ry, rz = radii
    for vertex in obj.data.vertices:
        x, y, z = vertex.co
        wobble = 1 + rng.uniform(-0.085, 0.085)
        vertex.co.x = x * rx * wobble
        vertex.co.y = y * ry * wobble
        # Slightly flattened bases make the stones sit directly on the map.
        vertex.co.z = max(-rz * 0.78, z * rz * (1 + rng.uniform(-0.09, 0.09)))
    for material in materials:
        obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = False
        if face.normal.z > 0.5:
            face.material_index = rng.choices((0, 1, 2), weights=(5, 3, 1))[0]
        else:
            face.material_index = rng.choices((0, 1, 2), weights=(3, 2, 3))[0]
    return obj


def crack_on_rock(name, rock, center, radii, path, dark):
    """Lay a thin fissure ribbon flush into the actual faceted rock surface."""
    rx, ry, _ = radii
    samples = []
    for nx, ny in path:
        x, y = center[0] + nx * rx, center[1] + ny * ry
        local_origin = Vector((x - center[0], y - center[1], 1.0))
        hit, local_point, _normal, _face = rock.ray_cast(local_origin, (0, 0, -1))
        if not hit:
            continue
        # Lift the decal by a tiny amount to prevent z-fighting while keeping
        # it visually flush with the faceted surface.
        samples.append((x, y, center[2] + local_point.z + .003))
    if len(samples) < 2:
        return

    verts, faces = [], []
    half_width = .007
    for index, (x, y, z) in enumerate(samples):
        before = samples[max(0, index - 1)]
        after = samples[min(len(samples) - 1, index + 1)]
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy) or 1
        px, py = -dy / length, dx / length
        taper = .5 if index in (0, len(samples) - 1) else 1.0
        w = half_width * taper
        verts.extend(((x + px*w, y + py*w, z), (x - px*w, y - py*w, z)))
        if index:
            a = index * 2
            faces.extend(((a-2, a-1, a+1), (a-2, a+1, a)))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(dark)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)


def build(seed=58231):
    rng = random.Random(seed)
    stone = [
        stone_material("Ermo | ardósia quente", (0.205, 0.196, 0.17)),
        stone_material("Ermo | faces gastas", (0.275, 0.257, 0.218)),
        stone_material("Ermo | sombras minerais", (0.135, 0.129, 0.116)),
    ]
    fissure = stone_material("Fissuras profundas", (0.02, 0.018, 0.015), 1.0)

    main_a = ((-0.105, -0.075, 0.112), (0.315, 0.238, 0.145))
    main_b = ((0.17, 0.125, 0.092), (0.235, 0.195, 0.118))
    rock_a = make_rock("Placa fraturada principal", *main_a, stone, rng, 2)
    rock_b = make_rock("Placa fraturada lateral", *main_b, stone, rng, 2)
    # Separate chips around the main plates give the cluster a broken silhouette.
    for index, (pos, scale) in enumerate((
        ((-0.345, 0.16, 0.045), (0.09, 0.075, 0.055)),
        ((0.33, -0.18, 0.042), (0.075, 0.060, 0.05)),
        ((-0.28, -0.25, 0.036), (0.062, 0.052, 0.04)),
        ((0.05, 0.34, 0.035), (0.055, 0.048, 0.04)),
        ((0.37, 0.20, 0.031), (0.044, 0.037, 0.032)),
    )):
        make_rock("Estilhaço de rocha %02d" % index, pos, scale, stone, rng, 1)

    crack_on_rock("Fenda principal da placa", rock_a, *main_a,
                  [(-0.98, 0.13), (-0.58, 0.02), (-0.20, 0.18),
                   (0.12, -0.02), (0.54, -0.16), (0.95, -0.04)], fissure)
    crack_on_rock("Ramo de fissura esquerda", rock_a, *main_a,
                  [(-0.26, 0.14), (-0.44, 0.42), (-0.38, 0.79)], fissure)
    crack_on_rock("Ramo de fissura inferior", rock_a, *main_a,
                  [(0.10, -0.02), (-0.02, -0.34), (0.15, -0.72)], fissure)
    crack_on_rock("Fenda da placa lateral", rock_b, *main_b,
                  [(-0.90, -0.22), (-0.48, 0.03), (-0.08, -0.12),
                   (0.28, 0.10), (0.86, 0.23)], fissure)
    crack_on_rock("Ramo lateral de fratura", rock_b, *main_b,
                  [(-0.08, -0.12), (0.04, -0.43), (-0.20, -0.76)], fissure)

    # A few stone crumbs sit in the fissures without making a soil mound.
    for index, (x, y, size) in enumerate(((-0.06, -0.025, .022),
                                          (.03, -.005, .016),
                                          (.23, .095, .018))):
        make_rock("Cascalho na rachadura %02d" % index,
                  (x, y, size * .72), (size, size * .75, size),
                  stone, rng, 1)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.065, 0.06, 0.053, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    for name, location, energy, size, color in (
        ("Sol filtrado", (1.0, -1.4, 1.8), 48, 1.05, (1.0, .83, .66)),
        ("Luz fria do céu", (-1.2, -.35, 1.2), 28, 1.0, (.74, .82, .92)),
        ("Recorte mineral", (.1, 1.0, 1.35), 36, .8, (1.0, .78, .53)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, .13))
    bpy.ops.object.camera_add(location=(1.35, -2.25, 1.62))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.18
    point_at(camera, (0, 0, .13))
    scene.camera = camera


def merge_by_material():
    for material in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and material in obj.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Rochas rachadas | " + material.name


def main():
    clear_scene()
    build()
    merge_by_material()
    setup_scene()
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))
    scene.render.film_transparent = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    main()
