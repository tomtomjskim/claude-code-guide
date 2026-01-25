# MCP 서버 설정 가이드

## 개요

MCP (Model Context Protocol)는 Claude Code의 기능을 확장하는 서버 프로토콜입니다.
이 문서는 권장 MCP 서버 설정과 활용법을 설명합니다.

---

## 1. 설정 파일 위치

```
~/.claude/settings.json        # 글로벌 MCP 설정
프로젝트/.claude/settings.json  # 프로젝트별 MCP 설정 (오버라이드)
```

---

## 2. 핵심 MCP 서버

### 2.1 Serena MCP (필수 권장)

시맨틱 코드 분석 및 편집을 위한 MCP 서버.

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

#### 주요 도구
| 도구 | 용도 | 사용 시점 |
|------|------|----------|
| `find_symbol` | 심볼(클래스, 함수) 검색 | 특정 코드 찾을 때 |
| `get_symbols_overview` | 파일 심볼 개요 | 파일 구조 파악 |
| `find_referencing_symbols` | 참조 찾기 | 영향도 분석 |
| `replace_symbol_body` | 심볼 본문 교체 | 함수/클래스 수정 |
| `replace_content` | 정규식 치환 | 부분 수정 |
| `search_for_pattern` | 패턴 검색 | 코드 패턴 찾기 |

#### Serena 활용 전략
```
1. 파일 구조 파악 → get_symbols_overview
2. 특정 심볼 찾기 → find_symbol
3. 영향도 분석 → find_referencing_symbols
4. 코드 수정 → replace_symbol_body / replace_content
```

### 2.2 Team Orchestrator MCP

멀티 에이전트 팀 오케스트레이션.

```json
{
  "mcpServers": {
    "team-orchestrator": {
      "command": "node",
      "args": ["/path/to/team-orchestrator-mcp/dist/index.js"]
    }
  }
}
```

#### 주요 도구
| 카테고리 | 도구 | 설명 |
|----------|------|------|
| Team | `team_init` | 팀 템플릿 초기화 |
| Team | `team_list_templates` | 템플릿 목록 |
| Agent | `agent_list` | 에이전트 목록 |
| Workflow | `workflow_run` | 워크플로우 실행 |
| Registry | `registry_search` | 템플릿 검색 |

---

## 3. 추가 MCP 서버 (선택)

### 3.1 GitHub MCP
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

### 3.2 Database MCP (PostgreSQL)
```json
{
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {
      "DATABASE_URL": "postgresql://user:pass@host:5432/db"
    }
  }
}
```

### 3.3 Filesystem MCP
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
  }
}
```

---

## 4. MCP 선택 가이드

### 프로젝트 유형별 권장 MCP

| 프로젝트 유형 | 필수 MCP | 권장 MCP |
|--------------|---------|---------|
| 웹 개발 | Serena | Team Orchestrator, GitHub |
| 데이터/ML | Serena | Database, Filesystem |
| 인프라/DevOps | Serena | Filesystem, GitHub |
| 풀스택 | Serena | Team Orchestrator, Database, GitHub |

### 도구 선택 흐름
```
코드 분석이 필요한가?
├── 빠른 키워드 검색 → Claude 기본 Grep, Glob
├── 심볼 기반 분석 → Serena MCP
└── 깊은 탐색 필요 → Task(Explore)

코드 수정이 필요한가?
├── 단순 텍스트 치환 → Claude 기본 Edit
├── 심볼 단위 수정 → Serena replace_symbol_body
└── 정규식 치환 → Serena replace_content

팀 협업이 필요한가?
├── 워크플로우 실행 → Team Orchestrator
└── 에이전트 스폰 → Task tool
```

---

## 5. 성능 최적화

### 5.1 MCP 우선순위
```
1. Serena → 코드 분석/수정 (가장 정확)
2. Claude 기본 도구 → 빠른 검색/읽기
3. Task 에이전트 → 복잡한 탐색
```

### 5.2 Serena 사용 팁
```markdown
DO:
- 심볼 이름을 알 때 find_symbol 사용
- 파일 구조 파악 시 get_symbols_overview 먼저
- 수정 전 find_referencing_symbols로 영향도 확인

DON'T:
- 전체 파일을 읽은 후 다시 심볼 분석
- 단순 텍스트 검색에 Serena 사용
- 작은 수정에 replace_symbol_body 사용
```

---

## 6. 트러블슈팅

### MCP 서버 연결 실패
```bash
# 1. MCP 서버 수동 실행 테스트
uvx --from serena-mcp serena --project .

# 2. 로그 확인
tail -f ~/.claude/logs/mcp.log

# 3. 권한 확인
ls -la ~/.claude/
```

### Serena 심볼 분석 실패
```bash
# 언어 서버 확인 (Python 예시)
pip install python-lsp-server

# TypeScript 예시
npm install -g typescript typescript-language-server
```

---

## 7. 설정 템플릿

### 웹 개발 프로젝트
```json
{
  "alwaysThinkingEnabled": true,
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

### 데이터 프로젝트
```json
{
  "alwaysThinkingEnabled": true,
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

---

## 다음 단계

- [커맨드/스킬 가이드](02-commands-skills.md)
- [개발 파이프라인](03-development-pipeline.md)
