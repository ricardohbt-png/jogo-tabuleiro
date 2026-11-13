"""Cria o GLB próprio do Urso Pardo com uma paleta marrom enegrecida.

Executar da raiz do projeto: python -X utf8 tools/recolor_urso_pardo_glb.py
O modelo original do Urso Negro permanece intacto; geometria, UVs e textura
embutida são preservados, alterando apenas o fator de cor e a rugosidade.
"""
from pathlib import Path
import json
import struct


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models3d/monstros/urso.glb"
OUTPUT = ROOT / "assets/models3d/monstros/urso_pardo.glb"
GLB_MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def read_chunks(data):
    magic, version, total_length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2 or total_length != len(data):
        raise ValueError("GLB inválido ou versão incompatível")
    chunks = []
    offset = 12
    while offset < len(data):
        length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunks.append((chunk_type, data[offset:offset + length]))
        offset += length
    return chunks


def write_chunks(chunks):
    encoded = bytearray()
    for chunk_type, payload in chunks:
        encoded.extend(struct.pack("<II", len(payload), chunk_type))
        encoded.extend(payload)
    return struct.pack("<III", GLB_MAGIC, 2, 12 + len(encoded)) + encoded


def main():
    chunks = read_chunks(SOURCE.read_bytes())
    json_index = next((i for i, (kind, _) in enumerate(chunks)
                       if kind == JSON_CHUNK), None)
    if json_index is None:
        raise ValueError("O GLB não contém chunk JSON")

    document = json.loads(chunks[json_index][1].decode("utf-8").rstrip(" \t\r\n\0"))
    materials = document.get("materials", [])
    if not materials:
        raise ValueError("O GLB original não contém materiais para recolorir")

    # Tom castanho escuro, quase preto, multiplicado pela textura original.
    for material in materials:
        pbr = material.setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = [0.08, 0.035, 0.018, 1.0]
        pbr["roughnessFactor"] = 0.90
        pbr["metallicFactor"] = 0.0

    json_bytes = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    chunks[json_index] = (JSON_CHUNK, json_bytes)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".tmp.glb")
    temporary.write_bytes(write_chunks(chunks))
    temporary.replace(OUTPUT)
    print(f"Criado {OUTPUT} ({len(materials)} materiais; geometria e textura preservadas)")


if __name__ == "__main__":
    main()
