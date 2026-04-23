# P1-2 Preset Consolidation + P1-7/P1-8 Description Rewrite Implementation Plan (Bundle C)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/v4/strategy.md` §3 **P1-2 + P1-7 + P1-8** 통합 구현 (사용자 Bundle C 승인 2026-04-23):
- **P1-2**: 6개 스킬(`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`) 프리셋 정의 중복 제거 → "프리셋 체계 변경 = 1곳 수정"
- **P1-7**: `test`, `qa-test` SKILL.md frontmatter **description** 재작성 (qa-e2e는 strategy가 "이미 명확"으로 제외)
- **P1-8**: `analyze`, `spec`, `check-spec` SKILL.md frontmatter **description** 재작성

`CLAUDE.md:56-63` "PDARR + preset system"을 canonical로 확정하고, 각 SKILL.md는 스킬 고유 정보(시간/Phase/팀 구성)만 보존한 채 canonical 링크로 이관. 동시에 SKILL.md frontmatter의 description을 PDARR 축 위치가 드러나도록 간결화 — `/dispatch` 라우팅이 description만 읽어도 역할 판별이 가능.

**Architecture:** canonical은 **2-tier 구조** —
- **CLAUDE.md:56-63** = 최상위 4줄 rule (Flow + 2축 + Complexity tier 요약)
- **docs/14-preset-system.md** = 상세 참조 문서 (스킬별 depth 범위 테이블, --team 팀 구성, 조합 예시)

나머지 모든 문서(README.md, skills/README.md, 6 SKILL.md)는 두 canonical 중 적절한 곳으로 **링크**만 유지하고 프리셋 메커니즘을 독자적으로 재선언하지 않는다. qa-test의 `minimal/basic/standard/full` 4단계 라벨은 **기존 인터페이스 보존(non-breaking)** + 2축 depth 매핑 테이블을 추가한다. qa-e2e는 depth 축이 본질적으로 없으므로(scenario-driven) execution 축(`--team`)과 modifier(`--browser`/`--tc`/`--prepare`)만 있음을 canonical에 명시한다.

**Tech Stack:** Markdown. 테스트 프레임워크 없음 — 검증은 (1) `bash scripts/install-skills.sh --team --force && bash scripts/validate-system.sh`가 P1-1 기준선(Errors: 6 PyYAML-env) 유지, (2) 각 SKILL.md에 canonical 마커(`<!-- PRESET_CANONICAL_LINK -->`) 존재 검증 체크 추가, (3) 6 SKILL.md 내부에 중복 2축 테이블이 남아있지 않음을 grep으로 확인.

**Spec:**
- [`docs/v4/strategy.md`](../strategy.md) §3 P1-2 (W3 V6, W2 Group 6 — 9곳 중복 + 라벨 불일치)
- [`.audit/result-W2.md`](../../../.audit/result-W2.md) Group 6 (원시 증거)
- [`.audit/result-W3.md`](../../../.audit/result-W3.md) V6 (SSOT 위반 9곳)

**Preserved constraints:**
- 한국어 기조 유지
- P0-A(2de8492) + P1-1(40d6b31) 상태 위에 쌓임 — 같은 파일 재수정 시 P1-1 변경 덮지 않음
- `/qa-test --minimal|--basic|--standard|--full` 기존 인터페이스 보존 (사용자 스크립트 의존 가능성 → non-breaking)
- `out-of-scope`: README.md:22-45 historical markers, docs/10-code-review-system.md, agents.yaml:729 중복, docs/v3-changelog.md append-only, skills/test/SKILL.md(P1-7 범위), skills/reflect|complete|organize-docs/SKILL.md(P1-9 범위)

---

## Verified Pre-conditions (2026-04-23)

P0-A 및 P1-1 커밋 이후 상태 직접 확인 완료:

- **`CLAUDE.md:56-63`** — "PDARR + preset system" 섹션: Flow 1줄 + 2축 3줄(qa-e2e 포함 "6 skills") + Complexity tier 1줄. **현재 "qa-e2e에 depth axis가 적용된다"는 사실상의 오주장 포함** — canonical 확정 시 정정 필요
- **`skills/README.md:77-92`** — "프리셋 시스템" 16줄 (2축 다이어그램 + 조합 예시 5줄 + 대상 6 스킬 나열). 요약 수준이라 canonical 링크 1줄로 축약 가능
- **`README.md:404-422`** — "프리셋 시스템 (v3.0 확장)" 19줄. **"3개 스킬에 공통 적용"이라고 주장하며 analyze/spec/check-code만 예시** — 6 스킬로 정정 필요
- **`docs/14-preset-system.md`** — 257줄 상세 문서. "적용 대상 스킬" 테이블(L27-31)에 **analyze/spec/check-spec/check-code 4개만 나열 — qa-test/qa-e2e 미포함**. qa-test/qa-e2e를 canonical 상세 참조에 포함시키려면 섹션 확장 필요
- **6 SKILL.md 프리셋 섹션 현황:**
  - `skills/analyze/SKILL.md:11-41` — `## 분석 프리셋` + 2축 테이블 2개 + 조합 예시 6줄 + --quick/--thorough 상세 + --team 팀 구성. **총 31줄**
  - `skills/spec/SKILL.md:10-77` — `## 명세서 프리셋` + 2축 테이블 2개 + 조합 예시 6줄 + --quick/--thorough 상세 + --team 팀 + 워크플로우 5단계. **총 68줄**
  - `skills/check-spec/SKILL.md:10-60` — `## 설계 검수 프리셋` + 2축 테이블 2개 + 조합 예시 5줄 + --quick/--thorough 상세 + --team 팀. **총 51줄**
  - `skills/check-code/SKILL.md:19-54` — `## 실행 모드 (프리셋)` + 2축 테이블 2개 + 조합 예시 7줄 + "기존 호환 모드" 4줄. **총 36줄**. 추가로 L474-488에 `## --team 모드 (Agent Teams 리뷰)` 팀 구성 14줄 존재 (별개 섹션)
  - `skills/qa-test/SKILL.md:10-94` — `## 사용법` 8줄(`--minimal/--basic/--standard/--full` 4라벨) + `## --team 모드` 70줄(팀 구성 테이블 + 실행 흐름 + 난이도 조합 5줄 + 리포트 섹션 예시). **총 85줄**. 2축 체계 기술 없음 — 라벨 mapping 필요
  - `skills/qa-e2e/SKILL.md:10-99` — `## 사용법` 12줄(`--browser/--tc/--prepare/--team`) + `## --team 모드` 80줄(팀 구성 + 실행 흐름 + 차이 테이블 + 리포트 섹션). **총 90줄**. depth 축 없음
- **총 삭제/축약 대상:** 약 370줄(6 SKILL.md 프리셋 관련 섹션 합)
- **보존 대상:** 각 스킬의 `--team` 팀 구성, 실행 흐름, 리포트 섹션(스킬 고유 정보) — 약 200줄
- **순 감소 예상:** 약 170줄

---

## 🔀 Bundle Decision: **옵션 C 확정** (사용자 승인 2026-04-23)

**선택된 범위:** P1-2(본문 프리셋 정리) + P1-7(test/qa-test description) + P1-8(analyze/spec/check-spec description)

**합의 근거:**
- strategy.md는 P1-2와 P1-8을 명시적으로 묶음 권장 — "preset 2축은 SKILL.md 본문 상단 링크로 이관 (P1-2와 묶음)"
- P1-7의 test/qa-test 역시 같은 "description 청소" 컨셉 + qa-test는 P1-2 본문 수정과 동일 파일이라 중복 편집 회피 이점
- qa-e2e description은 strategy §P1-7에서 "이미 명확"으로 판정 — 본 번들에서 **수정 제외** (out-of-scope)

**추가되는 파일 및 변경:**
- **신규 스코프 파일 1개**: `skills/test/SKILL.md` (P1-7, frontmatter description만)
- **기존 스코프 파일 추가 변경**:
  - `analyze/SKILL.md` description (P1-8)
  - `spec/SKILL.md` description (P1-8)
  - `check-spec/SKILL.md` description (P1-8)
  - `qa-test/SKILL.md` description (P1-7)

**번들 제외 항목 (각각 별도 슬라이스):**
- P1-6 Complexity Tier 임계값 — 프리셋과 축 독립
- P1-9 reflect/complete/organize-docs description — 파일 집합 및 개념 이질
- qa-e2e description (P1-7 내부 제외) — strategy가 "이미 명확"으로 판정

---

## File Structure

### Created

- `docs/v4/plans/2026-04-23-p1-2-preset-consolidation.md` — 이 플랜 문서

### Modified (canonical tier)

- `CLAUDE.md:56-63` — "PDARR + preset system" 섹션
  - Flow 1줄 보존
  - **2축 설명에서 "qa-e2e" 분리 명시** — "depth축: 5 skills / execution축 전용: qa-e2e" 표현으로 정정
  - Complexity tier 요약 1줄 보존
  - 상세는 `docs/14-preset-system.md` 링크
- `docs/14-preset-system.md` — canonical 상세 참조
  - L24-31 "적용 대상 스킬" 테이블에 **qa-test, qa-e2e 행 추가**
  - qa-test depth 매핑 테이블 신규 섹션 추가 (기존 4라벨 ↔ 2축 alias)
  - qa-e2e "depth 축 미적용 사유" 박스 신규 섹션 추가
  - "L255 `v3.0 아키텍처` 링크"는 P1-1 스코프 밖이었으므로 보존

### Modified (consumer tier — 6 SKILL.md 프리셋 섹션 축소)

