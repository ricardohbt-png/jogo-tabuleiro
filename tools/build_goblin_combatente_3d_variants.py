"""Build/review the approved Goblin Combatant GLB family locally with Blender.

Run: blender --background --python tools/build_goblin_combatente_3d_variants.py
Only equipment geometry is authored here. The body is copied from the approved
candidate (original POSITION/UV/JPEG), and the original axe asset is copied intact.
"""
import copy, hashlib, json, math, shutil, struct
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/models3d/monstros'
REVIEW = ROOT / '.superpowers/sdd/2026-10-08-goblin-combatant-gear-variants/samples'
BASE = OUT / 'goblin_combatente.glb'
CANDIDATE = OUT / 'goblinCombatente_lanca_curta_com_escudo.glb'
WEAPONS = ('lanca_curta', 'bordao', 'cajado_madeira', 'shortsword', 'maca', 'machado_basico')
DTYPES = {5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'}
WIDTHS = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}

def read_glb(path):
    blob = Path(path).read_bytes()
    assert blob[:4] == b'glTF'
    size, kind = struct.unpack_from('<II', blob, 12)
    doc = json.loads(blob[20:20+size])
    start = 20+size
    binary_size, kind = struct.unpack_from('<II',blob,start)
    return doc, blob[start+8:start+8+binary_size]

def accessor(source, idx):
    doc, binary = source
    a = doc['accessors'][idx]; v = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype(DTYPES[a['componentType']]); width = WIDTHS[a['type']]
    offset = v.get('byteOffset',0)+a.get('byteOffset',0)
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=offset,
                      strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()

def primitives(source, side=None):
    result=[]
    for p in source[0]['meshes'][0]['primitives']:
        if p['material']==0: continue
        indices=accessor(source,p['indices']).reshape(-1,3)
        positions=accessor(source,p['attributes']['POSITION'])
        positive=positions[indices].mean(axis=1)[:,0]>0
        mask=positive if side=='shield' else ~positive
        if mask.any(): result.append((source,p,indices[mask]))
    return result

def compose(parts,path):
    """Bake one node/mesh while preserving exact body attribute/image bytes."""
    doc={'asset':{'version':'2.0','generator':'LFH Blender 5.1.2 equipment family'},
         'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':path.stem}],
         'meshes':[{'name':path.stem,'primitives':[]}], 'materials':[], 'textures':[],
         'images':[], 'samplers':[], 'accessors':[], 'bufferViews':[], 'buffers':[]}
    binary=bytearray(); maps={}
    def view(data,target=None):
        while len(binary)%4: binary.append(0)
        v={'buffer':0,'byteOffset':len(binary),'byteLength':len(data)}
        if target: v['target']=target
        idx=len(doc['bufferViews']); doc['bufferViews'].append(v); binary.extend(data); return idx
    def resource(source,category,idx):
        key=(id(source),category,idx)
        if key in maps: return maps[key]
        value=copy.deepcopy(source[0][category][idx]); new=len(doc[category]); maps[key]=new
        doc[category].append(value)
        if category=='materials':
            for prop in ('baseColorTexture','metallicRoughnessTexture'):
                tex=value.get('pbrMetallicRoughness',{}).get(prop)
                if tex: tex['index']=resource(source,'textures',tex['index'])
        if category=='textures':
            value['source']=resource(source,'images',value['source'])
            if 'sampler' in value: value['sampler']=resource(source,'samplers',value['sampler'])
        if category=='images':
            old=source[0]['bufferViews'][value['bufferView']]; off=old.get('byteOffset',0)
            value['bufferView']=view(source[1][off:off+old['byteLength']])
        return new
    def array(data,kind,component,target):
        a={'bufferView':view(data.tobytes(),target),'componentType':component,'count':len(data),'type':kind}
        if kind=='VEC3': a.update(min=data.min(axis=0).tolist(),max=data.max(axis=0).tolist())
        idx=len(doc['accessors']); doc['accessors'].append(a); return idx
    for source,p,indices in parts:
        attrs={}; indices=np.asarray(indices,dtype=np.uint32).reshape(-1)
        used,inverse=np.unique(indices,return_inverse=True)
        for name,idx in p['attributes'].items():
            if name=='NORMAL': continue # match original flat-faceted body export
            old=source[0]['accessors'][idx]
            attrs[name]=array(accessor(source,idx)[used],old['type'],old['componentType'],34962)
        ind=inverse.astype('<u2' if len(used)<65536 else '<u4').reshape(-1,1)
        doc['meshes'][0]['primitives'].append({'attributes':attrs,
            'indices':array(ind,'SCALAR',5123 if len(used)<65536 else 5125,34963),
            'material':resource(source,'materials',p['material'])})
    doc['buffers']=[{'byteLength':len(binary)}]
    payload=json.dumps(doc,separators=(',',':')).encode(); payload+=b' '*((-len(payload))%4)
    binary+=b'\0'*((-len(binary))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(payload)+len(binary))+
        struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary)

