# v4.0 전략

**생성일**: 2026-04-22
**상태**: 감사 통합 완료, 구현 대기
**출처**: `.audit/result-W{1,2,3}.md` 3 워커 결과를 Coherence-first tie-breaker로 통합
**설계 문서**: [`docs/v4/design.md`](./design.md) · [`docs/v4/plan.md`](./plan.md)

---

## 1. Vision

v4.0은 **coherence 부채 청산 릴리스**이다. v3.0 → v3.2 → v3.3 신규 기능이 쌓이면서 버전 숫자·에이전트 이름·스킬 프리셋·hooks 네이밍·validate 스크립트 커버리지가 여러 층에서 서로 다른 세대를 동시 주장하는 상태 — 즉 **레포가 자기 자신의 SSOT 원칙을 어기는 상태**를 종료한다. v4.0 이후 "버전 bump = 1곳 수정", "에이전트 추가 = agents.yaml 한 곳 수정", "프리셋 정의 변경 = CLAUDE.md 한 곳 수정"이 강제되어야 한다. 신규 기능 추가는 **범위 밖** — 구조 재정렬과 하드코딩 제거에 집중한다.

---

## 2. Breaking Changes

v4.0은 non-breaking 변경이 다수이지만, SSOT 복원을 위해 최소한의 breaking이 필요하다.

| # | 항목 | 현 상태 | v4.0 상태 | Migration |
|---|------|---------|-----------|-----------|
| B1 | `prompts/qa.md` 파일명 | 단축명 `qa.md` (다른 15개 에이전트와 규약 불일치) | `prompts/qa-engineer.md` (agents.yaml 정식명과 일치) | 재설치 시 자동 반영 — **사용자가 직접 `prompts/qa.md`를 수정했다면 CUSTOMIZE 재작성 필요** |
| B2 | `hooks/scripts/*.sh` 파일명 | `safety-careful.sh`, `safety-freeze.sh`, `event-review-trigger.sh` (boilerplates와 동일명) | `safety-careful.reference.sh` 등 `.reference.sh` 접미어로 역할 자기설명 | 재설치 시 자동 반영 — `settings.local.json`에서 `hooks/scripts/X.sh`를 직접 참조하는 사용자는 **settings.local.json 수동 병합** |
| B3 | `validate-system.sh` 에이전트 하드코딩 | 7곳에 에이전트 이름 박힘 (`for agent_name in developer qa-engineer` 등) | `agents.yaml` 파싱 기반 동적 검증 (bash `grep -E '^  [a-z-]+:$'` 또는 `yq`) | 재설치 시 자동 반영 — `yq` 의존 회피를 위해 bash grep 파싱 선택 시 별도 의존성 없음 |

v4.0 추가 **non-breaking** 변경은 §3에 정리.

---

## 3. Prioritized Backlog

### P0 — v4.0 릴리스 블로커 (5건)

현재 상태에서 `validate-system.sh`가 drift를 잡지 못하거나, 사용자 설치가 부분 실패하거나, 레포 자신이 CLAUDE.md·SSOT 원칙을 위반하는 항목.

#### P0-1. `agents/pm.md` 누락 — PM 에이전트 파일 시스템 불일치
- **증거**:
  - `agents.yaml:263-633` — `agents:` 블록에 `pm` 선언
  - `prompts/pm.md` (19,421B) — PM 상세 프롬프트 존재
  - `ls agents/` — 15개 파일만, `pm.md` **없음** (W1 C1)
- **해결안**: `agents/pm.md` 신규 생성 (다른 15개와 동일 패턴: frontmatter + `## Template` + `## Boundary`). `validate-system.sh`에 "agents.yaml 선언 에이전트와 `agents/*.md` 파일 매칭" 검증 추가.
- **임팩트**: `--team` 설치 후 PM 서브에이전트 스폰 가능성 복원. 현재는 validate 통과하더라도 런타임에 PM 스폰 실패 가능.
- **담당 컴포넌트**: agents/, scripts/validate-system.sh
- **breaking**: no

#### P0-2. `validate-system.sh` 자기 모순 제거 (`## v3.0 Template` 잔재)
- **증거**:
  - `validate-system.sh:43` — `grep -q "## v3.0 Template" "$agent"` — 에이전트 파일에 v3.0 헤더 강제
  - `validate-system.sh:2, :20, :99, :412, :416` — 같은 스크립트가 `v3.2` canonical을 검증 (W1 H5)
