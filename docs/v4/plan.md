# v4.0 Audit Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/v4/design.md`에 정의된 4-phase coherence 감사를 실행하여 `docs/v4/strategy.md`(v4.0 전략 문서)를 산출한다.

**Architecture:** Sonnet Scout 1개가 드리프트 inventory 수집 → Main(현 세션)이 3개 워커용 digest로 분할 → Opus Worker 3개 병렬 분석(Contradictions/Redundancy/SSOT) → Main이 Coherence-first tie-breaker로 통합하여 strategy 문서 작성.

**Tech Stack:** Claude Code Agent tool (Sonnet, Opus subagents); Bash(grep/find/test/ls); Markdown. **코드 테스트 프레임워크 없음** — 검증은 파일 존재·구조·라인 수 bash 체크로 대체.

**Spec:** [`docs/v4/design.md`](./design.md) — 실행 전 반드시 통독 (특히 §3 프롬프트, §4 digest 분할, §5 통합 로직, §7 오류 매트릭스).

**Preserved constraints:** 한국어 기조, 메타 레포 성격, `.audit/` 휘발성 / `docs/v4/` 영구.

---

## Task Overview

| # | Task | Phase | Output | User Checkpoint |
|---|------|-------|--------|:---:|
| 1 | Phase 0 Preflight | — | `.audit/` dir | — |
| 2 | Dispatch Scout (Sonnet) | 1 | `.audit/inventory.md` | — |
| 3 | Verify Scout output | 1 | (검증만) | **✅ CP-1** |
| 4 | Generate 3 Digests | 2 | `.audit/digest-W{1,2,3}.md` | — |
| 5 | Verify Digests | 2 | (검증만) | **✅ CP-2** (비용 임박) |
| 6 | Dispatch 3 Workers in parallel | 3 | `.audit/result-W{1,2,3}.md` | — |
| 7 | Verify Worker outputs | 3 | (검증만) | **✅ CP-3** |
| 8 | Integrate → strategy.md | 4 | `docs/v4/strategy.md` | — |
| 9 | Commit + §8 self-validation | 4 | commit | **✅ CP-4** (종료) |

**체크포인트 철학**: CP-2만 "실행 전" 관문 (Opus ×3 병렬 디스패치는 돌이킬 수 없는 토큰 비용). 나머지는 "산출 후" 확인.

---

## File Structure

### Created during execution

| 경로 | Phase | 커밋 |
|------|-------|:----:|
| `.audit/` (directory) | 0 | — |
| `.audit/inventory.md` | 1 | X |
| `.audit/digest-W1.md` | 2 | X |
| `.audit/digest-W2.md` | 2 | X |
| `.audit/digest-W3.md` | 2 | X |
| `.audit/result-W1.md` | 3 | X |
| `.audit/result-W2.md` | 3 | X |
| `.audit/result-W3.md` | 3 | X |
| `docs/v4/strategy.md` | 4 | **O** |

### Read (from spec)

- `docs/v4/design.md` — 모든 프롬프트·로직의 SSOT (각 Task에서 `@` 참조)
- 레포 전체 (Scout의 SCOPE 범위 — design §3.2)

---

## Task 1: Phase 0 Preflight

**Files:**
- Check-only: `agents.yaml`, `agents/`, `prompts/`, `skills/`, `scripts/validate-system.sh`
- Create: `.audit/` (directory)

**Why**: `design.md §7.0` — Scout spawn 전 필수 경로 검증. 누락 시 glob이 비어 Scout이 silently PARTIAL inventory 생성.

- [ ] **Step 1: 작업 디렉토리 확인**

```bash
pwd
# Expected: /Users/jeongsik/develop/claude-code-guide
```

- [ ] **Step 2: 필수 경로 6개 존재·권한 검증**

