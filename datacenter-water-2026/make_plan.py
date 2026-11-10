"""Write plan.json for the data center water shorts from words.json (made by make_audio.py).
Usage: python3 make_plan.py
Scene changes sit in the middle of the pauses between sentences, or just before a given word inside one."""
import json, os

here = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(here), 'shorts-assets')
MEMES = os.path.join(ASSETS, 'memes', 'pepe') + '/'
SFX = os.path.join(ASSETS, 'sfx')
W = json.load(open(os.path.join(here, 'words.json'), encoding='utf-8'))
S = W['sentences']
DUR = W['duration']


def gap(k):  # middle of the pause after sentence k (0-based)
    return round((S[k]['end'] + S[k + 1]['start']) / 2, 2)


def word(k, i):  # start of word i of sentence k
    return S[k]['words'][i][0]


def ko(img, lines, bounce):
    # Korean already drawn in the capture; the lines the narration is on pop out as one group
    return {"img": img, "lines": lines, "bounce": bounce, "static": False, "pad": [0, 0]}


L = {  # Korean line boxes [top, bottom, left, right] printed by newsmark.js
    "cross": [[205, 259, 51, 572], [331, 385, 48, 511], [457, 505, 48, 792], [583, 631, 48, 570], [709, 763, 51, 642],
              [835, 883, 51, 699], [961, 1009, 48, 657], [1087, 1135, 48, 603], [1213, 1267, 48, 331],
              [1339, 1387, 48, 798], [1465, 1513, 48, 374]],
    "absh": [[512, 575, 35, 463], [686, 740, 38, 787], [860, 914, 38, 572], [1034, 1088, 38, 351],
             [3068, 3119, 41, 860], [3188, 3239, 44, 737], [3308, 3353, 44, 716], [3428, 3479, 41, 699],
             [3548, 3599, 41, 795], [3668, 3719, 41, 838]],
    "golfp": [[281, 329, 48, 643], [407, 461, 48, 515], [533, 587, 48, 669], [659, 713, 51, 287], [785, 833, 48, 706],
              [911, 965, 51, 617]],
    "intro": [[331, 379, 51, 657], [457, 505, 48, 818], [583, 637, 48, 572], [709, 757, 51, 516], [852, 900, 48, 601]],
}
b = {
    's1': 0.0,
    's2': gap(0), 's3': gap(1), 'm1': gap(2),
    's5': gap(3), 's5b': round(word(4, 4) - 0.08, 2),       # "바로 이 비교를" -> paragraph
    's6': gap(4), 's7': gap(5), 's7b': round(word(6, 6) - 0.08, 2),  # "수돗물은 10퍼센트도"
    's8': gap(6), 's9': gap(7), 's10': gap(8), 'm2': round(word(9, 2) - 0.1, 2),  # "결론은"
}
T = lambda k, i: round(word(k, i), 2)
segments = [
    {"start": b['s1'], "type": "pieces", "items": [{"img": "tw1", "y": [10, 880]}]},
    {"start": b['s2'], "type": "pieces", "items": [{"img": "fig4", "y": [0, 510]}]},
    {"start": b['s3'], "type": "pieces", "items": [{"img": "golf", "y": [0, 1015]}]},
    {"start": b['m1'], "type": "meme", "src": MEMES + "thumbs-up.jpg"},
    {"start": b['s5'], "type": "pieces", "items": [{"img": "absh", "y": [240, 1230],
        "ko": ko("absh", L["absh"], [[0.25, round(b['s5b'] - b['s5'], 2), [0, 1, 2, 3]]])}]},
    {"start": b['s5b'], "type": "pieces", "items": [{"img": "cross", "y": [110, 900],
        "ko": ko("cross", L["cross"], [[0.05, round(S[4]['end'] - b['s5b'], 2), [4, 5]]])}]},
    {"start": b['s6'], "type": "pieces", "items": [{"img": "cross", "y": [650, 1560],
        "ko": ko("cross", L["cross"], [[round(T(5, 0) - b['s6'], 2), round(T(5, 5) - b['s6'] - 0.1, 2), [7, 8]],
                                       [round(T(5, 5) - b['s6'], 2), round(S[5]['end'] - b['s6'], 2), [9, 10]]])}]},
    {"start": b['s7'], "type": "pieces", "items": [{"img": "golf", "y": [0, 1015]}]},
    {"start": b['s7b'], "type": "pieces", "items": [{"img": "golfp", "y": [100, 990],
        "ko": ko("golfp", L["golfp"], [[0.05, round(S[6]['end'] - b['s7b'], 2), [2, 3, 4]]])}]},
    {"start": b['s8'], "type": "pieces", "items": [{"img": "intro", "y": [230, 930],
        "ko": ko("intro", L["intro"], [[round(T(7, 2) - b['s8'], 2), round(S[7]['end'] - b['s8'], 2), [2, 3, 4]]])}]},
    {"start": b['s9'], "type": "pieces", "items": [{"img": "absh", "y": [2960, 3738],
        "ko": ko("absh", L["absh"], [[round(T(8, 1) - b['s9'], 2), round(T(8, 2) - b['s9'] - 0.05, 2), [6, 7]],
                                     [round(T(8, 2) - b['s9'], 2), round(S[8]['end'] - b['s9'], 2), [8, 9]]])}]},
    {"start": b['s10'], "type": "pieces", "items": [{"img": "tw1", "y": [10, 880]}]},
    {"start": b['m2'], "type": "meme", "src": MEMES + "shrug-confused.jpg"},
]

