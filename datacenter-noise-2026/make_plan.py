"""Prepare audio and plan.json for the data center noise shorts.
Usage: python3 make_plan.py <narration.wav> <tweet_video.mp4> <workDir>
Writes <workDir>/narration_edit.wav, <workDir>/noise.wav and ./plan.json (this folder).

Timing comes from ffmpeg silencedetect on the narration (sentence ends below).
A 2.0 s gap is inserted after sentence 1 so the clip's noise plays alone, and 1.1 s is added at the end."""
import json, os, subprocess, sys

narr, video, work = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(here), 'shorts-assets')
MEMES = os.path.join(ASSETS, 'memes', 'pepe') + '/'
SFX = os.path.join(ASSETS, 'sfx')
os.makedirs(work, exist_ok=True)

GAP_AT, GAP = 3.2, 2.0      # inside the 2.90-3.46 pause after sentence 1
TAIL = 1.1
NARR_DUR = 45.4
DUR = round(NARR_DUR + GAP + TAIL, 2)


def T(t):  # original narration time -> edited time
    return round(t + GAP if t > GAP_AT else t, 2)


def ff(args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + args, check=True)


# narration: +3.4 dB (measured -19.4 LUFS -> about -16), 2.0 s gap after sentence 1, 1.1 s tail
ff(['-i', narr, '-filter_complex',
    f"[0:a]aresample=48000,volume=3.4dB,asplit[a][b];"
    f"[a]atrim=0:{GAP_AT},asetpts=N/SR/TB[p1];"
    f"[b]atrim={GAP_AT},asetpts=N/SR/TB[p2];"
    f"aevalsrc=0:d={GAP}:s=48000[g];aevalsrc=0:d={TAIL}:s=48000[t];"
    f"[p1][g][p2][t]concat=n=4:v=0:a=1[o]", '-map', '[o]', '-ac', '1', os.path.join(work, 'narration_edit.wav')])

# clip sound: even out the level (the hum gets quieter near the houses), then make it loud (about -14 LUFS)
ff(['-i', video, '-vn', '-af',
    'highpass=f=40,dynaudnorm=f=300:g=15:p=0.9,loudnorm=I=-14:TP=-1.5:LRA=7', '-ar', '48000',
    os.path.join(work, 'noise.wav')])

# scene boundaries (edited time), placed in the middle of the pauses between sentences
b = {
    's2': GAP_AT,                     # clip starts right after sentence 1
    's3': T((8.92 + 9.25) / 2),
    's3b': T(11.0),                   # photo -> headline inside sentence 3
    's4': T((13.41 + 13.88) / 2),
    's5': T((19.25 + 19.87) / 2),
    's5b': T(21.23),                  # "유일한 이유는 아니었지만," -> poll paragraph
    's6': T((26.65 + 27.31) / 2),
    's7': T((29.07 + 29.66) / 2),
    's8': T((33.48 + 34.06) / 2),
    's8b': T(34.06 + 1.0),            # 6abc headline 1 s, then the quote
    's9': T((36.27 + 36.77) / 2),
    's10': T((40.46 + 41.11) / 2),
    'm1': T(7.0),                     # "웅 하는 기계 소리가 끊이지 않습니다" -> speechless pepe
    'm2': T(38.65),                   # "그냥 집을 나가버린다고" -> crying pepe
}
CLIP2_FROM = 6.8  # the clip's houses part for the ending
segments = [
    {"start": 0.0, "type": "pieces", "items": [{"img": "tw1", "y": [20, 500]}]},
    {"start": b['s2'], "type": "video", "src": video, "from": 0},
    {"start": b['m1'], "type": "meme", "src": MEMES + "speechless.jpg"},
    {"start": b['s3'], "type": "pieces", "items": [{"img": "pbs1", "y": [0, 1030]}]},
    {"start": b['s3b'], "type": "pieces", "items": [{"img": "pbs1", "y": [1300, 2240]}]},
    {"start": b['s4'], "type": "pieces", "items": [{"img": "pbs2", "y": [3200, 4530]}]},
    {"start": b['s5'], "type": "pieces", "items": [{"img": "time1", "y": [240, 860]}]},
    {"start": b['s5b'], "type": "pieces", "items": [{"img": "time1", "y": [3420, 4740]}]},
    {"start": b['s6'], "type": "pieces", "items": [{"img": "nbc1", "y": [330, 1240]}]},
    {"start": b['s7'], "type": "pieces", "items": [{"img": "nbc1", "y": [3850, 4700]}]},
    {"start": b['s8'], "type": "pieces", "items": [{"img": "abc1", "y": [0, 690]}]},
    {"start": b['s8b'], "type": "pieces", "items": [{"img": "abc1", "y": [4300, 4850]}]},
    {"start": b['s9'], "type": "pieces", "items": [{"img": "wftv1", "y": [60, 850]}]},
    {"start": b['m2'], "type": "meme", "src": MEMES + "crying.jpg"},
    {"start": b['s10'], "type": "video", "src": video, "from": CLIP2_FROM},
]

