# Claude Code Workflow Commands 구축 가이드

프로젝트에 체계적인 AI 개발 워크플로우를 구축하기 위한 종합 가이드.
이 문서 하나로 동일한 구조를 새 프로젝트에 셋업할 수 있다.

---

## 1. 개요

### 이 구조가 해결하는 문제

| 문제 | 해결 |
|------|------|
| 단순 버그에 과도한 분석 실행 | `/dispatch`가 복잡도 판단 후 최적 경로 라우팅 |
| 대규모 작업에 단일 Agent 한계 | PRD→Analyze 2단계 판단 후 팀 Agent 병렬 실행 |
| 검수 커맨드 중복/혼란 | 역할별 명확 분리 (설계검수 vs 코드검수) |
| 작업 후 학습 부재 | Reflect→Memory 저장으로 세션 간 학습 지속 |
| 산출물 산재 | Complete가 docs/complete/로 통합 정리 |

### 핵심 철학

**PDARR 사이클**: Plan → Document → Act → Review → Reflect

모든 작업은 이 사이클의 전체 또는 일부를 거친다.
단순 작업은 Act만, 복잡한 작업은 전체 사이클을 돌린다.
`/dispatch`가 작업 크기에 맞는 사이클 범위를 결정한다.

---

## 2. 전체 아키텍처

### 커맨드 전체 맵

```
[시작점]
  /dispatch ─── 스마트 라우터 (복잡도 판단 → 경로 선택)

[계획 단계 - Plan]
  /prd ────── 요구사항 문서 + 복잡도 1차 판단
  /analyze ── 코드베이스 분석 + 실행전략 2차 판단
  /spec ───── 기술 명세서 작성

[실행 단계 - Act]
  /test ───── TDD 테스트 케이스 작성
  /run ────── 구현 (Orchestrator-Worker 패턴)

[검증 단계 - Review]
  /check-spec ── 설계문서 ↔ 코드베이스 일관성 검수
  /check-code ── 코드 품질 검수 (REVIEW 단계 통합)
  /qa-test ───── 종합 QA 자동화

[회고 단계 - Reflect]
  /reflect ──── 자기성찰 + Memory 저장
  /complete ─── 작업 완료 정리 + docs/complete 통합

[유틸리티]
  /stage ────── Git 스테이징 + 커밋 메시지 제안
  /flow ─────── 현재 컨텍스트 정리 (상태 파악용)
  /workflow ─── 통합 오케스트레이터 (PDARR 전체 자동화)
```

### 라우팅 흐름도

```
사용자 요청
    │
    ▼
[/dispatch] ← 30초 이내 판단
    │
    ├─ Trivial ─→ 직접 수정 (커맨드 불필요)
    │
    ├─ Simple ──→ /run 직행
    │                └─→ /check-code → /stage
    │
    ├─ Medium ──→ /analyze (2차 판단 포함)
    │                ├─ 단일 Agent → /run
    │                └─ 병렬 필요 → /run (병렬 Task 2-3개)
    │                     └─→ /check-code → /stage
    │
    ├─ Complex ─→ /prd (1차 판단 포함)
    │                └─→ /analyze (2차 판단 포함)
    │                     ├─ 팀 Agent → /workflow (팀 모드)
    │                     └─ 단일 OK → /spec → /run
    │                          └─→ /check-code → /reflect → /complete → /stage
    │
    └─ Review ──→ /check-spec 또는 /check-code
```

---

## 3. 2단계 판단 시스템

이 구조의 핵심. 작업 규모에 맞는 실행 전략을 자동 결정한다.

### 1차 판단: PRD 단계

PRD 작성 시 "복잡도 사전 평가" 섹션을 포함한다.
요구사항 텍스트 기반으로 예상 규모를 추정.

```markdown
## 복잡도 사전 평가 (1차 판단)

### 작업 규모 추정
- 예상 파일 변경: {N}개
- 영향 도메인: {도메인 목록}
- 레이어 관여: {어떤 레이어들}
- 신규 테이블 필요: Y/N

### 복잡도 판정
- [ ] Trivial / Simple / Medium / Complex

### 병렬화 가능성
- 독립 작업 단위: {식별된 목록}
- 추천: 단일 Agent / 병렬 Task / 팀 Agent
```

**판단 기준 (프로젝트에 맞게 조정):**

| 지표 | Simple | Medium | Complex |
|------|--------|--------|---------|
| 파일 수 | 1-2개 | 3-5개 | 6개+ |
| 레이어 수 | 1개 | 1-2개 | 3개+ |
| 프론트+백엔드 | 한쪽만 | 한쪽 주력 | 양쪽 동시 |
| 신규 테이블 | 없음 | 0-1개 | 2개+ |

### 2차 판단: Analyze 단계

코드베이스 실제 분석 후 1차 판단을 보정.
파일 간 의존성, 병렬화 가능한 독립 단위를 구체적으로 식별.

