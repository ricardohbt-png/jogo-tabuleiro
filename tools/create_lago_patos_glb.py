"""Cria uma miniatura de lago rural com patos, juncos e pedras."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "lago_patos"


def mat(name, color, roughness=0.88):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def sphere(name, pos, scale, material, segments=16, rings=10, rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rot:
        obj.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def cylinder(name, pos, radius, depth, material, vertices=12, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=pos)
    obj = bpy.context.object
    obj.name = name
    if rot:
        obj.rotation_euler = rot
    obj.data.materials.append(material)
    return obj


def beam(name, a, b, radius, material, vertices=7):
    a, b = Vector(a), Vector(b)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return obj


def mesh_obj(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def pond_surface(name, rx, ry, z_bottom, z_top, material, segments=80):
    """Espelho d'água com contorno orgânico, em vez de uma piscina oval perfeita."""
    verts, faces = [(0, 0, z_top)], []
    top_ring, bottom_ring = [], []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        wobble = (1.0 + 0.035 * math.sin(3 * angle + 0.4)
                  + 0.023 * math.sin(5 * angle + 1.2)
                  + 0.012 * math.sin(9 * angle - 0.7))
        x, y = rx * wobble * math.cos(angle), ry * wobble * math.sin(angle)
        top_ring.append(len(verts))
        verts.append((x, y, z_top))
        bottom_ring.append(len(verts))
        verts.append((x, y, z_bottom))
    for i in range(segments):
        n = (i + 1) % segments
        faces.append((0, top_ring[i], top_ring[n]))
        faces.append((top_ring[i], bottom_ring[i], bottom_ring[n], top_ring[n]))
    obj = mesh_obj(name, verts, faces, material)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def ripple_arc(name, center, radius, start, end, z, material, width=0.006,
               segments=22):
    verts, faces = [], []
    for i in range(segments + 1):
        t = start + (end - start) * i / segments
        x, y = radius * math.cos(t), radius * 0.68 * math.sin(t)
        tx, ty = -radius * math.sin(t), radius * 0.68 * math.cos(t)
        length = max(1e-6, math.hypot(tx, ty))
        nx, ny = -ty / length, tx / length
        verts.extend(((center[0] + x + nx * width, center[1] + y + ny * width, z),
                      (center[0] + x - nx * width, center[1] + y - ny * width, z)))
    for i in range(segments):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    obj = mesh_obj(name, verts, faces, material)
    return obj


