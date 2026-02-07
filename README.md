# Claude Code 셋업 가이드

**Claude Code를 효과적으로 사용하기 위한 종합 가이드 및 템플릿**

---

## 개요

이 레포지토리는 Claude Code 초기 설정부터 팀 워크플로우까지 모든 것을 다룹니다.

### 주요 내용
- MCP 서버 설정 (Serena, Team Orchestrator 등)
- 개발 파이프라인 (요구사항 → 설계 → 검수 → 구현)
- 문서화 규칙 및 템플릿
- 에이전트 페르소나 정의
- 체크리스트 기반 워크플로우
- 세션 히스토리 관리

---

## 빠른 시작

### 1. 글로벌 설정

```bash
# ~/.claude/settings.json
{
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
mkdir -p docs/{requires,spec/{architecture,api,ui},tasks,todo,complete,checklists,history}
mkdir -p .claude
```

### 3. CLAUDE.md 설정

```bash
# 템플릿 복사
cp templates/CLAUDE.md /your/project/.claude/CLAUDE.md

# 프로젝트에 맞게 수정
```

---

## 문서 목록

| 문서 | 설명 |
|------|------|
| [셋업 체크리스트](docs/00-setup-checklist.md) | 초기 설정 체크리스트 |
| [MCP 설정](docs/01-mcp-configuration.md) | Serena, Team Orchestrator 등 MCP 설정 |
| [커맨드/스킬](docs/02-commands-skills.md) | /analyze, /design, /implement 커맨드 |
| [개발 파이프라인](docs/03-development-pipeline.md) | PRD → 설계 → 검수 → 구현 |
| [문서화 규칙](docs/04-documentation-rules.md) | 세션 독립적 문서화 |
| [에이전트 페르소나](docs/05-agent-personas.md) | PM, Architect, Developer, QA |
| [프로젝트 구조](docs/06-project-structure.md) | 표준 프로젝트 구조 |
| [CLAUDE.md 템플릿](docs/07-claude-md-template.md) | 프로젝트 설정 템플릿 |
| [추천 플러그인](docs/09-recommended-plugins.md) | 추천 플러그인 설치 및 활용 가이드 |
| [코드 리뷰 시스템](docs/10-code-review-system.md) | 전문 리뷰어 6명, 6단계, 3프리셋, 하이브리드 모드 |

---

## 핵심 개념

### 개발 파이프라인

```
┌──────────┐   ┌──────┐   ┌────────┐   ┌──────┐   ┌────────┐   ┌───────┐
│ 요구사항  │──▶│ 설계 │──▶│설계검수│──▶│ 구현 │──▶│구현검수│──▶│ 완료  │
│   분석   │   │      │   │        │   │      │   │        │   │       │
└──────────┘   └──────┘   └────────┘   └──────┘   └────────┘   └───────┘
     │             │                       │                       │
     ▼             ▼                       ▼                       ▼
 requires/      spec/                   tasks/                 complete/
```

### 문서 구조

```
docs/
├── requires/           # 요구사항 (REQ-XXX)
├── spec/               # 설계
│   ├── architecture/   # 아키텍처
│   ├── api/           # API
│   └── ui/            # UI/UX
├── tasks/             # 진행중 (TASK-XXX)
├── todo/              # 대기중
├── complete/          # 완료 (DONE-XXX)
├── checklists/        # 체크리스트 템플릿
└── history/           # 세션 히스토리
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

### 세션 관리

```markdown
/session-start
→ 이전 히스토리 확인
→ 진행중 태스크 확인
→ 새 히스토리 파일 생성

[작업 진행]

/session-end
→ 히스토리 저장
→ TODO 정리
```

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

### 권장
- **Team Orchestrator MCP** - 멀티 에이전트 오케스트레이션

### 설정 예시
```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    },
    "team-orchestrator": {
      "command": "node",
      "args": ["/path/to/team-orchestrator-mcp/dist/index.js"]
    }
  }
}
```

---

## 추천 플러그인

### 필수
- **[Superpowers](https://github.com/obra/superpowers)** - TDD, 체계적 디버깅, 서브에이전트 개발 워크플로우
  - 설치: `claude plugin marketplace add obra/superpowers-marketplace && claude plugin install superpowers@superpowers-marketplace`
  - 주요 기능: brainstorming, write-plan, execute-plan, TDD, systematic-debugging
  - 42,000+ GitHub Stars, Anthropic 공식 마켓플레이스 등록

### 추천 (추가 검토)
- **[Context7](https://github.com/upstash/context7)** - 최신 문서 검색/참조
- **[Superpowers Lab](https://github.com/obra/superpowers-lab)** - 실험적 스킬 확장
- **[Superpowers Chrome](https://github.com/obra/superpowers-chrome)** - 브라우저 직접 제어

자세한 내용은 [추천 플러그인 가이드](docs/09-recommended-plugins.md)를 참조하세요.

---

## 사용 예시

### 새 기능 개발

```
사용자: "로그인 기능 구현해줘"

/analyze 로그인 기능
→ 체크리스트 기반 질문
   - "이메일/비밀번호 로그인인가요?"
   - "소셜 로그인이 필요한가요?"
→ docs/requires/REQ-001-login.md 생성

/design login
→ 아키텍처 설계 (mermaid 다이어그램)
→ API 설계 (인터페이스 정의)
→ docs/spec/ 문서 생성

/implement login
→ 설계 문서 기반 구현
→ 테스트 코드 작성

/review login
→ 체크리스트 기반 검수
→ 피드백 또는 승인

→ docs/complete/DONE-001-login.md 생성
```

---

## 관련 프로젝트

### MCP 서버

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [Serena MCP](https://github.com/serena-ai/serena-mcp) | 시맨틱 코드 분석/편집 | 필수 - 코드 탐색, 심볼 분석, 리팩토링 |
| [Team Orchestrator MCP](https://github.com/tomtomjskim/team-orchestrator-mcp) | 멀티 에이전트 오케스트레이션 | 권장 - 팀 템플릿, 워크플로우, 에이전트 관리 |

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
│  ┌──────────────┐    ┌─────────────────────┐    ┌───────────────────┐  │
│  │  Serena MCP  │    │ Team Orchestrator   │    │  Agent Orchestra  │  │
│  │              │    │       MCP           │    │     Monitor       │  │
│  │ - 코드 분석  │    │                     │    │                   │  │
│  │ - 심볼 탐색  │    │ - 팀 템플릿         │───▶│ - 실시간 대시보드 │  │
│  │ - 리팩토링   │    │ - 워크플로우 엔진   │    │ - 태스크 추적     │  │
│  │              │    │ - 에이전트 관리     │    │ - 이벤트 로그     │  │
│  └──────────────┘    │ - 이벤트 발행       │    └───────────────────┘  │
│                      └─────────────────────┘                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

자세한 내용은 [관련 프로젝트 가이드](docs/08-related-projects.md)를 참조하세요.

---

## License

MIT