```bash
cd /Users/jeongsik/develop/claude-code-guide && \
test -f agents.yaml                    && echo "OK  agents.yaml" || echo "FAIL agents.yaml" && \
test -d agents/                        && echo "OK  agents/" || echo "FAIL agents/" && \
test -d prompts/                       && echo "OK  prompts/" || echo "FAIL prompts/" && \
test -d skills/                        && echo "OK  skills/" || echo "FAIL skills/" && \
test -f scripts/validate-system.sh     && echo "OK  validate-system.sh" || echo "FAIL validate-system.sh" && \
test -w .                              && echo "OK  cwd writable" || echo "FAIL cwd writable"
```
Expected: 6개 `OK` — 하나라도 `FAIL` 시 **감사 중단** 후 사용자 보고 (design §7.0).

- [ ] **Step 3: `.audit/` 디렉토리 생성**

```bash
mkdir -p .audit && ls -la .audit/
```
Expected: 빈 디렉토리 `.audit/` 생성.

- [ ] **Step 4: `.gitignore` 확인 (`.audit/` 등록 여부)**

```bash
grep -n "^\.audit/$" .gitignore
```
Expected: 매칭 라인 출력. 없으면 **중단** (이전 커밋에서 등록됐어야 함 — 누락 시 결과 파일이 실수로 커밋될 리스크).

**누락 시 remediation**: `echo -e "\n# v4.0 audit ephemeral artifacts\n.audit/" >> .gitignore && git add .gitignore && git commit -m "chore: add .audit/ to .gitignore (v4 audit preflight)"` 실행 후 이 Step 재확인.

- [ ] **Step 5: 커밋 없음 — Phase 0은 검증만**

---

## Task 2: Dispatch Scout (Phase 1)

**Files:**
- Will create (by Scout): `.audit/inventory.md`

**Why**: `design.md §2.1` + `§3.2` — Sonnet Scout이 7개 드리프트 카테고리를 수집하여 이후 모든 판단의 근거 파일 생성.

- [ ] **Step 1: Scout 프롬프트 조립 확인**

design.md `§3.1 공통 프리앰블` + `§3.2 Scout` 전체를 prompt로 결합. 아래 명시 슬롯 모두 포함되어야:
- 공통 프리앰블 (작업 루트, Tie-breaker, 인용 필수, 한국어, 결과 파일 쓰기)
- SCOPE (읽기 허용/금지 경로, 쓰기 허용 `.audit/inventory.md`)
- RULES (Bash 화이트리스트, PARTIAL 허용)
- TASK (7 섹션 생성 순서)
- RETURN (파일 경로 + 복귀 포맷)

- [ ] **Step 2: Agent 도구로 Scout 디스패치 (Sonnet)**

```
Agent(
  description: "v4 audit Scout — drift inventory",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: <design §3.1 + §3.2 전문>
)
```

중요:
- `model: "sonnet"` 지정 필수 (기본값은 agent 정의에 의존)
- 서브에이전트 내부에서 PreToolUse hook 미적용 — SCOPE·RULES가 유일한 가드레일
- 복귀 메시지는 `PASS | .audit/inventory.md | <발견 수>, <Top 3 카테고리>` 3줄

- [ ] **Step 3: 복귀 메시지 확인**

Expected: `PASS | .audit/inventory.md | ...` 또는 `PARTIAL | ...`.
- `PASS` → Task 3로 진행
- `PARTIAL` → Task 3에서 blind-spot 확인
- 기타(FAIL/타임아웃) → `design §7.1` "Scout 완전 실패" 경로: Main이 `preflight-collect.sh` 직접 실행 + 수동 grep으로 재구축

- [ ] **Step 4: 커밋 없음 — `.audit/`는 gitignored**

---

## Task 3: Verify Scout Output (CP-1)

**Files:**
- Read: `.audit/inventory.md`

**Why**: inventory 품질이 이후 3 워커 품질의 상한. 불량 시 재실행 또는 수동 재구축 결정.

- [ ] **Step 1: 파일 존재 + 크기 확인**

