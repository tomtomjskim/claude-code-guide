# Settings 전체 스키마 레퍼런스

## 개요

Claude Code settings는 4개의 레이어가 병합되어 최종 설정을 구성합니다. 이 문서는 v2.1.88 소스 분석 기반으로 60개 이상의 설정 키를 카테고리별로 정리하고, 실전에서 유용한 조합 3가지를 제시합니다.

---

## 1. 4-레이어 병합 우선순위

설정 파일은 낮은 우선순위에서 높은 우선순위 순으로 적용됩니다. 동일한 키가 여러 레이어에 존재하면 **더 높은 우선순위 레이어가 덮어씁니다.**

| 순위 | 레이어 | 파일 위치 | 설명 |
|------|--------|----------|------|
| 1 (최저) | **managed** | 시스템 관리자 배포 | 기업 정책, 사용자 수정 불가 |
| 2 | **policy** | 조직 정책 레이어 | IT/보안팀 강제 설정 |
| 3 | **project** | `.claude/settings.json` | 프로젝트별 설정 (git 커밋 가능) |
| 4 (최고) | **user** | `~/.claude/settings.json` | 개인 사용자 설정 |

> `settings.local.json`은 user 레이어와 동일한 우선순위이며 `.gitignore`에 포함됩니다. 민감한 개인 설정(API 키 경로, 로컬 경로 등)을 분리할 때 사용합니다.

---

## 2. 전체 설정 키 레퍼런스

### 2.1 AI / 모델 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `model` | string | `claude-sonnet-4-5` | 기본 사용 모델 ID |
| `smallModel` | string | `claude-haiku-4-5` | 빠른 작업용 경량 모델 |
| `largeContextModel` | string | `claude-sonnet-4-5` | 대용량 컨텍스트 작업 모델 |
| `maxTokens` | number | `8192` | output 최대 토큰 수 |
| `maxThinkingTokens` | number | `0` | extended thinking 토큰 예산 (`0`=비활성) |
| `alwaysThinkingEnabled` | boolean | `false` | 모든 요청에 extended thinking 활성화 |
| `temperature` | number | — | temperature 오버라이드 (보통 모델 기본값 사용) |
| `topP` | number | — | top-p 샘플링 오버라이드 |

### 2.2 메모리 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `memory` | object | — | 메모리 시스템 설정 블록 |
| `memory.enabled` | boolean | `true` | MEMORY.md 자동 로드 활성화 |
| `memory.maxFiles` | number | `5` | 턴당 주입할 최대 메모리 파일 수 |
| `memory.maxTokensPerFile` | number | — | 파일당 최대 토큰 수 |
| `autoMemoryEnabled` | boolean | `true` | 자동 메모리 저장 활성화 |
| `claudeMdExcludes` | string[] | `[]` | CLAUDE.md 로딩 제외 경로 목록 |

### 2.3 UI / UX 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `theme` | string | `"dark"` | UI 테마 (`"dark"` / `"light"` / `"system"`) |
| `verbose` | boolean | `false` | 상세 출력 모드 |
| `stream` | boolean | `true` | 스트리밍 응답 활성화 |
| `showTiming` | boolean | `false` | API 호출 소요 시간 표시 |
| `showTokenUsage` | boolean | `false` | 턴별 토큰 사용량 표시 |
| `notifications` | boolean | `true` | 데스크탑 알림 활성화 |
| `preferredNotificationType` | string | `"system"` | 알림 유형 (`"system"` / `"terminal-bell"` / `"iterm2"`) |
| `diffTool` | string | — | diff 뷰어 오버라이드 (예: `"vimdiff"`) |
| `editor` | string | — | 파일 편집기 오버라이드 (예: `"cursor"`) |
| `outputFormat` | string | `"text"` | 출력 포맷 (`"text"` / `"json"` / `"stream-json"`) |

### 2.4 권한 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `permissionMode` | string | `"default"` | 권한 확인 모드 (`"default"` / `"plan"` / `"auto"` / `"bypass"`) |
| `allowedTools` | string[] | `[]` | 허용할 도구 목록 (빈 배열 = 전체 허용) |
| `disallowedTools` | string[] | `[]` | 차단할 도구 목록 |
| `dangerouslySkipPermissions` | boolean | `false` | 모든 권한 확인 건너뜀 (위험, CI 전용) |
| `autoApprovePatterns` | string[] | `[]` | 자동 승인할 glob 패턴 목록 |
| `requireApprovalPatterns` | string[] | `[]` | 항상 승인 요청할 패턴 목록 |
| `readOnlyMode` | boolean | `false` | 파일 쓰기 전체 차단 (탐색 전용 세션) |

