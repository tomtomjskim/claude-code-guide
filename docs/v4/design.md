# v4.0 Audit Execution Design

**생성일**: 2026-04-22
**상태**: 승인 완료, 실행 대기
**다음 단계**: `writing-plans` 스킬로 전환하여 실제 팀 디스패치 실행 계획 수립

---

## Summary

`claude-code-guide` 레포의 누적된 coherence 드리프트를 감사하고 **v4.0 전략**을 산출한다. 실행 패턴은 **Tiered Scout → Workers** (Sonnet Scout 1개 + Opus Workers 3개 병렬 + Main Opus 통합). 모든 트레이드오프는 **Coherence-first tie-breaker**로 해소한다.

산출물:
- `docs/v4/design.md` — 이 문서 (감사 실행 설계)
- `docs/v4/strategy.md` — Phase 4 산출 (v4.0 전략)

---

## 1. 사전 고정 제약 (Design 이전 확정)

| 축 | 값 | 근거 |
|---|---|------|
| Scope | **E (all layers)** | 본 레포의 가치는 5컴포넌트 맞물림 → 단일 레이어 감사는 교차 이슈 누락 |
| Version target | **v4.0 major** | 누적된 드리프트 (버전/네이밍/넘버링) 청산의 최적 타이밍 |
| Tie-breaker | **Coherence-first** | v4.0 본질은 구조 재정렬, 일관성이 나머지 렌즈의 전제 |
| 실행 패턴 | **Tiered Scout → Workers** | `.claude/rules/subagent-strategy.md` 및 `docs/33-subagent-efficiency.md` 준수 (레포 자체 규칙) |
| 보존 제약 | 한국어 기조, 레포 목적(meta-repo) | 사용자 명시 |

---

## 2. Architecture

### 2.1 역할 분담

| Phase | 주체 | 모델 | 고정 오버헤드 |
|-------|------|------|---------|
| 1. Scout | 서브에이전트 1개 | **Sonnet** | ~14k tokens |
| 2. Digest | Main (현 세션) | Opus | 0 |
| 3. Workers | 서브에이전트 3개 **병렬** | **Opus × 3** | ~42k tokens |
| 4. Integrate | Main (현 세션) | Opus | 0 |

**총 서브에이전트 비용**: ~56k fixed overhead. Workers는 탐색 턴 없이 digest 기반 작업 → Classic 4-5 에이전트 병렬 대비 ~50% 절감 (docs/33 벤치마크 기준).

> **Note**: Scout이 Sonnet인 이유 — `subagent-strategy.md`의 기본 Tiered Dispatch 표는 Scout=Haiku를 제안하지만, 이 감사는 coherence 렌즈 특성상 cross-reference 추론 정확도가 inventory 품질의 상한을 결정함. 의도적 상향 결정은 **Appendix A** 참조.

### 2.2 데이터 흐름

```
Phase 1  Scout (Sonnet)
         └─→ .audit/inventory.md  [7 섹션, 구조화]

Phase 2  Main Digest (Opus, 현 세션)
         └─→ .audit/digest-W1.md  (Contradictions 렌즈)
             .audit/digest-W2.md  (Redundancy 렌즈)
             .audit/digest-W3.md  (SSOT 렌즈)

Phase 3  Workers (Opus × 3, 병렬 1턴)
         ├─ W1: .audit/result-W1.md
         ├─ W2: .audit/result-W2.md
         └─ W3: .audit/result-W3.md

Phase 4  Main Integrate (Opus, 현 세션)
         └─→ docs/v4/strategy.md
             ├─ §1 Vision
             ├─ §2 Breaking Changes
             ├─ §3 Prioritized Backlog (P0/P1/P2)
             ├─ §4 Migration Scenarios
             ├─ §5 Success Criteria
             └─ §6 Decision Log (Appendix)
```

### 2.3 산출물 경로 정규화 규칙

**규칙**: 휘발성은 `.` 접두 최상위, 영구는 `docs/v4/` 버전 스코프.

