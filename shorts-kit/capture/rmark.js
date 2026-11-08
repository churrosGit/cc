// Capture Reddit posts at 360px mobile with thin red/green boxes around key parts and Korean translations inserted below.
// node rmark.js <marks.json> <outdir> [names...]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [specFile, out, ...only] = process.argv.slice(2);
const fontdir = path.join(__dirname, '..', 'fonts');
const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const COLORS = { red: '#e3262b', green: '#14964a' };
const CSS = `
  @font-face{font-family:'PretendardX';font-weight:600;src:url(/__ccfont/semibold.woff2) format('woff2')}
  #auto_picture_area, ins, iframe, shreddit-comments-page-ad, shreddit-ad-post, [class*="promotedlink"] { display:none !important; }
  .x-blur { filter: blur(5px) !important; }
  .x-mark { outline: 1.5px solid var(--c) !important; outline-offset: 4px; border-radius: 3px; }
  .x-tr { display:block; width:fit-content; max-width:100%; margin:9px 0 12px; padding:6px 10px 7px; border-radius:6px;
          background: var(--c); color:#fff; font: 600 15px/1.45 'PretendardX', sans-serif; letter-spacing:-0.2px; white-space:normal; }
`;
(async () => {
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const ctx = await browser.newContext({
    viewport: { width: 360, height: 780 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, bypassCSP: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    locale: 'ko-KR', timezoneId: 'Asia/Seoul',
  });
  await ctx.route('**/__ccfont/semibold.woff2', r => r.fulfill({ path: path.join(fontdir, 'Pretendard-SemiBold.woff2'), contentType: 'font/woff2' }));
  const result = {};
  for (const [name, s] of Object.entries(spec)) {
    if (only.length && !only.includes(name)) continue;
    const page = await ctx.newPage();
    await page.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3500);
    await page.addStyleTag({ content: CSS });
    const info = await page.evaluate(([marks, COLORS]) => {
      document.querySelectorAll('#pdp-credit-bar a[href*="/user/"], #pdp-credit-bar faceplate-hovercard').forEach(e => e.classList.add('x-blur'));
      const post = document.querySelector('shreddit-post');
      const body = post.querySelector('[id$="-post-rtjson-content"]');
      if (body) { body.style.maxHeight = 'none'; body.style.overflow = 'visible'; }
      post.querySelectorAll('shreddit-post-text-body, [id$="-post-rtjson-content"]').forEach(e => { e.style.overflow = 'visible'; e.style.maxHeight = 'none'; });
      post.querySelectorAll('*').forEach(e => { const cs = getComputedStyle(e);
        if (cs.maskImage && cs.maskImage !== 'none') { e.style.maskImage = 'none'; e.style.webkitMaskImage = 'none'; }
        if (/gradient/.test(cs.backgroundImage) && e.getBoundingClientRect().height < 200 && !e.closest('table')) e.style.display = 'none'; });
      const missing = []; let bottom = 0;
      for (const [kind, match, color, tr] of marks) {
        let el = null;
        if (kind === 'title') el = post.querySelector('h1[id^="post-title"]');
        if (kind === 'p') el = [...post.querySelectorAll('p')].find(p => p.innerText.includes(match));
        if (kind === 'table') el = post.querySelector('table');
        if (kind === 'media') el = post.querySelector('shreddit-player-2, shreddit-player, gallery-carousel, shreddit-aspect-ratio, figure, img.media-lightbox-img');
        if (!el) { missing.push(kind + ':' + match); continue; }
        el.classList.add('x-mark'); el.style.setProperty('--c', COLORS[color]);
        const t = document.createElement('div'); t.className = 'x-tr'; t.style.setProperty('--c', COLORS[color]); t.textContent = tr;
        if (el.slot) t.slot = el.slot;
        if (kind === 'title') { el.style.margin = '0 10px'; el.style.padding = '3px 6px'; el.style.outlineOffset = '0px'; t.style.marginLeft = '10px'; t.style.marginRight = '10px'; }
        el.dataset.kind = kind; t.dataset.kind = kind + '-tr';
        if (kind === 'media' || kind === 'table') el.parentNode.insertBefore(t, el); else el.insertAdjacentElement('afterend', t);
      }
      window.scrollTo(0, 0);
      document.querySelectorAll('.x-mark, .x-tr').forEach(e => { if (!e.closest('[class*="x-skip"]')) bottom = Math.max(bottom, e.getBoundingClientRect().bottom); });
      const rects = {}; document.querySelectorAll('[data-kind]').forEach(e => { const b = e.getBoundingClientRect(); rects[e.dataset.kind] = [Math.round(b.top), Math.round(b.bottom)]; });
      return { missing, bottom: Math.ceil(bottom), rects };
    }, [s.marks, COLORS]);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(800);
    Object.assign(info, await page.evaluate(() => { const rects = {}; let bottom = 0;
      document.querySelectorAll('[data-kind]').forEach(e => { const b = e.getBoundingClientRect(); rects[e.dataset.kind] = [Math.round(b.top), Math.round(b.bottom)]; bottom = Math.max(bottom, b.bottom); });
      return { rects, bottom: Math.ceil(bottom) }; }));
    const h = Math.min(Math.max(440, info.bottom + 20), 900);
    await page.screenshot({ path: path.join(out, name + '.png'), clip: { x: 0, y: 0, width: 360, height: h } });
    result[name] = { h: h * 3, ...info };
    console.log(name, JSON.stringify(result[name]));
    await page.close();
  }
  await browser.close();
})();
