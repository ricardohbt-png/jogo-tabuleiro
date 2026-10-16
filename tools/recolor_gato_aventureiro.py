import argparse
import sys
from pathlib import Path
import math
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--preview', required=True)
parser.add_argument('--preview-back', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
source = Path(args.input).resolve(); out = Path(args.output).resolve()
preview = Path(args.preview).resolve(); preview_back = Path(args.preview_back).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if len(meshes) != 1:
    raise RuntimeError(f'Esperava a malha original única; encontrei {len(meshes)} malhas')
obj = meshes[0]; mesh = obj.data

# Paleta lida da referência: conversão sRGB -> linear para COLOR_0/glTF.
def srgb8(hex_color):
    h = hex_color.lstrip('#')
    vals = [int(h[i:i+2],16)/255.0 for i in (0,2,4)]
    return tuple(v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4 for v in vals)
PALETTE = {
    'fur': srgb8('#E97827'), 'fur_light': srgb8('#F79A45'),
    'cream': srgb8('#F4DFC1'), 'ear': srgb8('#D78173'),
    'cape': srgb8('#155D7B'), 'cape_light': srgb8('#287B98'),
    'leather': srgb8('#60371F'), 'leather_light': srgb8('#87532D'),
    'gold': srgb8('#C18432'), 'steel': srgb8('#8B999C'),
    'stone': srgb8('#69645A'), 'stone_light': srgb8('#827A6D'),
    'base': srgb8('#35261A'), 'eye': srgb8('#8EAA4C'),
}

# Returns one paint color for every mesh corner. Orange is the complete coat base;
# masks then paint all photo-specific markings and equipment on top of it.
def paint_color(v):
    x,y,z = v.x,v.y,v.z
    r = math.sqrt(x*x+y*y)
    # Pedestal ring and rocky top are distinct all the way around the mini.
    if z < -0.88 or (z < -0.61 and r > 0.79):
        return PALETTE['base']
    if z < -0.62:
        # A little stone variation, in the same gray-brown range as the reference.
        return PALETTE['stone_light'] if math.sin(x*23+y*19+z*17) > 0.35 else PALETTE['stone']

    # Main cape: back panel plus front sash and shoulder wrap; tail remains orange.
    if -0.58 < z < 0.55 and y > 0.16 and abs(x) < 0.66:
        return PALETTE['cape_light'] if math.sin(x*17+z*20) > 0.25 else PALETTE['cape']
    if -0.48 < z < 0.40 and y < -0.22 and -0.10 < x < 0.62:
        return PALETTE['cape_light'] if math.sin(x*16-z*24) > 0.30 else PALETTE['cape']
    if -0.08 < z < 0.37 and y < -0.30 and -0.68 < x < -0.36:
        return PALETTE['cape']

    # Leather harness and waist belt on the front of the torso.
    if -0.39 < z < 0.16 and y < -0.32 and -0.66 < x < 0.30:
        strap_line = abs(z - (0.16 - 0.57*(x + 0.60))) < 0.055
        waist_belt = -0.30 < z < -0.17 and -0.56 < x < 0.10
        holster = -0.35 < z < 0.08 and -0.05 < x < 0.22
        if strap_line or waist_belt or holster:
            return PALETTE['leather_light'] if (int((x+1)*36)%4 == 0) else PALETTE['leather']

    # Warm cream bib, muzzle, socks and paws, using visible front-facing surfaces.
    muzzle = y < -0.43 and -0.61 < x < -0.13 and 0.35 < z < 0.53 and ((x+0.38)/0.26)**2 + ((z-0.45)/0.13)**2 < 1.35
    bib = y < -0.43 and -0.48 < x < -0.16 and -0.16 < z < 0.10
    paws = y < -0.16 and -0.68 < z < -0.30 and -0.72 < x < 0.40
    if muzzle or bib or paws:
        return PALETTE['cream']

    # Pink inner ears, olive eyes, and the gold clasp are keyed to the sculpted regions.
    if z > 0.76 and y < -0.30 and (-0.68 < x < -0.48 or -0.27 < x < -0.12):
        return PALETTE['ear']
    if -0.20 < z < 0.13 and y < -0.48 and (x+0.50)**2/0.012 + (z+0.02)**2/0.006 < 1:
        return PALETTE['gold']

    # The blade/guard on the front gets steel, with a small gold hilt.
    if -0.42 < z < -0.05 and y < -0.35 and -0.18 < x < 0.08:
        if z > -0.15:
            return PALETTE['gold']
        return PALETTE['steel']

    # Slight warm highlight variation keeps the full coat painted rather than flat.
    shade = 0.96 + 0.04 * (0.5 + 0.5 * math.sin(18*x + 13*y + 21*z))
    return tuple(min(1.0,c*shade) for c in PALETTE['fur'])

attr = mesh.color_attributes.get('Color')
if attr: mesh.color_attributes.remove(attr)
attr = mesh.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
mesh.color_attributes.active_color = attr
counts = {k:0 for k in PALETTE}
for poly in mesh.polygons:
    # Vertex-domain classification blends color transitions across each triangle.
    for idx in poly.loop_indices:
        vertex = mesh.vertices[mesh.loops[idx].vertex_index]
        chosen = paint_color(vertex.co)
        attr.data[idx].color = (*chosen, 1.0)
    poly.use_smooth = True

# COLOR_0 is linked in the shader so Blender writes it into the GLB for Three.js.
mesh.materials.clear()
mat = bpy.data.materials.new('Pintura completa baseada na foto')
mat.diffuse_color = (1,1,1,1); mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (1,1,1,1); bsdf.inputs['Roughness'].default_value = 0.78
vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
mesh.materials.append(mat)
for poly in mesh.polygons: poly.material_index=0

# Fill the sculpted eye recesses with the reference's olive irises, pupils and pink nose.
def add_detail(name, location, scale, color):
    m=bpy.data.materials.new(name + ' material'); m.diffuse_color=(*color,1); m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Base Color'].default_value=(*color,1); bsdf.inputs['Roughness'].default_value=0.22
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,radius=1,location=location)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
for i,x in enumerate((-0.52,-0.29)):
    add_detail(f'Iris verde {i+1}',(x,-0.545,0.605),(0.022,0.011,0.028),PALETTE['eye'])
    add_detail(f'Pupila {i+1}',(x,-0.556,0.605),(0.004,0.006,0.019),srgb8('#17130F'))
    add_detail(f'Reflexo {i+1}',(x-0.006,-0.562,0.616),(0.003,0.003,0.004),srgb8('#FFF1D2'))
