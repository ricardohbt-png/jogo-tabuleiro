"""Gera o modelo 3D editável da decoração moita e uma prévia renderizada."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, roughness=0.88):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
    return mat


def ellipsoid(name, location, scale, mat, segments=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def branch(name, points, radius, mat):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 4
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points):
        point.co = (*coord, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.context.object.select_set(False)


def leaf(name, base, direction, length, width, mat):
    """Folha larga e facetada, com nervura em relevo muito discreta."""
    origin = Vector(base)
    forward = Vector(direction).normalized()
    side = forward.cross(Vector((0, 0, 1)))
    if side.length < 1e-5:
        side = forward.cross(Vector((0, 1, 0)))
    side.normalize()
    middle = origin + forward * (length * 0.56)
    tip = origin + forward * length
    ridge = Vector((0, 0, 0.012))
    verts = [tuple(origin), tuple(middle - side * width * 0.48),
             tuple(middle + ridge), tuple(middle + side * width * 0.48),
             tuple(tip)]
    faces = [(0, 1, 2), (0, 2, 3), (1, 4, 2), (2, 4, 3),
             (2, 1, 0), (3, 2, 0), (2, 4, 1), (3, 4, 2)]
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)


def build_bush():
    rng = random.Random(62031)
    greens = [
        material("Folhas | verde floresta", (0.035, 0.105, 0.030)),
        material("Folhas | verde bosque", (0.060, 0.16, 0.040)),
        material("Folhas | oliva iluminado", (0.14, 0.23, 0.055)),
        material("Folhas | sombra", (0.022, 0.070, 0.025)),
    ]
    woods = [material("Galhos | castanho", (0.16, 0.075, 0.035)),
             material("Galhos | luz", (0.24, 0.115, 0.050))]
    moss = material("Musgo discreto na base", (0.08, 0.12, 0.035))

    # Um arbusto compacto, redondo e irregular; a base fica estreita para
    # assentar no tile sem a placa de chão usada em algumas peças de cenário.
    ellipsoid("Núcleo de folhagem", (0, 0, 0.34), (0.25, 0.23, 0.25), greens[0])
    for i in range(7):
        angle = math.tau * i / 7 + rng.uniform(-0.16, 0.16)
        radius = rng.uniform(0.21, 0.27)
        z = rng.uniform(0.26, 0.47)
        scale = (rng.uniform(0.12, 0.16), rng.uniform(0.11, 0.15),
                 rng.uniform(0.13, 0.17))
        center = (math.cos(angle) * radius, math.sin(angle) * radius, z)
        ellipsoid("Massa de folhas %02d" % i, center, scale, rng.choice(greens[:3]))

    # Folhas largas facetadas formam uma silhueta orgânica e volumosa.
    for i in range(38):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(0.19, 0.28)
        z = rng.uniform(0.23, 0.55)
        base = (math.cos(angle) * radius, math.sin(angle) * radius, z)
        foliage = ellipsoid("Folha larga %02d" % i, base,
                            (rng.uniform(0.11, 0.17), rng.uniform(0.040, 0.060),
                             rng.uniform(0.065, 0.095)), rng.choice(greens),
                            segments=10, rings=6)
        foliage.rotation_euler[2] = angle + rng.uniform(-0.35, 0.35)
        foliage.rotation_euler[1] = rng.uniform(-0.30, 0.30)

    # Ramos discretos visíveis somente junto à base.
    for i in range(5):
        angle = math.tau * i / 5 + rng.uniform(-0.2, 0.2)
        end = (math.cos(angle) * rng.uniform(0.22, 0.30),
               math.sin(angle) * rng.uniform(0.20, 0.28),
               rng.uniform(0.36, 0.48))
        branch("Ramo curto %02d" % i,
               [(0, 0, 0.06), (end[0] * 0.45, end[1] * 0.45, 0.23), end],
               0.012, woods[i % 2])

    # Pequenas manchas de musgo no contorno, sem formar um pedestal.
    for i in range(8):
        angle = math.tau * i / 8
        ellipsoid("Musgo da raiz %02d" % i,
                 (math.cos(angle) * 0.21, math.sin(angle) * 0.18, 0.045),
                 (0.070, 0.050, 0.025), moss, segments=8, rings=5)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    build_bush()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    for name, loc, energy, color in (
        ("Luz principal", (1.1, -1.5, 2.0), 70, (1.0, 0.90, 0.72)),
        ("Preenchimento", (-1.3, -0.5, 1.2), 36, (0.78, 0.94, 0.72)),
        ("Recorte", (0.4, 1.2, 1.6), 52, (0.88, 1.0, 0.76)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = 1.1
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.34))

    bpy.ops.object.camera_add(location=(1.35, -2.15, 1.55))
    camera = bpy.context.object
    camera.name = "Câmera de prévia"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.35
    point_at(camera, (0, 0, 0.34))
    scene.camera = camera
    scene.render.filepath = str(OUT / "moita_preview.png")

    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "moita.blend"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "moita.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT moita meshes=", len(meshes))


if __name__ == "__main__":
    main()
