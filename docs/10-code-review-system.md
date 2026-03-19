# 코드 리뷰 시스템 v3.0

## 개요

7명의 전문 리뷰어 에이전트를 활용한 체계적 코드 리뷰 시스템입니다.
v3.0에서는 Code Reviewer(7번째 리뷰어)가 추가되었으며, Tiebreaker Protocol, Model Routing,
Failure Recovery, Explorer 통합 분석이 새로운 기능으로 포함됩니다.

3단계 프리셋(quick/standard/thorough)과 하이브리드 실행 모드를 지원합니다.

---

## 1. 전문 리뷰어 (7개, v3.0)

### 리뷰어 페르소나

| 리뷰어 | 페르소나 | 핵심 관점 | 전문 분야 |
|--------|---------|----------|----------|
| Security Reviewer | Security Sentinel | "공격자에게 노출되면?" | OWASP Top 10, 인증/인가, 시크릿 |
| Performance Reviewer | Performance Prophet | "트래픽 10배면?" | 복잡도, N+1, 메모리, 번들 |
| Test Coverage Reviewer | Test Guardian | "이 테스트가 진짜 검증하나?" | assertion 품질, 격리, 피라미드 |
| Accessibility Reviewer | Access Advocate | "장애인도 쓸 수 있나?" | WCAG 2.1 AA, 키보드, 스크린리더 |
| UX Reviewer | UX Harmonizer | "사용자가 혼란스럽지 않나?" | 디자인 시스템, 반응형, 상태 처리 |
| API Reviewer | API Arbiter | "1년 후에도 호환되나?" | REST 규약, 버전, 하위호환 |
| **Code Reviewer** *(v3.0 신규)* | **Code Reviewer** | **"이 코드가 프로덕션 준비가 되었나?"** | **가독성, 유지보수성, 코드 냄새** |

### 조건부 실행

- **항상 실행**: Security, Performance, Test Coverage, **Code Reviewer (v3.0 추가)**
- **UI 변경 시**: Accessibility, UX
- **API 변경 시**: API

---

## 2. 리뷰 프리셋

| 프리셋 | 단계 | 예상 시간 | 용도 |
|--------|------|----------|------|
| `quick` | Phase 1만 | ~2분 | 자동 분석만 (린트, 보안스캔, 커버리지) |
| `standard` | Phase 1→2→3→6 | ~10분 | 일반 PR (기본값) |
| `thorough` | 전체 6단계 | ~20분 | 중요 변경, 릴리즈 전 |

### 프리셋 선택 가이드
```
단순 수정/설정 변경?         → quick
일반 기능 추가/버그 수정?    → standard
릴리즈 전/보안 관련?         → thorough
중요 대규모 변경?            → 팀 리뷰 (Agent Teams + thorough)
```

---

## 3. 6단계 워크플로우 (v3.0)

```
Phase 1: 자동 분석 (병렬)
  ├── QA: 린트 분석
  ├── Security: 자동 보안 스캔 + 의존성 감사
  ├── QA: 테스트 커버리지
  └── Explorer: 복잡도 분석 + 코드 조직화 분석  ← v3.0 강화
       ↓
Phase 2: 보안 & 성능 심층 리뷰 (병렬)
  ├── Security Reviewer: OWASP, 인증, 입력검증
  └── Performance Reviewer: 복잡도, N+1, 번들
       ↓
Phase 3: 아키텍처 & API & 코드 품질 리뷰 (병렬)  ← v3.0 변경
  ├── Architect: 설계 패턴, SoC, 확장성
  ├── API Reviewer: REST 규약, 버전, 호환성 (조건부)
  ├── Explorer: code_organization_analysis  ← v3.0 신규
  └── Code Reviewer: 가독성, 유지보수성, 코드 냄새  ← v3.0 신규
       ↓
Phase 4: 기능 & UX 리뷰 (병렬)
  ├── Developer: 로직, 엣지케이스, 에러처리
  ├── Accessibility Reviewer: WCAG 2.1 AA (조건부)
  ├── UX Reviewer: 디자인 시스템 준수 (조건부)
  └── DBA: 쿼리 성능, 인덱스 (조건부)
       ↓
Phase 5: 테스트 품질 평가
  └── Test Coverage Reviewer: assertion 품질, 격리, 피라미드
       ↓
Phase 6: 종합 판정 (v3.0: Tiebreaker 포함)
  └── PM: 전체 리뷰 종합, Tiebreaker, 판정, PR 코멘트 생성
```

### Phase 3의 Explorer 통합 (v3.0 신규)

Phase 3에서 Explorer는 `code_organization_analysis`를 수행합니다:

```yaml
code_organization_analysis:
  checks:
    - module_boundaries: "모듈 경계가 적절히 분리되었는가"
    - circular_dependencies: "순환 의존성이 새로 생겼는가"
    - file_size_growth: "특정 파일이 비정상적으로 커졌는가"
    - naming_consistency: "변경된 파일의 명명 규칙이 일관성이 있는가"
  output: "code_organization_report"
  feeds_into:
    - Code Reviewer (Phase 3)
    - Architect (Phase 3)
```

---

## 4. 심각도 분류 (통일 기준)

| Level | 의미 | 예시 | 조치 |
|-------|------|------|------|
| **CRITICAL** | 즉시 악용/장애 가능 | SQL Injection, 메모리 누수, API 계약 파괴, 인증 우회 | 배포 차단, 즉시 수정 |
| **HIGH** | 조건부 위험/사용자 영향 | XSS, N+1 쿼리, 폼 라벨 누락, 심각한 코드 중복 | 다음 배포 전 수정 필수 |
| **MEDIUM** | 잠재적 이슈 | 과도한 CORS, SELECT *, 디자인 불일치, 불명확한 명명 | 계획적 수정 |
| **LOW** | 개선 권장 | 보안 헤더 누락, 미세 최적화, 스타일 개선 | 선택적 |

---

## 5. 프로젝트 타입별 리뷰

| 타입 | 중점 영역 | 스킵 |
|------|----------|------|
| `nextjs` | FE 성능, SSR, 접근성, API 라우트, Code 품질 | - |
| `fastapi` | API 계약, DB 쿼리, 입력 검증, Code 품질 | 접근성, UX |
| `static-pwa` | 번들, 서비스워커, 오프라인, 접근성 | DB, API 계약 |

---

## 6. v3.0 신규 기능

### Tiebreaker Protocol

복수의 리뷰어 의견이 충돌할 때 PM이 다음 절차로 판정합니다.

```
단계 1: CRITICAL 우선
  → CRITICAL 이슈를 가진 리뷰어가 항상 우선합니다
  → CRITICAL이 복수인 경우 단계 2로 이동합니다

단계 2: 도메인 전문성 가중치
  → 보안 이슈   : Security Sentinel 우선
  → 성능 이슈   : Performance Prophet 우선
  → 테스트 이슈 : Test Guardian 우선
  → API 계약    : API Arbiter 우선
  → 코드 품질   : Code Reviewer 우선

단계 3: 증거 기반 판정
  → RFC, OWASP, WCAG 등 표준 문서 인용
  → 벤치마크 데이터 또는 실제 로그 증거
  → 기존 코드베이스의 선례

단계 4: 에스컬레이션
  → 1-3단계로 해결되지 않으면 사용자에게 에스컬레이션
  → PM은 각 리뷰어 의견과 근거를 요약하여 제시
```

**실제 충돌 시나리오 예시**:
```
상황: Performance Prophet이 캐싱 추가를 MEDIUM으로 권장
      Code Reviewer가 과도한 복잡성 추가를 HIGH로 경고

Tiebreaker 판정:
→ HIGH vs MEDIUM → Code Reviewer 우선 (단계 2: 심각도 우선)
→ PM 최종 결정: 캐싱 단순화 또는 캐싱 제거 후 실제 성능 측정 먼저
```

---

### Model Routing (v3.0)

태스크 복잡도에 따라 최적 모델을 자동 선택합니다.

| 모델 | 용도 | 리뷰 적용 대상 |
|------|------|--------------|
| `claude-opus` | 깊은 추론, 고위험 | Security (CRITICAL 발견 시), PM 중재, 복합 아키텍처 리뷰 |
| `claude-sonnet` | 범용 (기본값) | 대부분의 리뷰어 |
| `claude-haiku` | 빠른 읽기 전용 | Explorer Phase 1 초기 탐색 |

```yaml
# code-review.yaml 모델 라우팅 정의
model_routing:
  phase1_exploration:
    model: haiku
    reason: "빠른 파일 스캔, 깊은 추론 불필요"

  phase2_security_critical:
    model: opus
    trigger: "security_reviewer.severity == CRITICAL"
    reason: "CRITICAL 보안 이슈는 깊은 추론 필요"

  phase6_tiebreaker:
    model: opus
    trigger: "conflicting_reviewer_opinions == true"
    reason: "중재 판정은 복잡한 추론 필요"

  default:
    model: sonnet
```

---

### Failure Recovery (v3.0)

리뷰 워크플로우 실패 시 `failure-policy.yaml`에 정의된 정책을 적용합니다.

```yaml
# 리뷰 실패 정책
code_review_failures:
  reviewer_timeout:
    on_fail: retry
    max_retries: 1
    fallback: "skip_reviewer_with_warning"

  phase_failure:
    on_fail: escalate
    message: "Phase {n} 리뷰 실패 - 수동 확인 필요"

  circuit_breaker:
    threshold: 3      # Phase 내 연속 3개 리뷰어 실패
    action: pause_review
    resume: manual
```

