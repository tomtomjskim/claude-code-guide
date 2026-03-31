# Todo App - 튜토리얼 프로젝트

## 프로젝트 개요
간단한 할 일 관리 웹 앱. HTML + CSS + JavaScript (프레임워크 없음).

## 기술 스택
- HTML5, CSS3, Vanilla JavaScript
- 빌드 도구 없음 — 브라우저에서 직접 실행

## 파일 구조
- `index.html` — 메인 페이지
- `style.css` — 스타일시트
- `app.js` — 앱 로직

## 코딩 컨벤션
- 한국어 주석 사용
- 함수명은 camelCase
- CSS 클래스는 kebab-case

## 알려진 개선 포인트
- localStorage 저장 미구현 (새로고침 시 데이터 소실)
- XSS 방어 없음 (todo.text를 innerHTML로 직접 삽입)
- 접근성(a11y) 미흡 (aria 속성 부재)
