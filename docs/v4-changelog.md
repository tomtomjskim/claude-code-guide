# Multi-Agent Team System v4.0 Changelog

**Release Date**: 2026-04-23
**Upgraded From**: v3.2 (canonical 유지 — v4는 *구조 재정렬 릴리스*로 버전 숫자 bump 없음)
**Strategy Doc**: [`docs/v4/strategy.md`](v4/strategy.md)
**Plans**: [`docs/v4/plans/`](v4/plans/)

---

## Summary

v4.0은 **coherence 부채 청산 릴리스**이다. v3.0 → v3.2 → v3.3 누적 기능 추가로 버전 숫자·에이전트 이름·스킬 프리셋·hooks 네이밍·validate 커버리지가 여러 층에서 서로 다른 세대를 동시 주장하던 상태 — 즉 **레포가 자기 자신의 SSOT 원칙을 어기던 상태**를 종료한다.

**v4.0 이후 강제되는 규약:**
- **버전 bump = 1곳 수정** (`agents.yaml:4` + validate의 `EXPECTED_VERSION`)
- **에이전트 추가 = `agents.yaml` 한 곳 수정** (validate가 자동 동기 검증)
- **프리셋 체계 변경 = `CLAUDE.md` + `docs/14-preset-system.md` 2곳만 수정** (6 SKILL.md는 canonical 링크)
- **복잡도 임계값 변경 = `.claude/rules/subagent-strategy.md` 1곳 수정** (dispatch + docs/33은 canonical mirror/링크)

**범위 밖 (의도적 out-of-scope):**
- 신규 기능 추가 없음
- 새 에이전트 / 새 스킬 / 새 hook 추가 없음
- 버전 숫자 bump 없음 (3.2 canonical 유지)

---

## Breaking Changes

### B1. `prompts/qa.md` → `prompts/qa-engineer.md` (P0-5, 커밋 2de8492)

- **영향**: 다른 15개 에이전트가 `agents/X.md ↔ prompts/X.md` 파일명 일치 규약을 따르는데 `qa`만 단축명이었음. 규약 복원
- **migration**:
  - Scenario A (CUSTOMIZE 미수정): `bash scripts/install-skills.sh --team --force` 재설치로 자동 반영
  - Scenario B (`prompts/qa.md` 직접 수정한 사용자): `prompts/qa-engineer.md` 신규 파일에 커스텀 내용 수동 이식

### B2. `hooks/scripts/*.sh` → `*.reference.sh` (P1-5, 커밋 0505d08)

- **영향**: `hooks/boilerplates/`와 `hooks/scripts/`에 동일 파일명(`safety-careful.sh` 등)이 공존하여 역할 구별 불가 → `.reference.sh` 접미어로 자기설명
- **rename 대상 3건**:
  - `safety-careful.sh` → `safety-careful.reference.sh`
  - `safety-freeze.sh` → `safety-freeze.reference.sh`
  - `event-review-trigger.sh` → `event-review-trigger.reference.sh`
- **migration**:
  - Scenario A: `install-skills.sh --team --force` 재설치로 자동 반영. 기본 `settings.local.json` 예시 따른 사용자는 `.reference.sh` 경로로 수정 필요
  - Scenario B: `.claude/settings.local.json`이 `~/.claude/team/hooks/scripts/safety-careful.sh` 등을 직접 참조하는 경우 **수동 병합 필요** — `.reference.sh`로 경로 업데이트
  - 구 파일 잔존 시 `rm "$HOME/.claude/team/hooks/scripts/{safety-careful,safety-freeze,event-review-trigger}.sh"`로 수동 정리 (참조되지 않으므로 방치해도 무해)

### B3. `validate-system.sh` 에이전트 이름 하드코딩 → `agents.yaml` 동적 파싱 (P0-4, 커밋 2de8492)

- **영향**: validate 스크립트 내부 7곳의 하드코딩된 에이전트 이름이 `agents.yaml` 파싱으로 전환. 외부 의존성 없음 (`yq` 대신 bash `awk`+`grep` 사용, Decision 3)
- **migration**: 재설치로 자동 반영. 사용자 조치 불필요

---

## Delivered Backlog

### P0 — v4.0 릴리스 블로커 (5건, all close)

