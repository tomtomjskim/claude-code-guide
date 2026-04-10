# Advisor Strategy 가이드

## 개요

**Advisor Strategy**는 2026년 4월 9일 Anthropic이 발표한 새로운 모델 협업 패턴입니다. 빠르고 저비용인 **executor 모델**(Sonnet/Haiku)이 작업을 수행하되, 복잡한 의사결정 시점에 고지능 **advisor 모델**(Opus)에게 자문을 구합니다.

기존 "큰 모델이 작은 모델에 위임" 패턴을 **역전**시킵니다: 작은 모델이 주도하고, 필요할 때만 큰 모델에 에스컬레이션.

**상태**: Beta (`advisor-tool-2026-03-01`)

---

**관련 문서**:
- [하네스 엔지니어링 가이드](29-harness-engineering.md)
- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [Settings 스키마 레퍼런스](20-settings-schema-reference.md)

**공식 자료**:
- [The advisor strategy (Anthropic 블로그)](https://claude.com/blog/the-advisor-strategy)
- [Advisor tool API 문서](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)

---

## 1. 핵심 개념

### 1.1 기존 패턴 vs Advisor 패턴

```
기존 (오케스트레이터 패턴):
  Opus (오케스트레이터) → Sonnet (작업자) → Opus (검토)
  비용: 높음 (Opus가 전체 흐름 관리)

Advisor 패턴:
  Sonnet (executor, 전체 수행) → Opus (advisor, 필요 시 자문)
  비용: 낮음 (Opus는 자문만, 도구 호출/출력 생성 안 함)
```

### 1.2 Advisor의 제약

```
Advisor는:
  ✅ 전체 대화 컨텍스트를 봄 (시스템 프롬프트, 도구 정의, 이전 턴, 도구 결과)
  ✅ 가이던스/조언을 제공함
  ❌ 도구를 직접 호출하지 않음
  ❌ 사용자 대면 출력을 생성하지 않음
  ❌ 파일을 읽거나 쓰지 않음
```

---

## 2. 성능 벤치마크

| 구성 | 벤치마크 | 결과 |
|------|---------|------|
| Sonnet + Opus Advisor | SWE-bench Multilingual | Sonnet 단독 대비 **+2.7pp** |
| Sonnet + Opus Advisor | 비용 | Sonnet 단독 대비 **11.9% 절감** |
| Haiku + Opus Advisor | BrowseComp | 19.7% → **41.2%** (2배+) |
| Haiku + Opus Advisor | 비용 | Sonnet 단독 대비 **85% 저렴** |

> **핵심**: Sonnet + Advisor = Opus에 근접한 품질, Sonnet 수준 비용.

---

## 3. 모델 조합

| Executor | Advisor | 용도 |
|----------|---------|------|
| Haiku 4.5 | Opus 4.6 | 대량 처리, 비용 최소화 |
| **Sonnet 4.6** | **Opus 4.6** | **권장 — 비용-품질 최적** |
| Opus 4.6 | Opus 4.6 | 최고 품질 (self-review) |

---

## 4. API 구현

### 4.1 기본 사용법 (Python)

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-6",  # executor
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    tools=[
        {
            "type": "advisor_20260301",
            "name": "advisor",
            "model": "claude-opus-4-6",  # advisor
        }
    ],
    messages=[
        {"role": "user", "content": "이 PHP 코드의 보안 취약점을 분석하고 수정해줘."}
    ],
)
```

### 4.2 TypeScript (Anthropic SDK)

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-6',
  max_tokens: 4096,
  betas: ['advisor-tool-2026-03-01'],
  tools: [
    {
      type: 'advisor_20260301',
      name: 'advisor',
      model: 'claude-opus-4-6',
    },
    // 다른 도구와 함께 사용 가능
    {
      name: 'run_bash',
      description: 'Run a bash command',
      input_schema: {
        type: 'object',
        properties: { command: { type: 'string' } },
      },
    },
  ],
  messages: [{ role: 'user', content: 'Build a REST API with error handling.' }],
});
```

### 4.3 도구 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `type` | string | 필수 | `"advisor_20260301"` 고정 |
| `name` | string | 필수 | `"advisor"` 고정 |
| `model` | string | 필수 | Advisor 모델 ID |
| `max_uses` | integer | 무제한 | 요청당 advisor 호출 횟수 제한 |
| `caching` | object | `null` | 프롬프트 캐싱 `{"type": "ephemeral", "ttl": "5m"}` |

