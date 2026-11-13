"""Corta a animação da morte do Gilo em cenas para contar a história slide a slide.
gilo_escorpioes_animacao.mp4 são 4 quadros parados com dissolvências de 1/3 s; aqui cada
passagem vira um clipe lento, e o retrato do cerco (gilo_escorpioes_praca.png) entra no meio.
Roda da raiz: python tools/gerar_gilo_cenas.py"""
import os
import subprocess
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "assets", "story")
ORIGEM = os.path.join(PASTA, "gilo_escorpioes_animacao.mp4")
CERCO = os.path.join(PASTA, "gilo_escorpioes_praca.png")
QUADROS = {"chegada": 1.0, "susto": 3.2, "queda": 5.5, "roupas": 8.0}   # segundos, no meio de cada cena parada
SEGURA, DISSOLVE = 0.4, 2.2


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def quadro(tempo, destino, *opcoes):
    ffmpeg("-ss", str(tempo), "-i", ORIGEM, "-frames:v", "1", *opcoes, destino)


def clipe(de, para, destino):
    total = SEGURA * 2 + DISSOLVE
    ffmpeg("-loop", "1", "-t", str(total), "-framerate", "24", "-i", de,
           "-loop", "1", "-t", str(total), "-framerate", "24", "-i", para,
           "-filter_complex", f"[0:v][1:v]xfade=transition=fade:duration={DISSOLVE}:offset={SEGURA},format=yuv420p",
           "-t", str(total), "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", "-an", destino)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        cena = {nome: os.path.join(tmp, nome + ".png") for nome in QUADROS}
        for nome, tempo in QUADROS.items():
            quadro(tempo, cena[nome])
        for nome, numero in (("chegada", 1), ("susto", 2), ("queda", 4)):
            quadro(QUADROS[nome], os.path.join(PASTA, f"gilo_cena_{numero}_{nome}.jpg"), "-q:v", "2")
        clipe(cena["chegada"], cena["susto"], os.path.join(PASTA, "gilo_cena_2_susto.mp4"))
        clipe(cena["susto"], CERCO, os.path.join(PASTA, "gilo_cena_3_cerco.mp4"))
        clipe(CERCO, cena["queda"], os.path.join(PASTA, "gilo_cena_4_queda.mp4"))
        clipe(cena["queda"], cena["roupas"], os.path.join(PASTA, "gilo_cena_5_roupas.mp4"))


if __name__ == "__main__":
    main()
