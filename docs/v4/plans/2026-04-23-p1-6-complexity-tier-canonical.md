# P1-6 Complexity Tier Canonical Implementation Plan

> **For agentic workers:** Inline execution planned due to small scope (2 files). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/v4/strategy.md` §3 P1-6 구현 — Complexity Tier(Trivial/Simple/Medium/Complex) 임계값 drift를 해소. `.claude/rules/subagent-strategy.md:17-22`을 canonical로 지정하고, `skills/dispatch/SKILL.md`와 `docs/33-subagent-efficiency.md`가 canonical을 참조/인용하는 구조로 정리.

**Architecture:** 1-tier canonical — `.claude/rules/subagent-strategy.md` 파일 수 기준 테이블 단독 SSOT. 두 소비자 문서(dispatch/SKILL.md, docs/33)는 canonical 링크 + 필요 시 mirror 테이블(skills/dispatch은 라우팅 flow 컨텍스트상 테이블 직접 보유가 UX상 가치 있음, docs/33은 narrative 문서라 링크만).

**Tech Stack:** Markdown. 테스트 없음 — 검증은 grep 기반 참조 무결성 sweep.

**Spec:**
- [`docs/v4/strategy.md`](../strategy.md) §3 P1-6 (W3 V8)

**Preserved constraints:**
- 한국어 기조
- P0-A, P1-1, P1-2+P1-7+P1-8 Bundle C 상태 위에 쌓임
- `/dispatch` UX: Quick Assessment 프레임(키워드 → 범위 보정)은 스킬 고유 가치이므로 **구조 보존**, 임계값만 canonical 정렬

---

## Verified Pre-conditions (2026-04-23, Bundle C 커밋 cc129ad 이후)

### Canonical 후보: `.claude/rules/subagent-strategy.md:17-22`

```
| 복잡도 | 판정 기준 | 실행 방식 |
|--------|----------|----------|
| Trivial | 파일 ≤2, 변경 ≤20줄 | 메인이 직접 수행 |
| Simple | 파일 ≤4, 변경 ≤100줄 | 메인 직접 또는 에이전트 1개 |
| Medium | 파일 ≤8 | 메인이 digest 생성 + Worker 1-2개 |
| Complex | 파일 >8 또는 서비스 2+ | Scout(Haiku) → digest → Worker N개(Sonnet) |
```

**핵심 축**: 파일 수. 보조: 변경 줄 수(Trivial/Simple), 서비스 수(Complex).

### 중복: `docs/33-subagent-efficiency.md:182-188`

```
Dispatch 판정 기준 (기계적):
  파일 수 ≤ 2, 변경 ≤ 20줄  → Trivial
  파일 수 ≤ 4, 변경 ≤ 100줄 → Simple
  파일 수 ≤ 8               → Medium
  파일 수 > 8 또는 서비스 2+ → Complex
```

**상태**: canonical과 정확히 동일. Drift 없음 but SSOT 위반(같은 내용을 두 곳 유지).

### Drift 실존: `skills/dispatch/SKILL.md:53-57`

```
- **Trivial**: 1-2줄 수정, 오타, 설정값 변경
- **Simple**: 단일 파일, 1-2개 함수
- **Medium**: 2-5개 파일, 1-2개 레이어
- **Complex**: 6개+ 파일, 3개+ 레이어, 프론트+백엔드 동시
```

**Drift 유형**:
- Trivial에서 "파일 수" 기준이 아닌 "줄 수"만 명시 — canonical의 "파일 ≤2"와 축 불일치
- Simple에서 "단일 파일" (=1) — canonical의 "≤4"와 임계값 불일치
- Medium에서 "2-5개 파일" — canonical의 "≤8"과 상한 불일치
- Complex에서 "6개+" — canonical "8+"와 하한 불일치
- "레이어 수", "프론트+백엔드" 축은 canonical에 없음 — dispatch 고유 보조 지표

### CLAUDE.md 현황 (P1-2 이후): line 65

> Complexity tiers (Trivial / Simple / Medium / Complex) in `/dispatch` drive which subset of the flow runs. Keep these tier names consistent across skills and docs — `/dispatch` and `.claude/rules/subagent-strategy.md` both reference them.

**상태**: 이름만 언급, 임계값 없음. 수정 불필요.

---

## File Structure

### Modified

- `skills/dispatch/SKILL.md` — L47-57 복잡도 판단 기준 블록을 canonical 정렬 + 링크로 교체. Keyword-based framing 보존.
- `docs/33-subagent-efficiency.md` — L182-194 중복 블록을 canonical 링크 + 핵심 요약으로 축소.

### Created

- `docs/v4/plans/2026-04-23-p1-6-complexity-tier-canonical.md` — 이 플랜.

### Not modified (out of scope)

- `.claude/rules/subagent-strategy.md` — canonical SSOT, 내용 불변
- `CLAUDE.md` — 이미 P1-2 커밋에서 tier 이름 언급만 유지(임계값 없음) 상태, 추가 수정 없음
- `scripts/validate-system.sh` — 신규 체크 추가 불필요 (threshold drift는 프레임워크 자체 불일치이므로 단순 pattern 매칭으로 검증 어려움)
- 다른 skills (P1-4, P1-9 범위)

---

## Task 1: `skills/dispatch/SKILL.md` 임계값 canonical 정렬

**Why:** dispatch는 라우팅 시작점이므로 임계값이 틀리면 사용자가 잘못된 실행 경로로 유도됨. Canonical에 정렬하여 일관성 확보하되, keyword + 범위 보정이라는 dispatch 고유 UX는 보존.

- [ ] **Step 1: L47-57 블록 교체**

**old_string:**
```
**복잡도 판단 기준**: <!-- CUSTOMIZE: point to your project's complexity matrix if available -->

