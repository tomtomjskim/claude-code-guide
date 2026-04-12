# 듀얼 모드 디자인 전략

## 개요

프론트엔드 디자인 작업을 **SYSTEMATIC**(기존 시스템 준수)과 **CREATIVE**(창의적 신규 설계) 두 모드로 분리하여, 기존 디자인 컨벤션을 보호하면서도 창의적 디자인이 가능한 구조입니다.

Anthropic 공식 `frontend-design` 플러그인의 미학 원칙과 프로젝트 디자인 시스템을 하네스 엔지니어링으로 통합합니다.

---

**관련 문서**:
- [하네스 엔지니어링 가이드](29-harness-engineering.md)
- [디자인 시스템 확장 규칙](32-design-system-extension.md)
- Designer 에이전트 프롬프트: `prompts/designer.md`
- 디자인 모드 규칙: `.claude/rules/design-mode.md`

---

## 1. 왜 듀얼 모드인가

### 문제: 단일 접근의 한계

| 접근 | 장점 | 한계 |
|------|------|------|
| SYSTEMATIC만 | 일관성, 예측 가능성 | 창의성 부족, 모든 UI가 비슷 |
| CREATIVE만 | 독창성, 임팩트 | 기존 시스템 파괴, 컨벤션 충돌 |

### 해결: 하네스로 모드 전환

```
사용자 요청 → 모드 판별 (.claude/rules/design-mode.md)
                ↓
    ┌───────────┴───────────┐
    ▼                       ▼
SYSTEMATIC                CREATIVE
(designer agent)      (/design-creative skill)
    │                       │
    ▼                       ▼
토큰 준수 구현         방향 수립 → 토큰 브릿지
    │                       │
    └───────────┬───────────┘
                ▼
        Design Gate Hook
        (컨벤션 위반 검증)
```

---

## 2. 모드 판별 기준

### 자동 판별 신호

| 신호 | 모드 | 근거 |
|------|------|------|
| 기존 화면/컴포넌트 수정 | SYSTEMATIC | 일관성 유지 |
| 버그 수정, 상태 추가 | SYSTEMATIC | 최소 개입 원칙 |
| "새 디자인", "fresh look" | CREATIVE | 명시적 요청 |
| "랜딩페이지", "프로토타입" | CREATIVE | 독립 산출물 |
| 리브랜딩, 대규모 리뉴얼 | CREATIVE | 시스템 재정의 필요 |
| 디자인 시스템 없는 신규 프로젝트 | CREATIVE | 토큰 미존재 |

### 모호한 경우

판별이 불명확하면 **SYSTEMATIC을 기본**으로 한다. 이유:
- 기존 시스템 파괴 위험이 창의성 부족 위험보다 크다
- CREATIVE가 필요하면 사용자가 명시적으로 전환 요청 가능
- SYSTEMATIC에서도 시각적 깊이(그림자, 투명도, 트랜지션)는 활용 가능

---

## 3. 하네스 구성 요소

### 3.1 경로 스코프 규칙

`.claude/rules/design-mode.md`가 프론트엔드 파일 수정 시 자동 로드되어 모드 규칙을 주입합니다.

### 3.2 Design Gate Hook

`PostToolUse:Edit|Write`에서 디자인 컨벤션 위반을 자동 감지합니다:
- 하드코딩된 hex 색상 (CSS 변수 미사용)
- 디자인 시스템 외 폰트 사용
- 4px 단위가 아닌 간격값

Hook은 `warn`만 발생시키고 `block`하지 않습니다 — CREATIVE 모드에서의 의도적 일탈을 허용하기 위함입니다.

### 3.3 스킬 분리

| 스킬/에이전트 | 모드 | 산출물 |
|--------------|------|--------|
| designer 에이전트 | SYSTEMATIC | Component Spec, UX Flow |
| `/design-creative` | CREATIVE | Design Direction + Token Spec + Component Spec |
| `frontend-design` (공식) | 참조용 | 직접 사용보다 원칙 참조 |

---

## 4. 공식 플러그인 활용 전략

### 직접 사용 vs 원칙 흡수

공식 `frontend-design` 플러그인을 **직접 트리거하지 않고**, 핵심 원칙만 `/design-creative` 스킬에 흡수합니다.

| 공식 플러그인 원칙 | 흡수 방식 |
|------------------|----------|
| Bold aesthetic direction | `/design-creative` Phase 2에 톤 선택 포함 |
| AI slop 회피 | 양쪽 모드 모두 anti-pattern으로 등록 |
| Distinctive typography | CREATIVE 모드에서 폰트 페어링 필수 |
| Motion high-impact moments | CREATIVE에서 모션 스펙 필수 산출물로 |
| Spatial composition | CREATIVE에서 레이아웃 실험 허용 |

### 이유

공식 플러그인은 "매번 다른 미학"을 추구하므로, 기존 프로젝트에서 직접 트리거되면 디자인 시스템을 무시합니다. 원칙만 흡수하면 창의성은 확보하되 최종 산출물은 토큰 매핑을 거칩니다.

---

## 5. 워크플로우 예시

### 예시 1: 기존 프로젝트 대시보드 수정

```
사용자: "관리자 대시보드에 차트 위젯 추가해줘"
→ 모드: SYSTEMATIC
→ designer 에이전트 → 기존 Card 컴포넌트 재사용 검토
→ Component Spec 작성 (기존 토큰 사용)
→ Developer에게 핸드오프
```

### 예시 2: 새 서비스 랜딩페이지

```
사용자: "BurstExpress 라이브커머스 랜딩페이지 만들어줘"
→ 모드: CREATIVE
→ /design-creative 실행
→ Phase 1: 라이브커머스 맥락 파악
→ Phase 2: 미학 방향 (예: editorial + dynamic)
→ Phase 3: 토큰 브릿지 (신규 토큰 정의)
→ Phase 4: 산출물 (Direction + Token + Component Spec)
```

### 예시 3: 리브랜딩

```
사용자: "전체 UI 색상 체계를 바꾸고 싶어"
→ 모드: CREATIVE
→ /design-creative 실행
→ Design System Extension Spec 작성
→ 기존 토큰명 유지, 값 변경 제안
→ 영향 범위 분석 포함
```

---

## 다음 단계

1. [디자인 시스템 확장 규칙](32-design-system-extension.md) — 토큰 추가/변경 절차
2. [하네스 엔지니어링 가이드](29-harness-engineering.md) — Hook/Rules 상세
3. `/design-creative` 스킬 — `skills/design-creative/SKILL.md`