| 경로 | 생명주기 | 커밋 | 비고 |
|------|---------|:----:|------|
| `.audit/` | 세션 내 | X | `.gitignore`에 등록 |
| `.audit/inventory.md` | 세션 내 | X | Scout 출력 |
| `.audit/digest-W{1,2,3}.md` | 세션 내 | X | Main 분할 산출 |
| `.audit/result-W{1,2,3}.md` | 세션 내 | X | Worker 출력 |
| `docs/v4/design.md` | 영구 | **O** | 이 문서 |
| `docs/v4/strategy.md` | 영구 | **O** | Phase 4 산출 |

`.gitignore` 추가: `.audit/` 1줄. 기존 `.`-접두 관례(`.claude/settings.local.json`, `.serena/`)와 일관.

### 2.4 병렬성 안전성

| 검증 항목 | 상태 |
|---------|------|
| 동일 파일 동시 수정 | No (W1→result-W1, W2→result-W2, W3→result-W3) |
| 읽기 중복 | 의도적 (digest는 Main이 워커별로 이미 분할) |
| 동일 워커 재실행 시 덮어쓰기 | 파일 단위 원자성으로 안전 |
| BLOCKED 시 처리 | §7 오류 매트릭스 참조 |

`.claude/rules/subagent-strategy.md` 조항 충족:
- "2개 기본, 3개는 각 10분+ 예상 시 조건부" → Workers 3개 각자 전체 레포 검토 → 조건 충족
- "동일 파일 수정 병렬 금지" → 서로 다른 파일만 쓰기 → 충족

---

## 3. Agent Specifications (4슬롯 프롬프트)

### 3.1 공통 프리앰블 (전 에이전트 동일 주입)

```
당신은 claude-code-guide 레포의 v4.0 감사 팀 멤버입니다.
- 작업 루트: /Users/jeongsik/develop/claude-code-guide
- Tie-breaker: Coherence-first (충돌 시 SSOT·일관성 강화 제안이 이깁니다)
- 모든 발견은 file_path:line_number 인용 필수
- 한국어로 작성 (기술 용어는 영어 원문 병기)
- 결과는 반드시 지정된 파일에 쓰고, 복귀는 요약 3줄 이내 + 파일 경로
```

### 3.2 Scout (Sonnet)

**SCOPE**
- 읽기 허용: `docs/**/*.md`, `skills/**/*.md`, `agents/*.md`, `prompts/*.md`, `workflows/*.yaml`, `agents.yaml`, `scripts/*.sh`, `hooks/**/*.sh`, `.claude/rules/*.md`, `.claude/hooks/*.sh`, `README.md`, `QUICKSTART.md`, `CLAUDE.md`
- 읽기 금지: `.git/`, `.serena/`, `node_modules/`, `tutorial/sandbox/`, `_keys/`
- 쓰기 허용: `.audit/inventory.md` 만

**RULES**
- 파일 수정 금지 (Edit/Write는 `.audit/inventory.md`에만)
- Bash는 `grep`, `find`, `ls`, `wc`, `awk`, `cat`만 허용 (상태 변경 금지)
- 토큰 예산 초과 시 중단하되 완성된 섹션은 반드시 flush (부분 > 깨진 산출)
- 관찰 항목마다 `file:line | string | 1-line context` 형식 고수

**TASK** — 7 섹션 순차 생성
1. **Version Claims** — `3\.[0-9]|v[0-9]\.[0-9]|version:\s*["\']?[0-9]`
2. **CUSTOMIZE Blocks** — `<!-- CUSTOMIZE` 열림/닫힘 매칭 검증
3. **Cross-Reference Graph** — `docs/*.md` 간 링크 broken target 플래그
4. **Agent Naming Consistency** — `agents.yaml` ↔ `agents/*.md` ↔ `prompts/*.md` 3-way
5. **Hooks Triple-Naming** — `hooks/boilerplates` / `hooks/scripts` / `.claude/hooks` 등장 및 혼용
6. **validate-system.sh Coverage** — 검사 항목 ↔ 실재 항목 diff
7. **Skills Description Overlap** — frontmatter description 중복 쌍

