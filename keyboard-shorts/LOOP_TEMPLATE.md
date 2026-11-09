# 비교 루프 영상 양식 (스패너 vs 라쳇 기준)

다른 주제(예: 기계식 키보드 vs 멤브레인/펜타그래프)를 같은 양식으로 만들 때 참고하는 사양.
기준 결과물: `video/spanner-vs-ratchet-loop-16s.mp4`, 소스: `video/loop.html`.

## 화면 양식
- 세로 **720×1280, 24fps**, 길이 8초 또는 16초, **무한루프**(마지막 프레임 → 첫 프레임이 이어지게 모든 동작 주기를 루프 길이의 약수로)
- 배경 `#0c0d10`, 패널 배경은 중앙이 밝은 radial gradient(`#2a2e36 → #15171c → #0a0b0e`)
- **상단 고정 제목**(전 구간): 2줄, 54px / weight 900, 비교 대상 중 "좋은 쪽" 이름만 주황 `#ff8a2a`
- **위/아래 2단 패널**(각 높이 525px, top 215 / 752): 위 = 기존 방식, 아래 = 개선된 방식
  - 패널 상단 캡션 띠: 이름 칩(위 회색 `#3b4250`, 아래 주황) + **설명 한 문장**(27px, 핵심어 주황), 어두운 그라데이션 띠 위에 표시
  - 패널 **왼쪽 아래 카운터 상자**: 「조인 횟수」 작은 글씨 + 큰 주황 숫자 + "회", 반투명 어두운 상자, 증가 시 살짝 커지는 효과
- 효과 문구 팝업(예: "딸깍!"): 주황 900 weight, 살짝 기울임, 0.4초 페이드

## 3D 스타일 (three.js 0.165, 스튜디오 메탈)
- `scene3d.js`의 `setupRenderer`(ACES, PCFSoft 그림자), `envMap`(RoomEnvironment 반사)
- 조명: 키 라이트 `0xfff1e0` 2.6 (−6,14,4) 그림자 + 림 라이트 `0x8fb8ff` 2.0 (7,4,−8)
- 재질: 크롬 `0xc4c9d1` metal 1 rough 0.28 / 검정 부품 `0x24272d` / 핵심 부품 주황 `0xff7a1a`(약한 emissive) / 스프링 하늘색 `0x7fb6ff`
- 핵심 내부 구조는 **덮개를 벗긴 단면**으로 보여주고, 움직이는 부품끼리는 **겹치지 않게**(충돌 계산 또는 미세 간격) — 겹치면 깨져 보임
- 기계식 동작은 실제 원리대로(방향, 걸림/미끄러짐 등) 정확하게

## 동작 / 비교 연출
- 두 패널을 **동시에 같은 시작 시점**으로, 개선된 쪽이 더 빠르게(예: 2배 횟수) 동작해 차이가 직관적으로 보이게
- 카운터 증가 시점 = 한 동작이 끝나는 순간

## 소리
- 나레이션 없음. 직접 합성한 오리지널 BGM(120BPM, 4마디=8초 단위, 루프 이음매 없음) + 동작 효과음
- `loop_audio.py events.json out.wav` — 페이지가 내보내는 `window.CLICKS / TAPS / DURATION`으로 효과음 위치 결정

## 렌더링 파이프라인
- 페이지는 `window.renderAt(t)`(t초 장면을 그림)와 `window.__done`을 제공
- 미리보기: `VW=720 VH=1280 PAGE=loop.html node preview.js 1.0 2.5 …` → `preview/f_<t>.jpg`
- 전체: `VW=720 VH=1280 PAGE=loop.html OUT=loop_silent.mp4 EVENTS=loop_events.json node render-video.js 24`
  → `python3 loop_audio.py loop_events.json loop_audio.wav` → ffmpeg로 합치기(`-c:v copy -c:a aac`)
- GPU 없는 환경(SwiftShader)이라 720p/24fps 기준 16초 ≈ 2분 20초
