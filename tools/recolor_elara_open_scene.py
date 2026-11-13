import sys
from pathlib import Path
import bpy
sys.path.insert(0, r'C:\Users\RICARDO\Desktop\jogo tabuleiro\tools')
import recolor_capanga_glb as paint
root = Path(r'C:\Users\RICARDO\Desktop\jogo tabuleiro')
front = root / 'assets/models3d/prisioneiros/elara_preview.png'
back = root / 'assets/models3d/prisioneiros/elara_preview_costas.png'
out = root / 'assets/models3d/prisioneiros/elara.glb'
blend = root / 'assets/models3d/prisioneiros/elara_blender_colorida.blend'
texture_path = root / 'assets/models3d/prisioneiros/elara_blender_colorida_textura.png'
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not meshes: raise RuntimeError('Não encontrei a miniatura aberta no Blender')
image, fb, bb, size, fr, br = paint._make_texture_atlas(front, back, texture_path)
paint._project_uv(meshes, fb, bb, size, fr, br)
mat = paint._material(image)
for obj in meshes:
    obj.data.materials.clear(); obj.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', export_materials='EXPORT')
print('ELARA_COLORIDA', out, 'MESHES', len(meshes))
