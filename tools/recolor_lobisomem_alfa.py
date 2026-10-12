"""Create the Alfa's black-fur miniature from the base werewolf assets."""
from __future__ import annotations

import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PNG = ROOT / "assets/pawns/monstros/lobisomem/lobisomem.png"
SOURCE_GLB = ROOT / "assets/models3d/monstros/lobisomem.glb"
OUTPUT_PNG = ROOT / "assets/pawns/monstros/lobisomem_alfa/lobisomem_alfa.png"
OUTPUT_GLB = ROOT / "assets/models3d/monstros/lobisomem_alfa.glb"


def _black_coat(image: Image.Image, *, preserve_highlights: bool = True) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    rgb = rgba[..., :3].astype(np.float32)
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    saturation = np.divide(mx - mn, mx, out=np.zeros_like(mx), where=mx > 0)
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    # Neutral fur and the muted olive/brown fur highlights share this mask.
    # Converting by luminance keeps sculpted texture readable as charcoal.
    hue_mask = np.ones_like(luminance, dtype=bool)
    value = np.clip(9.0 + luminance * 0.34, 9.0, 88.0)
    shaded = np.stack((value * 0.80, value * 0.86, value), axis=2)
    # Preserve vivid red details and the miniature's alpha silhouette.
    vivid_red = (rgb[..., 0] > rgb[..., 1] * 1.32) & (rgb[..., 0] > rgb[..., 2] * 1.20)
    mask = hue_mask & ~vivid_red
    if preserve_highlights:
        # Teeth and claws remain legible; coat highlights still become dark gray.
        mask &= luminance < 225
    rgb[mask] = shaded[mask]
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def recolor_pawn() -> None:
    image = Image.open(SOURCE_PNG)
    result = _black_coat(image)
    # The source eyes are amber. In the face crop, shift only those saturated
    # amber pixels to red, keeping teeth and the surrounding fur untouched.
    px = np.asarray(result).copy()
    rgb = px[..., :3].astype(np.int16)
    original_rgb = np.asarray(image.convert("RGBA"))[..., :3].astype(np.int16)
    yy, xx = np.indices(rgb.shape[:2])
    eye = ((xx >= 226) & (xx <= 232) & (yy >= 94) & (yy <= 100))
    # Paint the visible iris as a small red glow with a brighter center.
    src = original_rgb
    iris = eye & (src[..., 0] > src[..., 1] * 1.14) \
        & (src[..., 1] > src[..., 2] * 1.10) & (src[..., 0] > 70)
    px[..., 0][iris] = np.clip(src[..., 0][iris] * 1.35, 175, 255).astype(np.uint8)
    px[..., 1][iris] = np.clip(src[..., 1][iris] * 0.08, 0, 18).astype(np.uint8)
    px[..., 2][iris] = np.clip(src[..., 2][iris] * 0.10, 0, 22).astype(np.uint8)
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(px, "RGBA").save(OUTPUT_PNG, optimize=True)


def _glb_chunks(data: bytes):
    if data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2:
        raise ValueError("GLB de origem inválido")
    offset = 12
    chunks = []
    while offset < len(data):
        size, kind = struct.unpack_from("<I4s", data, offset)
        chunks.append((kind, data[offset + 8:offset + 8 + size]))
        offset += 8 + size
    return chunks


def recolor_glb() -> None:
    chunks = _glb_chunks(SOURCE_GLB.read_bytes())
    doc = json.loads(next(body for kind, body in chunks if kind == b"JSON").decode("utf-8").rstrip(" \0"))
    bin_data = bytearray(next(body for kind, body in chunks if kind == b"BIN\0"))
    image = doc["images"][0]
    view = doc["bufferViews"][image["bufferView"]]
    start = int(view.get("byteOffset", 0))
    end = start + int(view["byteLength"])
    texture = Image.open(io.BytesIO(bin_data[start:end])).convert("RGB")
    recolored = _black_coat(texture, preserve_highlights=False).convert("RGB")
    output = io.BytesIO()
    recolored.save(output, format="JPEG", quality=96, subsampling=0, optimize=True)
    encoded = output.getvalue()

    # The source atlas is the final bufferView. Replace only its embedded JPEG;
    # every mesh/index/UV/transform byte remains identical.
    if end != len(bin_data) - (len(bin_data) % 4):
        trailing = bytes(bin_data[end:])
        if any(trailing):
            raise ValueError("A textura não é o último bufferView do GLB")
    bin_data = bin_data[:start] + encoded
    while len(bin_data) % 4:
        bin_data.append(0)
    view["byteLength"] = len(encoded)
    doc["buffers"][0]["byteLength"] = len(bin_data)
    json_data = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_data += b" " * ((-len(json_data)) % 4)
    bin_body = bytes(bin_data)
    body = (struct.pack("<I4s", len(json_data), b"JSON") + json_data
            + struct.pack("<I4s", len(bin_body), b"BIN\0") + bin_body)
    OUTPUT_GLB.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)


if __name__ == "__main__":
    recolor_pawn()
    recolor_glb()
    print(f"PNG: {OUTPUT_PNG}")
    print(f"GLB: {OUTPUT_GLB}")
