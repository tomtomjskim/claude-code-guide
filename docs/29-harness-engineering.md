# 하네스 엔지니어링 가이드

## 개요

**하네스 엔지니어링(Harness Engineering)**은 Claude Code의 동작을 코드 밖에서 제어하는 기술입니다. settings.json, hooks, CLAUDE.md, skills, memory 5가지 컴포넌트를 조합하여 AI 어시스턴트의 행동 범위, 품질 기준, 비용 효율을 시스템적으로 설계합니다.

코드를 작성하지 않고도 Claude Code의 품질과 안전성을 근본적으로 바꿀 수 있는 유일한 방법입니다.

---

**관련 문서**:
- [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
- [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
- [스킬 경량화 가이드](27-skill-lightweight-guide.md)
- [Advisor Strategy 가이드](30-advisor-strategy.md)
- [환경 변수 레퍼런스](17-environment-variables.md)

---

## 1. 하네스 아키텍처 — 5가지 컴포넌트

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code 세션                    │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌────────┐              │
│  │ CLAUDE.md│  │ Memory   │  │ Skills │  ← 컨텍스트  │
│  │(매 턴 주입)│  │(관련 파일) │  │(호출 시) │  주입 레이어│
│  └────┬─────┘  └────┬─────┘  └───┬────┘              │
│       │              │            │                    │
│       ▼              ▼            ▼                    │
│  ┌──────────────────────────────────────┐            │
│  │          모델 추론 (Opus/Sonnet)       │            │
│  └──────────────┬───────────────────────┘            │
│                 │                                      │
│       ┌─────────▼─────────┐                           │
│       │   도구 호출 시도     │                           │
│       └─────────┬─────────┘                           │
│                 │                                      │
│  ┌──────────────▼──────────────┐                      │
│  │    Hooks (PreToolUse)       │  ← 행동 제어 레이어   │
│  │    → BLOCK / WARN / PASS   │                       │
│  └──────────────┬──────────────┘                      │
│                 │                                      │
│       ┌─────────▼─────────┐                           │
│       │     도구 실행       │                           │
│       └─────────┬─────────┘                           │
│                 │                                      │
│  ┌──────────────▼──────────────┐                      │
│  │    Hooks (PostToolUse)      │  ← 검증 레이어       │
│  │    → 구문 검증, 리뷰 트리거  │                       │
│  └─────────────────────────────┘                      │
│                                                       │
│  ┌─────────────────────────────┐                      │
│  │  settings.json              │  ← 설정 레이어       │
│  │  (모델, 권한, 환경변수, MCP) │                       │
│  └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────┘
```

### 컴포넌트별 역할

| # | 컴포넌트 | 제어 대상 | 적용 시점 | 파일 위치 |
|---|----------|----------|----------|----------|
| 1 | **settings.json** | 모델, 권한, 환경변수, MCP, hooks | 세션 시작 시 | `~/.claude/settings[.local].json`, `.claude/settings[.local].json` |
| 2 | **Hooks** | 도구 실행 전후 차단/검증 | 도구 호출 시 | settings.json 내 `hooks` 필드 |
| 3 | **CLAUDE.md** | 프로젝트 규칙, 컨벤션, 워크플로우 | 매 턴 주입 | `CLAUDE.md`, `.claude/CLAUDE.md` |
| 4 | **Skills** | 특정 작업의 실행 절차 | 슬래시 커맨드 호출 시 | `.claude/skills/*/SKILL.md` |
| 5 | **Memory** | 사용자/프로젝트/피드백 컨텍스트 | 매 턴 관련 파일 주입 | `~/.claude/projects/*/memory/*.md` |

---

## 2. 설정 레이어 우선순위

```
managed (최저) → policy → project → user/local (최고)

설정 파일 4+2 구조:
  managed/settings.json     ← 기업 IT 배포 (사용자 수정 불가)
  policy/settings.json      ← 조직 보안팀 강제
  .claude/settings.json     ← 프로젝트 공용 (git 커밋)
  .claude/settings.local.json ← 프로젝트 개인 (.gitignore)
  ~/.claude/settings.json   ← 글로벌 공용
  ~/.claude/settings.local.json ← 글로벌 개인 (권장: 토큰 최적화)
```

### 팀 운영 시 분리 원칙

| 설정 유형 | 파일 | 예시 |
|----------|------|------|
| 프로젝트 규칙 (팀 공유) | `.claude/settings.json` | hooks, allowedTools, autoCommit:false |
| 개인 최적화 | `.claude/settings.local.json` | fastMode:false, Cloud AI MCP disabled |
| 글로벌 공통 | `~/.claude/settings.json` | MCP 서버 (serena), 테마 |
| 글로벌 개인 | `~/.claude/settings.local.json` | 토큰 최적화, 서브에이전트 모델 |

---

## 3. Hooks — 행동 제어 엔진

Hooks는 Claude Code가 도구를 호출할 때 실행되는 셸 스크립트입니다. 하네스 엔지니어링에서 가장 강력한 제어 수단입니다.

### 3.1 Hook 라이프사이클

| 이벤트 | 시점 | 용도 |
|--------|------|------|
| `PreToolUse` | 도구 실행 **전** | 위험 명령 차단, 파일 보호 |
| `PostToolUse` | 도구 실행 **후** | 구문 검증, 리뷰 트리거, 감사 로그 |
| `Notification` | 알림 이벤트 발생 시 | 외부 알림 연동 |
| `Stop` | 세션 종료 시 | 정리 작업, 리포트 생성 |

### 3.2 Hook 설정 구조

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/safety-careful.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/syntax-check.sh"
          }
        ]
      }
    ]
  }
}
```

### 3.3 핵심 Hook 패턴 라이브러리

#### 패턴 1: 위험 명령 차단 (PreToolUse:Bash)

```bash
#!/bin/bash
# safety-careful.sh — Level 4 차단, Level 3 경고
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Level 4: 절대 차단
if echo "$CMD" | grep -qE 'rm\s+-rf\s+/|DROP\s+DATABASE|git\s+push\s+--force\s+origin\s+main'; then
    echo '{"decision": "block", "reason": "Level 4 위험 명령 차단"}'
    exit 0
fi

# Level 3: 경고
if echo "$CMD" | grep -qiE 'ALTER\s+TABLE|TRUNCATE|git\s+reset\s+--hard'; then
    echo '{"decision": "warn", "reason": "Level 3 주의 명령 — 확인 필요"}'
    exit 0
fi
```

#### 패턴 2: 파일 보호 (PreToolUse:Edit/Write)

```bash
#!/bin/bash
# safety-freeze.sh — 민감 파일 편집 차단
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")

# Tier 1: 절대 차단
if echo "$FILE" | grep -qE '\.env$|/etc/|credentials|secrets'; then
    echo '{"decision": "block", "reason": "민감 파일 편집 차단"}'
    exit 0
fi
```

#### 패턴 3: 구문 검증 (PostToolUse:Edit/Write)

```bash
#!/bin/bash
# syntax-check.sh — PHP/JS 구문 자동 검증
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

case "$FILE" in
    *.php) php -l "$FILE" 2>&1 ;;
    *.js)  node --check "$FILE" 2>&1 ;;
    *.ts)  npx tsc --noEmit "$FILE" 2>&1 ;;
esac
```

#### 패턴 4: 감사 로그 (PostToolUse:Bash)

```bash
#!/bin/bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
echo "[$(date -Iseconds)] Bash: $CMD" >> /var/log/claude-audit.log
```

### 3.4 Hook matcher 패턴

| matcher | 매칭 대상 |
|---------|----------|
| `"Bash"` | Bash 도구만 |
| `"Edit\|Write"` | Edit 또는 Write |
| `"mcp__serena__*"` | Serena MCP 모든 도구 |
| `"*"` | 모든 도구 |

---

## 4. CLAUDE.md — 프로젝트 DNA

### 4.1 CLAUDE.md 설계 원칙

```
1. 간결함: 5KB 이하 (프로젝트), 1KB 이하 (글로벌)
2. 행동 지시: "~하라", "~하지 마라" 형태
3. 참조 분리: 상세 가이드는 별도 파일, CLAUDE.md는 포인터만
4. 경로 스코프: .claude/rules/*.md로 경로별 규칙 분리
```

### 4.2 경량 CLAUDE.md 구조

```markdown
# [프로젝트명]

## 필수 규칙
- PHP 7.2 호환 필수, any 사용 금지
- SQL 파라미터 바인딩 사용하지 않음 (레거시 호환)
- 커밋 전 반드시 사용자 확인

## 기술 스택
PHP 7.2 | MySQL 5.7 | JS ES6 | SCSS

## 디렉토리
modules/ (컨트롤러), views/ (템플릿), domain/ (DDD)

## 참조
- 코딩 가이드: .claude/coding_guidelines.md
- DB 접근: .claude/tools/database_access_guide.md
- 워크플로우: .claude/workflow-commands-guide.md
```

### 4.3 경로 스코프 규칙 (rules/)

CLAUDE.md를 비대하게 만들지 않고 경로별 규칙을 적용하는 방법입니다.

```
.claude/rules/
├── admin-work.md       # modules/admin/**, views/admin/** 수정 시 자동 로드
├── ddd-classes.md      # domain/**, infrastructure/** 수정 시 자동 로드
├── scss-rules.md       # css/**.scss 수정 시 자동 로드
└── i18n-rules.md       # i18n/**, views/** 수정 시 자동 로드
```

각 rules 파일 상단에 적용 경로를 명시합니다:

```markdown
---
globs: domain/**,infrastructure/**,application/**
---
# DDD 클래스 규칙
- namespace 필수: `namespace Domain\[도메인명]\...`
- ...
```

**장점**: 관련 파일 수정 시에만 로드되므로 불필요한 토큰 소비 없음.

---

## 5. Skills — 재사용 가능한 작업 절차

### 5.1 스킬 설계 원칙

```
1. 본체(SKILL.md) ≤ 200줄, 5KB 이내
2. 상세 데이터는 references/ 디렉토리에 분리
3. 하나의 스킬 = 하나의 명확한 목표
4. 예제는 1개면 충분
```

### 5.2 스킬과 CLAUDE.md의 역할 분리

| 구분 | CLAUDE.md | Skills |
|------|-----------|--------|
| 로드 시점 | 매 턴 자동 | 슬래시 커맨드 호출 시 |
| 내용 | 프로젝트 규칙/제약 | 작업 실행 절차 |
| 크기 | 최소화 필수 | 적정 크기 유지 |
| 변경 빈도 | 낮음 (안정적) | 높음 (워크플로우 진화) |

상세는 [스킬 경량화 가이드](27-skill-lightweight-guide.md) 참조.

---

## 6. Memory — 대화 간 연속성

### 6.1 메모리 유형과 활용

| 유형 | 저장 내용 | 활용 시점 |
|------|----------|----------|
| `user` | 사용자 역할, 선호, 전문성 | 응답 톤/깊이 조절 |
| `feedback` | 사용자 교정/확인 | 동일 실수 반복 방지 |
| `project` | 진행 중 작업, 마감, 이해관계자 | 작업 맥락 이해 |
| `reference` | 외부 시스템 위치 (Linear, Slack 등) | 정보 소스 파악 |

### 6.2 메모리 비용 제어

```json
{
  "memory": { "enabled": true, "maxFiles": 3 },
  "autoMemoryEnabled": false
}
```

- `maxFiles: 3` — 턴당 주입 파일 수 제한 (기본 5)
- `autoMemoryEnabled: false` — 자동 저장 비활성화, 명시적 요청 시에만 저장
- 정기적으로 오래된 메모리 파일 정리

---

## 7. 사용 시나리오별 하네스 설계

### 7.1 개인 개발자 (비용 최적화)

```
settings.local.json:
  ✅ fastMode: false
  ✅ SUBAGENT_MODEL: sonnet
  ✅ Cloud AI MCP: disabled
  ✅ maxSkillsPerTurn: 3
  ✅ showTokenUsage: true

CLAUDE.md:
  ✅ 3KB 이내
  ✅ 규칙만, 설명 최소

Hooks:
  ✅ 구문 검증 (PostToolUse)
  선택: 위험 명령 차단

Skills:
  ✅ 사용 빈도 높은 5~7개만 활성화
  ✅ 각 5KB 이내
```

### 7.2 팀 프로젝트 (안전성 + 일관성)

```
.claude/settings.json (git 커밋):
  ✅ hooks: 위험 명령 차단 + 구문 검증 + 감사 로그
  ✅ allowedTools: 허용 도구 명시
  ✅ autoCommit: false
  ✅ gitWorktreeEnabled: true

.claude/settings.local.json (개인):
  ✅ 토큰 최적화 설정
  ✅ Cloud AI MCP 비활성화

.claude/rules/:
  ✅ 경로별 규칙 분리 (admin, DDD, SCSS 등)

CLAUDE.md:
  ✅ 핵심 규칙만 (5KB 이내)
  ✅ 상세는 .claude/*.md로 분리
```

### 7.3 자동화/NightOps (최소 비용 + 안전성)

```
settings.json:
  ✅ model: haiku (반복 작업)
  ✅ memory.enabled: false
  ✅ DISABLE_BACKGROUND_TASKS: 1
  ✅ permissionMode: auto
  ✅ outputFormat: json

Hooks:
  ✅ 위험 명령 차단 (PreToolUse) — 무인 실행이므로 필수
  ✅ 감사 로그 (PostToolUse)

Skills:
  ✅ maxSkillsPerTurn: 1
```

---

## 8. 하네스 검증

### 8.1 자동 검증

```bash
# 시스템 무결성 검증
bash scripts/validate-system.sh

# 토큰 낭비 진단
bash scripts/selfcheck-token-waste.sh /path/to/project
```

### 8.2 수동 점검 체크리스트

#### settings.json
- [ ] `fastMode: false` 설정
- [ ] `DISABLE_FAST_MODE=1` 환경변수
- [ ] `SUBAGENT_MODEL=sonnet` 환경변수
- [ ] 불필요한 Cloud AI MCP `disabled: true`
- [ ] `maxSkillsPerTurn` ≤ 3
- [ ] `memory.maxFiles` ≤ 5

#### Hooks
- [ ] PreToolUse:Bash — 위험 명령 차단 hook 등록
- [ ] PostToolUse:Edit/Write — 구문 검증 hook 등록
- [ ] Hook 스크립트 실행 권한 (`chmod +x`)

#### CLAUDE.md
- [ ] 프로젝트 CLAUDE.md ≤ 5KB
- [ ] 글로벌 CLAUDE.md ≤ 1KB
- [ ] 상세 가이드는 별도 파일로 분리
- [ ] 경로 스코프 규칙 활용 (`.claude/rules/`)

#### Skills
- [ ] SKILL.md 각 ≤ 8KB (이상적: ≤ 5KB)
- [ ] 12KB 초과 스킬 없음
- [ ] 상세 데이터는 `references/`로 분리
- [ ] 미사용 스킬 `disabled: true` 또는 `_archived/`로 이동

---

## 9. 하네스 진화 — 프로젝트 성장에 따른 확장

### Phase 1: 시작 (1인 개발)

```
CLAUDE.md (1~2KB) + settings.local.json (토큰 최적화)
```

### Phase 2: 성장 (규칙 축적)

```
+ .claude/rules/ (경로별 규칙)
+ Hooks (구문 검증)
+ Skills 3~5개
```

### Phase 3: 팀 (협업 표준화)

```
+ .claude/settings.json (팀 공용 hooks, 권한)
+ .claude/settings.local.json (개인 분리)
+ 팀 에이전트 시스템 (agents.yaml)
```

### Phase 4: 자동화 (NightOps)

```
+ 자동화 전용 settings 프로필
+ 감사 로그 hooks
+ 장애 복구 정책 (failure-policy.yaml)
```

---

## 다음 단계

1. [Settings 스키마 레퍼런스](20-settings-schema-reference.md) — 60+ 설정 키 상세
2. [토큰 낭비 자가진단](28-token-waste-selfcheck.md) — 7대 낭비 요소 진단
3. [스킬 경량화 가이드](27-skill-lightweight-guide.md) — 스킬 크기 최적화
4. [Advisor Strategy 가이드](30-advisor-strategy.md) — executor+advisor 모델 패턴
5. [환경 변수 레퍼런스](17-environment-variables.md) — 15+ 환경변수
