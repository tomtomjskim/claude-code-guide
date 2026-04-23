# 서브에이전트 효율성 가이드

## 개요

서브에이전트 스폰은 작업당 **~14,000 tokens 고정 비용**이 발생한다. 이 가이드는 고정 비용을 줄이고, 불필요한 스폰을 회피하며, 에이전트 간 중복 작업을 제거하는 12가지 전략을 다룬다.

각 전략에는 **성능 리스크 분석**이 포함되어 있다. 토큰 절감이 작업 품질이나 속도를 저하시키지 않는지 반드시 확인한 후 적용한다.

---

**관련 문서**:
- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
- [하네스 엔지니어링 가이드](29-harness-engineering.md) — 상위 축(5 컴포넌트) 맥락
- [Coordinator Mode](26-coordinator-mode.md)
- [Advisor Strategy](30-advisor-strategy.md)
- [컨텍스트 윈도우 내부](19-context-window-internals.md)
- [스킬 경량화 가이드](27-skill-lightweight-guide.md)

---

## 1. 고정 오버헤드 구조

서브에이전트 1회 스폰 시 발생하는 고정 비용:

| 구성 요소 | 토큰 수 | 비율 |
|----------|--------|------|
| 시스템 프롬프트 | ~8,000 | 57% |
| 도구 스키마 | ~3,000 | 21% |
| CLAUDE.md 체인 | ~3,000 | 21% |
| **합계** | **~14,000** | 100% |

Cloud AI MCP 비활성화를 안 하면 +5,000~7,000 추가.

### 1.1 손익분기 판단

```
메인이 직접 수행:  5,000 ~ 8,000 tokens (파일 1-2개)
서브에이전트 위임: 14,000(고정) + 변동 비용

서브에이전트가 효율적인 조건:
  → 대상 파일 3개 이상
  → 또는 변동 작업량이 20,000 tokens 이상
  → 또는 병렬화로 시간 절감이 비용 증가를 정당화할 때
```

---

## 2. 12가지 효율화 전략

### 전략 1: Result Pipe — 결과 파일 기록

에이전트 반환값이 오케스트레이터 컨텍스트를 대량 소비하는 문제를 해결한다.

**방법**: 에이전트에게 결과를 파일에 기록하고, 오케스트레이터에는 요약만 반환하도록 지시한다.

```markdown
## RETURN 규칙
- 상세 결과를 `/tmp/agent-result-{task-id}.md`에 기록하라
- 오케스트레이터에는 다음만 반환:
  - 상태: PASS | FAIL | PARTIAL
  - 결과 파일 경로
  - 핵심 이슈 (3줄 이내)
```

| 항목 | 현행 | 개선 | 절감 |
|------|------|------|------|
| 반환값 크기 | 2,000~5,000 tokens | 200~300 tokens | 90% |
| 5개 에이전트 합산 | 10,000~25,000 | 1,000~1,500 | 90% |

**성능 리스크**: 오케스트레이터가 상세 내용이 필요한 경우 추가 Read 발생.
**완화**: "PASS + 핵심 이슈 3줄"이면 90% 이상의 경우 Read 불필요. FAIL 시에만 상세 파일을 Read.

---

### 전략 2: Bash 프리플라이트 (Script-before-Agent)

에이전트 스폰 전에 Bash 스크립트로 정보를 수집하여 prompt에 인라인 주입한다. 에이전트의 탐색 턴(Glob+Grep+Read)을 제거한다.

```bash
# scripts/preflight-collect.sh
# 에이전트에 필요한 정보를 사전 수집

TARGET_DIR="${1:-.}"
echo "## File List"
find "$TARGET_DIR" -name "*.php" -o -name "*.ts" | head -30
echo ""
echo "## Key Patterns"
grep -rn "function\|class\|interface" "$TARGET_DIR" --include="*.php" | head -20
echo ""
echo "## Recent Changes"
git diff --stat HEAD~3 -- "$TARGET_DIR" 2>/dev/null | head -15
```

에이전트 prompt에 인라인:
```markdown
## CONTEXT (프리플라이트 수집 — 직접 탐색 금지)
{{preflight_output}}

## TASK
위 정보를 기반으로 작업하라. 추가 파일 탐색은 수정 대상 파일 Read만 허용.
```

