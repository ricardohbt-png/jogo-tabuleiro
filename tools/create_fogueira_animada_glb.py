"""Mescla a fogueira original com as chamas animadas da Chama Viva.

Roda da raiz: python tools/create_fogueira_animada_glb.py
O mesh/textura da fogueira original é preservado; os nós e a animação da
Chama Viva são anexados ao mesmo nó de cena.
"""
from __future__ import annotations

import copy
import json
import os
import struct


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, "assets", "objetos", "fogueira.glb")
FLAME_PATH = os.path.join(ROOT, "assets", "objetos", "chama_viva.glb")
DEST_PATH = os.path.join(ROOT, "assets", "objetos", "fogueira_animada.glb")


def read_glb(path):
    raw = open(path, "rb").read()
    if raw[:4] != b"glTF" or struct.unpack_from("<I", raw, 4)[0] != 2:
        raise ValueError(f"GLB inválido: {path}")
    json_len = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_len].decode("utf-8"))
    bin_header = 20 + json_len
    bin_len = struct.unpack_from("<I", raw, bin_header)[0]
    binary = raw[bin_header + 8:bin_header + 8 + bin_len]
    return document, binary


def pad4(data):
    return data + b"\0" * ((4 - len(data) % 4) % 4)


def merge(base_path=BASE_PATH, dest_path=DEST_PATH):
    base, base_bin = read_glb(base_path)
    flame, flame_bin = read_glb(FLAME_PATH)
    out = copy.deepcopy(base)

    base_bv = len(base.get("bufferViews", []))
    base_acc = len(base.get("accessors", []))
    base_mat = len(base.get("materials", []))
    base_mesh = len(base.get("meshes", []))
    base_node = len(base.get("nodes", []))

    # O buffer novo começa depois do BIN original, alinhado a 4 bytes.
    flame_bin_offset = len(pad4(base_bin))
    merged_bin = pad4(base_bin) + flame_bin

    flame_views = []
    for view in flame.get("bufferViews", []):
        item = copy.deepcopy(view)
        item["buffer"] = 0
        item["byteOffset"] = flame_bin_offset + item.get("byteOffset", 0)
        flame_views.append(item)
    out.setdefault("bufferViews", []).extend(flame_views)

    flame_accessors = copy.deepcopy(flame.get("accessors", []))
    for accessor in flame_accessors:
        accessor["bufferView"] += base_bv
    out.setdefault("accessors", []).extend(flame_accessors)

    flame_materials = copy.deepcopy(flame.get("materials", []))
    out.setdefault("materials", []).extend(flame_materials)

    flame_meshes = copy.deepcopy(flame.get("meshes", []))
    for mesh in flame_meshes:
        for primitive in mesh.get("primitives", []):
            primitive["material"] = primitive.get("material", 0) + base_mat
            primitive["indices"] = primitive["indices"] + base_acc
            primitive["attributes"] = {
                key: value + base_acc
                for key, value in primitive.get("attributes", {}).items()
            }
    out.setdefault("meshes", []).extend(flame_meshes)

    flame_nodes = copy.deepcopy(flame.get("nodes", []))
    for node in flame_nodes:
        if "mesh" in node:
            node["mesh"] += base_mesh
        if "children" in node:
            node["children"] = [child + base_node for child in node["children"]]
        # A fogueira original ocupa coordenadas centradas no modelo. Este
        # deslocamento assenta as chamas dentro da lenha depois do escalamento
        # automático do cliente, sem alterar o posicionamento da decoração.
        translation = list(node.get("translation", [0.0, 0.0, 0.0]))
        while len(translation) < 3:
            translation.append(0.0)
        translation[1] -= 0.28
        node["translation"] = translation
    out.setdefault("nodes", []).extend(flame_nodes)

    # A fogueira usa o nó world (índice 1) como raiz do mesh original.
    # Anexar as chamas a ele faz com que a centralização/escala do loader seja
    # aplicada de forma idêntica a toda a fogueira composta.
    flame_indices = list(range(base_node, base_node + len(flame_nodes)))
    world = out["nodes"][1]
    world.setdefault("children", []).extend(flame_indices)

    flame_anims = copy.deepcopy(flame.get("animations", []))
    for animation in flame_anims:
        for sampler in animation.get("samplers", []):
            sampler["input"] += base_acc
            sampler["output"] += base_acc
        for channel in animation.get("channels", []):
            channel["target"]["node"] += base_node
    out.setdefault("animations", []).extend(flame_anims)
    out["buffers"][0]["byteLength"] = len(merged_bin)
    out["asset"]["generator"] = "Legends for Hire composite campfire"

    json_bytes = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes = pad4(json_bytes).replace(b"\x00", b" ")
    bin_bytes = pad4(merged_bin)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    result = bytearray(struct.pack("<4sII", b"glTF", 2, total))
    result.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    result.extend(json_bytes)
    result.extend(struct.pack("<I4s", len(bin_bytes), b"BIN\0"))
    result.extend(bin_bytes)
    with open(dest_path, "wb") as fh:
        fh.write(result)
    print(f"GLB criado: {dest_path} ({len(result)} bytes)")


if __name__ == "__main__":
    merge()
