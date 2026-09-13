import bpy, sys
from mathutils import Vector

path=sys.argv[-2]; out=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=path)
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bb=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn=Vector((min(v.x for v in bb),min(v.y for v in bb),min(v.z for v in bb))); mx=Vector((max(v.x for v in bb),max(v.y for v in bb),max(v.z for v in bb))); center=(mn+mx)*.5; h=mx.z-mn.z
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(h*.15,-h*3.3,center.z+h*.85)); cam=bpy.context.object; look(cam,(center.x,center.y,center.z+h*.42)); cam.data.lens=58; bpy.context.scene.camera=cam
for loc,en,size in [((h*2.0,-h*3.0,center.z+h*2.8),1100,h*1.8),((-h*2,-h*1.4,center.z+h*1.5),450,h*1.6),((h*.5,h*2.2,center.z+h*1.8),550,h*1.6)]:
 bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=en; l.data.size=size; look(l,(center.x,center.y,center.z+h*.42))
bpy.ops.mesh.primitive_plane_add(size=h*8,location=(center.x,center.y,mn.z-h*.03)); f=bpy.context.object; fm=bpy.data.materials.new('preview_floor'); fm.use_nodes=True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.018,.018,.022,1); fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9; f.data.materials.append(fm)
s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=700; s.render.resolution_y=850; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.filepath=out; s.world=bpy.data.worlds.new('preview_world'); s.world.color=(.008,.008,.012); s.view_settings.look='AgX - Medium High Contrast'; bpy.ops.render.render(write_still=True)
