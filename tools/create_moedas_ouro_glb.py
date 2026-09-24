"""Cria um montinho de moedas de ouro para loot no chão da masmorra.

Roda da raiz do projeto:
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" --background --python tools/create_moedas_ouro_glb.py

Referência aprovada: assets/itens/moedas_ouro_referencia.png
Conceito gerado com OpenAI ImageGen; a malha final é procedural, feita no Blender.
"""
from __future__ import annotations

import math
import struct
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "itens" / "moedas_ouro.glb"
PREVIEW = ROOT / "assets" / "itens" / "moedas_ouro_preview.png"

RADIUS = 0.105
THICKNESS = 0.018
STACK_STEP = 0.0165


def make_material(name: str, color, metallic: float, roughness: float):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def finish_mesh(obj, material, bevel=0.0):
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("borda_arredondada", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return obj


def create_coin(name, x, y, bottom, angle, gold, bright, emblem=False):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=RADIUS,
        depth=THICKNESS,
        location=(x, y, bottom + THICKNESS / 2),
        rotation=(0, 0, angle),
    )
    coin = finish_mesh(bpy.context.object, gold, bevel=0.0024)
    coin.name = name
    MODEL_OBJECTS.append(coin)

    top = bottom + THICKNESS
    bpy.ops.mesh.primitive_torus_add(
        major_segments=48,
        minor_segments=8,
        location=(x, y, top - 0.0011),
        major_radius=RADIUS - 0.009,
        minor_radius=0.0021,
        rotation=(0, 0, angle),
    )
    rim = finish_mesh(bpy.context.object, bright)
    rim.name = f"{name}_friso"
    MODEL_OBJECTS.append(rim)

    if emblem:
        # Pequeno sol em relevo, legível nas faces que aparecem no tabuleiro.
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=0.018,
            depth=0.0016,
            location=(x, y, top + 0.0002),
        )
        center = finish_mesh(bpy.context.object, bright, bevel=0.0004)
        center.name = f"{name}_simbolo_central"
        MODEL_OBJECTS.append(center)

        z0 = top + 0.00015
        for ray in range(8):
            theta = angle + ray * math.tau / 8
            half_inner = 0.055
            half_outer = 0.032
            points = [
                (0.025 * math.cos(theta - half_inner), 0.025 * math.sin(theta - half_inner)),
                (0.025 * math.cos(theta + half_inner), 0.025 * math.sin(theta + half_inner)),
                (0.052 * math.cos(theta + half_outer), 0.052 * math.sin(theta + half_outer)),
                (0.052 * math.cos(theta - half_outer), 0.052 * math.sin(theta - half_outer)),
            ]
            vertices = [(x + px, y + py, z0) for px, py in points]
            vertices += [(vx, vy, vz + 0.0012) for vx, vy, vz in vertices]
            faces = [(3, 2, 1, 0), (4, 5, 6, 7)]
            faces += [(i, (i + 1) % 4, (i + 1) % 4 + 4, i + 4) for i in range(4)]
            mesh = bpy.data.meshes.new(f"{name}_raio_{ray + 1}_mesh")
            mesh.from_pydata(vertices, [], faces)
            mesh.materials.append(bright)
            ray_obj = bpy.data.objects.new(f"{name}_raio_{ray + 1}", mesh)
            bpy.context.collection.objects.link(ray_obj)
            MODEL_OBJECTS.append(ray_obj)


def aim_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_preview():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.04, 0.05, 1.0)
    background.inputs["Strength"].default_value = 0.08

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.002))
    floor = bpy.context.object
    floor.name = "preview_floor_only"
    floor_mat = make_material("preview_neutral_floor", (0.055, 0.065, 0.08), 0.0, 0.92)
    floor.data.materials.append(floor_mat)

    bpy.ops.object.camera_add(location=(0.82, -1.12, 0.91))
    camera = bpy.context.object
    camera.name = "preview_camera_only"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.82
    aim_at(camera, (0, 0.02, 0.075))
    scene.camera = camera

    for name, location, energy, size in [
        ("key", (0.0, -0.65, 1.25), 25.0, 0.75),
        ("fill", (-0.75, 0.15, 0.72), 12.0, 0.60),
        ("rim", (0.55, 0.60, 0.85), 20.0, 0.48),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = f"preview_light_{name}"
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        aim_at(light, (0, 0, 0.05))

    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def validate_glb(path: Path):
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise RuntimeError("Exportação inválida: cabeçalho GLB ausente")
    version, total_length = struct.unpack_from("<II", raw, 4)
    if version != 2 or total_length != len(raw):
        raise RuntimeError("Exportação inválida: versão ou tamanho GLB inconsistente")
    json_length, chunk_type = struct.unpack_from("<I4s", raw, 12)
    if chunk_type != b"JSON":
        raise RuntimeError("Exportação inválida: primeiro chunk JSON ausente")
    doc = json.loads(raw[20:20 + json_length].decode("utf-8"))
    if not doc.get("meshes") or not doc.get("materials"):
        raise RuntimeError("Exportação incompleta: meshes ou materiais ausentes")
    print(
        f"GLB validado: {path} | {len(raw)} bytes | "
        f"{len(doc['meshes'])} meshes | {len(doc['materials'])} materiais | "
        f"{len(doc.get('nodes', []))} nodes"
    )


def build():
    global MODEL_OBJECTS
    MODEL_OBJECTS = []
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    gold = make_material("ouro_polido", (0.72, 0.26, 0.018), 0.80, 0.30)
    bright = make_material("ouro_claro_relevo", (0.95, 0.45, 0.045), 0.76, 0.27)

    # Pilha baixa de seis moedas; pequenos desvios dão um aspecto natural sem
    # comprometer a estabilidade nem o assentamento do conjunto.
    for index in range(6):
        x = (0.006 if index % 2 else -0.004) * (index / 5)
        y = (0.003 if index % 2 else -0.003) * (index / 5)
        create_coin(
            f"moeda_pilha_{index + 1}", x, y, 0.0 + index * STACK_STEP,
            angle=index * 0.13, gold=gold, bright=bright, emblem=(index == 5),
        )

    # Três moedas soltas contornam a pilha; todas repousam com a face marcada
    # para cima, sem peças suspensas ou eixo dependente da câmera.
    for index, (x, y, angle) in enumerate([
        (-0.185, -0.075, -0.28),
        (0.184, -0.075, 0.22),
        (0.145, 0.190, -0.14),
    ], start=1):
        create_coin(
            f"moeda_sol_v{index}", x, y, 0.0, angle,
            gold=gold, bright=bright, emblem=True,
        )

    setup_preview()

    # A câmera, luzes e piso são somente para a prévia, não entram no asset.
    # Unir as peças por material deixa o item leve quando várias pilhas são
    # carregadas ao mesmo tempo no tabuleiro.
    merged_objects = []
    for material in (gold, bright):
        group = [
            obj for obj in bpy.context.scene.objects
            if obj.type == "MESH" and material in list(obj.data.materials)
        ]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        merged = bpy.context.view_layer.objects.active
        merged.name = f"moedas_{material.name}_malha"
        merged_objects.append(merged)
    MODEL_OBJECTS = merged_objects

    bpy.ops.object.select_all(action="DESELECT")
    for obj in MODEL_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = MODEL_OBJECTS[0]
    bpy.ops.export_scene.gltf(
        filepath=str(OUT),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
        export_yup=True,
    )
    validate_glb(OUT)
    print(f"Prévia renderizada: {PREVIEW}")


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build()
