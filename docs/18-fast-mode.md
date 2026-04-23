# Fast Mode 가이드

## 개요

Fast Mode는 Opus 4.6 전용 고속 출력 모드입니다. 비용이 일반 모드 대비 6배이므로 반드시 비활성화해야 합니다.

---

**관련 문서**:
- [환경 변수 레퍼런스](17-environment-variables.md)
- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [사용량 한도 및 Rate Limit](16-usage-limits-ratelimit.md)

---

## 1. Fast Mode란 무엇인가

Fast Mode는 claude-opus-4-6 모델에서만 사용할 수 있는 특수 출력 모드입니다. Anthropic이 Opus 4.6에 제공하는 고속 추론 경로로, 일반 Opus 4.6보다 응답 속도가 빠르지만 토큰당 비용이 6배 높습니다.

### 핵심 특징

```
모델:   claude-opus-4-6 전용
속도:   일반 모드보다 빠른 응답
비용:   일반 Opus 4.6 대비 6배
품질:   일반 모드와 동일 (차이 없음)
```

---

## 2. 비용 비교

### 모델별 토큰 가격 비교

| 모드 | Input | Output | Cache Write | Cache Read |
|------|-------|--------|-------------|------------|
| Sonnet 4.6 | $3.00 | $15.00 | $3.75 | $0.30 |
| Opus 4.6 (일반) | $5.00 | $25.00 | $6.25 | $0.50 |
| Opus 4.6 (Fast) | $30.00 | $150.00 | $37.50 | $3.00 |

단위: USD per 1M tokens

### Fast Mode 비용 승수

```
Opus 4.6 Fast vs Sonnet 4.6:
  Input:  $30 / $3   = 10배
  Output: $150 / $15 = 10배

Opus 4.6 Fast vs Opus 4.6 일반:
  Input:  $30 / $5   = 6배
  Output: $150 / $25 = 6배
```

### 실제 작업 비용 예시

```
코드 분석 작업 1회 (50K Input + 5K Output):
  Sonnet 4.6:       $0.000150 + $0.000075 = $0.000225
  Opus 4.6 일반:    $0.000250 + $0.000125 = $0.000375
  Opus 4.6 Fast:    $0.001500 + $0.000750 = $0.002250

Fast vs Sonnet 차이: $0.002025 (약 10배)
하루 100회 작업 시:
  Sonnet:         $0.0225
  Opus Fast:      $0.2250  (차이: $0.2025/일 = $6.08/월)
```

---

## 3. Fast Mode 활성화 5가지 조건 (fastMode.ts)

Fast Mode는 다음 5가지 조건이 모두 충족될 때 자동으로 활성화됩니다. 이 조건들을 이해하면 의도치 않은 Fast Mode 활성화를 예방할 수 있습니다.

### 조건 1: Opus 4.6 모델 사용

```
claude-opus-4-6 모델로 세션이 실행 중이어야 함
다른 모델(Sonnet, Haiku, 구버전 Opus)에서는 Fast Mode 없음
```

### 조건 2: Fast Mode 설정이 활성화됨

```
settings.json의 fastMode 값이 true (또는 미설정 기본값)
DISABLE_FAST_MODE 환경 변수가 설정되지 않음
```

### 조건 3: 응답 속도 임계값 초과

```
현재 요청의 예상 응답 지연이 임계값 이상
(대화가 길어져 응답이 느려진 상태)
Fast Mode로 전환하여 응답 속도를 개선
```

### 조건 4: 비용 임계값 미초과

```
현재 세션의 누적 비용이 특정 임계값 이하
(이미 많은 비용이 소비된 경우 Fast Mode 차단)
```

### 조건 5: 콘텐츠 유형 적합성

```
요청 유형이 Fast Mode에 적합한 경우
(코드 생성, 텍스트 요약 등 고속 처리 가능한 작업)
```

---

## 4. Cooldown 메커니즘

Fast Mode는 무한정 유지되지 않고 Cooldown 메커니즘으로 자동 해제됩니다.

### Cooldown 동작

