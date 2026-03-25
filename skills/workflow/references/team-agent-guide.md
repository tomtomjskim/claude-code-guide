# 팀 Agent 활용 가이드

복잡도가 Medium 이상인 작업은 Team Agent를 활용하여 병렬 처리할 수 있습니다.
팀 Agent는 여러 전문 Agent를 동시에 실행하여 PDARR 워크플로우의 처리 속도를 높입니다.

---

## 언제 팀 Agent를 사용하는가?

| 복잡도 | Agent 전략 | 설명 |
|--------|-----------|------|
| Simple | 단일 Task Agent | 단일 파일 수정, 간단한 버그 수정 |
| Medium | 단일 Task Agent + 병렬 호출 | 여러 파일 수정이나 2~3개 도메인 관련 |
| Complex | **Team Agent (권장)** | 다수 파일 생성, 전체 아키텍처 레이어, 프론트+백엔드 동시 |

---

## 팀 구성 패턴

### 패턴 1: PDARR 병렬 팀 (Complex 작업용)

```
Team: "pdarr-{module}"
+-- team-lead (orchestrator) - 전체 조율, 결과 취합
+-- analyzer (Explore) - Phase 1: PLAN (코드베이스 분석, 읽기 전용)
+-- spec-writer (general-purpose) - Phase 2: DOCUMENT (명세서 작성)
+-- backend-dev (general-purpose) - Phase 3: ACT - Backend 레이어
+-- frontend-dev (general-purpose) - Phase 3: ACT - API/View/Style/Script
+-- reviewer (general-purpose) - Phase 4: REVIEW (품질 검수)
```

### 패턴 2: 분석-구현 분리 팀 (Medium 작업용)

```
Team: "dev-{module}"
+-- team-lead (orchestrator) - 조율
+-- researcher (Explore) - 코드베이스 분석, 유사 기능 탐색
+-- developer (general-purpose) - 명세 + 구현 + 검수
```

### 패턴 3: 병렬 구현 팀 (다중 모듈 동시 작업)

```
Team: "parallel-{feature}"
+-- team-lead (orchestrator) - 조율, 의존성 관리
+-- worker-1 (general-purpose) - 모듈 A 구현
+-- worker-2 (general-purpose) - 모듈 B 구현
+-- worker-3 (general-purpose) - 모듈 C 구현
```

---

## 팀 생성 및 실행 절차

### Step 1: 팀 생성

```
TeamCreate(
  team_name="pdarr-{module}",
  description="PDARR 워크플로우 - {모듈명} 개발"
)
```

### Step 2: 태스크 생성 및 의존성 설정

```
# 태스크 생성 (Phase별)
TaskCreate(subject="코드베이스 분석", description="...", activeForm="코드베이스 분석 중")
TaskCreate(subject="명세서 작성", description="...", activeForm="명세서 작성 중")
TaskCreate(subject="백엔드 구현", description="...", activeForm="백엔드 구현 중")
TaskCreate(subject="프론트엔드 구현", description="...", activeForm="프론트엔드 구현 중")
TaskCreate(subject="품질 검수", description="...", activeForm="품질 검수 중")

# 의존성 설정
TaskUpdate(taskId="2", addBlockedBy=["1"])  # 명세 <- 분석
TaskUpdate(taskId="3", addBlockedBy=["2"])  # 백엔드 <- 명세
TaskUpdate(taskId="4", addBlockedBy=["2"])  # 프론트엔드 <- 명세 (백엔드와 병렬)
TaskUpdate(taskId="5", addBlockedBy=["3", "4"])  # 검수 <- 백엔드 + 프론트엔드
```

### Step 3: Teammate 생성 (Task Tool 사용)

```
# 분석 Agent (읽기 전용)
Task(
  subagent_type="general-purpose",
  team_name="pdarr-{module}",
  name="analyzer",
  description="코드베이스 분석",
  prompt="프로젝트의 {모듈} 관련 코드를 분석하세요. CLAUDE.md 규칙을 준수하세요..."
)

# 백엔드 개발 Agent
Task(
  subagent_type="general-purpose",
  team_name="pdarr-{module}",
  name="backend-dev",
  description="백엔드 구현",
  prompt="백엔드 레이어를 구현하세요..."
)

# 프론트엔드 개발 Agent (백엔드와 병렬 실행)
Task(
  subagent_type="general-purpose",
  team_name="pdarr-{module}",
  name="frontend-dev",
  description="프론트엔드 구현",
  prompt="API 엔드포인트, View, Style, Script를 구현하세요..."
)
```

### Step 4: 진행 상황 관리

```
# 태스크 현황 확인
TaskList()

# 특정 태스크 상세 확인
TaskGet(taskId="3")

# Teammate에게 메시지 전송
SendMessage(
  type="message",
  recipient="backend-dev",
  content="기존 도메인의 패턴을 참고하세요.",
  summary="도메인 패턴 참고 안내"
)

# 전체 팀 공지 (비용이 크므로 신중하게 사용)
SendMessage(
  type="broadcast",
  content="API 응답 포맷을 반드시 프로젝트 표준에 맞춰주세요.",
  summary="API 응답 포맷 공지"
)
```

### Step 5: 완료 및 정리

```
# 모든 Teammate 종료 요청
SendMessage(type="shutdown_request", recipient="analyzer", content="작업 완료")
SendMessage(type="shutdown_request", recipient="backend-dev", content="작업 완료")
SendMessage(type="shutdown_request", recipient="frontend-dev", content="작업 완료")

# 팀 삭제
TeamDelete()
```

---

## Teammate 프롬프트 작성 원칙

각 Teammate에게 전달하는 프롬프트에 반드시 포함할 내용:

