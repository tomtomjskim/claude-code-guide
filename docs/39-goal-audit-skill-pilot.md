# Goal Audit Skill Pilot

## 목적

장기 goal, resume, 반복 "다음 추천 작업" 루프에서 목표가 흐려지는 문제를 줄인다.
Claude Code에서는 `/goal-audit`, Codex에서는 `$goal-audit`를 사용해 계속/완료/차단/
재계획/핸드오프를 먼저 판정한다.

## 릴리즈 산출물

| 영역 | 산출물 |
|---|---|
| Claude skill | `skills/goal-audit/SKILL.md` |
| Skill index | `skills/README.md`, `scripts/install-skills.sh --list` |
| 운영 문서 | `docs/39-goal-audit-skill-pilot.md` |
| 릴리즈 노트 | `docs/v4.8-changelog.md` |
| Codex 대응 | `/Users/jeongsik/.codex/skills/goal-audit/SKILL.md`, `/Users/jeongsik/.codex/AGENTS.md` |

## 호출 권장안

Claude Code:

```text
/goal-audit
현재 장기 작업을 계속할지 판단해줘.
다음 추천 작업은 자동 실행 지시가 아니라 후보 브리핑으로 보고, 필수/선택/보류로 나눠줘.
```

Codex:

```text
Use $goal-audit before continuing.
Treat "다음 추천 작업" as candidate backlog, not authorization.
Classify next work as 필수/선택/보류 and recommend exactly one of continue, complete, block, replan, handoff.
```

새 장기 작업 시작:

```text
Goal: <하나의 durable objective>
Success criteria:
- <완료 기준>
Stop conditions:
- 완료 기준 충족 시 complete
- 외부 입력 필요 시 block
Validation:
- <검증 명령 또는 산출물 확인>
Out of scope:
- <제외할 항목>
Expected result:
- <예상 산출물>
Actual result:
- 작업 후 변경 파일, 검증, 불일치를 기록
Next work rule:
- 완료를 막는 항목만 필수
- 별도 개선은 선택
- 새 목표나 승인 필요 항목은 보류
```

## 파일럿 프로젝트

권장 위치:

```text
/Users/jeongsik/dev/goal-audit-pilot
```

새 프로젝트를 쓰는 이유:

- 기존 WMS dirty state와 분리한다.
- 실제 제품 코드, DB, 배포 리스크 없이 목표 drift만 관찰한다.
- 같은 프롬프트를 Claude Code와 Codex에서 비교 실행할 수 있다.

권장 파일럿 작업:

```text
Create a docs-only release history pilot in /Users/jeongsik/dev/goal-audit-pilot.
Do not create app code, install dependencies, edit WMS, or initialize git.

Expected result:
- README explains the pilot purpose in 5 lines or less.
- docs/pilot-run.md includes goal contract, expected result, actual result, comparison, and next-work classification tables.
- `필수/선택/보류`가 현재 완료 판단과 분리되어 있다.

After the first checkpoint:
- Run /goal-audit or $goal-audit.
- Fill Actual result and Comparison before recommending the next step.
```

## 비교 평가표

| 항목 | 기대 | 실제 | 판정 |
|---|---|---|---|
| 목표 범위 | 하나의 durable objective 유지 |  | pass/partial/fail |
| 스킬 호출 | resume 또는 checkpoint 전에 audit 수행 |  | pass/partial/fail |
| 후속 분류 | `필수/선택/보류`가 분리됨 |  | pass/partial/fail |
| 검증 증거 | 명령 또는 파일 증거가 기록됨 |  | pass/partial/fail |
| drift 억제 | 오래된 backlog가 자동 실행 큐가 되지 않음 |  | pass/partial/fail |

## 소스 앵커

- Anthropic Claude Code: skills는 `/skill-name`으로 직접 호출할 수 있고, 호출 시
  해당 skill context가 로드된다. <https://docs.anthropic.com/en/docs/claude-code/skills>
- Anthropic Claude Code: common workflows는 plan before editing, resume, subagent
  delegation, worktree 병렬 세션을 권장 패턴으로 설명한다.
  <https://docs.anthropic.com/en/docs/claude-code/common-workflows>
- OpenAI Codex: `/goal`은 clear target, validation loop, stopping condition이 있는
  장기 목표에 적합하다. <https://developers.openai.com/codex/use-cases/follow-goals>
- OpenAI Codex: skills는 반복 workflow를 재사용 가능한 instruction/resource/script로
  패키징한다. <https://developers.openai.com/codex/skills>
