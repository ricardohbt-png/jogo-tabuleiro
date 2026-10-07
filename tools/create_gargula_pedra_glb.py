"""Gera a gárgula de parede em pedra gasta, para PNG e GLB."""
from math import cos, pi, sin
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
BLEND = OUT / "gargula_pedra.blend"
GLB = OUT / "gargula_pedra.glb"
PNG = OUT / "gargula_pedra.png"
PREVIEW = OUT / "gargula_pedra_preview.png"


def material(name, color, roughness=.86, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if "stone" in name.lower() or "slate" in name.lower():
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 26
        noise.inputs["Detail"].default_value = 5
        noise.inputs["Roughness"].default_value = .78
        # Keep Base Color directly connected for glTF export; Blender cannot
        # serialize a procedural color ramp as a material's base-color factor.
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .23
        bump.inputs["Distance"].default_value = .028
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def finish(obj, name, mat, bevel=0):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("weathered, softened stone edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def ellipsoid(name, location, scale, mat, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1, location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish(obj, name, mat)


def rod(name, start, end, radius, mat, vertices=12, tip=0):
    a, b = Vector(start), Vector(end)
    delta = b-a
    if tip:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=tip, depth=delta.length,
                                        location=(a+b)*.5)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=delta.length, location=(a+b)*.5)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return finish(obj, name, mat, radius*.16)


def block(name, location, size, mat, bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel)