#### 3.1 키워드 + 범위 기반 판단

키워드로 초기 판단 후, 관련 파일 수 / 아키텍처 레이어 / 프론트+백엔드 여부로 보정하여 최종 판정:
- **Trivial**: 1-2줄 수정, 오타, 설정값 변경
- **Simple**: 단일 파일, 1-2개 함수
- **Medium**: 2-5개 파일, 1-2개 레이어
- **Complex**: 6개+ 파일, 3개+ 레이어, 프론트+백엔드 동시
```

**new_string:**
```
**복잡도 판단 기준**: canonical은 [`.claude/rules/subagent-strategy.md#tiered-dispatch--복잡도별-실행-방식`](../../.claude/rules/subagent-strategy.md). 아래 표는 canonical을 mirror한 것 + 보조 지표.

#### 3.1 Canonical 임계값 (파일 수 기준)

| 복잡도 | 판정 기준 | 보조 지표 (dispatch 고유) |
|--------|----------|--------------------------|
| **Trivial** | 파일 ≤2, 변경 ≤20줄 | 오타·설정값·1-2줄 수정류 |
| **Simple** | 파일 ≤4, 변경 ≤100줄 | 1-2개 함수, 1 레이어 |
| **Medium** | 파일 ≤8 | 1-2 레이어 |
| **Complex** | 파일 >8 또는 서비스 2+ | 3+ 레이어, 프론트+백엔드 동시 |

**보조 지표**는 canonical 기준에 해당하지 않는 초기 키워드 판단 시 보정 힌트. 최종 판정은 항상 canonical의 파일 수 / 서비스 수 기준이 우선.
```

- [ ] **Step 2: 검증**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) canonical 링크 존재
grep -n "rules/subagent-strategy.md" skills/dispatch/SKILL.md
# 기대: ≥1 (임계값 블록의 canonical 링크)

# (b) 드리프트 임계값 표현 잔존 없음
grep -nE "1-2줄 수정.*오타|단일 파일, 1-2개 함수|2-5개 파일, 1-2개 레이어|6개\+ 파일, 3개\+ 레이어" skills/dispatch/SKILL.md
# 기대: 출력 없음

# (c) canonical 정렬된 임계값 반영
grep -cE "파일 ≤2.*변경 ≤20줄|파일 ≤4.*변경 ≤100줄|파일 ≤8|파일 >8.*서비스 2\+" skills/dispatch/SKILL.md
# 기대: 4
```

---

## Task 2: `docs/33-subagent-efficiency.md` 중복 테이블 축소

**Why:** docs/33 L182-188의 "Dispatch 판정 기준" 블록은 canonical과 정확히 동일한 내용. 같은 테이블을 두 곳에 유지하는 것은 향후 threshold 조정 시 drift 재발의 근원. Canonical 링크로 교체하되, "Tiered Dispatch 전략" narrative 내 위치이므로 핵심 요약 1-2줄 보존.

- [ ] **Step 1: L182-194 블록 교체**

**old_string:**
```
```
Dispatch 판정 기준 (기계적):
  파일 수 ≤ 2, 변경 ≤ 20줄  → Trivial
  파일 수 ≤ 4, 변경 ≤ 100줄 → Simple
  파일 수 ≤ 8               → Medium
  파일 수 > 8 또는 서비스 2+ → Complex

실행 방식:
  Trivial → 메인이 직접 수행 (에이전트 없음)
  Simple  → 메인이 직접 수행 또는 에이전트 1개
  Medium  → 메인이 Read/Grep으로 digest 생성 + Worker 1-2개
  Complex → Scout(Haiku) → digest → Worker N개(Sonnet)
```
```

**new_string:**
```
임계값과 실행 방식은 canonical에 정의: [`.claude/rules/subagent-strategy.md#tiered-dispatch--복잡도별-실행-방식`](../.claude/rules/subagent-strategy.md).

