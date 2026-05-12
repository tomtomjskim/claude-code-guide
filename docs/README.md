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
| 12 | [v3.0 시스템 아키텍처](12-v3-architecture.md) | 5-section 템플릿, Handoff Protocol, 모델 라우팅, Tiebreaker 등 v3.0 전체 설계 |
| 13 | [핸드오프 & 실패 복구](13-handoff-and-failure.md) | Handoff Protocol 설정, failure-policy.yaml, 실전 예시, PM/에스컬레이션 템플릿 |
| 14 | [프리셋 시스템](14-preset-system.md) | 깊이(Depth) x 실행(Mode) 2축 프리셋 체계 |
| 15 | [Codex 플러그인](15a-codex-plugin.md) | OpenAI Codex CLI 통합 — 코드 리뷰, 디버깅 위임, Review Gate |

### 소스 분석 기반 심화 가이드 (v2.1.88)

Claude Code v2.1.88 소스 분석에서 확인된 내부 동작과 최적화 전략입니다.

| # | 문서 | 설명 |
|---|------|------|
| 15 | [토큰 가격표 & 비용 최적화](15-token-pricing-optimization.md) | 모델별 단가, 서브에이전트 전략, 플랜 예산 |
| 16 | [사용량 한도 & Rate Limit](16-usage-limits-ratelimit.md) | 5h/7d 윈도우, Early Warning, Overage |
| 17 | [환경변수 레퍼런스](17-environment-variables.md) | 비공개 포함 15+ 환경변수 |
| 18 | [Fast Mode 상세 & 비활성화](18-fast-mode.md) | 6x 비용, 비활성화 방법, 권장 설정 |
| 19 | [컨텍스트 윈도우 내부](19-context-window-internals.md) | auto-compact, 압축 구조, 재주입 |
| 20 | [Settings 전체 스키마](20-settings-schema-reference.md) | 60+ 키, 4단계 병합, 권장 조합 |
| 21 | [Memory 시스템 내부](21-memory-system-internals.md) | 한도, 랭킹, frontmatter 최적화 |
| 22 | [Agent Frontmatter 스키마](22-agent-frontmatter-schema.md) | 15개 필드 완전 레퍼런스 |
| 23 | [도구 동시성 모델](23-tool-concurrency-model.md) | 병렬/직렬 분류, 성능 팁 |
| 24 | [Retry & 에러 복구](24-retry-error-recovery.md) | 재시도 상수, 에러 분류, 에스컬레이션 |
| 25 | [Permission 결정 트리](25-permission-system.md) | 5모드, AST 파싱, ML 분류기 |
| 26 | [Coordinator Mode](26-coordinator-mode.md) | 멀티에이전트 오케스트레이션 |
| 27 | [스킬 경량화 가이드](27-skill-lightweight-guide.md) | 스킬 크기 기준, 본체/참조 분리, 경량 템플릿 |
| 28 | [토큰 낭비 자가진단](28-token-waste-selfcheck.md) | Cloud AI MCP, 7대 낭비 요소, 자동 진단, 시나리오별 프로필 |
| 29 | [하네스 엔지니어링](29-harness-engineering.md) | 5컴포넌트 통합 아키텍처, hooks 패턴, 시나리오별 설계 |
| 30 | [Advisor Strategy](30-advisor-strategy.md) | executor+advisor 패턴, API 구현, PDARR 연계, 비용 벤치마크 |
| 31 | [듀얼 모드 디자인 전략](31-design-strategy.md) | SYSTEMATIC/CREATIVE 디자인 모드, 디자인 게이트, 토큰 브릿지 |
| 32 | [디자인 시스템 확장 규칙](32-design-system-extension.md) | 토큰 추가/변경/제거 절차, 폰트 변경 규칙 |
| 33 | [서브에이전트 효율성](33-subagent-efficiency.md) | 12가지 효율화 전략, 성능 리스크 분석, Tiered Dispatch, Result Pipe |
| 34 | [DESIGN.md 운영 모델](34-design-md-operating-model.md) | DESIGN.md 개념 주입, 토큰 보일러플레이트, 버전 관리, 실행 태스크 |
| 35 | [DESIGN.md 도입 평가 케이스](35-design-md-adoption-cases.md) | 비권장 시그널, 부분 도입 권장 요소, 케이스 스터디, downstream 평가 절차 |

### 참조 문서
| 문서 | 위치 | 설명 |
|------|------|------|
| Workflow Guide (상세) | [`.claude/workflow-commands-guide.md`](../.claude/workflow-commands-guide.md) | 커맨드 구축 종합 가이드 (셋업, Agent 전략, 팀 패턴) |
| DESIGN.md System Guide | [`design-md-system-guide.html`](design-md-system-guide.html) | DESIGN.md 시스템 학습용 HTML 다이어그램과 검색 가능한 UI/UX 용어 사전 |
| v4.3 Changelog | [`v4.3-changelog.md`](v4.3-changelog.md) | PDARR + Goal-runtime 정렬 (`/breakdown` 신규, `/prd --vibe` 모드) |
| v4.2 Changelog | [`v4.2-changelog.md`](v4.2-changelog.md) | DESIGN.md 운영 모델 릴리즈 노트 |

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
