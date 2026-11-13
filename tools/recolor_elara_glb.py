"""Retextura Elara com as referencias de frente/costas, mantendo a superficie."""
import argparse
import hashlib
import os
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, help='GLB de origem com as duas projecoes originais.')
parser.add_argument('--output', default=str(ROOT / 'assets/models3d/prisioneiros/elara.glb'))
parser.add_argument('--preview-prefix', default=str(ROOT / 'assets/models3d/prisioneiros/elara_preview'))
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def surface_signature(obj):
    triangles = []
    for face in obj.data.polygons:
        triangles.append(tuple(sorted(tuple(round(float(x), 6) for x in obj.data.vertices[i].co) for i in face.vertices)))
    return hashlib.sha256(repr(sorted(triangles)).encode()).hexdigest()


class Reference:
    def __init__(self, path):
        self.image = bpy.data.images.load(str(path), check_existing=False)
        self.image.pack()
        self.w, self.h = self.image.size
        data = np.empty(self.w * self.h * 4, dtype=np.float32)
        self.image.pixels.foreach_get(data)
        self.data = data.reshape(self.h, self.w, 4)[::-1]
        self.rows = [np.flatnonzero(row[:, 3] > .94).tolist() for row in self.data]
        self.valid_y = [y for y, row in enumerate(self.rows) if row]

    def sample(self, uv):
        x = max(0, min(self.w - 1, round(float(uv[0]) * self.w)))
        y = max(0, min(self.h - 1, round((1 - float(uv[1])) * self.h)))
        return self.data[y, x]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=args.source)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
signature = surface_signature(obj)
original_faces = len(obj.data.polygons)
bm = bmesh.new()
bm.from_mesh(obj.data)
# Join only exactly coincident positions so normals can be shared at triangle
# borders. No subdivision, simplification, smoothing of positions or face cuts.
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
bm.to_mesh(obj.data)
bm.free()
for face in obj.data.polygons:
    face.use_smooth = True
obj.data.update()
# Gentle shading-only smoothing across the coarse facial triangles. Positions
# and the nose/eye relief stay intact; the painted face supplies fine detail.
normals = [v.normal.copy() for v in obj.data.vertices]
head = [v for v in obj.data.vertices if v.co.z > .64]
tree = KDTree(len(head))
for i, vertex in enumerate(head):
    tree.insert(vertex.co, i)
tree.balance()
for vertex in head:
    co = vertex.co
    if not (.67 < co.z < .86 and -.14 < co.x < .14 and co.y < -.06):
        continue
    neighbors = tree.find_range(co, .025)
    average = Vector()
    for _, index, distance in neighbors:
        average += normals[head[index].index] * float(np.exp(-(distance / .016) ** 2))
    if average.length:
        blend = min(1., (co.z - .67) / .025, (.86 - co.z) / .025)
        normals[vertex.index] = normals[vertex.index].lerp(average.normalized(), blend).normalized()
obj.data.normals_split_custom_set_from_vertices(normals)
assert len(obj.data.polygons) == original_faces and surface_signature(obj) == signature

refs = [Reference(ROOT / 'assets/pawns/prisioneiros/elara.png'),
        Reference(ROOT / 'assets/pawns/prisioneiros/elara_costas.png')]
