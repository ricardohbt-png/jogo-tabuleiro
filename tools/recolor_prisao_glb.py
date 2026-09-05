"""Aplica uma paleta de rocha escura e metal sujo à prisão.glb."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / "assets" / "objetos" / "prisao.glb"


ROCK_COLORS = {
    0: [0.11, 0.12, 0.13, 1.0],
    1: [0.16, 0.17, 0.18, 1.0],
    2: [0.09, 0.10, 0.11, 1.0],
    3: [0.19, 0.20, 0.21, 1.0],
}
DIRTY_METAL_COLOR = [0.19, 0.20, 0.18, 1.0]


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
    materials = document.get("materials", [])
    if len(materials) < 6:
        raise ValueError("A prisão.glb não contém os seis materiais esperados")

    for index, color in ROCK_COLORS.items():
        pbr = materials[index].setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = color
        pbr["metallicFactor"] = 0.0
        pbr["roughnessFactor"] = 0.90

    metal = materials[5].setdefault("pbrMetallicRoughness", {})
    metal["baseColorFactor"] = DIRTY_METAL_COLOR
    metal["metallicFactor"] = 0.70
    metal["roughnessFactor"] = 0.84

    write_glb(GLB_PATH, header, document, remainder)
    print(f"Materiais atualizados em {GLB_PATH}")
    for index in (*ROCK_COLORS, 5):
        pbr = materials[index]["pbrMetallicRoughness"]
        print(
            index,
            materials[index].get("name"),
            "baseColorFactor=",
            pbr["baseColorFactor"],
            "metallicFactor=",
            pbr.get("metallicFactor"),
            "roughnessFactor=",
            pbr.get("roughnessFactor"),
        )


if __name__ == "__main__":
    main()
