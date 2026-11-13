"""Pinta a refem a partir de duas referencias, preservando a malha integral.

Executar com o Python do Blender. Os PNGs sao amostrados em suas dimensoes
originais; somente as coordenadas UV e os materiais do GLB sao modificados.
"""
import argparse
import bisect
import hashlib
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', default=str(Path.home() / 'Downloads/refem_garota.glb'))
parser.add_argument('--output', default=str(ROOT / 'assets/models3d/prisioneiros/menina_pele_escura.glb'))
parser.add_argument('--preview-prefix', default=str(ROOT / 'assets/models3d/prisioneiros/menina_pele_escura_preview'))
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def geometry_digest(obj):
    xyz = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    indices = np.empty(len(obj.data.loops), dtype=np.int32)
    obj.data.vertices.foreach_get('co', xyz)
    obj.data.loops.foreach_get('vertex_index', indices)
    return hashlib.sha256(xyz.tobytes() + indices.tobytes()).hexdigest()


def lerp_at(value, anchors):
    anchors = sorted(anchors)
    if value <= anchors[0][0]:
        return anchors[0][1]
    if value >= anchors[-1][0]:
        return anchors[-1][1]
    i = bisect.bisect_right([a[0] for a in anchors], value)
    a, b = anchors[i - 1], anchors[i]
    t = (value - a[0]) / (b[0] - a[0])
    return a[1] * (1 - t) + b[1] * t


def align_face_uv(obj):
    """Fit facial landmarks smoothly; keep every UV outside the face untouched."""
    # Positions in the diagnostic orthographic view, paired with pixels in the
    # original 1024x1536 front reference. These anchor the sculpted eye sockets,
    # nose, lips and chin instead of fitting them to the silhouette of the hair.
    target = np.array([(563, 465), (746, 452), (697, 560), (686, 641),
                       (664, 733), (617, 367), (458, 600), (775, 595),
                       (500, 680), (740, 700), (300, 610),
                       (350, 465), (410, 485)], dtype=float) / 1000
    source = np.array([(489, 164), (557, 156), (531, 197), (534, 227),
                       (533, 263), (518, 121), (460, 215), (580, 213),
                       (478, 248), (570, 250), (414, 211),
                       (435, 164), (451, 180)], dtype=float)
    source[:, 0] /= 1024
    source[:, 1] = 1 - source[:, 1] / 1536

    def kernel(d):
        r2 = np.sum(d * d, axis=-1)
        return .5 * r2 * np.log(np.maximum(r2, 1e-20))

    k = kernel(target[:, None] - target[None, :])
    p = np.c_[np.ones(len(target)), target]
    matrix = np.block([[k + np.eye(len(target)) * 1e-7, p],
                       [p.T, np.zeros((3, 3))]])
    coeff = np.linalg.solve(matrix, np.r_[source, np.zeros((3, 2))])

    def smooth(a, b, value):
        t = max(0., min(1., (value - a) / (b - a)))
        return t * t * (3 - 2 * t)

    def weight(co):
        return (smooth(-.15, -.12, co.x) * (1 - smooth(.13, .16, co.x))
                * smooth(.595, .625, co.z) * (1 - smooth(.815, .85, co.z))
                * (1 - smooth(-.08, -.035, co.y)))

    uv = obj.data.uv_layers.active.data
    before = np.array([tuple(loop.uv) for loop in uv])
    changed = set()
    reclassified = 0
    for face in obj.data.polygons:
        if face.material_index not in (0, 2):
            continue
        center = sum((obj.data.vertices[i].co for i in face.vertices), Vector()) / len(face.vertices)
        from_hair = face.material_index == 2
        if from_hair:
            # The old dark-pixel classification also caught small shadows on
            # the forehead and lips. They belong to the frontal face painting.
            if center.x <= -.06 or center.z >= .82 or min(weight(obj.data.vertices[obj.data.loops[li].vertex_index].co) for li in face.loop_indices) <= .25:
                continue
            face.material_index = 0
            reclassified += 1
        for li in face.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            w = weight(co)
            if w <= 0:
                continue
            q = np.array([.5 + (co.x + .035) / .53,
                          .5 - (co.z - .735) / .53])
            basis = np.r_[kernel(target - q), 1., q]
            mapped = np.clip(basis @ coeff, 0., 1.)
            uv[li].uv = mapped if from_hair else before[li] * (1 - w) + mapped * w
            changed.add(li)
    after = np.array([tuple(loop.uv) for loop in uv])
    untouched = np.array([i not in changed for i in range(len(uv))])
    assert np.array_equal(before[untouched], after[untouched])
    print('FACE ONLY:', len(changed), 'UV corners adjusted;', reclassified,
          'facial shadow triangles returned to the front material; all other UVs identical.')