- **해결안**: `validate-system.sh:43`의 기대 헤더를 `## Template`(버전 중립)로 교체 + 15개 `agents/*.md`의 `## v3.0 Template` 헤더도 일괄 `## Template`로 rename. 스크립트 내부 버전 문자열을 `EXPECTED_VERSION="$(yq '.version' agents.yaml)"` 또는 `grep -E '^version:' agents.yaml` 파싱으로 집중.
- **임팩트**: 향후 버전 bump 시 validate가 자기 모순을 자동 감지. drift 축 1개 영구 제거.
- **담당 컴포넌트**: scripts/validate-system.sh, agents/*.md (15 파일)
- **breaking**: no

#### P0-3. `.claude/hooks/` byte-identical 복제본 제거
- **증거**:
  - `.claude/hooks/audit-agent.sh` (2456B) `diff` `hooks/boilerplates/audit-agent.sh` (2456B) → **완전 동일**
  - `.claude/hooks/guard-agent.sh` (8218B) `diff` `hooks/boilerplates/guard-agent.sh` (8218B) → **완전 동일** (W2 Group 4)
- **해결안**: `.claude/settings.local.json`의 hook command를 `bash hooks/boilerplates/audit-agent.sh`로 직접 지정, `.claude/hooks/` 디렉토리 삭제. CLAUDE.md:51의 "this repo's own active hooks" 서술은 유지하되 경로만 `hooks/boilerplates/`로 갱신.
- **임팩트**: boilerplate 업그레이드 시 `.claude/hooks/` 수동 sync 불필요. "업그레이드 시 잊기 쉬운 duplication" 교과서 사례 제거. 레포가 자기 SSOT 원칙 준수.
- **담당 컴포넌트**: .claude/hooks/ (삭제), .claude/settings.local.json
- **breaking**: no

#### P0-4. `validate-system.sh` 에이전트 이름 하드코딩 → agents.yaml 파싱 (B3)
- **증거**:
  - `validate-system.sh:74` — `for agent_name in developer qa-engineer`
  - `validate-system.sh:82` — `for agent_name in security-reviewer performance-reviewer test-coverage-reviewer code-reviewer`
  - `validate-system.sh:217` — `REVIEWER_PROMPTS=(... "qa")` (pm 누락, qa 단축명)
  - `validate-system.sh:237` — 6개 이름 skip 리스트 하드코딩 (W3 V2)
- **해결안**: agent 이름 리스트를 `agents.yaml`의 `agents:` 블록에서 동적 추출 (`grep -E '^  [a-z-]+:$' agents.yaml | sed 's/^  //;s/:$//'`). `pm.md` 포함 16개 자동 검증.
- **임팩트**: 에이전트 추가/삭제 시 스크립트 수정 불필요. drift 재생산 엔진 제거.
- **담당 컴포넌트**: scripts/validate-system.sh
- **breaking**: yes (B3) — 단, `yq` 대신 bash grep으로 구현하면 외부 의존성 없음

#### P0-5. `prompts/qa.md` → `prompts/qa-engineer.md` rename (B1)
- **증거**:
  - `agents.yaml` 및 `agents/qa-engineer.md:2` — `name: qa-engineer` (SSOT)
  - `prompts/qa.md` — 단축명, 다른 15개는 모두 정식명 사용
  - `validate-system.sh:217`이 단축명을 expected로 박아 drift 정당화 (W1 H2)
- **해결안**: `prompts/qa.md` → `prompts/qa-engineer.md` rename + `agents/qa-engineer.md:33` 경로 참조 수정 + `validate-system.sh:217` 배열 원소 업데이트 + `prompts/qa.md` 참조하는 문서 전수 일괄 교체 (grep-replace).
- **임팩트**: 에이전트 이름 = 프롬프트 파일명 규약 복원. 단 한 예외가 규약 전체를 무너뜨리고 있었음.
- **담당 컴포넌트**: prompts/, agents/qa-engineer.md, scripts/validate-system.sh, docs/
- **breaking**: yes (B1) — 외부 설치본에 영향, migration note 필요

---

### P1 — v4.0 필수 (9건)

coherence 부채가 v4.0 이후 즉시 재발생하는 항목. SSOT 위반이거나 영향 반경 3+ 파일.

#### P1-1. 버전 숫자 canonical 통일 (3.2 유지 + 문서 버전 분리)
- **증거**: `agents.yaml:4` `"3.2"` canonical ↔ `README.md:1` `v3.3` ↔ `QUICKSTART.md:3/:38/:129/:201` `v3.0` ↔ skills 4개 `(v3.0)` 레이블 ↔ docs/28:373 `(v3.3)`. 총 15+ 위치, 3개 값 혼재 (W1 H1/H3/H4/M5/M6/M7, W3 V1) — Decision Log 1 참조
- **해결안**: (1) `agents.yaml:4` canonical 유지 `version: "3.2"`. (2) README.md:1 제목에서 버전 제거하거나 별도 `doc_version` 필드로 분리 (시스템 버전과 문서 버전 축 분리). (3) QUICKSTART `v3.0 기능` 문구는 버전 제거하여 drift surface 영구 삭제. (4) skills 4개의 `(v3.0)` 프리셋 레이블 제거. (5) docs/28:373 내부 `(v3.3)` 레이블 제거. (6) validate-system.sh 출력 메시지의 `v3.2` 하드코딩을 agents.yaml 파싱으로 전환 (P0-2와 묶어 실행).
- **임팩트**: 버전 bump 시 수정 지점 15+ → 1. "이 레포는 몇 버전인가" 질문이 agents.yaml 단 1줄로 답변됨.
- **담당 컴포넌트**: README.md, QUICKSTART.md, skills/{spec,check-spec,analyze,check-code}/, docs/28-*, scripts/validate-system.sh
- **breaking**: no

#### P1-2. 프리셋 정의 6-스킬 중복 제거
- **증거**: `CLAUDE.md:58-61` 전역 정의 ↔ `skills/README.md:77-92` ↔ `README.md:404-422` ↔ `docs/14-preset-system.md` ↔ 6 스킬의 `## ~~ 프리셋 (v3.0)` 섹션 (analyze/spec/check-spec/check-code/qa-test/qa-e2e) ↔ 각 스킬 개별 옵션 조합 매트릭스. qa-test/qa-e2e는 depth 라벨마저 다름(minimal/basic/standard/full) (W3 V6, W2 Group 6)
- **해결안**: CLAUDE.md:58-61을 2축 체계 canonical로 지정. 각 스킬 SKILL.md 상단의 "~~ 프리셋" 섹션을 "2축 체계 정의: [CLAUDE.md#pdarr--preset-system](../../CLAUDE.md)" 링크 1줄로 대체 + 스킬 고유 정보(시간/산출물/Phase 매핑)만 남김. qa-test/qa-e2e 난이도 라벨은 depth 축과 매핑 테이블 추가.
- **임팩트**: 프리셋 체계 변경 시 수정 지점 9 → 1. `/dispatch` 라우팅 판단에 description만으로 충분.
- **담당 컴포넌트**: skills/{analyze,spec,check-spec,check-code,qa-test,qa-e2e}/, skills/README.md, README.md
- **breaking**: no

#### P1-3. 에이전트 목록 canonical 통일 (also flagged by W1 C1)
- **증거**: `agents.yaml:263-633` ↔ `agents.yaml:730 agent_count: 16` ↔ `README.md:378-400` 테이블 ↔ `README.md:19` `9+7=16` 요약 ↔ `validate-system.sh` 7건 하드코딩 (W3 V2)
- **해결안**: P0-4와 묶어 실행. README.md:378-400 테이블은 "에이전트 상세는 agents.yaml 참고" 링크로 대체하거나, CI 훅으로 agents.yaml에서 자동 생성. README.md:19 요약은 agents.yaml:730 `agent_count`를 참조.
- **임팩트**: 에이전트 추가 시 수정 지점 6 → 1 (agents.yaml만).
- **담당 컴포넌트**: README.md, scripts/validate-system.sh (P0-4와 중복)
- **breaking**: yes (P0-4 B3에 편입)

#### P1-4. 스킬 목록 canonical 통일
- **증거**: `skills/README.md:31-74` (5 테이블, 17 스킬) ↔ `README.md:34` `17개 Custom Skills` ↔ `CLAUDE.md:57` `/dispatch → /prd → ... → /stage` (9 스킬) ↔ `CLAUDE.md:70` `dispatch, flow, ...` (8 스킬). 실제 `ls skills/` = 18 디렉토리 (README.md:34 "17"은 drift) (W3 V3, W1 L2)
- **해결안**: `skills/README.md:31-74` canonical 지정. README.md:34는 "18개 Custom Skills" 수정 후 `skills/README.md#스킬-목록` 링크. CLAUDE.md:57, :70의 스킬 나열은 "전체 목록: skills/README.md" 링크. `validate-system.sh`에 "skills/*/SKILL.md 디렉토리 개수 + frontmatter 검증" 카테고리 추가.
- **임팩트**: 스킬 추가 시 수정 지점 4+ → 1. validate가 스킬 drift를 자동 감지.
- **담당 컴포넌트**: README.md, CLAUDE.md, scripts/validate-system.sh, skills/README.md
- **breaking**: no

