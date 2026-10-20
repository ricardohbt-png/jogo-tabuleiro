"""Color the violin miniature from assets/itens/violino.png."""
from __future__ import annotations
import sys
from pathlib import Path
import bpy
from mathutils import Vector


def _palette():
    # Madeira vinho-avermelhada, ferragens douradas e detalhes de ébano,
    # conforme a referência visual e ajustados para preservar o contraste no GLB.
    return {
        # A referência usa madeira vinho-avermelhada e ferragens douradas.
        # Reforço o canal vermelho para evitar que a conversão linear do PNG
        # deixe a madeira acinzentada no renderizador do jogo.
        "wood": ((.14,.025,.018),.62,.02),
        "gold": ((.48,.24,.045),.48,.68),
        "ebony": ((.012,.009,.008),.42,.08),
    }


def _material(name,color,roughness,metallic):
    mat=bpy.data.materials.new(f"Violino - {name}");mat.diffuse_color=(*color,1);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Roughness"].default_value=roughness;bsdf.inputs["Metallic"].default_value=metallic
    return mat


def _assign(meshes,palette):
    counts={n:0 for n in palette};mats={n:_material(n,*v) for n,v in palette.items()};indexes={n:i for i,n in enumerate(palette)}
    for obj in meshes:
        mesh=obj.data;mesh.materials.clear()
        for name in palette:mesh.materials.append(mats[name])
        xs=[v.co.x for v in mesh.vertices];zs=[v.co.z for v in mesh.vertices]
        cx,cz=(min(xs)+max(xs))*.5,(min(zs)+max(zs))*.5;hx,hz=(max(xs)-min(xs))*.5,(max(zs)-min(zs))*.5
        for face in mesh.polygons:
            p,n=face.center,face.normal;nx=(p.x-cx)/max(hx,1e-6);nz=(p.z-cz)/max(hz,1e-6)
            front=abs(n.y)>.52
            # Corpo de madeira escura; escala e cordas em ébano; filetes e
            # ferragens dourados nas laterais do corpo e na cabeça do violino.
            fingerboard=front and abs(nx)<.18 and nz>-.38
            gold=front and ((abs(nx)>.68 and nz<.18) or (nz>.76 and abs(nx)>.20))
            name="ebony" if fingerboard else ("gold" if gold else "wood")
            face.material_index=indexes[name];face.use_smooth=True;counts[name]+=1
    if min(counts.values())<100:raise RuntimeError(f"Distribuição de materiais insuficiente: {counts}")
    return counts


def _signature(meshes):
    pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    bounds=tuple(min(p[i] for p in pts) for i in range(3))+tuple(max(p[i] for p in pts) for i in range(3))
    return sum(len(o.data.vertices) for o in meshes),sum(len(o.data.polygons) for o in meshes),bounds


def _look_at(obj,target):obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Z").to_euler()


def _preview(meshes,output):
    pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3)));high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(low+high)*.5;span=max(high.x-low.x,high.y-low.y,high.z-low.z,.01)
    bpy.ops.object.camera_add(location=center+Vector((.42,-2.8,1.15))*span);camera=bpy.context.object
    camera.data.type="ORTHO";camera.data.ortho_scale=span*1.32;_look_at(camera,center);bpy.context.scene.camera=camera
    for offset,energy,size in ((Vector((-.8,-1.1,1.5))*span,170,span),(Vector((1.1,.1,.7))*span,90,.8*span),(Vector((0,1,1.2))*span,60,span)):
        bpy.ops.object.light_add(type="AREA",location=center+offset);light=bpy.context.object;light.data.energy=energy;light.data.shape="DISK";light.data.size=size;_look_at(light,center)
    scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.eevee.taa_render_samples=160
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG";scene.render.film_transparent=True;scene.render.filepath=str(output)
    scene.world=bpy.data.worlds.new("Prévia violino");scene.world.color=(.006,.008,.012);scene.view_settings.look="AgX - Medium High Contrast"
    output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source,destination,preview=(Path(v).resolve() for v in args)
    reference=Path(__file__).resolve().parents[1]/"assets"/"itens"/"violino.png"
    if not source.is_file() or not reference.is_file():raise FileNotFoundError(source if not source.is_file() else reference)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes:raise RuntimeError("O GLB não contém malhas")
    original=_signature(meshes);counts=_assign(meshes,_palette());destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=max(meshes,key=lambda o:len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format="GLB",use_selection=True,export_materials="EXPORT",export_normals=True,export_texcoords=True,export_cameras=False,export_lights=False)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(destination));exported=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    final=_signature(exported) if exported else None
    if not exported or final[1]!=original[1] or not all(abs(a-b)<=1e-4 for a,b in zip(final[2],original[2])) or not any(o.data.materials for o in exported):
        raise RuntimeError(f"Geometria/exportação inesperada: original={original}, saída={final}")
    _preview(exported,preview)
    print(f"Geometria: vértices={final[0]}, faces={final[1]}, bounds={final[2]}; faces por material={counts}")
    print(f"Referência: {reference}; GLB: {destination}; prévia: {preview}")

if __name__=="__main__":main()
