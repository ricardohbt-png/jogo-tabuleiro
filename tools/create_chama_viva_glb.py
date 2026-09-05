"""Cria a miniatura GLB animada da decoração Chama Viva.

Roda da raiz: python tools/create_chama_viva_glb.py
O arquivo gerado usa somente glTF 2.0 padrão, sem dependências externas, para
ser carregado pelo GLTFLoader r128 já usado pelo cliente.
"""
from __future__ import annotations

import json
import math
import os
import struct


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "assets", "objetos", "chama_viva.glb")


class Builder:
    def __init__(self):
        self.binary = bytearray()
        self.buffer_views = []
        self.accessors = []

    def _align(self, n=4):
        while len(self.binary) % n:
            self.binary.append(0)

    def view(self, payload: bytes, target=None):
        self._align()
        offset = len(self.binary)
        self.binary.extend(payload)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        if target is not None:
            view["target"] = target
        self.buffer_views.append(view)
        return len(self.buffer_views) - 1

    def accessor(self, view, component_type, count, kind, minimum=None, maximum=None):
        out = {
            "bufferView": view,
            "componentType": component_type,
            "count": count,
            "type": kind,
        }
        if minimum is not None:
            out["min"] = minimum
        if maximum is not None:
            out["max"] = maximum
        self.accessors.append(out)
        return len(self.accessors) - 1


def vec_accessor(builder, values, kind):
    flat = [float(v) for row in values for v in row]
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
    payload = struct.pack("<%sf" % len(flat), *flat)
    mins = [min(row[i] for row in values) for i in range(width)]
    maxs = [max(row[i] for row in values) for i in range(width)]
    view = builder.view(payload, 34962)
    return builder.accessor(view, 5126, len(values), kind, mins, maxs)


def index_accessor(builder, values):
    payload = struct.pack("<%sH" % len(values), *values)
    view = builder.view(payload, 34963)
    return builder.accessor(view, 5123, len(values), "SCALAR", [min(values)], [max(values)])


