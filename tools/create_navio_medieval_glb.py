"""Cria a miniatura 3D de um navio medieval usando o PNG como referência."""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_barco_medieval_glb as core

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
random.seed(20261102)
SCALE = (1.25, 1.30, 1.15)


def profile(t: float, v: float):
    """Casco comprido, com proa e popa elevadas e seção em V."""
    end = abs(t)
    taper = max(0.0, 1.0 - end ** 1.65) ** 0.72
    half_width = 0.47 * taper * (0.16 + 0.84 * v)
    bottom = 0.11 + 0.14 * end * end
    rim = 0.73 + 0.24 * end ** 4
    z = bottom + v * (rim - bottom)
    return half_width, z


def scaled_profile(t, v):
    half, z = profile(t, v)
    return half * SCALE[1], z * SCALE[2]


def cylinder_between(name, a, b, radius, mat, vertices=12, radius_top=None):
    start, end = Vector(a), Vector(b)
    direction = end - start
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=direction.length,
                                            location=(start+end)*0.5)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=direction.length,
                                        location=(start+end)*0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


def sail_point(u, v, center_x=-0.08):
    """Surface point on the lightly billowed square sail."""
    x = center_x - 0.78 + u * 1.58
    z = 1.16 + v * 0.93
    y = -0.08 - 0.15 * math.sin(math.pi*u) * math.sin(math.pi*v)
    return (x, y, z)


def make_sail(canvas):
    verts, faces = [], []
    nx, nz = 24, 18
    for j in range(nz+1):
        v = j/nz
        for i in range(nx+1):
            u = i/nx
            verts.append(sail_point(u, v))
    for j in range(nz):
        for i in range(nx):
            a = j*(nx+1)+i
            faces.append((a, a+1, a+nx+2, a+nx+1))
    sail = core.mesh_object("Vela principal", verts, faces, canvas, smooth=True)
    solid = sail.modifiers.new("Tecido com espessura", "SOLIDIFY")
    solid.thickness = 0.014
    bpy.context.view_layer.objects.active = sail
    bpy.ops.object.modifier_apply(modifier=solid.name)
    return sail


def make_patch(u0, v0, u1, v1, mat):
    corners = [sail_point(u0,v0), sail_point(u1,v0),
               sail_point(u1,v1), sail_point(u0,v1)]
    return core.mesh_object("Remendo costurado da vela", corners, [(0,1,2,3)], mat)


