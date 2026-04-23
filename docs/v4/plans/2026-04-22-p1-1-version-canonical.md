# P1-1 Version Canonical Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/v4/strategy.md` §3 P1-1 (+ §6 Decision 1) 구현 — 시스템 버전 주장이 `agents.yaml:4`에서만 선언되고 나머지는 드리프트 surface를 제거하거나 단일 변수로 집중되도록 repo 전반의 "drift 레이블"을 정리한다.

**Architecture:** 3개의 성격이 다른 변경을 한 커밋으로 묶는다 —
(a) 사용자 대면 문서(README/QUICKSTART)의 제목·선전 문구에서 시스템 버전 제거,
(b) 4개 스킬 프리셋 섹션 헤더의 `(v3.0)` 드리프트 레이블 제거,
(c) `selfcheck-token-waste.sh` ↔ `docs/28`의 `(v3.3)` 쌍을 동기 삭제,
(d) `validate-system.sh` 내부 canonical 버전 주장을 단일 `EXPECTED_VERSION` 변수로 집중,
(e) `CLAUDE.md` Versioning 섹션을 새 단일-bump 워크플로우에 맞게 갱신.

**구분 원칙 (drift vs historical marker):**
- **Drift 레이블(삭제 대상)**: "이 문서는 v3.3" / "이 스킬은 v3.0" — 현재 상태를 주장하며 버전 bump 시 stale 돼 독자를 오도함
- **Historical marker(보존 대상)**: "v3.1에 도입된 feature X" / `# v3.2: 분류 기준` / 첫 등장을 기록하는 timestamp — 바뀌는 대상이 아니므로 drift 재생산 없음

**Tech Stack:** Markdown (header replacement), Bash (sed/grep), 표준 유닉스 도구. 테스트 프레임워크 없음 — 검증은 `bash scripts/validate-system.sh` + `bash scripts/selfcheck-token-waste.sh` 의 exit 0과 참조 무결성 grep.

**Spec:**
- [`docs/v4/strategy.md`](../strategy.md) §3 P1-1 (감사 스냅샷), §6 Decision 1 (canonical 결정)
- [`.audit/result-W1.md`](../../../.audit/result-W1.md) H1/H3/H4/M5/M6/M7 (원시 증거)
- [`.audit/result-W3.md`](../../../.audit/result-W3.md) V1 (SSOT 위반 — 14곳)

**Preserved constraints:**
- 한국어 기조 유지
- P0-A 커밋(2de8492) 이후 상태 유지 — 같은 파일 수정 시 conflict 없도록 P0-A 경로를 덮지 않음
- Historical marker(첫 등장 timestamp)는 보존

**Verified pre-conditions (2026-04-22 P0-A 커밋 직후 기준):**
- `agents.yaml:4` = `version: "3.2"` (canonical SSOT, 변경 없음)
- `README.md:1` = `# Claude Code 셋업 가이드 v3.3` (drift)
- `QUICKSTART.md` 4곳 (3/38/129/201) 중 3곳이 drift (201은 doc 파일명 기반 링크 — 보존)
- `skills/{spec,check-spec,check-code,analyze}/SKILL.md` 각 1곳에 `(v3.0)` 섹션 레이블
- `docs/28-token-waste-selfcheck.md:373` = `자가진단 (v3.3)` (실제 스크립트 출력 예시)
- `scripts/selfcheck-token-waste.sh:3, :34` = `v3.3` (실제 스크립트 헤더·출력 — docs/28:373과 쌍)
- `scripts/validate-system.sh`의 version 문자열 14곳 확인:
  - **Canonical 주장(센트럴라이즈 대상)**: 라인 2, 33, 124, 459, 461 (현재 버전을 주장)
  - **Historical marker(보존)**: 라인 51(`v3.0 Template` 주석은 stale — "Template"로 수정), 77/79/90/147/149/241/261/293/295/310/312(v3.1 섹션 레이블들 — 해당 피처의 첫 등장 기록), 349/351/367/369/391/393/408/410/424/426/434/436(v3.2 섹션 레이블들), 455(체크 카테고리 분류 요약)
- `CLAUDE.md:86-93` Versioning 섹션 — "두 곳(agents.yaml + prompts 6 sections)에서 버전을 업데이트" 안내 (W1 M7 — validate-system.sh 내부 여러 위치가 추가로 수정돼야 한다는 사실 미반영)

