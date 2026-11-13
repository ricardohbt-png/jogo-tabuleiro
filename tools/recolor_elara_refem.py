"""Paint the new Elara mesh from its front/back references and soften its sides.

Run with Blender in background; output paths are supplied after --.
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import recolor_capanga_glb as base

args = argparse.ArgumentParser()
for name in ('input', 'front', 'back', 'glb', 'blend', 'texture', 'preview'):
    args.add_argument('--' + name, type=Path, required=True)
args = args.parse_args(sys.argv[sys.argv.index('--') + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.input))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
image, fb, bb, size, fr, br = base._make_texture_atlas(args.front, args.back, args.texture)
base._project_uv(meshes, fb, bb, size, fr, br)
lo, hi = base._bounds(meshes)
height = hi.z - lo.z

def smooth(a, b, x):
    t = max(0.0, min(1.0, (x-a)/(b-a)))
    return t*t*(3-2*t)

def side_colour(z):
    # Colours sampled from the reference's pedestal, dress, belt and sleeves.
    stops = [(0.00, (0.035, 0.030, 0.028)), (0.10, (0.035, 0.030, 0.028)),
             (0.16, (0.055, 0.045, 0.035)), (0.19, (0.028, 0.026, 0.025)),
             (0.58, (0.028, 0.026, 0.025)), (0.62, (0.12, 0.065, 0.035)),
             (0.66, (0.25, 0.18, 0.12)), (0.70, (0.70, 0.60, 0.49)),
             (0.84, (0.70, 0.60, 0.49)), (0.90, (0.72, 0.64, 0.53)),
             (1.00, (0.72, 0.64, 0.53))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if z <= b:
            t = smooth(a, b, z)
            return tuple(x*(1-t)+y*t for x,y in zip(ca, cb))
    return stops[-1][1]

atlas = bpy.data.images.new('Elara pintura final', width=2048, height=2048, alpha=False)
for obj in meshes:
    mesh = obj.data
    colors = mesh.color_attributes.new(name='PinturaLateral', type='FLOAT_COLOR', domain='CORNER')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index]
            point = obj.matrix_world @ v.co
            z = max(0.0, min(1.0, (point.z-lo.z)/height))
            normal = (obj.matrix_world.to_3x3() @ v.normal).normalized()
            weight = smooth(0.38, 0.83, abs(normal.x))
            colors.data[li].color = (*side_colour(z), weight)
    mat = base._material(image)
    mesh.materials.clear()
    mesh.materials.append(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = next(n for n in nodes if n.type == 'TEX_IMAGE')
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = 'CapangaFrontBackProjection'
    links.new(uv.outputs['UV'], tex.inputs['Vector'])
    attr = nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'PinturaLateral'
    mix = nodes.new('ShaderNodeMixRGB')
    links.new(attr.outputs['Alpha'], mix.inputs[0])
    links.new(tex.outputs['Color'], mix.inputs[1]); links.new(attr.outputs['Color'], mix.inputs[2])
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    emission = nodes.new('ShaderNodeEmission')
    links.new(mix.outputs[0], emission.inputs['Color']); links.new(emission.outputs[0], output.inputs['Surface'])
    target = nodes.new('ShaderNodeTexImage'); target.image = atlas
    nodes.active = target
    uv_layer = mesh.uv_layers.new(name='ElaraAtlas')
    mesh.uv_layers.active = uv_layer; uv_layer.active_render = True
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')

scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.samples = 1
scene.render.bake.use_clear = True
bpy.ops.object.bake(type='EMIT', margin=4)
atlas.filepath_raw = str(args.texture); atlas.file_format = 'PNG'; atlas.save(); atlas.pack()
for obj in meshes:
    mat = base._material(atlas)
    uv = mat.node_tree.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'ElaraAtlas'
    tex = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
    mat.node_tree.links.new(uv.outputs['UV'], tex.inputs['Vector'])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    direct = base._material(image)
    uv_direct = direct.node_tree.nodes.new('ShaderNodeUVMap')
    uv_direct.uv_map = 'CapangaFrontBackProjection'
    direct_tex = next(n for n in direct.node_tree.nodes if n.type == 'TEX_IMAGE')
    direct.node_tree.links.new(uv_direct.outputs['UV'], direct_tex.inputs['Vector'])
    obj.data.materials.append(direct)
    colors = obj.data.color_attributes['PinturaLateral']
    for face in obj.data.polygons:
        center = obj.matrix_world @ face.center
        z = (center.z-lo.z)/height
        face_detail = z > 0.86 and center.y < -0.04 and abs(center.x) < 0.13
        if face_detail or abs(center.y) > 0.12 or all(colors.data[i].color[3] < 0.08 for i in face.loop_indices):
            face.material_index = 1
        else:
            face.material_index = 0
        face.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=str(args.blend))
bpy.ops.export_scene.gltf(filepath=str(args.glb), export_format='GLB', export_materials='EXPORT')
base._preview(meshes, args.preview.with_name(args.preview.name + '_frente.png'), 'front')
base._preview(meshes, args.preview.with_name(args.preview.name + '_costas.png'), 'back')
camera = scene.camera
lo, hi = base._bounds(meshes); center = (lo+hi)*0.5
camera.location = center + Vector((-5, -1, 1.05)); base._look_at(camera, center)
scene.render.filepath = str(args.preview.with_name(args.preview.name + '_lateral.png'))
bpy.ops.render.render(write_still=True)