# clip sound: louder than the narration on its own, only slightly lower (-2 dB) under the narration
s2_end, s10_start = b['s3'], b['s10']
narr_end = T(45.06)
audio = [
    {"src": os.path.join(work, 'noise.wav'), "at": GAP_AT, "from": 0, "dur": GAP + 0.25, "gain_db": 4, "fade": 0.12},
    {"src": os.path.join(work, 'noise.wav'), "at": GAP_AT + GAP, "from": GAP, "dur": round(s2_end - GAP_AT - GAP, 2), "gain_db": -2, "fade": 0.25},
    {"src": os.path.join(work, 'noise.wav'), "at": s10_start, "from": CLIP2_FROM, "dur": round(narr_end - s10_start, 2), "gain_db": -2, "fade": 0.25},
    {"src": os.path.join(work, 'noise.wav'), "at": narr_end - 0.1, "from": round(CLIP2_FROM + narr_end - 0.1 - s10_start, 2), "dur": round(DUR - narr_end + 0.1, 2), "gain_db": 6, "fade": 0.15},
]

# sound effect at every scene change: whooshes in turn, a reaction sound on the two meme cuts.
# gain brings each whoosh's loudest 100 ms to about -15 dB so it is clearly heard (narration is about -17 dB); 'peak' is where the
# whoosh peaks inside the file, so it is started early enough to peak on the cut.
WHOOSH = [("098_후욱 -b중간2.wav", -8.7, 0.30, 0.75), ("041_바람.mp3", -10.3, 0.27, 0.72),
          ("096_후욱 -a짧은2.mp3", -15.5, 0.13, 0.37), ("070_휘익.mp3", -10.2, 0.42, 1.06)]
REACT = {"m1": ("074_어이없는 웃음소리.mp3", -11.7, 0.15, 2.0, -18),
         "m2": ("019_퓨히익.mp3", -16.7, 0.85, 1.5, -16)}
k = 0
for seg in segments[1:]:
    t = seg['start']
    key = next((m for m in REACT if abs(b[m] - t) < 1e-6), None)
    if key:
        f, loud, frm, dur, target = REACT[key]
        audio.append({"src": os.path.join(SFX, f), "at": t, "from": frm, "dur": dur, "gain_db": round(target - loud, 1), "fade": 0.1})
    else:
        f, loud, peak, dur = WHOOSH[k % len(WHOOSH)]; k += 1
        audio.append({"src": os.path.join(SFX, f), "at": round(max(t - peak, 0), 2), "from": 0, "dur": dur, "gain_db": round(-15 - loud, 1), "fade": 0.03})

subs = [
    [0.27, "미국 민주당이 이번 선거에서<br>이긴 이유라는 영상입니다"],
    [GAP_AT, "(소리를 켜고 들어보세요)"],
    [T(3.46), "데이터센터라는 건물을 지나<br>길 건너 주택가까지 걸어가도"],
    [T(7.0), "웅 하는 기계 소리가<br>끊이지 않습니다"],
    [T(9.25), "실제로 지난<br>미국 중간선거에서"],
    [T(11.0), "민주당은 상원과 하원을<br>모두 되찾았습니다"],
    [T(13.88), "데이터센터가 몰린<br>텍사스, 오하이오, 조지아에서도"],
    [T(16.84), "데이터센터에 강경한<br>민주당 주지사가 나왔습니다"],
    [T(19.87), "유일한 이유는 아니었지만"],
    [T(21.32), "출구조사에서<br>유권자 56%가"],
    [T(23.9), "AI와 데이터센터가<br>투표에 중요했다고 답했습니다"],
    [T(27.31), "주민들의 고통은<br>실제로 심각합니다"],
    [T(29.66), "뉴저지의 한 주민은<br>잠을 잘 수 없고"],
    [T(31.67), "소리가 집 전체에<br>울린다고 호소했고"],
    [T(34.06), "다른 주민은 불안감까지<br>생겼다고 말합니다"],
    [T(36.77), "유타의 한 주민은<br>발전기가 돌면"],
    [T(38.65), "그냥 집을 나가버린다고<br>털어놨습니다"],
    [T(41.11), "AI를 떠받치는<br>데이터센터가"],
    [T(42.97), "이제 미국 선거 판도까지<br>바꾸고 있습니다"],
    [narr_end + 0.2, ""],
]

plan = {"fps": 30, "duration": DUR, "content_y": 534, "content_h": 810,
        "title": "미국 민주당이 이긴 이유가<br>데이터센터 소음?",
        "segments": segments, "audio": audio, "subs": subs}
json.dump(plan, open(os.path.join(here, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
for k, s in enumerate(segments):
    end = segments[k + 1]['start'] if k + 1 < len(segments) else DUR
    print(f"{s['start']:6.2f}-{end:6.2f} ({end - s['start']:.2f}s) {s['type']} {s.get('items', [{}])[0].get('img', s.get('src', ''))[-20:]}")
