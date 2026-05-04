---
globs: "**/*.tsx,**/*.jsx,**/*.vue,**/*.svelte,**/*.css,**/*.scss,**/*.html"
---
# 디자인 모드 규칙

## 공통 DESIGN.md 규칙
- UI 파일을 수정하기 전 프로젝트 루트의 `DESIGN.md` 존재 여부를 확인한다
- `DESIGN.md`가 있으면 색상, 타이포그래피, spacing, radius, component token을 우선 준수한다
- `DESIGN.md`가 없고 UI 변경 범위가 크면 생성 또는 보강 필요성을 사용자에게 명시한다
- `UX_CONCEPT.md`, `IA.md`, `UI_SPEC.md`가 있으면 경험/화면 계약은 해당 문서를 우선하고, `DESIGN.md`에는 재사용 가능한 시각 시스템만 반영한다

## 기존 프로젝트 UI 수정 시 (SYSTEMATIC 모드)
- 프로젝트 디자인 시스템 CSS 변수 토큰만 사용한다
- 기존 컴포넌트 재사용을 우선 검토한다
- `frontend-design` 스킬 자동 트리거 금지 — 기존 designer 에이전트 프로세스를 따른다
- 색상/타이포그래피/간격은 `--primary`, `--text-*`, `--space-*` 등 정의된 토큰만 허용
- 하드코딩된 hex 색상, 임의 폰트 지정 금지

## 새 프로젝트/프로토타입/랜딩페이지 시 (CREATIVE 모드)
- 사용자가 명시적으로 "새 디자인", "랜딩페이지", "프로토타입", "creative" 요청 시에만 활성화
- `/design-creative` 스킬 또는 `frontend-design` 플러그인 사용 가능
- 산출물은 반드시 프로젝트 토큰 매핑 단계를 거친다
- 최종 산출물에 `DESIGN.md` 초안 또는 `DESIGN.md` 변경안을 포함한다
- 신규 토큰이 필요하면 Design System Extension Spec을 작성한다

## 모드 판별 기준
| 신호 | 모드 |
|------|------|
| 기존 화면 수정, 버그 수정, 컴포넌트 추가 | SYSTEMATIC |
| "새로운 느낌", "리브랜딩", "프로토타입" | CREATIVE |
| 디자인 시스템 토큰이 이미 존재하는 프로젝트 | SYSTEMATIC (기본) |
| 토큰 없는 신규 프로젝트 | CREATIVE |
