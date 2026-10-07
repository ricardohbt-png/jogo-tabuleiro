"""Renderiza as decorações sobre o plano de chão usado pelo cliente 3D."""
import re
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'objetos'
source = (ROOT / 'game.js').read_text(encoding='utf-8')
config = re.search(r'const DECOR_GLB_GROUND_Y = Object.freeze\(\{(.*?)\}\);', source, re.S).group(1)
anchors = dict((name, float(value)) for name, value in
               re.findall(r"'([^']+)': ([\d.]+)", config))

for slug, width in [('oasis_pequeno', 5.0), ('estatua_soterrada', 1.25)]:
    bpy.ops.wm.open_mainfile(filepath=str(ASSETS / (slug + '.blend')))
    # O chão cobre a geometria inferior como os tiles opacos do jogo.
    bpy.ops.mesh.primitive_plane_add(size=width,
                                    location=(0, 0, anchors[slug + '.glb'] - 0.005))
    floor = bpy.context.object
    floor.name = 'Piso de areia | referência do tabuleiro'
    material = bpy.data.materials.new('Areia do piso')
    material.diffuse_color = (0.54, 0.38, 0.19, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = material.diffuse_color
    shader.inputs['Roughness'].default_value = 0.95
    floor.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 800
    scene.render.filepath = str(ASSETS / (slug + '_grounded_preview.png'))
    bpy.ops.render.render(write_still=True)
    print('GROUND_PREVIEW', slug, 'anchor=', anchors[slug + '.glb'])
