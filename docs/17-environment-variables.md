# 환경 변수 레퍼런스

## 개요

Claude Code가 인식하는 모든 환경 변수를 카테고리별로 정리합니다. v2.1.88 소스 기준으로 확인된 변수들입니다.

---

**관련 문서**:
- [토큰 가격 및 비용 최적화](14-token-pricing-optimization.md)
- [사용량 한도 및 Rate Limit](15-usage-limits-ratelimit.md)
- [Fast Mode 가이드](17-fast-mode.md)
- [초기 셋업 체크리스트](00-setup-checklist.md)

---

## 1. 컨텍스트 관리

컨텍스트 윈도우 크기와 자동 압축 동작을 제어합니다.

### CLAUDE_CODE_AUTO_COMPACT_WINDOW

컨텍스트 자동 압축이 트리거되는 토큰 수 임계값입니다.

```bash
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000
```

| 항목 | 설명 |
|------|------|
| 기본값 | 모델 최대 컨텍스트 - 13K 토큰 |
| 권장값 | 150000 (비용 절감 목적) |
| 동작 | 컨텍스트가 이 값에 도달하면 자동 압축 실행 |
| 효과 | 낮게 설정할수록 Input 토큰 소비 감소 |

### CLAUDE_CODE_AUTOCOMPACT_PCT_OVERRIDE

자동 압축 후 유지할 컨텍스트 비율을 오버라이드합니다.

```bash
export CLAUDE_CODE_AUTOCOMPACT_PCT_OVERRIDE=0.7
```

| 항목 | 설명 |
|------|------|
| 기본값 | 내부 기본값 적용 |
| 범위 | 0.0 ~ 1.0 (분수) |
| 동작 | 압축 후 컨텍스트의 해당 비율만 유지 |
| 예시 | 0.7 = 압축 후 70% 유지 |

### CLAUDE_CODE_BLOCKING_LIMIT_OVERRIDE

컨텍스트가 이 값에 도달하면 새 요청을 차단합니다.

```bash
export CLAUDE_CODE_BLOCKING_LIMIT_OVERRIDE=180000
```

| 항목 | 설명 |
|------|------|
| 기본값 | 모델 최대 컨텍스트 - 3K 토큰 |
| 동작 | 이 한도 초과 시 요청 차단 |
| 목적 | 컨텍스트 오버플로우 방지 |

### CLAUDE_CODE_DISABLE_COMPACT

컨텍스트 압축 기능 자체를 비활성화합니다.

```bash
export CLAUDE_CODE_DISABLE_COMPACT=1
```

| 항목 | 설명 |
|------|------|
| 기본값 | 비활성화되지 않음 (압축 활성) |
| 주의 | 장기 세션에서 컨텍스트 한도 초과 위험 |
| 사용 시점 | 압축 없이 전체 컨텍스트 유지가 필요한 경우 |

### CLAUDE_CODE_DISABLE_AUTO_COMPACT

자동 압축만 비활성화합니다 (수동 압축은 가능).

```bash
export CLAUDE_CODE_DISABLE_AUTO_COMPACT=1
```

| 항목 | 설명 |
|------|------|
| 차이점 | DISABLE_COMPACT는 전체 압축 비활성, 이 변수는 자동만 비활성 |
| 수동 압축 | `/compact` 명령으로 여전히 실행 가능 |

### CLAUDE_CODE_DISABLE_1M_CONTEXT

1M 토큰 컨텍스트 모델 지원을 비활성화합니다.

```bash
export CLAUDE_CODE_DISABLE_1M_CONTEXT=1
```

| 항목 | 설명 |
|------|------|
| 기본값 | 1M 컨텍스트 지원 활성화 |
| 효과 | 표준 컨텍스트 크기(200K)로 제한 |
| 사용 시점 | 1M 컨텍스트로 인한 과도한 비용 방지 |

---

## 2. 모델 및 비용 제어

