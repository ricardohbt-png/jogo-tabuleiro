"""Export a textured, game-ready GLB from the authored Alva e Luz tower scene.

Run with Blender 5.1:
    blender -b assets/objetos/torre_alva_e_luz.blend --python tools/create_torre_alva_e_luz_v2.py
"""
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "objetos"
BASE = ASSET_DIR / "torre_alva_e_luz_v2"
OUTPUTS = [
    BASE.with_suffix(".blend"),
    BASE.with_suffix(".glb"),
    BASE.with_name(BASE.name + "_basecolor").with_suffix(".png"),
    BASE.with_name(BASE.name + "_preview").with_suffix(".png"),
]

ASSET_DIR.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.bake.margin = 10
scene.render.bake.use_pass_color = True
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False

stone_materials = {
    "Blocos | carvão": (0.115, 0.093, 0.071),
    "Blocos | cinza ardósia": (0.185, 0.155, 0.118),
    "Blocos | cinza gasto": (0.245, 0.207, 0.160),
    "Blocos | pedra clara": (0.335, 0.285, 0.215),
    "Calcário enegrecido": (0.175, 0.148, 0.112),
    "Pedra gasta no coroamento": (0.280, 0.231, 0.168),
}

for name, color in stone_materials.items():
    mat = bpy.data.materials.get(name)
    if not mat or not mat.use_nodes:
        continue
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    if not shader:
        continue
    shader.inputs["Roughness"].default_value = 0.88

    # Warm, subtle stone variation baked into the GLB's atlas below.
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "Variação de pedra"
    noise.inputs["Scale"].default_value = 19.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "Paleta de calcário envelhecido"
    lo, hi = ramp.color_ramp.elements[0], ramp.color_ramp.elements[1]
    lo.position = 0.2
    hi.position = 0.82
    lo.color = (*[c * 0.66 for c in color], 1.0)
    hi.color = (*[min(1.0, c * 1.34) for c in color], 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])

    fine = nodes.new("ShaderNodeTexNoise")
    fine.name = "Relevo microscópico"
    fine.inputs["Scale"].default_value = 74.0
    fine.inputs["Detail"].default_value = 2.0
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Grão mineral"
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.018
    links.new(fine.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)

# The tower source has separate authored meshes. Join them around the original
# centered ground pivot so one packed atlas and one runtime mesh stay simple.
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("The source Blender scene contains no tower meshes")
base = bpy.data.objects.get("Base circular de alvenaria") or meshes[0]
bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join()
tower = bpy.context.view_layer.objects.active
tower.name = "Torre de Alva e Luz | GLB"
tower.data.name = "Torre de Alva e Luz | malha"

# Give all surfaces a single non-overlapping UV map for the baked PBR color.
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(island_margin=0.012, area_weight=0.15, scale_to_bounds=False)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

atlas_path = OUTPUTS[2]
atlas = bpy.data.images.new(
    "Torre Alva e Luz | pedra PBR",
    width=2048,
    height=2048,
    alpha=False,
    float_buffer=False,
)
atlas.filepath_raw = str(atlas_path)
atlas.file_format = "PNG"

target_nodes = []
for mat in list(tower.data.materials):
    if not mat:
        continue
    if not mat.use_nodes:
        mat.use_nodes = True
    image_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    image_node.name = "Bake target | torre base color"
    image_node.image = atlas
    mat.node_tree.nodes.active = image_node
    target_nodes.append(image_node)

if not target_nodes:
    raise RuntimeError("The tower has no bakeable materials")

bpy.ops.object.select_all(action="DESELECT")
tower.select_set(True)
bpy.context.view_layer.objects.active = tower
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=10)
atlas.save()
atlas.pack()

# Replace the authoring shaders with a glTF-compatible textured stone material.
runtime_mat = bpy.data.materials.new("Pedra envelhecida | PBR")
runtime_mat.use_nodes = True
runtime_nodes = runtime_mat.node_tree.nodes
runtime_nodes.clear()
output = runtime_nodes.new("ShaderNodeOutputMaterial")
shader = runtime_nodes.new("ShaderNodeBsdfPrincipled")
shader.inputs["Roughness"].default_value = 0.9
texture = runtime_nodes.new("ShaderNodeTexImage")
texture.name = "Textura de pedra da torre"
texture.image = atlas
texture.interpolation = "Linear"
runtime_mat.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
runtime_mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
tower.data.materials.clear()
tower.data.materials.append(runtime_mat)
for polygon in tower.data.polygons:
    polygon.material_index = 0

# Preserve the authored isometric camera and lights for a review render.
scene.camera = bpy.data.objects.get("Câmera | miniatura isométrica") or scene.camera
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True
scene.render.filepath = str(OUTPUTS[3])
bpy.ops.render.render(write_still=True)

# The GLB contains only the tower mesh; camera and studio lights remain in BLEND.
bpy.ops.object.select_all(action="DESELECT")
tower.select_set(True)
bpy.context.view_layer.objects.active = tower
bpy.ops.export_scene.gltf(
    filepath=str(OUTPUTS[1]),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_materials="EXPORT",
    export_texcoords=True,
    export_normals=True,
)

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUTS[0]))
print("TORRE_ALVA_E_LUZ_V2", *(str(p) for p in OUTPUTS), "FACES", len(tower.data.polygons))
