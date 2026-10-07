"""Gera um relevo mural de uma pequena gruta entre rochas."""
from __future__ import annotations

import math
import random
import shutil
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)
SLUG = "gruta_parede"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for data in collection:
            if data.users == 0:
                collection.remove(data)


def material(name, color, roughness=.92, bump=.1, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1)
        strength = bsdf.inputs.get("Emission Strength")
        if strength:
            strength.default_value = .22
    if bump:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 32
        noise.inputs["Detail"].default_value = 3
        relief = nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = bump
        relief.inputs["Distance"].default_value = .012
        links.new(noise.outputs["Fac"], relief.inputs["Height"])
        links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def extruded_profile(name, outline, y_front, y_back, mat):
    count = len(outline)
    verts = [(x, y_front, z) for x, z in outline]
    verts += [(x, y_back, z) for x, z in outline]
    faces = [tuple(range(count)), tuple(range(2 * count - 1, count - 1, -1))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count)
                 for i in range(count))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def rock(name, pos, scale, mat, rng, segments=12):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1,
                                          location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for vertex in obj.data.vertices:
        vertex.co *= rng.uniform(.84, 1.14)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = False
    return obj


def curve(name, points, mat, radius=.004):
    data = bpy.data.curves.new(name + " curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def arch_outline(cx, bottom, rx, height, steps=12):
    points = [(cx - rx, bottom), (cx - rx, bottom + height * .48)]
    for index in range(steps + 1):
        angle = math.pi - math.pi * index / steps
        wobble = 1 + .035 * math.sin(index * 2.3)
        points.append((cx + rx * math.cos(angle) * wobble,
                       bottom + height * .48 + height * .52 * math.sin(angle) * wobble))
    points.extend(((cx + rx, bottom + height * .48), (cx + rx, bottom)))
    return points


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.035, .043, .041, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .28
    target = Vector((0, 0, .47))
    bpy.ops.object.camera_add(location=(1.02, 2.55, 1.02))
    camera = bpy.context.object
    camera.name = "Câmera do relevo mural"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.20
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for name, loc, energy, size, color in (
        ("Luz quente da clareira", (.6, 1.7, 1.6), 62, .9, (1.0, .78, .54)),
        ("Luz fria difusa", (-1.2, 1.0, .9), 39, 1.0, (.64, .76, .86)),
        ("Recorte suave", (.3, -.8, 1.25), 32, .8, (.91, .56, .34)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()


def build(seed=44172):
    rng = random.Random(seed)
    frame = [material("Moldura de calcário %02d" % i, color, .94, .12)
             for i, color in enumerate(((.36, .31, .25), (.46, .40, .32),
                                        (.29, .27, .23), (.40, .35, .28)))]
    cliff = [material("Rocha do painel %02d" % i, color, .96, .14)
             for i, color in enumerate(((.34, .30, .25), (.43, .37, .30),
                                        (.27, .26, .23), (.49, .40, .29)))]
    inner_rock = [material("Rocha em sombra %02d" % i, color, .98, .12)
                  for i, color in enumerate(((.16, .15, .13), (.23, .20, .16),
                                             (.28, .24, .19)))]
    deep = material("Interior escuro da gruta", (.035, .032, .028), .99, .05)
    depth = material("Parede distante na penumbra", (.12, .10, .08), .97, .08)
    mineral = material("Veio de cristal frio", (.19, .32, .31), .34, .03,
                       emission=(.08, .24, .22))
    moss = material("Musgo na moldura", (.17, .23, .12), .98, .08)
    old_engraving = material("Inscrição apagada", (.19, .17, .14), .98, .03)

    # Mounting slab with softly chipped corners; its flat rear sits against WALL.
    outer = [(-.32, .03), (-.355, .10), (-.35, .79), (-.29, .94),
             (.28, .94), (.35, .82), (.355, .12), (.30, .03)]
    extruded_profile("Placa de pedra que emoldura a imagem", outer,
                     .025, -.045, frame[0])
    inner_panel = [(-.276, .105), (-.29, .17), (-.28, .76), (-.23, .855),
                   (.23, .855), (.28, .76), (.29, .17), (.26, .105)]
    extruded_profile("Imagem em relevo da encosta", inner_panel,
                     .051, .028, cliff[1])

    # The dark arch is a painted-looking recess in the panel, never a passage.
    mouth = arch_outline(0, .12, .205, .57)
    extruded_profile("Sombra profunda da entrada", mouth, .076, .066, deep)
    distant = arch_outline(.015, .15, .115, .40)
    extruded_profile("Parede distante no interior", distant, .082, .077, depth)
    far_shadow = arch_outline(.015, .15, .083, .32)
    extruded_profile("Sombra no fundo da gruta", far_shadow, .087, .083, deep)

    # Uneven stone lips and fallen chunks frame the opening as a miniature scene.
    for side in (-1, 1):
        for row in range(4):
            z = .18 + row * .14
            rock("Bloco irregular do portal %s %02d" % (side, row),
                 (side * (.215 + rng.uniform(-.015, .012)),
                  .095 + rng.uniform(-.014, .012), z),
                 (rng.uniform(.075, .11), .055, rng.uniform(.075, .115)),
                 rng.choice(cliff), rng)
        for index in range(3):
            rock("Estrato da encosta %s %02d" % (side, index),
                 (side * rng.uniform(.25, .29), .072,
                  .30 + index * .17 + rng.uniform(-.025, .025)),
                 (rng.uniform(.05, .09), .05, rng.uniform(.065, .11)),
                 rng.choice(frame), rng)

    for index in range(5):
        x = (index - 2) * .095
        rock("Pedra partida sobre a entrada %02d" % index,
             (x, .092 + rng.uniform(-.008, .012), .68 + .025 * math.cos(index * .9)),
             (rng.uniform(.055, .09), .06, rng.uniform(.07, .11)),
             rng.choice(cliff), rng)
    # A shallow sill and a few loose stones make the cave mouth read clearly.
    for index in range(3):
        rock("Limiar rochoso %02d" % index,
             ((index - 1) * .105, .10, .145), (.09, .055, .045),
             rng.choice(cliff), rng)

    # Fine cracks and an almost-lost carved border make the wall image feel old.
    for side in (-1, 1):
        curve("Fissura na moldura %s" % side,
              [(side*.31, .09, .24), (side*.285, .09, .29),
               (side*.30, .09, .33)], old_engraving, .003)
        rock("Mancha de musgo na borda %s" % side,
             (side*.31, .089, .18), (.036, .018, .025), moss, rng, 10)

    # A pair of tiny mineral glints provides depth far inside the illustrated cave.
    for index, x in enumerate((-.055, .068)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1,
                                              location=(x, .091, .36 + index*.055))
        crystal = bpy.context.object
        crystal.name = "Veio mineral na penumbra %02d" % index
        crystal.scale = (.014, .008, .032)
        crystal.data.materials.append(mineral)
        for face in crystal.data.polygons:
            face.use_smooth = False

    # A restrained shallow carving identifies the plaque without turning it into a sign.
    curve("Marca antiga no rodapé", [(-.12, .079, .075), (0, .079, .065),
         (.12, .079, .075)], old_engraving, .003)


def build_natural_decal():
    """Use the photoreal cave cutout as the wall image and the GLB material."""
    image_path = OUT / (SLUG + "_textura.png")
    cave_image = bpy.data.images.load(str(image_path), check_existing=True)
    cave_image.pack()
    mat = bpy.data.materials.new("Entrada de caverna natural | imagem com alfa")
    mat.use_nodes = True
    mat.surface_render_method = "DITHERED"
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .95
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Recorte fotorrealista da gruta"
    texture.image = cave_image
    texture.interpolation = "Linear"
    texture.extension = "CLIP"
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])

    # A square, transparent wall decal preserves the natural silhouette.
    verts = [(-.46, .06, .04), (-.46, .06, .96),
             (.46, .06, .96), (.46, .06, .04)]
    mesh = bpy.data.meshes.new("Recorte vertical da gruta")
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.materials.append(mat)
    mesh.update()
    uv = mesh.uv_layers.new(name="UV da imagem natural")
    coordinates = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 0)}
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv.data[loop_index].uv = coordinates[vertex_index]
    obj = bpy.data.objects.new("Gruta natural | decal de parede", mesh)
    bpy.context.collection.objects.link(obj)


def main():
    clear_scene()
    source_png = OUT / (SLUG + "_textura.png")
    shutil.copyfile(source_png, OUT / (SLUG + ".png"))
    build_natural_decal()
    setup_scene()
    scene = bpy.context.scene
    scene.render.filepath = str(OUT / (SLUG + "_preview.png"))
    scene.render.film_transparent = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (SLUG + ".blend")))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_materials="EXPORT")
    print("ASSET_EXPORT", SLUG, "meshes=", len(meshes))


if __name__ == "__main__":
    main()