def material(name,color,metal=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=.8
    return m

def cylinder(name,a,b,r,mat,verts=8,r2=None):
    a,b=Vector(a),Vector(b); delta=b-a
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=delta.length,location=(a+b)/2)
    else: bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=delta.length,location=(a+b)/2)
    ob=bpy.context.object; ob.name=name; ob.rotation_mode='QUATERNION'
    ob.rotation_quaternion=Vector((0,0,1)).rotation_difference(delta.normalized()); ob.data.materials.append(mat)
    return ob

def mesh(name,verts,faces,mat):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def build_weapon(weapon):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    wood=material('Madeira_arma',(0.105,.056,.023))
    woodlight=material('Madeira_cajado',(.17,.088,.032))
    iron=material('Ferro_envelhecido',(.22,.25,.24),.42)
    leather=material('Couro_empunhadura',(.053,.032,.019))
    grip=Vector((-.650,-.110,-.075)); axis=Vector((-.14,-.91,-.39)).normalized()
    p=lambda t:grip+axis*t
    if weapon=='bordao':
        cylinder('Bordao_reto',p(-.47),p(.67),.030,wood)
        cylinder('Bordao_pega',p(-.08),p(.10),.033,leather)
        for t in (-.45,.63): cylinder('Bordao_ponteira',p(t),p(t+.045),.032,iron)
    elif weapon=='cajado_madeira':
        cylinder('Cajado_longo_madeira',p(-.44),p(.58),.034,woodlight,7,r2=.043)
        # A forked, crooked wood crown distinguishes the wood staff from the staff.
        tip=p(.58); crown=tip+Vector((.04,-.17,.025))
        cylinder('Cajado_curva',tip,crown,.043,woodlight,7,r2=.059)
        cylinder('Cajado_coroa',crown,crown+Vector((.075,-.10,.065)),.056,woodlight,7,r2=.037)
        cylinder('Cajado_ramo',crown,crown+Vector((-.067,-.055,-.045)),.033,woodlight,6,r2=.017)
        for t in (-.11,-.065,-.02): cylinder('Cajado_corda',p(t),p(t+.022),.038,leather)
    elif weapon=='shortsword':
        cylinder('Espada_cabo',p(-.14),p(.08),.038,leather)
        cylinder('Espada_pomo',p(-.18),p(-.135),.052,iron)
        across=Vector((.98,-.15,0)).normalized(); normal=axis.cross(across).normalized()
        cylinder('Espada_guarda',p(.095)-across*.115,p(.095)+across*.115,.025,iron,6)
        # Diamond section, flat edges and central ridge, tapered point.
        verts=[]
        for t,w,d in ((.115,.075,.018),(.54,.067,.014)):
            c=p(t); verts.extend([tuple(c-across*w),tuple(c+normal*d),tuple(c+across*w),tuple(c-normal*d)])
        verts.append(tuple(p(.67)))
        faces=[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]+[(i+4,(i+1)%4+4,8) for i in range(4)]+[(3,2,1,0)]
        mesh('Espada_lamina_diamante',verts,faces,iron)
    elif weapon=='maca':
        cylinder('Maca_cabo',p(-.15),p(.47),.033,wood)
        cylinder('Maca_pega',p(-.11),p(.09),.038,leather)
        cylinder('Maca_nucleo',p(.44),p(.60),.069,iron,8,r2=.082)
        across=Vector((1,0,0)); normal=axis.cross(across).normalized(); across=normal.cross(axis).normalized()
        # Six iron flanges around a compact head, readable from front and sides.
        for i in range(6):
            radial=across*math.cos(i*math.tau/6)+normal*math.sin(i*math.tau/6)
            tangent=axis.cross(radial)*.016
            c0=p(.435); c1=p(.585)
            vs=[tuple(c+radial*r+tangent*s) for c in (c0,c1) for r,s in ((.045,-1),(.125,-1),(.125,1),(.045,1))]
            mesh('Maca_aleta_%s'%i,vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],iron)
        cylinder('Maca_coroa',p(.60),p(.64),.055,iron,8,r2=.025)
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    temp=REVIEW/('equipment_'+weapon+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(temp),export_format='GLB',use_selection=True,export_normals=False)
    return read_glb(temp)

def all_parts(source):
    return [(source,p,accessor(source,p['indices']).reshape(-1,3)) for p in source[0]['meshes'][0]['primitives']]

