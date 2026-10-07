"""Cria um braseiro medieval de parede com chama animada e miniaturas."""
from pathlib import Path
from math import cos, pi, sin
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
FLAME_GLB = OUT / "chama_viva.glb"
MODEL_GLB = OUT / "braseiro_parede.glb"
SOURCE_BLEND = OUT / "braseiro_parede.blend"
IMAGE = OUT / "braseiro_parede.png"
PREVIEW = OUT / "braseiro_parede_preview.png"


def material(name, color, metallic=0.0, roughness=0.7, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        sock = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        if sock:
            sock.default_value = (*emission, 1)
        sock = shader.inputs.get("Emission Strength")
        if sock:
            sock.default_value = strength
    return mat


def finish(obj, mat, bevel=0.0):
    obj.data.materials.append(mat)
    if bevel and obj.type == "MESH":
        mod = obj.modifiers.new("soft worn edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=32, radius2=None):
    if radius2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius2, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, mat, min(radius, depth) * 0.12)


def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish(obj, mat)


def rod(name, a, b, radius, mat, vertices=12):
    a, b = Vector(a), Vector(b)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return finish(obj, mat, radius * 0.18)


def torus(name, loc, major, minor, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
                                     location=loc, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return finish(obj, mat)


def bowl(name, center, profile, mat, segments=40):
    cx, cy = center
    verts = []
    for radius, z in profile:
        verts.extend((cx + cos(i * 2*pi/segments)*radius,
                      cy + sin(i * 2*pi/segments)*radius, z) for i in range(segments))
    faces = []
    for ring in range(len(profile)-1):
        for i in range(segments):
            j = (i+1) % segments
            faces.append((ring*segments+i, ring*segments+j,
                          (ring+1)*segments+j, (ring+1)*segments+i))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build_fixture(iron, edge, bronze, brass, dark, coal, ember):
    # Wall plate lies at the rear (-Y); every other piece projects into the room (+Y).
    plate = cylinder("Wall anchor", (0, -0.144, 0.46), 0.105, 0.036, iron, 8)
    plate.rotation_euler.x = pi / 2  # disc stands vertically against the XZ wall plane
    boss = cylinder("Raised anchor boss", (0, -0.119, 0.46), 0.071, 0.022, edge, 8)
    boss.rotation_euler.x = pi / 2
    for i, (x, z) in enumerate(((-.061,.399),(.061,.399),(-.061,.521),(.061,.521))):
        rod("Anchor rivet %d" % i, (x,-.104,z), (x,-.092,z), .009, brass, 8)
    # Short scroll arm and hanging iron links.
    rod("Forged wall arm", (0,-.101,.46), (0,.112,.49), .022, edge)
    rod("Arm brace", (0,-.084,.405), (0,.102,.452), .011, bronze)
    torus("Suspension eye", (0,.115,.485), .043, .008, bronze)
    for i, x in enumerate((-.074, .074)):
        torus("Bowl hanging link %d" % i, (x,.153,.431), .030, .006, edge)
        torus("Bowl hanging link turn %d" % i, (x,.153,.396), .026, .006, edge)
        rod("Chain to bowl %d" % i, (x,.153,.392), (x,.153,.356), .006, iron)

    cx, cy = 0, .192
    bowl("Deep hammered iron bowl", (cx,cy), [
        (.055,.302),(.076,.315),(.105,.351),(.137,.409),(.148,.438),
        (.137,.444),(.121,.413),(.096,.374),(.069,.347),(.035,.337),
    ], iron)
    torus("Rolled bowl rim", (cx,cy,.439), .143, .010, bronze)
    torus("Bowl foot ring", (cx,cy,.323), .061, .009, edge)
    cylinder("Bowl exterior band", (cx,cy,.369), .108, .022, edge, 32)
    torus("Band bronze edge", (cx,cy,.382), .110, .004, bronze)
    # Forged ribs support the bowl from the lower ring to its rolled rim.
    for i in range(6):
        a = i * 2*pi/6
        x, y = cos(a), sin(a)
        rod("Bowl rib %d lower" % i, (x*.067,cy+y*.067,.328),
            (x*.128,cy+y*.128,.424), .008, edge)
        sphere("Rib rivet %d" % i, (x*.111,cy+y*.111,.397), (.010,.010,.010), brass)
    cylinder("Coal bed", (cx,cy,.346), .073, .009, dark, 28)
    for i in range(9):
        a = i * 2.399963229728653
        r = .018 + (i % 3)*.012
        sphere("Coal %d" % i, (cx+cos(a)*r,cy+sin(a)*r,.353+(i%2)*.004),
               (.012,.010,.006), ember if i % 3 == 0 else coal)


def import_flame():
    bpy.ops.import_scene.gltf(filepath=str(FLAME_GLB))
    parts = [o for o in list(bpy.context.scene.objects) if o.type == "MESH"
             and o.name in {"Chama externa", "Chama interna", "Nucleo luminoso"}]
    ember = next((o for o in list(bpy.context.scene.objects)
                  if o.type == "MESH" and o.name == "Brasa"), None)
    if len(parts) != 3:
        raise RuntimeError("Não encontrei as malhas animadas da chama viva.")
    if ember:
        bpy.data.objects.remove(ember, do_unlink=True)
    root = bpy.data.objects.new("Animated flame pivot", None)
    bpy.context.collection.objects.link(root)
    root.location = (0,.192,.345)
    root.scale = (.28,.28,.28)
    for obj in parts:
        loc, rot, scale = obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy()
        obj["preserve_animation"] = True
        obj.parent = root
        obj.matrix_parent_inverse.identity()
        obj.location, obj.rotation_euler, obj.scale = loc, rot, scale
    return root


def merge_static():
    curves = [o for o in bpy.context.scene.objects if o.type == "CURVE"]
    if curves:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in curves:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target="MESH")
    groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.get("preserve_animation"):
            key = obj.data.materials[0].name if obj.data.materials else "unmaterialed"
            groups.setdefault(key, []).append(obj)
    for key, objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        objects[0].name = "Brazier static - " + key


def render_setup():
    bpy.ops.object.camera_add(location=(1.25,2.0,1.03))
    camera = bpy.context.object
    target = Vector((0,.06,.42))
    camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = .90
    bpy.context.scene.camera = camera
    for name, loc, energy, color in (
        ("Warm key",(.4,1.5,1.7),220,(1,.72,.43)),
        ("Cool fill",(-1,.6,.9),120,(.59,.72,1)),
        ("Fire rim",(.8,-.6,1.1),120,(1,.31,.09)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.shape = "DISK"
        lamp.data.size = .9
        lamp.data.color = color
        lamp.rotation_euler = (target-lamp.location).to_track_quat("-Z","Y").to_euler()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .38
    scene.frame_start, scene.frame_end, scene.render.fps = 0, 31, 24
    scene.frame_set(7)


def main():
    if not FLAME_GLB.is_file():
        raise FileNotFoundError(FLAME_GLB)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    iron = material("blackened iron",(.045,.039,.034),.72,.48)
    edge = material("worn iron edges",(.15,.113,.075),.65,.43)
    bronze = material("aged bronze",(.34,.16,.048),.62,.42)
    brass = material("hammered brass rivets",(.54,.32,.10),.68,.39)
    dark = material("coal shadow",(.018,.012,.008),.05,.9)
    coal = material("charcoal",(.029,.021,.014),.05,.86)
    ember = material("glowing embers",(.38,.035,.004),.05,.72,(.75,.025,.001),.8)
    build_fixture(iron,edge,bronze,brass,dark,coal,ember)
    flame = import_flame()
    render_setup()
    scene = bpy.context.scene
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_BLEND))
    bpy.ops.render.render(write_still=True)

    # Transparent icon for the editor and 2D board.
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = .92
    scene.render.filepath = str(IMAGE)
    bpy.ops.render.render(write_still=True)

    merge_static()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in scene.objects:
        if obj.type == "MESH" or obj == flame:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = flame
    bpy.ops.export_scene.gltf(filepath=str(MODEL_GLB), export_format="GLB",
        use_selection=True, export_apply=True, export_animations=True, export_frame_range=True)
    print("Created", MODEL_GLB)


if __name__ == "__main__":
    main()