- `skills/analyze/SKILL.md` — L11-41 `## 분석 프리셋` 섹션: 2축 테이블 + 조합 예시 + --team 규칙 삭제. **보존**: --team 모드 팀 구성. **추가**: canonical 링크 1줄 + HTML 마커 `<!-- PRESET_CANONICAL_LINK -->`
- `skills/spec/SKILL.md` — L10-77 동형. 팀 워크플로우 5단계는 스킬 고유이므로 보존
- `skills/check-spec/SKILL.md` — L10-60 동형
- `skills/check-code/SKILL.md` — L19-54 동형. L474-488 `## --team 모드` 섹션은 별개 위치라 보존. L49-54 "기존 호환 모드"(`--context`/`--full`)는 스킬 고유 기능이므로 보존
- `skills/qa-test/SKILL.md` — L10-94:
  - 사용법 섹션에 **"난이도 ↔ 2축 depth 매핑 테이블" 추가** (non-breaking, 기존 4 라벨은 alias로 설명)
  - `## --team 모드` 중복 규칙(`--team 단독 = full`, `--team --minimal` 등 5줄) → canonical 링크로 대체
  - 보존: 팀 구성 테이블, 팀 실행 흐름, 리포트 추가 섹션, Tiebreaker 규칙(스킬 고유)
- `skills/qa-e2e/SKILL.md` — L10-99:
  - 사용법 상단에 **"depth 축 미적용, execution 축만 적용" 안내 1줄** 추가
  - `## --team 모드` 팀 구성·차이 테이블·리포트 섹션은 스킬 고유이므로 모두 보존
  - `--browser`, `--tc`, `--prepare`, `--headed` modifier 설명은 고유 기능이므로 모두 보존
  - 중복 canonical 규칙 없음(원래 2축 주장 미포함) — 수정 분량 최소

### Modified (summary tier — canonical 링크만)

- `skills/README.md:77-92` — 16줄 → **요약 3-4줄 + canonical 링크**로 축약. 예시 1-2개만 보존
- `README.md:404-422` — 19줄. "3개 스킬에 공통 적용" → "6개 스킬에 공통 적용"으로 정정 + canonical 링크. **v3.0 historical 레이블(L404 `(v3.0 확장)`)은 P1-1 out-of-scope 기조 유지**(historical marker로 해석 가능). 결정: L404 레이블은 **plan 진행 중 별도 판단** — 플래그 삭제 시 Task 4 Step 2에 포함, 보존 시 주석만 추가

### Modified (validation)

- `scripts/validate-system.sh` — 신규 체크 "Preset canonical marker in 6 SKILL.md" 추가
  - 각 대상 SKILL.md에 `<!-- PRESET_CANONICAL_LINK -->` 마커 존재 여부 확인
  - 중복 2축 테이블 선언(`|.*--quick.*standard.*--thorough.*|` 패턴) 잔존 시 WARNING
  - `EXPECTED_VERSION` 변경 없음 — 이번 슬라이스는 버전 bump 아님

### Modified (description — P1-7 + P1-8 bundle)

- `skills/test/SKILL.md` — frontmatter description 1줄 (P1-7, 본 번들에서 신규 스코프 추가)
- `skills/analyze/SKILL.md` — frontmatter description 1줄 (P1-8)
- `skills/spec/SKILL.md` — frontmatter description 1줄 (P1-8)
- `skills/check-spec/SKILL.md` — frontmatter description 1줄 (P1-8)
- `skills/qa-test/SKILL.md` — frontmatter description 1줄 (P1-7, Task 3.5 본문 수정과 동일 파일)

### Not modified (explicit out-of-scope)

- `skills/qa-e2e/SKILL.md` frontmatter description — strategy P1-7에서 "이미 명확"으로 판정 → 본문만 수정, description 불변
- `skills/check-code/SKILL.md` frontmatter description — P1-7/P1-8 대상 아님 (본문만 수정)
- `skills/reflect|complete|organize-docs/SKILL.md` — P1-9 범위
- `skills/dispatch/SKILL.md` L55-58 Complexity Tier 서술 — P1-6 범위
- `.claude/rules/subagent-strategy.md` — P1-6 범위
- `docs/10-code-review-system.md` — 6단계 리뷰 시스템 상세, check-code의 부록 성격 (플레인 리딩으로는 drift 없음)
- `agents.yaml:7-35` `routing_rules` — P2-3 범위 (모델 라우팅 canonical)
- `agents.yaml:729` `system_meta.version` 중복 — P1-1 explicit out-of-scope

---

## Task 1: `docs/14-preset-system.md` 확장 — 6 스킬 지원 완성

**Why first:** docs/14가 canonical 상세 참조로 지정되려면 대상 스킬을 전수 포괄해야 한다. qa-test와 qa-e2e가 빠진 상태로 나머지 SKILL.md에서 "상세는 docs/14 참조" 링크를 걸면 dead-end가 된다. docs/14 확장 → 각 SKILL.md 이관 순서로 진행해야 링크 무결성이 중간 상태에서도 유지된다.

**Files:**
- Modify: `docs/14-preset-system.md`

- [ ] **Step 1: L24-31 "적용 대상 스킬" 테이블 확장**

old_string:
```markdown
## 적용 대상 스킬

| 스킬 | 역할 | 프리셋 지원 |
|------|------|------------|
| `/analyze` | 코드베이스 분석, 영향도, 실행 전략 | depth + mode |
| `/spec` (또는 `/design`) | 기술 명세서 작성 | depth + mode |
| `/check-spec` | 설계문서 검수 | depth + mode |
| `/check-code` (또는 `/review`) | 코드 품질 검수 | depth + mode |
```

new_string:
```markdown
## 적용 대상 스킬

| 스킬 | 역할 | 프리셋 지원 | 비고 |
|------|------|------------|------|
| `/analyze` | 코드베이스 분석, 영향도, 실행 전략 | depth + mode | 표준 2축 |
| `/spec` (또는 `/design`) | 기술 명세서 작성 | depth + mode | 표준 2축 |
| `/check-spec` | 설계문서 검수 | depth + mode | 표준 2축 |
| `/check-code` (또는 `/review`) | 코드 품질 검수 | depth + mode | 표준 2축 + Phase 매핑 |
| `/qa-test` | 종합 QA 자동화 | depth(4라벨) + mode | 기존 `--minimal/--basic/--standard/--full` 유지 + 2축 alias 지원 (§§ qa-test 매핑 참조) |
| `/qa-e2e` | 비즈니스 E2E 검증 | **mode only** | depth 축 없음 — 시나리오 기반(§§ qa-e2e 주석 참조) |
```

- [ ] **Step 2: L210 `/check-code 프리셋` 섹션 뒤에 신규 섹션 2개 삽입 — `/qa-test`와 `/qa-e2e`**

old_string (정확 매칭을 위해 check-code 섹션 끝부분 포함, L210 `---` 앵커 이용):
```markdown
### /check-code 프리셋

기존 `docs/10-code-review-system.md`의 6단계 워크플로우와 통합:

| 깊이 | 실행 Phase |
|------|-----------|
| --quick | Phase 1만 (자동 분석) |
| standard | Phase 1→2→3→6 |
| --thorough | Phase 1→2→3→4→5→6 (전체) |

#### --team 모드
```
┌─ PM (Lead): 리뷰 조율, Tiebreaker 중재
├─ Security Sentinel: 보안 심층 검수
├─ Performance Prophet: 성능 심층 검수
├─ Code Reviewer: 코드 품질 종합
└─ API Arbiter: API 설계 검수 (해당 시)
```

---

## 프리셋 선택 가이드
```

new_string:
```markdown
### /check-code 프리셋

기존 `docs/10-code-review-system.md`의 6단계 워크플로우와 통합:

| 깊이 | 실행 Phase |
|------|-----------|
| --quick | Phase 1만 (자동 분석) |
| standard | Phase 1→2→3→6 |
| --thorough | Phase 1→2→3→4→5→6 (전체) |

#### --team 모드
```
┌─ PM (Lead): 리뷰 조율, Tiebreaker 중재
├─ Security Sentinel: 보안 심층 검수
├─ Performance Prophet: 성능 심층 검수
├─ Code Reviewer: 코드 품질 종합
└─ API Arbiter: API 설계 검수 (해당 시)
```

---

### /qa-test 프리셋

qa-test는 역사적으로 **4단계 난이도 라벨**(`--minimal/--basic/--standard/--full`)을 사용해왔다. 2축 체계와의 호환을 위해 **기존 라벨을 보존하면서 2축 depth alias를 병행 지원**한다.

#### 난이도 ↔ 2축 depth 매핑

| qa-test 라벨 | 2축 alias | 범위 | Phase |
|-------------|-----------|------|-------|
| `--minimal` | `--quick` | 문법 검증만 | Phase 2 |
| `--basic` | (alias 없음, quick 상위) | 문법 + 코드 품질 | Phase 2-3 |
| `--standard` (기본) | (동일, 기본값) | 문법 + 품질 + UI/이벤트 + 의존성 | Phase 2-5 |
| `--full` | `--thorough` | + 이전 리포트 비교 | Phase 2-7 |

**규칙:** 두 라벨은 동시에 유효한 별칭. `--quick`과 `--minimal`은 결과가 동일하며, 사용자가 편한 쪽을 쓸 수 있다. `--basic`은 4단계 체계 고유이며 2축 alias가 없음(의도적 — "quick 상위"는 2축에서 불필요한 세분화).

#### --team 모드
```
┌─ PM (Lead): Phase 분배, 결과 종합, 리포트 통합
├─ QA Engineer: Phase 2-5 실행, 시나리오 검증, DB 상태 확인
├─ Security Sentinel: SQL Injection, XSS, 권한 우회 테스트
├─ Performance Prophet: N+1 쿼리, 대량 데이터, 인덱스 누락
└─ Access Advocate: 권한별 접근, 세션 변조, 비인가 API 호출
```

`--team` 단독 사용 시 기본 난이도 = `--full`(= `--thorough` alias).

---

### /qa-e2e 프리셋

**qa-e2e는 depth 축을 적용하지 않는다.** 이유는 E2E 테스트의 본질이 **시나리오 파일(`test_scenarios.md`)에 선언된 TC 집합 전체 실행**이며, "깊이를 줄여 일부만 실행"은 시나리오 자체를 쪼개는 작업이지 depth 옵션이 아니기 때문이다. 대신 **특정 TC만 실행**하는 `--tc TC-N` 옵션으로 범위를 제어한다.

#### 지원 축 요약

| 축 | qa-e2e 지원 여부 | 옵션 |
|----|------------------|------|
| depth | ✗ | 없음 — TC 단위 `--tc TC-N`으로 범위 제어 |
| execution | ✓ | 기본 단일 / `--team` (다관점 병렬) |
| 추가 modifier | ✓ | `--browser`(Playwright UI), `--headed`(관찰 모드), `--prepare`(데이터 준비만) |

#### --team 모드
```
┌─ PM (Lead): TC 분배, 결과 종합, 리포트 통합
├─ QA Engineer: TC별 시나리오 실행, DB 상태 검증, 계산 검증
├─ DBA: 데이터 정합성, 트랜잭션, 외래키 무결성
├─ Security Sentinel: 결제/환불 보안, 금액 변조, 권한 우회
└─ Explorer: 크로스 도메인 영향, 연관 프로세스 사이드이펙트
```

`--team` 사용 시 범위는 전 TC(또는 `--tc`로 필터된 집합)에 팀 구성 적용.

---

## 프리셋 선택 가이드
```

