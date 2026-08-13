# 하네스 엔지니어링 가이드

> 검증 기준일: 2026-08-13

**하네스 엔지니어링(Harness Engineering)**은 Claude Code의 instruction, permission, tool, hook, Skill, subagent, context, logging 경계를 조합해 실행 품질과 피해 범위를 관리하는 방식입니다.

하네스는 중요한 제어 계층이지만 유일한 안전장치는 아닙니다. 애플리케이션 권한 검증, 안전한 코드, 테스트, secret 관리, network와 storage 정책을 대체하지 않습니다.

공식 기준:

- Settings: https://code.claude.com/docs/en/settings
- Model configuration: https://code.claude.com/docs/en/model-config
- Subagents: https://code.claude.com/docs/en/sub-agents
- Fast mode: https://code.claude.com/docs/en/fast-mode

관련 문서:

- [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
- [비용 및 토큰 최적화](15-token-pricing-optimization.md)
- [컨텍스트와 상태 관리](19-context-window-internals.md)
- [스킬 경량화](27-skill-lightweight-guide.md)
- [서브에이전트 효율성](33-subagent-efficiency.md)

---

## 1. 하네스 구성 요소

| 계층 | 제어 대상 | 대표 수단 |
|---|---|---|
| Settings | 모델, effort, context, MCP, 기능 옵션 | settings files, CLI flags |
| Permission and sandbox | 읽기·쓰기·실행 범위 | permission rules, sandbox, managed policy |
| Hooks | 도구 실행 전후의 결정론적 차단·검증 | PreToolUse, PostToolUse, Stop |
| Instructions | 프로젝트 목적, 제약, 검증 명령 | CLAUDE.md, `.claude/rules/` |
| Skills | 반복 작업의 bounded procedure | `.claude/skills/*/SKILL.md` |
| Subagents | 격리된 context와 역할별 model/tool | `.claude/agents/*.md` |
| Runtime boundary | response, state, log, cost, checkpoint | adapter, sanitizer, telemetry |

하나의 장문 `CLAUDE.md`에 모든 계층의 책임을 넣지 않습니다.

---

## 2. Settings 우선순위

현재 공식 우선순위는 높은 순서대로 다음과 같습니다.

```text
Managed settings
→ command line arguments
→ local settings
→ project settings
→ user settings
```

| Scope | 용도 | 예시 |
|---|---|---|
| Managed | 조직 정책, 사용자가 우회하면 안 되는 제한 | model allowlist, managed-only hooks, MCP policy |
| CLI | 현재 세션의 임시 override | `--model`, `--settings` |
| Local | 개인·프로젝트 로컬 override, Git 제외 | `.claude/settings.local.json` |
| Project | 팀이 공유하는 프로젝트 설정 | `.claude/settings.json` |
| User | 모든 프로젝트의 개인 기본값 | `~/.claude/settings.json` |

기존 문서의 `managed가 최저 우선순위` 설명은 잘못됐습니다. Managed settings는 일부 명시적 예외를 제외하면 다른 scope가 덮어쓸 수 없습니다.

배열, permission, 일부 보안 설정에는 merge 또는 restrictive-only 예외가 있으므로 단순히 파일 한 개만 보고 활성 값을 판단하지 않습니다.

확인:

```text
/status
claude doctor
```

`/status`의 setting sources와 `claude doctor`의 validation 결과를 함께 봅니다.

---

## 3. Settings 설계 원칙

### 팀 공유 설정

프로젝트 설정에는 팀이 실제로 공유해야 하는 것만 둡니다.

```json
{
  "autoCompactEnabled": true,
  "fastModePerSessionOptIn": true
}
```

- 모델을 프로젝트 설정에 고정하기 전에 조직 allowlist와 공급자를 확인합니다.
- `autoCompactWindow`는 실제 session 계측 없이 고정하지 않습니다.
- 개인 token 최적화와 credentials는 shared settings에 넣지 않습니다.
- shell에서 export된 secret을 settings JSON에 복사하지 않습니다.

### 조직 정책

다음처럼 우회되면 안 되는 항목은 managed tier에서 관리합니다.

- 사용 가능한 model과 provider
- 허용 또는 차단 MCP
- managed-only hooks와 permissions
- marketplace와 plugin supply chain
- login organization과 version floor/ceiling

Project 설정을 조직 보안 정책의 대체재로 사용하지 않습니다.

---

## 4. Permission과 sandbox

하네스의 첫 질문은 “모델이 잘 생각하는가”가 아니라 “실수했을 때 어디까지 피해가 가는가”입니다.

| 작업 | 기본 경계 |
|---|---|
| 파일 읽기 | workspace와 명시된 reference만 |
| 파일 쓰기 | 현재 repository 또는 승인된 worktree |
| Git | status와 diff는 허용, push·reset·force는 별도 승인 |
| Network | 현재 공식 문서나 명시 API가 필요할 때만 |
| Package install | lockfile과 공급망 영향 검토 |
| Production | 기본 금지, 별도 승인과 rollback 필요 |
| Secret | model input, log, fixture, issue에 직접 복사 금지 |

Permission prompt를 agent 간 메시지로 승인하지 않습니다. 사용자 또는 정책 계층만 권한을 부여합니다.

---

## 5. Hooks — 결정론적 제어

Hooks는 모델 instruction보다 다음 작업에 적합합니다.

- destructive command 차단
- protected file write 차단
- edit 후 syntax, lint, test 실행
- secret-like output 검사
- completion receipt 생성

### Hook가 하면 안 되는 일

- prompt 전체를 audit log에 저장
- Bash command 원문을 무조건 영구 저장
- tool result와 environment 전체를 직렬화
- secret을 마스킹 없이 외부 observability로 전송
- 실패 시 모든 작업을 무조건 차단하는 불명확한 regex

### 감사 로그 Allowlist

권장 event:

```json
{
  "timestamp": "<iso-time>",
  "session_hash": "<non-reversible-id>",
  "event": "PostToolUse",
  "tool": "Bash",
  "decision": "pass",
  "exit_code": 0,
  "duration_ms": 0
}
```

기본적으로 기록하지 않는 항목:

```text
prompt
full command
stdout/stderr 원문
tool result payload
environment variables
API response
thinking 또는 encrypted state
```

조사 목적으로 command 일부가 필요하면 별도 opt-in, 짧은 retention, redaction, 접근 감사를 둡니다.

실전 Hook은 이 저장소의 `hooks/boilerplates/`와 테스트를 기준으로 사용합니다.

---

## 6. CLAUDE.md — 안정적인 프로젝트 계약

CLAUDE.md에는 반복 가치가 높은 불변식만 둡니다.

```markdown
# 프로젝트 운영 규칙

## 기술 경계
- PHP 7.2와 MySQL 5.7 호환을 유지한다.
- 사용자 입력은 prepared statement, parameter binding 또는 프로젝트의 검증된 안전 helper를 사용한다.
- 사용자 입력을 SQL 문자열에 직접 보간하지 않는다.

## 검증
- PHP 수정 후 `php -l`을 실행한다.
- 동작 변경은 관련 regression test를 실행한다.
- 실행하지 못한 검증은 완료 메시지에 남긴다.

## 승인
- production, migration, remote push, destructive git은 사용자 승인이 필요하다.
```

기존의 `SQL 파라미터 바인딩 사용하지 않음` 예시는 제거합니다. 레거시 호환을 이유로 input validation과 query safety를 포기하지 않습니다.

### 문서 크기

5KB 같은 값은 보편적인 공식 한도가 아니라 로컬 운영 목표입니다.

다음 기준으로 줄입니다.

- 매 턴 필요한 규칙인가.
- 코드와 test로 강제할 수 있는가.
- path-scoped rule로 옮길 수 있는가.
- 특정 작업에서만 필요한 내용은 Skill reference로 옮길 수 있는가.

---

## 7. Skills — 호출될 때만 로드되는 절차

Skill 본체는 다음 계약에 집중합니다.

```text
trigger
objective
input and output
allowed tools
write scope
budget and max turns
validation
stop and failure policy
```

긴 이론, 연구 근거, 여러 예시는 `references/`로 분리합니다.

Skill 승격 조건:

- 같은 workflow가 반복된다.
- input/output이 안정됐다.
- 실패를 잡는 validator가 있다.
- authority와 stop condition을 정의할 수 있다.
- 일회성 prompt보다 유지 가치가 높다.

---

## 8. Subagents — context와 비용을 함께 격리

서브에이전트는 메인 context를 보호하고 역할별 권한을 제한할 수 있습니다.

```yaml
---
name: code-explorer
description: 코드 검색과 호출 경로 조사
model: haiku
effort: low
maxTurns: 8
tools: Read, Grep, Glob
---
```

```yaml
---
name: security-reviewer
description: 보안 또는 데이터 경계 변경 검토
model: opus
effort: high
maxTurns: 12
tools: Read, Grep, Glob
---
```

현재 model 해석 우선순위:

```text
CLAUDE_CODE_SUBAGENT_MODEL
→ 호출별 model
→ agent frontmatter
→ session model 상속
```

전역 `CLAUDE_CODE_SUBAGENT_MODEL`은 역할별 설정을 덮어쓰므로 조직 정책 또는 명확한 비용 실험이 있을 때만 사용합니다.

### 사용 조건

- 독립적인 read-heavy task
- 메인 context를 오염시키는 대량 output
- tool과 permission을 별도로 제한할 가치
- 역할별 model과 effort의 측정 가능한 이득

단순 수정에 reviewer를 여러 명 붙이지 않습니다. agent 수가 늘면 startup, file read, coordination, merge 검증 비용도 늘어납니다.

---

## 9. Context와 compaction

```json
{
  "autoCompactEnabled": true
}
```

- 모델별 기본 auto-compact window를 먼저 사용합니다.
- `autoCompactWindow`는 측정 후 조정합니다.
- compaction summary를 source of truth로 쓰지 않습니다.
- 중요 사실은 source와 validator가 있는 semantic checkpoint에 둡니다.
- subagent transcript와 main transcript의 retention을 별도로 검토합니다.

자세한 상태 경계는 [컨텍스트 윈도우와 상태 관리](19-context-window-internals.md)를 봅니다.

---

## 10. LLM API Response와 Provider State

Claude API 또는 다른 LLM API를 직접 호출하는 프로젝트는 response 전체를 한 객체로 보존하지 않습니다.

| Plane | 예 | 기본 정책 |
|---|---|---|
| Public output | 사용자에게 보이는 text, validated JSON | 업무 보존 정책 |
| Business state | evidence-linked fact, decision, open question | portable 가능 |
| Tool receipt | sanitized tool call/result summary | 최소 기간 |
| Telemetry | model, token, cache, latency, status | content-free |
| Provider state | thinking, redacted thinking, signature, opaque state | drop 또는 격리·짧은 TTL |

금지:

```text
logger.info(JSON.stringify(response))
```

권장 telemetry:

```json
{
  "request_id": "<id>",
  "model": "<model>",
  "input_tokens": 0,
  "cache_creation_input_tokens": 0,
  "cache_read_input_tokens": 0,
  "output_tokens": 0,
  "latency_ms": 0,
  "status": "ok"
}
```

- model switch 시 이전 thinking과 redacted thinking을 제거합니다.
- opaque signature를 파싱하지 않습니다.
- external transcript의 provider state를 replay하지 않습니다.
- provider state와 semantic checkpoint를 같은 database field에 저장하지 않습니다.

---

## 11. 사용 시나리오

### 개인 개발

```text
user settings
- fastModePerSessionOptIn: true
- autoCompactEnabled: true

project CLAUDE.md
- stack, 검증, 승인 경계

subagent
- 반복되는 역할만 model/effort/maxTurns 지정
```

### 팀 프로젝트

```text
managed
- model/MCP/plugin/security policy

project
- 공유 hook, test command, path rule

local
- 개인 UI와 실험 설정, secret 제외
```

### NightOps와 자동화

```text
- Fast Mode 기본 비활성화
- max turns, cost, retry, escalation 상한
- destructive tool deny
- content-free audit event
- failure receipt와 human handoff
```

무인 작업에서 permission bypass를 비용 최적화로 취급하지 않습니다.

---

## 12. 검증

```bash
bash scripts/validate-system.sh
bash scripts/selfcheck-token-waste.sh /path/to/project
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
```

수동 확인:

- [ ] `/status`에서 실제 settings source를 확인했다.
- [ ] `claude doctor`에 invalid setting이 없다.
- [ ] managed policy를 user/project가 우회한다고 설명하지 않는다.
- [ ] Hook log에 raw prompt, command, output, secret이 없다.
- [ ] SQL 예시는 parameter binding 또는 안전 helper를 사용한다.
- [ ] Skill과 CLAUDE.md의 책임이 중복되지 않는다.
- [ ] 서브에이전트 model 하향 후 품질을 측정했다.
- [ ] compaction summary와 business checkpoint를 분리했다.
- [ ] provider response 전체를 직렬화하지 않는다.

---

## 13. 안티패턴

| 안티패턴 | 문제 | 대안 |
|---|---|---|
| managed가 최저 우선순위라고 설명 | 조직 정책 우회 오해 | current precedence 적용 |
| 모든 작업에 동일 model과 high effort | 비용과 latency 증가 | 역할·위험 기반 routing |
| full command audit log | secret과 개인정보 유출 | metadata allowlist |
| SQL binding 금지 | injection 위험 | 안전한 query contract |
| CLAUDE.md에 모든 workflow 포함 | 매 턴 context 팽창 | Skill과 reference 분리 |
| agent를 항상 병렬 실행 | 중복 탐색과 merge 비용 | 독립 가치가 있을 때만 |
| raw API response 저장 | thinking과 secret 노출 | data-plane 분리 |
| compaction을 영구 memory로 사용 | provenance와 사실 손실 | semantic checkpoint |

---

## 다음 단계

1. [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
2. [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
3. [스킬 경량화](27-skill-lightweight-guide.md)
4. [서브에이전트 효율성](33-subagent-efficiency.md)
5. [컨텍스트와 상태 관리](19-context-window-internals.md)
