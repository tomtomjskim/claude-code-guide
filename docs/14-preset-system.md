# 프리셋 시스템: 깊이(Depth) x 실행(Mode) 2축 체계

## 개요

스킬의 실행 강도를 **깊이(depth)**와 **실행 모드(mode)** 2가지 축으로 독립 제어합니다.
기존 단일 축 프리셋(quick/standard/thorough/팀리뷰)의 한계를 해결하여,
**팀 에이전트를 투입하면서도 깊이를 자유롭게 조절**할 수 있습니다.

### 기존 (단일 축)
```
quick → standard → thorough → 팀 리뷰
```
문제: "팀을 투입하되 빠르게 탐색만" 불가능

### 개선 (2축)
```
깊이(depth):  --quick ← standard → --thorough
실행(mode):   단일    ← 기본    → --team
```
`--team --quick` = 팀이 빠르게 탐색만 수행

---

## 적용 대상 스킬

| 스킬 | 역할 | 프리셋 지원 | 비고 |
|------|------|------------|------|
| `/analyze` | 코드베이스 분석, 영향도, 실행 전략 | depth + mode | 표준 2축 |
| `/spec` (또는 `/design`) | 기술 명세서 작성 | depth + mode | 표준 2축 |
| `/check-spec` | 설계문서 검수 | depth + mode | 표준 2축 |
| `/check-code` (또는 `/review`) | 코드 품질 검수 | depth + mode | 표준 2축 + Phase 매핑 |
| `/qa-test` | 종합 QA 자동화 | depth(4라벨) + mode | 기존 `--minimal/--basic/--standard/--full` 유지 + 2축 alias 지원 (아래 `/qa-test 프리셋` 참조) |
| `/qa-e2e` | 비즈니스 E2E 검증 | **mode only** | depth 축 없음 — 시나리오 기반 (아래 `/qa-e2e 프리셋` 참조) |

---

## 깊이 (Depth) 정의

### --quick
최소한의 분석/검수만 수행. 명확한 단순 작업에 적합.

| 스킬 | --quick 범위 | 시간 |
|------|-------------|------|
| analyze | 영향 파일 목록 + 수정 방향 1줄 | ~2분 |
| spec | 핵심 architecture 문서만 | ~3분 |
| check-code | 문법 체크(lint) + 규칙 위반 스캔 | ~2분 |

### standard (기본)
일반적인 수준의 분석/검수. 인자 없이 호출 시 기본 적용.

| 스킬 | standard 범위 | 시간 |
|------|--------------|------|
| analyze | 영향 분석 + 실행 전략 추천(2차 판단) | ~5분 |
| spec | architecture + api_design + database_schema | ~10분 |
| check-code | 보안/성능/아키텍처/API 검수 (Phase 1→2→3→6) | ~10분 |

### --thorough
심층 분석/검수. 대안 비교, 보안/성능 설계, 전체 Phase 실행.

| 스킬 | --thorough 범위 | 시간 |
|------|----------------|------|
| analyze | 다관점 심층 + 대안 2-3개 비교 + 의존성 그래프 | ~15분 |
| spec | 전체 섹션 + 대안 비교 + 보안/성능 설계 + 마이그레이션 계획 | ~20분 |
| check-code | 6단계 전체 (보안/성능/아키텍처/기능/UX/테스트) | ~20분 |

---

## 실행 모드 (Mode) 정의

### 단일 (기본)
1명의 에이전트가 순차적으로 모든 작업 수행.

### --team
전문 에이전트 팀이 병렬로 수행. Handoff Protocol로 결과 전달.

| 스킬 | --team 구성 |
|------|------------|
| analyze | PM + Explorer + Architect + DBA |
| spec | PM + Explorer + Architect + DBA + Designer(선택) |
| check-code | PM + Security Sentinel + Performance Prophet + Code Reviewer + API Arbiter |

---

## 조합 규칙

### 기본 문법
```
/스킬 [--depth] [--mode] [대상]
```

### 조합 예시

```bash
# analyze 조합
/analyze {기능}                     # standard + 단일 (기본)
/analyze --quick {버그}             # quick + 단일
/analyze --thorough {기능}          # thorough + 단일
/analyze --team {기능}              # thorough + 팀 (기본 최대 깊이)
/analyze --team --quick {기능}      # quick + 팀 (빠른 팀 탐색)
/analyze --team --standard {기능}   # standard + 팀

# spec 조합
/spec                               # standard + 단일 (기본)
/spec --quick                       # quick + 단일
/spec --thorough                    # thorough + 단일
/spec --team                        # thorough + 팀 (기본 최대 깊이)
/spec --team --quick                # quick + 팀

# check-code 조합
/check-code {모듈}                  # standard + 단일 (기본)
/check-code --thorough {모듈}       # thorough + 단일
/check-code --team {모듈}           # thorough + 팀 (기본 최대 깊이)
/check-code --team --quick {모듈}   # quick + 팀 (빠른 팀 스캔)
```

