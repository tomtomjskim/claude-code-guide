# DESIGN.md 운영 모델

## 개요

`DESIGN.md`는 AI 코딩 에이전트가 프로젝트의 시각 정체성과 디자인 시스템을 지속적으로 읽을 수 있게 하는 루트 문서다. `CLAUDE.md`가 작업 방식과 안전 규칙을 정의한다면, `DESIGN.md`는 UI가 어떤 색, 타이포그래피, 간격, 컴포넌트 규칙, 금지 패턴을 따라야 하는지 정의한다.

이 문서는 `claude-code-guide`에서 `DESIGN.md` 개념을 Claude Code 팀 시스템, `/design-creative` 스킬, designer 에이전트, 디자인 게이트와 연결하는 운영 기준이다.

---

## 1. 차용 기준

| 출처 | 차용할 것 | 차용하지 않을 것 |
|---|---|---|
| Google `design.md` | YAML front matter + Markdown body, token schema, canonical section order, lint/diff/export 개념 | alpha 스펙을 고정 표준처럼 단정 |
| VoltAgent `awesome-design-md` | 브랜드별 분위기 설명 밀도, component/state/responsive/agent prompt guide 구조 | 공개 브랜드의 시각 정체성 직접 복제 |
| getdesign.md | 카테고리별 레퍼런스 탐색, mood/profile 선택지 | 레퍼런스 파일을 검토 없이 그대로 주입 |

운영 원칙은 **Google은 규격, VoltAgent는 예시 밀도, getdesign.md는 탐색 카탈로그**로 분리한다.

참조:
- https://github.com/google-labs-code/design.md
- https://github.com/VoltAgent/awesome-design-md
- https://getdesign.md/

---

## 2. 문서 역할 분리

| 파일 | 주 독자 | 정의 범위 |
|---|---|---|
| `CLAUDE.md` | Claude Code | 작업 방식, 명령, 권한, 검증, 프로젝트 운영 규칙 |
| `AGENTS.md` | 범용 코딩 에이전트 | 에이전트 공통 작업 규칙 |
| `DESIGN.md` | UI 생성/수정 에이전트 | 디자인 토큰, 컴포넌트 스타일, 레이아웃 원칙, 금지 패턴 |
| `UX_CONCEPT.md` | PM/Designer/Agent | 사용자 맥락, 톤앤매너, 경험 원칙 |
| `UI_SPEC.md` | Developer/Designer | 화면별 레이아웃, 상태, 인터랙션 계약 |

`DESIGN.md`는 UX 산출물을 대체하지 않는다. UX/IA/UI_SPEC에서 결정된 방향을 구현 가능한 디자인 시스템 계약으로 압축한다.

---

## 3. 표준 구조

`DESIGN.md`는 루트에 두며, 다음 두 계층을 갖는다.

1. YAML front matter: 기계가 읽는 토큰
2. Markdown body: 사람이 읽는 적용 원칙

권장 섹션 순서:

```text
Overview
Colors
Typography
Layout
Elevation & Depth
Shapes
Components
Responsive Behavior
Agent Prompt Guide
Do's and Don'ts
```

토큰은 가능한 한 CSS 변수 또는 Tailwind theme로 export 가능한 값만 둔다. 설명은 “예쁘게”가 아니라 “언제 어떤 판단으로 적용하는지”를 적는다.

---

## 4. 주입 워크플로우

### 4.1 신규 프로젝트

```text
요청 수신
→ 제품 유형 판별
→ UX_CONCEPT 또는 사용자 요구 확인
→ DESIGN.md 초안 생성
→ 토큰/컴포넌트/반응형 규칙 작성
→ AGENTS.md 또는 CLAUDE.md에 DESIGN.md 우선 읽기 규칙 추가
→ lint 또는 수동 체크
→ preview 필요 시 별도 HTML 산출
```

### 4.2 기존 프로젝트

```text
요청 수신
→ 기존 CSS 변수, Tailwind config, component library 조사
→ 현재 UI에서 사실 토큰 추출
→ DESIGN.md 생성 또는 보강
→ 기존 토큰명 우선 유지
→ 신규 토큰은 Design System Extension Spec으로 분리
→ 변경 영향 범위 기록
```

### 4.3 리브랜딩/CREATIVE 모드

`/design-creative`가 먼저 방향을 만든 뒤, 결과를 `DESIGN.md` 토큰으로 매핑한다. 토큰 값 변경은 사용자 확인이 필요하며, 기존 컴포넌트 파급 범위를 함께 제시한다.

---

## 5. Claude Code 통합 지점

| 지점 | 반영 방식 |
|---|---|
| `.claude/rules/design-mode.md` | UI 파일 수정 전 `DESIGN.md` 확인 규칙 추가 |
| `skills/design-creative` | 산출물에 `DESIGN.md` 초안 또는 변경안을 포함 |
| `prompts/designer.md` | SYSTEMATIC 모드에서 기존 `DESIGN.md` 준수 |
| `hooks/boilerplates` | 선택적으로 `npx @google/design.md lint DESIGN.md` 실행 |
| `templates/docs/DESIGN-template.md` | 대상 프로젝트 주입용 보일러플레이트 |

---

## 6. 버전 관리

`DESIGN.md` 자체는 프로젝트 산출물이므로 SemVer 대신 문서 내부 `version`을 사용한다.

| 변경 | 예시 | 처리 |
|---|---|---|
| Patch | 오탈자, 설명 보강, 누락 상태 추가 | `version: "0.1.1"` |
| Minor | 신규 토큰/컴포넌트 추가 | `version: "0.2.0"` |
| Major | 기존 토큰명 제거, 스케일 변경, 브랜드 방향 전환 | `version: "1.0.0"` 또는 사용자 승인 |

에이전트는 `DESIGN.md` 변경 시 다음을 완료 기록에 남긴다.

```text
DESIGN.md version:
변경 유형: patch/minor/major
변경 토큰:
영향 컴포넌트:
검증:
남은 리스크:
```

---

## 7. 실행 태스크

| ID | 작업 | 산출물 | 완료 기준 |
|---|---|---|---|
| DMD-01 | 개념 정리 | 이 문서 | 차용 기준과 역할 분리가 명확하다 |
| DMD-02 | 보일러플레이트 작성 | `templates/docs/DESIGN-template.md` | Google식 토큰 + agent guide 포함 |
| DMD-03 | 체크리스트 작성 | `templates/checklists/design-md-checklist.md` | lint 전후 수동 검증 가능 |
| DMD-04 | 디자인 모드 규칙 연결 | `.claude/rules/design-mode.md` | UI 수정 전 `DESIGN.md` 확인 규칙 존재 |
| DMD-05 | README/docs 인덱스 반영 | `README.md`, `docs/README.md` | 사용자가 문서 위치를 찾을 수 있다 |
| DMD-06 | 릴리즈 기록 | `docs/v4.2-changelog.md` | 변경 목적과 migration 기준이 남는다 |

---

## 8. 완료 체크

- [ ] `DESIGN.md`가 루트에 있거나 생성할 위치가 명시되어 있다.
- [ ] YAML token과 Markdown rationale이 모두 있다.
- [ ] 색상, 타이포그래피, spacing, rounded, component token이 최소 1개 이상 있다.
- [ ] 기존 프로젝트에서는 현재 토큰을 우선 사용한다.
- [ ] 신규 토큰은 추가 이유와 사용 위치를 적는다.
- [ ] 반응형 동작과 접근성 기준이 있다.
- [ ] Do's and Don'ts가 구현 판단에 충분하다.
- [ ] 가능하면 `npx @google/design.md lint DESIGN.md` 결과를 남긴다.
