"""Gera miniaturas do saco de grãos e da caixa de ferramentas para o jogo."""
from __future__ import annotations
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(blocks):
            if block.users == 0: blocks.remove(block)


def mat(name, color, rough=0.85, textured=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if textured:
        nodes, links = m.node_tree.nodes, m.node_tree.links
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 78
        noise.inputs["Detail"].default_value = 2
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.16
        bump.inputs["Distance"].default_value = 0.018
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def cube(name, loc, dims, material, bevel=0.015, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims; o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        b=o.modifiers.new("Bordas gastas", "BEVEL"); b.width=bevel; b.segments=2
        o.modifiers.new("Normais suaves", "WEIGHTED_NORMAL")
    return o


def sphere(name, loc, scale, material, rot=(0,0,0), ico=False):
    if ico: bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=loc)
    else: bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.rotation_euler=rot
    o.data.materials.append(material)
    if not ico:
        for p in o.data.polygons: p.use_smooth=True
    return o


def cylinder(name, loc, radius, depth, material, rot=(0,0,0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    b=o.modifiers.new("Borda boleada", "BEVEL"); b.width=0.008; b.segments=2
    o.modifiers.new("Normais", "WEIGHTED_NORMAL")
    return o


def torus(name, loc, major, minor, material, scale=(1,1,1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=36, minor_segments=8, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material)
    return o


def point_at(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


def finish(key, look_at, ortho=1.8):
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=768; scene.render.resolution_y=768; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=True
    scene.view_settings.view_transform="Standard"; scene.view_settings.look="Medium High Contrast"
    scene.world=bpy.data.worlds.new("Fundo transparente")
    bpy.ops.object.camera_add(location=(1.65,-2.3,1.8))
    cam=bpy.context.object; cam.name="Câmera da miniatura"; cam.data.type="ORTHO"; cam.data.ortho_scale=ortho
    point_at(cam,look_at); scene.camera=cam
    for name,loc,power,size,color in (
        ("Luz principal",(0.8,-1.5,2.5),90,1.7,(1.0,.84,.67)),
        ("Preenchimento",(-1.5,-.4,1.4),48,1.5,(.78,.85,1.0)),
        ("Recorte",(.5,1.4,2.0),62,1.2,(1.0,.75,.5)),
    ):
        bpy.ops.object.light_add(type="AREA",location=loc)
        light=bpy.context.object; light.name=name; light.data.energy=power; light.data.shape="DISK"; light.data.size=size; light.data.color=color
        point_at(light,look_at)
    scene.render.filepath=str(OUT/(key+".png"))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(key+".blend")))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT")
    meshes=[o for o in scene.objects if o.type=="MESH"]
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(key+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_yup=True,export_materials="EXPORT")
    print("DECOR_EXPORT",key,"meshes=",len(meshes))


def sack_of_grain():
    clear_scene()
    burlap=mat("Estopa | juta castanha",(.39,.255,.12),.98,True)
    burlap_light=mat("Estopa | trama clara",(.51,.36,.19),.98,True)
    seam=mat("Costura escura",(.20,.12,.06),.96)
    grain=[mat("Grãos | dourado",(.72,.50,.20),.83),mat("Grãos | palha",(.86,.68,.34),.84),mat("Grãos | sombra",(.53,.34,.12),.9)]
    # Saco abaulado em perfil, aberto no topo para identificar o conteúdo.
    profile=[(.045,.13),(.10,.24),(.23,.32),(.40,.34),(.53,.29),(.62,.205),(.64,.195)]
    n=40; verts=[]; faces=[]
    for ri,(z,r) in enumerate(profile):
        for j in range(n):
            a=2*math.pi*j/n
            ripple=1+.025*math.sin(a*7+ri*.7)+.012*math.sin(a*13-ri)
            verts.append((r*ripple*math.cos(a),r*.91*ripple*math.sin(a),z+.006*math.sin(a*5+ri)))
    for ri in range(len(profile)-1):
        for j in range(n):
            a=ri*n+j; b=ri*n+(j+1)%n
            faces.append((a,b,b+n,a+n))
    mesh=bpy.data.meshes.new("Tecido moldado Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(burlap); mesh.update()
    sack=bpy.data.objects.new("Saco de grãos de juta",mesh); bpy.context.collection.objects.link(sack)
    for p in mesh.polygons:p.use_smooth=True
    # Boca dobrada e sombra no interior.
    torus("Boca dobrada do saco",(0,0,.625),.188,.034,burlap_light,(1,.91,1))
    cylinder("Interior escuro",(0,0,.602),.171,.014,seam,vertices=40)
    # Grãos ovais cheios até perto da boca, com silhueta ondulada.
    for i in range(31):
        a=i*2.39996; r=.16*math.sqrt((i+.5)/31)
        x=r*math.cos(a); y=r*.88*math.sin(a)
        z=.625+.028*math.sin(i*1.31)
        sphere("Grão %02d"%i,(x,y,z),(.047,.026,.022),grain[i%3],rot=(.12*math.sin(i),.12*math.cos(i),a),ico=True)
    # Costura vertical e remendos perceptíveis em miniatura.
    for k in range(9):
        z=.12+k*.047
        sphere("Ponto da costura %02d"%k,(.0,-.30-(.04*math.sin(z*5)),z),(.012,.008,.009),seam,ico=True)
    for side in (-1,1):
        cube("Remendo costurado",(side*.265,-.145,.28),(.09,.018,.07),burlap_light,.01,rot=(0,side*.18,side*.22))
    finish("saco_grao",(0,0,.34),1.62)


def toolbox():
    clear_scene()
    wood=mat("Caixa | madeira escura",(.24,.12,.055),.88,True)
    wood_light=mat("Caixa | madeira mel",(.40,.23,.10),.85,True)
    dark=mat("Ferro | grafite",(.12,.14,.15),.56)
    iron=mat("Ferro | aço gasto",(.38,.40,.39),.48)
    red=mat("Cabo | couro vermelho",(.47,.095,.045),.78)
    steel=mat("Ferramentas | aço",(.48,.52,.51),.5)
    # Caixa baixa com paredes abertas e cavidade visível.
    cube("Fundo da caixa",(0,0,.14),(.74,.52,.08),wood,.025)
    cube("Frente da caixa",(0,-.235,.28),(.74,.055,.26),wood_light,.018)
    cube("Traseira da caixa",(0,.235,.28),(.74,.055,.26),wood,.018)
    cube("Lateral esquerda",(-.345,0,.28),(.055,.42,.26),wood_light,.016)
    cube("Lateral direita",(.345,0,.28),(.055,.42,.26),wood,.016)
    cube("Fundo escuro interno",(0,0,.326),(.61,.38,.018),dark,.003)
    # Tampa aberta, articulada atrás, mostrando as dobradiças metálicas.
    lid=cube("Tampa aberta",(0,.22,.53),(.77,.085,.48),wood_light,.022,rot=(math.radians(-28),0,0))
    cube("Reforço da tampa",(0,.18,.535),(.62,.025,.39),wood,.01,rot=(math.radians(-28),0,0))
    for x in (-.23,.23):
        cube("Dobradiça",(x,.236,.39),(.075,.03,.11),iron,.008,rot=(math.radians(-28),0,0))
    # Faixas, cantoneiras e fecho frontal.
    for x in (-.32,.32):
        cube("Cantoneira frontal",(x,-.267,.28),(.035,.018,.23),dark,.006)
        cube("Canto de ferro da tampa",(x,.20,.72),(.07,.025,.045),dark,.006,rot=(math.radians(-28),0,0))
    cube("Fecho",(0,-.275,.34),(.095,.022,.10),iron,.009)
    sphere("Pino do fecho",(0,-.292,.34),(.018,.012,.018),dark,ico=True)
    # Martelo: cabo, cabeça de aço e punho vermelho.
    cylinder("Cabo do martelo",(-.13,-.01,.49),.026,.39,wood_light,rot=(0,math.radians(-22),0),vertices=10)
    cube("Cabeça do martelo",(-.205,-.01,.67),(.22,.075,.075),steel,.018)
    cube("Punho do martelo",(-.20,-.01,.32),(.09,.07,.065),red,.015)
    # Chave inglesa com mordente aberto estilizado e cabo escuro.
    cube("Cabo da chave",(.10,-.02,.46),(.055,.07,.34),dark,.018,rot=(0,math.radians(16),0))
    cube("Cabeça da chave",(.15,-.02,.64),(.16,.075,.08),steel,.02,rot=(0,math.radians(16),0))
    cube("Abertura da chave",(.20,-.02,.685),(.07,.09,.06),dark,.012,rot=(0,math.radians(16),0))
    # Chave de fenda e serrote curto, com cabos legíveis.
    cylinder("Haste da chave de fenda",(.25,.08,.48),.012,.31,steel,rot=(0,math.radians(25),0),vertices=8)
    cylinder("Cabo da chave de fenda",(.31,.08,.64),.036,.12,red,rot=(0,math.radians(25),0),vertices=10)
    cube("Lâmina do serrote",(-.01,.09,.42),(.28,.045,.12),steel,.008,rot=(0,math.radians(-12),0))
    cube("Cabo do serrote",(-.16,.09,.49),(.12,.07,.13),wood_light,.02,rot=(0,math.radians(-12),0))
    # Dentes pequenos na borda da lâmina.
    for i in range(7):
        cube("Dente do serrote %02d"%i,(.015+i*.034,.065,.351),(.022,.025,.018),dark,.002,rot=(0,0,.25))
    finish("caixa_ferramentas",(0,0,.38),1.65)

sack_of_grain()
toolbox()