assert len(obj.data.materials) == 2, 'Use the original two-material GLB as source.'
original_images = [next(n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE') for m in obj.data.materials]
obj.data.uv_layers.active.name = 'ReferenceUV'
patch_names = ['HairProjection', 'SleeveProjection', 'DressProjection']
for name in patch_names:
    obj.data.uv_layers.new(name=name)
weights = obj.data.color_attributes.new(name='ProjectionWeights', type='FLOAT_COLOR', domain='CORNER')
# Creating custom-data layers can reallocate their storage in Blender. Resolve
# the UV layers again after all allocations instead of retaining old RNA refs.
uvs = obj.data.uv_layers['ReferenceUV'].data
patches = [obj.data.uv_layers[name] for name in patch_names]

def smooth(a, b, x):
    t = max(0., min(1., (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

xyz = np.array([tuple(v.co) for v in obj.data.vertices])
zgrid = np.linspace(xyz[:, 2].min(), xyz[:, 2].max(), 300)
profile = []
for z in zgrid:
    row = xyz[np.abs(xyz[:, 2] - z) < .025]
    if not len(row):
        row = xyz[np.argsort(np.abs(xyz[:, 2] - z))[:8]]
    profile.append((row[:, 0].min(), row[:, 0].max()))

for face in obj.data.polygons:
    ref = refs[face.material_index]
    for li in face.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        zi = int(np.clip(round((co.z - zgrid[0]) / (zgrid[-1] - zgrid[0]) * (len(zgrid) - 1)), 0, len(zgrid) - 1))
        lo, hi = profile[zi]
        side = smooth(.60, .97, abs((co.x - (lo + hi) / 2) / max((hi - lo) / 2, .001)))
        sample = ref.sample(uvs[li].uv)
        side = max(side, 1 - float(sample[3]))
        if face.material_index == 0:
            px, py = float(uvs[li].uv.x) * ref.w, (1 - float(uvs[li].uv.y)) * ref.h
            facial_detail = (smooth(490, 515, px) * (1 - smooth(620, 645, px))
                             * smooth(70, 85, py) * (1 - smooth(185, 210, py)))
            side *= 1 - facial_detail
        rgb = sample[:3]
        skin = smooth(1.15, 1.36, rgb[0] / max(rgb[1], .01)) * smooth(1.04, 1.19, rgb[1] / max(rgb[2], .01))
        upper_hair = smooth(.62, .70, co.z) * (1 - skin)
        rear_hair = smooth(.25, .38, co.z) * (1 - smooth(.64, .70, co.z)) * smooth(.01, .10, co.y) * (1 - skin)
        hair = max(upper_hair, rear_hair)
        sleeve = smooth(.24, .30, co.z) * (1 - smooth(.62, .69, co.z)) * (1 - hair) * (1 - skin)
        dress = smooth(-.81, -.76, co.z) * (1 - smooth(.21, .27, co.z))
        weights.data[li].color = (side * hair, side * sleeve, side * dress, smooth(-.82, -.78, co.z))

        x = 534 + np.clip((co.y + .19) / .42, 0, 1) * 82
        y = 182 + np.clip((.96 - co.z) / .68, 0, 1) * 165
        patches[0].data[li].uv = ((x + .5) / refs[1].w, 1 - (y + .5) / refs[1].h)
        x = 664 + np.clip((co.y + .25) / .5, 0, 1) * 24
        y = 266 + np.clip((.66 - co.z) / .4, 0, 1) * 70
        patches[1].data[li].uv = ((x + .5) / refs[0].w, 1 - (y + .5) / refs[0].h)
        y = 540 + np.clip((.23 - co.z) / 1.0, 0, 1) * 620
        row = refs[0].rows[round(float(y))]
        x = row[0] + 15 + np.clip((co.y + .42) / .9, 0, 1) * max(40, 505 - row[0] - 25)
        patches[2].data[li].uv = ((x + .5) / refs[0].w, 1 - (y + .5) / refs[0].h)

atlas = bpy.data.images.new('Elara - pintura uniforme', width=4096, height=4096, alpha=False)
for i, material in enumerate(obj.data.materials):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links

    def texture(image, uv_name):
        uv_node = nodes.new('ShaderNodeUVMap')
        uv_node.uv_map = uv_name
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        tex.extension = 'EXTEND'
        links.new(uv_node.outputs['UV'], tex.inputs['Vector'])
        return tex.outputs['Color']

    def mix(a, b, factor):
        node = nodes.new('ShaderNodeMixRGB')
        links.new(a, node.inputs[1])
        links.new(b, node.inputs[2])
        links.new(factor, node.inputs[0])
        return node.outputs[0]

    attr = nodes.new('ShaderNodeVertexColor')
    attr.layer_name = 'ProjectionWeights'
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(attr.outputs['Color'], split.inputs[0])
    color = mix(texture(original_images[i], 'ReferenceUV'), texture(refs[i].image, 'ReferenceUV'), attr.outputs['Alpha'])
    for image, uv_name, channel in [(refs[1].image, 'HairProjection', 'Red'),
                                     (refs[0].image, 'SleeveProjection', 'Green'),
                                     (refs[0].image, 'DressProjection', 'Blue')]:
        color = mix(color, texture(image, uv_name), split.outputs[channel])
    emission = nodes.new('ShaderNodeEmission')
    links.new(color, emission.inputs['Color'])
    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(emission.outputs[0], output.inputs['Surface'])
    target = nodes.new('ShaderNodeTexImage')
    target.image = atlas
    nodes.active = target
    target.select = True

# Bake the continuous projection blend to a nonoverlapping UV atlas. This
# prevents different textures from switching abruptly at triangle boundaries.
atlas_uv = obj.data.uv_layers.new(name='ElaraAtlas')
obj.data.uv_layers.active = atlas_uv
atlas_uv.active_render = True
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.004)
bpy.ops.object.mode_set(mode='OBJECT')
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.render.bake.use_clear = True
bpy.ops.object.bake(type='EMIT', margin=4)
scene.render.engine = 'BLENDER_EEVEE'
bpy.context.view_layer.update()
atlas.pack()

final_material = bpy.data.materials.new('Elara - pintura natural')
final_material.use_nodes = True
nodes = final_material.node_tree.nodes
shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
shader.inputs['Roughness'].default_value = .9
shader.inputs['Specular IOR Level'].default_value = .15
tex = nodes.new('ShaderNodeTexImage')
tex.image = atlas
uv_node = nodes.new('ShaderNodeUVMap')
uv_node.uv_map = 'ElaraAtlas'
final_material.node_tree.links.new(uv_node.outputs[0], tex.inputs['Vector'])
final_material.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
original_side = [face.material_index for face in obj.data.polygons]
direct_region = []
weights = obj.data.color_attributes['ProjectionWeights']
for face in obj.data.polygons:
    colors = [weights.data[li].color for li in face.loop_indices]
    no_wrap = all(max(c[:3]) < .005 for c in colors)
    direct_region.append(1 if no_wrap and all(c[3] > .999 for c in colors)
                         else (2 if no_wrap and all(c[3] < .001 for c in colors) else 0))
obj.data.materials.clear()
obj.data.materials.append(final_material)
for i, image in enumerate([refs[0].image, refs[1].image, original_images[0], original_images[1]]):
    mat = bpy.data.materials.new('Elara - ' + ['frente detalhada', 'costas detalhadas', 'base frente', 'base costas'][i])
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value = .9
    bsdf.inputs['Specular IOR Level'].default_value = .15
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image
    uv_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = 'ReferenceUV'
    mat.node_tree.links.new(uv_node.outputs[0], image_node.inputs['Vector'])
    mat.node_tree.links.new(image_node.outputs['Color'], bsdf.inputs['Base Color'])
    obj.data.materials.append(mat)
for face in obj.data.polygons:
    region = direct_region[face.index]
    face.material_index = (1 + original_side[face.index] if region == 1 else
                           (3 + original_side[face.index] if region == 2 else 0))
for name in [layer.name for layer in obj.data.uv_layers]:
    if name not in ('ElaraAtlas', 'ReferenceUV'):
        obj.data.uv_layers.remove(obj.data.uv_layers[name])
obj.data.color_attributes.remove(obj.data.color_attributes['ProjectionWeights'])

assert surface_signature(obj) == signature
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=args.output, export_format='GLB', export_apply=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=args.output)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
assert len(obj.data.polygons) == original_faces and surface_signature(obj) == signature
print('VERIFIED:', original_faces, 'triangles, identical surface; continuous reference painting baked to atlas.')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
points = np.array([tuple(v.co) for v in obj.data.vertices])
center = Vector(tuple((points.min(0) + points.max(0)) / 2))
data = bpy.data.cameras.new('Preview camera')
camera = bpy.data.objects.new('Preview camera', data)
scene.collection.objects.link(camera)
data.type = 'ORTHO'
data.ortho_scale = 2.2
scene.camera = camera
for name, offset, energy, size in [('Key', (-2, -3, 2), 120, 4), ('Fill', (2, -2, 0), 60, 3), ('Rear', (0, 3, 2), 120, 4)]:
    ld = bpy.data.lights.new(name, 'AREA')
    light = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(light)
    light.location = center + Vector(offset)
    ld.energy = energy
    ld.shape = 'DISK'
    ld.size = size
    light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
for name, offset in [('frente', (0, -5, 0)), ('costas', (0, 5, 0)), ('lateral', (-5, 0, 0)), ('3d', (-3, -5, .5))]:
    camera.location = center + Vector(offset)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = args.preview_prefix + '_' + name + '.png'
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
camera.location = (-.02, -5, .79)
camera.rotation_euler = (Vector((-.02, -.1, .79)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
data.ortho_scale = .43
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.filepath = args.preview_prefix + '_rosto.png'
bpy.ops.render.render(write_still=True)
print('OUTPUT:', args.output, os.path.getsize(args.output))
