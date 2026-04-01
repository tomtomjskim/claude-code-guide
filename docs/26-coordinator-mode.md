# Coordinator Mode

## 개요

Coordinator Mode는 Claude Code를 순수 오케스트레이터로 동작하게 하는 실험적 모드입니다.
이 모드에서 코디네이터 인스턴스는 코드를 직접 읽거나 수정하지 않고,
워커 에이전트를 통해 모든 작업을 위임합니다.

> **실험적 기능 경고**: Coordinator Mode는 현재 실험적(experimental) 상태입니다.
> 프로덕션 환경에서 사용하기 전에 충분한 테스트가 필요하며, 동작이 변경될 수 있습니다.

---

## 1. 활성화

```bash
# 환경변수로 활성화
export CLAUDE_CODE_COORDINATOR_MODE=1

# 또는 단일 세션에서
CLAUDE_CODE_COORDINATOR_MODE=1 claude
```

`settings.json`에서 영구 활성화:
```json
{
  "env": {
    "CLAUDE_CODE_COORDINATOR_MODE": "1"
  }
}
```

---

## 2. 사용 가능한 도구 (4개만)

Coordinator Mode에서 코디네이터는 오직 다음 4개의 도구만 사용할 수 있습니다.

| 도구 | 역할 | 설명 |
|------|------|------|
| `Agent` | 워커 스폰 | 새로운 서브에이전트를 생성하고 작업을 위임 |
| `SendMessage` | 에이전트 통신 | 실행 중인 에이전트에 메시지 전송 |
| `TaskStop` | 태스크 중단 | 실행 중인 에이전트/태스크를 중단 |
| `SyntheticOutput` | 합성 출력 | 워커 결과를 합성하여 최종 응답 생성 |

코디네이터는 `Read`, `Write`, `Edit`, `Bash`, `Grep` 등의 도구에 접근할 수 없습니다.
모든 파일 조작과 명령 실행은 워커 에이전트가 담당합니다.

---

## 3. 4단계 워크플로우

Coordinator Mode의 표준 작업 흐름은 4단계로 구성됩니다.

### 단계 1: Research (조사)

```
코디네이터
    │
    ▼
Agent("코드베이스 구조 파악") → 워커 A
Agent("요구사항 분석")        → 워커 B   (동시 실행)
Agent("의존성 확인")          → 워커 C
    │
    ▼
워커들의 조사 결과 수집 (SyntheticOutput)
```

이 단계에서 코디네이터는 여러 워커에게 코드베이스 탐색을 병렬로 위임하고
결과를 합산하여 전체적인 맥락을 파악합니다.

### 단계 2: Synthesis (합성)

```
코디네이터
    │
    ▼
조사 결과 분석
    │
    ▼
구현 계획 수립:
  - 작업 범위 분할
  - 워커 간 의존성 정의
  - 파일/컴포넌트별 담당 워커 배정
```

이 단계는 코디네이터 자체의 추론 과정이며 도구 호출 없이 진행됩니다.

### 단계 3: Implementation (구현)

```
코디네이터
    │
    ├─ Agent("백엔드 API 구현: src/api/users.ts") → 워커 D
    ├─ Agent("프론트엔드 컴포넌트: src/ui/UserList.tsx") → 워커 E
    └─ Agent("테스트 작성: tests/users.test.ts") → 워커 F
    │
    ▼
진행 상황 모니터링 (SendMessage로 중간 확인)
    │
    ▼
완료된 워커 결과 수집
```

### 단계 4: Verification (검증)

```
코디네이터
    │
    ▼
Agent("구현 결과 검증 및 통합 테스트") → 워커 G
    │
    ▼
검증 결과 수신
    │
    ├─ 성공 → SyntheticOutput으로 최종 보고
    └─ 실패 → 실패한 워커 재스폰 또는 수정 지시
```

---

## 4. 워커 통신 우선순위

코디네이터와 워커 에이전트 간 통신은 환경에 따라 다음 채널 중 가장 빠른 것을 사용합니다.

| 우선순위 | 채널 | 설명 | 지연 |
|---------|------|------|------|
| 1순위 | **UDS (Unix Domain Socket)** | 로컬 소켓 파일 통신 | 매우 낮음 |
| 2순위 | **Bridge** | 프로세스 간 브릿지 레이어 | 낮음 |
| 3순위 | **In-process** | 동일 프로세스 내 직접 호출 | 최소 |
| 4순위 | **File mailbox** | 파일 시스템 기반 메시지 교환 | 중간 |

