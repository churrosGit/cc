"""Prepare the user's screenshots as 1080-wide captures.
Usage: python3 mark_images.py <capDir>
- tw1.png: the tweet with avatar and display name/handle blurred
- fig4.png: paper Figure 4 (heading + charts) with red Korean under the heading and the panel captions
- golf.png: paper Figure 6 (golf courses) with red Korean heading and legend translation
Red Korean = Pretendard Medium, same red as the article translations."""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

cap = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(here), 'shorts-kit', 'fonts', 'Pretendard-Medium.woff2')
RED = (227, 38, 43)
W = 1080

# tweet: blur avatar and name + handle (keep "· 1일")
im = Image.open(os.path.join(here, 'src', 'tweet.png')).convert('RGB')
for box in [(14, 22, 158, 158), (165, 22, 745, 84)]:
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(15)), box[:2])
im.save(os.path.join(cap, 'tw1.png'))


def text(d, xy, t, fs, anchor='la'):
    d.text(xy, t, font=ImageFont.truetype(FONT, fs), fill=RED, anchor=anchor)


# Figure 4: heading 9-40, charts 181-354, captions 417-448 (image is 1046 wide)
src = Image.open(os.path.join(here, 'src', 'fig4.jpg')).convert('RGB').crop((0, 0, 1046, 510))
im = Image.new('RGB', (W, 510), 'white'); ox = (W - 1046) // 2; im.paste(src, (ox, 0))
d = ImageDraw.Draw(im)
text(d, (ox + 12, 62), '연간 물 소비량 (단위: 10억 갤런)', 40)
text(d, (ox + 12, 114), '2024년: 약 190억~230억 갤런', 40)
for cx, t in [(199, '저성장'), (534, '중간 성장'), (869, '고성장')]:
    text(d, (ox + cx, 462), t, 36, 'ma')
im.save(os.path.join(cap, 'fig4.png'))

# Figure 6 (golf): heading 42-84, chart 227-944 (image is 1038 wide); a red band goes between them
src = Image.open(os.path.join(here, 'src', 'golf.png')).convert('RGB')
top, rest = src.crop((0, 0, 1038, 92)), src.crop((0, 205, 1038, 960))
band = 168
im = Image.new('RGB', (W, top.height + band + rest.height), 'white'); ox = (W - 1038) // 2
im.paste(top, (ox, 0)); im.paste(rest, (ox, top.height + band))
d = ImageDraw.Draw(im)
text(d, (ox + 36, 100), '부록 I  미국 골프장 물 사용량 (단위: 100만 갤런)', 38)
text(d, (ox + 36, 154), '수돗물(보라) · 재활용수(주황) · 지하수(초록)', 36)
text(d, (ox + 36, 202), '강·하천(노랑) · 운하(분홍) · 호수·연못(파랑)', 36)
im.save(os.path.join(cap, 'golf.png'))
for n in ['tw1', 'fig4', 'golf']:
    print(n, Image.open(os.path.join(cap, n + '.png')).size)