#### P1-5. `hooks/scripts/*.sh` 역할 명시 rename (B2)
- **증거**: `hooks/boilerplates/`와 `hooks/scripts/`에 동일명 파일이 공존 — `safety-careful.sh`, `safety-freeze.sh`. `scripts/`는 v3.2 레퍼런스 구현(NightOps 경로 하드코딩), `boilerplates/`는 배포용 템플릿. CLAUDE.md:45 "Hooks directory has TWO meanings" 경고가 필요한 것은 파일명만 봐서는 구별 불가능하기 때문 (W2 Group 2)
- **해결안**: `hooks/scripts/safety-careful.sh` → `safety-careful.reference.sh`, `safety-freeze.sh` → `safety-freeze.reference.sh`, `event-review-trigger.sh` → `event-review-trigger.reference.sh`. `scripts/install-hooks.sh`, `scripts/validate-system.sh:309` 경로 패턴 동반 업데이트. CLAUDE.md:45-52 서술은 단순화.
- **임팩트**: 파일명만으로 역할 구별. 새 hook 추가 시 어느 디렉토리에 놓을지 판단 비용 감소. hooks/README.md 설명 테이블 분량 축소.
- **담당 컴포넌트**: hooks/scripts/, scripts/install-hooks.sh, scripts/validate-system.sh, hooks/README.md, CLAUDE.md
- **breaking**: yes (B2)