사용 모델과 비용 관련 동작을 제어합니다.

### CLAUDE_CODE_SUBAGENT_MODEL

Task 도구로 생성된 서브에이전트의 기본 모델을 지정합니다.

```bash
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet

# 또는 전체 모델 ID
export CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6-20251201
```

| 항목 | 설명 |
|------|------|
| 기본값 | 현재 세션과 동일한 모델 |
| 권장값 | sonnet (비용 최적화) |
| 효과 | Opus 세션에서 서브에이전트 비용 ~40% 절감 |
| 허용값 | sonnet, haiku, opus 또는 전체 모델 ID |

### CLAUDE_CODE_DISABLE_FAST_MODE

Fast Mode를 전역으로 비활성화합니다.

```bash
export CLAUDE_CODE_DISABLE_FAST_MODE=1
```

| 항목 | 설명 |
|------|------|
| 기본값 | Fast Mode 활성화 가능 (조건 충족 시 자동 전환) |
| 효과 | Opus 4.6 Fast Mode 차단 (6x 비용 방지) |
| 강력도 | settings.json의 fastMode:false보다 강력 |
| 자세한 내용 | [17-fast-mode.md](17-fast-mode.md) 참조 |

### ANTHROPIC_SMALL_FAST_MODEL

빠른 소규모 작업(autocomplete, 간단한 판단)에 사용할 모델을 지정합니다.

```bash
export ANTHROPIC_SMALL_FAST_MODEL=claude-haiku-3-5-20241022
```

| 항목 | 설명 |
|------|------|
| 기본값 | 내부 기본 소형 모델 |
| 사용처 | 자동완성, 단순 분류, 빠른 판단 |
| 권장값 | Haiku 3.5 (가장 저렴) |

---

## 3. 실행 제어

동시성, 백그라운드 작업, 코디네이터 동작을 제어합니다.

### CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY

도구 병렬 실행 최대 수를 제한합니다.

```bash
export CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY=3
```

| 항목 | 설명 |
|------|------|
| 기본값 | 10 (최대 병렬) |
| 권장값 | 3-5 (비용 및 API 부하 균형) |
| 효과 | 낮을수록 동시 API 호출 감소 |
| Read/Grep/Glob | 병렬 도구 (이 변수 영향 받음) |
| Bash/Edit | 직렬 도구 (영향 없음) |

### CLAUDE_CODE_DISABLE_BACKGROUND_TASKS

백그라운드 태스크 처리를 비활성화합니다.

```bash
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
```

| 항목 | 설명 |
|------|------|
| 기본값 | 백그라운드 태스크 활성화 |
| 사용 시점 | 비대화형 세션, NightOps 자동화 |
| 효과 | 안정적인 비대화형 실행 보장 |
| 주의 | 대화형 세션에서는 설정 불필요 |

### CLAUDE_CODE_COORDINATOR_MODE

멀티 에이전트 코디네이터 동작 모드를 설정합니다.

```bash
export CLAUDE_CODE_COORDINATOR_MODE=strict
```

| 항목 | 설명 |
|------|------|
| 기본값 | 기본 코디네이터 모드 |
| 값 | strict, permissive 등 |
| 사용처 | 에이전트 팀 오케스트레이션 튜닝 |

---

## 4. 디버깅

### CLAUDE_CODE_DEBUG

디버그 모드를 활성화합니다. 상세한 내부 로그가 출력됩니다.

```bash
export CLAUDE_CODE_DEBUG=1
```

| 항목 | 설명 |
|------|------|
| 기본값 | 비활성화 |
| 출력 내용 | API 요청/응답, 도구 호출 상세, 컨텍스트 상태 |
| 주의 | 민감 정보(API 키 등)가 로그에 포함될 수 있음 |
| 사용 시점 | 예상치 못한 동작 조사, 성능 분석 |

