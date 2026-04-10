# Multi-Agent Team System v3.0 Changelog

**Release Date**: 2026-03-19
**Upgraded From**: v2.0 (2026-02-07)

---

## Summary

v3.0 is a system-wide consistency and resilience upgrade. It standardizes every agent prompt with a shared 5-section template, introduces formal handoff contracts between agents, adds a system-wide failure recovery policy, enhances three key agents (QA, Designer, Publisher), and upgrades the PM orchestrator with tiebreaker logic, intelligent model routing, and adaptive workflow selection.

---

## Loop 1: Prompt Template Standardization

**All 16 agent prompts rewritten to 5-section template.**

### Template Structure (5-section-v1)

Every prompt now contains exactly these sections in order:

| # | Section | Purpose |
|---|---------|---------|
| 1 | `## Opening` | Agent identity, persona, one-line role statement |
| 2 | `## Working Mode` | Step-by-step execution process |
| 3 | `## Focus On` | Domain-specific priorities and checklist |
| 4 | `## Quality Checks` | Self-verification gates before output |
| 5 | `## Return` | Output format specification |
| 6 | `## Boundary` | Hard limits — what this agent must NOT do |

### Agents Standardized (16 total)

**Core Agents (9):**
- `pm.md` — Project Manager / Orchestrator
- `architect.md` — System Architect
- `developer.md` — Full-Stack Developer
- `qa.md` — QA Engineer
- `dba.md` — Database Administrator
- `designer.md` — UI/UX Designer
- `publisher.md` — Publisher / DevOps
- `documenter.md` — Technical Writer
- `explorer.md` — Code Explorer

**Specialist Reviewers (7):**
- `security-reviewer.md` — Security Sentinel
- `performance-reviewer.md` — Performance Prophet
- `test-coverage-reviewer.md` — Test Guardian
- `accessibility-reviewer.md` — Access Advocate
- `ux-reviewer.md` — UX Harmonizer
- `api-reviewer.md` — API Arbiter
- `code-reviewer.md` — Code Reviewer

---

## Loop 2: Handoff Protocol

**Formal agent-to-agent handoff contracts.**

### New File: `context/handoff-protocol.md`

Defines the standard handoff packet format passed between agents:

```
[HANDOFF from <sender> to <receiver>]
scope: <task scope>
changed_files: [list]
decisions: [key decisions made]
blockers: [issues for next agent]
approval_status: approved | pending | rejected
```

### agents.yaml Handoff Fields

Every agent entry in `agents.yaml` now has a `handoff:` block:

```yaml
handoff:
  accepts: [upstream-agent-list]
  produces: [output-artifact-list]
  requires_from_upstream: [required-field-list]
```

**Coverage**: All 16 agents (pm, architect, developer, qa-engineer, dba, designer, publisher, documenter, explorer, and all 6 specialist reviewers) have handoff blocks.

### Handoff Validation

- `handoff_protocol.validation: true` in agents.yaml
- On validation failure: `retry_once_then_escalate`
- PM verifies all required fields are present before forwarding

---

## Loop 3: Failure Recovery Policy

**System-wide failure handling, replacing ad hoc error management.**

### New File: `workflows/failure-policy.yaml`

Defines failure responses for every failure type:

| Failure Type | Strategy | Max Retries |
|-------------|----------|-------------|
| `agent_timeout` | retry with backoff | 2 |
| `agent_error` | retry once, then skip or escalate | 2 |
| `handoff_validation_fail` | retry once, then escalate | 1 |
| `blocker_found` | escalate to PM, pause pipeline | — |
| `quality_gate_fail` | return to previous agent | 1 |
| `all_agents_fail` | halt and report | — |

### Workflow `on_fail` Integration

Every workflow yaml now references `failure_policy:` at the top level and each phase has an `on_fail:` field specifying the failure action (retry, escalate, skip, halt).

**Workflows updated:**
- `standard.yaml`
- `quick-fix.yaml`
- `refactor.yaml`
- `feature-flag.yaml`
- `migration.yaml`
- `code-review.yaml`

---

## Loop 4: Agent Enhancements

**Three core agents significantly expanded.**

### QA Engineer (`qa.md`) — 330 lines

