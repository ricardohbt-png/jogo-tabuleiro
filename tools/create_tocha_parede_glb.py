"""Build the detailed wall torch GLB and preserve the existing flame loop."""
from pathlib import Path
from math import cos, pi, sin

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
FLAME_GLB = OUT / "chama_viva.glb"
MODEL_GLB = OUT / "tocha_parede.glb"
SOURCE_BLEND = OUT / "tocha_parede.blend"
PREVIEW = OUT / "tocha_parede_preview.png"


def make_material(name, color, metallic=0.0, roughness=0.65, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        socket = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1.0)
        strength = shader.inputs.get("Emission Strength")
        if strength:
            strength.default_value = emission_strength
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def bevel_apply(obj, width, segments=3):
    if width > 0:
        mod = obj.modifiers.new("worn rounded edges", "BEVEL")
        mod.width = width
        mod.segments = segments
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    normal = obj.modifiers.new("weighted corner normals", "WEIGHTED_NORMAL")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=normal.name)
    return obj


def uv_sphere(name, location, scale, mat, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return assign(obj, mat)


def cylinder(name, location, radius, depth, mat, vertices=24, bevel=0.003):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    assign(obj, mat)
    return bevel_apply(obj, bevel, 2)


def between(name, start, end, radius, mat, vertices=16, radius2=None):
    a, b = Vector(start), Vector(end)
    delta = b - a
    if radius2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length, location=(a + b) * 0.5)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius2,
                                        depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    assign(obj, mat)
    return bevel_apply(obj, min(radius, radius2 if radius2 else radius) * 0.18, 2)


