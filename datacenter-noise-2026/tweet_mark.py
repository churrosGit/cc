"""Mark the user's tweet screenshot: blur author name/avatar and insert a red note under line 1
("미국 민주당"), styled like the article translations: red Pretendard Medium on a see-through
background that hugs the glyphs (30% white over the black tweet background), no box.
Usage: python3 tweet_mark.py <screenshot.png> <out.png>"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

src, out = sys.argv[1:3]
FONT = __file__.rsplit('/', 2)[0] + '/shorts-kit/fonts/Pretendard-Medium.woff2'
RED = (227, 38, 43)
BG = (76, 76, 76)  # rgba(255,255,255,0.3) over black
im = Image.open(src).convert('RGB')
W = im.width
# blur avatar and display name + handle (keep "· 7시")
for box in [(14, 34, 158, 180), (162, 40, 792, 98)]:
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(15)), box[:2])
# line 1 = rows 102..141; the note goes right under it
CUT = 146
top, rest = im.crop((0, 0, W, CUT)), im.crop((0, CUT, W, im.height))
f = ImageFont.truetype(FONT, 51)
lines = ['※ 우리나라가 아니라 미국 민주당', '(11월 3일 미국 중간선거)']
lh, x = 66, 170
band = Image.new('RGB', (W, lh * len(lines) + 14), (0, 0, 0))
bd = ImageDraw.Draw(band)
for i, t in enumerate(lines):
    l, tt, r, b = bd.textbbox((x, 6 + i * lh), t, font=f)
    bd.rectangle((l, tt, r - 1, b - 1), fill=BG)
    bd.text((x, 6 + i * lh), t, font=f, fill=RED)
o = Image.new('RGB', (W, top.height + band.height + rest.height))
o.paste(top, (0, 0)); o.paste(band, (0, top.height)); o.paste(rest, (0, top.height + band.height))
o.save(out)
print(out, o.size, 'text end y =', top.height + band.height + (253 - CUT))