**RETURN**
- 파일: `.audit/inventory.md` (최대 500줄)
- 복귀: `PASS | <경로> | <발견 수>, <Top 3 카테고리>` — 3줄 이내

### 3.3 Worker 1 — Contradictions (Opus)

**SCOPE**
- 읽기 허용: `.audit/digest-W1.md` + 그 안에 인용된 파일만
- 쓰기 허용: `.audit/result-W1.md` 만

**RULES**
- 제안은 기존 모순을 없애는 **최소 변경**만 (신규 기능·확장 제안 금지)
- 심각도 필수: `CRITICAL` (validate 실패 또는 사용자 설치 실패) / `HIGH` (문서가 코드 거짓말) / `MEDIUM` (내부 문서 간 불일치) / `LOW` (스타일)
- 각 발견은 양쪽 증거 모두 인용 (단방향 증거 기각)
- 최대 20개, 초과 시 심각도 순 절단

**TASK** — 우선 탐색 지점
- 버전 드리프트 (agents.yaml 3.2 ↔ README 3.3 ↔ validate 강제)
- 스킬 description ↔ SKILL.md 본문
- 설치 스크립트 메시지 ↔ 실제 동작
- `.claude/rules/*.md` 주장 ↔ hook 실제 동작
- `CLAUDE.md` 주장 ↔ 레포 현재 상태

각 발견: Evidence A + Evidence B + 설명(1문장) + 해결안(Coherence-first) + Breaking 여부

**RETURN**
- 파일: `.audit/result-W1.md` (CRITICAL/HIGH/MEDIUM/LOW 섹션별)
- 복귀: `PASS | .audit/result-W1.md | C:N H:N M:N L:N, Top3 blockers`

### 3.4 Worker 2 — Redundancy & Consolidation (Opus)

**SCOPE**
- 읽기 허용: `.audit/digest-W2.md` + 인용된 파일
- 쓰기 허용: `.audit/result-W2.md`

**RULES**
- 통합 제안의 주 기준은 **drift surface 축소**. 단순 파일 수 감소는 근거 부족
- 삭제 제안 시 대체 계획 없으면 기각
- 그룹 멤버 2개 이상
- 최대 15 그룹

**TASK** — 통합 후보
1. 스킬 간 (`test` / `qa-test` / `qa-e2e`)
2. 에이전트 간 (`architect` / `code-reviewer` 구조 리뷰 영역)
3. 문서 간 (토큰 관련 15/28/33, 하네스 관련 29/33)
4. Hooks 3중 네이밍 → 단일 + 메타데이터 태그?
5. CUSTOMIZE 블록 반복 패턴 → shared include?
6. workflow.yaml ↔ skills/workflow ↔ /dispatch

각 그룹: Members / 공통 책임 / 실제 구별점 / 제안(merge/rename/split/keep) / Breaking

**RETURN**
- 파일: `.audit/result-W2.md`
- 복귀: `PASS | .audit/result-W2.md | Groups:N Merges:N Renames:N Keeps:N, Top3 wins`

### 3.5 Worker 3 — SSOT Violations (Opus)

**SCOPE**
- 읽기 허용: `.audit/digest-W3.md` + 인용된 파일
- 쓰기 허용: `.audit/result-W3.md`

**RULES**
- 구조 재편 제안 금지 (W2 영역). 이 워커는 "사실이 N곳에 선언됨 → 1곳으로"만 다룸
- 각 위반은 **모든 선언 위치** 열거 필수 (누락 시 위반 자체 무효)
- Canonical source 반드시 1개 지정 ("둘 중 아무거나" 기각)
- 참조 메커니즘 명시 (link / include / generate-from)
- 최대 20 위반

