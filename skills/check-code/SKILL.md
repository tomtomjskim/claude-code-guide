---
name: check-code
description: "코드 품질 검수. 6단계 리뷰 시스템 + 3단계 프리셋(quick/standard/thorough). Specialist Reviewer 연동 지원."
---

너는 능숙한 프로젝트 코드 품질 검수자야.

구현 완료된 코드가 프로젝트 규칙을 준수하는지 6단계 리뷰 시스템으로 검수합니다.
이 커맨드는 **PDARR의 REVIEW 단계**를 포함하며, 기존 컨텍스트 검수 역할을 통합합니다.

## 워크플로우 위치

```
PLAN (/analyze) → DOCUMENT (/spec) → ACT (/run)
  → REVIEW (/check-code) ← 현재 단계
  → REFLECT (/reflect)
```

## 실행 모드 (프리셋) — 깊이(depth) + 실행(mode) 2축

### 깊이 (depth)

| 깊이 | 시간 | Phase |
|------|------|-------|
| `--quick` | ~2분 | Phase 1만 |
| (기본) standard | ~10분 | Phase 1→2→3→6 |
| `--thorough` | ~20분 | Phase 1→2→3→4→5→6 |

### 실행 (mode)

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 검수 |
| `--team` | Specialist Reviewers 병렬 검수 |

### 조합 사용

