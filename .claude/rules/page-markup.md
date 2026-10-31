---
paths:
  - "index.html"
---

# index.html 마크업·디자인 규칙

## 구조

- 한 파일을 유지한다: CSS는 `<head>`의 `<style>`, JS는 페이지 끝 `<script>` 하나.
- 사용자가 요청하지 않는 한 외부 CDN, 프레임워크, 분석 스크립트를 추가하지 않는다.
- 새 항목은 `.claude/skills/add-paper/templates.html`의 마크업을 그대로 복사해 쓴다. 클래스 이름을 새로 만들지 않는다.
- 논문 `id`는 소문자·숫자·하이픈이고 티저 파일명과 같다: `id="duelrec"` ↔ `images/teasers/duelrec.png`.
- 티저 `<img>`는 `alt=""`(장식), 프로필 사진은 `alt="Photo of Chung Park"`.

## 디자인 토큰

- 색은 CSS 변수만 쓴다. 의미가 정해져 있다:
  - `--ink`, `--slate`: 텍스트
  - `--link`: 링크
  - `--live`: 실서비스 결과(초록 점)
  - `--award`: 수상·Oral(금색)
  - `--todo-*`: 플레이스홀더
- 새 색, 하드코딩 색을 추가하지 않는다. 예외는 티저 이미지 뒤의 흰 배경 하나.
- 다크 모드는 `:root[data-theme="dark"]`의 변수 값만 바꿔서 맞춘다.
- 서체:
  - 이름, 본문, 논문 제목: `var(--serif)`
  - 날짜, 저자, 학회, 링크, 배지: `var(--sans)`

## 쓰지 않는 것

- 대문자 라벨, GitHub·LinkedIn 같은 로고 아이콘, 카드 그림자, 등장 애니메이션
- `A · B · C`처럼 가운뎃점으로 이은 메타 문자열, 링크 끝의 `→`
- 곧은 따옴표·아포스트로피: 본문에는 ’ “ ”를 쓴다

## 확인

- 수정할 때마다 PostToolUse 훅이 `scripts/check_site.py --hook`을 실행한다. 오류가 나오면 다음 작업 전에 고친다.
- 레이아웃을 바꿨다면 `python3 scripts/screenshot.py`를 실행한다. 그다음 `.preview/`의 데스크톱·모바일·다크 이미지를 직접 열어 확인한다.
