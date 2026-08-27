# -*- coding: utf-8 -*-
r"""
Reduz a TEXTURA EMBUTIDA dos .glb. Nao toca na geometria.

POR QUE SO A TEXTURA (medido em 2026-08-25):
os modelos repintados tem 40.000 triangulos com 120.000 vertices -- 3 por
triangulo -- e isso PARECE malha nao soldada, com 6x de gordura. Nao e:

    kobold.glb  unicos(POSITION+NORMAL+UV) = 119.988 de 119.988  -> ganho 0%
                normais iguais nos 3 vertices do triangulo: 100%

As normais sao POR FACE (flat shading). glTF nao tem atributo por face, entao
cada triangulo precisa mesmo dos seus 3 vertices. Soldar por posicao trocaria
o sombreado facetado por suave -- mudaria a ARTE. Por isso este script nao
solda nada.

O que sobra, e e seguro, e a textura embutida: heroi warrior.glb carrega uma
imagem 2048x2048 (3,73 MB dos 5,21 MB do arquivo) para um peao desenhado com
~100 px de altura no tabuleiro.

SEGURANCA: original copiado para assets_originais/ antes de gravar.
Idempotente: textura ja dentro do alvo e pulada.

Uso, da raiz:
    python tools/otimizar_modelos3d.py --dry-run
    python tools/otimizar_modelos3d.py
    python tools/otimizar_modelos3d.py --restaurar
"""
import argparse
import glob
import io
import json
import os
import shutil
import struct
import sys

try:
    from PIL import Image
except ImportError:
    print("Falta Pillow.  Instale com:  python -m pip install Pillow")
    sys.exit(1)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(RAIZ, "assets_originais")

# Alvo por pasta. models3d = herois e monstros (o que o jogador mais olha, e
# ainda assim desenhado com ~100-200 px); objetos = decoracao de cenario.
# ATENCAO: os herois (assets/models3d/*.glb na RAIZ) ficam de fora. Eles sao
# desenhados em TELA CHEIA no carrossel da tela de selecao, entao a textura de
# 2048 e necessaria -- reduzir para 1024 degradou visivelmente e teve de ser
# restaurado. Os monstros ficam pequenos no tabuleiro e continuam em 1024.
POLITICA = {
    "assets/models3d/monstros": 1024,
    "assets/objetos": 512,
}
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def ler_glb(caminho):
    d = open(caminho, "rb").read()
    if d[:4] != b"glTF":
        return None, None
    off, js, bina = 12, None, None
    while off < len(d):
        ln, ty = struct.unpack_from("<II", d, off)
        ch = d[off + 8:off + 8 + ln]
        if ty == JSON_CHUNK:
            js = json.loads(ch.decode("utf-8"))
        elif ty == BIN_CHUNK:
            bina = bytearray(ch)
        off += 8 + ln
    return js, bina


def escrever_glb(js, bina):
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * ((4 - len(jb) % 4) % 4)            # chunks alinhados em 4
    bb = bytes(bina) + b"\0" * ((4 - len(bina) % 4) % 4)
    total = 12 + 8 + len(jb) + 8 + len(bb)
    out = bytearray()
    out += b"glTF" + struct.pack("<II", 2, total)
    out += struct.pack("<II", len(jb), JSON_CHUNK) + jb
    out += struct.pack("<II", len(bb), BIN_CHUNK) + bb
    return bytes(out)


