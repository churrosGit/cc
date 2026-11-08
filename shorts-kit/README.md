# shorts-kit

게시물 캡처형 쇼츠를 만드는 프로그램 모음입니다. 제작 규칙은 저장소 맨 위의 `CLAUDE.md`를 따릅니다.

## 폴더

| 경로 | 하는 일 |
|---|---|
| `capture/dc_list.py` | DC 모바일 갤러리 목록에서 제목·시간·링크 뽑기 (키워드 필터, 제목 검색) |
| `capture/dc_post.py` | DC 게시물의 제목·작성 시각·본문 텍스트 확인 |
| `capture/rnew.js` | 서브레딧 최신글을 스크롤하며 기준 시각 이후 글 목록 뽑기 (모바일 화면) |
| `capture/mobile_capture.js` | 360px 모바일 화면 캡처 (광고 숨김, 닉네임 흐림) |
| `capture/dcmark.js` | DC 게시물 캡처 + 빨강·초록 네모 마크업 |
| `capture/rmark.js` | 레딧 게시물 캡처 + 마크업 + 한국어 번역 삽입 |
| `build/pieces.py` | 캡처에서 블록 사이 빈 줄을 찾아 조각을 자를 위치 계산 |
| `build/ov_render.js` | 제목·자막 이미지와 흰 바탕 글자 카드 만들기 |
| `build/build.py` | 조각(블러필), 글자 카드, 제목·자막, 나레이션을 합쳐 영상 만들기 |
| `fonts/` | Pretendard 폰트 (SIL Open Font License, `fonts/LICENSE.txt`) |
| `examples/claude-users-2026-11/` | "전 세계 클로드 유저들이 이상함을 감지했다" 영상의 설정 파일과 원고 |

## 만드는 순서

1. 게시물 찾기
   ```bash
   python3 -I capture/dc_list.py claude 6 '오푸스|한도|멍청'          # 갤러리 id, 페이지 수, 키워드
   python3 -I capture/dc_list.py thesingularity 2 '' '클로드'          # 제목 검색
   python3 -I capture/dc_post.py claude/8451                           # 본문 확인
   node capture/rnew.js ClaudeCode 2026-11-06T15:00:00Z 120 > list.tsv # 레딧 최신글
   ```
2. 마크업 설정 파일(`dcmarks.json`, `marks.json`)을 쓰고 캡처하기
   ```bash
   node capture/dcmark.js dcmarks.json <캡처폴더>
   node capture/rmark.js marks.json <캡처폴더>
   python3 -I build/pieces.py <캡처폴더>/dc1.png 267   # 자를 위치 후보 확인 (DC는 267px부터)
   ```
3. 나레이션 음성의 쉬는 구간 확인
   ```bash
   ffmpeg -i narration.wav -af silencedetect=noise=-35dB:d=0.12 -f null - 2>&1 | grep silence_
   ```
4. `plan.json`에 장면(조각 위치, 시작 시각)과 자막을 적고 영상 만들기
   ```bash
   node build/ov_render.js <프로젝트폴더>
   python3 -I build/build.py <프로젝트폴더> <캡처폴더> narration.wav out.mp4
   ```

`node` 실행 시 Playwright를 찾지 못하면 `NODE_PATH=$(npm root -g)`를 앞에 붙입니다.

## plan.json 형식

- `segments`: 장면 목록. 각 장면은 `start`(초)부터 다음 장면 시작까지 이어집니다.
  - `{"type": "pieces", "items": [{"img": "dc1", "y": [267, 1024], "w": 1}]}`: 캡처 `dc1.png`의 세로 267~1024px 조각. 여러 조각이면 `w` 비율로 시간을 나눕니다.
  - `{"type": "text", "text": "① 사용 한도"}`: 흰 바탕 검정 글자 카드.
- `subs`: `[시작 초, "자막<br>둘째 줄"]` 목록.
- `title`, `duration`, `content_y`(534), `content_h`(810)는 예시 파일을 참고합니다.
