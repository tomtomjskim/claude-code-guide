# [프로젝트명]

## 프로젝트 개요
[프로젝트에 대한 간략한 설명]

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| Language | TypeScript 5.x |
| Frontend | Next.js 14, React 18 |
| Styling | Tailwind CSS |
| Backend | Node.js, Express (또는 Next.js API Routes) |
| Database | PostgreSQL |
| ORM | Prisma |
| Testing | Jest, React Testing Library |

---

## 프로젝트 구조

```
src/
├── app/                 # Next.js App Router
├── components/          # React 컴포넌트
│   ├── ui/             # 기본 UI 컴포넌트
│   └── features/       # 기능별 컴포넌트
├── lib/                 # 유틸리티
├── services/            # 비즈니스 로직
├── types/               # TypeScript 타입
└── hooks/               # Custom hooks

docs/
├── requires/            # 요구사항 (REQ-XXX)
├── spec/               # 설계 문서
├── tasks/              # 진행중 태스크 (TASK-XXX)
├── complete/           # 완료 문서 (DONE-XXX)
└── history/            # 세션 히스토리
```

---

## 코딩 컨벤션

### TypeScript
- strict 모드 필수
- any 타입 사용 금지
- 명시적 반환 타입 선언
- interface 우선 (type은 union/intersection에만)

### 네이밍
- 컴포넌트: PascalCase
- 함수/변수: camelCase
- 상수: UPPER_SNAKE_CASE
- 파일: kebab-case (컴포넌트는 PascalCase)

### 컴포넌트
- 함수형 컴포넌트만 사용
- Props는 interface로 정의
- 한 파일에 한 컴포넌트

### 에러 핸들링
- try-catch 필수 (비동기)
- 적절한 에러 메시지
- 사용자 친화적 에러 표시

---

## 문서화 규칙

### 문서 경로
- 요구사항: `docs/requires/REQ-XXX-[기능명].md`
- 설계: `docs/spec/[분류]/[기능명].md`
- 태스크: `docs/tasks/TASK-XXX-[기능명].md`
- 완료: `docs/complete/DONE-XXX-[기능명].md`
- 히스토리: `docs/history/YYYY-MM-DD-session-N.md`

### 예시 코드 규칙
- 인터페이스/타입 정의만 포함
- 구현 코드는 최소화
- 다이어그램으로 대체 가능하면 다이어그램 사용

### 세션 관리
- 세션 히스토리는 사용자가 요청했거나 작업 규모상 필요한 경우에만 생성
- 진행 상황은 필요한 만큼 간결하게 기록
- 세션 종료 시 TODO는 현재 요청, 문서상 backlog, 배포/검증 전용 항목을 분리

### 컨텍스트 오염 방지
- handoff, backlog, roadmap, gap-review, brainstorm, retrospective 문서는 사용자가 명시적으로 요청했거나 현재 구현에 특정 설계 문서가 필요할 때만 참조한다.
- 해당 문서를 참조할 때는 먼저 참조 이유와 범위를 밝힌다.
- 브리핑에서는 다음 세 가지를 분리한다:
  - 현재 사용자 요청으로 진행 중인 작업
  - 문서에서 발견한 backlog
  - 배포/검증 전용 항목
- 문서상 backlog를 사용자 확인 없이 다음 작업 큐로 승격하지 않는다.
- 기본 다음 작업 브리핑은 최신 사용자 지시와 실제 커밋/diff/worktree 상태를 기준으로 한다.
- 알려진 파일, PR, branch, error payload가 있으면 targeted read를 우선한다.
- 알려진 대상을 이유 없이 broad scan으로 확장하지 않는다.
- 새 docs, reports, screenshots, scripts, tests 같은 durable artifact는 사용자 요청 또는 승인된 계획의 정확한 경로가 있을 때만 만든다.
- 임시 검증 증거와 후속 아이디어는 새 문서보다 최종 응답, PR description, 기존 task 문서에 먼저 남긴다.
- 단순 명령이 quoting이나 syntax 문제로 실패하면 같은 무거운 도구 경로를 반복하지 않고 가장 단순한 동등 경로로 바꾼다.

---

## 에이전트 페르소나

### PM 모드
요청을 받으면:
1. 요구사항 명확화 질문 (체크리스트 기반)
2. 기존 코드 영향도 분석
3. 태스크 분해 및 계획 수립
4. 필요 시 docs/requires/ 문서 생성 후보 제안

### Explorer 모드
코드 분석 시:
1. Serena MCP로 구조 파악
2. 관련 코드 식별
3. 영향도 분석
4. 패턴/컨벤션 파악

### Architect 모드
설계 시:
1. 요구사항 문서 확인
2. 아키텍처 설계 (mermaid 다이어그램)
3. 인터페이스/타입 정의
4. 필요 시 docs/spec/ 문서 생성 후보 제안

### Developer 모드
구현 시:
1. 설계 문서 확인 필수
2. 설계 정확히 준수
3. 테스트 코드 함께 작성
4. 필요 시 기존 docs/tasks/ 업데이트

### QA 모드
검수 시:
1. 체크리스트 기반 검토
2. 요구사항 충족 확인
3. 코드 품질 검사
4. 피드백 또는 승인

---

## 커스텀 커맨드

### /analyze [요구사항]
요구사항 분석 모드 진입
- 체크리스트 기반 질문
- 영향도 분석
- 필요 시 docs/requires/ 문서 생성 후보 제안

### /design [기능명]
설계 모드 진입
- 아키텍처/API/UI 설계
- 필요 시 docs/spec/ 문서 생성 후보 제안

### /implement [태스크]
구현 모드 진입
- 설계 문서 기반 구현
- 테스트 코드 작성

### /review [대상]
검수 모드 진입
- 체크리스트 기반 검토
- 피드백 제공

### /session-start
새 세션 시작
- 이전 히스토리 확인
- 진행중 태스크 확인
- 필요 시 새 히스토리 파일 생성 후보 제안

### /session-end
세션 종료
- 히스토리 저장
- TODO 정리

---

## 체크리스트

### 요구사항 분석 체크리스트
- 핵심 기능 정의
- 입력/출력 정의
- 예외 케이스 파악
- 성공 기준 정의

### 설계 체크리스트
- 요구사항 반영
- 인터페이스 정의
- 에러 처리 고려
- 기존 아키텍처 일관성

### 구현 체크리스트
- 설계 문서 준수
- 타입 안전성
- 에러 핸들링
- 테스트 코드

### 검수 체크리스트
- 요구사항 충족
- 코드 품질
- 테스트 통과
- 문서 업데이트

---

## UI/UX 스타일 참조

### 디자인 시스템
[디자인 시스템 링크 또는 설명]

### 컴포넌트 라이브러리
- shadcn/ui 사용
- 커스텀 컴포넌트는 ui/ 디렉토리

### 스타일 규칙
- Tailwind CSS 사용
- 반응형 필수 (mobile-first)
- 다크모드 지원

---

## 참고 문서
- [아키텍처 개요](docs/reference/architecture-overview.md)
- [API 규칙](docs/reference/api-conventions.md)
- [코딩 컨벤션](docs/reference/coding-conventions.md)
