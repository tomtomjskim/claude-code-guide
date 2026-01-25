# 프로젝트 구조 템플릿

## 개요

Claude Code를 효과적으로 사용하기 위한 표준 프로젝트 구조입니다.

---

## 1. 전체 구조

```
프로젝트/
├── .claude/                    # Claude Code 설정
│   ├── CLAUDE.md              # 프로젝트 규칙
│   ├── settings.json          # 프로젝트 MCP 설정 (선택)
│   └── skills/                # 프로젝트 스킬 (선택)
│
├── docs/                       # 문서
│   ├── requires/              # 요구사항
│   ├── spec/                  # 설계
│   │   ├── architecture/
│   │   ├── api/
│   │   └── ui/
│   ├── tasks/                 # 진행중 태스크
│   ├── todo/                  # 대기 태스크
│   ├── complete/              # 완료 문서
│   ├── checklists/            # 체크리스트
│   ├── history/               # 세션 히스토리
│   └── reference/             # 참조 문서
│
├── src/                        # 소스 코드
│   ├── components/            # 컴포넌트
│   ├── services/              # 서비스
│   ├── utils/                 # 유틸리티
│   ├── types/                 # 타입 정의
│   └── ...
│
├── tests/                      # 테스트
│   ├── unit/
│   └── integration/
│
├── scripts/                    # 스크립트
│
├── .env.example               # 환경변수 예시
├── package.json
├── tsconfig.json
└── README.md
```

---

## 2. .claude/ 디렉토리

### CLAUDE.md
프로젝트별 규칙과 컨텍스트를 정의합니다.

```markdown
# 프로젝트명

## 개요
[프로젝트 설명]

## 기술 스택
- Frontend: Next.js, TypeScript, Tailwind
- Backend: Node.js, Express
- Database: PostgreSQL

## 디렉토리 구조
[주요 디렉토리 설명]

## 코딩 컨벤션
[코딩 규칙]

## 문서화 규칙
[문서화 규칙]

## 커맨드
[사용 가능한 커맨드]
```

### settings.json (선택)
프로젝트별 MCP 설정이 필요한 경우:

```json
{
  "mcpServers": {
    "project-specific-mcp": {
      "command": "...",
      "args": ["..."]
    }
  }
}
```

---

## 3. docs/ 디렉토리 상세

### requires/ - 요구사항

```
docs/requires/
├── REQ-001-user-authentication.md
├── REQ-002-dashboard.md
└── REQ-003-settings.md
```

### spec/ - 설계 문서

```
docs/spec/
├── architecture/
│   ├── overview.md           # 전체 아키텍처
│   ├── auth-system.md        # 인증 시스템
│   └── data-flow.md          # 데이터 흐름
│
├── api/
│   ├── auth-api.md           # 인증 API
│   └── user-api.md           # 사용자 API
│
├── ui/
│   ├── design-system.md      # 디자인 시스템
│   ├── login-page.md         # 로그인 페이지
│   └── dashboard.md          # 대시보드
│
└── data/
    ├── user-schema.md        # 사용자 스키마
    └── session-schema.md     # 세션 스키마
```

### tasks/ - 진행중 태스크

```
docs/tasks/
├── TASK-001-login-ui.md
└── TASK-002-auth-api.md
```

### todo/ - 대기 태스크

```
docs/todo/
├── TODO-003-password-reset.md
└── TODO-004-social-login.md
```

### complete/ - 완료 문서

```
docs/complete/
├── DONE-001-project-setup.md
└── DONE-002-database-schema.md
```

### checklists/ - 체크리스트 템플릿

```
docs/checklists/
├── requirements-checklist.md
├── design-checklist.md
├── implementation-checklist.md
└── review-checklist.md
```

### history/ - 세션 히스토리

```
docs/history/
├── 2025-01-25-session-1.md
├── 2025-01-25-session-2.md
└── 2025-01-26-session-1.md
```

