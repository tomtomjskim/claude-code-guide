# Retry & 에러 복구 상수

## 개요

Claude Code는 API 통신 실패, 과부하, Rate Limit 등 다양한 에러 상황에서 자동으로 재시도(retry)하고 복구합니다.
이 문서는 내부 재시도 상수, 백오프 전략, 에러 분류 테이블을 설명합니다.

---

## 1. 재시도 상수 (Retry Constants)

| 상수 | 값 | 설명 |
|------|-----|------|
| `MAX_RETRIES` | **10** | HTTP 요청 최대 재시도 횟수 |
| `HTTP_529_MAX_RETRIES` | **3** | 529 (Overloaded) 전용 재시도 상한 |
| `BASE_DELAY_MS` | **500ms** | 첫 번째 백오프 대기 시간 |
| `JITTER_FACTOR` | **25%** | 무작위 지터 비율 (thundering herd 방지) |
| `UNATTENDED_MAX_BACKOFF` | **5분** | 비대화형(unattended) 세션 최대 대기 |
| `BURST_COOLDOWN` | **10분** | 버스트 후 쿨다운 대기 시간 |

### 백오프 공식

```
delay(n) = BASE_DELAY_MS × 2^n × (1 + random(0, JITTER_FACTOR))
```

예시 (지터 없이):
```
1회차: 500ms
2회차: 1,000ms
3회차: 2,000ms
4회차: 4,000ms
5회차: 8,000ms
...
상한: UNATTENDED_MAX_BACKOFF = 5분 (비대화형) 또는 세션 설정값
```

---

## 2. HTTP 529 특별 처리

HTTP 529는 Anthropic 서버 과부하를 나타내는 커스텀 상태 코드입니다.

```
529 응답 수신
    │
    ▼
529 전용 재시도 카운터 증가
    │
    ├─ 재시도 횟수 < 3 → 백오프 후 재시도
    │
    └─ 재시도 횟수 = 3 → Non-streaming fallback으로 전환
                              (스트리밍 비활성화 후 일반 요청으로 재시도)
```

> Non-streaming fallback: 스트리밍 응답 대신 단일 블록 응답을 요청합니다.
> 서버 부하가 높을 때 스트리밍이 더 불안정할 수 있어 폴백으로 전환합니다.

---

## 3. 에러 분류 테이블

| HTTP 코드 | 이름 | 재시도 여부 | 처리 방식 |
|----------|------|-----------|----------|
| **400** | Bad Request | 아니오 | 즉시 실패, 요청 내용 검토 필요 |
| **401** | Unauthorized | 아니오 | API 키 확인, 즉시 사용자에게 보고 |
| **403** | Forbidden | 아니오 | 권한 부족, 즉시 실패 |
| **429** | Too Many Requests | 예 | Rate limit 플로우 진입 (하단 참조) |
| **500** | Internal Server Error | 예 | 백오프 후 최대 `MAX_RETRIES`(10)회 재시도 |
| **529** | Overloaded | 예 | 전용 카운터 3회 후 non-streaming fallback |

### 재시도 불가 에러 (400/401/403)

이 에러들은 재시도해도 결과가 바뀌지 않으므로 즉시 에러로 처리합니다.
- **400**: 요청 파라미터, 모델 이름, 프롬프트 형식 문제
- **401**: API 키 누락 또는 만료
- **403**: 계정 정지, 지역 제한, 기능 미허가

---

## 4. Rate Limit 플로우 (429)

```
429 응답 수신
    │
    ▼
extractQuotaStatusFromError() 호출
    │
    ▼
응답 헤더에서 할당량 정보 추출
  - x-ratelimit-remaining-requests
  - x-ratelimit-reset-requests
  - retry-after
    │
    ▼
상태 = "rejected" (거부됨)
    │
    ▼
대기: retry-after 값 또는 백오프 계산값 중 큰 값
    │
    ▼
재시도 (MAX_RETRIES 상한까지)
```

> `extractQuotaStatusFromError`는 응답 헤더와 바디를 파싱하여 남은 요청 수,
> 리셋 시간, 초당 토큰 한도 등을 추출합니다. 이 정보는 내부 상태에 캐싱됩니다.

---

## 5. 출력 크기 에스컬레이션

Claude Code는 응답이 잘리거나(truncated) 컨텍스트 초과가 예상될 때 출력 한도를 자동으로 확장합니다.

```
기본 출력 한도: 8K 토큰
    │
    ▼
출력 잘림 감지 (finish_reason = "max_tokens")
    │
    ▼
출력 한도 에스컬레이션: 64K 토큰
    │
    ▼
동일 요청 재시도 (확장된 한도로)
```

이 에스컬레이션은 단계적으로 발생하며, 64K까지 한 번만 확장됩니다.
모델이 지원하는 최대 출력 한도를 초과하면 에스컬레이션이 중단됩니다.

---

## 6. 비대화형 세션 (Unattended) 동작

`--no-interactive` 플래그 또는 NightOps/자동화 세션에서는 대기 전략이 달라집니다.

| 항목 | 대화형 세션 | 비대화형 세션 |
|------|-----------|-------------|
| 최대 백오프 | 설정에 따름 | **5분** 상한 |
| 버스트 쿨다운 | 짧음 | **10분** |
| 사용자 알림 | 실시간 | 로그 기록 후 계속 |
| 에러 시 중단 | 사용자 판단 | 재시도 소진 후 자동 종료 |

```bash
# 비대화형 세션 환경변수
CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1   # 백그라운드 태스크 비활성화
```

---

## 7. 에러 복구 전략 요약

```
에러 발생
    │
    ├─ 재시도 불가 (400/401/403)
    │       └─ 즉시 실패 보고
    │
    ├─ Rate Limit (429)
    │       └─ extractQuotaStatus → 대기 → 재시도 (최대 10회)
    │
    ├─ 서버 에러 (500)
    │       └─ 지수 백오프 → 재시도 (최대 10회)
    │
    └─ 과부하 (529)
            ├─ 재시도 < 3회: 백오프 후 재시도
            └─ 재시도 = 3회: Non-streaming fallback
```

---

## 관련 문서

- [환경변수 레퍼런스](16-environment-variables.md) - 재시도 관련 환경변수
- [사용량 한도 & Rate Limit](15-usage-limits-ratelimit.md) - 5h/7d 윈도우, Early Warning
- [컨텍스트 윈도우 내부](18-context-window-internals.md) - 출력 한도와 auto-compact 연동