| 항목 | 현행 | 개선 | 절감 |
|------|------|------|------|
| 에이전트 탐색 턴 | 3~5턴 × 3~8K | 0턴 | 9,000~40,000 tokens |
| 에이전트 실행 시간 | 100% | ~50% | 시간도 절반 |

**성능 리스크**: 프리플라이트 데이터가 stale해질 수 있음 (에이전트 실행 중 파일 변경).
**완화**: 수정 대상 파일은 실시간 Read 허용. 프리플라이트는 참조 파일(구조, 의존성)에만 적용.

---

### 전략 3: Prompt 슬롯 템플릿

구조화된 4슬롯 템플릿으로 prompt를 표준화한다.

```markdown
## SCOPE
수정 대상: src/api/users.ts (다른 파일 수정 금지)

## RULES
- PHP 7.2 호환 필수
- SQL은 prepared statement 사용
- 하드코딩 문자열 금지 (i18n 사용)

## TASK
refreshToken() 함수의 만료 시간을 30분에서 60분으로 변경.
변경 후 기존 테스트 통과 확인.

## RETURN
변경 파일 경로 + PASS/FAIL + 1줄 요약만 반환.
```

**규칙**:
- SCOPE와 RULES는 **절대 생략 금지** — 이 둘이 에이전트의 판단 품질을 결정
- TASK만 압축 대상 — 배경 설명 제거, 동사+목적어 중심
- RETURN은 전략 1(Result Pipe) 규칙과 동일

**성능 리스크**: 과도한 압축 시 에이전트 판단 오류 → 재작업.
**완화**: SCOPE/RULES를 생략하지 않으면 판단 품질은 유지됨. 절감 효과는 작지만(300~1,500 tokens) 재작업 방지 효과가 크다.

---

### 전략 4: CLAUDE.md 레이어링

서브에이전트에 CLAUDE.md 전체를 주입하지 않고, 작업 유형에 따라 필요한 레이어만 선택적으로 주입한다.

| 레이어 | 내용 | 토큰 | 대상 에이전트 |
|--------|------|------|-------------|
| **L0 (Core)** | 응답 언어, 민감 파일 규칙 | ~200 | 전체 |
| **L1 (Tech)** | 기술 스택, DB 규칙, i18n | ~500 | Developer, DBA, Reviewer |
| **L2 (Workflow)** | 워크플로우, 커밋, 배포 규칙 | ~300 | PM, Publisher |

```
현행: L0+L1+L2 = ~3,000 tokens/에이전트
개선: L0만 = ~200, L0+L1 = ~700
평균 절감: 1,500~2,000 tokens/에이전트
```

**성능 리스크**: **높음** — 필요한 규칙이 누락되면 에이전트 출력이 규칙 위반, 재작업 비용 발생.
**완화**:
1. **안전 기본값**: 의심스러우면 L0+L1 모두 주입 (L2만 조건부 생략)
2. **레이어 매핑 테이블**을 prompt 작성 시 참조

```
에이전트 유형별 필수 레이어:
  Explorer     → L0
  Developer    → L0 + L1
  DBA          → L0 + L1
  Reviewer     → L0 + L1
  PM           → L0 + L2
  Publisher    → L0 + L2
  Documenter   → L0
```

---

### 전략 5: Tiered Dispatch

작업 복잡도에 따라 정보 수집 방식을 분기한다. 모든 작업에 Scout 에이전트를 띄우지 않는다.

임계값과 실행 방식은 canonical에 정의: [`.claude/rules/subagent-strategy.md#tiered-dispatch--복잡도별-실행-방식`](../.claude/rules/subagent-strategy.md).

요약:
- 판정 축은 **파일 수**(보조: 변경 줄 수·서비스 수)
- 4단계(Trivial/Simple/Medium/Complex) 각각에 고유한 실행 방식(메인 직접 → 에이전트 1개 → digest + Worker 1-2 → Scout + Worker N)

**절감**: Medium에서 Scout 에이전트 1회(~20,000 tokens) 회피.

**성능 리스크**: 복잡도 오판 시 리소스 부족.
**완화**: 파일 수 + 변경 줄 수 기반 기계적 판정으로 주관 배제. 에이전트가 BLOCKED 반환 시 한 단계 상향.

---

### 전략 6: Context Digest 확대

현행 `context/digest-format.md` 패턴을 일반 구현 작업에도 확대 적용한다.