def torus(name, location, major, minor, mat, major_segments=32, minor_segments=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=major_segments, minor_segments=minor_segments,
                                     location=location, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return assign(obj, mat)


def curve_tube(name, points, radius, mat, resolution=16):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return assign(obj, mat)


def shield_plate(name, outline, front_y, thickness, mat, bevel=0.008):
    n = len(outline)
    back_y = front_y - thickness
    vertices = [(x, front_y, z) for x, z in outline] + [(x, back_y, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return bevel_apply(obj, bevel, 3)


def lathe(name, center_xy, profile, mat, segments=32):
    cx, cy = center_xy
    vertices = []
    for radius, z in profile:
        for i in range(segments):
            angle = 2 * pi * i / segments
            vertices.append((cx + cos(angle) * radius, cy + sin(angle) * radius, z))
    faces = []
    for ring in range(len(profile)):
        nxt = (ring + 1) % len(profile)
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, ring * segments + j,
                          nxt * segments + j, nxt * segments + i))
    mesh = bpy.data.meshes.new(name + " turned mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return assign(obj, mat) if not obj.data.materials else obj


def inset_outline(outline, factor):
    cx = sum(p[0] for p in outline) / len(outline)
    cz = sum(p[1] for p in outline) / len(outline)
    return [(cx + (x - cx) * factor, cz + (z - cz) * factor) for x, z in outline]


def build_torch(materials):
    iron, iron_edge, bronze, brass, dark, wood, wood_light, wood_dark = materials
    # Shield-shaped wall plate with a raised inset and beveled outline.
    plate = [
        (-0.185, 0.018), (-0.300, 0.108), (-0.274, 0.198), (-0.306, 0.292),
        (-0.296, 0.505), (-0.314, 0.608), (-0.220, 0.686), (-0.180, 0.738),
        (-0.138, 0.686), (-0.044, 0.608), (-0.064, 0.505), (-0.052, 0.292),
        (-0.086, 0.198), (-0.060, 0.108),
    ]
    shield_plate("Wall mounting plate - forged shield", plate, 0.040, 0.042, iron, 0.010)
    shield_plate("Raised shield face", inset_outline(plate, 0.88), 0.053, 0.015, iron_edge, 0.007)
    # Inner perimeter bead and a slim engraved center ridge.
    curve_tube("Shield perimeter bead", [(x, 0.064, z) for x, z in inset_outline(plate, 0.91)], 0.0045, bronze)
    curve_tube("Shield center spine", [(-0.18, 0.071, 0.16), (-0.18, 0.071, 0.34),
                                       (-0.18, 0.071, 0.52), (-0.18, 0.071, 0.64)], 0.004, brass)
    # Four layered mounting bolts with washers and hand-forged heads.
    bolts = [(-0.254, 0.128), (-0.106, 0.128), (-0.264, 0.588), (-0.096, 0.588)]
    for i, (x, z) in enumerate(bolts):
        torus("Plate bolt washer %02d" % i, (x, 0.065, z), 0.024, 0.004, bronze, 20, 6)
        uv_sphere("Plate hex bolt %02d" % i, (x, 0.073, z), (0.017, 0.010, 0.017), brass, 12, 8)
        cylinder("Bolt center pin %02d" % i, (x, 0.083, z), 0.004, 0.002, dark, 8, 0.0005)
    # Gothic center boss, raised diamond, and small stamped rivets.
    diamond = [(-0.18, 0.276), (-0.137, 0.326), (-0.18, 0.378), (-0.223, 0.326)]
    shield_plate("Center diamond boss", diamond, 0.079, 0.012, bronze, 0.004)
    uv_sphere("Boss center", (-0.18, 0.094, 0.326), (0.012, 0.008, 0.014), brass, 16, 10)
    for i, z in enumerate((0.235, 0.425, 0.48, 0.535)):
        uv_sphere("Small shield rivet %02d" % i, (-0.18, 0.073, z), (0.006, 0.004, 0.006), bronze, 12, 8)

    # Curved load-bearing arm: doubled iron scrolls connect plate and torch stem.
    curve_tube("Forged bracket main arm", [(-0.070, 0.018, 0.405), (-0.012, 0.070, 0.421),
                                            (0.028, 0.137, 0.405), (0.066, 0.178, 0.386)], 0.020, iron_edge)
    curve_tube("Bracket lower scroll", [(-0.050, 0.034, 0.315), (-0.004, 0.104, 0.306),
                                         (0.060, 0.160, 0.338), (0.075, 0.180, 0.365)], 0.012, bronze)
    curve_tube("Bracket upper brace", [(-0.046, 0.040, 0.520), (0.006, 0.112, 0.508),
                                        (0.052, 0.166, 0.474), (0.075, 0.181, 0.414)], 0.010, iron)
    for i, z in enumerate((0.32, 0.50)):
        uv_sphere("Bracket rivet %02d" % i, (-0.045, 0.061, z), (0.013, 0.009, 0.013), brass, 14, 8)

    # Turned hardwood shaft, capped with wrought collars and grain inlays.
    cx, cy = 0.092, 0.174
    lathe("Carved oak torch haft", (cx, cy), [
        (0.034, 0.118), (0.045, 0.140), (0.050, 0.170), (0.046, 0.195),
        (0.045, 0.490), (0.052, 0.518), (0.044, 0.548), (0.036, 0.566),
        (0.028, 0.558), (0.033, 0.520), (0.034, 0.180), (0.026, 0.145),
    ], wood, 24)
    for i in range(12):
        angle = 2 * pi * i / 12
        radius = 0.046
        x = cx + cos(angle) * radius
        y = cy + sin(angle) * radius
        grain = wood_light if i % 3 == 0 else wood_dark
        phase = (i % 4) * 0.012
        curve_tube("Oak grain inlay %02d" % i, [
            (x, y, 0.185 + phase),
            (cx + cos(angle + 0.025) * (radius + 0.001), cy + sin(angle + 0.025) * (radius + 0.001), 0.295),
            (cx + cos(angle - 0.018) * radius, cy + sin(angle - 0.018) * radius, 0.420),
            (x, y, 0.515 - phase),
        ], 0.0017, grain, 10)
    for i, z in enumerate((0.145, 0.177, 0.486, 0.526, 0.548)):
        depth = 0.025 if z in (0.177, 0.526) else 0.014
        cylinder("Haft iron collar %02d" % i, (cx, cy, z), 0.060 if depth > 0.02 else 0.054,
                 depth, iron_edge if i % 2 else iron, 24, 0.003)
        torus("Collar brass lip %02d" % i, (cx, cy, z - depth * 0.35), 0.057 if depth > 0.02 else 0.051,
              0.003, bronze, 28, 6)
        for j in range(4):
            a = 2 * pi * j / 4 + pi / 4
            uv_sphere("Collar stud %02d-%02d" % (i, j),
                      (cx + cos(a) * 0.060, cy + sin(a) * 0.060, z),
                      (0.006, 0.006, 0.006), brass, 10, 6)

    # Pointed lower ferrule; gives the hanging candelabrum a finished silhouette.
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.010, radius2=0.057, depth=0.095,
                                    location=(cx, cy, 0.060))
    lower_tip = bpy.context.object
    lower_tip.name = "Tapered iron lower finial"
    assign(lower_tip, iron_edge)
    bevel_apply(lower_tip, 0.003, 2)
    torus("Lower finial bronze ring", (cx, cy, 0.105), 0.052, 0.004, bronze, 24, 6)

    # Deep forged brazier cup, rolled lip, inner fire bowl, and radial ribs.
    bowl_center = (cx, cy)
    lathe("Open wrought iron brazier", bowl_center, [
        (0.046, 0.558), (0.068, 0.567), (0.082, 0.589), (0.104, 0.626),
        (0.130, 0.674), (0.145, 0.705), (0.134, 0.714), (0.119, 0.687),
        (0.096, 0.648), (0.073, 0.610), (0.049, 0.594),
    ], iron, 32)
    torus("Brazier rolled rim", (cx, cy, 0.707), 0.139, 0.010, bronze, 40, 8)
    torus("Brazier lower hoop", (cx, cy, 0.583), 0.071, 0.009, iron_edge, 32, 8)
    cylinder("Brazier underside socket", (cx, cy, 0.558), 0.070, 0.036, iron_edge, 24, 0.004)
    torus("Bowl socket brass seam", (cx, cy, 0.541), 0.061, 0.004, bronze, 28, 6)
    # Eight raised ribs follow the bowl and curl out into pointed flame guards.
    for i in range(8):
        angle = 2 * pi * i / 8
        c, s = cos(angle), sin(angle)
        curve_tube("Brazier cage rib %02d" % i, [
            (cx + c * 0.073, cy + s * 0.073, 0.590),
            (cx + c * 0.104, cy + s * 0.104, 0.636),
            (cx + c * 0.134, cy + s * 0.134, 0.691),
            (cx + c * 0.143, cy + s * 0.143, 0.770),
            (cx + c * 0.159, cy + s * 0.159, 0.806),
        ], 0.009, iron_edge, 12)
        uv_sphere("Cage tip rivet %02d" % i,
                  (cx + c * 0.159, cy + s * 0.159, 0.806), (0.010, 0.010, 0.010), bronze, 12, 8)
    # Six small pierced vents around the upper bowl wall.
    for i in range(6):
        angle = 2 * pi * i / 6
        uv_sphere("Brazier vent shadow %02d" % i,
                  (cx + cos(angle) * 0.132, cy + sin(angle) * 0.132, 0.674),
                  (0.006, 0.006, 0.012), dark, 10, 6)


def import_animated_flame():
    bpy.ops.import_scene.gltf(filepath=str(FLAME_GLB))
    flame_parts = [o for o in list(bpy.context.scene.objects)
                   if o.type == "MESH" and o.name in {"Chama externa", "Chama interna", "Nucleo luminoso"}]
    ember_disc = next((o for o in list(bpy.context.scene.objects)
                       if o.type == "MESH" and o.name == "Brasa"), None)
    if len(flame_parts) != 3 or ember_disc is None:
        raise RuntimeError("O GLB chama_viva.glb não trouxe as partes animadas esperadas.")
    # O disco da chama original era só um marcador plano. A tigela recebe
    # brasas próprias em 3D; preservamos aqui somente as três labaredas animadas.
    bpy.data.objects.remove(ember_disc, do_unlink=True)
    root = bpy.data.objects.new("Animated flame pivot", None)
    bpy.context.collection.objects.link(root)
    root.location = (0.092, 0.174, 0.585)
    root.scale = (0.32, 0.32, 0.32)
    for obj in flame_parts:
        loc, rot, scale = obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy()
        obj["preserve_animation"] = True
        obj.parent = root
        obj.matrix_parent_inverse.identity()
        obj.location, obj.rotation_euler, obj.scale = loc, rot, scale
    return root


def combine_static_geometry():
    # Mantém o .blend com peças editáveis, mas o GLB usa um mesh por material
    # para não transformar cada rebite e filete em um draw call separado.
    curves = [o for o in bpy.context.scene.objects if o.type == "CURVE"]
    if curves:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in curves:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target="MESH")
    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.get("preserve_animation"):
            continue
        key = obj.data.materials[0].name if obj.data.materials else "__unmaterialed__"
        groups.setdefault(key, []).append(obj)
    for key, objects in groups.items():
        if len(objects) < 2:
            objects[0].name = "Torch static - " + key
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        objects[0].name = "Torch static - " + key


