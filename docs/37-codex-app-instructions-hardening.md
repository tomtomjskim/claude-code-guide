# Codex App 지침과 Hook Hardening 운영 메모

이 문서는 Claude Code 가이드가 Codex App/CLI 운영 패턴을 참조할 때 필요한 대응 관계를 정리한다. 목적은 Claude Code의 hook/skill/team-system 운영 지식을 Codex App 환경에도 안전하게 적용하는 것이다.

## 1. 대응 관계

| Claude Code | Codex App/CLI |
|---|---|
| `CLAUDE.md` | `AGENTS.md` |
| `.claude/rules/*.md` | repo `AGENTS.md`, `AGENTS.override.md`, 또는 Codex skill |
| `.claude/agents/*.md` | `.codex/agents/*.toml` |
| `.claude/settings.local.json` hooks | `.codex/hooks.json` 또는 config hooks |
| `skills/*/SKILL.md` | Codex skill/plugin skill |
| guard-agent/safety hooks | PreToolUse/PostToolUse command hooks |

모든 정책을 전역 memory에 넣지 않는다. 판단 규칙은 지침에 두고, 기계적으로 판별 가능한 차단은 hook으로 분리한다.

## 2. 전역 지침 최소화

Codex 전역 `AGENTS.md`에는 다음만 둔다.

- TOM 응답 언어와 불확실성 표기
- 작업 discipline
- secret/destructive 안전 규칙
- request mode routing
- review output format
- final response footer 예외
- 특수 subagent output contract

프로젝트별 PHP/DB/UI 규칙, 특정 repo 명령, 테스트 절차는 전역이 아니라 repo `AGENTS.md`에 둔다.

## 3. Custom Agent 적용 범위

Codex custom agent는 Claude Code subagent와 달리 `.toml` 파일에 `developer_instructions`를 담는다.

권장 공통 섹션:

```text
## Applicability
## Tool Preflight
## Working Mode
## Return
## Boundary
```

특히 Frecto 같은 특정 프로젝트 agent는 적용 범위를 명확히 해야 한다.

```text
이 지침은 Frecto 저장소 또는 사용자가 Frecto 컨텍스트를 명시한 경우에만 적용한다.
Frecto 외 작업에서는 전역/프로젝트 AGENTS.md와 해당 코드베이스의 로컬 패턴을 우선한다.
```

도구 전제도 검증해야 한다.

```text
Serena/db-mcp가 실제로 사용 가능한지 먼저 확인한다.
도구가 없으면 rg, rg --files, 제한적 파일 읽기로 대체한다.
사용 불가 도구와 fallback은 tool_limitations에 기록한다.
```

## 4. `codex-rescue` 중복 생성 금지

`codex@openai-codex` 플러그인이 이미 `codex:codex-rescue`를 제공하는 경우, 같은 이름의 local `.codex/agents/codex-rescue.toml`을 만들지 않는다.

이유:

- 공식 agent는 `codex-companion` thin forwarder다.
- 같은 이름 local agent는 라우팅 충돌이나 shadowing을 만들 수 있다.
- output 누락 보정은 전역 `AGENTS.md`의 output contract로 처리하는 편이 안전하다.

별도 wrapper가 필요하면 다른 이름을 쓴다.

- `codex-rescue-output-auditor`
- `codex-result-surfacer`

## 5. Trusted Scope 단계 축소

Codex trusted project는 넓게 잡을수록 새 파일/외부 자료가 쉽게 trusted context로 들어온다.

권장 단계:

| 단계 | 조치 |
|---|---|
| Stage A | 현재 trust scope와 workflow 의존성 관찰 |
| Stage B | home directory 전체 trust 제거 |
| Stage C | parent dev directory trust 제거, explicit repo만 유지 |

실제 적용 사례:

- `/Users/jeongsik` trust 제거
- `/Users/jeongsik/dev`와 explicit repo trust는 유지

Stage C는 새 repo 작업 friction이 커질 수 있으므로 별도 승인 후 진행한다.

## 6. Hooks Pilot 패턴

Claude Code의 `safety-careful`, `safety-freeze`, `guard-agent` 사고방식을 Codex hook에 옮길 때는 한 프로젝트에서 먼저 pilot 한다.

`frecto_web` pilot 예:

| Guard | 차단 범위 |
|---|---|
| destructive file/git | `rm -rf`, `git reset --hard`, `git clean -fd` 계열 |
| secret read | `.env`, `auth.json`, private key 계열 직접 읽기 |
| prod runtime | prod DB marker + `php/mysql/node/composer/npm` runtime command |

읽기 전용 조사는 허용한다.

```bash
rg -n prod_burst CLAUDE.md
```

런타임 실행은 차단한다.

```bash
FRECTO_SERVER_CONFIG=prod php cron/foo.php
```

## 7. 검증 기준

Hook JSON:

```bash
python3 -m json.tool .codex/hooks.json
```

차단/허용 시뮬레이션:

```bash
COMMAND='rm -rf tmp/foo' <hook-condition>
COMMAND='sed -n 1,5p .env' <hook-condition>
COMMAND='FRECTO_SERVER_CONFIG=prod php cron/foo.php' <hook-condition>
COMMAND='rg -n prod_burst CLAUDE.md' <hook-condition>
```

기대:

- destructive/secret/prod runtime은 exit 2
- read-only search는 exit 0

## 8. Claude Guide 반영 기준

이 문서는 Claude Code 자체의 설치 스크립트나 `agents.yaml` 시스템 버전을 변경하지 않는다. Codex App hardening은 문서 릴리즈 축에서 관리하며, 팀 시스템 canonical version(`agents.yaml:4`)과 별개다.

관련 변경이 실제 hook boilerplate로 승격될 때만 `hooks/boilerplates/`와 `scripts/install-hooks.sh`를 수정한다.