```markdown
## 실행 전략 추천 (2차 판단)

### 1차 대비 보정
- 1차: Medium → 2차: Complex (이유: 숨은 의존성 발견)

### 병렬화 분석
- 독립 단위 A: Backend (Domain + Infra)
- 독립 단위 B: Frontend (View + SCSS + JS)
- 순차 필수: DB 스키마 → Domain

### 추천 실행 전략
| 전략 | 적합도 | 이유 |
|------|--------|------|
| 단일 Agent | ★☆☆ | 파일 8개, 양쪽 동시 |
| 팀 Agent | ★★★ | 백엔드/프론트 병렬 가능 |

### 추천 팀 구성
- backend-dev: Domain/Infra/App
- frontend-dev: API/View/SCSS/JS
- reviewer: 전체 검수
```

### Workflow가 판단을 활용하는 방식

`/workflow` 실행 시 Step 0에서 기존 판단 결과를 먼저 확인:

| PRD 있음 | Analyze 있음 | 행동 |
|---------|-------------|------|
| O | O | 판단 결과 바로 활용 → 팀 구성 즉시 결정 |
| O | X | 1차 판단 활용 → Analyze 실행 |
| X | X | 자체 분석 후 판단 |

---

## 4. 각 커맨드 상세

### /dispatch - 스마트 디스패처

**역할**: 모든 작업의 시작점. 30초 이내 판단 후 최적 경로 안내.

**핵심 로직**:
1. 키워드 분석 (버그→Simple, 시스템→Complex)
2. 기존 PRD/Analyze 결과 있는지 확인
3. 관련 파일 수 빠르게 추정
4. 복잡도 판정 → 경로 추천 → 사용자 확인

**특징**: 코딩 금지, 판단과 라우팅만 수행, 사용자 동의 후 진행.

---

### /prd - 요구사항 문서

**역할**: 요구사항 구조화 + 복잡도 1차 판단.

**산출물**: `docs/prd/{프로젝트명}/prd.md`

**핵심 섹션**:
- 개요, 배경, 요청사항, 비즈니스 로직
- **복잡도 사전 평가 (1차 판단)** ← 핵심 추가 섹션
- 우선순위 (P0/P1/P2)

**다음 단계**: `/analyze` → `/spec` → `/run`

---

### /analyze - 코드베이스 분석

**역할**: 실제 코드 분석 + 실행전략 2차 판단. 코딩 금지.

**산출물**: 분석 브리핑 (문서화 위치는 분석 유형별 상이)

**핵심 출력**:
- 원인 분석 (Root Cause), 접근 방법, 영향도
- **실행 전략 추천 (2차 판단)** ← 핵심 추가 출력
  - 1차 판단 보정, 병렬화 분석, 팀 구성 추천

**다음 단계**: `/spec` 또는 `/run` 또는 `/workflow` (판단 결과에 따라)

---

### /spec - 기술 명세서

**역할**: 구현 전 기술 설계 문서 작성. 코딩 금지.

**산출물**: `docs/spec/{모듈}/`
- `architecture.md` - 레이어별 설계
- `api_design.md` - API 엔드포인트
- `database_schema.md` - DB 스키마
- `create_table.sql` - 신규 테이블 SQL

**다음 단계**: `/test` → `/run`

---

### /test - TDD 테스트 케이스

**역할**: 구현 전 테스트 케이스 작성 (Red 단계).

**산출물**: `/tests/{도메인}/` 테스트 파일들

**다음 단계**: `/run` (Green-Refactor 사이클)

---

### /run - 구현

**역할**: Orchestrator-Worker 패턴으로 실제 코드 구현.

**작업 순서**:
1. Pre-Flight Check (문서/컨텍스트 확인)
2. Sequential: DB → Domain → Infrastructure → Application
3. Parallel: API + Frontend 동시
4. Post: autoload 업데이트, 테스트 실행

**다음 단계**: `/check-code` → `/reflect`

---

### /check-spec - 설계문서 검수

**역할**: 설계문서 ↔ 코드베이스 일관성 검증. 구현 전 사용.

**검수 항목**:
- 요구사항/로직 완전성
- 파일/경로 컨벤션
- API 패턴, DB 스키마, JS/SCSS 규칙

---

### /check-code - 코드 품질 검수

**역할**: 구현 완료 코드의 품질 검증. PDARR의 REVIEW 단계 통합.

**실행 모드**:
- `/check-code {모듈}` - 특정 모듈 검수
- `/check-code --context` - 현재 세션 작업 전체 검수
- `/check-code --full {모듈}` - 설계문서 대조 + 코드 검수

**검수 범위**: PHP 문법, 보안, SQL, SCSS, i18n, DDD 아키텍처

**다음 단계**: Critical 0건 → `/reflect` | Critical 1+건 → 수정 후 재검수

---

### /qa-test - 종합 QA 자동화

**역할**: 변경 파일 난이도별 자동 QA.

**난이도**: Minimal(문법만) → Basic(+품질) → Standard(+UI/시나리오) → Full(+E2E)

**산출물**: `docs/qa-reports/YYYY-MM-DD_{기능명}.md`

---

### /reflect - 자기성찰

**역할**: Self-Critique + 패턴 인식 + Memory 저장.

**프로세스**: Context 수집 → Self-Critique → 패턴 분석 → 신뢰도 평가 → Memory 저장

**산출물**:
- `docs/complete/YYYY-MM-DD.md` - 완료 기록
- Memory 파일 (세션 간 학습 지속)

---

### /complete - 작업 완료 정리