### 핵심 규칙

> **`--team` 단독 사용 시 기본 깊이 = thorough (최대 성능)**

팀 에이전트를 투입한다는 것은 중요한 작업이라는 의미이므로,
명시적으로 `--quick`이나 `--standard`를 지정하지 않는 한 최대 깊이를 적용합니다.

**예외:**
- `/qa-test --team`은 기본값 `--full`(= `--thorough` alias) 적용 — 동일 규칙
- `/qa-e2e --team`은 depth 축 미적용이므로 깊이 기본값 개념이 없음 — 전 TC(또는 `--tc` 필터 집합) 대상 팀 실행

---

## 스킬별 상세

### /analyze 프리셋

#### --quick 깊이
1. 관련 파일 Grep/Glob으로 식별
2. 수정 포인트 (파일:라인) 목록
3. 간단한 수정 방향 1줄

#### --thorough 깊이
standard에 추가:
1. **대안 비교**: 접근 방법 2-3개 비교 (장단점, 위험, 공수)
2. **아키텍처 영향**: 레이어별 변경 영향도, 하위호환 분석
3. **성능 영향**: 쿼리 복잡도, 인덱스 영향, 대용량 시나리오
4. **보안 영향**: 새 입력 경로의 보안 위험 사전 식별
5. **의존성 그래프**: 파일 간 호출 관계 시각화

#### --team 모드
```
┌─ PM (Lead): 분석 조율, 결과 종합
├─ Explorer: 코드베이스 탐색, 영향 범위, 유사 패턴
├─ Architect: 설계 관점 분석, 레이어 영향도, 확장성
└─ DBA: DB 스키마 관점 분석, 쿼리 영향, 인덱스
```

### /spec 프리셋

#### --quick 깊이
1. 핵심 architecture 문서만 작성 (개요 + 레이어 + 구현 순서)
2. 유사 패턴 참조 파일 경로 목록
3. 추정 소요 시간

#### --thorough 깊이
standard에 추가:
1. **대안 비교**: 설계 접근법 2-3개 비교 (장단점, 확장성, 유지보수성)
2. **보안 설계**: 입력 검증, 권한 체크, 공격 벡터 방어 명세
3. **성능 설계**: 쿼리 최적화 전략, 인덱스 계획, 캐싱 전략
4. **마이그레이션 계획**: 기존 데이터 영향, 롤백 전략
5. **i18n 설계**: 다국어 키 설계 (해당 시)

#### --team 모드
```
┌─ PM (Lead): 설계 조율, 결과 종합, 품질 게이트
├─ Explorer: 유사 패턴 탐색, 재사용 컴포넌트 식별
├─ Architect: 구조 설계, API 설계
├─ DBA: DB 스키마 설계, 인덱스 계획
└─ Designer: UI 구조 설계, 컴포넌트 패턴 (해당 시)
```

### /check-spec 프리셋

#### --quick 깊이
1. 문서 파일 존재 여부 (architecture.md, api_design.md, database_schema.md)
2. 필수 섹션 헤더 존재 여부
3. 명백한 누락 항목 식별

#### --thorough 깊이
standard에 추가:
1. **요구사항 완전성 심층**: 비즈니스 로직, 엣지 케이스, 상태 전이 검증
2. **대안 검토**: 설계 대안의 장단점이 충분히 비교되었는지
3. **보안/성능 설계**: 공격 벡터, N+1, 인덱스 계획이 포함되었는지
4. **마이그레이션 리스크**: 기존 데이터 영향, 롤백 전략 유무

#### --team 모드
```
┌─ PM (Lead): 검수 조율, 결과 종합
├─ Architect: 설계 일관성, 레이어 분리, 패턴 준수
├─ DBA: DB 스키마 정합성, 인덱스 계획, 쿼리 최적화 전략
└─ Explorer: 코드베이스 대조, 유사 패턴 비교, 영향 범위 확인
```

### /check-code 프리셋

기존 `docs/10-code-review-system.md`의 6단계 워크플로우와 통합:

| 깊이 | 실행 Phase |
|------|-----------|
| --quick | Phase 1만 (자동 분석) |
| standard | Phase 1→2→3→6 |
| --thorough | Phase 1→2→3→4→5→6 (전체) |

#### --team 모드
```
┌─ PM (Lead): 리뷰 조율, Tiebreaker 중재
├─ Security Sentinel: 보안 심층 검수
├─ Performance Prophet: 성능 심층 검수
├─ Code Reviewer: 코드 품질 종합
└─ API Arbiter: API 설계 검수 (해당 시)
```

---

### /qa-test 프리셋

