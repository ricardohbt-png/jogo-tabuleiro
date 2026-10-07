"""Monta o caldeirão de poção sobre a brasa 3D já existente.

Saídas: assets/objetos/caldeirao.blend, caldeirao_pocao.glb e caldeirao_preview.png.
O GLB incorpora o loop de chama de brasa_chao_animada.glb e anima bolhas próprias.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
FIRE_GLB = OUT / "brasa_chao_animada.glb"
GLB_TEMP = OUT / "caldeirao_pocao.glb"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def pbr_material(name, color, metallic=0.0, roughness=0.7, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1.0)
        strength = bsdf.inputs.get("Emission Strength")
        if strength:
            strength.default_value = emission_strength
    return mat


def lathe_vessel(name, section, material, segments=96):
    """Gera a parede com superfície externa, borda e interior oco."""
    verts, faces = [], []
    for ring, (radius, z) in enumerate(section):
        for i in range(segments):
            a = 2 * math.pi * i / segments
            wav = 1.0 + 0.004 * math.sin(a * 7 + ring * 1.2) + 0.002 * math.sin(a * 13 - ring)
            verts.append((radius * wav * math.cos(a), radius * wav * math.sin(a), z))
    for ring in range(len(section) - 1):
        for i in range(segments):
            a = ring * segments + i
            b = ring * segments + (i + 1) % segments
            c = (ring + 1) * segments + (i + 1) % segments
            d = (ring + 1) * segments + i
            faces.append((a, b, c, d))
    # Fecha discretamente o fundo exterior e o fundo interno da panela.
    bottom = len(verts)
    verts.append((0.0, 0.0, section[0][1]))
    inner = len(verts)
    verts.append((0.0, 0.0, section[-1][1]))
    for i in range(segments):
        faces.append((bottom, (i + 1) % segments, i))
        last = (len(section) - 1) * segments
        faces.append((inner, last + i, last + (i + 1) % segments))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    return obj


def add_torus(name, major_radius, minor_radius, location, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=72, minor_segments=12,
        major_radius=major_radius, minor_radius=minor_radius,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def add_beam(name, start, end, radius, material, vertices=14):
    a, b = Vector(start), Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=direction.length,
        location=(a + b) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Bordas macias", "BEVEL")
    bevel.width = min(radius * 0.22, 0.012)
    bevel.segments = 2
    obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
    return obj


def liquid_surface(material):
    """Disco orgânico irregular preenchendo a abertura sem esconder o aro."""
    rings, segments = 8, 96
    radius, z0 = 0.488, 0.585
    verts = [(0.0, 0.0, z0 + 0.006)]
    faces = []
    for ring in range(1, rings + 1):
        r = radius * ring / rings
        for i in range(segments):
            a = 2 * math.pi * i / segments
            edge = 1.0 + 0.012 * math.sin(5 * a + 0.3) + 0.008 * math.sin(9 * a - 1.1)
            wave = (0.005 * math.sin(3 * a + r * 16) + 0.003 * math.sin(7 * a - r * 11)) * (r / radius)
            verts.append((r * edge * math.cos(a), r * edge * math.sin(a), z0 + wave))
    for i in range(segments):
        faces.append((0, 1 + i, 1 + (i + 1) % segments))
    for ring in range(1, rings):
        first, second = 1 + (ring - 1) * segments, 1 + ring * segments
        for i in range(segments):
            faces.append((first + i, second + i, second + (i + 1) % segments, first + (i + 1) % segments))
    mesh = bpy.data.meshes.new("Poção fervente Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new("Poção verde fervente", mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def animate_bubble(obj, index):
    """Bolha sobe, incha e estoura; as fases desencontradas mantêm o loop vivo."""
    phase = (index * 5) % 30
    bpy.context.scene.frame_set(1)
    for frame in range(1, 32):
        t = (frame - 1 - phase) % 30
        if t < 3:
            z, size = 0.572 + 0.006 * t, 0.003 + 0.006 * t
        elif t < 12:
            q = (t - 3) / 9
            z, size = 0.59 + 0.17 * q, 0.018 + 0.032 * math.sin(math.pi * q)
        elif t < 16:
            q = (t - 12) / 4
            z, size = 0.76 + 0.02 * q, 0.05 * (1 - q) + 0.002
        else:
            z, size = 0.58, 0.001
        obj.location.z = z
        obj.scale = (size, size, size * 1.12)
        obj.keyframe_insert(data_path="location", frame=frame, group="Subida e estouro")
        obj.keyframe_insert(data_path="scale", frame=frame, group="Subida e estouro")
    action = obj.animation_data.action if obj.animation_data else None
    if action:
        action.name = "Bolhas fervendo %02d" % index


clear_scene()

# Importa a miniatura 3D existente, incluindo brasa, chamas e o loop original.
bpy.ops.import_scene.gltf(filepath=str(FIRE_GLB))
fire_objects = list(bpy.context.scene.objects)
fire_meshes = [o for o in fire_objects if o.type == "MESH"]
if not fire_meshes:
    raise RuntimeError("O GLB de brasa não trouxe nenhuma malha.")

# A malha-base traz chamas triangulares no centro. Recortamos apenas a parte
# escondida pelo caldeirão; as pedras e brasas continuam visíveis ao redor.
fire_mesh = max(fire_meshes, key=lambda o: len(o.data.polygons))
bm = bmesh.new()
bm.from_mesh(fire_mesh.data)
buried = []
for face in bm.faces:
    center = fire_mesh.matrix_world @ face.calc_center_median()
    if math.hypot(center.x, center.y) < 0.775 and center.z > -0.245:
        buried.append(face)
if buried:
    bmesh.ops.delete(bm, geom=buried, context="FACES_ONLY")
bm.to_mesh(fire_mesh.data)
bm.free()
fire_mesh.data.update()

# As chamas originais sobem mais alto que a borda. Comprimimos somente a malha
# animada na vertical: o loop e a base de carvão permanecem, mas a chama fica
# sob o caldeirão e não atravessa a poção.
flame_offsets = {
    "Chama externa": (0.0, 0.73),
    "Chama interna": (-0.30, 0.66),
    "Nucleo luminoso": (0.30, 0.66),
}
for flame in (o for o in fire_meshes if o.name in flame_offsets):
    dx, dy = flame_offsets[flame.name]
    for vertex in flame.data.vertices:
        vertex.co.x += dx
        vertex.co.y += dy
        vertex.co.z *= 0.48
    flame.data.update()

iron = pbr_material("Ferro fundido escurecido", (0.055, 0.071, 0.078), metallic=0.78, roughness=0.34)
iron_lit = pbr_material("Arestas de ferro", (0.13, 0.16, 0.16), metallic=0.72, roughness=0.31)
bronze = pbr_material("Latão envelhecido", (0.34, 0.19, 0.055), metallic=0.76, roughness=0.36)
liquid_mat = pbr_material("Poção verde luminosa", (0.035, 0.34, 0.055), metallic=0.18,
                          roughness=0.22, emission=(0.025, 0.45, 0.025), emission_strength=0.52)
bubble_mat = pbr_material("Bolhas verde-limão", (0.38, 0.93, 0.12), metallic=0.08,
                          roughness=0.17, emission=(0.16, 0.85, 0.055), emission_strength=1.05)
swirl_mat = pbr_material("Redemoinho esmeralda", (0.18, 0.67, 0.06), metallic=0.16,
                         roughness=0.26, emission=(0.06, 0.36, 0.012), emission_strength=0.32)

# Corpo bojudo, borda espessa e cavidade interna: o líquido fica visível abaixo do aro.
section = [
    (0.39, -0.225), (0.45, -0.19), (0.53, -0.09), (0.63, 0.045),
    (0.69, 0.20), (0.68, 0.34), (0.62, 0.48), (0.56, 0.60),
    (0.575, 0.655), (0.565, 0.685), (0.515, 0.685), (0.495, 0.65),
    (0.50, 0.59), (0.55, 0.45), (0.59, 0.30), (0.57, 0.15),
    (0.48, -0.005), (0.35, -0.105), (0.08, -0.145),
]
pot = lathe_vessel("Panela bojuda de ferro", section, iron)

# Aro de latão na borda, cinta no bojo e pequenos rebites feitos em relevo.
add_torus("Aro maciço de latão", 0.563, 0.027, (0, 0, 0.671), bronze)
add_torus("Cinta superior de ferro", 0.655, 0.018, (0, 0, 0.355), iron_lit)
add_torus("Cinta inferior de ferro", 0.618, 0.015, (0, 0, 0.025), iron_lit)

# Duas alças laterais fundidas e seus encaixes reforçados.
for side in (-1, 1):
    x = side * 0.695
    add_torus("Alça lateral", 0.143, 0.026, (x, 0, 0.485), iron_lit, (0, math.pi / 2, 0))
    add_beam("Suporte da alça", (side * 0.56, 0, 0.51), (side * 0.70, 0, 0.51), 0.037, bronze)
    # Dois rebites nas placas de fixação.
    for dz in (-0.045, 0.045):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.022,
                                             location=(side * 0.605, -0.032, 0.51 + dz))
        rivet = bpy.context.object
        rivet.name = "Rebite de latão"
        rivet.scale = (1.0, 0.62, 1.0)
        rivet.data.materials.append(bronze)
        for face in rivet.data.polygons:
            face.use_smooth = True

# Três pés curtos apoiam o fundo de ferro sobre o leito de carvão.
for i, angle in enumerate((math.radians(90), math.radians(210), math.radians(330))):
    c, s = math.cos(angle), math.sin(angle)
    add_beam("Pé de sustentação %d" % (i + 1), (0.53 * c, 0.53 * s, -0.055),
             (0.40 * c, 0.40 * s, -0.245), 0.046, iron, vertices=16)
    add_beam("Sapato do pé %d" % (i + 1), (0.40 * c, 0.40 * s, -0.235),
             (0.40 * c, 0.40 * s, -0.275), 0.057, iron_lit, vertices=16)

liquid_surface(liquid_mat)
# Redemoinhos baixos na superfície dão leitura de viscosidade sem cobrir as bolhas.
for i, (x, y, radius) in enumerate(((-0.16, -0.08, 0.17), (0.16, 0.10, 0.115), (0.02, -0.20, 0.07))):
    swirl = add_torus("Veio da poção %d" % (i + 1), radius, 0.008, (x, y, 0.594 + i * 0.002), swirl_mat)
    swirl.scale.y = 0.72

# Bolhas tridimensionais em seis posições; suas animações se desencontram ao longo do loop.
for i, (x, y, radius) in enumerate((
    (-0.24, -0.13, 0.043), (-0.08, 0.15, 0.035), (0.13, -0.04, 0.047),
    (0.25, 0.16, 0.031), (-0.27, 0.19, 0.028), (0.05, -0.27, 0.038),
), start=1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1, location=(x, y, 0.58))
    bubble = bpy.context.object
    bubble.name = "Bolha animada %02d" % i
    bubble.scale = (0.001, 0.001, 0.001)
    bubble.data.materials.append(bubble_mat)
    for face in bubble.data.polygons:
        face.use_smooth = True
    # O raio controla cada ciclo, mantendo a animação correspondente à mesma bolha.
    bubble.scale = (radius, radius, radius * 1.1)
    animate_bubble(bubble, i)

# A cena de prévia não faz parte do GLB.
scene = bpy.context.scene
scene.frame_start, scene.frame_end, scene.render.fps = 1, 31, 24
scene.frame_set(9)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1400, 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.world.color = (0.035, 0.045, 0.055)

floor_mat = pbr_material("Fundo de apresentação", (0.075, 0.086, 0.102), roughness=0.96)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.53))
floor = bpy.context.object
floor.name = "Piso de prévia — não exportado"
floor.data.materials.append(floor_mat)

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(2.55, -3.65, 2.28))
camera = bpy.context.object
camera.name = "Câmera de prévia"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 2.55
point_at(camera, (0, 0, 0.05))
scene.camera = camera

for name, location, energy, size, color in (
    ("Luz principal quente", (1.8, -2.2, 3.2), 250, 1.9, (1.0, 0.73, 0.45)),
    ("Luz de preenchimento", (-2.4, -0.4, 1.55), 175, 1.8, (0.54, 0.78, 1.0)),
    ("Luz de recorte verde", (0.35, 2.1, 2.5), 185, 1.3, (0.58, 1.0, 0.35)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    point_at(light, (0, 0, 0.1))

scene.render.filepath = str(OUT / "caldeirao_preview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "caldeirao.blend"))
bpy.ops.render.render(write_still=True)

# Exporta malhas e empties originais do asset e seus pais animados, sem a cena de estúdio.
asset_objects = set(fire_objects)
asset_objects.update(o for o in bpy.context.scene.objects if o.type == "MESH" and o != floor)
for obj in list(asset_objects):
    parent = obj.parent
    while parent:
        asset_objects.add(parent)
        parent = parent.parent
bpy.ops.object.select_all(action="DESELECT")
for obj in asset_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = pot
bpy.ops.export_scene.gltf(
    filepath=str(GLB_TEMP),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_materials="EXPORT",
)
print("CALDEIRAO_EXPORT", GLB_TEMP, "asset_objects=", len(asset_objects),
      "actions=", [a.name for a in bpy.data.actions])