- [ ] **Step 3: L116 "핵심 규칙" 박스 점검** — "`--team` 단독 사용 시 기본 깊이 = thorough" 규칙이 qa-e2e에는 적용 안됨을 명시

old_string:
```markdown
### 핵심 규칙

> **`--team` 단독 사용 시 기본 깊이 = thorough (최대 성능)**

팀 에이전트를 투입한다는 것은 중요한 작업이라는 의미이므로,
명시적으로 `--quick`이나 `--standard`를 지정하지 않는 한 최대 깊이를 적용합니다.
```

new_string:
```markdown
### 핵심 규칙

> **`--team` 단독 사용 시 기본 깊이 = thorough (최대 성능)**

팀 에이전트를 투입한다는 것은 중요한 작업이라는 의미이므로,
명시적으로 `--quick`이나 `--standard`를 지정하지 않는 한 최대 깊이를 적용합니다.

**예외:**
- `/qa-test --team`은 기본값 `--full`(= `--thorough` alias) 적용 — 동일 규칙
- `/qa-e2e --team`은 depth 축 미적용이므로 깊이 기본값 개념이 없음 — 전 TC(또는 `--tc` 필터 집합) 대상 팀 실행
```

- [ ] **Step 4: 검증 — 확장 반영 + dead 링크 없음**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) 테이블에 qa-test와 qa-e2e 행 추가 확인
grep -c "^| \`/qa-" docs/14-preset-system.md
# 기대: 2 (qa-test + qa-e2e)

# (b) 신규 섹션 헤더 존재
grep -nE "^### /qa-(test|e2e) 프리셋" docs/14-preset-system.md
# 기대: 2줄 (각 섹션 헤더 1번씩)

# (c) qa-test 매핑 테이블 존재 확인
grep "qa-test 라벨.*2축 alias" docs/14-preset-system.md
# 기대: 1줄

# (d) qa-e2e depth 미적용 주석 존재
grep "depth 축을 적용하지 않는다" docs/14-preset-system.md
# 기대: 1줄

# (e) 파일이 여전히 유효한 markdown (정렬된 헤더 수, 끊긴 code fence 없음)
awk 'BEGIN{open=0} /^```/{open=!open} END{exit open}' docs/14-preset-system.md
echo "code fence balance: $?"
# 기대: code fence balance: 0 (균형)
```

---

## Task 2: `CLAUDE.md:56-63` "PDARR + preset system" 섹션 정정

**Why:** 현재 섹션은 "6 skills에 depth + execution 2축이 동일하게 적용된다"는 오주장을 포함한다. qa-test는 라벨이 4단계로 다르고, qa-e2e는 depth 축 자체가 없다. canonical이 사실과 어긋나면 consumer tier(각 SKILL.md 링크) 전체가 오염된다. **가장 짧지만 정확성이 결정적**인 수정.

**Files:**
- Modify: `CLAUDE.md` (L56-63)

- [ ] **Step 1: "PDARR + preset system" 섹션 재작성**

old_string:
```markdown
## PDARR + preset system (what the skills encode)

- **Flow**: `/dispatch` → `/prd` → `/analyze` → `/spec` → `/run` → `/check-code` → `/reflect` → `/complete` → `/stage`
- **2-axis presets** on `analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`:
  - depth: `--quick` / standard / `--thorough`
  - execution: single (default) / `--team`
  - `--team` used alone implies `--thorough`
- Complexity tiers (Trivial / Simple / Medium / Complex) in `/dispatch` drive which subset of the flow runs. Keep these tier names consistent across skills and docs — `/dispatch` and `.claude/rules/subagent-strategy.md` both reference them.
```

new_string:
```markdown
## PDARR + preset system (what the skills encode)

- **Flow**: `/dispatch` → `/prd` → `/analyze` → `/spec` → `/run` → `/check-code` → `/reflect` → `/complete` → `/stage`
- **2-axis presets** — canonical details in [`docs/14-preset-system.md`](docs/14-preset-system.md):
  - depth axis (`--quick` / standard / `--thorough`): applies to `analyze`, `spec`, `check-spec`, `check-code`
  - depth axis with 4-label alias (`--minimal`/`--basic`/`--standard`/`--full` ↔ quick/standard/thorough): applies to `qa-test`
  - execution axis (single (default) / `--team`): applies to all 6 skills (`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`)
  - `qa-e2e` has **no depth axis** (scenario-driven — use `--tc TC-N` for range control)
  - `--team` used alone implies `--thorough` (or `--full` for qa-test). Not applicable to qa-e2e.
- Complexity tiers (Trivial / Simple / Medium / Complex) in `/dispatch` drive which subset of the flow runs. Keep these tier names consistent across skills and docs — `/dispatch` and `.claude/rules/subagent-strategy.md` both reference them.
```

- [ ] **Step 2: 검증 — canonical 위치 정확 + 링크 유효**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) docs/14 링크 유효
test -f docs/14-preset-system.md && echo "docs/14 exists"
# 기대: docs/14 exists

# (b) "qa-e2e has no depth axis" 명시 존재
grep "qa-e2e.*no depth axis" CLAUDE.md
# 기대: 1줄

# (c) 나머지 CLAUDE.md 섹션 불변 (Versioning 섹션이 변경되지 않았는지 확인)
grep -c "^## " CLAUDE.md
# 기대: 11 (섹션 수 동일, P1-1 기준선)
```

---

## Task 3: 6 SKILL.md 프리셋 섹션 축소

**Why:** canonical(CLAUDE.md:56-63 + docs/14)이 준비된 상태에서 각 스킬의 독자 프리셋 정의를 링크로 이관. 동일 2축 체계를 6번 반복 선언하던 drift surface 영구 제거. **스킬 고유 정보(팀 구성, Phase 매핑, 실행 흐름, 리포트 섹션)는 보존** — canonical에 녹여넣으면 오히려 canonical이 비대해져 역효과.

**Files:** 6 SKILL.md 병렬 수정 가능하나 main agent가 직접 Edit 진행 (각 파일이 작음, subagent 오버헤드 ~14k × 6 > 14k 회피). 순차 처리.

### Task 3.1: `skills/analyze/SKILL.md` 프리셋 섹션 축소

- [ ] **Step 1: L11-41 `## 분석 프리셋` 섹션 교체**

현재 L11-41 사이 31줄(2축 테이블 + 조합 예시 + --quick/--thorough 상세 + --team 모드) 중 **--team 팀 구성 박스(L57-66)는 보존** — 스킬 고유 정보. L11-54(프리셋 섹션 본체)만 교체.

old_string (L11부터 L54 `---` 앵커까지 — 읽기로 확정한 블록):
```
## 분석 프리셋

### 깊이(depth)와 실행(mode) 2축 체계

**깊이 (depth)** — 분석의 범위와 상세도:

| 깊이 | 시간 | 내용 |
|------|------|------|
| `--quick` | ~2분 | 영향 파일 목록 + 간단 수정 방향 |
| (기본) standard | ~5분 | 영향 분석 + 실행 전략(2차 판단) |
| `--thorough` | ~15분 | 다관점 심층 분석 + 대안 비교 |

**실행 (mode)** — 단일 에이전트 vs 팀:

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 분석 |
| `--team` | Explorer+Architect+DBA 병렬 분석 |

### 조합 사용

```
/analyze {기능}                    # standard + 단일 (기본)
/analyze --quick {버그}            # quick + 단일
/analyze --thorough {기능}         # thorough + 단일
/analyze --team {기능}             # thorough + 팀 (기본 최대 깊이)
/analyze --team --quick {기능}     # quick + 팀 (빠른 팀 탐색)
/analyze --team --standard {기능}  # standard + 팀
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### --quick 깊이
영향 파일 목록과 수정 방향만 빠르게 출력:
1. 관련 파일 Grep/Glob으로 식별
2. 수정 포인트 (파일:라인) 목록
3. 간단한 수정 방향 1줄

