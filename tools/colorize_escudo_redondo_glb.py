"""Recolor the round shield GLB using the small-shield PNG reference."""
from __future__ import annotations
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def _sample(pixels, mask, q):
    values = pixels[mask, :3]
    if len(values) < 100:
        raise RuntimeError(f"A referência tem poucos pixels para a paleta: {len(values)}")
    lum = values @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    threshold = float(np.quantile(lum, q))
    band = values[np.abs(lum - threshold) <= 0.012]
    if len(band) < 8:
        band = values[np.argsort(np.abs(lum - threshold))[:128]]
    return tuple(float(v) for v in np.clip(np.median(band, axis=0), 0.0, 1.0))


def _palette(reference):
    image = bpy.data.images.load(str(reference), check_existing=False)
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape((-1, 4))
    bpy.data.images.remove(image)
    rgb, alpha = pixels[:, :3], pixels[:, 3]
    spread = rgb.max(axis=1) - rgb.min(axis=1)
    warm = (alpha > .75) & (rgb[:, 0] > rgb[:, 1] * 1.08) & (rgb[:, 1] > rgb[:, 2] * 1.08)
    neutral = (alpha > .75) & (spread < .15) & (rgb.mean(axis=1) > .09)
    return {
        "wood": (tuple(v * .48 for v in _sample(pixels, warm, .50)), .78, .03),
        "steel": (tuple(v * .70 for v in _sample(pixels, neutral, .70)), .34, .72),
    }


def _material(name, color, roughness, metallic):
    mat = bpy.data.materials.new(f"Escudo Pequeno - {name}")
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def _assign(meshes, palette):
    counts = {name: 0 for name in palette}
    materials = {name: _material(name, *settings) for name, settings in palette.items()}
    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for mat in materials.values():
            mesh.materials.append(mat)
        xs = [v.co.x for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        radius = max(max(abs(x - cx) for x in xs), max(abs(z - cz) for z in zs))
        for face in mesh.polygons:
            dx, dz = face.center.x - cx, face.center.z - cz
            r = (dx * dx + dz * dz) ** .5 / max(radius, 1e-6)
            name = "steel" if r >= .82 or r <= .285 else "wood"
            face.material_index = 1 if name == "steel" else 0
            face.use_smooth = True
            counts[name] += 1
    if min(counts.values()) < 100:
        raise RuntimeError(f"Distribuição de cores insuficiente: {counts}")
    return counts


def _look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _signature(meshes):
    points = [obj.matrix_world @ v.co for obj in meshes for v in obj.data.vertices]
    bounds = tuple(min(p[i] for p in points) for i in range(3)) + tuple(max(p[i] for p in points) for i in range(3))
    return sum(len(o.data.vertices) for o in meshes), sum(len(o.data.polygons) for o in meshes), bounds


def _preview(meshes, output):
    points = [obj.matrix_world @ Vector(c) for obj in meshes for c in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) * .5
    span = max(high.x-low.x, high.y-low.y, high.z-low.z, .01)
    bpy.ops.object.camera_add(location=center + Vector((.45, -2.8, 1.65))*span)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.4
    _look_at(camera, center)
    bpy.context.scene.camera = camera
    for offset, energy, size in ((Vector((-.8,-1.1,1.5))*span,160,span),(Vector((1.1,.1,.7))*span,85,.8*span),(Vector((0,1,1.2))*span,60,span)):
        bpy.ops.object.light_add(type="AREA", location=center + offset)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        _look_at(light, center)
    bpy.ops.mesh.primitive_plane_add(size=span*8, location=(center.x, center.y, low.z-.035*span))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Prévia - fundo")
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(.025,.032,.045,1)
    floor_mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=.92
    floor.data.materials.append(floor_mat)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.eevee.taa_render_samples=160
    scene.render.resolution_x=1000
    scene.render.resolution_y=1000
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(output)
    scene.world=bpy.data.worlds.new("Prévia escudo pequeno")
    scene.world.color=(.006,.008,.012)
    scene.view_settings.look="AgX - Medium High Contrast"
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3: raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source,destination,preview=(Path(v).resolve() for v in args)
    reference=Path(__file__).resolve().parents[1]/"assets"/"itens"/"escudo_p.png"
    if not source.is_file() or not reference.is_file(): raise FileNotFoundError(source if not source.is_file() else reference)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes: raise RuntimeError("O GLB não contém malhas")
    original=_signature(meshes)
    counts=_assign(meshes,_palette(reference))
    destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes: obj.select_set(True)
    bpy.context.view_layer.objects.active=max(meshes,key=lambda o:len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format="GLB",use_selection=True,export_materials="EXPORT",export_normals=True,export_texcoords=True,export_cameras=False,export_lights=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    final=_signature(exported) if exported else None
    if not exported or final[1]!=original[1] or not all(abs(a-b)<=1e-4 for a,b in zip(final[2],original[2])) or not any(o.data.materials for o in exported):
        raise RuntimeError(f"Geometria/exportação inesperada: original={original}, saída={final}")
    _preview(exported,preview)
    print(f"Geometria preservada: vértices={final[0]}, faces={final[1]}, bounds={final[2]}")
    print(f"Faces por material: {counts}; referência: {reference}; GLB: {destination}; prévia: {preview}")

if __name__=="__main__": main()