def duck_body_mesh(name, center, yaw, scale, body_mat, breast_mat, neck_mat, sex):
    """Perfil contínuo do corpo à cabeça para evitar o aspecto de esferas empilhadas."""
    profile = ((-0.285, 0.012, 0.020, 0.030),
               (-0.245, 0.008, 0.075, 0.062),
               (-0.160, 0.000, 0.118, 0.086),
               (-0.040, 0.000, 0.135, 0.100),
               ( 0.075, 0.012, 0.115, 0.090),
               ( 0.140, 0.028, 0.078, 0.082),
               ( 0.145, 0.072, 0.054, 0.068),
               ( 0.176, 0.125, 0.054, 0.068),
               ( 0.215, 0.170, 0.071, 0.066),
               ( 0.255, 0.180, 0.074, 0.064),
               ( 0.298, 0.170, 0.055, 0.052),
               ( 0.322, 0.155, 0.025, 0.030))
    sides = 24
    verts, faces, face_materials = [], [], []

    def world_point(x, y, z):
        x, y, z = x * scale, y * scale, z * scale
        return (center[0] + x * math.cos(yaw) - y * math.sin(yaw),
                center[1] + x * math.sin(yaw) + y * math.cos(yaw),
                center[2] + z)

    for i, (x, z, ry, rz) in enumerate(profile):
        before, after = profile[max(0, i - 1)], profile[min(len(profile) - 1, i + 1)]
        tx, tz = after[0] - before[0], after[1] - before[1]
        length = max(1e-6, math.hypot(tx, tz))
        px, pz = -tz / length, tx / length
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            offset_y = math.cos(angle) * ry
            offset = math.sin(angle) * rz
            verts.append(world_point(x + px * offset, offset_y, z + pz * offset))

    for i in range(len(profile) - 1):
        xmid = (profile[i][0] + profile[i + 1][0]) / 2
        zmid = (profile[i][1] + profile[i + 1][1]) / 2
        if sex == "mallard" and zmid > 0.14:
            mat_index = 2
        elif xmid > 0.07 and zmid < 0.10:
            mat_index = 1
        else:
            mat_index = 0
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            c = (i + 1) * sides + (j + 1) % sides
            d = (i + 1) * sides + j
            faces.append((a, b, c, d))
            face_materials.append(mat_index)
    faces.append(tuple(reversed(range(sides))))
    face_materials.append(0)
    last_ring = (len(profile) - 1) * sides
    faces.append(tuple(last_ring + j for j in range(sides)))
    face_materials.append(0)

    obj = mesh_obj(name, verts, faces, body_mat)
    obj.data.materials.append(breast_mat)
    obj.data.materials.append(neck_mat)
    for face, mat_index in zip(obj.data.polygons, face_materials):
        face.material_index = mat_index
        face.use_smooth = True
    return obj


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def duck(name, center, yaw, body_mat, neck_mat, head_mat, wing_mat,
         breast_mat, bill_mat, eye_mat, speculum_mat, scale=1.0,
         mottled=False, duckling=False):
    def p(x, y, z):
        x, y, z = x * scale, y * scale, z * scale
        return (center[0] + x * math.cos(yaw) - y * math.sin(yaw),
                center[1] + x * math.sin(yaw) + y * math.cos(yaw),
                center[2] + z)

    duck_body_mesh(name + " corpo e pescoço", center, yaw, scale,
                   body_mat, breast_mat, head_mat,
                   "mallard" if head_mat is neck_mat else "other")

    # Bico achatado e largo: duas seções ovais formam uma cunha curta.
    bill_verts, bill_faces = [], []
    sections = ((0.290, 0.050, 0.026), (0.350, 0.039, 0.018),
                (0.405, 0.012, 0.008))
    sides = 10
    for x, half_width, half_height in sections:
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            yy = math.cos(angle) * half_width
            zz = 0.165 + math.sin(angle) * half_height
            point = p(x, yy, zz)
            bill_verts.append(point)
    for ring in range(len(sections) - 1):
        for i in range(sides):
            a = ring * sides + i
            b = ring * sides + (i + 1) % sides
            bill_faces.append((a, b, b + sides, a + sides))
    bill_faces.append(tuple(range(sides - 1, -1, -1)))
    bill_faces.append(tuple((len(sections) - 1) * sides + i for i in range(sides)))
    bill = mesh_obj(name + " bico achatado", bill_verts, bill_faces, bill_mat)

    for side in (-1, 1):
        sphere(name + " olho", p(0.255, side * 0.067, 0.193),
               (0.014 * scale, 0.012 * scale, 0.014 * scale), eye_mat,
               segments=12, rings=8)
        sphere(name + " asa", p(-0.020, side * 0.104, 0.010),
               (0.151 * scale, 0.038 * scale, 0.062 * scale), wing_mat,
               segments=22, rings=14, rot=(0, 0.05, yaw - 0.12))
        # Faixa iridescente e clara de penas secundárias, típica do pato-real.
        sphere(name + " faixa clara da asa", p(-0.038, side * 0.137, 0.022),
               (0.081 * scale, 0.009 * scale, 0.012 * scale), breast_mat,
               segments=16, rings=10, rot=(0, 0.02, yaw - 0.12))
        sphere(name + " espelho da asa", p(-0.055, side * 0.139, 0.006),
               (0.061 * scale, 0.010 * scale, 0.027 * scale), speculum_mat,
               segments=16, rings=10, rot=(0, 0.03, yaw - 0.12))

        if mottled:
            # Pequenas marcas de penas em tons terrosos quebram a cor uniforme.
            for i, (dx, dz, size) in enumerate(((-0.13, 0.045, 0.020),
                                                (-0.06, 0.065, 0.015),
                                                (0.015, 0.045, 0.018),
                                                (-0.11, -0.018, 0.014))):
                sphere(f"{name} pena salpicada {side} {i}",
                       p(dx, side * 0.132, dz),
                       (size * scale * 1.45, 0.005 * scale, size * scale * 0.55),
                       speculum_mat if i % 2 else breast_mat,
                       segments=10, rings=6)

    if duckling:
        # Faixa escura suave sobre os olhos e penugem clara nas bochechas.
        for side in (-1, 1):
            sphere(name + " mancha facial", p(0.228, side * 0.068, 0.186),
                   (0.047 * scale, 0.006 * scale, 0.010 * scale), breast_mat,
                   segments=12, rings=8)


