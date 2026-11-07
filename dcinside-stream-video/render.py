import json, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H = 660, 372          # output size (16:9 landscape, 660px wide)
SS = 2                   # supersampling factor
BAR = 34                 # browser address bar height (output px)
VH = H - BAR             # viewport height
FPS = 30
SRC_SCALE = 3            # page screenshot DPR
URL = "m.dcinside.com/board/thesingularity/1516221?recommend=1"

FONT_DIR = "../fontpkg/"
f_cap = ImageFont.truetype(FONT_DIR + "NanumGothicBold.ttf", 16 * SS)
f_url = ImageFont.truetype(FONT_DIR + "NanumGothic.ttf", 12 * SS)

PADX = 60
_pg = Image.open("page3x.png").convert("RGB")
page = Image.new("RGB", (_pg.size[0] + 2 * PADX * SRC_SCALE, _pg.size[1]), (255, 255, 255))
page.paste(_pg, (PADX * SRC_SCALE, 0))
L = json.load(open("layout.json"))
DOC_H = page.size[1] / SRC_SCALE
IMG = L["img"]

def I(ix, iy):                      # tweet-image natural px -> page css px
    return (IMG["x"] + ix, IMG["y"] + iy)
def IR(x1, y1, x2, y2):
    a, b = I(x1, y1); c, d = I(x2, y2)
    return (a, b, c, d)
def R(r, pad=0):
    return (r["x"] - pad, r["y"] - pad, r["x"] + r["w"] + pad, r["y"] + r["h"] + pad)
def LC(left, cy, z):
    return (left + 330 / z, cy, z)
def ctr(rect):
    return ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)

C = L["comments"]
def ctext(i, t):
    for x in C[i]["texts"]:
        if x["t"] == t: return R(x["r"])
    raise KeyError(t)

def ease(t):  # easeInOutCubic
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

RED = (236, 38, 38)
BLUE = (30, 110, 255)
YEL = (255, 232, 64)
PINK = (255, 170, 200)
CYAN = (150, 225, 255)
GRN = (170, 245, 150)

# ---------------------------------------------------------------- script
# cam = (cx, cy, zoom) in page css px.  marks: (kind, data, start, dur, opts)
title_rect = R(L["title"][0]); mal = R(L["malmeori"][0])
stats = [x for x in L["reco"]]
st = {x["t"].split()[0]: (x["x"], x["y"], x["x"] + x["w"], x["y"] + x["h"]) for x in stats}

P1 = [IR(13, 84, 573, 106), IR(13, 108, 502, 130)]
P2 = [IR(13, 154, 570, 176), IR(13, 178, 318, 200)]
Q12 = [IR(28, 726, 500, 744), IR(28, 750, 566, 768)]
Q34 = [IR(28, 773, 560, 791), IR(28, 797, 249, 815)]
ENG = [IR(27, 824, 532, 840), IR(27, 842, 435, 858)]
GPT2 = I(97, 554); M4 = I(531, 298)