| # | 항목 | 커밋 |
|---|------|------|
| **P0-1** | `agents/pm.md` 생성 — PM 에이전트 파일 시스템 불일치 해소 | [2de8492](../commit/2de8492) |
| **P0-2** | `validate-system.sh` 자기 모순 제거 (`## v3.0 Template` → `## Template`) | [2de8492](../commit/2de8492) |
| **P0-3** | `.claude/hooks/` byte-identical 복제본 제거 + 자기 가드 활성화 | [31b0a17](../commit/31b0a17) |
| **P0-4** | `validate-system.sh` 에이전트 이름 하드코딩 → `agents.yaml` 동적 파싱 (B3) | [2de8492](../commit/2de8492) |
| **P0-5** | `prompts/qa.md` → `prompts/qa-engineer.md` rename (B1) | [2de8492](../commit/2de8492) |

### P1 — v4.0 필수 (9건, all close)

| # | 항목 | 커밋 |
|---|------|------|
| **P1-1** | 버전 숫자 canonical 통일 (`EXPECTED_VERSION` 중앙화) | [40d6b31](../commit/40d6b31) |
| **P1-2** | 프리셋 정의 6-스킬 중복 제거 (canonical 2-tier + marker) | [cc129ad](../commit/cc129ad) |
| **P1-3** | 에이전트 목록 canonical 통일 | P0-A에 선행 흡수 ([2de8492](../commit/2de8492)) |
| **P1-4** | 스킬 목록 canonical 통일 (`design-creative` 누락 보강 + 17→18) | [d25c0e8](../commit/d25c0e8) |
| **P1-5** | `hooks/scripts/*.sh` → `*.reference.sh` rename (B2) | [0505d08](../commit/0505d08) |
| **P1-6** | Complexity Tier 임계값 canonical 통일 | [d417e14](../commit/d417e14) |
| **P1-7** | `test` / `qa-test` description 재작성 | [cc129ad](../commit/cc129ad) |
| **P1-8** | `analyze` / `spec` / `check-spec` description 재작성 (PDARR 축 명시) | [cc129ad](../commit/cc129ad) |
| **P1-9** | `reflect` / `complete` / `organize-docs` description 재작성 | [dd19fb8](../commit/dd19fb8) |

### P2 — v4.0 nice-to-have (10건, 본 릴리스에서 2건 부분 해소, 나머지 open)

- **P2-5 부분 해소**: P1-5에서 `CLAUDE.md` "Hooks directory has TWO meanings" 제목을 "layout"으로 완화 + `.reference.sh` 접미어로 파일명 자기설명 → P2-5 원 요구(3중 네이밍 해소)의 주요 부분 달성
- **나머지 8건**: 후속 릴리스 또는 필요시 선별 처리 ([docs/v4/plans/p2-survey.md](v4/plans/p2-survey.md) 참조)

---

## Key Structural Changes

### Canonical SSOT 재정렬

| Canonical 위치 | 대상 | 과거 중복/drift 위치 수 | 현재 |
|---------------|------|-------------------------|------|
| `agents.yaml:4` | 시스템 버전 | 15+ 곳 혼재 (3.0/3.2/3.3) | 1곳 (+ `EXPECTED_VERSION` 단일 참조) |
| `agents.yaml:263+` | 에이전트 목록 | README + validate 7곳 하드코딩 | 1곳 (validate가 동적 파싱) |
| `skills/README.md:31-74` | 스킬 목록 (18개) | "17개" drift × 3곳 | 1곳 (canonical) |
| `CLAUDE.md:56 + docs/14` | 프리셋 체계 (2축) | 9곳 중복 선언 (6 SKILL + 3 summary) | 2-tier canonical |
| `.claude/rules/subagent-strategy.md:17-22` | Complexity Tier 임계값 | dispatch + docs/33 독자 주장 | 1곳 (consumers link) |

### Validate 체크 확장

| 신설 체크 | 감지 대상 |
|----------|-----------|
| Check (P0-1 내부) | `agents.yaml` 선언 ↔ `agents/*.md` 파일 매칭 |
| Check 19 (P1-2) | 6 SKILL.md의 `<!-- PRESET_CANONICAL_LINK -->` 마커 + 중복 2축 테이블 잔존 탐지 |
| Check 13 업데이트 (P1-5) | hooks/scripts 신규 `.reference.sh` 파일명으로 검증 |

**총 체크 카테고리**: v3.2 기준 18개 → v4.0 기준 **19개** (v4.0: 1개 신설)

### Non-breaking 개선

- `qa-test`: 기존 4라벨(`--minimal/--basic/--standard/--full`) 보존 + 2축 alias(`--quick/--thorough`) 병행 지원
- `qa-e2e`: depth 축 미적용 본질 명문화 (scenario-driven, `--tc TC-N`으로 범위 제어)
- `design-creative`: skills/README.md 누락 복원 (스킬 자체는 기존 존재, 문서 가시성 복원)

---