def build():
    rng = random.Random(88104)
    grass = mat("Margem verde musgo", (0.24, 0.32, 0.15))
    grass_lite = mat("Capim baixo ao sol", (0.22, 0.29, 0.12))
    soil = mat("Lodo escuro da margem", (0.12, 0.10, 0.07))
    water = mat("Água verde profunda", (0.018, 0.105, 0.085), 0.38)
    water_light = mat("Reflexo suave na água", (0.08, 0.16, 0.13), 0.42)
    rocks = [mat("Pedra de margem %d" % i, color) for i, color in enumerate((
        (0.20, 0.19, 0.15), (0.27, 0.25, 0.20), (0.15, 0.17, 0.15)))]
    reed = mat("Juncos verde-oliva", (0.13, 0.23, 0.09))
    reed_lite = mat("Pontas dos juncos", (0.25, 0.30, 0.11))
    lily = mat("Folhas de nenúfar", (0.11, 0.27, 0.12))
    lily_light = mat("Folhas claras", (0.20, 0.35, 0.14))
    flower = mat("Flor amarela", (0.96, 0.68, 0.16))
    bill_mallard = mat("Bico amarelo do pato-real", (0.90, 0.52, 0.08), 0.28)
    bill_female = mat("Bico oliva da fêmea", (0.30, 0.27, 0.15), 0.32)
    bill_duckling = mat("Bico alaranjado do filhote", (0.88, 0.38, 0.045), 0.30)
    eye = mat("Olhos escuros", (0.018, 0.014, 0.010), 0.19)
    mallard_body = mat("Penas cinza e castanhas", (0.29, 0.31, 0.27), 0.73)
    mallard_neck = mat("Pescoço verde iridescente", (0.025, 0.17, 0.095), 0.32)
    mallard_breast = mat("Peito castanho do pato-real", (0.26, 0.105, 0.040), 0.77)
    mallard_wing = mat("Asas cinza acastanhadas", (0.24, 0.25, 0.22), 0.78)
    speculum = mat("Penas verde-azuladas", (0.035, 0.23, 0.20), 0.35)
    female_body = mat("Penas pardas da fêmea", (0.28, 0.18, 0.10), 0.82)
    female_light = mat("Penas claras salpicadas", (0.49, 0.35, 0.21), 0.86)
    female_dark = mat("Penas escuras salpicadas", (0.18, 0.115, 0.068), 0.86)
    duckling_body = mat("Penugem dourada do filhote", (0.68, 0.48, 0.23), 0.84)
    duckling_breast = mat("Peito claro do filhote", (0.82, 0.66, 0.39), 0.84)
    duckling_dark = mat("Marcas do filhote", (0.32, 0.20, 0.10), 0.85)

    # Sem plataforma: só manchas de lodo e grama rente ao piso do tile.
    for i, (x, y, sx, sy) in enumerate(((-1.02, -0.47, 0.20, 0.09),
                                        (0.98, 0.48, 0.18, 0.08),
                                        (0.58, -0.88, 0.15, 0.07),
                                        (-0.36, 0.94, 0.17, 0.07),
                                        (1.20, -0.12, 0.12, 0.07),
                                        (-1.23, 0.12, 0.13, 0.08))):
        patch_mat = soil if i % 2 == 0 else grass
        sphere("Mancha baixa da margem", (x, y, 0.008), (sx, sy, 0.003), patch_mat,
               segments=16, rings=8)
    # Espelho irregular muito fino, rente ao terreno, sem aro circular elevado.
    pond_surface("Água rasa de contorno irregular", 1.17, 0.91,
                 -0.005, 0.008, water, segments=80)

    # Pedras baixas contornam a água; cada uma varia um pouco em forma e escala.
    for i in range(14):
        angle = 2 * math.pi * i / 18 + rng.uniform(-0.08, 0.08)
        radius = rng.uniform(1.08, 1.25)
        x = 1.15 * radius * math.cos(angle)
        y = 0.91 * radius * math.sin(angle)
        scale = (rng.uniform(0.09, 0.15), rng.uniform(0.065, 0.11), rng.uniform(0.035, 0.065))
        sphere("Pedra baixa da margem", (x, y, 0.008 + scale[2] * 0.36), scale,
               rng.choice(rocks), segments=10, rings=6,
               rot=(rng.uniform(-0.15, 0.15), rng.uniform(-0.2, 0.2), angle))

    # Dois patos-reais adultos e um filhote, sentados na linha d'água.
    duck("Pato-real macho", (-0.39, -0.13, 0.105), 0.12,
         mallard_body, mallard_neck, mallard_neck, mallard_wing,
         mallard_breast, bill_mallard, eye, speculum, scale=1.0)
    duck("Pata-real", (0.40, 0.29, 0.105), -2.58,
         female_body, female_body, female_body, female_body,
         female_light, bill_female, eye, female_dark,
         scale=0.94, mottled=True)
    duck("Patinho", (0.38, -0.49, 0.092), 0.56,
         duckling_body, duckling_body, duckling_body, duckling_body,
         duckling_breast, bill_duckling, eye, duckling_dark,
         scale=0.70, duckling=True)
    # Reflexos ondulados quebrados em arcos curtos acompanham os patos.
    for index, (x, y, radius) in enumerate(((-0.39, -0.13, 0.30),
                                            (0.40, 0.29, 0.28),
                                            (0.38, -0.49, 0.23))):
        ripple_arc(f"Reflexo em arco {index + 1}a", (x, y), radius,
                   0.18, 1.05, 0.011, water_light)
        ripple_arc(f"Reflexo em arco {index + 1}b", (x, y), radius * 1.18,
                   3.55, 4.45, 0.010, water_light, width=0.004, segments=18)

    # Nenúfares e pequenas flores ocupam as bordas sem cobrir os patos.
    for i, (x, y) in enumerate(((-0.88, 0.34), (0.87, 0.58), (-0.90, -0.53), (0.04, 0.76))):
        z = 0.012
        sphere("Folha de nenúfar", (x, y, z), (0.13, 0.085, 0.012),
               lily if i % 2 else lily_light, segments=12, rings=6)
        if i in (0, 2):
            sphere("Flor de lago", (x + 0.025, y, z + 0.015), (0.032, 0.032, 0.022),
                   flower, segments=10, rings=6)

    # Juncos altos em pequenos grupos na margem e folhas baixas entre as pedras.
    for cx, cy, count in ((-1.13, 0.60, 4), (1.08, -0.73, 3), (-0.26, 1.03, 3)):
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = cx + 0.07 * math.cos(angle)
            y = cy + 0.07 * math.sin(angle)
            height = rng.uniform(0.24, 0.37)
            beam("Haste de junco", (x, y, 0.005),
                 (x + 0.07 * math.cos(angle), y + 0.07 * math.sin(angle), 0.005 + height),
                 0.014, reed, vertices=6)
            beam("Espiga do junco", (x + 0.07 * math.cos(angle), y + 0.07 * math.sin(angle),
                                      0.005 + height * 0.78),
                 (x + 0.07 * math.cos(angle), y + 0.07 * math.sin(angle), 0.005 + height),
                 0.018, reed_lite, vertices=6)
        for j in range(2):
            angle = j * math.pi + 0.35
            beam("Folha de junco", (cx, cy, 0.005),
                 (cx + 0.15 * math.cos(angle), cy + 0.15 * math.sin(angle), 0.12),
                 0.016, lily, vertices=5)

    # Pequenos tufos de grama quebram o contorno redondo da margem.
    for i in range(8):
        angle = 2 * math.pi * (i + 0.3) / 8
        x, y = 1.25 * math.cos(angle), 1.12 * math.sin(angle)
        for j in range(3):
            a = angle + j * 2 * math.pi / 3
            beam("Tufo baixo da margem", (x, y, 0.004),
                 (x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), 0.095 + 0.008 * j),
                 0.012, grass_lite, vertices=5)


