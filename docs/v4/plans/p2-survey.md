# P2 Survey — 10 Items Current State & Bundling Proposal

**작성일**: 2026-04-23
**상태**: v4 P0+P1 완료 후 P2 진입 준비
**출처**: 실제 repo 상태 조사 + strategy §3 P2-1~10

---

## 한눈에 보기

| # | 항목 | 실제 drift 건수 | 난이도 | 번들 후보 |
|---|------|----------------|--------|----------|
| **P2-1** | Cross-reference broken links | **37+건 확인** | 중 | Bundle E (docs 단독) |
| **P2-2** | check-code CUSTOMIZE stack 예시 분리 | 9 블록 | 중 | Bundle F (skill refactor) |
| **P2-3** | 모델 라우팅 canonical 통일 | 4 location | 작음 | Bundle G (SSOT 재정렬) |
| **P2-4** | PDARR 흐름 canonical 통일 | 4 location | 작음 | Bundle G |
| **P2-5** | Hooks 3중 네이밍 제목 수정 | 1 제목 + hooks/README | **P1-5 부분 해소**, 작음 | 독립 or drop |
| **P2-6** | 서브에이전트 14k 오버헤드 canonical | 3 location | 작음 | Bundle G |
| **P2-7** | 설치 스크립트 옵션 canonical | 4 doc | 중 | Bundle E (docs) |
| **P2-8** | docs 15/28/33 + 29/33 cross-link 강화 | 4 doc 상호링크 | 작음 | Bundle E |
| **P2-9** | architect ↔ code-reviewer 경계 | 1 description | 최소 | 독립 (분 단위) |
| **P2-10** | PDARR 3축 매핑 테이블 | 1 추가 | 작음 | 독립 |

**총 예상 작업량**: 약 3-4 슬라이스 (번들링 적용 시)

---

## 상세 상태

### P2-1 Cross-reference broken links (37+ 건)

**증거 — 2026-04-23 실측:**

| 깨진 참조 | 실제 파일 | 참조하는 파일 수 |
|----------|----------|-----------------|
| `14-token-pricing-optimization.md` | `15-token-pricing-optimization.md` | **9** (docs/17, 18, 28, 30, 33, README.md 등) |
| `08-workflows.md` | `11-workflow-commands.md` | 2 (docs/10, docs/05) |
| `13-handoff-failure-recovery.md` | `13-handoff-and-failure.md` | 1 (docs/00-setup-checklist.md) |
| README.md L288-299 "두 번째 테이블" | -1 offset 12건 | 1 (README 테이블 전체) |
| `docs/15-26*` 내부 ~23건 (+1 offset 추정) | - | 9+ |

**총**: 37건+ (strategy 주장과 일치 또는 초과)

**해결 접근**:
- sed 스크립트로 일괄 치환 (파일명 기준)
- README.md 테이블은 수동 재번호
- `docs/v4/strategy.md`·`docs/v3-changelog.md` 내 참조는 **historical document 원칙으로 보존**

**난이도**: 중 (sed 일괄 후 수동 검증 필요). **단독 처리 권장** (docs/ 전수 sweep).

---

### P2-2 check-code CUSTOMIZE stack 예시 분리

**증거**: `skills/check-code/SKILL.md` 9개 `<!-- CUSTOMIZE -->` 블록 내부에 PHP/React/Python 예시가 반복.

**해결 접근**: `skills/check-code/references/stack-examples.md` 신규 파일에 stack별 예시 분리, SKILL.md는 summary + link.

**난이도**: 중 (파일 분리 + link 패턴 도입). **단독 처리**.

---

### P2-3 모델 라우팅 canonical 통일

**증거 — 4곳 중복 확인:**
- `agents.yaml:7-35` `routing_rules` — canonical 후보 (strategy 권장)
- `.claude/rules/subagent-strategy.md:62-68` — 간결 표
- `docs/33-subagent-efficiency.md:341-349` — 상세 표
- `skills/workflow/SKILL.md:154-164` — 에이전트별 매핑

