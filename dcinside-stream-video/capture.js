const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({
    viewport: { width: 660, height: 338 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    locale: 'ko-KR'
  });
  const page = await ctx.newPage();
  let dcconOk = 0, dcconFail = 0;
  await page.route(/dcimg8\.dcinside\.co\.kr\/viewimage/, r => r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync('../body_img.png') }));
  // dcimg5.dcinside.com is not reachable here; the same dccon is served by dcimg1/dcimg2.dcinside.com
  // dcimg5.dcinside.com is not reachable from here; the same dccons were prefetched from dcimg1/dcimg2.dcinside.com
  await page.route(/dcimg5\.dcinside\.com\/dccon/, r => {
    const no = new URL(r.request().url()).searchParams.get('no');
    const f = '../dccons/' + no + '.bin';
    if (fs.existsSync(f)) { dcconOk++; return r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(f) }); }
    dcconFail++;
    return r.fulfill({ status: 200, contentType: 'image/svg+xml', body: fs.readFileSync('dccon.svg') });
  });
  await page.route(/(addc\.dcinside|netinsight|pstatic|wcs\.naver|googletag|google-analytics|kakaocdn|jsdelivr)/, r => r.abort());
  await page.goto('https://m.dcinside.com/board/thesingularity/1516221?recommend=1', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(2500);
  for (let y=0;y<4500;y+=250){ await page.evaluate(y=>window.scrollTo(0,y),y); await page.waitForTimeout(150); }
  await page.waitForTimeout(4000); await page.evaluate(()=>window.scrollTo(0,0)); await page.waitForTimeout(1000);
  // hide floating/fixed bits & tooltips
  await page.evaluate(()=>{
    for (const e of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(e);
      if (cs.position==='fixed' || cs.position==='sticky') e.style.setProperty('display','none','important');
    }
    for (const e of document.querySelectorAll('body *')) {
      const t=(e.innerText||'').trim();
      if (t.startsWith("'ㅇㅇ'는 갤러리에서 권장하는") && e.children.length<6) e.style.setProperty('visibility','hidden','important');
      if (/^댓글\s*▼?$/.test(t) && e.closest('.thum-txtin') && !e.querySelector('img')) e.style.setProperty('display','none','important');
    }
  });
  await page.waitForTimeout(500);
  const layout = await page.evaluate(()=>{
    const SY=scrollY;
    const R=r=>({x:r.left,y:r.top+SY,w:r.width,h:r.height});
    function textRects(sub, minY=0, root=document.body){
      const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
      let n; while((n=w.nextNode())){
        const i=n.data.indexOf(sub); if(i<0) continue;
        const rg=document.createRange(); rg.setStart(n,i); rg.setEnd(n,i+sub.length);
        const rs=[...rg.getClientRects()].map(R).filter(r=>r.w>0);
        if(rs.length && rs[0].y>=minY) {
          // merge rects on same line
          const lines=[]; for(const r of rs){const l=lines.find(L=>Math.abs(L.y-r.y)<4); if(l){const x2=Math.max(l.x+l.w,r.x+r.w); l.x=Math.min(l.x,r.x); l.w=x2-l.x;} else lines.push({...r});}
          return lines;
        }
      }
      return null;
    }
    const out={};
    out.docH=document.documentElement.scrollHeight;
    out.gallname=textRects('특이점이 온다');
    out.title=textRects('이제 AECI 점수는 2개월마다 2배가 되는 중');
    out.malmeori=textRects('정보]');
    out.date=textRects('2026.11.07 21:58');
    out.views=textRects('조회수');
    const img=[...document.querySelectorAll('img')].find(i=>(i.src||'').includes('dcimg8')||(i.dataset.original||'').includes('dcimg8'));
    out.img=R(img.getBoundingClientRect());
    out.bodytext=textRects('우주 끝까지 날아올라서 사람들을 구해다오');
    out.silbe=textRects('실베추');
    out.cmtHead=textRects('댓글', 1000, document.querySelector('.all-comment:not(.list)')||document.body);
    out.comments=[...document.querySelectorAll('.all-comment-lst > li')].map(li=>{
      const texts=[]; const w=document.createTreeWalker(li,NodeFilter.SHOW_TEXT); let n;
      while((n=w.nextNode())){ const t=n.data.trim(); if(!t) continue; const rg=document.createRange(); rg.selectNodeContents(n); const rs=[...rg.getClientRects()].map(R).filter(r=>r.w>0); if(rs.length) texts.push({t, r:rs[0]}); }
      const imgs=[...li.querySelectorAll('img')].map(i=>R(i.getBoundingClientRect())).filter(r=>r.w>20);
      return {r:R(li.getBoundingClientRect()), texts, imgs};
    });
    // stats line elements
    const stats=[...document.querySelectorAll('.gall-thum-btm li, .gall-thum-btm span')].slice(0,0);
    return out;
  });
  // locate '추천 21' and '댓글 7' near views line
  layout.reco = await page.evaluate(()=>{const SY=scrollY;const r=[];for(const e of document.querySelectorAll('li,span,a,button')){const t=(e.innerText||'').replace(/\s+/g,' ').trim(); if(/^(추천 \d+|댓글 \d+|조회수 \d+)$/.test(t)){const b=e.getBoundingClientRect(); if(b.top+SY<400) r.push({t,x:b.left,y:b.top+SY,w:b.width,h:b.height});}} return r;});
  layout.star = await page.evaluate(()=>{const SY=scrollY;const r=[];for(const e of document.querySelectorAll('*')){const t=(e.innerText||'').replace(/\s+/g,' ').trim(); if(t==='개념'){const b=e.getBoundingClientRect(); r.push({x:b.left,y:b.top+SY,w:b.width,h:b.height});}} return r;});
  console.log('dccon ok', dcconOk, 'fail', dcconFail);
  fs.writeFileSync('layout.json', JSON.stringify(layout,null,1));
  await page.screenshot({ path: 'page3x.png', fullPage: true });
  await b.close();
})();
