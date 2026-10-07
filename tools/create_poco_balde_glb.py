"""Cria a miniatura do poço de fazenda com balde para 2D e 3D."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, roughness=0.9):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def cylinder(name, loc, radius, depth, material, vertices=12, bevel=0.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Arestas suaves", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cube(name, loc, scale, material, bevel=0.025, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Cantos gastos", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def tube(name, points, radius, material):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def hollow_bucket(name, loc, material):
    x, y, z = loc
    # Parede levemente cônica, aberta no topo, com fundo fechado.
    verts = []
    sides = 16
    for radius, height in ((0.138, z - 0.105), (0.155, z + 0.105),
                           (0.127, z + 0.105), (0.112, z - 0.085)):
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((x + radius * math.cos(a), y + radius * math.sin(a), height))
    faces = []
    for ring_a, ring_b in ((0, 1), (1, 2), (2, 3)):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((ring_a * sides + i, ring_a * sides + j,
                          ring_b * sides + j, ring_b * sides + i))
    faces.append(tuple(3 * sides + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def build():
    clear()
    stone = [mat("Pedra cinza %d" % i, c) for i, c in enumerate((
        (0.38, 0.39, 0.36), (0.48, 0.47, 0.42), (0.31, 0.33, 0.32),
        (0.55, 0.52, 0.45))) ]
    wood = [mat("Madeira %d" % i, c) for i, c in enumerate((
        (0.24, 0.12, 0.055), (0.39, 0.22, 0.09), (0.30, 0.16, 0.065))) ]
    iron = mat("Ferro escuro", (0.12, 0.14, 0.15), 0.55)
    rope = mat("Corda de cânhamo", (0.55, 0.38, 0.20))
    water = mat("Água no fundo", (0.055, 0.28, 0.39), 0.28)
    dark = mat("Interior do poço", (0.075, 0.065, 0.05))
    bucket_inside = mat("Interior do balde", (0.13, 0.095, 0.052))

    # Poço baixo de pedra: abertura escura e água visível no fundo.
    cylinder("Sombra do poço", (0, 0, 0.15), 0.51, 0.24, dark, 16, 0.02)
    cylinder("Água no fundo", (0, 0, 0.285), 0.39, 0.018, water, 24, 0)
    # Alvenaria em blocos individuais, com juntas e tons ligeiramente variados.
    count = 14
    for row, z in enumerate((0.22, 0.40, 0.58)):
        for i in range(count):
            a = 2 * math.pi * (i + (0.5 if row % 2 else 0)) / count
            r = 0.49
            block = cube("Bloco de pedra %d %d" % (row, i),
                         (r * math.cos(a), r * math.sin(a), z),
                         (0.245, 0.18, 0.16), stone[(i + row * 2) % len(stone)], 0.025,
                         (0, 0, a))
    # Espessas pedras da borda deixam a cavidade legível de cima.
    for i in range(14):
        a = 2 * math.pi * (i + 0.5) / 14
        cube("Pedra do aro %02d" % i,
             (0.50 * math.cos(a), 0.50 * math.sin(a), 0.69),
             (0.26, 0.19, 0.13), stone[(i + 1) % len(stone)], 0.02, (0, 0, a))

    # Pórtico de madeira e eixo horizontal do sarilho.
    for x in (-0.70, 0.70):
        cube("Esteio de carvalho", (x, 0.02, 0.79), (0.13, 0.15, 1.52), wood[0], 0.025,
             (0, 0, -0.035 if x < 0 else 0.035))
        cube("Pé do esteio", (x, 0.02, 0.13), (0.22, 0.25, 0.14), wood[2], 0.025)
    cylinder("Eixo do sarilho", (0, 0.02, 1.40), 0.075, 1.62, wood[1], 12, 0.015).rotation_euler[1] = math.pi / 2
    # Manivela na lateral direita.
    cylinder("Cubo da manivela", (0.84, 0.02, 1.40), 0.105, 0.10, iron, 10, 0.01).rotation_euler[1] = math.pi / 2
    cube("Braço da manivela", (0.92, 0.02, 1.25), (0.075, 0.09, 0.32), iron, 0.025)
    cylinder("Pega de madeira", (0.92, -0.02, 1.08), 0.055, 0.22, wood[2], 10, 0.01).rotation_euler[0] = math.pi / 2
    # Corda descendo para dentro do poço e balde pequeno pendurado na borda.
    tube("Corda enrolada e pendente", [(0.02, -0.02, 1.39), (0.06, -0.02, 1.27),
                                       (0.055, -0.02, 1.13), (0.055, -0.02, 0.87),
                                       (0.055, -0.02, 0.78)], 0.018, rope)
    # Balde em primeiro plano, para ser reconhecível em vista isométrica.
    cx, cy, bz = 0.36, -0.62, 0.30
    hollow_bucket("Corpo aberto do balde", (cx, cy, bz), wood[1])
    cylinder("Fundo do balde", (cx, cy, bz - 0.105), 0.137, 0.025, wood[0], 12, 0.01)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.145, minor_radius=0.018,
                                    major_segments=20, minor_segments=8,
                                    location=(cx, cy, bz + 0.105))
    bpy.context.object.name = "Aro de ferro do balde"
    bpy.context.object.data.materials.append(iron)
    cylinder("Água no balde", (cx, cy, bz + 0.088), 0.116, 0.012, water, 16, 0)
    # Arco do cabo em U.
    tube("Alça de ferro", [(cx - 0.15, cy, bz + 0.13), (cx - 0.17, cy, bz + 0.31),
                            (cx, cy, bz + 0.38), (cx + 0.17, cy, bz + 0.31),
                            (cx + 0.15, cy, bz + 0.13)], 0.012, iron)

    # Reduz chamadas de desenho mantendo objetos separados por material.
    for material in list(bpy.data.materials):
        group = [o for o in bpy.context.scene.objects
                 if o.type == "MESH" and o.data.materials and material in o.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Poço | " + material.name
        group[0].data.name = group[0].name + " Mesh"

    # Chão de apresentação (não exportado) e render ortográfico com transparência.
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.015))
    floor = bpy.context.object
    floor.name = "Piso de prévia"
    floor.data.materials.append(mat("Fundo pedra", (0.07, 0.08, 0.09)))
    bpy.ops.object.camera_add(location=(2.5, -3.2, 2.75))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.75
    point_at(camera, (0, 0, 0.68))
    scene = bpy.context.scene
    scene.camera = camera
    for name, loc, energy, size in (("Principal", (1.0, -2.0, 4), 105, 3),
                                    ("Preenchimento", (-3, -1, 2.3), 62, 3),
                                    ("Recorte", (1.5, 2.5, 3.2), 78, 2)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        point_at(light, (0, 0, 0.55))

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = str(OUT / "poco_balde_preview.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "poco_balde.blend"))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / "poco_balde.png")
    bpy.ops.render.render(write_still=True)

    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in scene.objects if o.type == "MESH" and o != floor]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / "poco_balde.glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT poco_balde meshes=%d" % len(meshes))


if __name__ == "__main__":
    build()