---

## File Structure

### Modified

- `README.md` (:1 — 제목에서 `v3.3` 제거)
- `QUICKSTART.md` (:3, :38, :129 — 3곳; :201은 파일명-기반 링크라 보존)
- `skills/spec/SKILL.md` (:10)
- `skills/check-spec/SKILL.md` (:10)
- `skills/check-code/SKILL.md` (:424)
- `skills/analyze/SKILL.md` (:11)
- `docs/28-token-waste-selfcheck.md` (:373 — 예시 출력에서 `(v3.3)` 제거)
- `scripts/selfcheck-token-waste.sh` (:3, :34 — 스크립트 헤더·실제 출력에서 `v3.3` 제거)
- `scripts/validate-system.sh` (:1-14 영역에 `EXPECTED_VERSION` 상수 도입; :2, :33, :51, :124, :459, :461 중앙화)
- `CLAUDE.md` (:86-93 Versioning 섹션 — 단일-bump 워크플로우로 재작성)

### Created

- `docs/v4/plans/2026-04-22-p1-1-version-canonical.md` — 이 문서

### Explicitly NOT modified (out of scope)

- `README.md:22-45` "v3.X 신규" feature labels — 도입 시점을 기록하는 historical marker, drift 아님
- `docs/10-code-review-system.md` — "v3.0 코드 리뷰 시스템" 역사를 기술하는 문서, 다수 v3.0 참조는 맥락 설명
- `docs/26-coordinator-mode.md`, `docs/14-preset-system.md` — v3.0 아키텍처 문서로의 링크, 파일명·내용 기반
- `docs/12-v3-architecture.md` 및 이를 가리키는 `QUICKSTART.md:201` 링크 — 파일명이 v3 이므로 링크 레이블도 일관
- `agents.yaml` 인라인 주석(`# v3.2: Blast-Radius 분류 기준` 등 라인 37/447/662/693) — feature 도입 시점 historical
- `agents.yaml:729` 중복 `version: "3.2"` — drift는 아니나 SSOT 위반, P1-1 scope 밖 (별도 정리 후보)
- `validate-system.sh`의 v3.1/v3.2 섹션 레이블(10여 줄) — 해당 체크가 도입된 버전을 기록하는 marker
- `docs/v3-changelog.md` — append-only historical 문서, 현재 상태 주장 아님
- `README.md:19` "9 Core + 7 Specialist Reviewers" 요약, 에이전트 목록 테이블 — P1-3 scope

---

## Task 1: README.md 제목 + QUICKSTART.md 선전 문구에서 drift 버전 제거

**Why:** 사용자가 최초 진입하는 두 문서의 상단에서 시스템 버전을 주장하면, 향후 버전 bump마다 두 문서의 편집이 강제된다. 제목을 버전-중립으로 고정하면 drift surface 영구 제거. QUICKSTART의 "v3.0 기능 실전 활용" 문구는 현재 v3.2임에도 여전히 v3.0을 광고하므로 현 독자 기준 오정보.

**Files:**
- Modify: `README.md` (line 1 only)
- Modify: `QUICKSTART.md` (lines 3, 38, 129 — 3 changes)

- [ ] **Step 1: `README.md:1` — 제목에서 ` v3.3` 제거**

Edit:
- old_string: `# Claude Code 셋업 가이드 v3.3`
- new_string: `# Claude Code 셋업 가이드`

- [ ] **Step 2: `QUICKSTART.md:3` — 선전 문구에서 `v3.0` 제거**

Edit:
- old_string: `v3.0 기능을 실전에서 바로 활용하기 위한 실전 가이드.`
- new_string: `이 가이드의 기능을 실전에서 바로 활용하기 위한 실전 가이드.`

- [ ] **Step 3: `QUICKSTART.md:38` — 설명 문장에서 `v3.0` 제거**

Edit:
- old_string: `기존과 동일하게 사용. v3.0 기능은 기존 워크플로우를 **확장**한 것이지 대체가 아님.`
- new_string: `기존과 동일하게 사용. 추가 기능은 기존 워크플로우를 **확장**한 것이지 대체가 아님.`

- [ ] **Step 4: `QUICKSTART.md:129` — 비교 테이블 헤더의 `v3.0` → `현재`**

Edit:
- old_string: `| 기능 | 이전 | v3.0 |`
- new_string: `| 기능 | 이전 | 현재 |`

