// Renderiza intro/index.html cuadro por cuadro y lo convierte a MP4.
// Uso: node capture.mjs [--fps 30] [--out out/intro.mp4] [--frames a,b,c]
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1]]);
  return acc;
}, []));
const fps = Number(args.fps || 30);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname));
const out = path.resolve(args.out || path.join(root, 'out/intro.mp4'));
const framesDir = path.join(root, 'out/frames');

const types = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, r));
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.error('[page error]', e.message));
const q = new URLSearchParams({ capture: '1' });
await page.goto(`http://localhost:${port}/intro/index.html?${q}`);
await page.waitForFunction(() => window.renderAt && window.logoReady);
await page.evaluate(() => document.fonts.ready);

const duration = await page.evaluate(() => window.DURATION);
const canvas = await page.$('canvas');

if (args.frames) {
  // Solo algunos cuadros de prueba (en segundos)
  fs.mkdirSync(path.join(root, 'out/stills'), { recursive: true });
  for (const s of args.frames.split(',').map(Number)) {
    await page.evaluate(t => window.renderAt(t), s);
    await canvas.screenshot({ path: path.join(root, `out/stills/t${s.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
  }
} else {
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });
  const n = Math.round(duration * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.renderAt(t), i / fps);
    await canvas.screenshot({ path: path.join(framesDir, `f${String(i).padStart(4, '0')}.png`) });
    if (i % 30 === 0) console.log(`cuadro ${i}/${n}`);
  }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(framesDir, 'f%04d.png'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]);
  console.log('listo:', out);
}
await browser.close();
server.close();