```
Fast Mode 활성화 후:
  1. 일정 토큰 수 또는 시간 경과
  2. Cooldown 기간 진입
  3. Cooldown 중: Fast Mode 비활성화
  4. Cooldown 종료 후: 조건 재평가하여 재활성화 가능

Cooldown 목적:
  - 장시간 Fast Mode 고착 방지
  - 비용 폭발 방어
  - 사용자에게 상태 변화 알림
```

### 실제 동작 패턴

```
세션 시작 → 일반 모드 →
[조건 5개 충족] → Fast Mode 활성화 →
[Cooldown 트리거] → 일반 모드 복귀 →
[조건 재충족] → Fast Mode 재활성화 → ...

문제: 이 사이클이 반복되면 비용이 예측 불가능하게 증가
해결: DISABLE_FAST_MODE=1 로 사이클 자체를 차단
```

---

## 5. Fast Mode 비활성화 방법 3가지

### 방법 1: 환경 변수 (가장 강력, 권장)

`CLAUDE_CODE_DISABLE_FAST_MODE=1` 설정은 모든 경로로 활성화되는 Fast Mode를 차단합니다. settings.json 설정보다 우선하며, 실수로 재활성화될 가능성이 없습니다.

```bash
# 현재 셸 세션에 즉시 적용
export CLAUDE_CODE_DISABLE_FAST_MODE=1

# 영구 적용 (bashrc/zshrc)
echo 'export CLAUDE_CODE_DISABLE_FAST_MODE=1' >> ~/.bashrc
source ~/.bashrc

# 단일 명령 실행 시
CLAUDE_CODE_DISABLE_FAST_MODE=1 claude "작업 실행"
```

환경 변수 방법이 가장 강력한 이유:
- settings.json 설정보다 높은 우선순위
- Claude Code 프로세스 전체에 적용
- 실수로 덮어쓰기 불가
- 자동화 스크립트에서 확실한 보장

### 방법 2: settings.json fastMode:false

프로젝트별 또는 글로벌 설정 파일에 명시합니다.

```json
// ~/.claude/settings.json (글로벌)
{
  "fastMode": false,
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1"
  }
}
```

```json
// 프로젝트/.claude/settings.json (프로젝트 전용)
{
  "fastMode": false
}
```

주의 사항:
- 환경 변수보다 낮은 우선순위
- settings 파일 수정으로 실수 가능성 있음
- 프로젝트별 적용이 필요할 때 유용

### 방법 3: Managed Settings

관리자 레벨 설정으로 조직 전체에 적용합니다.

```json
// Managed settings (최하위 우선순위, 기관/팀 정책)
{
  "fastMode": false
}
```

Managed Settings 특징:
- 팀/조직 전체에 일괄 적용
- 개별 사용자 설정으로 덮어쓰기 가능 (우선순위 최하위)
- 정책 기반 강제 비활성화에는 부적합

### 비활성화 방법 비교

| 방법 | 강도 | 범위 | 우선순위 | 권장도 |
|------|------|------|---------|--------|
| 환경 변수 DISABLE_FAST_MODE=1 | 최강 | 현재 프로세스 전체 | 최상 | 강력 권장 |
| settings.json fastMode:false | 강함 | 설정 범위 | 중간 | 환경 변수와 병용 |
| Managed settings fastMode:false | 약함 | 조직 전체 | 최하 | 보조 수단 |

**권장: 환경 변수 + settings.json 병용**

---

## 6. 왜 Fast Mode를 비활성화해야 하는가

### 이유 1: 비용이 6배

```
Opus 4.6 일반 vs Fast 비교:
  일반: Input $5/1M,  Output $25/1M
  Fast: Input $30/1M, Output $150/1M

동일한 작업에 6배의 비용 지불
품질 향상은 전혀 없음
```

### 이유 2: 품질은 완전히 동일

Fast Mode는 단순히 응답 속도를 높이는 것이지 추론 품질을 높이지 않습니다.

```
Fast Mode ON 상태:
  - 응답 생성 속도: 빠름
  - 추론 품질: 일반 모드와 동일
  - 정확성: 일반 모드와 동일
  - 코드 품질: 일반 모드와 동일

결론: 품질 차이 없이 비용만 6배
```

### 이유 3: 사용량 한도를 급속히 소진

