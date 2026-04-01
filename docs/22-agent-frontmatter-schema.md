# Agent Frontmatter 완전 스키마

## 개요

`~/.claude/agents/` 디렉토리의 `.md` 파일은 YAML frontmatter로 에이전트 동작을 정밀하게 제어합니다. 이 문서는 v2.1.88 소스 분석으로 확인된 16개 필드 전체를 정리합니다.

---

## 1. 전체 필드 레퍼런스

### 1.1 model

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | `"inherit"` |
| 허용값 | `"inherit"` / `"sonnet"` / `"opus"` / `"haiku"` / 전체 모델 ID |

사용할 LLM 모델을 지정합니다. `"inherit"`는 부모(호출자) 에이전트의 모델을 그대로 사용합니다. 전체 모델 ID를 명시하면 정확한 버전 고정이 가능합니다.

```yaml
model: claude-sonnet-4-6              # 전체 ID 명시 (버전 고정)
model: opus                           # 별칭 (최신 opus 계열)
model: inherit                        # 부모 모델 상속 (기본)
```

### 1.2 effort

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | `"medium"` |
| 허용값 | `"low"` / `"medium"` / `"high"` / `"max"` |

extended thinking 예산과 처리 깊이를 제어합니다. `"max"`는 가능한 최대 thinking 토큰을 사용하며 비용이 크게 증가합니다.

| 값 | thinking 토큰 예산 | 적합한 작업 |
|----|-----------------|------------|
| `"low"` | 0 (disabled) | 간단한 파일 읽기, 포맷팅 |
| `"medium"` | ~4K | 일반 구현, 코드 리뷰 |
| `"high"` | ~16K | 복잡한 설계, 디버깅 |
| `"max"` | 모델 최대값 | 심층 분석, 보안 감사 |

### 1.3 permissionMode

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | `"default"` |
| 허용값 | `"bubble"` / `"plan"` / `"default"` / `"auto"` / `"bypass"` |

에이전트의 도구 실행 권한 확인 방식을 지정합니다.

| 값 | 동작 |
|----|------|
| `"bubble"` | 권한 확인을 부모 에이전트로 버블업 (서브에이전트 기본) |
| `"plan"` | 실행 전 계획을 보여주고 일괄 승인 요청 |
| `"default"` | 위험도에 따라 선택적으로 확인 요청 |
| `"auto"` | 모든 도구 자동 승인 (위험도 낮은 도구) |
| `"bypass"` | 모든 권한 확인 건너뜀 (CI/자동화 전용, 주의 필요) |

### 1.4 maxTurns

| 항목 | 내용 |
|------|------|
| 타입 | `number` |
| 기본값 | — (제한 없음) |

에이전트가 실행할 수 있는 최대 대화 턴 수입니다. 무한 루프나 과도한 API 비용을 방지하기 위한 안전장치입니다. 초과 시 에이전트는 현재 상태를 반환하고 종료합니다.

```yaml
maxTurns: 10    # 탐색 전용 에이전트 (빠른 완료 보장)
maxTurns: 50    # 복잡한 구현 에이전트
maxTurns: 100   # 장기 자율 작업 에이전트
```

### 1.5 isolation

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | — (격리 없음) |
| 허용값 | `"worktree"` / `"remote"` |

에이전트 작업 환경의 격리 수준을 지정합니다.

| 값 | 동작 |
|----|------|
| `"worktree"` | git worktree를 생성하여 격리된 파일시스템에서 작업. 메인 브랜치를 건드리지 않음 |
| `"remote"` | 원격 실행 환경 사용 (미래 기능, 현재 실험적) |

### 1.6 background

| 항목 | 내용 |
|------|------|
| 타입 | `boolean` |
| 기본값 | `false` |

`true` 설정 시 에이전트가 백그라운드에서 비동기로 실행됩니다. 호출자는 완료를 기다리지 않고 즉시 다음 작업을 진행합니다. 병렬 에이전트 실행 패턴에 사용됩니다.

### 1.7 omitClaudeMd

| 항목 | 내용 |
|------|------|
| 타입 | `boolean` |
| 기본값 | `false` |

