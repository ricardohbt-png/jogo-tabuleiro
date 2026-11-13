"""Cria a miniatura GLB do barco medieval ilustrado em barco_medieval.png."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(20261102)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)


def material(name, color, roughness=0.78, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def mesh_object(name, verts, faces, mat, smooth=False):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return obj


def box(name, location, dimensions, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
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


def sphere(name, location, radius, mat, vertices=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=vertices, ring_count=6,
                                        radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tube(name, points, mat, radius=0.012, resolution=2):
    curve = bpy.data.curves.new(name + " Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def profile(t: float, v: float):
    """Cross-section at longitudinal fraction t and hull height v (0..1)."""
    end = abs(t)
    taper = max(0.0, 1.0 - end ** 1.65) ** 0.72
    half_width = 0.47 * taper * (0.16 + 0.84 * v)
    bottom = 0.11 + 0.20 * end * end
    rim = 0.76 - 0.22 * end * end
    z = bottom + v * (rim - bottom)
    return half_width, z


def make_strake(name, sign, v0, v1, mat, longitudinal=True, inset=0.0):
    verts, faces = [], []
    steps = 32
    ts = [-0.995 + 1.99 * i / steps for i in range(steps + 1)]
    if longitudinal:
        for t in ts:
            for v in (v0, v1):
                width, z = profile(t, v)
                verts.append((1.16 * t, sign * max(0.0, width - inset), z))
        for i in range(steps):
            a = i * 2
            faces.append((a, a + 2, a + 3, a + 1))
    else:
        pass
    obj = mesh_object(name, verts, faces, mat)
    solid = obj.modifiers.new("Espessura da tábua", "SOLIDIFY")
    solid.thickness = 0.024
    solid.offset = -1.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=solid.name)
    bevel = obj.modifiers.new("Bordas arredondadas", "BEVEL")
    bevel.width = 0.009
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    normal = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=normal.name)
    return obj


def make_keel(wood):
    verts, faces = [], []
    steps = 28
    for i in range(steps + 1):
        t = -0.995 + 1.99 * i / steps
        width, z = profile(t, 0.15)
        half = max(0.018, width * 0.52)
        z0 = max(0.055, z - 0.055)
        verts.extend(((1.13*t, -half, z0), (1.13*t, half, z0),
                      (1.13*t, -half, z0 + 0.055), (1.13*t, half, z0 + 0.055)))
    for i in range(steps):
        a = 4*i
        b = a+4
        faces.extend(((a, b, b+2, a+2), (a+1, a+3, b+3, b+1),
                      (a+2, b+2, b+3, a+3), (a, a+1, b+1, b)))
    return mesh_object("Quilha inferior", verts, faces, wood)


def make_floor_boards(mats):
    result = []
    for i in range(9):
        y = -0.25 + i * 0.0625
        verts, faces = [], []
        steps = 24
        for j in range(steps + 1):
            t = -0.89 + 1.78 * j / steps
            width, z = profile(t, 0.40)
            edge = min(width * 0.76, 0.275)
            if abs(y) > edge:
                verts.extend(((1.0*t, y, z+0.018), (1.0*t, y, z+0.045)))
            else:
                verts.extend(((1.0*t, y, z+0.018), (1.0*t, y, z+0.045)))
        for j in range(steps):
            a = j*2
            faces.append((a, a+2, a+3, a+1))
        result.append(mesh_object(f"Assoalho {i+1:02d}", verts, faces, mats[i % len(mats)]))
    return result


def make_rib(x, half_width, wood):
    # Cada costela forma um U aberto, acompanhando o interior do casco.
    points = []
    for i in range(17):
        angle = math.pi * i / 16
        y = -half_width * math.cos(angle)
        z = 0.36 + 0.27 * abs(math.cos(angle))
        points.append((x, y, z))
    return tube("Costela interna", points, wood, 0.018, 1)


def make_camera(name, location, target, lens=52):
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = name
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.55
    camera.data.lens = lens
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    return camera


def setup_lights(target):
    scene = bpy.context.scene
    for name, location, power, size, color in (
        ("Luz principal", (2.5, -3.1, 4.0), 420, 3.0, (1.0, 0.84, 0.67)),
        ("Preenchimento", (-3.0, -1.0, 2.7), 250, 3.5, (0.78, 0.86, 1.0)),
        ("Luz traseira", (0.5, 3.0, 3.2), 300, 2.5, (1.0, 0.68, 0.44)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()


def main():
    clear_scene()
    wood = [
        material("Carvalho envelhecido", (0.145, 0.059, 0.023)),
        material("Carvalho gasto claro", (0.205, 0.092, 0.036)),
        material("Carvalho escuro", (0.092, 0.033, 0.012)),
        material("Madeira de borda", (0.245, 0.116, 0.045)),
    ]
    wood_inside = material("Interior do casco", (0.165, 0.071, 0.027))
    iron = material("Ferro oxidado", (0.115, 0.085, 0.067), 0.56, 0.62)
    rope = material("Corda de cânhamo", (0.43, 0.31, 0.16))
    grain_dark = material("Veios escuros", (0.105, 0.046, 0.022))
    grain_light = material("Veios claros", (0.275, 0.127, 0.048))

    make_keel(wood[2])
    # Casco exterior: sete tábuas longitudinais por bordo, com pequenas juntas.
    bands = 7
    for sign in (-1, 1):
        for i in range(bands):
            v0 = 0.10 + i * 0.125
            v1 = v0 + 0.115
            mat = wood[(i + (0 if sign < 0 else 1)) % len(wood)]
            make_strake(f"Tábua exterior {sign}_{i+1}", sign, v0, v1, mat, inset=0.0)
            # Linha fina de veio acompanha parte das tábuas, sem competir com a forma.
            for j in range(3):
                t0 = -0.78 + j * 0.52 + random.uniform(-0.035, 0.035)
                t1 = min(0.94, t0 + random.uniform(0.17, 0.33))
                v = (v0 + v1) * 0.5 + random.uniform(-0.025, 0.025)
                points = []
                for k in range(8):
                    t = t0 + (t1-t0)*k/7
                    w, z = profile(t, v)
                    points.append((1.16*t, sign*(w+0.003), z + random.uniform(-0.003, 0.003)))
                tube("Veio gasto da madeira", points,
                     grain_dark if j % 2 else grain_light, 0.0025, 1)

        # Revestimento interno de madeira visível acima do piso.
        for i in range(5):
            v0 = 0.38 + i * 0.13
            v1 = min(0.99, v0 + 0.12)
            make_strake(f"Tábua interna {sign}_{i+1}", sign, v0, v1,
                        wood_inside if i % 2 else wood[(i+1) % len(wood)], inset=0.045)

    make_floor_boards(wood)
    # Bancos de duas tábuas largas apoiados nas laterais internas.
    for index, x in enumerate((-0.43, 0.42), start=1):
        t = x / 1.16
        half, _ = profile(t, 0.92)
        box(f"Banco transversal {index}", (x, 0, 0.62 - 0.045*abs(t)),
            (0.105, half*1.72, 0.075), wood[1 if index == 1 else 0], 0.018)

    # Costelas internas e longarinas de borda.
    for x in (-0.82, -0.50, -0.17, 0.17, 0.50, 0.82):
        t = x / 1.16
        half, _ = profile(t, 0.92)
        make_rib(x, max(0.08, half-0.04), wood[1])
    for sign in (-1, 1):
        points = []
        for i in range(33):
            t = -0.985 + 1.97*i/32
            half, z = profile(t, 1.0)
            points.append((1.16*t, sign*half, z+0.012))
        tube("Borda superior do casco", points, wood[3], 0.038, 3)

    # Estribos externos de ferro com rebites nas laterais do casco.
    for x in (-0.78, 0.0, 0.78):
        t = x / 1.16
        points = []
        for i in range(15):
            v = 0.18 + 0.79*i/14
            half, z = profile(t, v)
            points.append((x, -half-0.018, z))
        for i in range(14, -1, -1):
            v = 0.18 + 0.79*i/14
            half, z = profile(t, v)
            points.append((x, half+0.018, z))
        tube("Faixa de ferro exterior", points, iron, 0.025, 2)
        for sign in (-1, 1):
            for v in (0.28, 0.52, 0.76, 0.94):
                half, z = profile(t, v)
                sphere("Rebite de ferro", (x, sign*(half+0.030), z), 0.022, iron, 10)

    # Proa elevada, argola e cabo curto de amarração.
    for x, name in ((-1.12, "Espelho da popa"), (1.12, "Espelho da proa")):
        half, z = profile(x/1.16, 0.92)
        box(name, (x, 0, z-0.005), (0.12, max(0.09, half*1.75), 0.28), wood[1], 0.025)
    ring_points = []
    for i in range(25):
        a = math.tau*i/24
        ring_points.append((1.205, 0.11+0.045*math.cos(a), 0.55+0.055*math.sin(a)))
    tube("Argola de amarração", ring_points, iron, 0.012, 2)
    tube("Corda de proa", [(1.22, 0.12, 0.56), (1.31, 0.15, 0.45),
                           (1.35, 0.18, 0.34), (1.31, 0.20, 0.27),
                           (1.24, 0.20, 0.30), (1.22, 0.18, 0.39)], rope, 0.027, 3)
    tube("Ponta solta da corda", [(1.22, 0.18, 0.39), (1.24, 0.18, 0.30),
                                 (1.28, 0.17, 0.20), (1.31, 0.16, 0.12)], rope, 0.020, 3)

    # Une o prop em uma malha de múltiplos materiais para carregamento simples no jogo.
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    active = meshes[0]
    bpy.context.view_layer.objects.active = active
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.join()
    boat = bpy.context.object
    boat.name = "Barco Medieval"
    boat.data.name = "Barco Medieval Mesh"
    boat["front_axis"] = "+X (proa)"
    boat["support_face"] = "bottom keel at Z=0"
    boat["source_reference"] = "assets/objetos/barco_medieval.png"
    boat["intended_footprint"] = "2x1 tiles"

    target = (0.0, 0.0, 0.44)
    camera = make_camera("Câmera principal - 3/4", (3.35, -4.25, 3.05), target)
    scene = bpy.context.scene
    scene.camera = camera
    setup_lights(target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.color = (0.05, 0.05, 0.05)

    blend_path = OUT / "barco_medieval.blend"
    glb_path = OUT / "barco_medieval.glb"
    preview_path = OUT / "barco_medieval_preview.png"
    scene.render.filepath = str(preview_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)

    bpy.ops.object.select_all(action="DESELECT")
    boat.select_set(True)
    bpy.context.view_layer.objects.active = boat
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB",
                              use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT")
    print("saved_blend", blend_path)
    print("saved_glb", glb_path)
    print("saved_preview", preview_path)
    print("boat_bounds", tuple(round(v, 3) for v in boat.dimensions))
    print("polygons", len(boat.data.polygons))


if __name__ == "__main__":
    main()
