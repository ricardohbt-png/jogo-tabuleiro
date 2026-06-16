#!/usr/bin/env python3
"""
Gera peões-standee 3D dos heróis — peça de tabuleiro clássica.
================================================================
A figura recortada da foto vira uma placa com espessura discreta e uniforme
(como peça de acrílico impressa): foto da FRENTE num lado, foto das COSTAS no
outro, borda lateral escura limpa. Silhueta exata, sem deformação — visual de
peça física de jogo, de pé sobre a base de madeira que o jogo já desenha.

Uso:
    python gerar_standee.py            # todos os personagens
    python gerar_standee.py richard    # só um

Entrada: assets/pawns/_fontes/<Personagem>/frente|costas.(png|jpeg)
         (fallback: ficha única <Personagem>.jpeg)
Saída  : assets/models3d/<classe>.glb
"""

import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, zoom
from shapely.geometry import Polygon
from skimage import measure

# Reusa recorte (rembg), remoção de pedestal, fichas e mapeamento de classes
import gerar_miniaturas_3d as G

BASE  = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro")
SAIDA = BASE / "assets" / "models3d"

ESPESSURA  = 0.075   # espessura da placa, fração da altura da figura
COR_BORDA  = [38, 34, 40, 255]   # lateral "acrílico" grafite-escuro
SIMPLIFICA = 1.6     # tolerância (px) da simplificação do contorno
TEX_LADO   = 1024    # resolução máx. das texturas embutidas


# ── Texturas ───────────────────────────────────────────────────────────────────

def _preencher_fora(rgb, alpha):
    """Pixels de fora recebem a cor sólida mais próxima (sem franja na borda)."""
    _, (iy, ix) = distance_transform_edt(alpha < 0.5, return_indices=True)
    return rgb[iy, ix]


def alinhar_verso(rgbB, aB, aF):
    """Espelha o verso e o alinha RIGIDAMENTE à frente (altura pelos pés/topo,
    centro pelo centroide) — preserva as proporções da foto, sem esticamento.
    Onde a silhueta da frente extrapola a das costas, preenche com a cor mais
    próxima das costas."""
    rgbB, aB = rgbB[:, ::-1].astype(np.float64), aB[:, ::-1]
    h, w = aF.shape

    ysF, xsF = np.where(aF > 0.5)
    ysB, xsB = np.where(aB > 0.5)
    esc = (ysF.max() - ysF.min() + 1) / max(ysB.max() - ysB.min() + 1, 1)

    rgbB = zoom(rgbB, (esc, esc, 1), order=1)
    aB = zoom(aB, (esc, esc), order=1)
    ysB2, xsB2 = np.where(aB > 0.5)

    # desloca: pés alinhados, centroides x alinhados
    dy = int(round(ysF.max() - ysB2.max()))
    dx = int(round(xsF.mean() - xsB2.mean()))

    outR = np.zeros((h, w, 3))
    outA = np.zeros((h, w))
    sy0, sy1 = max(0, -dy), min(aB.shape[0], h - dy)
    sx0, sx1 = max(0, -dx), min(aB.shape[1], w - dx)
    if sy1 > sy0 and sx1 > sx0:
        outR[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx] = rgbB[sy0:sy1, sx0:sx1]
        outA[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx] = aB[sy0:sy1, sx0:sx1]

    # preenche o que a frente cobre e as costas não (bordas levemente diferentes);
    # escurece o preenchido para ler como sombra em vez de franja clara
    cheio = _preencher_fora(outR, outA)
    sombra = np.where((outA > 0.5)[..., None], 1.0, 0.52)
    return cheio * sombra


def _textura(rgb, alpha):
    cheio = _preencher_fora(rgb, alpha)
    img = Image.fromarray(np.clip(cheio, 0, 255).astype(np.uint8), 'RGB')
    if max(img.size) > TEX_LADO:
        f = TEX_LADO / max(img.size)
        img = img.resize((int(img.width * f), int(img.height * f)), Image.LANCZOS)
    return img


# ── Geometria ──────────────────────────────────────────────────────────────────

def poligono_da_silhueta(alpha):
    """Contorno suavizado da figura → shapely Polygon (maior componente + furos)."""
    a = gaussian_filter(alpha, sigma=1.4)
    a = np.pad(a, 2)                                   # garante contornos fechados
    contornos = measure.find_contours(a, 0.5)
    if not contornos:
        raise ValueError("sem contorno")

    h = alpha.shape[0]
    aneis = []
    for c in contornos:
        pts = [(x - 2, h - (y - 2)) for y, x in c]     # (col,lin)→(x, y p/ cima)
        p = Polygon(pts)
        if p.is_valid and p.area > 30:
            aneis.append(p)
    aneis.sort(key=lambda p: p.area, reverse=True)
    exterior = aneis[0]
    furos = [p.exterior.coords for p in aneis[1:]
             if exterior.contains(p.representative_point()) and p.area > exterior.area * 0.002]
    poli = Polygon(exterior.exterior.coords, furos).buffer(0)
    if poli.geom_type == 'MultiPolygon':
        poli = max(poli.geoms, key=lambda g: g.area)
    return poli.simplify(SIMPLIFICA)