**역할**: 산재된 문서를 `docs/complete/`로 통합.

**프로세스**:
1. 관련 문서 탐색
2. `docs/complete/{날짜}_{모듈}/` 생성
3. 설계문서 → `spec_summary.md`로 압축
4. README.md 생성
5. 불필요 파일 정리 (사용자 승인 후)
6. `summary.md` 업데이트

---

### /stage - Git 스테이징

**역할**: 작업 파일 자동 식별 → git add → 커밋 메시지 제안.

**커밋 컨벤션**: `feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`

---

### /flow - 컨텍스트 정리

**역할**: 현재 진행 중인 작업 상태를 정리하여 표시. 코딩 금지.

---

### /workflow - 통합 오케스트레이터

**역할**: PDARR 전체 사이클을 한 번에 실행. 팀 Agent 조율.

**핵심 개선점**:
- Step 0: PRD/Analyze 기존 판단 결과 먼저 확인
- Step 2: 판단 기반 실행 전략 자동 결정
- 팀 Agent 구성 시 판단 결과의 추천 구성 활용

---

## 5. 실행 전략별 Agent 활용 (핵심)

이 구조의 가장 중요한 부분.
**Claude Code 네이티브 도구**(TeamCreate, Task, SendMessage 등)와 **커스텀 커맨드**(/prd, /analyze, /run 등)를
조합하여 작업 규모에 맞는 최적의 실행 방식을 선택한다.

### 5.1 두 시스템의 역할 분담

```
┌─────────────────────────────────┐  ┌──────────────────────────────────┐
│  커스텀 커맨드 (.claude/commands/)│  │  Claude Code 네이티브 도구          │
│                                  │  │                                   │
│  "무엇을 할 것인가" 정의          │  │  "어떻게 조율할 것인가" 실행         │
│                                  │  │                                   │
│  /prd    → PRD 작성 규칙         │  │  Task()       → Agent 생성/실행    │
│  /analyze → 분석 방법론           │  │  TeamCreate() → 팀 생성            │
│  /spec   → 명세서 템플릿          │  │  TaskCreate() → 작업 항목 관리     │
│  /run    → 구현 패턴/규칙         │  │  TaskUpdate() → 진행상태/의존성    │
│  /check-code → 검수 기준          │  │  SendMessage() → Agent 간 통신     │
│  /reflect → 회고 프로세스         │  │  TaskList()   → 작업 현황 조회     │
└─────────────────────────────────┘  └──────────────────────────────────┘
              │                                       │
              └───────────── 혼합 사용 ───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  /workflow         │
                    │  (오케스트레이터)    │
                    │  커맨드 지식 +      │
                    │  네이티브 도구 조합  │
                    └───────────────────┘
```

**핵심 원리**: 커스텀 커맨드의 프롬프트 내용(규칙, 체크리스트, 템플릿)을
Claude Code의 Task/Team 도구를 통해 Agent에게 전달하여 실행시킨다.

---

### 5.2 실행 전략 3가지

#### 전략 A: 단일 Agent (Simple ~ Medium)

가장 기본적인 방식. 메인 Agent가 직접 커맨드를 실행한다.

```
사용자: /run 상품 목록 정렬 버그 수정
   ↓
메인 Agent가 run.md 프롬프트를 읽고 직접 구현
   ↓
/check-code → /stage
```

**사용 조건**: 파일 1-3개, 단일 레이어, 순차 작업
**도구**: 커스텀 커맨드만 사용, 네이티브 팀 도구 불필요

---

#### 전략 B: 병렬 Task Agent (Medium)

메인 Agent가 Task 도구로 독립 Agent 2-3개를 병렬 생성.
팀을 만들지 않고 **독립적인 Task Agent**를 동시에 실행한다.

```
사용자: /workflow 주문 상세 팝업 개선

메인 Agent (오케스트레이터):
  ├─ Task(subagent_type="Explore")   → 코드베이스 분석
  │    결과 수신 후
  ├─ Task(subagent_type="general-purpose") → 백엔드 수정 (병렬)
  ├─ Task(subagent_type="general-purpose") → 프론트엔드 수정 (병렬)
  │    모두 완료 후
  └─ 메인 Agent가 직접 /check-code 실행
```

**사용 조건**: 독립 작업 단위 2-3개, 팀 조율 불필요
**도구**: Task 도구만 사용 (TeamCreate 불필요)
**장점**: 팀 오버헤드 없이 병렬 처리
**핵심**: 각 Task의 `prompt`에 커스텀 커맨드 내용을 포함시킴

**실제 호출 예시:**
```javascript
// 분석 Agent (읽기 전용)
Task(
  subagent_type = "Explore",
  description = "주문 팝업 코드 분석",
  prompt = "modules/admin/orders/adminOrderDetailPopup.php와
            views/admin/orders/adminOrderDetailPopup.php를 분석하세요.
            변경 필요한 부분과 영향 범위를 파악하세요."
)

// 분석 결과 수신 후, 백엔드/프론트엔드 병렬 실행
Task(
  subagent_type = "general-purpose",
  description = "백엔드 수정",
  prompt = "CLAUDE.md와 .claude/coding_guidelines.md를 읽고 준수하세요.
            modules/admin/orders/adminOrderDetailPopup.php를 수정하세요.
            [구체적 수정사항...]
            담당 범위: modules/ 파일만. views/는 수정하지 마세요."
)

Task(
  subagent_type = "general-purpose",
  description = "프론트엔드 수정",
  prompt = "CLAUDE.md와 .claude/coding_guidelines.md를 읽고 준수하세요.
            views/admin/orders/adminOrderDetailPopup.php와
            css/adminOrderDetailPopup.scss를 수정하세요.
            [구체적 수정사항...]
            담당 범위: views/, css/ 파일만. modules/는 수정하지 마세요."
)
```