#### P1-6. Complexity Tier 임계값 drift 해소
- **증거**: `.claude/rules/subagent-strategy.md:17-22` — Trivial ≤2 files/≤20 lines, Simple ≤4/≤100, Medium ≤8, Complex >8. `skills/dispatch/SKILL.md:55-58` — Trivial 1-2줄, Simple "단일 파일", Medium "2-5개 파일", Complex "6개+" (**임계값 불일치**) (W3 V8)
- **해결안**: `.claude/rules/subagent-strategy.md:17-22` canonical 지정. `skills/dispatch/SKILL.md:55-58`을 subagent-strategy 표 그대로 인용 또는 "기준: `.claude/rules/subagent-strategy.md#tiered-dispatch` 참조"로 대체. `docs/33-subagent-efficiency.md:182-193`도 동일 링크화.
- **임팩트**: 동일 복잡도 판정 기준. 사용자가 `/dispatch`를 이해할 때 두 곳을 비교하며 혼동할 필요 없음.
- **담당 컴포넌트**: skills/dispatch/SKILL.md, docs/33-subagent-efficiency.md, .claude/rules/subagent-strategy.md
- **breaking**: no

#### P1-7. 테스트 피라미드 3층 description 재작성 (test / qa-test / qa-e2e)
- **증거**: 3 스킬의 description에서 "QA", "테스트", "수행" 키워드 겹침. `/dispatch` 라우팅 판단 시 description만으로 구별 어려움 (W2 Group 1)
- **해결안**: description 재작성 — `test: "TDD Red 단계. 구현 전 테스트 케이스 작성. 실행 없음."` / `qa-test: "단위·통합 레벨 QA 자동 실행. 변경 파일 대상."` / `qa-e2e: "비즈니스 로직 + 데이터 정합성 E2E 검증. Playwright/DB 통합."` (이미 qa-e2e는 명확, 나머지 2개만 업데이트)
- **임팩트**: `/dispatch`가 description만 읽어도 테스트 피라미드 층 판단 가능.
- **담당 컴포넌트**: skills/{test,qa-test}/SKILL.md
- **breaking**: no

