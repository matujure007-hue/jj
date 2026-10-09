# Reel JetSMART (1080×1920, 15 s)

Resultado: `out/reel_jetsmart.mp4` (con música) y `out/reel_jetsmart_sin_musica.mp4` (solo efectos, para ponerle música en Instagram).

1. Intro 3D (0–7 s): logo oficial → panel amarillo que separa "Jet" y "SMART" → avión que rompe el panel → cielo → valle de Medellín.
2. Clip (7–13 s): `../clips/8249922-hd_1080_1920_25fps.mp4` con zoom de entrada y barrida amarilla.
3. Cierre (13–15 s): logo + "Vuela a Medellín".

## Cómo regenerarlo

```
node capture.mjs                     # intro/index.html -> out/intro.mp4
python3 sfx.py out/intro_sfx.wav     # efectos de la intro
python3 music.py out/musica.wav      # ritmo dembow sintetizado
python3 compose.py                   # arma todo
```

`intro/index.html` también se puede abrir en el navegador para ver la escena en vivo.