### 2.5 MCP 서버 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `mcpServers` | object | `{}` | MCP 서버 정의 맵 (`서버이름: 설정`) |
| `mcpServers.<name>.command` | string | 필수 | 실행할 명령어 |
| `mcpServers.<name>.args` | string[] | `[]` | 명령어 인수 |
| `mcpServers.<name>.env` | object | `{}` | 서버에 전달할 환경 변수 |
| `mcpServers.<name>.disabled` | boolean | `false` | 서버 일시 비활성화 |
| `mcpServers.<name>.timeout` | number | `30000` | 연결 타임아웃 (ms) |
| `mcpTimeout` | number | `30000` | 전체 MCP 기본 타임아웃 (ms) |
| `mcpRetries` | number | `3` | MCP 연결 실패 시 재시도 횟수 |

### 2.6 Hooks 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `hooks` | object | `{}` | 훅 정의 맵 |
| `hooks.PreToolUse` | object[] | `[]` | 도구 실행 전 훅 목록 |
| `hooks.PostToolUse` | object[] | `[]` | 도구 실행 후 훅 목록 |
| `hooks.Notification` | object[] | `[]` | 알림 이벤트 훅 |
| `hooks.Stop` | object[] | `[]` | 세션 종료 시 훅 |
| `hooks.<event>[].matcher` | string | — | 훅 적용 조건 (glob 또는 정규식) |
| `hooks.<event>[].hooks` | object[] | 필수 | 실행할 훅 액션 배열 |
| `hooks.<event>[].hooks[].type` | string | 필수 | 훅 타입 (`"command"` / `"script"`) |
| `hooks.<event>[].hooks[].command` | string | 필수 | 실행할 명령어 |

### 2.7 Git 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `gitEnabled` | boolean | `true` | git 통합 활성화 |
| `autoCommit` | boolean | `false` | 파일 변경 시 자동 커밋 (주의: 비권장) |
| `gitBranch` | string | — | 기본 작업 브랜치 오버라이드 |
| `gitCommitTemplate` | string | — | 커밋 메시지 템플릿 |
| `gitDiffContext` | number | `3` | diff 컨텍스트 줄 수 |
| `gitWorktreeEnabled` | boolean | `false` | git worktree 모드 활성화 |

### 2.8 컨텍스트 / 압축 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `autoCompact` | boolean | `true` | auto-compact 활성화 |
| `compactThreshold` | number | — | auto-compact 트리거 임계값 (토큰) |
| `maxContextFiles` | number | `20` | 컨텍스트에 포함할 최대 파일 수 |
| `contextIncludePatterns` | string[] | `[]` | 항상 컨텍스트에 포함할 glob 패턴 |
| `contextExcludePatterns` | string[] | `[]` | 컨텍스트에서 제외할 glob 패턴 |

### 2.9 플러그인 / 스킬 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `enabledPlugins` | object | `{}` | 플러그인 활성화 맵 (`플러그인ID: boolean`) |
| `skillsDirectory` | string | `".claude/skills"` | 스킬 파일 디렉토리 경로 |
| `autoLoadSkills` | boolean | `true` | 세션 시작 시 스킬 자동 로드 |
| `maxSkillsPerTurn` | number | `5` | 턴당 주입할 최대 스킬 수 |

### 2.10 기타 설정

| 키 | 타입 | 기본값 | 설명 |
|----|------|--------|------|
| `telemetryEnabled` | boolean | `true` | 익명 사용량 통계 전송 |
| `updateChannel` | string | `"stable"` | 업데이트 채널 (`"stable"` / `"beta"`) |
| `autoUpdate` | boolean | `true` | 자동 업데이트 활성화 |
| `locale` | string | — | 로케일 오버라이드 (예: `"ko-KR"`) |
| `timezone` | string | — | 타임존 오버라이드 (예: `"Asia/Seoul"`) |
| `logLevel` | string | `"warn"` | 로그 레벨 (`"debug"` / `"info"` / `"warn"` / `"error"`) |
| `logFile` | string | — | 로그 파일 경로 |
| `crashReporting` | boolean | `true` | 충돌 리포트 전송 |
| `apiKeyHelper` | string | — | API 키 공급 스크립트 경로 |
| `apiBaseUrl` | string | — | API endpoint 오버라이드 |
| `includeCoAuthoredBy` | boolean | `true` | 커밋에 `Co-Authored-By: Claude` 추가 |

---

## 3. 권장 설정 조합

### 3.1 개인 Pro 설정 (일상적인 개발)

개인 사용자가 풍부한 기능을 활용하면서 비용과 속도를 균형 있게 유지하는 설정입니다.

**파일 위치**: `~/.claude/settings.json`

```json
{
  "model": "claude-sonnet-4-5",
  "smallModel": "claude-haiku-4-5",
  "alwaysThinkingEnabled": true,
  "maxThinkingTokens": 8000,
  "memory": {
    "enabled": true,
    "maxFiles": 5
  },
  "autoCompact": true,
  "showTokenUsage": true,
  "theme": "dark",
  "notifications": true,
  "preferredNotificationType": "iterm2",
  "gitEnabled": true,
  "includeCoAuthoredBy": true,
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    }
  },
  "enabledPlugins": {
    "superpowers@superpowers-marketplace": true
  },
  "telemetryEnabled": false
}
```

