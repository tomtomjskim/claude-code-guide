# 토큰 가격 및 비용 최적화 가이드

## 개요

Claude Code 사용 비용을 이해하고 최적화하는 방법을 설명합니다. modelCost.ts (v2.1.88) 기준 가격 정보와 실전 절감 전략을 다룹니다.

---

**관련 문서**:
- [환경 변수 레퍼런스](17-environment-variables.md)
- [Fast Mode 가이드](18-fast-mode.md)
- [사용량 한도 및 Rate Limit](16-usage-limits-ratelimit.md)
- [토큰 낭비 자가진단](28-token-waste-selfcheck.md) — 7대 낭비 요소 실전 진단
- [서브에이전트 효율성 가이드](33-subagent-efficiency.md) — 14k 고정 비용 분해 및 12가지 절감 전략
- [초기 셋업 체크리스트](00-setup-checklist.md)

---

## 1. 모델별 토큰 가격

가격 단위: USD per 1M tokens (modelCost.ts v2.1.88 기준)

| 모델 | Input | Output | Cache Write | Cache Read | Web Search |
|------|-------|--------|-------------|------------|------------|
| claude-haiku-3-5 | $0.80 | $4.00 | $1.00 | $0.08 | $0.01 |
| claude-haiku-4-5 | $1.00 | $5.00 | $1.25 | $0.10 | $0.01 |
| claude-sonnet-4 | $3.00 | $15.00 | $3.75 | $0.30 | $0.01 |
| claude-sonnet-4-5 | $3.00 | $15.00 | $3.75 | $0.30 | $0.01 |
| claude-sonnet-4-6 | $3.00 | $15.00 | $3.75 | $0.30 | $0.01 |
| claude-opus-4 | $15.00 | $75.00 | $18.75 | $1.50 | $0.01 |
| claude-opus-4-1 | $15.00 | $75.00 | $18.75 | $1.50 | $0.01 |
| claude-opus-4-5 (일반) | $5.00 | $25.00 | $6.25 | $0.50 | $0.01 |
| claude-opus-4-6 (일반) | $5.00 | $25.00 | $6.25 | $0.50 | $0.01 |
| claude-opus-4-6 (Fast) | $30.00 | $150.00 | $37.50 | $3.00 | $0.01 |

> **주의**: Opus 4.6 Fast Mode는 일반 Sonnet 대비 10배, 일반 Opus 4.6 대비 6배 비싸다. Fast Mode 비활성화 방법은 [18-fast-mode.md](18-fast-mode.md)를 참조하라.

---

## 2. 비용 계산 공식

### 기본 공식

```
총 비용 = (Input 토큰 × Input 단가)
        + (Output 토큰 × Output 단가)
        + (Cache Write 토큰 × Cache Write 단가)
        + (Cache Read 토큰 × Cache Read 단가)
        + (Web Search 횟수 × Web Search 단가)
```

모든 단가는 1M 토큰당 USD이므로:

```
실제 비용 = 위 합계 / 1,000,000
```

### 계산 예시: 일반적인 코드 작업 1회 (Sonnet 4.6)

```
상황: 대형 파일 읽기 + 코드 수정 + 설명 생성
- Input: 50,000 토큰 (파일 컨텍스트 + 프롬프트)
- Output: 3,000 토큰 (코드 + 설명)
- Cache Write: 40,000 토큰 (파일 내용 캐싱)
- Cache Read: 0 (첫 요청)

비용 계산:
  Input:       50,000 × $3.00   / 1,000,000 = $0.000150
  Output:       3,000 × $15.00  / 1,000,000 = $0.000045
  Cache Write: 40,000 × $3.75   / 1,000,000 = $0.000150
  ─────────────────────────────────────────────────────
  1회 총 비용: ~$0.000345 (약 $0.00035)
```

### 캐시 재사용 효과

동일 파일을 반복 참조하면 Cache Read 비용($0.30/1M)이 적용되어 Input 비용($3.00/1M)의 1/10로 절감됩니다.

```
캐시 없는 50,000 Input:  $0.000150
캐시 있는 50,000 Cache Read: $0.000015
절감: 90%
```

---

## 3. 서브에이전트 Sonnet 강제 전략

### 왜 중요한가

Claude Code는 서브에이전트(Task 도구로 생성된 에이전트)를 기본적으로 현재 세션과 동일한 모델로 실행합니다. Opus 모델로 세션을 시작하면 서브에이전트도 Opus로 실행되어 비용이 폭발적으로 증가합니다.

### 환경 변수 설정

```bash
# 서브에이전트를 항상 Sonnet으로 강제
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet

# 또는 특정 버전 지정
export CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6-20251201
```

### 비용 절감 효과

```
오케스트레이터: Opus 4.6 (일반) = $5/$25 per 1M
서브에이전트 기본(Opus): $5/$25 per 1M
서브에이전트 Sonnet 강제: $3/$15 per 1M

서브에이전트 비용 절감: ~40%
```

### 멀티 에이전트 팀에서의 적용

```bash
# NightOps 비대화형 세션 예시
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000

claude --model opus "PM 모드로 코드 리뷰 실행"
# → 오케스트레이터: Opus (복잡한 조율)
# → 서브에이전트: Sonnet (실제 작업)
```

