// Capture DC mobile posts at 360px with thin red/green boxes around key phrases (no header/category bars needed later).
// node dcmark.js <marks.json> <outdir> [names...]  -> <name>.png (full width, from page top to end of body + margin)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [specFile, out, ...only] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const COLORS = { red: '#e3262b', green: '#14964a' };
const CSS = `
  #auto_picture_area, .adv-groupno, [class*="adv-group"], section.clkhigh, .pwlink, ins, iframe { display:none !important; }
  .x-blur { filter: blur(5px) !important; }
  .x-mark { outline: 1.5px solid var(--c); outline-offset: 3px; border-radius: 2px;
            -webkit-box-decoration-break: clone; box-decoration-break: clone; }
`;
(async () => {
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const ctx = await browser.newContext({
    viewport: { width: 360, height: 780 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    locale: 'ko-KR', timezoneId: 'Asia/Seoul',
  });
  for (const [name, s] of Object.entries(spec)) {
    if (only.length && !only.includes(name)) continue;
    const page = await ctx.newPage();
    await page.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3500);
    await page.addStyleTag({ content: CSS });
    const info = await page.evaluate(([marks, COLORS]) => {
      document.querySelectorAll('.gallview-tit-box .ginfo2 li:first-child, .gallview-tit-box [class*="nick"]').forEach(e => e.classList.add('x-blur'));
      const roots = { title: document.querySelector('.gallview-tit-box .tit'), body: document.querySelector('.thum-txtin') };
      const missing = [];
      for (const [where, phrase, color] of marks) {
        if (where === 'titleblock' || where === 'bodyblock') {
          let el = null;
          if (where === 'titleblock') el = roots.title;
          else el = [...document.querySelectorAll('.thum-txtin p, .thum-txtin div')].filter(p => p.innerText.includes(phrase)).pop();
          if (el) { el.classList.add('x-mark'); el.style.setProperty('--c', COLORS[color]); el.style.display = 'block'; el.style.width = 'fit-content'; el.style.outlineOffset = '4px'; }
          else missing.push(where + ':' + phrase);
          continue;
        }
        const root = roots[where]; let done = false;
        if (root) {
          const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
          let n;
          while (!done && (n = tw.nextNode())) {
            const i = n.nodeValue.indexOf(phrase);
            if (i < 0) continue;
            const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + phrase.length);
            const span = document.createElement('span'); span.className = 'x-mark'; span.style.setProperty('--c', COLORS[color]);
            r.surroundContents(span); done = true;
          }
        }
        if (!done) missing.push(where + ':' + phrase);
      }
      window.scrollTo(0, 0);
      const box = e => e ? [Math.round(e.getBoundingClientRect().top), Math.round(e.getBoundingClientRect().bottom)] : null;
      const ps = [...document.querySelectorAll('.thum-txtin p, .thum-txtin div')].filter(p => p.innerText.trim() && !p.closest('#auto_picture_area'));
      return { missing, gall: box(document.querySelector('.gall-tit-box')), titleBox: box(document.querySelector('.gallview-tit-box')),
               bodyEnd: ps.length ? Math.round(Math.max(...ps.map(p => p.getBoundingClientRect().bottom))) : null };
    }, [s.marks, COLORS]);
    await page.waitForTimeout(500);
    const h = Math.min((info.bodyEnd || 500) + 24, 900);
    await page.screenshot({ path: path.join(out, name + '.png'), clip: { x: 0, y: 0, width: 360, height: h } });
    console.log(name, JSON.stringify({ h: h * 3, ...info }));
    await page.close();
  }
  await browser.close();
})();
