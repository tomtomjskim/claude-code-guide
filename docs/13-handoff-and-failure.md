# 핸드오프 & 실패 복구 실전 가이드

## 개요

이 가이드는 v3.0의 두 핵심 메커니즘인 **Handoff Protocol**과 **Failure Recovery**를 실제로 설정하고 활용하는 방법을 다룹니다.

---

## 1. Handoff Protocol 설정

### 1-1. handoff-protocol.md 생성

에이전트 간 컨텍스트 전달 계약을 문서화합니다.

```bash
mkdir -p ~/.claude/team/context
cat > ~/.claude/team/context/handoff-protocol.md << 'EOF'
# Handoff Protocol v1.0

## 원칙
- 모든 에이전트는 작업 완료 시 5-field Return 구조로 결과를 반환한다.
- 수신 에이전트는 required_fields 검증 후 작업을 시작한다.
- 검증 실패 시 retry_once → escalate_to_pm 순서로 처리한다.

## 핸드오프 스키마
```yaml
handoff:
  from_agent: string
  to_agent: string
  task_id: string
  payload:
    scope: string
    findings: string[]
    recommendation: string
    validation_status: pass | fail | partial
    residual_risk: string[]
    artifacts: string[]
  validation:
    required_fields: [scope, findings, recommendation, validation_status]
    on_validation_fail: retry_once | escalate_to_pm
```

## Data Flow
analysis → design → preparation → implementation → verification → deployment → documentation
EOF
```

### 1-2. agents.yaml에 handoff 블록 추가

각 에이전트에 `accepts`, `produces`, `requires_from_upstream`을 명시합니다.

```yaml
# ~/.claude/team/agents.yaml (관련 섹션)

agents:
  explorer:
    handoff:
      accepts: []
      produces: [exploration-report]
      requires_from_upstream: []

  architect:
    handoff:
      accepts: [explorer, pm]
      produces: [design-doc, architecture-diagram]
      requires_from_upstream: [scope, findings]

  dba:
    handoff:
      accepts: [architect]
      produces: [migration-sql, schema-doc]
      requires_from_upstream: [scope, design_doc]

  designer:
    handoff:
      accepts: [architect]
      produces: [ui-spec, component-list]
      requires_from_upstream: [scope, design_doc]

  developer:
    handoff:
      accepts: [architect, designer, dba]
      produces: [source-code, implementation-report]
      requires_from_upstream: [scope, design_doc]

  qa:
    handoff:
      accepts: [developer]
      produces: [test-report, qa-artifacts]
      requires_from_upstream: [scope, artifacts, residual_risk]

  publisher:
    handoff:
      accepts: [qa, reviewers]
      produces: [deployment-report]
      requires_from_upstream: [validation_status, artifacts]

  documenter:
    handoff:
      accepts: [publisher, developer, api-reviewer]
      produces: [documentation]
      requires_from_upstream: [artifacts, findings]
```

---

## 2. Failure Recovery 설정

### 2-1. failure-policy.yaml 생성

```bash
cat > ~/.claude/team/workflows/failure-policy.yaml << 'EOF'
# Failure Policy v1.0

version: "3.0"

policies:
  retry:
    description: 멱등 태스크 재시도
    max_attempts: 2
    backoff: none
    applicable_to:
      - explore
      - document
      - review
      - test

  escalate:
    description: PM에게 에스컬레이션 후 재분해
    applicable_to:
      - implement
      - design
      - schema-change

  rollback:
    description: 즉시 롤백 후 에스컬레이션
    strategies:
      code_rollback: "git revert HEAD --no-edit"
      container_rollback: "docker compose stop {service} && docker compose up -d --no-deps {service}"
      schema_rollback: "psql -f rollback-{migration_id}.sql"
    applicable_to:
      - deploy
      - migrate

  circuit_breaker:
    description: 연속 3회 실패 시 워크플로우 일시 중단
    threshold: 3
    action: pause_and_report_to_user
EOF
```

### 2-2. 워크플로우에 on_fail 추가

각 워크플로우 단계에 `on_fail` 필드를 추가합니다.

```yaml
# standard.yaml 예시

steps:
  - id: explore
    agent: explorer
    on_fail: retry

  - id: design
    agent: architect
    on_fail: escalate

  - id: db_schema
    agent: dba
    on_fail: rollback

  - id: implement
    agent: developer
    on_fail: escalate

  - id: test
    agent: qa
    on_fail: retry

  - id: deploy
    agent: publisher
    on_fail: rollback
```

---

