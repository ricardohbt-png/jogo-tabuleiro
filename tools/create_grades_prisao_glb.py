"""Cria o modelo 3D de uma seção reta de grades de prisão."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def material(name, color, metallic=0.72, roughness=0.46):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def block(name, location, dimensions, mat, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Arestas gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def rivet(name, location, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8,
                                        radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1.0, 0.38, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def make_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)

    asset_collection = bpy.data.collections.new("Grades de prisão - GLB")
    bpy.context.scene.collection.children.link(asset_collection)
    iron = material("Ferro forjado escurecido", (0.075, 0.082, 0.09))
    edge = material("Ferro gasto nas arestas", (0.18, 0.19, 0.20), metallic=0.78,
                    roughness=0.39)

    # Uma seção ocupa uma casa de largura; a altura cresce no eixo Z do Blender.
    width = 1.82
    post_x = width / 2 - 0.105
    post_y = 0.0
    height = 2.65
    parts = []

    # Colunas laterais reforçadas, bases, faixas de união e pontas forjadas.
    for side, x in (("esquerda", -post_x), ("direita", post_x)):
        parts.append(block(f"Coluna {side}", (x, post_y, height / 2),
                           (0.17, 0.18, height), iron, 0.025))
        parts.append(block(f"Sapata {side}", (x, post_y, 0.12),
                           (0.25, 0.27, 0.22), iron, 0.025))
        parts.append(block(f"Abraçadeira inferior {side}", (x, -0.004, 0.34),
                           (0.25, 0.25, 0.16), edge, 0.016))
        parts.append(block(f"Abraçadeira superior {side}", (x, -0.004, 2.34),
                           (0.25, 0.25, 0.17), edge, 0.016))
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.14, radius2=0.0,
                                        depth=0.19, location=(x, post_y, 2.78),
                                        rotation=(0, 0, math.pi / 4))
        cap = bpy.context.object
        cap.name = f"Ponta piramidal {side}"
        cap.data.materials.append(edge)
        parts.append(cap)
        for z in (0.34, 2.34):
            for offset in (-0.065, 0.065):
                parts.append(rivet("Rebite da coluna", (x + offset, -0.139, z),
                                   0.035, edge))

    # Travessas contínuas na frente, ligadas às colunas laterais.
    rail_mid = (2.34 + 0.17) / 2
    rail_height = 0.17
    rail_width = width - 0.035
    for name, z in (("Travessa superior", 2.34), ("Travessa inferior", 0.34)):
        parts.append(block(name, (0, -0.035, z),
                           (rail_width, 0.17, rail_height), iron, 0.024))
        for x in (-0.72, -0.48, -0.24, 0, 0.24, 0.48, 0.72):
            if abs(x) <= rail_width / 2 - 0.08:
                parts.append(rivet("Rebite da travessa", (x, -0.126, z),
                                   0.024, edge))

    # Barras quadradas e robustas; pequenos encaixes reforçam a junção com as travessas.
    bar_xs = (-0.59, -0.39, -0.195, 0.0, 0.195, 0.39, 0.59)
    bar_bottom = 0.44
    bar_top = 2.24
    for index, x in enumerate(bar_xs, 1):
        parts.append(block(f"Barra vertical {index}",
                           (x, 0.018, (bar_bottom + bar_top) / 2),
                           (0.063, 0.075, bar_top - bar_bottom), iron, 0.012))
        for z in (0.45, 2.23):
            parts.append(block(f"Encaixe da barra {index}", (x, -0.008, z),
                               (0.095, 0.12, 0.10), edge, 0.012))

    # Agrupa as peças para facilitar edição; exporta as malhas originais selecionadas.
    for obj in parts:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        asset_collection.objects.link(obj)
        obj.select_set(False)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.world.color = (0.045, 0.045, 0.045)

    camera_data = bpy.data.cameras.new("Camera de prévia")
    camera = bpy.data.objects.new("Camera de prévia", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (3.0, -5.2, 2.10)
    target = Vector((0, 0, 1.4))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 3.65
    scene.camera = camera

    for name, location, energy, size in (
        ("Luz principal", (-3.0, -4.0, 5.0), 620, 4.0),
        ("Luz de recorte", (3.0, 2.0, 3.8), 480, 3.0),
    ):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (Vector((0, 0, 1.25)) - light.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.filepath = str(OUT / "grades_prisao_preview.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "grades_prisao.blend"))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in asset_collection.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_collection.objects[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / "grades_prisao.glb"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    print(f"GRADE_PRISAO_EXPORT meshes={len(asset_collection.objects)}")


make_scene()