### --thorough 깊이
standard + 아래 심층 분석 추가:
1. **대안 비교**: 접근 방법 2-3개를 비교 (장단점, 위험, 공수)
2. **아키텍처 영향**: 레이어별 변경 영향도, 하위호환 분석
3. **성능 영향**: 쿼리 복잡도, 인덱스 영향, 대용량 시나리오
4. **보안 영향**: 새 입력 경로의 보안 위험 사전 식별
5. **의존성 그래프**: 파일 간 import/include/호출 관계 시각화
```

new_string:
```
## 분석 프리셋 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계(depth × execution 2축)는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#analyze-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

### /analyze 고유 범위 요약

| 깊이 | 시간 | 출력 |
|------|------|------|
| `--quick` | ~2분 | 영향 파일 목록 + 수정 방향 1줄 |
| standard (기본) | ~5분 | 영향 분석 + 실행 전략(2차 판단) |
| `--thorough` | ~15분 | 다관점 심층 분석 + 대안 2-3개 비교 + 의존성 그래프 |

**`--thorough`에서 추가되는 항목:** 대안 비교, 아키텍처 영향, 성능 영향, 보안 영향, 의존성 그래프(import/include/호출 시각화).
```

- [ ] **Step 2: frontmatter description 재작성 (P1-8)**

old_string:
```
description: "코드베이스 분석 및 실행 전략 추천. 3단계 프리셋(quick/standard/thorough) + 팀 분석(--team) 지원. 코딩하지 않고 분석 결과만 출력."
```

new_string:
```
description: "PDARR pre-spec. 코드베이스 영향 분석 + 실행 전략 추천. 코드 작성 없음."
```

**근거:** strategy §P1-8 — "공통 preset 문구(3단계 프리셋 + --team) 제거, PDARR 축 위치만 명시". preset 체계 변경 시 description 불변.

### Task 3.2: `skills/spec/SKILL.md` 프리셋 섹션 축소

- [ ] **Step 1: L10-77 `## 명세서 프리셋` 섹션 교체 — 팀 워크플로우 5단계는 보존**

old_string (L10부터 L77 `---` 앵커 바로 전까지, 팀 워크플로우 섹션 전체 포함):
```
## 명세서 프리셋

### 깊이(depth)와 실행(mode) 2축 체계

**깊이 (depth)** — 명세서의 범위와 상세도:

| 깊이 | 시간 | 내용 |
|------|------|------|
| `--quick` | ~3분 | architecture.md만 (핵심 구조) |
| (기본) standard | ~10분 | architecture + api_design + database_schema |
| `--thorough` | ~20분 | 전체 9섹션 + 대안 비교 + 보안/성능 설계 |

**실행 (mode)** — 단일 에이전트 vs 팀:

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 작성 |
| `--team` | Architect+DBA+Explorer+Designer 협업 |

### 조합 사용

```
/spec                              # standard + 단일 (기본)
/spec --quick                      # quick + 단일
/spec --thorough                   # thorough + 단일
/spec --team                       # thorough + 팀 (기본 최대 깊이)
/spec --team --quick               # quick + 팀 (빠른 팀 설계)
/spec --team --standard            # standard + 팀
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### --quick 깊이
기존 유사 패턴이 명확할 때 최소 명세:
1. architecture.md: 개요 + 레이어 구조 + 구현 순서만
2. 유사 패턴 참조 파일 경로 목록
3. 추정 소요 시간

### --thorough 깊이
standard + 아래 심층 내용 추가:
1. **대안 비교**: 설계 접근법 2-3개 비교 (장단점, 확장성, 유지보수성)
2. **보안 설계**: 입력 검증, 권한 체크, XSS/SQL Injection 방어 명세
3. **성능 설계**: 쿼리 최적화 전략, 인덱스 계획, 캐싱 전략
4. **마이그레이션 계획**: 기존 데이터 영향, 롤백 전략
5. **i18n 키 설계**: 전체 키 목록 + 중복 검사 결과

### --team 모드 (Agent Teams)
전문 에이전트 4-5명이 동시에 다른 관점에서 설계:

```
팀 구성:
┌─ PM (Lead): 설계 조율, 결과 종합, 품질 게이트
├─ Explorer (haiku→sonnet): 유사 패턴 탐색, 재사용 컴포넌트 식별
├─ Architect (sonnet/opus): 구조 설계, API 설계
├─ DBA: DB 스키마 설계, 인덱스 계획, 쿼리 최적화 전략
└─ Designer: UI 구조 설계, 스타일 계획, UX 패턴 선정 (해당 시)
```

**워크플로우**:
1. Explorer + DBA 병렬 분석 (코드/DB 현황 파악)
2. Architect가 분석 결과 기반 구조 설계 (Handoff 수신)
3. DBA가 database_schema.md + create_table.sql 작성
4. Designer가 UI 구조 설계 (해당 시)
5. PM이 종합 → 사용자 승인 요청

- Handoff Protocol: `.claude/team/protocols/handoff-protocol.md`
- Failure Policy: `.claude/team/workflows/failure-policy.yaml`
- 에이전트 프롬프트: `.claude/team/prompts/{agent}.md`
```

new_string:
```
## 명세서 프리셋 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계(depth × execution 2축)는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#spec-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

### /spec 고유 범위 요약

| 깊이 | 시간 | 출력 |
|------|------|------|
| `--quick` | ~3분 | architecture.md만 (핵심 구조) |
| standard (기본) | ~10분 | architecture + api_design + database_schema |
| `--thorough` | ~20분 | 전체 9섹션 + 대안 비교 + 보안/성능 설계 + 마이그레이션 + i18n |

**`--thorough`에서 추가되는 항목:** 설계 접근법 2-3개 대안 비교, 보안 설계(XSS/SQL Injection/권한), 성능 설계(쿼리/인덱스/캐싱), 마이그레이션(롤백 전략), i18n 키 설계(중복 검사).

### --team 모드: 워크플로우

팀 구성(PM/Explorer/Architect/DBA/Designer)과 공통 규칙은 canonical 참조. /spec 고유 실행 순서:

1. Explorer + DBA 병렬 분석 (코드/DB 현황 파악)
2. Architect가 분석 결과 기반 구조 설계 (Handoff 수신)
3. DBA가 `database_schema.md` + `create_table.sql` 작성
4. Designer가 UI 구조 설계 (해당 시)
5. PM이 종합 → 사용자 승인 요청

- Handoff Protocol: `.claude/team/protocols/handoff-protocol.md`
- Failure Policy: `.claude/team/workflows/failure-policy.yaml`
- 에이전트 프롬프트: `.claude/team/prompts/{agent}.md`
```

- [ ] **Step 2: frontmatter description 재작성 (P1-8)**

old_string:
```
description: "기술 명세서 작성. 3단계 프리셋(quick/standard/thorough) + 팀 설계(--team) 지원. docs/spec/[module]/에 문서 생성. 코딩하지 않음."
```

new_string:
```
description: "PDARR author. 기술 명세서 작성. docs/spec/[module]/ 생성."
```

### Task 3.3: `skills/check-spec/SKILL.md` 프리셋 섹션 축소

- [ ] **Step 1: L10-60 `## 설계 검수 프리셋` 섹션 교체**

old_string (L10부터 L60 `---` 앵커 바로 전까지, 팀 구성 박스까지 포함):
```
## 설계 검수 프리셋

### 깊이(depth)와 실행(mode) 2축 체계

**깊이 (depth)** — 검수의 범위와 상세도:

| 깊이 | 시간 | 내용 |
|------|------|------|
| `--quick` | ~2분 | 문서 구조 + 필수 섹션 존재 여부만 |
| (기본) standard | ~5분 | 구조 + 코드베이스 대조 + 규칙 검증 (Phase 1~3) |
| `--thorough` | ~10분 | 전체 Phase + 요구사항 완전성 심층 + 대안 검토 |

**실행 (mode)** — 단일 에이전트 vs 팀:

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 검수 |
| `--team` | Architect+DBA+Explorer 다관점 검수 |

### 조합 사용

```
/check-spec {모듈}                    # standard + 단일 (기본)
/check-spec --quick {모듈}            # quick + 단일
/check-spec --thorough {모듈}         # thorough + 단일
/check-spec --team {모듈}             # thorough + 팀 (기본 최대 깊이)
/check-spec --team --quick {모듈}     # quick + 팀 (빠른 구조 확인)
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### --quick 깊이
1. 문서 파일 존재 여부 (architecture.md, api_design.md, database_schema.md)
2. 필수 섹션 헤더 존재 여부
3. 명백한 누락 항목 식별

### --thorough 깊이
standard + 추가:
1. **요구사항 완전성 심층** (0절 전체): 비즈니스 로직, 엣지 케이스, 상태 전이
2. **대안 검토**: 설계 대안의 장단점이 충분히 비교되었는지
3. **보안/성능 설계**: 공격 벡터, N+1, 인덱스 계획이 명세에 포함되었는지
4. **마이그레이션 리스크**: 기존 데이터 영향, 롤백 전략 유무

### --team 모드 (Agent Teams)
```
팀 구성:
┌─ PM (Lead): 검수 조율, 결과 종합
├─ Architect: 설계 일관성, 레이어 분리, 패턴 준수
├─ DBA: DB 스키마 정합성, 인덱스 계획, 쿼리 최적화 전략
└─ Explorer: 코드베이스 대조, 유사 패턴 비교, 영향 범위 확인
```
```

new_string:
```
## 설계 검수 프리셋 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계(depth × execution 2축)는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#check-spec-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

