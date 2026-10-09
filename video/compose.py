"""Arma el Reel final: intro 3D + clip + cierre con logo, con sonido.

Requiere haber corrido antes:
  node capture.mjs                    -> out/intro.mp4
  python3 sfx.py out/intro_sfx.wav
  python3 music.py out/musica.wav
Uso: python3 compose.py
Genera out/reel_jetsmart.mp4 (con música) y out/reel_jetsmart_sin_musica.mp4.
"""
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
CLIP = ROOT.parent / 'clips' / '8249922-hd_1080_1920_25fps.mp4'
W, H, FPS = 1080, 1920, 30
YELLOW = (255, 198, 41)
NAVY = (31, 64, 104)

INTRO_DUR = 7.0
CLIP_IN, CLIP_OUT, CLIP_SPEED = 1.0, 7.6, 1.1   # 6.6 s del original a 1.1x = 6.0 s
CLIP_DUR = (CLIP_OUT - CLIP_IN) / CLIP_SPEED
WIPE = 0.3                                      # barrida amarilla al final del clip
END_DUR = 2.0
SLOGAN = 'Vuela a Medellín'


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def end_card():
    """Cuadros del cierre: el amarillo sale hacia la izquierda y aparece el logo."""
    frames = OUT / 'endcard'
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    jet = Image.open(ROOT / 'intro' / 'logo_jet.png')
    smart = Image.open(ROOT / 'intro' / 'logo_smart.png')
    logo = Image.new('RGBA', (430 + smart.width, smart.height))
    logo.alpha_composite(jet, (0, 0))
    logo.alpha_composite(smart, (430, 0))
    font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', 64)
    n = int(END_DUR * FPS)
    for i in range(n):
        t = i / FPS
        img = Image.new('RGBA', (W, H), (255, 255, 255, 255))
        # Logo: escala con rebote suave + aparece
        k = ease((t - 0.12) / 0.45)
        if k > 0:
            lw = int(860 * (0.88 + 0.12 * k))
            lg = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
            a = lg.getchannel('A').point(lambda v: int(v * k))
            lg.putalpha(a)
            img.alpha_composite(lg, ((W - lg.width) // 2, H // 2 - lg.height // 2 - 60))
        # Eslogan: sube y aparece
        k2 = ease((t - 0.45) / 0.4)
        if k2 > 0:
            layer = Image.new('RGBA', (W, H))
            d = ImageDraw.Draw(layer)
            tw = d.textlength(SLOGAN, font=font)
            y = H // 2 + 130 + int(30 * (1 - k2))
            d.text(((W - tw) / 2, y), SLOGAN, font=font, fill=NAVY + (int(255 * k2),))
            # barrita amarilla debajo
            bw = int(220 * k2)
            d.rounded_rectangle(((W - bw) / 2, y + 100, (W + bw) / 2, y + 112), 6, fill=YELLOW + (255,))
            img.alpha_composite(layer)
        # Panel amarillo que se va a la izquierda
        x = int(-W * ease(t / 0.35))
        if x > -W:
            ImageDraw.Draw(img).rectangle((x, 0, x + W, H), fill=YELLOW + (255,))
        img.convert('RGB').save(frames / f'e{i:03d}.png')
    return frames


def run(*args):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *map(str, args)], check=True)


def main():
    frames = end_card()
    total = INTRO_DUR + CLIP_DUR + END_DUR
    wipe_at = CLIP_DUR - WIPE
    vf = (
        f'[1:v]trim=start={CLIP_IN}:end={CLIP_OUT},setpts=(PTS-STARTPTS)/{CLIP_SPEED},fps={FPS},'
        # "punch": entra con zoom y se asienta
        f"scale=w='2*trunc(540*(1+0.14*pow(max(0\\,1-t/0.55)\\,2)))':h=-2:eval=frame,crop={W}:{H},"
        'eq=saturation=1.15:contrast=1.05,fade=in:st=0:d=0.35:color=white,setsar=1[c0];'
        f'color=c=0xFFC629:s={W}x{H}:r={FPS}:d={CLIP_DUR}[y];'
        f"[c0][y]overlay=x='if(lt(t\\,{wipe_at:.3f})\\,{W}\\,{W}*(1-pow((t-{wipe_at:.3f})/{WIPE}\\,2)))':y=0:eval=frame,format=yuv420p[c];"
        '[0:v]setsar=1,format=yuv420p[i];'
        f'[2:v]fps={FPS},setsar=1,format=yuv420p[e];'
        '[i][c][e]concat=n=3:v=1:a=0[v]'
    )
    video = OUT / 'reel_video.mp4'
    run('-i', OUT / 'intro.mp4', '-i', CLIP, '-framerate', FPS, '-i', frames / 'e%03d.png',
        '-filter_complex', vf, '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-r', FPS, video)

    # Audio: efectos de la intro + música
    run('-i', video, '-i', OUT / 'intro_sfx.wav', '-i', OUT / 'musica.wav', '-filter_complex',
        f'[1:a]apad=whole_dur={total}[s];[2:a]volume=0.8[m];[s][m]amix=inputs=2:normalize=0,'
        'alimiter=limit=0.95[a]',
        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', total,
        '-movflags', '+faststart', OUT / 'reel_jetsmart.mp4')
    # Versión solo con efectos, para ponerle música desde Instagram
    run('-i', video, '-i', OUT / 'intro_sfx.wav', '-filter_complex', f'[1:a]apad=whole_dur={total}[a]',
        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', total,
        '-movflags', '+faststart', OUT / 'reel_jetsmart_sin_musica.mp4')
    video.unlink()
    print('listo:', OUT / 'reel_jetsmart.mp4', f'({total:.1f} s)')


if __name__ == '__main__':
    main()
