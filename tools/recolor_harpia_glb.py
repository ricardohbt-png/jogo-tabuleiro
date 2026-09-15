"""Ajusta os materiais da Harpia para a paleta de harpia.png."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


# Tons de ave de rapina envelhecida: pele bege fria, penas cinza-terra e
# detalhes ocre apagados, evitando o contraste marrom/preto do arquivo-base.
PALETTE = {
    "pele": ((0.32, 0.285, 0.235), 0.0, 0.90),
    "pena": ((0.190, 0.162, 0.125), 0.0, 0.92),
    "cabelo": ((0.072, 0.067, 0.061), 0.0, 0.95),
    "escama": ((0.245, 0.158, 0.042), 0.0, 0.88),
    "garra": ((0.025, 0.024, 0.022), 0.0, 0.93),
    "couro": ((0.045, 0.026, 0.014), 0.0, 0.94),
    "pedra": ((0.085, 0.078, 0.069), 0.0, 0.97),
    "plinto": ((0.016, 0.016, 0.018), 0.0, 0.96),
    "pena_esc": ((0.130, 0.105, 0.079), 0.0, 0.94),
    "pena_coxa": ((0.145, 0.118, 0.086), 0.0, 0.93),
}


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise RuntimeError(f"GLB inválido: {path}")
    pos, document, binary = 12, None, None
    while pos < length:
        chunk_length, chunk_type = struct.unpack_from("<I4s", data, pos)
        pos += 8
        chunk = data[pos : pos + chunk_length]
        pos += chunk_length
        if chunk_type == b"JSON":
            document = json.loads(chunk.rstrip(b" \t\r\n\x00"))
        elif chunk_type == b"BIN\x00":
            binary = chunk
    if document is None or binary is None:
        raise RuntimeError("GLB sem JSON/BIN")
    return document, binary


def write_glb(document: dict, binary: bytes, output: Path) -> None:
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    document["buffers"][0]["byteLength"] = len(binary)
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raw += b" " * ((4 - len(raw) % 4) % 4)
    total = 12 + 8 + len(raw) + 8 + len(binary)
    result = (struct.pack("<4sII", b"glTF", 2, total)
              + struct.pack("<I4s", len(raw), b"JSON") + raw
              + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_bytes(result)
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document, binary = read_glb(args.input)
    materials = {m.get("name"): m for m in document.get("materials", [])}
    missing = sorted(set(PALETTE) - set(materials))
    if missing:
        raise RuntimeError("Materiais esperados ausentes: " + ", ".join(missing))
    for name, (color, metallic, roughness) in PALETTE.items():
        pbr = materials[name].setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = [*color, 1.0]
        pbr["metallicFactor"] = metallic
        pbr["roughnessFactor"] = roughness
    write_glb(document, binary, args.output)
    print(f"saved {args.output} (materials={len(PALETTE)})")


if __name__ == "__main__":
    main()
