"""Aplica a paleta bordô da cortina vermelha ao seu modelo GLB."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / "assets" / "objetos" / "cortina_vermelha.glb"


def read_glb(path: Path) -> tuple[bytes, dict, bytes]:
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
    return data[:12], document, data[json_end:]


def write_glb(path: Path, header: bytes, document: dict, remainder: bytes) -> None:
    json_chunk = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    total_length = 12 + 8 + len(json_chunk) + len(remainder)
    output = header[:8] + struct.pack("<I", total_length)
    output += struct.pack("<II", len(json_chunk), 0x4E4F534A)
    output += json_chunk + remainder
    path.write_bytes(output)


def main() -> None:
    header, document, remainder = read_glb(GLB_PATH)
    materials = document.setdefault("materials", [])
    material = {
        "name": "Veludo_Bordo_Cortina",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.30, 0.018, 0.045, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.80,
        },
    }
    material_index = next(
        (i for i, existing in enumerate(materials)
         if existing.get("name") == material["name"]),
        None,
    )
    if material_index is None:
        material_index = len(materials)
        materials.append(material)
    else:
        materials[material_index] = material

    assigned = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            primitive["material"] = material_index
            assigned += 1
    if not assigned:
        raise ValueError("O GLB não contém primitivas para receber o material")

    write_glb(GLB_PATH, header, document, remainder)
    print(f"Material aplicado em {GLB_PATH}")
    print(f"Primitivas atualizadas: {assigned}")
    print(materials[material_index])


if __name__ == "__main__":
    main()
