# Agent Operating Kernel Trial Evaluation for Claude Code

```yaml
template_id: agent-operating-kernel-evaluation
template_version: 0.1.0
evaluates_template_id: agent-operating-kernel
evaluates_template_version:
adapter: claude-code
adapter_version:
project:
task:
trial_date:
evaluator:
```

이 템플릿은 `templates/CLAUDE.kernel.md`를 실제 프로젝트에 적용한 뒤, 기존 PDARR/practical mode와 contract mode의 차이를 비교하기 위한 기록 양식이다. 한 작업당 한 파일로 남긴다.

## 1. Trial Metadata

| 항목 | 값 |
|---|---|
| Project | |
| Repo/path | |
| Task summary | |
| Claude mode/agent path | direct / skill / subagent / team |
| Model/effort label | |
| Risk class | low / correctness / security-privacy / data-destructive / deploy / financial |
| Complexity | trivial / simple / medium / complex / critical |
| Kernel applied? | yes / partial / no |

## 2. Baseline Expectation

커널을 적용하지 않았다면 어떤 방식으로 진행했을지 짧게 적는다.

- Expected PDARR path:
- Expected verification:
- Expected docs:
- Expected risk:

## 3. Applied Contract

- [ ] Scope / non-goals declared
- [ ] Trust boundary declared
- [ ] Decision IDs recorded
- [ ] Approval gates respected
- [ ] Rollback or recovery path recorded
- [ ] Verification evidence recorded
- [ ] Docs updated or intentionally skipped

## 4. Decision Evidence

| ID | Decision | Reason | Cost | Escape hatch |
|---|---|---|---|---|
| D1 | | | | |

## 5. Outcome Metrics

| Metric | Value | Notes |
|---|---|---|
| Elapsed time | | |
| Extra planning/review time | | |
| Commands/tests run | | |
| Rework count | | |
| Issues caught before final | | |
| Issues found after final | | |
| User approval prompts | | |
| Token/cost estimate | | optional |

## 6. Quality Review

| 기준 | 점수 1-5 | 근거 |
|---|---:|---|
| Scope control | | |
| Decision traceability | | |
| Reversibility | | |
| Verification quality | | |
| Handoff clarity | | |
| Speed / friction | | |

## 7. Comparison

| 질문 | 답변 |
|---|---|
| 커널 적용으로 실제로 줄어든 위험은? | |
| practical mode였다면 더 빨랐을 부분은? | |
| contract mode가 과했던 부분은? | |
| 다음에도 같은 risk class에서 적용할 가치가 있는가? | yes / tune / no |

## 8. Verdict

- Verdict: adopt / tune / reject / needs more trials
- Keep:
- Change:
- Remove:
- Next trial candidate:
