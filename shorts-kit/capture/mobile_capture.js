// Mobile 360px capture of a post's top area, ads hidden, author names blurred.
// node mcap2.js <outdir> <cssHeight> <name>=<url> ...   -> <name>.png (1080 x cssHeight*3)
const { chromium } = require('playwright');
const path = require('path');
const [out, hStr, ...args] = process.argv.slice(2);
const H = +hStr;
const CSS = `
  #auto_picture_area, .adv-groupno, [class*="adv-group"], section.clkhigh, .pwlink, ins, iframe,
  shreddit-comments-page-ad, shreddit-ad-post, [class*="promotedlink"] { display: none !important; }
  .x-blur { filter: blur(5px) !important; }
`;
(async () => {
  const browser = await chromium.launch({ proxy: { server: process.env.HTTPS_PROXY } });
  const ctx = await browser.newContext({
    viewport: { width: 360, height: 780 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    locale: 'ko-KR', timezoneId: 'Asia/Seoul',
  });
  for (const a of args) {
    const i = a.indexOf('='); const name = a.slice(0, i), url = a.slice(i + 1);
    const page = await ctx.newPage();
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(3500);
      await page.addStyleTag({ content: CSS });
      await page.evaluate(() => {
        // DC: nickname/IP line in the post header
        document.querySelectorAll('.gallview-tit-box .ginfo2 li:first-child, .gallview-tit-box .ginfo2 .nick, .gallview-tit-box [class*="nick"]').forEach(e => e.classList.add('x-blur'));
        // Reddit: author links / names in the post credit bar
        document.querySelectorAll('#pdp-credit-bar a[href*="/user/"], #pdp-credit-bar [slot="authorName"], #pdp-credit-bar faceplate-hovercard').forEach(e => e.classList.add('x-blur'));
        window.scrollTo(0, 0);
      });
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(out, name + '.png'), clip: { x: 0, y: 0, width: 360, height: H } });
      console.log(name, 'ok');
    } catch (e) { console.log(name, 'ERR', e.message.split('\n')[0]); }
    await page.close();
  }
  await browser.close();
})();
