"""Gera uma pira de lenha carbonizada com chama animada em PNG e GLB."""
from math import cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
FLAME_GLB = OUT / "chama_viva.glb"
BLEND = OUT / "pira_chamas.blend"
GLB = OUT / "pira_chamas.glb"
PNG = OUT / "pira_chamas.png"
PREVIEW = OUT / "pira_chamas_preview.png"


def material(name, color, metallic=0.0, roughness=.85, emission=None,
             emission_strength=0.0, bump_distance=.012):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        socket = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1)
        strength = shader.inputs.get("Emission Strength")
        if strength:
            strength.default_value = emission_strength
    if bump_distance:
        noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 30
        noise.inputs["Detail"].default_value = 4
        bump = mat.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .2
        bump.inputs["Distance"].default_value = bump_distance
        mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        mat.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def finish(obj, name, mat, bevel=0):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("soft worn edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def block(name, location, size, mat, bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel)


def sphere(name, location, scale, mat, segments=18, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        radius=1, location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for face in obj.data.polygons:
        face.use_smooth = True
    return finish(obj, name, mat)


def rod(name, start, end, radius, mat, vertices=16, bevel=.004):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=delta.length, location=(a+b)*.5)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return finish(obj, name, mat, bevel)


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


def bark_crack(name, points, mat, radius=.003):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points)-1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def log(name, a, b, radius, bark, cut, char):
    """A charred bark cylinder with pale end grain and a few scorched seams."""
    a, b = Vector(a), Vector(b)
    axis = (b-a).normalized()
    obj = rod(name, a, b, radius, bark, 20, .006)
    for end, sign in ((a, -1), (b, 1)):
        pos = end + axis * sign * .004
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius*.86,
                                            depth=.012, location=pos)
        disk = bpy.context.object
        disk.rotation_mode = "QUATERNION"
        disk.rotation_quaternion = axis.to_track_quat("Z", "Y")
        finish(disk, name + " cut end grain", cut, .003)
        # Dark annual rings make the end grain visible at miniature scale.
        bpy.ops.mesh.primitive_torus_add(major_segments=24, minor_segments=6,
                                         major_radius=radius*.54, minor_radius=.0025,
                                         location=pos + axis*.007)
        ring = bpy.context.object
        ring.rotation_mode = "QUATERNION"
        ring.rotation_quaternion = axis.to_track_quat("Z", "Y")
        finish(ring, name + " growth ring", char)
    # Two irregular surface seams catch the orange firelight across the bark.
    direction = axis.cross(Vector((0,0,1)))
    if direction.length < .1:
        direction = axis.cross(Vector((0,1,0)))
    direction.normalize()
    side = direction.cross(axis).normalized()
    for offset in (-.30,.27):
        points=[]
        for i, t in enumerate((.18,.34,.49,.64,.79)):
            center = a.lerp(b,t)
            phi = offset + (0.09 if i%2 else -0.04)
            radial = (direction*cos(phi)+side*sin(phi))*(radius*.91)
            points.append(tuple(center+radial))
        bark_crack(name + " scorched bark split", points, char, .0025)
    return obj


def build_pyre(stone, stone_light, bark, bark_light, char, ember, gold):
    # A low stone ring anchors the wood to the floor tile and contains embers.
    block("Square scorched stone hearth", (0,0,.065), (.82,.78,.13), stone, .025)
    block("Inset hearth surface", (0,0,.142), (.70,.66,.035), char, .009)
    torus("Hearth bronze offering rim", (0,0,.164), .285, .009, gold)
    for i in range(8):
        a = 2*pi*i/8
        x,y = .315*cos(a),.28*sin(a)
        block("Hearth rim ashlar", (x,y,.177), (.105,.105,.055), stone_light, .009)
    # Six crossing courses form a recognizable stacked funeral/ritual pyre.
    courses = [
        (.218,.58,.105,0), (.310,.52,.095,pi/2),
        (.397,.46,.085,0), (.474,.38,.075,pi/2),
    ]
    log_index=0
    for level,(z,length,radius,rotation) in enumerate(courses):
        offset = .105 if level%2==0 else .095
        for side in (-1,1):
            lateral = side*offset
            if rotation == 0:
                a=( -length/2, lateral, z)
                b=( length/2, lateral, z+.012*(level%2))
            else:
                a=(lateral, -length/2, z)
                b=(lateral, length/2, z+.012*(level%2))
            log("Charred stacked oak log %02d"%log_index,a,b,radius,bark,bark_light,char)
            log_index += 1
    # Short diagonal crown logs leave a visible opening around the live flame.
    for i, angle in enumerate((pi/4,3*pi/4)):
        dx,dy=cos(angle)*.145,sin(angle)*.145
        log("Crown support log %02d"%i,(-dx,-dy,.535),(dx,dy,.55),.062,
            bark,bark_light,char)
    # Glowing coals and scattered ash are fixed decoration, not damage triggers.
    for i in range(13):
        a=i*2.399963229728653
        r=.045+.065*((i*7)%5)/4
        sphere("Ember in the timber gaps %02d"%i,
               (r*cos(a),r*sin(a),.31+(i%4)*.045),
               (.018,.014,.009),ember,12,8)
    for i in range(6):
        a=i*2.399963229728653
        x,y=.30*cos(a),.27*sin(a)
        sphere("Ash on the hearth %02d"%i,(x,y,.194),(.024,.017,.008),char,10,6)


