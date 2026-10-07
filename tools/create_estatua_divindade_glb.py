"""Gera uma estátua de divindade para templo em PNG e GLB."""
from math import cos, pi, sin
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
BLEND = OUT / "estatua_divindade.blend"
GLB = OUT / "estatua_divindade.glb"
PNG = OUT / "estatua_divindade.png"
PREVIEW = OUT / "estatua_divindade_preview.png"


def material(name, color, metallic=0.0, roughness=.88, bump_distance=.014):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if bump_distance:
        noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 32
        noise.inputs["Detail"].default_value = 4
        noise.inputs["Roughness"].default_value = .78
        bump = mat.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .18
        bump.inputs["Distance"].default_value = bump_distance
        mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        mat.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def finish(obj, name, mat, bevel=0):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("worn carved edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def block(name, location, size, mat, bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel)


def sphere(name, location, scale, mat, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat)


def cylinder(name, location, radius, depth, mat, vertices=32, bevel=.004):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=location)
    return finish(bpy.context.object, name, mat, bevel)


def rod(name, start, end, radius, mat, tip=0, vertices=12):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                    radius2=tip or radius, depth=delta.length,
                                    location=(a + b) * .5)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat, min(radius * .12, .004))


def torus(name, location, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10,
                                     major_radius=major, minor_radius=minor,
                                     location=location)
    obj = bpy.context.object
    if rotation is not None:
        obj.rotation_euler = rotation
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat)