---

#### 전략 C: 팀 Agent (Complex)

Claude Code 네이티브 팀 도구를 전면 사용.
**TeamCreate → TaskCreate → Task(teammate) → SendMessage → TeamDelete** 전체 라이프사이클.

```
사용자: /workflow 셀러 수수료 정산 시스템 구현

/workflow (team-lead):
  │
  ├─ TeamCreate("pdarr-commission")
  │
  ├─ TaskCreate(#1 "분석", #2 "명세", #3 "백엔드", #4 "프론트", #5 "검수")
  ├─ TaskUpdate(#2 blockedBy #1, #3 blockedBy #2, ...)
  │
  ├─ Task(team_name, name="analyzer")    → #1 수행
  │    완료 → SendMessage로 결과 전달
  │
  ├─ Task(team_name, name="spec-writer") → #2 수행
  │    완료 → 사용자 승인 대기
  │
  ├─ Task(team_name, name="backend-dev")  → #3 수행 ┐
  ├─ Task(team_name, name="frontend-dev") → #4 수행 ┤ 병렬!
  │    모두 완료                                      ┘
  │
  ├─ Task(team_name, name="reviewer")     → #5 수행
  │
  ├─ SendMessage(shutdown_request) → 모든 Teammate 종료
  └─ TeamDelete()
```

**사용 조건**: 파일 6개+, 3개+ 레이어, 프론트+백엔드 동시
**도구**: TeamCreate + TaskCreate + Task + SendMessage + TeamDelete 전체 활용

---

### 5.3 네이티브 팀 도구 상세

Claude Code가 제공하는 팀 관련 도구와 사용법:

#### TeamCreate - 팀 생성

```javascript
TeamCreate(
  team_name = "pdarr-{모듈명}",
  description = "PDARR 워크플로우 - {모듈명} 개발"
)
```
- `~/.claude/teams/{team-name}/config.json` 생성
- `~/.claude/tasks/{team-name}/` 태스크 디렉토리 생성
- 팀 이름은 프로젝트 내에서 유일해야 함

#### TaskCreate - 작업 항목 생성

```javascript
TaskCreate(
  subject = "백엔드 구현 - Domain/Infra/Application",
  description = "Commission 도메인의 Entity, Repository, Manager를 구현.
                 CLAUDE.md 규칙 준수. PHP 7.2 호환.",
  activeForm = "백엔드 구현 중"
)
```
- `subject`: 명령형 ("Run tests", "백엔드 구현")
- `activeForm`: 현재 진행형 ("Running tests", "백엔드 구현 중")
- 생성 시 `pending` 상태

#### TaskUpdate - 상태/의존성 관리

```javascript
// 의존성 설정: #3 백엔드는 #2 명세 완료 후 시작
TaskUpdate(taskId = "3", addBlockedBy = ["2"])

// 작업 시작
TaskUpdate(taskId = "3", status = "in_progress", owner = "backend-dev")

// 작업 완료
TaskUpdate(taskId = "3", status = "completed")
```

#### Task - Teammate Agent 생성

```javascript
// Explore Agent (읽기 전용, 분석/검색 전문)
Task(
  subagent_type = "Explore",
  team_name = "pdarr-commission",
  name = "analyzer",
  description = "코드베이스 분석",
  prompt = "..."
)

// General-purpose Agent (읽기+쓰기, 구현 가능)
Task(
  subagent_type = "general-purpose",
  team_name = "pdarr-commission",
  name = "backend-dev",
  description = "백엔드 구현",
  prompt = "..."
)
```

**subagent_type 선택 기준:**

| 타입 | 도구 | 용도 |
|------|------|------|
| `Explore` | 읽기만 (Glob, Grep, Read, WebSearch) | 분석, 검색, 조사 |
| `general-purpose` | 전체 (Read, Write, Edit, Bash 등) | 구현, 수정, 테스트 |
| `Plan` | 읽기만 | 설계, 계획 수립 |
| `Bash` | Bash만 | 커맨드 실행 전문 |

**team_name + name이 있으면** 팀의 Teammate로 등록됨.
**team_name 없으면** 독립 Task Agent로 실행됨 (전략 B).

#### SendMessage - Agent 간 통신

```javascript
// 특정 Teammate에게 DM
SendMessage(
  type = "message",
  recipient = "backend-dev",
  content = "Domain 레이어 구현 시 Coupon 도메인의 기존 패턴을 참고하세요.",
  summary = "Domain 패턴 참고 안내"
)

// 전체 공지 (비용 주의: N명 × N호출)
SendMessage(
  type = "broadcast",
  content = "API 응답은 반드시 {result, payload} 형식으로 맞춰주세요.",
  summary = "API 응답 포맷 공지"
)

// Teammate 종료 요청
SendMessage(
  type = "shutdown_request",
  recipient = "backend-dev",
  content = "작업 완료, 종료합니다"
)
```

