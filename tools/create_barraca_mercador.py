"""Cria a barraca de mercador e cestos de feira para as decorações do editor."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, color, metallic=0.0, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def cube(name, loc, dims, mat, bevel=0.0, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        mod = obj.modifiers.new("Bordas gastas", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        normal = obj.modifiers.new("Normais de madeira", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=normal.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=12, rotation=None, radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    assign(obj, mat)
    bevel = obj.modifiers.new("Arestas suaves", "BEVEL")
    bevel.width = min(radius * 0.12, 0.012)
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, loc, scale, mat, segments=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def rod(name, a, b, radius, mat, vertices=8):
    start, end = Vector(a), Vector(b)
    delta = end - start
    obj = cylinder(name, (start + end) * 0.5, radius, delta.length, mat, vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def curve(name, points, radius, mat):
    path = bpy.data.curves.new(name + " path", "CURVE")
    path.dimensions = "3D"
    path.resolution_u = 4
    path.bevel_depth = radius
    path.bevel_resolution = 2
    spline = path.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points):
        point.co = (*coord, 1)
    obj = bpy.data.objects.new(name, path)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.context.object.select_set(False)
    return bpy.context.object


def torus(name, loc, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=16, minor_segments=6,
                                     location=loc, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    return obj


def make_basket(prefix, center, size, materials, contents):
    x, y, z = center
    wood, weave_light, weave_dark = materials["basket"]
    width, depth, height = size
    cylinder(prefix + " | corpo trançado", (x, y, z + height * 0.48),
             width * 0.43, height * 0.92, wood, 12,
             radius_top=width * 0.55)
    for j in range(4):
        ring_z = z + height * (0.18 + j * 0.20)
        torus(prefix + " | aro horizontal %d" % j,
              (x, y, ring_z), width * (0.47 + j * 0.035), 0.009,
              weave_light if j % 2 == 0 else weave_dark)
    torus(prefix + " | borda", (x, y, z + height * 0.93),
          width * 0.59, 0.018, weave_light)
    for i in range(12):
        angle = math.tau * i / 12
        lower = (x + math.cos(angle) * width * 0.47,
                 y + math.sin(angle) * width * 0.47, z + height * 0.08)
        upper = (x + math.cos(angle) * width * 0.60,
                 y + math.sin(angle) * width * 0.60, z + height * 0.88)
        rod(prefix + " | fibra vertical %02d" % i, lower, upper, 0.009,
            weave_light if i % 2 == 0 else weave_dark)

    # Alças semicirculares visíveis acima das cestas.
    curve(prefix + " | alça", [
        (x - width * 0.28, y, z + height * 0.90),
        (x - width * 0.22, y, z + height * 1.24),
        (x, y, z + height * 1.36),
        (x + width * 0.22, y, z + height * 1.24),
        (x + width * 0.28, y, z + height * 0.90)], 0.012, weave_dark)

    if contents == "fruit":
        fruit = materials["fruit"]
        colors = [fruit[0], fruit[1], fruit[2], fruit[0], fruit[3], fruit[1], fruit[2]]
        for i, mat in enumerate(colors):
            angle = (i / len(colors)) * math.tau
            r = width * (0.18 if i < 4 else 0.10)
            px, py = x + math.cos(angle) * r, y + math.sin(angle) * r
            pz = z + height * (1.00 + (0.10 if i % 3 == 0 else 0.0))
            sphere(prefix + " | fruta %02d" % i, (px, py, pz),
                   (width * 0.16, width * 0.15, width * 0.17), mat)
            cylinder(prefix + " | talo %02d" % i,
                     (px, py, pz + width * 0.16), width * 0.018,
                     width * 0.07, materials["stem"], 6)
    elif contents == "bread":
        bread, crust = materials["bread"]
        for i in range(4):
            angle = math.tau * i / 4 + 0.2
            px, py = x + math.cos(angle) * width * 0.18, y + math.sin(angle) * width * 0.18
            loaf = sphere(prefix + " | pão %02d" % i,
                          (px, py, z + height * (1.03 + (i % 2) * 0.08)),
                          (width * 0.20, width * 0.12, width * 0.12), bread)
            loaf.rotation_euler[2] = angle
            # Sulcos dourados marcam os pães sem adicionar letras ou placas.
            curve(prefix + " | corte do pão %02d" % i,
                  [(px - width * 0.06, py - width * 0.03, z + height * 1.13),
                   (px, py, z + height * 1.17),
                   (px + width * 0.06, py + width * 0.03, z + height * 1.13)],
                  0.006, crust)


def add_balance(prefix, center, scale, mats):
    x, y, z = center
    metal, brass = mats["metal"], mats["brass"]
    s = scale
    cylinder(prefix + " | pé", (x, y, z + 0.025 * s), 0.13 * s, 0.05 * s, brass)
    cylinder(prefix + " | haste", (x, y, z + 0.22 * s), 0.035 * s, 0.37 * s, metal)
    sphere(prefix + " | nó superior", (x, y, z + 0.405 * s),
           (0.07 * s, 0.07 * s, 0.065 * s), brass)
    beam_z = z + 0.37 * s
    rod(prefix + " | braço", (x - 0.25 * s, y, beam_z),
        (x + 0.25 * s, y, beam_z), 0.022 * s, brass)
    for side in (-1, 1):
        px = x + side * 0.21 * s
        for dx in (-0.085, 0.085):
            rod(prefix + " | corrente", (px + dx * s, y, beam_z - 0.01 * s),
                (px + dx * s, y, z + 0.12 * s), 0.006 * s, metal, 6)
        cylinder(prefix + " | prato", (px, y, z + 0.105 * s),
                 0.12 * s, 0.025 * s, brass, 12)
    sphere(prefix + " | pivô", (x, y, beam_z + 0.025 * s),
           (0.028 * s, 0.028 * s, 0.028 * s), metal, 8, 6)


def stall_materials():
    return {
        "wood": [material("Carvalho mel", (0.34, 0.16, 0.055)),
                 material("Carvalho claro", (0.48, 0.26, 0.10)),
                 material("Carvalho sombra", (0.20, 0.085, 0.030))],
        "cloth": [material("Lona vermelho queimado", (0.42, 0.035, 0.020)),
                  material("Lona linho", (0.67, 0.48, 0.25))],
        "basket": [material("Vime castanho", (0.28, 0.14, 0.055)),
                   material("Vime claro", (0.49, 0.29, 0.12)),
                   material("Vime escuro", (0.21, 0.095, 0.035))],
        "fruit": [material("Maçã rubra", (0.58, 0.025, 0.012)),
                  material("Maçã verde", (0.13, 0.32, 0.025)),
                  material("Pera dourada", (0.70, 0.34, 0.018)),
                  material("Ameixa", (0.20, 0.045, 0.28))],
        "bread": [material("Pão assado", (0.42, 0.15, 0.025)),
                  material("Cortes dourados", (0.72, 0.40, 0.10))],
        "stem": material("Talos", (0.20, 0.30, 0.075)),
        "metal": material("Ferro escurecido", (0.095, 0.105, 0.10), 0.72, 0.48),
        "brass": material("Bronze de balança", (0.58, 0.34, 0.095), 0.56, 0.42),
    }


def make_stall():
    m = stall_materials()
    w = m["wood"]
    made = []
    # Quatro montantes sustentam o toldo; a frente fica voltada para -Y.
    for x in (-0.82, 0.82):
        for y in (-0.74, 0.74):
            made.append(cube("Barraca | montante", (x, y, 1.00),
                             (0.09, 0.09, 1.93), w[0], 0.012))
            made.append(cube("Barraca | pé", (x, y, 0.12),
                             (0.15, 0.15, 0.10), w[2], 0.014))
    for y in (-0.74, 0.74):
        made.append(cube("Barraca | travessa lateral", (0, y, 1.84),
                         (1.72, 0.07, 0.09), w[1], 0.01))
    for x in (-0.82, 0.82):
        made.append(cube("Barraca | travessa de topo", (x, 0, 2.00),
                         (0.07, 1.58, 0.08), w[1], 0.01))

    # Balcão frontal de tábuas com suportes e uma prateleira inferior.
    front_y = -0.60
    counter_z = 0.94
    for x in (-0.62, 0.62):
        made.append(cube("Balcão | suporte", (x, front_y, 0.59),
                         (0.075, 0.32, 0.68), w[2], 0.008))
    for i in range(4):
        made.append(cube("Balcão | tábua frontal %d" % i,
                         (0, front_y - 0.17, 0.54 + i * 0.15),
                         (1.44, 0.055, 0.13), w[i % 2], 0.006))
    made.append(cube("Balcão | tampo", (0, front_y - 0.06, counter_z),
                     (1.62, 0.52, 0.11), w[1], 0.018))
    made.append(cube("Balcão | prateleira", (0, front_y + 0.01, 0.30),
                     (1.42, 0.34, 0.07), w[0], 0.01))
    # Pregos de ferro legíveis na frente do balcão.
    for x in (-0.57, 0.57):
        for z in (0.55, 0.70, 0.85):
            cylinder("Balcão | prego", (x, front_y - 0.201, z),
                     0.012, 0.012, m["metal"], 8, (math.pi / 2, 0, 0))

    # Toldo em listras de lona sobre duas águas, com beiral frontal ondulado.
    stripe_count = 7
    for side in (-1, 1):
        for i in range(stripe_count):
            x0 = -0.90 + 1.80 * i / stripe_count
            x1 = -0.90 + 1.80 * (i + 1) / stripe_count
            y0, y1 = ((-0.86, 0.0) if side == -1 else (0.0, 0.86))
            z_eave, z_ridge = 2.03, 2.30
            verts = [(x0, y0, z_eave), (x1, y0, z_eave),
                     (x1, y1, z_ridge), (x0, y1, z_ridge)] if side == -1 else [
                         (x0, y0, z_ridge), (x1, y0, z_ridge),
                         (x1, y1, z_eave), (x0, y1, z_eave)]
            mesh = bpy.data.meshes.new("Lona do toldo mesh")
            mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
            mesh.materials.append(m["cloth"][i % 2])
            panel = bpy.data.objects.new("Toldo | faixa %d" % i, mesh)
            bpy.context.collection.objects.link(panel)
            made.append(panel)
    # Borda pendente em painéis curtos, como babado de feira.
    for i in range(9):
        x = -0.82 + i * 0.205
        cloth = m["cloth"][i % 2]
        made.append(cube("Toldo | babado frontal %d" % i,
                         (x, -0.84, 1.94), (0.19, 0.035, 0.16), cloth, 0.022))
    # Travessa da cumeeira e ripas visíveis sob a lona.
    made.append(cube("Toldo | cumeeira", (0, 0, 2.27),
                     (1.82, 0.07, 0.07), w[2], 0.01))
    for x in (-0.60, 0, 0.60):
        for side in (-1, 1):
            rod("Toldo | ripa", (x, 0, 2.24),
                (x, side * 0.82, 2.01), 0.022, w[1])

    # Mercadorias no balcão: frutas, pães e uma balança de pratos em bronze.
    make_basket("Cesto de frutas da barraca", (-0.48, -0.60, 1.00),
                (0.34, 0.30, 0.28), m, "fruit")
    make_basket("Cesto de pães da barraca", (0.48, -0.60, 1.00),
                (0.34, 0.30, 0.28), m, "bread")
    add_balance("Balança do mercador", (0.0, -0.61, 1.00), 0.85, m)

    # Sacos de mercadoria e pequena caixa na prateleira baixa.
    sack = material("Saco de juta", (0.48, 0.32, 0.14))
    sphere("Saco de grãos no balcão", (0.34, -0.13, 0.47),
           (0.18, 0.13, 0.17), sack)
    made.append(cube("Caixote sob o balcão", (-0.42, -0.40, 0.47),
                     (0.34, 0.30, 0.31), w[0], 0.018))
    return made


def make_standalone_baskets():
    m = stall_materials()
    made = []
    make_basket("Cesto de maçãs", (-0.18, -0.04, 0.00),
                (0.38, 0.34, 0.35), m, "fruit")
    make_basket("Cesto de pães", (0.22, 0.10, 0.00),
                (0.35, 0.31, 0.31), m, "bread")
    return made


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_and_export(slug, builder, target, ortho):
    clear_scene()
    builder()
    bpy.ops.object.camera_add(location=(target[0] + 3.0, target[1] - 4.0,
                                        target[2] + 2.7))
    camera = bpy.context.object
    camera.name = "Câmera | miniatura isométrica"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho
    point_at(camera, target)
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.07, 0.06, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for name, location, energy, size, color in (
        ("Luz principal", (2.4, -3.0, 4.3), 245, 3.0, (1.0, 0.84, 0.66)),
        ("Luz de preenchimento", (-3.0, -1.2, 2.8), 145, 3.5, (0.76, 0.86, 1.0)),
        ("Luz de recorte", (0.6, 3.0, 3.8), 185, 2.5, (1.0, 0.72, 0.48)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        point_at(light, target)
    scene.render.filepath = str(OUT / (slug + "_preview.png"))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (slug + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (slug + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (slug + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", slug, "meshes=", len(meshes))


def main():
    render_and_export("barraca_mercador", make_stall,
                      (0, 0, 1.15), 3.12)
    render_and_export("cestos_feira", make_standalone_baskets,
                      (0, 0, 0.28), 1.34)


if __name__ == "__main__":
    main()
