# Claude Code 컨텍스트 윈도우와 상태 관리

> 검증 기준일: 2026-08-13
> 이 문서는 공개 공식 동작을 기준으로 합니다. 특정 Claude Code 버전의 번들 내부 상수와 미공개 구현을 장기 계약으로 취급하지 않습니다.

공식 기준:

- Model configuration: https://code.claude.com/docs/en/model-config
- Settings: https://code.claude.com/docs/en/settings
- Subagents: https://code.claude.com/docs/en/sub-agents
- Thinking: https://platform.claude.com/docs/en/about-claude/models/extended-thinking-models
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

관련 문서:

- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [하네스 엔지니어링](29-harness-engineering.md)
- [스킬 경량화](27-skill-lightweight-guide.md)

---

## 1. 컨텍스트는 무엇으로 구성되는가

Claude Code의 active context에는 다음 계층이 들어갈 수 있습니다.

```text
시스템과 조직 정책
사용자·프로젝트 CLAUDE.md와 rules
활성화된 tools, MCP, Skills
현재 대화 message history
파일과 검색 결과
subagent가 반환한 요약
thinking 또는 redacted_thinking block
compaction 이후의 summary
```

파일을 많이 읽는 것보다 필요한 근거를 정확히 선택하고, 오래된 정보를 active context에서 제거하는 것이 중요합니다.

---

## 2. Context window와 1M 지원

현재 Claude Code 공식 문서는 Fable 5, Sonnet 5, Opus 4.6 이후 일부 모델, Sonnet 4.6에 1M context 지원을 설명합니다. 사용 가능 여부는 모델, 공급자, 구독 플랜과 usage credits에 따라 다릅니다.

확인 방법:

```text
/model
/status
```

일부 모델과 환경은 `[1m]` alias를 지원하고, 일부 최신 모델은 별도 suffix 없이 1M이 기본입니다. 구버전의 고정 임계값이나 feature flag를 그대로 재사용하지 말고 현재 모델 설정 문서를 확인합니다.

### 컨텍스트가 크다고 모두 넣지 않는다

1M context는 다음을 허용하지만 권장하지는 않습니다.

- 저장소 전체 무차별 입력
- 완료된 debug log 영구 유지
- 같은 문서의 여러 버전 동시 주입
- 검증되지 않은 trace와 내부 state 보존
- 여러 agent의 중복 탐색 결과 누적

큰 window는 선택 비용을 없애지 않습니다. 불필요한 context는 비용, latency, instruction conflict, stale fact 위험을 늘립니다.

---

## 3. Auto-compaction

현재 설정:

```json
{
  "autoCompactEnabled": true,
  "autoCompactWindow": 500000
}
```

- `autoCompactEnabled` 기본값은 true입니다.
- `autoCompactWindow`는 100,000~1,000,000 token 범위에서 설정할 수 있습니다.
- 값을 지정하지 않으면 Claude Code가 모델에 맞춘 window를 사용합니다.
- `/autocompact`, `--autocompact`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`가 설정을 변경하거나 override할 수 있습니다.

### 기본 권장

`autoCompactWindow`를 임의로 150K 같은 고정값으로 낮추지 않습니다. 다음을 측정한 뒤 조정합니다.

- compaction 전 token
- summary 이후 재탐색 횟수
- 누락된 결정과 제약
- retry와 context 재주입 비용
- 장기 작업 성공률

### Compaction의 신뢰 경계

compaction summary는 연속성을 위한 모델 입력입니다. 다음 용도로 단독 사용하지 않습니다.

- 감사 로그
- 사실의 최종 source of truth
- 승인 또는 배포 근거
- 정확한 tool 실행 기록
- hidden reasoning의 복원본

중요 상태는 별도의 semantic checkpoint로 관리합니다.

---

## 4. Semantic checkpoint

```yaml
verified_facts:
  - claim: "검증된 사실"
    evidence: "test:runtime-contract"
assumptions: []
decisions: []
open_questions: []
tool_receipts: []
```

checkpoint 원칙:

- fact마다 source 또는 validator가 있습니다.
- assumption과 fact를 분리합니다.
- contradiction은 기존 내용을 조용히 덮지 않습니다.
- 완료된 tool 결과는 raw payload보다 실행 영수증과 핵심 결과를 남깁니다.
- 모델 또는 provider를 변경해도 business state는 유지할 수 있어야 합니다.
- thinking block을 portable business state로 사용하지 않습니다.

---

## 5. Thinking block과 opaque state

현재 Claude API는 regular `thinking`, `redacted_thinking`, opaque `signature` 같은 block을 반환할 수 있습니다.

### 동일 모델의 multi-turn 또는 tool workflow

- API가 반환한 thinking block을 필요한 경우 그대로 round-trip합니다.
- 내용을 수정, 재구성, 순서 변경하지 않습니다.
- `redacted_thinking`도 별도 block type으로 포함합니다.
- `signature`와 encrypted `data`를 해석하거나 파싱하지 않습니다.

### 모델 전환

공식 문서는 모델을 전환할 때 이전 assistant turn의 `thinking`과 `redacted_thinking` block을 제거하도록 안내합니다.

```text
same model continuation
→ required blocks를 unchanged round-trip