1. **프로젝트 규칙 참조**: "CLAUDE.md와 프로젝트 코딩 규칙을 반드시 읽고 준수하세요." <!-- CUSTOMIZE: point to your project's coding guidelines -->
2. **담당 범위 명시**: "백엔드 레이어만 담당합니다. View는 건드리지 마세요."
3. **검증 절차 포함**: "문법 검증, SQL 검증 필수."
4. **완료 조건 명시**: "모든 파일 생성 후 TaskUpdate로 태스크를 completed로 변경하세요."
5. **충돌 방지**: "다음 파일은 다른 Agent가 담당합니다: {파일 목록}. 수정하지 마세요."

---

## 주의사항

- **파일 충돌 방지**: 같은 파일을 여러 Agent가 동시 수정하면 충돌 발생. 반드시 담당 파일을 분리
- **의존성 관리**: `addBlockedBy`로 실행 순서를 보장. 분석 완료 전 구현 시작 금지
- **비용 인식**: 각 Teammate는 별도 API 호출. 단순 작업에 팀은 과도한 비용 발생
- **broadcast 최소화**: 전체 공지는 Teammate 수만큼 API 호출 발생. DM(message) 우선 사용
- **Idle 상태 이해**: Teammate가 idle이 되는 것은 정상. 메시지 전송하면 다시 활성화됨

---

## 자동 결정 로직

**PRD/Analyze 판단 결과 기반 자동 결정:**

```
Step 0에서 PRD/Analyze 확인
    |
    +-- 2차 판단 "단일 Agent" -> 단일 Task Agent로 PDARR 실행
    +-- 2차 판단 "병렬 Task" -> 독립 작업 단위별 Task Agent 2-3개
    +-- 2차 판단 "팀 Agent"  -> 팀 Agent 구성 (위 패턴 참조)
```

**판단 결과가 없는 경우 (자체 판단):**

| 복잡도 | Agent 전략 | 자동/수동 |
|--------|-----------|----------|
| Simple | 단일 Task Agent | 자동 |
| Medium | 자체 범위 분석 후 결정 | Semi-Auto: 질문 |
| Complex | 팀 Agent 추천 | Semi-Auto: 질문 |

---

## 워크플로우 모드별 팀 적용

| 모드 | 팀 사용 | 설명 |
|------|---------|------|
| Full-Auto | PRD/Analyze 판단 기반 자동 | 판단 결과에 따라 자동 팀 구성 |
| Semi-Auto | 팀 구성 승인 | 판단 결과 제시 후 "이 구성으로 진행하시겠습니까?" |
| Step-by-Step | 수동 팀 구성 | 각 Teammate 생성 시마다 승인 |

---

## 실행 예시 (단일 Agent)

```
/workflow 본인인증 콜백 모듈 구현

-> Step 1: 요구사항 파싱
  - 기능: 본인인증 콜백 처리
  - 도메인: User (추정)
  - 복잡도: Medium

-> Step 2: 워크플로우 모드 선택 (AskUserQuestion)
  [사용자 선택: Semi-Auto]

-> Step 3: Task Tool 실행
  Task(subagent_type="general-purpose", ...)

-> Agent 실행 시작...
  [Phase 1: PLAN] 분석 중...
  [Phase 2: DOCUMENT] 명세서 작성 중...
  [Validation Gate #1] 승인 요청...
  [Phase 3: ACT] 구현 중...
  [Phase 4: REVIEW] 검수 중...
  [Phase 5: REFLECT] 반성 중...

-> 완료!
```

---

## 실행 예시 (팀 Agent, Complex 작업)

```
/workflow 수수료 정산 모듈 구현

-> Step 1: 요구사항 파싱
  - 기능: 수수료 정산 시스템
  - 도메인: Commission
  - 복잡도: Complex (전 레이어 + 정산 로직 + 관리자 UI)

-> Step 2: 워크플로우 모드 선택 (AskUserQuestion)
  [사용자 선택: Semi-Auto]
  -> 복잡도 Complex -> "팀 Agent를 사용하시겠습니까?" (AskUserQuestion)
  [사용자 선택: 예]

-> Step 3: 팀 생성
  TeamCreate(team_name="pdarr-commission", description="수수료 정산 모듈 PDARR")

-> Step 4: 태스크 생성 및 의존성 설정
  Task #1: 코드베이스 분석 (blockedBy: 없음)
  Task #2: 명세서 작성 (blockedBy: #1)
  Task #3: 백엔드 구현 (blockedBy: #2)
  Task #4: 프론트엔드 구현 (blockedBy: #2)
  Task #5: 품질 검수 (blockedBy: #3, #4)

-> Step 5: Teammate 생성 및 실행
  [analyzer] 코드베이스 분석 시작...
  [analyzer] 분석 완료 -> Task #1 completed
  [spec-writer] 명세서 작성 시작... (Task #2 unblocked)
  [spec-writer] 명세서 완료 -> Task #2 completed
  [Validation Gate] 승인 요청 -> 사용자 승인
  [backend-dev] 백엔드 구현 시작... (Task #3 unblocked)
  [frontend-dev] 프론트엔드 구현 시작... (Task #4 unblocked, 병렬!)
  [backend-dev] 백엔드 완료 -> Task #3 completed
  [frontend-dev] 프론트엔드 완료 -> Task #4 completed
  [reviewer] 품질 검수 시작... (Task #5 unblocked)
  [reviewer] 검수 완료 -> Task #5 completed

-> Step 6: 팀 종료
  SendMessage(shutdown_request) -> 모든 Teammate 종료
  TeamDelete() -> 팀 리소스 정리

-> 완료! (백엔드/프론트엔드 병렬 처리로 단일 Agent 대비 시간 단축)
```