### reference/ - 참조 문서

```
docs/reference/
├── architecture-overview.md   # 아키텍처 개요
├── coding-conventions.md      # 코딩 컨벤션
├── style-guide.md            # 스타일 가이드
└── api-conventions.md        # API 규칙
```

---

## 4. 초기 설정 스크립트

### 프로젝트 초기화 스크립트
```bash
#!/bin/bash
# scripts/init-claude-structure.sh

# docs 디렉토리 생성
mkdir -p docs/{requires,spec/{architecture,api,ui,data},tasks,todo,complete,checklists,history,reference}

# .claude 디렉토리 생성
mkdir -p .claude

# 기본 파일 생성
touch docs/requires/.gitkeep
touch docs/tasks/.gitkeep
touch docs/todo/.gitkeep
touch docs/complete/.gitkeep
touch docs/history/.gitkeep

echo "Claude Code 문서 구조 생성 완료"
```

---

## 5. 체크리스트 템플릿 파일

### requirements-checklist.md
```markdown
# 요구사항 분석 체크리스트

## 기능 정의
- [ ] 핵심 기능 식별
- [ ] 사용자 스토리 작성
- [ ] 입력/출력 정의

## 범위
- [ ] 포함 범위 명확
- [ ] 제외 범위 명확
- [ ] MVP 정의

## 예외 케이스
- [ ] 에러 상황 정의
- [ ] 경계 조건 파악

## 성공 기준
- [ ] 완료 기준 명확
- [ ] 테스트 기준 정의
```

### design-checklist.md
```markdown
# 설계 검수 체크리스트

## 완전성
- [ ] 요구사항 반영
- [ ] 인터페이스 정의
- [ ] 에러 처리 고려

## 일관성
- [ ] 기존 아키텍처 일관성
- [ ] 네이밍 컨벤션
- [ ] 패턴 일관성

## 구현 가능성
- [ ] 기술적 가능성
- [ ] 리소스 적절성
```

### implementation-checklist.md
```markdown
# 구현 체크리스트

## 구현 전
- [ ] 설계 문서 확인
- [ ] 기존 코드 분석
- [ ] 인터페이스 확인

## 구현 중
- [ ] 설계 준수
- [ ] 타입 안전성
- [ ] 에러 핸들링

## 테스트
- [ ] 단위 테스트
- [ ] 엣지 케이스
- [ ] 에러 케이스
```

### review-checklist.md
```markdown
# 검수 체크리스트

## 요구사항
- [ ] 기능 충족
- [ ] 예외 처리
- [ ] 성능 기준

## 코드 품질
- [ ] 타입 안전성
- [ ] 에러 핸들링
- [ ] 중복 없음

## 테스트
- [ ] 테스트 존재
- [ ] 테스트 통과
- [ ] 커버리지
```

---

## 6. .gitignore 추가 항목

```gitignore
# Claude Code
.claude/settings.local.json

# 세션 히스토리 (민감 정보 포함 가능)
# docs/history/*.md  # 필요시 주석 해제
```

---

## 7. README.md 템플릿

```markdown
# 프로젝트명

## 개요
[프로젝트 설명]

## 기술 스택
- [기술 1]
- [기술 2]

## 시작하기

### 설치
```bash
npm install
```

### 개발 서버
```bash
npm run dev
```

## 문서
- [아키텍처](docs/reference/architecture-overview.md)
- [API 문서](docs/spec/api/)
- [코딩 컨벤션](docs/reference/coding-conventions.md)

## 개발 프로세스
이 프로젝트는 Claude Code와 함께 개발됩니다.
- 요구사항: `docs/requires/`
- 설계: `docs/spec/`
- 진행 태스크: `docs/tasks/`
- 완료: `docs/complete/`

## 라이선스
MIT
```

---

## 다음 단계

- [CLAUDE.md 템플릿](07-claude-md-template.md)
