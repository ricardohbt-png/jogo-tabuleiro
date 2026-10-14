"""Gera os sons de gelo das reações elementais (síntese original, sem terceiros).
Roda da raiz: python tools/gerar_sfx_gelo.py
  combate/congelar.ogg : água que congela — estalo de gelo, varredura gelada
                         subindo e faíscas cristalinas.
  combate/crosta.ogg   : lava que endurece — chiado de vapor, batida grave de
                         pedra e estalos secos, com um resto de cristais do frio.
O resultado passa por tools/preparar_sfx.py (mono, ganho fixo, .ogg), como as
demais amostras. Determinístico (sementes fixas)."""
import os
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preparar_sfx  # noqa: E402

TAXA = 44100


def _t(dur):
    return np.arange(int(dur * TAXA)) / TAXA


def _banda(x, lo, hi):
    """Passa-faixa por FFT (zera fora de [lo, hi] Hz, com bordas suaves)."""
    f = np.fft.rfftfreq(len(x), 1 / TAXA)
    X = np.fft.rfft(x)
    g = np.clip((f - lo) / max(lo * 0.2, 50), 0, 1) * np.clip((hi - f) / max(hi * 0.1, 50), 0, 1)
    return np.fft.irfft(X * g, len(x))


def _env(n, ataque, queda):
    """Envelope: sobe em `ataque` s, cai exponencialmente com constante `queda` s."""
    t = np.arange(n) / TAXA
    e = np.minimum(t / max(ataque, 1e-4), 1.0) * np.exp(-t / queda)
    return e


def _somar(dest, trecho, inicio):
    i = int(inicio * TAXA)
    if i >= len(dest):
        return
    fim = min(len(dest), i + len(trecho))
    dest[i:fim] += trecho[:fim - i]


def _estalo(rng, dur, lo, hi, queda):
    n = int(dur * TAXA)
    return _banda(rng.standard_normal(n), lo, hi) * _env(n, 0.001, queda)


def _faisca(rng, freq, dur=0.18):
    """Pequeno 'tlim' de cristal: seno com um parcial inarmônico e queda rápida."""
    t = _t(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.71 * t + rng.uniform(0, 6))
    return x * _env(len(t), 0.0008, dur / 5)


def _varredura(dur, f0, f1, rng):
    """Ruído estreito cuja faixa sobe de f0 a f1 (sopro gelado)."""
    n = int(dur * TAXA)
    ruido = rng.standard_normal(n)
    saida = np.zeros(n)
    passos = 24
    for k in range(passos):
        a, b = k * n // passos, (k + 1) * n // passos
        fc = f0 * (f1 / f0) ** (k / (passos - 1))
        seg = _banda(ruido[a:b], fc * 0.8, fc * 1.3)
        saida[a:b] = seg
    return saida * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5


def congelar():
    rng = np.random.default_rng(7)
    out = np.zeros(int(1.5 * TAXA))
    _somar(out, 1.1 * _estalo(rng, 0.12, 2500, 9000, 0.03), 0.0)          # estalo inicial
    _somar(out, 0.55 * _varredura(0.55, 900, 5200, rng), 0.02)            # sopro subindo
    for inicio, g in ((0.14, 0.7), (0.30, 0.55), (0.52, 0.45), (0.78, 0.30)):
        _somar(out, g * _estalo(rng, 0.09, 1800, 7000, 0.02), inicio)     # rachaduras
    # cristais: densos no começo, rareando
    # (tempos estratificados: sorteio solto deixava um buraco de silêncio no meio)
    inst = np.concatenate([0.02 + np.arange(18) * 0.027 + rng.uniform(0, 0.02, 18),
                           0.52 + np.arange(9) * 0.075 + rng.uniform(0, 0.05, 9)])
    for ti in inst:
        queda = 1.0 if ti < 0.52 else max(0.25, 1.0 - (ti - 0.52) / 0.9)
        _somar(out, queda * rng.uniform(0.12, 0.28) * _faisca(rng, rng.uniform(2300, 6200)), ti)
    return out


def crosta():
    rng = np.random.default_rng(11)
    out = np.zeros(int(1.7 * TAXA))
    n_v = int(1.1 * TAXA)
    vapor = _banda(rng.standard_normal(n_v), 2200, 9500) * _env(n_v, 0.04, 0.35)
    _somar(out, 0.55 * vapor, 0.0)                                         # chiado de vapor
    # bolhas estourando no começo
    for ti in np.sort(rng.uniform(0.02, 0.45, 9)):
        _somar(out, 0.25 * _estalo(rng, 0.03, 700, 2500, 0.008), ti)
    # batida grave de pedra assentando
    t = _t(0.5)
    freq = 95 * np.exp(-t * 2.2) + 48
    thunk = np.sin(2 * np.pi * np.cumsum(freq) / TAXA) * _env(len(t), 0.002, 0.11)
    _somar(out, 0.9 * thunk, 0.22)
    _somar(out, 0.5 * _estalo(rng, 0.10, 200, 900, 0.03), 0.22)
    # estalos secos da crosta se formando
    for inicio, g in ((0.38, 0.6), (0.52, 0.5), (0.70, 0.35), (0.95, 0.25)):
        _somar(out, g * _estalo(rng, 0.07, 600, 3200, 0.015), inicio)
    # resto de cristais do frio, discreto
    for ti in np.sort(rng.uniform(0.15, 0.9, 7)):
        _somar(out, rng.uniform(0.07, 0.15) * _faisca(rng, rng.uniform(2800, 6200)), ti)
    return out


def _gravar_wav(x, caminho):
    pico = float(np.max(np.abs(x))) or 1.0
    pcm = np.int16(np.clip(x / pico * 0.9, -1, 1) * 32767)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        for nome, fn in (("congelar", congelar), ("crosta", crosta)):
            wav = os.path.join(tmp, nome + ".wav")
            _gravar_wav(fn(), wav)
            tam = preparar_sfx.preparar(wav, f"combate/{nome}.ogg")
            print(f"combate/{nome}.ogg  {tam / 1024:.1f} KB")