def robe_mesh(stone):
    """A continuous, gently fluted robe, wider at the hem and shoulders."""
    levels = [(.245,.235,.17),(.285,.23,.166),(.36,.218,.16),
              (.47,.184,.143),(.60,.154,.127),(.75,.142,.12),
              (.88,.153,.13),(.99,.175,.14),(1.075,.13,.115)]
    n = 64
    verts, faces = [], []
    for ring, (z, rx, ry) in enumerate(levels):
        for i in range(n):
            t = 2*pi*i/n
            pleat = .009*cos(8*t + .25*ring) + .003*cos(4*t)
            verts.append(((rx+pleat)*cos(t), -.005+(ry+pleat*.65)*sin(t), z))
    for ring in range(len(levels)-1):
        for i in range(n):
            j = (i+1)%n
            faces.append((ring*n+i, ring*n+j, (ring+1)*n+j, (ring+1)*n+i))
    faces.append(tuple(range(n-1,-1,-1)))
    faces.append(tuple((len(levels)-1)*n+i for i in range(n)))
    mesh = bpy.data.meshes.new("One-piece carved robe mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Long fluted temple robe", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(stone)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def build_statue(stone, stone_light, recess, gold):
    # Stepped square plinth occupies less than one map tile.
    block("Square sandstone footing", (0,0,.09), (.78,.70,.18), stone, .025)
    block("Carved plinth upper course", (0,0,.215), (.67,.59,.065), stone_light, .012)
    block("Inscribed pedestal face", (0,-.303,.145), (.34,.012,.045), recess, .005)
    # Three shallow chisel marks suggest a sacred sun seal without writing.
    torus("Pedestal sun seal", (0,-.313,.145), .022, .0035, gold, (pi/2,0,0))
    for side in (-1,1):
        sphere("Pedestal seal point", (side*.033,-.314,.145), (.004,.003,.004), gold, 12, 8)

    robe_mesh(stone)
    # Neck, shoulders, and bent forearms meet at a small votive orb.
    cylinder("Carved neck", (0,-.006,1.105), .061, .12, stone, 24, .009)
    sphere("Mantled shoulders", (0,-.01,1.005), (.158,.116,.088), stone)
    for side in (-1,1):
        shoulder = (side*.145,-.035,1.005)
        elbow = (side*.18,-.105,.82)
        wrist = (side*.07,-.185,.685)
        rod("Draped sleeve upper fold", shoulder, elbow, .046, stone, .034, 16)
        sphere("Sleeve elbow", elbow, (.043,.041,.047), stone)
        rod("Draped sleeve lower fold", elbow, wrist, .035, stone, .024, 16)
        sphere("Sculpted hand", (side*.047,-.188,.656), (.036,.028,.046), stone_light)
        for digit in range(3):
            dx = side*(.024 + digit*.013)
            rod("Carved finger", (dx,-.209,.654), (dx+side*.003,-.221,.622),
                .007, stone_light, .004, 8)
    sphere("Small votive orb", (0,-.217,.674), (.029,.026,.029), gold)
    torus("Orb incised ring", (0,-.239,.674), .017, .0025, stone_light,
          (pi/2,0,0))

    # Head is proportioned as a calm adult face, with quiet carved features.
    sphere("Serene sculpted head", (0,-.018,1.245), (.112,.091,.133), stone,
           40, 28)
    sphere("Sculpted hair cap", (0,.004,1.331), (.105,.078,.045), stone)
    for side in (-1,1):
        sphere("Carved ear", (side*.105,-.018,1.242), (.019,.021,.035), stone)
        # Tiny recessed eyes and soft brow planes remain part of the stone face.
        sphere("Closed eye shadow", (side*.044,-.100,1.247), (.014,.004,.004),
               recess, 16, 10)
        brow = sphere("Calm brow plane", (side*.046,-.099,1.269),
                      (.040,.009,.008), stone_light, 20, 12)
        brow.rotation_euler[1] = side*pi/18
        sphere("Hair lock beside face", (side*.097,-.053,1.255),
               (.021,.034,.074), stone_light, 20, 12)
    sphere("Nose bridge relief", (0,-.105,1.237), (.014,.015,.037),
           stone_light, 20, 12)
    sphere("Nose tip relief", (0,-.113,1.216), (.018,.012,.013), stone,
           18, 10)
    sphere("Mouth crease", (0,-.109,1.196), (.022,.004,.0035), recess,
           16, 8)
    # Subtle forehead mark and necklace tie the figure to a temple pantheon.
    sphere("Forehead sun mark", (0,-.108,1.294), (.006,.002,.008), gold, 16, 10)
    torus("Sun medallion setting", (0,-.142,.963), .031, .004, gold,
          (pi/2,0,0))
    sphere("Sun medallion center", (0,-.146,.963), (.009,.004,.009), gold)

    # A carved solar halo stands behind the head with narrow radial rays.
    torus("Stone halo outer ring", (0,.062,1.255), .188, .017, stone_light,
          (pi/2,0,0))
    torus("Gilded halo inner inlay", (0,.057,1.255), .158, .0045, gold,
          (pi/2,0,0))
    for i in range(12):
        a = 2*pi*i/12
        x1,z1 = .193*cos(a),1.255+.193*sin(a)
        x2,z2 = .237*cos(a),1.255+.237*sin(a)
        rod("Halo chisel ray", (x1,.06,z1), (x2,.06,z2), .008, stone_light,
            .002, 8)


def setup_render():
    scene = bpy.context.scene
    target = Vector((0,-.005,.78))
    bpy.ops.object.camera_add(location=(2.1,-3.4,2.05))
    camera = bpy.context.object
    camera.name = "Temple statue showcase camera"
    camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.92
    scene.camera = camera
    for name, location, energy, color, size in (
        ("Warm temple key", (1.1,-2.3,2.8), 150, (1,.79,.56), 1.3),
        ("Cool stone fill", (-1.7,-1.0,1.5), 82, (.62,.73,1), 1.1),
        ("Halo rim", (.4,1.0,2.0), 110, (1,.48,.20), .75),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = size
        lamp.data.color = color
        lamp.rotation_euler = (target-lamp.location).to_track_quat("-Z","Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.018,.022,.032,1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .2


def merge_static():
    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            key = obj.data.materials[0].name if obj.data.materials else "unmaterialed"
            groups.setdefault(key, []).append(obj)
    for key, objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        objects[0].name = "Temple deity statue - " + key


def fuse_carved_stone(stone):
    """Unify the robe, head, limbs, and lower plinth into one carved stone form."""
    pieces = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"
              and obj.data.materials and obj.data.materials[0] == stone]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in pieces:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    body = bpy.context.object
    body.name = "Single fused limestone statue and lower plinth"
    remesh = body.modifiers.new("unify hand-carved limestone", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = .0045
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = body.modifiers.new("soften joins between carved forms", "SMOOTH")
    smooth.factor = .5
    smooth.iterations = 2
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for face in body.data.polygons:
        face.use_smooth = True


def add_preview_tile():
    tile = material("Preview only temple floor", (.12,.125,.13), .0, .96, 0)
    block("Preview only flagstone tile", (0,0,-.035), (1,1,.07), tile, .018)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    stone = material("Aged warm limestone", (.40,.34,.245), 0, .96, .022)
    stone_light = material("Worn carved limestone edges", (.52,.445,.335), 0, .94, .016)
    recess = material("Deep chisel recess", (.12,.095,.065), 0, 1, 0)
    gold = material("Muted votive gold", (.42,.245,.075), .58, .46, .006)
    build_statue(stone, stone_light, recess, gold)
    fuse_carved_stone(stone)
    setup_render()
    scene = bpy.context.scene
    scene.render.filepath = str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)

    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 1.64
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)

    merge_static()
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB",
                              use_selection=True, export_apply=True)
    # The one-tile context is only for the preview and never enters the game model.
    add_preview_tile()
    scene.render.film_transparent = False
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.camera.data.ortho_scale = 1.92
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    print("Created", GLB)


if __name__ == "__main__":
    main()
