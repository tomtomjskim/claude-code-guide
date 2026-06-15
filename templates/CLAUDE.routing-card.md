# Agent/Model Routing Card for Claude Code

```yaml
template_id: agent-model-routing-card
template_version: 0.1.0
adapter: claude-code
adapter_version: 0.1.0
applied_at:
```

이 카드는 안전 커널이 아니라 성능/효율 라우팅 기준이다. 프로젝트의 기존 `CLAUDE.md` 또는 `.claude/rules/`에 필요한 표만 복사한다.

## Routing Defaults

| Situation | Route | Effort / model tier | Notes |
|---|---|---|---|
| 단순 설명, 문서 정리, 1파일 수정 | direct | fast/default | subagent/team 금지 |
| 기존 패턴이 명확한 구현 | direct | medium/default | 기존 컨벤션 우선 |
| 낯선 코드베이스 탐색 | explorer read-only -> executor | medium | explorer는 파일/제약 확인 |
| 원인 불명 버그 | executor + hypothesis explorer + final reviewer | high | 가설 분리 |
| UI/디자인 변경 | pattern explorer + executor + visual reviewer | medium/high | 기존 화면 패턴 우선 |
| DB/API 계약 변경 | executor + schema/API reviewer | high | schema/source/test evidence 필요 |
| 보안/데이터/배포/금융 | contract mode + reviewer | deep/maximum | approval + rollback 필수 |
| 여러 독립 하위작업 | lead + disjoint workers | high | ownership 분리 시에만 |
| worktree 충돌 가능 | main writer + read-only reviewers | medium/high | 같은 파일 병렬 write 금지 |

## Agent Role Cards

| Role | Use when | Must return | Must not |
|---|---|---|---|
| Explorer | 모르는 코드/문서/제약 확인 | files, facts, uncertainty | edit files |
| Reviewer | 결함 발견 기대값 있음 | severity-ranked findings | rewrite implementation |
| Advisor | 설계/운영 판단 지원 | options, tradeoffs, recommendation | own final decision |
| Worker | 독립 파일 범위 명확 | changed paths, verification | touch shared files outside ownership |
| Operator reviewer | deploy/data/secrets/service risk | approval gates, rollback gaps | run lifecycle/destructive commands |

## Route ROI Check

긴 trial 문서를 만들지 않는다. 실제 작업 후 필요한 경우 5-10줄만 남긴다.

```text
Task:
Chosen route:
Baseline route:
Why this route:
Useful findings:
Applied findings:
Overhead:
Issues caught:
Next time route: downgrade | same | upgrade
```
