# Quick Start Guide

이 가이드의 기능을 실전에서 바로 활용하기 위한 실전 가이드.

---

## 0. 스킬 설치

```bash
git clone https://github.com/tomtomjskim/claude-code-guide.git
cd claude-code-guide

# 프로젝트에 워크플로우 스킬 설치
bash scripts/install-skills.sh /path/to/your-project

# (선택) 팀 에이전트까지 포함
bash scripts/install-skills.sh --team /path/to/your-project
```

설치 후 아래 커맨드를 바로 사용할 수 있습니다. 기술 스택에 맞게 커스터마이징하려면 [skills/README.md](skills/README.md)를 참조하세요.

### 0-b. Hook 설치 (안전장치)

```bash
# 전체 Hook 설치 (standard 프리셋 — 권장)
bash scripts/install-hooks.sh /path/to/your-project

# 또는 필수 안전장치만 (minimal 프리셋)
bash scripts/install-hooks.sh --preset minimal /path/to/your-project
```

설치 후 각 파일의 `🔧 커스터마이징 영역`을 프로젝트에 맞게 수정하세요. 상세: [hooks/README.md](hooks/README.md)

---

## 1. 일상 코딩 (변경 없음)

기존과 동일하게 사용. 추가 기능은 기존 워크플로우를 **확장**한 것이지 대체가 아님.

```
/dispatch {작업}          # 평소대로 시작
/run {간단한 수정}         # 평소대로 구현
/check-code {모듈}        # standard 프리셋 (기본)
```

---

## 2. 프리셋 선택 기준

### 2축 체계: 깊이(depth) x 실행(mode)

```
깊이:  --quick ← standard → --thorough
실행:  단일    ← 기본    → --team

--team 단독 사용 = thorough + 팀 (기본 최대 깊이)
--team --quick   = quick + 팀 (조합 가능)
```

### /analyze 프리셋

| 상황 | 프리셋 | 명령어 |
|------|--------|--------|
| 버그 원인 빠른 파악 | `--quick` | `/analyze --quick {버그 현상}` |
| 일반 기능 분석 (기본) | standard | `/analyze {기능}` |
| 복잡 기능, 아키텍처 변경 | `--thorough` | `/analyze --thorough {기능}` |
| 크로스 도메인, 대규모 기능 | `--team` | `/analyze --team {기능}` |

### /spec 프리셋

| 상황 | 프리셋 | 명령어 |
|------|--------|--------|
| 패턴 명확한 간단 기능 | `--quick` | `/spec --quick` |
| 일반 명세서 (기본) | standard | `/spec` |
| 외부 연동, 복잡 기능 | `--thorough` | `/spec --thorough` |
| 대규모 신규 모듈 | `--team` | `/spec --team` |

### /check-spec 프리셋

| 상황 | 프리셋 | 명령어 |
|------|--------|--------|
| 구조만 빠르게 확인 | `--quick` | `/check-spec --quick {모듈}` |
| 일반 설계 검수 (기본) | standard | `/check-spec {모듈}` |
| 요구사항 완전성 심층 | `--thorough` | `/check-spec --thorough {모듈}` |
| Architect+DBA 다관점 검수 | `--team` | `/check-spec --team {모듈}` |

### /check-code 프리셋

| 상황 | 프리셋 | 명령어 |
|------|--------|--------|
| 빠른 문법 체크만 | `--quick` | `/check-code --quick {모듈}` |
| 일반 코드 검수 (기본) | standard | `/check-code {모듈}` |
| 배포 전 종합 검수 | `--thorough` | `/check-code --thorough {모듈}` |
| 보안 감사/대규모 리팩토링 | `--team` | `/check-code --team {모듈}` |

---

## 3. 팀 에이전트 활용 시점

**사용하지 않아도 되는 경우** (대부분):
- 버그 수정, 소규모 기능 추가 → 단일 에이전트 or `/run`
- 분석만 필요 → `/analyze`

**팀 에이전트 추천 상황**:

| 작업 복잡도 | 수정 파일 수 | 추천 |
|------------|------------|------|
| 1~3개 파일 | 단순 수정 | 단일 에이전트 |
| 4~6개 파일 | 중간 수정 | 병렬 Task Agent |
| 7개+ 파일 | 전 레이어 | **팀 에이전트** (Type C~D) |
| 코드 리뷰만 | 리뷰 전용 | **팀 리뷰** (Type E) |

---

## 4. Model Routing 체감 효과

**자동 적용** — 별도 설정 불필요:

- Explorer 초기 탐색 → **haiku** (빠르고 저렴)
- 일반 구현/리뷰 → **sonnet** (기본)
- CRITICAL 보안 이슈, 복잡 아키텍처 → **opus** (정확)

---

## 5. Handoff / Failure Recovery 체감

**자동 적용** — `--team` 또는 `/workflow` 사용 시:

| 기능 | 이전 | 현재 |
|------|------|------|
| 에이전트 간 전달 | 비구조적 텍스트 | 5-field 구조 (scope/findings/recommendation/validation_status/residual_risk) |
| 에이전트 실패 | "재시도/중단?" 매번 질문 | 탐색/리뷰 → 자동 재시도, 구현 → PM 에스컬레이션 |
| 연속 실패 | 계속 시도 | 3회 연속 → 자동 중단 → 사용자 판단 |

---

## 6. 작업 유형별 실전 패턴

### 패턴 A: 일상 개발
```
/run {작업}
/check-code {모듈}
/stage
```

### 패턴 B: 중요 기능 개발
```
/analyze --thorough {기능}
/spec --thorough
/run
/check-code --thorough {모듈}
/stage
```

### 패턴 C: 대규모 기능 (팀 에이전트)
```
/analyze --team {기능}
/spec --team
/workflow {기능}
/check-code --team {모듈}
```

### 패턴 D: 배포 전 보안 감사
```
/check-code --team {모듈}
  → Security Sentinel + Performance Prophet + Code Reviewer + API Arbiter
  → Tiebreaker로 의견 충돌 자동 중재
```

---

## 7. 피해야 할 안티패턴

| 안티패턴 | 이유 | 대안 |
|---------|------|------|
| 버그 수정에 --team | 토큰 3~5배 낭비 | 단일 에이전트 |
| 모든 검수에 --team | 30분 소요, 비용 높음 | standard 사용 |
| --thorough를 매번 사용 | 20분 소요 | 배포 전에만 |
| 수동으로 모델 지정 | Model Routing이 더 효율적 | 자동에 위임 |
| 구현 후에만 검수 | 설계 오류가 전파됨 | **앞단(analyze/spec)에 투자** |

---

## 8. 새 에이전트 추가 시

1. `templates/prompts/TEMPLATE.md` 복사
2. 5-Section 작성 (Opening/Working Mode/Focus On/Quality Checks/Return/Boundary)
3. `templates/agents-v3.yaml`의 agents 섹션에 등록
4. 필요 시 team_templates에 새 조합 추가

---

## 관련 문서

- [Skills 설치/커스터마이징](skills/README.md)
- [Hook 보일러플레이트](hooks/README.md)
- [프리셋 시스템 상세](docs/14-preset-system.md)
- [에이전트 페르소나](docs/05-agent-personas.md)
- [코드 리뷰 시스템](docs/10-code-review-system.md)
- [하네스 엔지니어링](docs/29-harness-engineering.md)
- [v3.0 아키텍처](docs/12-v3-architecture.md)
