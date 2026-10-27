"""Darken only the cloak and hat materials of the Kobold Magician GLB.

The GLB JSON chunk is edited in place within a copied container so vertex,
index, UV, normal, and embedded texture bytes remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


JSON_CHUNK = 0x4E4F534A
PALETTE = {
    # Velvet cloak: black base, visible charcoal folds, gray stitching.
    "Veludo negro": ((0.008, 0.009, 0.012, 1.0), 0.0, 0.91),
    "Veludo gasto": ((0.070, 0.075, 0.086, 1.0), 0.0, 0.84),
    "Veludo em sombra": ((0.014, 0.016, 0.020, 1.0), 0.0, 0.95),
    "Bordado bronze escuro": ((0.150, 0.160, 0.180, 1.0), 0.12, 0.72),
    # Hat: black leather with gray worn edges, seams, and band.
    "Couro da copa": ((0.010, 0.012, 0.016, 1.0), 0.0, 0.90),
    "Couro gasto": ((0.076, 0.082, 0.094, 1.0), 0.0, 0.83),
    "Couro em sombra": ((0.006, 0.008, 0.011, 1.0), 0.0, 0.96),
    "Couro da aba": ((0.025, 0.029, 0.036, 1.0), 0.0, 0.91),
    "Aba gasta": ((0.125, 0.135, 0.153, 1.0), 0.0, 0.82),
    "Faixa bronze": ((0.190, 0.200, 0.220, 1.0), 0.18, 0.70),
    "Faixa sombreada": ((0.052, 0.058, 0.068, 1.0), 0.05, 0.88),
}


def _glb_chunks(data: bytes):
    if len(data) < 20:
        raise ValueError("Arquivo GLB curto demais")
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2 or total != len(data):
        raise ValueError("Cabeçalho GLB inválido ou versão não suportada")
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        start = offset + 8
        end = start + length
        if end > len(data):
            raise ValueError("Chunk GLB truncado")
        yield offset, length, kind, data[start:end]
        offset = end
    if offset != len(data):
        raise ValueError("Chunks GLB desalinhados")


def recolor(source: Path, output: Path) -> dict:
    original = source.read_bytes()
    chunks = list(_glb_chunks(original))
    json_chunks = [i for i, chunk in enumerate(chunks) if chunk[2] == JSON_CHUNK]
    if len(json_chunks) != 1:
        raise ValueError("Esperava exatamente um chunk JSON no GLB")

    chunk_index = json_chunks[0]
    doc = json.loads(chunks[chunk_index][3].decode("utf-8").rstrip(" \t\r\n\0"))
    materials = doc.get("materials") or []
    found = set()
    for material in materials:
        name = material.get("name")
        if name not in PALETTE:
            continue
        color, metallic, roughness = PALETTE[name]
        pbr = material.setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = list(color)
        pbr["metallicFactor"] = metallic
        pbr["roughnessFactor"] = roughness
        found.add(name)

    missing = sorted(set(PALETTE) - found)
    if missing:
        raise ValueError("Materiais do manto/chapéu ausentes: " + ", ".join(missing))

    encoded = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((-len(encoded)) % 4)
    result = bytearray(struct.pack("<III", 0x46546C67, 2, 0))
    for i, (_old_offset, _old_length, kind, payload) in enumerate(chunks):
        if i == chunk_index:
            payload = encoded
        result += struct.pack("<II", len(payload), kind)
        result += payload
    struct.pack_into("<I", result, 8, len(result))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)

    # The binary chunk holds all geometry and embedded texture data; it must
    # match the original byte-for-byte after the material-only edit.
    before_bin = [chunk[3] for chunk in chunks if chunk[2] != JSON_CHUNK]
    after_bin = [chunk[3] for chunk in _glb_chunks(bytes(result)) if chunk[2] != JSON_CHUNK]
    if before_bin != after_bin:
        output.unlink(missing_ok=True)
        raise RuntimeError("Os chunks binários mudaram durante a recoloração")
    return {
        "materials": sorted(found),
        "geometry_texture_sha256": hashlib.sha256(b"".join(before_bin)).hexdigest(),
        "input_bytes": len(original),
        "output_bytes": len(result),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = recolor(args.source, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