**적용 조건**: Worker 에이전트 2개 이상이 동일 코드베이스를 참조할 때.

```yaml
# 경량 digest (구현용)
digest:
  target_files:
    - path: "src/api/users.ts"
      exports: ["getUser", "updateUser", "refreshToken"]
      dependencies: ["src/db/connection.ts", "src/auth/jwt.ts"]
    - path: "src/auth/jwt.ts"
      exports: ["signToken", "verifyToken"]
      key_logic: "RS256 서명, 만료 시간 ENV에서 읽음"
  project_rules:
    tech_stack: "PHP 7.2, MySQL 5.7"
    constraints: ["i18n 필수", "addslashes 패턴"]
```

→ 리뷰어 6명 × 10파일 = 60회 파일 읽기를 ~20회로 감소 (토큰 40-60% 절감).

**성능 리스크**: Digest가 stale하면 오판.
**완화**: `generated_at` 타임스탬프 포함. 5분 이상 경과 시 재생성.

---

### 전략 7: 병렬 에이전트 수 가이드라인

| 병렬 수 | 비용 | 시간 | 권장 조건 |
|---------|------|------|----------|
| 1 | 1× | 기준 | 기본값 |
| 2 | 2× | 50% | 독립 작업이 명확할 때 |
| 3 | 3× | 33% | 각 작업 10분+ 예상 시 |
| 4+ | 4×+ | 25% | **PM 명시적 승인 필요** |

**규칙**:
- 동일 파일을 수정하는 에이전트는 절대 병렬 금지
- 비용이 선형 증가하므로, 시간 절감 가치가 비용을 정당화하는지 판단
- 순차 실행 시 SendMessage로 워커 재사용 검토 (고정 비용 1회만 지불)

---

### 전략 8: Advisor 패턴 적용 (리뷰 대체)

검증/리뷰 목적의 서브에이전트를 Advisor Tool로 대체한다.

```
서브에이전트 리뷰: 14,000(고정) + 10,000(작업) = 24,000 tokens
Advisor 자문:      2,000~3,000 tokens
절감: ~88%
```

**적용 범위**:

| 작업 | 서브에이전트 유지 | Advisor 대체 |
|------|-----------------|-------------|
| 코드 구현 | O | - |
| 파일 수정이 필요한 리뷰 | O | - |
| 설계 판단 자문 | - | O |
| 보안/성능 점검 (읽기 전용) | - | O |
| 코드 품질 검토 | - | O |

**성능 리스크**: Advisor는 파일을 직접 읽거나 수정할 수 없음. 실행 가능성 검증 안 됨.
**완화**: 파일 수정이 필요한 리뷰에는 서브에이전트 유지. Advisor는 읽기 전용 판단에만 적용.

---

### 전략 9: 캐시 워밍 시퀀싱

동일 시스템 프롬프트를 공유하는 에이전트들의 캐시 효율을 극대화한다.

```
현행: 3개 에이전트 동시 스폰
  → 각각 Cache Write = 3 × Input 비용

개선: 1개 먼저 → 완료 후 2개 동시 스폰
  → 1회 Cache Write + 2회 Cache Read
  → Cache Read = Input의 1/10
  → 후속 에이전트 Input 비용 90% 절감
```

**전제 조건**:
1. 프롬프트 접두사(시스템 프롬프트 + 프로젝트 규칙)가 동일해야 함
2. 5분 TTL 내에 후속 에이전트를 스폰해야 함
3. 첫 에이전트는 경량 작업으로 배정하여 빠르게 완료

**성능 리스크**: 첫 에이전트가 병목 → 전체 파이프라인 지연.
**완화**: 첫 에이전트를 Scout(탐색) 역할로 배정. 2-Phase 구조와 자연스럽게 결합.

---

### 전략 10: Spawn-Gate Hook 강화

현행 `guard-agent.sh`의 판단 로직을 확대한다.

```bash
# guard-agent.sh 확장 판단 로직
# 1. 작업 설명에서 파일 수 추정
FILE_COUNT=$(echo "$DESCRIPTION" | grep -oP '\d+' | head -1)
# 2. "단순 수정" 키워드 감지
if echo "$DESCRIPTION" | grep -qE '단순|간단|1줄|typo|오타'; then
  echo "[BLOCKED] 5줄 이하 수정은 메인에서 직접 Edit 사용"
  exit 1
fi
# 3. "탐색/분석" 키워드 감지
if echo "$DESCRIPTION" | grep -qE '탐색|분석|조사|확인|검색'; then
  echo "[BLOCKED] 탐색 목적은 메인에서 Read/Grep/Glob 사용"
  exit 1
fi
```

