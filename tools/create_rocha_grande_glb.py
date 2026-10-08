"""Cria uma rocha maciça marrom para o editor e o tabuleiro 3D."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "rocha_grande"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in list(collection):
            if data.users == 0:
                collection.remove(data)


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .94
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 32
    noise.inputs["Detail"].default_value = 2
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .11
    bump.inputs["Distance"].default_value = .018
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def build():
    rng = random.Random(72026)
    stones = [
        material("Rocha | marrom-terra", (.36, .205, .115)),
        material("Rocha | ocre quente", (.45, .275, .155)),
        material("Rocha | face iluminada", (.53, .345, .205)),
        material("Rocha | sombra", (.285, .155, .09)),
        material("Rocha | mineral", (.40, .255, .17)),
    ]

    # Uma única malha de icosfera, deformada para formar uma rocha contínua.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1,
                                          location=(0, 0, .62))
    rock = bpy.context.object
    rock.name = "Rocha grande maciça"
    rock.data.name = "Malha contínua da rocha"
    for vert in rock.data.vertices:
        direction = vert.co.normalized()
        broad = 1 + .075 * math.sin(direction.x * 5.1 + direction.y * 2.8)
        broad += .045 * math.cos(direction.y * 6.2 - direction.z * 3.7)
        broad *= rng.uniform(.91, 1.09)
        vert.co.x *= 1.00 * broad
        vert.co.y *= .78 * broad
        vert.co.z *= .73 * broad
        if vert.co.z < -.42:
            vert.co.z = -.42 + (vert.co.z + .42) * .20
    for stone in stones:
        rock.data.materials.append(stone)
    for face in rock.data.polygons:
        face.material_index = rng.choices(range(len(stones)),
                                           weights=(35, 27, 13, 15, 10))[0]
        face.use_smooth = False

    # A base achatada encosta no piso; as dimensões ficam dentro do footprint 2x2.
    rock.location.z = .49


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
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .25
    for name, loc, energy, size, color in (
        ("Luz quente", (2.2, -2.7, 3.2), 55, 2.2, (1.0, .86, .72)),
        ("Preenchimento", (-2.0, -1.1, 1.8), 30, 2.4, (.82, .87, .94)),
        ("Recorte", (.3, 2.1, 2.8), 42, 1.8, (1.0, .82, .66)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, .55))
    bpy.ops.object.camera_add(location=(2.4, -3.6, 2.5))
    camera = bpy.context.object
    camera.name = "Câmera da rocha"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.65
    point_at(camera, (0, 0, .57))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))


def export():
    clear_scene()
    build()
    setup_scene()
    bpy.ops.object.select_all(action="DESELECT")
    rock = bpy.data.objects["Rocha grande maciça"]
    rock.select_set(True)
    bpy.context.view_layer.objects.active = rock
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=1")


if __name__ == "__main__":
    export()
