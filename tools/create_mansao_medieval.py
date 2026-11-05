"""Constrói a maquete e uma prévia para revisão; não exporta o GLB."""
from pathlib import Path
import math
import random
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'objetos'
random.seed(43)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
    return m

stone=material('Calcário claro',(.58,.51,.40)); pale=material('Reboco',(.78,.68,.51))
trim=material('Madeira escura',(.19,.095,.045)); roof=material('Ardósia azul',(.14,.19,.24))
roof_alt=material('Ardósia clara',(.20,.25,.30)); glass=material('Vidro âmbar',(.70,.39,.10))
gold=material('Metal dourado',(.70,.43,.09)); red=material('Estandarte carmesim',(.46,.045,.035))
leaf=material('Folhagem',(.12,.25,.075)); door=material('Porta madeira',(.32,.15,.06))

def box(name, p, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('Bordas','BEVEL'); m.width=bevel; m.segments=2
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=m.name)
    return o

def beam(name,a,b,width,mat):
    a,b=Vector(a),Vector(b); d=b-a
    o=box(name,(a+b)/2,(width,width,d.length),mat)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def roof_gable(name, cx,cy,w,depth,eave,ridge):
    vertices=[(cx-w/2,cy-depth/2,eave),(cx+w/2,cy-depth/2,eave),(cx,cy-depth/2,ridge),
              (cx-w/2,cy+depth/2,eave),(cx+w/2,cy+depth/2,eave),(cx,cy+depth/2,ridge)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],[(0,3,5,2),(2,5,4,1),(0,2,1),(3,4,5)]); mesh.materials.append(roof); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    for y in (cy-depth/2,cy+depth/2):
        beam('Beiral', (cx-w/2,y,eave),(cx,y,ridge),.08,trim)
        beam('Beiral', (cx,y,ridge),(cx+w/2,y,eave),.08,trim)
    beam('Cumeeira',(cx,cy-depth/2,ridge),(cx,cy+depth/2,ridge),.07,trim)

def window_front(x,z,scale=1):
    box('Janela vitral',(x,-1.933,z),(.42*scale,.035,.65*scale),glass,.02)
    for side in (-1,1):
        box('Moldura janela',(x+side*.23*scale,-1.96,z),(.055,.05,.76*scale),stone)
    for dz in (-.37,.37): box('Moldura janela',(x,-1.96,z+dz*scale),(.51*scale,.05,.055),stone)
    for dx in (-.10,.10): box('Caixilho vertical',(x+dx*scale,-1.99,z),(.025,.025,.65*scale),trim)
    for dz in (-.13,.13): box('Caixilho horizontal',(x,-1.99,z+dz*scale),(.42*scale,.025,.025),trim)

box('Fundação',(0,0,.15),(5.5,4.15,.30),stone,.06)
box('Paredes de pedra',(0,0,1.45),(5.15,3.8,2.45),stone,.035)
box('Segundo piso de reboco',(0,0,2.85),(5.05,3.75,.65),pale,.02)
for x in (-2.5,-1.6,-.85,0,.85,1.6,2.5):
    box('Viga vertical',(x,-1.91,2.86),(.10,.10,.70),trim)
for z in (2.51,3.18): box('Viga horizontal',(0,-1.93,z),(5.15,.1,.11),trim)
for x in (-1.85,-1.10,1.10,1.85): window_front(x,1.60)
for x in (-1.5,-.75,.75,1.5): window_front(x,2.88,.70)
box('Porta dupla',(0,-1.96,1.02),(1.0,.09,1.65),door,.04)
for x in (-.52,0,.52): box('Porta moldura',(x,-2.04,1.02),(.07,.08,1.74),trim)
for z in (.48,1.35): box('Ferragem da porta',(0,-2.08,z),(.85,.035,.06),trim)
for x in (-.22,.22):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.065,location=(x,-2.11,1.04)); bpy.context.object.data.materials.append(gold)
for i in range(3): box('Degrau',(0,-2.05-i*.20,.30-i*.08),(1.55+i*.18,.40,.16),stone,.02)
for x in (-2.5,2.5):
    box('Torre lateral',(x,0,1.66),(.30,3.9,3.05),stone,.025)