def setup_render():
    sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=sc.render.resolution_y=384; sc.render.resolution_percentage=100
    sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'
    sc.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('review_world'); sc.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    camera=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera')); sc.collection.objects.link(camera)
    sc.camera=camera; camera.data.type='ORTHO'; camera.data.ortho_scale=2.75
    target=Vector((0,0,-.05))
    for name,loc,power,size in [('Key',(2,-3,4),900,4),('Fill',(-3,-2,1.5),500,3),('Rim',(0,3,3),850,3)]:
        ob=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA')); sc.collection.objects.link(ob)
        ob.location=loc; ob.data.energy=power; ob.data.shape='DISK'; ob.data.size=size
        ob.rotation_euler=(target-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    return sc,camera,target

def validate_and_render():
    source=read_glb(BASE); candidate=read_glb(CANDIDATE); expected=accessor(source,source[0]['meshes'][0]['primitives'][0]['attributes']['POSITION'])
    bmin=expected.min(axis=0); bmax=expected.max(axis=0); base_dims=bmax-bmin
    rows=[]
    for weapon in WEAPONS:
        for shield in ('sem_escudo','com_escudo'):
            path=OUT/f'goblinCombatente_{weapon}_{shield}.glb'; src=read_glb(path); doc,binary=src
            assert all('uri' not in b for b in doc['buffers']+doc.get('images',[]))
            positions=np.concatenate([accessor(src,p['attributes']['POSITION'])[accessor(src,p['indices']).reshape(-1)] for p in doc['meshes'][0]['primitives']])
            dims=positions.max(axis=0)-positions.min(axis=0)
            assert np.allclose(dims,base_dims,rtol=0,atol=1e-7),(path,dims,base_dims)
            body=doc['meshes'][0]['primitives'][0]
            bodyref=source if weapon=='machado_basico' else candidate
            refp=bodyref[0]['meshes'][0]['primitives'][0]
            # Compare triangles with UVs, independent of compact index ordering.
            for attr in ('POSITION','TEXCOORD_0'):
                values=accessor(src,body['attributes'][attr])[accessor(src,body['indices']).reshape(-1)]
                ref=accessor(bodyref,refp['attributes'][attr])[accessor(bodyref,refp['indices']).reshape(-1)]
                assert np.array_equal(values,ref),(path,attr)
            for a,b in ((src,bodyref),):
                av=a[0]['bufferViews'][a[0]['images'][0]['bufferView']]; bv=b[0]['bufferViews'][b[0]['images'][0]['bufferView']]
                assert a[1][av.get('byteOffset',0):av.get('byteOffset',0)+av['byteLength']]==b[1][bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(path))
            meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']; assert meshes
            sc,cam,target=setup_render()
            for view,location in [('front',(0,-4.5,2.2)),('oblique',(-3.5,-4,2.0))]:
                cam.location=location; cam.rotation_euler=(target-Vector(location)).to_track_quat('-Z','Y').to_euler()
                sc.render.filepath=str(REVIEW/f'{path.stem}_{view}.png'); bpy.ops.render.render(write_still=True)
            row={'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'triangles':sum(doc['accessors'][p['indices']]['count']//3 for p in doc['meshes'][0]['primitives']),
                 'dimensions_gltf':dims.tolist(),'images_embedded':len(doc.get('images',[])),
                 'body_position_uv_exact':True,'body_jpeg_exact':True,'reopened_blender':True,'scale_drift_percent':0}
            rows.append(row); print('VALIDATED',json.dumps(row))
    (REVIEW/'goblin_3d_family_validation.json').write_text(json.dumps(rows,indent=2),encoding='utf8')

def main():
    REVIEW.mkdir(parents=True,exist_ok=True)
    base=read_glb(BASE); candidate=read_glb(CANDIDATE)
    body=all_parts(candidate)[:1]; axe=all_parts(base)
    spear=primitives(candidate,'spear'); shield=primitives(candidate,'shield')
    generated={weapon:all_parts(build_weapon(weapon)) for weapon in ('bordao','cajado_madeira','shortsword','maca')}
    for weapon in WEAPONS:
        for has_shield in (False,True):
            path=OUT/f'goblinCombatente_{weapon}_{"com_escudo" if has_shield else "sem_escudo"}.glb'
            if weapon=='machado_basico' and not has_shield: shutil.copyfile(BASE,path)
            elif weapon=='lanca_curta' and has_shield:
                if path.resolve() != CANDIDATE.resolve(): shutil.copyfile(CANDIDATE,path)
            else:
                parts=axe if weapon=='machado_basico' else body+(spear if weapon=='lanca_curta' else generated[weapon])
                compose(parts+(shield if has_shield else []),path)
    validate_and_render()

if __name__=='__main__': main()