class Reference:
    def __init__(self, path):
        self.image = bpy.data.images.load(str(path), check_existing=False)
        self.image.pack()
        self.width, self.height = self.image.size
        pixels = np.empty(self.width * self.height * 4, dtype=np.float32)
        self.image.pixels.foreach_get(pixels)
        self.pixels = pixels.reshape(self.height, self.width, 4)[::-1]
        alpha = self.pixels[:, :, 3]
        self.rows = []
        for row in alpha:
            valid = np.flatnonzero(row > .94)
            if len(valid):
                # Stay inside each foreground segment, away from matte edges.
                starts = np.r_[0, np.flatnonzero(np.diff(valid) > 1) + 1]
                ends = np.r_[starts[1:], len(valid)]
                inset = [valid[a + 3:b - 3] for a, b in zip(starts, ends) if b - a > 7]
                valid = np.concatenate(inset) if inset else valid
            self.rows.append(valid.tolist())
        self.nonempty = [i for i, row in enumerate(self.rows) if row]

    def foreground_row(self, y):
        y = max(0, min(self.height - 1, round(y)))
        if not self.rows[y]:
            i = bisect.bisect_left(self.nonempty, y)
            choices = self.nonempty[max(0, i - 1):i + 1]
            y = min(choices, key=lambda v: abs(v - y))
        return y, self.rows[y]

    def uv(self, fraction, y, interval=None):
        y, valid = self.foreground_row(y)
        lo, hi = interval if interval else (valid[0], valid[-1])
        x = lo + max(0., min(1., fraction)) * (hi - lo)
        # Fill lateral surfaces with nearby foreground color, never background.
        i = bisect.bisect_left(valid, x)
        choices = valid[max(0, i - 1):i + 1]
        x = min(choices, key=lambda v: abs(v - x)) if choices else valid[-1]
        return ((x + .5) / self.width, 1 - (y + .5) / self.height)

    def rgb(self, uv):
        x = max(0, min(self.width - 1, round(uv[0] * self.width)))
        y = max(0, min(self.height - 1, round((1 - uv[1]) * self.height)))
        return self.pixels[y, x, :3]


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=args.source)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
original_faces = len(obj.data.polygons)
original_vertices = len(obj.data.vertices)
original_digest = geometry_digest(obj)
coords = np.array([tuple(v.co) for v in obj.data.vertices])
zmin, zmax = coords[:, 2].min(), coords[:, 2].max()
center_x = (coords[:, 0].min() + coords[:, 0].max()) / 2
original_bounds = np.array([coords.min(axis=0), coords.max(axis=0)])

# Horizontal cross-sections fit the reference to the actual body width.
order = np.argsort(coords[:, 2])
sorted_coords = coords[order]
sorted_z = sorted_coords[:, 2]
zgrid = np.linspace(zmin, zmax, 450)
bounds = []
for z in zgrid:
    a = np.searchsorted(sorted_z, z - .018)
    b = np.searchsorted(sorted_z, z + .018)
    row = sorted_coords[a:b]
    if not len(row):
        row = sorted_coords[max(0, a - 3):min(len(coords), a + 3)]
    sections = [row]
    for sign in (-1, 1):
        leg = row[(row[:, 0] - center_x) * sign > 0]
        sections.append(leg if len(leg) else row)
    bounds.append([(r[:, 0].min(), r[:, 0].max()) for r in sections])

refs = [Reference(ROOT / 'assets/pawns/prisioneiros/menina_pele_escura.png'),
        Reference(ROOT / 'assets/pawns/prisioneiros/menina_pele_escura_costas.png')]
upper_y = [(zmax, 20), (.60, 268), (.48, 324), (.15, 552),
           (-.38, 965), (-.54, 1082)]
uv = obj.data.uv_layers.active.data
for face in obj.data.polygons:
    side = face.material_index
    ref = refs[side]
    for li in face.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        zi = max(0, min(len(zgrid) - 1, round((co.z - zmin) / (zmax - zmin) * (len(zgrid) - 1))))
        is_leg = co.z < -.54
        view_left = (co.x < center_x) if side == 0 else (co.x > center_x)
        section = (1 if co.x < center_x else 2) if is_leg else 0
        lo, hi = bounds[zi][section]
        fraction = (co.x - lo) / max(hi - lo, .00001)
        if side == 1:
            fraction = 1 - fraction
        interval = None
        if not is_leg:
            y = lerp_at(co.z, upper_y)
        else:
            # The reference includes a pedestal; sample the shoes, not the stone.
            shoe_bottom = (1267 if view_left else 1312) if side == 0 else 1280
            y = lerp_at(co.z, [(-.54, 1082), (-.73, 1165), (zmin, shoe_bottom)])
            if side == 0:
                left = [(zmin, (365, 455)), (-.83, (382, 486)), (-.54, (389, 494))]
                right = [(zmin, (612, 702)), (-.83, (582, 700)), (-.54, (567, 696))]
            else:
                left = [(zmin, (330, 440)), (-.83, (366, 475)), (-.54, (370, 490))]
                right = [(zmin, (620, 715)), (-.83, (586, 703)), (-.54, (566, 703))]
            anchors = left if view_left else right
            interval = tuple(lerp_at(co.z, [(z, pair[j]) for z, pair in anchors]) for j in (0, 1))
        # Hands finish above the tunic hem in the reference. Give their lower
        # surfaces a separate fit so fingers never sample the blue fabric.
        if -.27 < co.z < .025 and -.18 < co.y < .145 and (co.x < -.285 or co.x > .265):
            y = lerp_at(co.z, [(-.27, 802 if side == 0 else 790), (-.10, 735), (.025, 640)])
            lo_hand, hi_hand = ((-.415, -.285) if co.x < center_x else (.265, .365))
            fraction = max(0., min(1., (co.x - lo_hand) / (hi_hand - lo_hand)))
            if side == 1:
                fraction = 1 - fraction
            if side == 0:
                interval = (292, 347) if view_left else (672, 724)
            else:
                interval = (280, 335) if view_left else (686, 736)
        uv[li].uv = ref.uv(fraction, y, interval)