def montar_standee(rgbF, aF, rgbB_alinhado, destino):
    h_px, w_px = aF.shape
    poli = poligono_da_silhueta(aF)
    esp = ESPESSURA * h_px

    placa = trimesh.creation.extrude_polygon(poli, esp)   # extrusão em +Z
    placa.apply_translation([0, 0, -esp / 2])             # centra a espessura

    fn = placa.face_normals
    eh_frente = fn[:, 2] > 0.5
    eh_costas = fn[:, 2] < -0.5
    eh_lado = ~(eh_frente | eh_costas)

    texF = _textura(rgbF, aF)
    texB = _textura(rgbB_alinhado, aF)

    cena = trimesh.Scene()
    for nome, sel, tex in (('frente', eh_frente, texF),
                           ('costas', eh_costas, texB)):
        sub = trimesh.Trimesh(vertices=placa.vertices, faces=placa.faces[sel], process=False)
        sub.remove_unreferenced_vertices()
        uv = np.stack([sub.vertices[:, 0] / w_px,
                       sub.vertices[:, 1] / h_px], axis=1)
        mat = trimesh.visual.material.PBRMaterial(
            baseColorTexture=tex, metallicFactor=0.05, roughnessFactor=0.55,
            alphaMode='OPAQUE', doubleSided=False)
        sub.visual = trimesh.visual.TextureVisuals(uv=np.clip(uv, 0, 1), material=mat)
        cena.add_geometry(sub, geom_name=nome)

    lado = trimesh.Trimesh(vertices=placa.vertices, faces=placa.faces[eh_lado], process=False)
    lado.remove_unreferenced_vertices()
    lado.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=COR_BORDA, metallicFactor=0.1, roughnessFactor=0.45,
            alphaMode='OPAQUE', doubleSided=False))
    cena.add_geometry(lado, geom_name='borda')

    # normaliza: altura 1, pés em y=0, centrado em x/z
    caixa = placa.bounds
    escala = 1.0 / (caixa[1][1] - caixa[0][1])
    for g in cena.geometry.values():
        g.apply_translation([-(caixa[0][0] + caixa[1][0]) / 2, -caixa[0][1], 0])
        g.apply_scale(escala)

    cena.export(destino)
    tris = sum(len(g.faces) for g in cena.geometry.values())
    print(f"  ✓ {destino.name} ({destino.stat().st_size // 1024} KB, {tris} tris, "
          f"espessura {ESPESSURA:.0%} da altura)")


# ── Pipeline ───────────────────────────────────────────────────────────────────

def vista_limpa(frame):
    rgb, alpha = G.recortar(frame)
    t, f, c = G.medir_estatua(alpha)
    return rgb, G.cortar_em(alpha, c + int(0.015 * max(f - t, 1)))


def processar(caminho):
    classe = G.classe_do_arquivo(caminho.stem)
    if classe is None:
        return
    print(f"[{classe}] ← {caminho.name}")

    if caminho.is_dir():
        quadros = G.quadros_de_pasta(caminho)
    else:
        layout = G.VISTAS.get(caminho.stem.lower())
        if layout is None:
            print("  ✗ ficha sem layout — pulando")
            return
        quadros = G.fatiar(Image.open(caminho), layout)

    if 'front' not in quadros or 'back' not in quadros:
        print("  ✗ precisa de frente e costas")
        return

    rgbF, aF = vista_limpa(quadros['front'])
    rgbB, aB = vista_limpa(quadros['back'])

    # recorte pela caixa da frente (margem pequena)
    ys, xs = np.where(aF > 0.5)
    m = 6
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, aF.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, aF.shape[1])
    rgbF, aF = rgbF[y0:y1, x0:x1], aF[y0:y1, x0:x1]

    rgbB_alinhado = alinhar_verso(rgbB, aB, aF)
    montar_standee(rgbF, aF, rgbB_alinhado, SAIDA / f"{classe}.glb")


def main():
    SAIDA.mkdir(exist_ok=True)
    alvo = sys.argv[1].lower() if len(sys.argv) > 1 else None
    for f in sorted(G.FONTES.iterdir()):
        if not f.is_dir() and f.suffix.lower() not in G.EXTS:
            continue
        if alvo and alvo not in f.stem.lower():
            continue
        if not f.is_dir() and (G.FONTES / f.stem).is_dir():
            continue
        try:
            processar(f)
        except Exception as e:
            print(f"  ✗ ERRO em {f.name}: {e}")


if __name__ == '__main__':
    main()
