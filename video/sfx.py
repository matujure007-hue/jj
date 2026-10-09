"""Genera los efectos de sonido de la intro (sincronizados con intro/index.html).

Uso: python3 sfx.py out/intro_sfx.wav
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 7.0
IMPACT = 2.7
rng = np.random.default_rng(7)
n = int(SR * DUR)
t = np.arange(n) / SR


def lowpass(x, cutoff):
    """Filtro de un polo; cutoff puede ser un arreglo (barrido)."""
    cutoff = np.broadcast_to(cutoff, x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def env(t0, attack, release, shape=2.0):
    e = np.zeros(n)
    up = (t >= t0 - attack) & (t < t0)
    e[up] = ((t[up] - (t0 - attack)) / attack) ** shape
    down = t >= t0
    e[down] = np.exp(-(t[down] - t0) / release)
    return e


noise = rng.standard_normal(n)
out = np.zeros(n)

# Golpe grave cuando aparece el logo
k = t >= 0.15
out[k] += 0.55 * np.sin(2 * np.pi * 48 * (t[k] - 0.15)) * np.exp(-(t[k] - 0.15) * 4)

# Whoosh del panel abriéndose (ruido con barrido de filtro)
sweep = 300 + 3500 * np.clip((t - 1.0) / 0.9, 0, 1) ** 2
w = lowpass(noise, sweep) - lowpass(noise, 120)
out += 0.9 * w * env(1.75, 0.75, 0.25)

# Avión pasando sobre la cámara (rugido con efecto Doppler)
jet = lowpass(noise, 900) * 1.4 + lowpass(noise, 4000) * 0.4
pitch = 160 * np.where(t < 2.15, 1.25, 0.85)
phase = np.cumsum(2 * np.pi * pitch / SR)
jet += 0.25 * np.sin(phase) + 0.12 * np.sin(2.01 * phase)
out += 1.1 * jet * env(2.15, 0.35, 0.45)

# Impacto: boom grave + vidrios rompiéndose
k = t >= IMPACT
dt = t[k] - IMPACT
out[k] += 1.0 * np.sin(2 * np.pi * (70 * dt - 25 * dt ** 2)) * np.exp(-dt * 3.5)
crash = noise - lowpass(noise, 2500)
out += 0.9 * crash * env(IMPACT, 0.005, 0.35)
# Tintineo de pedazos cayendo
for _ in range(90):
    t0 = IMPACT + rng.exponential(0.35)
    if t0 > DUR - 0.2:
        continue
    f = rng.uniform(2500, 7500)
    k = (t >= t0) & (t < t0 + 0.12)
    d = t[k] - t0
    out[k] += rng.uniform(0.05, 0.18) * np.exp(-(t0 - IMPACT) * 1.5) * np.sin(2 * np.pi * f * d) * np.exp(-d * 60)

# Viento en el cielo
wind = lowpass(noise, 400 + 250 * np.sin(t * 1.7) ** 2)
out += 0.9 * wind * np.clip((t - IMPACT) / 0.8, 0, 1) * np.clip((DUR - t) / 1.2, 0.35, 1)

# Whoosh final hacia los clips
sweep = 200 + 5000 * np.clip((t - 6.2) / 0.8, 0, 1) ** 2
out += 0.8 * (lowpass(noise, sweep) - lowpass(noise, 150)) * env(6.95, 0.7, 0.08)

out /= np.max(np.abs(out)) * 1.12
stereo = np.stack([out, out], axis=1)
pcm = (stereo * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(pcm.tobytes())
print('listo:', sys.argv[1])
