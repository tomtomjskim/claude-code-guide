---
name: qa-test
description: "QA 자동화. 변경 파일에 대해 난이도별(minimal/basic/standard/full) 종합 QA 테스트 수행 및 리포트 생성."
---
# QA Test - 종합 QA 자동화

변경된 파일에 대해 난이도별 종합 QA 테스트를 수행하고 리포트를 생성합니다.

## 사용법

```
/qa-test                              # 변경 파일 자동 테스트 (난이도 자동)
/qa-test [기능명]                      # 특정 기능 테스트
/qa-test --minimal                    # 최소 테스트 (문법만)
/qa-test --basic                      # 기본 테스트
/qa-test --standard                   # 표준 테스트
/qa-test --full                       # 전체 테스트
/qa-test customerDetailPopup --full   # 특정 기능 전체 테스트
/qa-test --team                       # 팀 에이전트 종합 QA (full + 다관점)
/qa-test --team --basic [기능명]      # 팀 에이전트 + 난이도 조합
```

---

## --team 모드: 팀 에이전트 종합 QA

`--team` 사용 시 5명의 전문가가 **병렬**로 각자 관점에서 QA를 수행합니다.
단일 모드와 달리 **다관점 동시 검증**으로 누락을 최소화합니다.

### 팀 구성 (Type F: QA Team)

| 에이전트 | 역할 | 검증 관점 |
|---------|------|----------|
| **PM** (Lead) | Phase 분배, 결과 종합, 리포트 통합 | 전체 조율 |
| **QA Engineer** | Phase 2~5 실행, 시나리오 검증, DB 상태 확인 | 기능 정합성 |
| **Security Sentinel** | SQL Injection, XSS, 권한 우회, 입력값 조작 테스트 | 보안 취약점 |
| **Performance Prophet** | N+1 쿼리 탐지, 대량 데이터 시나리오, 인덱스 누락 | 성능 병목 |
| **Access Advocate** | 권한별 접근 테스트, 세션 변조, 비인가 API 호출 | 접근 제어 |

### --team 실행 흐름

```
PM: Phase 0 (난이도 판별) + 팀원별 태스크 분배
  +-- QA Engineer:        Phase 2~5 (문법/품질/UI/의존성)
  +-- Security Sentinel:  보안 테스트 (Phase 3 확장)
  +-- Performance Prophet: 성능 테스트 (Phase 3 확장)
  +-- Access Advocate:    접근 제어 테스트 (Phase 4 확장)
PM: Phase 6~7 (종합 리포트 생성 + 이전 비교)
```

### --team 난이도 조합

```
--team 단독     = full + 팀 (기본 최대 깊이)
--team --minimal = minimal + 팀 (문법만 다관점)
--team --basic   = basic + 팀
--team --standard = standard + 팀
--team --full    = full + 팀 (명시적)
```

### --team 리포트 추가 섹션

단일 모드 리포트에 아래 섹션이 추가됩니다:

```markdown
## 보안 테스트 결과 (Security Sentinel)
| 항목 | 테스트 | 결과 |
|------|--------|------|
| SQL Injection | 입력값 이스케이핑 적용 여부 | 통과/실패 |
| XSS | 출력 이스케이핑 적용 여부 | 통과/실패 |
| 권한 우회 | 비인가 접근 시도 | 통과/실패 |

## 성능 테스트 결과 (Performance Prophet)
| 항목 | 테스트 | 결과 |
|------|--------|------|
| N+1 쿼리 | 루프 내 쿼리 탐지 | 통과/실패 |
| 인덱스 | WHERE 절 컬럼 인덱스 확인 | 통과/경고 |
| 대량 데이터 | LIMIT 없는 SELECT | 통과/실패 |

## 접근 제어 테스트 결과 (Access Advocate)
| 항목 | 테스트 | 결과 |
|------|--------|------|
| 세션 검증 | 비로그인 접근 차단 | 통과/실패 |
| 권한 체크 | 타 역할 접근 차단 | 통과/실패 |
| API 권한 | 비인가 API 호출 차단 | 통과/실패 |
```

### --team 의견 충돌 시

Tiebreaker Protocol 적용:
1. CRITICAL 이슈 우선
2. 도메인 전문성 가중치 (보안 → Security Sentinel, 성능 → Performance Prophet)
3. 증거 기반 판정 (보안 표준, 프로젝트 규칙, 측정 데이터)
4. 해결 불가 시 사용자 에스컬레이션

---

## 단일 모드 자동 수행 작업

### Phase 0: 난이도 판별

**자동 판별 규칙:**

<!-- CUSTOMIZE: Difficulty Classification
Replace with your project's file patterns for automatic difficulty classification.

Example (PHP MVC):
| 파일 패턴 | 난이도 |
|----------|--------|
| config/, i18n/, *.json, *.md | Minimal |
| classes/, util/, 단순 헬퍼 | Basic |
| views/, modules/ (목록, 일반) | Standard |
| 결제, 인증, 주문, 핵심 CRUD, 팝업 | Full |