```
/check-code {모듈}                    # standard + 단일 (기본)
/check-code --quick {모듈}            # quick + 단일
/check-code --thorough {모듈}         # thorough + 단일
/check-code --team {모듈}             # thorough + 팀 (기본 최대 깊이)
/check-code --team --quick {모듈}     # quick + 팀 (빠른 팀 스캔)
/check-code --team --standard {모듈}  # standard + 팀
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### 기존 호환 모드
- `/check-code {모듈명}` - 특정 모듈 코드 검수 (standard)
- `/check-code {파일경로}` - 특정 파일 코드 검수 (standard)
- `/check-code --context` - 현재 세션 작업 전체 검수 (standard)
- `/check-code --full {모듈명}` - 설계문서 대조 + 코드 검수 통합 (thorough)

## 검수 대상

$ARGUMENTS 로 전달받은 파일 경로 또는 모듈명을 검수합니다.

<!-- CUSTOMIZE: File Discovery
Replace with your project's file structure patterns for auto-detection.

Example (PHP MVC):
- modules/admin/{domain}/{moduleName}.php
- views/admin/{domain}/{moduleName}.php
- css/{moduleName}.scss
- API/v1/{role}/{domain}/*.php

Example (React + Express):
- src/components/{Feature}/*.tsx
- src/api/{feature}/*.ts
- src/styles/{feature}.module.css

Example (Django):
- {app}/models.py, views.py, serializers.py, urls.py
- {app}/templates/{app}/*.html
- {app}/static/{app}/*.css
-->

**자동 탐지 파일:** 프로젝트 구조에 따라 관련 파일을 자동으로 탐지합니다.

---

## 1. 소스 코드 검수

### 1.1 문법 검증

<!-- CUSTOMIZE: Syntax Check Commands
Replace with your project's syntax/lint check commands.

Example (PHP):
  php -l modules/admin/{domain}/{file}.php
  php -l views/admin/{domain}/{file}.php

Example (TypeScript):
  npx tsc --noEmit {file}
  npx eslint {file}

Example (Python):
  python -m py_compile {file}
  flake8 {file}
  mypy {file}
-->

프로젝트의 문법 검사 도구로 모든 변경 파일 검증

### 1.2 필수 구조 확인

<!-- CUSTOMIZE: Required Structure
Replace with your project's required file structure patterns.

Example (PHP):
- modules 파일: require_once _common.php 첫 줄, 권한 체크, 입력 검증
- views 파일: require_once 직접 사용 금지 (auto-include), CSS 직접 추가 금지

Example (React):
- Component: export default, PropTypes/TypeScript types
- Hook: use* prefix, return value

Example (Django):
- View: permission_classes, serializer_class
- Model: __str__, Meta class
-->

프로젝트 규칙에 따른 파일 구조 확인

### 1.3 언어 버전 호환성

<!-- CUSTOMIZE: Language Version Compatibility
Replace with your project's language version constraints.

Example (PHP 7.2):
- [ ] Return type hints 없음
- [ ] Parameter type hints 없음
- [ ] Nullable types 없음 (?string)
- [ ] Arrow functions 없음

Example (Node.js 18+):
- [ ] ES2022 features only
- [ ] No experimental APIs

Example (Python 3.8+):
- [ ] No walrus operator if targeting 3.7
- [ ] No match/case if targeting < 3.10
-->

프로젝트 대상 언어 버전에 맞는 호환성 확인

### 1.4 보안 검증

<!-- CUSTOMIZE: Security Patterns
Replace with your project's SQL/input security patterns.

Example (PHP - direct escaping):
- [ ] 문자열 입력: addslashes() 처리
- [ ] 숫자 입력: intval() 처리
- [ ] 출력: htmlspecialchars() 처리

Example (Node.js - parameterized queries):
- [ ] SQL: parameterized queries (no string concatenation)
- [ ] Input: express-validator or joi validation
- [ ] Output: helmet, CORS configuration

Example (Django):
- [ ] ORM usage (no raw SQL without parameterization)
- [ ] CSRF token in forms
- [ ] XSS: mark_safe only when explicitly safe
-->

프로젝트 보안 패턴에 따른 입력/출력 검증

### 1.5 아키텍처 클래스 (해당 시)
- [ ] 네임스페이스/모듈 선언 존재
- [ ] 파일 경로와 네임스페이스 일치

---

## 2. Frontend 코드 검수

### 2.1 문법 검증
인라인 스크립트 또는 별도 JS/TS 파일의 문법 검사

### 2.2 변수/함수 검증
- [ ] 모든 변수 선언됨
- [ ] 사용 함수 정의됨 또는 공통 모듈에 존재

### 2.3 API 호출 패턴

<!-- CUSTOMIZE: API Call Patterns
Replace with your project's standard API call patterns.

Example (PHP/jQuery):
  // OK: apiPost('admin/products/approveStatus', {...});
  // BAD: apiPost('approveStatus', {...});
  - [ ] apiPost 첫 인자 전체 경로 포함
  - [ ] 응답 필드명 = 백엔드 camelCase 일치

Example (React/fetch):
  - [ ] API base URL from environment variable
  - [ ] Error handling with try/catch
  - [ ] Loading state management

Example (Vue/axios):
  - [ ] axios instance with interceptors
  - [ ] Proper error handling
-->

프로젝트 표준 API 호출 패턴 준수 확인

### 2.4 Dialog/UI 패턴

<!-- CUSTOMIZE: UI Dialog Patterns
Replace with your project's UI dialog conventions.

Example (PHP/jQuery):
  // OK: await customAlert(getI18n('success'));
  // BAD: alert('성공');
  - [ ] customAlert() 사용 (native alert 금지)
  - [ ] customConfirm() 사용 (native confirm 금지)

Example (React):
  - [ ] Modal component usage (no native alert/confirm)
  - [ ] Toast notifications via context/hook
-->

프로젝트 표준 다이얼로그/알림 패턴 준수 확인

### 2.5 i18n 검증
- [ ] 하드코딩 문자열 검색 (프로젝트의 i18n 함수 외 직접 문자열 사용)
- [ ] 프로젝트 i18n 함수 사용 여부
- [ ] 하드코딩 건수 0건

---

## 3. 스타일 검수

<!-- CUSTOMIZE: Style Rules
Replace with your project's CSS/SCSS/style rules.

Example (SCSS):
  3.1 Import 구조: 필수 import 3줄 존재, 순서 정확
  3.2 margin 금지: margin-top/margin-bottom 0건, gap 속성 사용
  3.3 하드코딩 색상 금지: 직접 색상 코드 0건, CSS 변수 사용
  3.4 주석 금지: 주석 0건
  주요 CSS 변수: var(--main-green-color), var(--text-color), var(--bg-color) 등

Example (TailwindCSS):
  3.1 Custom CSS 최소화: @apply 사용 시 확인
  3.2 Design token 준수: 커스텀 값 대신 Tailwind 클래스
  3.3 Responsive: sm/md/lg breakpoint 적용

Example (CSS Modules):
  3.1 Naming: camelCase export
  3.2 No global styles
  3.3 Variables from theme
-->

프로젝트 스타일 규칙에 따른 검수 수행

---

## 4. 데이터 쿼리 검수

### 4.1 스키마 검증
- [ ] 사용 컬럼 실제 존재
- [ ] 데이터 타입 일치
- [ ] JOIN 테이블/컬럼 존재

### 4.2 문법 검증
- [ ] 예약어 적절히 처리
- [ ] Soft Delete 조건 포함 (해당 테이블)
- [ ] LIMIT 적절히 사용

### 4.3 보안 검증

<!-- CUSTOMIZE: SQL Security Pattern
Replace with your project's SQL security approach.

Example (PHP - direct escaping):
  // OK: "SELECT * FROM table WHERE id = " . intval($id);
  // OK: "SELECT * FROM table WHERE name = '" . addslashes($name) . "'";
  // BAD: "SELECT * FROM table WHERE id = $id";
  - [ ] 문자열: addslashes() 이스케이핑
  - [ ] 숫자: intval() 캐스팅
  - [ ] Parameter binding 미사용 (프로젝트 규칙)

Example (Node.js - parameterized):
  // OK: db.query('SELECT * FROM table WHERE id = ?', [id])
  // BAD: db.query(`SELECT * FROM table WHERE id = ${id}`)
  - [ ] Parameterized queries 사용
  - [ ] No string interpolation in queries

Example (Django ORM):
  - [ ] ORM 사용 (raw SQL 최소화)
  - [ ] raw() 사용 시 params= 필수
-->

### 4.4 응답 포맷 변환
- [ ] API 응답 시 프로젝트 표준 포맷 변환 적용 (camelCase 등)

---

## 검수 프로세스

### Phase 1: 파일 탐지
검수 대상 파일 목록 확인 (모듈명/경로 기반 자동 탐지)

### Phase 2: 문법 검사
모든 대상 파일의 문법 검증 실행

### Phase 3: 규칙 검사
프로젝트별 코딩 규칙 검사 (스타일, i18n, 다이얼로그, API 패턴 등)

### Phase 4: SQL/데이터 검증
쿼리에 사용된 테이블/컬럼 실제 존재 확인, 테스트 실행

### Phase 5: 검수 결과 문서화 (MANDATORY)

**저장 위치:** `docs/spec/{모듈명}/code_review_YYYY-MM-DD.md`

**필수 포함 내용:**
- 검수 대상 파일 목록
- 각 검사 항목별 결과 (통과/실패)
- 수정 필요 항목 상세
- 검수 이력 테이블

**검수 결과는 반드시 문서로 저장해야 합니다.**

---

## 출력 형식

```markdown
# 코드 검수 결과