`true` 설정 시 이 에이전트의 컨텍스트에 CLAUDE.md 파일을 주입하지 않습니다. 비용 절감이나 노이즈 제거가 필요한 특수 목적 에이전트에서 사용합니다.

> 주의: CLAUDE.md의 중요한 규칙이 누락되므로 신중하게 사용해야 합니다.

### 1.8 memory

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | — (메모리 미사용) |
| 허용값 | `"user"` / `"project"` / `"local"` |

에이전트가 접근할 메모리 범위를 지정합니다.

| 값 | 접근 범위 |
|----|----------|
| `"user"` | `~/.claude/` 하위 전체 메모리 |
| `"project"` | 현재 프로젝트의 `.claude/` 메모리만 |
| `"local"` | 로컬 전용 (`.claude/local/`) 메모리 |

### 1.9 tools

| 항목 | 내용 |
|------|------|
| 타입 | `string[]` |
| 기본값 | `[]` (전체 허용) |

에이전트에게 허용할 도구 목록을 명시적으로 지정합니다. 빈 배열이면 전체 도구가 허용됩니다. 최소 권한 원칙을 적용하려면 필요한 도구만 나열합니다.

```yaml
tools:
  - Read
  - Grep
  - Glob
  - mcp__serena__find_symbol
  - mcp__serena__get_symbols_overview
```

### 1.10 disallowedTools

| 항목 | 내용 |
|------|------|
| 타입 | `string[]` |
| 기본값 | `[]` |

에이전트에게 차단할 도구 목록입니다. `tools` 화이트리스트와 달리 블랙리스트 방식입니다. 대부분은 허용하되 특정 도구만 차단할 때 유용합니다.

```yaml
disallowedTools:
  - Bash        # 탐색 전용 에이전트에서 실행 차단
  - Write       # 읽기 전용 에이전트에서 쓰기 차단
  - Edit
```

### 1.11 mcpServers

| 항목 | 내용 |
|------|------|
| 타입 | `object[]` |
| 기본값 | `[]` |

이 에이전트 전용으로 추가할 MCP 서버 목록입니다. 글로벌 settings.json에 정의된 서버 외에 에이전트별로 특수한 MCP 서버를 추가할 때 사용합니다.

```yaml
mcpServers:
  - name: my-db-mcp
    command: uvx
    args: ["--from", "my-db-mcp", "db-server"]
    env:
      DB_URL: "postgresql://..."
```

### 1.12 hooks

| 항목 | 내용 |
|------|------|
| 타입 | `object` |
| 기본값 | `{}` |

에이전트 실행 전후에 트리거되는 훅을 정의합니다. 글로벌 hooks와 별도로 에이전트별 훅을 설정할 수 있습니다.

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'Bash invoked' >> /tmp/agent-audit.log"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "git add -A && git diff --cached > /tmp/last-write.diff"
```

### 1.13 skills

| 항목 | 내용 |
|------|------|
| 타입 | `string[]` |
| 기본값 | `[]` |

이 에이전트에 주입할 스킬 파일 목록입니다. 스킬은 `~/.claude/skills/` 또는 `.claude/skills/`에 위치한 마크다운 파일입니다.

```yaml
skills:
  - tdd-workflow
  - security-checklist
  - code-review-template
```

### 1.14 initialPrompt

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | — |

에이전트가 시작될 때 자동으로 실행할 초기 프롬프트입니다. 에이전트 초기화, 환경 설정 확인, 컨텍스트 수집 등 반복적인 시작 작업을 자동화할 때 사용합니다.

```yaml
initialPrompt: |
  먼저 프로젝트 구조를 파악하고, 현재 git 상태를 확인한 뒤,
  작업 시작 준비가 되었음을 알려주세요.
```

### 1.15 criticalSystemReminder_EXPERIMENTAL

| 항목 | 내용 |
|------|------|
| 타입 | `string` |
| 기본값 | — |
| 상태 | **실험적** — 향후 변경 가능 |

매 턴마다 시스템 프롬프트 끝에 반복 주입되는 중요 지시문입니다. 에이전트가 특정 규칙을 절대 잊지 않도록 강제할 때 사용합니다. 실험적 기능이므로 안정적인 환경에서는 주의해서 사용하세요.

```yaml
criticalSystemReminder_EXPERIMENTAL: |
  절대로 프로덕션 DB에 직접 쓰기 작업을 수행하지 마세요.
  모든 DB 변경은 마이그레이션 스크립트로만 수행해야 합니다.