```bash
# 디버그 로그를 파일로 저장
CLAUDE_CODE_DEBUG=1 claude --print "작업 실행" 2>&1 | tee debug.log
```

---

## 5. 실험적 기능

아직 안정화되지 않은 실험적 기능들입니다. 프로덕션 환경에서는 주의하여 사용하세요.

### CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS

에이전트 팀 기능을 활성화합니다.

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

| 항목 | 설명 |
|------|------|
| 상태 | 실험적 (v2.1.88 기준) |
| 기능 | 멀티 에이전트 팀 오케스트레이션 |
| 주의 | 안정성 보장 없음, 동작 변경 가능 |

### CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS

Fast Mode 중 네트워크 오류 발생 시 재시도 없이 건너뜁니다.

```bash
export CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS=1
```

| 항목 | 설명 |
|------|------|
| 상태 | 실험적 |
| 사용 시점 | 네트워크 불안정 환경에서의 Fast Mode |
| 효과 | 네트워크 오류 시 폴백 없이 진행 |

---

## 6. 설정 방법

### 방법 1: Shell 직접 export

현재 셸 세션에만 적용됩니다.

```bash
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet
export CLAUDE_CODE_DISABLE_FAST_MODE=1
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000

claude  # 위 설정이 적용된 상태로 실행
```

### 방법 2: ~/.bashrc 또는 ~/.zshrc 등록

모든 셸 세션에 영구 적용됩니다.

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
echo 'export CLAUDE_CODE_SUBAGENT_MODEL=sonnet' >> ~/.bashrc
echo 'export CLAUDE_CODE_DISABLE_FAST_MODE=1' >> ~/.bashrc
echo 'export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000' >> ~/.bashrc

# 즉시 적용
source ~/.bashrc
```

### 방법 3: settings.json env 섹션 (권장)

프로젝트별 또는 글로벌 설정으로 관리합니다. 설정 파일로 버전 관리가 가능합니다.

```json
// ~/.claude/settings.json (글로벌)
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY": "5"
  }
}
```

```json
// 프로젝트/.claude/settings.json (프로젝트 전용)
{
  "env": {
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000",
    "CLAUDE_CODE_DEBUG": "0"
  }
}
```

### 방법 4: 인라인 실행

단일 명령 실행 시 임시 적용합니다.

```bash
CLAUDE_CODE_DISABLE_FAST_MODE=1 \
CLAUDE_CODE_SUBAGENT_MODEL=sonnet \
claude --print "코드 분석 실행"
```

---

## 7. 권장 설정 프리셋

### 대화형 개발 세션 (기본)

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000"
  }
}
```

### 자동화/NightOps 세션

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000",
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY": "3"
  }
}
```

### 디버깅 세션

```json
{
  "env": {
    "CLAUDE_CODE_DEBUG": "1",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"
  }
}
```

### 최대 절약 세션 (한도 근접 시)

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "haiku",
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000",
    "CLAUDE_CODE_AUTOCOMPACT_PCT_OVERRIDE": "0.6",
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY": "2",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "ANTHROPIC_SMALL_FAST_MODEL": "claude-haiku-3-5-20241022"
  }
}
```

---

## 8. 설정 우선순위

환경 변수는 settings.json의 env 섹션과 셸 export 모두 지원됩니다.

```
우선순위 (높음 → 낮음):
  1. 셸 export (현재 세션)
  2. settings.local.json env
  3. 프로젝트 settings.json env
  4. 글로벌 ~/.claude/settings.json env
  5. managed settings

주의: 셸에서 이미 export된 변수는 settings.json보다 우선합니다.
```

---

## 다음 단계

1. [Fast Mode 가이드](17-fast-mode.md)
2. [토큰 가격 및 비용 최적화](14-token-pricing-optimization.md)
3. [사용량 한도 및 Rate Limit](15-usage-limits-ratelimit.md)
4. [초기 셋업 체크리스트](00-setup-checklist.md)
