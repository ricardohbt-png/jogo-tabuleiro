"""Gera miniaturas de ancinho, forcado e balde com água para o celeiro."""
from __future__ import annotations
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"objetos"
OUT.mkdir(parents=True,exist_ok=True)


def clear():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        for b in list(blocks):
            if b.users==0: blocks.remove(b)


def mat(name,color,rough=.82):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*color,1); bs.inputs["Roughness"].default_value=rough
    return m


def cube(name,loc,dims,m,bevel=.01,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims; o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    if bevel:
        b=o.modifiers.new("Bordas arredondadas","BEVEL"); b.width=bevel; b.segments=2
        o.modifiers.new("Normais suavizadas","WEIGHTED_NORMAL")
    return o


def rod(name,a,b,r,m,vertices=10,r2=None):
    start,end=Vector(a),Vector(b); delta=end-start
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=delta.length,location=(start+end)/2)
    else: bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r2,depth=delta.length,location=(start+end)/2)
    o=bpy.context.object; o.name=name; o.rotation_euler=delta.to_track_quat("Z","Y").to_euler(); o.data.materials.append(m)
    return o


def torus(name,loc,major,minor,m,scale=(1,1,1),rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=8,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(m); return o


def point_at(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()


def finish(key,target,ortho=1.78):
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=768; s.render.resolution_y=768; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGBA"; s.render.film_transparent=True
    s.view_settings.view_transform="Standard"; s.view_settings.look="Medium High Contrast"; s.world=bpy.data.worlds.new("Fundo transparente")
    bpy.ops.object.camera_add(location=(1.6,-2.25,1.72)); cam=bpy.context.object; cam.name="Câmera da miniatura"; cam.data.type="ORTHO"; cam.data.ortho_scale=ortho; point_at(cam,target); s.camera=cam
    for name,loc,power,size,color in (("Principal",(.8,-1.5,2.4),90,1.7,(1,.84,.68)),("Preenchimento",(-1.4,-.2,1.4),46,1.5,(.78,.86,1)),("Recorte",(.5,1.2,2),62,1.3,(1,.75,.5))):
        bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.name="Luz "+name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size; l.data.color=color; point_at(l,target)
    s.render.filepath=str(OUT/(key+".png")); bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(key+".blend"))); bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="DESELECT"); objs=[o for o in s.objects if o.type=="MESH"]
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(key+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_yup=True,export_materials="EXPORT")
    print("DECOR_EXPORT",key,"meshes",len(objs))


def ancinho():
    clear(); wood=mat("Cabo de freixo",(.42,.24,.105)); grip=mat("Madeira escurecida",(.25,.13,.055)); iron=mat("Aço gasto",(.37,.40,.40),.52)
    # Cabo comprido ligeiramente inclinado; travessa dentada junto ao chão.
    rod("Cabo do ancinho",(-.02,0,.04),(.11,0,.88),.027,wood,12)
    rod("Ponteira do cabo",(.105,0,.79),(.13,0,.91),.032,grip,10)
    cube("Travessa de ferro",(.0,0,.17),(.49,.075,.055),iron,.014)
    for i in range(9):
        x=-.215+i*.054
        rod("Dente do ancinho %02d"%i,(x,-.005,.15),(x-.012,-.005,.045),.012,iron,8,r2=.003)
    cube("Abraçadeira central",(0,-.043,.17),(.085,.018,.075),grip,.008,rot=(0,-.08,0))
    finish("ancinho",(0,0,.47),1.55)


def forcado():
    clear(); wood=mat("Cabo de freixo",(.43,.25,.11)); grip=mat("Madeira escura",(.24,.12,.05)); iron=mat("Ferro forjado",(.29,.32,.32),.48)
    rod("Cabo do forcado",(-.025,0,.035),(.035,0,.78),.028,wood,12)
    rod("Ponta do cabo",(.028,0,.72),(.04,0,.84),.034,grip,10)
    # Soquete metálico e quatro dentes compridos abertos em leque.
    cube("Soquete do forcado",(.035,0,.79),(.13,.09,.14),iron,.018,rot=(0,-.08,0))
    for i,x in enumerate((-.12,-.045,.045,.12)):
        bend=x*.24
        rod("Dente do forcado %d"%i,(.035+x*.42,-.002,.82),(.035+x,-.002,.99),.015,iron,9,r2=.004)
        rod("Base do dente %d"%i,(.035+x*.10,-.002,.78),(.035+x*.42,-.002,.82),.018,iron,9)
    cube("Anel do soquete",(.035,-.05,.77),(.14,.018,.04),grip,.006)
    finish("forcado",(0,0,.50),1.58)


def balde_agua():
    clear(); wood=[mat("Balde | carvalho escuro",(.28,.15,.067)),mat("Balde | carvalho claro",(.40,.24,.11))]; iron=mat("Aros de ferro",(.24,.27,.28),.48)
    water=mat("Água azul",(.035,.29,.48),.28); ripple=mat("Reflexo na água",(.28,.72,.86),.25)
    # Corpo cônico de madeira com tábuas visíveis e fundo assentado no piso.
    n=40; verts=[]; faces=[]
    for z,r in ((.02,.205),(.42,.285)):
        for i in range(n):
            a=2*math.pi*i/n; verts.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    mesh=bpy.data.meshes.new("Corpo aberto do balde Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(wood[0]); mesh.update()
    body=bpy.data.objects.new("Corpo aberto do balde",mesh); bpy.context.collection.objects.link(body)
    body.modifiers.new("Normais","WEIGHTED_NORMAL")
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.207,depth=.035,location=(0,0,.035))
    base=bpy.context.object; base.name="Fundo de madeira do balde"; base.data.materials.append(wood[0])
    # Aduelas finas marcadas ao redor do corpo.
    for i in range(12):
        a=2*math.pi*i/12; rad=.248
        rod("Aduela %02d"%i,(rad*math.cos(a),rad*math.sin(a),.045),(rad*math.cos(a),rad*math.sin(a),.395),.011,wood[i%2],8)
    torus("Aro inferior",(0,0,.085),.202,.014,iron,(1,1,1))
    torus("Aro superior",(0,0,.405),.279,.016,iron,(1,1,1))
    cylinder=None
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.258,depth=.018,location=(0,0,.376))
    surface=bpy.context.object; surface.name="Superfície da água"; surface.data.materials.append(water)
    # Ondas e brilho discreto para distinguir água sem parecer gelo.
    torus("Onda da água",(.02,-.015,.388),.135,.006,ripple,(1,.82,.34))
    torus("Reflexo longo",(-.055,.045,.389),.075,.005,ripple,(1.2,.55,.28))
    # Asa metálica arqueada levantada; duas hastes laterais e pega de madeira.
    rod("Alça esquerda",(-.27,0,.37),(-.205,0,.67),.012,iron,8)
    rod("Alça direita",(.27,0,.37),(.205,0,.67),.012,iron,8)
    rod("Pega da alça",(-.205,0,.67),(.205,0,.67),.014,wood[1],10)
    finish("balde_agua_chao",(0,0,.34),1.45)

ancinho(); forcado(); balde_agua()