**해결 접근**: `agents.yaml:7-35`을 canonical로 지정, 나머지 3곳은 "상세: agents.yaml#model_routing" 링크.

**난이도**: 작음. **Bundle G로 묶음 가능**.

---

### P2-4 PDARR 흐름 canonical 통일

**증거 — 4곳 중복**:
- `CLAUDE.md:58` canonical 후보 (P1-2에서 이미 canonical 기여)
- `README.md:305-323, :588-593` — 2곳
- `skills/workflow/SKILL.md:90-118` — 1곳
- `skills/dispatch/SKILL.md:146-172` — 1곳

**해결 접근**: `CLAUDE.md:58` canonical. README와 skills의 ASCII 흐름도는 UX 가치 보존하되 "상세 순차: CLAUDE.md#pdarr--preset-system" 주석 추가. skills/workflow Phase 매핑은 CLAUDE.md 순차와 매핑 테이블 추가.

**난이도**: 작음. **Bundle G로 묶음 가능**.

---

### P2-5 Hooks 3중 네이밍 제목 수정 — **P1-5에서 부분 해소**

**현재 상태** (P1-5 커밋 0505d08 이후):
- `CLAUDE.md:47` 제목 "Hooks directory has TWO meanings" → "Hooks directory layout"으로 완화됨
- `.reference.sh` 접미어로 파일명 자기설명 달성

**남은 잔여 작업**:
- `hooks/README.md:145-171` 3중 네이밍 상세 설명이 여전히 존재 → 축소 가능 (파일명으로 자기설명되므로 장문 설명 불필요)

**해결 접근**: hooks/README.md 해당 섹션 경량화. 매우 작음.

**난이도**: 최소. **독립 처리 or drop** (본질은 P1-5에서 해소).

---

### P2-6 서브에이전트 14k 오버헤드 canonical

**증거 — 3+ 곳**:
- `docs/33-subagent-efficiency.md:21-32` 분해 표 — canonical 후보 (strategy 권장)
- `.claude/rules/subagent-strategy.md:9` 요약 1줄
- `CLAUDE.md:81` 요약 1줄
- `docs/33` 내부 4곳 추가 언급 (5, 30, 38, 244, 440)

**해결 접근**: docs/33:21-32를 canonical로 지정, 나머지 2곳(subagent-strategy.md, CLAUDE.md)은 요약 + canonical 링크.

**난이도**: 작음. **Bundle G로 묶음 가능**.

---

### P2-7 설치 스크립트 옵션 canonical

**증거 — 4곳**:
- `scripts/install-skills.sh --help` / `install-hooks.sh --help` — canonical 후보 (런타임 출력)
- `README.md:85-132`
- `skills/README.md:9-25`
- `hooks/README.md:19-45`
- `CLAUDE.md:28-30`

**해결 접근**: 각 스크립트의 `--help` 출력을 canonical로 지정. 문서는 "상세: `bash scripts/install-hooks.sh --help`" 링크.

**난이도**: 중 (사용자가 문서에서 읽는 옵션이므로 요약은 남겨야 하고, 상세만 옮기는 것이 현실적).

---

### P2-8 docs 15/28/33 + 29/33 cross-link 강화

**증거**: 토큰 관련(15/28/33)과 하네스 관련(29/33)에 겹치는 멘탈 모델.

**해결 접근**: 29와 33 상단에 관련 섹션 forward 링크. 15/28은 33의 부록 섹션으로 forward 링크. **파일 merge 금지** (history 손실).

**난이도**: 작음. **Bundle E로 묶음 가능** (docs 편집).

---

### P2-9 architect ↔ code-reviewer description 경계

