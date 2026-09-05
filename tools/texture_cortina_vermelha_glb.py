"""Texturiza o GLB da cortina usando a arte PNG original."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / "assets" / "objetos" / "cortina_vermelha.glb"
PNG_PATH = ROOT / "assets" / "objetos" / "cortina_vermelha.png"


def align4(value: int) -> int:
    return (value + 3) & ~3


def read_glb(path: Path) -> tuple[bytes, dict, bytes, bytes]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"GLB inválido: {path}")
    version, declared_length = struct.unpack_from("<II", data, 4)
    if version != 2 or declared_length != len(data):
        raise ValueError("Cabeçalho GLB incompatível")
    json_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:  # JSON
        raise ValueError("O primeiro chunk do GLB não é JSON")
    json_end = 20 + json_length
    document = json.loads(data[20:json_end].rstrip(b" \t\r\n"))
    remainder = data[json_end:]
    if len(remainder) < 8:
        raise ValueError("GLB sem chunk BIN")
    bin_length, bin_type = struct.unpack_from("<II", remainder, 0)
    if bin_type != 0x004E4942:  # BIN
        raise ValueError("O segundo chunk do GLB não é BIN")
    bin_end = 8 + bin_length
    if bin_end > len(remainder):
        raise ValueError("Chunk BIN incompleto")
    return data[:12], document, remainder[8:bin_end], remainder[bin_end:]


def append_blob(binary: bytearray, payload: bytes) -> tuple[int, int]:
    offset = align4(len(binary))
    binary.extend(b"\0" * (offset - len(binary)))
    binary.extend(payload)
    return offset, len(payload)


def positions(document: dict, binary: bytes) -> list[tuple[float, float, float]]:
    accessor = document["accessors"][1]
    view = document["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    stride = view.get("byteStride", 12)
    out = []
    for index in range(count):
        out.append(struct.unpack_from("<fff", binary, start + index * stride))
    return out


def write_glb(path: Path, header: bytes, document: dict, binary: bytes, tail: bytes) -> None:
    json_chunk = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    bin_chunk = bytes(binary)
    bin_padding = b"\0" * ((4 - len(bin_chunk) % 4) % 4)
    bin_chunk += bin_padding
    total_length = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk) + len(tail)
    output = header[:8] + struct.pack("<I", total_length)
    output += struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
    output += struct.pack("<II", len(bin_chunk), 0x004E4942) + bin_chunk + tail
    path.write_bytes(output)


def main() -> None:
    header, document, original_binary, tail = read_glb(GLB_PATH)
    image = Image.open(PNG_PATH).convert("RGBA")
    alpha_bbox = image.getchannel("A").getbbox()
    if not alpha_bbox:
        raise ValueError("O PNG da cortina não possui área visível")
    image_width, image_height = image.size
    left, top, right, bottom = alpha_bbox
    # O GLB é uma malha frontal sem UV. Projetamos XY na área não transparente
    # do PNG para preservar também os arabescos e acabamentos dourados.
    uv_min_u, uv_max_u = left / image_width, right / image_width
    uv_min_v, uv_max_v = top / image_height, bottom / image_height
    points = positions(document, original_binary)
    accessor = document["accessors"][1]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    uv_data = bytearray()
    for x, y, _z in points:
        u = uv_min_u + (x - min_x) / max(max_x - min_x, 1e-9) * (uv_max_u - uv_min_u)
        v = uv_max_v - (y - min_y) / max(max_y - min_y, 1e-9) * (uv_max_v - uv_min_v)
        uv_data.extend(struct.pack("<ff", u, v))

    binary = bytearray(original_binary)
    uv_offset, uv_length = append_blob(binary, bytes(uv_data))
    uv_view_index = len(document.setdefault("bufferViews", []))
    document["bufferViews"].append({
        "buffer": 0, "byteOffset": uv_offset, "byteLength": uv_length,
        "target": 34962,
    })
    uv_accessor_index = len(document.setdefault("accessors", []))
    document["accessors"].append({
        "bufferView": uv_view_index, "componentType": 5126,
        "count": accessor["count"], "type": "VEC2",
        "min": [uv_min_u, uv_min_v], "max": [uv_max_u, uv_max_v],
    })
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            primitive.setdefault("attributes", {})["TEXCOORD_0"] = uv_accessor_index

    png_bytes = PNG_PATH.read_bytes()
    image_offset, image_length = append_blob(binary, png_bytes)
    image_view_index = len(document["bufferViews"])
    document["bufferViews"].append({
        "buffer": 0, "byteOffset": image_offset, "byteLength": image_length,
    })
    image_index = len(document.setdefault("images", []))
    document["images"].append({
        "bufferView": image_view_index, "mimeType": "image/png",
        "name": "cortina_vermelha.png",
    })
    sampler_index = len(document.setdefault("samplers", []))
    document["samplers"].append({
        "magFilter": 9729, "minFilter": 9987,
        "wrapS": 33071, "wrapT": 33071,
    })
    texture_index = len(document.setdefault("textures", []))
    document["textures"].append({
        "sampler": sampler_index, "source": image_index,
        "name": "cortina_vermelha.png",
    })

    materials = document.setdefault("materials", [])
    if not materials:
        materials.append({})
    material = materials[0]
    pbr = material.setdefault("pbrMetallicRoughness", {})
    pbr["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
    pbr["baseColorTexture"] = {"index": texture_index}
    pbr["metallicFactor"] = 0.0
    pbr["roughnessFactor"] = 0.80
    material["name"] = "Cortina_Vermelha_Texturizada"
    material["alphaMode"] = "BLEND"
    material["doubleSided"] = True
    document["buffers"][0]["byteLength"] = len(binary)
    write_glb(GLB_PATH, header, document, binary, tail)
    print(f"Textura aplicada em {GLB_PATH}")
    print(f"UVs: {len(points)} | PNG: {image_width}x{image_height} | alpha_bbox: {alpha_bbox}")


if __name__ == "__main__":
    main()
