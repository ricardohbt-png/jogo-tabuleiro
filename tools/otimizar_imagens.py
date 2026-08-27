# -*- coding: utf-8 -*-
r"""
Reamostra a arte de interface para o tamanho em que ela e REALMENTE exibida.

POR QUE (medido em 2026-08-25):
o jogo guardava icones de 1254x1254 que aparecem a 16x16 na tela. Cada um
custava ~2,6 MB de download E ~6 MB de bitmap decodificado na memoria -- o
navegador decodifica no tamanho natural, nao no tamanho exibido. Uma entrada
de masmorra baixava ~40 MB, e cada icone novo que aparecia durante a partida
provocava uma engasgada no quadro (decode de PNG roda na thread principal).

    assets/habilidades: 123,7 MB -> 6,5 MB  (icone exibido a 16-36 px)
    assets/itens:       157,5 MB -> 24,3 MB (item exibido a 55x85)
    assets/armadilhas:  123,8 MB -> 33,1 MB (popup ~310 px)
    TOTAL das imagens:  636 MB -> 186 MB

O alvo de cada pasta guarda 7-16x de folga sobre o tamanho de exibicao, entao
nao ha perda visivel nem em tela retina. Arte de TELA CHEIA (cenas, cidade,
historia, taverna, transicao) fica INTACTA -- essa precisa da resolucao.

SEGURANCA: o original de todo arquivo tocado e copiado para assets_originais/
(mesma estrutura de pastas) ANTES da primeira gravacao. Nada e sobrescrito sem
copia. Rodar de novo e inofensivo: arquivo ja dentro do alvo e pulado.

Uso, da raiz:
    python tools/otimizar_imagens.py --dry-run     # so relata
    python tools/otimizar_imagens.py               # aplica
    python tools/otimizar_imagens.py --restaurar   # desfaz tudo
"""
import argparse
import io
import os
import shutil
import sys

try:
    from PIL import Image
except ImportError:
    print("Falta Pillow.  Instale com:  python -m pip install Pillow")
    sys.exit(1)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(RAIZ, "assets_originais")

# pasta -> (maior lado permitido, para que serve)
# O alvo vem do tamanho de exibicao REAL, conferido no DOM e no CSS.
POLITICA = {
    "assets/habilidades":   (256,  "icone de habilidade, exibido a 16-36 px"),
    "assets/magias":        (256,  "icone de magia"),
    "assets/itens":         (512,  "item na bolsa/loja, exibido a 55x85"),
    "assets/itens magicos": (512,  "item magico"),
    "assets/armadilhas":    (640,  "arte do popup de armadilha, ~310 px"),
    "assets/objetos":       (512,  "textura de decoracao 3D / emoji 2D"),
    "assets/pawns":         (512,  "peao 2D no tabuleiro"),
    "assets/retratos":      (1024, "retrato do Bestiario -- quadro grande"),
    "assets/textures":      (1024, "textura da mesa"),
}
# FORA da politica, de proposito:
#   assets/portraits  -- e a TELA DE SELECAO: selecao_personagens.jpg e o fundo
#                        de tela cheia e os retratos vao num quadro de ate
#                        340 px de altura (680 px em tela retina). A pasta
#                        inteira tem 0,9 MB: reduzir nao economiza nada e a
#                        perda aparece na hora. Ja foi reduzida uma vez por
#                        engano e teve de ser restaurada.
#   assets/cenas, city, story, tavern, cenarios, "tela de transicao", dicas
#                     -- arte de tela cheia.
# Pastas deliberadamente FORA: arte de tela cheia precisa da resolucao.
#   assets/cenas, assets/city, assets/story, assets/tavern, assets/cenarios,
#   assets/tela de transição, assets/dicas
EXT = (".png", ".jpg", ".jpeg", ".webp")


def humano(n):
    return "%.1f MB" % (n / 1048576.0) if n >= 1048576 else "%.0f KB" % (n / 1024.0)


