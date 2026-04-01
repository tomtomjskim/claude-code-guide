# Memory 시스템 내부 동작

## 개요

Claude Code의 Memory 시스템은 세션 간 지식을 지속적으로 축적하고, 현재 작업과 관련된 정보를 자동으로 주입하는 장기 기억 메커니즘입니다. 단순한 파일 로딩이 아닌, Sonnet 기반 관련도 순위 결정과 frontmatter 메타데이터 최적화를 통해 제한된 컨텍스트 공간을 효율적으로 활용합니다.

---

## 1. 저장 한도 및 파일 구조

### 1.1 용량 제한

| 항목 | 한도 | 초과 시 동작 |
|------|------|------------|
| MEMORY.md 파일 크기 | 200줄 / 25KB | 오래된 항목 자동 압축 또는 경고 |
| 개별 메모리 파일 크기 | 40,000자 (약 40KB) | 쓰기 거부 또는 자동 분할 |
| 턴당 주입 파일 수 | 최대 5개 | 관련도 상위 5개만 주입 |

### 1.2 MEMORY.md 구조

`~/.claude/projects/<project-hash>/memory/MEMORY.md` 또는 프로젝트 루트 `.claude/MEMORY.md`에 위치합니다.

```markdown
# Memory

## Reference
- [파일명](상대경로.md) — 한 줄 설명

## Project
- [항목명](파일경로.md) — 설명

## Feedback
- [피드백명](파일경로.md) — 설명

## User
- [개인설정명](파일경로.md) — 설명

## Patterns
- `패턴명` — 설명
```

MEMORY.md는 **인덱스 파일**입니다. 실제 내용은 링크된 개별 파일에 저장되며, MEMORY.md에는 각 파일의 이름과 한 줄 설명만 기록합니다.

---

## 2. 관련도 순위 결정 메커니즘

### 2.1 Sonnet 기반 side query

매 턴 시작 시 Claude Code는 현재 사용자 요청을 별도의 경량 Sonnet 쿼리로 분석합니다.

```
[side query 흐름]

사용자 입력 → Sonnet에 전달 (전체 대화 없이 요청만)
                    ↓
          "이 요청과 관련된 메모리 파일 순위를 매겨라"
                    ↓
          MEMORY.md 인덱스 + 각 파일의 frontmatter 분석
                    ↓
          관련도 점수 계산 (0-1.0)
                    ↓
          상위 5개 파일 선택 → 메인 컨텍스트에 주입
```

이 side query는 별도의 API 호출이므로 비용이 발생합니다. `memory.enabled: false` 설정으로 비활성화할 수 있습니다.

### 2.2 frontmatter 기반 매칭

관련도 순위는 각 메모리 파일의 YAML frontmatter를 주요 신호로 활용합니다.

```yaml
---
name: "Sports Analysis Tom's Pick Strategy"
description: "K리그 분석 시 상대전적+폼 가중치 적용, 해외 리그 득실력 비교 전략"
type: "feedback"
tags: ["sports", "k-league", "strategy", "prediction"]
updated: "2026-03-15"
priority: high
---
```

| frontmatter 필드 | 역할 |
|-----------------|------|
| `name` | 파일의 공식 이름, 검색 쿼리와 직접 매칭 |
| `description` | 내용 요약, 관련도 계산의 핵심 신호 |
| `type` | 분류 필터링 (섹션 4.1 참조) |
| `tags` | 키워드 기반 빠른 매칭 |
| `updated` | 최신성 가중치 (최근 업데이트일수록 우선) |
| `priority` | `high` / `medium` / `low` — 관련도 동점 시 tiebreaker |

---

## 3. 주입 우선순위 및 컨텍스트 배치

### 3.1 메모리 파일 주입 순서

관련도 순위가 결정되면 다음 순서로 컨텍스트에 배치됩니다.

```
[컨텍스트 최상단]
  1. CLAUDE.md (글로벌)
  2. CLAUDE.md (프로젝트)
  3. MEMORY.md 인덱스 (요약만)
  4. 선택된 메모리 파일 1 (가장 관련 높음)
  5. 선택된 메모리 파일 2
  6. 선택된 메모리 파일 3
  7. 선택된 메모리 파일 4
  8. 선택된 메모리 파일 5
  9. Skills (최대 5개)
[컨텍스트 나머지]
  10. 대화 히스토리
  11. 현재 사용자 요청
```

### 3.2 주입 거부 조건

다음 조건에서는 해당 파일이 주입 목록에서 제외됩니다.

- 파일 크기가 40,000자를 초과하는 경우
- frontmatter의 관련도 점수가 임계값(약 0.3) 미만인 경우
- `claudeMdExcludes` 패턴과 일치하는 경로인 경우

---

## 4. 메모리 타입 가이드

올바른 `type` 분류는 관련도 매칭 정확도를 높입니다.

### 4.1 타입별 용도

