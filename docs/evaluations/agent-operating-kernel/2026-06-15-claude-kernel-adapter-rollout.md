# Agent Operating Kernel Trial Evaluation: Claude Guide Rollout

```yaml
template_id: agent-operating-kernel-evaluation
template_version: 0.1.0
evaluates_template_id: agent-operating-kernel
evaluates_template_version: 0.1.0
adapter: claude-code
adapter_version: 0.1.0
work_id: AOK-CLAUDE-2026-06-15
project: claude-code-guide
task: Add Claude Code Agent Operating Kernel adapter and evaluation path
trial_date: 2026-06-15
evaluator: codex
baseline_type: estimated
summary_target: wiki/generated/reviews/2026-06-15-agent-operating-kernel-session-trial.md
```

## 1. Trial Metadata

| 항목 | 값 |
|---|---|
| Project | claude-code-guide |
| Repo/path | `/Users/jeongsik/dev/claude-code-guide` |
| Task summary | Claude Code용 kernel adapter, evaluation template, changelog entry 추가 |
| Claude mode/agent path | direct |
| Model/effort label | GPT-5 family / medium |
| Risk class | correctness |
| Risk level | medium |
| Kernel trigger | uncertainty, user-requested |
| Complexity | medium |
| Kernel applied? | partial |
| Baseline type | estimated |

## 2. Baseline Expectation

- Expected PDARR path: README와 템플릿만 추가하고 v4.4 changelog에 바로 합쳤을 가능성이 높다.
- Expected verification: `git diff --check`, status 확인.
- Expected docs: adapter는 생기지만 시험 적용 평가 파일은 없었을 수 있다.
- Expected risk: 원격의 기존 v4.4 릴리스와 충돌하면서 버전 의미가 섞일 위험.

## 3. Applied Contract

| 항목 | 값 |
|---|---|
| In scope | Claude adapter/evaluation/changelog/README/docs index 반영 |
| Out of scope | `agents.yaml`, hooks, skills, PDARR flow 변경 |
| Allowed paths | `templates/`, `docs/`, `README.md`, `docs/evaluations/` |
| Done criteria | v4.4 보존, v4.5 분리, 평가 경로 문서화, whitespace/status/push 확인 |
| Approval required | yes |
| Approval received | yes |
| Verification result | pass |
| Residual risk | v4.5 adoption 후 실제 Claude 프로젝트 적용 사례 부족 |
| Follow-up date | 2026-07-15 |

- [x] Scope / non-goals declared
- [x] Trust boundary declared
- [x] Decision IDs recorded
- [x] Approval gates respected
- [x] Rollback or recovery path recorded
- [x] Verification evidence recorded
- [x] Docs updated or intentionally skipped

## 4. Decision Evidence

| ID | Status | Decision | Reason | Evidence | Cost/Risk | Escape hatch | Review after |
|---|---|---|---|---|---|---|---|
| D1 | accepted | Claude adapter를 optional template로 추가 | 기존 PDARR/agent routing을 강제 변경하지 않기 위함 | `templates/CLAUDE.kernel.md` | 사용자가 수동 적용해야 함 | adapter 파일을 제거해도 기존 설치 영향 없음 | 2026-07-15 |
| D2 | accepted | 평가 템플릿을 adapter와 함께 추가 | trial 비교 없이는 practical mode 대비 효과 판단 불가 | `templates/CLAUDE.kernel-evaluation.md` | 문서량 증가 | 낮은 사용률이면 archive | 2026-07-15 |
| D3 | accepted | 원격 v4.4를 보존하고 kernel rollout을 v4.5로 분리 | 원격에 이미 v4.4 external skill adoption 릴리스가 존재 | `docs/v4.4-changelog.md`, `docs/v4.5-changelog.md` | 버전 번호 증가 | 필요 시 v4.5를 Unreleased로 되돌릴 수 있음 | 2026-07-15 |
| D4 | accepted | `agents.yaml` 라우팅 변경을 제외 | 모델/agent 운영 변경과 kernel 계약을 분리 | unchanged `agents.yaml` | 즉시 자동화 없음 | 별도 검증 후 라우팅 문서에 추가 | 2026-07-15 |

## 5. Outcome Metrics

| Metric | Value | Notes |
|---|---|---|
| Elapsed time | not measured | 세션 단위 작업 |
| Extra planning/review time | medium | version conflict 판단 포함 |
| Commands/tests run | `git diff --check`, `git status`, `git log`, `git push` | 문서 변경이라 unit test 없음 |
| Rework count | 1 | v4.4 add/add conflict 해결 후 v4.5로 분리 |
| Issues caught before final | 2 | GitHub auth account mismatch, version conflict |
| Issues found after final | 0 known | 현재 기준 |
| User approval prompts | multiple | `.git` write, push, auth switch |
| Token/cost estimate | not measured | optional |

## 6. Quality Review

| 기준 | 점수 1-5 | 근거 |
|---|---:|---|
| Scope control | 4 | adapter/evaluation/changelog로 제한 |
| Decision traceability | 4 | versioning 결정을 명시 |
| Reversibility | 4 | 신규 파일 중심, 기존 v4.4 보존 |
| Verification quality | 4 | status/check/push 확인 |
| Handoff clarity | 5 | 적용/평가 템플릿과 v4.5 설명이 있음 |
| Speed / friction | 3 | 릴리스 충돌 해결 때문에 시간 증가 |

## 7. Comparison

| 질문 | 답변 |
|---|---|
| 커널 적용으로 실제로 줄어든 위험은? | v4.4 의미를 덮어쓰는 버전 부채, PDARR에 커널을 강제하는 위험 |
| practical mode였다면 더 빨랐을 부분은? | v4.5 분리 대신 v4.4에 바로 합쳤을 가능성이 있음 |
| contract mode가 과했던 부분은? | correctness-only 문서 변경치고 평가 기록이 길다 |
| 다음에도 같은 risk class에서 적용할 가치가 있는가? | tune |

## 8. Verdict

- Verdict: tune
- Keep: v4.4 보존, v4.5 분리, adapter/evaluation 짝 구성
- Change: 낮은 위험 문서 작업에서는 summary-only evaluation 허용
- Remove: 없음
- Next trial candidate: 실제 Claude 프로젝트 `CLAUDE.md`에 adapter 일부 적용 후 friction 측정

## 9. Reviewer Findings Applied

- Newton 지적 반영: `docs/README.md` changelog index에 v4.5 항목을 추가했다.
- Newton 지적 반영: evaluation file naming 예시를 `docs/evaluations/agent-operating-kernel/YYYY-MM-DD-{project}-{task}.md`로 맞췄다.
- Newton 지적 반영: template/evaluation에서 version capture와 baseline type을 명시했다.