**실패 시나리오별 처리**:
| 시나리오 | 정책 | 결과 |
|---------|------|------|
| 개별 리뷰어 타임아웃 | retry 1회 → skip with WARN | 리뷰 결과에 누락 표시 |
| Phase 전체 실패 | escalate → 사용자 확인 | 워크플로우 일시 중단 |
| 연속 3개 리뷰어 실패 | circuit-breaker → 중단 | 수동 재개 필요 |

---

## 7. 하이브리드 실행 모드

### 서브에이전트 모드 (기본)
```
PM이 Task()로 순차/병렬 스폰
├── 비용 효율적
├── 단일 컨텍스트 내 격리
└── 최대 4개 병렬
```

### Agent Teams 모드 (확장)
```
"팀 리뷰" 키워드로 활성화
├── 6명 Teammate 독립 병렬 (v3.0: +Code Reviewer)
├── 각 Teammate = 독립 컨텍스트 + 역할 병합
│   ├── T1: Security
│   ├── T2: Performance + DB
│   ├── T3: Architecture + API + Code Quality
│   ├── T4: Logic + Test Quality
│   ├── T5: Accessibility + UX
│   └── T6: Code Reviewer (v3.0 신규)
└── 최대 병렬 처리
```

---

## 8. 퀵 커맨드

```
"빠른 리뷰: [설명]"       → quick 프리셋 (~2분)
"리뷰: [설명]"            → standard 프리셋 (~10분, 기본)
"상세 리뷰: [설명]"       → thorough 프리셋 (~20분)
"팀 리뷰: [설명]"         → Agent Teams 모드 + thorough
```

---

## 9. 품질 게이트

### 코드 리뷰 승인 전 필수 (v3.0 강화)

```
필수 통과 (FAIL → 배포 차단):
  - Security Reviewer의 CRITICAL 이슈 없음
  - Performance Reviewer의 CRITICAL 이슈 없음
  - Code Reviewer의 CRITICAL 이슈 없음  ← v3.0 추가
  - 테스트 통과
  - 린트 에러 없음

권장 통과 (WARN → 조건부 진행):
  - 커버리지 80% 이상
  - 사이클로매틱 복잡도 10 이하
  - HIGH 이슈 없음

선택:
  - 문서 업데이트
  - 변경 로그 업데이트
  - 접근성 통과
```

### 자동 게이트 체크 스크립트

```bash
# validate-system.sh (v3.0 신규)
#!/bin/bash
# 배포 전 자동 품질 게이트 검증

run_lint_check()         # 린트 오류 확인
run_test_suite()         # 테스트 통과 확인
check_security_scan()    # 보안 스캔 결과 확인
check_coverage()         # 커버리지 임계값 확인
validate_build()         # 빌드 성공 확인
```

---

## 10. 리뷰 히스토리

리뷰 결과는 `~/.claude/team/artifacts/reviews/`에 90일간 보관됩니다.
추세 분석을 통해 반복되는 이슈 패턴을 식별할 수 있습니다.

**히스토리 파일 구조**:
```
~/.claude/team/artifacts/reviews/
  ├── YYYY-MM-DD-{project}-{preset}.md   # 리뷰 결과
  ├── trends/
  │   ├── security-issues.json           # 보안 이슈 추세
  │   ├── performance-issues.json        # 성능 이슈 추세
  │   └── code-quality.json              # 코드 품질 추세
  └── summary/
      └── YYYY-MM.md                     # 월별 요약
```

---

## 11. 설정 파일 (v3.0)

| 파일 | 용도 |
|------|------|
| `~/.claude/team/agents.yaml` | 에이전트 정의 v3.0 (16개: 9 core + 7 reviewer) |
| `~/.claude/team/workflows/code-review.yaml` | 리뷰 워크플로우 (7-reviewer, 3 presets, model routing) |
| `~/.claude/team/prompts/*-reviewer.md` | 리뷰어 상세 프롬프트 (7개, code-reviewer.md 신규) |
| `~/.claude/agents/*.md` | 공식 서브에이전트 (14개) |
| `~/.claude/team/templates/review-*.md` | 프로젝트별 리뷰 템플릿 |
| `~/.claude/team/protocols/handoff-protocol.md` | 핸드오프 데이터 계약 *(v3.0 신규)* |
| `~/.claude/team/protocols/failure-policy.yaml` | 실패 복구 정책 *(v3.0 신규)* |
| `scripts/validate-system.sh` | 배포 전 시스템 검증 스크립트 *(v3.0 신규)* |

---

## 다음 단계

- [에이전트 페르소나 v3.0](05-agent-personas.md)
- [추천 플러그인](09-recommended-plugins.md)
- [워크플로우 가이드](08-workflows.md)
