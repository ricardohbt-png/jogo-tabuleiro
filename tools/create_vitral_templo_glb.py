"""Cria um vitral gótico de templo, com PNG e modelo GLB para a decoração."""
from pathlib import Path
from math import cos, pi, sin

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
BLEND = OUT / "vitral_templo.blend"
GLB = OUT / "vitral_templo.glb"
PNG = OUT / "vitral_templo.png"
PREVIEW = OUT / "vitral_templo_preview.png"


def make_material(name, color, metallic=0.0, roughness=0.6, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1)
        socket = bsdf.inputs.get("Emission Strength")
        if socket:
            socket.default_value = strength
    # Fine procedural relief prevents the stone and glass from reading as flat plastic.
    if "stone" in name or "limestone" in name or "glass" in name:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 18.0 if "stone" in name or "limestone" in name else 34.0
        tex.inputs["Detail"].default_value = 4.0 if "stone" in name or "limestone" in name else 2.0
        tex.inputs["Roughness"].default_value = .72
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = .18
        ramp.color_ramp.elements[0].color = (*(v*.70 for v in color), 1)
        ramp.color_ramp.elements[1].position = .82
        ramp.color_ramp.elements[1].color = (*(min(1.0,v*1.22+.015) for v in color), 1)
        links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .12 if "glass" in name else .20
        bump.inputs["Distance"].default_value = .012 if "glass" in name else .022
        links.new(tex.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        if "glass" in name:
            coat = bsdf.inputs.get("Coat Weight")
            if coat:
                coat.default_value = .32
            coat_rough = bsdf.inputs.get("Coat Roughness")
            if coat_rough:
                coat_rough.default_value = .18
    return mat


def mesh_object(name, verts, faces, mat, recalc=False):
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def extruded_profile(name, outline, y_front, y_back, mat):
    n = len(outline)
    verts = [(x, y_front, z) for x, z in outline]
    verts += [(x, y_back, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    faces.extend((i, (i+1) % n, (i+1) % n + n, i+n) for i in range(n))
    return mesh_object(name, verts, faces, mat, True)


def surface_panel(name, points, y, mat):
    return mesh_object(name, [(x, y, z) for x, z in points], [tuple(range(len(points)))], mat)


def glass_panel(name, points, mat):
    """Thick, lightly beveled cathedral glass with visible hand-ground edges."""
    obj = extruded_profile(name, points, .061, .028, mat)
    bevel = obj.modifiers.new("hand-ground glass edges", "BEVEL")
    bevel.width = .004
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def rod(name, start, end, radius, mat, vertices=12):
    a, b = Vector(start), Vector(end)
    delta = b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length,
                                        location=(a+b)*0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("soft lead edges", "BEVEL")
    bevel.width = radius * 0.2
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(mat)
    return obj


def make_frame(name, outer, inner, y_front, y_back, stone, trim):
    """Create a solid pointed arch ring with visible inner and outer bevel bands."""
    n = len(outer)
    verts = ([(x,y_front,z) for x,z in outer] + [(x,y_front,z) for x,z in inner]
             + [(x,y_back,z) for x,z in outer] + [(x,y_back,z) for x,z in inner])
    of, inf, ob, inb = 0, n, 2*n, 3*n
    faces = []
    for i in range(n):
        j = (i+1) % n
        faces.extend(((of+i,of+j,inf+j,inf+i),
                      (ob+j,ob+i,inb+i,inb+j),
                      (of+i,ob+i,ob+j,of+j),
                      (inf+j,inb+j,inb+i,inf+i)))
    obj = mesh_object(name, verts, faces, stone, True)
    obj.data.materials.append(trim)
    # A thin warm-metal bead around the inner edge gives the leaded glass a finished border.
    for i in range(n):
        x1,z1 = inner[i]
        x2,z2 = inner[(i+1) % n]
        rod("Bronze inner bead %02d" % i, (x1,y_front+0.008,z1),
            (x2,y_front+0.008,z2), 0.004, trim, 8)
    return obj


def make_rose(palette, lead, y, center_z=0.655):
    cx, cz, radius, segments = 0.0, center_z, 0.092, 12
    for i in range(segments):
        a0, a1 = 2*pi*i/segments, 2*pi*(i+1)/segments
        outer0 = (radius*cos(a0), center_z + radius*sin(a0))
        outer1 = (radius*cos(a1), center_z + radius*sin(a1))
        inner0 = (0.023*cos(a0), center_z + 0.023*sin(a0))
        inner1 = (0.023*cos(a1), center_z + 0.023*sin(a1))
        glass_panel("Rose glass petal %02d" % i, [inner0,outer0,outer1,inner1],
                    palette[i % len(palette)])
    glass_panel("Rose center jewel", [
        (0.023*cos(2*pi*i/16), center_z+0.023*sin(2*pi*i/16)) for i in range(16)
    ], palette[2])
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
                                     location=(cx,y+0.034,cz), major_radius=radius,
                                     minor_radius=0.006)
    ring = bpy.context.object
    ring.name = "Rose window lead ring"
    ring.rotation_euler.x = pi/2
    ring.data.materials.append(lead)


def build_window(mats):
    stone, stone_edge, lead, bronze, dark, blue, red, gold, green, pale = mats
    outer = [(-.36,.035),(-.36,.57),(-.33,.65),(-.26,.73),(-.16,.82),
             (0,.96),(.16,.82),(.26,.73),(.33,.65),(.36,.57),(.36,.035)]
    inner = [(-.295,.085),(-.295,.56),(-.268,.625),(-.207,.692),(-.126,.77),
             (0,.875),(.126,.77),(.207,.692),(.268,.625),(.295,.56),(.295,.085)]

    # Dark backing and jewel-toned panes sit on the room-facing side of the frame.
    extruded_profile("Dark glass backing", inner, .015, -.018, dark)
    panes = [
        ("Lower left blue",[(-.274,.105),(-.025,.105),(-.025,.285),(-.274,.285)],blue),
        ("Lower right ruby",[(.025,.105),(.274,.105),(.274,.285),(.025,.285)],red),
        ("Middle left gold",[(-.274,.312),(-.025,.312),(-.025,.50),(-.274,.50)],gold),
        ("Middle right green",[(.025,.312),(.274,.312),(.274,.50),(.025,.50)],green),
        ("Upper left jewel",[(-.25,.525),(-.118,.525),(-.118,.682),(-.203,.682),(-.25,.625)],red),
        ("Upper right jewel",[(.118,.525),(.25,.525),(.25,.625),(.203,.682),(.118,.682)],blue),
        ("Left arch panel",[(-.188,.704),(-.113,.778),(-.043,.843),(-.043,.724),(-.105,.704)],green),
        ("Right arch panel",[(.043,.724),(.043,.843),(.113,.778),(.188,.704),(.105,.704)],gold),
    ]
    for name, points, material in panes:
        glass_panel(name, points, material)

    make_rose([blue,red,gold,green,pale,blue,red,gold,green,pale,blue,red], lead, .038)
    make_frame("Gothic sandstone arch", outer, inner, .075, -.075, stone, bronze)

    # Jewel pins and quatrefoil tracery details around the upper panes.
    for side in (-1,1):
        cx, cz = side*.158, .592
        for i in range(4):
            angle = pi*i/2
            sphere("Tracery quatrefoil %s %d" % (side,i),
                   (cx+.025*cos(angle),.068,cz+.025*sin(angle)),
                   (.012,.006,.012),bronze)
        sphere("Upper glass jewel %s" % side,(side*.235,.069,.585),
               (.011,.007,.016),pale)

    # Lead mullions divide the lower windows and connect to the rose.
    for i, (a,b,r) in enumerate([
        ((0,.07,.10),(0,.07,.55),.009),
        ((-.27,.07,.297),(.27,.07,.297),.008),
        ((-.27,.07,.512),(-.105,.07,.512),.008),
        ((.105,.07,.512),(.27,.07,.512),.008),
        ((-.205,.07,.692),(-.108,.07,.692),.007),
        ((.108,.07,.692),(.205,.07,.692),.007),
        ((0,.07,.748),(0,.07,.836),.006),
    ]):
        rod("Lead mullion %02d" % i, a, b, r, lead)

    # Carved stone joints, a shallow sill, and riveted iron anchor tabs.
    for side in (-1,1):
        for i,z in enumerate((.17,.36,.55)):
            rod("Stone joint %s %d" % (side,i), (side*.314,.083,z),
                (side*.354,.083,z), .004, stone_edge, 8)
        for i,z in enumerate((.13,.48)):
            sphere("Anchor stud %s %d" % (side,i), (side*.342,.094,z),
                   (.012,.008,.012), bronze)
    # Projecting sill catches light and makes the window read as a wall fixture.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,.005,.035))
    sill = bpy.context.object
    sill.name = "Carved stone sill"
    sill.dimensions = (.78,.19,.07)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sill.data.materials.append(stone_edge)
    bevel = sill.modifiers.new("worn sill edges", "BEVEL")
    bevel.width = .018
    bevel.segments = 3
    bpy.context.view_layer.objects.active = sill
    bpy.ops.object.modifier_apply(modifier=bevel.name)


def combine_static():
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
        objects[0].name = "Stained glass - " + key


def setup_render():
    target = Vector((0,.015,.48))
    bpy.ops.object.camera_add(location=(1.05,2.3,1.08))
    camera = bpy.context.object
    camera.name = "Three quarter preview camera"
    camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.20
    bpy.context.scene.camera = camera
    for name, location, energy, color in [
        ("Warm key",(.4,1.6,1.8),95,(1.0,.80,.58)),
        ("Cool glass fill",(-1.2,.8,1.0),65,(.55,.68,1.0)),
        ("Warm rim",(.7,-.8,1.3),38,(1.0,.44,.20)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = 1.0
        light.data.color = color
        light.rotation_euler = (target-light.location).to_track_quat("-Z","Y").to_euler()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.035,.040,.050,1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .30


def make_preview_wall():
    """Temple stone backdrop for the showcase render only; excluded from the GLB."""
    mortar = make_material("temple wall mortar",(.065,.055,.045),0,.96)
    blocks = [make_material("temple limestone block %d" % i,color,0,.9)
              for i,color in enumerate(((.14,.12,.095),(.18,.15,.115),
                                        (.21,.18,.14),(.16,.15,.13)))]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-.235,.48))
    backing = bpy.context.object
    backing.name = "Preview wall mortar backing"
    backing.dimensions = (2.15,.13,1.78)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    backing.data.materials.append(mortar)

    # Staggered ashlar courses with softened, slightly irregular edges.
    for row in range(9):
        z, offset = -.28+row*.19, (.22 if row%2 else 0)
        col = -3
        while col*.42+offset <= 1.15:
            x = col*.42+offset
            if x >= -1.15:
                bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-.155,z))
                block = bpy.context.object
                block.name = "Preview ashlar %d %d" % (row,col)
                block.dimensions = (.405,.10,.174)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                block.data.materials.append(blocks[(row*3+col)%len(blocks)])
                bevel = block.modifiers.new("worn masonry corners","BEVEL")
                bevel.width, bevel.segments = .012, 2
                bpy.context.view_layer.objects.active = block
                bpy.ops.object.modifier_apply(modifier=bevel.name)
            col += 1

    # Restrained carved marks near the edges frame the window without distracting from it.
    carving = make_material("worn temple carving",(.22,.19,.15),0,.92)
    for x,z in ((-.78,.04),(.78,.88),(-.78,.88),(.78,.04)):
        rod("Preview carved wall motif",(x,-.098,z),(x+.07,-.098,z),.003,carving,8)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    stone = make_material("warm carved limestone",(.38,.31,.22),.04,.84)
    stone_edge = make_material("limestone highlights",(.57,.46,.31),.10,.70)
    lead = make_material("dark hammered lead",(.055,.065,.075),.72,.45)
    bronze = make_material("aged bronze fittings",(.35,.17,.055),.66,.40)
    dark = make_material("shadowed glass bed",(.012,.018,.035),.05,.42)
    blue = make_material("sapphire blue glass",(.008,.05,.38),.18,.24,(.01,.06,.35),.16)
    red = make_material("ruby red glass",(.40,.008,.025),.14,.28,(.30,.005,.012),.15)
    gold = make_material("amber gold glass",(.58,.21,.008),.16,.27,(.48,.12,.004),.14)
    green = make_material("emerald green glass",(.008,.24,.07),.16,.25,(.004,.20,.04),.16)
    pale = make_material("pale opal glass",(.32,.48,.58),.10,.24,(.20,.34,.48),.12)
    build_window((stone,stone_edge,lead,bronze,dark,blue,red,gold,green,pale))
    setup_render()
    scene = bpy.context.scene
    scene.render.filepath = str(PNG)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.camera.data.ortho_scale = 1.12
    scene.render.film_transparent = True
    bpy.ops.render.render(write_still=True)

    combine_static()
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in scene.objects if o.type == "MESH"]
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB",
                              use_selection=True, export_apply=True)
    # The wall is intentionally added after GLB export so the decoration stays mountable.
    make_preview_wall()
    scene.render.film_transparent = False
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.camera.data.ortho_scale = 2.05
    scene.camera.location = (1.42,2.7,1.25)
    target = Vector((0,-.05,.48))
    scene.camera.rotation_euler = (target-scene.camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    print("Created", GLB)


if __name__ == "__main__":
    main()
