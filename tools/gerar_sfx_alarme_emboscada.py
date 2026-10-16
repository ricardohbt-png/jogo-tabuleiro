"""Gera o alarme curto original usado na transição da emboscada de estrada.

Roda da raiz: python tools/gerar_sfx_alarme_emboscada.py
Saída: assets/sfx/exploracao/alarme_emboscada.ogg
"""
import os
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preparar_sfx  # noqa: E402

TAXA = 44100


def _alarme():
    total = int(1.22 * TAXA)
    out = np.zeros(total, dtype=np.float64)
    # Chamado curto de trombeta em três notas descendentes, com caráter de perigo.
    # Os harmônicos dão o timbre de bronze; não há ruído nem outra camada sonora.
    harmonicos = np.array([1.0, 0.66, 0.48, 0.34, 0.23, 0.16, 0.11, 0.07, 0.045, 0.025])
    for inicio, fundamental, dur in ((0.00, 349.23, 0.23), (0.29, 277.18, 0.23), (0.58, 261.63, 0.52)):
        n = int(dur * TAXA)
        t = np.arange(n) / TAXA
        vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 5.2 * t)
        tone = np.zeros(n, dtype=np.float64)
        for ordem, ganho in enumerate(harmonicos, start=1):
            freq = fundamental * ordem * vibrato
            fase = 2 * np.pi * np.cumsum(freq) / TAXA
            tone += ganho * np.sin(fase)
        ataque = np.minimum(t / 0.018, 1.0)
        saida = np.minimum((dur - t) / 0.045, 1.0)
        envelope = np.clip(ataque * saida, 0, 1)
        pulse = tone * envelope
        offset = int(inicio * TAXA)
        out[offset:offset + n] += pulse

    return out


def _gravar_wav(samples, path):
    peak = float(np.max(np.abs(samples))) or 1.0
    pcm = np.int16(np.clip(samples / peak * 0.9, -1, 1) * 32767)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(TAXA)
        wav.writeframes(pcm.tobytes())


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "alarme_emboscada.wav")
        _gravar_wav(_alarme(), wav_path)
        size = preparar_sfx.preparar(wav_path, "exploracao/alarme_emboscada.ogg")
        print(f"exploracao/alarme_emboscada.ogg  {size / 1024:.1f} KB")
