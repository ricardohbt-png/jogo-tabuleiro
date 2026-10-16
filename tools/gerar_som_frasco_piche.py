"""Gera três impactos originais para o Frasco de Piche (mono, Ogg Vorbis q4)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "sfx" / "combate"
RATE = 44_100
DURATION = 0.58


def lowpass(signal: np.ndarray, cutoff: float) -> np.ndarray:
    """Filtro passa-baixas simples e estável para ruído de impacto."""
    alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff / RATE)
    out = np.empty_like(signal)
    last = 0.0
    for i, sample in enumerate(signal):
        last += alpha * (sample - last)
        out[i] = last
    return out


def envelope(length: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(length, dtype=np.float64) / RATE
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def render(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    length = round(RATE * DURATION)
    t = np.arange(length, dtype=np.float64) / RATE
    noise = rng.standard_normal(length)

    # Ataque: vidro agudo em estilhaços, misturado com um baque grave e úmido.
    crack = (noise - lowpass(noise, 1_300)) * envelope(length, 0.0015, 0.045)
    wet = lowpass(noise, 720) * envelope(length, 0.002, 0.085)
    thump_freq = rng.uniform(105, 145)
    thump = np.sin(2 * np.pi * thump_freq * t) * envelope(length, 0.001, 0.065)

    # Ressonâncias metálicas curtas sugerem o frasco quebrando sem soar como explosão.
    shards = np.zeros(length, dtype=np.float64)
    for start in rng.uniform(0.006, 0.045, size=5):
        hz = rng.uniform(1_700, 4_200)
        decay = rng.uniform(0.012, 0.035)
        active = t >= start
        tau = t[active] - start
        shards[active] += np.sin(2 * np.pi * hz * tau) * np.exp(-tau / decay)

    # Cauda de pequenas gotas espessas que termina rapidamente.
    drips = np.zeros(length, dtype=np.float64)
    for start in rng.uniform(0.10, 0.42, size=4):
        hz = rng.uniform(180, 480)
        active = t >= start
        tau = t[active] - start
        dur = rng.uniform(0.025, 0.06)
        drips[active] += (rng.uniform(0.3, 0.7) * np.sin(2 * np.pi * hz * tau)
                          * np.exp(-tau / dur))
    drips += lowpass(rng.standard_normal(length), 950) * envelope(length, 0.10, 0.13) * 0.24

    signal = 0.50 * crack + 0.38 * wet + 0.30 * thump + 0.12 * shards + 0.11 * drips
    # Pequenas diferenças de duração e timbre entre as tomadas.
    signal *= 0.94 + 0.06 * np.cos(2 * np.pi * t / DURATION)
    signal *= np.exp(-np.maximum(t - 0.48, 0) / 0.035)
    peak = np.max(np.abs(signal))
    if peak:
        signal *= 0.82 / peak
    return np.asarray(np.clip(signal, -1, 1) * 32767, dtype="<i2")


def main() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg não encontrado no PATH")
    DEST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="frasco-piche-") as tmp:
        for variant in range(1, 4):
            wav_path = Path(tmp) / f"impacto_{variant}.wav"
            ogg_path = DEST / f"frasco_piche_impacto_{variant}.ogg"
            samples = render(8100 + variant)
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(RATE)
                wav.writeframes(samples.tobytes())
            subprocess.run([
                ffmpeg, "-y", "-v", "error", "-i", str(wav_path),
                "-c:a", "libvorbis", "-q:a", "4", str(ogg_path),
            ], check=True)
            print(ogg_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
