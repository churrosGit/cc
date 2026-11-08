// Scroll a subreddit's /new/ feed and dump posts newer than a cutoff: node rnew.js <sub> <cutoffISO> [maxScrolls]
const { chromium } = require('playwright');
(async () => {
  const [sub, cutoff, maxS] = process.argv.slice(2);
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const page = await browser.newPage({ viewport: { width: 360, height: 780 }, isMobile: true, userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36' });
  await page.goto(`https://www.reddit.com/r/${sub}/new/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);
  const seen = new Map();
  for (let i = 0; i < (+maxS || 60); i++) {
    const posts = await page.$$eval('shreddit-post', els => els.map(e => ({
      t: e.getAttribute('created-timestamp'), title: e.getAttribute('post-title'),
      link: e.getAttribute('permalink'), score: e.getAttribute('score'), c: e.getAttribute('comment-count'),
      flair: (e.querySelector('shreddit-post-flair') || {}).innerText || ''
    })));
    posts.forEach(p => seen.set(p.link, p));
    const oldest = posts.map(p => p.t).sort()[0];
    if (oldest && new Date(oldest) < new Date(cutoff)) break;
    await page.evaluate(() => window.scrollBy(0, 5000));
    await page.waitForTimeout(1500);
  }
  for (const p of [...seen.values()].sort((a, b) => (a.t < b.t ? 1 : -1))) {
    if (new Date(p.t) >= new Date(cutoff))
      console.log(`${p.t.slice(0, 16)}\t${p.score}↑ ${p.c}c\t${(p.flair || '').replace(/\s+/g, ' ').trim()}\t${p.title}\thttps://www.reddit.com${p.link}`);
  }
  await browser.close();
})();