segs = [
 dict(cam=(330, 169, 1.0), cur=ctr(R(L["gallname"][0])),
      text="자, 오늘 읽어볼 글은 '특이점이 온다' 갤러리 개념글입니다",
      marks=[("circle", R(L["gallname"][0], 4), 0.7, 0.6, {})]),
 dict(cam=LC(6, 212, 1.8), cur=None,
      text="제목 — \"이제 AECI 점수는 2개월마다 2배가 되는 중\"",
      marks=[("hl", [ (mal[0], mal[1], title_rect[2], mal[3]) ], 0.3, 1.6, {})]),
 dict(cam=LC(6, 238, 1.8), cur=ctr(st["추천"]),
      text="11월 7일 밤 9시 58분 글. 조회수 1900여, 추천 21, 댓글 7개",
      marks=[("under", R(L["date"][0]), 0.2, 0.5, {}),
             ("box", (st["조회수"][0]-3, st["조회수"][1]-3, st["댓글"][2]+3, st["댓글"][3]+3), 0.9, 0.7, {})]),
 dict(cam=LC(18, I(0, 60)[1], 1.7), cur=ctr(IR(58, 5, 192, 45)),
      text="본문은 니콜라 저코비치(@nikolaj2030)의 트윗 번역 캡처예요",
      marks=[("circle", IR(56, 4, 196, 48), 0.3, 0.6, {})]),
 dict(cam=LC(10, I(0, 112)[1], 1.12), cur=None,
      text="\"그래프에서 추출된 AECI 점수는, 시간 지평선이 두 배가 되는 시간이 이제 약 2개월 정도라는 걸 암시한다\"",
      marks=[("hl", P1, 0.2, 2.6, {})]),
 dict(cam=LC(10, I(0, 112)[1], 1.12), cur=ctr(IR(270, 108, 332, 130)), keep_prev=True,
      text="그리고 Model 4의 TH(타임 호라이즌)는 약 240시간 — 사람 기준 열흘짜리 작업이라는 뜻이죠",
      marks=[("under", IR(440, 85, 506, 106), 0.1, 0.4, {}),
             ("circle", IR(268, 108, 334, 130), 0.6, 0.6, {})]),
 dict(cam=LC(10, I(0, 168)[1], 1.12), cur=None,
      text="단, 본인도 \"이 증거는 꽤 약하다\"고 단서를 답니다. 이렇게 큰 숫자까지 1:1로 맞아떨어지는지는 불분명하다고요",
      marks=[("hl", P2, 0.2, 2.2, {"color": PINK}),
             ("box", IR(121, 154, 205, 178), 2.5, 0.6, {})]),
 dict(cam=(330, I(0, 458)[1], 1.0), cur=I(60, 420),
      text="그래프 보시죠. 세로축은 로그 스케일이라 한 칸 올라갈 때마다 몇 배씩 뜁니다",
      marks=[("box", IR(42, 300, 80, 565), 0.4, 0.8, {}),
             ("arrow", (I(140, 470), I(84, 420)), 1.4, 0.5, {})]),
 dict(cam=LC(50, I(0, 330)[1], 2.1), cur=None,
      text="2019~2023년엔 260일마다 2배 → 소넷 4.5까지 92일마다 2배 → Opus 4.5 이후엔 56일마다 2배!",
      marks=[("hl", [IR(84, 311, 232, 325)], 0.2, 0.8, {"color": YEL}),
             ("hl", [IR(84, 325, 247, 339)], 1.5, 0.8, {"color": CYAN}),
             ("hl", [IR(84, 339, 247, 353)], 2.8, 0.8, {"color": PINK})]),
 dict(cam=LC(20, I(0, 500)[1], 1.6), cur=GPT2, cam2=(2.0, LC(150, I(0, 380)[1], 1.25), 1.3),
      text="GPT-2는 고작 3초짜리 작업이었는데, 오른쪽 위 Model 4는 100시간 선을 훌쩍 넘었습니다",
      marks=[("circle", (GPT2[0]-14, GPT2[1]-12, GPT2[0]+34, GPT2[1]+16), 0.2, 0.5, {}),
             ("arrow", ((GPT2[0]+40, GPT2[1]-14), (M4[0]-28, M4[1]+14)), 1.6, 1.8, {"color": BLUE}),
             ("circle", IR(498, 270, 560, 345), 3.5, 0.6, {})]),
 dict(cam=(470, I(0, 335)[1], 1.9), cur=I(470, 395),
      text="특히 Opus 4.5 이후 주황색 구간, 기울기가 확 가팔라지죠",
      marks=[("box", IR(450, 338, 494, 368), 0.2, 0.5, {}),
             ("arrow", (I(505, 395), I(552, 300)), 0.9, 0.7, {})]),
 dict(cam=LC(20, I(0, 712)[1], 1.6), cur=ctr(IR(55, 693, 100, 718)),
      text="아래는 METR 공식 계정의 답글입니다",
      marks=[("circle", IR(26, 690, 288, 721), 0.2, 0.6, {})]),
 dict(cam=LC(10, I(0, 770)[1], 1.12), cur=None,
      text="\"2025년 10월 이후, 앤트로픽 모델의 AECI 점수는 이전 속도의 1.9배로 성장했다\" (95% 구간 1.5~2.8배)",
      marks=[("hl", Q12, 0.2, 2.4, {}),
             ("circle", IR(338, 748, 384, 770), 2.8, 0.5, {})]),
 dict(cam=LC(10, I(0, 795)[1], 1.12), cur=None,
      text="다만 분석 방식에 따라 추정치가 달라지고, 벤치마크 점수가 실제 능력으로 어떻게 이어지는지는 아직 불분명하다고 선을 긋네요",
      marks=[("hl", Q34, 0.2, 2.2, {"color": GRN})]),
 dict(cam=LC(10, I(0, 842)[1], 1.12), cur=None,
      text="영어 원문 제목도 같은 얘기 — \"2025년 10월 이전 속도의 1.9배\"",
      marks=[("under", IR(364, 822, 521, 835), 0.2, 0.6, {}),
             ("under", IR(26, 838, 110, 850), 0.9, 0.4, {})]),
 dict(cam=LC(4, ctr(R(L["bodytext"][0]))[1], 2.2), cur=None,
      text="그리고 글쓴이의 한마디: \"우주 끝까지 날아올라서 사람들을 구해다오\" ㅋㅋ",
      marks=[("hl", [R(L["bodytext"][0], 1)], 0.2, 1.6, {})]),
 dict(cam=(330, 1396, 1.7), cur=(334, 1398),
      text="개념글 추천 21개, 그중 고정닉 추천이 18개네요",
      marks=[("circle", (262, 1364, 366, 1428), 0.3, 0.7, {})]),
 dict(cam=(330, 1620 + 150, 1.0), cur=ctr(R(L["cmtHead"][0])),
      text="댓글 보러 갑시다. 총 7개",
      marks=[("circle", (R(L["cmtHead"][0], 5)[0], R(L["cmtHead"][0], 5)[1], R(L["cmtHead"][0], 5)[2] + 22, R(L["cmtHead"][0], 5)[3]), 0.3, 0.5, {})]),
 dict(cam=LC(0, 1728, 1.7), cur=None,
      text="첫 댓글 \"다큰낙타\"… 그리고 \"다들 고생했다\"",
      marks=[("hl", [ctext(0, "다큰낙타")], 0.2, 0.7, {}),
             ("hl", [ctext(1, "다들 고생했다")], 1.4, 0.8, {})]),
 dict(cam=LC(0, 1976, 1.05), cur=(120, 1940),
      text="^-^님, 울엄마님은 디시콘으로 반응 — 디시콘 이미지는 녹화 환경에서 로딩이 안 됐어요",
      marks=[("box", (8, 1822, 216, 1930), 0.2, 0.6, {}),
             ("box", (8, 1975, 116, 2082), 0.9, 0.5, {})]),
 dict(cam=LC(0, 2140, 1.8), cur=None,
      text="\"헛수고하셨습니다\"… 냉정하네요 ㅋㅋ",
      marks=[("hl", [ctext(4, "헛수고하셨습니다")], 0.2, 0.8, {"color": PINK})]),
 dict(cam=LC(0, 2262, 1.8), cur=None,
      text="키나루디안마기: \"우주 끝까지면 구조대도 은하급이네 ㅋㅋ\" — 본문 드립을 제대로 받았네요",
      marks=[("hl", [ctext(6, "우주 끝까지면 구조대도 은하급이네 ㅋㅋ")], 0.2, 1.4, {})]),
 dict(cam=LC(0, 2370, 1.2), cur=(70, 2380),
      text="마지막은 SingularityAI님의 디시콘으로 마무리",
      marks=[("box", (8, 2323, 116, 2431), 0.2, 0.6, {})]),
 dict(cam=(330, I(0, 425)[1], 1.0), cur=M4,
      text="두 달마다 2배라는 추세, 진짜 이어질지 지켜봐야겠네요. 오늘은 여기까지!",
      marks=[("circle", IR(498, 270, 560, 345), 0.6, 0.6, {"color": BLUE})]),
]

