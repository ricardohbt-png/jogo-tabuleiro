"""Aplica materiais de couro e latão ao GLB do chapéu sem alterar sua geometria."""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r"C:\Users\RICARDO\Downloads\chapeu_aventureiro.glb")
OUT=ROOT/"assets"/"itens"
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
mesh_objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if len(mesh_objs)!=1: raise RuntimeError(f"Esperava uma malha, achei {len(mesh_objs)}")
obj=mesh_objs[0]; mesh=obj.data
initial=(len(mesh.vertices),len(mesh.polygons),len(mesh.edges))

def make_material(name,color,roughness,metallic=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1.0); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1.0)
    bs.inputs["Roughness"].default_value=roughness
    bs.inputs["Metallic"].default_value=metallic
    return m

# Tons inspirados na referência: couro castanho, faixa ligeiramente mais clara e fivela de latão.
leather=make_material("Couro castanho escuro",(.20,.065,.028),.76)
brim=make_material("Couro da aba | castanho quente",(.255,.085,.038),.78)
band=make_material("Faixa de couro",(.105,.032,.012),.72)
brass=make_material("Fivela de latão envelhecido",(.55,.30,.075),.42,.62)
materials=(leather,brim,band,brass)
mesh.materials.clear()
for m in materials: mesh.materials.append(m)

counts=[0]*len(materials)
for poly in mesh.polygons:
    x,y,z=poly.center
    radius=math.hypot(x,y)
    # O fecho fica no centro da face frontal, próximo à faixa inferior do chapéu.
    if y < -.43 and abs(x) < .16 and -.19 < z < -.045 and .38 < radius < .62:
        idx=3
    elif z < -.13 and radius > .60:
        idx=1
    elif -.18 < z < .035 and .34 < radius < .62:
        idx=2
    else:
        idx=0
    poly.material_index=idx
    poly.use_smooth=True
    counts[idx]+=1

scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGBA"; scene.render.film_transparent=False
scene.view_settings.view_transform="Standard"; scene.view_settings.look="Medium High Contrast"
scene.world=bpy.data.worlds.new("Preview neutro do chapéu"); scene.world.color=(.12,.12,.12)
def point_at(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(-1.8,-2.5,1.8)); camera=bpy.context.object; camera.name="Câmera de prévia"; camera.data.type="ORTHO"; camera.data.ortho_scale=2.18; point_at(camera,(0,0,-.02)); scene.camera=camera
for name,loc,power,size,color in (
    ("Principal",(.8,-1.7,2.8),30,1.8,(1.0,.84,.68)),
    ("Preenchimento",(-1.8,-.6,1.4),16,1.7,(.78,.86,1.0)),
    ("Recorte",(.5,1.7,2.2),24,1.4,(1.0,.75,.5)),
):
    bpy.ops.object.light_add(type="AREA",location=loc); light=bpy.context.object; light.name=name; light.data.energy=power; light.data.shape="DISK"; light.data.size=size; light.data.color=color; point_at(light,(0,0,-.02))

bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active=obj
preview=OUT/"chapeu_aventureiro_preview.png"; scene.render.filepath=str(preview)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"chapeu_aventureiro.blend"))
bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/"chapeu_aventureiro.glb"),export_format="GLB",use_selection=True,export_apply=True,export_yup=True,export_materials="EXPORT")
final=(len(mesh.vertices),len(mesh.polygons),len(mesh.edges))
if final!=initial: raise RuntimeError(f"A geometria mudou: antes={initial}, depois={final}")
print("HAT_COLORIZE_OK", "geometry=",initial,"materials=",counts,"glb=",OUT/"chapeu_aventureiro.glb")