New capabilities:
- **5-layer test strategy**: unit, integration, E2E, performance, security
- **Risk-based prioritization**: test effort proportional to change risk
- **Regression impact analysis**: identifies tests broken by changes
- **Structured bug report format**: severity, steps, expected vs actual, environment
- **Coverage thresholds**: unit 80%, integration 60%, E2E critical paths
- **Test pyramid enforcement**: ratio validation (unit:integration:e2e = 70:20:10)

### UI/UX Designer (`designer.md`) — 364 lines

New capabilities:
- **Design token system**: spacing, color, typography, shadow scales
- **Component variant matrix**: state × variant documentation
- **Mobile-first responsive spec**: breakpoint-by-breakpoint layout
- **Interaction design**: hover, focus, active, disabled, loading states
- **Handoff spec format**: pixel-precise implementation guide for developers
- **Dark mode consideration**: explicit light/dark token mapping

### Publisher/DevOps (`publisher.md`) — 404 lines

New capabilities:
- **Pre-deploy checklist**: 12-point gate (tests, lint, build, secrets, rollback plan)
- **Docker deployment protocol**: build → test image → push → rolling restart
- **Rollback procedure**: automated trigger conditions and steps
- **Health check verification**: post-deploy endpoint validation
- **Resource monitoring**: mem_limit, disk usage, container restart count
- **Zero-downtime deploy**: `--no-deps` pattern with health gate before traffic shift

---

## Loop 5: PM Intelligence Upgrades

**PM orchestrator gains three new intelligence layers.**

### Tiebreaker Protocol

When specialist reviewers disagree (e.g., Security says BLOCK, Performance says APPROVE):

```
Priority order (highest wins):
1. Security Reviewer (blocks deployment)
2. Performance Reviewer (if >200ms regression)
3. QA Engineer (if test coverage drops)
4. Architect (structural concerns)
5. Other reviewers
```

- Documented in `pm.md` under `## Tiebreaker Protocol`
- PM records tiebreaker decision and rationale in final report

### Model Routing (v1.0)

Intelligent model selection based on task characteristics:

| Condition | Agent | Model |
|-----------|-------|-------|
| `cross_service_architecture` | architect | opus |
| `critical_security_issue` | security-reviewer | opus |
| `large_change_set` (10+ files) | code-reviewer | opus |
| `db_migration` | dba | opus |
| `simple_scan` | explorer | haiku |
| `trivial_fix` | all | haiku |
| default | all | sonnet |

- Configured in `agents.yaml` under `model_routing:`
- PM applies routing rules at task dispatch time

### Adaptive Workflow Selection

PM no longer defaults to `standard` workflow. Selection logic:

| Trigger | Workflow |
|---------|----------|
| Single bug fix, no schema change | `quick-fix` |
| DB schema change required | `migration` |
| Code restructuring, no new features | `refactor` |
| New feature with feature flag | `feature-flag` |
| PR review requested | `code-review` |
| Multi-service feature | `standard` |

- Documented in `pm.md` under `## Adaptive Workflow Selection`

### Explorer Integration

PM now dispatches Explorer as Phase 0 before architecture or implementation:

```
Phase 0 (Explorer, haiku):
  → codebase scan
  → impact report
  → feeds Architect / Developer with scope context
```

- Explorer always runs with `model: haiku` for cost efficiency
- Output: `analysis-report.md` passed via handoff packet

---

## Loop 6: Meta-Orchestration and System Validation

**System-level consistency tooling.**

### Validation Script: `scripts/validate-system.sh`

A read-only bash script that verifies system integrity:

| Check | What It Verifies |
|-------|-----------------|
| Prompt sections | All 16 prompts have all 6 required sections |
| Agent definitions | All `.md` files have `## v3.0 Template` and `## Boundary` |
| agents.yaml version | `version: "3.0"` present |
| Handoff protocol | `handoff_protocol:` block present |
| Model routing | `model_routing:` block present |
| Handoff coverage | Count of agents with `handoff:` blocks |
| Workflow failure policy | All workflows reference `failure_policy:` |
| failure-policy.yaml | File exists |
| handoff-protocol.md | File exists |
| PM prompt sections | All 5 PM-specific sections present |

**Usage**: `bash ~/.claude/team/scripts/validate-system.sh`
**Exit code**: 0 = PASS, N = number of errors

### system_meta Block in agents.yaml