---

## 4. 플랜별 예상 예산

### Claude Pro ($20/월)

- 월 $20 크레딧 (사용량 기준 과금 아님, 사용량 제한 방식)
- 5시간 롤링 윈도우 한도 존재
- 주 7일 한도 존재
- Opus 사용량 별도 주간 한도 (seven_day_opus)

**실용적 가이드라인**:
```
하루 평균 세션: 2-3회
세션당 평균 비용(추정 Sonnet): $0.05 - $0.20
월 예상 작업량: 60-90회 세션
```

### Claude Max 5x ($100/월)

- Pro 대비 5배 사용량
- Opus 모델 접근 가능
- 장기 작업, 복잡한 분석에 적합

**권장 모델 전략**:
```
일상 개발: Sonnet 4.6 (기본)
복잡한 설계/분석: Opus 4.6 (일반)
긴급/빠른 응답: Sonnet 4.6 (Fast Mode 금지)
```

### Claude Max 20x ($200/월)

- Pro 대비 20배 사용량
- 대규모 자동화, 멀티 에이전트 팀 운영
- NightOps 자율 운영 시스템에 적합

**멀티 에이전트 비용 예시**:
```
7단계 standard 워크플로우 1회:
  Architect (Opus): ~$0.10
  Developer × 2 (Sonnet): ~$0.04
  QA (Sonnet): ~$0.02
  Reviewer × 3 (Sonnet): ~$0.06
  총: ~$0.22 / 워크플로우
```

---

## 5. settings.json 비용 절감 설정

### 기본 비용 절감 설정

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000",
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY": "3"
  }
}
```

### 비대화형/자동화 세션 설정

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000"
  }
}
```

### 설정별 절감 효과

| 설정 | 절감 효과 | 부작용 |
|------|----------|--------|
| `SUBAGENT_MODEL=sonnet` | 서브에이전트 비용 ~40% 절감 | 없음 (품질 동일) |
| `DISABLE_FAST_MODE=1` | Opus Fast Mode 차단, 6x 비용 방지 | 없음 |
| `AUTO_COMPACT_WINDOW=150000` | 컨텍스트 압축으로 Input 토큰 감소 | 일부 컨텍스트 손실 가능 |
| `MAX_TOOL_USE_CONCURRENCY=3` | 병렬 도구 호출 제한 | 속도 약간 감소 |
| `DISABLE_BACKGROUND_TASKS=1` | 비대화형 세션 안정화 | 백그라운드 태스크 비활성화 |

---

## 6. 캐시 활용 전략

### Prompt Caching 원리

Claude API는 반복되는 프롬프트 접두사를 캐싱합니다. CLAUDE.md 내용, 도구 정의, 긴 시스템 프롬프트가 캐싱 대상입니다.

**캐시 효율 극대화 방법**:
```
1. CLAUDE.md를 안정적으로 유지 (자주 변경하면 캐시 무효화)
2. 시스템 프롬프트를 프롬프트 앞부분에 배치
3. 동일 세션에서 반복 작업 시 캐시 효과 극대화
```

### Cache Write vs Cache Read 비용

```
Cache Write: Input 가격의 1.25배 (캐시 저장 비용)
Cache Read:  Input 가격의 0.1배  (캐시 조회 비용)

동일 내용을 N번 반복 사용 시 손익분기:
  Write 1회 + Read (N-1)회 < Input N회
  → N=2부터 이미 이득
```

---

## 7. 비용 모니터링

### 세션 비용 추적

Claude Code는 각 세션에서 소비한 토큰과 비용을 `/cost` 명령으로 확인할 수 있습니다.

```bash
# 세션 내에서
/cost

# 출력 예시:
# Session cost: $0.0234
# Total tokens: 45,231 (input: 38,100, output: 7,131)
# Cache: write 12,000, read 26,100
```

### 월간 비용 추정 공식

```
월간 비용 = 일 평균 세션 수 × 세션 평균 비용 × 30

예시 (개발자, Sonnet 주력):
  세션 수: 5회/일
  세션 비용: $0.10 평균
  월간: 5 × $0.10 × 30 = $15.00
```

---

## 8. 모델 선택 가이드

| 작업 유형 | 권장 모델 | 이유 |
|----------|----------|------|
| 단순 파일 수정, 포맷팅 | Haiku 3.5 | 최저 비용 |
| 일반 코드 구현, 리뷰 | Sonnet 4.6 | 비용-품질 최적 |
| 복잡한 아키텍처 설계 | Opus 4.6 (일반) | 높은 추론 품질 |
| 빠른 응답이 필수인 경우 | Sonnet 4.6 | Fast Mode 없이도 충분히 빠름 |
| 절대 사용 금지 | Opus 4.6 Fast | 6x 비용, 품질 동일 |

---

## 다음 단계

1. [사용량 한도 및 Rate Limit](16-usage-limits-ratelimit.md)
2. [환경 변수 레퍼런스](17-environment-variables.md)
3. [Fast Mode 가이드](18-fast-mode.md)
4. [초기 셋업 체크리스트](00-setup-checklist.md)