```

### 1.16 requiredMcpServers

| 항목 | 내용 |
|------|------|
| 타입 | `string[]` |
| 기본값 | `[]` |

이 에이전트 실행에 필수적인 MCP 서버 이름 목록입니다. 목록의 서버가 연결되지 않으면 에이전트 실행을 시작하지 않습니다.

```yaml
requiredMcpServers:
  - serena        # serena MCP 없이는 실행 거부
  - github-mcp    # GitHub MCP 없이는 실행 거부
```

---

## 2. 전체 필드 요약표

| 필드 | 타입 | 기본값 | 필수 |
|------|------|--------|------|
| `model` | string | `"inherit"` | 아니오 |
| `effort` | string | `"medium"` | 아니오 |
| `permissionMode` | string | `"default"` | 아니오 |
| `maxTurns` | number | 무제한 | 아니오 |
| `isolation` | string | 없음 | 아니오 |
| `background` | boolean | `false` | 아니오 |
| `omitClaudeMd` | boolean | `false` | 아니오 |
| `memory` | string | 없음 | 아니오 |
| `tools` | string[] | `[]` | 아니오 |
| `disallowedTools` | string[] | `[]` | 아니오 |
| `mcpServers` | object[] | `[]` | 아니오 |
| `hooks` | object | `{}` | 아니오 |
| `skills` | string[] | `[]` | 아니오 |
| `initialPrompt` | string | 없음 | 아니오 |
| `criticalSystemReminder_EXPERIMENTAL` | string | 없음 | 아니오 |
| `requiredMcpServers` | string[] | `[]` | 아니오 |

---

## 3. 실전 예시

### 3.1 탐색 전용 에이전트 (비용 최적화)

코드베이스 분석과 정보 수집에 특화된 에이전트입니다. 파일 쓰기와 실행을 차단하여 안전하게 탐색만 수행하며, 비용을 최소화합니다.

```yaml
---
model: haiku
effort: low
permissionMode: auto
maxTurns: 15
background: false
omitClaudeMd: false
memory: project
tools:
  - Read
  - Grep
  - Glob
  - mcp__serena__find_symbol
  - mcp__serena__get_symbols_overview
  - mcp__serena__find_referencing_symbols
  - mcp__serena__search_for_pattern
disallowedTools:
  - Bash
  - Write
  - Edit
requiredMcpServers:
  - serena
---

# Explorer Agent

코드베이스를 분석하고 정보를 수집하는 탐색 전용 에이전트입니다.
파일 수정이나 명령 실행은 절대 수행하지 않습니다.

[에이전트 프롬프트 본문]
```

**선택 이유**:
- `model: haiku` — 탐색은 고성능 모델 불필요, 비용 절감
- `effort: low` — thinking 비활성화로 응답 속도 향상
- `tools` 화이트리스트 — Read/Grep/Glob/Serena만 허용, 쓰기 계열 전체 차단
- `maxTurns: 15` — 탐색이 무한 루프에 빠지는 것을 방지
- `requiredMcpServers: [serena]` — serena 없이는 심볼 분석 불가, 조기 실패

### 3.2 보안 리뷰어 (격리 + 높은 추론)

코드 변경 사항을 심층 분석하여 보안 취약점을 찾는 에이전트입니다. 격리된 환경에서 높은 추론 품질로 분석하되, 코드 수정은 허용하지 않습니다.

```yaml
---
model: claude-opus-4-5
effort: high
permissionMode: plan
maxTurns: 30
isolation: worktree
background: false
omitClaudeMd: false
memory: user
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - mcp__serena__find_symbol
  - mcp__serena__get_symbols_overview
  - mcp__serena__find_referencing_symbols
  - mcp__serena__search_for_pattern