roof_gable('Telhado principal',0,0,5.6,4.0,3.12,4.72)
for x in (-1.75,1.75):
    box('Chaminé',(x,.48,4.18),(.46,.48,1.45),stone,.03)
    box('Topo chaminé',(x,.48,4.92),(.56,.58,.12),stone,.02)
    for dx in (-.12,.12):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.08,depth=.22,location=(x+dx,.48,5.08)); bpy.context.object.data.materials.append(door)
for x in (-.75,.75):
    box('Bandeira',(x,-1.99,2.02),(.30,.03,.68),red)
    box('Haste bandeira',(x,-2.01,2.39),(.40,.04,.05),gold)
    box('Sinal heráldico',(x,-2.04,2.03),(.055,.025,.25),gold)
for x in (-2.02,2.02):
    for j in range(7):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.11,location=(x+random.uniform(-.08,.08),-1.98,.5+j*.30))
        bpy.context.object.name='Hera'; bpy.context.object.data.materials.append(leaf)

# Frontão de destaque, vitral central e estrutura de madeira.
mesh=bpy.data.meshes.new('Frontão nobre')
mesh.from_pydata([(-1.05,-2.08,3.13),(1.05,-2.08,3.13),(0,-2.08,4.24)],[],[(0,1,2)])
mesh.materials.append(pale); mesh.update()
gable=bpy.data.objects.new('Frontão nobre',mesh); bpy.context.collection.objects.link(gable)
beam('Moldura do frontão',(-1.08,-2.11,3.13),(0,-2.11,4.26),.10,trim)
beam('Moldura do frontão',(0,-2.11,4.26),(1.08,-2.11,3.13),.10,trim)
box('Vitral nobre',(0,-2.12,3.53),(.70,.04,.55),glass,.015)
for x in (-.24,0,.24): box('Caixilho vitral',(x,-2.16,3.53),(.035,.03,.58),trim)
for z in (3.25,3.52,3.81): box('Moldura vitral',(0,-2.16,z),(.76,.03,.035),trim)
for x in (-2.68,2.68):
    for y in (-1.20,-.40,.40,1.20):
        for z in (1.55,2.72):
            box('Janela lateral',(x,y,z),(.04,.42,.58),glass,.012)
            for dy in (-.24,.24): box('Moldura lateral',(x,y+dy,z),(.07,.05,.68),stone)
            for dz in (-.34,.34): box('Moldura lateral',(x,y,z+dz),(.07,.53,.05),stone)
            box('Caixilho lateral',(x*1.005,y,z),(.025,.035,.58),trim)
for z in (.58,1.00,1.42,1.84,2.26):
    box('Fiada frontal',(0,-1.907,z),(5.05,.018,.015),pale)
    for x in (-2.66,2.66): box('Fiada lateral',(x,0,z),(.018,3.70,.015),pale)
# Telhas em fileiras, sobre os dois planos do telhado.
for side in (-1,1):
    for row in range(1,12):
        frac=row/12
        x=side*2.8*frac; z=4.72-(4.72-3.12)*frac+.015
        beam('Fileira de ardósia',(x,-1.98,z),(x,1.98,z),.012,roof_alt)
    for col in range(1,13):
        y=-2+4*col/13
        beam('Junta de ardósia',(0,y,4.73),(side*2.8,y,3.13),.009,roof_alt)

# Iluminação e câmera apenas para revisão, não integram a miniatura.
bpy.ops.object.camera_add(location=(8,-10,8)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,2))-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='ORTHO'; camera.data.ortho_scale=8.8
bpy.context.scene.camera=camera
bpy.ops.object.light_add(type='AREA',location=(1,-6,10)); light=bpy.context.object; light.data.energy=1100; light.data.shape='DISK'; light.data.size=9
light.rotation_euler=(Vector((0,0,2))-light.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/'mansao_medieval_previa.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mansao_medieval.blend'))
bpy.ops.render.render(write_still=True)
