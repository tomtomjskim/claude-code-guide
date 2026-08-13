# Fast Mode 가이드

> 검증 기준일: 2026-08-13  
> 공식 문서: https://code.claude.com/docs/en/fast-mode

Fast Mode는 지원되는 Claude Opus 모델을 더 빠른 inference configuration으로 실행하는 선택 기능입니다. 비용과 latency의 교환이지, 항상 꺼야 하는 오류 상태가 아닙니다.

관련 문서:

- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [모델 설정](20-settings-schema-reference.md)
- [사용량 한도 및 Rate Limit](16-usage-limits-ratelimit.md)

---

## 1. 현재 동작

2026-08-13 공식 문서 기준:

| 항목 | 내용 |
|---|---|
| 지원 모델 | Claude Opus 5, Claude Opus 4.8 |
| 성능 | 최대 약 2.5배 높은 output tokens per second |
| 품질 | 같은 모델 weights와 capabilities |
| Fast API 단가 | Input $10 / MTok, Output $50 / MTok |
| 제공 상태 | research preview |
| Claude Code 사용 | CLI에서 `/fast` |
| 비지원 | Sonnet, Haiku, Opus 4.7 이하, VS Code extension |

기능, 가격, 지원 모델은 preview 기간에 바뀔 수 있습니다. 사용 전 공식 문서를 다시 확인합니다.

---

## 2. 잘못 알려진 내용 교정

기존 문서의 다음 설명은 현재 사실과 다릅니다.

```text
Opus 4.6 전용                 → 아님
일반 Opus 대비 6배 단가       → 현재 지원 모델 기준 2배
조건을 만족하면 자동 활성화   → 사용자가 /fast 또는 설정으로 opt-in
반드시 항상 비활성화해야 함   → workload와 비용 정책에 따라 결정
```

Fast Mode는 같은 모델의 속도 설정이므로 intelligence와 capability는 동일합니다. 다만 동일 weights라는 사실이 특정 작업의 체감 품질, 오류율, 비용 효율이 완전히 같다는 보장은 아닙니다. 실제 작업에서 latency와 accepted-result cost를 같이 측정합니다.

---

## 3. 비용 계산 예시

50K input, 5K output을 cache 없이 처리한다고 가정합니다.

### 표준 Opus 5 또는 Opus 4.8

```text
Input:  50,000 × $5  / 1,000,000 = $0.250
Output:  5,000 × $25 / 1,000,000 = $0.125
합계:                                $0.375
```

### Fast Mode

```text
Input:  50,000 × $10 / 1,000,000 = $0.500
Output:  5,000 × $50 / 1,000,000 = $0.250
합계:                                $0.750
```

동일 토큰 기준 Fast Mode는 표준 Opus의 2배입니다. 실제 비용은 cache, thinking, retry, tool call, 세션 중간 전환 여부에 따라 달라집니다.

---

## 4. 언제 사용할 것인가

| 상황 | 권장 |
|---|---|
| 대화형 디버깅, 즉시 피드백이 중요한 반복 | 고려 |
| 짧은 시간에 여러 설계 대안을 비교 | 고려 |
| 장기 자율 실행 | 표준 속도 우선 |
| batch, CI/CD, 야간 자동화 | 표준 속도 우선 |
| 비용 상한이 엄격한 작업 | 기본 OFF |
| 사용자 대기 시간이 실패 비용보다 큰 긴급 작업 | 명시적 opt-in 고려 |

Fast Mode와 effort는 다른 축입니다.

| 설정 | 영향 |
|---|---|
| Fast Mode | 같은 모델, 더 낮은 latency, 더 높은 단가 |
| 낮은 effort | thinking 감소 가능, 더 빠르고 저렴할 수 있으나 복잡 작업 품질 저하 가능 |

---

## 5. 활성화와 해제

### 대화형 CLI

```text
/fast
```

활성화되면 `Fast mode ON` 메시지와 `↯` 표시가 나타납니다. 다시 `/fast`를 실행해 상태를 확인하거나 끕니다.

