// node render-video.js [fps]  -> frames piped to ffmpeg -> silent.mp4 ; also writes events.json (click/tap times)
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const FPS = +(process.argv[2] || 30);
const types = { '.html': 'text/html', '.js': 'text/javascript' };
const srv = http.createServer((q, s) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); s.end(d); } }); })
.listen(0, async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('[error]', e.message));
  await page.goto(`http://localhost:${srv.address().port}/${process.env.PAGE || 'video.html'}`, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
  const ev = await page.evaluate(() => ({ clicks: window.CLICKS, taps: window.TAPS, duration: window.DURATION }));
  fs.writeFileSync(path.join(__dirname, process.env.EVENTS || 'events.json'), JSON.stringify(ev));
  const N = Math.round(ev.duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(__dirname, process.env.OUT || 'silent.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    await page.evaluate(t => window.renderAt(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('done', ((Date.now() - t0) / 1000).toFixed(0), 's');
  await browser.close(); srv.close();
});