**성능 리스크**: 과도한 차단 → 필요한 에이전트도 막힘.
**완화**: 차단 시 반드시 "대안 제시" 포함. 사용자가 재시도 시 override 허용.

---

### 전략 11: 에이전트 사용량 로거

매 에이전트 호출의 메타데이터를 기록하여 장기적 최적화 데이터를 축적한다.

```jsonl
{"ts":"2026-04-15T10:30:00","model":"sonnet","input_tokens":18500,"output_tokens":3200,"type":"implement","files":3,"duration_ms":45000,"result":"DONE"}
{"ts":"2026-04-15T10:31:00","model":"sonnet","input_tokens":16200,"output_tokens":2800,"type":"review","files":2,"duration_ms":32000,"result":"DONE_WITH_CONCERNS"}
```

**분석 대상**:
- Haiku로 충분했던 Sonnet 호출
- 에이전트 없이 가능했던 단순 작업
- 반복되는 동일 유형 작업 → 스크립트 자동화 후보

**구현**: PostToolUse Hook으로 Agent 도구 완료 시 자동 기록.

---

### 전략 12: 모델 라우팅 세분화

**Canonical**: [`agents.yaml` `model_routing`](../agents.yaml) — 에이전트별 조건·threshold·모델 매핑. 본 섹션은 작업 유형 중심 요약.

현행 3단계(Opus/Sonnet/Haiku)를 작업 유형에 따라 더 구체적으로 매핑한다.

| 작업 유형 | 모델 | 이유 |
|----------|------|------|
| 파일 탐색, 구조 분석 | Haiku | 읽기 전용, 판단 불필요 |
| 단순 편집, 포맷팅, 문서 수정 | Haiku | 규칙 따르기만 하면 됨 |
| 일반 코드 구현 | Sonnet | 비용-품질 최적 |
| 코드 리뷰, 보안 분석 | Sonnet | 판단 필요하나 Sonnet으로 충분 |
| 복잡한 아키텍처 설계, 멀티서비스 조율 | Opus | 높은 추론 품질 필요 |

```
비용 비교 (에이전트 1회, 변동 비용 10K tokens 기준):
  Opus:   Input 10K × $5 + Output 3K × $25 = $0.125
  Sonnet: Input 10K × $3 + Output 3K × $15 = $0.075  (40% 절감)
  Haiku:  Input 10K × $1 + Output 3K × $5  = $0.025  (80% 절감)
```

---

## 3. 우선순위 매트릭스

| 순위 | 전략 | 절감 규모 | 성능 리스크 | 구현 난이도 | 즉시 적용 |
|------|------|----------|-----------|-----------|----------|
| 1 | Result Pipe | 에이전트당 2~5K | 낮 | 매우 쉬움 | O |
| 2 | Bash 프리플라이트 | 에이전트당 9~40K | 낮 | 쉬움 | O |
| 3 | Prompt 슬롯 템플릿 | 에이전트당 300~1.5K | 낮 | 쉬움 | O |
| 4 | 모델 라우팅 세분화 | 에이전트당 40~80% | 없음 | 쉬움 | O |
| 5 | Tiered Dispatch | 세션당 14~42K | 중 | 중간 | O |
| 6 | CLAUDE.md 레이어링 | 에이전트당 1.5~2K | **높** | 쉬움 | 조건부 |
| 7 | Context Digest 확대 | Worker×3 시 40~60% | 낮 | 중간 | O |
| 8 | 병렬 수 가이드라인 | 비용 선형 절감 | 없음 | 쉬움 | O |
| 9 | Advisor 대체 | 리뷰당 ~20K | 중 | 중간 | 조건부 |
| 10 | 캐시 워밍 시퀀싱 | 후속 에이전트 60% | 중 | 중간 | 검증 필요 |
| 11 | Spawn-Gate Hook | 세션당 14~42K | 낮 | 중간 | O |
| 12 | 사용량 로거 | 장기 10~20% | 없음 | 쉬움 | O |

---

## 4. 실행 로드맵

### Phase 1 — 즉시 적용 (prompt 수정만)

