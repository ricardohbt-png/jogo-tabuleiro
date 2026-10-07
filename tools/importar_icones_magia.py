"""Importa ícones de magia gerados para assets/magias/<id>.png (256x256).

Uso (da raiz):  python tools/importar_icones_magia.py <pasta> [--substituir]

Cada arquivo da pasta deve ter o id da magia como nome (voo.png, teleporte.jpg,
metamorfose.webp...). O script recorta o quadrado central, reduz para 256x256
no mesmo formato dos ícones existentes (RGB) e lista o que ainda falta. Ícone que
já existe só é trocado com --substituir. Prompts: docs/icones-magias-prompts.md
"""
import contextlib
import io
import os
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "assets", "magias")
LADO = 256
EXTENSOES = (".png", ".jpg", ".jpeg", ".webp")


def ids_do_grimorio():
    sys.path.insert(0, RAIZ)
    with contextlib.redirect_stdout(io.StringIO()):
        import server
    return set(server.GRIMORIO)


def preparar(origem):
    """Quadrado central, 256x256, RGB (transparência vira preto, como o fundo)."""
    im = Image.open(origem)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fundo = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(fundo, im)
    im = im.convert("RGB")
    w, h = im.size
    lado = min(w, h)
    x, y = (w - lado) // 2, (h - lado) // 2
    im = im.crop((x, y, x + lado, y + lado))
    return im.resize((LADO, LADO), Image.LANCZOS)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    pasta = argv[0]
    substituir = "--substituir" in argv
    if not os.path.isdir(pasta):
        print(f"Pasta não encontrada: {pasta}")
        return 1
    ids = ids_do_grimorio()
    importados, pulados, desconhecidos = [], [], []
    for nome in sorted(os.listdir(pasta)):
        base, ext = os.path.splitext(nome)
        if ext.lower() not in EXTENSOES:
            continue
        if base not in ids:
            desconhecidos.append(nome)
            continue
        alvo = os.path.join(DESTINO, base + ".png")
        if os.path.exists(alvo) and not substituir:
            pulados.append(base)
            continue
        preparar(os.path.join(pasta, nome)).save(alvo, optimize=True)
        importados.append(base)
    faltam = sorted(i for i in ids if not os.path.exists(os.path.join(DESTINO, i + ".png")))
    print(f"Importados ({len(importados)}): {', '.join(importados) or '-'}")
    if pulados:
        print(f"Já existiam, mantidos ({len(pulados)}): {', '.join(pulados)}  (use --substituir)")
    if desconhecidos:
        print(f"Nome não é id de magia ({len(desconhecidos)}): {', '.join(desconhecidos)}")
    print(f"Ainda faltam ({len(faltam)}): {', '.join(faltam) or 'nenhum'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
