// node preview.js 2 7 12 ...  -> frame_<t>.png stills for checking
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const types = { '.html': 'text/html', '.js': 'text/javascript' };
const srv = http.createServer((q, s) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); s.end(d); } }); })
.listen(0, async () => {
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1' } : undefined;
  const browser = await chromium.launch({ proxy, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: +(process.env.VW || 1080), height: +(process.env.VH || 1920) } });
  page.on('pageerror', e => console.log('[error]', e.message)); page.on('console', m => console.log('[page]', m.text()));
  await page.goto(`http://localhost:${srv.address().port}/${process.env.PAGE || 'video.html'}`, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
  fs.mkdirSync(path.join(__dirname, 'preview'), { recursive: true });
  for (const t of process.argv.slice(2)) {
    const t0 = Date.now(); await page.evaluate(t => window.renderAt(t), +t);
    await page.screenshot({ path: path.join(__dirname, 'preview', `f_${t}.jpg`), type: 'jpeg', quality: 85 });
    console.log(t, Date.now() - t0, 'ms');
  }
  console.log('clicks', JSON.stringify(await page.evaluate(() => window.CLICKS)));
  await browser.close(); srv.close();
});