model switch
→ previous thinking/redacted_thinking strip
→ verified business checkpoint와 tool evidence로 재구성
```

다른 모델이 block을 무시하더라도 input token에는 포함될 수 있습니다. 비용과 상태 오염을 막기 위해 명시적으로 제거합니다.

### 저장 정책

- Git, issue, PR, 공개 transcript에 opaque state를 복사하지 않습니다.
- 일반 application log에 raw response를 기록하지 않습니다.
- 필요 시 provider state는 짧은 TTL과 tenant/user/session binding으로 격리합니다.
- summary text를 실제 내부 reasoning 원문이나 감사 증거로 간주하지 않습니다.

---

## 6. Prompt caching과 thinking

공식 API 기준:

- thinking block 자체에 `cache_control`을 직접 붙일 수 없습니다.
- 이전 assistant turn 안의 thinking block은 다른 content와 함께 cache될 수 있습니다.
- cache read 시 thinking block도 input token에 포함될 수 있습니다.
- thinking mode, budget 또는 effort 변경은 message cache를 무효화할 수 있습니다.
- speed를 standard와 fast 사이에서 바꾸면 cache가 분리됩니다.

따라서 thinking을 많이 생성한 긴 대화에서 모델, effort, speed를 자주 변경하면 cache hit과 context 비용이 악화될 수 있습니다.

---

## 7. Subagent context

서브에이전트는 독립 context window와 system prompt를 사용하고 메인 대화에는 최종 결과를 반환합니다.

장점:

- 대량 검색 결과와 log를 메인 context에서 격리
- 도구와 permission 제한
- 역할별 model과 effort 선택

비용:

- 별도의 model call
- startup instruction과 file read
- 결과 통합과 재검증
- 중복 탐색 가능성

현재 Claude Code는 서브에이전트에도 auto-compaction을 적용합니다. 메인 대화가 compact되어도 별도 subagent transcript는 독립적으로 유지될 수 있으므로, 민감한 output과 retention 정책을 별도로 봅니다.

### 사용 기준

```text
side task가 메인 context를 크게 오염
독립적인 read-heavy 조사
도구 권한을 제한해야 함
역할별 모델 라우팅 가치가 있음
```

단순 1~2파일 수정이나 즉시 다음 단계에 필요한 조사에는 서브에이전트가 오히려 비쌀 수 있습니다.

---

## 8. Context hygiene 운영 루프

### 작업 시작

1. CLAUDE.md와 현재 요청을 읽습니다.
2. 관련 문서와 파일을 검색해 후보를 좁힙니다.
3. source priority와 최신 상태를 확인합니다.
4. 긴 history보다 현재 code, test, authoritative docs를 우선합니다.

### 작업 중

- 중복 file read를 줄입니다.
- tool output은 필요한 부분만 반환합니다.
- resolved debug trace를 계속 재주입하지 않습니다.
- subagent에게 compact packet과 명확한 scope를 줍니다.
- 중요한 결정은 checkpoint에 즉시 반영합니다.

### 작업 종료

- 변경, 검증, 미실행 범위, 잔여 위험을 기록합니다.
- 일시적 trace와 stable knowledge를 분리합니다.
- 다음 세션에는 raw transcript 전체가 아니라 검증된 checkpoint를 전달합니다.

---

## 9. 안티패턴

| 안티패턴 | 문제 | 대안 |
|---|---|---|
| context window가 크므로 전체 repo 입력 | 비용과 충돌 증가 | 검색 후 관련 범위만 읽기 |
| autoCompactWindow를 근거 없이 고정 | 요약 누락 또는 불필요한 context 비용 | 모델 기본값 후 계측 |
| compaction summary를 SSOT로 사용 | 사실 변형과 provenance 손실 | evidence-linked checkpoint |
| thinking block을 일반 JSON log에 저장 | 민감정보와 opaque state 노출 | logging allowlist |
| 모델 전환 후 이전 thinking 유지 | 무시되는 token과 state 혼합 | thinking block strip |
| 서브에이전트 결과를 검증 없이 합침 | 오류 전파 | 메인 executor 검증 |
| 높은 effort로 context 문제 해결 | token 증가, stale context 유지 | retrieval와 compaction 개선 |

---

## 10. 검증 체크리스트

- [ ] 현재 모델의 context window를 `/model` 또는 공식 문서로 확인했다.
- [ ] `autoCompactWindow` 값에 측정 근거가 있다.
- [ ] compaction summary와 verified checkpoint를 구분한다.
- [ ] model switch 시 thinking과 redacted_thinking을 제거한다.
- [ ] opaque signature와 encrypted state를 파싱하지 않는다.
- [ ] raw response와 thinking state를 일반 log에 저장하지 않는다.
- [ ] cache usage와 context 비용을 usage field로 확인한다.
- [ ] subagent retention과 민감 output을 별도로 검토한다.
