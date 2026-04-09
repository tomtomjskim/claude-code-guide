# Codex 플러그인 가이드

> OpenAI Codex CLI를 Claude Code 내에서 통합 사용하는 플러그인. 코드 리뷰, 디버깅 위임, 구현 태스크 핸드오프 지원.

---

## 개요

| 항목 | 내용 |
|------|------|
| **플러그인 이름** | codex |
| **개발자** | OpenAI |
| **마켓플레이스** | [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) |
| **Codex CLI** | [openai/codex](https://github.com/openai/codex) |
| **버전** | 1.0.3 (플러그인) / 0.118.0 (CLI) |
| **요구사항** | Node.js 18+, Codex CLI, OpenAI 인증 |

### 핵심 용도

- **코드 리뷰**: 로컬 git 변경사항에 대한 Codex 리뷰 실행
- **Adversarial 리뷰**: 설계 선택과 트레이드오프를 도전적으로 검증
- **Rescue (디버깅 위임)**: Claude가 막혔을 때 Codex에게 조사/구현 핸드오프
- **Review Gate**: 세션 종료 시 자동 리뷰 게이트

---

## 설치

### 1단계: 마켓플레이스 등록

```bash
/plugin marketplace add openai/codex-plugin-cc
```

### 2단계: 플러그인 설치

```bash
/plugin install codex@openai-codex
```

### 3단계: 플러그인 로드

```bash
/reload-plugins
```

### 4단계: 셋업 확인

```bash
/codex:setup
```

출력 예시:
```
| 항목       | 상태                              |
|-----------|----------------------------------|
| Node.js   | v22.17.1                         |
| npm       | 10.9.2                           |
| Codex CLI | v0.118.0 (advanced runtime)      |
| 인증       | js525er@gmail.com (ChatGPT 로그인) |
```

### 5단계: Codex CLI 인증 (미인증 시)

```bash
# 브라우저 로그인 (기본)
!codex login

# 디바이스 인증 (브라우저 불가 시)
!codex login --device-auth

# API 키 인증
!codex login --with-api-key
```

### 6단계: Review Gate 활성화 (선택)

```bash
/codex:setup --enable-review-gate
```

> Review Gate: 세션 종료(`Stop`) 시 Codex가 자동으로 이전 작업을 리뷰하는 게이트. 비활성화는 `--disable-review-gate`.

---

## 슬래시 커맨드 (7개)

| 커맨드 | 설명 | 주요 옵션 |
|--------|------|----------|
| `/codex:setup` | 셋업 확인 및 Review Gate 토글 | `--enable-review-gate`, `--disable-review-gate` |
| `/codex:review` | Codex 코드 리뷰 실행 | `--wait`, `--background`, `--base <ref>`, `--scope <auto\|working-tree\|branch>` |
| `/codex:adversarial-review` | 도전적 설계/구현 리뷰 | 위와 동일 + `[focus text]` |
| `/codex:rescue` | Codex에게 디버깅/구현 위임 | `--background`, `--wait`, `--resume`, `--fresh`, `--model <model>`, `--effort <level>` |
| `/codex:status` | 활성/최근 Codex 작업 상태 확인 | `[job-id]`, `--wait`, `--all` |
| `/codex:result` | 완료된 Codex 작업 결과 조회 | `[job-id]` |
| `/codex:cancel` | 백그라운드 Codex 작업 취소 | `[job-id]` |

---

## 사용법 상세

### `/codex:review` — 코드 리뷰

로컬 git 상태(staged + unstaged + untracked)를 Codex가 리뷰합니다.

```bash
# 기본 (워킹 트리 리뷰, 크기에 따라 fore/background 선택)
/codex:review

# 포그라운드 실행 (결과 대기)
/codex:review --wait

# 백그라운드 실행
/codex:review --background

# 특정 브랜치 기준 리뷰
/codex:review --base main

# 브랜치 전체 변경사항 리뷰
/codex:review --scope branch
```

**동작 흐름:**
1. 리뷰 대상 크기 추정 (`git status`, `git diff --shortstat`)
2. 1-2개 파일 → Wait 권장, 그 외 → Background 권장
3. 리뷰 결과 출력 (severity 순 정렬)
4. 결과 확인 후 **수정은 사용자가 지시해야 함** (자동 수정 금지)

---

### `/codex:adversarial-review` — 도전적 리뷰

일반 리뷰와 달리 **설계 선택, 가정, 트레이드오프**를 도전적으로 질문합니다.

```bash
# 기본 adversarial 리뷰
/codex:adversarial-review

# 특정 영역 포커스
/codex:adversarial-review 인증 로직의 세션 관리 전략이 적절한지

# 브랜치 기준 + 포커스
/codex:adversarial-review --base main 성능 병목 가능성 검토
```

---

### `/codex:rescue` — 디버깅/구현 위임

Claude가 막혔거나 second opinion이 필요할 때 Codex에게 작업을 위임합니다.

```bash
# 기본 (포그라운드, 쓰기 가능)
/codex:rescue 이 버그의 근본 원인을 찾아서 수정해줘

# 백그라운드 실행
/codex:rescue --background 전체 테스트 실패 원인 조사

# 이전 Codex 작업 이어서 진행
/codex:rescue --resume 위 수정에서 누락된 엣지 케이스 처리

# 새 스레드로 시작
/codex:rescue --fresh 다른 접근법으로 재구현

# 모델 지정
/codex:rescue --model spark 빠르게 진단만 해줘

# 추론 노력 수준 지정
/codex:rescue --effort high 복잡한 동시성 버그 분석
```

**옵션 상세:**

| 옵션 | 값 | 설명 |
|------|-----|------|
| `--background` | - | 백그라운드 실행 |
| `--wait` | - | 포그라운드 실행 (기본) |
| `--resume` | - | 이전 Codex 스레드 이어서 |
| `--fresh` | - | 새 스레드로 시작 |
| `--model` | `spark`, `gpt-5.4-mini` 등 | 사용할 모델 지정 |
| `--effort` | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` | 추론 노력 수준 |

**사용 시나리오:**
- Claude가 반복 시도 후 해결 못 할 때
- 독립적 second opinion이 필요할 때
- 대규모 코드베이스 조사가 필요할 때
- 복잡한 근본 원인 분석이 필요할 때

---

### `/codex:status` — 작업 상태 확인

```bash
# 현재 세션의 모든 작업 상태
/codex:status

# 특정 작업 상세
/codex:status <job-id>

# 모든 작업 (과거 포함)
/codex:status --all
```

---

### `/codex:result` — 작업 결과 조회

```bash
# 최근 완료된 작업 결과
/codex:result

# 특정 작업 결과
/codex:result <job-id>
```

출력 포함 항목: Job ID, 상태, verdict, summary, findings, details, artifacts, next steps

---

### `/codex:cancel` — 작업 취소

```bash
/codex:cancel <job-id>
```

---

## 내부 구조

### 스킬 (3개, 내부용)

| 스킬 | 설명 |
|------|------|
| `codex-cli-runtime` | Codex companion 런타임 호출 계약 |
| `codex-result-handling` | Codex 출력 결과 표시 규칙 |
| `gpt-5-4-prompting` | Codex/GPT-5.4 프롬프트 작성 가이드 |

### 에이전트 (1개)

| 에이전트 | 모델 | 설명 |
|---------|------|------|
| `codex-rescue` | sonnet | Codex task 런타임에 대한 thin forwarding wrapper |

### 훅 (3개)

| 이벤트 | 동작 |
|--------|------|
| `SessionStart` | 세션 라이프사이클 시작 기록 |
| `SessionEnd` | 세션 라이프사이클 종료 기록 |
| `Stop` | Review Gate 활성화 시 자동 리뷰 실행 (timeout: 900초) |

---

## Review Gate

### 개념

세션 종료(`Stop` 이벤트) 시 Codex가 이전 Claude 작업을 자동으로 리뷰하는 안전장치입니다.

### 설정

```bash
# 활성화
/codex:setup --enable-review-gate

# 비활성화
/codex:setup --disable-review-gate
```

### 동작 흐름

```
Claude 작업 완료 → 사용자 Stop → Stop Hook 발동
→ Codex가 직전 작업 리뷰 → 리뷰 결과 표시
→ 문제 발견 시 사용자에게 알림
```

---

## 일반적인 워크플로우

### 1. 구현 후 리뷰

```
1. Claude로 기능 구현
2. /codex:review --wait          # 구현 결과 리뷰
3. 리뷰 결과 확인 → 필요시 수정 지시
4. /codex:adversarial-review     # 설계 검증 (선택)
```

### 2. 디버깅 위임

```
1. Claude가 버그 조사 중 막힘
2. /codex:rescue 이 에러의 근본 원인 찾아줘
3. Codex 결과 확인
4. /codex:rescue --resume 위 분석 기반으로 수정해줘
```

### 3. PR 전 최종 리뷰

```
1. 구현 완료 + 테스트 통과
2. /codex:review --scope branch --base main
3. /codex:adversarial-review --base main 보안/성능 관점
4. 리뷰 통과 → PR 생성
```

### 4. Review Gate 자동 리뷰

```
1. /codex:setup --enable-review-gate
2. Claude로 작업 진행
3. 작업 완료 시 Stop → Codex 자동 리뷰 실행
4. 리뷰 결과에 문제 있으면 작업 재개
```

---

## Superpowers 플러그인과의 관계

| 기능 | Superpowers | Codex | 병행 전략 |
|------|------------|-------|----------|
| 코드 리뷰 | `requesting-code-review` | `/codex:review` | Superpowers로 구조 리뷰 + Codex로 구현 리뷰 |
| 디버깅 | `systematic-debugging` | `/codex:rescue` | Superpowers로 4단계 분석 → 막히면 Codex 위임 |
| TDD | `test-driven-development` | - | Superpowers 전담 |
| 설계 검증 | `brainstorming` | `/codex:adversarial-review` | 설계 후 Codex로 도전적 검증 |
| 브랜치 완료 | `finishing-a-development-branch` | Review Gate | 브랜치 완료 전 Codex Review Gate로 최종 검수 |

---

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `Codex is unavailable` | `npm install -g @openai/codex` |
| `requires OpenAI authentication` | `!codex login` 실행 |
| `browser login blocked` | `!codex login --device-auth` 또는 `--with-api-key` |
| 백그라운드 작업 상태 모름 | `/codex:status` |
| 백그라운드 작업 취소하고 싶음 | `/codex:cancel <job-id>` |
| 이전 Codex 작업 이어가고 싶음 | `/codex:rescue --resume ...` |
| Review Gate 비활성화 | `/codex:setup --disable-review-gate` |

---

## 다음 단계

- [추천 플러그인 가이드](09-recommended-plugins.md)
- [셋업 체크리스트](00-setup-checklist.md)
- [코드 리뷰 시스템](10-code-review-system.md)