**TASK** — 고정 체크리스트
1. 버전 숫자
2. 에이전트 목록
3. 스킬 목록
4. PDARR 흐름 정의
5. 모델 라우팅
6. 프리셋 정의 (`--quick`, `--team` 등)
7. Hooks 3중 네이밍 구별 설명

각 위반: Fact / 선언 위치(N) / Canonical 제안(1) / 참조 메커니즘 / Breaking

**RETURN**
- 파일: `.audit/result-W3.md`
- 복귀: `PASS | .audit/result-W3.md | Violations:N CanonicalFiles:N StopHoldingState:N, Top3 unifications`

---

## 4. Phase 2 — Digest 분할 로직

### 4.1 Inventory 섹션 → Worker 매핑

| Inventory 섹션 | → W1 | → W2 | → W3 |
|---|:---:|:---:|:---:|
| 1. Version Claims | ● 강 | — | ● 강 |
| 2. CUSTOMIZE Blocks | ● | ● 강 | — |
| 3. Cross-Reference Graph | ● 강 | — | ● |
| 4. Agent Naming | ● 강 | ● | ● 강 |
| 5. Hooks Triple-Naming | ● | ● 강 | ● |
| 6. validate-system.sh Coverage | ● 강 | — | — |
| 7. Skills Description Overlap | — | ● 강 | ● |

### 4.2 Digest 스켈레톤 (W_i 공통)

```markdown
# Digest — Worker {N} · {Focus}
Source  : .audit/inventory.md
Filtered: {섹션 번호 목록}
Date    : {timestamp}

## 1. Filtered Evidence
  (해당 워커에 강·보조로 매핑된 inventory 섹션을 인라인 복사)

## 2. Main's Connecting Notes
  (섹션 간 교차 관찰 — 워커의 판단 부담 축소)

## 3. Explicit Read Scope
  (재읽기 허용 파일 화이트리스트, 5~10개 이하)

## 4. Return Contract Reminder
  (출력 파일 + 복귀 포맷 재주입)
```

### 4.3 Main's Connecting Notes — 필수 교차 관찰

**W1용**
- 버전 드리프트 ↔ validate-system.sh 커버리지 공백
- 에이전트 이름 3-way 불일치 ↔ agents.yaml 선언 ↔ 실제 프롬프트

**W2용**
- skills description 키워드 중복 ↔ CUSTOMIZE 블록 반복 패턴
- hooks 3중 네이밍 ↔ README/hooks-README/CLAUDE.md 설명 차이

**W3용**
- **7개 고정 체크리스트**: 버전 숫자 · 에이전트 목록 · 스킬 목록 · PDARR 흐름 · 모델 라우팅 · 프리셋 정의 · Hooks 3중 네이밍 구별
  (§3.5 TASK의 7개 고정 체크리스트와 정확히 일치 — 이 문서 자체의 SSOT 시범)

---

## 5. Phase 4 — Integrate & Tie-breaker

### 5.1 정규화

- 세 워커 결과에서 동일 이슈(파일 인용 중복)를 병합
- 선행 우선순위: **W1 > W3 > W2**
  - 근거: 모순(틀린 상태) → SSOT(취약한 상태) → Redundancy(비효율 상태)의 인과 순
- 동일 이슈가 하위 워커에서도 잡혔다면 상위에 병합 후 "cross-ref" 표기

### 5.2 Tie-breaker (Coherence-first) — 5단계 사다리

| 순위 | 판정 기준 | 이기는 쪽 |
|-----|---------|--------|
| 1 | SSOT를 **생성**하는가? | 생성하는 쪽 |
| 2 | Drift surface를 **축소**하는가? | 축소하는 쪽 |
| 3 | 규칙/문서/코드 **세 축을 동기화**하는가? | 동기화하는 쪽 |
| 4 | 위 3개 동일 → YAGNI | **작은 변경** |
| 5 | 여전히 동률 | Main 판단 + **Decision Log 필수 기록** |

### 5.3 P0 / P1 / P2 라벨링