Example (React + Express):
| 파일 패턴 | 난이도 |
|----------|--------|
| *.config.*, *.json, *.md | Minimal |
| utils/, helpers/, types/ | Basic |
| components/, pages/ (일반) | Standard |
| auth/, payment/, checkout/ | Full |

Example (Django):
| 파일 패턴 | 난이도 |
|----------|--------|
| settings/, *.json, *.md | Minimal |
| utils/, management/commands/ | Basic |
| views/, templates/ (일반) | Standard |
| payment/, auth/, order/ | Full |
-->

| 파일 패턴 | 난이도 |
|----------|--------|
| 설정, 정적 파일, 문서 | Minimal |
| 유틸리티, 헬퍼, 타입 정의 | Basic |
| 일반 뷰/페이지/컴포넌트 | Standard |
| 결제, 인증, 주문 등 핵심 비즈니스 로직 | Full |

**난이도별 테스트 범위:**
| Level | 문법 | 품질 | UI/이벤트 | 시나리오 | E2E |
|-------|------|------|----------|---------|-----|
| Minimal | O | - | - | - | - |
| Basic | O | O | - | - | - |
| Standard | O | O | O | O | - |
| Full | O | O | O | O | O |

---

### Phase 1: 변경 파일 분석

```bash
git diff --name-only HEAD
```

- 변경 파일 목록 확인
- 파일별 역할 분류
- 난이도 자동 결정 (또는 사용자 지정 사용)

---

### Phase 2: 문법 검증 (All Levels)

<!-- CUSTOMIZE: Syntax Check Commands
Replace with your project's syntax check commands.

Example (PHP): php -l [파일]
Example (TypeScript): npx tsc --noEmit [파일] && npx eslint [파일]
Example (Python): python -m py_compile [파일] && flake8 [파일]
-->

- 프로젝트 문법 검사 도구로 모든 변경 파일 검증
- 오류 시 위치와 수정 방안 제시

---

### Phase 3: 코드 품질 검증 (Basic+)

변경된 파일 읽고 검증:

| 항목 | 검증 내용 |
|------|----------|
| SQL Injection | 입력값 이스케이핑/파라미터화 사용 여부 |
| XSS | 출력 이스케이핑 처리 여부 |
| 미정의 변수 | 초기화 없이 사용되는 변수 |
| 괄호 불일치 | 열린/닫힌 괄호 수 일치 |
| 이벤트 바인딩 | 이벤트 핸들러 존재 확인 |

---

### Phase 4: UI/이벤트 시나리오 (Standard+)

변경된 View/Module 파일 분석:

**1. 접근 경로**
- 라우팅에서 URL 확인
- 필수 파라미터 확인

**2. UI 요소 검증**
- 필수 HTML 요소 존재 (form, table, button 등)
- CSS 클래스 사용 일관성
- 조건부 렌더링 로직

**3. 이벤트 동작**
- 이벤트 핸들러 (클릭, 변경 등)
- API 호출 함수
- 팝업/모달 열기/닫기

**4. 입출력 검증**
- 필수 입력 필드
- 출력 데이터 포맷

---

### Phase 5: 의존성 분석 (Standard+)

- 변경 파일이 참조하는 다른 파일
- 변경으로 영향받을 수 있는 파일
- 사이드이펙트 위험도 평가

---

### Phase 6: 리포트 생성

**리포트 저장:**
```
docs/qa-reports/YYYY-MM-DD_[기능명].md
```

**summary.md 업데이트:**
- 최근 테스트 목록 추가
- 통계 업데이트
- 미해결 이슈 반영

---

### Phase 7: 이전 리포트 비교 (있으면)

- 이전 테스트 결과와 diff
- 새로 발생한 이슈 하이라이트
- 품질 변화 추이

---

## 출력 형식

```
==========================================
QA Test Report: [기능명]
==========================================
Date: YYYY-MM-DD
Level: Standard
Result: PASS

## 변경 파일 (N개)
- path/to/module.file (Module)
- path/to/view.file (View)

## 테스트 결과
| Phase | 항목 | 결과 |
|-------|------|------|
| 2 | 문법 검증 | 2/2 |
| 3 | 코드 품질 | 통과 |
| 4 | UI/이벤트 | 5/5 |
| 5 | 의존성 | 2개 영향 |

## 시나리오 체크리스트
- [x] 페이지 접근: GET /path/to/page
- [x] UI: 필수 요소 렌더링
- [x] 이벤트: 버튼 클릭 동작
- [x] 입력: 필수값 검증
- [x] 출력: 데이터 표시

## 발견 이슈
없음 (또는 목록)

## Console 에러 체크 (수동)
(프로젝트별 콘솔 에러 체크 명령)

==========================================
리포트 저장: docs/qa-reports/YYYY-MM-DD_[기능명].md
summary.md 업데이트 완료
==========================================
```

---

## 실행 지침

**위 Phase 0~7을 순서대로 자동 실행하세요.**

1. `$ARGUMENTS` 파싱 (기능명, --level 옵션)
2. 난이도 결정
3. 해당 난이도의 Phase만 실행
4. 결과 리포트 생성 및 저장
5. summary.md 업데이트
6. 결과 출력

**말없이 바로 실행하고 리포트를 출력하세요.**
