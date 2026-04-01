# 사용량 한도 및 Rate Limit 가이드

## 개요

Claude Code의 사용량 한도 체계와 Rate Limiting 동작 방식을 설명합니다. 한도를 이해하면 세션을 효율적으로 계획하고, 갑작스러운 차단을 예방할 수 있습니다.

---

**관련 문서**:
- [토큰 가격 및 비용 최적화](14-token-pricing-optimization.md)
- [환경 변수 레퍼런스](16-environment-variables.md)
- [Fast Mode 가이드](17-fast-mode.md)

---

## 1. 한도 유형 (Limit Types)

Claude Code는 5가지 한도 유형을 정의합니다.

### five_hour

5시간 롤링 윈도우 내의 사용량 한도입니다.

```
윈도우: 현재 시각 기준 과거 5시간
초기화: 롤링 방식 (고정 시간이 아니라 연속 슬라이딩)
대상: 전체 모델 사용량
```

단기간 집중 작업 시 가장 먼저 도달하는 한도입니다. 한 번 초과하면 5시간을 기다려야 합니다.

### seven_day

7일 롤링 윈도우 내의 전체 사용량 한도입니다.

```
윈도우: 현재 시각 기준 과거 7일
초기화: 롤링 방식
대상: 전체 모델 사용량
```

주간 사용량의 상한선으로, 일반적인 사용 패턴에서는 five_hour보다 먼저 도달하기 어렵습니다.

### seven_day_opus

7일 롤링 윈도우 내의 Opus 모델 전용 한도입니다.

```
윈도우: 현재 시각 기준 과거 7일
초기화: 롤링 방식
대상: Opus 모델 사용량만
```

Opus를 과도하게 사용하면 전체 seven_day 한도에 영향을 주기 전에 이 한도에 먼저 도달할 수 있습니다.

### seven_day_sonnet

7일 롤링 윈도우 내의 Sonnet 모델 전용 한도입니다.

```
윈도우: 현재 시각 기준 과거 7일
초기화: 롤링 방식
대상: Sonnet 모델 사용량만
```

### overage

플랜 기본 한도를 초과한 추가 사용량입니다.

```
조건: 기본 플랜 한도 초과 시 활성화
과금: 추가 비용 발생 (플랜에 따라 다름)
설정: settings.json에서 allowedOverage 설정 가능
```

---

## 2. 퍼센티지 계산 원리

### API 헤더 기반 계산

사용량 비율은 Anthropic API 응답 헤더의 `x-usage-*` 값을 기반으로 계산됩니다. 헤더 값은 0에서 1 사이의 분수(fraction)로 반환됩니다.

```
헤더 예시:
  x-usage-five-hour: 0.45      → 5시간 한도의 45% 사용
  x-usage-seven-day: 0.23      → 7일 한도의 23% 사용
  x-usage-seven-day-opus: 0.67 → Opus 7일 한도의 67% 사용

퍼센티지 변환:
  utilization = fraction × 100
  예: 0.45 → 45%
```

### 표시 방식

Claude Code UI에서는 각 한도 유형별로 다음을 표시합니다:

```
[한도 유형] [사용률 %] / [경과 시간 %]

예:
  5h limit:  45% used / 28% elapsed
  7d limit:  23% used / 14% elapsed
  Opus 7d:   67% used / 14% elapsed
```

---

## 3. 상태 값 (Status Values)

각 한도 유형은 3가지 상태 중 하나를 가집니다.

### allowed

정상 상태. 현재 사용량이 한도의 안전 범위 내에 있습니다.

```
조건: utilization < Early Warning 임계값
동작: 정상 요청 처리
```

### allowed_warning

경고 상태. 사용량이 임계값에 근접했습니다. 요청은 계속 처리되지만 주의가 필요합니다.

```
조건: utilization >= Early Warning 임계값
동작: 정상 요청 처리 + 경고 메시지 표시
UI: 노란색/주황색 경고 표시
```

### rejected

차단 상태. 한도를 초과하여 요청이 거부됩니다.

```
조건: utilization >= 100% (또는 overage 비활성화 상태에서 한도 초과)
동작: 요청 거부, 오류 반환
복구: 롤링 윈도우가 지날 때까지 대기
```

---

## 4. Early Warning 임계값

Early Warning 시스템은 한도 초과 전에 미리 경고를 주는 메커니즘입니다. "남은 시간 대비 사용량이 너무 빠르다"고 판단될 때 경고합니다.

### 5시간 한도 (five_hour)

```
경고 조건: 사용률 90% 이상 AND 남은 시간 72% 이상
해석: 5시간 중 1.4시간도 안 지났는데 90%를 사용한 경우
```

즉, 5시간 윈도우의 28%(약 84분) 시점에 이미 90%를 소비했다면 경고가 발생합니다.

### 7일 한도 (seven_day)

3단계 경고 임계값이 존재합니다:

```
1단계 경고: 사용률 75% 이상 AND 남은 시간 60% 이상
  → 7일 중 2.8일 경과 전에 75% 소비
  해석: 초반에 너무 빠르게 소비 중

2단계 경고: 사용률 50% 이상 AND 남은 시간 35% 이상
  → 7일 중 4.55일 경과 전에 50% 소비

3단계 경고: 사용률 25% 이상 AND 남은 시간 15% 이상
  → 7일 중 5.95일 경과 전에 25% 소비
```