def make_preview_scene():
    bpy.ops.object.camera_add(location=(1.55, 2.15, 1.20))
    camera = bpy.context.object
    camera.name = "Three quarter preview camera"
    target = Vector((0.0, 0.07, 0.47))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.32
    bpy.context.scene.camera = camera
    for name, location, energy, size, color in [
        ("Warm key", (0.2, 1.8, 1.9), 165, 1.4, (1.0, 0.82, 0.62)),
        ("Cool metal fill", (-1.4, 0.8, 1.0), 95, 1.3, (0.68, 0.76, 1.0)),
        ("Rim light", (0.9, -1.0, 1.6), 125, 1.0, (1.0, 0.43, 0.20)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = str(PREVIEW)
    scene.world.use_nodes = True
    world_bg = scene.world.node_tree.nodes.get("Background")
    world_bg.inputs["Color"].default_value = (0.035, 0.042, 0.052, 1.0)
    world_bg.inputs["Strength"].default_value = 0.48
    scene.frame_start = 0
    scene.frame_end = 31
    scene.render.fps = 24
    scene.frame_set(7)


def build():
    if not FLAME_GLB.is_file():
        raise FileNotFoundError("GLB da chama animada ausente: " + str(FLAME_GLB))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in list(datablocks):
            if data.users == 0:
                datablocks.remove(data)

    iron = make_material("blackened iron", (0.055, 0.047, 0.039), 0.70, 0.48)
    iron_edge = make_material("worn iron edges", (0.125, 0.100, 0.071), 0.66, 0.44)
    bronze = make_material("aged bronze trim", (0.27, 0.125, 0.043), 0.62, 0.43)
    brass = make_material("hammered brass fasteners", (0.44, 0.265, 0.085), 0.68, 0.39)
    dark = make_material("deep brazier shadows", (0.018, 0.012, 0.008), 0.12, 0.86)
    wood = make_material("smoked oak", (0.125, 0.045, 0.016), 0.0, 0.66)
    wood_light = make_material("oak grain highlights", (0.27, 0.115, 0.031), 0.0, 0.67)
    wood_dark = make_material("oak grain grooves", (0.050, 0.018, 0.006), 0.0, 0.76)
    build_torch((iron, iron_edge, bronze, brass, dark, wood, wood_light, wood_dark))
    ember = make_material("dull red embers", (0.28, 0.035, 0.006), 0.0, 0.84,
                          emission=(0.45, 0.018, 0.001), emission_strength=0.45)
    coal = make_material("charcoal black", (0.025, 0.019, 0.014), 0.05, 0.88)
    cx, cy = 0.092, 0.174
    cylinder("Coal bed", (cx, cy, 0.603), 0.080, 0.010, coal, 20, 0.002)
    for i in range(9):
        angle = i * 2.399963229728653
        radius = 0.018 + (i % 3) * 0.014
        size = 0.012 + (i % 3) * 0.002
        uv_sphere("Charcoal lump %02d" % i,
                  (cx + cos(angle) * radius, cy + sin(angle) * radius, 0.611 + (i % 2) * 0.006),
                  (size * 1.25, size, size * 0.65), ember if i % 3 == 0 else coal, 12, 8)
    flame_root = import_animated_flame()
    make_preview_scene()

    scene = bpy.context.scene
    scene.render.filepath = str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_BLEND))
    bpy.ops.render.render(write_still=True)
    combine_static_geometry()

    # Export the actual fixture plus the imported, keyed flame nodes. The
    # animations are glTF clips and are replayed by Three.js AnimationMixer.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in scene.objects:
        if obj.type == "MESH" or obj == flame_root:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = flame_root
    bpy.ops.export_scene.gltf(
        filepath=str(MODEL_GLB), export_format="GLB", use_selection=True,
        export_apply=True, export_animations=True, export_frame_range=True,
    )
    print("Created", MODEL_GLB)


if __name__ == "__main__":
    build()