qa-test는 역사적으로 **4단계 난이도 라벨**(`--minimal/--basic/--standard/--full`)을 사용해왔다. 2축 체계와의 호환을 위해 **기존 라벨을 보존하면서 2축 depth alias를 병행 지원**한다.

#### 난이도 ↔ 2축 depth 매핑

| qa-test 라벨 | 2축 alias | 범위 | Phase |
|-------------|-----------|------|-------|
| `--minimal` | `--quick` | 문법 검증만 | Phase 2 |
| `--basic` | (alias 없음, quick 상위) | 문법 + 코드 품질 | Phase 2-3 |
| `--standard` (기본) | (동일, 기본값) | 문법 + 품질 + UI/이벤트 + 의존성 | Phase 2-5 |
| `--full` | `--thorough` | + 이전 리포트 비교 | Phase 2-7 |

**규칙:** 두 라벨은 동시에 유효한 별칭. `--quick`과 `--minimal`은 결과가 동일하며, 사용자가 편한 쪽을 쓸 수 있다. `--basic`은 4단계 체계 고유이며 2축 alias가 없음(의도적 — "quick 상위"는 2축에서 불필요한 세분화).

#### --team 모드
```
┌─ PM (Lead): Phase 분배, 결과 종합, 리포트 통합
├─ QA Engineer: Phase 2-5 실행, 시나리오 검증, DB 상태 확인
├─ Security Sentinel: SQL Injection, XSS, 권한 우회 테스트
├─ Performance Prophet: N+1 쿼리, 대량 데이터, 인덱스 누락
└─ Access Advocate: 권한별 접근, 세션 변조, 비인가 API 호출
```

`--team` 단독 사용 시 기본 난이도 = `--full`(= `--thorough` alias).

---

### /qa-e2e 프리셋

**qa-e2e는 depth 축을 적용하지 않는다.** 이유는 E2E 테스트의 본질이 **시나리오 파일(`test_scenarios.md`)에 선언된 TC 집합 전체 실행**이며, "깊이를 줄여 일부만 실행"은 시나리오 자체를 쪼개는 작업이지 depth 옵션이 아니기 때문이다. 대신 **특정 TC만 실행**하는 `--tc TC-N` 옵션으로 범위를 제어한다.

#### 지원 축 요약

| 축 | qa-e2e 지원 여부 | 옵션 |
|----|------------------|------|
| depth | ✗ | 없음 — TC 단위 `--tc TC-N`으로 범위 제어 |
| execution | ✓ | 기본 단일 / `--team` (다관점 병렬) |
| 추가 modifier | ✓ | `--browser`(Playwright UI), `--headed`(관찰 모드), `--prepare`(데이터 준비만) |

#### --team 모드
```
┌─ PM (Lead): TC 분배, 결과 종합, 리포트 통합
├─ QA Engineer: TC별 시나리오 실행, DB 상태 검증, 계산 검증
├─ DBA: 데이터 정합성, 트랜잭션, 외래키 무결성
├─ Security Sentinel: 결제/환불 보안, 금액 변조, 권한 우회
└─ Explorer: 크로스 도메인 영향, 연관 프로세스 사이드이펙트
```

`--team` 사용 시 범위는 전 TC(또는 `--tc`로 필터된 집합)에 팀 구성 적용.

---

## 프리셋 선택 가이드

### 작업 유형별 권장

```
버그 수정 / 소규모 수정:
  /analyze --quick → /run → /check-code

일반 기능:
  /analyze → /spec → /run → /check-code

중요 기능 (인증, 결제, 외부 연동):
  /analyze --thorough → /spec --thorough → /run → /check-code --thorough

대규모 신규 모듈 (최대 성능):
  /analyze --team → /spec --team → /workflow → /check-code --team

팀인데 빠르게 (탐색만):
  /analyze --team --quick → 팀이 빠르게 영향 범위만 파악
```

### 피해야 할 안티패턴

| 안티패턴 | 이유 | 대안 |
|---------|------|------|
| 버그 수정에 --team | 토큰 3~5배 낭비 | 단일 에이전트 |
| 모든 검수에 --team | 30분 소요, 비용 높음 | standard(기본) 사용 |
| --thorough를 매번 사용 | 20분 소요 | 배포 전에만 사용 |

### 원칙

> **작업 중요도가 높을수록 앞단(analyze/spec)에 투자하라.**
> 분석/설계가 잘못되면 구현부터 전부 틀어진다.

---

## 관련 문서

- [코드 리뷰 시스템](10-code-review-system.md) - check-code 6단계 Phase 상세
- [에이전트 페르소나](05-agent-personas.md) - 팀 에이전트 프롬프트
- [v3.0 아키텍처](12-v3-architecture.md) - Model Routing, Handoff, Failure Recovery
- [핸드오프 & 실패 복구](13-handoff-and-failure.md) - --team 모드 시 적용되는 프로토콜
