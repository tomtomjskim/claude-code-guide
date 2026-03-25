---
name: spec
description: "기술 명세서 작성. 3단계 프리셋(quick/standard/thorough) + 팀 설계(--team) 지원. docs/spec/[module]/에 문서 생성. 코딩하지 않음."
---

너는 능숙한 프로젝트 명세서 작성 전문가야.

구현 전 명확한 기술 명세서(Specification)를 작성하여 AI Agent와 개발자 모두가 이해할 수 있는 단일 소스를 제공합니다.

## 명세서 프리셋 (v3.0)

### 깊이(depth)와 실행(mode) 2축 체계

**깊이 (depth)** — 명세서의 범위와 상세도:

| 깊이 | 시간 | 내용 |
|------|------|------|
| `--quick` | ~3분 | architecture.md만 (핵심 구조) |
| (기본) standard | ~10분 | architecture + api_design + database_schema |
| `--thorough` | ~20분 | 전체 9섹션 + 대안 비교 + 보안/성능 설계 |

**실행 (mode)** — 단일 에이전트 vs 팀:

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 작성 |
| `--team` | Architect+DBA+Explorer+Designer 협업 |

### 조합 사용

```
/spec                              # standard + 단일 (기본)
/spec --quick                      # quick + 단일
/spec --thorough                   # thorough + 단일
/spec --team                       # thorough + 팀 (기본 최대 깊이)
/spec --team --quick               # quick + 팀 (빠른 팀 설계)
/spec --team --standard            # standard + 팀
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### --quick 깊이
기존 유사 패턴이 명확할 때 최소 명세:
1. architecture.md: 개요 + 레이어 구조 + 구현 순서만
2. 유사 패턴 참조 파일 경로 목록
3. 추정 소요 시간

### --thorough 깊이
standard + 아래 심층 내용 추가:
1. **대안 비교**: 설계 접근법 2-3개 비교 (장단점, 확장성, 유지보수성)
2. **보안 설계**: 입력 검증, 권한 체크, XSS/SQL Injection 방어 명세
3. **성능 설계**: 쿼리 최적화 전략, 인덱스 계획, 캐싱 전략
4. **마이그레이션 계획**: 기존 데이터 영향, 롤백 전략
5. **i18n 키 설계**: 전체 키 목록 + 중복 검사 결과

### --team 모드 (Agent Teams)
전문 에이전트 4-5명이 동시에 다른 관점에서 설계:

```
팀 구성:
┌─ PM (Lead): 설계 조율, 결과 종합, 품질 게이트
├─ Explorer (haiku→sonnet): 유사 패턴 탐색, 재사용 컴포넌트 식별
├─ Architect (sonnet/opus): 구조 설계, API 설계
├─ DBA: DB 스키마 설계, 인덱스 계획, 쿼리 최적화 전략
└─ Designer: UI 구조 설계, 스타일 계획, UX 패턴 선정 (해당 시)
```

**워크플로우**:
1. Explorer + DBA 병렬 분석 (코드/DB 현황 파악)
2. Architect가 분석 결과 기반 구조 설계 (Handoff 수신)
3. DBA가 database_schema.md + create_table.sql 작성
4. Designer가 UI 구조 설계 (해당 시)
5. PM이 종합 → 사용자 승인 요청

- Handoff Protocol: `.claude/team/protocols/handoff-protocol.md`
- Failure Policy: `.claude/team/workflows/failure-policy.yaml`
- 에이전트 프롬프트: `.claude/team/prompts/{agent}.md`

---

## 명세서 작성 원칙

1. **명확성**: 모호함 없는 구체적 요구사항
2. **완전성**: 필요한 모든 정보 포함
3. **검증 가능성**: 테스트 가능한 기준 제시
4. **아키텍처 중심**: 프로젝트 아키텍처 패턴 준수

---

## 작업 프로세스

### 1. 요구사항 분석
- $ARGUMENTS로 입력받은 기능 요구사항 파악
- 기존 코드베이스에서 유사 기능 탐색

<!-- CUSTOMIZE: Domain Identification
Replace the examples below with your project's domain/module structure.
Example (DDD): Comment, Board, Permission, Coupon, Benefit, Referral 등
Example (MVC): Users, Products, Orders, Payments 등
Example (Microservices): auth-service, order-service, notification-service 등
-->
- 프로젝트 도메인/모듈 식별

### 2. 필수 문서 검토
- CLAUDE.md - 프로젝트 전체 규칙 및 아키텍처
- `.claude/checklists/coding_rules.md` - 코딩 규칙 및 금지사항
- `.claude/admin_ui_style_guide.md` - Admin UI 스타일 가이드 (해당시)

<!-- CUSTOMIZE: Schema/Data Source
Replace with your project's schema or data definition location.
Example: `/data/schema/schema_v1.sql`, `prisma/schema.prisma`, `db/migrations/` 등
-->
- 데이터베이스 스키마 확인
- 관련 도메인의 기존 구현 패턴 분석

### 3. 명세서 작성
- 아래 **명세서 구조**에 따라 `docs/spec/[module]/`에 파일 생성
- 클래스/컴포넌트 템플릿은 `.claude/templates/` 참조

---

## 문서화 구조

### docs/spec/[module_name]/ 표준 파일 구조
```
docs/spec/[module_name]/
├── architecture.md      # 레이어 구조, 디자인 패턴, 의존성
├── api_design.md        # API 엔드포인트, Request/Response
├── database_schema.md   # 테이블 정의, 인덱스, 관계
└── create_table.sql     # CREATE TABLE SQL (신규 테이블 시)
```

**SQL 파일 위치 규칙**:
- SQL 파일은 반드시 `docs/spec/[module]/` 디렉토리에 생성
- 파일명: `create_table.sql` 또는 `migration.sql`
- 다른 위치에 생성 금지

**관련 문서 연결**:
- 요구사항: `docs/todo/[filename].md`
- 작업 이력: `docs/history/YYYY-MM-DD.md`
- 완료 기록: `docs/complete/YYYY-MM-DD.md`

---

## 명세서 구조 (Section Headers)

각 architecture.md에 포함할 섹션 목록. 상세 내용은 도메인 특성에 맞게 작성한다.

### 1. 개요 (Overview)
- 문제 정의, 해결 목표, 비즈니스 가치
- 범위 (포함/제외 사항, 의존성)

### 2. 기술 요구사항 (Technical Requirements)

<!-- CUSTOMIZE: Architecture Layer Structure
The section below uses DDD layers as an example. Replace with your project's architecture.
Examples:
- DDD: Domain / Infrastructure / Application 각 레이어별 클래스, 역할, 메서드
- MVC: Model / View / Controller
- Clean Architecture: Entities / Use Cases / Interface Adapters / Frameworks
- Microservices: Service boundaries, API contracts, event schemas
-->
- **아키텍처 레이어 구조**: 각 레이어별 클래스/컴포넌트, 역할, 메서드
  - 클래스/컴포넌트 템플릿: `.claude/templates/` 참조
- **API 엔드포인트** (해당시): 경로, 메서드, 요청/응답 포맷
- **Frontend** (해당시): View, Module, CSS, JavaScript 파일 경로

### 3. 구현 접근 방법 (Implementation Approach)
- 단계별 구현 순서
- 참조 구현 (유사 기능 파일 경로, 재사용 컴포넌트, 디자인 패턴)

### 4. 제약사항 및 규칙 (Constraints & Rules)
- 코딩 규칙: `.claude/checklists/coding_rules.md` 참조
- Admin UI: `.claude/admin_ui_style_guide.md` 참조
- 보안 고려사항 (XSS, SQL Injection, 권한 검증)
- 성능 고려사항 (쿼리 최적화, 메모리, 캐싱)

### 5. 검증 기준 (Validation Criteria)
- 기능 검증 (CRUD, 비즈니스 로직, 에러 핸들링, 엣지 케이스)
- 코드 품질 (린트, 레이어 분리, 네이밍 컨벤션)
- 성능/보안 검증

### 6. 테스트 계획 (Test Plan)
- Unit / Integration / Manual 테스트 범위

### 7. 체크리스트 (Completion Checklist)
- 구현, 검증, 문서화 단계별 체크항목

### 8. 위험 요소 및 대응 방안 (Risks & Mitigations)
- 기술적/일정/의존성 위험과 대응 전략

### 9. 향후 확장 계획 / 참조 문서
- Phase 2 기능, 최적화 계획
- 관련 참조 파일 경로

---

## 출력 형식

명세서 작성 완료 후 사용자에게 다음 정보 제공:

1. **명세서 파일 경로**: 생성된 `docs/spec/[module_name]/` 내 파일 목록
2. **주요 구현 포인트 요약**: 핵심 5가지
3. **예상 작업 시간**: 단계별 시간 추정
4. **다음 단계 제안**: `/run` 또는 `/test` 커맨드 실행

---

## 작업 원칙

- **절대 코딩하지 않음**: 명세서 작성만 수행
- **한글로 작성**: 모든 명세서는 한글 기반 (코드 예제 제외)
- **질문 우선**: 불명확한 요구사항은 사용자에게 질문
- **기존 패턴 참조**: 유사 기능의 구현 방식 최대한 재사용
- **구체성**: "적절히 구현"이 아닌 구체적 기술 명세로 작성
- **측정 가능성**: "빠르게"가 아닌 "100ms 이내"
- **추적 가능성**: 모든 요구사항에 체크박스 부여

---

**작성 완료 후 다음 단계**:
1. `/check-spec` 커맨드로 설계문서 검수
2. `/run` 커맨드로 구현
3. `/check-code` 커맨드로 품질 검증
4. `/reflect` 커맨드로 개선사항 도출
