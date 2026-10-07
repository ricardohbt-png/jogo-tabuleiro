"""Cria a miniatura 3D de um monte de feno para o tabuleiro.

Gera a fonte editável .blend, a prévia PNG e o GLB usado pelo jogo.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(48127)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def material(name, color, roughness=0.86):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def make_uv_blob(name, center, scale, mat, seed, segments=24, rings=16):
    rng = random.Random(seed)
    verts, faces = [], []
    for j in range(rings + 1):
        phi = math.pi * j / rings
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            noise = 1.0 + rng.uniform(-0.045, 0.045)
            verts.append((
                center[0] + scale[0] * math.sin(phi) * math.cos(theta) * noise,
                center[1] + scale[1] * math.sin(phi) * math.sin(theta) * noise,
                center[2] + scale[2] * math.cos(phi) * noise,
            ))
    for j in range(rings):
        for i in range(segments):
            a = j * segments + i
            b = j * segments + (i + 1) % segments
            c = (j + 1) * segments + (i + 1) % segments
            d = (j + 1) * segments + i
            # Ordem invertida: faces apontam para fora do volume.
            faces.append((a, d, c, b))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    return obj


def add_tapered_strand(name, points, radius, mat, sides=5):
    """Malha tubular fina, com pontas afiladas e geometria exportável sem curves."""
    verts, faces = [], []
    pts = [Vector(p) for p in points]
    for k, point in enumerate(pts):
        tangent = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        helper = Vector((0, 0, 1)) if abs(tangent.z) < 0.92 else Vector((0, 1, 0))
        u = tangent.cross(helper).normalized()
        v = tangent.cross(u).normalized()
        taper = min(1.0, 0.38 + min(k, len(pts) - 1 - k) * 0.28)
        rr = radius * taper
        for n in range(sides):
            ang = 2 * math.pi * n / sides
            q = point + rr * (math.cos(ang) * u + math.sin(ang) * v)
            verts.append(tuple(q))
    for k in range(len(pts) - 1):
        for n in range(sides):
            a = k * sides + n
            b = k * sides + (n + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    start = (len(pts) - 1) * sides
    faces.append(tuple(start + n for n in range(sides)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def straw_surface(phi, theta, offset=0.0):
    # Perfil de um monte irregular, com topo deslocado e contorno sem simetria perfeita.
    profile = ((0.00, 0.510, 0.018), (0.10, 0.465, 0.125), (0.20, 0.405, 0.225),
               (0.30, 0.345, 0.292), (0.40, 0.285, 0.340), (0.50, 0.225, 0.370),
               (0.60, 0.170, 0.382), (0.70, 0.120, 0.380), (0.80, 0.075, 0.365),
               (0.90, 0.040, 0.325), (1.00, 0.000, 0.270))
    t = max(0.0, min(1.0, phi / math.pi))
    for k in range(len(profile) - 1):
        if profile[k][0] <= t <= profile[k + 1][0]:
            f = (t - profile[k][0]) / (profile[k + 1][0] - profile[k][0])
            z = profile[k][1] * (1 - f) + profile[k + 1][1] * f
            r = profile[k][2] * (1 - f) + profile[k + 1][2] * f
            break
    wav = (1.0 + 0.072 * math.sin(theta * 3 + phi * 1.7)
           + 0.036 * math.sin(theta * 7 - phi * 2.4)
           + 0.018 * math.sin(theta * 11 + phi * 4.0))
    r = r * wav + offset
    cx, cy = 0.035 * t, -0.025 * t
    z += 0.026 * math.sin(theta * 3 + phi * 2) + 0.012 * math.cos(theta * 7 - phi)
    return (cx + r * math.cos(theta), cy + r * 0.92 * math.sin(theta),
            z + offset * (1 - t))


def make_mound(mat):
    verts, faces = [], []
    rings, segments = 64, 96
    for j in range(rings + 1):
        phi = math.pi * j / rings
        for i in range(segments):
            verts.append(straw_surface(phi, 2 * math.pi * i / segments))
    for j in range(rings):
        for i in range(segments):
            a = j * segments + i
            b = j * segments + (i + 1) % segments
            c = (j + 1) * segments + (i + 1) % segments
            d = (j + 1) * segments + i
            faces.append((a, d, c, b))
    top_center = len(verts)
    verts.append((0.0, 0.0, 0.510))
    bottom_center = len(verts)
    verts.append((0.035, -0.025, 0.000))
    for i in range(segments):
        faces.append((top_center, i, (i + 1) % segments))
        last = rings * segments
        faces.append((bottom_center, last + (i + 1) % segments, last + i))
    mesh = bpy.data.meshes.new("Massa do feno Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new("Massa do monte de feno", mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def add_straw_blade(name, points, width, thickness, mat, sides=6):
    """Feixe achatado com pontas afinadas e seção irregular, sem aparência de arame."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    count = len(pts)
    for k, point in enumerate(pts):
        tangent = (pts[min(k + 1, count - 1)] - pts[max(k - 1, 0)]).normalized()
        radial = Vector((point.x - 0.035, point.y + 0.025, 0.22)).normalized()
        side = tangent.cross(radial)
        if side.length < 1e-5:
            side = tangent.cross(Vector((0, 1, 0)))
        side.normalize()
        normal = side.cross(tangent).normalized()
        taper = min(1.0, 0.42 + min(k, count - 1 - k) * 0.34)
        wobble = 1.0 + 0.12 * math.sin(k * 1.71 + point.x * 29.0)
        for n in range(sides):
            a = 2 * math.pi * n / sides
            q = point + side * (math.cos(a) * width * 0.5 * taper * wobble)
            q += normal * (math.sin(a) * thickness * 0.5 * taper)
            verts.append(tuple(q))
    for k in range(count - 1):
        for n in range(sides):
            a = k * sides + n
            b = k * sides + (n + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides - 1, -1, -1)))
    start = (count - 1) * sides
    faces.append(tuple(start + n for n in range(sides)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


clear_scene()

# Tons quentes e distintos deixam fibras e camadas legíveis também em escala de jogo.
hay_mats = [
    material("Feno | dourado seco", (0.40, 0.265, 0.115), 0.96),
    material("Feno | palha mel", (0.52, 0.355, 0.165), 0.95),
    material("Feno | fibras claras", (0.62, 0.455, 0.235), 0.94),
    material("Feno | sombra tostada", (0.30, 0.185, 0.075), 0.98),
    material("Feno | palha pálida", (0.56, 0.465, 0.295), 0.96),
]
# Massa orgânica e baixa, com a base larga assentada diretamente no chão.
make_mound(hay_mats[0])

# Feixes pequenos seguem trajetórias próximas e paralelas, como palha assentada
# em camadas. O sentido varia entre grupos para quebrar a aparência de espiral.
strand_id = 0
bundle = 0
for row in range(16):
  for column in range(42):
    phi_center = 0.20 + row * (2.62 / 15) + random.uniform(-0.055, 0.055)
    theta_center = 2 * math.pi * (column + random.uniform(-0.32, 0.32)) / 42
    direction = random.choice((-1, 1))
    dphi_center = direction * random.uniform(0.38, 0.88)
    dtheta_center = random.uniform(-0.48, 0.48)
    for strand in range(random.randint(1, 2)):
        phi0 = phi_center + random.uniform(-0.025, 0.025)
        theta0 = theta_center + random.uniform(-0.035, 0.035)
        dphi = dphi_center + random.uniform(-0.12, 0.12)
        dtheta = dtheta_center + random.uniform(-0.12, 0.12)
        off = random.uniform(0.004, 0.010)
        pts = []
        for j in range(8):
            t = j / 7
            phi = max(0.12, min(3.00, phi0 + dphi * t + 0.025 * math.sin(math.pi * t + strand)))
            theta = theta0 + dtheta * t + 0.018 * math.sin(2 * math.pi * t + bundle)
            pts.append(straw_surface(phi, theta, off + 0.001 * math.sin(math.pi * t)))
        mat = random.choices(hay_mats, weights=(36, 28, 13, 12, 11), k=1)[0]
        add_straw_blade("Feixe %03d" % strand_id, pts,
                        random.uniform(0.0045, 0.0080),
                        random.uniform(0.0013, 0.0022), mat)
        strand_id += 1
    bundle += 1

# Fibras compridas quebram a silhueta, sem formar uma franja uniforme ao redor.
for i in range(22):
    theta0 = random.uniform(0, 2 * math.pi)
    start = random.uniform(0.72, 1.65)
    end = random.uniform(2.25, 2.88)
    pts = [straw_surface(start + (end - start) * j / 8,
                         theta0 + 0.30 * j / 8 + 0.06 * math.sin(j + i), 0.012)
           for j in range(9)]
    add_straw_blade("Haste comprida %02d" % i, pts,
                    random.uniform(0.0035, 0.0060), 0.0017,
                    random.choice(hay_mats[:4]))

# Pontas cortadas e cruzadas junto à base, como palha que escapou do amontoado.
for i in range(30):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.285, 0.345)
    z = random.uniform(0.025, 0.105)
    length = random.uniform(0.045, 0.095)
    p0 = (0.035 + r * math.cos(a), -0.025 + r * math.sin(a), z)
    p1 = (0.035 + (r + length * 0.48) * math.cos(a + 0.10),
          -0.025 + (r + length * 0.48) * math.sin(a + 0.10), z + random.uniform(-0.004, 0.016))
    p2 = (0.035 + (r + length) * math.cos(a + 0.18),
          -0.025 + (r + length) * math.sin(a + 0.18), z + random.uniform(-0.008, 0.020))
    add_straw_blade("Ponta de palha %02d" % i, [p0, p1, p2],
                    random.uniform(0.004, 0.007), 0.0018,
                    random.choice(hay_mats[1:]))

# Consolidar por material reduz draw calls e deixa a miniatura leve para o tabuleiro.
for mat in hay_mats:
    bpy.ops.object.select_all(action="DESELECT")
    group = [o for o in bpy.context.scene.objects if o.type == "MESH" and any(m == mat for m in o.data.materials)]
    if not group:
        continue
    for obj in group:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    group[0].name = "Monte de feno | " + mat.name
    group[0].data.name = group[0].name + " Mesh"

# Origem no centro do footprint e base exatamente no piso; dimensões finais ~0.78×0.72×0.54.
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1200
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.render.film_transparent = False
bpy.context.scene.world.color = (0.055, 0.065, 0.085)

floor_mat = material("Fundo de prévia", (0.075, 0.085, 0.105), 1.0)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.006))
floor = bpy.context.object
floor.name = "Piso de prévia (não exportado)"
floor.data.materials.append(floor_mat)

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(1.45, -2.15, 1.38))
camera = bpy.context.object
camera.name = "Câmera de prévia"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 1.55
point_at(camera, (0, 0, 0.26))
bpy.context.scene.camera = camera

for name, loc, energy, size, color in (
    ("Luz principal", (1.2, -1.4, 2.4), 38, 1.25, (1.0, 0.88, 0.69)),
    ("Luz de preenchimento", (-1.6, -0.4, 1.1), 18, 1.4, (1.0, 0.96, 0.85)),
    ("Luz de recorte", (0.4, 1.4, 1.9), 26, 0.9, (1.0, 0.80, 0.53)),
):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    point_at(light, (0, 0, 0.22))

scene = bpy.context.scene
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.render.filepath = str(OUT / "monte_feno_preview.png")
scene.camera.data.lens = 55
scene.render.resolution_x = 1400
scene.render.resolution_y = 1200
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "monte_feno.blend"))
bpy.ops.render.render(write_still=True)

# Exporta só as malhas do asset, sem piso, luzes e câmera da composição.
bpy.ops.object.select_all(action="DESELECT")
export_meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o != floor]
for obj in export_meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = export_meshes[0]
bpy.ops.export_scene.gltf(
    filepath=str(OUT / "monte_feno.glb"),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
)
print("MONTE_FENO_EXPORT", OUT / "monte_feno.glb", "meshes=", len(export_meshes))