add_detail('Nariz rosado',(-0.405,-0.635,0.485),(0.023,0.012,0.015),srgb8('#D96C62'))
# Review both sides with matching lighting.
scene=bpy.context.scene
pts=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
mins=[min(p[i] for p in pts) for i in range(3)]; maxs=[max(p[i] for p in pts) for i in range(3)]
center=Vector([(a+b)/2 for a,b in zip(mins,maxs)]); extent=max(maxs[i]-mins[i] for i in range(3))
cd=bpy.data.cameras.new('Preview camera'); cam=bpy.data.objects.new('Preview camera',cd); scene.collection.objects.link(cam); cd.type='ORTHO'; cd.ortho_scale=extent*2.0; scene.camera=cam
scene.render.engine='BLENDER_EEVEE'; scene.eevee.taa_render_samples=96
scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=True
scene.world=bpy.data.worlds.new('Preview world'); scene.world.color=(0.08,0.08,0.08)
for i,(offset,power,size) in enumerate([((2,-3,5),1500,3.8),((-4,-1,2),800,3.0),((0,4,3),1000,3.4)]):
    ld=bpy.data.lights.new(f'Area {i}','AREA'); lo=bpy.data.objects.new(f'Area {i}',ld); scene.collection.objects.link(lo); lo.location=center+Vector(offset)*extent; ld.energy=power; ld.shape='DISK'; ld.size=size*extent; lo.rotation_euler=(center-lo.location).to_track_quat('-Z','Y').to_euler()
cam.location=center+Vector((0.65,-2.8,1.05))*extent; cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(preview); bpy.ops.render.render(write_still=True)
cam.location=center+Vector((0.25,3.2,1.15))*extent; cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(preview_back); bpy.ops.render.render(write_still=True)
for o in list(scene.objects):
    if o.type in {'CAMERA','LIGHT'}: bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_apply=True,export_materials='EXPORT',export_normals=True,export_skins=False,export_animations=False)
print(f'Faces pintadas com cor por vértice: {len(mesh.polygons)}; vértices/cantos coloridos: {len(attr.data)}')
print(f'Exportado: {out}')