**주의:** `QUICKSTART.md:201`의 `[v3.0 아키텍처](docs/12-v3-architecture.md)`는 대상 파일이 `12-v3-architecture.md`(파일명에 v3)이므로 링크 레이블과 파일명이 일관 → 보존. 수정 금지.

- [ ] **Step 5: 검증**

```bash
grep -n "v3\.[0-9]" README.md | head -3
# 기대: 라인 22-45 영역의 "v3.X 신규" historical markers만 남음, 라인 1 결과 없음
grep -n "v3\.[0-9]" QUICKSTART.md
# 기대: 라인 201 하나만 남음 (파일명 링크)
```

---

## Task 2: 4개 스킬 SKILL.md에서 `(v3.0)` 프리셋 레이블 제거

**Why:** 해당 섹션의 현재 상태는 v3.2 레포에서 동작하는 프리셋이다. 내부 헤더에 `(v3.0)`을 박아두면 사용자가 각 스킬을 열 때마다 "이 스킬은 v3.0? 레포는 v3.2?" 라는 버전 불일치를 목격한다. 드리프트 surface를 섹션 헤더 레벨에서 영구 제거 (YAGNI).

**Files:**
- Modify: `skills/spec/SKILL.md` (line 10)
- Modify: `skills/check-spec/SKILL.md` (line 10)
- Modify: `skills/check-code/SKILL.md` (line 424)
- Modify: `skills/analyze/SKILL.md` (line 11)

- [ ] **Step 1: `skills/spec/SKILL.md:10`**

Edit:
- old_string: `## 명세서 프리셋 (v3.0)`
- new_string: `## 명세서 프리셋`

- [ ] **Step 2: `skills/check-spec/SKILL.md:10`**

Edit:
- old_string: `## 설계 검수 프리셋 (v3.0)`
- new_string: `## 설계 검수 프리셋`

- [ ] **Step 3: `skills/check-code/SKILL.md:424`**

Edit:
- old_string: `## 6단계 리뷰 시스템 (v3.0)`
- new_string: `## 6단계 리뷰 시스템`

- [ ] **Step 4: `skills/analyze/SKILL.md:11`**

Edit:
- old_string: `## 분석 프리셋 (v3.0)`
- new_string: `## 분석 프리셋`

- [ ] **Step 5: 검증 — 4개 파일에 `(v3.0)` 0건**

```bash
grep -n "(v3\.0)" skills/spec/SKILL.md skills/check-spec/SKILL.md skills/check-code/SKILL.md skills/analyze/SKILL.md
# 기대: 출력 없음

grep -rn "(v3\.0)" skills/ --include="SKILL.md" 2>/dev/null
# 기대: 출력 없음 (다른 스킬에 숨어있는 경우 확인용)
```

---

## Task 3: `docs/28` 예시 출력 + `selfcheck-token-waste.sh` 실제 출력 동기화

**Why:** `docs/28-token-waste-selfcheck.md:373`의 코드 블록은 `selfcheck-token-waste.sh`의 실제 출력을 재현한다. 한 쪽만 수정하면 문서가 스크립트 동작을 왜곡해 설명하게 된다. 쌍을 동시에 업데이트해야 "문서 = 코드 실제 동작" 불변량 유지.

**Files:**
- Modify: `scripts/selfcheck-token-waste.sh` (line 3 주석, line 34 echo)
- Modify: `docs/28-token-waste-selfcheck.md` (line 373 예시 블록)

- [ ] **Step 1: `scripts/selfcheck-token-waste.sh:3` 주석 헤더에서 `v3.3` 제거**

Edit:
- old_string: `# Claude Code 토큰 낭비 자가진단 스크립트 v3.3`
- new_string: `# Claude Code 토큰 낭비 자가진단 스크립트`

- [ ] **Step 2: `scripts/selfcheck-token-waste.sh:34` echo 출력에서 `(v3.3)` 제거**

Edit:
- old_string: `echo -e "${BOLD}  Claude Code 토큰 낭비 자가진단 (v3.3)${NC}"`
- new_string: `echo -e "${BOLD}  Claude Code 토큰 낭비 자가진단${NC}"`

- [ ] **Step 3: `docs/28-token-waste-selfcheck.md:373` 예시 블록 동기화**

Edit:
- old_string: `  Claude Code 토큰 낭비 자가진단 (v3.3)`
- new_string: `  Claude Code 토큰 낭비 자가진단`

