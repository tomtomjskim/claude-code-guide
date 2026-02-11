# Workflow Commands 가이드

## 개요

PDARR 사이클 기반의 체계적인 AI 개발 워크플로우 커맨드 시스템.
`/dispatch`가 작업 복잡도를 자동 판단하여 최적의 실행 경로를 선택한다.

> 상세 가이드: [`.claude/workflow-commands-guide.md`](../.claude/workflow-commands-guide.md)

---

## 핵심 철학: PDARR

**Plan → Document → Act → Review → Reflect**

모든 작업은 이 사이클의 전체 또는 일부를 거친다.

| 복잡도 | 사이클 범위 | 시작 커맨드 |
|--------|-----------|------------|
| Trivial | 직접 수정 | 불필요 |
| Simple | Act → Review | `/run` |
| Medium | Document → Act → Review | `/analyze` |
| Complex | Plan → Document → Act → Review → Reflect | `/prd` or `/workflow` |

---

## 커맨드 전체 맵

### 시작점
| 커맨드 | 역할 |
|--------|------|
| `/dispatch` | 스마트 라우터 - 복잡도 판단 후 최적 경로 라우팅 |

### 계획 단계 (Plan)
| 커맨드 | 역할 | 산출물 |
|--------|------|--------|
| `/prd` | 요구사항 문서 + 복잡도 1차 판단 | `docs/prd/{프로젝트}/prd.md` |
| `/analyze` | 코드베이스 분석 + 실행전략 2차 판단 | 분석 브리핑 |
| `/spec` | 기술 명세서 작성 | `docs/spec/{모듈}/` |

### 실행 단계 (Act)
| 커맨드 | 역할 | 산출물 |
|--------|------|--------|
| `/test` | TDD 테스트 케이스 작성 (Red) | `/tests/{도메인}/` |
| `/run` | 구현 (Orchestrator-Worker) | 코드 |

### 검증 단계 (Review)
| 커맨드 | 역할 | 산출물 |
|--------|------|--------|
| `/check-spec` | 설계문서 ↔ 코드베이스 일관성 검수 | 검수 리포트 |
| `/check-code` | 코드 품질 검수 | 검수 리포트 |
| `/qa-test` | 종합 QA 자동화 | `docs/qa-reports/` |

### 회고 단계 (Reflect)
| 커맨드 | 역할 | 산출물 |
|--------|------|--------|
| `/reflect` | 자기성찰 + Memory 저장 | Memory 파일 |
| `/complete` | 작업 완료 정리 | `docs/complete/` |

### 유틸리티
| 커맨드 | 역할 |
|--------|------|
| `/stage` | Git 스테이징 + 커밋 메시지 제안 |
| `/flow` | 현재 컨텍스트 정리 |
| `/workflow` | PDARR 전체 사이클 자동화 (팀 Agent 조율) |

---

## 2단계 판단 시스템

작업 규모에 맞는 실행 전략을 자동 결정하는 핵심 메커니즘.

```
/prd ── 1차 판단 (요구사항 텍스트 기반 추정)
  │
  ▼
/analyze ── 2차 판단 (코드베이스 실제 분석 후 보정)
  │
  ▼
실행 전략 결정 ── 단일 Agent / 병렬 Task / 팀 Agent
```

| 지표 | Simple | Medium | Complex |
|------|--------|--------|---------|
| 파일 수 | 1-2개 | 3-5개 | 6개+ |
| 레이어 수 | 1개 | 1-2개 | 3개+ |
| 프론트+백엔드 | 한쪽만 | 한쪽 주력 | 양쪽 동시 |

---

## 실행 전략 3가지

### 전략 A: 단일 Agent (Simple ~ Medium)
메인 Agent가 직접 커맨드 실행. 파일 1-3개, 단일 레이어.

### 전략 B: 병렬 Task Agent (Medium)
독립 Task Agent 2-3개 병렬 생성. TeamCreate 불필요. 파일 4-6개.

### 전략 C: 팀 Agent (Complex)
TeamCreate → TaskCreate → Task(teammate) → SendMessage → TeamDelete.
파일 7개+, 3개+ 레이어.

---

## 라우팅 흐름도

```
/dispatch (30초 이내 판단)
  │
  ├─ Trivial → 직접 수정
  ├─ Simple  → /run → /check-code → /stage
  ├─ Medium  → /analyze → /run → /check-code → /stage
  ├─ Complex → /prd → /analyze → /workflow (팀 Agent)
  └─ Review  → /check-spec 또는 /check-code
```

---

## 셋업 가이드

새 프로젝트에 이 워크플로우를 적용하려면:

1. `.claude/commands/` 디렉토리에 커맨드 `.md` 파일 배치
2. `docs/{prd,todo,spec,history,qa-reports,complete}` 산출물 디렉토리 생성
3. CLAUDE.md에 워크플로우 참조 추가
4. `~/.claude/settings.json`에 팀 Agent 실험 기능 활성화
5. (선택) `~/.zshrc`에 래퍼 함수로 리마인드 배너 등록

> 상세 셋업 절차는 [`.claude/workflow-commands-guide.md`](../.claude/workflow-commands-guide.md)의 Section 7을 참조.

---

## 관련 문서

- [커맨드/스킬 가이드](02-commands-skills.md) - 기본 커맨드 참조
- [개발 파이프라인](03-development-pipeline.md) - 기본 파이프라인 참조
- [에이전트 페르소나](05-agent-personas.md) - Agent 역할 정의
- [코드 리뷰 시스템](10-code-review-system.md) - 전문 리뷰어 시스템
