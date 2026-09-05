"""Faz o brasão texturizado reproduzir as cores do PNG sem alteração da luz 3D."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / "assets" / "objetos" / "brasao_leao.glb"
UNLIT = "KHR_materials_unlit"


def main() -> None:
    data = GLB_PATH.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError("GLB inválido")
    version, _declared_length = struct.unpack_from("<II", data, 4)
    json_length, chunk_type = struct.unpack_from("<II", data, 12)
    if version != 2 or chunk_type != 0x4E4F534A:
        raise ValueError("Cabeçalho GLB incompatível")
    json_end = 20 + json_length
    document = json.loads(data[20:json_end].rstrip(b" \t\r\n"))
    materials = document.get("materials", [])
    if not materials:
        raise ValueError("O GLB não possui material")
    material = materials[0]
    extensions_used = document.setdefault("extensionsUsed", [])
    if UNLIT not in extensions_used:
        extensions_used.append(UNLIT)
    material.setdefault("extensions", {})[UNLIT] = {}
    material["pbrMetallicRoughness"]["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
    # O GLB original não tinha material na primitiva; sem esta referência o
    # Three.js usa o material branco padrão e ignora a textura do brasão.
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            primitive["material"] = 0

    json_chunk = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    remainder = data[json_end:]
    total_length = 12 + 8 + len(json_chunk) + len(remainder)
    output = data[:8] + struct.pack("<I", total_length)
    output += struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk + remainder
    GLB_PATH.write_bytes(output)
    print(f"Material unlit aplicado em {GLB_PATH}")


if __name__ == "__main__":
    main()
