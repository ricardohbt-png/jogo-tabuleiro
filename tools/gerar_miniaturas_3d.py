#!/usr/bin/env python3
"""
Gera miniaturas 3D (GLB) a partir das fichas multi-vista (10–12 quadros).
============================================================================
Entrada : assets/pawns/_fontes/<Personagem>.jpeg — ficha com vistas rotuladas
          (front, back, left/right side, 3/4s, top view)
Saída   : assets/models3d/<classe>.glb

Técnica (casco visual + projeção direcional):
  1. Fatia a ficha pelos separadores pretos; mapeia cada quadro a uma vista
  2. rembg recorta cada vista; pedestal removido (salto de largura)
  3. Normaliza: pés em y=0, altura=1, centro pelo centroide
  4. Esculpe um grid de voxels com as silhuetas de até 8 ângulos
     (frente 0°, costas 180°, perfis ±90°, 3/4 ±45°/±135°)
  5. Marching cubes → malha; suaviza; maior componente
  6. Cada face é texturizada com a foto do ângulo que melhor a vê
     (frente/costas/perfis/topo) — projeção planar registrada com o carve
"""

import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from rembg import new_session, remove
from scipy.ndimage import (
    binary_dilation, binary_fill_holes, distance_transform_edt,
    gaussian_filter, gaussian_filter1d, label,
)
from skimage.measure import marching_cubes

BASE   = Path(r"C:\Users\RICARDO\Desktop\jogo tabuleiro")
FONTES = BASE / "assets" / "pawns" / "_fontes"
SAIDA  = BASE / "assets" / "models3d"

RES_Y     = 200       # voxels no eixo vertical
TOL_SIL   = 0.012     # dilatação das silhuetas antes do carve (fração da altura)
SUAVIZA   = 1.15      # sigma do gaussiano no volume antes do marching cubes
PREF_FB   = 1.32      # preferência por frente/costas na atribuição de textura
CONSIST   = 0.86      # vista só esculpe se mantiver ≥ esta fração do volume

CLASSES = {
    'bard':  ['bard', 'henrique'],
    'cleric': ['cler', 'lewis'],
    'warrior': ['guerr', 'anao', 'warrior', 'viktor', 'victor'],
    'mage':  ['mago', 'mage', 'pedro'],
    'paladin': ['palad', 'richard'],
    'rogue': ['ladin', 'rogue', 'ladr', 'luccas'],
}

# Ordem dos quadros (linha a linha) por ficha — layouts variam entre personagens.
# Nomes: hero, front, back, sideL, sideR, f34L, f34R, b34L, b34R, top
VISTAS = {
    'richard':  [['hero', 'b34R'],
                 ['front', 'back', 'sideL', 'sideR'],
                 ['f34L', 'f34R', 'b34L', 'top']],
    'viktor':   [['hero'],
                 ['front', 'back', 'sideL', 'sideR', 'b34R'],
                 ['f34L', 'f34R', 'b34L', 'top']],
    'pedro':    [['hero', 'b34R'],
                 ['front', 'back', 'sideL', 'sideR', 'b34L'],
                 ['f34L', 'f34R', 'b34L2', 'b34R2', 'top']],
    'luccas':   [['hero', 'b34R'],
                 ['front', 'back', 'sideL', 'sideR', 'b34L'],
                 ['f34L', 'f34R', 'b34L2', 'b34R2', 'top']],
    'lewis':    [['hero', 'b34R'],
                 ['front', 'back', 'sideL', 'sideR', 'b34L'],
                 ['f34L', 'f34R', 'b34L2', 'b34R2', 'top']],
    'henrique': [['hero', 'b34R'],
                 ['front', 'back', 'sideL', 'sideR', 'b34L'],
                 ['f34L', 'f34R', 'b34L2', 'b34R2', 'top']],
}