- [ ] **Step 4: 검증 — 스크립트 실행 출력과 문서 예시 일치**

```bash
# (a) 스크립트에 v3.3 잔존 없음
grep -n "v3\.3" scripts/selfcheck-token-waste.sh
# 기대: 출력 없음

# (b) docs/28에 v3.3 잔존 없음
grep -n "v3\.3" docs/28-token-waste-selfcheck.md
# 기대: 출력 없음 (다른 라인에 v3.3 있으면 추가 검토 필요)

# (c) 실제 스크립트 실행 출력이 문서 예시와 일치하는지 — 첫 2줄만 비교
bash scripts/selfcheck-token-waste.sh 2>&1 | head -4 | tail -2
# 기대 첫 줄: "  Claude Code 토큰 낭비 자가진단" (괄호 버전 없음)
```

**주의:** selfcheck-token-waste.sh의 실제 동작(7 체크)을 변경하지 않도록 line 3, 34 외엔 건드리지 않는다. 스크립트가 실패해도 P1-1 범위에선 복구 시도하지 않고 상태만 보고.

---

## Task 4: `scripts/validate-system.sh` 버전 canonical 중앙화 + stale 주석 정리

**Why:** W1 M7 — "버전 bump 시 수정 지점이 2곳(CLAUDE.md 안내)이 아니라 validate-system.sh 내부에 7곳 이상 흩어져 있다". `EXPECTED_VERSION` 단일 상수에 집중시키면 향후 bump는 `agents.yaml:4` + `EXPECTED_VERSION` 단 2곳 + validate 실행 → 불일치 자동 감지. 현재 stale `# 2. Check all agents have v3.0 Template` 주석도 P0-A 이후 실제 체크(`## Template`)와 괴리돼 있어 동반 수정.

**Files:**
- Modify: `scripts/validate-system.sh`

**중앙화 대상 (canonical 주장 5곳):** 라인 2, 33, 124, 459, 461  
**Stale 주석 수정 1곳:** 라인 51  
**보존 (historical marker — 수정 금지):** 라인 77, 79, 90, 147, 149, 241, 261, 293, 295, 310, 312, 349, 351, 367, 369, 391, 393, 408, 410, 424, 426, 434, 436, 455

- [ ] **Step 1: 스크립트 상단(라인 15 근처, `ERRORS=0` 선언 직전)에 `EXPECTED_VERSION` 상수 삽입**

정확한 삽입 위치: 현재 `AGENTS_YAML="..."` 라인(파일의 라인 11) 직후, 그 뒤의 빈 줄 이전.

**중요 — Edit 도구 사용 규칙:**
- 아래 `old_string`과 `new_string`은 **파일 원문 그대로** 복사해서 쓴다. 본 plan 문서의 markdown code fence에 들여쓰기가 있어도, 파일 원문에는 들여쓰기 없음(top-level bash 문장). Edit 도구는 literal string 매칭이므로 leading space 포함 시 불일치.
- Step 1이 +5 라인(빈 줄 + comment 3줄 + EXPECTED_VERSION 1줄)을 삽입하므로 이후 스텝의 라인 번호는 기존 대비 **+5 이동**한다. Step 2~7의 모든 Edit는 old_string 정확 매칭에만 의존 — 라인 번호 언급은 맥락 참고용일 뿐이다.

Edit 내용:
- old_string (정확히 4줄, 들여쓰기 없음):
  ```
AGENTS_YAML="$HOME/.claude/team/agents.yaml"

ERRORS=0
WARNINGS=0
  ```
- new_string (정확히 9줄, 들여쓰기 없음):
  ```
AGENTS_YAML="$HOME/.claude/team/agents.yaml"

# v4.0 P1-1: 버전 canonical 중앙화 (strategy.md Decision 1)
# 이 스크립트가 검증하는 team system의 예상 버전. agents.yaml:4의 value와 일치해야 함.
# 버전 bump 시 (1) agents.yaml:4 (2) 아래 EXPECTED_VERSION 두 곳만 동시 업데이트.
EXPECTED_VERSION="3.2"

ERRORS=0
WARNINGS=0
  ```

- [ ] **Step 2: 라인 2 파일 헤더 주석에서 `v3.2` 제거 (버전-중립)**

Edit:
- old_string: `# Multi-Agent Team System v3.2 Validation Script`
- new_string: `# Multi-Agent Team System Validation Script`

