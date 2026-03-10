# Claude Code 셋업 가이드

**Claude Code를 효과적으로 사용하기 위한 종합 가이드 및 템플릿**

---

## 개요

이 레포지토리는 Claude Code 초기 설정부터 팀 워크플로우까지 모든 것을 다룹니다.

### 주요 내용
- PDARR 워크플로우 커맨드 시스템 (/dispatch, /prd, /run, /workflow 등)
- 2단계 복잡도 판단 → 최적 실행 전략 자동 선택
- 멀티 Agent 팀 구성 (단일/병렬/팀 Agent 3전략)
- MCP 서버 설정 (Serena 등)
- 에이전트 페르소나 정의 (9 Core + 6 Specialist Reviewers)
- 문서화 규칙 및 템플릿
- 체크리스트 기반 워크플로우

---

## 빠른 시작

### 1. 글로벌 설정

```bash
# ~/.claude/settings.json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "alwaysThinkingEnabled": true,
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
# 이 레포의 템플릿 사용
cp -r templates/project-structure/* /your/project/

# 또는 수동 생성
mkdir -p .claude/commands
mkdir -p docs/{prd,todo,spec,history,qa-reports,complete}
```

### 3. CLAUDE.md 설정

```bash
# 템플릿 복사
cp templates/CLAUDE.md /your/project/.claude/CLAUDE.md

# 프로젝트에 맞게 수정
```

### 4. 워크플로우 가이드 배치

```bash
# 워크플로우 가이드를 프로젝트 .claude/에 복사
cp .claude/workflow-commands-guide.md /your/project/.claude/
```

---

## 문서 목록

| # | 문서 | 설명 |
|---|------|------|
| 00 | [셋업 체크리스트](docs/00-setup-checklist.md) | 초기 설정 체크리스트 |
| 01 | [MCP 설정](docs/01-mcp-configuration.md) | Serena 등 MCP 설정 |
| 02 | [커맨드/스킬](docs/02-commands-skills.md) | 기본 슬래시 커맨드 및 스킬 구조 |
| 03 | [개발 파이프라인](docs/03-development-pipeline.md) | 기본 파이프라인 (요구사항 → 설계 → 검수 → 구현) |
| 04 | [문서화 규칙](docs/04-documentation-rules.md) | 세션 독립적 문서화 |
| 05 | [에이전트 페르소나](docs/05-agent-personas.md) | PM, Architect, Developer, QA 등 15개 Agent |
| 06 | [프로젝트 구조](docs/06-project-structure.md) | 표준 프로젝트 구조 |
| 07 | [CLAUDE.md 템플릿](docs/07-claude-md-template.md) | 프로젝트 설정 템플릿 |
| 08 | [관련 프로젝트](docs/08-related-projects.md) | Serena MCP, Agent Monitor 등 |
| 09 | [추천 플러그인](docs/09-recommended-plugins.md) | Superpowers, Context7 등 |
| 10 | [코드 리뷰 시스템](docs/10-code-review-system.md) | 전문 리뷰어 6명, 6단계, 3프리셋 |
| 11 | [Workflow Commands](docs/11-workflow-commands.md) | PDARR 워크플로우 커맨드 요약 |
| -- | [Workflow Guide (상세)](.claude/workflow-commands-guide.md) | 커맨드 구축 종합 가이드 |

---

## 핵심 개념

### PDARR 워크플로우

**Plan → Document → Act → Review → Reflect**

모든 작업은 복잡도에 따라 이 사이클의 전체 또는 일부를 거친다.
`/dispatch`가 작업 크기에 맞는 사이클 범위를 자동 결정한다.

```
사용자 요청
    │
    ▼
[/dispatch] ← 30초 이내 판단
    │
    ├─ Trivial ─→ 직접 수정
    ├─ Simple ──→ /run → /check-code → /stage
    ├─ Medium ──→ /analyze → /run → /check-code → /stage
    ├─ Complex ─→ /prd → /analyze → /workflow (팀 Agent)
    └─ Review ──→ /check-spec 또는 /check-code
```

### 커맨드 전체 맵

```
[시작점]    /dispatch ─── 스마트 라우터

[계획]      /prd ─── /analyze ─── /spec

[실행]      /test ─── /run

[검증]      /check-spec ─── /check-code ─── /qa-test

[회고]      /reflect ─── /complete

[유틸]      /stage ─── /flow ─── /workflow
```

