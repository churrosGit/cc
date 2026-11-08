"""List DC mobile gallery posts (title, date/time, nick, views, comments, url), optionally filtered by keyword regex."""
import re, subprocess, sys, html, urllib.parse
UA = "Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"
gall, pages, kw = sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ''
search = sys.argv[4] if len(sys.argv) > 4 else ''
pat = re.compile(kw, re.I) if kw else None
item = re.compile(r'<a href="(https://m\.dcinside\.com/board/[^"#]+)" class="lt">.*?<span class="subjectin">(.*?)</span>.*?'
                  r'<ul class="ginfo ">\s*(?:<li\s*>([^<]*)</li>)?\s*<li class="list-nick">(.*?)<span.*?</li>\s*<li>([^<]*)</li>\s*<li>조회 (\d+)</li>.*?'
                  r'<span class="ct ">(\d+)</span>', re.S)
for p in range(1, pages + 1):
    q = {'page': p}
    if search:
        q.update({'s_type': 'subject_m', 'serval': search})
    url = f"https://m.dcinside.com/board/{gall}?" + urllib.parse.urlencode(q)
    h = subprocess.run(['curl', '-sS', '-m', '25', '-A', UA, url], capture_output=True, text=True).stdout
    for m in item.finditer(h):
        link, title, head, nick, when, views, cmts = m.groups()
        title = html.unescape(re.sub('<[^>]+>', '', title)).strip()
        if pat and not pat.search(title):
            continue
        print(f"{when}\t{views}v {cmts}c\t{title}\t{link}")