#### P1-8. analyze / spec / check-spec description 재작성
- **증거**: 3 스킬 description에 "3단계 프리셋(quick/standard/thorough) + --team" 문구 반복 (W2 Group 6)
- **해결안**: 공통 preset 문구를 description에서 제거. PDARR 축 위치만 명시:
  - analyze → `"PDARR pre-spec. 코드베이스 영향 분석 + 실행 전략 추천. 코드 작성 없음."`
  - spec → `"PDARR author. 기술 명세서 작성. docs/spec/[module]/ 생성."`
  - check-spec → `"PDARR post-spec. docs/spec/ 문서의 규칙·코드베이스 일관성 검증."`
  - preset 2축은 SKILL.md 본문 상단 링크로 이관 (P1-2와 묶음).
- **임팩트**: preset 체계 변경 시 3 스킬 description 불변. 책임 경계가 description에서 명시적으로 PDARR 축으로 위치함.
- **담당 컴포넌트**: skills/{analyze,spec,check-spec}/SKILL.md
- **breaking**: no

#### P1-9. reflect / complete / organize-docs 책임 명시
- **증거**: 3 스킬 모두 `docs/complete/` 또는 `history/complete` 건드림. description에서 역할 구별 흐림 (W2 Group 8)
- **해결안**: description 재작성 — `reflect: "Self-Critique + Memory 학습. docs/complete/는 사이드이펙트."` / `complete: "세션 완료 통폐합. docs/complete/ 업데이트 주 책임."` / `organize-docs: "사후 catch-up. Git diff 기반 누락 탐지·보강."`
- **임팩트**: 세션 종료 단계에서 `/dispatch`가 3 스킬 중 어느 것을 부를지 description만으로 판단.
- **담당 컴포넌트**: skills/{reflect,complete,organize-docs}/SKILL.md
- **breaking**: no

---

### P2 — v4.0 nice-to-have (10건)

드리프트 재생산 속도는 느리나 개선 시 문서 IA와 UX가 향상되는 항목.

#### P2-1. Cross-reference broken links 일괄 수정 (37건)
- **증거**: `docs/15-26*` 내부 23건 `+1` 오프셋 (W1 M4), README.md:288-299 두 번째 테이블 12건 `-1` 오프셋 (W1 M1), docs/10:343 `08-workflows.md` → `11-workflow-commands.md` (W1 M2), docs/00:381 `13-handoff-failure-recovery.md` → `13-handoff-and-failure.md` (W1 M3)
- **해결안**: `grep -rn "14-token-pricing" docs/` 식 일괄 검색 후 +1/-1 오프셋 대응 sed 스크립트로 일괄 교체. 장기적으로는 docs/ 인덱스(README 또는 docs/README.md)를 SSOT로 두고 개별 파일 간 직접 링크 대신 인덱스 경유 패턴으로 전환 (후속 과제).
- **담당 컴포넌트**: docs/ 9개 파일, README.md
- **breaking**: no

#### P2-2. `check-code` CUSTOMIZE 블록 stack 예시 분리
- **증거**: `skills/check-code/SKILL.md` 9개 CUSTOMIZE 블록 내부에 PHP/React/Python stack 예시 반복 (W2 Group 5)
- **해결안**: `skills/check-code/references/stack-examples.md` 신규 파일에 stack별 예시 분리. SKILL.md는 `<!-- INCLUDE: references/stack-examples.md#syntax -->` 규칙 또는 "stack별 예시: references/stack-examples.md" 링크로 축소.
- **담당 컴포넌트**: skills/check-code/
- **breaking**: no