### 2단계 판단 시스템

| 단계 | 커맨드 | 판단 기반 | 출력 |
|------|--------|----------|------|
| 1차 | `/prd` | 요구사항 텍스트 | 복잡도 추정, 병렬화 가능성 |
| 2차 | `/analyze` | 코드베이스 실제 분석 | 1차 보정, 팀 구성 추천 |

### 실행 전략 3가지

| 전략 | 조건 | 도구 | 파일 규모 |
|------|------|------|----------|
| A: 단일 Agent | Simple~Medium | 커스텀 커맨드만 | ~3개 |
| B: 병렬 Task | Medium | Task() | 4-6개 |
| C: 팀 Agent | Complex | TeamCreate + Task + SendMessage | 7개+ |

> 상세 가이드: [`.claude/workflow-commands-guide.md`](.claude/workflow-commands-guide.md)

---

### 문서 구조

```
docs/
├── prd/               # PRD 문서 (요구사항 + 1차 판단)
├── spec/              # 기술 설계
│   ├── architecture/  # 아키텍처
│   ├── api/           # API
│   └── ui/            # UI/UX
├── todo/              # 대기중
├── history/           # 세션 히스토리
├── qa-reports/        # QA 리포트
└── complete/          # 완료 (통합 정리)
    └── summary.md     # 전체 요약
```

### 에이전트 페르소나

