// node ov_render.js <projectDir>  (reads <projectDir>/plan.json, writes <projectDir>/txt/*.png)
// Renders title/subtitle overlays (1080x1920, transparent) and white text cards (1080x810) from plan.json.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const dir = process.argv[2];
const plan = JSON.parse(fs.readFileSync(path.join(dir, 'plan.json'), 'utf8'));
const outd = path.join(dir, 'txt'); fs.mkdirSync(outd, { recursive: true });
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  const url = 'file://' + path.join(__dirname, 'ov.html');
  const shot = async (html, file, transparent) => {
    await page.goto(url);
    await page.evaluate(h => { document.body.innerHTML = h; }, html);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outd, file), omitBackground: transparent });
  };
  await shot(`<div class="title">${plan.title}</div>`, 'title.png', true);
  for (let k = 0; k < plan.subs.length; k++)
    await shot(`<div class="sub">${plan.subs[k][1]}</div>`, `sub${String(k).padStart(2, '0')}.png`, true);
  await page.setViewportSize({ width: 1080, height: 810 });
  for (const [i, s] of plan.segments.entries())
    if (s.type === 'text') await shot(`<div class="card">${s.text}</div>`, `card${i}.png`, false);
  console.log('overlays done');
  await browser.close();
})();
