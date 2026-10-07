"""Gera a miniatura do sino ritualístico em PNG transparente e GLB."""
from math import cos, pi, sin
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
BLEND = OUT / "sino_ritualistico.blend"
GLB = OUT / "sino_ritualistico.glb"
PNG = OUT / "sino_ritualistico.png"
PREVIEW = OUT / "sino_ritualistico_preview.png"


def material(name, color, metallic=0.0, roughness=0.7):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    # Cast bronze and carved stone receive fine, restrained surface variation.
    if "Bronze" in name or "Stone" in name or "Wood" in name:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 24 if "Stone" in name else 38
        noise.inputs["Detail"].default_value = 3.5
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*(v * .74 for v in color), 1)
        ramp.color_ramp.elements[1].color = (*(min(1, v * 1.18 + .02) for v in color), 1)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        # Keep the authored bronze/stone hue as the exported PBR base color.
        # The former ramp hookup washed the bell out in GLB viewers; retain
        # procedural variation only as fine surface relief.
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .14 if "Bronze" in name else .22
        bump.inputs["Distance"].default_value = .012 if "Bronze" in name else .025
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def finish(obj, name, mat, bevel=0):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("worn, softened edges", "BEVEL")
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


def cylinder(name, location, radius, depth, mat, vertices=12, bevel=.004):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location)
    return finish(bpy.context.object, name, mat, bevel)


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1,
                                         location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat)


def rod(name, start, end, radius, mat, vertices=12):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) * .5)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return finish(obj, name, mat, radius * .18)


def torus(name, location, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
                                     major_radius=major, minor_radius=minor,
                                     location=location)
    obj = bpy.context.object
    if rotation is not None:
        obj.rotation_euler = rotation
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat)