def import_flames():
    if not FLAME_GLB.is_file():
        raise FileNotFoundError(FLAME_GLB)
    roots=[]
    # Three interleaved animated tongues read as a fire rising through the logs.
    for index,(location,scale,angle) in enumerate((
        ((0,-.015,.435),.37,0),
        ((.145,-.035,.405),.30,.72),
        ((-.135,.035,.415),.31,-.82),
    )):
        before=set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(FLAME_GLB))
        imported=[o for o in list(bpy.context.scene.objects) if o not in before]
        parts=[o for o in imported if o.type=="MESH"
               and o.name.split(".")[0] in {"Chama externa","Chama interna","Nucleo luminoso"}]
        if len(parts)!=3:
            raise RuntimeError("Não encontrei as malhas animadas da chama viva.")
        ember=next((o for o in imported if o.type=="MESH"
                    and o.name.split(".")[0]=="Brasa"),None)
        if ember:
            bpy.data.objects.remove(ember,do_unlink=True)
        root=bpy.data.objects.new("Pira animated flame pivot %d"%index,None)
        bpy.context.collection.objects.link(root)
        root.location=location
        root.scale=(scale,scale,scale)
        root.rotation_euler[2]=angle
        for obj in parts:
            loc,rot,mesh_scale=obj.location.copy(),obj.rotation_euler.copy(),obj.scale.copy()
            obj["preserve_animation"]=True
            obj.parent=root
            obj.matrix_parent_inverse.identity()
            obj.location,obj.rotation_euler,obj.scale=loc,rot,mesh_scale
        roots.append(root)
    return roots


def merge_static():
    curves=[o for o in bpy.context.scene.objects if o.type=="CURVE"]
    if curves:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in curves:
            obj.select_set(True)
        bpy.context.view_layer.objects.active=curves[0]
        bpy.ops.object.convert(target="MESH")
    groups={}
    for obj in bpy.context.scene.objects:
        if obj.type=="MESH" and not obj.get("preserve_animation"):
            key=obj.data.materials[0].name if obj.data.materials else "unmaterialed"
            groups.setdefault(key,[]).append(obj)
    for key,objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        if len(objects)>1:
            bpy.ops.object.join()
        objects[0].name="Flame pyre static - "+key


def setup_render():
    scene=bpy.context.scene
    target=Vector((0,0,.55))
    bpy.ops.object.camera_add(location=(1.45,-2.65,1.42))
    camera=bpy.context.object
    camera.name="Flame pyre showcase camera"
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type="ORTHO"
    camera.data.ortho_scale=1.34
    scene.camera=camera
    for name,location,energy,color,size in (
        ("Warm fire key",(.4,-1.3,1.9),155,(1,.64,.31),.9),
        ("Cool stone fill",(-1.4,-.6,1.0),70,(.54,.68,1),1.0),
        ("Firelight rim",(.8,1.0,1.45),125,(1,.30,.07),.7),
    ):
        bpy.ops.object.light_add(type="AREA",location=location)
        lamp=bpy.context.object
        lamp.name=name
        lamp.data.energy=energy
        lamp.data.shape="DISK"
        lamp.data.size=size
        lamp.data.color=color
        lamp.rotation_euler=(target-lamp.location).to_track_quat("-Z","Y").to_euler()
    scene.render.engine="BLENDER_EEVEE"
    scene.eevee.taa_render_samples=48
    scene.render.resolution_x=scene.render.resolution_y=768
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=False
    scene.view_settings.view_transform="AgX"
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.018,.016,.02,1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.24
    scene.frame_start,scene.frame_end,scene.render.fps=0,31,24
    scene.frame_set(7)


def add_preview_tile():
    tile=material("Preview only flagstone",(.11,.12,.13),0,.96,bump_distance=0)
    block("Preview only 1x1 floor tile",(0,0,-.035),(1,1,.07),tile,.015)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    stone=material("Dark temple hearth stone",(.12,.105,.085),metallic=0,
                   roughness=.96,bump_distance=.025)
    stone_light=material("Worn hearth stone edges",(.24,.205,.16),metallic=0,
                         roughness=.91,bump_distance=.018)
    bark=material("Blackened oak bark",(.055,.025,.012),metallic=0,
                  roughness=.96,bump_distance=.026)
    bark_light=material("Exposed scorched wood grain",(.12,.046,.012),metallic=0,
                        roughness=.92,bump_distance=.018)
    char=material("Deep charcoal and cracks",(.015,.009,.006),metallic=0,
                  roughness=.98,bump_distance=.008)
    ember=material("Glowing embers",(.55,.055,.003),metallic=0,roughness=.72,
                   emission=(1,.085,.002),emission_strength=1.2,bump_distance=.004)
    gold=material("Dull ritual bronze",(.28,.105,.026),metallic=.58,
                  roughness=.47,bump_distance=.006)
    build_pyre(stone,stone_light,bark,bark_light,char,ember,gold)
    flames=import_flames()
    setup_render()
    scene=bpy.context.scene
    scene.render.filepath=str(PREVIEW)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)

    scene.render.film_transparent=True
    scene.render.resolution_x=scene.render.resolution_y=512
    scene.camera.data.ortho_scale=1.18
    scene.render.filepath=str(PNG)
    bpy.ops.render.render(write_still=True)

    merge_static()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in scene.objects:
        if obj.type=="MESH" or obj in flames:
            obj.select_set(True)
    bpy.context.view_layer.objects.active=flames[0]
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format="GLB",
        use_selection=True,export_apply=True,export_animations=True,export_frame_range=True)
    add_preview_tile()
    scene.render.film_transparent=False
    scene.render.resolution_x=scene.render.resolution_y=768
    scene.camera.data.ortho_scale=1.34
    scene.render.filepath=str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    print("Created",GLB)


if __name__ == "__main__":
    main()