| 라벨 | 기준 |
|-----|------|
| **P0** | 현 상태에서 `validate-system.sh` 실패 OR 사용자 설치/사용 실패 OR 레포가 자기 규칙을 어김 |
| **P1** | coherence 부채가 v4.0 이후 즉시 재발생 (SSOT 위반 + 영향 반경 3+ 파일) |
| **P2** | 개선되면 좋지만 드리프트 재생산 속도 느림 (표면 정리, 문서 IA) |

### 5.4 Breaking Changes 정리

- 모든 해결안에서 `breaking: yes` 필터링
- 각 항목에 Migration Note 1줄 부착: `재설치 시 자동 반영` / `CUSTOMIZE 재작성 필요` / `settings.local.json 수동 병합` 중 하나
- Breaking 없는 해결만으로 v4.0 구성 가능성은 낮음 → 1~2개 기대치

---

## 6. `docs/v4/strategy.md` 스켈레톤

Phase 4가 단일 파일에 6개 섹션으로 구성 (의도적 SSOT 시범).

```markdown
# v4.0 전략

## 1. Vision
(v4.0이 해결하는 것, 3~5줄. coherence 부채 청산이 핵심 서사)

## 2. Breaking Changes
| 항목 | 현 상태 | v4.0 상태 | Migration |

## 3. Prioritized Backlog
### P0 (N개) — v4.0 릴리스 블로커
  각 항목: 제목 + 증거(file:line 최소 2개) + 해결안 1줄 + 예상 임팩트 + 담당 컴포넌트(5 중)
### P1 (N개) — v4.0 필수
### P2 (N개) — v4.0 nice-to-have

## 4. Migration Scenarios
- 시나리오 A: "v3.3을 설치만 한 사용자" → `install-skills.sh --force`
- 시나리오 B: "CUSTOMIZE 블록 수정해 쓰던 사용자" → diff 안내 + 충돌 지점 목록

## 5. Success Criteria (v4.0 완료 판정, all must pass)
- [ ] `validate-system.sh` 0 errors / 0 warnings
- [ ] 모든 P0 백로그 close
- [ ] 버전 주장이 repo 전체에서 단 1곳에 선언 (SSOT 통과)
- [ ] CLAUDE.md · README · QUICKSTART · 각 skill 본문이 PDARR 흐름을 동일 기술
- [ ] hooks 네이밍 3중 → 단일 또는 문서화된 명시적 역할 분리
- [ ] `.claude/rules/*` 주장 ↔ 실제 hook 동작 일치

## 6. Decision Log (Appendix)
(tie-breaker 동률로 Main이 임의 판단한 항목만)
```

---

## 7. 오류 처리 매트릭스

### 7.0 Phase 0 Preflight (Scout spawn 전 필수 검증)

Scout 디스패치 **직전** Main이 다음을 확인. 하나라도 실패 시 감사 중단하고 사용자에게 보고.

```bash
# 필수 경로 존재 확인 (Scout의 Section 4, 6이 여기에 의존)
test -f agents.yaml            || FAIL "agents.yaml 누락 — Section 4 의미 상실"
test -d agents/                || FAIL "agents/ 누락 — Section 4 의미 상실"
test -d prompts/               || FAIL "prompts/ 누락 — Section 4 의미 상실"
test -f scripts/validate-system.sh || FAIL "validate-system.sh 누락 — Section 6 불가"
test -d skills/                || FAIL "skills/ 누락 — Section 7 의미 상실"
test -w .                      || FAIL ".audit/ 생성 불가 — 작업 디렉토리 쓰기 권한 없음"
```

이 단계는 "glob이 비어서 Scout이 silently 부분 inventory 생성"을 방지. 누락 경로가 있으면 **설계 전제가 깨진 것**이므로 진행 불가.

### 7.1 실패 모드 매트릭스

| 실패 모드 | 즉각 대응 | Fallback |
|---------|---------|---------|
| Phase 0 preflight 실패 | 감사 중단, 누락 항목 사용자에게 보고 | 레포 구조 재확인 요청 (대체 경로 추측 금지) |
| Scout 완전 실패 | Main이 `scripts/preflight-collect.sh` 직접 실행 + 수동 grep으로 inventory 재구축 | 속도 -30%, 품질 동등 유지 |
| Scout PARTIAL | 누락 섹션을 digest에서 비우고 "blind spot" 태그 | strategy.md §5에 "미확인 영역" 명시 |
| Worker BLOCKED | digest에 2~3 파일 추가 + 1회 재디스패치 | 2차 BLOCKED 시 나머지 2 워커로 진행 + strategy에 "W_i 커버리지 누락" |
| Worker PARTIAL (캡 초과) | 반환분 사용, 초과분은 심각도 Top-N 절단 완료 | strategy §6 Decision Log에 "W_i 캡 초과" 기록 |
| 워커 간 충돌 · tie-breaker 동률 | Main 판단 + Decision Log 필수 | 사용자 재검토 권고 플래그 |
| Main 토큰 예산 blowout | 진행분 `strategy.md` flush + draft 표기 | 사용자에게 "다음 세션 §3 P1부터 재개" 안내 |
| `docs/v4/` 권한 실패 | 중단 후 사용자 확인 요청 | 대체 경로 제안 금지 (정규화 깨짐) |

### 순환 방지
- Worker 재디스패치는 **각 워커당 최대 1회**
- Phase 4 통합 재시도 없음 — 동률은 Decision Log로 즉시 해소

---

## 8. 감사 자체의 Success Criteria

v4.0 전략의 판정 기준(§5)과 별도로, **이 감사 실행**이 성공적으로 끝났는지 판단하는 기준:

- [ ] `.audit/inventory.md` 존재 + 7 섹션 모두 채워짐, **또는** 누락 섹션이 명시적 "blind spot" 태그를 갖고 §7 오류 경로(Scout PARTIAL)를 거쳤음 — 이 경우 PARTIAL도 pass로 카운트
- [ ] `.audit/result-W{1,2,3}.md` 3개 모두 존재 (BLOCKED 워커가 있다면 strategy에 명시)
- [ ] `docs/v4/strategy.md` 6 섹션 모두 존재
- [ ] strategy §3 백로그 총 항목 ≥ 5 (이하면 감사 품질 부족 의심)
- [ ] strategy §2 Breaking Changes ≥ 1 (0이면 v4.0 명분 부족 — downgrade 검토)
- [ ] strategy §6 Decision Log에 기록된 동률 판정이 있다면 각자 근거 명시됨

---

## Appendix A — 재검토 권고 항목

실행 후 사용자가 되짚을 포인트:

- **Scout 모델 선정**: Sonnet이 Haiku 대비 ~0% 비용 차이(고정 오버헤드)를 감안한 선택. inventory 품질이 기대 이하면 다음 감사부터 Opus로 상향 검토.
- **Worker 3분할**: Contradictions/Redundancy/SSOT로 나눴으나 실제 결과에서 W2·W3 경계가 자주 모호해지면 차기 감사 시 2-워커 구조(Contradictions + Structural) 또는 4-워커 구조(위 3개 + Security) 재설계 후보.
- **P0 기준**: `validate-system.sh`를 기준점으로 삼았으나, 이 스크립트 자체가 drift 영향권에 있음. v4.0 이후에는 strategy §5의 Success Criteria를 새 기준으로 승격 후보.

---

## 관련 문서

- `.claude/rules/subagent-strategy.md` — 본 설계가 준수한 서브에이전트 규칙
- `docs/33-subagent-efficiency.md` — Tiered Scout → Workers 패턴 원본
- `docs/29-harness-engineering.md` — 5컴포넌트 하네스 모델
- `docs/30-advisor-strategy.md` — 차기 감사에서 고려할 대안 패턴
- `CLAUDE.md` — 이 레포 작업 시 기본 규칙