def flame_mesh(builder, material_index, base_radius, height, lean):
    """Low-poly flame tongue made of three rings and one tip."""
    segments = 8
    vertices = []
    rings = ((0.0, base_radius), (height * 0.34, base_radius * 0.78),
             (height * 0.68, base_radius * 0.42))
    for y, radius in rings:
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            vertices.append([math.cos(a) * radius, y, math.sin(a) * radius * 0.82])
    tip = len(vertices)
    vertices.append([lean, height, 0.0])
    faces = []
    for ring in range(2):
        start = ring * segments
        nxt = (ring + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.extend((start + i, start + j, nxt + j, start + i, nxt + j, nxt + i))
    top = 2 * segments
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend((top + i, top + j, tip))
    # Fundo fechado para não deixar a chama aberta vista de cima/baixo.
    for i in range(1, segments - 1):
        faces.extend((0, i + 1, i))
    return {
        "primitives": [{
            "attributes": {"POSITION": vec_accessor(builder, vertices, "VEC3")},
            "indices": index_accessor(builder, faces),
            "material": material_index,
        }]
    }


def disc_mesh(builder, material_index, radius=0.36, height=0.08):
    segments = 12
    vertices = [[0.0, 0.0, 0.0], [0.0, height, 0.0]]
    for y in (0.0, height):
        vertices.extend([
            [math.cos(2 * math.pi * i / segments) * radius, y,
             math.sin(2 * math.pi * i / segments) * radius]
            for i in range(segments)
        ])
    faces = []
    low, high = 2, 2 + segments
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend((0, low + j, low + i, 1, high + i, high + j))
        faces.extend((low + i, low + j, high + j, low + i, high + j, high + i))
    return {
        "primitives": [{
            "attributes": {"POSITION": vec_accessor(builder, vertices, "VEC3")},
            "indices": index_accessor(builder, faces),
            "material": material_index,
        }]
    }


def quaternion_z(angle):
    return [0.0, 0.0, math.sin(angle / 2.0), math.cos(angle / 2.0)]


def build():
    b = Builder()
    materials = [
        {"pbrMetallicRoughness": {"baseColorFactor": [0.18, 0.025, 0.005, 1], "metallicFactor": 0.0, "roughnessFactor": 0.9}},
        {"pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.12, 0.005, 1], "metallicFactor": 0.0, "roughnessFactor": 0.55}, "emissiveFactor": [0.9, 0.025, 0.0]},
        {"pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.52, 0.015, 1], "metallicFactor": 0.0, "roughnessFactor": 0.45}, "emissiveFactor": [1.0, 0.18, 0.005]},
        {"pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.92, 0.24, 1], "metallicFactor": 0.0, "roughnessFactor": 0.35}, "emissiveFactor": [1.0, 0.65, 0.04]},
    ]
    meshes = [
        disc_mesh(b, 0),
        flame_mesh(b, 1, 0.31, 0.88, -0.10),
        flame_mesh(b, 2, 0.23, 0.70, 0.08),
        flame_mesh(b, 3, 0.13, 0.48, -0.03),
    ]
    nodes = [
        {"name": "Brasa", "mesh": 0},
        {"name": "Chama externa", "mesh": 1, "translation": [0.0, 0.08, 0.0]},
        {"name": "Chama interna", "mesh": 2, "translation": [0.0, 0.10, 0.0], "scale": [0.82, 0.82, 0.82]},
        {"name": "Nucleo luminoso", "mesh": 3, "translation": [0.0, 0.12, 0.0], "scale": [0.72, 0.72, 0.72]},
    ]
    times = [0.0, 0.18, 0.39, 0.62, 0.86, 1.10, 1.28]
    time_accessor = vec_accessor(b, [[v] for v in times], "SCALAR")
    samplers = []
    channels = []

    def animate_scale(node_index, values):
        out = vec_accessor(b, values, "VEC3")
        sampler = len(samplers)
        samplers.append({"input": time_accessor, "output": out, "interpolation": "LINEAR"})
        channels.append({"sampler": sampler, "target": {"node": node_index, "path": "scale"}})

    def animate_rotation(node_index, angles):
        out = vec_accessor(b, [quaternion_z(a) for a in angles], "VEC4")
        sampler = len(samplers)
        samplers.append({"input": time_accessor, "output": out, "interpolation": "LINEAR"})
        channels.append({"sampler": sampler, "target": {"node": node_index, "path": "rotation"}})

    animate_scale(1, [[1.00, 0.92, 1.00], [1.05, 1.12, 0.98], [0.96, 1.02, 1.04],
                      [1.08, 0.88, 0.95], [0.94, 1.15, 1.02], [1.03, 0.98, 1.00], [1.00, 0.92, 1.00]])
    animate_scale(2, [[0.82, 0.82, 0.82], [0.76, 0.94, 0.80], [0.88, 0.78, 0.84],
                      [0.72, 1.00, 0.82], [0.90, 0.86, 0.88], [0.80, 0.92, 0.80], [0.82, 0.82, 0.82]])
    animate_scale(3, [[0.72, 0.72, 0.72], [0.62, 0.88, 0.68], [0.80, 0.64, 0.74],
                      [0.66, 0.92, 0.68], [0.78, 0.70, 0.76], [0.68, 0.84, 0.70], [0.72, 0.72, 0.72]])
    animate_rotation(1, [0.00, 0.10, -0.08, 0.13, -0.12, 0.06, 0.00])
    animate_rotation(2, [0.00, -0.14, 0.11, -0.08, 0.15, -0.05, 0.00])
    animate_rotation(3, [0.00, 0.18, -0.16, 0.10, -0.12, 0.08, 0.00])

    doc = {
        "asset": {"version": "2.0", "generator": "Legends for Hire flame generator"},
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2, 3]}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "bufferViews": b.buffer_views,
        "accessors": b.accessors,
        "buffers": [{"byteLength": len(b.binary)}],
        "animations": [{"name": "Chama Viva Loop", "samplers": samplers, "channels": channels}],
    }
    json_bytes = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    bin_bytes = bytes(b.binary)
    bin_bytes += b"\0" * ((4 - len(bin_bytes) % 4) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    out = bytearray(struct.pack("<4sII", b"glTF", 2, total))
    out.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    out.extend(json_bytes)
    out.extend(struct.pack("<I4s", len(bin_bytes), b"BIN\0"))
    out.extend(bin_bytes)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "wb") as fh:
        fh.write(out)
    print(f"GLB criado: {DEST} ({len(out)} bytes)")


if __name__ == "__main__":
    build()