# ---------------------------------------------------------------- timeline
INTRO = 1.8
def read_time(text):
    return max(2.4, 1.3 + len(text) * 0.085)

t = INTRO
prev_cam = segs[0]["cam"]
for i, s in enumerate(segs):
    cam = s["cam"]
    dist = math.hypot(cam[0] - prev_cam[0], cam[1] - prev_cam[1]) + 260 * abs(math.log(cam[2] / prev_cam[2]))
    camT = 0 if i == 0 else min(1.5, max(0.6, 0.45 + dist / 900))
    s["t0"] = t
    s["arr"] = t + camT
    last_mark = max([m[2] + m[3] for m in s["marks"]] + [0])
    s["t1"] = s["arr"] + max(read_time(s["text"]), last_mark + 1.0)
    s["prev_cam"] = prev_cam
    s["camT"] = camT
    t = s["t1"]
    prev_cam = s["cam2"][1] if "cam2" in s else cam
TOTAL = t + 1.0
for i, s in enumerate(segs):
    nxt = segs[i + 1] if i + 1 < len(segs) else None
    s["mark_end"] = nxt["t1"] if (nxt and nxt.get("keep_prev")) else s["t1"] + 0.25

def cam_at(t):
    if t < segs[0]["t0"]:
        return segs[0]["cam"]
    for s in segs:
        if s["t0"] <= t < s["t1"]:
            a, b, k = s["prev_cam"], s["cam"], 1.0
            if s["camT"] > 0:
                k = ease((t - s["t0"]) / s["camT"])
            if "cam2" in s and t >= s["arr"] + s["cam2"][0]:
                off, c2, du = s["cam2"]
                a, b, k = s["cam"], c2, ease((t - s["arr"] - off) / du)
            z = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * k)
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, z)
    return segs[-1]["cam"]

