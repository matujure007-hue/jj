"""Ritmo de reguetón (dembow) sintetizado para el Reel, 100 BPM.

Entra con todo cuando arranca el clip (7.0 s) y remata con un golpe en el cierre (13.0 s).
Uso: python3 music.py out/musica.wav
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 15.0
BPM = 100
DROP = 7.0      # empieza el clip
END = 13.0      # empieza el cierre con logo
STEP = 60 / BPM / 4  # semicorchea
rng = np.random.default_rng(3)
n = int(SR * DUR)
out = np.zeros((n, 2))


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= n:
        return
    sig = sig[: n - i]
    out[i:i + len(sig), 0] += sig * gain * (1 - pan) ** 0.5
    out[i:i + len(sig), 1] += sig * gain * (1 + pan) ** 0.5


def tt(d):
    return np.arange(int(d * SR)) / SR


def kick():
    t = tt(0.45)
    f = 45 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def snare():
    t = tt(0.22)
    noise = rng.standard_normal(len(t))
    noise = noise - np.convolve(noise, np.ones(6) / 6, 'same')  # quita graves
    return (0.6 * noise + 0.5 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22)


def hat():
    t = tt(0.05)
    noise = rng.standard_normal(len(t))
    return (noise - np.convolve(noise, np.ones(3) / 3, 'same')) * np.exp(-t * 90)


def note(freq, d, kind='bass'):
    t = tt(d)
    if kind == 'bass':
        s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
        return s * np.minimum(1, t * 200) * np.exp(-t * 1.2)
    # pluck: armónicos que se apagan rápido
    s = sum(np.sin(2 * np.pi * freq * k * t) / k * np.exp(-t * (3 + k * 2.5)) for k in range(1, 7))
    return s * np.minimum(1, t * 400)


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# Am – F – C – G (raíz del bajo, acorde)
CHORDS = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
DEMBOW_SNARE = {3, 6, 11, 14}
ARP = [0, 1, 2, 1, 0, 2, 1, 2]

bar_len = STEP * 16
bars = int(np.ceil((END - DROP) / bar_len)) + 1
for b in range(bars):
    root, chord = CHORDS[b % 4]
    for s in range(16):
        at = DROP + (b * 16 + s) * STEP
        if at >= END:
            break
        if s % 4 == 0:
            add(kick(), at, 0.9)
        if s in DEMBOW_SNARE:
            add(snare(), at, 0.45, pan=0.1)
        if s % 2 == 0:
            add(hat(), at, 0.18 if s % 4 else 0.1, pan=-0.3)
        if s in (0, 3, 6, 8, 11, 14):
            add(note(midi(root), STEP * 2.5, 'bass'), at, 0.35)
        if s % 2 == 0:
            add(note(midi(chord[ARP[(s // 2) % 8]] + 12), STEP * 3, 'pluck'), at, 0.12, pan=0.35 if s % 4 else -0.35)

# Remate en el cierre: golpe + acorde largo
root, chord = CHORDS[0]
add(kick(), END, 1.0)
add(snare(), END, 0.5)
for m in chord:
    add(note(midi(m + 12), 2.0, 'pluck'), END, 0.22)
add(note(midi(root), 2.0, 'bass'), END, 0.45)

# Pre-entrada: redoble que sube antes del drop
for i in range(8):
    at = DROP - (8 - i) * STEP / 2
    add(snare(), at, 0.08 + 0.04 * i)

out /= np.max(np.abs(out)) * 1.1
with wave.open(sys.argv[1], 'wb') as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((out * 32767).astype(np.int16).tobytes())
print('listo:', sys.argv[1])
