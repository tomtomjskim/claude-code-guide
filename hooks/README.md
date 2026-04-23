# Claude Code Hook 보일러플레이트 시스템

## 개요

Claude Code Hook은 도구 실행 전후에 자동으로 실행되는 셸 스크립트입니다.
위험한 명령 차단, 보호 파일 수정 방지, 서브에이전트 남용 제어 등 **안전장치를 코드로 정의**합니다.
이 디렉토리의 보일러플레이트를 프로젝트에 복사하고, 커스터마이징 영역만 수정하면 바로 사용할 수 있습니다.

## 사용 가능한 Hook

| Hook | 이벤트 | Matcher | 설명 |
|------|--------|---------|------|
| `guard-agent` | PreToolUse | Agent | 서브에이전트 호출 제어 (탐색 차단, 횟수 제한, 제약사항 검증) |
| `safety-careful` | PreToolUse | Bash | 파괴적 Bash 명령 차단 (`rm -rf /`, `DROP DATABASE` 등) |
| `safety-freeze` | PreToolUse | Edit, Write | 보호 파일 수정 차단 (`.env`, 프로덕션 설정 등) |
| `audit-agent` | PostToolUse | Agent | 서브에이전트 호출 감사 로그 기록 |

## 설치 방법

### 인스톨러 사용 (권장)

```bash
# 전체 Hook 설치 (standard 프리셋)
bash scripts/install-hooks.sh /path/to/my-project

# 프리셋 선택 설치
bash scripts/install-hooks.sh --preset minimal /path/to/my-project

# 특정 Hook만 선택
bash scripts/install-hooks.sh --hooks guard-agent,safety-careful /path/to/my-project

# 기존 Hook 덮어쓰기
bash scripts/install-hooks.sh --force /path/to/my-project

# 사용 가능한 Hook 목록 확인
bash scripts/install-hooks.sh --list
```

인스톨러는 다음을 자동 수행합니다:
1. `<project>/.claude/hooks/` 디렉토리에 Hook 스크립트 복사
2. `<project>/.claude/settings.local.json`에 Hook 등록 (matcher/event 매핑)

### 수동 설치

```bash
mkdir -p <project>/.claude/hooks
cp hooks/boilerplates/guard-agent.sh <project>/.claude/hooks/
chmod +x <project>/.claude/hooks/guard-agent.sh
```

이후 `settings.local.json`에 직접 등록:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/guard-agent.sh" }]
      }
    ]
  }
}
```

## 프리셋

| 프리셋 | 포함 Hook | 용도 |
|--------|-----------|------|
| `minimal` | guard-agent, safety-careful | 필수 안전장치만 빠르게 적용 |
| `standard` | 전체 4개 | 일반 프로젝트 권장 (기본값) |

## 커스터마이징

각 Hook 파일 상단의 **커스터마이징 영역**에서 프로젝트별 설정을 조정합니다.

### guard-agent.sh

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `BLOCKED_TYPES` | `"Explore"` | 차단할 서브에이전트 타입 (공백 구분) |
| `MAX_AGENT_CALLS` | `10` | 세션당 최대 Agent 호출 횟수 (0=무제한) |
| `MIN_PROMPT_LENGTH` | `200` | 이 길이 미만의 prompt는 단순 작업으로 간주 |
| `MIN_FILE_COUNT` | `2` | 이 개수 이하 파일 + 짧은 prompt → 차단 |
| `MIN_EFFICIENT_FILES` | `4` | 이 개수 미만 파일 → 토큰 효율 경고 |
| `ANALYSIS_PATTERN` | 내장 패턴 | 탐색/분석 의도 감지 정규식 (PCRE/ERE 자동 전환) |
| `CONSTRAINT_MISSING_ACTION` | `"warn"` | 제약사항 미포함 시 동작 (`warn` / `block`) |

### safety-careful.sh

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `TRUSTED_PATHS` | `()` | 무조건 허용할 스크립트 경로 목록 |
| `LEVEL4_PATTERNS` | 내장 패턴 | 절대 차단할 파괴적 명령 정규식 |

### safety-freeze.sh

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `FROZEN_TIER1` | 내장 목록 | 절대 수정 불가 파일 (`.env`, 프로덕션 설정) |
| `FROZEN_TIER2` | 내장 목록 | 경고 후 허용 대상 파일 |

### audit-agent.sh

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LOG_DIR` | `/tmp/claude-hooks` | 감사 로그 저장 디렉토리 |
| `PROMPT_PREVIEW_LENGTH` | `120` | 로그에 기록할 prompt 미리보기 길이 |

## 업그레이드

이미 설치된 Hook을 최신 보일러플레이트로 업그레이드하려면:

```bash
# 1. 기존 커스터마이징 백업
cp <project>/.claude/hooks/guard-agent.sh <project>/.claude/hooks/guard-agent.sh.bak

# 2. 최신 보일러플레이트 덮어쓰기
bash scripts/install-hooks.sh --force /path/to/project

# 3. 백업에서 커스터마이징 변수만 복원
# 각 파일의 '🔧 커스터마이징 영역' 블록만 비교하여 옮기세요
diff <project>/.claude/hooks/guard-agent.sh.bak <project>/.claude/hooks/guard-agent.sh
```

**커스터마이징 영역만 분리된 설계**이므로, 로직 업데이트 시 변수 블록만 복원하면 됩니다.

### 버전 확인

각 Hook 파일 상단 주석의 버전 태그를 비교하여 업그레이드 필요 여부를 판단합니다.

## 주의사항

- **서브에이전트에는 Hook이 전파되지 않습니다.** Hook은 메인 Claude Code 세션에서만 실행됩니다. `Agent` 도구로 생성된 서브에이전트는 별도의 Hook 컨텍스트를 가지지 않으므로, 서브에이전트 내부 동작을 제어하려면 `guard-agent` Hook으로 호출 자체를 제어해야 합니다.
- Hook의 exit code 규칙: `0` = 허용, `2` = 차단 (stderr 메시지가 모델에 피드백됨)
- Hook 스크립트 오류 시 기본적으로 **fail-open** (허용) 방식으로 동작합니다.
- `settings.local.json`은 `.gitignore`에 추가하여 프로젝트별 로컬 설정으로 유지하세요.

## 관련 문서

- [settings.json 스키마 레퍼런스](../docs/20-settings-schema-reference.md)
- [하네스 엔지니어링](../docs/29-harness-engineering.md)
- [권한 시스템](../docs/25-permission-system.md)
- [에이전트 프론트매터 스키마](../docs/22-agent-frontmatter-schema.md)

## 디렉토리 구조

```
hooks/
  boilerplates/              # 프로젝트 독립적 커스터마이징 가능 템플릿
    guard-agent.sh
    safety-careful.sh
    safety-freeze.sh
    audit-agent.sh
  scripts/                   # 레퍼런스 구현 (운영 예시, .reference.sh 접미어로 역할 자기설명)
    safety-careful.reference.sh
    safety-freeze.reference.sh
    event-review-trigger.reference.sh
  event-driven-review.yaml   # 이벤트 기반 리뷰 설정
  README.md
scripts/
  install-hooks.sh           # 보일러플레이트 인스톨러 스크립트
```

## scripts/ vs boilerplates/ 관계

| 디렉토리 | 성격 | 용도 |
|----------|------|------|
| `hooks/scripts/*.reference.sh` | **레퍼런스 구현** | 특정 서버 경로(`/home/ubuntu/`)가 하드코딩된 실제 운영 예시. 팀 시스템 설치 시 `~/.claude/team/hooks/scripts/`로 복사되어 사용됨. `.reference.sh` 접미어로 boilerplate와 구별. |
| `hooks/boilerplates/` | **커스터마이징 가능 템플릿** | 프로젝트 독립적인 범용 템플릿. 하드코딩 경로 없이 변수로 설정 가능. 새 프로젝트에는 이것을 사용. |

`scripts/`는 이 레포의 팀 시스템에서 직접 사용하는 Hook이고, `boilerplates/`는 다른 프로젝트에 복사하여 커스터마이징할 수 있도록 설계된 템플릿입니다.

## event-driven-review.yaml

`event-driven-review.yaml`은 PostToolUse Hook과 연동되는 **이벤트 기반 코드 리뷰 설정**입니다.

- `scripts/event-review-trigger.reference.sh`가 코드 변경 이벤트를 감지하면, 이 YAML에 정의된 리뷰 규칙에 따라 자동 리뷰를 트리거합니다.
- boilerplate Hook과의 관계: boilerplate는 개별 도구 호출의 차단/허용을 제어하고, event-driven-review는 코드 변경 후 리뷰 프로세스를 관리합니다. 두 시스템은 독립적으로 동작하며 함께 사용할 수 있습니다.

## 새 Hook 만들기

1. **`.sh` 파일 작성**: `hooks/boilerplates/` 디렉토리에 새 Hook 스크립트를 작성합니다. 기존 boilerplate의 구조(커스터마이징 영역 + 로직)를 따릅니다.
2. **HOOK_CATALOG에 항목 추가**: `scripts/install-hooks.sh`의 `HOOK_CATALOG` 배열에 `"hook명:이벤트:matcher"` 형식으로 항목을 추가합니다.
3. **README 테이블 업데이트**: 이 문서의 "사용 가능한 Hook" 테이블에 새 Hook의 이벤트, matcher, 설명을 추가합니다.