### /check-spec 고유 범위 요약

| 깊이 | 시간 | 출력 |
|------|------|------|
| `--quick` | ~2분 | 문서 파일 + 필수 섹션 존재 여부만 |
| standard (기본) | ~5분 | 구조 + 코드베이스 대조 + 규칙 검증 (Phase 1-3) |
| `--thorough` | ~10분 | 전체 Phase + 요구사항 완전성 심층(0절) + 대안 검토 + 마이그레이션 리스크 |

**`--thorough`에서 추가되는 항목:** 요구사항 완전성 심층(비즈니스 로직/엣지 케이스/상태 전이), 설계 대안 비교, 보안/성능 설계 유무(공격 벡터/N+1/인덱스), 마이그레이션 리스크(데이터 영향/롤백).
```

- [ ] **Step 2: frontmatter description 재작성 (P1-8)**

old_string:
```
description: "설계문서(spec) 검수. 3단계 프리셋(quick/standard/thorough) + 팀 검수(--team) 지원. docs/spec/ 문서의 규칙/코드베이스 일관성 검토."
```

new_string:
```
description: "PDARR post-spec. docs/spec/ 문서의 규칙·코드베이스 일관성 검증."
```

### Task 3.4: `skills/check-code/SKILL.md` 프리셋 섹션 축소

- [ ] **Step 1: L19-54 `## 실행 모드 (프리셋)` 섹션 교체 — "기존 호환 모드" 4줄은 보존**

old_string (L19부터 L47까지 "기존 호환 모드" 바로 앞까지):
```
## 실행 모드 (프리셋) — 깊이(depth) + 실행(mode) 2축

### 깊이 (depth)

| 깊이 | 시간 | Phase |
|------|------|-------|
| `--quick` | ~2분 | Phase 1만 |
| (기본) standard | ~10분 | Phase 1→2→3→6 |
| `--thorough` | ~20분 | Phase 1→2→3→4→5→6 |

### 실행 (mode)

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 검수 |
| `--team` | Specialist Reviewers 병렬 검수 |

### 조합 사용

```
/check-code {모듈}                    # standard + 단일 (기본)
/check-code --quick {모듈}            # quick + 단일
/check-code --thorough {모듈}         # thorough + 단일
/check-code --team {모듈}             # thorough + 팀 (기본 최대 깊이)
/check-code --team --quick {모듈}     # quick + 팀 (빠른 팀 스캔)
/check-code --team --standard {모듈}  # standard + 팀
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)
```

new_string:
```
## 실행 모드 (프리셋) <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계(depth × execution 2축)는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#check-code-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

### /check-code 고유 범위 요약 (Phase 매핑)

| 깊이 | 시간 | 실행 Phase |
|------|------|-----------|
| `--quick` | ~2분 | Phase 1만 (자동 분석) |
| standard (기본) | ~10분 | Phase 1→2→3→6 (보안/성능/아키텍처/종합판정) |
| `--thorough` | ~20분 | Phase 1→2→3→4→5→6 (+ UX/접근제어, + 테스트 품질) |
```

**Note:** L49-54의 "기존 호환 모드" 4줄(`/check-code --context`, `/check-code --full`)은 스킬 고유 옵션이므로 **보존**. 해당 블록 미편집. L474-488의 `## --team 모드 (Agent Teams 리뷰)` 섹션도 팀 구성 상세라 보존.

**Note:** check-code는 P1-7/P1-8 description 재작성 대상 **아님** (strategy에서 명시 제외). frontmatter description은 **불변**, 본문만 수정.

### Task 3.5: `skills/qa-test/SKILL.md` 프리셋 섹션 축소 + 2축 매핑 추가

- [ ] **Step 1: L10-21 `## 사용법` 섹션을 "매핑 테이블 + canonical 링크" 형태로 확장**

old_string:
```
## 사용법

```
/qa-test                              # 변경 파일 자동 테스트 (난이도 자동)
/qa-test [기능명]                      # 특정 기능 테스트
/qa-test --minimal                    # 최소 테스트 (문법만)
/qa-test --basic                      # 기본 테스트
/qa-test --standard                   # 표준 테스트
/qa-test --full                       # 전체 테스트
/qa-test customerDetailPopup --full   # 특정 기능 전체 테스트
/qa-test --team                       # 팀 에이전트 종합 QA (full + 다관점)
/qa-test --team --basic [기능명]      # 팀 에이전트 + 난이도 조합
```
```

new_string:
```
## 사용법 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#qa-test-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

### 난이도 라벨 ↔ 2축 depth alias

qa-test는 기존 4단계 라벨을 보존하면서 2축 alias도 지원합니다(둘 다 동시에 유효).

| 4단계 라벨 | 2축 alias | 범위 |
|-----------|-----------|------|
| `--minimal` | `--quick` | 문법만 (Phase 2) |
| `--basic` | (alias 없음) | 문법 + 품질 (Phase 2-3) |
| `--standard` (기본) | standard | + UI/이벤트 + 의존성 (Phase 2-5) |
| `--full` | `--thorough` | + 이전 리포트 비교 (Phase 2-7) |

### 명령 예시

```
/qa-test                              # 변경 파일 자동 (난이도 자동 판별)
/qa-test [기능명]                      # 특정 기능
/qa-test --minimal        (= --quick)   # 문법만
/qa-test --basic                        # 문법 + 품질
/qa-test --standard       (= standard)  # 기본
/qa-test --full           (= --thorough)# 전체
/qa-test --team                          # 팀 (기본 = --full)
/qa-test --team --basic [기능명]          # 팀 + 기본
```
```

- [ ] **Step 2: L51-59 `## --team 난이도 조합` 중복 규칙 삭제 (canonical로 이관됨)**

old_string:
```
### --team 난이도 조합

```
--team 단독     = full + 팀 (기본 최대 깊이)
--team --minimal = minimal + 팀 (문법만 다관점)
--team --basic   = basic + 팀
--team --standard = standard + 팀
--team --full    = full + 팀 (명시적)
```
```

new_string:
```
### --team 난이도 조합

`--team` 단독 사용 시 기본 난이도 = `--full`(= `--thorough` alias). 상세 조합은 위 난이도 매핑 테이블 참조.
```

**Note:** `## --team 모드` 상단 설명(L25-30), 팀 구성 테이블(L32-38), 실행 흐름(L42-49), 리포트 추가 섹션(L63-86), Tiebreaker(L88-93)는 **스킬 고유 정보 전부 보존**.

- [ ] **Step 3: frontmatter description 재작성 (P1-7)**

old_string:
```
description: "QA 자동화. 변경 파일에 대해 난이도별(minimal/basic/standard/full) 종합 QA 테스트 수행 및 리포트 생성."
```

new_string:
```
description: "단위·통합 레벨 QA 자동 실행. 변경 파일 대상."
```

**근거:** strategy §P1-7 — "test / qa-test / qa-e2e description 재작성. 테스트 피라미드 층 판별을 description만으로 가능하도록 범위 명확화".

### Task 3.6: `skills/qa-e2e/SKILL.md` 프리셋 섹션 축소

- [ ] **Step 1: L10-24 `## 사용법` 섹션 상단에 depth 축 미적용 안내 추가 + canonical 링크**

old_string:
```
## 사용법

```
/qa-e2e                                    # 현재 세션 작업의 테스트 시나리오 자동 탐색
/qa-e2e {모듈명}                            # docs/spec/{모듈}/test_scenarios.md 기반 (DB 검증)
/qa-e2e {시나리오파일경로}                   # 특정 시나리오 파일 지정
/qa-e2e {모듈명} --tc TC-2                  # 특정 테스트 케이스만 실행
/qa-e2e {모듈명} --prepare                  # 테스트 데이터 준비만 (실행 안 함)
/qa-e2e --team {모듈명}                     # 팀 에이전트 E2E (다관점 병렬 검증)
/qa-e2e --team {모듈명} --tc TC-2           # 팀 + 특정 TC만
/qa-e2e --browser {모듈명}                  # Playwright 브라우저 E2E 테스트
/qa-e2e --browser {모듈명} --headed         # Playwright 유저 관찰 모드
/qa-e2e --browser {모듈명} --tc TC-2        # 특정 TC만 브라우저 테스트
```
```

new_string:
```
## 사용법 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#qa-e2e-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

> **qa-e2e는 depth 축을 적용하지 않습니다** — E2E는 시나리오 기반이므로 "깊이를 줄여 부분만 실행"이 아닌 **`--tc TC-N`으로 TC 단위 필터**로 범위를 제어합니다. execution 축(`--team`)과 modifier(`--browser`/`--headed`/`--prepare`)는 지원합니다.

```
/qa-e2e                                    # 현재 세션 작업의 테스트 시나리오 자동 탐색
/qa-e2e {모듈명}                            # docs/spec/{모듈}/test_scenarios.md 기반 (DB 검증)
/qa-e2e {시나리오파일경로}                   # 특정 시나리오 파일 지정
/qa-e2e {모듈명} --tc TC-2                  # 특정 테스트 케이스만 실행
/qa-e2e {모듈명} --prepare                  # 테스트 데이터 준비만 (실행 안 함)
/qa-e2e --team {모듈명}                     # 팀 에이전트 E2E (다관점 병렬 검증)
/qa-e2e --team {모듈명} --tc TC-2           # 팀 + 특정 TC만
/qa-e2e --browser {모듈명}                  # Playwright 브라우저 E2E 테스트
/qa-e2e --browser {모듈명} --headed         # Playwright 유저 관찰 모드
/qa-e2e --browser {모듈명} --tc TC-2        # 특정 TC만 브라우저 테스트
```
```