#### TeamDelete - 팀 정리

```javascript
TeamDelete()
// 모든 Teammate 종료 후 호출
// ~/.claude/teams/{team-name}/ 삭제
// ~/.claude/tasks/{team-name}/ 삭제
```

---

### 5.4 커스텀 커맨드 × 팀 도구 혼합 패턴

핵심: **커스텀 커맨드의 지식을 Teammate의 프롬프트에 주입**하는 방식.

#### 패턴 A: 커맨드 내용을 프롬프트에 직접 포함

```javascript
Task(
  subagent_type = "general-purpose",
  team_name = "pdarr-commission",
  name = "backend-dev",
  prompt = `
    당신은 Frecto 프로젝트의 백엔드 개발자입니다.

    ## 필수 규칙 (CLAUDE.md에서 발췌)
    - PHP 7.2 호환: 타입 힌트, 리턴 타입 금지
    - SQL: 파라미터 바인딩 금지, addslashes() 사용
    - 트랜잭션: begin_transaction(), commit(), rollback()

    ## 담당 범위
    - domain/Commission/ (Entity, VO, Repository Interface)
    - infrastructure/Commission/repositories/
    - application/Commission/CommissionManager.php

    ## 금지 범위 (다른 Agent 담당)
    - views/, css/, API/ → frontend-dev가 담당
    - 이 파일들을 수정하지 마세요

    ## 작업 내용
    [구체적 구현 지시사항...]

    ## 완료 조건
    1. 모든 파일 php -l 통과
    2. TaskUpdate로 태스크를 completed로 변경
    3. team-lead에게 완료 메시지 전송
  `
)
```

#### 패턴 B: 커맨드 파일 읽기 지시

```javascript
Task(
  subagent_type = "general-purpose",
  name = "developer",
  prompt = `
    ## 사전 준비 (필수)
    1. CLAUDE.md를 읽고 프로젝트 규칙을 숙지하세요
    2. .claude/coding_guidelines.md를 읽고 코딩 규칙을 파악하세요
    3. docs/spec/commission/ 설계 문서를 읽으세요

    ## 구현 방법
    .claude/commands/run.md의 Phase 2~3 절차를 따라 구현하세요:
    - Sequential: DB → Domain → Infra → Application
    - Parallel: API + Frontend

    ## 검증 방법
    구현 완료 후 .claude/commands/check-code.md의 검수 항목을 자체 검증하세요.
  `
)
```

**패턴 A vs B 선택 기준:**

| 상황 | 추천 | 이유 |
|------|------|------|
| 규칙이 간단하고 명확 | 패턴 A (직접 포함) | 불필요한 파일 읽기 없음 |
| 규칙이 복잡하고 상세 | 패턴 B (파일 읽기) | 프롬프트 크기 절약, 최신 규칙 반영 |
| Explore Agent | 패턴 A (직접 포함) | Explore는 Read만 가능, 충분 |
| general-purpose Agent | 패턴 B (파일 읽기) | 전체 도구 사용 가능 |

---

### 5.5 2단계 판단 → 팀 구성 자동 결정 흐름

PRD 1차 판단과 Analyze 2차 판단이 팀 구성으로 이어지는 구체적 흐름:

```
/prd 실행
  └─ 1차 판단 출력:
     복잡도: Complex
     독립 작업: [Backend(Domain+Infra), Frontend(API+View), DB스키마]
     추천: 팀 Agent
         ↓
/analyze 실행
  └─ 2차 판단 출력:
     보정: Complex 유지 (실제 파일 8개 확인)
     병렬화:
       - 독립 A: Domain + Infra (backend-dev)
       - 독립 B: API + View + SCSS (frontend-dev)
       - 순차: DB → Domain (DB 먼저)
     추천 팀 구성:
       analyzer(Explore), backend-dev, frontend-dev, reviewer
         ↓
/workflow 실행
  └─ Step 0: Analyze 2차 판단 읽기
     Step 2: 추천 팀 구성 그대로 채택 (또는 사용자 보정)
     Step 4: 팀 생성 및 실행
       TeamCreate("pdarr-commission")
       TaskCreate(#1 분석, #2 백엔드, #3 프론트, #4 검수)
       TaskUpdate(#2 blockedBy #1, #3 blockedBy #1, #4 blockedBy #2,#3)
       Task(Explore, "analyzer") → #1
       ... (결과 기반으로 #2, #3 병렬) ...
       Task(general-purpose, "reviewer") → #4
```

---

### 5.6 팀 구성 패턴 카탈로그

#### 패턴 1: PDARR 병렬 팀 (Complex, 신규 모듈)
```
team-lead (orchestrator) ─── /workflow가 이 역할
├── analyzer (Explore) ─── 코드베이스 분석 (읽기 전용)
├── spec-writer (general-purpose) ── 명세서 작성
├── backend-dev (general-purpose) ── Domain/Infra/App (병렬)
├── frontend-dev (general-purpose) ─ API/View/SCSS/JS (병렬)
└── reviewer (general-purpose) ───── 품질 검수
```
**의존성**: analyzer → spec-writer → [backend-dev, frontend-dev] → reviewer

