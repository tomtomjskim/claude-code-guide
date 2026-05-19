# 스킬 경량화 가이드

## 개요

Claude Code 스킬(`.claude/skills/*.md`)은 호출 시 **전체 내용이 컨텍스트에 주입**됩니다. 비대한 스킬은 매 턴마다 수천 토큰을 소비하며, 다수의 스킬이 로드되면 유효 컨텍스트 윈도우가 급격히 줄어듭니다. 이 가이드는 스킬을 경량화하여 토큰 효율을 극대화하는 전략을 다룹니다.

---

**관련 문서**:
- [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [컨텍스트 윈도우 내부 동작](19-context-window-internals.md)
- [Settings 스키마 레퍼런스](20-settings-schema-reference.md)

---

## 1. 스킬이 토큰을 소비하는 구조

### 1.1 스킬 주입 플로우

```
사용자가 /check-code 호출
  → Claude Code가 skills/check-code/SKILL.md 전체를 읽음
  → 시스템 프롬프트에 스킬 내용 주입 (매 턴마다)
  → references/ 디렉토리 파일도 함께 주입될 수 있음
  → 주입된 토큰은 Input 비용으로 과금
```

### 1.2 스킬 크기별 토큰 소비 추정

1KB ≈ 250~300 토큰 (한국어 기준, 영문은 ~400 토큰)

| 스킬 크기 | 토큰 수 (추정) | Sonnet 턴당 비용 | 10턴 대화 시 |
|-----------|---------------|-----------------|-------------|
| 2KB (경량) | ~600 | $0.0018 | $0.018 |
| 5KB (보통) | ~1,500 | $0.0045 | $0.045 |
| 10KB (비대) | ~3,000 | $0.009 | $0.09 |
| 16KB (과대) | ~4,800 | $0.0144 | $0.144 |

> **핵심**: 16KB 스킬 1개가 10턴 대화에서 $0.14를 소비합니다. 스킬 3~4개가 동시 로드되면 스킬만으로 세션 비용의 30%를 차지할 수 있습니다.

### 1.3 현재 프로젝트 스킬 크기 감사

```
스킬명               크기     줄 수   상태
─────────────────────────────────────────
organize-docs/refs   18.5KB   705줄   ⚠️ 과대 — 분리 필요
qa-e2e              16.0KB   480줄   ⚠️ 과대 — 분리 필요
check-code          15.5KB   534줄   ⚠️ 과대 — 분리 필요
run                 12.5KB   391줄   ⚠️ 비대 — 축소 권장
analyze              9.2KB   246줄   ⚠️ 비대 — 축소 권장
spec                 8.5KB   225줄   주의
profile              8.3KB   222줄   주의
qa-test              8.7KB   298줄   주의
check-spec           7.4KB   248줄   ✅ 양호
dispatch             4.9KB   181줄   ✅ 양호
complete             5.2KB   164줄   ✅ 양호
prd                  ─       194줄   ✅ 양호
```

---

## 2. 경량화 기준 (권장 한도)

### 2.1 크기 기준

| 등급 | SKILL.md 크기 | 토큰 수 | 판정 |
|------|-------------|---------|------|
| 🟢 경량 | ≤ 5KB | ≤ 1,500 | 최적 |
| 🟡 보통 | 5~8KB | 1,500~2,400 | 허용 |
| 🟠 비대 | 8~12KB | 2,400~3,600 | 축소 권장 |
| 🔴 과대 | > 12KB | > 3,600 | 즉시 분리 필요 |

### 2.2 줄 수 기준

```
SKILL.md 본체: ≤ 200줄 (목표), 최대 300줄
references/: 참조 파일 전체 합산 ≤ 500줄
```

### 2.3 핵심 원칙

```
1. SKILL.md = "실행 지시" (무엇을 어떻게 할지)
2. references/ = "참조 데이터" (필요할 때만 읽기)
3. 스킬은 프롬프트이지 문서가 아니다
4. 예제는 1개면 충분하다 (3개 이상은 과잉)
5. 체크리스트는 항목만 나열하고 설명은 생략한다
```

### 2.4 외부 스킬 도입 기준

외부 skill repo의 좋은 패턴은 그대로 복사하지 말고 기존 PDARR 스킬에 먼저
흡수합니다.

| 패턴 | 우선 반영 위치 | 이유 |
|------|----------------|------|
| `diagnose` | `qa-test`, `check-code` | 원인 불명 버그의 재현 루프와 회귀 검증이 QA gate에 맞음 |
| `tracer bullet TDD` | `test` | Red 단계에서 작은 vertical slice를 고정해야 함 |
| `zoom-out` | `analyze` | unfamiliar code의 entry point와 영향 범위를 먼저 좁힘 |
| `prototype` | `spec`, `design-creative` | throwaway 실험은 설계 질문과 폐기/흡수 기준이 필요함 |
| `triage`, `to-issues` | GitHub/plugin workflow | issue write가 있으므로 dry-run과 사용자 확인이 필요함 |

채택하지 않을 기본값:

- 최신 원격 설치 명령을 canonical로 두지 않는다.
- GitHub issue/label/comment write를 승인 없이 실행하지 않는다.
- raw 작업 메모를 공개 문서 뷰어에 복사하지 않는다.
- terse communication mode를 안전/승인 메시지보다 우선하지 않는다.

---

## 3. 경량화 전략

### 3.1 전략 A: 본체/참조 분리 (SKILL.md + references/)

**가장 효과적인 전략**. SKILL.md는 실행 지시만 담고, 상세 데이터는 `references/` 디렉토리로 분리합니다.

#### 분리 전

```
skills/check-code/
└── SKILL.md          # 534줄, 15.5KB (전체 주입)
```

#### 분리 후

```
skills/check-code/
├── SKILL.md                    # ~180줄, ~5KB (주입되는 부분)
└── references/
    ├── review-phases.md        # 6단계 상세 체크리스트
    ├── severity-criteria.md    # 심각도 분류 기준
    └── report-template.md      # 리포트 양식
```

#### SKILL.md에서 참조 방식

```markdown
## 6단계 리뷰 (상세는 references/review-phases.md 참조)

| Phase | 이름 | 핵심 |
|-------|------|------|
| 1 | 정적 분석 | lint, type-check |
| 2 | 로직 검증 | 비즈니스 룰 |
| 3 | 보안 스캔 | OWASP Top 10 |
| 4 | 성능 검토 | N+1, 메모리 |
| 5 | 접근성/UX | WCAG, 반응형 |
| 6 | 종합 판정 | PASS/CONDITIONAL/FAIL |

> 각 Phase의 상세 체크리스트가 필요하면 `references/review-phases.md`를 읽어라.
```

**효과**: 15.5KB → 5KB (67% 절감). 상세 체크리스트는 Claude가 필요할 때 Read 도구로 접근.

### 3.2 전략 B: 조건부 섹션 제거

스킬 내에서 모든 프리셋(quick/standard/thorough)의 상세 절차를 나열하면 비대해집니다. 기본 모드만 본체에 두고 나머지는 조건부로 참조합니다.

#### Before (비대)

```markdown
## Quick 모드 (15줄 상세)
...전체 절차...

## Standard 모드 (30줄 상세)
...전체 절차...

## Thorough 모드 (50줄 상세)
...전체 절차...
```

#### After (경량)

```markdown
## 실행 모드

| 모드 | 범위 | Phase |
|------|------|-------|
| --quick | Phase 1만 | ~2분 |
| (기본) | Phase 1→2→3→6 | ~10분 |
| --thorough | 전체 | ~20분 |

기본 모드(standard)로 실행하라. --quick 또는 --thorough 플래그가 있으면
references/preset-details.md 에서 해당 모드의 상세 절차를 읽어라.
```

### 3.3 전략 C: 예제 최소화

#### Before

```markdown
### 예제 1: React 컴포넌트 검수
(30줄)

### 예제 2: API 엔드포인트 검수
(25줄)

### 예제 3: DB 마이그레이션 검수
(20줄)
```

#### After

```markdown
### 출력 예시

```
## 검수 결과: [모듈명]
- Phase 1 (정적 분석): PASS
- Phase 2 (로직 검증): CONDITIONAL — 2건 수정 필요
- 종합: CONDITIONAL PASS (수정 후 재검수)
```
```

**효과**: 75줄 → 8줄.

### 3.4 전략 D: 중복 제거

여러 스킬에 반복되는 "워크플로우 위치" 다이어그램, "프리셋 조합" 테이블을 공통 참조로 추출합니다.

```
skills/
├── _shared/                      # 공통 참조
│   ├── pdarr-workflow-map.md     # 워크플로우 위치 다이어그램
│   ├── preset-matrix.md          # 깊이×모드 조합 테이블
│   └── output-format.md          # 공통 출력 양식
├── check-code/
│   └── SKILL.md                  # "공통 참조: _shared/preset-matrix.md"
└── qa-test/
    └── SKILL.md                  # "공통 참조: _shared/preset-matrix.md"
```

---

## 4. settings.json 스킬 관련 최적화

### 4.1 스킬 자동 로드 제어

```json
{
  "autoLoadSkills": false,
  "maxSkillsPerTurn": 3
}
```

| 설정 | 기본값 | 권장값 | 효과 |
|------|--------|--------|------|
| `autoLoadSkills` | `true` | `false` | 세션 시작 시 모든 스킬 주입 방지 |
| `maxSkillsPerTurn` | `5` | `2~3` | 턴당 주입 스킬 수 제한 |
| `skillsDirectory` | `.claude/skills` | (기본 유지) | 스킬 디렉토리 위치 |

### 4.2 불필요한 스킬 비활성화

사용하지 않는 스킬 파일에 frontmatter `disabled: true`를 추가하여 비활성화합니다.

```markdown
---
name: organize-docs
description: "문서 정리"
disabled: true
---
```

또는 스킬 파일을 `.claude/skills/_disabled/` 디렉토리로 이동합니다.

---

## 5. 경량화 실행 체크리스트

### Phase 1: 감사 (현재 상태 파악)

```bash
# 스킬별 크기 감사 (토큰 낭비 진단 스크립트 활용)
bash scripts/selfcheck-token-waste.sh

# 수동 확인
find .claude/skills -name "SKILL.md" -exec wc -c {} \; | sort -rn
```

- [ ] 모든 스킬의 SKILL.md 크기 확인
- [ ] 12KB 초과 스킬 목록 작성
- [ ] references/ 파일 크기도 합산 확인

### Phase 2: 분리 (본체/참조 분리)

- [ ] 12KB 초과 스킬: 체크리스트/예제/상세절차를 `references/`로 이동
- [ ] SKILL.md에 `references/파일명.md 참조` 안내 추가
- [ ] 분리 후 SKILL.md 크기 8KB 이하 확인

### Phase 3: 축소 (불필요 내용 제거)

- [ ] 예제 3개 이상 → 1개로 축소
- [ ] 중복 워크플로우 다이어그램 → `_shared/`로 추출
- [ ] 프리셋별 상세 절차 → 기본 모드만 본체, 나머지 references/
- [ ] 설명적 문장 → 테이블/리스트로 압축

### Phase 4: 설정 (토큰 절감 설정 적용)

- [ ] `maxSkillsPerTurn: 3` 설정
- [ ] 사용하지 않는 스킬 `disabled: true` 처리
- [ ] `autoLoadSkills: false` 검토 (프로젝트 특성에 따라)

---

## 6. 경량화 Before/After 비교

### check-code 스킬 예시

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| SKILL.md 크기 | 15.5KB | 5.2KB | -66% |
| 줄 수 | 534줄 | 178줄 | -67% |
| 추정 토큰 | ~4,600 | ~1,560 | -66% |
| 10턴 Sonnet 비용 | $0.138 | $0.047 | -$0.091 |

### 전체 스킬 셋 (17개) 최적화 효과 추정

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| 총 스킬 크기 | ~150KB | ~60KB | -60% |
| 동시 로드 3개 평균 | ~30KB/~9,000토큰 | ~12KB/~3,600토큰 | -60% |
| 10턴 세션 비용 (스킬만) | $0.27 | $0.108 | -$0.162 |

---

## 7. 스킬 작성 템플릿 (경량 버전)

새 스킬을 만들 때 아래 템플릿을 기준으로 합니다.

```markdown
---
name: skill-name
description: "한 줄 설명 (50자 이내)"
---

너는 [역할]이다.

## 목표

[1~2문장으로 이 스킬이 달성할 것]

## 입력

$ARGUMENTS: [입력 설명]

## 실행 절차

1. [단계 1]
2. [단계 2]
3. [단계 3]

> 상세 체크리스트 → references/checklist.md

## 출력 양식

```
## [제목]
- 항목 1: 결과
- 항목 2: 결과
- 종합: PASS / FAIL
```

## 경계

- 하지 말 것 1
- 하지 말 것 2
```

**목표 크기**: 100~200줄, 3~5KB 이내.

---

## 다음 단계

1. [토큰 낭비 자가진단](28-token-waste-selfcheck.md)
2. [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
3. [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
4. [컨텍스트 윈도우 내부 동작](19-context-window-internals.md)