def clamp_cam(cx, cy, z):
    vw, vh = W / z, VH / z
    if vw >= 660:
        x0 = (660 - vw) / 2
    else:
        x0 = min(max(cx - vw / 2, 0), 660 - vw)
    y0 = min(max(cy - vh / 2, 0), DOC_H - vh)
    return x0, y0, vw, vh

# ---------- cursor path: list of (time, point) keyframes in page coords
cur_keys = [(0.0, (420, 300)), (INTRO, (420, 300))]
for s in segs:
    for kind, data, st_, du, op in s["marks"]:
        if kind == "hl":
            cur_keys.append((s["arr"] + st_, (data[0][0], data[0][3])))
            cur_keys.append((s["arr"] + st_ + du, (data[-1][2], data[-1][3])))
    if s["cur"] is not None:
        cur_keys.append((s["arr"] + 0.05, s["cur"]))
cur_keys.sort(key=lambda k: k[0])

def cursor_at(t):
    prev = cur_keys[0]
    for k in cur_keys:
        if k[0] > t:
            span = k[0] - prev[0]
            if span <= 0: return k[1]
            # move during the last 0.55s before the key (or linear for highlight drags)
            mv = min(span, 0.55)
            u = ease((t - (k[0] - mv)) / mv)
            return (prev[1][0] + (k[1][0] - prev[1][0]) * u, prev[1][1] + (k[1][1] - prev[1][1]) * u)
        prev = k
    return prev[1]

# ---------------------------------------------------------------- drawing helpers
def to_s(p, camr):
    x0, y0, vw, vh = camr
    z = W / vw
    return ((p[0] - x0) * z * SS, BAR * SS + (p[1] - y0) * z * SS)

def stroke(d, pts, color, width, alpha=255):
    if len(pts) < 2: return
    c = color + (alpha,)
    d.line(pts, fill=c, width=width, joint="curve")
    r = width / 2
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=c)

def circle_pts(rect, prog, seed):
    cx, cy = ctr(rect)
    rx = (rect[2] - rect[0]) / 2 * 1.12 + 3
    ry = (rect[3] - rect[1]) / 2 * 1.25 + 3
    total = 2 * math.pi * 1.12
    n = 60
    pts = []
    a0 = -math.pi * 0.62
    for i in range(int(n * prog) + 1):
        a = a0 + total * i / n
        wob = 1 + 0.035 * math.sin(3 * a + seed) + 0.04 * (i / n)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    return pts

def box_pts(rect, prog):
    x1, y1, x2, y2 = rect
    path = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1 - 2)]
    segl = [math.dist(path[i], path[i + 1]) for i in range(4)]
    tot = sum(segl) * prog
    pts = [path[0]]
    for i in range(4):
        if tot >= segl[i]:
            pts.append(path[i + 1]); tot -= segl[i]
        else:
            f = tot / segl[i]
            pts.append((path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f))
            break
    return pts

CURSOR = [(0, 0), (0, 17), (4.5, 13), (7.5, 20), (10, 19), (7, 12), (12.5, 12)]