disallowedTools:
  - Write
  - Edit
  - mcp__serena__replace_symbol_body
  - mcp__serena__replace_content
skills:
  - security-checklist
  - owasp-top10
requiredMcpServers:
  - serena
criticalSystemReminder_EXPERIMENTAL: |
  당신은 읽기 전용 보안 감사자입니다.
  코드를 수정하지 마세요. 발견한 취약점을 보고서로 작성하세요.
---

# Security Reviewer Agent

공격자의 시각에서 코드를 검토하는 보안 리뷰어입니다.
"공격자에게 노출되면 어떻게 되는가?"를 항상 질문합니다.

[에이전트 프롬프트 본문]
```

**선택 이유**:
- `model: opus` — 보안 취약점 발견에는 최고 수준의 추론 필요
- `effort: high` — 복잡한 취약점 패턴 분석에 충분한 thinking 예산
- `isolation: worktree` — 독립된 환경에서 코드 변경 없이 분석
- `permissionMode: plan` — Bash 실행 전 계획 확인 (감사 추적)
- `disallowedTools`에 Edit/Write/replace 계열 전체 차단 — 수정 불가
- `criticalSystemReminder_EXPERIMENTAL` — 매 턴마다 읽기 전용 역할 상기
- `skills: [security-checklist, owasp-top10]` — 보안 체크리스트 항상 주입

### 3.3 자동화 워커 (비용 최소화)

NightOps나 CI/CD 파이프라인에서 반복 작업을 수행하는 에이전트입니다. 사람의 개입 없이 자율 실행되므로 비용과 안정성이 최우선입니다.

```yaml
---
model: haiku
effort: low
permissionMode: bypass
maxTurns: 50
background: true
omitClaudeMd: true
memory: project
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
disallowedTools: []
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[$(date -u +%Y-%m-%dT%H:%M:%SZ)] BASH: ${TOOL_INPUT}' >> /var/log/nightops-audit.log"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "echo '[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WRITE: ${TOOL_INPUT_PATH}' >> /var/log/nightops-audit.log"
initialPrompt: |
  환경 변수와 설정 파일을 확인하고, 오늘 날짜 기준 실행할 작업 목록을 파악하세요.
  작업 시작 전 /var/log/nightops.log에 시작 시간을 기록하세요.
---

# NightOps Worker Agent

야간 자율 운영 태스크를 수행하는 자동화 워커입니다.
사람의 개입 없이 미리 정의된 작업을 완료합니다.

[에이전트 프롬프트 본문]
```

**선택 이유**:
- `model: haiku` + `effort: low` — 반복 자동화 작업에 최저 비용 모델
- `permissionMode: bypass` — CI 환경에서 모든 확인 건너뜀 (사람 없음)
- `background: true` — 비동기 실행, 호출자 블로킹 없음
- `omitClaudeMd: true` — CLAUDE.md 로딩 오버헤드 제거 (컨텍스트 절약)
- `maxTurns: 50` — 장기 작업 허용하되 무한 루프 방지
- Hooks audit log — `bypass` 모드에서도 모든 작업 추적 보장
- `initialPrompt` — 매 실행 시 표준화된 초기화 수행

---

## 4. 필드 조합 패턴

### 4.1 비용 최적화 조합

```yaml
model: haiku
effort: low
omitClaudeMd: true
maxTurns: 10
```

### 4.2 격리 + 안전 조합

```yaml
isolation: worktree
disallowedTools:
  - Write
  - Edit
  - Bash
permissionMode: plan
criticalSystemReminder_EXPERIMENTAL: "파일을 수정하지 마세요."
```

### 4.3 자율 운영 조합

```yaml
permissionMode: bypass
background: true
maxTurns: 100
hooks:
  PreToolUse: [...]    # 감사 로그 필수
```

---

## 다음 단계

- [컨텍스트 윈도우 내부 동작](18-context-window-internals.md)
- [Settings 전체 스키마 레퍼런스](19-settings-schema-reference.md)
- [Memory 시스템 내부 동작](20-memory-system-internals.md)
- [에이전트 페르소나](05-agent-personas.md)
- [v3.0 아키텍처](12-v3-architecture.md)
