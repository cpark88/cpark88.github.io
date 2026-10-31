# cpark88.github.io

Chung Park(박정)의 개인 홈페이지. GitHub Pages가 `main` 브랜치 루트를 그대로 서빙한다.
빌드 단계가 없다: 페이지 전체가 `index.html` 한 파일(HTML·CSS·JS)이다.
**공개 레포다.** 커밋하는 모든 파일은 이 문서를 포함해 누구나 볼 수 있다.

## 파일 지도

| 경로 | 내용 |
|---|---|
| `index.html` | 페이지 전체. 섹션 순서: Intro → News → Selected publications(한 목록, 유형 태그로 구분) → Experience → Education → Talks → Academic service |
| `images/profile.jpg` | 프로필 사진(4:5). 없으면 이니셜 타일이 보인다 |
| `images/teasers/<id>.png` | 논문 티저. `<id>`는 `<article class="pub" id>`와 같다. 없으면 약어 타일이 보인다 |
| `assets/cv.pdf` | CV |
| `fonts/` | Source Serif 4, Source Sans 3 (직접 호스팅, SIL OFL) |
| `scripts/check_site.py` | 규칙 검사기. `index.html`을 고치면 훅이 자동 실행한다 |
| `scripts/make_teaser.py` | 그림이나 PDF 페이지를 티저 PNG로 만든다 |
| `scripts/screenshot.py` | 라이트·다크·모바일 스크린샷을 `.preview/`에 만든다 (Playwright 필요) |
| `.claude/skills/` | `/add-paper`, `/publish` |
| `.claude/rules/page-markup.md` | 마크업·디자인 규칙 (`index.html` 작업 시 자동 로드) |
| `.claude/private-terms.txt` | 페이지에 나오면 안 되는 단어 목록 (gitignore, 절대 커밋하지 않는다) |

## 명령

- 검사: `python3 scripts/check_site.py` (공개 전: `--strict`)
- 로컬 미리보기: `python3 -m http.server 8000` → http://localhost:8000
- 스크린샷: `python3 scripts/screenshot.py`
- 티저: `python3 scripts/make_teaser.py <그림|PDF> <id> [--page N] [--crop X,Y,W,H]`

## 콘텐츠 규칙

- 사실(제목, 저자, 학회, 수치, 날짜)은 출처에서 확인한 것만 쓴다. 출처는 논문, arXiv, 학회 페이지, 공개 레포, 또는 사용자 본인의 말이다.
  - 확인하지 못한 칸은 `<span class="todo">…</span>`로 남기고 사용자에게 묻는다.
- **익명 심사 중이고 공개본이 없는 논문은 올리지 않는다.** 제목, 약어, 뉴스, HTML 주석으로도 올리지 않는다.
  - 공개 레포라 페이지 소스와 커밋 기록까지 공개된다.
- 사내 비공개 정보(내부 서비스명, 과제명, 공개되지 않은 수치)는 쓰지 않는다.
  - 새로 알게 된 비공개 이름은 `.claude/private-terms.txt`에 추가한다.
- 초록 점 줄(`.impact`)은 논문이나 공개 레포에 나온 실서비스 결과만 쓴다. 숫자와 비교 대상은 출처 그대로 둔다.
- 페이지 문구는 영어로 쓴다. 평서문·능동태로 쓰고, 아포스트로피와 따옴표는 ’ “ ”를 쓴다.
- 본인 이름은 저자 목록에서 `<strong>Chung Park</strong>`, 교신저자는 이름 뒤에 `†`를 붙인다. 공저자 표기는 논문에 실린 그대로 쓴다.
- 논문, 경력, 뉴스를 바꾸면 CV(`assets/cv.pdf`)도 갱신할지 사용자에게 묻는다.

## 뉴스

- `<ol class="news">` 맨 위에 넣는다(최신순): `<li><time datetime="YYYY-MM">Mon YYYY</time><p>…</p></li>`
- 논문을 언급하면 해당 항목으로 링크한다: `<a href="#id">`
- 8개를 넘으면 가장 오래된 것부터 지운다. 논문 자체는 Selected publications에 남는다.

## 작업 흐름

- 논문 추가·수정·이동(채택, 수상, preprint → 학회): `/add-paper <링크|BibTeX|PDF|설명>`
- 커밋·푸시: `/publish`. `git push` 전에는 항상 사용자에게 확인받는다.
- 그 밖의 수정도 끝나면 `python3 scripts/check_site.py`로 오류 0개를 확인한다. footer의 "Last updated Month YYYY"는 공개할 때 그달로 바꾼다.
- 개인 메모(CV 원본 위치 등)는 `CLAUDE.local.md`에 둔다(gitignore).
