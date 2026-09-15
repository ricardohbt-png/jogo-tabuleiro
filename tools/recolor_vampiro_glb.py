"""Tune Vampire GLB materials to match its painted miniature reference."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


PALETTE = {
    # Palidez fria de morto-vivo, sem o branco brilhante do material anterior.
    "pele": ((0.31, 0.29, 0.275), 0.0, 0.90),
    "cabelo": ((0.018, 0.015, 0.016), 0.0, 0.91),
    # Casaco preto-azulado: a cor só aparece nas dobras iluminadas.
    "casaco": ((0.018, 0.026, 0.038), 0.0, 0.94),
    # Forro e faixa em vinho ressecado, não vermelho saturado.
    "forro": ((0.065, 0.009, 0.014), 0.0, 0.94),
    "camisa": ((0.22, 0.19, 0.145), 0.0, 0.91),
    "faixa": ((0.10, 0.008, 0.012), 0.0, 0.90),
    # Couro antigo e calça de carvão, coerentes com a arte escura.
    "couro": ((0.075, 0.035, 0.014), 0.0, 0.93),
    "calca": ((0.020, 0.017, 0.015), 0.0, 0.96),
    "aco": ((0.10, 0.11, 0.12), 0.70, 0.60),
    # Lajes de cripta em vez do piso de pedra clara.
    "pedra": ((0.050, 0.045, 0.035), 0.0, 0.96),
    "prato": ((0.012, 0.011, 0.012), 0.0, 0.96),
}


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise RuntimeError(f"GLB inválido: {path}")
    pos = 12
    document = None
    binary = None
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


def patch_materials(document: dict) -> None:
    materials = {m.get("name"): m for m in document.get("materials", [])}
    missing = sorted(set(PALETTE) - set(materials))
    if missing:
        raise RuntimeError("Materiais esperados ausentes: " + ", ".join(missing))
    for name, (color, metallic, roughness) in PALETTE.items():
        pbr = materials[name].setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = [*color, 1.0]
        pbr["metallicFactor"] = metallic
        pbr["roughnessFactor"] = roughness


def write_glb(document: dict, binary: bytes, output: Path) -> None:
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    document["buffers"][0]["byteLength"] = len(binary)
    json_bytes = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary)
    result = (
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<I4s", len(json_bytes), b"JSON")
        + json_bytes
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + binary
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_bytes(result)
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    document, binary = read_glb(args.input)
    patch_materials(document)
    write_glb(document, binary, args.output)
    print(f"saved {args.output} (materials={len(PALETTE)})")


if __name__ == "__main__":
    main()
