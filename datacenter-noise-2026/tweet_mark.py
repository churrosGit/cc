"""Mark the user's tweet screenshot: blur author name/avatar, red box on line 1, insert a red note below it.
Usage: python3 tweet_mark.py <screenshot.png> <out.png>"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

src, out = sys.argv[1:3]
FONT = __file__.rsplit('/', 2)[0] + '/shorts-kit/fonts/Pretendard-SemiBold.woff2'
RED = (227, 38, 43)
im = Image.open(src).convert('RGB')
W = im.width
# blur avatar and display name + handle (keep "· 7시")
for box in [(14, 34, 158, 180), (162, 40, 792, 98)]:
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(15)), box[:2])
# line 1 = rows 102..141, x 170..600
L1_BOTTOM, CUT = 141, 152
top = im.crop((0, 0, W, CUT))
rest = im.crop((0, CUT, W, im.height))
d = ImageDraw.Draw(top)
d.rounded_rectangle((157, 89, 613, 151), radius=9, outline=RED, width=4)
# note band
f = ImageFont.truetype(FONT, 45)
lines = ['※ 우리나라가 아니라 미국 민주당', '(11월 3일 미국 중간선거)']
lh = 66
bw = max(f.getlength(t) for t in lines) + 60
bh = lh * len(lines) + 36
gap_top, gap_bot = 27, 30
band = Image.new('RGB', (W, gap_top + bh + gap_bot), (0, 0, 0))
bd = ImageDraw.Draw(band)
bd.rounded_rectangle((157, gap_top, 157 + bw, gap_top + bh), radius=18, fill=RED)
for i, t in enumerate(lines):
    bd.text((157 + 30, gap_top + 18 + i * lh + 4), t, font=f, fill='white')
o = Image.new('RGB', (W, top.height + band.height + rest.height))
o.paste(top, (0, 0)); o.paste(band, (0, top.height)); o.paste(rest, (0, top.height + band.height))
o.save(out)
print(out, o.size, 'text end y =', top.height + band.height + (253 - CUT))
