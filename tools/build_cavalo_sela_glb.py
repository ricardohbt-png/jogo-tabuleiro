"""Build the Cavalo de Sela miniature from its transparent PNG reference."""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets/pawns/monstros/cavalo_sela/cavalo_sela.png"
OUT = ROOT / "assets/models3d/monstros"
BLEND = OUT / "cavalo_sela.blend"
GLB = OUT / "cavalo_sela.glb"
PREVIEW = OUT / "cavalo_sela_preview.png"

MATERIALS = {
    "Pelagem Castanha": ((0.245, 0.060, 0.020, 1), 0.70, 0.0),
    "Pelagem Luz": ((0.34, 0.093, 0.027, 1), 0.75, 0.0),
    "Pelagem Sombra": ((0.18, 0.044, 0.018, 1), 0.77, 0.0),
    "Crina e Cauda": ((0.035, 0.021, 0.016, 1), 0.84, 0.0),
    "Crina Luz": ((0.075, 0.043, 0.029, 1), 0.82, 0.0),
    "Marca Branca": ((0.82, 0.77, 0.67, 1), 0.82, 0.0),
    "Focinho": ((0.14, 0.115, 0.10, 1), 0.88, 0.0),
    "Olho": ((0.018, 0.012, 0.009, 1), 0.24, 0.0),
    "Íris": ((0.26, 0.105, 0.026, 1), 0.3, 0.0),
    "Brilho do Olho": ((0.95, 0.83, 0.58, 1), 0.18, 0.0),
    "Couro da Sela": ((0.075, 0.022, 0.009, 1), 0.58, 0.0),
    "Couro Claro": ((0.17, 0.061, 0.018, 1), 0.66, 0.0),
    "Manta": ((0.30, 0.19, 0.085, 1), 0.94, 0.0),
    "Manta Borda": ((0.17, 0.07, 0.026, 1), 0.85, 0.0),
    "Metal Latão": ((0.64, 0.37, 0.085, 1), 0.32, 0.58),
    "Casco": ((0.075, 0.045, 0.027, 1), 0.46, 0.0),
    "Casco Banda": ((0.35, 0.23, 0.12, 1), 0.55, 0.08),
}


def material(name: str):
    color, roughness, metallic = MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


MATS = {}


