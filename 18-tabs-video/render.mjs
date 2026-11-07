// usage: (serve this folder on 127.0.0.1:8123) node render.mjs <outDir> [times...]   (no times => full 900 frames)
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
import fs from 'fs';

const out = process.argv[2];
const times = process.argv.slice(3).map(Number);
fs.mkdirSync(out, { recursive: true });
const FPS = 30, DUR = 30;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto('http://127.0.0.1:8123/index.html');
await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });

const list = times.length ? times : Array.from({ length: FPS * DUR }, (_, i) => i / FPS);
const t0 = Date.now();
for (let i = 0; i < list.length; i++) {
  const t = list[i];
  await page.evaluate(t => window.setTime(t), t);
  const name = times.length ? `t${t.toFixed(2)}.jpg` : `f${String(i).padStart(4, '0')}.jpg`;
  await page.screenshot({ path: `${out}/${name}`, type: 'jpeg', quality: 93 });
  if (i % 60 === 0) console.log(`frame ${i}/${list.length}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}
await browser.close();
