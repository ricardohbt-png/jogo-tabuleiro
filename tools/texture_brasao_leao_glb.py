"""Texturiza o GLB do brasão usando a arte PNG original."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / "assets" / "objetos" / "brasao_leao.glb"
PNG_PATH = ROOT / "assets" / "objetos" / "brasao_leao.png"


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
    if chunk_type != 0x4E4F534A:
        raise ValueError("O primeiro chunk do GLB não é JSON")
    json_end = 20 + json_length
    document = json.loads(data[20:json_end].rstrip(b" \t\r\n"))
    remainder = data[json_end:]
    if len(remainder) < 8:
        raise ValueError("GLB sem chunk BIN")
    bin_length, bin_type = struct.unpack_from("<II", remainder, 0)
    if bin_type != 0x004E4942 or 8 + bin_length > len(remainder):
        raise ValueError("Chunk BIN inválido")
    return data[:12], document, remainder[8:8 + bin_length], remainder[8 + bin_length:]


def append_blob(binary: bytearray, payload: bytes) -> tuple[int, int]:
    offset = align4(len(binary))
    binary.extend(b"\0" * (offset - len(binary)))
    binary.extend(payload)
    return offset, len(payload)


def read_positions(document: dict, binary: bytes) -> list[tuple[float, float, float]]:
    accessor = document["accessors"][1]
    view = document["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", 12)
    return [
        struct.unpack_from("<fff", binary, start + index * stride)
        for index in range(accessor["count"])
    ]


def write_glb(path: Path, header: bytes, document: dict, binary: bytes, tail: bytes) -> None:
    json_chunk = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    bin_chunk = bytes(binary)
    bin_chunk += b"\0" * ((4 - len(bin_chunk) % 4) % 4)
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
        raise ValueError("O PNG do brasão não possui área visível")
    iw, ih = image.size
    left, top, right, bottom = alpha_bbox
    points = read_positions(document, original_binary)
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    u0, u1 = left / iw, right / iw
    v0, v1 = top / ih, bottom / ih
    uv_data = bytearray()
    for x, y, _z in points:
        u = u0 + (x - min_x) / max(max_x - min_x, 1e-9) * (u1 - u0)
        v = v1 - (y - min_y) / max(max_y - min_y, 1e-9) * (v1 - v0)
        uv_data.extend(struct.pack("<ff", u, v))

    binary = bytearray(original_binary)
    uv_offset, uv_length = append_blob(binary, bytes(uv_data))
    buffer_views = document.setdefault("bufferViews", [])
    uv_view = len(buffer_views)
    buffer_views.append({"buffer": 0, "byteOffset": uv_offset, "byteLength": uv_length, "target": 34962})
    accessors = document.setdefault("accessors", [])
    uv_accessor = len(accessors)
    accessors.append({"bufferView": uv_view, "componentType": 5126,
                      "count": len(points), "type": "VEC2",
                      "min": [u0, v0], "max": [u1, v1]})
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            primitive.setdefault("attributes", {})["TEXCOORD_0"] = uv_accessor

    image_offset, image_length = append_blob(binary, PNG_PATH.read_bytes())
    image_view = len(buffer_views)
    buffer_views.append({"buffer": 0, "byteOffset": image_offset, "byteLength": image_length})
    images = document.setdefault("images", [])
    image_index = len(images)
    images.append({"bufferView": image_view, "mimeType": "image/png", "name": "brasao_leao.png"})
    samplers = document.setdefault("samplers", [])
    sampler_index = len(samplers)
    samplers.append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
    textures = document.setdefault("textures", [])
    texture_index = len(textures)
    textures.append({"sampler": sampler_index, "source": image_index, "name": "brasao_leao.png"})

    materials = document.setdefault("materials", [])
    if not materials:
        materials.append({})
    material = materials[0]
    pbr = material.setdefault("pbrMetallicRoughness", {})
    pbr["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
    pbr["baseColorTexture"] = {"index": texture_index}
    pbr["metallicFactor"] = 0.0
    pbr["roughnessFactor"] = 0.72
    material["name"] = "Brasao_Leao_Texturizado"
    material["alphaMode"] = "BLEND"
    material["doubleSided"] = True
    document["buffers"][0]["byteLength"] = len(binary)
    write_glb(GLB_PATH, header, document, binary, tail)
    print(f"Textura aplicada em {GLB_PATH}")
    print(f"UVs: {len(points)} | PNG: {iw}x{ih} | alpha_bbox: {alpha_bbox}")


if __name__ == "__main__":
    main()