### User settings

```json
{
  "fastMode": true
}
```

### 세션별 opt-in 권장

비용 통제가 필요한 개인 또는 조직은 persistent ON보다 세션별 opt-in이 안전합니다.

```json
{
  "fastModePerSessionOptIn": true
}
```

이 설정에서는 각 세션이 OFF로 시작하고 필요한 세션에서만 `/fast`를 실행합니다.

### 완전 비활성화

```bash
export CLAUDE_CODE_DISABLE_FAST_MODE=1
```

무인 자동화, 비용 상한이 강한 환경, 조직 정책에서 fast mode 자체를 금지할 때 사용합니다.

---

## 6. 세션 중간 전환 비용

Fast Mode를 대화 중간에 처음 켜면 기존 대화 전체가 fast-mode cache와 다른 prefix로 취급됩니다. 공식 문서는 첫 활성화 시 전체 conversation context에 fast-mode uncached input 단가가 적용될 수 있다고 설명합니다.

따라서:

- 사용할 것이 확실하면 세션 초기에 켭니다.
- 긴 대화가 이미 쌓였다면 새 세션 또는 checkpoint 기반 재시작 비용과 비교합니다.
- fast와 standard speed는 prompt cache를 공유하지 않는다는 점을 반영합니다.
- 단순히 한두 응답을 빠르게 받으려고 긴 세션 중간에 켜는 것은 비쌀 수 있습니다.

---

## 7. Rate Limit과 fallback

Fast Mode는 표준 Opus와 별도 rate limit을 사용합니다.

rate limit에 도달하면 Claude Code는 표준 속도로 fallback할 수 있고, cooldown이 끝나면 fast mode가 다시 활성화될 수 있습니다. 이 동작을 사용자가 알 수 없는 임의 비용 상승으로 해석하지 말고 `/fast` 상태와 알림을 확인합니다.

비용 예측이 중요한 자동화에서는 다음 중 하나를 선택합니다.

```text
fast mode를 사용하지 않음
또는
명시적 session budget과 fallback policy를 둠
```

---

## 8. Usage Credits와 구독

Claude Code 구독 사용자의 Fast Mode는 usage credits를 사용할 수 있으며 구독 포함 usage와 별도로 과금될 수 있습니다. Team과 Enterprise는 조직 Owner의 활성화가 필요할 수 있습니다.

플랜 동작은 변경 가능성이 있으므로 다음을 확인합니다.

- `/fast` 명령의 availability 메시지
- `/status`
- 조직 관리 설정
- 공식 Fast Mode 문서
- usage credits와 billing 설정

---

## 9. 권장 정책

### 개인 개발

```json
{
  "fastModePerSessionOptIn": true
}
```

- 기본 OFF
- live debugging이나 즉시 반복이 필요할 때만 `/fast`
- 작업 후 latency와 비용을 비교

### 팀

- 조직이 fast mode를 허용할지 명시합니다.
- 허용하더라도 per-session opt-in을 기본으로 둡니다.
- usage credit owner와 budget alert를 둡니다.
- 동일 작업의 standard/Fast accepted-result cost를 비교합니다.

### 무인 자동화

```bash
export CLAUDE_CODE_DISABLE_FAST_MODE=1
```

batch와 장기 작업은 표준 속도 또는 더 적합한 모델 라우팅을 우선합니다.

---

## 10. 검증 체크리스트

- [ ] 현재 지원 모델과 가격을 공식 문서에서 확인했다.
- [ ] Fast Mode를 4.6 전용 또는 6배 가격으로 설명하지 않는다.
- [ ] 세션 중간 활성화 시 cache miss 비용을 고려했다.
- [ ] speed와 effort를 구분했다.
- [ ] 자동화는 명시적인 ON/OFF 정책을 가진다.
- [ ] usage credits와 subscription included usage를 혼동하지 않는다.
- [ ] 품질과 capability가 동일하다는 설명을 accepted-result cost 동일로 확대 해석하지 않는다.
