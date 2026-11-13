"""Cria variantes levantada e abaixada do portão levadiço para o tabuleiro."""
from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def material(name, color, metallic=0.0, roughness=0.76):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def cube(name, location, dimensions, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Bordas trabalhadas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = obj.modifiers.new("Normais ponderadas", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cylinder(name, start, end, radius, mat, vertices=10, radius_top=None):
    start, end = Vector(start), Vector(end)
    delta = end - start
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=delta.length,
                                            location=(start + end) / 2)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=delta.length,
                                        location=(start + end) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


def gear(name, center, radius, mat, teeth=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius * 0.77,
                                    minor_radius=radius * 0.16,
                                    major_segments=teeth, minor_segments=6,
                                    location=center, rotation=(math.pi / 2, 0, 0))
    rim = bpy.context.object
    rim.name = name + " | aro"
    rim.data.materials.append(mat)
    cylinder(name + " | cubo", (center[0], center[1] - 0.018, center[2]),
             (center[0], center[1] + 0.018, center[2]), radius * 0.21, mat, 10)
    for i in range(4):
        a = math.tau * i / 4
        p1 = (center[0] + math.cos(a) * radius * 0.20, center[1],
              center[2] + math.sin(a) * radius * 0.20)
        p2 = (center[0] + math.cos(a) * radius * 0.69, center[1],
              center[2] + math.sin(a) * radius * 0.69)
        cylinder(f"{name} | raio {i+1}", p1, p2, radius * 0.075, mat, 8)


def make_panel(prefix, bottom_z, iron, iron_light, bronze):
    made = []
    x_min, x_max = -0.335, 0.335
    panel_height = 1.50
    y_front = -0.115
    bar_xs = [x_min + i * ((x_max - x_min) / 6) for i in range(7)]
    for i, x in enumerate(bar_xs):
        made.append(cylinder(f"{prefix} | barra vertical {i+1}",
                             (x, y_front, bottom_z + 0.08),
                             (x, y_front, bottom_z + panel_height - 0.02),
                             0.022, iron if i % 2 else iron_light, 8))
        made.append(cylinder(f"{prefix} | ponta inferior {i+1}",
                             (x, y_front, bottom_z - 0.005),
                             (x, y_front, bottom_z + 0.12),
                             0.005, iron, 8, radius_top=0.036))
    for i, zoff in enumerate((0.20, 0.72, 1.25)):
        z = bottom_z + zoff
        made.append(cylinder(f"{prefix} | travessa {i+1}",
                             (x_min - 0.045, y_front - 0.006, z),
                             (x_max + 0.045, y_front - 0.006, z),
                             0.038 if i == 2 else 0.032,
                             iron_light if i == 2 else iron, 10))
        for side, x in enumerate((x_min - 0.052, x_max + 0.052)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6,
                                                radius=0.026,
                                                location=(x, y_front - 0.014, z))
            rivet = bpy.context.object
            rivet.name = f"{prefix} | rebite {i+1}-{side+1}"
            rivet.scale = (1, 0.38, 1)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            rivet.data.materials.append(bronze)
            made.append(rivet)
    # Cadeado e aro central dão escala e identificam o conjunto como um portão móvel.
    cube(prefix + " | placa central", (0, y_front - 0.035, bottom_z + 0.58),
         (0.105, 0.035, 0.15), bronze, 0.012)
    made.append(bpy.context.object)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.047, minor_radius=0.011,
                                    major_segments=12, minor_segments=6,
                                    location=(0, y_front - 0.061, bottom_z + 0.52),
                                    rotation=(math.pi / 2, 0, 0))
    handle = bpy.context.object
    handle.name = prefix + " | argola"
    handle.data.materials.append(iron_light)
    made.append(handle)
    return made