## 3. 핸드오프 실전 예시

### 예시 A: Explorer → Architect 핸드오프

Explorer가 탐색을 마치고 Architect에게 전달하는 상황입니다.

**Explorer Return (출력)**
```
scope: "auth 모듈 — src/auth/, middleware/jwt.ts, routes/user.ts (3파일)"

findings:
  - "JWT 검증 로직이 middleware/jwt.ts와 routes/user.ts에 중복 구현됨 (확인)"
  - "토큰 만료 처리 누락 — jwt.verify() 에러 핸들링 없음 (확인)"
  - "refresh token 저장소 미존재 — 재발급 불가 구조 (확인)"

recommendation: "JWT 검증 미들웨어 단일화 + refresh token Redis 저장소 추가"

validation_status: pass

residual_risk:
  - "레거시 /api/v1/login 엔드포인트가 별도 auth 로직을 가질 수 있음 — 추가 확인 필요"
```

**Architect가 수신 후 확인하는 항목**
- scope, findings, recommendation, validation_status 4개 필드 존재 여부
- validation_status가 pass인지 확인
- residual_risk 항목을 설계 범위에 반영할지 결정

### 예시 B: Developer → QA 핸드오프

Developer가 구현을 마치고 QA에게 전달하는 상황입니다.

**Developer Return (출력)**
```
scope: "JWT 미들웨어 통합 — middleware/jwt.ts 재작성, routes/user.ts 수정, Redis 연결 추가 (4파일)"

findings:
  - "jwt.ts: verifyToken() 단일 함수로 통합, 만료/서명 에러 분리 처리"
  - "user.ts: 미들웨어 참조로 교체, 직접 검증 로직 제거"
  - "redis.ts: refresh token 저장/조회/삭제 구현"
  - "레거시 /api/v1/login: 별도 auth 로직 없음 확인 — residual_risk 해소"

recommendation: "정상 로그인/만료 토큰/refresh 토큰 재발급 3가지 시나리오 집중 테스트"

validation_status: partial

residual_risk:
  - "Redis 연결 실패 시 fallback 없음 — Redis 장애 시 전체 인증 불가"
  - "동시 refresh 요청 race condition 미처리"
```

**QA가 수신 후 집중할 항목**
- validation_status가 partial이므로 residual_risk 2건을 테스트 케이스에 포함
- Redis 장애 시나리오 및 동시성 테스트 추가

---

## 4. 실패 복구 실전 예시

### 예시 A: 배포 실패 → 즉시 롤백

Publisher가 컨테이너 배포 중 실패한 상황입니다.

```
[Publisher] 배포 시작: lotto-service v2.1.0
[Publisher] docker compose build lotto-service → 성공
[Publisher] docker compose up -d --no-deps lotto-service → 실패 (exit 1)
[Publisher] on_fail: rollback 적용
[Publisher] 롤백 실행: docker compose stop lotto-service
[Publisher] 이전 이미지로 재시작: docker compose up -d --no-deps lotto-service
[Publisher] 롤백 완료 — 서비스 정상 복구

[PM] 에스컬레이션 보고:
  - 실패 태스크: deploy/lotto-service
  - 실패 원인: 컨테이너 시작 실패 (포트 충돌 추정)
  - 현재 상태: 롤백 완료, 이전 버전 운영 중
  - 필요 조치: 사용자 확인 후 원인 분석 및 재배포
```

### 예시 B: 구현 실패 → 에스컬레이션

Developer가 태스크를 완료하지 못한 상황입니다.

```
[Developer] 구현 시도: Redis refresh token 저장소
[Developer] 실패: Redis 클라이언트 라이브러리 버전 호환성 문제
[Developer] on_fail: escalate 적용

[PM] 에스컬레이션 수신
  - 실패 태스크: implement/redis-token-store
  - 실패 원인: ioredis v4 API가 현재 Node.js 버전과 비호환
  - 제안 1: ioredis v5로 업그레이드
  - 제안 2: node-redis 라이브러리로 교체
  - 태스크 재분해 필요

[PM] 사용자에게 보고:
  "Redis 클라이언트 라이브러리 호환성 이슈가 발생했습니다.
   제안 1(ioredis v5 업그레이드) 또는 제안 2(node-redis 전환) 중
   어떤 방향으로 진행할까요?"
```

### 예시 C: 서킷 브레이커 작동

같은 태스크가 연속 3회 실패한 상황입니다.