```bash
test -f .audit/inventory.md && wc -l .audit/inventory.md
```
Expected: 파일 존재. 라인 수 **50~500**.
- 50 미만 → 품질 의심, Scout 재디스패치 후보
- 500 초과 → Scout가 캡을 어김, RULES 위반 — 사용자 보고

- [ ] **Step 2: 7 섹션 헤더 존재 확인**

```bash
grep -c "^## [1-7]\." .audit/inventory.md
```
Expected: `7` (정확히 7개 섹션). 7 미만 시 PARTIAL, `§7.1 Scout PARTIAL` 경로: 누락 섹션을 digest에서 비우고 blind-spot 태그.

- [ ] **Step 3: 섹션별 내용 미리보기**

```bash
awk '/^## /{print NR": "$0}' .audit/inventory.md
```
Expected: 7개 섹션 제목 출력 — 각 섹션 명이 design §3.2 TASK의 7개 카테고리와 매칭되는지 시각 확인.

- [ ] **Step 4: 인용 형식 sampling (3줄 랜덤)**

```bash
grep -E "\.(md|yaml|sh):[0-9]+" .audit/inventory.md | head -3
```
Expected: `file:line | context` 형식 3줄. 인용 없으면 Scout이 RULES 어김.

- [ ] **✅ User Checkpoint 1 (CP-1):**

사용자에게 inventory 품질 보고:
- 총 라인 수, 섹션 수, PASS/PARTIAL
- Scout 복귀 메시지의 Top 3 카테고리
- 사용자가 `.audit/inventory.md`를 직접 읽고 **진행/재실행/중단** 선택
- 재실행 선택 시 Task 2 반복 (최대 1회, 이후 수동 재구축)

---

## Task 4: Generate 3 Digests (Phase 2)

**Files:**
- Read: `.audit/inventory.md`
- Create: `.audit/digest-W1.md`, `.audit/digest-W2.md`, `.audit/digest-W3.md`

**Why**: `design.md §4` — 워커들이 inventory를 재스캔하지 않도록 Main이 렌즈별로 증거를 미리 재단. 워커 프롬프트의 SCOPE에 digest 경로만 열어주기 때문에 **이 단계 품질이 워커 판단의 상한**.

- [ ] **Step 1: inventory.md 전체 읽기 (Main)**

Read 도구로 `.audit/inventory.md` 전체 로드. 7 섹션 내용을 메모리에 보유.

- [ ] **Step 2: W1 Digest 작성 (Contradictions)**

`design §4.1 매핑표`에 따라 W1에 할당된 섹션(1강·3강·4강·5·6강)만 필터링 + `§4.3 W1용 connecting notes`(버전 드리프트↔validate 공백, 에이전트 이름 3-way 불일치) 추가.

`§4.2 Digest 스켈레톤` 4개 블록(Filtered Evidence / Connecting Notes / Explicit Read Scope / Return Contract Reminder) 구조 엄수.

Write `.audit/digest-W1.md`.

- [ ] **Step 3: W1 Digest 검증**

```bash
test -f .audit/digest-W1.md && \
grep -c "^## " .audit/digest-W1.md && \
wc -l .audit/digest-W1.md
```
Expected: 파일 존재, 4 섹션(`## 1.` ~ `## 4.`), 30~200 라인.

- [ ] **Step 4: W2 Digest 작성 (Redundancy)**

W2에 할당된 섹션(2강·4·5강·7강) 필터링 + W2 connecting notes(skills description 중복↔CUSTOMIZE 패턴, hooks 3중 네이밍↔설명 차이) 추가.

Write `.audit/digest-W2.md`. 검증은 Step 3와 동일 구조.

- [ ] **Step 5: W3 Digest 작성 (SSOT)**

W3에 할당된 섹션(1강·3·4강·5·7) 필터링 + W3 connecting notes(**7개 고정 체크리스트**: 버전 숫자·에이전트 목록·스킬 목록·PDARR 흐름·모델 라우팅·프리셋 정의·Hooks 3중 네이밍 구별) 추가.

