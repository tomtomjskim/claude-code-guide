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
├── agents/            # 공식 서브에이전트 (v3.0, 15개)
└── team/              # 팀 오케스트레이션 설정 (선택)
    ├── agents.yaml    # 에이전트 정의 (v3.0, 16개)
    ├── prompts/       # 역할별 프롬프트 (16개)
    ├── workflows/     # 워크플로우 (8개 + failure-policy.yaml)
    ├── templates/     # 리뷰/세션 템플릿
    ├── artifacts/     # 산출물 (리뷰 히스토리 포함)
    ├── context/
    │   └── handoff-protocol.md   # 핸드오프 프로토콜 정의
    └── scripts/
        └── validate-system.sh    # 시스템 무결성 검증 스크립트
```

### 1.3 settings.json 필수 설정
```json
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

---

## 2. MCP 서버 설정 체크리스트

### 필수 MCP
- [ ] **Serena MCP** - 시맨틱 코드 분석/편집
  - 심볼 기반 코드 탐색
  - 정밀한 코드 수정
  - 참조 분석

### 권장 MCP
- [ ] **GitHub MCP** - GitHub 연동 (PR, Issue)
- [ ] **Database MCP** - DB 직접 접근 (선택)

> **멀티 에이전트 오케스트레이션**은 Claude Code 네이티브 도구(Task, Agent, TeamCreate, SendMessage)로 처리합니다. Team Orchestrator MCP는 더 이상 권장하지 않습니다.

### MCP 설정 확인
```bash
# MCP 서버 연결 테스트
claude --mcp-test
```

---

## 2.5 플러그인 설정 체크리스트

### 필수 플러그인
- [ ] **Superpowers** - TDD, 체계적 디버깅, 서브에이전트 개발
  ```bash
  claude plugin marketplace add obra/superpowers-marketplace
  claude plugin install superpowers@superpowers-marketplace
  ```

### 권장 플러그인: Codex (OpenAI)
- [ ] **Codex** - 코드 리뷰, 디버깅 위임, Review Gate
  ```bash
  claude plugin marketplace add openai/codex-plugin-cc
  claude plugin install codex@openai-codex
  /reload-plugins
  /codex:setup --enable-review-gate
  # 미인증 시: !codex login
  ```

### 플러그인 설정 확인
```bash
# 설치된 플러그인 확인
claude plugin list

# settings.json에서 활성화 확인
# "enabledPlugins": { "superpowers@superpowers-marketplace": true }
```

자세한 내용은 [추천 플러그인 가이드](09-recommended-plugins.md) 및 [Codex 플러그인 가이드](15a-codex-plugin.md)를 참조하세요.

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

> v3.0부터 각 페르소나는 **5-section 표준 템플릿**을 따릅니다: Opening / Working Mode / Focus On / Quality Checks / Return / Boundary

### 6.1 기본 페르소나 (Core Agents)
- [ ] **PM** - 요구사항 분석, 태스크 분해
- [ ] **Architect** - 시스템 설계
- [ ] **Developer** - 구현
- [ ] **QA** - 검수
- [ ] **DBA** - DB 스키마, 마이그레이션
- [ ] **Designer** - UI/UX 설계
- [ ] **Publisher** - 빌드/배포
- [ ] **Documenter** - 문서화
- [ ] **Explorer** - 코드 탐색, 영향도 분석

### 6.2 Specialist Reviewers (v3.0, 7개)
- [ ] **Security Reviewer** - "공격자에게 노출되면?"
- [ ] **Performance Reviewer** - "트래픽 10배면?"
- [ ] **Test Coverage Reviewer** - "이 테스트가 진짜 검증하나?"
- [ ] **Accessibility Reviewer** - "장애인도 쓸 수 있나?"
- [ ] **UX Reviewer** - "사용자가 혼란스럽지 않나?"
- [ ] **API Reviewer** - "1년 후에도 호환되나?"
- [ ] **Code Reviewer** - "코드 품질과 유지보수성이 충분한가?"

### 6.3 페르소나별 규칙
- 각 페르소나의 역할과 책임
- 산출물 정의
- 체크리스트
- 5-section 템플릿 준수 확인

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
- [ ] 시스템 무결성 검증: `bash ~/.claude/team/scripts/validate-system.sh`

