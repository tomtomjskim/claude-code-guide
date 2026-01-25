# Claude Code 셋업 가이드

Claude Code를 효과적으로 사용하기 위한 종합 가이드입니다.

---

## 문서 목록

| 문서 | 설명 |
|------|------|
| [00. 셋업 체크리스트](00-setup-checklist.md) | 초기 설정 체크리스트 |
| [01. MCP 설정](01-mcp-configuration.md) | MCP 서버 설정 가이드 (Serena 등) |
| [02. 커맨드/스킬](02-commands-skills.md) | 슬래시 커맨드 및 스킬 가이드 |
| [03. 개발 파이프라인](03-development-pipeline.md) | PRD 분석 → 설계 → 검수 → 구현 파이프라인 |
| [04. 문서화 규칙](04-documentation-rules.md) | 세션 독립적 문서화 규칙 |
| [05. 에이전트 페르소나](05-agent-personas.md) | PM, Architect, Developer 등 페르소나 |
| [06. 프로젝트 구조](06-project-structure.md) | 표준 프로젝트 구조 템플릿 |
| [07. CLAUDE.md 템플릿](07-claude-md-template.md) | 프로젝트 CLAUDE.md 템플릿 |

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
# 문서 구조 생성
mkdir -p docs/{requires,spec/{architecture,api,ui},tasks,todo,complete,checklists,history}
mkdir -p .claude

# CLAUDE.md 생성 (07-claude-md-template.md 참조)
touch .claude/CLAUDE.md
```

### 3. 첫 세션
```
/session-start
→ 히스토리 파일 생성

"로그인 기능 구현해줘"

/analyze 로그인 기능
→ 체크리스트 기반 질문
→ docs/requires/REQ-001-login.md 생성

/design login
→ 아키텍처/API/UI 설계
→ docs/spec/ 문서 생성

/implement login
→ 설계 기반 구현

/review login
→ 체크리스트 기반 검수

/session-end
→ 히스토리 저장
```

---

## 핵심 개념

### 파이프라인
```
요구사항 분석 → 설계 → 설계검수 → 구현 → 구현검수 → 문서화
```

### 문서 흐름
```
docs/requires/ → docs/spec/ → docs/tasks/ → docs/complete/
```

### 에이전트 역할
| 에이전트 | 역할 |
|---------|------|
| PM | 요구사항 분석, 태스크 분해 |
| Explorer | 코드 탐색, 영향도 분석 |
| Architect | 시스템 설계 |
| Developer | 구현 |
| QA | 검수 |
| Documenter | 문서화 |

### 세션 관리
- 시작: 이전 히스토리 확인, 새 히스토리 생성
- 진행: 실시간 기록
- 종료: 히스토리 저장, TODO 정리

---

## 권장 사항

### MCP
- **Serena**: 필수 - 시맨틱 코드 분석
- **Team Orchestrator**: 권장 - 멀티 에이전트

### 문서화
- 예시 코드 최소화
- 다이어그램 활용 (mermaid)
- 세션 히스토리 필수

### 체크리스트
- 요구사항 분석 체크리스트
- 설계 검수 체크리스트
- 구현 검수 체크리스트

---

## 관련 링크

- [Team Orchestrator MCP](https://github.com/tomtomjskim/team-orchestrator-mcp)
- [Serena MCP](https://github.com/serena-ai/serena-mcp)
- [Claude Code 공식 문서](https://docs.anthropic.com/claude-code)