**Rationale:** 파일 헤더에 버전 박아두면 스크립트 자체를 upgrade할 때마다 drift. 버전-중립.

- [ ] **Step 3: 라인 33 echo 타이틀 동적화**

Edit:
- old_string: `echo "=== Multi-Agent Team System v3.2 Validation ==="`
- new_string: `echo "=== Multi-Agent Team System v$EXPECTED_VERSION Validation ==="`

- [ ] **Step 4: 라인 51 stale 주석 수정 (`v3.0 Template` → 실제 체크와 동기화)**

**P0-A 이후 현실:** 라인 56 실제 체크는 `grep -q "^## Template$"`인데 라인 51 주석은 여전히 `v3.0 Template`이라고 주장. 주석을 코드에 맞춤.

Edit:
- old_string: `# 2. Check all agents have v3.0 Template and Boundary sections`
- new_string: `# 2. Check all agents have ## Template and ## Boundary sections`

- [ ] **Step 5: 라인 124 canonical 체크 동적화**

Edit:
- old_string: `if grep -q 'version: "3.2"' "$AGENTS_YAML" 2>/dev/null; then`
- new_string: `if grep -q "version: \"$EXPECTED_VERSION\"" "$AGENTS_YAML" 2>/dev/null; then`

**주의:** bash 단일따옴표 → 이중따옴표 변경. `$EXPECTED_VERSION` 확장 위해 이중따옴표 필수, 내부 이중따옴표 이스케이프(`\"`).

- [ ] **Step 6: 라인 124 아래 Version echo + 에러 메시지도 동적화**

(라인 번호는 Step 1 삽입 후 +5 이동 — exact old_string 매칭으로 처리하므로 실제 라인 위치는 무관). 현재 매칭 대상:
```bash
if grep -q 'version: "3.2"' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Version: 3.2 ✓"
else
    echo "ERROR: agents.yaml version is not 3.2"
```

`  Version: 3.2 ✓` → `  Version: $EXPECTED_VERSION ✓`  
`agents.yaml version is not 3.2` → `agents.yaml version is not $EXPECTED_VERSION`

Edit 1:
- old_string: `    echo "  Version: 3.2 ✓"`
- new_string: `    echo "  Version: $EXPECTED_VERSION ✓"`

Edit 2:
- old_string: `    echo "ERROR: agents.yaml version is not 3.2"`
- new_string: `    echo "ERROR: agents.yaml version is not $EXPECTED_VERSION"`

- [ ] **Step 7: 라인 459, 461 최종 PASS 메시지 동적화**

Edit 1 (line 459 근처):
- old_string: `    echo "✅ System validation PASSED (v3.2) — no issues"`
- new_string: `    echo "✅ System validation PASSED (v$EXPECTED_VERSION) — no issues"`

Edit 2 (line 461 근처):
- old_string: `    echo "⚠️  System validation PASSED with $WARNINGS warnings (v3.2)"`
- new_string: `    echo "⚠️  System validation PASSED with $WARNINGS warnings (v$EXPECTED_VERSION)"`

- [ ] **Step 8: 검증 — canonical 주장 5곳이 모두 `$EXPECTED_VERSION` 경유**

```bash
# (a) 스크립트 실행 시 출력에서 canonical 버전이 모두 동일 (EXPECTED_VERSION 값 그대로)
bash scripts/install-skills.sh /tmp/p0a-install-target --team --force 2>&1 | tail -3
bash scripts/validate-system.sh 2>&1 | grep -E "Multi-Agent|Version:|validation PASSED|validation FAILED"
# 기대: 출력에 "3.2"가 등장하는 위치가 모두 동일 값, 불일치 없음

# (b) 스크립트 내부에 "3.2" 리터럴은 EXPECTED_VERSION 선언 1줄에만 존재
grep -n '"3\.2"' scripts/validate-system.sh
# 기대: 정확히 1줄 — `EXPECTED_VERSION="3.2"` 선언. 다른 리터럴 매칭 없음.

# `v3.2` 문자열(historical marker 포함 가능)은 별도로:
grep -n 'v3\.2' scripts/validate-system.sh
# 기대: Section 13/14/15/16/17/18의 historical 레이블들만. Line 2(파일 헤더)·
# Line 33(echo 타이틀)에 v3.2가 리터럴로 등장하지 않음(EXPECTED_VERSION 경유).

# (c) regression — baseline errors와 동일 (6 errors = PyYAML missing env issue only)
bash scripts/validate-system.sh 2>&1 | grep -E "^ERROR|^Errors:"
# 기대: "Errors: 6" + PyYAML-origin ERROR 6줄 (agents.yaml, code-review, failure-policy, standard, session-state-schema, event-driven-review 중 일부 조합)
```

