# 컨텍스트 윈도우 내부 동작

## 개요

Claude Code의 컨텍스트 윈도우는 단순한 토큰 버퍼가 아닙니다. 모델별 유효 용량 계산, 자동 압축 트리거, 압축 후 재주입 우선순위, 출력 토큰 에스컬레이션까지 여러 레이어가 협력하여 동작합니다. 이 문서는 v2.1.88 소스 분석을 기반으로 내부 동작을 정리합니다.

---

## 1. 모델별 유효 컨텍스트 용량

### 1.1 200K 모델 (claude-sonnet, claude-opus 기본)

| 항목 | 토큰 수 | 계산 방식 |
|------|--------|----------|
| 전체 컨텍스트 윈도우 | 200,000 | 모델 스펙 |
| output 예약 공간 | 20,000 | 최대 output token 예약 |
| **유효 입력 윈도우** | **180,000** | 200K - 20K |
| auto-compact 트리거 | **167,000** | 유효 윈도우 - 13,000 |
| blocking 임계값 | **177,000** | 유효 윈도우 - 3,000 |

**auto-compact**: 사용된 컨텍스트가 167K를 초과하면 자동 압축이 시작됩니다. 이 시점에는 아직 13K의 여유가 있으므로 압축 작업 자체가 컨텍스트를 소진하더라도 안전합니다.

**blocking**: 177K를 초과하면 새로운 요청이 차단됩니다. 이미 auto-compact가 실패했거나 비활성화된 상태에서 도달하는 최후 방어선입니다.

### 1.2 임계값 계산 공식

```
auto_compact_threshold = effective_window - 13_000
blocking_threshold     = effective_window - 3_000
effective_window       = model_context_window - max_output_tokens
```

`max_output_tokens`의 기본값은 8,192이지만, 에스컬레이션 후에는 최대 64,000까지 확장됩니다 (섹션 5 참조). 에스컬레이션이 발생하면 유효 윈도우가 줄어들고 임계값도 함께 당겨집니다.

---

## 2. 1M 컨텍스트 모델 활성화

### 2.1 활성화 조건

1M 컨텍스트는 기본 활성화되지 않습니다. 다음 세 가지 조건이 모두 충족되어야 합니다.

| 조건 | 설명 |
|------|------|
| `[1m]` suffix | 에이전트 이름 또는 설정에 `[1m]` 접미사 포함 |
| `context_1m` beta flag | API 요청 시 beta header에 `context_1m` 포함 |
| `coral_reef_sonnet` flag | 내부 feature flag 활성화 필요 |

### 2.2 1M 모델 용량 계산

```
전체 윈도우:   1,048,576 토큰
output 예약:      20,000 토큰
유효 입력:     1,028,576 토큰
auto-compact:  1,015,576 토큰 (유효 - 13K)
blocking:      1,025,576 토큰 (유효 - 3K)
```

### 2.3 비용 주의사항

1M 컨텍스트는 캐싱 효율이 낮고 per-token 비용이 동일하게 적용됩니다. 장기 세션에서는 200K 모델 + auto-compact 조합이 비용 대비 효율이 더 높을 수 있습니다.

---

## 3. Auto-Compact: 압축 동작

### 3.1 압축 트리거 조건

```
현재 사용 토큰 > auto_compact_threshold
AND DISABLE_AUTO_COMPACT != "1"
AND DISABLE_COMPACT != "1"
```

### 3.2 압축 9-Section Summary 구조

자동 압축 시 대화 히스토리는 9개 섹션으로 구조화된 요약문으로 대체됩니다.

| 섹션 | 내용 |
|------|------|
| 1. Task Overview | 전체 작업 목표와 현재 진행 상태 |
| 2. Completed Steps | 완료된 작업 목록 (파일 변경 포함) |
| 3. Current State | 현재 작업 중인 항목과 진행 위치 |
| 4. Key Decisions | 중요한 설계/구현 결정 사항 |
| 5. File Changes | 수정/생성/삭제된 파일 목록과 변경 내용 요약 |
| 6. Errors & Fixes | 발생한 오류와 해결 방법 |
| 7. Pending Items | 미완료 태스크와 다음 단계 |
| 8. Context Notes | 이후 작업에 필요한 중요 컨텍스트 |
| 9. Tool State | 마지막으로 사용한 도구와 결과 상태 |

압축은 별도의 Sonnet 모델 호출로 수행됩니다. 즉, 압축 자체에도 API 비용이 발생합니다.

---

## 4. 압축 후 재주입 (Post-Compact Reinjection)

압축이 완료되면 다음 항목들이 새 컨텍스트 상단에 자동으로 재주입됩니다.

### 4.1 재주입 우선순위 및 한도