Write `.audit/digest-W3.md`. 검증은 Step 3와 동일.

- [ ] **Step 6: 3 digest 일괄 검증**

```bash
ls -la .audit/digest-W{1,2,3}.md && \
for f in .audit/digest-W{1,2,3}.md; do echo "=== $f ==="; head -5 "$f"; done
```
Expected: 3 파일 모두 존재, 각 파일 머리 5줄에 `# Digest — Worker N · <Focus>` 헤더.

- [ ] **Step 7: 커밋 없음**

---

## Task 5: Digest Quality Checkpoint (CP-2)

**Why**: 다음 Task에서 Opus 서브에이전트 3개를 병렬 디스패치 — **비용 환불 불가**. 디스패치 전 digest 품질을 관문에서 확인.

- [ ] **Step 1: 각 digest 라인 수 + 인용 파일 수**

```bash
for f in .audit/digest-W{1,2,3}.md; do
  lines=$(wc -l < "$f")
  refs=$(grep -oE "\.(md|yaml|sh):[0-9]+" "$f" | sort -u | wc -l)
  echo "$f: $lines lines, $refs unique citations"
done
```
Expected: 각 30~200 lines, 5~30 unique citations. 인용 0이면 digest 품질 불량.

- [ ] **Step 2: Connecting Notes 존재 확인**

```bash
grep -A3 "Main's Connecting Notes" .audit/digest-W*.md | head -30
```
Expected: 각 워커 digest에 `§4.3` 명시된 연결 노트 본문 존재.

- [ ] **✅ User Checkpoint 2 (CP-2):**

사용자에게 보고:
- 3 digest 크기·인용 수·connecting notes 유무
- 다음 단계: **Opus ×3 병렬 디스패치 (예상 비용 구간 제시)**
- 사용자 선택: **병렬 디스패치 / digest 수정 / 중단**
- 중단 선택 시 감사 전체 일시 정지, `.audit/` 보존하고 세션 종료 — 재개 시 Task 6부터

---

## Task 6: Dispatch 3 Workers in Parallel (Phase 3)

**Files:**
- Will create (by Workers): `.audit/result-W1.md`, `.audit/result-W2.md`, `.audit/result-W3.md`

**Why**: `design.md §3.3/§3.4/§3.5` — 3 워커가 각 렌즈로 독립 분석. 병렬로 실행해야 시간 최소화 + Result Pipe 패턴으로 오케스트레이터 컨텍스트 보호.

- [ ] **Step 1: 병렬 디스패치 원칙 재확인**

- **1개 메시지에 Agent 도구 3번** (병렬 보장)
- 각 워커 `model: "opus"` 명시
- 각 프롬프트는 `design §3.1 공통 프리앰블` + `§3.{3,4,5} 해당 워커 전문`
- SCOPE: 해당 워커의 digest 파일만 읽기 허용, `result-W{N}.md`만 쓰기 허용

- [ ] **Step 2: Worker 1 (Contradictions, Opus) 프롬프트 조립**

`design §3.3` 전문 + 공통 프리앰블. TASK의 "우선 탐색 지점" 5개 중 버전 드리프트를 가장 먼저.

- [ ] **Step 3: Worker 2 (Redundancy, Opus) 프롬프트 조립**

`design §3.4` 전문 + 공통 프리앰블. TASK의 6개 통합 후보 전부 순회.

- [ ] **Step 4: Worker 3 (SSOT, Opus) 프롬프트 조립**

`design §3.5` 전문 + 공통 프리앰블. TASK의 **7개 고정 체크리스트** 전부 순회 (최근 반영된 §4.3 수정 반영 확인).

- [ ] **Step 5: 3 Agent 호출을 1 메시지에 배치하여 병렬 실행**

