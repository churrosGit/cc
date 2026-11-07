# 디시 특이점갤 게시물 읽기 영상 (660×372, 16:9)

- `thesingularity-1516221-stream-30s.mp4`: 30초 빠른 진행 버전. 660×372, 30fps, 디시콘 실제 이미지 포함
- `thesingularity-1516221-stream.mp4`: 처음 만든 2분 19초 버전. 디시콘이 자리표시 이미지로 나옴
- `capture.js`: Playwright로 모바일 웹(m.dcinside.com)을 렌더링. 안드로이드 UA, isMobile, 터치를 켜고 너비 660px, DPR 3으로 전체 페이지를 캡처하고 마크업 좌표를 `layout.json`에 저장
- `render_fast.py`: 30초 버전 렌더러. 구간별 길이를 고정하고 카메라와 마크업 속도를 빠르게 조정
- `render.py`: 캡처 이미지를 바탕으로 카메라 확대/이동, 형광펜, 펜 마크업, 커서, 주소창, 자막을 합성한 뒤 ffmpeg로 인코딩
- `dccon.svg`: 디시콘을 받지 못했을 때 쓰는 자리표시 이미지. 30초 버전에서는 dcimg5 대신 dcimg1/dcimg2.dcinside.com에서 미리 받은 디시콘(`../dccons/`)을 넣음

실행 순서: `node capture.js && python3 render.py`
(본문 이미지 `../body_img.png`와 NanumGothic 폰트 `../fontpkg/`가 있어야 합니다)