### 경고 임계값 요약 테이블

| 한도 유형 | 사용률 | 남은 시간 | 해석 |
|----------|--------|----------|------|
| five_hour | ≥ 90% | ≥ 72% | 5h 윈도우 초반에 거의 소진 |
| seven_day | ≥ 75% | ≥ 60% | 7d 전반부에 3/4 소진 |
| seven_day | ≥ 50% | ≥ 35% | 중반부에 절반 소진 |
| seven_day | ≥ 25% | ≥ 15% | 후반부 진입 전 25% 소진 |

---

## 5. Overage 시스템

### Overage 개념

기본 플랜 한도를 초과했을 때 추가 비용을 지불하고 계속 사용하는 옵션입니다.

```
기본 동작: 한도 도달 시 요청 거부 (rejected)
Overage 활성화 시: 추가 비용으로 계속 사용 가능
```

### settings.json 설정

```json
{
  "allowedOverage": true
}
```

### 주의사항

```
Overage 허용 시:
- 추가 비용 발생 (플랜별 overage 단가 적용)
- 예상치 못한 청구서 발생 가능
- 자동화/야간 작업에서 무제한 소비 위험

권장:
- 대화형 세션: 필요에 따라 활성화
- 자동화 세션: 반드시 비활성화 또는 하드 리밋 설정
```

---

## 6. 한도 절약 실전 팁

### 6.1 5시간 한도 관리

```
문제: 짧은 시간에 집중 작업 시 five_hour 한도 소진
해결 전략:
  1. 작업을 5시간 이상 분산 (인터리빙)
  2. 대용량 파일 읽기는 필요한 부분만 (limit/offset 파라미터)
  3. 컨텍스트 윈도우를 150K로 제한하여 Input 토큰 감소
     export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000
```

### 6.2 Opus 한도 보존

```
seven_day_opus 한도를 아끼는 전략:
  1. Sonnet으로 가능한 작업은 Sonnet 사용
  2. 서브에이전트는 SUBAGENT_MODEL=sonnet 강제
  3. Opus는 실제로 필요한 복잡한 설계/분석에만 사용
  4. Fast Mode 반드시 비활성화 (Opus Fast = 6x 비용)
```

### 6.3 일일 작업 계획

```
효율적인 하루 작업 계획:
  오전: 복잡한 설계/분석 (Opus, 집중 사용)
  오후: 구현 작업 (Sonnet, 분산 사용)
  저녁: 간단한 수정/리뷰 (Sonnet or Haiku)

five_hour 한도 회복을 고려:
  오전 집중 후 → 5시간 대기 없이 오후 작업 가능
  (오전 사용분이 오후에 롤링 윈도우에서 벗어남)
```

### 6.4 자동화 세션 최적화

```bash
# NightOps/자동화 세션 권장 설정
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet
export CLAUDE_CODE_DISABLE_FAST_MODE=1
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000

# 비용이 가장 낮은 시간대에 실행 (한도 소진 없는 시간)
# crontab 예시: 새벽 1-5시 실행
# 0 1 * * * /scripts/nightops.sh
```

### 6.5 경고 상태 대응 방법

```
allowed_warning 수신 시:
  즉시: 현재 작업 중요도 평가
  높음: 계속 진행 (rejected 되면 재개 불가)
  낮음: 작업 저장 후 한도 회복 대기

실용적 판단:
  현재 작업을 완료할 수 있을 만큼 남았는가?
  → YES: 계속 진행
  → NO: 핵심 작업만 완료 후 중단
```

### 6.6 컨텍스트 압축으로 토큰 절감

```bash
# 자동 컨텍스트 압축 창 설정
# 컨텍스트가 150K 토큰에 도달하면 자동 압축
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000

# 압축 비율 설정 (기본값 대비 조정)
# 낮은 값 = 더 자주 압축 = 토큰 절감 but 컨텍스트 손실 위험
export CLAUDE_CODE_AUTOCOMPACT_PCT_OVERRIDE=0.7
```

---

## 7. 한도 모니터링 설정

### 현재 사용량 확인

```bash
# 세션 내에서 현재 사용량 확인
/usage

# 또는 API를 통해 직접 확인
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/usage
```

### 알림 설정 아이디어

자동화 시스템에서 한도 모니터링이 필요한 경우:

```javascript
// 한도 경고 시 Telegram 알림 예시 (Node.js)
const checkUsageLimits = async () => {
  const response = await claude.messages.create({ ... });
  const usageHeaders = response.headers;

  const fiveHour = parseFloat(usageHeaders['x-usage-five-hour'] || '0');
  if (fiveHour > 0.80) {
    await sendTelegramAlert(`5h 한도 ${(fiveHour * 100).toFixed(0)}% 사용 중`);
  }
};
```

---

## 다음 단계

1. [환경 변수 레퍼런스](16-environment-variables.md)
2. [Fast Mode 가이드](17-fast-mode.md)
3. [토큰 가격 및 비용 최적화](14-token-pricing-optimization.md)
4. [초기 셋업 체크리스트](00-setup-checklist.md)