| 재주입 항목 | 한도 | 설명 |
|------------|------|------|
| 1. Files (관련 파일) | 최대 5개, 50K 토큰 | 현재 작업과 관련도 높은 파일 우선 |
| 2. Skills | 최대 5개, 25K 토큰 | 활성화된 스킬 정의 |
| 3. Plan | 제한 없음 | 현재 작업 계획 전체 |
| 4. Tool Delta | 제한 없음 | 마지막 도구 실행 결과 |
| 5. Agent Listing | 제한 없음 | 사용 가능한 에이전트 목록 |

**총 재주입 한도**: 약 75K 토큰 (Files 50K + Skills 25K + 기타)

### 4.2 파일 관련도 순위 결정

재주입할 5개 파일은 다음 기준으로 선택됩니다.

1. 압축 직전 대화에서 명시적으로 참조된 파일
2. 현재 Plan에 언급된 파일
3. 최근 수정된 파일 (타임스탬프 기준)
4. 이전 세션에서 자주 참조된 파일 (Memory 기반)

---

## 5. Output Token 에스컬레이션

Claude Code는 작업 복잡도에 따라 output token 한도를 동적으로 조정합니다.

### 5.1 에스컬레이션 단계

| 단계 | Output Token 한도 | 활성화 조건 |
|------|-----------------|------------|
| 기본 | 8,192 | 모든 요청의 초기값 |
| 에스컬레이션 1 | 16,384 | 긴 코드 생성 감지 |
| 에스컬레이션 2 | 32,768 | 대용량 파일 작업 |
| 최대 | 64,000 | 명시적 max output 설정 |

### 5.2 에스컬레이션 영향

output token이 증가하면 유효 입력 윈도우가 감소합니다.

```
output = 64,000 적용 시:
  유효 윈도우 = 200,000 - 64,000 = 136,000
  auto-compact = 136,000 - 13,000 = 123,000  ← 훨씬 일찍 압축 발생
```

대용량 파일 생성 작업 시 예상보다 일찍 auto-compact가 발생하는 원인이 이 때문입니다.

---

## 6. 환경 변수 레퍼런스

컨텍스트 윈도우 동작을 제어하는 환경 변수 목록입니다.

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | number | 모델 최대값 | auto-compact 트리거 임계값을 강제 설정. 예: `150000`으로 설정 시 150K에서 압축 시작 |
| `CLAUDE_CODE_DISABLE_AUTO_COMPACT` | `"1"` | 미설정 | `"1"` 설정 시 자동 압축 비활성화 (blocking까지 계속 진행) |
| `CLAUDE_CODE_DISABLE_COMPACT` | `"1"` | 미설정 | 모든 압축 기능 비활성화 (DISABLE_AUTO_COMPACT 포함) |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | `"1"` | 미설정 | `"1"` 설정 시 1M 컨텍스트 사용 불가 (200K 강제) |

### 6.1 비대화형 세션 권장 설정

NightOps, CI/CD 등 자동화 세션에서는 비용 절감을 위해 다음 설정을 권장합니다.

```bash
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000   # 150K에서 조기 압축
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1   # 백그라운드 태스크 비활성화
```

---

## 7. 컨텍스트 사용량 모니터링

### 7.1 토큰 소비 패턴

일반적인 세션에서 컨텍스트 소비 패턴:

```
초기 로드:      CLAUDE.md(들) + MEMORY.md + 초기 질문  ≈ 10-30K
파일 읽기:      파일당 평균 2-5K                       ≈ 누적
도구 결과:      Bash 출력, grep 결과 등                ≈ 누적
대화 히스토리:  턴당 평균 1-3K                         ≈ 누적
```

### 7.2 압축 빈도 최적화

| 전략 | 효과 |
|------|------|
| 파일을 필요한 부분만 Read (offset/limit 활용) | 컨텍스트 절약 |
| Bash 출력을 `head -50`으로 제한 | 도구 결과 축소 |
| 불필요한 파일 반복 읽기 방지 | 중복 제거 |
| `AUTO_COMPACT_WINDOW` 낮게 설정 | 조기 압축으로 긴 세션 안정화 |

---

## 8. 흐름도 요약

```
요청 도착
    ↓
현재 토큰 수 계산
    ↓
  < 167K ?  ─── 정상 처리 ───→ 응답 생성
    ↓ NO
  < 177K ?  ─── auto-compact 시작
    │              ↓
    │         9-section 요약 생성 (Sonnet 호출)
    │              ↓
    │         재주입: Files(5/50K) + Skills(5/25K) + Plan + Tool Delta + Agents
    │              ↓
    │         새 컨텍스트로 재처리
    ↓ NO
  177K 초과 → BLOCKING (요청 거부, 세션 초기화 필요)
```

---

## 다음 단계

- [Settings 전체 스키마 레퍼런스](20-settings-schema-reference.md)
- [Memory 시스템 내부 동작](21-memory-system-internals.md)
- [Agent Frontmatter 완전 스키마](22-agent-frontmatter-schema.md)
