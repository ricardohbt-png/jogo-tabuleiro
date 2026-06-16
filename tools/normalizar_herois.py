# -*- coding: utf-8 -*-
"""
Normaliza as imagens 2D de HEROIS e MONSTROS para uso como billboard no tabuleiro.

Decisoes do usuario (2026-06-13):
  - Recortar SO o personagem/criatura: remover o podio e o banner pintados.
  - Remover a borda branca de adesivo; remover fundo branco quando houver.
  - Padronizar (pes na borda inferior), salvar RGBA. Originais viram *_original.png.

A base de madeira + placa do engine sao mantidas (a figura fica em pe sobre elas),
por isso recortamos com os PES na borda inferior.

Pipeline por item:
  1. Le a fonte (sempre do backup *_original.png, idempotente).
  2. Adesivo (ja tem alpha) -> erode o alpha p/ comer o anel branco.
     Estatua (fundo branco)  -> rembg (isnet-general-use).
  3. Corta o podio pela fracao 'cut' (do bbox do conteudo, medida do TOPO).
  4. Apara justo; folga so em cima/laterais; pes na base; salva.

Fases (heroi | monstro | tudo):
  python tools/normalizar_herois.py seg-her    # reguas dos herois (achar o corte)
  python tools/normalizar_herois.py seg-mon    # reguas dos monstros
  python tools/normalizar_herois.py final-her  # aplica nos herois
  python tools/normalizar_herois.py final-mon  # aplica nos monstros
  python tools/normalizar_herois.py final      # herois + monstros
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from rembg import remove, new_session

RAIZ  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAWNS = os.path.join(RAIZ, 'assets', 'pawns')
TMP   = os.path.join(RAIZ, 'tools', '_norm')
os.makedirs(TMP, exist_ok=True)

MAX_H    = 800      # altura maxima da textura final (sem upscale)
PAD_TOP  = 0.025    # folga acima da cabeca (fracao da altura do conteudo)
PAD_SIDE = 0.025    # folga lateral (fracao da largura do conteudo)
ERODE_PX = 3        # erosao leve do alpha (so a franja serrilhada; o miolo branco
                    # sai na remocao de quase-branco). 3px preserva lancas/caudas finas.

# Fonte de cada heroi (warrior veio com erro de digitacao no nome do arquivo).
FONTE_HER = {'warrior': 'frrent.png', 'mage': 'frente.png', 'rogue': 'frente.png',
             'cleric': 'frente.png', 'bard': 'frente.png', 'paladin': 'frente.png'}
# Linha de corte (fracao do bbox, do TOPO): mantem [0..cut), descarta o podio.
CUT_HER = {'warrior': 0.82, 'mage': 0.87, 'rogue': 0.82, 'cleric': 0.81,
           'bard': 0.81, 'paladin': 0.84}
CUT_MON = {'aranhasombria': 0.86, 'escorpiaodepedra': 0.86, 'esqueletoAnimal': 0.86,
           'esqueletoHumano': 0.86, 'koboldbesteiro': 0.85, 'koboldlanceiro': 0.85,
           'loboCinzento': 0.86}

_session = new_session('isnet-general-use')


def itens(grupo):
    """Lista de dicts {name, folder, srcname, outname, backup, cut} p/ o grupo."""
    out = []
    if grupo in ('her', 'tudo'):
        for c, src in FONTE_HER.items():
            d = os.path.join(PAWNS, c)
            out.append(dict(name=c, folder=d, srcname=src, outname='frente.png',
                            backup=os.path.join(d, 'frente_original.png'),
                            cut=CUT_HER.get(c, 1.0)))
    if grupo in ('mon', 'tudo'):
        for n, cut in CUT_MON.items():
            d = os.path.join(PAWNS, 'monstros', n)
            out.append(dict(name=n, folder=d, srcname=f'{n}.png', outname=f'{n}.png',
                            backup=os.path.join(d, f'{n}_original.png'), cut=cut))
    return out


def _src_path(it):
    """Usa sempre o backup original (idempotente); cria-o na 1a vez."""
    if not os.path.exists(it['backup']):
        orig = os.path.join(it['folder'], it['srcname'])
        if os.path.exists(orig):
            Image.open(orig).save(it['backup'])
    return it['backup'] if os.path.exists(it['backup']) else os.path.join(it['folder'], it['srcname'])


def _tem_alpha_real(im):
    if im.mode not in ('RGBA', 'LA'):
        return False
    return im.getchannel('A').getextrema()[0] < 250


def segmentar(it):
    im = Image.open(_src_path(it)).convert('RGBA')
    if _tem_alpha_real(im):
        a = im.getchannel('A').point(lambda v: 255 if v > 128 else 0)
        # zera o quase-branco (anel de adesivo, incl. concavidades) — limiar alto
        # (>242 em TODOS os canais) preserva partes claras da figura (ossos, metal).
        r, g, b = im.convert('RGB').split()
        mn = ImageChops.darker(ImageChops.darker(r, g), b)
        nearwhite = mn.point(lambda v: 255 if v > 242 else 0)
        a = ImageChops.subtract(a, nearwhite)
        a = a.filter(ImageFilter.MinFilter(2 * ERODE_PX + 1))   # erode: come o resto do anel
        a = a.filter(ImageFilter.GaussianBlur(0.6))
        out = im.copy(); out.putalpha(a)
        return out
    out = remove(im.convert('RGB'), session=_session, alpha_matting=True,
                 alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=15,
                 alpha_matting_erode_size=6)
    return out.convert('RGBA')


def regua(seg, name):
    bbox = seg.getbbox()
    fg = seg.crop(bbox) if bbox else seg
    W, H = fg.size
    cinza = Image.new('RGBA', (W, H), (90, 90, 96, 255))
    cinza.alpha_composite(fg)
    cinza = cinza.convert('RGB')
    d = ImageDraw.Draw(cinza)
    for pct in range(5, 100, 5):
        y = int(H * pct / 100)
        cor = (255, 60, 60) if pct % 10 == 0 else (255, 160, 60)
        d.line([(0, y), (W, y)], fill=cor, width=2)
        d.text((4, y + 2), f'{pct}', fill=cor)
    cinza.save(os.path.join(TMP, f'{name}_regua.png'))
    return cinza


def contato(imgs, nome, alvo_h=900):
    redim = []
    for im in imgs:
        w = max(1, int(im.width * alvo_h / im.height))
        redim.append(im.resize((w, alvo_h)))
    larg = sum(i.width for i in redim) + 10 * (len(redim) + 1)
    sheet = Image.new('RGB', (larg, alvo_h + 20), (20, 20, 24))
    x = 10
    for im in redim:
        sheet.paste(im, (x, 10)); x += im.width + 10
    p = os.path.join(TMP, nome)
    sheet.save(p)
    return p


def finalizar(it):
    seg = segmentar(it)
    fg = seg.crop(seg.getbbox())
    W, H = fg.size
    if it['cut'] < 1.0:
        fg = fg.crop((0, 0, W, int(H * it['cut'])))
    b2 = fg.getbbox()
    if b2:
        fg = fg.crop(b2)
    cw = fg.width + int(2 * PAD_SIDE * fg.width)
    ch = fg.height + int(PAD_TOP * fg.height)
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    canvas.alpha_composite(fg, ((cw - fg.width) // 2, ch - fg.height))
    if canvas.height > MAX_H:
        nw = max(1, int(canvas.width * MAX_H / canvas.height))
        canvas = canvas.resize((nw, MAX_H), Image.LANCZOS)
    canvas.save(os.path.join(it['folder'], it['outname']))
    return canvas


def main():
    fase = sys.argv[1] if len(sys.argv) > 1 else 'seg-her'
    if fase.startswith('seg'):
        grupo = 'mon' if fase.endswith('mon') else 'her'
        reguas = []
        for it in itens(grupo):
            seg = segmentar(it)
            seg.save(os.path.join(TMP, f"{it['name']}_seg.png"))
            reguas.append(regua(seg, it['name']))
            print(f"  seg {it['name']}: {seg.getbbox()}")
        print('Contact sheet:', contato(reguas, f'reguas_{grupo}.png'))
    elif fase.startswith('final'):
        grupo = 'mon' if fase.endswith('mon') else ('tudo' if fase == 'final' else 'her')
        finais = []
        for it in itens(grupo):
            finais.append(finalizar(it))
            print(f"  final {it['name']}: ok")
        print('Contact sheet:', contato(finais, f'final_{grupo}.png'))
    else:
        print('uso: normalizar_herois.py [seg-her|seg-mon|final-her|final-mon|final]')


if __name__ == '__main__':
    main()