def extruded_shape(name, outline, front_y, back_y, mat):
    n = len(outline)
    verts = [(x,front_y,z) for x,z in outline] + [(x,back_y,z) for x,z in outline]
    faces = [tuple(range(n)), tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh = bpy.data.meshes.new(name+" mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, .008)


def torus(name, location, major, minor, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
                                     location=location, major_radius=major,
                                     minor_radius=minor)
    obj = bpy.context.object
    if rotation is not None:
        obj.rotation_euler = rotation
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish(obj, name, mat)


def wing(side, stone, highlight):
    # Folded bat wings form a threatening silhouette while staying within one cell.
    pts = [(side*.105,.055,.59),(side*.175,.055,.76),
           (side*.288,.055,.84),(side*.283,.055,.75),
           (side*.315,.055,.70),(side*.267,.055,.65),
           (side*.305,.055,.60),(side*.238,.055,.53),
           (side*.271,.055,.45),(side*.19,.055,.34),
           (side*.112,.055,.31)]
    verts = [(x,y,z) for x,y,z in pts]
    outline = tuple(range(len(pts)))
    faces = [outline if side > 0 else tuple(reversed(outline))]
    obj = bpy.data.meshes.new("Folded wing stone mesh")
    obj.from_pydata(verts, [], faces)
    wing_obj = bpy.data.objects.new("Folded stone wing", obj)
    bpy.context.collection.objects.link(wing_obj)
    obj.materials.append(stone)
    solidify = wing_obj.modifiers.new("carved wing membrane thickness", "SOLIDIFY")
    solidify.thickness = .022
    bpy.context.view_layer.objects.active = wing_obj
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    # Raised ribs follow the long bones of each folded wing.
    shoulder = (side*.12,.085,.58)
    for i, tip in enumerate(((side*.285,.005,.82),(side*.311,.006,.70),
                             (side*.301,.006,.60),(side*.268,.01,.46))):
        rod("Wing raised stone rib %d" % i, shoulder, tip,
            .009 if i == 0 else .0065, stone, 9)
    rod("Wing outer claw", (side*.29,.012,.83), (side*.32,.025,.875),
        .014, stone, 9, .001)
    return wing_obj


def build_gargoyle(stone, highlight, slate, shadow, support_stone):
    # Shallow arched backing fits the face of an ordinary wall cell.
    extruded_shape("Gothic wall mounting plaque", [
        (-.335,.04),(.335,.04),(.335,.55),(.29,.70),(.18,.81),
        (0,.86),(-.18,.81),(-.29,.70),(-.335,.55),
    ], -.155, -.205, slate)
    # Weathered carved ledge and layered moulding.
    block("Projecting gargoyle perch", (0,-.005,.185), (.72,.32,.12), support_stone, .018)
    block("Perch lower moulding", (0,-.018,.105), (.66,.29,.045), highlight, .008)
    block("Perch top lip", (0,.005,.255), (.64,.30,.04), support_stone, .008)
    for side in (-1,1):
        ellipsoid("Perch corner boss", (side*.29,.164,.19), (.035,.014,.032), slate)

    # A compact, anatomically articulated crouch, carved as one architectural figure.
    ellipsoid("Gargoyle crouched torso", (0,.065,.405), (.125,.11,.18), stone)
    ellipsoid("Hunched shoulder mass", (0,.085,.535), (.145,.12,.10), stone)
    for side in (-1,1):
        # Folded legs press into the ledge; splayed claws grip the stone lip.
        ellipsoid("Bent stone haunch", (side*.133,.07,.335), (.084,.105,.087), stone)
        rod("Gargoyle shin", (side*.17,.10,.34), (side*.205,.175,.235),
            .045, stone, 14)
        ellipsoid("Gargoyle paw", (side*.205,.196,.235), (.082,.065,.038), stone)
        for digit in range(3):
            x = side*(.16 + digit*.044)
            rod("Paw talon", (x,.235,.23), (x+side*.009,.285,.205),
                .012, stone, 10, .001)

        # Long arms descend from the shoulders and end in hooked fingers.
        ellipsoid("Gargoyle shoulder", (side*.15,.12,.54), (.061,.066,.073), stone)
        ellipsoid("Gargoyle elbow", (side*.19,.195,.43), (.039,.038,.046), stone)
        rod("Gargoyle upper arm", (side*.16,.17,.52), (side*.19,.195,.43),
            .034, stone, 14)
        rod("Gargoyle forearm", (side*.19,.195,.43), (side*.21,.22,.31),
            .030, stone, 14)
        ellipsoid("Gargoyle knuckle", (side*.21,.232,.30), (.043,.039,.035), stone)
        for digit in range(3):
            x = side*(.195 + digit*.031)
            rod("Hooked stone finger", (x,.255,.30), (x+side*.012,.305,.255),
                .011, stone, 10, .001)

        wing(side, stone, highlight)

    # Long tail curls around the perch, a distinct gargoyle silhouette detail.
    pts = [(.12,.0,.37),(.22,.01,.34),(.285,.014,.38),
           (.292,.014,.46),(.245,.01,.51),(.215,.01,.48)]
    for i in range(len(pts)-1):
        rod("Curled gargoyle tail", pts[i], pts[i+1], .018-i*.0015,
            stone, 10)
    rod("Tail pointed tip", pts[-1], (.188,.012,.49), .022, stone, 10, .001)

    # Smaller, angular face: a carved beast mask rather than a round cartoon muzzle.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1,
                                           location=(0,.205,.69))
    skull = bpy.context.object
    skull.name = "Angular carved gargoyle skull"
    skull.scale = (.097,.083,.103)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(skull, skull.name, stone)
    ellipsoid("Tapered upper muzzle", (0,.27,.65), (.053,.052,.038), stone)
    ellipsoid("Sculpted lower jaw", (0,.267,.615), (.064,.041,.025), stone)
    # A narrow shadowed snarl is set between stone lips; no protruding black nose.
    ellipsoid("Carved mouth recess", (0,.307,.627), (.038,.004,.006), shadow)
    ellipsoid("Stone nose plane", (0,.306,.657), (.019,.013,.012), stone)
    for side in (-1,1):
        # Thin, recessed eyes and planar cheek ridges read as chisel work.
        x = side*.046
        ellipsoid("Recessed eye slit", (x,.278,.707), (.016,.004,.005), shadow, 16, 10)
        rod("Carved cheek plane", (side*.085,.252,.672),
            (side*.047,.291,.632), .018, stone, 10)
        rod("Heavy carved brow", (side*.083,.276,.731),
            (side*.012,.297,.72), .016, stone, 12)
        # High horns and pointed ears break the outline above the head.
        rod("Worn swept-back horn", (side*.067,.195,.765),
            (side*.105,.135,.827), .022, stone, 14, .003)
        ellipsoid("Horn root", (side*.067,.2,.77), (.025,.024,.018), stone)
        rod("Carved pointed ear", (side*.09,.187,.70),
            (side*.15,.145,.736), .016, stone, 12, .002)
    ellipsoid("Nostril left", (-.01,.316,.66), (.0035,.0025,.003), shadow, 12, 8)
    ellipsoid("Nostril right", (.01,.316,.66), (.0035,.0025,.003), shadow, 12, 8)

    # Small stone chips and iron mounting pins age the wall fitting.
    for side in (-1,1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.012,
                                               location=(side*.30,-.119,.61))
        finish(bpy.context.object, "Plaque iron anchor pin", shadow)
        ellipsoid("Plaque worn stone pin", (side*.30,-.113,.61), (.009,.006,.009), highlight)


def fuse_statue_body(stone):
    """Voxel-remesh the overlapping carved forms into one continuous statue."""
    parts = [obj for obj in bpy.context.scene.objects
             if obj.type == "MESH"
             and any(mat.name == stone.name for mat in obj.data.materials)]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.object
    body.name = "Unified hand-carved gargoyle statue"
    remesh = body.modifiers.new("fuse sculpted stone forms", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = .006
    remesh.use_smooth_shade = True
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = body.modifiers.new("soften chisel transitions", "SMOOTH")
    smooth.factor = .55
    smooth.iterations = 2
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    # Natural stone holds a soft carved surface instead of flat, cartoon facets.
    for face in body.data.polygons:
        face.use_smooth = True
    texture = bpy.data.textures.new("Subtle stone erosion", type="CLOUDS")
    texture.noise_scale = .11
    displacement = body.modifiers.new("microscopic weathered stone", "DISPLACE")
    displacement.texture = texture
    displacement.strength = .0012
    bpy.ops.object.modifier_apply(modifier=displacement.name)


def setup_render():
    scene = bpy.context.scene
    target = Vector((0,.04,.50))
    bpy.ops.object.camera_add(location=(1.15,2.35,1.08))
    camera = bpy.context.object
    camera.name = "Gargoyle showcase camera"
    camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.08
    scene.camera = camera
    for name, location, power, color in (
        ("Cold stone key", (.35,1.45,1.55), 44, (.74,.82,1)),
        ("Warm face fill", (-1.0,.9,.95), 19, (1,.60,.34)),
        ("Hard moon rim", (.7,-.6,1.2), 33, (.40,.55,1)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = power
        lamp.data.shape = "DISK"
        lamp.data.size = .65
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
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.012,.016,.028,1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .14


def add_preview_wall():
    """A small masonry context for the preview; it is excluded from PNG and GLB."""
    mortar = material("Preview temple mortar", (.045,.05,.058), .98)
    stones = [material("Preview wall stone %d" % i, color, .96)
              for i,color in enumerate(((.12,.13,.145),(.15,.155,.16),
                                        (.18,.175,.165),(.135,.15,.17)))]
    block("Preview wall backing", (0,-.37,.46), (1.65,.16,1.50), mortar, .015)
    for row in range(7):
        z = -.15 + row*.22
        offset = .19 if row % 2 else 0
        for col in range(-3,4):
            x = col*.40 + offset
            if abs(x) < .90:
                block("Preview ashlar", (x,-.282,z), (.385,.095,.202),
                      stones[(row*3+col) % len(stones)], .012)


def merge_static():
    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
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
        objects[0].name = "Stone gargoyle - " + key


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    stone = material("Weathered dark stone", (.055,.062,.071), .98)
    highlight = material("Worn stone ridges", (.085,.092,.10), .96)
    slate = material("Carved slate plaque", (.028,.034,.044), .99)
    shadow = material("Deep carved recess", (.006,.008,.012), 1)
    support_stone = material("Gargoyle support stone", (.075,.08,.087), .97)
    build_gargoyle(stone, highlight, slate, shadow, support_stone)
    fuse_statue_body(stone)
    setup_render()
    scene = bpy.context.scene
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 1.05
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
    # The contextual wall belongs only to the product preview, never the placeable asset.
    add_preview_wall()
    scene.render.film_transparent = False
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.camera.data.ortho_scale = 1.38
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    print("Created", GLB)


if __name__ == "__main__":
    main()
