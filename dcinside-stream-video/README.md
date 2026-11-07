# 디시 특이점갤 게시물 읽기 영상 (660×372, 16:9)

- `thesingularity-1516221-stream.mp4`: 결과 영상. 660×372, 30fps, 약 2분 19초, 무음 오디오 트랙 포함
- `capture.js`: Playwright로 모바일 웹(m.dcinside.com)을 렌더링. 안드로이드 UA, isMobile, 터치를 켜고 너비 660px, DPR 3으로 전체 페이지를 캡처하고 마크업 좌표를 `layout.json`에 저장
- `render.py`: 캡처 이미지를 바탕으로 카메라 확대/이동, 형광펜, 펜 마크업, 커서, 주소창, 자막을 합성한 뒤 ffmpeg로 인코딩
- `dccon.svg`: 녹화 환경에서 디시콘 이미지 호스트가 막혀 대신 넣은 자리표시 이미지

실행 순서: `node capture.js && python3 render.py`
(본문 이미지 `../body_img.png`와 NanumGothic 폰트 `../fontpkg/`가 있어야 합니다)