```
five_hour 한도 소진 속도 비교:
  Sonnet 4.6: 기준 속도
  Opus 4.6 일반: Sonnet 대비 약 1.67배 빠름
  Opus 4.6 Fast: Sonnet 대비 약 10배 빠름

실제 영향:
  Sonnet으로 5시간 작업 가능한 분량 →
  Opus Fast로는 약 30분에 한도 소진
```

### 이유 4: 예측 불가능한 자동 활성화

```
문제점:
  사용자가 인지하지 못한 상태에서 자동 전환
  세션 중간에 갑자기 비용 6배로 변경
  조건이 충족되면 언제든지 활성화

해결:
  DISABLE_FAST_MODE=1 설정으로 이 불확실성 제거
```

### 이유 5: 자동화 세션에서 치명적

```
NightOps/자동화 스크립트에서 Fast Mode 활성화 시:
  - 감시자 없이 고비용으로 장시간 실행
  - 월 사용량 한도 단시간에 소진
  - 예상치 못한 추가 과금 (overage) 발생

필수 설정:
  export CLAUDE_CODE_DISABLE_FAST_MODE=1
```

---

## 7. 권장 설정: 환경 변수 + settings.json 병용

두 방법을 함께 사용하면 최강의 Fast Mode 차단이 가능합니다.

### 글로벌 설정 (모든 세션에 적용)

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export CLAUDE_CODE_DISABLE_FAST_MODE=1
```

```json
// ~/.claude/settings.json
{
  "fastMode": false,
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000"
  }
}
```

### 자동화 스크립트 템플릿

```bash
#!/bin/bash
# NightOps/자동화 스크립트 헤더

# Fast Mode 차단 (필수)
export CLAUDE_CODE_DISABLE_FAST_MODE=1

# 서브에이전트 비용 최적화
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet

# 비대화형 세션 안정화
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1

# 컨텍스트 비용 절감
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000

# Claude Code 실행
claude --model opus --print "$TASK_PROMPT"
```

### 확인 방법

Fast Mode가 실제로 비활성화되었는지 확인합니다.

```bash
# 환경 변수 확인
echo $CLAUDE_CODE_DISABLE_FAST_MODE
# 출력: 1 (설정된 경우)

# settings.json 확인
cat ~/.claude/settings.json | grep -A2 fastMode
# 출력: "fastMode": false

# 실제 세션에서 확인
# Claude Code UI 상단에 "Fast Mode: OFF" 표시 없음
# 또는 /status 명령으로 확인
```

---

## 8. Fast Mode 상태 확인

### 세션 내 확인

```bash
# 세션 시작 후 상태 확인
/status

# Fast Mode 관련 정보:
# Model: claude-opus-4-6-20251201
# Fast Mode: disabled (DISABLE_FAST_MODE=1)
```

### 비용 급증 감지

Fast Mode가 의도치 않게 활성화되었다면 `/cost` 명령의 비용이 예상보다 훨씬 높게 나타납니다.

```bash
# 비용 확인
/cost

# 예상보다 10배 이상 높다면 Fast Mode 활성화 의심
# 즉시 세션 종료 후 DISABLE_FAST_MODE=1 설정 추가
```

---

## 체크리스트: Fast Mode 비활성화 완료 확인

- [ ] `~/.bashrc`에 `export CLAUDE_CODE_DISABLE_FAST_MODE=1` 추가
- [ ] `~/.claude/settings.json`에 `"fastMode": false` 추가
- [ ] `~/.claude/settings.json` env 섹션에 `"CLAUDE_CODE_DISABLE_FAST_MODE": "1"` 추가
- [ ] 자동화 스크립트에 `export CLAUDE_CODE_DISABLE_FAST_MODE=1` 포함
- [ ] 새 터미널 열어 환경 변수 적용 확인: `echo $CLAUDE_CODE_DISABLE_FAST_MODE`

---

## 다음 단계

1. [환경 변수 레퍼런스](17-environment-variables.md)
2. [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
3. [사용량 한도 및 Rate Limit](16-usage-limits-ratelimit.md)
4. [초기 셋업 체크리스트](00-setup-checklist.md)