def build_frame(stone, stone_light, iron, iron_light, bronze):
    frame = []
    # Cada face fica dentro de um vão de 1×1; as guias seguram a grade nos dois lados.
    for side, x in enumerate((-0.445, 0.445)):
        frame.append(cube(f"Pilar de pedra {side+1}", (x, 0.025, 0.87),
                          (0.105, 0.21, 1.74), stone, 0.018))
        frame.append(cube(f"Guia de ferro {side+1}", (x * 0.80, -0.105, 0.86),
                          (0.045, 0.085, 1.55), iron, 0.012))
        frame.append(cube(f"Base lavrada {side+1}", (x, -0.005, 0.12),
                          (0.17, 0.29, 0.22), stone_light, 0.018))
        frame.append(cube(f"Capitel {side+1}", (x, -0.005, 1.66),
                          (0.18, 0.27, 0.18), stone_light, 0.018))
    frame.append(cube("Viga superior de pedra", (0, 0.025, 1.74),
                      (0.91, 0.23, 0.16), stone, 0.02))
    frame.append(cube("Viga de ferro do mecanismo", (0, -0.12, 1.62),
                      (0.70, 0.10, 0.075), iron, 0.012))
    # Cabrestante, engrenagem e catraca ficam fora do vão caminhável.
    gear("Engrenagem", (0.365, -0.205, 1.54), 0.105, bronze, teeth=12)
    frame.extend([obj for obj in bpy.context.scene.objects
                  if obj.name.startswith("Engrenagem")])
    cylinder("Eixo do cabrestante", (0.365, -0.12, 1.54),
             (0.365, 0.04, 1.54), 0.027, iron_light, 10)
    frame.append(bpy.context.object)
    return frame


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.world.color = (0.08, 0.08, 0.08)
    bpy.ops.object.camera_add(location=(3.3, -4.6, 3.25))
    camera = bpy.context.object
    camera.name = "Câmera isométrica do tabuleiro"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.05
    target = Vector((0, 0, 1.48))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for name, location, power, size, color in (
        ("Luz principal", (3.0, -3.8, 4.5), 440, 3.0, (1.0, 0.84, 0.67)),
        ("Luz de preenchimento", (-3.5, -1.2, 2.8), 260, 3.2, (0.71, 0.82, 1.0)),
        ("Luz de recorte", (0.0, 3.0, 3.6), 360, 2.5, (1.0, 0.72, 0.43)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()


def render(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def export_glb(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                              use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT")


def main():
    clear_scene()
    iron = material("Ferro escurecido", (0.105, 0.135, 0.16), 0.78, 0.34)
    iron_light = material("Ferro gasto", (0.30, 0.34, 0.37), 0.68, 0.40)
    stone = material("Granito cinza", (0.28, 0.30, 0.31), 0.03, 0.89)
    stone_light = material("Pedra das bordas", (0.40, 0.40, 0.38), 0.04, 0.84)
    bronze = material("Bronze do cabrestante", (0.49, 0.29, 0.105), 0.72, 0.36)
    frame = build_frame(stone, stone_light, iron, iron_light, bronze)
    lowered = make_panel("Grade abaixada", 0.105, iron, iron_light, bronze)
    raised = make_panel("Grade levantada", 1.30, iron, iron_light, bronze)
    setup_scene()
    scene = bpy.context.scene

    for obj in raised:
        obj.hide_render = True
    render(OUT / "portao_levadico_baixado.png")
    export_glb(OUT / "portao_levadico_baixado.glb", frame + lowered)

    for obj in lowered:
        obj.hide_render = True
    for obj in raised:
        obj.hide_render = False
    render(OUT / "portao_levadico_levantado.png")
    export_glb(OUT / "portao_levadico_levantado.glb", frame + raised)

    for obj in lowered:
        obj.hide_render = False
    for obj in raised:
        obj.hide_render = True
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "portao_levadico.blend"))
    print("PORTAO_ASSETS", OUT / "portao_levadico_baixado.glb",
          OUT / "portao_levadico_levantado.glb")


if __name__ == "__main__":
    main()
