# Claude Code 초기 셋업 체크리스트

## 개요

Claude Code를 효과적으로 사용하기 위한 초기 설정 가이드입니다.
이 문서를 따라 설정하면 일관된 개발 환경과 워크플로우를 구축할 수 있습니다.

---

## 1. 기본 환경 설정

### 1.1 Claude Code 설치 확인
```bash
# Claude Code 버전 확인
claude --version

# 업데이트 (필요시)
npm update -g @anthropic-ai/claude-code
```

### 1.2 글로벌 설정 파일
```
~/.claude/
├── settings.json       # 글로벌 설정
├── CLAUDE.md          # 글로벌 규칙/컨텍스트
└── team/              # 팀 오케스트레이션 설정 (선택)
    ├── agents.yaml
    ├── prompts/
    └── workflows/
```

### 1.3 settings.json 필수 설정
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

---

## 2. MCP 서버 설정 체크리스트

### 필수 MCP
- [ ] **Serena MCP** - 시맨틱 코드 분석/편집
  - 심볼 기반 코드 탐색
  - 정밀한 코드 수정
  - 참조 분석

### 권장 MCP
- [ ] **Team Orchestrator MCP** - 멀티 에이전트 오케스트레이션
- [ ] **GitHub MCP** - GitHub 연동 (PR, Issue)
- [ ] **Database MCP** - DB 직접 접근 (선택)

### MCP 설정 확인
```bash
# MCP 서버 연결 테스트
claude --mcp-test
```

---

## 3. 프로젝트별 설정

### 3.1 프로젝트 CLAUDE.md 생성
```
프로젝트루트/
├── .claude/
│   └── CLAUDE.md      # 프로젝트별 규칙
├── docs/
│   ├── requires/      # 요구사항
│   ├── spec/          # 설계 문서
│   ├── tasks/         # 태스크 관리
│   └── complete/      # 완료 문서
└── ...
```

### 3.2 CLAUDE.md 필수 섹션
- [ ] 프로젝트 개요
- [ ] 기술 스택
- [ ] 디렉토리 구조
- [ ] 코딩 컨벤션
- [ ] 문서화 규칙
- [ ] 커밋 규칙
- [ ] 에이전트 페르소나

---

## 4. 워크플로우 설정

### 4.1 개발 파이프라인 정의
```
요구사항 분석 → 설계 → 검수 → 구현 → 구현검수 → 문서화
```

### 4.2 각 단계별 체크리스트 준비
- [ ] 요구사항 체크리스트 (`docs/checklists/requirements.md`)
- [ ] 설계 체크리스트 (`docs/checklists/design.md`)
- [ ] 구현 체크리스트 (`docs/checklists/implementation.md`)
- [ ] 검수 체크리스트 (`docs/checklists/review.md`)

---

## 5. 문서화 구조 설정

### 5.1 docs 디렉토리 구조
```
docs/
├── requires/           # 요구사항 문서
│   └── REQ-001-feature-name.md
├── spec/               # 설계 문서
│   ├── architecture/
│   ├── api/
│   └── ui/
├── tasks/              # 진행중 태스크
│   └── TASK-001-feature-name.md
├── todo/               # 대기중 태스크
├── complete/           # 완료된 문서
│   └── DONE-001-feature-name.md
├── checklists/         # 체크리스트 템플릿
└── history/            # 작업 히스토리
    └── 2025-01-25-session.md
```

### 5.2 문서 템플릿 준비
- [ ] 요구사항 템플릿
- [ ] 설계 문서 템플릿
- [ ] 태스크 템플릿
- [ ] 세션 히스토리 템플릿

---

## 6. 에이전트 페르소나 설정

### 6.1 기본 페르소나
- [ ] **PM** - 요구사항 분석, 태스크 분해
- [ ] **Architect** - 시스템 설계
- [ ] **Developer** - 구현
- [ ] **QA** - 검수
- [ ] **Documenter** - 문서화

### 6.2 페르소나별 규칙
- 각 페르소나의 역할과 책임
- 산출물 정의
- 체크리스트

---

## 7. 커맨드/스킬 설정

### 7.1 권장 슬래시 커맨드
```
/init-project    - 프로젝트 초기화
/analyze-req     - 요구사항 분석
/design          - 설계 모드
/implement       - 구현 모드
/review          - 검수 모드
/document        - 문서화
/session-start   - 세션 시작 (히스토리 생성)
/session-end     - 세션 종료 (히스토리 저장)
```

### 7.2 스킬 설정
- Skills 디렉토리 위치: `~/.claude/skills/` 또는 프로젝트 `.claude/skills/`

---

## 8. 품질 규칙 설정

### 8.1 코드 품질
- [ ] 예시 코드 최소화 규칙
- [ ] 타입 안전성 (TypeScript strict)
- [ ] 에러 핸들링 규칙
- [ ] 테스트 커버리지 기준

### 8.2 문서 품질
- [ ] 문서 업데이트 규칙
- [ ] 코드-문서 동기화
- [ ] 버전 관리

---

## 9. 세션 관리

### 9.1 세션 시작 시
1. 이전 세션 히스토리 확인
2. 현재 진행중 태스크 확인
3. 오늘 작업 목표 설정

### 9.2 세션 종료 시
1. 작업 내용 히스토리 기록
2. 다음 작업 TODO 정리
3. 미완료 태스크 상태 업데이트

---

## 10. 검증

### 최종 체크리스트
- [ ] MCP 서버 연결 확인
- [ ] 글로벌 CLAUDE.md 설정 완료
- [ ] 프로젝트 CLAUDE.md 템플릿 준비
- [ ] 문서 디렉토리 구조 생성
- [ ] 체크리스트 템플릿 준비
- [ ] 에이전트 페르소나 정의
- [ ] 커맨드/스킬 설정

---

## 다음 단계

1. [MCP 상세 설정](01-mcp-configuration.md)
2. [커맨드/스킬 가이드](02-commands-skills.md)
3. [개발 파이프라인](03-development-pipeline.md)
4. [문서화 규칙](04-documentation-rules.md)
5. [에이전트 페르소나](05-agent-personas.md)
