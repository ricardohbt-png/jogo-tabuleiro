"""Prepara um som para assets/sfx/ (spec 2026-09-23-sons).
Uso: python tools/preparar_sfx.py <origem> <destino relativo a assets/sfx>
        [--loop] [--ja-loop] [--stereo] [--ss=S] [--to=S] [--pitch=F] [--fade=S] [--q=N]
- efeito: corta silêncio nas pontas, ganho fixo p/ -18 LUFS (pico <= -2 dBTP), mono, .ogg q4
- --loop: sem corte; loudness -26 LUFS; emenda com crossfade de 1 s (o fim
  funde no começo), estéreo.
- --ja-loop: arquivo que JÁ emenda sem clique: só loudness -26 LUFS, estéreo,
  sem crossfade.
- --ss/--to: recorta um trecho da origem (segundos) antes de tratar — para
  arquivos com vários sons em sequência.
- --pitch=F: abaixa/sobe o tom por reamostragem (0.8 = mais grave e mais
  longo). Gera um DERIVADO — registre assim no LICENCAS.md.
- --fade=S: rampa de entrada e de saída de S segundos (efeito) — para trechos
  cortados do meio de um som contínuo (fogo, água, vento), que estalariam.
- --q=N: qualidade Vorbis (padrão 4 efeito, 3 ambiente).
O loudnorm trabalha internamente a 192 kHz; a saída é forçada a 44,1 kHz."""
import json, os, subprocess, sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TAXA = "44100"


def _ganho_efeito(entrada, corte):
    """Ganho LINEAR (dB) para o efeito: mira -18 LUFS sem deixar o pico
    verdadeiro passar de -2 dBTP. O loudnorm de passada única, em clipes de
    décimos de segundo, deixava o pico em 0 dBFS; ganho fixo não distorce.
    Clipe curto demais para medir LUFS (< 0,4 s) vai por pico a -3 dBTP."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + entrada +
                       ["-af", corte + ",loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    dados = json.loads(txt[txt.rindex("{"):txt.rindex("}") + 1])
    i, tp = float(dados["input_i"]), float(dados["input_tp"])
    if i < -60:
        return -3.0 - tp
    return min(-18.0 - i, -2.0 - tp)


def preparar(origem, destino, loop=False, ja_loop=False, stereo=False,
             ss=None, to=None, pitch=None, q=None, fade=None):
    saida = os.path.join(RAIZ, "assets", "sfx", destino)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    entrada = ["-i", origem]
    if ss is not None:
        entrada = ["-ss", str(ss)] + entrada
    if to is not None:
        entrada = entrada[:-2] + ["-to", str(to)] + entrada[-2:]
    pre = ""
    if pitch:
        pre = f"aresample={TAXA},asetrate={int(int(TAXA) * float(pitch))},aresample={TAXA},"
    if loop:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entrada + ["-filter_complex",
               f"[0]{pre}asplit[a][b];[a]atrim=0:1,asetpts=PTS-STARTPTS[cab];"
               "[b]atrim=1,asetpts=PTS-STARTPTS[corpo];"
               "[corpo][cab]acrossfade=d=1,loudnorm=I=-26:TP=-3:LRA=11[o]",
               "-map", "[o]", "-ac", "2", "-ar", TAXA, "-c:a", "libvorbis",
               "-q:a", str(q or 3), saida]
    elif ja_loop:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entrada + [
               "-af", pre + "loudnorm=I=-26:TP=-3:LRA=11",
               "-ac", "2", "-ar", TAXA, "-c:a", "libvorbis", "-q:a", str(q or 3), saida]
    else:
        # O downmix vai DENTRO do grafo, antes da medição: o `-ac 1` do
        # ffmpeg soma L+R a -3 dB cada (+3 dB num som centrado) e furava o
        # teto de pico que a medição tinha acabado de calcular.
        mix = "" if stereo else "aformat=channel_layouts=mono,"
        corte = (pre + mix + "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                 "silenceremove=start_periods=1:start_threshold=-50dB,areverse")
        if fade:
            f = float(fade)
            corte += f",afade=t=in:d={f},areverse,afade=t=in:d={f},areverse"
        filtro = corte + f",volume={_ganho_efeito(entrada, corte):.2f}dB"
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entrada + ["-af", filtro,
               "-ac", "2" if stereo else "1", "-ar", TAXA, "-c:a", "libvorbis",
               "-q:a", str(q or 4), saida]
    subprocess.run(cmd, check=True)
    return os.path.getsize(saida)


def _opt(nome):
    for a in sys.argv[1:]:
        if a.startswith(f"--{nome}="):
            return a.split("=", 1)[1]
    return None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    tam = preparar(args[0], args[1], loop="--loop" in sys.argv,
                   ja_loop="--ja-loop" in sys.argv, stereo="--stereo" in sys.argv,
                   ss=_opt("ss"), to=_opt("to"), pitch=_opt("pitch"), q=_opt("q"), fade=_opt("fade"))
    print(f"{args[1]}  {tam/1024:.1f} KB")
