// Usage: node render.js d1.html [d2.html ...]  -> writes same-name .png (1080x1920)
// Serves this folder over HTTP (ES modules need it) and renders with WebGL (SwiftShader).
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png' };
const srv = http.createServer((q, s) => {
  const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); } else { s.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); s.end(d); } });
}).listen(0, async () => {
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[error]', e.message));
  for (const f of process.argv.slice(2)) {
    await page.goto(`http://localhost:${port}/${f}`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(200);
    const out = f.replace(/\.html$/, '.png');
    await page.screenshot({ path: out });
    console.log('wrote', out);
  }
  await browser.close(); srv.close();
});
