# CLAUDE.md 템플릿

## 개요

프로젝트 루트의 `.claude/CLAUDE.md` 파일 템플릿입니다.
이 파일은 Claude Code가 프로젝트 컨텍스트를 이해하는 데 사용됩니다.

---

## 기본 템플릿

```markdown
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
- 세션 시작 시 히스토리 파일 생성
- 진행 상황 실시간 기록
- 세션 종료 시 TODO 정리

---

## 에이전트 페르소나

### PM 모드
요청을 받으면:
1. 요구사항 명확화 질문 (체크리스트 기반)
2. 기존 코드 영향도 분석
3. 태스크 분해 및 계획 수립
4. docs/requires/ 문서 생성

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
4. docs/spec/ 문서 생성

### Developer 모드
구현 시:
1. 설계 문서 확인 필수
2. 설계 정확히 준수
3. 테스트 코드 함께 작성
4. docs/tasks/ 업데이트

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
- docs/requires/ 문서 생성

### /design [기능명]
설계 모드 진입
- 아키텍처/API/UI 설계
- docs/spec/ 문서 생성

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
- 새 히스토리 파일 생성

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
```

---

## 웹 개발 프로젝트용 확장

```markdown
## Next.js 특화 규칙

### App Router
- 페이지: `app/[route]/page.tsx`
- 레이아웃: `app/[route]/layout.tsx`
- API: `app/api/[route]/route.ts`

### 서버/클라이언트 컴포넌트
- 기본은 서버 컴포넌트
- 'use client'는 필요한 경우만
- 클라이언트 컴포넌트는 최소화

### 데이터 페칭
- 서버 컴포넌트에서 직접 fetch
- 클라이언트는 React Query 또는 SWR

---

## API 규칙

### 엔드포인트 구조
```
GET    /api/[resource]          # 목록
GET    /api/[resource]/[id]     # 상세
POST   /api/[resource]          # 생성
PATCH  /api/[resource]/[id]     # 수정
DELETE /api/[resource]/[id]     # 삭제
```

### 응답 형식
```typescript
// 성공
{
  success: true,
  data: { ... }
}

// 에러
{
  success: false,
  error: {
    code: "ERROR_CODE",
    message: "에러 메시지"
  }
}
```

---

## 데이터베이스 규칙

### Prisma 스키마
- 모델명: PascalCase
- 필드명: camelCase
- 관계: 명시적 정의

### 마이그레이션
- 작은 단위로 마이그레이션
- 롤백 가능하게 작성
```

---

## 데이터/ML 프로젝트용 확장

```markdown
## Python 특화 규칙

### 프로젝트 구조
```
src/
├── data/           # 데이터 처리
├── models/         # ML 모델
├── features/       # 피처 엔지니어링
├── utils/          # 유틸리티
└── pipelines/      # 파이프라인
```

### 코딩 컨벤션
- PEP 8 준수
- Type hints 필수
- Docstring 필수

### 노트북 규칙
- 탐색용으로만 사용
- 프로덕션 코드는 .py로 이동
- 결과 저장 시 docs/에 기록
```

---

## 마이크로서비스용 확장

```markdown
## 서비스 구조

### 서비스별 독립 문서
```
services/
├── auth-service/
│   └── docs/
├── user-service/
│   └── docs/
└── api-gateway/
    └── docs/
```

### 통합 문서
```
docs/
├── architecture/
│   └── microservices-overview.md
├── api/
│   └── api-gateway.md
└── deployment/
    └── k8s-setup.md
```
```

---

## 사용 방법

1. 위 템플릿을 `.claude/CLAUDE.md`에 복사
2. 프로젝트에 맞게 수정
3. 기술 스택, 구조, 컨벤션 업데이트
4. 필요한 섹션 추가/제거

---

## 팁

### 컨텍스트 최적화
- 필수 정보만 포함
- 너무 길면 분리 (참조 문서로)
- 자주 변경되는 정보는 별도 파일

### 효과적인 규칙
- 명확하고 구체적으로
- 예시보다 규칙 우선
- 체크리스트 활용