---

## 5. 비용 구조

### 5.1 빌링 모델

```
Executor 토큰 → executor 모델 요금
Advisor 토큰 → advisor 모델 요금 (별도)
```

Advisor 출력: 일반적으로 400~700 토큰, thinking 포함 시 1,400~1,800 토큰.

### 5.2 비용 비교 (코드 분석 1회 기준)

```
Opus 단독:
  Input 50K × $5/1M + Output 5K × $25/1M = $0.375

Sonnet + Opus Advisor (2회 자문):
  Executor: Input 50K × $3 + Output 5K × $15 = $0.225
  Advisor:  Input 50K × $5 × 2 + Output 1.5K × $25 × 2 = $0.575
  합산: ~$0.80 (advisor 비용 포함)

실제 벤치마크 기준:
  Sonnet + Advisor = Sonnet 대비 11.9% 절감
  이유: advisor 조언으로 executor 시행착오 감소 → 총 토큰 절감
```

### 5.3 max_uses로 비용 제어

```python
{
    "type": "advisor_20260301",
    "name": "advisor",
    "model": "claude-opus-4-6",
    "max_uses": 3  # 요청당 최대 3회 자문
}
```

---

## 6. Advisor 호출 전략 — Best Practices

### 6.1 최적 호출 시점 (작업당 2~3회)

Anthropic 내부 코딩 평가에서 검증된 패턴:

```
1. 작업 시작 후 탐색 완료 시점 — 접근 전략 수립 전
2. 어려움 발생 시 — 에러 반복, 접근 수렴 안 됨
3. 작업 완료 직전 — 결과 검증 (Review Gate)
```

### 6.2 시스템 프롬프트 가이드 (권장)

executor의 시스템 프롬프트에 아래를 추가하면 advisor 활용 품질이 향상됩니다:

```
advisor 도구는 더 강한 리뷰 모델이다. 파라미터 없이 호출하면
전체 대화 히스토리가 자동으로 전달된다.

실질적 작업(코드 작성, 파일 수정, 결론 선언) 전에 advisor를 호출하라.
파일 탐색, 소스 읽기 등 탐색 작업은 실질적 작업이 아니다.

추가 호출 시점:
- 작업 완료 시 (호출 전에 결과를 파일에 저장할 것)
- 막혔을 때 (에러 반복, 수렴 안 됨)
- 접근 방식 변경 고려 시

advice를 진지하게 받아들여라. 실패한 경우에만 적응하고,
충돌 시 한 번 더 advisor를 호출하여 해결하라.
```

### 6.3 Advisor 출력 최적화 (토큰 절감)

```
시스템 프롬프트에 추가:
"advisor는 100단어 이내로 응답하고, 설명 대신 번호 매긴 단계를 사용하라."

효과: advisor 출력 35~45% 토큰 절감
```

---

## 7. Claude Code 워크플로우와의 연계

### 7.1 PDARR 워크플로우에 Advisor 매핑

```
PLAN (/analyze, /spec)
  → Advisor 호출: "이 요구사항의 핵심 리스크는?"
  → Executor가 분석/설계 수행

DOCUMENT (/spec)
  → Executor가 명세서 초안 작성
  → Advisor 호출: "이 설계에서 놓친 엣지 케이스는?"

ACT (/run)
  → Executor가 구현
  → 막혔을 때 Advisor 호출

REVIEW (/check-code)
  → Advisor 호출: "이 구현의 보안/성능 이슈는?"
  → Review Gate 역할

REFLECT (/reflect)
  → Advisor 호출: "다음에 개선할 점은?"
```

### 7.2 기존 모델 라우팅과의 차이

| 기존 Model Routing | Advisor Strategy |
|-------------------|-----------------|
| 작업 유형별 모델 고정 선택 | 작업 중 동적 자문 |
| PM이 dispatch 시 결정 | Executor가 필요 시 호출 |
| 에이전트 단위 | 단일 요청 내 |
| 서브에이전트 생성 비용 | 자문만, 경량 |

### 7.3 실전 적용 시나리오

#### API 기반 프로젝트에서의 코드 리뷰 파이프라인