요약:
- 판정 축은 **파일 수**(보조: 변경 줄 수·서비스 수)
- 4단계(Trivial/Simple/Medium/Complex) 각각에 고유한 실행 방식(메인 직접 → 에이전트 1개 → digest + Worker 1-2 → Scout + Worker N)
```

- [ ] **Step 2: 검증**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) 중복 테이블 제거됨
grep -cE "파일 수 ≤ 2.*변경 ≤ 20줄|파일 수 ≤ 4.*변경 ≤ 100줄" docs/33-subagent-efficiency.md
# 기대: 0

# (b) canonical 링크 존재
grep -n "rules/subagent-strategy.md#tiered-dispatch" docs/33-subagent-efficiency.md
# 기대: ≥1

# (c) "전략 5: Tiered Dispatch" 섹션 헤더 보존
grep -n "^### 전략 5: Tiered Dispatch" docs/33-subagent-efficiency.md
# 기대: 1
```

---

## Task 3: 통합 검증 sweep

- [ ] **Step 1: 참조 무결성 + 앵커 slug 유효성**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) canonical 앵커 일관 (두 consumer 모두 같은 slug 사용)
grep -h "rules/subagent-strategy.md#" skills/dispatch/SKILL.md docs/33-subagent-efficiency.md | sort -u
# 기대: 1줄 (동일 앵커)

# (b) subagent-strategy.md heading이 앵커와 매칭
grep "^## Tiered Dispatch" .claude/rules/subagent-strategy.md
# 기대: "## Tiered Dispatch — 복잡도별 실행 방식"
# Anchor slug: `tiered-dispatch--복잡도별-실행-방식` (GitHub slugifier 기준)

# (c) Drift 어휘 잔존 검사 — 구버전 임계값 어휘 ("6개+", "2-5개", "3개+" 등)
grep -rnE "6개\+ 파일|2-5개 파일|3개\+ 레이어" skills/dispatch/SKILL.md docs/33-subagent-efficiency.md
# 기대: 출력 없음

# (d) validate 재실행 — baseline 유지
bash scripts/install-skills.sh /tmp/p1-6-check --team --force 2>&1 | tail -3
bash scripts/validate-system.sh 2>&1 | grep -E "^Errors:|^Warnings:|categories"
# 기대: Errors: 6 (baseline), Warnings: 0, "Checks: 19 categories"
```

- [ ] **Step 2: git diff sanity**

```bash
git status --short
git diff --stat
```

기대:
- `M  skills/dispatch/SKILL.md` (~10줄 변경)
- `M  docs/33-subagent-efficiency.md` (~14줄 변경)
- `A  docs/v4/plans/2026-04-23-p1-6-complexity-tier-canonical.md`

---

## Task 4: 단일 커밋

- [ ] **Step 1: 스테이징 + 커밋**

```bash
git add skills/dispatch/SKILL.md docs/33-subagent-efficiency.md docs/v4/plans/2026-04-23-p1-6-complexity-tier-canonical.md
git commit -m "$(cat <<'EOF'
feat(v4 P1-6): Complexity Tier 임계값 canonical 통일

strategy.md §3 P1-6 구현. skills/dispatch/SKILL.md에서 복잡도 판단
기준이 canonical(.claude/rules/subagent-strategy.md)과 다른 프레임워크
(줄 수 + 레이어 + 프론트/백 혼합)로 선언되어 있던 drift를 해소.

canonical: .claude/rules/subagent-strategy.md:17-22 (파일 수 기준 표)

변경 사항:
- skills/dispatch/SKILL.md L47-57 — 독자 임계값(1-2줄/단일 파일/2-5개/
  6개+)을 canonical mirror 테이블로 교체. keyword-based Quick Assessment
  framing은 보존, canonical 링크 1줄 추가. 보조 지표(레이어, 프론트+백)는
  "dispatch 고유 초기 힌트"로 위치 재정의
- docs/33-subagent-efficiency.md L182-194 — canonical과 정확히 동일했던
  중복 테이블을 canonical 링크 + 요약 2줄로 축소 (Tiered Dispatch
  전략 narrative 흐름은 보존)

Drift 해소 결과:
- Trivial: dispatch "1-2줄" → canonical "파일 ≤2, 변경 ≤20줄"
- Simple: dispatch "단일 파일" → canonical "파일 ≤4, 변경 ≤100줄"
- Medium: dispatch "2-5개" → canonical "파일 ≤8"
- Complex: dispatch "6개+" → canonical "파일 >8 또는 서비스 2+"

검증:
- canonical 앵커 2곳(skills/dispatch + docs/33)에서 동일 slug 사용
- "6개+ 파일", "2-5개 파일" 등 구 drift 어휘 0건
- validate-system.sh baseline 유지 (Errors 6 PyYAML env, Warnings 0)

Non-breaking:
- /dispatch UX 구조(Quick Assessment 프레임, Phase 1-4) 보존
- tier 이름 4종(Trivial/Simple/Medium/Complex) 불변
- docs/33 "전략 5: Tiered Dispatch" 섹션 헤더·narrative 보존

Out of scope (후속 슬라이스):
- P1-4 스킬 목록 canonical 통일
- P1-9 reflect/complete/organize-docs description
- P1-5 (B2) hooks/scripts rename

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 2: 커밋 사후 검증 + 푸시**

```bash
git log --oneline -3
git show --stat HEAD
git status
# working tree clean 확인 후 git push
```
