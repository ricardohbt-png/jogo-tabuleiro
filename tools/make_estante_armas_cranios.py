"""Gera a estante de armas e crânios em GLB para as decorações da masmorra.

Uso (a partir da raiz do projeto):
    "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" \
        --background --python tools/make_estante_armas_cranios.py
"""

import os
import math

import bpy
from mathutils import Vector


ROOT = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
OUTPUT = os.path.join(ROOT, "assets", "objetos", "estante_armas_cranios.glb")


def material(name, color, metallic=0.0, roughness=0.72):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


WOOD = material("Madeira rústica", (0.22, 0.075, 0.025), roughness=0.9)
WOOD_LIGHT = material("Bordas gastas", (0.38, 0.15, 0.045), roughness=0.86)
WOOD_DARK = material("Fundo escuro", (0.09, 0.028, 0.012), roughness=0.96)
IRON = material("Ferro envelhecido", (0.12, 0.13, 0.13), metallic=0.78, roughness=0.55)
BLADE = material("Aço gasto", (0.38, 0.41, 0.40), metallic=0.9, roughness=0.3)
LEATHER = material("Couro marrom", (0.16, 0.045, 0.018), roughness=0.9)
BONE = material("Osso antigo", (0.62, 0.52, 0.34), roughness=0.82)
SOCKET = material("Cavidades", (0.012, 0.008, 0.006), roughness=1.0)


def apply_material(obj, mat):
    obj.data.materials.append(mat)
    return obj


def bevel(obj, amount=0.025):
    mod = obj.modifiers.new("bordas desgastadas", "BEVEL")
    mod.width = amount
    mod.segments = 2
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def box(name, location, dimensions, mat, edge=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, mat)
    if edge:
        bevel(obj, min(edge, min(dimensions) * 0.28))
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth,
        location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    apply_material(obj, mat)
    bevel(obj, min(radius * 0.18, 0.012))
    return obj


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, mat)
    return obj


def sword(name, x, y, z, lean=0.0, length=0.86):
    """Espada simples apoiada verticalmente na estante, com a lâmina visível."""
    blade = box(name + " lâmina", (x, y - 0.035, z + length * 0.55),
                (0.075, 0.045, length), BLADE, edge=0.012)
    blade.rotation_euler[1] = lean
    grip_z = z + 0.06
    grip = cylinder(name + " empunhadura", (x, y - 0.04, grip_z),
                    0.045, 0.28, LEATHER, vertices=10)
    grip.rotation_euler[1] = lean
    guard = box(name + " guarda", (x, y - 0.04, z + 0.21),
                (0.24, 0.055, 0.045), IRON, edge=0.01)
    guard.rotation_euler[1] = lean
    pommel = sphere(name + " pomo", (x, y - 0.04, z - 0.09),
                    (0.065, 0.065, 0.065), IRON)
    pommel.rotation_euler[1] = lean


def axe(name, x, y, z, angle=0.0, length=0.8):
    """Machado horizontal, com cabo de madeira e cabeça metálica."""
    handle = cylinder(name + " cabo", (x, y, z), 0.038, length, WOOD_LIGHT,
                      rotation=(0, math.pi / 2, angle), vertices=10)
    head_x = x + math.cos(angle) * length * 0.42
    head_y = y + math.sin(angle) * length * 0.42
    head = box(name + " lâmina", (head_x, head_y - 0.01, z),
               (0.22, 0.075, 0.30), IRON, edge=0.025)
    head.rotation_euler[1] = angle
    blade = box(name + " fio", (head_x + 0.035, head_y - 0.012, z),
                (0.12, 0.045, 0.22), BLADE, edge=0.012)
    blade.rotation_euler[1] = angle


def skull(name, x, y, z, scale=1.0):
    """Crânio decorativo estilizado, voltado para a frente (-Y)."""
    sphere(name + " calota", (x, y, z + 0.12 * scale),
           (0.17 * scale, 0.14 * scale, 0.18 * scale), BONE)
    box(name + " mandíbula", (x, y - 0.03 * scale, z - 0.045 * scale),
        (0.19 * scale, 0.13 * scale, 0.095 * scale), BONE, edge=0.018 * scale)
    for side in (-1, 1):
        sphere(name + " órbita", (x + side * 0.062 * scale, y - 0.125 * scale,
                                   z + 0.13 * scale),
               (0.038 * scale, 0.018 * scale, 0.045 * scale), SOCKET)
    for side in (-1, 1):
        box(name + " dente", (x + side * 0.038 * scale, y - 0.103 * scale,
                               z - 0.035 * scale),
            (0.022 * scale, 0.018 * scale, 0.035 * scale), SOCKET, edge=0.003)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Os materiais são criados no carregamento deste script e serão usados na
    # montagem logo depois; não removê-los durante a limpeza da cena.
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def build():
    clear_scene()
    # Estrutura principal: largura X, profundidade Y, altura Z; frente em -Y.
    box("poste esquerdo", (-0.86, 0.0, 1.34), (0.18, 0.56, 2.68), WOOD_LIGHT, 0.035)
    box("poste direito", (0.86, 0.0, 1.34), (0.18, 0.56, 2.68), WOOD_LIGHT, 0.035)
    for z in (0.36, 1.08, 1.80, 2.52):
        box("prateleira", (0.0, 0.0, z), (1.72, 0.58, 0.13), WOOD_LIGHT, 0.025)
    for z in (0.62, 1.34, 2.06):
        box("painel traseiro", (0.0, 0.23, z), (1.58, 0.10, 0.60), WOOD_DARK, 0.012)
    # Travessas e ferragens rústicas.
    for z in (0.26, 2.64):
        box("travessa frontal", (0.0, -0.28, z), (1.85, 0.10, 0.16), WOOD, 0.02)
    for x in (-0.86, 0.86):
        for z in (0.35, 2.55):
            box("cantoneira de ferro", (x, -0.30, z), (0.22, 0.035, 0.22), IRON, 0.012)

    # Espadas expostas nas duas prateleiras inferiores.
    sword("espada esquerda", -0.58, -0.30, 0.43, lean=-0.06, length=0.72)
    sword("espada central", -0.16, -0.30, 0.43, lean=0.02, length=0.78)
    sword("espada direita", 0.34, -0.30, 1.15, lean=0.04, length=0.78)
    sword("espada curta", 0.68, -0.30, 1.15, lean=-0.08, length=0.62)

    # Machados apoiados horizontalmente, incluindo um sobre o topo.
    axe("machado inferior", -0.22, -0.33, 0.53, angle=0.02, length=0.78)
    axe("machado superior", 0.10, -0.33, 2.70, angle=-0.12, length=0.86)

    # Crânios sobre a parte superior da estante.
    skull("crânio esquerdo", -0.46, -0.11, 2.65, scale=0.88)
    skull("crânio direito", 0.46, -0.10, 2.65, scale=0.78)

    # O exportador glTF converte automaticamente o Z-up do Blender para o
    # Y-up do GLB, que é o sistema usado pelo carregador do jogo. A base em
    # Z=0 no Blender chega como base em Y=0 no arquivo final.
    # Origem próxima ao centro e base no chão para o carregador do jogo.
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT,
        export_format="GLB",
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"GLB gerado: {OUTPUT}")


if __name__ == "__main__":
    build()
