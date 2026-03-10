# Claude Code 셋업 가이드

Claude Code를 효과적으로 사용하기 위한 종합 가이드입니다.

---

## 문서 목록

| # | 문서 | 설명 |
|---|------|------|
| 00 | [셋업 체크리스트](00-setup-checklist.md) | 초기 설정 체크리스트 |
| 01 | [MCP 설정](01-mcp-configuration.md) | MCP 서버 설정 가이드 (Serena 등) |
| 02 | [커맨드/스킬](02-commands-skills.md) | 기본 슬래시 커맨드 및 스킬 가이드 |
| 03 | [개발 파이프라인](03-development-pipeline.md) | 기본 파이프라인 (요구사항 → 설계 → 검수 → 구현) |
| 04 | [문서화 규칙](04-documentation-rules.md) | 세션 독립적 문서화 규칙 |
| 05 | [에이전트 페르소나](05-agent-personas.md) | PM, Architect, Developer 등 15개 페르소나 |
| 06 | [프로젝트 구조](06-project-structure.md) | 표준 프로젝트 구조 템플릿 |
| 07 | [CLAUDE.md 템플릿](07-claude-md-template.md) | 프로젝트 CLAUDE.md 템플릿 |
| 08 | [관련 프로젝트](08-related-projects.md) | Serena MCP, Agent Monitor, 네이티브 멀티 에이전트 |
| 09 | [추천 플러그인](09-recommended-plugins.md) | Superpowers, Context7 등 |
| 10 | [코드 리뷰 시스템](10-code-review-system.md) | 전문 리뷰어 6명, 6단계, 3프리셋, 하이브리드 모드 |
| 11 | [Workflow Commands](11-workflow-commands.md) | PDARR 워크플로우 커맨드 요약 |

### 참조 문서
| 문서 | 위치 | 설명 |
|------|------|------|
| Workflow Guide (상세) | [`.claude/workflow-commands-guide.md`](../.claude/workflow-commands-guide.md) | 커맨드 구축 종합 가이드 (셋업, Agent 전략, 팀 패턴) |

---

## 빠른 시작

### 1. 글로벌 설정
```json
// ~/.claude/settings.json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "alwaysThinkingEnabled": true,
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    }
  }
}
```

### 2. 프로젝트 초기화
```bash
# 문서/커맨드 구조 생성
mkdir -p .claude/commands
mkdir -p docs/{prd,todo,spec/{architecture,api,ui},history,qa-reports,complete}

# CLAUDE.md 생성 (07-claude-md-template.md 참조)
touch .claude/CLAUDE.md
```

### 3. 워크플로우 시작
```
/dispatch "로그인 기능 구현"
→ 복잡도 자동 판단 → 최적 경로 라우팅

Trivial → 직접 수정
Simple  → /run → /check-code → /stage
Medium  → /analyze → /run → /check-code → /stage
Complex → /prd → /analyze → /workflow (팀 Agent)
```

---

## 핵심 개념

### PDARR 워크플로우

**Plan → Document → Act → Review → Reflect**

```
사용자 요청
    │
    ▼
[/dispatch] ← 스마트 라우터
    │
    ├─ [계획] /prd → /analyze → /spec
    │
    ├─ [실행] /test → /run
    │
    ├─ [검증] /check-spec / /check-code / /qa-test
    │
    └─ [회고] /reflect → /complete → /stage
```

### 에이전트 역할
| 에이전트 | 역할 |
|---------|------|
| PM | 요구사항 분석, 태스크 분해 |
| Explorer | 코드 탐색, 영향도 분석 |
| Architect | 시스템 설계 |
| Developer | 구현 |
| QA | 검수 |
| DBA | DB 스키마/마이그레이션 |
| Designer | UI/UX 설계 |
| Publisher | 빌드/배포 |
| Documenter | 문서화 |
| 6 Specialist Reviewers | 보안, 성능, 테스트, 접근성, UX, API 전문 리뷰 |

### 실행 전략
| 전략 | 조건 | 도구 |
|------|------|------|
| 단일 Agent | Simple~Medium, ~3파일 | 커스텀 커맨드만 |
| 병렬 Task | Medium, 4-6파일 | Task() |
| 팀 Agent | Complex, 7파일+ | TeamCreate + Task + SendMessage |

---

## 권장 사항

### MCP
- **Serena**: 필수 - 시맨틱 코드 분석
- 멀티 에이전트: Claude Code 네이티브 도구 (Task, Agent, TeamCreate)

### 플러그인
- **Superpowers**: 필수 - TDD, 디버깅, 서브에이전트 개발

### 문서화
- 예시 코드 최소화
- 다이어그램 활용 (mermaid)
- 산출물은 docs/ 구조에 따라 정리

---

## 관련 링크

- [Agent Orchestra Monitor](https://github.com/tomtomjskim/agent-orchestra-monitor) - 실시간 모니터링 대시보드
- [Serena MCP](https://github.com/serena-ai/serena-mcp) - 시맨틱 코드 분석
- [Superpowers](https://github.com/obra/superpowers) - 개발 워크플로우 플러그인
- [Claude Code 공식 문서](https://docs.anthropic.com/claude-code)
