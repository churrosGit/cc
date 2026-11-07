# 육각 너트 × 스패너 vs 라쳇 — 쇼츠 디자인 시안 (3D)

세로 1080×1920 쇼츠의 대표 프레임 3종. 모든 장면은 three.js 실시간 3D 모델
(`scene3d.js`: 너트·볼트·일반 스패너·라쳇 링헤드 내부의 톱니바퀴/멈춤쇠/스프링)로
렌더링되므로, 선택된 시안은 같은 모델에 회전 키프레임만 넣어 그대로 영상화할 수 있다.

| 파일 | 콘셉트 |
| --- | --- |
| `d1-studio-metal.png` | 스튜디오 메탈 시네마틱 — 크롬 질감, 단면 클로즈업 + 원형 확대 인셋, 주황 강조 (톱니 20개로 큼직하게 표현) |
| `d2-xray-split.png` | 엑스레이 투시 · 상하 분할 — 위: 일반 스패너(돌리고·빼고·끼우고), 아래: 반투명 라쳇 내부 |
| `d3-clay-iso.png` | 클레이 아이소메트릭 — 밝은 파스텔 무광 질감, 두 공구를 한 화면에 비교 |
| `overview.png` | 세 시안 비교용 모음 |

다시 렌더링: `node render.js d1-studio-metal.html d2-xray-split.html d3-clay-iso.html`
(Playwright + Chromium의 SwiftShader WebGL 사용, three.js는 jsDelivr CDN에서 로드)
