---
name: qa-e2e
description: "E2E 비즈니스 로직 테스트. test_scenarios.md 기반으로 비즈니스 프로세스의 시나리오별 테스트를 실행하고 DB 검증까지 수행. --browser 모드로 Playwright 브라우저 E2E 테스트 지원. /qa-e2e {모듈명} 또는 /qa-e2e {시나리오파일경로}. 테스트 시나리오 문서가 있을 때, 비즈니스 프로세스 검증이 필요할 때, 배포 전 e2e 확인이 필요할 때 사용."
---

# QA E2E - 비즈니스 로직 End-to-End 테스트

테스트 시나리오 문서(test_scenarios.md)를 기반으로 비즈니스 프로세스를 단계별로 검증합니다.
코드 품질 검수(/qa-test, /check-code)와 다르게 **실제 비즈니스 흐름과 데이터 정합성**을 검증합니다.

## 사용법 <!-- PRESET_CANONICAL_LINK -->

**프리셋 체계는 [`CLAUDE.md` §PDARR + preset system](../../CLAUDE.md#pdarr--preset-system)과 [`docs/14-preset-system.md#qa-e2e-프리셋`](../../docs/14-preset-system.md)에서 canonical로 관리합니다.**

> **qa-e2e는 depth 축을 적용하지 않습니다** — E2E는 시나리오 기반이므로 "깊이를 줄여 부분만 실행"이 아닌 **`--tc TC-N`으로 TC 단위 필터**로 범위를 제어합니다. execution 축(`--team`)과 modifier(`--browser`/`--headed`/`--prepare`)는 지원합니다.

```
/qa-e2e                                    # 현재 세션 작업의 테스트 시나리오 자동 탐색
/qa-e2e {모듈명}                            # docs/spec/{모듈}/test_scenarios.md 기반 (DB 검증)
/qa-e2e {시나리오파일경로}                   # 특정 시나리오 파일 지정
/qa-e2e {모듈명} --tc TC-2                  # 특정 테스트 케이스만 실행
/qa-e2e {모듈명} --prepare                  # 테스트 데이터 준비만 (실행 안 함)
/qa-e2e --team {모듈명}                     # 팀 에이전트 E2E (다관점 병렬 검증)
/qa-e2e --team {모듈명} --tc TC-2           # 팀 + 특정 TC만
/qa-e2e --browser {모듈명}                  # Playwright 브라우저 E2E 테스트
/qa-e2e --browser {모듈명} --headed         # Playwright 유저 관찰 모드
/qa-e2e --browser {모듈명} --tc TC-2        # 특정 TC만 브라우저 테스트
```

---

## --team 모드: 팀 에이전트 E2E 테스트

`--team` 사용 시 5명의 전문가가 **병렬**로 비즈니스 프로세스를 다각도에서 검증합니다.
단일 모드의 "흐름 검증"에 **데이터 정합성, 보안, 크로스 도메인 영향**을 동시 확인합니다.

### 팀 구성 (Type G: QA E2E Team)

| 에이전트 | 역할 | 검증 관점 |
|---------|------|----------|
| **PM** (Lead) | TC 분배, 결과 종합, 리포트 통합 | 전체 조율 |
| **QA Engineer** | TC별 시나리오 실행, DB 상태 검증, 계산 검증 | 비즈니스 흐름 |
| **DBA** | 데이터 정합성, 트랜잭션 검증, 인덱스 영향, 외래키 무결성 | 데이터 계층 |
| **Security Sentinel** | 결제/환불 보안, 금액 변조 시도, 권한 우회 테스트 | 결제 보안 |
| **Explorer** | 크로스 도메인 영향 분석, 연관 프로세스 사이드이펙트 탐지 | 영향 범위 |

### --team 실행 흐름

```
PM: Phase 0 (시나리오 파싱) + TC별 팀원 분배
  +-- QA Engineer:        Phase 1~3 (데이터 준비 → 시나리오 실행 → 결과 검증)
  +-- DBA:                데이터 정합성 검증 (트랜잭션, 외래키, 잔액 정합)
  +-- Security Sentinel:  결제 보안 테스트 (금액 변조, PG 검증, 환불 초과)
  +-- Explorer:           크로스 도메인 영향 (재고, 포인트, 쿠폰, 통계 연동)
PM: Phase 4 (종합 E2E 리포트 생성)
```

### --team vs 단일 모드 차이

| 항목 | 단일 모드 | --team 모드 |
|------|----------|------------|
| 시나리오 실행 | 순차 | TC별 병렬 분배 |
| DB 검증 | 기대값 비교만 | + 트랜잭션 무결성, 외래키, 잔액 정합 |
| 보안 검증 | 없음 | 금액 변조, 환불 초과, 권한 우회 |
| 영향 분석 | 의존성 파일만 | 크로스 도메인 (연관 비즈니스 프로세스) |
| 리포트 | 단일 리포트 | 관점별 섹션 통합 리포트 |

### --team 리포트 추가 섹션

단일 모드 리포트에 아래 섹션이 추가됩니다:

```markdown
## 데이터 정합성 검증 (DBA)
| 항목 | 검증 SQL | 결과 |
|------|---------|------|
| 트랜잭션 완전성 | 상위-하위 테이블 상태 일치 | 통과/실패 |
| 잔액 정합 | 총결제 = 총환불 + 잔액 | 통과/실패 |
| 외래키 무결성 | 고아 레코드 없음 | 통과/실패 |

## 결제 보안 검증 (Security Sentinel)
| 항목 | 테스트 | 결과 |
|------|--------|------|
| 환불 초과 방지 | refund > balance 차단 | 통과/실패 |
| 금액 변조 | 클라이언트 금액 ≠ 서버 계산 시 차단 | 통과/실패 |
| PG 정합 | PG 취소금액 = DB 환불금액 | 수동확인 |

## 크로스 도메인 영향 (Explorer)
| 도메인 | 영향 | 검증 |
|--------|------|------|
| 재고 | 취소 시 재고 복원 | 통과/실패 |
| 포인트 | 사용 포인트 환불 | 통과/실패 |
| 쿠폰 | 사용 쿠폰 복원 | 통과/실패 |
| 통계 | 매출 통계 반영 | 수동확인 |
```

### --team 의견 충돌 시

Tiebreaker Protocol 적용:
1. CRITICAL 이슈 우선 (금액 불일치, 데이터 유실)
2. 도메인 전문성 가중치 (DB → DBA, 결제 → Security Sentinel)
3. 증거 기반 판정 (실행 SQL 결과, 계산 trace)
4. 해결 불가 시 사용자 에스컬레이션

---

## 단일 모드 수행 작업

### Phase 0: 시나리오 문서 탐색

### 시나리오 파일 위치 규칙
```
docs/spec/{모듈명}/test_scenarios.md
```

파일이 없으면 사용자에게 안내:
> 테스트 시나리오 문서가 없습니다. `/spec` 또는 수동으로 `test_scenarios.md`를 작성해주세요.

### 시나리오 문서 파싱
- `### TC-N:` 또는 `### S-N:` 패턴으로 테스트 케이스 식별
- 각 TC의 사전 조건, 테스트 액션, 기대 결과, 검증 SQL 추출
- `--tc` 옵션 시 해당 TC만 필터

---

## Phase 1: 테스트 데이터 준비

시나리오에서 필요한 데이터를 DB에서 조회하여 테스트 가능 여부를 확인합니다.

<!-- CUSTOMIZE: Test Data Queries
Replace with your project's test data verification queries.

Example (e-commerce):
### 1.1 상품 데이터 확인
  SELECT p.product_id, p.product_name, p.state_code
  FROM product p WHERE p.state_code = 1 LIMIT 5

### 1.2 기존 테스트 주문 확인
  SELECT o.order_no, o.order_status, od.product_name
  FROM orders o INNER JOIN order_detail od ON ...
  WHERE o.customer_id = '{testCustomerId}' LIMIT 5

### 1.3 테스트 가능 여부 판단
  - 필요 상품 존재 여부
  - 테스트 주문 생성 필요 여부
  - 결제 수단 (테스트 PG 사용 가능 여부)

Example (SaaS):
### 1.1 테스트 사용자 확인
  SELECT id, email, plan_type FROM users WHERE is_test = true LIMIT 5

### 1.2 테스트 워크스페이스 확인
  SELECT id, name FROM workspaces WHERE owner_id = {testUserId} LIMIT 5

Example (CMS):
### 1.1 테스트 콘텐츠 확인
  SELECT id, title, status FROM posts WHERE author_id = {testAuthorId} LIMIT 5
-->

### 1.1 관련 데이터 확인
시나리오에 명시된 데이터가 DB에 존재하는지 확인

### 1.2 기존 테스트 데이터 확인
이미 생성된 테스트 데이터가 있는지 확인

### 1.3 테스트 가능 여부 판단
- 필요 데이터 존재 여부
- 추가 데이터 생성 필요 여부
- 외부 연동 테스트 가능 여부

**데이터 부족 시**: 수동 데이터 생성 가이드 출력

---

## Phase 2: 시나리오별 테스트 실행

각 TC를 순서대로 실행합니다. 자동 실행 가능한 것(DB 조회, API 검증)과 수동 필요한 것(UI 조작)을 구분합니다.

### 2.1 테스트 실행 형태

| 유형 | 방법 | 비고 |
|------|------|------|
| **DB 검증** | DB 도구로 SQL 실행 | 자동 |
| **API 검증** | curl/API 호출 시뮬레이션 | 반자동 (인증 필요) |
| **UI 검증** | 수동 테스트 가이드 출력 | 수동 (URL + 클릭 순서) |
| **계산 검증** | 코드 로직 trace | 자동 (입력값 → 예상 출력값) |

### 2.2 단계별 출력

각 TC마다:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-N: {시나리오 이름}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[사전 조건]
  {필요한 데이터/상태 설명}

[테스트 액션]
  1. {첫 번째 액션}
  2. {두 번째 액션}
  3. {세 번째 액션}

[자동 검증]
  통과: {자동으로 확인된 항목}
  실패: {실패한 항목} (있는 경우)

[수동 확인 필요]
  미확인: {사용자가 확인해야 할 항목}
```

---

## Phase 3: 결과 검증

### 3.1 자동 DB 검증
시나리오의 검증 SQL을 실행하여 기대값과 비교

### 3.2 계산 검증 (로직 trace)
입력값을 넣고 코드 로직을 따라가며 기대 출력값 산출:
```
입력: {입력 파라미터}
계산:
  1단계: {계산 과정}
  2단계: {계산 과정}
  3단계: {계산 과정}
기대: {최종 기대 결과}
```

### 3.3 정합성 검증

<!-- CUSTOMIZE: Business Integrity Checks
Replace with your project's business-specific integrity validation rules.

Example (e-commerce: order→payment→claim→refund):
- PG 취소 금액 <= balanceAmount
- 총 환불 + 총 차감 = 총 결제
- 포인트 복구 <= 포인트 사용

Example (SaaS: subscription→billing→usage):
- 사용량 <= 플랜 한도
- 청구 금액 = 단가 * 사용량
- 환불 <= 결제 금액

Example (CMS: create→publish→archive):
- 발행 콘텐츠 개수 = DB 조회 결과
- 아카이브 후 공개 목록에서 제거
- 연관 리소스 상태 동기화
-->

프로젝트 비즈니스 규칙에 따른 정합성 검증 수행

---

## Phase 4: 리포트 생성 (권장)

테스트 완료 후 리포트 작성을 권장합니다. 중간 결과가 아닌 **최종 결과 확정 후** 작성해야 합니다.
- 모든 TC 실행 완료 + 재시도/수정 반영 후 최종 결과로 작성
- 중간에 TC가 실패하여 코드 수정 → 재실행한 경우, 최종 통과 결과만 기록
- 리포트 미작성 시에도 테스트 자체는 유효하나, 이력 추적과 회귀 테스트 기준으로 활용하기 어려움

### 저장 위치
```
docs/qa-reports/YYYY-MM-DD_{모듈명}_e2e.md
```

### 리포트 형식

```markdown
# E2E 테스트 리포트

**모듈**: {모듈명}
**실행일**: YYYY-MM-DD
**환경**: dev
**결과**: PASS / FAIL (N/M 통과)

## 테스트 결과 요약

| TC | 시나리오 | 자동검증 | 수동확인 | 결과 |
|----|---------|---------|---------|------|
| TC-1 | {시나리오} | N/N | 미확인 | PASS |
| TC-2 | {시나리오} | N/N | 확인 | PASS |
| TC-3 | {시나리오} | N/N | 미확인 | PASS |

## TC별 상세 결과
(각 TC의 검증 SQL 실행 결과, 계산 검증, 수동 확인 항목)

## 발견 이슈
(있으면 기록)

## 미확인 항목
(수동 테스트 필요한 항목 목록)
```

---

## 실행 지침

1. `$ARGUMENTS` 파싱 (모듈명, --tc, --prepare 옵션)
2. 시나리오 문서 탐색 및 파싱
3. 테스트 데이터 준비 (DB 조회)
4. TC별 순차 실행 (자동 검증 + 수동 가이드)
5. 리포트 생성 및 저장
6. 결과 출력

**DB 도구 사용 시**: LIMIT 필수, SELECT 특정 컬럼, WHERE 조건 필수

---

## --browser 모드: Playwright 브라우저 E2E 테스트

`--browser` 사용 시 Playwright를 활용하여 **실제 브라우저에서 UI 상호작용을 검증**합니다.
DB 검증(기본 모드)과 브라우저 검증(--browser)은 독립적이며 조합 가능합니다.

### 경로 규칙 (ABSOLUTE — 다른 위치 생성 금지)

```
qa-automation/                              <- 모든 QA 파일 (gitignored, 통째 삭제 가능)
+-- configs/playwright.config.js            <- 설정 (1곳, 수정만)
+-- tests/e2e/
|   +-- helpers/                            <- 공통 헬퍼만 (auth.js 등)
|   |   +-- auth.js                         # 인증/세션
|   |   +-- {모듈}.js                       # 모듈별 조작 헬퍼
|   +-- {모듈명}/                            # 모듈별 spec 파일
|       +-- *.spec.js                       # Playwright 테스트
+-- tests/reports/                          <- 결과물 (스크린샷, HTML 리포트)
    +-- playwright-report/
    +-- screenshots/
```

**금지**: `tests/`, `qa/`, 프로젝트 루트 등 `qa-automation/` 외부에 Playwright 파일 생성
**이유**: `qa-automation/` = gitignored 단일 디렉토리. 통째 삭제로 정리 가능

### 실행 흐름

```
1. $ARGUMENTS 파싱 (모듈명, --browser, --headed, --tc 옵션)
2. test_scenarios.md 파싱 → 브라우저 TC 식별 (type: browser 태그)
3. Playwright 테스트 파일 존재 확인:
   qa-automation/tests/e2e/{모듈명}/*.spec.js
4. 테스트 실행:
   npx playwright test --config=qa-automation/configs/playwright.config.js {모듈명}/
   (--headed 옵션 시: --headed 추가)
   (--tc 옵션 시: -g "TC-N" 패턴 매칭)
5. 결과 수집 + DB 검증 병행
6. 통합 리포트 생성
```

### 환경 변수

<!-- CUSTOMIZE: Environment Variables
Replace with your project's test environment variables.

Example (e-commerce):
TEST_BASE_URL=http://localhost
TEST_ADMIN_URL=http://localhost/admin
TEST_ADMIN_ID=
TEST_ADMIN_PW=
TEST_CUSTOMER_ID=
TEST_CUSTOMER_PW=

Example (SaaS):
TEST_BASE_URL=http://localhost:3000
TEST_API_URL=http://localhost:3001/api
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=

Example (generic):
TEST_BASE_URL=http://localhost:{port}
TEST_AUTH_TOKEN=
-->

```bash
TEST_BASE_URL=http://localhost          # dev 서버 주소
TEST_ADMIN_URL=http://localhost/admin   # 관리자 URL (해당시)
TEST_ADMIN_ID=                          # 관리자 계정
TEST_ADMIN_PW=
TEST_CUSTOMER_ID=                       # 테스트 사용자 계정
TEST_CUSTOMER_PW=
```

### 인증 방식

<!-- CUSTOMIZE: Authentication Method
Replace with your project's test authentication approach.

Example (guest login):
GET /user/guest → 게스트 세션 자동 생성
async function loginAsGuest(page) {
    await page.goto(baseUrl + '/user/guest', { waitUntil: 'networkidle' });
}

Example (cookie-based):
async function loginWithCredentials(page, email, password) {
    await page.goto(baseUrl + '/login');
    await page.fill('#email', email);
    await page.fill('#password', password);
    await page.click('button[type="submit"]');
}

Example (token-based):
async function loginWithToken(context) {
    await context.addCookies([{ name: 'auth', value: token, url: baseUrl }]);
}
-->

프로젝트의 인증 방식에 맞는 테스트 로그인 헬퍼 활용

### test_scenarios.md에서 브라우저 TC 표기

```markdown
### TC-N: {시나리오 이름} [browser]

**사전 조건**: {필요 상태}
**테스트 액션**:
1. {UI 조작 1}
2. {UI 조작 2}
3. {결과 확인}

**기대 결과**:
- {기대 동작 1}
- {기대 동작 2}

**DB 검증**:
```sql
SELECT {columns} FROM {table} WHERE {condition}
```
→ {기대값}
```

### Playwright spec 파일 작성 컨벤션

```javascript
const { test, expect } = require('@playwright/test');

test.describe('{모듈명} - {기능}', () => {
    test.beforeEach(async ({ page, context }) => {
        // 인증 상태 로드
        // 페이지 이동
    });

    test('TC-N: {시나리오 이름}', async ({ page }) => {
        // 1. UI 상호작용
        // 2. 결과 검증 (expect)
    });
});
```

### 헬퍼 함수 패턴 (재사용)

모듈별 반복 조작은 `helpers/{모듈}.js`로 분리:

```javascript
// helpers/{module}.js 예시
async function openModal(page) { ... }
async function fillForm(page, data) { ... }
async function submitAndWait(page) { ... }
async function getDisplayedValue(page, selector) { ... }
```

### --browser 리포트 추가 섹션

기본 리포트에 아래 섹션 추가:

```markdown
## 브라우저 E2E 결과 (Playwright)

| TC | 시나리오 | 브라우저 | 스크린샷 | 결과 |
|----|---------|---------|---------|------|
| TC-N | {시나리오} | chromium | 통과 | PASS |

### 스크린샷
- TC-N: `qa-automation/tests/reports/screenshots/TC-N.png`

### 콘솔 에러
- 0건 (clean)
```

### --browser + --team 조합

둘 다 사용 시:
- QA Engineer: Playwright TC 실행
- DBA: 실행 후 DB 정합성 검증
- Security Sentinel: 브라우저 콘솔 에러, XSS 가능성 체크
- Explorer: 다른 페이지 사이드이펙트 검증
