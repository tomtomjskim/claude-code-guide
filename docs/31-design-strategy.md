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
    프로젝트별 Design Gate (선택)
      (커스텀 컨벤션 검증)
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

### 3.2 Design Gate Hook (프로젝트별 커스텀)

디자인 컨벤션은 프로젝트마다 다르므로(그리드 단위, 허용 폰트, 토큰 네이밍 등), 이 가이드에서 구체적 구현을 제공하지 않습니다. 대신 프로젝트별로 커스텀 게이트를 작성하는 보일러플레이트를 제공합니다.

#### 작성 가이드

```bash
#!/bin/bash
# your-project-design-gate.sh — 프로젝트 디자인 컨벤션 검사
# 아래 변수를 프로젝트에 맞게 수정하세요.

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 1. 대상 확장자 (프로젝트에 맞게 수정)
case "$FILE" in
  *.tsx|*.jsx|*.css|*.scss) ;;
  *) exit 0 ;;
esac
[ -f "$FILE" ] || exit 0

# 2. 프로젝트별 설정 — 여기를 수정
GRID_UNIT=4                    # 그리드 단위 (4px, 8px 등)
BANNED_FONTS="Arial|Helvetica" # 금지 폰트 (프로젝트 폰트 외)
TOKEN_PREFIX="--"              # CSS 변수 접두사

# 3. 검사 로직 (예시 — 프로젝트에 맞게 추가/제거)
VIOLATIONS=""

# hex 색상 검사 (토큰 정의, 주석 제외)
HEX_COUNT=$(grep -E '#[0-9a-fA-F]{3,8}' "$FILE" 2>/dev/null \
  | grep -v 'var(--' | grep -v '//' | grep -v "^\s*${TOKEN_PREFIX}" \
  | wc -l | tr -d ' ')
[ "$HEX_COUNT" -gt 0 ] && VIOLATIONS="${VIOLATIONS}하드코딩 색상 ${HEX_COUNT}건. "

# 금지 폰트 검사
grep -iqE "font-family:.*\b(${BANNED_FONTS})\b" "$FILE" 2>/dev/null \
  && VIOLATIONS="${VIOLATIONS}금지 폰트 사용. "

# 4. 결과 출력
if [ -n "$VIOLATIONS" ]; then
  echo "{\"decision\": \"warn\", \"reason\": \"디자인 컨벤션: ${VIOLATIONS}\"}"
fi
```

#### settings.json 등록 예시

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "bash hooks/scripts/your-project-design-gate.sh" }]
      }
    ]
  }
}
```

#### 핵심 원칙
- `decision: "warn"` 사용 — CREATIVE 모드의 의도적 일탈을 허용
- 검사 항목은 프로젝트 디자인 시스템에서 도출
- `.claude/rules/design-mode.md`가 AI 생성 시점에 이미 컨벤션을 유도하므로, 게이트는 **보조적 사후 검증**

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
