// Capture news articles at 360px mobile with 2px red/green boxes and Korean translations inserted
// in the mark color on a nearly see-through, very slightly blurred background.
// Cookie banners, sticky bars, ads and video players are removed; the page is captured from the top.
// node newsmark.js <spec.json> <outdir> [names...]
// spec: { "<name>": { "url": "...", "h": 2400, "hide": ["css", ...],
//          "marks": [ { "text": "substring", "tag": "p", "color": "red|green", "tr": "번역", "pos": "after|before" } ] } }
//   tag defaults to "h1,h2,p,li,blockquote,figcaption"; the smallest matching element containing text is marked.
//   pos "before" puts the translation above (use for images/tables).
//   "lines": ["줄1 번역", ...] instead of "tr" writes the Korean under each English line (interlinear);
//   "fs" sets its font size (CSS px, default 17). The English lines found are printed so the
//   translations can be matched to them.
// Output: <name>.png (1080 wide) and prints mark rects in output pixels (x3) for piece planning.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [specFile, out, ...only] = process.argv.slice(2);
const fontdir = path.join(__dirname, '..', 'fonts');
const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const COLORS = { red: '#e3262b', green: '#14964a' };
const CSS = `
  @font-face{font-family:'PretendardX';font-weight:600;src:url(/__ccfont/semibold.woff2) format('woff2')}
  html, body { overflow: visible !important; height: auto !important; position: static !important; }
  iframe, ins, video, [id^="google_ads"], [id^="div-gpt"], [class*="ad-slot"], [class*="AdSlot"], [class*="advert"],
  [data-ad], [data-ad-unit], [class*="taboola"], [id*="taboola"], [class*="outbrain"] { display:none !important; }
  *:focus, *:focus-visible { outline: none !important; }
  .x-mark { outline: 2px solid var(--c) !important; outline-offset: 4px; border-radius: 3px; }
  .x-tr { display:block; width:fit-content; max-width:100%; margin:12px 0 14px; padding:6px 10px 7px; border-radius:6px; box-sizing:border-box;
          background: rgba(255,255,255,0.3); -webkit-backdrop-filter: blur(1.5px); backdrop-filter: blur(1.5px);
          color: var(--c); font: 600 15px/1.45 'PretendardX', sans-serif; letter-spacing:-0.2px; white-space:normal; text-align:left; }
  .x-ln { position:absolute; white-space:nowrap; padding:0 4px; border-radius:4px; pointer-events:none;
          background: rgba(255,255,255,0.3); -webkit-backdrop-filter: blur(1.5px); backdrop-filter: blur(1.5px);
          color: var(--c); font: 600 var(--fs)/1.25 'PretendardX', sans-serif; letter-spacing:-0.3px; }
`;
(async () => {
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const ctx = await browser.newContext({
    viewport: { width: 360, height: 780 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, bypassCSP: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    locale: 'en-US', timezoneId: 'America/New_York',
  });
  await ctx.route('**/__ccfont/semibold.woff2', r => r.fulfill({ path: path.join(fontdir, 'Pretendard-SemiBold.woff2'), contentType: 'font/woff2' }));
  for (const [name, s] of Object.entries(spec)) {
    if (only.length && !only.includes(name)) continue;
    const page = await ctx.newPage();
    await page.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    // dismiss cookie/consent dialogs by clicking a decline/continue/accept button when one is visible
    for (const re of [/continue without agreeing/i, /reject all/i, /^(accept|agree)/i]) {
      const b = page.getByRole('button', { name: re }).or(page.getByRole('link', { name: re })).first();
      if (await b.isVisible().catch(() => false)) { await b.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(1500); break; }
    }
    // scroll through once so lazy images load, then back to top
    for (let y = 0; y < (s.h || 2400); y += 500) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(250); }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.addStyleTag({ content: CSS + (s.hide || []).map(h => `${h}{display:none !important}`).join('\n') });
    const info = await page.evaluate(([marks, COLORS]) => {
      // drop overlays: anything fixed/sticky (cookie banners, sticky headers, floating players)
      document.querySelectorAll('body *').forEach(e => {
        const cs = getComputedStyle(e);
        if ((cs.position === 'fixed' || cs.position === 'sticky') && !e.querySelector('h1, article'))
          e.style.setProperty('display', 'none', 'important');
      });
      const missing = [];
      for (const m of marks) {
        const cands = [...document.querySelectorAll(m.tag || 'h1,h2,p,li,blockquote,figcaption')]
          .filter(e => e.innerText && e.innerText.includes(m.text) && e.getBoundingClientRect().height > 0);
        cands.sort((a, b) => a.innerText.length - b.innerText.length);
        const el = cands[0];
        if (!el) { missing.push(m.text); continue; }
        el.classList.add('x-mark'); el.style.setProperty('--c', COLORS[m.color]);
        el.dataset.kind = m.id || m.text.slice(0, 12);
        if (m.lines) {
          // interlinear: open up the line spacing, then put the Korean for each English line right under it
          const fs = parseFloat(getComputedStyle(el).fontSize);
          const kfs = m.fs || 17;
          el.style.setProperty('line-height', Math.round(fs * 1.2 + kfs * 1.25 - 2) + 'px', 'important');
          el.style.position = 'relative';
          el.style.paddingBottom = Math.round(kfs * 0.9) + 'px';
          const words = [];
          const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          while (walk.nextNode()) {
            const n = walk.currentNode; const re = /\S+/g; let mm;
            while ((mm = re.exec(n.data))) {
              const r = document.createRange(); r.setStart(n, mm.index); r.setEnd(n, mm.index + mm[0].length);
              const b = r.getClientRects()[0]; if (b) words.push({ w: mm[0], b });
            }
          }
          const lines = [];
          for (const { w, b } of words) {
            const L = lines.find(l => Math.abs(l.top - b.top) < 4);
            if (L) { L.text += ' ' + w; L.left = Math.min(L.left, b.left); L.bottom = Math.max(L.bottom, b.bottom); }
            else lines.push({ text: w, top: b.top, bottom: b.bottom, left: b.left });
          }
          lines.sort((a, b) => a.top - b.top);
          const eb = el.getBoundingClientRect();
          lines.forEach((l, i) => {
            if (!m.lines[i]) return;
            const t = document.createElement('div'); t.className = 'x-ln'; t.textContent = m.lines[i];
            t.style.setProperty('--c', COLORS[m.color]); t.style.setProperty('--fs', kfs + 'px');
            t.style.left = (l.left - eb.left - 4) + 'px'; t.style.top = (l.bottom - eb.top - 3) + 'px';
            el.appendChild(t);
          });
          missing.push('LINES ' + JSON.stringify(lines.map(l => l.text)));
        }
        if (m.tr) {
          const t = document.createElement('div'); t.className = 'x-tr'; t.style.setProperty('--c', COLORS[m.color]); t.textContent = m.tr;
          t.dataset.kind = (m.id || m.text.slice(0, 12)) + '-tr';
          if (m.pos === 'before') el.parentNode.insertBefore(t, el); else el.insertAdjacentElement('afterend', t);
        }
      }
      return { missing };
    }, [s.marks || [], COLORS]);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1000);
    const rects = await page.evaluate(() => {
      const r = {}; document.querySelectorAll('[data-kind]').forEach(e => {
        const b = e.getBoundingClientRect(); r[e.dataset.kind] = [Math.round((b.top + scrollY) * 3), Math.round((b.bottom + scrollY) * 3)]; });
      return r; });
    const h = Math.min(s.h || 2400, await page.evaluate(() => document.documentElement.scrollHeight));
    await page.screenshot({ path: path.join(out, name + '.png'), clip: { x: 0, y: 0, width: 360, height: h }, fullPage: true });
    console.log(name, JSON.stringify({ h: h * 3, ...info, rects }));
    await page.close();
  }
  await browser.close();
})();
