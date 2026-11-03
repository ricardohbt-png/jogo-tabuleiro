"""Cria a miniatura do cocho de madeira para o tabuleiro.

Gera o PNG transparente da miniatura, a fonte editável .blend e o GLB usado
pela renderização 3D. Execute com Blender 5.1 em modo background.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in datablocks:
            if block.users == 0:
                datablocks.remove(block)


def material(name, color, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def plank(name, location, dimensions, mat, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Bordas suavizadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.affect = "EDGES"
        obj.modifiers.new("Normais das bordas", "WEIGHTED_NORMAL")
    return obj


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


clear_scene()

wood = [
    material("Madeira | castanho antigo", (0.20, 0.105, 0.052)),
    material("Madeira | carvalho quente", (0.31, 0.17, 0.082)),
    material("Madeira | tábua clara", (0.40, 0.235, 0.115)),
    material("Madeira | sombra", (0.115, 0.057, 0.030)),
]
metal = material("Ferro escurecido | cintas", (0.12, 0.14, 0.15), 0.58)
feed = [
    material("Ração | feno dourado", (0.58, 0.37, 0.12)),
    material("Ração | grão claro", (0.72, 0.52, 0.22)),
    material("Ração | sombra", (0.37, 0.22, 0.075)),
]

# O cocho mede cerca de 1,68 × 0,56 × 0,60; o eixo comprido acompanha X.
# A abertura é real, com fundo visível, paredes internas e tábuas externas.
length, width = 1.68, 0.56
bottom_z = 0.245
plank("Fundo interno escuro", (0, 0, bottom_z + 0.12), (1.38, 0.34, 0.035), wood[3], 0.006)
for i, yy in enumerate((-0.185, 0.0, 0.185)):
    plank("Tábua do fundo %d" % i, (0, yy, bottom_z + 0.085),
          (1.52, 0.18, 0.10), wood[(i + 1) % 3], 0.009)

# Quatro travessas robustas deixam a silhueta claramente apoiada no chão.
for side, yy in (("frente", -0.235), ("trás", 0.235)):
    for end, xx in (("esquerda", -0.66), ("direita", 0.66)):
        plank("Pé %s %s" % (side, end), (xx, yy, 0.105), (0.12, 0.12, 0.21), wood[0], 0.012)
    plank("Longarina inferior " + side, (0, yy, 0.19), (1.48, 0.10, 0.10), wood[0], 0.012)

# Laterais em duas fiadas, com pequenas frestas e tons alternados de madeira.
for side, yy in (("frontal", -0.245), ("traseira", 0.245)):
    for row, z in enumerate((0.32, 0.435)):
        plank("Lateral %s fiada %d" % (side, row), (0, yy, z),
              (1.64, 0.075, 0.105), wood[(row + (side == "traseira")) % 3], 0.012)

# Cabeceiras emolduradas e inclinadas levemente para fora, como uma gamela.
for end, xx in (("esquerda", -0.79), ("direita", 0.79)):
    obj = plank("Cabeceira " + end, (xx, 0, 0.355), (0.075, 0.51, 0.29), wood[1], 0.014)
    obj.rotation_euler[1] = -0.05 if end == "esquerda" else 0.05

# Aros metálicos curtos reforçam os cantos e ajudam a ler a forma em escala pequena.
for yy in (-0.287, 0.287):
    for xx in (-0.60, 0.60):
        plank("Cinta de ferro", (xx, yy, 0.395), (0.045, 0.012, 0.22), metal, 0.004)

# Ração baixa, irregular e abaixo da borda; preserva a leitura da cavidade.
for i in range(25):
    x = -0.57 + (i % 9) * 0.14 + (0.035 if i % 2 else 0)
    y = -0.12 + (i // 9) * 0.115
    z = 0.405 + 0.012 * math.sin(i * 1.7)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1,
                                           location=(x, y, z))
    obj = bpy.context.object
    obj.name = "Ração %02d" % i
    obj.scale = (0.075 + (i % 3) * 0.008, 0.035, 0.025 + (i % 2) * 0.006)
    obj.rotation_euler[2] = (i % 5) * 0.31
    obj.data.materials.append(feed[i % len(feed)])

# Assentar origem no centro do footprint e unir por material para reduzir draw calls.
for mat in wood + [metal] + feed:
    bpy.ops.object.select_all(action="DESELECT")
    group = [o for o in bpy.context.scene.objects
             if o.type == "MESH" and any(m == mat for m in o.data.materials)]
    if not group:
        continue
    for obj in group:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    group[0].name = "Cocho | " + mat.name
    group[0].data.name = group[0].name + " Mesh"

# Composição ortográfica isométrica, fundo transparente para o sprite 2D.
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.world = bpy.data.worlds.new("Mundo neutro do cocho")
scene.world.color = (0.08, 0.08, 0.08)

bpy.ops.object.camera_add(location=(1.85, -2.45, 2.10))
camera = bpy.context.object
camera.name = "Câmera da miniatura"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 2.28
point_at(camera, (0, 0, 0.31))
scene.camera = camera

for name, loc, energy, size, color in (
    ("Luz principal", (0.8, -1.7, 2.7), 95, 1.8, (1.0, 0.84, 0.65)),
    ("Preenchimento", (-1.5, -0.4, 1.6), 52, 1.7, (0.76, 0.84, 1.0)),
    ("Recorte", (0.5, 1.4, 2.3), 70, 1.3, (1.0, 0.72, 0.43)),
):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    point_at(light, (0, 0, 0.28))

scene.render.filepath = str(OUT / "cocho.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "cocho.blend"))
bpy.ops.render.render(write_still=True)

# Exporta somente a geometria do objeto; câmera e luzes ficam no .blend de fonte.
bpy.ops.object.select_all(action="DESELECT")
export_meshes = [o for o in scene.objects if o.type == "MESH"]
for obj in export_meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = export_meshes[0]
bpy.ops.export_scene.gltf(
    filepath=str(OUT / "cocho.glb"), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_materials="EXPORT")
print("COCHO_EXPORT", OUT / "cocho.glb", "meshes=", len(export_meshes))
