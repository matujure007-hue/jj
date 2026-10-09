# Video Reel JetSMART

Intro en 3D (logo → panel amarillo → avión que lo rompe → cielo → valle de Medellín), 1080×1920 a 30 fps.

- `intro/index.html`: la escena (Three.js). Ábrela en el navegador para verla en vivo.
- `capture.mjs`: la renderiza cuadro por cuadro a MP4 (`node capture.mjs`). Con `--logo clips/logo.png` usa el logo oficial.
- `sfx.py`: genera los efectos de sonido (`python3 sfx.py out/intro_sfx.wav`).
- `out/intro_con_sonido.mp4`: resultado final de la intro.

Los clips de Medellín van en `../clips/`.