def reamostrar(caminho, alvo):
    """Devolve os bytes reamostrados, ou None se nao vale a pena mexer."""
    try:
        im = Image.open(caminho)
        im.load()
    except Exception:
        return None
    if max(im.size) <= alvo:
        return None                      # ja esta dentro do alvo
    im.thumbnail((alvo, alvo), Image.LANCZOS)
    buf = io.BytesIO()
    ext = os.path.splitext(caminho)[1].lower()
    if ext in (".jpg", ".jpeg"):
        im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    else:
        # Preserva transparencia: quase todo icone do jogo tem alfa.
        if im.mode == "P":
            im = im.convert("RGBA")
        elif im.mode not in ("RGBA", "RGB", "LA", "L"):
            im = im.convert("RGBA")
        im.save(buf, "PNG", optimize=True)
    dados = buf.getvalue()
    # Se o "otimizado" ficou maior (acontece em imagem ja minuscula), desiste.
    return dados if len(dados) < os.path.getsize(caminho) else None


def restaurar():
    if not os.path.isdir(BACKUP):
        print("Nao ha assets_originais/ -- nada para restaurar.")
        return 0
    n = 0
    for base, _dirs, arqs in os.walk(BACKUP):
        for a in arqs:
            org = os.path.join(base, a)
            rel = os.path.relpath(org, BACKUP)
            dst = os.path.join(RAIZ, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(org, dst)
            n += 1
    print("Restaurados %d arquivos de assets_originais/." % n)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="so relata, nao grava")
    ap.add_argument("--restaurar", action="store_true", help="desfaz usando assets_originais/")
    args = ap.parse_args()

    if args.restaurar:
        restaurar()
        return

    total_antes = total_depois = 0
    tocados = pulados = 0
    print("%-24s %5s %5s %11s %11s %7s" % ("pasta", "alvo", "arq", "antes", "depois", "corte"))
    for rel_dir, (alvo, uso) in POLITICA.items():
        d = os.path.join(RAIZ, rel_dir)
        if not os.path.isdir(d):
            continue
        p_antes = p_depois = 0
        p_n = 0
        for base, _dirs, arqs in os.walk(d):
            for a in sorted(arqs):
                if os.path.splitext(a)[1].lower() not in EXT:
                    continue
                caminho = os.path.join(base, a)
                tam = os.path.getsize(caminho)
                p_antes += tam
                p_n += 1
                novo = reamostrar(caminho, alvo)
                if novo is None:
                    p_depois += tam
                    pulados += 1
                    continue
                p_depois += len(novo)
                tocados += 1
                if args.dry_run:
                    continue
                # copia de seguranca antes de qualquer gravacao
                rel = os.path.relpath(caminho, RAIZ)
                bkp = os.path.join(BACKUP, rel)
                if not os.path.exists(bkp):
                    os.makedirs(os.path.dirname(bkp), exist_ok=True)
                    shutil.copy2(caminho, bkp)
                with open(caminho, "wb") as f:
                    f.write(novo)
        if not p_n:
            continue
        total_antes += p_antes
        total_depois += p_depois
        corte = 100.0 * (1 - p_depois / p_antes) if p_antes else 0.0
        print("%-24s %5d %5d %11s %11s %6.1f%%  %s"
              % (rel_dir, alvo, p_n, humano(p_antes), humano(p_depois), corte, uso))

    print("")
    if total_antes:
        print("TOTAL: %s -> %s   (corte de %.0f%%, economia de %s)"
              % (humano(total_antes), humano(total_depois),
                 100.0 * (1 - total_depois / total_antes), humano(total_antes - total_depois)))
    print("Arquivos reamostrados: %d   |   ja dentro do alvo (pulados): %d" % (tocados, pulados))
    if args.dry_run:
        print("\n--dry-run: nada foi gravado.")
    else:
        print("\nOriginais em assets_originais/  (desfaz com --restaurar)")


if __name__ == "__main__":
    main()