## Success Criteria Verification (strategy §5)

- [x] **`validate-system.sh` baseline 유지** — Errors 6은 PyYAML env baseline (v4 이전부터 존재, 우리 변경과 무관). 신규 에러 0건
- [x] **모든 P0 백로그 close** (P0-1~P0-5 전수)
- [x] **버전 주장이 repo 전체에서 단 1곳 선언** (`agents.yaml:4`, 나머지는 링크·동적 참조·제거)
- [x] **CLAUDE.md · README · QUICKSTART · 각 skill 본문이 PDARR 흐름을 canonical 경유 기술** (CLAUDE.md:56 canonical + consumer 링크)
- [x] **hooks 네이밍 3중 → 파일명 자기설명** (`.reference.sh` 접미어, P1-5)
- [x] **`.claude/rules/*` 주장 ↔ 실제 hook 동작 일치** (`.claude/hooks/` 제거로 drift 축 제거, Complexity Tier 통일)

---

## Migration Scenarios

### Scenario A: "v3.3 설치만 한 사용자" (CUSTOMIZE 미수정)

```bash
cd <repo>
git pull origin main
bash scripts/install-skills.sh <target> --team --force
bash scripts/install-hooks.sh <target> --force
bash scripts/validate-system.sh
# 기대: Errors 6 (PyYAML baseline), Warnings 0
```

- B1 (qa.md → qa-engineer.md): 재설치로 자동 반영
- B2 (.reference.sh 접미어): 재설치로 자동 반영. `settings.local.json`이 기본 예시 경로를 따르면 README.md 최신 예시로 경로 수동 수정 필요
- B3 (validate 동적 파싱): 재설치로 자동 반영

### Scenario B: "CUSTOMIZE 수정 사용자"

1. 재설치 전 `diff -r ~/.claude/ <backup>`로 수정 사항 백업
2. `bash scripts/install-skills.sh --force` 실행
3. 충돌 지점 확인 (재설치 후 덮어써진 CUSTOMIZE 블록):
   - `skills/{analyze,spec,check-spec,check-code,qa-test,qa-e2e}/SKILL.md` — 프리셋 본문이 canonical 링크로 교체됨 (P1-2). CUSTOMIZE 블록은 본문 하단에 보존되었으므로 머지 포인트 확인
   - `skills/{analyze,spec,check-spec,test,qa-test,reflect,complete,organize-docs}/SKILL.md` — frontmatter description 재작성 (P1-7/P1-8/P1-9). 사용자 커스텀 description 사용 시 수동 복원
4. `prompts/qa.md` 직접 편집한 경우 → `prompts/qa-engineer.md` 신규 파일에 수정사항 이식
5. `.claude/settings.local.json`에서 `hooks/scripts/safety-careful.sh` 등을 직접 참조하는 경우 → `.reference.sh` 접미어로 수정

---

## Commits (chronological)

```
31b0a17 feat(v4 P0-3): .claude/hooks/ byte-identical 복제본 제거 + 자기 가드 활성화
2de8492 feat(v4 P0-A): P0 Bundle A — pm.md 생성 + qa rename + validate 동적 파싱
40d6b31 feat(v4 P1-1): 버전 canonical 통일 — drift 레이블 제거 + EXPECTED_VERSION 중앙화
cc129ad feat(v4 P1-2+P1-7+P1-8): 프리셋 중복 제거 + 5 스킬 description 재작성
d417e14 feat(v4 P1-6): Complexity Tier 임계값 canonical 통일
dd19fb8 feat(v4 P1-9): reflect/complete/organize-docs description 재작성
d25c0e8 feat(v4 P1-4): 스킬 목록 canonical 통일 — design-creative 누락 보강 + "17→18" drift 정정
0505d08 feat(v4 P1-5): hooks/scripts/*.sh → *.reference.sh rename (Breaking B2)
```

**총 8 커밋** (P0-A bundle + P1-2+P1-7+P1-8 bundle 덕에 14개 전략 항목을 8 커밋에 통폐합)

---

## Statistics

- **수정 파일**: 약 30개 (고유 파일 기준, 커밋 중복 제거)
- **순수 라인 변화**: +3400 / -500 (plan 문서 3개 약 +2500줄 포함)
- **실제 코드/문서 변화**: 약 +900 / -500 (plan 제외, 구조 재정렬 중심)
- **중복 제거**: 프리셋 정의 9곳 → 2곳, 에이전트 이름 하드코딩 7곳 → 0곳, 버전 드리프트 15곳 → 1곳
- **신규 체크**: Check 19 "Preset canonical markers 6/6" 자동 감지 체계
