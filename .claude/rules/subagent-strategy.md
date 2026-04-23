---
description: "서브에이전트 사용 전략 — 스폰 판단, prompt 구조, 토큰 효율, 성능 보호"
---
# 서브에이전트 사용 전략

> 상세 가이드: [docs/33-subagent-efficiency.md](../../docs/33-subagent-efficiency.md)

## 핵심 원칙
- 서브에이전트 1회 = **~14,000 tokens 고정 비용** (시스템 프롬프트 + 도구 스키마 + CLAUDE.md). 분해 상세는 [`docs/33-subagent-efficiency.md#1-고정-오버헤드-구조`](../../docs/33-subagent-efficiency.md#1-고정-오버헤드-구조) 참조
- 서브에이전트 내부에서는 PreToolUse Hook이 적용되지 않는다
- 서브에이전트는 `.claude/rules/*.md`를 상속받지 않을 수 있다
- prompt에 필요한 규칙을 명시적으로 포함해야 한다
- **토큰 절감보다 작업 정확성이 우선** — 의심 시 더 많은 컨텍스트를 주입

## Tiered Dispatch — 복잡도별 실행 방식

| 복잡도 | 판정 기준 | 실행 방식 |
|--------|----------|----------|
| Trivial | 파일 ≤2, 변경 ≤20줄 | 메인이 직접 수행 |
| Simple | 파일 ≤4, 변경 ≤100줄 | 메인 직접 또는 에이전트 1개 |
| Medium | 파일 ≤8 | 메인이 digest 생성 + Worker 1-2개 |
| Complex | 파일 >8 또는 서비스 2+ | Scout(Haiku) → digest → Worker N개(Sonnet) |

### 복잡도 × 예산 × 실행 3축 매핑

각 복잡도는 `agents.yaml` `workflow_budgets`의 예산 레벨과 전형적으로 대응한다. 예산은 비용 상한이며 복잡도 판정의 결과이지 입력이 아니다.

| 복잡도 | 예산 (agents.yaml) | 상한 | 실행 축 |
|--------|-------------------|------|--------|
| Trivial | `quick-fix` | $2.00 | 메인 직접 (에이전트 스폰 없음) |
| Simple | `quick-fix` 또는 `standard` | $2-5 | 메인 직접 또는 에이전트 1개 |
| Medium | `standard` | $5.00 | 메인 digest + Worker 1-2개 |
| Complex | `thorough` | $10.00 | Scout(Haiku) → digest → Worker N개(Sonnet) |

예산 정의 canonical: [`agents.yaml` `workflow_budgets`](../../agents.yaml). 실행 축은 위 Tiered Dispatch 표 참조.

### 메인이 직접 수행 (에이전트 금지)
- 파일 탐색, 코드 분석, 구조 파악 → Read/Grep/Glob 직접 사용
- 단일 파일 수정, 버그 수정, 설정 변경
- 5줄 이하의 간단한 수정

### 서브에이전트 위임 허용
- 3개 이상 파일에 걸친 구현 작업
- 독립적인 병렬 작업 (빌드 + 테스트 + 린트 동시)
- 장기 세션(20+ 턴)에서 컨텍스트 보호가 필요한 구현
- 명확한 스펙이 정의된 모듈 단위 작업

## Prompt 4슬롯 템플릿

```markdown
## SCOPE: 수정 대상 파일 (다른 파일 수정 금지)
## RULES: 필수 준수 규칙 (생략 금지)
## TASK: 동사+목적어 중심 지시 (배경 설명 제거)
## RETURN: 결과 파일 경로 + PASS/FAIL + 핵심 이슈 3줄 이내
```

**SCOPE와 RULES는 절대 생략 금지** — 이 둘이 에이전트 판단 품질을 결정한다.

## Result Pipe — 결과 반환 규칙

에이전트 반환값이 오케스트레이터 컨텍스트를 소비하는 것을 방지한다.

- 상세 결과를 파일에 기록 (`/tmp/agent-result-{task}.md`)
- 오케스트레이터에는 **상태 + 파일 경로 + 핵심 요약 3줄**만 반환
- FAIL 시에만 오케스트레이터가 결과 파일을 Read

## Bash 프리플라이트

에이전트 스폰 전 Bash로 정보를 수집하여 prompt에 인라인 주입한다.
에이전트의 탐색 턴(Glob+Grep+Read)을 제거하여 9K-40K tokens 절감.

- 수정 대상 파일만 에이전트가 직접 Read 허용
- 참조 파일(구조, 의존성)은 프리플라이트 데이터 사용

## 모델 라우팅

**Canonical**: [`agents.yaml` `model_routing`](../../agents.yaml) — 에이전트별 조건·threshold·모델 매핑의 권위 정의. 아래 표는 비용 중심 요약.

| 작업 유형 | 모델 | 비용 비율 |
|----------|------|----------|
| 탐색, 구조 분석, 포맷팅 | Haiku | 1× |
| 일반 구현, 리뷰, 문서 수정 | Sonnet | 3× |
| 복잡한 설계, 멀티서비스 조율 | Opus | 5× |

## 병렬 에이전트 규칙

- 2개까지 기본 허용 (독립 작업이 명확할 때)
- 3개는 각 작업 10분+ 예상 시 조건부 허용
- 4개 이상은 PM 명시적 승인 필요
- **동일 파일을 수정하는 에이전트는 절대 병렬 금지**
- 순차 작업 시 SendMessage로 워커 재사용 검토 (고정 비용 1회)

## 토큰 효율 기타

- 독립 작업 2-3개를 **하나의 서브에이전트로 합쳐서** 오버헤드 1회로 줄인다
- 동일 파일을 여러 서브에이전트가 중복 읽지 않도록 한다
- 검증/리뷰 목적은 Advisor 패턴 검토 (서브에이전트 대비 88% 절감)
- 에이전트가 BLOCKED 반환 시 Tiered Dispatch 한 단계 상향