1. **Result Pipe**: 서브에이전트 prompt RETURN 섹션에 파일 기록 규칙 추가
2. **Prompt 슬롯 템플릿**: `[SCOPE][RULES][TASK][RETURN]` 4슬롯 표준화
3. **모델 라우팅**: 작업 유형별 모델 매핑 테이블 적용

### Phase 2 — 단기 (스크립트 작성)

4. **Bash 프리플라이트**: `scripts/preflight-collect.sh` 작성
5. **Tiered Dispatch**: 복잡도 판정 규칙을 subagent-strategy.md에 추가
6. **사용량 로거**: PostToolUse Hook + jsonl 로깅

### Phase 3 — 중기 (검증 후 적용)

7. **CLAUDE.md 레이어링**: L0/L1/L2 분리 + 안전 기본값 테스트
8. **Advisor 통합**: 읽기 전용 리뷰에 Advisor 패턴 적용
9. **캐시 워밍**: 프롬프트 접두사 표준화 + 시퀀싱 효과 측정

---

## 5. A/B 벤치마크 — Old vs New 전략

동일 작업(스크립트 생성)을 Old 방식과 New 방식으로 실행한 실측 결과.

### 테스트 조건

| 항목 | Old (대조군) | New (실험군) |
|------|-------------|-------------|
| 모델 | Sonnet 4.6 | Sonnet 4.6 |
| Prompt 구조 | 장황한 배경 설명 + 자유 형식 | 4슬롯 템플릿 (SCOPE/RULES/TASK/RETURN) |
| 사전 정보 | 없음 (에이전트가 직접 탐색) | 프리플라이트 데이터 인라인 |
| 반환 규칙 | 전체 결과 + 상세 설명 반환 | Result Pipe (PASS/FAIL + 1줄 요약) |
| 작업 내용 | `scripts/preflight-collect.sh` 생성 | 동일 |

### 결과

| 지표 | Old | New | 절감율 |
|------|-----|-----|-------|
| **Total Tokens** | 55,933 | 24,925 | **55.4%** |
| **Tool Uses** | 22 | 4 | **81.8%** |
| **Duration** | 236초 | 47초 | **80.1%** |
| **반환값 크기** | ~2,500 tokens | ~100 tokens | **96%** |

### 절감 요인 분해

| 요인 | 절감 기여 | 전략 대응 |
|------|----------|----------|
| 프리플라이트 데이터 인라인 → 탐색 턴 18회→0회 | ~20,000 tokens | 전략 2 |
| "직접 탐색 최소화" 지시 → 불필요 Read/Grep 차단 | ~7,600 tokens | 전략 2, 3 |
| 반환값 압축 (Result Pipe) | ~2,400 tokens | 전략 1 |
| 배경 설명 제거 (4슬롯 템플릿) | ~1,000 tokens | 전략 3 |

### 품질 영향

두 에이전트 모두 동일 사양의 스크립트를 생성했으며, 출력 품질 저하는 관측되지 않았다.

- Old: 22회 도구 호출로 기존 스크립트를 탐색하고, 패턴을 분석한 후 생성
- New: 4회 도구 호출로 프리플라이트 데이터를 참조하여 즉시 생성

**결론**: 프리플라이트 + 탐색 차단이 **가장 큰 절감 요인**(전체 절감의 ~65%)이며, prompt 압축 단독 효과는 상대적으로 작다. Tool uses 감소가 duration 감소와 직결되어 **비용과 속도 모두 개선**된다.

---

## 6. 성능 저하 방지 원칙

1. **안전 기본값 우선**: 토큰 절감보다 작업 정확성이 우선. 의심 시 더 많은 컨텍스트를 주입
2. **SCOPE/RULES 생략 금지**: prompt 압축은 TASK와 배경 설명에서만 수행
3. **재작업 비용 인식**: 에이전트 1회 재스폰(~14K) > 추가 컨텍스트 주입(~2K)
4. **점진적 적용**: Phase 1 → 효과 측정 → Phase 2 → 효과 측정 → Phase 3
5. **FAIL 시 상향 규칙**: Tiered Dispatch에서 에이전트가 BLOCKED 반환 시 한 단계 상향

---

## 다음 단계

1. [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
2. [Advisor Strategy](30-advisor-strategy.md)
3. [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
4. [Coordinator Mode](26-coordinator-mode.md)
