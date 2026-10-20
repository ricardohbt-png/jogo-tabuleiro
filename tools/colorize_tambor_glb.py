"""Color the drum miniature from assets/itens/tambor.png."""
from __future__ import annotations
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def _sample(px, mask, q):
    rgb = px[mask, :3]
    if len(rgb) < 100:
        raise RuntimeError(f"Poucos pixels na paleta da referência: {len(rgb)}")
    lum = rgb @ np.array((.2126, .7152, .0722), dtype=np.float32)
    level = float(np.quantile(lum, q))
    band = rgb[np.abs(lum - level) <= .012]
    if len(band) < 8:
        band = rgb[np.argsort(np.abs(lum - level))[:128]]
    return tuple(float(v) for v in np.clip(np.median(band, axis=0), 0, 1))


def _palette(reference):
    image = bpy.data.images.load(str(reference), check_existing=False)
    px = np.asarray(image.pixels[:], dtype=np.float32).reshape((-1, 4))
    bpy.data.images.remove(image)
    rgb, alpha = px[:, :3], px[:, 3]
    r, g, b = rgb.T
    warm = (alpha > .75) & (r > g * 1.08) & (g > b * 1.08)
    gold = (alpha > .75) & (r > g * 1.28) & (g > b * 1.22)
    crimson = (alpha > .75) & (r > g * 1.22) & (r > b * 1.16) & (r < .45)
    head = (alpha > .75) & (r > g) & (g > b * 1.08) & (rgb.mean(axis=1) > .25) & ((r-g) < .30)
    return {
        "drumhead": (_sample(px, head, .58), .86, .0),
        "gold": (tuple(v * s for v, s in zip(_sample(px, gold, .42), (.92, .72, .50))), .4, .64),
        "wood": (tuple(v * s for v, s in zip(_sample(px, warm, .22), (.78, .62, .48))), .68, .05),
        "burgundy": (tuple(v * s for v, s in zip(_sample(px, crimson, .50), (.72, .58, .72))), .56, .08),
    }


def _material(name, color, roughness, metallic):
    mat = bpy.data.materials.new(f"Tambor - {name}")
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _assign(meshes, palette):
    counts = {name: 0 for name in palette}
    mats = {name: _material(name, *settings) for name, settings in palette.items()}
    indexes = {name: i for i, name in enumerate(palette)}
    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for name in palette:
            mesh.materials.append(mats[name])
        xs, ys, zs = ([v.co.axis for v in mesh.vertices] for axis in ()) if False else (None, None, None)
        xs = [v.co.x for v in mesh.vertices]; ys = [v.co.y for v in mesh.vertices]; zs = [v.co.z for v in mesh.vertices]
        cx, cy, cz = [(min(a)+max(a))*.5 for a in (xs,ys,zs)]
        hx, hy = (max(xs)-min(xs))*.5, (max(ys)-min(ys))*.5
        for face in mesh.polygons:
            p, n = face.center, face.normal
            dx, dz = p.x-cx, p.z-cz
            radius = (dx*dx + dz*dz) ** .5
            angle = np.arctan2(dz, dx)
            head = abs(n.y) > .68 and radius < .88
            rim = abs(n.y) > .48 and .87 <= radius < .98
            shell = abs(n.y) < .48 and .48 <= radius < .78
            # O couro vermelho aparece em painéis laterais; o restante do corpo
            # do tambor mantém o acabamento de madeira escura.
            red_panel = shell and abs((p.y-cy)/max(hy,1e-6)) < .24 and np.cos(angle) > .35
            mallet = p.x > cx+.62 and radius > .68
            if head:
                name = "drumhead"
            elif rim:
                name = "gold"
            elif red_panel:
                name = "burgundy"
            elif mallet or shell or radius >= .72:
                name = "wood"
            else:
                name = "wood"
            face.material_index = indexes[name]
            face.use_smooth = True
            counts[name] += 1
    if min(counts.values()) < 50:
        raise RuntimeError(f"Distribuição de materiais insuficiente: {counts}")
    return counts


def _look_at(obj, target, up="Y"):
    obj.rotation_euler = (target-obj.location).to_track_quat("-Z", up).to_euler()


def _signature(meshes):
    pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    bounds=tuple(min(p[i] for p in pts) for i in range(3))+tuple(max(p[i] for p in pts) for i in range(3))
    return sum(len(o.data.vertices) for o in meshes),sum(len(o.data.polygons) for o in meshes),bounds


def _preview(meshes, output):
    pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3))); high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(low+high)*.5; span=max(high.x-low.x,high.y-low.y,high.z-low.z,.01)
    bpy.ops.object.camera_add(location=center+Vector((.38,2.8,.55))*span)
    camera=bpy.context.object; camera.data.type="ORTHO"; camera.data.ortho_scale=span*1.38; _look_at(camera,center,"Z"); bpy.context.scene.camera=camera
    for offset,energy,size in ((Vector((-1,1.2,1.5))*span,170,span),(Vector((1,-.2,.7))*span,90,.8*span),(Vector((0,-1.5,1))*span,60,span)):
        bpy.ops.object.light_add(type="AREA",location=center+offset); light=bpy.context.object; light.data.energy=energy; light.data.shape="DISK"; light.data.size=size; _look_at(light,center)
    bpy.ops.mesh.primitive_plane_add(size=span*8,location=(center.x,low.y-.04*span,center.z))
    floor=bpy.context.object; fm=bpy.data.materials.new("Prévia - fundo"); fm.use_nodes=True
    bsdf=fm.node_tree.nodes.get("Principled BSDF"); bsdf.inputs["Base Color"].default_value=(.025,.032,.045,1); bsdf.inputs["Roughness"].default_value=.92; floor.data.materials.append(fm)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.eevee.taa_render_samples=160
    scene.render.resolution_x=1000; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(output)
    scene.world=bpy.data.worlds.new("Prévia tambor"); scene.world.color=(.006,.008,.012); scene.view_settings.look="AgX - Medium High Contrast"
    output.parent.mkdir(parents=True,exist_ok=True); bpy.ops.render.render(write_still=True)


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3: raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source,destination,preview=(Path(v).resolve() for v in args)
    reference=Path(__file__).resolve().parents[1]/"assets"/"itens"/"tambor.png"
    if not source.is_file() or not reference.is_file(): raise FileNotFoundError(source if not source.is_file() else reference)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes: raise RuntimeError("O GLB não contém malhas")
    original=_signature(meshes); counts=_assign(meshes,_palette(reference))
    destination.parent.mkdir(parents=True,exist_ok=True); bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=max(meshes,key=lambda o:len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format="GLB",use_selection=True,export_materials="EXPORT",export_normals=True,export_texcoords=True,export_cameras=False,export_lights=False)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(destination)); exported=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    final=_signature(exported) if exported else None
    if not exported or final[1]!=original[1] or not all(abs(a-b)<=1e-4 for a,b in zip(final[2],original[2])) or not any(o.data.materials for o in exported):
        raise RuntimeError(f"Geometria/exportação inesperada: original={original}, saída={final}")
    _preview(exported,preview)
    print(f"Geometria: vértices={final[0]}, faces={final[1]}, bounds={final[2]}; faces por material={counts}")
    print(f"Referência: {reference}; GLB: {destination}; prévia: {preview}")

if __name__=="__main__": main()