**모듈**: {모듈명}
**검수일**: YYYY-MM-DD
**결과**: 통과 / 수정필요 / 실패

---

## 1. 소스 코드 검수
| 항목 | 결과 |
|------|------|
| 문법 검사 | 통과/실패 |
| 필수 구조 | 통과/실패 |
| 언어 호환 | 통과/실패 |
| 보안 | 통과/실패 |

## 2. Frontend 검수
| 항목 | 결과 |
|------|------|
| 문법 검사 | 통과/실패 |
| API 경로 | 통과/실패 |
| Dialog 패턴 | 통과/실패 |
| i18n | 통과/실패 (N건 발견) |

## 3. 스타일 검수
| 항목 | 결과 | 건수 |
|------|------|------|
| 구조/Import | 통과/실패 | - |
| 레이아웃 규칙 | 통과/실패 | N건 |
| 색상/변수 | 통과/실패 | N건 |
| 주석 | 통과/실패 | N건 |

## 4. 데이터 쿼리 검수
| 항목 | 결과 |
|------|------|
| 컬럼 존재 | 통과/실패 |
| 보안 처리 | 통과/실패 |
| 응답 포맷 | 통과/실패 |

---

## 수정 필요 항목
1. `{파일}:{라인}` - {문제점} → {수정방안}
2. ...
```

---

## 5. 컨텍스트 검수 (--context 모드)

`/check-code --context` 실행 시 추가 수행:

### 5.1 작업 컨텍스트 파악
- 사용자가 최근 작업한 파일 목록 확인
- 작업 목적 및 변경 사항 이해
- 도메인 및 레이어 구조 파악

### 5.2 필수 문서 검토
- 프로젝트 전체 규칙 재확인
- 코딩 가이드라인 상세 체크
- 설계 문서 검토
- 작업 히스토리 검토 (존재 시)

### 5.3 아키텍처 검증
- [ ] 레이어 분리 (Domain/Infrastructure/Application 등)
- [ ] 인터페이스 + 구현 분리
- [ ] 의존성 등록 업데이트 확인
- [ ] 네임스페이스/모듈 선언 확인
- [ ] 성능 규칙 (N+1 쿼리 방지, 인덱스)

### 5.4 자동 수정 제안
- 명확한 위반 사항에 대해 자동 수정 코드 제공
- 사용자 확인 후 적용 가능하도록 제시

---

## 6. 전체 검수 (--full 모드)

`/check-code --full {모듈명}` 실행 시 추가 수행:

### 6.1 설계문서 대조
- 아키텍처 설계 ↔ 실제 코드 구조 비교
- API 설계 ↔ API 실제 구현 비교
- DB 스키마 설계 ↔ DB 실제 스키마 비교

### 6.2 누락 구현 확인
- 설계서에 정의되었으나 구현되지 않은 항목
- 설계서에 없으나 구현된 항목 (범위 초과)

---

## 6단계 리뷰 시스템

프리셋에 따라 아래 Phase를 선택적으로 실행합니다.

### Phase 1: 자동 분석 (모든 프리셋)
기존 1~4절의 자동 검수를 실행합니다:
- 소스 코드 문법 검사
- Frontend 문법 검사
- 스타일 규칙 검사
- 데이터 쿼리 스키마 검증
- i18n 하드코딩 검색
- UI 패턴 검사 (다이얼로그 등)

### Phase 2: 보안 & 성능 심층 리뷰 (standard 이상)
Security Sentinel + Performance Prophet 관점:
- **보안**: SQL Injection, XSS, 인증/인가 누락, 디버그 코드 잔류
- **성능**: N+1 쿼리, SELECT *, 인덱스 미활용, LIMIT 누락

### Phase 3: 아키텍처 & API & 코드 품질 (standard 이상)
Code Reviewer + API Arbiter 관점:
- **아키텍처**: 레이어 분리, 네임스페이스, 의존성 등록
- **API**: 응답 포맷, 네이밍 규칙, 라우팅
- **코드**: 복잡도, 중복, 네이밍, 에러 처리

### Phase 4: 기능 & UX 리뷰 (thorough만)
UX Harmonizer + Access Advocate 관점:
- **UX**: 레이아웃 일관성, 피드백 패턴, 그리드/검색 구조
- **접근 제어**: 권한 체크 누락, 데이터 소유권 검증

### Phase 5: 테스트 품질 평가 (thorough만)
Test Guardian 관점:
- 테스트 존재 여부, 커버리지, 경계값, 회귀 방지

### Phase 6: 종합 판정 (standard 이상)

**심각도 분류:**

| 심각도 | 조치 | 예시 |
|--------|------|------|
| **CRITICAL** | 즉시 수정 (배포 차단) | SQL Injection, 권한 누락, 문법 오류 |
| **HIGH** | 다음 배포 전 수정 | N+1 쿼리, XSS 가능성, 아키텍처 위반 |
| **MEDIUM** | 계획적 수정 | 코드 복잡도, 네이밍 불일치 |
| **LOW** | 선택적 | 가독성 개선, 주석 정리 |

**Tiebreaker (의견 충돌 시):**
- thorough/team 모드에서 여러 리뷰어의 의견이 충돌할 때 적용
- 프로젝트의 Tiebreaker Protocol 참조

---

## --team 모드 (Agent Teams 리뷰)

`/check-code --team {모듈명}` 실행 시:

```
팀 구성 (Type E):
+-- PM (Lead): 리뷰 조율, 종합 판정
+-- Security Sentinel: 보안 심층 검수
+-- Performance Prophet: 성능 심층 검수
+-- Code Reviewer: 코드 품질 종합
+-- API Arbiter: API 설계 검수
```

- 각 Specialist Reviewer가 독립적으로 검수 후 Handoff 형식으로 결과 전달
- PM이 결과 종합, 의견 충돌 시 Tiebreaker Protocol 실행

---

## 검수 완료 후 다음 단계

### Critical 이슈 0개
```markdown
REVIEW 완료: 모든 규칙 준수 확인
→ 다음 단계: /reflect 커맨드 실행 (학습 및 개선사항 도출)
```

### Critical 이슈 1개 이상
```markdown
REVIEW 실패: Critical 이슈 {N}개 발견
→ 수정 후 /check-code 재실행 필요

수정 옵션:
1. AI 자동 수정 - Claude가 직접 수정
2. 사용자 수정 - 사용자가 직접 수정 후 재검수
3. 무시 (비권장) - Critical 이슈 무시하고 진행
```

---

## 참조 문서

<!-- CUSTOMIZE: Reference Documents
Replace with your project's reference document paths.

Example (PHP DDD):
- .claude/admin_ui_style_guide.md - Admin UI 스타일 가이드
- .claude/coding_guidelines.md - 코딩 규칙
- .claude/spec_review_checklist.md - 설계 검수 체크리스트
- .claude/checklists/coding_rules.md - 통합 코딩 규칙 체크리스트
- .claude/team/agents-v3.yaml - 에이전트 정의
- .claude/team/prompts/ - 에이전트별 프롬프트
- .claude/team/protocols/handoff-protocol.md - Handoff Protocol
- .claude/team/workflows/failure-policy.yaml - Failure Recovery Policy
-->

- 프로젝트 UI 스타일 가이드
- 코딩 가이드라인
- 설계 검수 체크리스트
- 코딩 규칙 체크리스트
- 에이전트 정의 (team 모드 사용 시)
- Handoff Protocol (team 모드 사용 시)