---

## 11. v3.0 고급 설정

### 11.1 Handoff Protocol 설정

에이전트 간 컨텍스트를 구조화된 방식으로 전달하기 위한 프로토콜입니다.

```bash
# 핸드오프 프로토콜 정의 파일 위치
~/.claude/team/context/handoff-protocol.md
```

핸드오프 메시지는 다음 구조를 따릅니다:
```
HANDOFF: [송신 에이전트] → [수신 에이전트]
TASK: [태스크 설명]
CONTEXT: [현재까지의 작업 컨텍스트]
ARTIFACTS: [생성된 산출물 경로 목록]
NEXT_ACTION: [수신 에이전트가 수행해야 할 다음 작업]
CONSTRAINTS: [제약 사항 및 주의 사항]
```

- [ ] `handoff-protocol.md` 파일 생성 확인
- [ ] 핸드오프 구조 숙지
- [ ] 에이전트 페르소나에 핸드오프 수신/송신 규칙 추가

### 11.2 Failure Policy 설정

에이전트 실패 시 복구 전략을 정의합니다.

```bash
# 실패 정책 파일 위치
~/.claude/team/workflows/failure-policy.yaml
```

```yaml
# failure-policy.yaml 예시
failure_policy:
  retry:
    max_attempts: 3
    backoff: exponential
  escalate:
    threshold: 2          # 재시도 2회 실패 시 상위 에이전트로 에스컬레이션
    target: PM
  rollback:
    enabled: true
    checkpoint: last_successful_artifact
  circuit_breaker:
    enabled: true
    failure_threshold: 5  # 5회 연속 실패 시 차단
    recovery_timeout: 300 # 5분 후 재시도
```

- [ ] `failure-policy.yaml` 파일 생성
- [ ] retry/escalate/rollback/circuit-breaker 정책 설정
- [ ] 에이전트별 실패 처리 동작 검증

### 11.3 Model Routing 설정

작업 복잡도에 따라 적절한 모델을 동적으로 선택합니다.

| 모델 | 사용 시점 | 비용 |
|------|----------|------|
| claude-opus | 복잡한 설계/분석, thorough 리뷰 | 높음 |
| claude-sonnet | 일반 구현, standard 리뷰 (기본값) | 중간 |
| claude-haiku | 단순 태스크, quick 리뷰, 반복 작업 | 낮음 |

```bash
# 모델 라우팅 규칙은 agents.yaml에 정의
# agents.yaml 예시
agents:
  architect:
    model: claude-opus      # 설계는 항상 opus
  developer:
    model: claude-sonnet    # 구현은 sonnet (기본)
  reviewer_quick:
    model: claude-haiku     # 빠른 리뷰는 haiku
```

- [ ] `agents.yaml`에 에이전트별 model 필드 추가
- [ ] 리뷰 프리셋별 모델 매핑 확인 (quick→haiku, standard→sonnet, thorough→opus)
- [ ] "모델 [opus/haiku]로 [작업]" 커맨드 패턴 숙지

### 11.4 System Validation

설치 및 설정 완료 후 전체 시스템 무결성을 검증합니다.

```bash
# 시스템 검증 스크립트 실행
bash ~/.claude/team/scripts/validate-system.sh
```

검증 항목:
- [ ] agents.yaml 문법 오류 없음
- [ ] prompts/ 디렉토리 내 모든 파일 존재 확인 (16개)
- [ ] workflows/ 디렉토리 내 파일 존재 확인 (failure-policy.yaml 포함)
- [ ] handoff-protocol.md 존재 확인
- [ ] MCP 서버 연결 상태
- [ ] 에이전트 페르소나 5-section 템플릿 준수 여부

---

## 다음 단계

1. [MCP 상세 설정](01-mcp-configuration.md)
2. [커맨드/스킬 가이드](02-commands-skills.md)
3. [개발 파이프라인](03-development-pipeline.md)
4. [문서화 규칙](04-documentation-rules.md)
5. [에이전트 페르소나](05-agent-personas.md)
6. [v3.0 아키텍처](12-v3-architecture.md)
7. [핸드오프 & 실패 복구](13-handoff-and-failure.md)