**Note:** 나머지 모든 섹션(L27-480+, `## --team 모드` 전체, Phase 0-4, --browser 섹션 전체)은 스킬 고유 기능이므로 **보존**. 원본 2축 주장이 없었으므로 삭제할 canonical 중복 없음.

**Note:** qa-e2e frontmatter description은 **변경하지 않는다** — strategy §P1-7에서 "이미 qa-e2e는 명확"으로 판정되어 본 번들에서 명시 out-of-scope. 본문 수정(depth 축 미적용 경고)만 반영.

### Task 3.7: `skills/test/SKILL.md` description 재작성 (P1-7, 신규 스코프)

**Why:** test 스킬은 P1-2 본문 수정 대상이 아니지만 P1-7 description 재작성 대상. strategy P1-7 원문:
> test: "TDD Red 단계. 구현 전 테스트 케이스 작성. 실행 없음."

**현재 description:** `"TDD 테스트 작성. 구현 전 테스트 케이스를 생성. Red-Green-Refactor 사이클의 Red 단계만 담당."`

거의 동일 의도이지만 strategy 제안이 더 간결(`"실행 없음"` 강조로 run과의 경계 명확화). non-breaking.

**Files:**
- Modify: `skills/test/SKILL.md` (frontmatter description만, 본문 및 나머지 섹션 불변)

- [ ] **Step 1: frontmatter description 재작성**

old_string:
```
description: "TDD 테스트 작성. 구현 전 테스트 케이스를 생성. Red-Green-Refactor 사이클의 Red 단계만 담당."
```

new_string:
```
description: "TDD Red 단계. 구현 전 테스트 케이스 작성. 실행 없음."
```

- [ ] **Step 2: 검증**

```bash
cd /Users/jeongsik/develop/claude-code-guide
grep "^description:" skills/test/SKILL.md
# 기대: description: "TDD Red 단계. 구현 전 테스트 케이스 작성. 실행 없음."

# 본문(TDD 원칙 이후) 불변 확인
head -10 skills/test/SKILL.md
# 기대: Line 6 이후 원문 그대로
```

- [ ] **Step 3: 6 SKILL.md 일괄 검증 (P1-2 + P1-7 + P1-8 통합)**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) 6 SKILL.md 모두 PRESET_CANONICAL_LINK 마커 존재
for f in analyze spec check-spec check-code qa-test qa-e2e; do
  grep -c "<!-- PRESET_CANONICAL_LINK -->" skills/$f/SKILL.md
done
# 기대: 각 파일당 1

# (b) 중복 2축 테이블 잔존 없음 (6 파일에서 `--quick.*standard.*--thorough` 헤더 행이 남아있지 않음)
# qa-test는 매핑 테이블이 있으므로 패턴 특정 필요
grep -nE "^\|.*--quick.*standard.*--thorough.*\|$" skills/analyze/SKILL.md skills/spec/SKILL.md skills/check-spec/SKILL.md skills/check-code/SKILL.md skills/qa-test/SKILL.md skills/qa-e2e/SKILL.md
# 기대: qa-test의 매핑 테이블 1줄만 (alias 표 헤더 `| 4단계 라벨 | 2축 alias | 범위 |` 다르므로 매칭 안됨). 실제 출력: 빈 결과 또는 qa-test 매핑 예외 행 없음

# (c) `--team 단독 사용 시 기본 깊이 = thorough` 중복 선언 0건
grep -rn "--team.*단독.*기본 깊이" skills/ --include="SKILL.md"
# 기대: 출력 없음 — canonical에만 존재

