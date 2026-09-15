"""Recolor the crocodile GLB from the matching crocodile thumbnail palette."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image


def read_glb(path: Path) -> tuple[dict, bytes, int, int]:
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise RuntimeError(f"GLB inválido: {path}")

    pos = 12
    json_chunk = None
    bin_chunk = None
    while pos < length:
        chunk_length, chunk_type = struct.unpack_from("<I4s", data, pos)
        pos += 8
        chunk_data = data[pos : pos + chunk_length]
        pos += chunk_length
        if chunk_type == b"JSON":
            json_chunk = chunk_data
        elif chunk_type == b"BIN\x00":
            bin_chunk = chunk_data
    if json_chunk is None or bin_chunk is None:
        raise RuntimeError(f"GLB sem JSON/BIN: {path}")
    return json.loads(json_chunk.rstrip(b" \t\r\n\x00")), bin_chunk, len(json_chunk), len(data)


def make_reference_lut(reference: Path) -> np.ndarray:
    ref = np.array(Image.open(reference).convert("RGBA"), dtype=np.uint8)
    rgb = ref[:, :, :3].astype(np.float32)
    alpha = ref[:, :, 3]
    mask = (alpha >= 8) & (rgb.max(axis=2) > 8)
    if not np.any(mask):
        raise RuntimeError(f"Referência sem pixels utilizáveis: {reference}")

    pixels = rgb[mask]
    luminance = pixels @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    centers: list[float] = []
    colors: list[np.ndarray] = []
    for lo in range(0, 256, 16):
        hi = lo + 16
        selected = (luminance >= lo) & (luminance < hi)
        if np.any(selected):
            centers.append((lo + hi - 1) * 0.5)
            colors.append(np.median(pixels[selected], axis=0))
    if len(centers) < 2:
        raise RuntimeError("Paleta insuficiente na referência")

    centers_np = np.asarray(centers, dtype=np.float32)
    colors_np = np.asarray(colors, dtype=np.float32)
    levels = np.arange(256, dtype=np.float32)
    lut = np.column_stack(
        [np.interp(levels, centers_np, colors_np[:, channel]) for channel in range(3)]
    )
    return np.clip(lut, 0, 255).astype(np.uint8)


def recolor_texture(texture: Image.Image, lut: np.ndarray) -> Image.Image:
    source = np.array(texture.convert("RGB"), dtype=np.uint8)
    source_float = source.astype(np.float32)
    luminance = np.clip(
        source_float @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32), 0, 255
    ).astype(np.uint8)
    recolored = lut[luminance]
    dark = source.max(axis=2) <= 8
    recolored[dark] = source[dark]
    return Image.fromarray(recolored, mode="RGB")


def patch_glb(input_path: Path, reference_path: Path, output_path: Path) -> None:
    document, binary, _json_length, _total_length = read_glb(input_path)
    images = document.get("images", [])
    if len(images) != 1 or "bufferView" not in images[0]:
        raise RuntimeError("Esperava uma única imagem embutida em bufferView")

    image_view_index = images[0]["bufferView"]
    views = document.get("bufferViews", [])
    image_view = views[image_view_index]
    image_offset = int(image_view.get("byteOffset", 0))
    image_length = int(image_view["byteLength"])
    image_end = image_offset + image_length
    if image_end != len(binary):
        raise RuntimeError("A imagem não é o último recurso do GLB; abortando para preservar a malha")

    with Image.open(__import__("io").BytesIO(binary[image_offset:image_end])) as embedded:
        lut = make_reference_lut(reference_path)
        recolored = recolor_texture(embedded, lut)
        import io

        encoded = io.BytesIO()
        recolored.save(encoded, format="JPEG", quality=94, subsampling=0, optimize=True)
        replacement = encoded.getvalue()

    new_binary = binary[:image_offset] + replacement
    new_binary += b"\x00" * ((4 - len(new_binary) % 4) % 4)
    image_view["byteLength"] = len(replacement)
    document["buffers"][0]["byteLength"] = len(new_binary)
    images[0]["mimeType"] = "image/jpeg"

    json_bytes = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    glb_length = 12 + 8 + len(json_bytes) + 8 + len(new_binary)
    header = struct.pack("<4sII", b"glTF", 2, glb_length)
    result = (
        header
        + struct.pack("<I4s", len(json_bytes), b"JSON")
        + json_bytes
        + struct.pack("<I4s", len(new_binary), b"BIN\x00")
        + new_binary
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_bytes(result)
    temporary.replace(output_path)
    print(f"saved {output_path} (texture {image_length} -> {len(replacement)} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if not args.reference.is_file():
        raise FileNotFoundError(args.reference)
    patch_glb(args.input, args.reference, args.output)


if __name__ == "__main__":
    main()
