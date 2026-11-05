"""Exporta a maquete aprovada sem câmera ou iluminação de revisão."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
bpy.context.view_layer.objects.active = next(obj for obj in bpy.context.selected_objects if obj.type == 'MESH')
bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=str(root / 'assets' / 'objetos' / 'mansao_medieval.glb'),
                          export_format='GLB', use_selection=True, export_yup=True)