# (d) 스킬별 고유 정보는 보존되었는지 (sanity check — team 구성 박스 존재)
grep -l "PM (Lead)" skills/*/SKILL.md | wc -l
# 기대: ≥ 6 (6 SKILL 모두에 --team 팀 구성 박스 보존)

# (e) P1-7/P1-8 description 재작성 일괄 검증 (Bundle C)
grep "^description:" skills/analyze/SKILL.md skills/spec/SKILL.md skills/check-spec/SKILL.md skills/test/SKILL.md skills/qa-test/SKILL.md
# 기대:
#   skills/analyze/SKILL.md:description: "PDARR pre-spec. ..."
#   skills/spec/SKILL.md:description: "PDARR author. ..."
#   skills/check-spec/SKILL.md:description: "PDARR post-spec. ..."
#   skills/test/SKILL.md:description: "TDD Red 단계. ..."
#   skills/qa-test/SKILL.md:description: "단위·통합 레벨 QA 자동 실행. ..."

# (f) qa-e2e와 check-code description은 변경 없음 (strategy 명시 out-of-scope)
grep "^description:" skills/qa-e2e/SKILL.md skills/check-code/SKILL.md
# 기대: 기존 description 그대로 (변경 없음)

# (g) description에서 "3단계 프리셋" 문구 잔존 없음 (P1-8 완료 검증)
grep -lE '3단계 프리셋|quick.*standard.*thorough' skills/analyze/SKILL.md skills/spec/SKILL.md skills/check-spec/SKILL.md 2>/dev/null | head -5
# 기대: 출력 없음 (3 파일 모두 description에서 preset 문구 제거됨)
```

---

## Task 4: `skills/README.md`와 `README.md` 프리셋 섹션 축약

**Why:** 두 문서는 canonical(CLAUDE.md + docs/14)의 **요약 + 링크**여야 한다. skills/README.md는 현재 16줄로 거의 canonical 중복이고, README.md는 "3개 스킬" drift까지 있어 오정보 상태.

**Files:**
- Modify: `skills/README.md:77-92`
- Modify: `README.md:404-422`

- [ ] **Step 1: `skills/README.md:77-92` 축약**

old_string:
```
## 프리셋 시스템

`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`는 **2축 프리셋**을 지원합니다.

```
깊이(depth):  --quick ← standard(기본) → --thorough
실행(mode):   단일    ← 기본           → --team
```

```bash
/analyze --quick {버그}          # 빠른 분석
/analyze {기능}                  # 표준 분석
/analyze --thorough {기능}       # 심층 분석
/analyze --team {기능}           # 팀 에이전트 분석 (최대 깊이)
/check-code --team --quick {모듈} # 팀 + 빠른 스캔 (조합 가능)
```
```

new_string:
```
## 프리셋 시스템

6개 스킬이 2축 프리셋(depth × execution)을 지원합니다. 상세 체계는 canonical 문서 참조:

- [`CLAUDE.md` §PDARR + preset system](../CLAUDE.md#pdarr--preset-system) — 규칙 요약
- [`docs/14-preset-system.md`](../docs/14-preset-system.md) — 스킬별 depth 범위/팀 구성/조합 예시

**적용 스킬:**

| 스킬 | depth | execution | 비고 |
|------|-------|-----------|------|
| `analyze`, `spec`, `check-spec`, `check-code` | ✓ | ✓ | 표준 2축 |
| `qa-test` | ✓ (4라벨 + alias) | ✓ | `--minimal/--basic/--standard/--full` ↔ `--quick/standard/--thorough` |
| `qa-e2e` | ✗ | ✓ | 시나리오 기반 (`--tc TC-N`으로 범위 제어) |

```bash
/analyze --quick {버그}              # 빠른 분석
/analyze --team {기능}               # 팀 분석 (기본 thorough)
/check-code --team --quick {모듈}    # 팀 + 빠른 스캔 조합
```
```

- [ ] **Step 2: `README.md:404-422` 정정 — "3개 스킬" → 6개 + canonical 링크**

old_string:
```
### 프리셋 시스템 (v3.0 확장)

**깊이(depth) x 실행(mode) 2축 독립 제어:**

```
깊이:  --quick ← standard → --thorough
실행:  단일    ← 기본    → --team

--team 단독 = thorough + 팀 (기본 최대 성능)
--team --quick = quick + 팀 (조합 가능)
```

**3개 스킬에 공통 적용:**
```
/analyze --team {기능}              # 팀 분석 (최대 깊이)
/spec --team                        # 팀 설계 (최대 깊이)
/check-code --team {모듈}           # 팀 리뷰 (최대 깊이)
/check-code --team --quick {모듈}   # 팀 리뷰 (빠른 스캔)
```

자세한 내용은 [프리셋 시스템](docs/14-preset-system.md), [코드 리뷰 시스템](docs/10-code-review-system.md)을 참조하세요.
```

new_string:
```
### 프리셋 시스템

**깊이(depth) × 실행(mode) 2축 독립 제어.** canonical 규칙은 [`CLAUDE.md` §PDARR + preset system](CLAUDE.md#pdarr--preset-system), 상세 체계는 [`docs/14-preset-system.md`](docs/14-preset-system.md).

**6개 스킬에 공통 적용** (`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`):

```
깊이:  --quick ← standard → --thorough
실행:  단일    ← 기본    → --team

--team 단독 = thorough + 팀 (기본 최대 성능, qa-test는 --full)
qa-e2e는 depth 축 미적용 — --tc TC-N으로 범위 제어
```

```
/analyze --team {기능}              # 팀 분석
/check-code --team --quick {모듈}   # 팀 + 빠른 스캔 조합
/qa-e2e --team {모듈}               # 팀 E2E (전 TC 또는 --tc 필터)
```

6단계 코드 리뷰 Phase 매핑 상세: [코드 리뷰 시스템](docs/10-code-review-system.md).
```

**Note:** `(v3.0 확장)` historical 레이블은 P1-1 out-of-scope 기조에 따라 **제거** — "이 섹션은 v3.0에 추가됨"이라는 현재 상태 주장이 아니라 historical timestamp인지 경계에 가까움. 이번 슬라이스에서는 섹션 전체를 다시 쓰고 있으므로 제거가 자연스럽고 drift surface 축소. P1-1 sweep에서 out-of-scope였던 이유는 "섹션 자체를 재작성하지 않는 스코프"였기 때문.

- [ ] **Step 3: 검증**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) README.md에 "3개 스킬" 잔존 없음
grep "3개 스킬" README.md
# 기대: 출력 없음

# (b) skills/README.md에 canonical 링크 존재
grep -c "CLAUDE.md#pdarr" skills/README.md
# 기대: 1

# (c) README.md에 canonical 링크 존재
grep -c "CLAUDE.md#pdarr" README.md
# 기대: 1

# (d) 두 문서 모두 "6개" 스킬로 갱신
grep -cE "6(개|-)" skills/README.md README.md | grep -v ":0$"
# 기대: 두 파일 모두 매치 (최소 1회 이상)
```

---

## 🔔 Checkpoint (a): `validate-system.sh` 수정 직전

**이 시점 repo 상태 (기대):**
- `docs/14-preset-system.md` — qa-test/qa-e2e 포함 6 스킬 지원
- `CLAUDE.md:56-63` — qa-e2e depth 미적용 명시
- 6 SKILL.md 프리셋 섹션 — canonical 링크 1줄 + 스킬 고유 정보만 남김
- `skills/README.md`, `README.md` — canonical 링크 + 축약 요약
- `validate-system.sh` — 아직 수정 전(마커 검증 체크 추가 예정)

**재개 전 확인:**
- `git status`로 의도한 변경 파일 목록(9개 modified + 1 created)만 stage/unstaged인가
- 이번 Task 5에서 validate 체크를 추가해도 기존 Errors 수(PyYAML baseline 6) 변화 없는가

→ 사용자 확인 후 Task 5 진행.

---

## Task 5: `scripts/validate-system.sh`에 preset canonical marker 체크 추가

**Why:** 이번 슬라이스가 끝나는 순간부터 "프리셋 체계 변경 = canonical 1곳 수정" 규약이 **문서로만** 지켜지고 있다. 향후 누군가 SKILL.md에 2축 테이블을 다시 복사-붙여넣기 하면 drift가 재발생. validate에 마커 체크를 추가하여 **자동 감지** — 이 체크가 없으면 P1-2는 "1회성 정리"에 불과하고 SSOT 관리 시스템이 되지 못한다.

**Files:**
- Modify: `scripts/validate-system.sh`

- [ ] **Step 1: 새 체크 섹션 추가 (체크 9 `Prompt Terminology` 이후, 체크 10으로 삽입)**

**삽입 위치:** 현재 체크 9 종료(case 블록 닫히는 `done` 이후) 직후, 현재의 체크 10 직전. `validate-system.sh`의 섹션 시작 패턴은 `# 10. XXX` 주석 + `echo "Check 10/..."`.

**Edit 접근:** 기존 체크 10의 시작 앵커(`# 10.` 주석)를 찾아 그 앞에 새 블록 삽입.

old_string (기존 체크 10 시작부 — 정확한 위치는 현재 파일 상태 기준, main agent가 Edit 전 Read로 확정 필요):
```bash
# NOTE: 아래 old_string은 구조 가이드. 실제 실행 시 validate-system.sh를 먼저 Read하여
# 현재 체크 10 (또는 마지막 체크 바로 전) 시작 주석을 정확히 복사할 것.
```

**실제 실행 플로우:**
1. `Read scripts/validate-system.sh` (전체 또는 체크 번호 영역)
2. 마지막 체크 번호 확인 (가령 N번이라면), 새 체크를 N+1로 삽입
3. 아래 new_block을 기존 마지막 체크의 종료와 `echo ""` 사이 또는 `# Summary` 블록 직전에 삽입

new_block (추가할 코드):
```bash
# N+1. Preset canonical marker check (v4.0 P1-2)
# 6 스킬의 SKILL.md에 canonical 링크 마커 존재 + 2축 테이블 중복 선언 부재 확인
echo ""
echo "Check N+1: Preset canonical markers (6 skills)"
PRESET_SKILLS=("analyze" "spec" "check-spec" "check-code" "qa-test" "qa-e2e")
PRESET_MARKER="<!-- PRESET_CANONICAL_LINK -->"
MISSING_MARKERS=0
DUPLICATE_TABLES=0

for skill in "${PRESET_SKILLS[@]}"; do
    skill_file="$SKILLS_DIR/$skill/SKILL.md"
    if [ ! -f "$skill_file" ]; then
        echo "  WARNING: $skill/SKILL.md not found (skipping)"
        continue
    fi

    # (a) canonical 마커 존재
    if ! grep -q "$PRESET_MARKER" "$skill_file"; then
        echo "ERROR: $skill/SKILL.md missing preset canonical marker '$PRESET_MARKER'"
        ERRORS=$((ERRORS + 1))
        MISSING_MARKERS=$((MISSING_MARKERS + 1))
    fi

    # (b) 중복 2축 테이블 선언 탐지 — `| ... --quick ... standard ... --thorough ... |` 헤더 패턴
    # qa-test의 alias 매핑 테이블은 헤더가 `| 4단계 라벨 | 2축 alias | 범위 |`로 다르므로 매칭 안됨
    if grep -qE '^\|[^|]*--quick[^|]*\|[^|]*standard[^|]*\|[^|]*--thorough[^|]*\|[[:space:]]*$' "$skill_file"; then
        echo "WARNING: $skill/SKILL.md contains 2-axis depth table — canonical duplication (should link only)"
        WARNINGS=$((WARNINGS + 1))
        DUPLICATE_TABLES=$((DUPLICATE_TABLES + 1))
    fi
done

echo "  Preset canonical markers: $((${#PRESET_SKILLS[@]} - MISSING_MARKERS))/${#PRESET_SKILLS[@]} skills"
if [ "$DUPLICATE_TABLES" -gt 0 ]; then
    echo "  Duplicate 2-axis tables detected: $DUPLICATE_TABLES"
fi
```

**주의:**
- `$SKILLS_DIR` 변수가 validate-system.sh 상단에 이미 존재함(`SKILLS_DIR="$HOME/.claude/skills"` 패턴). 확인 후 없으면 block 상단에 추가.
- "N+1"은 실제 삽입 시 현재 최대 체크 번호 +1로 교체 (예: 현재 18이면 19).
- 패턴 `^\|[^|]*--quick[^|]*\|[^|]*standard[^|]*\|[^|]*--thorough[^|]*\|[[:space:]]*$`는 한 행에 `--quick`, `standard`, `--thorough`가 **모두** 파이프로 구분되어 등장하는 depth 테이블 헤더만 매칭. qa-test의 alias 테이블 헤더(`| 4단계 라벨 | 2축 alias | 범위 |`)와 qa-test 매핑 행(`| `--minimal` | `--quick` | 문법만 (Phase 2) |`)은 패턴 불일치로 오탐 없음.

- [ ] **Step 2: 검증 — 새 체크 동작**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (a) 재설치 + validate 실행
bash scripts/install-skills.sh /tmp/p1-2-install-target --team --force 2>&1 | tail -3
bash scripts/validate-system.sh 2>&1 | grep -A 3 "Preset canonical markers"
# 기대: "Preset canonical markers: 6/6 skills"
# 기대: "Duplicate 2-axis tables detected" 줄 없음 (0건)

# (b) regression — ERROR/WARNING 수가 P1-1 baseline을 초과하지 않음
bash scripts/validate-system.sh 2>&1 | grep -E "^Errors:|^Warnings:"
# 기대: Errors: 6 (PyYAML env baseline), Warnings: 0 (또는 P1-1 baseline과 동일)

# (c) 부정 시뮬레이션 — 마커를 임의 제거하면 ERROR 발생하는지
cp "$HOME/.claude/skills/analyze/SKILL.md" /tmp/analyze-backup.md
sed -i.bak '/PRESET_CANONICAL_LINK/d' "$HOME/.claude/skills/analyze/SKILL.md"
bash scripts/validate-system.sh 2>&1 | grep "analyze.*missing preset canonical"
# 기대: "ERROR: analyze/SKILL.md missing preset canonical marker '<!-- PRESET_CANONICAL_LINK -->'"

# 복원
cp /tmp/analyze-backup.md "$HOME/.claude/skills/analyze/SKILL.md"
rm /tmp/analyze-backup.md "$HOME/.claude/skills/analyze/SKILL.md.bak" 2>/dev/null
bash scripts/validate-system.sh 2>&1 | grep -c "missing preset canonical"
# 기대: 0
```

---

## Task 6: 통합 검증 + 커밋 전 sweep

- [ ] **Step 1: 전체 `git status` + `git diff --stat` 검토**

```bash
cd /Users/jeongsik/develop/claude-code-guide
git status --short
git diff --stat
```

기대 변경 요약 (Bundle C):
- `M  CLAUDE.md` (~8 lines, L56-63 영역)
- `M  README.md` (~19 lines 교체)
- `M  docs/14-preset-system.md` (~80 lines 추가, qa-test/qa-e2e 섹션)
- `M  skills/README.md` (~16 lines 교체)
- `M  skills/analyze/SKILL.md` (~31 lines → ~10 lines + description 1줄)
- `M  skills/spec/SKILL.md` (~68 lines → ~20 lines + description 1줄)
- `M  skills/check-spec/SKILL.md` (~51 lines → ~12 lines + description 1줄)
- `M  skills/check-code/SKILL.md` (~29 lines 교체 — description 및 L49 이후 불변)
- `M  skills/test/SKILL.md` (description 1줄만, 본문 불변)
- `M  skills/qa-test/SKILL.md` (~20 lines 수정 + description 1줄)
- `M  skills/qa-e2e/SKILL.md` (~5 lines 추가, description 불변)
- `M  scripts/validate-system.sh` (~30 lines 추가, 새 체크 블록)
- `A  docs/v4/plans/2026-04-23-p1-2-preset-consolidation.md`

**총 수정 파일: 12개** (M 11 + A 1). description 추가 수정: 5 파일(analyze/spec/check-spec/test/qa-test).

- [ ] **Step 2: 참조 무결성 sweep**

```bash
cd /Users/jeongsik/develop/claude-code-guide

# (1) canonical 링크가 6 SKILL.md에 모두 존재
for f in analyze spec check-spec check-code qa-test qa-e2e; do
  grep -c "CLAUDE.md#pdarr" skills/$f/SKILL.md
done
# 기대: 각 파일당 ≥1

# (2) 6 SKILL.md에 중복 2축 테이블 0건 (canonical이 아닌 곳에서 `--quick...standard...--thorough` 헤더 패턴)
grep -lE '^\|[^|]*--quick[^|]*\|[^|]*standard[^|]*\|[^|]*--thorough[^|]*\|' skills/analyze/SKILL.md skills/spec/SKILL.md skills/check-spec/SKILL.md skills/check-code/SKILL.md skills/qa-test/SKILL.md skills/qa-e2e/SKILL.md
# 기대: 출력 없음

# (3) docs/14에 qa-test/qa-e2e 섹션 존재
grep -c "### /qa-" docs/14-preset-system.md
# 기대: 2

# (4) "3개 스킬" drift 잔존 없음
grep -rn "3개 스킬" . --include="*.md" 2>/dev/null | grep -v "\.audit/\|docs/v4/\|\.git/"
# 기대: 출력 없음

# (5) CLAUDE.md ↔ docs/14 상호 링크 (canonical 원환 성립)
grep -n "docs/14-preset-system" CLAUDE.md
# 기대: ≥1줄
grep -n "CLAUDE.md" docs/14-preset-system.md
# 기대: ≥0 (docs/14 자체는 더 세부이고, 역링크 필수는 아님 — CLAUDE.md가 상위)
```

- [ ] **Step 3: 시스템 재설치 + validate 실행**

```bash
bash scripts/install-skills.sh /tmp/p1-2-install-target --team --force 2>&1 | tail -5
bash scripts/validate-system.sh 2>&1 | tail -15
```

기대:
- `Errors: 6` (PyYAML env baseline과 동일)
- `Warnings: 0`
- 새 체크 출력: `Preset canonical markers: 6/6 skills`

---

## 🔔 Checkpoint (b): 커밋 직전

**이 시점 repo 상태:**
- Task 1-6 모두 완료
- 기대 변경 요약과 `git diff --stat` 일치
- validate-system.sh 신규 체크 포함해서 ERROR baseline 동일

**사용자 확인 후 Task 7 진행.**

---

## Task 7: 단일 커밋 생성

- [ ] **Step 1: 스테이징**

```bash
cd /Users/jeongsik/develop/claude-code-guide
git add CLAUDE.md README.md skills/ docs/14-preset-system.md scripts/validate-system.sh docs/v4/plans/2026-04-23-p1-2-preset-consolidation.md
git status --short
```

기대: Task 6 Step 1의 변경 요약과 정확히 일치.

- [ ] **Step 2: 커밋**

```bash
git commit -m "$(cat <<'EOF'
feat(v4 P1-2+P1-7+P1-8): 프리셋 중복 제거 + 5 스킬 description 재작성

strategy.md §3 P1-2 + P1-7 + P1-8 Bundle C 구현 (사용자 승인 2026-04-23).
6 스킬에서 2축 프리셋 체계가 9곳에 반복 선언되던 문제를 canonical 2-tier
(CLAUDE.md + docs/14) + 소비자 링크 구조로 정리. 동시에 5 SKILL.md의
frontmatter description을 PDARR 축 위치가 드러나도록 간결화.

Canonical 2-tier:
- CLAUDE.md:56-63 — 최상위 4줄 rule (Flow + 2축 요약 + Complexity tier)
- docs/14-preset-system.md — 스킬별 depth 범위/팀 구성/조합 상세

정확성 정정:
- CLAUDE.md — "6 skills가 depth + mode를 동일 적용" 오주장 제거.
  실상: 4 skills 표준 2축 / qa-test 4라벨+alias / qa-e2e mode only
- docs/14 "적용 대상 스킬" 테이블 — 4개 → 6개로 확장, 각 스킬의
  축 지원 여부·비고 열 추가
- docs/14에 qa-test 난이도 ↔ 2축 alias 매핑 테이블 신규 섹션
- docs/14에 qa-e2e depth 축 미적용 사유(시나리오 기반) 명시
- README.md:404-422 — "3개 스킬에 공통 적용" drift → "6개 스킬"로 정정

6 SKILL.md 프리셋 섹션 축소 (약 ~300줄 감소 → ~60줄):
- 각 SKILL.md 상단에 <!-- PRESET_CANONICAL_LINK --> 마커 + canonical
  링크 1줄로 교체
- 보존: 스킬 고유 정보 — 팀 구성 박스, 실행 흐름(spec 5단계),
  Phase 매핑(check-code), 리포트 섹션(qa-test/qa-e2e), Tiebreaker
- qa-test: 기존 --minimal/--basic/--standard/--full 라벨 **보존**
  (non-breaking) + --quick/--thorough alias 병행 지원 명시
- qa-e2e: depth 축 미적용 경고 박스 + --tc/--browser modifier 보존

Skills/README.md + README.md 요약 축약:
- 둘 다 canonical 링크 경유 요약 테이블 형태로 축소
- skills/README.md에 6 스킬 축 지원 매트릭스 추가

validate-system.sh 신규 체크:
- Check N+1: Preset canonical markers — 6 SKILL.md에 마커 존재 여부
- 중복 2축 테이블 헤더 패턴 탐지 (WARNING, 미래 drift 재발 방지)

검증:
- bash scripts/install-skills.sh --team --force + validate-system.sh
  → Errors 6 (PyYAML env baseline, 우리 변경 무관), Warnings 0
- Preset canonical markers: 6/6 skills
- "3개 스킬" drift 잔존 0건
- 6 SKILL.md에 중복 2축 depth 테이블 0건

description 재작성 (5 SKILL.md, P1-7+P1-8):
- analyze: "PDARR pre-spec. 코드베이스 영향 분석 + 실행 전략 추천.
  코드 작성 없음." — "3단계 프리셋" 문구 제거, PDARR 축 명시 (P1-8)
- spec: "PDARR author. 기술 명세서 작성. docs/spec/[module]/ 생성." (P1-8)
- check-spec: "PDARR post-spec. docs/spec/ 문서의 규칙·코드베이스
  일관성 검증." (P1-8)
- test: "TDD Red 단계. 구현 전 테스트 케이스 작성. 실행 없음." — run과의
  경계 명확화 (P1-7)
- qa-test: "단위·통합 레벨 QA 자동 실행. 변경 파일 대상." — 테스트 피라미드
  층 판별을 description만으로 가능 (P1-7)

Non-breaking:
- qa-test 기존 4라벨 사용자 스크립트 호환 유지 (alias는 추가)
- 각 SKILL.md 사용법 명령 줄 그대로 보존
- --team / --browser / --tc / --prepare 등 modifier 그대로
- 신규 description은 동일 개념 더 간결화 — 기능 변경 없음

Explicit out-of-scope (후속 슬라이스):
- check-code, qa-e2e description — strategy가 "이미 명확" 판정
- P1-6 Complexity Tier 임계값 통일 (프리셋과 축 독립)
- P1-9 reflect/complete/organize-docs description
- docs/10-code-review-system.md, agents.yaml:729 중복 — P1-1 out-of-scope
  기조 유지

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 커밋 사후 검증**

```bash
git log --oneline -3
git show --stat HEAD | tail -20
git status
```

기대: 최신 커밋 = feat(v4 P1-2) 또는 feat(v4 P1-2+P1-8), working tree clean.

---

## Remaining Out-of-Scope Items (after P1-2)

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| P1-3 | 에이전트 목록 canonical 통일 | 대기 | P0-A로 일부 선행(동적 파싱 게이트) |
| P1-4 | 스킬 목록 canonical 통일 | 대기 | skills/README.md:31-74 canonical 지정 필요 |
| P1-5 (B2) | `hooks/scripts/*.sh` rename | 대기 | Breaking — 별도 슬라이스 |
| P1-6 | Complexity Tier 임계값 통일 | 대기 | 프리셋과 독립 축 |
| P1-7 | test/qa-test/qa-e2e description 재작성 | **본 슬라이스 완료** (qa-e2e 제외) | Bundle C 포함 |
| P1-8 | analyze/spec/check-spec description 재작성 | **본 슬라이스 완료** | Bundle C 포함 |
| P1-9 | reflect/complete/organize-docs description | 대기 | |
| P2-1~10 | 문서 drift 정리 | 대기 | |

**다음 슬라이스 후보:** P1-4(스킬 목록 canonical) 또는 P1-6(Complexity Tier 통일) — 두 항목 모두 프리셋과 직교, 이번 작업과 독립.
