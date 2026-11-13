import math
import os
import random
import bpy
from mathutils import Vector


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "models3d", "monstros")
os.makedirs(OUT, exist_ok=True)
BLEND_PATH = os.path.join(OUT, "vaca.blend")
GLB_PATH = os.path.join(OUT, "vaca.glb")
PREVIEW_PATH = os.path.join(OUT, "vaca_preview.png")


def material(name, color, roughness=0.72, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = metallic
    return mat


WHITE = material("Pelagem marfim", (0.88, 0.86, 0.77))
BLACK = material("Manchas pretas", (0.035, 0.045, 0.052))
HOOF = material("Casco castanho escuro", (0.16, 0.105, 0.073), 0.5)
HORN = material("Chifre marfim", (0.77, 0.69, 0.51), 0.48)
MUZZLE = material("Focinho rosado", (0.75, 0.36, 0.32), 0.48)
NOSTRIL = material("Narinas", (0.12, 0.045, 0.042), 0.4)
EYE = material("Olhos", (0.035, 0.025, 0.02), 0.22)
EYE_GLEAM = material("Brilho dos olhos", (0.98, 0.9, 0.72), 0.18)
UDDER = material("Úbere", (0.68, 0.38, 0.34), 0.65)
TAIL_TIP = material("Ponta da cauda", (0.09, 0.07, 0.055), 0.8)

CREATED = []


def finish(obj, name, mat, smooth=True):
    obj.name = name
    obj.data.materials.append(mat)
    if obj.type == "MESH" and smooth:
        for face in obj.data.polygons:
            face.use_smooth = True
    CREATED.append(obj)
    return obj


def uv_sphere(name, loc, scale, mat, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat)


def capsule_leg(name, x, y, height=0.64, radius_top=0.105, radius_bottom=0.078):
    z0 = 0.23
    z1 = z0 + height
    bpy.ops.mesh.primitive_cone_add(
        vertices=20, radius1=radius_bottom, radius2=radius_top,
        depth=height, location=(x, y, (z0 + z1) / 2.0))
    obj = bpy.context.object
    bevel = obj.modifiers.new("Arredondamento suave", "BEVEL")
    bevel.width = 0.055
    bevel.segments = 3
    obj.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    finish(obj, name, WHITE)
    uv_sphere(name + " junta", (x, y, z1 - 0.03), (radius_top, radius_top, 0.12), WHITE, 20, 12)
    uv_sphere(name + " casco", (x + 0.045, y, 0.15), (0.14, 0.105, 0.10), HOOF, 24, 14)


def curve_tube(name, points, radius, mat, resolution=12):
    curve = bpy.data.curves.new(name + " forma", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    CREATED.append(obj)
    return obj


def ellipsoid_patch(name, center, radii, phi_center, lat_center, size_phi, size_lat,
                    seed, surface_offset=0.006, segments=40):
    """Black irregular mesh patch fitted directly onto an ellipsoid surface."""
    cx, cy, cz = center
    rx, ry, rz = radii
    rng = random.Random(seed)
    phases = [rng.uniform(-0.08, 0.08) for _ in range(segments)]
    verts = []
    rings = 4
    center_lat = max(-1.35, min(1.35, lat_center))
    center_n = (math.cos(center_lat) * math.cos(phi_center),
                math.cos(center_lat) * math.sin(phi_center), math.sin(center_lat))
    center_normal = Vector((center_n[0] / rx, center_n[1] / ry, center_n[2] / rz)).normalized()
    center_point = Vector((cx + rx * center_n[0], cy + ry * center_n[1], cz + rz * center_n[2]))
    verts.append(tuple(center_point + center_normal * surface_offset))
    for ring in range(1, rings + 1):
        frac = ring / rings
        for i in range(segments):
            angle = (2 * math.pi * i / segments)
            wave = 1.0 + 0.15 * math.sin(3 * angle + phases[i]) + 0.09 * math.sin(5 * angle - seed)
            dphi = math.cos(angle) * size_phi * frac * wave
            dlat = math.sin(angle) * size_lat * frac * wave
            phi = phi_center + dphi
            lat = max(-1.35, min(1.35, lat_center + dlat))
            nx = math.cos(lat) * math.cos(phi)
            ny = math.cos(lat) * math.sin(phi)
            nz = math.sin(lat)
            # Ellipsoid normal gives an even, barely raised offset without a flat decal.
            normal = Vector((nx / rx, ny / ry, nz / rz)).normalized()
            point = Vector((cx + rx * nx, cy + ry * ny, cz + rz * nz)) + normal * surface_offset
            verts.append(tuple(point))
    faces = []
    first = 1
    for i in range(segments):
        faces.append((0, first + i, first + (i + 1) % segments))
    for ring in range(1, rings):
        a0 = 1 + (ring - 1) * segments
        b0 = 1 + ring * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((a0 + i, b0 + i, b0 + j, a0 + j))
    mesh = bpy.data.meshes.new(name + " malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(BLACK)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    CREATED.append(obj)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


# Clear the file and make the cow as an assembled, volumetric miniature.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)

# Body, shoulders and neck.
body_center = (-0.08, 0.0, 1.05)
body_radii = (0.79, 0.39, 0.40)
uv_sphere("Corpo", body_center, body_radii, WHITE, 48, 32)
uv_sphere("Peito", (0.48, 0.0, 1.10), (0.42, 0.39, 0.47), WHITE, 40, 28)
uv_sphere("Pescoço", (0.65, 0.0, 1.38), (0.39, 0.34, 0.48), WHITE, 40, 28)

# Four legs with slight forward stance and distinct cloven-hoof blocks.
for name, x, y, h in [
    ("Perna dianteira esquerda", 0.45, -0.245, 0.64),
    ("Perna dianteira direita", 0.45, 0.245, 0.64),
    ("Perna traseira esquerda", -0.53, -0.245, 0.59),
    ("Perna traseira direita", -0.53, 0.245, 0.59),
]:
    capsule_leg(name, x, y, h)

# Head and broad pink muzzle, facing +X.
uv_sphere("Cabeça", (0.91, 0.0, 1.70), (0.34, 0.30, 0.37), WHITE, 40, 28)
uv_sphere("Focinho", (1.17, 0.0, 1.51), (0.245, 0.265, 0.18), MUZZLE, 36, 24)
for side in (-1, 1):
    uv_sphere("Narinas", (1.365, side * 0.115, 1.565), (0.028, 0.052, 0.034), NOSTRIL, 20, 12)
    # Eyes sit on the front-facing sides, with tiny catchlights.
    uv_sphere("Olho", (0.98, side * 0.276, 1.79), (0.057, 0.034, 0.061), EYE, 24, 16)
    uv_sphere("Brilho do olho", (1.002, side * 0.305, 1.81), (0.014, 0.009, 0.016), EYE_GLEAM, 16, 10)
    # Ears point outward and slightly forward.
    ear = uv_sphere("Orelha", (0.73, side * 0.38, 1.80), (0.21, 0.11, 0.095), BLACK, 28, 18)
    ear.rotation_euler[1] = -0.28
    inner = uv_sphere("Interior da orelha", (0.74, side * 0.423, 1.805), (0.13, 0.018, 0.047), MUZZLE, 24, 14)
    inner.rotation_euler[1] = -0.28
    # Short swept horns, pale at the tips.
    curve_tube("Chifre", [(0.83, side * 0.19, 1.94), (0.79, side * 0.24, 2.07), (0.72, side * 0.27, 2.12)], 0.045, HORN)

# Holstein coat markings conform to the body rather than floating as a picture plane.
for spec in [
    (1.25, 0.18, 0.34, 0.37, 11), (1.92, -0.20, 0.31, 0.31, 12),
    (-1.30, -0.13, 0.31, 0.35, 13), (-1.96, 0.21, 0.28, 0.30, 14),
    (2.75, -0.02, 0.30, 0.34, 15), (-2.72, 0.05, 0.28, 0.31, 16),
]:
    ellipsoid_patch("Mancha da pelagem", body_center, body_radii, *spec)
# Dark forehead patch and a smaller cheek marking.
uv_sphere("Marca da testa", (1.05, 0.0, 1.93), (0.14, 0.16, 0.12), BLACK, 28, 18)
uv_sphere("Marca da face", (0.91, -0.265, 1.67), (0.14, 0.035, 0.17), BLACK, 24, 16)

# Belly and udder detail.
uv_sphere("Úbere", (-0.32, 0.0, 0.69), (0.29, 0.23, 0.19), UDDER, 32, 20)
for x in (-0.45, -0.20):
    for y in (-0.115, 0.115):
        uv_sphere("Teta", (x, y, 0.555), (0.043, 0.043, 0.11), UDDER, 20, 12)

# Curved tail with a dark tuft.
curve_tube("Cauda", [(-0.77, 0.03, 1.30), (-0.99, 0.05, 1.18), (-1.10, 0.04, 0.94), (-1.08, 0.03, 0.76)], 0.032, WHITE)
uv_sphere("Tufo da cauda", (-1.08, 0.03, 0.72), (0.065, 0.06, 0.12), TAIL_TIP, 20, 14)

# Keep the source file organized and the runtime asset compact.
root = bpy.data.collections.new("Vaca - miniatura 3D")
bpy.context.scene.collection.children.link(root)
for obj in CREATED:
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    root.objects.link(obj)
    obj["asset_type"] = "monster_miniature"
    obj["front_axis"] = "+X"

# Studio preview setup (not included in the exported GLB).
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items else "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.16, 0.16, 0.16)
scene.view_settings.view_transform = "AgX"

bpy.ops.object.camera_add(location=(2.8, -4.8, 2.55))
camera = bpy.context.object
camera.name = "Preview Camera"
look_at(camera, (0.0, 0.0, 1.0))
camera.data.type = "ORTHO"
camera.data.ortho_scale = 3.55
scene.camera = camera

bpy.ops.object.light_add(type="AREA", location=(1.5, -3.0, 4.0))
key = bpy.context.object
key.data.energy = 470
key.data.shape = "DISK"
key.data.size = 4.0
look_at(key, (0.0, 0.0, 1.0))
bpy.ops.object.light_add(type="AREA", location=(-2.2, 1.8, 2.7))
fill = bpy.context.object
fill.data.energy = 260
fill.data.size = 3.0
look_at(fill, (0.0, 0.0, 1.0))

# A temporary matte ground gives the preview contact shadow only.
ground_mat = material("Preview ground", (0.13, 0.105, 0.08))
bpy.ops.mesh.primitive_plane_add(size=200, location=(0.0, 0.0, 0.015))
ground = bpy.context.object
ground.name = "Preview ground (not exported)"
ground.data.materials.append(ground_mat)

scene.render.filepath = PREVIEW_PATH
bpy.ops.render.render(write_still=True)

# Save a reusable Blender source including the preview rig, but export only cow geometry.
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.object.select_all(action="DESELECT")
for obj in CREATED:
    obj.select_set(True)
bpy.context.view_layer.objects.active = CREATED[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_materials="EXPORT")
print("VACA_ASSET", GLB_PATH, BLEND_PATH, PREVIEW_PATH)