#### P2-3. 모델 라우팅 canonical 통일
- **증거**: `.claude/rules/subagent-strategy.md:62-68` 간결 표, `docs/33-subagent-efficiency.md:341-349` 상세 표, `skills/workflow/SKILL.md:154-164` 에이전트별 매핑, `agents.yaml:7-35` routing_rules (W3 V5)
- **해결안**: `agents.yaml:7-35` canonical 지정. 나머지 3곳은 "상세: agents.yaml#model_routing" 링크. `token_budget.model_costs`도 동일 참조 패턴.
- **담당 컴포넌트**: .claude/rules/subagent-strategy.md, docs/33, skills/workflow/SKILL.md
- **breaking**: no

#### P2-4. PDARR 흐름 정의 canonical 통일
- **증거**: `CLAUDE.md:57` canonical 후보, README.md:305-323/:588-593, skills/workflow/SKILL.md:90-118, skills/dispatch/SKILL.md:146-172 중복 (W3 V4, W2 Group 12)
- **해결안**: CLAUDE.md:57 canonical. README와 skills의 ASCII 흐름도는 보존(사용자 가치 있음)하되 "상세 순차: CLAUDE.md#Flow 참조" 주석 추가. skills/workflow의 Phase 매핑은 CLAUDE.md 순차와 매핑 테이블 추가.
- **담당 컴포넌트**: README.md, skills/workflow/SKILL.md, skills/dispatch/SKILL.md
- **breaking**: no

#### P2-5. Hooks 3중 네이밍 canonical + 제목 수정
- **증거**: `CLAUDE.md:47` 제목 `Hooks directory has TWO meanings` 그러나 bullet 3개 (a/b/c). hooks/README.md:145-171은 `.claude/hooks/` 미언급 (W3 V7)
- **해결안**: CLAUDE.md:47 제목 `TWO` → `THREE`. hooks/README.md:145-171을 "3중 네이밍 구별은 CLAUDE.md#hooks-directory-has-three-meanings 참조" 링크로 대체. P1-5 rename 적용 후에는 구별 자체가 파일명으로 자기설명되므로 설명 분량 축소.
- **담당 컴포넌트**: CLAUDE.md, hooks/README.md
- **breaking**: no

#### P2-6. 서브에이전트 14k 오버헤드 canonical 통일
- **증거**: `docs/33-subagent-efficiency.md:21-32` 분해 표 canonical 후보. `.claude/rules/subagent-strategy.md:9`와 `CLAUDE.md:76`에 동일 상수 요약 (W3 V9)
- **해결안**: docs/33:21-32를 canonical로 지정. 나머지 2곳은 "상세 분해: docs/33#고정-오버헤드-구조" 링크.
- **담당 컴포넌트**: .claude/rules/subagent-strategy.md, CLAUDE.md
- **breaking**: no

#### P2-7. 설치 스크립트 옵션 canonical 통일
- **증거**: README.md:85-132, skills/README.md:9-25, hooks/README.md:19-45, CLAUDE.md:28-30에 옵션 반복 선언 (W3 V10)
- **해결안**: 각 스크립트의 `--help` 출력을 canonical로 지정. 문서는 "상세: `bash scripts/install-hooks.sh --help`" 링크. CI 훅으로 `--help` 출력을 문서에 include하는 옵션도 고려 (long-term).
- **담당 컴포넌트**: README.md, skills/README.md, hooks/README.md, CLAUDE.md
- **breaking**: no

#### P2-8. docs 15/28/33 (토큰) + 29/33 (하네스) cross-link 강화
- **증거**: 토큰 관련 15/28/33, 하네스 관련 29/33에 겹치는 멘탈 모델 존재 (W2 Group 10)
- **해결안**: 29와 33 상단에 `> 관련: 29-harness-engineering.md §X` 주석. 15/28은 33의 부록 섹션으로 forward 링크. 파일 merge는 히스토리 손실이라 기각.
- **담당 컴포넌트**: docs/15, docs/28, docs/29, docs/33
- **breaking**: no

#### P2-9. architect ↔ code-reviewer description 경계 명시
- **증거**: `agents/code-reviewer.md` description에 "아키텍처" 단어 포함 → `architect`와 구조 리뷰 영역 겹침 (W2 Group 11)
- **해결안**: code-reviewer description의 "아키텍처" → "기구현된 코드의 아키텍처 준수 여부"로 좁힘. 시간축 구별 명시 (pre vs post).
- **담당 컴포넌트**: agents/code-reviewer.md
- **breaking**: no

