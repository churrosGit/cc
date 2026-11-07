# 18 Tabs — 30초 세로 영상

[@okapi_fukugyo의 X 게시글](https://x.com/okapi_fukugyo/status/2118893124194082977)에 나온
"AI 영상을 AI 티 안 나게 만드는 무료 사이트 18곳"을 소개하는 30초짜리 세로 영상(1080×1920, 30fps)입니다.

결과물: [`18tabs.mp4`](18tabs.mp4)

## 게시글에서 실제로 쓴 도구

| 사이트 | 영상에서 쓴 곳 |
|---|---|
| polyhaven.com | 스튜디오 HDRI 조명, 3D 모델 3개(카메라, TV, 붐박스) — 모두 CC0 |
| threejs.org | 전체 3D 렌더링, 블룸, 셰이더, 표면 샘플링(포인트 → TV 조립 장면) |
| easings.net | 모든 텍스트·오브젝트 움직임의 이징 공식, "모션" 장면의 5가지 곡선 비교 |

나머지 사이트는 계정이나 크레딧이 필요해서 화면 속 소개로만 들어갔습니다.
배경음은 `audio.py`로 직접 합성했습니다(120 BPM, 장면 전환마다 휙 소리와 임팩트).

## 구성 (4초 × 6장면)

0–3초 인트로 · 3D 소재 · 모션 · 웹 3D · AI → 3D · 사운드 · 프롬프트 · 27–30초 "18 TABS" 아웃트로

## 다시 만들기

```bash
npm install
python3 -m http.server 8123 --bind 127.0.0.1 &
node render.mjs frames                      # 900프레임 (Playwright + Chromium)
python3 audio.py soundtrack.wav
ffmpeg -framerate 30 -i frames/f%04d.jpg -i soundtrack.wav \
  -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest 18tabs.mp4
```

`node render.mjs test 4.5 12.5`처럼 시간을 넘기면 그 순간의 프레임만 렌더링합니다.
