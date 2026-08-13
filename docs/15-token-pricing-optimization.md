# Claude Code 비용 및 토큰 최적화 가이드

> 검증 기준일: 2026-08-13  
> 가격·모델·기능은 빠르게 바뀝니다. 이 문서의 숫자를 장기 기준으로 복사하지 말고 아래 공식 문서를 다시 확인하세요.

공식 기준:

- Claude 가격: https://platform.claude.com/docs/en/about-claude/pricing
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude Code 모델 설정: https://code.claude.com/docs/en/model-config
- Claude Code 서브에이전트: https://code.claude.com/docs/en/sub-agents
- Fast mode: https://code.claude.com/docs/en/fast-mode

관련 문서:

- [Fast Mode 가이드](18-fast-mode.md)
- [컨텍스트 윈도우와 상태 관리](19-context-window-internals.md)
- [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
- [서브에이전트 효율성 가이드](33-subagent-efficiency.md)

---

## 1. 최적화 목표

가장 싼 단일 호출을 찾는 것이 목표가 아닙니다.

```text
accepted-result cost
= 전체 과금 비용 / 검증과 사용자 승인까지 통과한 결과 수
```

다음 비용을 모두 포함합니다.

- 최초 모델 호출
- SDK 자동 재시도와 애플리케이션 재시도
- 후보 생성과 선택
- 상위 모델 또는 effort 승격
- prompt cache write/read
- tool call과 별도 validator 호출
- 실패한 결과와 폐기된 결과

저가 모델이 여러 번 실패하거나, 높은 effort가 불필요한 thinking token을 생성하면 호출당 가격은 낮아도 승인 결과당 비용은 더 커질 수 있습니다.

---

## 2. API 비용 계산식

Anthropic API usage의 입력 토큰은 서로 겹치지 않는 세 항목으로 계산합니다.

```text
총 입력 토큰
= input_tokens
+ cache_creation_input_tokens
+ cache_read_input_tokens
```

비용 계산식:

```text
총비용
= input_tokens × 일반 입력 단가
+ cache_creation_input_tokens × cache write 단가
+ cache_read_input_tokens × cache read 단가
+ output_tokens × 출력 단가
```

모든 단가는 USD per 1M tokens이므로 각 항목을 `1,000,000`으로 나눕니다.

### 주의: cache token 이중 계산 금지

전체 prompt가 50,000토큰이고 그중 40,000토큰이 새 cache entry로 기록됐다면, 일반 입력은 50,000이 아니라 나머지 10,000토큰입니다.

잘못된 계산:

```text
50,000 일반 입력 + 40,000 cache write
```

올바른 usage 분해:

```text
10,000 input_tokens
40,000 cache_creation_input_tokens
3,000 output_tokens
```

---

## 3. 검증된 계산 예시

다음 예시는 Claude Sonnet 4.6의 2026-08-13 공식 API 단가를 사용합니다.

```text
일반 입력:       $3.00 / MTok
5분 cache write: $3.75 / MTok
cache read:      $0.30 / MTok
출력:            $15.00 / MTok
```

### 최초 요청: cache write 40K

```text
input_tokens:                10,000
cache_creation_input_tokens: 40,000
output_tokens:                3,000

일반 입력:   10,000 × $3.00  / 1,000,000 = $0.030
cache write: 40,000 × $3.75  / 1,000,000 = $0.150
출력:         3,000 × $15.00 / 1,000,000 = $0.045
--------------------------------------------------
합계:                                      $0.225
```

### 동일 prefix 재사용: cache read 40K

```text
input_tokens:            10,000
cache_read_input_tokens: 40,000
output_tokens:            3,000

일반 입력:  10,000 × $3.00  / 1,000,000 = $0.030
cache read: 40,000 × $0.30  / 1,000,000 = $0.012
출력:        3,000 × $15.00 / 1,000,000 = $0.045
--------------------------------------------------
합계:                                     $0.087
```

기존 문서의 `$0.000345` 예시는 단위 계산이 1,000배 틀렸고 cache write 토큰을 일반 입력과 중복 계산했습니다.

---

## 4. Prompt caching 손익분기

공식 multiplier:

| 항목 | 일반 입력 대비 |
|---|---:|
| 5분 cache write | 1.25배 |
| 1시간 cache write | 2배 |
| cache read | 0.1배 |

### 5분 TTL

동일 prefix를 한 번만 더 읽어도 다음과 같습니다.

```text
cache 사용: 1.25P + 0.1P = 1.35P
미사용:     1P + 1P       = 2P
```

즉 실제 cache hit가 한 번 발생하면 이론상 이득입니다.

### 1시간 TTL

```text
최초 + 1회 read: 2P + 0.1P = 2.1P  > 미사용 2P
최초 + 2회 read: 2P + 0.2P = 2.2P  < 미사용 3P
```

1시간 cache는 최소 두 번의 실제 read가 있어야 이론상 이득입니다.

실제 손익은 다음 조건도 확인해야 합니다.

- 모델별 최소 cacheable token 수
- 동일 prefix 여부
- cache TTL 안의 재사용 횟수
- tool, system, message 순서 변경
- speed, thinking, effort 설정 변경에 따른 cache invalidation
- cache hit이 발생했는지 usage field 확인

### Prefix 구조

```text
stable prefix
- tool definitions
- system instructions
- stable examples
- output schema

dynamic suffix
- 현재 사용자 요청
- 검색 결과와 현재 코드
- timestamp, request ID, volatile metadata
```

동적 값을 cache breakpoint 앞에 넣으면 매 요청마다 새 hash가 만들어져 cache write만 반복하고 read를 얻지 못할 수 있습니다.

---

## 5. 모델과 effort 라우팅

### 기본 원칙

```text
deterministic 처리 가능 여부 확인
→ 가장 낮은 성공 가능 모델과 effort
→ schema, test, validator
→ 실패 조건이 확인될 때만 bounded escalation
```

| 작업 | 출발점 | 승격 조건 |
|---|---|---|
| 파일 탐색, 정형 추출 | 빠른 모델 또는 낮은 effort | 누락, schema 실패 |
| 일반 구현과 리뷰 | Sonnet 계열 또는 medium effort | 테스트 실패, 다중 모듈 영향 |
| 복잡한 설계와 원인 분석 | 강한 모델 또는 high 고려 | 근거 충돌, 재현 실패 |
| 보안·데이터·배포 | 적합한 강한 모델 + 독립 검증 | 미해결 위험이 있으면 완료 금지 |

모델명은 사용 가능한 최신 alias와 조직 allowlist에 따라 달라집니다. 문서에 고정된 구버전 모델 ID보다 `/model`, `/status`, 관리 정책을 먼저 확인합니다.

### 서브에이전트 모델 우선순위

현재 Claude Code의 해석 순서는 다음과 같습니다.

```text
CLAUDE_CODE_SUBAGENT_MODEL
→ 호출별 model parameter
→ subagent frontmatter model
→ 메인 세션 모델 상속
```

전역 환경 변수는 모든 서브에이전트를 덮어쓰므로 비용 통제 정책이 명확할 때만 사용합니다. 일반적으로는 역할별 frontmatter가 더 세밀합니다.

```yaml
---
name: code-searcher
description: 읽기 전용 코드 탐색
model: haiku
effort: low
maxTurns: 8
tools: Read, Grep, Glob
---
```

```yaml
---
name: security-reviewer
description: 보안 위험이 있는 변경만 검토
model: opus
effort: high
maxTurns: 12
tools: Read, Grep, Glob
---
```

모델을 낮추면 비용은 줄 수 있지만 품질이 동일하다고 가정하지 않습니다. 대표 작업에서 validator pass rate, retry, 발견 결함, accepted-result cost를 비교합니다.

---

## 6. Fast Mode와 비용

Fast Mode는 비용 낭비 기능도, 품질 향상 기능도 아닙니다. 같은 Opus 모델을 더 빠른 inference configuration으로 실행하고 더 높은 단가를 지불하는 latency 선택지입니다.

- 대화형 디버깅과 빠른 반복: 검토 가치 있음
- 장기 자동화, batch, CI, 비용 민감 작업: 표준 속도 우선
- 세션 중간에 처음 활성화하면 기존 대화 context가 fast-mode uncached input으로 다시 과금될 수 있으므로 필요하면 세션 시작 시 결정
- 조직 비용 통제가 필요하면 `fastModePerSessionOptIn: true` 또는 `CLAUDE_CODE_DISABLE_FAST_MODE=1` 사용

자세한 내용은 [Fast Mode 가이드](18-fast-mode.md)를 봅니다.

---

## 7. Context와 compaction

Claude Code는 모델별 context window에 맞춰 자동 compaction을 지원합니다.

권장 기본값:

- `autoCompactEnabled`는 기본 동작을 유지합니다.
- `autoCompactWindow`를 임의로 낮추기 전에 실제 session token과 품질을 측정합니다.
- compaction summary를 감사 로그나 검증된 business state로 취급하지 않습니다.
- 중요한 결정은 evidence-linked checkpoint로 별도 보존합니다.
- 오래된 debug output, 중복 tool result, 완료된 계획을 active context에서 제거합니다.

현재 설정 예시:

```json
{
  "autoCompactEnabled": true,
  "fastModePerSessionOptIn": true
}
```

모델별로 조정된 기본 window가 있으므로 `autoCompactWindow`는 측정 근거 없이 고정하지 않는 편이 안전합니다.

---

## 8. 비용 계측

최소 telemetry:

```text
request 또는 task ID
model과 effort
input_tokens
cache_creation_input_tokens
cache_read_input_tokens
output_tokens
thinking tokens 또는 관련 usage가 제공될 때 해당 값
latency
retry count
escalation count
validator result
accepted/rejected result
billed cost
```

핵심 지표:

```text
accepted_result_cost
retry_amplification
escalation_rate
validator_pass_rate
cache_hit_ratio
p50/p95_latency
```

콘텐츠, prompt 원문, tool result, thinking block을 비용 로그에 함께 저장하지 않습니다.

---

## 9. API 가격과 구독 한도 분리

다음은 서로 다른 개념입니다.

| 항목 | 의미 |
|---|---|
| API token price | 실제 토큰별 USD 과금 |
| subscription usage limit | Pro, Max, Team 등의 사용량 정책 |
| usage credits | 구독 포함량을 넘어 별도 과금되는 기능·사용량 |
| rate limit | 시간당 또는 분당 요청·토큰 제한 |

구독 플랜의 세션 횟수나 월간 작업량을 API 달러 비용으로 임의 환산하지 않습니다. 플랜 정책은 계정, 조직, 시점에 따라 달라질 수 있으므로 `/status`, 관리 콘솔, 공식 지원 문서를 확인합니다.

---

## 10. 검증 체크리스트

- [ ] 공식 가격과 모델 가용성을 현재 날짜로 다시 확인했다.
- [ ] cache token을 일반 input token과 중복 계산하지 않았다.
- [ ] 계산 예시를 calculator 또는 unit test로 검증했다.
- [ ] retry와 escalation을 비용에 포함했다.
- [ ] 서브에이전트 모델을 낮춘 뒤 품질 회귀를 측정했다.
- [ ] Fast Mode를 무조건 금지하거나 무조건 사용하지 않았다.
- [ ] cache hit을 usage field로 확인했다.
- [ ] compaction summary를 검증된 checkpoint와 분리했다.
- [ ] 비용 로그에 prompt, secret, thinking state가 들어가지 않는다.

검증 명령:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
bash scripts/validate-repository.sh
```
