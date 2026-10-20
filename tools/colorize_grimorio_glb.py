"""Color the grimoire miniature from the in-game PNG reference."""
from __future__ import annotations
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def _sample(pixels, mask, q):
    rgb = pixels[mask, :3]
    if len(rgb) < 100:
        raise RuntimeError(f"Poucos pixels na paleta de referência: {len(rgb)}")
    lum = rgb @ np.array((.2126, .7152, .0722), dtype=np.float32)
    level = float(np.quantile(lum, q))
    band = rgb[np.abs(lum - level) <= .012]
    if len(band) < 8:
        band = rgb[np.argsort(np.abs(lum - level))[:128]]
    return tuple(float(x) for x in np.clip(np.median(band, axis=0), 0, 1))


def _palette(reference):
    image = bpy.data.images.load(str(reference), check_existing=False)
    px = np.asarray(image.pixels[:], dtype=np.float32).reshape((-1, 4))
    bpy.data.images.remove(image)
    rgb, alpha = px[:, :3], px[:, 3]
    spread = rgb.max(axis=1) - rgb.min(axis=1)
    gold = (alpha > .75) & (rgb[:, 0] > rgb[:, 1] * 1.12) & (rgb[:, 1] > rgb[:, 2] * 1.10)
    blue = (alpha > .75) & (rgb[:, 2] > rgb[:, 0] * 1.30) & (rgb[:, 2] > rgb[:, 1] * 1.10)
    page = (alpha > .75) & (spread < .40) & (rgb.mean(axis=1) > .30) & (rgb[:, 0] > rgb[:, 2] * 1.35) & (rgb[:, 1] > rgb[:, 2] * 1.12) & ((rgb[:, 0] - rgb[:, 1]) < .32)
    return {
        "blue_leather": (tuple(v * .52 for v in _sample(px, blue, .14)), .62, .08),
        "gold": (tuple(v * scale for v, scale in zip(_sample(px, gold, .26), (.86, .58, .38))), .44, .52),
        "parchment": (_sample(px, page, .56), .82, .01),
    }


def _material(name, color, roughness, metallic):
    mat = bpy.data.materials.new(f"Grimório - {name}")
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _assign(meshes, palette):
    counts = {n: 0 for n in palette}
    mats = {n: _material(n, *v) for n, v in palette.items()}
    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for n in palette:
            mesh.materials.append(mats[n])
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        cx, cy, cz = [(min(v) + max(v)) / 2 for v in (xs, ys, zs)]
        hx, hy, hz = [(max(v) - min(v)) / 2 for v in (xs, ys, zs)]
        idx = {n:i for i,n in enumerate(palette)}
        for face in mesh.polygons:
            p, n = face.center, face.normal
            nx = (p.x-cx) / max(hx, 1e-6)
            ny = (p.y-cy) / max(hy, 1e-6)
            nz = (p.z-cz) / max(hz, 1e-6)
            front = abs(n.z) > .52
            # O bloco de páginas ocupa a borda inferior; as capas continuam
            # azuis e as ferragens douradas ficam nos cantos e no fecho.
            is_page = (ny < -.48 and -.72 < nx < .82)
            is_gold = front and (
                (abs(nx) > .72 and abs(ny) > .60)
                or (nx > .76 and -.06 < ny < .22)
                or nx < -.86
            )
            name = "parchment" if is_page else ("gold" if is_gold else "blue_leather")
            face.material_index = idx[name]
            face.use_smooth = True
            counts[name] += 1
    if min(counts.values()) < 100:
        raise RuntimeError(f"Distribuição de materiais insuficiente: {counts}")
    return counts


def _look_at(obj, target):
    obj.rotation_euler = (target-obj.location).to_track_quat("-Z", "Y").to_euler()


def _signature(meshes):
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    bounds = tuple(min(p[i] for p in pts) for i in range(3)) + tuple(max(p[i] for p in pts) for i in range(3))
    return sum(len(o.data.vertices) for o in meshes), sum(len(o.data.polygons) for o in meshes), bounds


def _render_preview(meshes, output):
    pts=[o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3))); high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(low+high)*.5; span=max(high.x-low.x,high.y-low.y,high.z-low.z,.01)
    bpy.ops.object.camera_add(location=center+Vector((.28,-.18,2.8))*span)
    camera=bpy.context.object; camera.data.type="ORTHO"; camera.data.ortho_scale=span*1.4; _look_at(camera,center); bpy.context.scene.camera=camera
    for offset,energy,size in ((Vector((-.8,-1.1,1.5))*span,160,span),(Vector((1.1,.1,.7))*span,85,.8*span),(Vector((0,1,1.2))*span,60,span)):
        bpy.ops.object.light_add(type="AREA",location=center+offset); light=bpy.context.object; light.data.energy=energy; light.data.shape="DISK"; light.data.size=size; _look_at(light,center)
    bpy.ops.mesh.primitive_plane_add(size=span*8,location=(center.x,center.y,low.z-.035*span))
    floor=bpy.context.object; fm=bpy.data.materials.new("Prévia - fundo"); fm.use_nodes=True
    bsdf=fm.node_tree.nodes.get("Principled BSDF"); bsdf.inputs["Base Color"].default_value=(.025,.032,.045,1); bsdf.inputs["Roughness"].default_value=.92; floor.data.materials.append(fm)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.eevee.taa_render_samples=160
    scene.render.resolution_x=1000; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(output)
    scene.world=bpy.data.worlds.new("Prévia grimório"); scene.world.color=(.006,.008,.012); scene.view_settings.look="AgX - Medium High Contrast"
    output.parent.mkdir(parents=True,exist_ok=True); bpy.ops.render.render(write_still=True)


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3: raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source,destination,preview=(Path(v).resolve() for v in args)
    reference=Path(__file__).resolve().parents[1]/"assets"/"itens"/"grimorio.png"
    if not source.is_file() or not reference.is_file(): raise FileNotFoundError(source if not source.is_file() else reference)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes: raise RuntimeError("O GLB não contém malhas")
    original=_signature(meshes); counts=_assign(meshes,_palette(reference))
    destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=max(meshes,key=lambda o:len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format="GLB",use_selection=True,export_materials="EXPORT",export_normals=True,export_texcoords=True,export_cameras=False,export_lights=False)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(destination)); exported=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    final=_signature(exported) if exported else None
    if not exported or final[1]!=original[1] or not all(abs(a-b)<=1e-4 for a,b in zip(final[2],original[2])) or not any(o.data.materials for o in exported):
        raise RuntimeError(f"Geometria/exportação inesperada: origem={original}, saída={final}")
    _render_preview(exported,preview)
    print(f"Geometria: vértices={final[0]}, faces={final[1]}, bounds={final[2]}; faces por material={counts}")
    print(f"Referência: {reference}; GLB: {destination}; prévia: {preview}")

if __name__=="__main__": main()