---

## Task 5: `CLAUDE.md` Versioning 섹션 업데이트

**Why:** W1 M7 — 현재 CLAUDE.md:86-93은 "agents.yaml + prompts sections 두 곳만 업데이트하면 된다"고 안내하지만, P0-A 이전에는 validate-system.sh 내부 7곳 이상이 동시에 수정돼야 했고, P0-A+P1-1 이후에는 `agents.yaml:4` + `EXPECTED_VERSION`(validate-system.sh) 두 곳만 업데이트하면 된다. 새 단일-bump 워크플로우를 반영하도록 재작성.

**Files:**
- Modify: `CLAUDE.md` (lines 86-93 섹션 전체)

- [ ] **Step 1: `CLAUDE.md` Versioning 섹션 재작성**

현재 라인 86-93 상태:
```markdown
## Versioning

The team system version is set in **two places** and `validate-system.sh` checks they match:

- `agents.yaml` → `version: "3.2"`
- Prompts under `prompts/` must contain the 6 required sections (`## Opening`, `## Working Mode`, `## Focus On`, `## Quality Checks`, `## Return`, `## Boundary`)

When bumping the version, update both, then re-run `validate-system.sh` with 0 errors expected.
```

Edit:
- old_string (전체 섹션 8줄):
  ```
  ## Versioning

  The team system version is set in **two places** and `validate-system.sh` checks they match:

  - `agents.yaml` → `version: "3.2"`
  - Prompts under `prompts/` must contain the 6 required sections (`## Opening`, `## Working Mode`, `## Focus On`, `## Quality Checks`, `## Return`, `## Boundary`)

  When bumping the version, update both, then re-run `validate-system.sh` with 0 errors expected.
  ```
- new_string:
  ```
  ## Versioning

  The team system version is declared **once** in `agents.yaml:4` (`version: "3.2"`). `scripts/validate-system.sh` holds the expected value in a single `EXPECTED_VERSION` constant at the top of the script; the script fails if the installed `agents.yaml` diverges.

  To bump the version:
  1. Update `agents.yaml:4` `version` field
  2. Update `scripts/validate-system.sh` `EXPECTED_VERSION`
  3. Run `bash scripts/install-skills.sh <target> --team --force && bash scripts/validate-system.sh` — 0 errors expected (beyond the PyYAML-env baseline)

  Prompt template structure (orthogonal axis, not version-linked): every file under `prompts/` must contain the 6 required sections (`## Opening`, `## Working Mode`, `## Focus On`, `## Quality Checks`, `## Return`, `## Boundary`). `validate-system.sh` check 1 enforces this.
  ```

- [ ] **Step 2: 검증 — 섹션 수정 반영 + 다른 CLAUDE.md 섹션 불변**

```bash
grep -A 10 "^## Versioning" CLAUDE.md
# 기대: 새 내용이 "declared **once** in agents.yaml:4"로 시작