#### P2-10. PDARR 3축 매핑 테이블 (agents.yaml / workflow / dispatch)
- **증거**: agents.yaml의 quick-fix/standard/thorough ↔ dispatch의 Trivial/Simple/Medium/Complex 이름·기준 불일치 (W2 Group 12)
- **해결안**: `.claude/rules/subagent-strategy.md` 또는 `docs/29-harness-engineering.md`에 "복잡도 × 예산 × 실행 3축 매핑" 테이블 추가. 예: `Trivial → quick-fix → 메인 직접`, `Complex → thorough → Scout→Workers`.
- **담당 컴포넌트**: .claude/rules/subagent-strategy.md 또는 docs/29
- **breaking**: no

---

## 4. Migration Scenarios

### Scenario A: "v3.3을 설치만 한 사용자" (CUSTOMIZE 미수정)

```bash
bash scripts/install-skills.sh --force
bash scripts/install-hooks.sh --force
```

- B1 (qa.md → qa-engineer.md): 재설치로 자동 반영.
- B2 (hooks/scripts `.reference.sh` 접미어): 재설치로 자동 반영. `.claude/settings.local.json`이 `hooks/scripts/X.sh`를 직접 참조하지 않는 한 추가 조치 불필요.
- B3 (validate-system.sh 동적 파싱): 재설치로 자동 반영.
- P0-3 (.claude/hooks 제거): 사용자 설치본에 영향 없음 — 이 레포 자체에만 적용.

### Scenario B: "CUSTOMIZE 블록을 수정해 쓰던 사용자"

1. 재설치 전 `diff -r ~/.claude/ <backup>` 로 수정 사항 백업.
2. `bash scripts/install-skills.sh --force` 실행.
3. 충돌 지점 확인 (재설치 후 덮어써진 CUSTOMIZE 블록):
   - `skills/{spec,check-spec,analyze,check-code}/SKILL.md` — 프리셋 레이블 `(v3.0)` 제거 및 description 재작성 (P1-2/P1-8)
   - `skills/{test,qa-test,qa-e2e}/SKILL.md` — description 재작성 (P1-7)
   - `skills/{reflect,complete,organize-docs}/SKILL.md` — description 재작성 (P1-9)
4. 백업과 머지 — CUSTOMIZE 블록 내부 사용자 커스터마이징은 보존, description과 프리셋 상단 섹션은 새 구조로 교체.
5. `prompts/qa.md`를 직접 편집해 사용하던 경우 → **CUSTOMIZE 재작성 필요**. `prompts/qa-engineer.md` 신규 파일에 수정 사항 이식.
6. `.claude/settings.local.json`에서 `hooks/scripts/safety-careful.sh` 등을 직접 참조하던 경우 → `.reference.sh` 접미어로 수정 (수동 병합).

---

## 5. Success Criteria (v4.0 완료 판정, all must pass)

- [ ] **`validate-system.sh` 0 errors / 0 warnings** — 현재 `## v3.0 Template` 체크와 `3.2` canonical 공존 상태가 해소되어 자기 모순 없음
- [ ] **모든 P0 백로그 close** — P0-1~P0-5 전수 해결 (pm.md 생성, validate 모순 제거, .claude/hooks 제거, validate 동적 파싱, qa rename)
- [ ] **버전 주장이 repo 전체에서 단 1곳에 선언** — `agents.yaml:4` canonical, 다른 모든 곳은 링크·동적 참조·제거 (P1-1)
- [ ] **CLAUDE.md · README · QUICKSTART · 각 skill 본문이 PDARR 흐름을 동일 기술** — canonical은 CLAUDE.md:57, 나머지는 링크 또는 매핑 테이블 (P2-4)
- [ ] **hooks 네이밍 3중 → 파일명 자기설명** — `.reference.sh` 접미어 rename 완료 (P1-5), CLAUDE.md 제목 `THREE meanings` 수정 (P2-5)
- [ ] **`.claude/rules/*` 주장 ↔ 실제 hook 동작 일치** — `.claude/hooks/` 제거로 drift 축 제거 (P0-3), Complexity Tier 임계값 통일 (P1-6)

---

## 6. Decision Log

### Decision 1: 버전 canonical — "3.2 유지 + 문서 버전 축 분리" vs "3.3으로 bump"

