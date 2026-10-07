"""Cria formações de estalactites/estalagmites e uma fenda fumegante.

Exporta .blend editável, GLB para o tabuleiro, PNG transparente para o editor
e prévia renderizada para revisão visual.
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


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.cameras, bpy.data.lights):
        for block in list(data):
            if block.users == 0:
                data.remove(block)


def material(name, color, roughness=0.92, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission, 1)
        shader.inputs["Emission Strength"].default_value = emission_strength
    return m


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def ellipsoid(name, pos, scale, mat, segments=18, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tapered_curve(name, points, radii, mat, bevel):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 10
    curve.bevel_depth = bevel
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point, radius in zip(spline.bezier_points, points, radii):
        bp.co = point
        bp.radius = radius
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def irregular_spike(name, x, y, z_base, height, radius, mat, rng, upward=True, lean=0):
    """Espícula calcária de anéis facetados e ponta ligeiramente desviada."""
    sides = 9
    if upward:
        levels = [(0.0, 1.0), (0.14, 0.86), (0.53, 0.52), (0.83, 0.25), (1.0, 0.035)]
    else:
        levels = [(0.0, 0.78), (0.16, 1.0), (0.49, 0.58), (0.81, 0.27), (1.0, 0.035)]
    verts, faces = [], []
    z_tip = z_base + height if upward else z_base - height
    for li, (t, factor) in enumerate(levels):
        center_x = x + lean * t
        center_y = y + lean * 0.34 * math.sin(t * math.pi)
        z = z_base + height * t if upward else z_base - height * t
        for j in range(sides):
            a = math.tau * j / sides
            wobble = rng.uniform(0.90, 1.10) * (1 + 0.055 * math.sin(a * 3 + li * 0.8))
            rr = radius * factor * wobble
            verts.append((center_x + math.cos(a) * rr,
                          center_y + math.sin(a) * rr,
                          z + (0.012 * math.sin(a * 2 + li) if li == 0 else 0)))
    for li in range(len(levels) - 1):
        for j in range(sides):
            a = li * sides + j
            b = li * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.append(tuple(range(sides)))
    faces.append(tuple((len(levels) - 1) * sides + j for j in reversed(range(sides))))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # Bordas irregulares ficam facetadas; só o acabamento em forma de ponta é suave.
    return obj


def rock_cluster(rng, x, y, z, scale, mat, prefix):
    for i in range(5):
        a = math.tau * i / 5 + rng.uniform(-0.25, 0.25)
        r = scale * rng.uniform(0.28, 0.65)
        s = rng.uniform(0.10, 0.18) * scale
        ellipsoid(prefix + " pedra quebrada", (x + math.cos(a) * r,
                  y + math.sin(a) * r, z + rng.uniform(-0.015, 0.035)),
                  (s * 1.35, s, s * 0.78), mat, 12, 8)


def rock_shelf(rng, mat):
    """Recorte de teto anguloso em vez de uma laje lisa e oval."""
    sides = 11
    verts, faces = [], []
    for ring, (z, radius, y_scale) in enumerate(((0.93, 0.27, 0.235), (1.045, 0.31, 0.25))):
        for j in range(sides):
            a = math.tau * j / sides
            wobble = rng.uniform(0.86, 1.12)
            verts.append((math.cos(a) * radius * wobble,
                          math.sin(a) * y_scale * wobble,
                          z + (rng.uniform(-0.045, 0.045) if ring else rng.uniform(-0.015, 0.015))))
    for j in range(sides):
        faces.append((j, (j + 1) % sides, sides + (j + 1) % sides, sides + j))
    faces.append(tuple(sides + j for j in range(sides)))
    mesh = bpy.data.meshes.new("Recorte de teto calcário mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new("Recorte de teto calcário | borda quebrada", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def ground_ribbon(name, points, widths, mat, z):
    """Faixa plana e recortada em XY para rachadura ou veio de magma."""
    verts, faces = [], []
    for i, point in enumerate(points):
        p = Vector((point[0], point[1]))
        before = Vector((points[max(0, i - 1)][0], points[max(0, i - 1)][1]))
        after = Vector((points[min(len(points) - 1, i + 1)][0],
                        points[min(len(points) - 1, i + 1)][1]))
        direction = after - before
        side = Vector((-direction.y, direction.x))
        if side.length < 1e-6:
            side = Vector((0, 1))
        side.normalize()
        verts.extend(((p.x - side.x * widths[i], p.y - side.y * widths[i], z),
                      (p.x + side.x * widths[i], p.y + side.y * widths[i], z)))
    for i in range(len(points) - 1):
        faces.append((i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_stalactites(rng):
    limestone = [material("Calcário | cinza quente", (0.16, 0.17, 0.17)),
                 material("Calcário | face clara", (0.23, 0.23, 0.22)),
                 material("Calcário | sombra fria", (0.09, 0.11, 0.12)),
                 material("Calcário | bege mineral", (0.20, 0.17, 0.13))]

    # Um fragmento de teto em arco sustenta as pontas descendentes; estalagmites
    # sobem da mesma base, formando uma coluna natural compacta de caverna.
    ellipsoid("Base de calcário irregular", (0, 0, 0.075),
              (0.34, 0.31, 0.085), limestone[2], 14, 8)
    rock_shelf(rng, limestone[0])

    # Três pontas robustas e pequenas agulhas secundárias apontam para cima.
    for i, (x, y, h, r) in enumerate((
        (-0.10, -0.06, 0.79, 0.125), (0.12, 0.045, 0.91, 0.145),
        (0.02, 0.16, 0.62, 0.105), (-0.22, 0.12, 0.38, 0.085),
        (0.23, -0.12, 0.46, 0.095), (-0.20, -0.18, 0.30, 0.07),
    )):
        irregular_spike("Estalagmite %02d" % i, x, y, 0.13, h, r,
                        rng.choice(limestone), rng, upward=True,
                        lean=rng.uniform(-0.07, 0.07))

    # Estalactites de comprimentos diversos pendem do recorte de teto.
    for i, (x, y, h, r) in enumerate((
        (-0.22, -0.15, 0.55, 0.10), (-0.06, -0.03, 0.76, 0.125),
        (0.15, -0.14, 0.47, 0.095), (0.24, 0.11, 0.63, 0.11),
        (-0.12, 0.20, 0.38, 0.08), (0.04, 0.12, 0.51, 0.085),
    )):
        irregular_spike("Estalactite %02d" % i, x, y, 1.00, h, r,
                        rng.choice(limestone), rng, upward=False,
                        lean=rng.uniform(-0.055, 0.055))

    # Pequenas lascas escuras encostadas à base ajudam a ancorar a formação.
    for i in range(5):
        x, y = rng.uniform(-0.27, 0.27), rng.uniform(-0.23, 0.23)
        chip = ellipsoid("Lasca calcária baixa %02d" % i, (x, y, 0.10),
                         (rng.uniform(0.045, 0.085), 0.045, 0.027),
                         limestone[2], 9, 6)
        for face in chip.data.polygons:
            face.use_smooth = False


def build_fissure(rng):
    # Tons de terra queimada e rocha vulcânica: a peça lê como solo, não como
    # uma pedra oval flutuando sobre o tabuleiro.
    earth = [material("Solo | carvão quente", (0.145, 0.086, 0.047)),
             material("Solo | terra queimada", (0.18, 0.103, 0.055)),
             material("Solo | cinza ferrugem", (0.205, 0.122, 0.066)),
             material("Solo | ardósia terrosa", (0.155, 0.112, 0.078)),
             material("Solo | face ocre", (0.22, 0.138, 0.074))]
    side = material("Borda do terreno | basalto", (0.075, 0.065, 0.055))
    crack = material("Rachadura | sombra profunda", (0.018, 0.012, 0.008))
    ember = material("Rachadura | brasa discreta", (0.28, 0.052, 0.009),
                     roughness=0.72, emission=(0.55, 0.055, 0.004),
                     emission_strength=0.28)

    # Lâmina de terreno irregular, achatada e facetada, com espessura mínima.
    # Um contorno quadrado orgânico ajuda a alinhar a decoração ao plano do chão.
    outline = [(-0.39, -0.29), (-0.29, -0.36), (-0.08, -0.35),
               (0.13, -0.37), (0.34, -0.30), (0.39, -0.12),
               (0.35, 0.10), (0.39, 0.27), (0.20, 0.35),
               (-0.02, 0.33), (-0.26, 0.37), (-0.39, 0.22),
               (-0.35, 0.02)]
    verts = [(x, y, 0.055) for x, y in outline]
    verts += [(x, y, 0.12 + rng.uniform(-0.008, 0.008)) for x, y in outline]
    verts.append((0, 0, 0.12))
    n = len(outline)
    faces, material_ids = [], []
    for i in range(n):
        faces.append((i, (i + 1) % n, n + (i + 1) % n, n + i))
        material_ids.append(len(earth))
        faces.append((2 * n, n + i, n + (i + 1) % n))
        material_ids.append(1)
    mesh = bpy.data.meshes.new("Terreno rachado | malha baixa")
    mesh.from_pydata(verts, [], faces)
    for mat in earth + [side]:
        mesh.materials.append(mat)
    mesh.update()
    ground = bpy.data.objects.new("Chão rachado | terra vulcânica", mesh)
    bpy.context.collection.objects.link(ground)
    for poly, mat_id in zip(mesh.polygons, material_ids):
        poly.material_index = mat_id

    # Rachadura principal sinuosa e três ramificações; bordas ocres quebradas
    # emolduram o fundo escuro com um brilho de brasa estreito e controlado.
    fissures = [
        ([(-0.37, -0.18), (-0.28, -0.12), (-0.20, -0.065),
          (-0.11, 0.015), (-0.025, 0.04), (0.07, 0.005),
          (0.15, 0.065), (0.23, 0.11), (0.34, 0.17)],
         [0.004, 0.018, 0.026, 0.020, 0.032, 0.018, 0.025, 0.020, 0.003]),
        ([(-0.13, 0.0), (-0.19, 0.09), (-0.24, 0.18), (-0.31, 0.25)],
         [0.012, 0.018, 0.012, 0.002]),
        ([(0.04, 0.025), (0.02, 0.13), (0.07, 0.23), (0.12, 0.31)],
         [0.014, 0.022, 0.014, 0.002]),
        ([(0.13, 0.052), (0.18, -0.035), (0.27, -0.095), (0.34, -0.17)],
         [0.010, 0.020, 0.012, 0.002]),
    ]
    for i, (points, widths) in enumerate(fissures):
        ground_ribbon("Fenda escura ramificada %02d" % i,
                      points, widths, crack, 0.124)
        inner = [w * 0.12 for w in widths]
        ground_ribbon("Filete de brasa %02d" % i,
                      points, inner, ember, 0.125)

    # Fragmentos baixos nas bordas, como placas de chão que se ergueram ao rachar.
    for i, (x, y, sx, sy) in enumerate((
        (-0.28, -0.22, 0.11, 0.065), (-0.13, -0.27, 0.09, 0.055),
        (0.13, -0.27, 0.12, 0.065), (0.30, -0.20, 0.09, 0.06),
        (-0.31, 0.17, 0.085, 0.06), (0.28, 0.24, 0.095, 0.06),
    )):
        shard = ellipsoid("Placa quebrada baixa %02d" % i,
                          (x, y, 0.125), (sx, sy, 0.022),
                          earth[(i + 1) % len(earth)], 8, 5)
        shard.rotation_euler[2] = rng.uniform(-0.45, 0.45)
        for face in shard.data.polygons:
            face.use_smooth = False

    # Nuvens de vapor arredondadas e translúcidas. Cada uma sobe e oscila num
    # ciclo próprio; o mixer GLB do tabuleiro reproduz os clipes em loop.
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 48
    scene.render.fps = 24
    emitters = [(-0.17, -0.045), (-0.015, 0.025),
                (0.16, 0.08), (-0.24, 0.19)]
    for i, (x, y) in enumerate(emitters):
        fog = material("Vapor animado %02d" % i,
                       (0.54 + i * 0.025, 0.58 + i * 0.018,
                        0.57 + i * 0.015), roughness=1.0)
        shader = fog.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Alpha"].default_value = 0.34
        fog.diffuse_color = (*fog.diffuse_color[:3], 0.34)
        if hasattr(fog, "surface_render_method"):
            fog.surface_render_method = "DITHERED"
        cloud_data = bpy.data.metaballs.new("Vapor orgânico %02d" % i)
        cloud_data.resolution = 0.045
        cloud_data.render_resolution = 0.025
        cloud_data.threshold = 0.34
        plume = bpy.data.objects.new("Vapor contínuo %02d" % i, cloud_data)
        bpy.context.collection.objects.link(plume)
        for j, (co, radius, stretch) in enumerate((
            ((0.0, 0.0, 0.00), 0.069, (0.86, 0.80, 0.82)),
            ((-0.026, 0.006, 0.052), 0.074, (0.78, 0.76, 1.02)),
            ((0.028, 0.010, 0.105), 0.062, (0.76, 0.74, 1.08)),
            ((0.012, 0.020, 0.150), 0.042, (0.76, 0.75, 1.14)),
        )):
            element = cloud_data.elements.new()
            element.co = co
            element.radius = radius
            element.size_x, element.size_y, element.size_z = stretch
        bpy.ops.object.select_all(action="DESELECT")
        plume.select_set(True)
        bpy.context.view_layer.objects.active = plume
        bpy.ops.object.convert(target="MESH")
        plume = bpy.context.object
        assign(plume, fog)
        for face in plume.data.polygons:
            face.use_smooth = True
        plume.name = "Vapor contínuo %02d" % i
        plume.location = (x, y, 0.13 + i * 0.025)
        # A deriva lateral e a subida são curtas para evitar saltos aparentes
        # quando o clipe reinicia; os emissores têm fases desencontradas.
        base_z = 0.13 + i * 0.025
        for frame, dz, dx in ((1, 0.0, 0.0),
                              (24, 0.10, 0.035),
                              (48, 0.0, 0.0)):
            plume.location = (x + dx, y, base_z + dz)
            plume.keyframe_insert(data_path="location", frame=frame)


def build_geiser_lava(rng):
    """Miniatura 1x1 com leito vulcânico e erupção curta e intermitente."""
    basalt = [material("Gêiser | basalto carvão", (0.055, 0.052, 0.049)),
              material("Gêiser | basalto oxidado", (0.105, 0.063, 0.043)),
              material("Gêiser | cinza mineral", (0.115, 0.105, 0.091))]
    fissure = material("Gêiser | fissura escura", (0.018, 0.012, 0.009))
    crater = material("Gêiser | cavidade", (0.012, 0.008, 0.006))
    pool = material("Gêiser | magma em repouso", (0.20, 0.018, 0.003),
                    roughness=0.9, emission=(0.48, 0.018, 0.001),
                    emission_strength=0.38)
    lava = material("Gêiser | lava da erupção", (0.32, 0.026, 0.003),
                    roughness=0.82, emission=(0.62, 0.028, 0.001),
                    emission_strength=0.72)
    core = material("Gêiser | centro incandescente", (0.55, 0.085, 0.004),
                    roughness=0.78, emission=(0.72, 0.09, 0.002),
                    emission_strength=0.8)

    # Leito baixo e irregular, sem a borda circular de um vulcão em miniatura.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1,
                                          location=(0, 0, 0.058))
    ground = bpy.context.object
    ground.name = "Gêiser | rocha vulcânica integrada ao chão"
    ground.scale = (0.435, 0.415, 0.064)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for vert in ground.data.vertices:
        x, y, z = vert.co
        angle = math.atan2(y, x)
        radial = rng.uniform(0.91, 1.08) + 0.045 * math.sin(angle * 3 + 0.7)
        vert.co.x *= radial
        vert.co.y *= radial
        if z > 0:
            vert.co.z *= rng.uniform(0.90, 1.10)
    assign(ground, basalt[0])
    for face in ground.data.polygons:
        face.use_smooth = True

    # Camadas de rocha partidas e cinza acumulada quebram a simetria da borda.
    for i, (x, y, sx, sy, height) in enumerate((
        (-0.31, -0.19, 0.095, 0.063, 0.032),
        (0.28, -0.23, 0.087, 0.068, 0.029),
        (-0.34, 0.12, 0.074, 0.058, 0.026),
        (0.10, 0.32, 0.078, 0.047, 0.024),
        (0.34, 0.03, 0.074, 0.051, 0.023),
    )):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=1, location=(x, y, 0.072 + height * 0.35))
        rock = bpy.context.object
        rock.name = "Gêiser | fragmento basáltico %02d" % i
        rock.scale = (sx, sy, height)
        rock.rotation_euler[2] = rng.uniform(-0.8, 0.8)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for vert in rock.data.vertices:
            vert.co *= rng.uniform(0.84, 1.13)
        assign(rock, basalt[i % len(basalt)])
        for face in rock.data.polygons:
            face.use_smooth = False

    # Rachaduras ramificadas conduzem o olhar para uma abertura baixa e escura.
    fissures = [
        [(-0.015, -0.025, 0.11), (-0.12, -0.10, 0.105), (-0.24, -0.19, 0.10), (-0.33, -0.24, 0.09)],
        [(0.015, 0.005, 0.11), (0.13, -0.06, 0.105), (0.23, -0.16, 0.10), (0.32, -0.22, 0.09)],
        [(0.0, 0.025, 0.11), (-0.04, 0.13, 0.105), (-0.02, 0.24, 0.10), (-0.08, 0.33, 0.09)],
        [(-0.02, 0.0, 0.11), (-0.14, 0.07, 0.105), (-0.24, 0.12, 0.10), (-0.32, 0.16, 0.09)],
    ]
    for i, points in enumerate(fissures):
        tapered_curve("Gêiser | rachadura mineral %02d" % i, points,
                      [0.75, 0.55, 0.34, 0.08], fissure, 0.018)
    def irregular_patch(name, rx, ry, z, mat, sides):
        verts = [(0, 0, z)]
        for j in range(sides):
            angle = math.tau * j / sides
            r = rng.uniform(0.82, 1.12)
            verts.append((rx * r * math.cos(angle),
                          ry * r * math.sin(angle),
                          z + rng.uniform(-0.003, 0.003)))
        faces = [(0, 1 + j, 1 + ((j + 1) % sides)) for j in range(sides)]
        mesh = bpy.data.meshes.new(name + " mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    irregular_patch("Gêiser | cavidade irregular", 0.14, 0.105,
                    0.116, crater, 13)
    magma_rest = ellipsoid("Gêiser | magma baixo no repouso", (0.005, -0.003, 0.121),
                           (0.052, 0.028, 0.0035), pool, 18, 8)
    magma_rest.rotation_euler[2] = -0.28
    # Lascas próximas ao respiradouro formam um rebordo partido, sem aro simétrico.
    for i, (x, y, sx, sy, sz) in enumerate((
        (-0.13, -0.035, 0.060, 0.043, 0.032),
        (0.115, -0.065, 0.051, 0.040, 0.028),
        (-0.045, 0.12, 0.052, 0.037, 0.025),
    )):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=1, location=(x, y, 0.115 + sz * 0.30))
        lip = bpy.context.object
        lip.name = "Gêiser | lasca na borda da cratera %02d" % i
        lip.scale = (sx, sy, sz)
        lip.rotation_euler[2] = rng.uniform(-0.9, 0.9)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for vert in lip.data.vertices:
            vert.co *= rng.uniform(0.84, 1.14)
        assign(lip, basalt[(i + 1) % len(basalt)])
        for face in lip.data.polygons:
            face.use_smooth = False

    # Filetes de lava escura nas fendas: brilho contido, sem neon uniforme.
    # A erupção dura menos de um segundo em um ciclo de cinco; a cratera e o
    # brilho baixo continuam visíveis no intervalo de repouso.
    jet_points = [(0, 0, 0.13), (-0.012, 0.004, 0.20),
                  (0.028, 0.018, 0.28), (0.065, 0.025, 0.35),
                  (0.045, 0.035, 0.40)]
    jet = tapered_curve("Gêiser | jato breve de lava", jet_points,
                        [0.70, 0.86, 0.58, 0.31, 0.035], lava, 0.041)
    core_points = [(x * 0.70, y, z) for x, y, z in jet_points[:3]]
    hot_core = tapered_curve("Gêiser | núcleo incandescente", core_points,
                             [0.20, 0.24, 0.08], core, 0.012)
    eruption = ((1, 0.001), (67, 0.001), (70, 0.12), (73, 0.78),
                (77, 1.0), (82, 0.82), (86, 0.18), (90, 0.001),
                (120, 0.001))
    for obj in (jet, hot_core):
        for frame, scale in eruption:
            obj.scale = (scale, scale, scale)
            obj.keyframe_insert(data_path="scale", frame=frame)

    # Poucas gotas irregulares só acompanham a janela curta da erupção.
    for i, (x, y, peak, radius) in enumerate((
        (-0.052, -0.025, 0.35, 0.009),
        (0.058, 0.020, 0.38, 0.008),
    )):
        drop_mat = material("Gêiser | gota de lava %02d" % i,
                            (0.52, 0.07, 0.006), roughness=0.8,
                            emission=(0.9, 0.055, 0.001), emission_strength=0.9)
        drop = ellipsoid("Gêiser | gota breve %02d" % i,
                         (x, y, 0.15), (radius, radius * 0.85, radius * 1.25),
                         drop_mat, 10, 6)
        for frame, z, size in ((1, 0.15, 0.001), (71 + i, 0.20, 0.001),
                               (75 + i, peak, 0.9), (80 + i, peak + 0.045, 0.72),
                               (85 + i, 0.22, 0.001), (120, 0.15, 0.001)):
            drift = 0.018 * math.sin(math.pi * frame / 120 + i * 0.8)
            drop.location = (x + drift, y, z)
            drop.scale = (size, size, size)
            drop.keyframe_insert(data_path="location", frame=frame)
            drop.keyframe_insert(data_path="scale", frame=frame)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 120
    scene.render.fps = 24


def build_fumarola(rng):
    """Respiradouro vulcânico baixo com uma rajada curta de vapor em loop."""
    basalt = material("Fumarola | basalto frio", (0.075, 0.071, 0.066))
    basalt_warm = material("Fumarola | pedra oxidada", (0.13, 0.087, 0.058))
    ash = material("Fumarola | cinza", (0.17, 0.16, 0.145))
    vent = material("Fumarola | interior", (0.018, 0.016, 0.014))
    vapor = material("Fumarola | vapor", (0.58, 0.59, 0.57), roughness=1.0)
    vapor_shader = vapor.node_tree.nodes.get("Principled BSDF")
    vapor_shader.inputs["Alpha"].default_value = 0.44
    vapor.diffuse_color = (*vapor.diffuse_color[:3], 0.44)
    if hasattr(vapor, "surface_render_method"):
        vapor.surface_render_method = "DITHERED"

    # A borda é baixa e irregular para parecer rocha quebrada no próprio piso.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1,
                                          location=(0, 0, 0.038))
    bed = bpy.context.object
    bed.name = "Fumarola | solo vulcânico"
    bed.scale = (0.405, 0.37, 0.042)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for vert in bed.data.vertices:
        angle = math.atan2(vert.co.y, vert.co.x)
        radial = rng.uniform(0.87, 1.10) + 0.060 * math.sin(angle * 4 + 0.5)
        vert.co.x *= radial
        vert.co.y *= radial
        vert.co.z *= rng.uniform(0.9, 1.1)
    assign(bed, basalt)
    for face in bed.data.polygons:
        face.use_smooth = True

    # Placas basálticas assimétricas deixam a saída de vapor exposta.
    for i, (x, y, sx, sy, sz) in enumerate((
        (-0.27, -0.13, 0.095, 0.060, 0.025),
        (0.29, -0.17, 0.080, 0.066, 0.030),
        (-0.31, 0.12, 0.068, 0.056, 0.023),
        (0.12, 0.27, 0.084, 0.052, 0.026),
        (0.34, 0.08, 0.062, 0.048, 0.021),
        (-0.06, -0.31, 0.075, 0.047, 0.022),
    )):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=1, location=(x, y, 0.044 + sz * 0.22))
        rock = bpy.context.object
        rock.name = "Fumarola | placa de basalto %02d" % i
        rock.scale = (sx, sy, sz)
        rock.rotation_euler[2] = rng.uniform(-0.9, 0.9)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for vert in rock.data.vertices:
            vert.co *= rng.uniform(0.88, 1.12)
        assign(rock, basalt_warm if i in (1, 4) else ash if i == 3 else basalt)
        for face in rock.data.polygons:
            face.use_smooth = False

    # Boca oblonga e rachaduras escuras apontam para fora em direções desiguais.
    ellipsoid("Fumarola | abertura de vapor", (0, 0, 0.082),
              (0.112, 0.078, 0.009), vent, 18, 8)
    for i, (x, y, sx, sy, sz) in enumerate((
        (-0.12, -0.045, 0.049, 0.036, 0.020),
        (0.105, -0.055, 0.045, 0.034, 0.018),
        (-0.025, 0.112, 0.052, 0.031, 0.019),
    )):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=1, location=(x, y, 0.069 + sz * 0.28))
        lip = bpy.context.object
        lip.name = "Fumarola | rocha partida da boca %02d" % i
        lip.scale = (sx, sy, sz)
        lip.rotation_euler[2] = rng.uniform(-0.75, 0.75)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(lip, basalt_warm if i == 1 else ash)
        for face in lip.data.polygons:
            face.use_smooth = False
    for i, points in enumerate((
        [(-0.05, -0.045, 0.083), (-0.12, -0.09, 0.080), (-0.21, -0.12, 0.075)],
        [(0.045, 0.035, 0.083), (0.12, 0.08, 0.080), (0.22, 0.11, 0.075)],
        [(-0.025, 0.055, 0.083), (-0.04, 0.14, 0.080), (-0.02, 0.23, 0.075)],
    )):
        tapered_curve("Fumarola | fissura %02d" % i, points,
                      [0.62, 0.32, 0.06], vent, 0.012)

    # Uma nuvem orgânica aparece por menos de um segundo em um ciclo de cinco.
    cloud_data = bpy.data.metaballs.new("Fumarola | nuvem em rajada")
    cloud_data.resolution = 0.055
    cloud_data.render_resolution = 0.035
    cloud_data.threshold = 0.58
    cloud = bpy.data.objects.new("Fumarola | nuvem intermitente", cloud_data)
    bpy.context.collection.objects.link(cloud)
    for co, radius, stretch in (
        ((0.00, 0.00, 0.02), 0.112, (0.82, 0.78, 1.02)),
        ((-0.055, 0.008, 0.105), 0.098, (0.78, 0.82, 1.08)),
        ((0.045, 0.014, 0.19), 0.11, (0.84, 0.78, 1.08)),
        ((-0.025, 0.018, 0.28), 0.083, (0.78, 0.83, 1.10)),
        ((0.04, 0.022, 0.35), 0.064, (0.80, 0.76, 1.12)),
    ):
        element = cloud_data.elements.new()
        element.co = co
        element.radius = radius
        element.size_x, element.size_y, element.size_z = stretch
    bpy.ops.object.select_all(action="DESELECT")
    cloud.select_set(True)
    bpy.context.view_layer.objects.active = cloud
    bpy.ops.object.convert(target="MESH")
    cloud = bpy.context.object
    assign(cloud, vapor)
    for face in cloud.data.polygons:
        face.use_smooth = True
    cloud.name = "Fumarola | nuvem intermitente"

    # O sopro sobe, se dissipa e permanece invisível durante o repouso.
    puff_keys = ((1, 0.001, 0.0), (76, 0.001, 0.0), (79, 0.24, 0.015),
                 (83, 0.78, 0.075), (87, 1.0, 0.14), (90, 0.72, 0.21),
                 (94, 0.001, 0.29), (120, 0.001, 0.29))
    for frame, scale, rise in puff_keys:
        cloud.scale = (scale, scale, scale)
        cloud.location = (0.0, 0.0, rise)
        cloud.keyframe_insert(data_path="scale", frame=frame)
        cloud.keyframe_insert(data_path="location", frame=frame)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 120
    scene.render.fps = 24


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene(slug):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.065, 0.075, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.24
    for name, loc, energy, size, color in (
        ("Luz âmbar", (1.0, -1.4, 2.0), 38, 1.25, (1.0, 0.76, 0.48)),
        ("Preenchimento azul", (-1.4, -0.4, 1.3), 24, 1.2, (0.63, 0.79, 0.93)),
        ("Recorte mineral", (0.15, 1.1, 1.6), 29, 0.9, (0.79, 0.87, 1.0)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, 0.48 if slug == "estalactites_estalagmites" else 0.20))
    bpy.ops.object.camera_add(location=(1.45, -2.35, 1.8))
    camera = bpy.context.object
    camera.name = "Câmera da miniatura"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.72 if slug == "estalactites_estalagmites" else 1.45
    point_at(camera, (0, 0, 0.58 if slug == "estalactites_estalagmites" else 0.28))
    scene.camera = camera
    scene.render.filepath = str(OUT / (slug + "_preview.png"))


def merge_by_material():
    for mat in list(bpy.data.materials):
        group = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and mat in obj.data.materials[:]]
        if len(group) < 2:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        bpy.ops.object.join()
        group[0].name = "Caverna | " + mat.name


def export_one(slug, builder, seed, preview_frame=1):
    clear_scene()
    builder(random.Random(seed))
    merge_by_material()
    setup_scene(slug)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (slug + ".blend")))
    bpy.context.scene.render.filepath = str(OUT / (slug + "_idle_preview.png"))
    bpy.ops.render.render(write_still=True)
    bpy.context.scene.frame_set(preview_frame)
    bpy.context.scene.render.filepath = str(OUT / (slug + "_preview.png"))
    bpy.ops.render.render(write_still=True)
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.filepath = str(OUT / (slug + ".png"))
    bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (slug + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", slug, "meshes=", len(meshes))


def build():
    export_one("estalactites_estalagmites", build_stalactites, 81021)
    export_one("fenda_fumegante", build_fissure, 81037)


if __name__ == "__main__":
    build()