grep -n "v3\.[0-9]\|\"3\.[0-9]\"" CLAUDE.md
# 기대: 라인 50(`reference implementation ... (v3.2)`)만 남음 (descriptive, out of scope)
```

---

## 🔔 Checkpoint (a): 커밋 전 최종 점검

**이 시점 repo 상태:**
- Task 1-5 완료. 10개 파일 수정 + 1개 신규(이 plan 문서)
- `bash scripts/validate-system.sh`가 설치 후 6 errors (baseline 동일, PyYAML env) 외 새 오류 없음
- `bash scripts/selfcheck-token-waste.sh` 첫 출력 라인 = `Claude Code 토큰 낭비 자가진단` (괄호 버전 없음)

**사용자 확인 후 Task 6 진행.**

---

## Task 6: 통합 검증 + 커밋 전 sweep

- [ ] **Step 1: 전체 `git diff --stat` 검토**

```bash
cd /Users/jeongsik/develop/claude-code-guide
git status --short
git diff --stat
```

기대 요약:
- `M  README.md` (1 line)
- `M  QUICKSTART.md` (3 lines)
- `M  skills/{analyze,check-code,check-spec,spec}/SKILL.md` (각 1 line)
- `M  docs/28-token-waste-selfcheck.md` (1 line)
- `M  scripts/selfcheck-token-waste.sh` (2 lines)
- `M  scripts/validate-system.sh` (~10 lines incl. EXPECTED_VERSION block)
- `M  CLAUDE.md` (~10 lines incl. new Versioning section)
- `A  docs/v4/plans/2026-04-22-p1-1-version-canonical.md`

- [ ] **Step 2: 참조 무결성 sweep (drift 레이블 제거 검증)**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (1) README 제목에서 v3.3 제거
grep -n "^# Claude Code 셋업 가이드" README.md
# 기대: "# Claude Code 셋업 가이드" (v3.3 없음)

# (2) skills 4개 (v3.0) 레이블 제거
grep -rn "(v3\.0)" skills/ --include="SKILL.md"
# 기대: 출력 없음

# (3) QUICKSTART의 drift 문구 제거 (파일명-기반 링크는 보존)
grep -n "v3\.0" QUICKSTART.md | grep -v "12-v3-architecture.md"
# 기대: 출력 없음 (남은 유일한 v3.0 언급은 docs/12-v3-architecture.md 링크)

# (4) docs/28 ↔ selfcheck 동기화 — ANSI escape 제거 후 비교
TITLE=$(bash scripts/selfcheck-token-waste.sh 2>&1 | head -5 | sed -e 's/\x1b\[[0-9;]*m//g' -e 's/^  //' | grep "자가진단")
DOC_EXAMPLE=$(sed -n '373p' docs/28-token-waste-selfcheck.md | sed 's/^  //')
test -n "$TITLE" || echo "WARN: selfcheck 출력에서 자가진단 라인 못찾음"
test -n "$DOC_EXAMPLE" || echo "WARN: docs/28:373 empty"
[ "$TITLE" = "$DOC_EXAMPLE" ] && echo "OK: selfcheck ↔ docs/28 동기화 확인" || echo "MISMATCH: '$TITLE' vs '$DOC_EXAMPLE'"

# (5) validate-system.sh canonical 중앙화 — 변수 참조 정확히 7회 + 선언 주석 언급
grep -c 'EXPECTED_VERSION' scripts/validate-system.sh
# 기대: 정확히 8 (선언 1 + 3줄 comment 내 언급 1 + 실제 사용 6: Step 3/5/6×2/7×2)
grep -n '"3\.2"' scripts/validate-system.sh
# 기대: 정확히 1줄 — EXPECTED_VERSION="3.2" 선언 자체
```

- [ ] **Step 3: 시스템 재설치 + validate 실행**

```bash
bash scripts/install-skills.sh /tmp/p0a-install-target --team --force 2>&1 | tail -3
bash scripts/validate-system.sh 2>&1 | tail -8
```

기대:
- `Errors: 6` (PyYAML env baseline과 동일)
- `Warnings: 0`
- PASS/FAIL 메시지에 `(v3.2)` 등장 (EXPECTED_VERSION이 전개됨)

---

## 🔔 Checkpoint (b): 커밋 직전

**사용자 확인 후 Task 7 진행.**

---

## Task 7: 단일 커밋 생성

- [ ] **Step 1: 스테이징**

```bash
cd /Users/jeongsik/develop/claude-code-guide
git add README.md QUICKSTART.md skills/ docs/28-token-waste-selfcheck.md scripts/selfcheck-token-waste.sh scripts/validate-system.sh CLAUDE.md docs/v4/plans/
git status --short
```

기대: 위 Task 6 Step 1의 요약과 정확히 일치.

- [ ] **Step 2: 커밋**

