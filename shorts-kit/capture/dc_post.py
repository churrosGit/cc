"""Print title, date and body text of DC mobile posts given gallery/id pairs."""
import re, subprocess, sys, html
UA = "Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"
for gid in sys.argv[1:]:
    url = f"https://m.dcinside.com/board/{gid}"
    h = subprocess.run(['curl', '-sS', '-m', '25', '-A', UA, url], capture_output=True, text=True).stdout
    t = re.search(r'<span class="tit">(.*?)</span>', h, re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip() if t else '?'
    d = re.search(r'<li>(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})</li>', h)
    b = re.search(r'<div class="thum-txtin">(.*?)</div>\s*(?:<!--|<div)', h, re.S)
    body = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', b.group(1)))).strip() if b else ''
    print(f"[{gid}] {d.group(1) if d else '?'} | {t}\n    {body[:260]}\n")