# sound effect at EVERY scene change: a whoosh on each cut (meme cuts also get a reaction sound).
# gain brings each sound's loudest 100 ms to TARGET (narration's typical loud 100 ms is about -15 on this scale,
# so the whoosh is clearly heard over it); 'peak' = where the whoosh peaks inside the file, so it peaks on the cut.
TARGET = -11
WHOOSH = [("002_휙(만화적).mp3", -10.2, 0.42, 1.06), ("098_후욱 -b중간2.wav", -8.7, 0.30, 0.75),
          ("042_바람2.mp3", -7.4, 0.29, 0.65), ("070_휘익.mp3", -10.2, 0.42, 1.06)]
REACT = {"m1": ("015_띠링.mp3", -17.3, 0, 0.94, -13),
         "m2": ("019_퓨히익.mp3", -16.7, 0.85, 1.5, -13)}
audio = []
for k, seg in enumerate(segments[1:]):
    t = seg['start']
    f, loud, peak, dur = WHOOSH[k % len(WHOOSH)]
    audio.append({"src": os.path.join(SFX, f), "at": round(max(t - peak, 0), 2), "from": 0, "dur": dur,
                  "gain_db": round(TARGET - loud, 1), "fade": 0.03})
    key = next((m for m in REACT if abs(b[m] - t) < 1e-6), None)
    if key:
        f, loud, frm, dur, target = REACT[key]
        audio.append({"src": os.path.join(SFX, f), "at": round(t + 0.15, 2), "from": frm, "dur": dur,
                      "gain_db": round(target - loud, 1), "fade": 0.05})

SUBS = [  # (sentence, first word, text)
    (0, 0, "데이터센터가 물을 낭비한다는 건<br>거짓말이라는 글이 화제입니다"),
    (1, 0, "2024년 미국 데이터센터가<br>쓴 물은 최대 230억 갤런"),
    (2, 0, "같은 해 골프장이 쓴 물의<br>4%밖에 안 된다는 겁니다"),
    (3, 0, "원문과 대조해 보니<br>숫자는 맞았습니다"),
    (4, 0, "그런데 근거로 든<br>논문에는"),
    (4, 4, "바로 이 비교를 경계하는<br>내용이 적혀 있습니다"),
    (5, 0, "골프장과 비교하는 건<br>의미가 없고"),
    (5, 5, "오히려 여론을<br>오도한다는 겁니다"),
    (6, 0, "골프장 물은 대부분<br>지하수, 호수, 재활용수이고"),
    (6, 6, "수돗물은<br>10%도 안 됩니다"),
    (7, 0, "반면 데이터센터는 주로 주민들과<br>같은 수돗물을 끌어다 씁니다"),
    (8, 0, "논문은 2030년까지<br>뉴욕시 하루 급수량에 맞먹는"),
    (8, 6, "수도 시설이 새로<br>필요할 수 있다고 내다봤습니다"),
    (9, 0, "숫자는 맞았지만"),
    (9, 2, "결론은 논문과<br>달랐던 셈입니다"),
]
subs = [[max(round(word(s, i) - 0.05, 2), 0), t] for s, i, t in SUBS] + [[round(S[-1]['end'] + 0.2, 2), ""]]

plan = {"fps": 30, "duration": DUR, "content_y": 534, "content_h": 810,
        "title": "데이터센터 물 낭비는<br>거짓말이다?",
        "segments": segments, "audio": audio, "subs": subs}
json.dump(plan, open(os.path.join(here, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
for k, s in enumerate(segments):
    end = segments[k + 1]['start'] if k + 1 < len(segments) else DUR
    print(f"{s['start']:6.2f}-{end:6.2f} ({end - s['start']:.2f}s) {s['type']} {s.get('items', [{}])[0].get('img', s.get('src', ''))[-20:]}")
