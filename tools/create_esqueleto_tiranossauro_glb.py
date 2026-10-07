"""Gera a miniatura de um esqueleto de tiranossauro tombado (PNG/GLB)."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "esqueleto_tiranossauro"


def material(name, color, roughness=.88, bump=.08):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if bump:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 34
        noise.inputs["Detail"].default_value = 3
        relief = nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = bump
        relief.inputs["Distance"].default_value = .012
        links.new(noise.outputs["Fac"], relief.inputs["Height"])
        links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def ellipsoid(name, location, scale, mat, segments=20, rings=12, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = smooth
    return obj


def bone(name, points, radii, mat, bevel=.04, resolution=8):
    curve = bpy.data.curves.new(name + " curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
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
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def tooth(name, base, tip, radius, mat):
    start, end = Vector(base), Vector(tip)
    direction = end - start
    midpoint = (start + end) * .5
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius, radius2=.001,
                                   depth=direction.length, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Desgaste suave nas pontas", "BEVEL")
    bevel.width = .004
    bevel.segments = 2
    obj.modifiers.new("Normais de superfície", "WEIGHTED_NORMAL")
    return obj


def make_skeleton(rng, bone_mats, dark, teeth):
    ivory, pale, ochre = bone_mats
    # A long, irregular spine and tapering tail establish the animal's scale.
    spine_x = [1.05, .86, .67, .48, .29, .10, -.09, -.28, -.47, -.66,
               -.85, -1.04, -1.23, -1.42, -1.60, -1.77, -1.93, -2.08]
    for i, x in enumerate(spine_x):
        t = i / (len(spine_x)-1)
        width = .105 * (1-t) ** 1.15 + .020
        z = .105 + .018 * math.sin(i * .83)
        ellipsoid("Vértebra da coluna %02d" % i, (x, .015, z),
                  (width * 1.23, width, width * .78),
                  (pale, ivory, ochre)[i % 3], 16, 10, False)
        if i < 10:
            ellipsoid("Processo espinhoso %02d" % i,
                      (x, .015, z + width * .53),
                      (width * .34, width * .42, width * .75),
                      ivory if i % 2 else pale, 12, 8, False)
    # The neural canal ridge ties individual vertebrae into one continuous
    # animal silhouette and the thinner tail section remains readable at map scale.
    bone("Coluna vertebral contínua", [(1.02, .015, .095), (.58, .015, .105),
                                        (.12, .015, .09), (-.35, .015, .095),
                                        (-.82, .015, .09), (-1.28, .015, .075),
                                        (-1.72, .015, .065), (-2.13, .015, .045)],
         [1.15, 1.05, .92, .78, .62, .46, .29, .08], pale, .036)
    # Rib pairs flare from the thoracic spine. Several lie partly broken.
    for i, x in enumerate((.57, .37, .17, -.03, -.23, -.43, -.63, -.81)):
        z = .115 + .015 * math.sin(i * .8)
        spread = .46 - i * .025
        mat = (pale, ivory, ochre)[i % 3]
        for side in (-1, 1):
            bend = .035 * (i % 2)
            points = [(x, .02, z), (x-.045, side*.15, z+.025),
                      (x-.10+bend, side*(spread*.75), z+.018),
                      (x-.06, side*spread, .035)]
            bone("Costela %02d %s" % (i, side), points,
                 [1.10, .95, .76, .48], mat, .035 if i < 4 else .029)
    bone("Esterno estreito", [(.52, 0, .045), (.22, 0, .052),
                               (-.10, 0, .048), (-.40, 0, .045)],
         [.65, 1, .82, .42], ochre, .040)
    # Shoulder and pelvis are broad, recognizable bone structures.
    ellipsoid("Cintura escapular", (.69, .015, .12), (.22, .34, .075), ochre, 16, 10, False)
    for side in (-1, 1):
        bone("Clavícula %s" % side,
             [(.82, 0, .16), (.65, side*.20, .14), (.42, side*.29, .09)],
             [1, .8, .45], pale, .037)
    bone("Arco do ílio esquerdo", [(-.78, .02, .15), (-.89, -.20, .18),
                                    (-1.12, -.33, .15), (-1.27, -.22, .10)],
         [1, .92, .72, .35], ivory, .060)
    bone("Arco do ílio direito", [(-.78, .02, .15), (-.89, .20, .18),
                                   (-1.12, .33, .15), (-1.27, .22, .10)],
         [1, .92, .72, .35], pale, .058)
    bone("Púbis da bacia", [(-1.14, -.22, .075), (-.93, 0, .055),
                             (-1.14, .22, .075)], [1, .78, .52], ochre, .043)
    for side in (-1, 1):
        bone("Ílio da bacia %s" % side,
             [(-.90, .02, .15), (-1.03, side*.27, .16), (-1.20, side*.32, .105)],
             [1.0, .72, .30], pale, .047)
        # Powerful hind legs are folded and crossed beside the pelvis.
        hip = (-.98, side*.22, .12)
        knee = (-1.30, side*.44, .085)
        ankle = (-1.00, side*.53, .055)
        bone("Fêmur robusto %s" % side,
             [hip, (-1.12, side*.34, .17), knee], [1, .82, .63],
             ivory if side == 1 else pale, .067)
        ellipsoid("Rótula %s" % side, knee, (.095, .09, .068), ochre, 16, 9, False)
        bone("Tíbia dobrada %s" % side,
             [knee, (-1.16, side*.52, .10), ankle], [1, .72, .43], pale, .045)
        for toe in range(3):
            sy = side * (.50 + toe*.065)
            start = (-1.00, sy, .06)
            end = (-.81 - .04*(toe == 1), sy + side*.035, .035)
            bone("Falange do pé %s %s" % (side, toe),
                 [start, (-.91, sy, .045), end], [1, .65, .22], ivory, .025)
            tooth("Garra do pé %s %s" % (side, toe), end,
                  (end[0]+.09, end[1]+side*.018, .008), .022, ochre)
    # Tiny forelimbs, each with two long fingers and hooked claws.
    for side in (-1, 1):
        bone("Braço curto %s" % side,
             [(.76, side*.23, .16), (.93, side*.34, .11), (.91, side*.43, .075)],
             [1, .72, .43], ochre, .031)
        for finger in range(2):
            sy = side*(.43 + finger*.045)
            end = (.79 + finger*.08, sy, .045)
            bone("Dedo dianteiro %s %s" % (side, finger),
                 [(.91, side*.43, .075), (.86, sy, .06), end],
                 [1, .68, .28], pale, .017)
            tooth("Garra dianteira %s %s" % (side, finger), end,
                  (end[0]-.035, sy+side*.015, .005), .013, ochre)

    # Skull at the right end: expanded cranium, eye sockets, open jaws and teeth.
    ellipsoid("Crânio largo", (1.13, .015, .205), (.34, .31, .19), pale, 16, 10, False)
    for side in (-1, 1):
        ellipsoid("Órbita escura %s" % side, (1.20, side*.272, .245),
                  (.105, .035, .092), dark, 20, 12)
        bone("Arco orbital %s" % side,
             [(1.04, side*.27, .30), (1.15, side*.31, .36),
              (1.29, side*.27, .32), (1.31, side*.25, .24)],
             [1, .9, .78, .60], ivory, .035)
        # Brow ridges and cheekbones give the skull a fossilized predator profile.
        bone("Crista da sobrancelha %s" % side,
             [(1.08, side*.23, .34), (1.17, side*.30, .39), (1.29, side*.23, .33)],
             [1, .82, .40], ochre, .032)
        bone("Bochecha do crânio %s" % side,
             [(.98, side*.25, .19), (1.09, side*.31, .12), (1.28, side*.25, .14)],
             [1, .75, .28], ivory, .038)
    # Upper snout and lower jaw are separated so the open mouth reads clearly.
    ellipsoid("Focinho superior", (1.48, .015, .18), (.47, .225, .125), ivory, 16, 10, False)
    bone("Borda óssea do focinho", [(1.20, -.19, .205), (1.47, -.207, .19),
                                     (1.83, -.15, .155)], [1, .82, .48], pale, .025)
    bone("Mandíbula inferior", [(1.19, -.19, .065), (1.46, -.16, .04),
                                 (1.77, -.11, .05), (1.89, -.06, .07)],
         [1, .82, .55, .28], ochre, .044)
    bone("Mandíbula distante", [(1.19, .19, .065), (1.45, .16, .04),
                                 (1.73, .11, .055)], [1, .75, .30], pale, .036)
    # Conical teeth alternate along both jaws; top teeth point down, bottom up.
    for i, x in enumerate((1.24, 1.34, 1.44, 1.55, 1.66, 1.77, 1.84)):
        y = -.19 + .055 * max(0, x-1.65)
        length = .075 if i not in (0, 6) else .10
        tooth("Dente superior %02d" % i, (x, y, .165),
              (x-.012, y-.009, .165-length), .025 if i % 2 else .029, teeth)
    for i, x in enumerate((1.29, 1.40, 1.51, 1.62, 1.73, 1.82)):
        y = -.17 + .05 * max(0, x-1.65)
        tooth("Dente inferior %02d" % i, (x, y, .065),
              (x+.008, y-.01, .065+.065), .021 if i % 2 else .025, teeth)
    # A few loose fragments and weathered chips anchor the bones without a base.
    for i, (x, y, sx, sy) in enumerate(((-1.45, -.61, .07, .045),
                                         (-.58, .57, .06, .04),
                                         (.43, -.59, .05, .035),
                                         (1.0, .48, .05, .04))):
        ellipsoid("Fragmento de osso no chão %02d" % i, (x, y, .025),
                  (sx, sy, .023), (ochre, pale, ivory)[i % 3], 12, 7, False)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in list(collection):
            if data.users == 0:
                collection.remove(data)
    rng = random.Random(740021)
    bones = [material("Marfim envelhecido", (.62, .49, .32), .9, .12),
             material("Osso gasto e claro", (.78, .68, .51), .86, .08),
             material("Osso antigo ocre", (.43, .29, .17), .95, .12)]
    dark = material("Cavidades do crânio", (.045, .028, .016), .98, .02)
    teeth = material("Dentes fossilizados", (.83, .75, .58), .67, .05)
    make_skeleton(rng, bones, dark, teeth)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.055, .047, .038, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .32
    for name, loc, energy, size, color in (
        ("Luz quente de museu", (1.0, -2.1, 3.0), 210, 2.0, (1.0, .80, .58)),
        ("Luz fria suave", (-2.0, -.2, 2.3), 135, 2.2, (.72, .82, 1.0)),
        ("Recorte do esqueleto", (1.0, 2.0, 2.8), 180, 1.8, (1.0, .68, .39)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        point_at(lamp, (0, 0, .12))
    bpy.ops.object.camera_add(location=(.35, -5.8, 8.2))
    camera = bpy.context.object
    camera.name = "Câmera de revisão da ossada"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.65
    point_at(camera, (-.05, 0, .12))
    scene.camera = camera
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))
    scene.render.film_transparent = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.render.filepath = str(OUT / (SLUG + ".png"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True,
                              export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    build()