def lathe_bell(profile, mat):
    segments = 64
    verts = [(radius * cos(2*pi*i/segments), .105 + radius * sin(2*pi*i/segments), z)
             for radius, z in profile for i in range(segments)]
    faces = []
    for ring in range(len(profile)):
        next_ring = (ring + 1) % len(profile)
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring*segments+i, ring*segments+j,
                          next_ring*segments+j, next_ring*segments+i))
    mesh = bpy.data.meshes.new("Ritual bell cast bronze mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Hollow cast bronze bell", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def build_bell(stone, stone_trim, bronze, bright_bronze, patina, wood, dark):
    # Broad layered plinth keeps the 1x1 floor decoration planted on the tile.
    block("Carved square stone foot", (0, 0, .075), (.82, .64, .15), stone, .025)
    block("Upper altar step", (0, 0, .17), (.67, .51, .075), stone_trim, .016)
    block("Inset altar top", (0, 0, .216), (.58, .43, .035), stone, .009)
    for x in (-.31, .31):
        block("Pillar plinth", (x, 0, .275), (.18, .48, .085), stone_trim, .012)
        block("Pillar capital", (x, 0, 1.09), (.19, .49, .10), stone_trim, .012)
        cylinder("Carved octagonal stone pillar", (x, 0, .685), .071, .76,
                 stone, 8, .008)
        cylinder("Pillar collar lower", (x, 0, .34), .084, .035,
                 stone_trim, 8, .004)
        cylinder("Pillar collar upper", (x, 0, 1.025), .086, .04,
                 stone_trim, 8, .004)
        # Shallow bronze inlay bands make the supports read as temple fittings.
        cylinder("Pillar bronze inlay", (x, .002, .94), .074, .012,
                 bright_bronze, 8, .002)
        for dz in (.44, .54, .64, .74, .84):
            rod("Pillar carved flute", (x-.032, .071, dz), (x-.032, .071, dz+.045),
                .003, stone_trim, 8)
            rod("Pillar carved flute", (x+.032, .071, dz), (x+.032, .071, dz+.045),
                .003, stone_trim, 8)

    # Stone lintel, a dark wooden suspension beam, and its hammered iron hangers.
    block("Engraved stone lintel", (0, 0, 1.17), (.78, .50, .13), stone, .018)
    block("Dark oak bell crossbeam", (0, .012, 1.255), (.58, .30, .065), wood, .016)
    for x in (-.205, .205):
        cylinder("Crossbeam iron peg", (x, .18, 1.255), .018, .018,
                 dark, 10, .002)
    torus("Suspension eye", (0, .105, 1.205), .047, .009, bright_bronze,
          (pi/2, 0, 0))
    # A centered chain reaches the crown loop so the bell visibly hangs from the beam.
    for i in range(6):
        z = 1.139 - i*.036
        torus("Forged suspension chain link", (0, .105, z), .015, .0038,
              dark if i % 2 else bright_bronze,
              (pi/2 if i % 2 else 0, 0, 0))
    rod("Suspension chain core", (0, .105, 1.105), (0, .105, .955),
        .0045, dark, 10)

    profile = [
        (.045, .916), (.058, .909), (.067, .889), (.076, .858),
        (.095, .829), (.126, .798), (.159, .759), (.184, .716),
        (.197, .676), (.199, .646), (.195, .627), (.181, .619),
        (.173, .629), (.169, .649), (.154, .687), (.129, .728),
        (.101, .767), (.078, .800), (.061, .835), (.049, .871),
        (.038, .897),
    ]
    lathe_bell(profile, bronze)
    sphere("Bell crown boss", (0, .105, .919), (.052, .052, .025), bright_bronze)
    torus("Bell crown suspension loop", (0, .105, .946), .026, .006,
          bright_bronze, (pi/2, 0, 0))
    # Rolled mouth, waist and shoulder rings catch warm highlights.
    for z, radius, thickness in ((.635, .188, .011), (.675, .196, .006),
                                 (.775, .145, .005), (.847, .083, .004)):
        torus("Cast bronze bell band", (0, .105, z), radius, thickness, bright_bronze)
    torus("Bell mouth patina line", (0, .105, .646), .197, .0035, patina)

    # The clapper hangs inside the open bell and ends in a rounded bronze striker.
    rod("Bell clapper stem", (0, .105, .647), (0, .105, .535), .009, dark, 10)
    sphere("Clapper striker", (0, .105, .526), (.031, .031, .035), bright_bronze)
    rod("Pull rope", (0, .105, .526), (0, .105, .34), .009, wood, 10)
    sphere("Rope tassel knot", (0, .105, .338), (.018, .018, .023), bright_bronze)
    for i in range(3):
        rod("Tassel strand", ((i-1)*.012, .105, .326), ((i-1)*.018, .105, .275),
            .0045, wood, 8)

    # Small raised rosette and beadwork mark the front without turning the bell into text.
    torus("Bell front sun medallion", (0, .302, .75), .045, .006,
          bright_bronze, (pi/2, 0, 0))
    sphere("Bell sun center", (0, .308, .75), (.015, .009, .015), bright_bronze)
    for side in (-1, 1):
        for z in (.731, .75, .769):
            sphere("Bell engraved bead", (side*.029, .304, z),
                   (.0045, .003, .0045), bright_bronze)
        # A pair of tiny offering bowls and votive candles sit on the altar step.
        x = side*.215
        cylinder("Votive candle cup", (x, .21, .242), .043, .026,
                 bright_bronze, 20, .003)
        cylinder("Unlit ivory ritual candle", (x, .21, .277), .021, .055,
                 stone_trim, 16, .003)
        rod("Unlit candle wick", (x, .21, .306), (x, .21, .315), .003,
            dark, 8)

    # Small square relief marks on the front of the altar base.
    for x in (-.27, -.18, .18, .27):
        sphere("Altar bronze stud", (x, .326, .087), (.012, .006, .012), bright_bronze)
    block("Altar front inset", (0, .324, .078), (.17, .012, .065), dark, .008)
    torus("Altar front seal", (0, .334, .08), .023, .004, bright_bronze,
          (pi/2, 0, 0))


def animate_bell():
    """Give the suspended assembly a short, damped swing for click playback."""
    moving_prefixes = (
        "Hollow cast bronze bell", "Bell crown", "Cast bronze bell band",
        "Bell mouth patina", "Bell clapper", "Clapper striker", "Pull rope",
        "Rope tassel", "Tassel strand", "Bell front", "Bell sun", "Bell engraved",
    )
    pivot = bpy.data.objects.new("Ritual bell swing pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = (0, .105, .946)
    bpy.context.view_layer.update()
    for obj in list(bpy.context.scene.objects):
        if obj == pivot or obj.type != "MESH" or not obj.name.startswith(moving_prefixes):
            continue
        world = obj.matrix_world.copy()
        obj.parent = pivot
        obj.matrix_world = world

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 25
    scene.render.fps = 24
    pivot.rotation_mode = "XYZ"
    # One bell strike: strong initial swing, then a quick, visible decay.
    for frame, angle in ((1, 0), (4, .105), (8, -.078), (12, .052),
                         (16, -.032), (20, .017), (25, 0)):
        pivot.rotation_euler[0] = angle
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame,
                              group="Ritual bell swing")
    action = pivot.animation_data.action
    action.name = "Ritual bell strike and swing"
    # Blender inserts Bezier keyframes by default, giving the swing a natural
    # eased decay without a linear mechanical stop.


def setup_render():
    scene = bpy.context.scene
    target = Vector((0, .04, .68))
    bpy.ops.object.camera_add(location=(1.30, 2.5, 1.58))
    camera = bpy.context.object
    camera.name = "Ritual bell showcase camera"
    camera.rotation_euler = (target-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.58
    scene.camera = camera
    for name, location, energy, color in (
        ("Warm temple key", (.5, 1.8, 2.1), 125, (1, .77, .49)),
        ("Cool bronze fill", (-1.3, .7, 1.2), 60, (.57, .68, 1)),
        ("Amber rim", (.7, -.8, 1.5), 52, (1, .40, .16)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = .85
        lamp.data.color = color
        lamp.rotation_euler = (target-lamp.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.035, .03, .025, 1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .35


def merge_static():
    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.parent and obj.parent.name == "Ritual bell swing pivot":
            # Keep suspended components separate so the bell, crown, and
            # clapper all follow the animated pivot in the exported GLB.
            continue
        key = obj.data.materials[0].name if obj.data.materials else "unmaterialed"
        groups.setdefault(key, []).append(obj)
    for key, objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        objects[0].name = "Ritual bell - " + key


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    stone = material("Temple Stone", (.20, .16, .115), .02, .83)
    stone_trim = material("Temple Stone highlights", (.34, .25, .15), .08, .72)
    bronze = material("Aged Bronze", (.38, .19, .065), .82, .34)
    bright_bronze = material("Polished Bronze wear", (.72, .43, .16), .78, .27)
    patina = material("Bronze verdigris", (.025, .105, .075), .42, .62)
    wood = material("Dark Wood", (.105, .052, .023), .05, .76)
    dark = material("Blackened Iron", (.036, .033, .029), .68, .52)
    build_bell(stone, stone_trim, bronze, bright_bronze, patina, wood, dark)
    animate_bell()
    setup_render()
    scene = bpy.context.scene
    scene.render.filepath = str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)

    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 1.52
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)

    merge_static()
    bpy.ops.object.select_all(action="DESELECT")
    export_objects = [obj for obj in scene.objects
                      if obj.type == "MESH" or obj.name == "Ritual bell swing pivot"]
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Ritual bell swing pivot"]
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB",
                              use_selection=True, export_apply=True,
                              export_animations=True, export_frame_range=True,
                              export_animation_mode="ACTIONS")
    print("Created", GLB)


if __name__ == "__main__":
    main()