# A small patch of the rear reference provides curls on the side of the head.
# Mapping depth horizontally avoids stretching a single silhouette pixel into
# horizontal bands around the hair; skin and the frontal facial painting stay.
hair_faces = []
for face in obj.data.polygons:
    center = sum((obj.data.vertices[i].co for i in face.vertices), Vector()) / len(face.vertices)
    if center.z <= .60 or abs(face.normal.x) <= .5:
        continue
    average_uv = sum((uv[li].uv for li in face.loop_indices), Vector((0., 0.))) / len(face.loop_indices)
    rgb = refs[face.material_index].rgb(average_uv)
    if float(rgb.mean()) < .29 and float(rgb[0]) < .43:
        hair_faces.append(face)
hair_mat = bpy.data.materials.new('Menina pele escura - cabelo lateral')
hair_mat.use_nodes = True
obj.data.materials.append(hair_mat)
for face in hair_faces:
    face.material_index = 2
    for li in face.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        x = 420 + max(0., min(1., (co.y + .22) / .44)) * 160
        y = 70 + max(0., min(1., (zmax - co.z) / .40)) * 135
        uv[li].uv = ((x + .5) / refs[1].width, 1 - (y + .5) / refs[1].height)

# Keep the pedestal photographed behind the heels out of the shoe material.
boot_mat = bpy.data.materials.new('Menina pele escura - couro dos sapatos')
boot_mat.use_nodes = True
obj.data.materials.append(boot_mat)
for face in obj.data.polygons:
    if sum(obj.data.vertices[i].co.z for i in face.vertices) / len(face.vertices) >= -.84:
        continue
    face.material_index = 3
    for li in face.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        x = 385 + max(0., min(1., (co.y + .21) / .4)) * 60
        y = 1210 + max(0., min(1., (-.84 - co.z) / (-.84 - zmin))) * 55
        uv[li].uv = ((x + .5) / refs[0].width, 1 - (y + .5) / refs[0].height)

for i, mat in enumerate(obj.data.materials):
    mat.name = 'Menina pele escura - ' + ['frente', 'costas', 'cabelo lateral', 'couro dos sapatos'][i]
    nodes = mat.node_tree.nodes
    nodes.clear()
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = refs[0 if i in (0, 3) else 1].image
    tex.extension = 'EXTEND'
    tex.location = (-400, 0)
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Roughness'].default_value = .9
    shader.inputs['Specular IOR Level'].default_value = .15
    shader.inputs['Alpha'].default_value = 1.
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    mat.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])

align_face_uv(obj)
assert geometry_digest(obj) == original_digest, 'The source geometry was modified.'
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=args.output, export_format='GLB', export_apply=True)

# Reopen the exported artifact and confirm every original triangle remains.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=args.output)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
new_coords = np.array([tuple(v.co) for v in obj.data.vertices])
assert len(obj.data.polygons) == original_faces
assert np.max(np.abs(np.array([new_coords.min(axis=0), new_coords.max(axis=0)]) - original_bounds)) < .00001
print('GEOMETRY VERIFIED:', original_faces, 'triangles preserved;', original_vertices,
      'original vertices; geometry digest unchanged before export.')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'
center = Vector(((new_coords[:, 0].min() + new_coords[:, 0].max()) / 2,
                 (new_coords[:, 1].min() + new_coords[:, 1].max()) / 2,
                 (zmin + zmax) / 2))
camera_data = bpy.data.cameras.new('Preview camera')
camera = bpy.data.objects.new('Preview camera', camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'
camera_data.ortho_scale = (zmax - zmin) * 1.08
scene.camera = camera
for name, offset, power, size in [('Key', (-2, -3, 2), 120, 4),
                                   ('Fill', (2, -2, 0), 60, 3),
                                   ('Rear', (0, 3, 2), 120, 4)]:
    data = bpy.data.lights.new(name, 'AREA')
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = center + Vector(offset)
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
for name, offset in [('frente', (0, -5, 0)), ('costas', (0, 5, 0)),
                      ('lateral', (-5, 0, 0)), ('3d', (-3, -5, .6))]:
    camera.location = center + Vector(offset)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = args.preview_prefix + '_' + name + '.png'
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
camera.location = (-.035, -5, .735)
camera.rotation_euler = (Vector((-.035, -.04, .735)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.ortho_scale = .53
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.filepath = args.preview_prefix + '_rosto.png'
bpy.ops.render.render(write_still=True)
print('OUTPUT:', args.output, os.path.getsize(args.output))