**증거** (실측 2026-04-23):
- `agents/architect.md`: `"시스템 아키텍트 - 구조적 무결성 관점의 아키텍처 설계, 기술 결정, 구현 전략 수립"`
- `agents/code-reviewer.md`: `"코드 리뷰 전문가 - 프로덕션 준비도 게이트, 품질, 아키텍처, 테스트 종합 검증"`

code-reviewer description에 "아키텍처" 단어 포함 → 경계 흐림.

**해결 접근**: code-reviewer description의 "아키텍처" → "기구현된 코드의 아키텍처 준수 여부"로 좁힘. 시간축 구별 명시 (pre vs post).

**난이도**: 최소 (1줄 수정). **독립 처리**.

---

### P2-10 PDARR 3축 매핑 테이블 신규

**증거**: `agents.yaml`의 quick-fix/standard/thorough ↔ dispatch의 Trivial/Simple/Medium/Complex 이름·기준 불일치 (P1-6에서 complexity tier는 해소, agents.yaml 축은 별도).

**해결 접근**: `.claude/rules/subagent-strategy.md` 또는 `docs/29-harness-engineering.md`에 "복잡도 × 예산 × 실행 3축 매핑" 테이블 신규. 예: `Trivial → quick-fix → 메인 직접`, `Complex → thorough → Scout→Workers`.

**난이도**: 작음 (테이블 1개 신규). **독립 처리**.

---

## 번들링 제안

### Bundle E: docs drift cleanup (P2-1 + P2-8)

**포함**: P2-1(broken links 37건), P2-8(cross-link 강화)
**범위**: docs/ 전수 sweep + 링크 보강
**예상 파일**: docs/ 대부분 + README.md 2 테이블
**예상 규모**: Bundle C급 (20+ 파일, 주로 1-2줄씩)

**이점**: docs 영역 한 번에 정리, 이후 docs 작업 시 링크 신뢰도 복원

### Bundle F: skill refactor (P2-2 단독)

**포함**: P2-2(check-code CUSTOMIZE 분리)
**범위**: check-code skill 재구조화 + references/ 신규 파일
**예상 파일**: 2개 (SKILL.md + references/stack-examples.md 신규)

### Bundle G: SSOT 재정렬 (P2-3 + P2-4 + P2-6)

**포함**: P2-3(모델 라우팅), P2-4(PDARR 흐름), P2-6(14k 오버헤드) — 모두 "canonical + consumer 링크" 패턴
**범위**: 3개 canonical 지정 + 약 9개 consumer 참조 링크화
**예상 파일**: 약 6-8개
**예상 규모**: P1-6급 (작음)

**이점**: 같은 테마(SSOT 재정렬)로 리뷰·검증 효율화

### 독립 처리 (번들 부적합)

- **P2-9**: 1줄 description 수정. 5분.
- **P2-10**: 테이블 1개 신규. 10분.
- **P2-5 잔여**: hooks/README.md 섹션 경량화. 10분. P1-5에서 주요 부분 해소되어 drop 가능.

---

## 실행 권장 순서

1. **Bundle G (SSOT 재정렬)** — 가장 깔끔한 scope, P1-2/P1-6 패턴 재사용
2. **P2-9, P2-10 독립 처리** — 짧은 마무리
3. **Bundle F (check-code refactor)** — 단독 skill 작업
4. **Bundle E (docs cleanup)** — 최대 scope, 마지막으로 한꺼번에 sweep
5. **P2-5 잔여**: drop 또는 Bundle E에 병합

**대안**: v4.0을 P1 완료 시점에서 마감하고 P2는 v4.1 또는 별도 릴리스로 분리. Bundle E가 가장 영향 크므로 v4 내 우선 처리 vs 별도 릴리스 판단 필요.

---

## Out of Scope (v4 전체에서)

- `docs/v4/strategy.md` / `docs/v3-changelog.md` 내 깨진 참조 — **historical documents, append-only 원칙 준수**
- 새 기능 / 새 에이전트 / 새 스킬 추가
- 버전 숫자 bump (3.2 canonical 유지)