def finish(obj, name, mat_name, bevel=0.0, smooth=True):
    obj.name = name
    obj.data.materials.append(MATS[mat_name])
    if obj.type == "MESH" and smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    if bevel:
        mod = obj.modifiers.new("Arestas macias", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.profile = 0.5
        mod2 = obj.modifiers.new("Normais de canto", "WEIGHTED_NORMAL")
        mod2.keep_sharp = True
    return obj


def ellipsoid(name, loc, scale, mat, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    return finish(obj, name, mat)


def rounded_box(name, loc, scale, mat, bevel):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel=bevel, smooth=False)


def tube_mesh(name, points, radii, mat, sides=16, closed_ends=True):
    """Smooth tapered tube through center points; radii are (width, depth)."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    reference = Vector((1, 0, 0))
    for i, center in enumerate(pts):
        tangent = (pts[min(i + 1, len(pts) - 1)] - pts[max(0, i - 1)]).normalized()
        u = reference - tangent * reference.dot(tangent)
        if u.length < 1e-5:
            reference = Vector((0, 1, 0))
            u = reference - tangent * reference.dot(tangent)
        u.normalize()
        v = tangent.cross(u).normalized()
        rx, ry = radii[i]
        for j in range(sides):
            angle = (2 * math.pi * j) / sides
            pos = center + u * (math.cos(angle) * rx) + v * (math.sin(angle) * ry)
            verts.append(tuple(pos))
    for i in range(len(pts) - 1):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    if closed_ends:
        faces.extend([tuple(reversed(range(sides))), tuple((len(pts) - 1) * sides + j for j in range(sides))])
    mesh = bpy.data.meshes.new(name + " Malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(MATS[mat])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def curve(name, points, mat, radius, resolution=8):
    data = bpy.data.curves.new(name + " Curva", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 12
    data.bevel_depth = radius
    data.bevel_resolution = resolution
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(MATS[mat])
    return obj


def cone_between(name, start, end, radius_bottom, radius_top, mat, vertices=24):
    a, b = Vector(start), Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius_bottom, radius2=radius_top,
                                    depth=direction.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return finish(obj, name, mat, smooth=True)


def build_body():
    # Main barrel, deep chest and rounded hindquarters give the miniature a
    # horse silhouette instead of the one-piece oval body of a generic pawn.
    ellipsoid("Tronco", (0, 0.08, 1.16), (0.43, 0.67, 0.37), "Pelagem Castanha", 48, 32)
    ellipsoid("Peito musculoso", (0, -0.34, 1.16), (0.37, 0.38, 0.39), "Pelagem Luz", 40, 28)
    ellipsoid("Garupa musculosa", (0, 0.43, 1.20), (0.43, 0.36, 0.37), "Pelagem Castanha", 40, 28)
    ellipsoid("Ombro direito", (0.30, -0.31, 1.02), (0.14, 0.25, 0.26), "Pelagem Luz")
    ellipsoid("Ombro esquerdo", (-0.30, -0.31, 1.02), (0.14, 0.25, 0.26), "Pelagem Castanha")
    ellipsoid("Coxa direita", (0.29, 0.43, 0.98), (0.15, 0.25, 0.27), "Pelagem Luz")
    ellipsoid("Coxa esquerda", (-0.29, 0.43, 0.98), (0.15, 0.25, 0.27), "Pelagem Castanha")

    tube_mesh("Pescoço alto e arqueado",
        [(0, -0.36, 1.31), (0, -0.49, 1.48), (0, -0.63, 1.68), (0, -0.77, 1.84), (0, -0.83, 1.91)],
        [(0.35, 0.32), (0.31, 0.30), (0.26, 0.26), (0.22, 0.23), (0.20, 0.21)],
        "Pelagem Luz", 28)
    tube_mesh("Cabeça estreita de cavalo",
        [(0, -0.80, 1.91), (0, -0.88, 1.80), (0, -0.97, 1.65), (0, -1.04, 1.51), (0, -1.09, 1.45)],
        [(0.20, 0.20), (0.205, 0.215), (0.18, 0.19), (0.15, 0.16), (0.14, 0.15)],
        "Pelagem Castanha", 28)
    ellipsoid("Bochecha direita", (0.12, -0.91, 1.63), (0.09, 0.13, 0.14), "Pelagem Luz")
    ellipsoid("Bochecha esquerda", (-0.12, -0.91, 1.63), (0.09, 0.13, 0.14), "Pelagem Castanha")
    ellipsoid("Focinho aveludado", (0, -1.15, 1.47), (0.15, 0.20, 0.12), "Focinho", 32, 20)
    ellipsoid("Queixo", (0, -1.04, 1.39), (0.13, 0.14, 0.075), "Pelagem Sombra")

    # Pale facial blaze: a narrow raised patch following the forehead to muzzle.
    blaze_points = [
        (0, -1.065, 1.86), (0, -1.125, 1.75), (0, -1.178, 1.63),
        (0, -1.220, 1.53), (0, -1.265, 1.485),
    ]
    widths = [0.060, 0.070, 0.057, 0.047, 0.055]
    verts, faces = [], []
    for (x, y, z), w in zip(blaze_points, widths):
        verts.extend([(x - w, y - 0.006, z), (x + w, y - 0.006, z)])
    for i in range(len(blaze_points) - 1):
        faces.append((2*i, 2*i+1, 2*i+3, 2*i+2))
    mesh = bpy.data.meshes.new("Lista branca da face Malha")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(MATS["Marca Branca"])
    obj = bpy.data.objects.new("Lista branca da face", mesh)
    bpy.context.collection.objects.link(obj)
    solid = obj.modifiers.new("Espessura mínima", "SOLIDIFY")
    solid.thickness = 0.012
    bevel = obj.modifiers.new("Bordas da marca", "BEVEL")
    bevel.width, bevel.segments = 0.012, 2


def build_ears_eyes_and_mane():
    for side, label in ((-1, "E"), (1, "D")):
        x = side * 0.145
        cone_between(f"Orelha {label}", (x, -0.77, 1.99), (side * 0.21, -0.72, 2.28),
                     0.105, 0.025, "Pelagem Castanha", 24)
        cone_between(f"Interior da orelha {label}", (x, -0.805, 2.035), (side * 0.20, -0.767, 2.23),
                     0.050, 0.012, "Pelagem Sombra", 20)
        # Eyes are placed on the cheek planes so the expression reads in the
        # game camera from either side, with a tiny warm catchlight.
        ellipsoid(f"Orbita {label}", (side * 0.166, -0.948, 1.79), (0.048, 0.046, 0.058), "Pelagem Sombra", 24, 16)
        ellipsoid(f"Olho {label}", (side * 0.196, -0.966, 1.795), (0.027, 0.032, 0.036), "Íris", 24, 16)
        ellipsoid(f"Pupila {label}", (side * 0.214, -0.987, 1.796), (0.012, 0.017, 0.024), "Olho", 20, 12)
        ellipsoid(f"Brilho {label}", (side * 0.223, -0.999, 1.810), (0.007, 0.008, 0.009), "Brilho do Olho", 16, 10)
        ellipsoid(f"Narina {label}", (side * 0.133, -1.267, 1.50), (0.022, 0.018, 0.032), "Olho", 20, 12)

    # Flowing forelock and mane: a broad crest with individual swept locks.
    tube_mesh("Crista escura da crina",
        [(0, -0.80, 2.12), (0, -0.70, 2.02), (0, -0.59, 1.88), (0, -0.48, 1.72), (0, -0.37, 1.53)],
        [(0.12, 0.11), (0.14, 0.13), (0.13, 0.12), (0.11, 0.10), (0.075, 0.08)],
        "Crina e Cauda", 20)
    for side in (-1, 1):
        for i in range(5):
            x = side * (0.06 + 0.025 * (i % 2))
            curve(f"Mecha de crina {side}_{i}", [
                (x, -0.78 + i*0.018, 2.12 - i*0.012),
                (x + side*0.045, -0.64 + i*0.025, 1.96 - i*0.022),
                (x + side*0.07, -0.53 + i*0.027, 1.76 - i*0.035),
                (x + side*0.09, -0.39 + i*0.026, 1.58 - i*0.04),
            ], "Crina Luz" if i in (1, 4) else "Crina e Cauda", 0.025 - i*0.0015, 5)
    for i in range(7):
        x = (i - 3) * 0.035
        curve(f"Franja {i}", [
            (x * 0.65, -0.79, 2.17),
            (x, -0.88, 2.13),
            (x * 1.2, -0.99, 2.03),
            (x * 1.4, -1.00, 1.96),
        ], "Crina Luz" if i == 3 else "Crina e Cauda", 0.028, 5)

    # Tail root emerges above the rump, then sweeps backward and down in a
    # tapered mass, with raised strands to keep the silhouette readable.
    tube_mesh("Cauda longa",
        [(0.25, 0.63, 1.32), (0.31, 0.75, 1.22), (0.34, 0.83, 1.02), (0.36, 0.93, 0.78), (0.37, 0.99, 0.55)],
        [(0.12, 0.12), (0.12, 0.11), (0.105, 0.10), (0.075, 0.08), (0.025, 0.04)],
        "Crina e Cauda", 20)
    for i in range(7):
        x = 0.34 + (i - 3) * 0.022
        curve(f"Fio da cauda {i}", [
            (x*0.75, 0.70, 1.30), (x*0.92, 0.82, 1.10),
            (x, 0.90, 0.84), (x*0.75, 0.97, 0.59 - abs(i-3)*0.015),
        ], "Crina Luz" if i in (1, 5) else "Crina e Cauda", 0.018, 4)


def build_legs():
    legs = [
        # label, x, points top-to-bottom, radii
        ("Dianteira D", 0.235, [(-0.29, 1.09), (-0.27, 0.72), (-0.31, 0.38), (-0.34, 0.19)],
         [(0.135,0.14),(0.095,0.10),(0.061,0.06),(0.050,0.05)]),
        ("Dianteira E", -0.235, [(-0.34, 1.07), (-0.37, 0.70), (-0.35, 0.38), (-0.36, 0.19)],
         [(0.135,0.14),(0.098,0.10),(0.062,0.06),(0.050,0.05)]),
        ("Traseira D", 0.24, [(0.42, 1.10), (0.52, 0.79), (0.39, 0.49), (0.47, 0.19)],
         [(0.17,0.17),(0.13,0.13),(0.078,0.08),(0.052,0.05)]),
        ("Traseira E", -0.24, [(0.46, 1.09), (0.55, 0.78), (0.42, 0.49), (0.50, 0.19)],
         [(0.17,0.17),(0.13,0.13),(0.078,0.08),(0.052,0.05)]),
    ]
    for label, x, yz, radii in legs:
        pts = [(x, y, z) for y, z in yz]
        tube_mesh(f"{label} perna superior", pts[:3], radii[:3], "Pelagem Luz" if "D" in label else "Pelagem Castanha", 20)
        # Dark stockings taper above each hoof, matching the reference PNG.
        y, _ = yz[2]
        tube_mesh(f"{label} meia escura",
            [(x, yz[2][0], yz[2][1]), (x, yz[3][0], yz[3][1]), (x, yz[3][0], 0.13)],
            [(0.063,0.062),(0.054,0.052),(0.050,0.049)], "Pelagem Sombra", 18)
        hoof_y = yz[3][0] - 0.005
        ellipsoid(f"{label} coroa do casco", (x, hoof_y, 0.16), (0.076, 0.105, 0.085), "Pelagem Sombra", 24, 16)
        ellipsoid(f"{label} casco", (x, hoof_y - 0.015, 0.085), (0.075, 0.105, 0.075), "Casco", 24, 16)
        # Thin warm rim reads as the coronet band seen in the image.
        ellipsoid(f"{label} banda do casco", (x, hoof_y - 0.015, 0.14), (0.078, 0.107, 0.022), "Casco Banda", 24, 12)


def build_tack():
    # Saddle blanket and layered saddle sit just above the back, not as a
    # separate pedestal, and remain readable in the map's small camera.
    rounded_box("Manta de sela", (0, 0.05, 1.48), (0.64, 0.61, 0.10), "Manta", 0.075)
    rounded_box("Borda escura da manta", (0, 0.05, 1.425), (0.65, 0.60, 0.03), "Manta Borda", 0.035)
    ellipsoid("Assento almofadado da sela", (0, 0.07, 1.55), (0.29, 0.32, 0.075), "Couro da Sela", 36, 20)
    ellipsoid("Arção frontal", (0, -0.15, 1.59), (0.26, 0.07, 0.075), "Couro Claro", 28, 16)
    ellipsoid("Arção traseiro", (0, 0.29, 1.60), (0.26, 0.075, 0.085), "Couro Claro", 28, 16)
    for side, label in ((-1, "E"), (1, "D")):
        rounded_box(f"Abas da sela {label}", (side*0.365, 0.08, 1.36), (0.10, 0.48, 0.34), "Couro da Sela", 0.045)
        curve(f"Costura da aba {label}", [
            (side*0.421, -0.10, 1.47), (side*0.421, -0.12, 1.30),
            (side*0.421, 0.17, 1.25), (side*0.421, 0.27, 1.42),
        ], "Couro Claro", 0.009, 4)
        # Stirrups and straps hang on each side of the saddle.
        curve(f"Estribo de couro {label}", [
            (side*0.40, 0.03, 1.43), (side*0.43, 0.04, 1.20),
            (side*0.47, 0.04, 0.88), (side*0.48, 0.04, 0.78),
        ], "Couro Claro", 0.026, 5)
        curve(f"Estribo metal {label}", [
            (side*0.47, -0.02, 0.82), (side*0.56, -0.02, 0.82),
            (side*0.57, -0.02, 0.65), (side*0.46, -0.02, 0.65),
            (side*0.46, -0.02, 0.82),
        ], "Metal Latão", 0.018, 5)
        rounded_box(f"Piso do estribo {label}", (side*0.515, -0.02, 0.65), (0.14,0.11,0.035), "Couro da Sela", 0.012)
        ellipsoid(f"Fivela do estribo {label}", (side*0.43, 0.035, 1.16), (0.04,0.035,0.045), "Metal Latão", 20, 12)

    # Breast collar keeps the saddle secure and adds a crisp line across chest.
    curve("Peitoral de couro", [
        (-0.34, -0.44, 1.31), (-0.27, -0.58, 1.12), (0, -0.61, 1.05),
        (0.27, -0.58, 1.12), (0.34, -0.44, 1.31),
    ], "Couro Claro", 0.035, 6)
    ellipsoid("Medalhão peitoral", (0, -0.635, 1.055), (0.07,0.03,0.065), "Metal Latão", 24, 16)

    # Bridle: browband, cheek straps, noseband, bit rings and reins on both sides.
    curve("Testeira da cabeçada", [(-0.20,-0.87,1.92),(-0.12,-0.91,1.96),(0,-0.93,1.97),(0.12,-0.91,1.96),(0.20,-0.87,1.92)], "Couro Claro", 0.028, 5)
    curve("Cachaceira", [(-0.17,-0.80,1.99),(0,-0.77,2.04),(0.17,-0.80,1.99)], "Couro da Sela", 0.026, 5)
    for side, label in ((-1,"E"),(1,"D")):
        curve(f"Faceira {label}", [(side*0.18,-0.86,1.91),(side*0.19,-0.91,1.72),(side*0.16,-1.00,1.53)], "Couro da Sela", 0.025, 5)
        curve(f"Cachaceira lateral {label}", [(side*0.17,-0.81,1.98),(side*0.23,-0.71,1.89),(side*0.28,-0.55,1.78)], "Couro Claro", 0.022, 5)
        ellipsoid(f"Argola da embocadura {label}", (side*0.17,-1.12,1.48), (0.035,0.025,0.035), "Metal Latão", 20, 12)
        curve(f"Rédea {label}", [(side*0.16,-1.12,1.48),(side*0.24,-0.97,1.33),(side*0.28,-0.68,1.35),(side*0.36,-0.31,1.48),(side*0.39,0.05,1.50)], "Couro Claro", 0.018, 5)
    curve("Focinheira", [(-0.15,-1.20,1.51),(-0.10,-1.27,1.49),(0,-1.29,1.48),(0.10,-1.27,1.49),(0.15,-1.20,1.51)], "Couro Claro", 0.034, 5)
    curve("Freio", [(-0.13,-1.17,1.45),(0,-1.20,1.43),(0.13,-1.17,1.45)], "Metal Latão", 0.017, 5)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def configure_preview(model_objects):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("Mundo de prévia Cavalo de Sela")
    scene.world.color = (0.055, 0.045, 0.035)
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.image_settings.color_mode = "RGBA"

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,0))
    floor = bpy.context.object
    floor.name = "PREVIEW only - floor"
    floor.data.materials.append(MATS["Pelagem Sombra"])
    floor.hide_set(True)
    floor.hide_render = False

    bpy.ops.object.camera_add(location=(3.3, -4.7, 2.65))
    camera = bpy.context.object
    camera.name = "PREVIEW only - camera"
    camera.location = (4.2, -3.2, 2.65)
    look_at(camera, (0.08, 0.02, 1.14))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.55
    scene.camera = camera

    for name, location, power, size, color in [
        ("Key", (3.0,-4.2,5.2), 500, 3.4, (1.0,0.79,0.56)),
        ("Fill", (-3.5,-2.0,3.0), 320, 3.0, (0.56,0.69,1.0)),
        ("Rim", (0.5,3.0,4.2), 650, 2.6, (1.0,0.48,0.20)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = f"PREVIEW only - {name}"
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        look_at(light, (0,0,1.0))

    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)

    # Keep preview camera, lights and floor in the editable .blend, but exclude
    # them from the runtime GLB by exporting only the horse's mesh/curve objects.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in model_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = model_objects[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB), export_format="GLB", use_selection=True,
        export_apply=True, export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_cameras=False, export_lights=False,
    )


def main():
    if not REFERENCE.is_file():
        raise FileNotFoundError(f"PNG de referência ausente: {REFERENCE}")
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name in MATERIALS:
        MATS[name] = material(name)

    scene = bpy.context.scene
    scene["asset_id"] = "cavalo_sela"
    scene["reference_image"] = str(REFERENCE.relative_to(ROOT)).replace("\\", "/")
    scene["model_notes"] = "Cavalo castanho de sela; cabeça, crina, cauda, quatro patas, cascos, manta, sela e cabeçada modelados em malha/curvas."

    build_body()
    build_ears_eyes_and_mane()
    build_legs()
    build_tack()
    model_objects = [o for o in scene.objects if o.type in {"MESH", "CURVE"}]
    configure_preview(model_objects)
    print(f"CAVALO_EXPORT_OK blend={BLEND} glb={GLB} preview={PREVIEW} model_objects={len(model_objects)}")


if __name__ == "__main__":
    main()