#### 패턴 2: 분석-구현 분리 (Medium, 기존 모듈 수정)
```
team-lead (orchestrator)
├── researcher (Explore) ── 영향 범위 분석 (읽기 전용)
└── developer (general-purpose) ── 분석 결과 기반 구현
```
**의존성**: researcher → developer

#### 패턴 3: 병렬 독립 구현 (다중 버그, 다중 모듈)
```
team-lead (orchestrator)
├── worker-1 (general-purpose) ── 모듈 A 수정
├── worker-2 (general-purpose) ── 모듈 B 수정
└── worker-3 (general-purpose) ── 모듈 C 수정
```
**의존성**: 없음 (모두 독립)

#### 패턴 4: 분석+검수 전문 팀 (/check-spec, /check-code 대규모)
```
team-lead (orchestrator)
├── spec-reviewer (Explore) ── 설계문서 검수 (/check-spec 지식)
├── code-reviewer (Explore) ── 코드 품질 검수 (/check-code 지식)
└── fixer (general-purpose) ── 발견된 이슈 수정
```
**의존성**: [spec-reviewer, code-reviewer] → fixer

---

### 5.7 Teammate 프롬프트 작성 원칙

각 Teammate에게 전달하는 프롬프트에 반드시 포함:

```markdown
## 필수 포함 항목 (5가지)

1. **프로젝트 규칙 참조**
   "CLAUDE.md와 .claude/coding_guidelines.md를 반드시 읽고 준수하세요."

2. **담당 범위 명시**
   "Domain, Infrastructure 레이어만 담당합니다.
    views/, css/ 파일은 수정하지 마세요."

3. **검증 절차 포함**
   "php -l로 문법 검증, SQL은 addslashes 확인."

4. **완료 조건 명시**
   "모든 파일 생성 후 TaskUpdate로 태스크를 completed로 변경하세요."

5. **충돌 방지**
   "다음 파일은 다른 Agent가 담당합니다: {파일 목록}. 수정하지 마세요."
```

**안티패턴 (하지 말 것):**
- 같은 파일을 여러 Agent에게 할당
- Teammate에게 다른 Teammate의 작업 결과를 기다리라고만 하고 의존성 미설정
- 프로젝트 규칙 참조 없이 구현 지시
- broadcast로 일상적 메시지 전송 (DM 사용)

---

### 5.8 팀 Agent 비용/효율 판단

| 항목 | 단일 Agent | 병렬 Task | 팀 Agent |
|------|-----------|-----------|----------|
| API 호출 수 | 1 | N (Agent 수) | N + 관리 호출 |
| 컨텍스트 공유 | 완벽 | 없음 (각자 독립) | SendMessage로 제한적 |
| 파일 충돌 위험 | 없음 | 낮음 | 관리 필요 |
| 설정 오버헤드 | 없음 | 낮음 | 높음 (팀/태스크 생성) |
| 병렬 처리 | 불가 | 가능 | 가능 + 조율 |
| 적합 작업 규모 | ~3파일 | 4-6파일 | 7파일+ |

**결론**: 팀 Agent는 병렬화 이점이 설정 오버헤드를 초과할 때만 사용.
"팀 만들기가 직접 하는 것보다 빠른가?"를 항상 자문.

---

### 5.9 팀 라이프사이클 전체 예시

Complex 작업의 전체 흐름을 한 번에 보여주는 예시:

```javascript
// === Phase 1: 팀 생성 ===
TeamCreate(
  team_name = "pdarr-commission",
  description = "수수료 정산 모듈 PDARR"
)

// === Phase 2: 태스크 생성 + 의존성 ===
TaskCreate(subject="코드베이스 분석", activeForm="분석 중")           // #1
TaskCreate(subject="백엔드 구현", activeForm="백엔드 구현 중")        // #2
TaskCreate(subject="프론트엔드 구현", activeForm="프론트엔드 구현 중") // #3
TaskCreate(subject="품질 검수", activeForm="검수 중")                // #4

TaskUpdate(taskId="2", addBlockedBy=["1"])  // 백엔드 ← 분석
TaskUpdate(taskId="3", addBlockedBy=["1"])  // 프론트 ← 분석
TaskUpdate(taskId="4", addBlockedBy=["2","3"])  // 검수 ← 백엔드+프론트

// === Phase 3: Teammate 생성 ===
// 분석 Agent (Explore = 읽기 전용)
Task(
  subagent_type = "Explore",
  team_name = "pdarr-commission",
  name = "analyzer",
  prompt = "Commission 관련 코드를 분석하세요. [상세...]"
)
// → analyzer 완료 → TaskUpdate(#1, completed)
// → team-lead에게 분석 결과 메시지 전송

// 백엔드 + 프론트엔드 Agent (동시 생성 = 병렬)
Task(
  subagent_type = "general-purpose",
  team_name = "pdarr-commission",
  name = "backend-dev",
  prompt = "CLAUDE.md 읽고 Domain/Infra/App 구현. [상세...]"
)
Task(
  subagent_type = "general-purpose",
  team_name = "pdarr-commission",
  name = "frontend-dev",
  prompt = "CLAUDE.md 읽고 API/View/SCSS 구현. [상세...]"
)
// → 두 Agent가 병렬로 작업
// → 각각 완료 시 TaskUpdate(completed)

// 검수 Agent (#2,#3 완료 후 시작)
Task(
  subagent_type = "general-purpose",
  team_name = "pdarr-commission",
  name = "reviewer",
  prompt = ".claude/commands/check-code.md 기준으로 전체 코드 검수. [상세...]"
)

// === Phase 4: 결과 취합 + 종료 ===
SendMessage(type="shutdown_request", recipient="analyzer")
SendMessage(type="shutdown_request", recipient="backend-dev")
SendMessage(type="shutdown_request", recipient="frontend-dev")
SendMessage(type="shutdown_request", recipient="reviewer")

TeamDelete()
```

