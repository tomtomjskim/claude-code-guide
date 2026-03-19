# v3.0 시스템 아키텍처

## 개요

v3.0은 에이전트 간 구조화된 통신, 실패 복구, 지능형 오케스트레이션을 도입한 대규모 업그레이드입니다.

## v2.0 → v3.0 주요 변경사항

| 항목 | v2.0 | v3.0 |
|------|------|------|
| 프롬프트 구조 | 비표준 (에이전트별 상이) | 5-section 표준 템플릿 (16/16) |
| 출력 계약 | 없음 (자유 형식) | Return 5-field 구조 (필수) |
| 바운더리 제약 | 없음 | 에이전트별 2-3개 제약 |
| 컨텍스트 전달 | ad-hoc | Handoff Protocol v1.0 |
| 실패 처리 | 없음 | failure-policy.yaml (retry/escalate/rollback) |
| 모델 선택 | 고정 (sonnet) | 동적 라우팅 (opus/sonnet/haiku) |
| 리뷰어 충돌 | 미처리 | Tiebreaker Protocol (4규칙) |
| 워크플로우 선택 | 수동 | Adaptive Workflow Selection |
| 시스템 검증 | 없음 | validate-system.sh (7항목) |
| 리뷰어 수 | 6명 | 7명 (Code Reviewer 추가) |

## 5-Section 표준 템플릿

모든 에이전트 프롬프트는 다음 6개 섹션을 순서대로 포함합니다.

### 1. Opening
한 줄로 에이전트의 소유 범위와 철학을 정의합니다.
패턴: "Own [domain] as [quality standard], not [anti-pattern]."

예시:
- PM: "Own project orchestration as mission-critical coordination, not task routing."
- Developer: "Own code implementation as production-grade craftsmanship, not feature delivery."
- Security Reviewer: "Own security review as attack surface reduction, not vulnerability checklist theater."

### 2. Working Mode
4단계 작업 흐름:
1. **범위 파악**: 영향 받는 경계/진입점을 매핑
2. **증거 분리**: 확인된 증거와 가설을 구분
3. **최소 개입**: 가장 작은 일관된 개입을 구현
4. **검증**: 정상 경로, 실패 경로, 통합 엣지 각 1건 검증

### 3. Focus On
6-8개의 도메인별 핵심 관심사 목록

### 4. Quality Checks
결과 반환 전 확인해야 할 5개 검증 항목

### 5. Return
표준 출력 계약 (5개 필드):
- **scope**: 분석/변경 범위
- **findings**: 핵심 발견사항 (증거 포함)
- **recommendation**: 최소한의 실행 가능한 다음 단계
- **validation_status**: 검증 완료 vs 추가 검증 필요
- **residual_risk**: 잔여 위험 및 미해결 사항

### 6. Boundary
스코프 크립을 방지하는 2-3개의 "하지 마라" 규칙
패턴: "부모 에이전트가 명시적으로 요청하지 않는 한 [금지 행동]"

## Handoff Protocol

### 개요
에이전트 간 컨텍스트 전달을 위한 표준 계약입니다.

### 핸드오프 스키마
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

### Data Flow Contracts
```
analysis → design:
  explorer.findings + pm.scope → architect

design → preparation:
  architect.artifacts + architect.findings → dba, designer

preparation → implementation:
  dba.artifacts + designer.artifacts + architect.artifacts → developer

implementation → verification:
  developer.artifacts + developer.scope + developer.residual_risk → qa, reviewers

verification → deployment:
  qa.artifacts + qa.validation_status + reviewers.artifacts → publisher

deployment → documentation:
  publisher.artifacts + developer.artifacts + api-reviewer.findings → documenter
```

### agents.yaml에서의 정의
```yaml
developer:
  handoff:
    accepts: [architect, designer, dba]
    produces: [source-code, implementation-report]
    requires_from_upstream: [scope, design_doc]
```

## Failure Recovery

### 정책 구조
```yaml
failure_policies:
  retry:         # 멱등 태스크 (탐색, 문서화, 리뷰, 테스트)
  escalate:      # 복잡한 태스크 (구현, 스키마 변경, 설계)
  rollback:      # 배포/마이그레이션 태스크
  circuit_breaker: # 연속 3회 실패 시 일시 중단
```

### 태스크별 실패 매핑
| 태스크 유형 | on_fail | 비고 |
|------------|---------|------|
| 탐색/분석 | retry | 다른 접근법으로 재시도 |
| 설계 | escalate | 요구사항 재검토 필요 |
| 구현 | escalate | 태스크 재분해 필요 |
| 테스트 | retry → escalate | 환경 이슈 가능 |
| 배포 | rollback → escalate | 즉시 롤백 |
| 스키마 변경 | rollback → escalate | 데이터 보호 우선 |

### 롤백 전략
- **code_rollback**: `git revert HEAD --no-edit`
- **container_rollback**: `docker compose stop/up -d [service]`
- **schema_rollback**: 사전 준비된 롤백 SQL 실행