def wrap(text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if font.getlength(cur + ch) > maxw and cur:
            # try to break at last space
            sp = cur.rfind(" ")
            if sp > len(cur) * 0.5:
                lines.append(cur[:sp]); cur = cur[sp + 1:] + ch
            else:
                lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

def draw_bar(d, t):
    d.rectangle((0, 0, W * SS, BAR * SS), fill=(222, 225, 230))
    s = SS
    # back / forward / reload glyphs
    gy = BAR * s / 2
    col = (95, 99, 104)
    d.line([(16 * s, gy), (24 * s, gy)], fill=col, width=2 * s)
    d.line([(16 * s, gy), (20 * s, gy - 4 * s)], fill=col, width=2 * s)
    d.line([(16 * s, gy), (20 * s, gy + 4 * s)], fill=col, width=2 * s)
    d.arc((34 * s, gy - 5 * s, 44 * s, gy + 5 * s), 30, 330, fill=col, width=2 * s)
    # url pill
    d.rounded_rectangle((56 * s, 6 * s, 628 * s, (BAR - 6) * s), radius=11 * s, fill=(255, 255, 255))
    # lock
    lx, ly = 68 * s, gy
    d.rounded_rectangle((lx, ly - 2 * s, lx + 8 * s, ly + 5 * s), radius=1 * s, fill=col)
    d.arc((lx + 1.5 * s, ly - 7 * s, lx + 6.5 * s, ly + 1 * s), 180, 360, fill=col, width=int(1.5 * s))
    shown = URL
    if t < 1.0:
        shown = URL[: int(len(URL) * max(0, (t - 0.1) / 0.8))]
    tx = 84 * s
    host = "m.dcinside.com"
    d.text((tx, gy), shown[: len(host)], font=f_url, fill=(32, 33, 36), anchor="lm")
    if len(shown) > len(host):
        d.text((tx + f_url.getlength(host), gy), shown[len(host):], font=f_url, fill=(110, 114, 120), anchor="lm")
    if t < 1.0 and int(t * 4) % 2 == 0:
        cx_ = tx + f_url.getlength(shown) + 1 * s
        d.line([(cx_, gy - 7 * s), (cx_, gy + 7 * s)], fill=(32, 33, 36), width=s)
    # kebab
    for k in (-5, 0, 5):
        d.ellipse((644 * s - 2 * s, gy + k * s - 2 * s, 644 * s + 2 * s, gy + k * s + 2 * s), fill=col)
    # loading progress
    if 1.0 <= t < 1.8:
        p = ease((t - 1.0) / 0.7)
        d.rectangle((0, (BAR - 2) * s, W * s * p, BAR * s), fill=(26, 115, 232))

# ---------------------------------------------------------------- frame
def frame(t):
    cx, cy, z = cam_at(t)
    camr = clamp_cam(cx, cy, z)
    x0, y0, vw, vh = camr
    box = ((x0 + PADX) * SRC_SCALE, y0 * SRC_SCALE, (x0 + vw + PADX) * SRC_SCALE, (y0 + vh) * SRC_SCALE)
    view = page.resize((W * SS, VH * SS), Image.BICUBIC, box=box, reducing_gap=None)
    img = Image.new("RGB", (W * SS, H * SS), (255, 255, 255))
    if t >= 1.15:
        img.paste(view, (0, BAR * SS))
        if t < 1.5:   # page fade-in after "loading"
            white = Image.new("RGB", img.size, (255, 255, 255))
            img = Image.blend(white, img, (t - 1.15) / 0.35)

    # highlights (multiply layer)
    hl = Image.new("RGB", img.size, (255, 255, 255))
    hd = ImageDraw.Draw(hl)
    pen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(pen)
    zz = W / vw
    for si, s in enumerate(segs):
        if not (s["arr"] <= t < s["mark_end"]):
            continue
        fade = min(1.0, (s["mark_end"] - t) / 0.25)
        for mi, (kind, data, st_, du, op) in enumerate(s["marks"]):
            ta = s["arr"] + st_
            if t < ta: continue
            prog = min(1.0, (t - ta) / du)
            color = op.get("color", YEL if kind == "hl" else RED)
            if kind == "hl":
                widths = [r[2] - r[0] for r in data]
                tot = sum(widths)
                done = prog * tot
                for r in data:
                    w_ = r[2] - r[0]
                    if done <= 0: break
                    part = min(1.0, done / w_)
                    done -= w_
                    a = to_s((r[0] - 2, r[1] + (r[3] - r[1]) * 0.08), camr)
                    b = to_s((r[0] - 2 + (w_ + 4) * part, r[3] + 1), camr)
                    cc = tuple(int(255 - (255 - c) * fade) for c in color)
                    hd.rounded_rectangle((a[0], a[1], b[0], b[1]), radius=3 * SS, fill=cc)
            else:
                alpha = int(235 * fade)
                width = int(max(2.2, 1.6 * zz ** 0.5) * SS)
                if kind == "circle":
                    pts = [to_s(p, camr) for p in circle_pts(data, prog, si + mi)]
                elif kind == "box":
                    pad = 2
                    rr = (data[0] - pad, data[1] - pad, data[2] + pad, data[3] + pad)
                    pts = [to_s(p, camr) for p in box_pts(rr, prog)]
                elif kind == "under":
                    x1, _, x2, y2 = data
                    n = 24
                    pts = [to_s((x1 + (x2 - x1) * prog * i / n, y2 + 2 + 0.8 * math.sin(i * 0.9)), camr) for i in range(n + 1)]
                elif kind == "arrow":
                    (ax, ay), (bx, by) = data
                    ex, ey = ax + (bx - ax) * prog, ay + (by - ay) * prog
                    pts = [to_s((ax, ay), camr), to_s((ex, ey), camr)]
                    stroke(pd, pts, color, width, alpha)
                    if prog > 0.85:
                        e = pts[1]; s0 = pts[0]
                        ang = math.atan2(e[1] - s0[1], e[0] - s0[0])
                        hlen = 11 * SS
                        for da in (2.6, -2.6):
                            stroke(pd, [e, (e[0] + hlen * math.cos(ang + da), e[1] + hlen * math.sin(ang + da))], color, width, alpha)
                    continue
                stroke(pd, pts, color, width, alpha)
    img = ImageChops.multiply(img, hl)
    img.paste(pen, (0, 0), pen)

    # cursor
    if t >= 1.4:
        p = to_s(cursor_at(t), camr)
        if BAR * SS < p[1] < H * SS:
            poly = [(p[0] + x * SS * 1.05, p[1] + y * SS * 1.05) for x, y in CURSOR]
            d = ImageDraw.Draw(img)
            d.polygon(poly, fill=(255, 255, 255), outline=(0, 0, 0), width=int(1.3 * SS))

    d = ImageDraw.Draw(img, "RGBA")
    draw_bar(d, t)

    # caption
    for s in segs:
        if s["t0"] + 0.1 <= t < s["t1"] - 0.05:
            a = min(1.0, (t - s["t0"] - 0.1) / 0.18, (s["t1"] - 0.05 - t) / 0.12)
            lines = wrap(s["text"], f_cap, 600 * SS)
            lh = 22 * SS
            bh = lh * len(lines) + 12 * SS
            by1 = H * SS - 10 * SS
            by0 = by1 - bh
            maxw = max(f_cap.getlength(l) for l in lines)
            bx0 = (W * SS - maxw) / 2 - 12 * SS
            bx1 = (W * SS + maxw) / 2 + 12 * SS
            d.rounded_rectangle((bx0, by0, bx1, by1), radius=8 * SS, fill=(12, 12, 16, int(205 * a)))
            for li, line in enumerate(lines):
                d.text((W * SS / 2, by0 + 6 * SS + lh * li + lh / 2), line, font=f_cap,
                       fill=(255, 255, 255, int(255 * a)), anchor="mm")
            break

    out = img.resize((W, H), Image.LANCZOS)
    if t > TOTAL - 0.7:
        out = Image.blend(out, Image.new("RGB", out.size, (0, 0, 0)), min(1.0, (t - (TOTAL - 0.7)) / 0.7))
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        for tt in map(float, sys.argv[2:]):
            frame(tt).save(f"still_{tt:06.2f}.png")
        print("TOTAL", TOTAL)
        for i, s in enumerate(segs):
            print(i, round(s["t0"], 2), round(s["arr"], 2), round(s["t1"], 2), s["text"][:30])
        sys.exit()
    n = int(TOTAL * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", "out.mp4"],
                          stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0: print(f"{i}/{n}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", TOTAL)