```
<1 single message>
  Agent(description: "v4 W1 Contradictions", subagent_type: "general-purpose",
        model: "opus", prompt: <§3.1 + §3.3>)
  Agent(description: "v4 W2 Redundancy", subagent_type: "general-purpose",
        model: "opus", prompt: <§3.1 + §3.4>)
  Agent(description: "v4 W3 SSOT", subagent_type: "general-purpose",
        model: "opus", prompt: <§3.1 + §3.5>)
</1 single message>
```

- [ ] **Step 6: 3개 복귀 메시지 수집**

각자 예상 포맷 (design §3.3/§3.4/§3.5 RETURN):
- W1: `PASS | .audit/result-W1.md | C:N H:N M:N L:N, Top3 blockers`
- W2: `PASS | .audit/result-W2.md | Groups:N Merges:N Renames:N Keeps:N, Top3 wins`
- W3: `PASS | .audit/result-W3.md | Violations:N CanonicalFiles:N StopHoldingState:N, Top3 unifications`

**포맷 드리프트 허용**: Opus 워커는 가끔 RETURN 라인을 장식하거나 줄 수 초과. 판정은 **파일 존재 + Task 7의 구조 검증**이 우선이며 복귀 라인 포맷은 참고용. 복귀가 깨져도 파일이 유효하면 진행.

- [ ] **Step 7: BLOCKED/PARTIAL 처리 (해당 워커만, 최대 1회 재디스패치)**

`design §7.1` 규정:
- 워커 BLOCKED → 해당 워커 digest에 2~3 파일 추가 + 1회 재디스패치
- 2차 BLOCKED → 나머지 2 워커로 진행 + strategy에 `W_i 커버리지 누락` 기록
- PARTIAL (캡 초과) → 그대로 사용, Decision Log에 기록

- [ ] **Step 8: 커밋 없음**

---

## Task 7: Verify Worker Outputs (CP-3)

**Files:**
- Read: `.audit/result-W1.md`, `.audit/result-W2.md`, `.audit/result-W3.md`

- [ ] **Step 1: 3 파일 존재 확인**

```bash
ls -la .audit/result-W{1,2,3}.md 2>&1
```
Expected: 3 파일 모두 존재. 누락 시 해당 워커 BLOCKED 미복구 상태 — 사용자 보고.

- [ ] **Step 2: 각 파일 섹션 구조 sampling**

```bash
for f in .audit/result-W{1,2,3}.md; do
  echo "=== $f ==="
  grep "^##\|^###" "$f" | head -10
  echo ""
done
```
Expected:
- W1: CRITICAL/HIGH/MEDIUM/LOW 섹션
- W2: Group 1, 2, 3, ... 그룹 섹션
- W3: Violation 1, 2, 3, ... 위반 섹션

- [ ] **Step 3: 총 발견 항목 수 집계**

```bash
echo "W1 findings: $(grep -cE '^(### )?[0-9]+\.' .audit/result-W1.md)"
echo "W2 groups  : $(grep -cE '^(### )?Group [0-9]+' .audit/result-W2.md)"
echo "W3 viols   : $(grep -cE '^(### )?Violation [0-9]+' .audit/result-W3.md)"
```
합계 **5 이상** 요망 (design §8 Success Criteria: "백로그 총 항목 ≥ 5").

- [ ] **✅ User Checkpoint 3 (CP-3):**

사용자에게 보고:
- 3 워커 복귀 메시지 요약
- 총 발견 수, 심각도 분포
- W1 Top3 blockers / W2 Top3 wins / W3 Top3 unifications 복귀 메시지 인라인
- 사용자 선택: **통합 진행 / 특정 워커 재실행 / 중단**

---

## Task 8: Integrate → strategy.md (Phase 4)

**Files:**
- Read: `.audit/result-W1.md`, `.audit/result-W2.md`, `.audit/result-W3.md`
- Create: `docs/v4/strategy.md`

**Why**: `design.md §5` + `§6` — 3 워커 결과를 Coherence-first tie-breaker로 통합하여 v4.0 단일 전략 문서 산출.

- [ ] **Step 1: 3 result 파일 전체 읽기**