File mailbox는 UDS나 Bridge가 사용 불가능한 환경(예: 컨테이너 간 통신)에서 폴백으로 사용됩니다.

```
# File mailbox 경로 (기본값)
/tmp/claude-coordinator-mailbox/
    ├── inbox/    # 코디네이터 → 워커 메시지
    └── outbox/   # 워커 → 코디네이터 응답
```

---

## 5. 모범 사례 (Best Practices)

### 5.1 구체적인 지시 사용

코디네이터가 워커에게 지시할 때는 모호한 표현 대신 구체적이고 실행 가능한 지시를 사용합니다.

```
나쁜 예:
Agent("인증 관련 코드 수정해줘")

좋은 예:
Agent("""
파일: src/auth/jwt.ts
작업: refreshToken() 함수에서 만료 시간을 30분에서 60분으로 변경.
      변경 후 src/auth/jwt.test.ts의 기존 테스트가 통과하는지 확인.
      테스트 실패 시 테스트도 함께 수정.
""")
```

### 5.2 코디네이터는 코드에 직접 접근하지 않는다

Coordinator Mode의 핵심 원칙입니다.

```
금지 (코디네이터가 직접):
- 파일 읽기/쓰기
- Bash 명령 실행
- 코드 수정

허용 (워커를 통해):
- "이 파일의 내용을 읽고 알려줘" → Agent 위임
- "이 테스트를 실행하고 결과 알려줘" → Agent 위임
```

### 5.3 워커 작업 범위 분리

여러 워커를 동시에 스폰할 때는 파일 충돌이 없도록 작업 범위를 명확히 분리합니다.

```
올바른 분리:
  워커 A: src/api/users.ts (독립적)
  워커 B: src/api/products.ts (독립적)
  워커 C: src/components/Header.tsx (독립적)

잘못된 분리 (충돌 위험):
  워커 A: src/api/ 전체 수정
  워커 B: src/api/users.ts 수정 (A와 충돌 가능)
```

### 5.4 단계별 동기화 포인트 설정

복잡한 구현에서는 각 단계 완료 후 검증 단계를 명시적으로 추가합니다.

```
Research 완료 → 코디네이터 합성 → Implementation 시작
    ↓
Implementation 완료 → Verification 워커 → 결과 확인
    ↓
검증 통과 → 최종 보고 / 검증 실패 → 수정 워커 재스폰
```

---

## 6. 일반 모드와 비교

| 항목 | 일반 모드 | Coordinator Mode |
|------|----------|-----------------|
| 코드 직접 접근 | 가능 | 불가 (워커에 위임) |
| 도구 수 | 전체 | Agent/SendMessage/TaskStop/SyntheticOutput (4개) |
| 적합한 규모 | 단일~중형 작업 | 대형 멀티팀 작업 |
| 컨텍스트 공유 | 단일 컨텍스트 | 코디네이터 + 워커 각자의 독립 컨텍스트 |
| 속도 | 빠름 | 오케스트레이션 오버헤드 있음 |
| 비용 | 낮음~중간 | 워커 수만큼 비용 증가 |

---

## 7. 사용 사례

### 7.1 대규모 리팩토링

```
코디네이터: "express에서 fastify로 전체 마이그레이션"
    ├─ 워커 A: 패키지 의존성 분석
    ├─ 워커 B: 라우터 파일 변환 (routes/*.ts)
    ├─ 워커 C: 미들웨어 변환 (middleware/*.ts)
    ├─ 워커 D: 테스트 업데이트 (tests/*.ts)
    └─ 워커 E: 검증 및 통합 테스트
```

### 7.2 멀티 서비스 배포 준비

```
코디네이터: "v2.0 릴리즈 준비"
    ├─ 워커 A: CHANGELOG.md 생성
    ├─ 워커 B: API 문서 업데이트
    ├─ 워커 C: 버전 범프 (package.json, pyproject.toml)
    ├─ 워커 D: Docker 이미지 빌드 테스트
    └─ 워커 E: 최종 검증
```

---

## 관련 문서

- [도구 동시성 모델](22-tool-concurrency-model.md) - Agent 병렬 실행 상세
- [Agent Frontmatter 스키마](21-agent-frontmatter-schema.md) - 워커 에이전트 설정
- [환경변수 레퍼런스](16-environment-variables.md) - `CLAUDE_CODE_COORDINATOR_MODE` 포함 전체 환경변수
- [v3.0 아키텍처](12-v3-architecture.md) - 멀티에이전트 팀 시스템 전체 설계