#### Core Agents (9개)
| 에이전트 | 역할 | 산출물 |
|---------|------|--------|
| PM | 요구사항 분석, 태스크 분해, 리뷰 판정 | REQ-XXX.md |
| Explorer | 코드 탐색, 영향도 분석 | 분석 리포트 |
| Architect | 시스템 설계 | spec/*.md |
| Developer | 구현 | 코드, 테스트 |
| QA | 검수 | 검수 리포트 |
| DBA | DB 스키마, 마이그레이션 | schema.sql |
| Designer | UI/UX 설계 | component-spec.md |
| Publisher | 빌드/배포 | deployment-log.md |
| Documenter | 문서화 | DONE-XXX.md |

#### Specialist Reviewers (6개, v2.0)
| 리뷰어 | 페르소나 | 핵심 관점 |
|--------|---------|----------|
| Security Reviewer | Security Sentinel | "공격자에게 노출되면?" |
| Performance Reviewer | Performance Prophet | "트래픽 10배면?" |
| Test Coverage Reviewer | Test Guardian | "이 테스트가 진짜 검증하나?" |
| Accessibility Reviewer | Access Advocate | "장애인도 쓸 수 있나?" |
| UX Reviewer | UX Harmonizer | "사용자가 혼란스럽지 않나?" |
| API Reviewer | API Arbiter | "1년 후에도 호환되나?" |

### 코드 리뷰 v2.0

```
"빠른 리뷰: [설명]"       → quick (~2분, 자동 분석만)
"리뷰: [설명]"            → standard (~10분, 기본)
"상세 리뷰: [설명]"       → thorough (~20분, 전체 6단계)
"팀 리뷰: [설명]"         → Agent Teams + thorough
```

자세한 내용은 [코드 리뷰 시스템 가이드](docs/10-code-review-system.md)를 참조하세요.

---

## 템플릿

### 프로젝트 템플릿
- [프로젝트 구조](templates/project-structure/) - 표준 디렉토리 구조
- [CLAUDE.md](templates/CLAUDE.md) - 프로젝트 설정 파일
- [체크리스트](templates/checklists/) - 워크플로우 체크리스트

### 문서 템플릿
- [요구사항 (REQ-XXX)](templates/docs/REQ-template.md)
- [설계 문서](templates/docs/SPEC-template.md)
- [태스크 (TASK-XXX)](templates/docs/TASK-template.md)
- [완료 (DONE-XXX)](templates/docs/DONE-template.md)
- [세션 히스토리](templates/docs/SESSION-template.md)

---

## MCP 권장 설정

### 필수
- **Serena MCP** - 시맨틱 코드 분석/편집

> 멀티 에이전트 오케스트레이션은 Claude Code 네이티브 도구(Task, Agent, TeamCreate, SendMessage)로 처리합니다. Team Orchestrator MCP는 더 이상 권장하지 않습니다.

### 설정 예시
```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    }
  }
}
```

---

## 추천 플러그인

### 필수
- **[Superpowers](https://github.com/obra/superpowers)** - TDD, 체계적 디버깅, 서브에이전트 개발 워크플로우 (14개 스킬)
  - 설치: `claude plugin marketplace add obra/superpowers-marketplace && claude plugin install superpowers@superpowers-marketplace`
  - 주요 기능: brainstorming, writing-plans, executing-plans, TDD, systematic-debugging, dispatching-parallel-agents 등
- **Skill Creator** (Anthropic 공식) - 스킬 생성/테스트/개선/벤치마크
  - 설치: `claude plugin install skill-creator@claude-plugins-official`
  - 4가지 모드: Create, Eval, Improve, Benchmark
  - 슬래시 커맨드: `/skill-creator`

### 추천 (추가 검토)
- **[Context7](https://github.com/upstash/context7)** - 최신 문서 검색/참조
- **[Superpowers Lab](https://github.com/obra/superpowers-lab)** - 실험적 스킬 확장
- **[Superpowers Chrome](https://github.com/obra/superpowers-chrome)** - 브라우저 직접 제어

자세한 내용은 [추천 플러그인 가이드](docs/09-recommended-plugins.md)를 참조하세요.

---

## 사용 예시

### PDARR 워크플로우로 새 기능 개발

```
사용자: "수수료 정산 시스템 구현해줘"

/dispatch "수수료 정산 시스템"
→ Complex 판정 → /prd 경로 추천

/prd 수수료 정산
→ 요구사항 구조화
→ 1차 판단: Complex (파일 8개+, 3레이어)
→ docs/prd/commission/prd.md 생성

/analyze commission
→ 코드베이스 분석
→ 2차 판단: 팀 Agent 추천 (백엔드/프론트 병렬)
→ 팀 구성: analyzer, backend-dev, frontend-dev, reviewer

/workflow
→ TeamCreate → TaskCreate → 병렬 Agent 실행
→ 백엔드/프론트엔드 동시 구현
→ /check-code 자동 검수
→ /reflect → /complete → /stage
```

### 간단한 버그 수정

```
사용자: "상품 목록 정렬 버그 수정해줘"

/dispatch "정렬 버그"
→ Simple 판정 → /run 직행

/run
→ 직접 수정 → 테스트

/check-code → /stage
```

---

## 관련 프로젝트

### MCP 서버

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [Serena MCP](https://github.com/serena-ai/serena-mcp) | 시맨틱 코드 분석/편집 | 필수 - 코드 탐색, 심볼 분석, 리팩토링 |

### 모니터링

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [Agent Orchestra Monitor](https://github.com/tomtomjskim/agent-orchestra-monitor) | 실시간 에이전트 모니터링 대시보드 | 에이전트 활동 시각화, 태스크 추적 |

### 에코시스템 구성도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Claude Code                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌─────────────────────────────────────────────┐   │
│  │  Serena MCP  │    │  Claude Code Native Multi-Agent Tools        │   │
│  │              │    │                                              │   │
│  │ - 코드 분석  │    │  Task()        - 서브에이전트 스폰           │   │
│  │ - 심볼 탐색  │    │  Agent()       - 에이전트 실행              │   │
│  │ - 리팩토링   │    │  TeamCreate()  - 팀 생성                    │   │
│  │              │    │  SendMessage() - 에이전트 간 통신           │   │
│  └──────────────┘    └──────────────────────┬──────────────────────┘   │
│                                             │                            │
│                                             ▼                            │
│                              ┌───────────────────────┐                  │
│                              │  Agent Orchestra      │                  │
│                              │  Monitor              │                  │
│                              │  - 실시간 대시보드    │                  │
│                              │  - 태스크 추적        │                  │
│                              │  - 이벤트 로그        │                  │
│                              └───────────────────────┘                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PDARR Workflow Commands (.claude/commands/)                      │  │
│  │  /dispatch → /prd → /analyze → /spec → /run → /check-code       │  │
│  │  → /reflect → /complete → /stage                                  │  │
│  │                                                                    │  │
│  │  + Superpowers Plugin (14 Skills)                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

자세한 내용은 [관련 프로젝트 가이드](docs/08-related-projects.md)를 참조하세요.

---

## License

MIT