- **상황**: W1 H1 분석은 "README v3.3 기능 서술이 실재하므로 agents.yaml을 3.3으로 올리는 편이 README 본문 재작성을 피해 drift surface 최소화"라고 주장. W3 V1은 "agents.yaml:4 canonical 유지 + README는 별개 문서 버전으로 분리"라고 주장. 두 제안 모두 Coherence를 복원하나 방향이 다름.
- **Tie-breaker 사다리 적용**:
  1. SSOT 생성? — W3 쪽이 시스템 버전과 문서 버전을 명시적 2축으로 분리하여 더 강한 SSOT. W1은 여전히 "README 제목 = 시스템 버전" 혼용 구조 유지.
  2. Drift surface 축소? — W3 쪽이 향후 문서 개정(메이저 기능 없는 문서 업데이트)이 시스템 버전 bump를 강요하지 않도록 분리하여 drift 재발 억제. W1 접근은 즉시 surface는 줄이나 다음 문서 개정에서 같은 문제 재발.
  3. 세 축 동기화? — W3 쪽이 규칙(agents.yaml)·문서(README doc_version)·코드(validate-system.sh 동적 파싱)를 각자 고유 축으로 명시.
- **채택**: W3 방향 — **agents.yaml:4 `version: "3.2"` 유지** + README.md:1에서 버전 제거(또는 별도 `doc_version` 축 신설). QUICKSTART 전체의 `v3.0 기능` 문구는 버전 제거로 drift 영구 삭제. skills `(v3.0)` 레이블 전수 제거. validate-system.sh의 `v3.2` 하드코딩 5곳은 agents.yaml 파싱으로 대체.
- **근거**: Coherence-first 사다리 1·2·3단계 모두 W3 승. "작은 변경" 기준(4단계)으로는 W1이 다소 유리하나 이는 1-3단계가 동률일 때만 적용.

### Decision 2: `hooks/scripts/` 역할 명시 방식 — ".reference.sh 접미어" vs "hooks/templates + hooks/references 2-tier 재편"

- **상황**: W2 Group 2는 `.reference.sh` 접미어를 제안, W2 Group 3은 `hooks/templates/ + hooks/references/` 디렉토리 rename을 후보로 제시. 두 접근 모두 3중 네이밍 문제 해결.
- **Tie-breaker 사다리 적용**:
  1. SSOT 생성? — 둘 다 파일명 자기설명 = 동률.
  2. Drift surface 축소? — 접미어 방식이 boilerplate/scripts 2 디렉토리 구조 유지하며 파일명만 변경 → 외부 문서·설치본의 "hooks/boilerplates" 인용을 보존. 2-tier 재편은 모든 경로 인용을 갱신해야 함.
  3. 세 축 동기화? — 둘 다 충족.
  4. YAGNI → 작은 변경. 접미어 방식 승 (3개 파일 rename vs 디렉토리 rename + 모든 인용 갱신).
- **채택**: `.reference.sh` 접미어. `boilerplate`가 이미 업계 표준 용어고 README/문서 인용이 많아 디렉토리 rename은 ROI 부족.

### Decision 3: `validate-system.sh` 동적 파싱 구현 — "`yq` 의존" vs "bash grep 파싱"

- **상황**: W3 V2는 yq 기반 파싱을 기본으로 제안하되 "대안: bash grep 파싱"을 각주로 언급. breaking 여부가 달라짐.
- **Tie-breaker 사다리 적용**:
  1. SSOT 생성? — 둘 다 agents.yaml을 canonical로 승격하여 동률.
  2. Drift surface 축소? — 둘 다 동률.
  3. 세 축 동기화? — 둘 다 동률.
  4. YAGNI → 작은 변경. bash grep 방식이 외부 의존 0개 추가 (현재 validate-system.sh는 bash + grep + find + 표준 유닉스 도구만 사용).
- **채택**: **bash grep 파싱** — `grep -E '^  [a-z-]+:$' agents.yaml | sed 's/^  //;s/:$//'`. yq 설치 부담 회피. Breaking 영향 최소.

---

**다음 단계**: 각 P0 항목을 개별 구현 세션(writing-plans → executing-plans)으로 분할하여 순차 실행. P0 완료 후 P1 병렬 착수 검토.