**핵심 선택 이유**:
- `alwaysThinkingEnabled: true` — 복잡한 문제에 extended thinking 자동 활성화
- `showTokenUsage: true` — 비용 인식 향상
- `autoCompact: true` — 긴 세션에서 context 안정성 확보

### 3.2 자동화 / CI 설정 (NightOps, 배치 작업)

비대화형 자동화 세션에서 비용 최소화와 안정성을 최우선으로 하는 설정입니다.

**파일 위치**: `.claude/settings.json` (프로젝트 레벨) 또는 환경 변수로 주입

```json
{
  "model": "claude-haiku-4-5",
  "maxTokens": 4096,
  "alwaysThinkingEnabled": false,
  "memory": {
    "enabled": false
  },
  "autoCompact": true,
  "compactThreshold": 120000,
  "permissionMode": "auto",
  "dangerouslySkipPermissions": false,
  "notifications": false,
  "telemetryEnabled": false,
  "verbose": false,
  "outputFormat": "json",
  "logLevel": "error",
  "logFile": "/var/log/claude-automation.log"
}
```

**함께 사용할 환경 변수**:
```bash
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=120000
```

**핵심 선택 이유**:
- `model: haiku` — 반복 작업은 경량 모델로 비용 절감
- `compactThreshold: 120000` — 조기 압축으로 긴 배치 세션 안정화
- `outputFormat: json` — 파이프라인에서 출력 파싱 용이
- `memory.enabled: false` — 자동화 세션에서 메모리 주입 오버헤드 제거

### 3.3 Enterprise 설정 (팀 공유, 보안 강화)

팀 레포지토리에 커밋되는 설정으로, 모든 팀원에게 일관된 환경과 보안 기준을 적용합니다.

**파일 위치**: `.claude/settings.json` (git 커밋)

```json
{
  "model": "claude-sonnet-4-5",
  "memory": {
    "enabled": true,
    "maxFiles": 3
  },
  "autoCompact": true,
  "permissionMode": "default",
  "allowedTools": [
    "Read",
    "Edit",
    "Write",
    "Bash",
    "Grep",
    "Glob",
    "mcp__serena__find_symbol",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__replace_symbol_body",
    "mcp__serena__search_for_pattern",
    "mcp__serena__replace_content"
  ],
  "disallowedTools": [
    "WebFetch",
    "WebSearch"
  ],
  "dangerouslySkipPermissions": false,
  "gitEnabled": true,
  "gitWorktreeEnabled": true,
  "autoCommit": false,
  "includeCoAuthoredBy": true,
  "claudeMdExcludes": [
    "vendor/**",
    "node_modules/**",
    "dist/**"
  ],
  "contextExcludePatterns": [
    "**/*.min.js",
    "**/*.map",
    "**/node_modules/**",
    "**/dist/**",
    "**/.git/**"
  ],
  "logLevel": "info",
  "telemetryEnabled": false,
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '[AUDIT] Bash tool invoked at $(date)' >> /var/log/claude-audit.log"
          }
        ]
      }
    ]
  }
}
```

**핵심 선택 이유**:
- `allowedTools` 명시 — 허용된 도구만 사용 (WebFetch/WebSearch 차단으로 외부 데이터 유출 방지)
- `gitWorktreeEnabled: true` — 에이전트 격리 작업 지원
- `autoCommit: false` — 실수에 의한 자동 커밋 방지
- Hooks audit log — 모든 Bash 실행 감사 추적

---

## 4. 설정 검증

### 4.1 설정 파일 유효성 확인

```bash
# 현재 적용된 설정 확인 (4레이어 병합 결과)
claude config list

# 특정 키 값 확인
claude config get model

# 설정 파일 직접 편집
claude config edit

# 프로젝트 설정만 확인
cat .claude/settings.json | python3 -c "import json,sys; json.load(sys.stdin); print('Valid JSON')"
```

### 4.2 레이어별 충돌 디버깅

같은 키가 여러 레이어에 설정된 경우 user 레이어가 최종 적용됩니다. 예상치 못한 설정값이 적용된다면:

```bash
# 글로벌 설정 확인
cat ~/.claude/settings.json

# 프로젝트 설정 확인
cat .claude/settings.json

# 어느 레이어에서 값이 오는지 추적
claude config get <key> --verbose
```

---

## 다음 단계

- [컨텍스트 윈도우 내부 동작](19-context-window-internals.md)
- [Memory 시스템 내부 동작](21-memory-system-internals.md)
- [Agent Frontmatter 완전 스키마](22-agent-frontmatter-schema.md)