Read 도구로 3 파일 전체 로드.

- [ ] **Step 2: 정규화 — 중복 이슈 병합 (W1 > W3 > W2 선행)**

`design §5.1`:
- 동일 파일 인용이 여러 워커에 걸쳐 등장 → W1에 병합, 하위는 cross-ref
- cross-ref 표기는 strategy 본문에 `(also flagged by W_i)` 형태

- [ ] **Step 3: Tie-breaker 5단계 사다리 적용**

`design §5.2`:
1. SSOT 생성? → 생성하는 쪽
2. Drift surface 축소? → 축소하는 쪽
3. 세 축 동기화? → 동기화하는 쪽
4. YAGNI → 작은 변경
5. 동률 → Main 판단 + **§6 Decision Log 필수 기록**

- [ ] **Step 4: P0/P1/P2 라벨링**

`design §5.3`:
- P0: validate 실패 or 사용자 설치 실패 or 레포가 자기 규칙 위반
- P1: SSOT 위반 + 영향 반경 3+ 파일
- P2: 표면 정리, 문서 IA

- [ ] **Step 5: Breaking Changes 추출 + Migration Note**

`design §5.4`:
- `breaking: yes` 필터링
- 각 항목에 `재설치 시 자동 반영` / `CUSTOMIZE 재작성 필요` / `settings.local.json 수동 병합` 중 하나 부착

- [ ] **Step 6: `docs/v4/strategy.md` 작성 (6 섹션)**

`design §6 스켈레톤` 구조 엄수:
- §1 Vision (3~5줄, coherence 부채 청산 서사)
- §2 Breaking Changes (표)
- §3 Prioritized Backlog (P0/P1/P2)
- §4 Migration Scenarios (2 시나리오)
- §5 Success Criteria (6 체크리스트)
- §6 Decision Log (동률 판정만)

- [ ] **Step 7: 작성 완료 검증**

```bash
test -f docs/v4/strategy.md && \
grep -c "^## [1-6]\." docs/v4/strategy.md && \
wc -l docs/v4/strategy.md
```
Expected: 파일 존재, 6 섹션, 라인 수 100~800.

- [ ] **Step 8: 커밋은 Task 9에서 (검증 후)**

---

## Task 9: Commit strategy.md + §8 Self-validation

**Files:**
- Read: `docs/v4/strategy.md`, `docs/v4/design.md`
- Commit: `docs/v4/strategy.md`

**Why**: `design.md §8` — 이 감사 실행 자체의 Success Criteria 검증.

- [ ] **Step 1: design.md §8 체크리스트 6개 검증**

각 항목을 Read + bash로 확인:

```bash
# 1. inventory 7 섹션 또는 blind-spot 태그
grep -c "^## [1-7]\." .audit/inventory.md
# 2. 3 result 파일 존재
ls .audit/result-W{1,2,3}.md 2>&1
# 3. strategy 6 섹션
grep -c "^## [1-6]\." docs/v4/strategy.md
# 4. 백로그 총 항목 ≥ 5
grep -cE "^- |^\*|^[0-9]+\." docs/v4/strategy.md
# 5. Breaking Changes ≥ 1
awk '/^## 2\./,/^## 3\./' docs/v4/strategy.md | grep -c "^|"
# 6. Decision Log (동률 판정 있으면 근거 명시)
awk '/^## 6\./,/^---/' docs/v4/strategy.md | head -50
```

- [ ] **Step 2: strategy.md와 design.md 교차 일관성 한 번 더**

strategy §5 Success Criteria의 6 체크리스트가 design §6 스켈레톤에 명시된 그대로 박혀있는지 시각 확인.

- [ ] **Step 3: 커밋 준비 — staging 확인**

```bash
git add docs/v4/strategy.md && \
git status --short
```
Expected: `A  docs/v4/strategy.md` 1줄만 (다른 파일 오염 없음 — `.audit/`는 gitignored).