| 타입 | 용도 | 예시 |
|------|------|------|
| `reference` | 기술 문서, 소스 분석, API 레퍼런스 | Claude Code 소스맵, DB 스키마 |
| `project` | 프로젝트 진행 상태, 아키텍처, 로드맵 | NightOps 현황, 미완료 태스크 |
| `feedback` | 사용자 선호, 금지 패턴, 스타일 규칙 | 카드 좌측 컬러바 금지, AI 패턴 금지 |
| `user` | 개인 설정, 세션 규칙 | Session Summary 규칙, 개인 워크플로우 |

### 4.2 타입별 주입 빈도

| 타입 | 일반적 주입 빈도 | 이유 |
|------|----------------|------|
| `feedback` | 매우 높음 | 모든 코드 작업에 스타일 규칙 필요 |
| `project` | 높음 | 현재 작업 컨텍스트 유지 |
| `user` | 중간 | 세션 관리 규칙 등 |
| `reference` | 낮음 | 특정 기술 작업 시에만 관련 |

---

## 5. frontmatter 최적화 실전 예시

### 5.1 잘못된 frontmatter (관련도 낮음)

```yaml
---
name: "note1"
description: "some notes"
type: "misc"
---
```

문제점: `name`과 `description`이 너무 일반적이어서 어떤 요청과도 높은 관련도를 가지지 못합니다.

### 5.2 최적화된 frontmatter

```yaml
---
name: "Sports Analysis Improvement Plan 2026-04"
description: "축구/야구/농구 스포츠 분석 서비스 3-Phase 개선 계획. 핸디캡/언오버 예측, Calibration Phase E, Tom's Pick 전략 고도화 포함"
type: "project"
tags: ["sports", "sports-analysis", "improvement", "roadmap", "prediction", "handicap"]
updated: "2026-04-01"
priority: high
---
```

개선 효과:
- `description`에 핵심 기술 용어 명시 → 관련 요청 시 높은 매칭
- `tags` 배열로 다양한 쿼리 키워드 커버
- `priority: high`로 동점 시 우선 선택

---

## 6. 저장하지 말아야 할 내용

메모리 시스템은 지속성을 위한 것이므로 다음 내용은 저장하면 안 됩니다.

### 6.1 저장 금지 항목

| 항목 | 이유 |
|------|------|
| API 키, 비밀번호, 토큰 | 보안 위험 — git 커밋 시 노출 가능 |
| 이메일 주소, 전화번호 | 개인정보 — 불필요한 노출 |
| 일회성 디버깅 로그 | 관련도 노이즈 증가, 공간 낭비 |
| 임시 파일 경로 | 환경 의존적, 다른 환경에서 유효하지 않음 |
| 대용량 코드 스니펫 | 40K 한도 소진, 관련 파일을 직접 Read하는 것이 효율적 |
| 동적 데이터 (가격, 통계 등) | 금방 outdated 됨 |

### 6.2 저장 권장 항목

- 사용자 선호사항 (UI 패턴, 코드 스타일)
- 반복적으로 등장하는 아키텍처 패턴
- 프로젝트 현재 상태와 미완료 작업
- 중요한 설계 결정과 그 이유 (ADR)
- 자주 실수하는 패턴과 수정 방법

---

## 7. 메모리 관리 실전 팁

### 7.1 MEMORY.md 용량 관리

200줄 한도에 가까워지면 다음 방법으로 정리합니다.

```bash
# 현재 MEMORY.md 줄 수 확인
wc -l ~/.claude/projects/*/memory/MEMORY.md

# 오래된 항목 아카이브
# 6개월 이상 참조되지 않은 항목을 archive/ 하위 디렉토리로 이동
```

### 7.2 개별 파일 크기 관리

```bash
# 모든 메모리 파일 크기 확인
find ~/.claude/projects/ -name "*.md" -path "*/memory/*" | \
  xargs wc -c | sort -rn | head -20
```

40K 한도에 근접한 파일은 내용을 핵심만 남기고 축약하거나, 여러 파일로 분리합니다.

### 7.3 자동 메모리 저장 제어

Claude Code는 중요하다고 판단한 내용을 자동으로 메모리에 저장합니다. 저장 전 확인이 필요하다면:

```json
{
  "autoMemoryEnabled": false
}
```

`false` 설정 시 Claude가 메모리 저장을 제안하지만 자동으로 저장하지는 않습니다.

---

## 8. 압축 후 메모리 동작

auto-compact 발생 시 메모리 파일은 압축되지 않습니다. 압축 후 재주입 시 동일한 관련도 순위 결정 과정이 다시 수행되어 상위 5개 파일이 새 컨텍스트에 주입됩니다. 즉, **메모리는 컨텍스트 압축에 영향을 받지 않으며** 세션 내내 안정적으로 접근 가능합니다.

---

## 다음 단계

- [컨텍스트 윈도우 내부 동작](18-context-window-internals.md)
- [Settings 전체 스키마 레퍼런스](19-settings-schema-reference.md)
- [Agent Frontmatter 완전 스키마](21-agent-frontmatter-schema.md)