### 서킷 브레이커
연속 3회 실패 시 워크플로우 자동 일시 중단.
PM이 사용자에게 상황 보고 → 사용자 판단 후 재개.

## Model Routing

### 기본 라우팅
| 모델 | 용도 | 대상 에이전트 |
|------|------|-------------|
| opus | 깊은 추론, 고위험 결정 | architect(복합 설계), PM(중재), security-reviewer(CRITICAL) |
| sonnet | 범용 (기본값) | developer, qa, dba, designer, publisher, documenter, 모든 리뷰어 |
| haiku | 빠른 읽기 전용 | explorer(초기 탐색), 자동화 검사 |

### 동적 오버라이드
| 조건 | 모델 변경 | 이유 |
|------|----------|------|
| 크로스서비스 아키텍처 | architect → opus | 복합 의존성 |
| CRITICAL 보안 이슈 | security-reviewer → opus | 심층 분석 |
| 10+ 파일 변경 | code-reviewer → opus | 통합 영향도 |
| DB 마이그레이션 | dba → opus | 데이터 무결성 |
| 단순 오타/스타일 | all → haiku | 비용 최적화 |

### 라우팅 결정 매트릭스
```
위험도 HIGH + 복잡도 HIGH → opus
위험도 HIGH + 복잡도 LOW → sonnet
위험도 LOW + 복잡도 HIGH → sonnet
위험도 LOW + 복잡도 LOW → haiku (읽기 전용만)
```

## Tiebreaker Protocol

리뷰어 간 심각도 충돌 시 PM이 적용하는 중재 규칙:

### 규칙 1: CRITICAL 항상 우선
어떤 리뷰어든 CRITICAL이면 다른 리뷰어가 이슈 없음이라도 CRITICAL 채택.

### 규칙 2: 도메인 전문성 가중치
| 영역 | 1순위 리뷰어 | 2순위 |
|------|-------------|-------|
| 보안 취약점 | Security Reviewer | Code Reviewer |
| 성능 병목 | Performance Reviewer | Code Reviewer |
| 접근성 | Accessibility Reviewer | UX Reviewer |
| API 호환성 | API Reviewer | Architect |
| 테스트 품질 | Test Coverage Reviewer | QA Engineer |
| UX 일관성 | UX Reviewer | Designer |

### 규칙 3: 증거 기반 판정
확인된 증거 > 추정 > 가설
데이터 기반 > 의견 기반
작은 변경 > 큰 변경

### 규칙 4: 미해결 시 에스컬레이션
양쪽 입장을 요약하여 사용자에게 제시.

## Adaptive Workflow Selection

| 요청 패턴 | 워크플로우 | 이유 |
|-----------|-----------|------|
| 단일 파일 버그 수정 | quick-fix | 최소 4단계 |
| UI만 변경 | standard (DBA 스킵) | DB 불필요 |
| DB 스키마 변경 | migration | 롤백 필수 |
| 복수 서비스 변경 | standard (전체) | 모든 에이전트 |
| 리팩토링 | refactor | 테스트 확인 중심 |
| 긴급/장애 | quick-fix + publisher | 빠른 복구 |

## 시스템 검증

### validate-system.sh
7개 항목을 자동 검증:
1. 16개 프롬프트의 6개 필수 섹션
2. 15개 서브에이전트의 v3.0 Template/Boundary 섹션
3. agents.yaml 버전, handoff_protocol, model_routing
4. 에이전트 핸드오프 블록 수
5. 워크플로우 failure_policy 참조
6. handoff-protocol.md 존재
7. PM 프롬프트 핵심 섹션 (5개)

### 실행
```bash
bash ~/.claude/team/scripts/validate-system.sh
```

## 파일 구조

```
~/.claude/
├── agents/                    # 서브에이전트 정의 (15개, v3.0)
├── team/
│   ├── agents.yaml            # 에이전트 설정 (v3.0)
│   ├── prompts/               # 상세 프롬프트 (16개, 5-section)
│   ├── workflows/             # 워크플로우 (8개 + failure-policy)
│   │   ├── standard.yaml
│   │   ├── quick-fix.yaml
│   │   ├── refactor.yaml
│   │   ├── feature-flag.yaml
│   │   ├── migration.yaml
│   │   ├── code-review.yaml
│   │   ├── incident-response.yaml
│   │   ├── new-project.yaml
│   │   └── failure-policy.yaml  # v3.0 신규
│   ├── context/
│   │   └── handoff-protocol.md  # v3.0 신규
│   ├── scripts/
│   │   └── validate-system.sh   # v3.0 신규
│   ├── docs/
│   │   └── v3-changelog.md      # v3.0 신규
│   ├── templates/
│   └── artifacts/
└── CLAUDE.md                  # 글로벌 설정 (v3.0)
```

## 다음 단계
- [에이전트 페르소나 v3.0](05-agent-personas.md)
- [코드 리뷰 시스템 v3.0](10-code-review-system.md)