```
[QA] 테스트 실행 시도 1 → 실패 (DB 연결 타임아웃)
[QA] retry 1 → 실패 (DB 연결 타임아웃)
[QA] retry 2 → 실패 (DB 연결 타임아웃)
[Circuit Breaker] 임계값 도달 (3회) → 워크플로우 일시 중단

[PM] 사용자 보고:
  "테스트 단계에서 연속 3회 실패가 발생하여 워크플로우를 일시 중단했습니다.
   증상: DB 연결 타임아웃 (매번 동일)
   가능한 원인: PostgreSQL 컨테이너 비정상, 연결 풀 고갈
   확인 방법: docker compose logs postgres
   준비되시면 워크플로우 재개를 알려주세요."
```

---

## 5. PM 핸드오프 템플릿

PM이 에이전트에게 태스크를 전달할 때 사용하는 표준 템플릿입니다.

```
[PM → {Agent}] Task: {task_id}

**Context**
- 요청 원문: {user_request}
- 워크플로우: {workflow_name} / 단계: {step_id}
- 선행 에이전트: {previous_agent} (validation_status: {status})

**Scope**
{scope from previous agent or PM analysis}

**Findings (선행 에이전트로부터)**
{findings list}

**Your Task**
{specific instructions for this agent}

**Constraints**
- 범위 외 변경 금지
- 완료 시 5-field Return 구조로 결과 반환
- 실패 시 on_fail 정책: {retry | escalate | rollback}

**Artifacts 위치**
{path or reference to prior artifacts}
```

### 실제 사용 예시

```
[PM → Developer] Task: auth-jwt-refactor-003

**Context**
- 요청 원문: "JWT 인증 중복 코드 정리 및 refresh token 구현"
- 워크플로우: standard / 단계: implement
- 선행 에이전트: architect (validation_status: pass)

**Scope**
middleware/jwt.ts, routes/user.ts, lib/redis.ts (신규), tests/auth.test.ts

**Findings (Architect로부터)**
- JWT 검증 단일 미들웨어로 통합 설계 완료
- refresh token → Redis TTL 7일로 설계
- 레거시 /api/v1/login 별도 처리 불필요 (Explorer 확인)

**Your Task**
1. middleware/jwt.ts: verifyToken() 단일 함수로 통합
2. lib/redis.ts: refresh token CRUD 구현
3. routes/user.ts: 미들웨어 참조로 교체
4. 단위 테스트 3개 이상 작성

**Constraints**
- 범위 외 파일 수정 금지
- 완료 시 5-field Return 구조로 결과 반환
- 실패 시 on_fail 정책: escalate

**Artifacts 위치**
~/.claude/team/artifacts/auth-jwt-refactor/architect-design.md
```

---

## 6. 에스컬레이션 보고 템플릿

PM이 사용자에게 에스컬레이션을 보고할 때 사용하는 표준 형식입니다.

```
[워크플로우 중단 보고]

태스크: {task_id}
단계: {workflow_step}
담당 에이전트: {agent}

실패 원인:
  {concrete failure reason with evidence}

현재 상태:
  {current system state — rollback 완료 여부 등}

선택지:
  A. {option A — 예: 태스크 재분해 후 재시도}
  B. {option B — 예: 라이브러리 변경 후 재시도}
  C. {option C — 예: 해당 기능 보류}

권장사항:
  {PM 판단 기반 권장 선택지 및 이유}

재개하려면:
  선택하신 방향을 알려주시면 즉시 재개하겠습니다.
```

---

## 7. 체크리스트

### 핸드오프 설정 체크리스트
- [ ] `~/.claude/team/context/handoff-protocol.md` 생성
- [ ] `agents.yaml`의 각 에이전트에 `handoff` 블록 추가
- [ ] 각 에이전트 프롬프트에 Return 5-field 구조 명시
- [ ] `validate-system.sh` 실행하여 핸드오프 블록 수 검증

### 실패 복구 설정 체크리스트
- [ ] `~/.claude/team/workflows/failure-policy.yaml` 생성
- [ ] 각 워크플로우 파일 단계에 `on_fail` 필드 추가
- [ ] 배포 워크플로우에 롤백 명령 명시
- [ ] DB 마이그레이션 워크플로우에 롤백 SQL 경로 명시
- [ ] `validate-system.sh` 실행하여 failure_policy 참조 검증

---

## 관련 문서
- [v3.0 시스템 아키텍처](12-v3-architecture.md)
- [에이전트 페르소나 v3.0](05-agent-personas.md)
- [코드 리뷰 시스템 v3.0](10-code-review-system.md)