```yaml
system_meta:
  version: "3.0"
  agent_count: 16
  template_version: "5-section-v1"
  handoff_protocol: "v1.0"
  failure_policy: "v1.0"
  model_routing: "v1.0"
  last_validated: "2026-03-19"
  upgrade_from: "2.0"
```

---

## File Inventory (v3.0)

### New Files

| File | Description |
|------|-------------|
| `context/handoff-protocol.md` | Agent handoff packet standard |
| `workflows/failure-policy.yaml` | System failure recovery rules |
| `scripts/validate-system.sh` | System integrity validator |
| `docs/v3-changelog.md` | This file |

### Modified Files

| File | Changes |
|------|---------|
| `agents.yaml` | version 3.0, handoff blocks, model_routing, handoff_protocol, system_meta |
| `prompts/*.md` (16 files) | 5-section template applied |
| `workflows/*.yaml` (6 files) | failure_policy + on_fail per phase |
| `~/.claude/CLAUDE.md` | Version bump, new features documented |

---

## Migration Notes (v2.0 → v3.0)

- All 16 prompts are backward-compatible (same agent behavior, richer structure)
- Handoff validation is enforced but has retry-once fallback (non-breaking)
- Model routing is additive (default remains sonnet, no existing flows break)
- failure-policy.yaml is referenced by workflows but does not change external behavior unless a failure occurs
- Explorer as Phase 0 adds a new phase to standard/refactor workflows (slight overhead, higher output quality)

---

## Upgrade Checklist (v3.0)

- [x] Loop 1: 16 prompts standardized with 5-section template
- [x] Loop 2: Handoff protocol + agents.yaml handoff fields
- [x] Loop 3: failure-policy.yaml + all workflows have on_fail
- [x] Loop 4: QA (330 lines), Designer (364 lines), Publisher (404 lines) enhanced
- [x] Loop 5: PM tiebreaker + model routing + adaptive workflow + Explorer integration
- [x] Loop 6: validate-system.sh + v3-changelog.md + system_meta + CLAUDE.md update

---

# v3.2 Changelog — gstack 병합 업그레이드