def merge_by_material():
    for material in list(bpy.data.materials):
        group = [o for o in bpy.context.scene.objects
                 if o.type == "MESH" and material in o.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Lago | " + material.name


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.10, 0.09, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    for name, loc, energy, size, color in (
        ("Luz solar", (2.8, -3.5, 4.5), 310, 3.0, (1.0, 0.86, 0.68)),
        ("Preenchimento", (-3.0, -0.3, 2.8), 190, 2.6, (0.75, 0.88, 1.0)),
        ("Luz de contorno", (0.6, 2.5, 3.8), 240, 2.3, (0.70, 0.86, 1.0)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.25))
    preview_ground_mat = mat("Piso de prévia - não exportado", (0.16, 0.19, 0.13), 0.96)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.004))
    preview_ground = bpy.context.object
    preview_ground.name = "Piso de prévia - remover antes da exportação"
    preview_ground.data.materials.append(preview_ground_mat)
    bpy.ops.object.camera_add(location=(3.2, -4.8, 3.55))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.65
    point_at(camera, (0, 0, 0.36))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))
    return preview_ground


def export_asset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        if data in (bpy.data.cameras, bpy.data.lights):
            continue
        for block in list(data):
            if block.users == 0:
                data.remove(block)
    build()
    merge_by_material()
    preview_ground = setup_scene()
    scene = bpy.context.scene
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(preview_ground, do_unlink=True)
    scene.render.film_transparent = True
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    export_asset()
