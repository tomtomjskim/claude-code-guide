# Bundle G — SSOT 재정렬 (P2-3 + P2-4 + P2-6)

**작성일**: 2026-04-23
**상태**: v4 P2 진입 1차 슬라이스
**범위**: P2-3(모델 라우팅) + P2-4(PDARR 흐름) + P2-6(14k 오버헤드) canonical 재정렬

---

## Goal

세 개 canonical 축을 각각 1곳으로 집중하고 consumers는 링크·요약만 유지. 과거 pattern(P1-2 프리셋, P1-6 Complexity Tier) 재적용.

| 주제 | Canonical | Consumers (링크 추가 대상) |
|------|-----------|--------------------------|
| 모델 라우팅 | `agents.yaml:7-35` `routing_rules` | `.claude/rules/subagent-strategy.md:62-68`, `docs/33:341-349`, `skills/workflow/SKILL.md:154-164` |
| PDARR 흐름 | `CLAUDE.md:58` `Flow` bullet | `README.md:305-323`, `skills/workflow/SKILL.md:89-118`, `skills/dispatch/SKILL.md:146-172` |
| 14k 오버헤드 | `docs/33:21-32` 분해 표 | `.claude/rules/subagent-strategy.md:9`, `CLAUDE.md:81` |

**원칙**: consumer 내용 보존(ASCII 흐름도·Phase 요약·비용 테이블은 UX 가치), canonical 링크 1줄 추가로 "상세/권위는 canonical" 명시.

---

## Tasks

### Task 1: P2-3 모델 라우팅 consumers에 canonical 링크 추가

- [ ] `.claude/rules/subagent-strategy.md:61-68` 섹션 상단에 canonical 링크 1줄
- [ ] `docs/33-subagent-efficiency.md:~338` 모델 라우팅 섹션 상단에 canonical 링크
- [ ] `skills/workflow/SKILL.md:~152` Model Routing 섹션 상단에 canonical 링크

### Task 2: P2-4 PDARR 흐름 consumers에 canonical 링크 추가

- [ ] `README.md:305` PDARR 워크플로우 섹션 상단에 canonical 링크
- [ ] `skills/workflow/SKILL.md:~89` PDARR Phase 요약 섹션 상단에 canonical 링크
- [ ] `skills/dispatch/SKILL.md:~143` 전체 흐름도 섹션 상단에 canonical 링크

### Task 3: P2-6 14k 오버헤드 consumers에 canonical 링크 추가

- [ ] `.claude/rules/subagent-strategy.md:9` 한 줄 요약에 canonical 링크 appending
- [ ] `CLAUDE.md:81` 한 줄 요약에 canonical 링크 appending

### Task 4: 검증 + 커밋

- [ ] `docs/33:21-32` heading `## 1. 고정 오버헤드 구조` slug 확인 (canonical 앵커)
- [ ] 모든 consumer가 같은 canonical 참조 위치 사용
- [ ] validate baseline 유지
- [ ] 단일 커밋 + 푸시

---

## Out of Scope

- canonical 자체 수정 금지 (agents.yaml, CLAUDE.md:58, docs/33:21-32 불변)
- README.md·skills 내 ASCII 흐름도·Phase 상세 문구 삭제 금지 (UX 가치 보존)
- 새 canonical 지정 없음 (기존 구조 유지)
