"""Create a black-textured copy of the stone scorpion miniature for its giant variant.

Run with Blender 5.1: blender --background --python tools/recolor_escorpiao_gigante.py
"""
from pathlib import Path
import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models3d/monstros/escorpiao.glb"
OUTPUT = ROOT / "assets/models3d/monstros/escorpiao_gigante_preto.glb"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not mesh_objects:
    raise RuntimeError("O GLB original não trouxe nenhuma malha")

for obj in mesh_objects:
    for material in obj.data.materials:
        if material is None:
            continue
        material.use_nodes = True
        nodes = material.node_tree.nodes
        principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        if principled is None:
            principled = nodes.new("ShaderNodeBsdfPrincipled")
            output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
            if output is None:
                output = nodes.new("ShaderNodeOutputMaterial")
            material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        base_color = principled.inputs["Base Color"]
        for link in list(material.node_tree.links):
            if link.to_node == principled and link.to_socket == base_color:
                material.node_tree.links.remove(link)
        # A near-black, matte finish reads as black while keeping the sculpted
        # shell, claws, and tail legible under the board's lighting.
        base_color.default_value = (0.006, 0.006, 0.006, 1.0)
        principled.inputs["Roughness"].default_value = 0.96
        principled.inputs["Metallic"].default_value = 0.0
        if "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = 0.08

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
temporary = OUTPUT.with_suffix(".tmp.glb")
bpy.ops.export_scene.gltf(
    filepath=str(temporary),
    export_format="GLB",
    export_materials="EXPORT",
    export_image_format="AUTO",
)
temporary.replace(OUTPUT)
print(f"saved {OUTPUT} (meshes={len(mesh_objects)}, materials={len(bpy.data.materials)})")