# Azimute da câmera por vista (0 = frente/+Z; positivo = lado esquerdo do boneco/+X)
AZIMUTE = {
    'front': 0.0, 'back': 180.0, 'sideL': 90.0, 'sideR': -90.0,
    'f34L': 45.0, 'f34R': -45.0, 'b34L': 135.0, 'b34R': -135.0,
    'b34L2': 135.0, 'b34R2': -135.0,
}
VISTAS_CARVE  = ['front', 'back', 'sideL', 'sideR', 'f34L', 'f34R', 'b34L', 'b34R']
VISTAS_TEXTURA = ['front', 'back', 'sideL', 'sideR']   # + top (tratado à parte)

_SESSAO = new_session('isnet-general-use')

EXTS = ('.png', '.jpg', '.jpeg', '.webp')

# ── Modo pasta: um arquivo POR VISTA em alta resolução (preferido) ─────────────
# _fontes/<Personagem>/frente.png, costas.png, esquerda.png, direita.png,
# frente_esquerda.png, frente_direita.png, costas_esquerda.png,
# costas_direita.png, topo.png — nomes em pt ou en; diagonais são opcionais.
VISTA_ARQUIVO = [
    ('f34L',  ('frente_esq', 'front_left', 'f34l')),
    ('f34R',  ('frente_dir', 'front_right', 'f34r')),
    ('b34L',  ('costas_esq', 'back_left', 'b34l', 'tras_esq')),
    ('b34R',  ('costas_dir', 'back_right', 'b34r', 'tras_dir')),
    ('sideL', ('esquerd', 'left', 'sidel')),
    ('sideR', ('direit', 'right', 'sider')),
    ('front', ('frente', 'front')),
    ('back',  ('costas', 'back', 'tras')),
    ('top',   ('topo', 'top', 'cima')),
]


def _sem_acentos(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(c))


def quadros_de_pasta(pasta):
    """Carrega vistas de arquivos separados (alta resolução)."""
    quadros = {}
    for arq in sorted(pasta.iterdir()):
        if arq.suffix.lower() not in EXTS:
            continue
        nome = _sem_acentos(arq.stem.lower()).replace('-', '_').replace(' ', '_')
        for vista, chaves in VISTA_ARQUIVO:
            if vista not in quadros and any(k in nome for k in chaves):
                quadros[vista] = Image.open(arq).convert('RGB')
                break
    return quadros


def classe_do_arquivo(nome):
    n = nome.lower()
    for classe, chaves in CLASSES.items():
        if any(k in n for k in chaves):
            return classe
    return None


# ── Fatiamento da ficha ────────────────────────────────────────────────────────

def _bandas(escuro_1d, tam_min):
    """Segmentos não-escuros de um perfil booleano de separadores."""
    bandas, ini = [], None
    for i, e in enumerate(escuro_1d):
        if not e and ini is None:
            ini = i
        elif e and ini is not None:
            if i - ini >= tam_min:
                bandas.append((ini, i))
            ini = None
    if ini is not None and len(escuro_1d) - ini >= tam_min:
        bandas.append((ini, len(escuro_1d)))
    return bandas


def _ima(candidatos, alvo, tol):
    """Separador: linha escura candidata mais próxima do esperado, senão o esperado."""
    if len(candidatos):
        i = int(np.argmin(np.abs(candidatos - alvo)))
        if abs(candidatos[i] - alvo) <= tol:
            return int(candidatos[i])
    return int(alvo)


# frações verticais esperadas das divisões entre linhas (linha 1 é mais alta)
_FRACS_LINHAS = [0.45, 0.72]


def fatiar(img, layout):
    """Divide a ficha: grade esperada + ímã para a linha escura mais próxima."""
    g = np.asarray(img.convert('L'), dtype=np.float64)
    h, w = g.shape

    cand_lin = np.where((g < 30).mean(axis=1) > 0.88)[0]
    cand_lin = cand_lin[(cand_lin > h * 0.10) & (cand_lin < h * 0.95)]
    div = [_ima(cand_lin, h * f, h * 0.07) for f in _FRACS_LINHAS]
    limites = [0] + div + [h]

    quadros = {}
    for (y0, y1), nomes in zip(zip(limites[:-1], limites[1:]), layout):
        n = len(nomes)
        gl = g[y0:y1]
        cand_col = np.where((gl < 30).mean(axis=0) > 0.88)[0]
        cand_col = cand_col[(cand_col > w * 0.04) & (cand_col < w * 0.96)]
        xs = [0] + [_ima(cand_col, w * i / n, w * 0.05) for i in range(1, n)] + [w]
        for i, nome in enumerate(nomes):
            quadros[nome] = img.crop((xs[i], y0, xs[i + 1], y1)).convert('RGB')
    return quadros


