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

| 스킬 | 역할 | 프리셋 지원 |
|------|------|------------|
| `/analyze` | 코드베이스 분석, 영향도, 실행 전략 | depth + mode |
| `/spec` (또는 `/design`) | 기술 명세서 작성 | depth + mode |
| `/check-code` (또는 `/review`) | 코드 품질 검수 | depth + mode |

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