```python
# frecto_web 같은 프로젝트에서 Advisor를 활용한 자동 리뷰
import anthropic

client = anthropic.Anthropic()

# 1. Sonnet이 코드 변경사항을 분석
# 2. 보안/성능 관련 판단 시 Opus Advisor에 자문
# 3. Advisor의 조언을 반영하여 리뷰 리포트 생성

response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8192,
    betas=["advisor-tool-2026-03-01"],
    tools=[
        {
            "type": "advisor_20260301",
            "name": "advisor",
            "model": "claude-opus-4-6",
            "max_uses": 2,  # 비용 제어: 시작 시 1회 + 완료 전 1회
        }
    ],
    system="PHP 7.2 프로젝트의 코드 리뷰어. OWASP Top 10, SQL 인젝션, XSS에 주의. "
           "리뷰 시작 전과 완료 전에 advisor를 호출하라.",
    messages=[
        {"role": "user", "content": f"다음 diff를 리뷰해줘:\n\n{diff_content}"}
    ],
)
```

---

## 8. 고급 기능

### 8.1 Advisor 프롬프트 캐싱

3회 이상 advisor 호출 시 캐싱 활성화가 손익분기입니다.

```python
tools = [
    {
        "type": "advisor_20260301",
        "name": "advisor",
        "model": "claude-opus-4-6",
        "caching": {"type": "ephemeral", "ttl": "5m"},
    }
]
```

- 긴 에이전트 루프: 캐싱 활성화
- 짧은 단발성 작업: 캐싱 비활성화
- 한번 설정 후 유지 (중간 토글 시 캐시 미스)

### 8.2 Multi-turn 대화

이전 턴의 `advisor_tool_result` 블록을 다음 요청에 반드시 포함해야 합니다.

```python
# 첫 번째 요청 응답에서 advisor_tool_result 포함
# 두 번째 요청에 그대로 전달
messages = [
    {"role": "user", "content": "분석해줘"},
    {"role": "assistant", "content": [
        {"type": "text", "text": "..."},
        {"type": "server_tool_use", "id": "srvtoolu_abc", "name": "advisor", "input": {}},
        {"type": "advisor_tool_result", "tool_use_id": "srvtoolu_abc",
         "content": {"type": "advisor_result", "text": "..."}},
        {"type": "text", "text": "..."}
    ]},
    {"role": "user", "content": "추가 수정해줘"}
]
```

### 8.3 Effort 설정과의 조합

```
Sonnet (medium effort) + Opus Advisor
  = Sonnet (default effort) 수준 지능
  + 더 낮은 비용

최대 지능이 필요하면:
  Sonnet (default effort) + Opus Advisor
```

---

## 9. 제한사항

| 제한 | 설명 |
|------|------|
| Beta API | `betas: ["advisor-tool-2026-03-01"]` 헤더 필요 |
| 스트리밍 | Advisor 추론 중 executor 스트림 일시 중지 |
| 토큰 제한 | `max_tokens`는 executor에만 적용, advisor는 제한 불가 |
| 호출 횟수 | 대화 수준 제한 없음 (클라이언트에서 직접 관리) |
| 플랫폼 | Claude API 직접 호출만 (Bedrock/Vertex 미지원) |
| Priority Tier | 모델별 별도 적용 (executor tier ≠ advisor tier) |

---

## 10. 체크리스트

### Advisor 도입 시

- [ ] Beta 헤더 추가 (`advisor-tool-2026-03-01`)
- [ ] Executor 모델 선택 (권장: Sonnet 4.6)
- [ ] Advisor 모델 선택 (권장: Opus 4.6)
- [ ] `max_uses` 설정 (권장: 2~3)
- [ ] 시스템 프롬프트에 advisor 호출 가이드 추가
- [ ] Multi-turn 시 advisor_tool_result 전달 구현

### 비용 최적화

- [ ] `max_uses: 3` 이하로 제한
- [ ] Advisor 출력 길이 제한 프롬프트 추가 ("100단어 이내")
- [ ] 3회+ 호출 시 캐싱 활성화
- [ ] `usage.iterations[]`로 비용 모니터링

---

## 다음 단계

1. [하네스 엔지니어링 가이드](29-harness-engineering.md) — 하네스 설계 전체
2. [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md) — 모델별 단가
3. [Settings 스키마 레퍼런스](20-settings-schema-reference.md) — 설정 키 상세