- [ ] **Step 4: 커밋 (HEREDOC + Co-Authored-By)**

```bash
git commit -m "$(cat <<'EOF'
feat(v4): v4.0 strategy — 감사 결과 통합

3 Opus Workers(Contradictions/Redundancy/SSOT)의 결과를 Coherence-first
tie-breaker로 통합. docs/v4/strategy.md 6 섹션:
  §1 Vision
  §2 Breaking Changes (N건)
  §3 Prioritized Backlog — P0:N, P1:N, P2:N
  §4 Migration Scenarios
  §5 Success Criteria
  §6 Decision Log

감사 실행 설계: docs/v4/design.md
감사 실행 계획: docs/v4/plan.md
자가 검증: design.md §8 체크리스트 N/6 pass

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

커밋 메시지의 N 자리는 실제 수치로 치환.

- [ ] **Step 5: 커밋 확인**

```bash
git log --oneline -5
```
Expected: 최상단에 `feat(v4): v4.0 strategy ...` 커밋.

- [ ] **✅ User Checkpoint 4 (CP-4) — 최종:**

사용자에게 최종 보고:
- strategy.md 경로 + 6 섹션 요약
- §8 체크리스트 pass/fail 6건
- Breaking Changes 목록 (1줄씩)
- P0/P1/P2 항목 수
- Decision Log에 동률 판정이 있다면 해당 항목
- **다음 단계 제안**: v4.0 실제 구현 (각 P0부터 별도 `/run` or 새 세션에서 `writing-plans` → `executing-plans`)

---

## Task 10: Cleanup & Handoff

**Why**: `.audit/` 휘발성 산출물 정리 + v4.0 실제 구현 세션으로 핸드오프.

- [ ] **Step 1: `.audit/` 보존 결정 (사용자 선택)**

```bash
du -sh .audit/
```
- 보존 → 현 세션에서 참조 필요 시 편리
- 삭제 → `rm -rf .audit/` (언제든 재실행 가능, gitignored라 영향 없음)

- [ ] **Step 2: 핸드오프 문서 작성 (선택)**

v4.0 실제 구현을 다른 세션에서 진행할 경우, strategy §3 백로그 P0부터 순서대로 새 브레인스토밍 → writing-plans → executing-plans 사이클을 각각 돌림.

- [ ] **Step 3: 커밋 없음**

---

## Related Skills

- `@superpowers:subagent-driven-development` — Worker 디스패치 패턴 (Task 6)
- `@superpowers:executing-plans` — 인라인 실행 (대체 경로)
- `@superpowers:verification-before-completion` — 각 Task의 검증 단계
- `@superpowers:systematic-debugging` — BLOCKED 재디스패치 시

## Anti-patterns to Avoid

- **Workers 순차 디스패치** — `design §2.4` 위반. 반드시 1 메시지 3 Agent 호출.
- **inventory.md 워커에 그대로 주입** — Task 4 digest 생성을 건너뛰면 Workers가 중복 스캔 + 토큰 3~4배.
- **strategy.md를 결과 파일 단순 concat으로 작성** — Tie-breaker 적용 없음 = Coherence-first 원칙 실패.
- **`.audit/` 커밋** — `.gitignore` 우회는 드리프트 재생산. 영구 산출은 `docs/v4/`만.
- **Scout 재디스패치 무한** — 1회로 제한. 2회째 실패 시 수동 재구축 (§7.1).

## Remaining Open Decisions

실행 중 발생 가능한 판단 포인트 (CP에서 사용자 승인 필요):

1. Scout inventory 라인 수가 50 미만 → 재실행 or 수동 재구축?
2. CP-2에서 Opus ×3 병렬 비용 허용 여부
3. W1 CRITICAL 0건, HIGH 0건이면 v4.0 명분 부족 — downgrade 검토 필요
4. Decision Log 항목 5개 초과 → 감사 품질 자기 의심, 재검토 권고

---

**Plan status**: Complete, ready for execution.
**Next**: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`.