# ── Recorte e normalização por vista ───────────────────────────────────────────

def recortar(frame):
    rgb = np.asarray(frame, dtype=np.float64)
    mask = remove(frame, session=_SESSAO, only_mask=True)
    alpha = np.asarray(mask, dtype=np.float64) / 255.0
    fig = binary_fill_holes(alpha > 0.5)
    rot, n = label(fig)
    if n > 1:
        tam = np.bincount(rot.ravel()); tam[0] = 0
        fig = rot == tam.argmax()
    return rgb, np.where(fig, 1.0, 0.0)


def medir_estatua(alpha):
    """(topo, fundo, corte) da estátua: corte = topo do pedestal (salto de largura)."""
    solido = alpha > 0.5
    h, _ = solido.shape
    ys, _ = np.where(solido)
    topo, fundo = int(ys.min()), int(ys.max())
    larg = gaussian_filter1d(solido.sum(axis=1).astype(np.float64), max(2, h // 150))
    y0 = topo + int((fundo - topo) * 0.55)
    y1 = topo + int((fundo - topo) * 0.96)
    corte = y0 + int(np.argmax(np.diff(larg)[y0:y1]))
    return topo, fundo, corte


def cortar_em(alpha, corte):
    """Remove tudo abaixo de `corte` e mantém o maior componente."""
    out = alpha.copy()
    out[min(corte, alpha.shape[0] - 1):, :] = 0.0
    fig = binary_fill_holes(out > 0.5)
    rot, n = label(fig)
    if n > 1:
        tam = np.bincount(rot.ravel()); tam[0] = 0
        out = np.where(rot == tam.argmax(), out, 0.0)
    return out


class Vista:
    """Silhueta + foto de uma vista, com registro mundo↔pixel.
    Mundo: pés y=0, altura=1; eixo-u da imagem = x·cos(a) − z·sin(a)."""

    def __init__(self, nome, rgb, alpha):
        self.nome = nome
        self.az = np.deg2rad(AZIMUTE[nome])
        self.alpha = alpha
        ys, xs = np.where(alpha > 0.5)
        self.h_px = ys.max() - ys.min() + 1          # altura da figura em px
        self.y_pes = ys.max()                         # linha dos pés
        self.cx = xs.mean()                           # centroide horizontal
        # foto com fundo preenchido pela cor sólida mais próxima e BORRADO
        # (sem listras quando a malha amostra um pouco fora da silhueta)
        _, (iy, ix) = distance_transform_edt(alpha < 0.5, return_indices=True)
        cheio = rgb[iy, ix]
        fora_borrado = gaussian_filter(cheio, sigma=(7, 7, 0))
        dentro = (alpha > 0.5)[..., None]
        self.rgb = np.where(dentro, rgb, fora_borrado)

    def px(self, u, y):
        """coords mundo (u ao longo do eixo da imagem, y altura) → px (col, lin)"""
        return self.cx + u * self.h_px, self.y_pes - y * self.h_px

    def sil_dilatada(self):
        r = max(2, int(TOL_SIL * self.h_px))
        return binary_dilation(self.alpha > 0.5, iterations=r)


# ── Carve + malha ──────────────────────────────────────────────────────────────

def esculpir(vistas):
    # extensão XZ: meia-largura máxima entre as vistas + margem
    metade = 0.30
    for v in vistas.values():
        xs = np.where((v.alpha > 0.5).any(axis=0))[0]
        metade = max(metade, (xs.max() - xs.min() + 1) / v.h_px / 2)
    metade = min(metade * 1.06, 0.62)

    ny = RES_Y
    nxz = int(2 * metade * ny / 1.04)
    ys = np.linspace(-0.015, 1.025, ny)
    xs = np.linspace(-metade, metade, nxz)
    zs = np.linspace(-metade, metade, nxz)

    vol = np.ones((ny, nxz, nxz), dtype=bool)
    X, Z = np.meshgrid(xs, zs, indexing='ij')          # (nx, nz)

    def mascara(v):
        sil = v.sil_dilatada()
        hh, ww = sil.shape
        U = X * np.cos(v.az) - Z * np.sin(v.az)
        pu, _ = v.px(U, 0.0)
        pu = np.clip(np.round(pu).astype(np.int64), 0, ww - 1)
        _, pv = v.px(0.0, ys)
        pv = np.clip(np.round(pv).astype(np.int64), 0, hh - 1)
        return sil[pv[:, None, None], pu[None, :, :]]

    for n in ('front', 'back', 'sideL', 'sideR'):
        if n in vistas:
            vol &= mascara(vistas[n])

    # Diagonais: cada uma só esculpe se concordar com o casco das 4 principais
    for n in ('f34L', 'f34R', 'b34L', 'b34R', 'b34L2', 'b34R2'):
        if n not in vistas:
            continue
        m = mascara(vistas[n])
        mantem = (vol & m).sum() / max(vol.sum(), 1)
        if mantem >= CONSIST:
            vol &= m
        else:
            print(f"    ({n} inconsistente — removeria {(1-mantem)*100:.0f}% do volume; ignorada)")

    # maior componente + fechamento de cavidades
    rot, n = label(vol)
    if n > 1:
        tam = np.bincount(rot.ravel()); tam[0] = 0
        vol = rot == tam.argmax()
    vol = binary_fill_holes(vol)

    campo = gaussian_filter(vol.astype(np.float32), sigma=SUAVIZA)
    dy = ys[1] - ys[0]; dx = xs[1] - xs[0]
    verts, faces, _, _ = marching_cubes(campo, 0.5, spacing=(dy, dx, dx))
    # (y, x, z) → (x, y, z), com offsets dos eixos
    verts = verts[:, [1, 0, 2]]
    verts[:, 0] += xs[0]; verts[:, 1] += ys[0]; verts[:, 2] += zs[0]
    return verts, faces


# ── Texturização por projeção direcional ───────────────────────────────────────

def _uv_da_vista(v, verts):
    u = verts[:, 0] * np.cos(v.az) - verts[:, 2] * np.sin(v.az)
    pu, pv = v.px(u, verts[:, 1])
    hh, ww = v.alpha.shape
    return np.stack([pu / (ww - 1), 1.0 - pv / (hh - 1)], axis=1)


def _textura(v, lado_alvo=1024):
    img = Image.fromarray(np.clip(v.rgb, 0, 255).astype(np.uint8), 'RGB')
    f = lado_alvo / max(img.size)
    if f < 1.0 or max(img.size) < 768:    # downscale fotos grandes; upscale quadros pequenos
        f = min(f, lado_alvo / max(img.size)) if f < 1.0 else 768 / max(img.size)
        img = img.resize((max(int(img.width * f), 8), max(int(img.height * f), 8)), Image.LANCZOS)
    return img


def registrar_topo(frame_top, vista_front):
    """Topo: registra escala/centro pelo pedestal (círculo na vista de cima)."""
    rgb = np.asarray(frame_top.convert('RGB'), dtype=np.float64)
    mask = remove(frame_top, session=_SESSAO, only_mask=True)
    alpha = np.asarray(mask, dtype=np.float64) / 255.0
    ys, xs = np.where(alpha > 0.5)
    if len(xs) < 50:
        return None
    diam_px = xs.max() - xs.min() + 1
    # diâmetro do pedestal em unidades-mundo: largura inferior da silhueta
    # ORIGINAL da frente (antes da remoção) ≈ topo do quadro frontal sem corte
    a0 = vista_front._alpha_original
    h0 = vista_front.h_px_original
    fundo = a0[int(a0.shape[0] * 0.90):, :]
    cols = np.where((fundo > 0.5).any(axis=0))[0]
    diam_mundo = (cols.max() - cols.min() + 1) / h0 if len(cols) else 0.45
    esc = diam_px / max(diam_mundo, 1e-3)              # px por unidade-mundo
    _, (iy, ix) = distance_transform_edt(alpha < 0.5, return_indices=True)
    return {
        'rgb': rgb[iy, ix], 'esc': esc,
        'cx': xs.mean(), 'cy': ys.mean(),
        'shape': alpha.shape,
    }


def _uv_topo(reg, verts):
    pu = reg['cx'] + verts[:, 0] * reg['esc']
    pv = reg['cy'] + verts[:, 2] * reg['esc']
    hh, ww = reg['shape']
    return np.stack([pu / (ww - 1), 1.0 - pv / (hh - 1)], axis=1)


ALVO_TRIS = 60000     # triângulos por peça após decimação


def montar_glb(verts, faces, vistas, reg_topo, destino):
    malha = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    malha.fix_normals()

    # remove fragmentos soltos (slivers da tolerância do carve)
    partes = malha.split(only_watertight=False)
    if len(partes) > 1:
        limite = 0.03 * sum(len(p.faces) for p in partes)
        grandes = [p for p in partes if len(p.faces) >= limite]
        malha = trimesh.util.concatenate(grandes) if grandes else malha

    # decimação (mantém a forma, corta ~2/3 dos triângulos)
    if len(malha.faces) > ALVO_TRIS:
        import fast_simplification
        v2, f2 = fast_simplification.simplify(
            malha.vertices.astype(np.float32), malha.faces.astype(np.int64),
            target_count=ALVO_TRIS)
        malha = trimesh.Trimesh(vertices=v2, faces=f2, process=True)
        malha.fix_normals()
    fn = malha.face_normals
    fv = malha.faces

    # pontuação por vista: frente nz, costas −nz, ladoL nx, ladoR −nx, topo ny
    pesos = {
        'front': fn[:, 2] * PREF_FB,
        'back': -fn[:, 2] * PREF_FB,
        'sideL': fn[:, 0],
        'sideR': -fn[:, 0],
    }
    if reg_topo is not None:
        pesos['top'] = fn[:, 1] * 0.95
    nomes = list(pesos.keys())
    score = np.stack([pesos[n] for n in nomes], axis=1)
    escolha = np.argmax(score, axis=1)

    cena = trimesh.Scene()
    for i, nome in enumerate(nomes):
        sel = escolha == i
        if not sel.any():
            continue
        sub = trimesh.Trimesh(vertices=malha.vertices, faces=fv[sel], process=False)
        sub.remove_unreferenced_vertices()
        if nome == 'top':
            uv = _uv_topo(reg_topo, sub.vertices)
            img = Image.fromarray(np.clip(reg_topo['rgb'], 0, 255).astype(np.uint8), 'RGB')
        else:
            v = vistas[nome]
            uv = _uv_da_vista(v, sub.vertices)
            img = _textura(v)
        mat = trimesh.visual.material.PBRMaterial(
            baseColorTexture=img, metallicFactor=0.04,
            roughnessFactor=0.58, alphaMode='OPAQUE', doubleSided=False)
        sub.visual = trimesh.visual.TextureVisuals(uv=np.clip(uv, 0, 1), material=mat)
        cena.add_geometry(sub, node_name=nome, geom_name=nome)

    cena.export(destino)
    bbox = verts.max(axis=0) - verts.min(axis=0)
    print(f"  ✓ {destino.name} ({destino.stat().st_size // 1024} KB, "
          f"{len(fv)} tris, bbox {bbox[0]:.2f}×{bbox[1]:.2f}×{bbox[2]:.2f})")


# ── Pipeline ───────────────────────────────────────────────────────────────────

def processar(caminho):
    classe = classe_do_arquivo(caminho.stem)
    if classe is None:
        print(f"  ✗ {caminho.name}: classe não reconhecida — pulando")
        return
    print(f"[{classe}] ← {caminho.name}")

    if caminho.is_dir():
        # modo preferido: um arquivo por vista, alta resolução
        quadros = quadros_de_pasta(caminho)
        if not quadros:
            print("  ✗ pasta sem vistas reconhecidas")
            return
        # sem diagonais o casco fica estufado nos cantos (45°): se existir a
        # ficha antiga homônima, empresta as diagonais dela SÓ para esculpir —
        # o filtro de consistência descarta se a pose divergir
        faltam_diag = [n for n in ('f34L', 'f34R', 'b34L', 'b34R') if n not in quadros]
        ficha = next((p for ext in EXTS if (p := FONTES / f"{caminho.name}{ext}").exists()), None)
        if faltam_diag and ficha and ficha.stem.lower() in VISTAS:
            try:
                da_ficha = fatiar(Image.open(ficha), VISTAS[ficha.stem.lower()])
                for n in faltam_diag:
                    if n in da_ficha:
                        quadros[n] = da_ficha[n]
                print(f"    (diagonais emprestadas da ficha: {[n for n in faltam_diag if n in quadros]})")
            except Exception as e:
                print(f"    (ficha antiga ilegível: {e})")
        print(f"    vistas: {sorted(quadros)}")
    else:
        layout = VISTAS.get(caminho.stem.lower())
        if layout is None:
            print(f"  ✗ {caminho.name}: ficha sem layout mapeado — pulando")
            return
        quadros = fatiar(Image.open(caminho), layout)

    # 1) recorta todas as vistas de carve (com pedestal ainda)
    brutas = {}
    for nome in VISTAS_CARVE:
        if nome in quadros:
            try:
                brutas[nome] = recortar(quadros[nome])
            except Exception as e:
                print(f"    ({nome}: {e} — vista ignorada)")
    faltam = [n for n in VISTAS_TEXTURA if n not in brutas]
    if faltam:
        print(f"  ✗ vistas essenciais ausentes: {faltam}")
        return

    # 2) corte do pedestal na MESMA fração de altura em todas as vistas
    #    (mediana das detecções — alinha verticalmente o registro do carve)
    medidas = {n: medir_estatua(a) for n, (_, a) in brutas.items()}
    fracs = [(f - c) / max(f - t, 1) for (t, f, c) in medidas.values()]
    fmed = float(np.median(fracs))

    vistas = {}
    for nome, (rgb, alpha) in brutas.items():
        try:
            t, f, _ = medidas[nome]
            corte = int(f - fmed * (f - t)) + int(0.015 * (f - t))
            vistas[nome] = Vista(nome, rgb, cortar_em(alpha, corte))
        except Exception as e:
            print(f"    ({nome}: {e} — vista ignorada)")

    # guarda dados pré-remoção do pedestal p/ registrar o topo
    vf = vistas['front']
    a0 = brutas['front'][1]
    vf._alpha_original = a0
    ys0, _ = np.where(a0 > 0.5)
    vf.h_px_original = ys0.max() - ys0.min() + 1

    reg_topo = None
    if 'top' in quadros:
        try:
            reg_topo = registrar_topo(quadros['top'], vf)
        except Exception as e:
            print(f"    (topo ignorado: {e})")

    verts, faces = esculpir(vistas)
    montar_glb(verts, faces, vistas, reg_topo, SAIDA / f"{classe}.glb")


def main():
    SAIDA.mkdir(exist_ok=True)
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    for f in sorted(FONTES.iterdir()):
        # pastas (1 arquivo/vista) têm prioridade sobre a ficha única homônima
        if not f.is_dir() and f.suffix.lower() not in EXTS:
            continue
        if alvo and alvo.lower() not in f.stem.lower():
            continue
        if not f.is_dir() and (FONTES / f.stem).is_dir():
            continue   # já será processado pela pasta
        try:
            processar(f)
        except Exception as e:
            print(f"  ✗ ERRO em {f.name}: {e}")


if __name__ == '__main__':
    main()
