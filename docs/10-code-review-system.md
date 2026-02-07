# 코드 리뷰 시스템 v2.0

## 개요

6명의 전문 리뷰어 에이전트를 활용한 체계적 코드 리뷰 시스템입니다.
3단계 프리셋(quick/standard/thorough)과 하이브리드 실행 모드를 지원합니다.

---

## 1. 전문 리뷰어

### 리뷰어 페르소나

| 리뷰어 | 페르소나 | 핵심 관점 | 전문 분야 |
|--------|---------|----------|----------|
| Security Reviewer | Security Sentinel | "공격자에게 노출되면?" | OWASP Top 10, 인증/인가, 시크릿 |
| Performance Reviewer | Performance Prophet | "트래픽 10배면?" | 복잡도, N+1, 메모리, 번들 |
| Test Coverage Reviewer | Test Guardian | "이 테스트가 진짜 검증하나?" | assertion 품질, 격리, 피라미드 |
| Accessibility Reviewer | Access Advocate | "장애인도 쓸 수 있나?" | WCAG 2.1 AA, 키보드, 스크린리더 |
| UX Reviewer | UX Harmonizer | "사용자가 혼란스럽지 않나?" | 디자인 시스템, 반응형, 상태 처리 |
| API Reviewer | API Arbiter | "1년 후에도 호환되나?" | REST 규약, 버전, 하위호환 |

### 조건부 실행
- **항상 실행**: Security, Performance, Test Coverage
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

## 3. 6단계 워크플로우

```
Phase 1: 자동 분석 (병렬)
  ├── QA: 린트 분석
  ├── Security: 자동 보안 스캔 + 의존성 감사
  ├── QA: 테스트 커버리지
  └── Explorer: 복잡도 분석
       ↓
Phase 2: 보안 & 성능 심층 리뷰 (병렬)
  ├── Security Reviewer: OWASP, 인증, 입력검증
  └── Performance Reviewer: 복잡도, N+1, 번들
       ↓
Phase 3: 아키텍처 & API 리뷰 (병렬)
  ├── Architect: 설계 패턴, SoC, 확장성
  └── API Reviewer: REST 규약, 버전, 호환성 (조건부)
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
Phase 6: 종합 판정
  └── PM: 전체 리뷰 종합, 판정, PR 코멘트 생성
```

---

## 4. 심각도 분류 (통일 기준)

| Level | 의미 | 예시 | 조치 |
|-------|------|------|------|
| **CRITICAL** | 즉시 악용/장애 가능 | SQL Injection, 메모리 누수, API 계약 파괴 | 배포 차단, 즉시 수정 |
| **HIGH** | 조건부 위험/사용자 영향 | XSS, N+1 쿼리, 폼 라벨 누락 | 다음 배포 전 수정 필수 |
| **MEDIUM** | 잠재적 이슈 | 과도한 CORS, SELECT *, 디자인 불일치 | 계획적 수정 |
| **LOW** | 개선 권장 | 보안 헤더 누락, 미세 최적화 | 선택적 |

---

## 5. 프로젝트 타입별 리뷰

| 타입 | 중점 영역 | 스킵 |
|------|----------|------|
| `nextjs` | FE 성능, SSR, 접근성, API 라우트 | - |
| `fastapi` | API 계약, DB 쿼리, 입력 검증 | 접근성, UX |
| `static-pwa` | 번들, 서비스워커, 오프라인, 접근성 | DB, API 계약 |

---

## 6. 하이브리드 실행 모드

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
├── 5명 Teammate 독립 병렬
├── 각 Teammate = 독립 컨텍스트 + 역할 병합
│   ├── T1: Security
│   ├── T2: Performance + DB
│   ├── T3: Architecture + API
│   ├── T4: Logic + Test Quality
│   └── T5: Accessibility + UX
└── 최대 병렬 처리
```

---

## 7. 퀵 커맨드

```
"빠른 리뷰: [설명]"       → quick 프리셋 (~2분)
"리뷰: [설명]"            → standard 프리셋 (~10분, 기본)
"상세 리뷰: [설명]"       → thorough 프리셋 (~20분)
"팀 리뷰: [설명]"         → Agent Teams 모드 + thorough
```

---

## 8. 품질 게이트

### 코드 리뷰 승인 전 필수
- Security Reviewer의 CRITICAL 이슈 없음
- Performance Reviewer의 CRITICAL 이슈 없음

### 리뷰 기준
```
필수 통과:
- CRITICAL 보안 이슈 없음
- CRITICAL 성능 이슈 없음
- 테스트 통과
- 린트 에러 없음

권장 통과:
- 커버리지 80% 이상
- 복잡도 10 이하
- HIGH 이슈 없음

선택:
- 문서 업데이트
- 변경 로그 업데이트
- 접근성 통과
```

---

## 9. 리뷰 히스토리

리뷰 결과는 `~/.claude/team/artifacts/reviews/`에 90일간 보관됩니다.
추세 분석을 통해 반복되는 이슈 패턴을 식별할 수 있습니다.

---

## 10. 설정 파일

| 파일 | 용도 |
|------|------|
| `~/.claude/team/agents.yaml` | 에이전트 정의 (15개) |
| `~/.claude/team/workflows/code-review.yaml` | 워크플로우 (6단계, 3프리셋) |
| `~/.claude/team/prompts/*-reviewer.md` | 리뷰어 상세 프롬프트 (6개) |
| `~/.claude/agents/*.md` | 공식 서브에이전트 (14개) |
| `~/.claude/team/templates/review-*.md` | 프로젝트별 리뷰 템플릿 |

---

## 다음 단계

- [에이전트 페르소나](05-agent-personas.md)
- [추천 플러그인](09-recommended-plugins.md)