**Release Date**: 2026-03-25
**Upgraded From**: v3.0/v3.1 (2026-03-23)
**Reference**: [gstack](https://github.com/garrytan/gstack) (Garry Tan's AI Workflow Platform)

---

## Summary

v3.2 is a "실체화(materialization)" upgrade. Previously, YAML declarations (parallel execution, circuit breakers, event hooks) relied entirely on PM prompt comprehension. v3.2 bridges the gap between declaration and enforcement by registering actual shell scripts as Claude Code hooks, introducing file-based state management, and adding structured autonomy controls.

Key theme: **"Fill the empty hooks field"** — settings.json hooks were completely empty despite 5 hook modules existing in harness-kit.

---

## Changes

### 1. Completion Status Protocol (Handoff Protocol v2.0)

- `validation_status` (pass/fail/partial) deprecated → `completion_status` (4-state)
- **4 states**: DONE, DONE_WITH_CONCERNS, BLOCKED, NEEDS_CONTEXT
- **Retry 3-layer separation**:
  - Agent internal: max_attempts=2 (failure-policy.yaml)
  - Handoff level: max_retries=1 (handoff-protocol)
  - Circuit breaker: consecutive_failures=3 (agents.yaml)
- `protocol_version: "2.0"` field for consumer version detection
- Quality gate pass criteria: DONE=pass, DONE_WITH_CONCERNS=conditional, BLOCKED/NEEDS_CONTEXT=block

### 2. Safety Hooks (실체화)

Three shell scripts registered as actual Claude Code hooks in settings.json:

| Hook | Type | Script | Purpose |
|------|------|--------|---------|
| careful | PreToolUse:Bash | `safety-careful.sh` | Level 4 block (rm -rf /, DROP DATABASE, git push --force) + Level 3 warn (ALTER TABLE) |
| freeze | PreToolUse:Edit/Write | `safety-freeze.sh` | Tier 1 block (.env, /etc/) + Tier 2 warn (docker-compose.yml) |
| event-trigger | PostToolUse:Edit/Write | `event-review-trigger.sh` | File pattern → reviewer trigger logging |

- `realpath` normalization prevents path traversal bypass
- NightOps trusted context: `/home/ubuntu/nightops/`, `/home/ubuntu/scripts/` paths exempt
- Safe exceptions: node_modules, .next, dist, build, __pycache__

### 3. Autonomy Levels (5-tier)

| Level | Name | Autonomy | Enforcement |
|-------|------|----------|-------------|
| 0 | safe | Full | None |
| 1 | reversible | Auto + post-verify | PostToolUse hook |
| 2 | semi-reversible | Auto + snapshot + healthcheck | PreToolUse + PostToolUse |
| 3 | caution | User approval required | PreToolUse warn |
| 4 | forbidden | Never autonomous | PreToolUse block |

### 4. Blast-Radius Classification (4-level)

| Level | Criteria | Workflow | Model |
|-------|----------|----------|-------|
| single_file | 1 file, ≤100 lines | quick-fix | haiku |
| single_module | 2-5 files, ≤300 lines | quick-fix | sonnet |
| cross_module | 6-15 files, ≤1000 lines | standard | sonnet |
| cross_service | >15 files OR 2+ services | standard | opus |

- PM override policy: upgrade=autonomous+notify, downgrade=user-required
- Orthogonal with Diff-Aware categories (blast_radius × category matrix)

### 5. Diff-Aware Phase 0 (code-review.yaml)

New Phase 0 `diff_analysis` before Phase 1:
- `blast_radius_measure`: file count, lines, import_depth, service count
- `diff_categorize`: security/api/ui/performance/infra/tests/docs/general
- `post_processing`: dynamic condition update for downstream phases
- `reviewer_routing`: category → reviewer mapping
- `preset_override`: cross_service → auto-escalate quick→standard

### 6. Phase 5b Opus Upgrade Option

Conditional model tier upgrade for adversarial review:
- Trigger: `blast_radius == cross_service OR security_critical == true`
- Action: sonnet → opus for cross-verification
- Cost guard: token_budget limit respected, fallback to sonnet

### 7. Session Resume (File-based State Chain)

- Session directory: `~/.claude/team/context/sessions/{date}_{task_id}/`
- `session.yaml`: workflow metadata (status, phase, cost)
- `handoffs/*.yaml`: ordered handoff payloads
- `artifacts/`: agent-generated files
- TTL: completed=90d, failed=14d, abandoned=1d, running=7d
- PM resume logic: detect running sessions, load last phase, continue

### 8. Event-Driven Review trusted_contexts

NightOps paths added to event-driven-review.yaml exemption list.

### 9. validate-system.sh v3.2 (18 categories)

6 new validation categories:
- #13: Safety hook scripts existence + executable
- #14: settings.json hooks registration (≥3)
- #15: Handoff protocol v2.0 completion_status
- #16: Blast-radius + autonomy_levels in agents.yaml
- #17: Phase 0 diff_analysis in code-review.yaml
- #18: Session state schema YAML validity

---

## New Files

| File | Description |
|------|-------------|
| `hooks/scripts/safety-careful.sh` | Bash command safety gate |
| `hooks/scripts/safety-freeze.sh` | File edit protection gate |
| `hooks/scripts/event-review-trigger.sh` | Review trigger logger |
| `context/session-state-schema.yaml` | Session file format spec |

## Modified Files

| File | Changes |
|------|---------|
| `agents.yaml` | v3.2, blast_radius, autonomy_levels, completion_status_criteria |
| `context/handoff-protocol.md` | v2.0, 4-state, retry layers, session resume |
| `workflows/code-review.yaml` | Phase 0, Phase 5b opus upgrade |
| `workflows/failure-policy.yaml` | partial_success + completion_status mapping |
| `hooks/event-driven-review.yaml` | trusted_contexts |
| `prompts/pm.md` | completion_status, session resume, blast-radius override |
| `scripts/validate-system.sh` | 18 categories |
| `settings.json` | hooks field populated (3 hooks) |
| `~/.claude/CLAUDE.md` | v3.2 features |

---

## Design Decisions

1. **F (Cross-Tier Adversarial) deferred to v4.0**: Full cross-model review (Claude+Codex) is overkill. Reduced to conditional opus upgrade in Phase 5b.
2. **File-based sessions over DB**: Interactive workflows use files, NightOps uses PostgreSQL. Clear separation avoids dual-write.
3. **realpath normalization mandatory**: Security reviewer flagged path traversal via `rm -rf node_modules/../../../etc/passwd`.
4. **PM override asymmetry**: Upgrade (quick→standard) is autonomous because it's conservative. Downgrade requires user approval because it risks under-review.
5. **gstack patterns adopted**: Completion Status, Safety Hooks, Diff-Aware scoping, file-based state chains. Rejected: MANUAL TRIGGER ONLY, Preamble tiers, Supabase telemetry.

---

# v3.3 Changelog — 스킬 경량화 & 토큰 낭비 방지

**Release Date**: 2026-04-10
**Upgraded From**: v3.2 (2026-03-25)

---

## Summary

v3.3은 "비용 최적화(cost optimization)" 업그레이드입니다. 스킬 비대화로 인한 컨텍스트 낭비, Cloud AI MCP 자동 활성화로 인한 시스템 프롬프트 비대화, 설정 미비로 인한 토큰 낭비 등 실제 비용에 영향을 미치는 문제를 체계적으로 진단하고 해결하는 가이드와 도구를 추가합니다.

Key theme: **"토큰이 어디서 새는지 알고, 막아라"**

---

## Changes

### 1. 스킬 경량화 가이드 (docs/27-skill-lightweight-guide.md)

- **스킬 크기 4등급 기준**: 🟢 경량(≤5KB) / 🟡 보통(5~8KB) / 🟠 비대(8~12KB) / 🔴 과대(>12KB)
- **경량화 4대 전략**:
  - A: 본체/참조 분리 (SKILL.md + references/) — 67% 토큰 절감
  - B: 조건부 섹션 제거 (기본 모드만 본체)
  - C: 예제 최소화 (3개→1개)
  - D: 공통 참조 추출 (_shared/)
- **경량 스킬 템플릿**: 100~200줄, 3~5KB 이내 목표
- **settings.json 스킬 최적화**: `maxSkillsPerTurn`, `autoLoadSkills` 제어
- **현재 프로젝트 감사**: 17개 스킬 중 3개 과대(>12KB), 4개 비대(8~12KB) 식별

### 2. 토큰 낭비 자가진단 가이드 (docs/28-token-waste-selfcheck.md)

- **7대 토큰 낭비 요소** 체계화:
  1. Cloud AI MCP 자동 활성화 (매 턴 4,500~7,000 토큰)
  2. Deferred Tools 목록 주입 (매 턴 1,500~2,000 토큰)
  3. 스킬 비대화 (호출 시 3,000~5,000 토큰)
  4. CLAUDE.md 비대화 (매 턴 1,500~3,000 토큰)
  5. 메모리 과다 주입 (매 턴 1,000~2,000 토큰)
  6. Fast Mode 미차단 (비용 6x)
  7. 서브에이전트 모델 미지정 (비용 40% 추가)
- **Cloud AI MCP 비활성화 가이드**: Canva, Figma, Gmail, Google Calendar, Magic Patterns
- **시나리오별 최적화 프로필 3종**: Pro 사용자, Max 사용자, 자동화/NightOps
- **settings.json 위험 설정 체크리스트**
- **정기 점검 일정**: 세션/주/월/업데이트 후

### 3. 토큰 낭비 자동 진단 스크립트 (scripts/selfcheck-token-waste.sh)

7항목 자동 점검 스크립트:

| # | 점검 항목 | 판정 기준 |
|---|----------|----------|
| 1 | Fast Mode 차단 | 환경변수 + settings.json 이중 차단 |
| 2 | 서브에이전트 모델 | SUBAGENT_MODEL 환경변수/설정 존재 |
| 3 | Cloud AI MCP | 활성화된 Cloud AI MCP 서버 수 |
| 4 | 스킬 크기 | 12KB 초과 SKILL.md 존재 여부 |
| 5 | CLAUDE.md 크기 | 글로벌 2KB / 프로젝트 5KB 초과 |
| 6 | 메모리 파일 | 파일 수 및 합산 크기 |
| 7 | settings.json 위험 설정 | maxSkillsPerTurn, memory.maxFiles 등 |

출력: PASS/WARN/FAIL 요약, 예상 턴당 낭비 토큰 수, 권장 조치

### 4. docs 넘버링 충돌 해소

- `15-codex-plugin.md` → `15a-codex-plugin.md` 리네임
- `15-token-pricing-optimization.md` 유지
- 참조 문서 3곳(00-setup-checklist, 09-recommended-plugins, README) 업데이트

---

## New Files

| File | Description |
|------|-------------|
| `docs/27-skill-lightweight-guide.md` | 스킬 경량화 가이드 |
| `docs/28-token-waste-selfcheck.md` | 토큰 낭비 자가진단 가이드 |
| `scripts/selfcheck-token-waste.sh` | 토큰 낭비 자동 진단 스크립트 |

## Modified Files

| File | Changes |
|------|---------|
| `README.md` | v3.3 버전 범프, v3.3 신규 항목 4건 추가 |
| `docs/README.md` | 문서 인덱스에 #27, #28 추가, 15a 리네임 반영 |
| `docs/v3-changelog.md` | v3.3 섹션 추가 |
| `docs/15-codex-plugin.md` → `docs/15a-codex-plugin.md` | 넘버링 충돌 해소 |
| `docs/00-setup-checklist.md` | 15a 참조 업데이트 |
| `docs/09-recommended-plugins.md` | 15a 참조 업데이트 |

## Renamed Files

| Before | After | Reason |
|--------|-------|--------|
| `docs/15-codex-plugin.md` | `docs/15a-codex-plugin.md` | 15-token-pricing-optimization.md와 번호 충돌 |

---

## Design Decisions

1. **스킬 분리 전략은 references/ 사용**: `.claude/skills/스킬명/references/` 패턴은 Claude Code가 기본 지원하므로 추가 설정 불필요.
2. **Cloud AI MCP 비활성화는 settings.json disabled 방식**: MCP 서버를 삭제하면 향후 사용 시 재설정이 필요하므로 `disabled: true`로 토글 방식 채택.
3. **진단 스크립트는 jq 없이도 동작**: python3 fallback으로 jq 미설치 환경 지원.
4. **시나리오별 프로필 3종**: Pro(비용 민감)/Max(균형)/NightOps(최소 비용) — 사용자가 자신의 플랜에 맞는 설정을 즉시 복사 적용 가능.

### 5. 하네스 엔지니어링 가이드 (docs/29-harness-engineering.md)

- **5컴포넌트 통합 아키텍처**: settings.json, Hooks, CLAUDE.md, Skills, Memory의 상호 관계와 데이터 플로우
- **Hook 패턴 라이브러리 4종**: 위험 명령 차단, 파일 보호, 구문 검증, 감사 로그
- **시나리오별 하네스 설계 3종**: 개인 개발자, 팀 프로젝트, 자동화/NightOps
- **settings.json vs settings.local.json 분리 원칙**: 팀 공유(hooks, 권한) vs 개인(토큰 최적화)
- **경로 스코프 규칙**: `.claude/rules/*.md`로 CLAUDE.md 비대화 방지
- **하네스 진화 4단계**: 시작 → 성장 → 팀 → 자동화

### 6. Advisor Strategy 가이드 (docs/30-advisor-strategy.md)

- **Anthropic 2026-04-09 발표 Beta**: executor+advisor 모델 협업 패턴
- **벤치마크**: Sonnet+Opus Advisor = Sonnet 대비 +2.7pp, 11.9% 비용 절감
- **API 구현**: Python/TypeScript 코드 예제, 도구 파라미터, 비용 구조
- **Best Practices**: 작업당 2~3회 호출, 시스템 프롬프트 가이드, 출력 토큰 절감
- **PDARR 워크플로우 연계**: Plan→advisor, Act→advisor(막힐 때), Review→advisor(검증)
- **고급 기능**: 프롬프트 캐싱, multi-turn, effort 설정 조합

### 7. settings.local.json 개인 설정 분리

- docs/28 토큰 낭비 자가진단에 `settings.local.json` 권장 위치 안내 추가
- 시나리오별 프로필을 `settings.local.json` 기준으로 업데이트
- frecto_web 프로젝트에 토큰 최적화 `settings.local.json` 실제 적용

### 추가 New Files

| File | Description |
|------|-------------|
| `docs/29-harness-engineering.md` | 하네스 엔지니어링 종합 가이드 |
| `docs/30-advisor-strategy.md` | Advisor Strategy 가이드 |

### 추가 Modified Files

| File | Changes |
|------|---------|
| `docs/28-token-waste-selfcheck.md` | settings.local.json 권장 안내, 시나리오별 프로필 업데이트 |
| `docs/README.md` | #29, #30 문서 인덱스 추가 |
| `README.md` | v3.3 하네스/Advisor 항목 추가 |