def camera_and_lights(target):
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=(3.45, -4.6, 3.45))
    camera = bpy.context.object
    camera.name = "Câmera principal - navio"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.65
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for name, location, power, size, color in (
        ("Luz principal", (2.5, -3.1, 4.2), 470, 3.0, (1.0, 0.86, 0.70)),
        ("Preenchimento", (-3.0, -1.0, 2.8), 250, 3.5, (0.80, 0.87, 1.0)),
        ("Luz traseira", (0.5, 3.0, 3.6), 320, 2.5, (1.0, 0.68, 0.46)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector(target)-light.location).to_track_quat("-Z", "Y").to_euler()


def main():
    core.clear_scene()
    core.profile = profile
    wood = [
        core.material("Carvalho naval escurecido", (0.14, 0.055, 0.021)),
        core.material("Carvalho gasto", (0.20, 0.088, 0.034)),
        core.material("Carvalho profundo", (0.085, 0.030, 0.011)),
        core.material("Madeira das bordas", (0.25, 0.116, 0.044)),
    ]
    interior = core.material("Madeira do convés", (0.18, 0.078, 0.029))
    iron = core.material("Ferro naval oxidado", (0.12, 0.091, 0.071), 0.58, 0.60)
    rope = core.material("Corda de cânhamo", (0.27, 0.16, 0.07))
    canvas = core.material("Lona de vela", (0.38, 0.27, 0.15), 0.94)
    canvas_edge = core.material("Costura da lona", (0.24, 0.16, 0.085), 0.98)
    patch_mat = core.material("Remendo ocre", (0.25, 0.12, 0.055), 0.98)
    pennant_mat = core.material("Flâmula vermelho queimado", (0.15, 0.022, 0.012), 0.93)

    hull_meshes = []
    hull_meshes.append(core.make_keel(wood[2]))
    for side in (-1, 1):
        for i in range(7):
            v0 = 0.10 + i*0.125
            v1 = v0 + 0.115
            hull_meshes.append(core.make_strake(
                f"Tábua externa {side}_{i+1}", side, v0, v1,
                wood[(i+(0 if side < 0 else 1)) % len(wood)]))
        for i in range(5):
            v0 = 0.39 + i*0.12
            hull_meshes.append(core.make_strake(
                f"Tábua interna {side}_{i+1}", side, v0, min(0.99,v0+0.11),
                interior if i%2 else wood[(i+1)%len(wood)], inset=0.045))
    hull_meshes.extend(core.make_floor_boards(wood))
    for obj in hull_meshes:
        for vertex in obj.data.vertices:
            vertex.co.x *= SCALE[0]
            vertex.co.y *= SCALE[1]
            vertex.co.z *= SCALE[2]

    # Bordas contínuas e pequenas costelas visíveis no interior.
    for side in (-1,1):
        points=[]
        for i in range(37):
            t=-0.985 + 1.97*i/36
            half,z=scaled_profile(t,1.0)
            points.append((1.16*t*SCALE[0],side*half,z+0.015))
        core.tube("Borda superior do casco", points, wood[3], 0.043, 3)
    for x in (-0.82,-0.50,-0.17,0.17,0.50,0.82):
        t=x/1.16
        half,_=scaled_profile(t,0.92)
        points=[]
        for i in range(17):
            angle=math.pi*i/16
            y=-half*math.cos(angle)
            z=(0.35+0.28*abs(math.cos(angle)))*SCALE[2]
            points.append((x*SCALE[0],y,z))
        core.tube("Costela estrutural interna",points,wood[1],0.022,2)

    # Convés elevado na popa, proa reforçada e guarda-corpo simples.
    for i in range(7):
        y=(-0.24+i*0.08)*SCALE[1]
        core.box("Tábua do tombadilho",(-0.91*SCALE[0],y,0.98*SCALE[2]),
                 (0.48*SCALE[0],0.075*SCALE[1],0.065),wood[(i+1)%len(wood)],0.012)
    for x in (-1.03,1.03):
        t=x/1.16
        half,z=scaled_profile(t,0.98)
        core.box("Espelho elevado da proa ou popa",(x*SCALE[0],0,z),
                 (0.15*SCALE[0],max(0.12,half*1.75),0.35*SCALE[2]),wood[1],0.025)
    for side in (-1,1):
        for t in (-0.94,-0.72,-0.48,0.48,0.72,0.94):
            half,z=scaled_profile(t,0.98)
            x=1.16*t*SCALE[0]
            core.box("Esteio do guarda-corpo",(x,side*half,z+0.095),
                     (0.075,0.065,0.20),wood[3],0.012)
        rail=[]
        for i in range(21):
            t=-0.96 + 1.92*i/20
            half,z=scaled_profile(t,0.98)
            rail.append((1.16*t*SCALE[0],side*half,z+0.19))
        core.tube("Corrimão do convés",rail,wood[3],0.032,3)

    # Faixas e rebites de ferro no casco.
    for x0 in (-0.80,0.0,0.80):
        t=x0/1.16
        pts=[]
        for i in range(15):
            v=0.18+0.78*i/14
            half,z=scaled_profile(t,v)
            pts.append((x0*SCALE[0],-half-0.02,z))
        for i in range(14,-1,-1):
            v=0.18+0.78*i/14
            half,z=scaled_profile(t,v)
            pts.append((x0*SCALE[0],half+0.02,z))
        core.tube("Estribo de ferro",pts,iron,0.024,2)
        for side in (-1,1):
            for v in (0.28,0.52,0.76,0.94):
                half,z=scaled_profile(t,v)
                core.sphere("Rebite naval",(x0*SCALE[0],side*(half+0.032),z),0.021,iron,10)

    # Leme de popa, pendendo atrás do casco.
    cylinder_between("Eixo do leme",(-1.28*SCALE[0],0,0.76),
                     (-1.28*SCALE[0],0,0.26),0.035,wood[2],10)
    core.box("Pá do leme",(-1.29*SCALE[0],0,0.22),(0.10,0.32,0.34),wood[1],0.025)
    for side in (-1,1):
        cylinder_between("Suporte do leme",(-1.22*SCALE[0],side*0.09,0.75),
                         (-1.28*SCALE[0],side*0.09,0.48),0.025,iron,8)

    # Mastro principal, verga, vela e flâmula.
    mast_x=-0.08
    cylinder_between("Mastro principal",(mast_x,0,0.72),(mast_x,0,2.48),
                     0.073,wood[2],14,0.045)
    cylinder_between("Verga da vela",(mast_x-0.97,0,2.04),(mast_x+0.97,0,2.04),
                     0.036,wood[1],12,0.036)
    sail=make_sail(canvas)
    sail["material"]="lona cru com remendos e costura"
    # Costuras verticais da vela, acompanhando o tecido arqueado.
    for u in (0.18,0.36,0.54,0.72,0.88):
        points=[sail_point(u,i/16) for i in range(17)]
        core.tube("Costura vertical da vela",points,canvas_edge,0.006,1)
    for v in (0.10,0.90):
        points=[sail_point(i/24,v) for i in range(25)]
        core.tube("Bainha da vela",points,canvas_edge,0.009,1)
    make_patch(0.18,0.26,0.34,0.43,patch_mat)
    make_patch(0.67,0.52,0.81,0.67,patch_mat)
    # Flâmula curta no topo do mastro.
    pennant=core.mesh_object("Flâmula da gávea",
        [(mast_x,0,2.46),(mast_x+0.60,0,2.44),
         (mast_x+0.48,0,2.31),(mast_x+0.66,0,2.20)],
        [(0,1,2,3)],pennant_mat)
    pennant_solid=pennant.modifiers.new("Tecido da flâmula","SOLIDIFY")
    pennant_solid.thickness=0.012
    bpy.context.view_layer.objects.active=pennant
    bpy.ops.object.modifier_apply(modifier=pennant_solid.name)

    # Estais conectam mastro, verga, proa e popa.
    for sign in (-1,1):
        core.tube("Estai lateral",[(mast_x,sign*0.035,2.42),
                    (0.45*SCALE[0],sign*0.28,1.40),
                    (1.10*SCALE[0],sign*0.42,0.96)],rope,0.014,2)
        core.tube("Estai de popa",[(mast_x,sign*0.035,2.40),
                    (-0.75*SCALE[0],sign*0.34,1.32),
                    (-1.05*SCALE[0],sign*0.33,1.06)],rope,0.014,2)
        core.tube("Amarração da verga",[(mast_x-0.94,0,2.04),
                    (mast_x-0.86,sign*0.06,1.82),
                    (mast_x-0.72,sign*0.08,1.57)],rope,0.011,2)
    # Pequenos cabos da vela à verga para sustentar o pano.
    for u in (0.06,0.27,0.50,0.73,0.95):
        p=sail_point(u,1.0)
        core.tube("Amarração da vela",[(p[0],p[1],p[2]),(p[0],0,2.04)],rope,0.008,1)

    # Anotações de eixo e escala e fusão das peças num objeto de vários materiais.
    bpy.ops.object.select_all(action="DESELECT")
    meshes=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
    for obj in meshes:
        obj.select_set(True)
    active=meshes[0]
    bpy.context.view_layer.objects.active=active
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.join()
    ship=bpy.context.object
    ship.name="Navio Medieval"
    ship.data.name="Navio Medieval Mesh"
    ship["front_axis"]="+X (proa)"
    ship["support_face"]="keel at bottom"
    ship["source_reference"]="assets/objetos/navio_medieval.png"
    ship["intended_footprint"]="3x2 tiles"

    target=(0.0,0.0,1.10)
    camera_and_lights(target)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=1400
    scene.render.resolution_y=1100
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=True
    scene.view_settings.view_transform="Standard"
    scene.view_settings.look="Medium High Contrast"
    scene.world.color=(0.045,0.045,0.045)

    blend=OUT/"navio_medieval.blend"
    glb=OUT/"navio_medieval.glb"
    preview=OUT/"navio_medieval_preview.png"
    scene.render.filepath=str(preview)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    ship.select_set(True)
    bpy.context.view_layer.objects.active=ship
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",
                              use_selection=True,export_apply=True,
                              export_yup=True,export_materials="EXPORT")
    print("saved_blend",blend)
    print("saved_glb",glb)
    print("saved_preview",preview)
    print("source_image",OUT/"navio_medieval.png")
    print("bounds",tuple(round(v,3) for v in ship.dimensions))
    print("polygons",len(ship.data.polygons))


if __name__=="__main__":
    main()
