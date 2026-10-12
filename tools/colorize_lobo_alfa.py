"""Cria a miniatura preto e branco do Lobo Alfa a partir do lobo cinzento."""
from __future__ import annotations

import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PNG = ROOT / "assets/pawns/monstros/loboCinzento/loboCinzento.png"
SOURCE_GLB = ROOT / "assets/models3d/monstros/lobo.glb"
OUTPUT_PNG = ROOT / "assets/pawns/monstros/lobo_alfa/lobo_alfa.png"
OUTPUT_GLB = ROOT / "assets/models3d/monstros/lobo_alfa.glb"


def _lobo_preto_branco(image: Image.Image, *, atlas: bool = False) -> Image.Image:
    """Escurece a pelagem e deixa faixas claras com transições texturizadas."""
    rgba = np.asarray(image.convert("RGBA")).copy()
    rgb = rgba[..., :3].astype(np.float32)
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = maximum - minimum
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    neutral = saturation < (76 if not atlas else 42)

    # Preto com detalhe cinza nas áreas de sombra, preservando a textura esculpida.
    dark = np.clip(11 + luminance * 0.30, 11, 70)
    result = np.stack((dark * 0.84, dark * 0.91, dark), axis=2)

    if not atlas:
        height, width = luminance.shape
        yy, xx = np.indices((height, width), dtype=np.float32)
        # Máscaras ovais em zonas de pelagem: focinho, peito/pernas dianteiras e flanco.
        white_zones = [
            (0.19, 0.41, 0.12, 0.09, 0.86),
            (0.30, 0.55, 0.11, 0.17, 0.92),
            (0.20, 0.62, 0.09, 0.16, 0.86),
            (0.37, 0.62, 0.07, 0.17, 0.80),
        ]
        white_strength = np.zeros_like(luminance)
        for cx, cy, rx, ry, opacity in white_zones:
            x_norm, y_norm = xx / width, yy / height
            distance = ((x_norm - cx) / rx) ** 2 + ((y_norm - cy) / ry) ** 2
            # A borda irregular evita manchas geométricas lisas e imita a quebra
            # natural da pelagem entre as áreas claras e escuras.
            irregular = (np.sin(xx * 0.047 + yy * 0.031)
                         + 0.55 * np.sin(xx * 0.083 - yy * 0.059)
                         + 0.3 * np.sin(xx * 0.019 + yy * 0.091)) * 0.055
            edge = np.clip((1.08 + irregular - distance) / 0.24, 0, 1)
            edge = edge * edge * (3 - 2 * edge)
            white_strength = np.maximum(white_strength, edge * opacity)
        # O pedestal começa abaixo do corpo: não o converte em pelagem.
        white_strength *= (yy < height * 0.72)
        # Uma faixa clara irregular no flanco, como a barriga/peito de um lobo
        # de pelagem bicolor, mantém as costas negras e quebra o oval anterior.
        x_norm, y_norm = xx / width, yy / height
        top = np.clip((y_norm - 0.30) / 0.035, 0, 1)
        bottom = np.clip((0.46 - y_norm) / 0.045, 0, 1)
        left = np.clip((x_norm - 0.42) / 0.05, 0, 1)
        right = np.clip((0.79 - x_norm) / 0.06, 0, 1)
        band_noise = 0.82 + 0.18 * np.clip(
            0.5 + 0.25 * np.sin(xx * 0.041 + yy * 0.029)
            + 0.25 * np.sin(xx * 0.073 - yy * 0.047), 0, 1)
        flank_band = top * bottom * left * right * band_noise
        white_strength = np.maximum(white_strength, flank_band * 0.82)
        white = np.clip(166 + luminance * 0.30, 166, 242)
        light = np.stack((white, white * 0.99, white * 0.94), axis=2)
        result = result * (1 - white_strength[..., None]) + light * white_strength[..., None]
        coat = neutral & (yy < height * 0.74) & (luminance > 24)
    else:
        # Atlas UV: as ilhas de pelo são predominantemente neutras e ficam na metade superior.
        yy = np.indices(luminance.shape, dtype=np.float32)[0]
        light_strength = np.clip((luminance - 35) / 30, 0, 1)
        light_strength = light_strength * (yy < luminance.shape[0] * 0.64)
        white = np.clip(163 + luminance * 0.32, 163, 235)
        light = np.stack((white, white * 0.99, white * 0.94), axis=2)
        result = result * (1 - light_strength[..., None]) + light * light_strength[..., None]
        coat = neutral & (yy < luminance.shape[0] * 0.64) & (luminance > 20)

    # Olhos, nariz, boca, dentes, base e detalhes coloridos mantêm a pintura original.
    rgb[coat] = result[coat]
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def colorize_png() -> None:
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    _lobo_preto_branco(Image.open(SOURCE_PNG)).save(OUTPUT_PNG, optimize=True)


def _glb_chunks(data: bytes):
    if data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2:
        raise ValueError("GLB do lobo inválido")
    offset = 12
    chunks = []
    while offset < len(data):
        size, kind = struct.unpack_from("<I4s", data, offset)
        chunks.append((kind, data[offset + 8:offset + 8 + size]))
        offset += 8 + size
    return chunks


def colorize_glb() -> None:
    chunks = _glb_chunks(SOURCE_GLB.read_bytes())
    doc = json.loads(next(body for kind, body in chunks if kind == b"JSON").decode("utf-8").rstrip(" \0"))
    bin_data = bytearray(next(body for kind, body in chunks if kind == b"BIN\0"))
    image = doc["images"][0]
    view = doc["bufferViews"][image["bufferView"]]
    start = int(view.get("byteOffset", 0))
    end = start + int(view["byteLength"])
    atlas = Image.open(io.BytesIO(bin_data[start:end])).convert("RGBA")
    recolored = _lobo_preto_branco(atlas, atlas=True).convert("RGB")
    output = io.BytesIO()
    recolored.save(output, format="JPEG", quality=96, subsampling=0, optimize=True)
    encoded = output.getvalue()
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
    colorize_png()
    colorize_glb()
    print(f"PNG: {OUTPUT_PNG}")
    print(f"GLB: {OUTPUT_GLB}")