```bash
git commit -m "$(cat <<'EOF'
feat(v4 P1-1): 버전 canonical 통일 — drift 레이블 제거 + EXPECTED_VERSION 중앙화

strategy.md §3 P1-1 + §6 Decision 1 구현. 시스템 버전 주장이 repo 여러 곳에
drift 레이블로 중복되던 문제를 정리 — canonical은 agents.yaml:4 한 곳만.

Drift vs historical marker 구분 원칙 적용:
- Drift(삭제 대상): "이 문서는 v3.3" / "이 스킬은 v3.0" — 현재 상태 주장
- Historical marker(보존): "v3.1에 도입된 feature" — 첫 등장 timestamp

변경 사항:
- README.md:1 — 제목 "v3.3" 제거 (문서 버전과 시스템 버전 분리)
- QUICKSTART.md:3,38,129 — "v3.0 기능" 선전 문구·비교 테이블 헤더 정리
  (라인 201은 docs/12-v3-architecture.md 파일명-기반 링크라 보존)
- skills/{spec,check-spec,check-code,analyze}/SKILL.md — 4개 `(v3.0)`
  프리셋/섹션 레이블 제거. 스킬 내부에서 버전 주장 제거 → 레포 bump 시
  드리프트 surface 영구 삭제
- docs/28-token-waste-selfcheck.md:373 + scripts/selfcheck-token-waste.sh:3,34
  — "(v3.3)" 문서 예시 ↔ 스크립트 실제 출력 쌍을 동기 삭제. 문서·코드 일관
- scripts/validate-system.sh — EXPECTED_VERSION 단일 상수 도입. 헤더 주석·
  echo 타이틀·canonical 체크·PASS 메시지 5곳을 상수 경유로 전환. 라인 51
  stale 주석 "v3.0 Template" → "## Template" 동기화 (P0-A 실제 체크와 일치).
  historical marker(v3.1/v3.2 섹션 레이블 10여 줄)는 보존
- CLAUDE.md Versioning 섹션 재작성 — "두 곳 업데이트" (W1 M7 지적) →
  agents.yaml:4 + EXPECTED_VERSION 두 곳 + validate 실행의 단일-bump
  워크플로우 명시

검증:
- install-skills.sh --team --force + validate-system.sh → Errors 6 (PyYAML
  env baseline, 우리 변경 무관), 새 오류 0
- selfcheck-token-waste.sh 첫 출력 라인 = 문서 예시 일치
- `(v3.0)` skills 레이블 0건, README 제목 버전-중립
- validate 내부 리터럴 "3.2" = EXPECTED_VERSION 선언 1회만 (나머지
  historical marker)

Out of scope (별도 작업):
- README.md:22-45 "v3.X 신규" feature introduction markers (historical)
- docs/10-code-review-system.md v3.0 참조 다수 (v3.0 역사 기술 문서)
- agents.yaml:729 system_meta.version 중복 (SSOT 위반이나 현재 drift 아님)
- P1-3 에이전트 목록 canonical 통일 — 다음 슬라이스

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 커밋 사후 검증**

```bash
git log --oneline -2
git show --stat HEAD | tail -15
git status
# 최종 drift sweep — v3.3 잔존 확인. README.md:22-45의 "v3.X 신규" historical marker 블록은
# 플랜에서 명시적으로 보존한 영역(out of scope)이므로 예상 매치. 그 외 위치에서 v3.3이
# 발견되면 drift 잔재.
git grep -n "v3\.3" -- . ':!docs/v3-changelog.md' ':!docs/v4/' ':!.audit/' ':!.git/'
# 기대 매치 (preserved historical markers):
#   README.md:35-45  "v3.3 신규: X" feature introduction labels (총 11줄)
#   README.md:75     docs/ 디렉터리 설명 "v3.3: 서브에이전트 효율성..." (1줄)
#   README.md:212    "### v3.3 가이드" 문서 목록 섹션 헤더 (1줄)
# 위 13줄 외 추가 매치가 있으면 drift 잔재 — 리뷰 필요.
```

기대: 최신 커밋 = feat(v4 P1-1), working tree clean, main 브랜치 ahead of origin by 2. git grep은 README.md의 13줄 historical markers만 매치.

---

## Remaining Out-of-Scope Items (after P1-1)

| # | 항목 | 상태 |
|---|------|------|
| P1-2 | 프리셋 정의 6-스킬 중복 제거 | 대기 |
| P1-3 | 에이전트 목록 canonical 통일 | 대기 |
| P1-4 | 스킬 목록 canonical 통일 | 대기 |
| P1-5 (B2) | `hooks/scripts/*.sh` rename | 대기 |
| P1-6 | Complexity Tier 임계값 통일 | 대기 |
| P1-7~9 | description 재작성 3건 | 대기 |
| P2-1~10 | 문서 drift 정리 | 대기 |

P1-1 완료 후 다음 후보: P1-5(hooks rename, B2 breaking) 또는 P1-2+P1-7~9(description 묶음).