def reamostrar_glb(caminho, alvo):
    """Devolve os bytes do .glb com as texturas reduzidas, ou None se nada muda."""
    js, bina = ler_glb(caminho)
    if not js or bina is None or not js.get("images"):
        return None
    # bufferView -> nova imagem
    novos = {}
    for im in js["images"]:
        bvi = im.get("bufferView")
        if bvi is None:
            continue
        bv = js["bufferViews"][bvi]
        off, ln = bv.get("byteOffset", 0), bv["byteLength"]
        blob = bytes(bina[off:off + ln])
        try:
            pi = Image.open(io.BytesIO(blob))
            pi.load()
        except Exception:
            continue
        if max(pi.size) <= alvo:
            continue
        pi.thumbnail((alvo, alvo), Image.LANCZOS)
        buf = io.BytesIO()
        if pi.mode in ("RGBA", "LA", "P"):
            pi.convert("RGBA").save(buf, "PNG", optimize=True)
            mime = "image/png"
        else:
            pi.convert("RGB").save(buf, "JPEG", quality=90, optimize=True)
            mime = "image/jpeg"
        dados = buf.getvalue()
        if len(dados) >= ln:
            continue                                # nao encolheu: deixa como esta
        novos[bvi] = (dados, mime)
        im["mimeType"] = mime
    if not novos:
        return None
    # Reconstroi o buffer binario inteiro, remapeando os offsets. Um bufferView
    # pode mudar de tamanho, entao TODOS os offsets seguintes se deslocam --
    # por isso o buffer e remontado do zero, na ordem original.
    ordem = sorted(range(len(js["bufferViews"])),
                   key=lambda i: js["bufferViews"][i].get("byteOffset", 0))
    novo_bin = bytearray()
    for i in ordem:
        bv = js["bufferViews"][i]
        off, ln = bv.get("byteOffset", 0), bv["byteLength"]
        dados = novos[i][0] if i in novos else bytes(bina[off:off + ln])
        while len(novo_bin) % 4:                    # mantem alinhamento
            novo_bin += b"\0"
        bv["byteOffset"] = len(novo_bin)
        bv["byteLength"] = len(dados)
        novo_bin += dados
    js["buffers"][0]["byteLength"] = len(novo_bin)
    js["buffers"][0].pop("uri", None)
    return escrever_glb(js, novo_bin)


def restaurar():
    n = 0
    for base, _d, arqs in os.walk(BACKUP):
        for a in arqs:
            if not a.lower().endswith(".glb"):
                continue
            org = os.path.join(base, a)
            dst = os.path.join(RAIZ, os.path.relpath(org, BACKUP))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(org, dst)
            n += 1
    print("Restaurados %d modelos." % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restaurar", action="store_true")
    args = ap.parse_args()
    if args.restaurar:
        restaurar()
        return

    antes = depois = 0
    tocados = pulados = 0
    for rel_dir, alvo in POLITICA.items():
        d = os.path.join(RAIZ, rel_dir)
        if not os.path.isdir(d):
            continue
        for caminho in sorted(glob.glob(os.path.join(d, "**", "*.glb"), recursive=True)):
            tam = os.path.getsize(caminho)
            antes += tam
            try:
                novo = reamostrar_glb(caminho, alvo)
            except Exception as e:
                print("  !! %s: %s (deixado como estava)" % (os.path.basename(caminho), e))
                depois += tam
                pulados += 1
                continue
            if novo is None or len(novo) >= tam:
                depois += tam
                pulados += 1
                continue
            depois += len(novo)
            tocados += 1
            print("  %-42s %6.2f MB -> %6.2f MB  (-%.0f%%)"
                  % (os.path.relpath(caminho, RAIZ), tam / 1048576.0,
                     len(novo) / 1048576.0, 100 * (1 - len(novo) / tam)))
            if args.dry_run:
                continue
            rel = os.path.relpath(caminho, RAIZ)
            bkp = os.path.join(BACKUP, rel)
            if not os.path.exists(bkp):
                os.makedirs(os.path.dirname(bkp), exist_ok=True)
                shutil.copy2(caminho, bkp)
            with open(caminho, "wb") as f:
                f.write(novo)

    print("\nTOTAL: %.0f MB -> %.0f MB  (economia de %.0f MB)"
          % (antes / 1048576.0, depois / 1048576.0, (antes - depois) / 1048576.0))
    print("Modelos alterados: %d   |   sem ganho / ja no alvo: %d" % (tocados, pulados))
    if args.dry_run:
        print("\n--dry-run: nada foi gravado.")


if __name__ == "__main__":
    main()