---

## 6. 디렉토리 구조

### .claude/commands/ 파일 목록

```
.claude/commands/
├── dispatch.md        # 스마트 라우터 (시작점)
├── prd.md             # PRD + 1차 판단
├── analyze.md         # 분석 + 2차 판단
├── spec.md            # 기술 명세서
├── test.md            # TDD 테스트 케이스
├── run.md             # 구현
├── check-spec.md      # 설계문서 검수
├── check-code.md      # 코드 검수 (REVIEW 통합)
├── check-context.md   # → check-code 리다이렉트
├── qa-test.md         # 종합 QA
├── reflect.md         # 자기성찰
├── complete.md        # 완료 정리
├── stage.md           # Git 스테이징
├── flow.md            # 컨텍스트 정리
└── workflow.md        # 통합 오케스트레이터
```

### docs/ 산출물 구조

```
docs/
├── prd/               # PRD 문서 (요구사항 + 1차 판단)
│   └── {프로젝트명}/
│       └── prd.md
├── todo/              # 간단한 할 일 목록
├── spec/              # 기술 설계 (architecture, api, db)
│   └── {모듈명}/
│       ├── architecture.md
│       ├── api_design.md
│       ├── database_schema.md
│       └── create_table.sql
├── history/           # 일일 작업 기록
├── qa-reports/        # QA 테스트 리포트
└── complete/          # 완료된 작업 통합
    ├── summary.md     # 전체 요약 (카테고리별)
    └── {날짜}_{모듈}/
        ├── README.md
        ├── prd/       # PRD 원본 보존
        └── spec/      # 설계문서 압축본
```

---

## 7. 새 프로젝트에 셋업하기

### Step 1: 디렉토리 생성

```bash
mkdir -p .claude/commands
mkdir -p docs/{prd,todo,spec,history,qa-reports,complete}
```

### Step 2: 커맨드 파일 복사

`.claude/commands/` 의 모든 `.md` 파일을 새 프로젝트에 복사.
각 파일의 첫 줄 역할 설명을 프로젝트에 맞게 수정.

### Step 3: 프로젝트 맞춤 수정

각 커맨드에서 프로젝트별로 조정해야 할 항목:

| 커맨드 | 조정 항목 |
|--------|----------|
| `/dispatch` | 복잡도 판단 기준 (파일 수, 레이어 등) |
| `/prd` | PRD 템플릿 섹션 (프로젝트 특성 반영) |
| `/analyze` | 참조할 규칙 문서 경로, DDD 도메인 목록 |
| `/spec` | 아키텍처 패턴, API 포맷, DB 규칙 |
| `/run` | Worker 구성, 코딩 규칙, 프레임워크 특성 |
| `/check-code` | 검수 항목 (언어별 문법, 보안 규칙) |
| `/workflow` | 팀 패턴, 병렬화 단위 |

### Step 4: CLAUDE.md에 워크플로우 참조 추가

```markdown
## Development Workflow

**커맨드 흐름**: /dispatch → /prd → /analyze → /spec → /run → /check-code → /reflect → /complete → /stage
**상세 가이드**: `.claude/workflow-commands-guide.md`
```

### Step 5: 팀 Agent 활성화 (settings.json)

`~/.claude/settings.json`에 팀 Agent 실험 기능 활성화:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

이 설정이 없으면 `/workflow`의 팀 Agent 기능을 사용할 수 없다.

### Step 6: zshrc 리마인드 배너 등록

`~/.zshrc`에 `claude` 래퍼 함수를 추가하면, 프로젝트 디렉토리에서 `claude` 실행 시 워크플로우 가이드가 자동 출력된다:

```bash
# Claude Code 래퍼 함수 (프로젝트에서 워크플로우 가이드 출력)
claude() {
    if [[ "$PWD" == *"프로젝트_디렉토리명"* ]]; then
        echo ''
        echo '╔══════════════════════════════════════════════════════════════╗'
        echo '║           🚀 프로젝트 워크플로우 가이드                      ║'
        echo '╠══════════════════════════════════════════════════════════════╣'
        echo '║                                                              ║'
        echo '║  ★ /dispatch "요청"     → 스마트 라우터 (시작점, 자동 판단)  ║'
        echo '║                                                              ║'
        echo '║  [계획] /prd "기능명"   → PRD + 복잡도 1차 판단              ║'
        echo '║         /analyze "요청" → 분석 + 실행전략 2차 판단           ║'
        echo '║         /spec           → 기술 명세서 작성                   ║'
        echo '║                                                              ║'
        echo '║  [실행] /run            → 구현                               ║'
        echo '║                                                              ║'
        echo '║  [검증] /check-spec     → 설계문서 검수                      ║'
        echo '║         /check-code     → 코드 검수 (--context/--full)       ║'
        echo '║         /qa-test        → 종합 QA                            ║'
        echo '║                                                              ║'
        echo '║  [완료] /reflect → /complete → /stage                        ║'
        echo '║                                                              ║'
        echo '╠══════════════════════════════════════════════════════════════╣'
        echo '║  Trivial → 직접수정 | Simple → /run                         ║'
        echo '║  Medium  → /analyze → /run | Complex → /prd → /workflow     ║'
        echo '╠══════════════════════════════════════════════════════════════╣'
        echo '║  📄  상세: .claude/workflow-commands-guide.md                 ║'
        echo '╚══════════════════════════════════════════════════════════════╝'
        echo ''
    fi
    command claude "$@"
}
```

**적용**: `source ~/.zshrc` 실행 또는 터미널 재시작.

**여러 프로젝트 지원**: `if` 조건을 `elif`로 확장하면 프로젝트별 다른 배너 표시 가능:
```bash
claude() {
    if [[ "$PWD" == *"project_a"* ]]; then
        echo '... Project A 배너 ...'
    elif [[ "$PWD" == *"project_b"* ]]; then
        echo '... Project B 배너 ...'
    fi
    command claude "$@"
}
```

### Step 7: CLAUDE.md에 워크플로우 참조 추가

프로젝트의 `CLAUDE.md` 참조 테이블에 가이드 추가:

```markdown
## Reference Files

| Guide | Location |
|-------|----------|
| Workflow Guide | `.claude/workflow-commands-guide.md` |
```

### Step 8: 테스트 실행

간단한 작업으로 `/dispatch` → `/run` → `/check-code` 경로 테스트.
복잡한 작업으로 `/dispatch` → `/prd` → `/analyze` → `/workflow` 경로 테스트.

---

## 8. 장점 및 활용 팁

### 이 구조의 장점

**효율성**
- 단순 작업에 불필요한 오버헤드 제거 (dispatch가 라우팅)
- 복잡한 작업은 병렬 처리로 시간 단축 (팀 Agent)
- PRD/Analyze 결과 재활용 (중복 분석 방지)

**품질**
- 2단계 판단으로 적절한 실행 전략 보장
- 구현 후 자동 검수 (check-code)
- 자기성찰로 세션 간 학습 축적 (reflect → Memory)

**추적성**
- 모든 산출물이 docs/에 구조화
- 완료 작업은 docs/complete/로 통합
- summary.md로 전체 작업 이력 한눈에 파악

### 활용 팁

1. **매번 /dispatch부터 시작하지 않아도 된다**
   - 명확히 Simple인 작업은 바로 `/run`
   - 이미 분석 완료된 작업은 바로 `/spec` 또는 `/run`

2. **커맨드를 건너뛸 수 있다**
   - `/prd` → `/run` (spec 생략, 간단한 기능)
   - `/analyze` → `/run` (spec 생략, 기존 패턴 활용)

3. **팀 Agent는 꼭 Complex에서만 쓰는 게 아니다**
   - 독립적인 3개 버그 수정 → 패턴 3 (병렬 구현)
   - 코드 분석이 오래 걸리는 경우 → 패턴 2 (분석-구현 분리)

4. **Memory 활용으로 세션 간 학습**
   - `/reflect`가 저장한 Memory를 다음 세션에서 자동 참조
   - 반복 실수 감소, 프로젝트별 패턴 축적

5. **검수는 상황에 맞게 선택**
   - 설계 단계 → `/check-spec`
   - 구현 직후 → `/check-code`
   - 전체 검수 → `/check-code --full`
   - 변경 파일 QA → `/qa-test`

---

## 9. 커맨드 파일 작성 규칙

새 커맨드를 추가할 때 지켜야 할 규칙:

### 파일 구조

```markdown
# 첫 줄: 역할 정의 (시스템 프롬프트 역할)
너는 능숙한 {프로젝트명} {역할}이야.

# 제약 조건 (필요 시)
<< 절대 코딩은 하지말것 >>

# 역할 설명
## 목적 / 역할

# 실행 프로세스
## Phase 1: ...
## Phase 2: ...

# 출력 형식
## 출력 형식

# 다음 단계
## 다음 단계
```

### 명명 규칙

- 파일명: kebab-case (`check-code.md`)
- 단일 단어 우선 (`analyze.md`, `dispatch.md`)
- 동사형 (`run`, `reflect`) 또는 명사형 (`spec`, `stage`)

### 연결성

- 각 커맨드의 "다음 단계"에 후속 커맨드 명시
- 입력(이전 커맨드 산출물)과 출력(다음 커맨드 입력) 명확히
- 워크플로우 위치를 PDARR 기준으로 표시

---

## 10. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-02-11 | 초기 작성. /dispatch 신설, PRD 1차 판단, Analyze 2차 판단, check-context→check-code 통합, workflow PRD/Analyze 결과 활용 개선 |
