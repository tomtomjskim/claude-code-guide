# Shared Agent Rules

이 문서는 Claude Code와 Codex를 함께 쓰는 환경에서 전역 agent rule을 공유하는 기준을 정의한다.

핵심 원칙은 프로젝트 내부 agent를 유지하고, 전역 agent는 공통 adapter만 둔다는 것이다.

## 1. 디렉터리 구조

권장 전역 구조:

```text
~/.agents/
  common-agents/          # Claude/Codex 공통 역할 규칙 SSOT
  adapters/
    claude/               # Claude Code frontmatter adapter
    codex/                # Codex TOML adapter
  backups/                # 기존 전역 adapter 백업

~/.claude/agents/         # ~/.agents/adapters/claude/*.md symlink
~/.codex/agents/          # ~/.agents/adapters/codex/*.toml symlink
```

프로젝트별 agent는 각 repo 내부에 둔다.

```text
<repo>/.claude/agents/
<repo>/.codex/agents/
```

Frecto, WMS 같은 프로젝트 특화 규칙은 전역 agent에 넣지 않는다.

## 2. 우선순위

| 범위 | 위치 | 우선순위 |
|---|---|---|
| 프로젝트 특화 | `<repo>/.claude/agents/`, `<repo>/.codex/agents/` | 높음 |
| 프로젝트 지침 | `<repo>/CLAUDE.md`, `<repo>/AGENTS.md` | 높음 |
| 전역 adapter | `~/.claude/agents/`, `~/.codex/agents/` | 중간 |
| 공통 rule SSOT | `~/.agents/common-agents/` | 원천 |

프로젝트 내부 agent가 있으면 전역 공통 agent보다 우선한다.

## 3. Adapter 패턴

Claude와 Codex는 agent 파일 형식이 다르다.

| 런타임 | Adapter 형식 |
|---|---|
| Claude Code | Markdown frontmatter + 본문 |
| Codex | TOML + `developer_instructions` |

따라서 공통 rule을 직접 양쪽 런타임에 넣지 않고, adapter가 공통 rule을 참조한다.

Claude adapter 예:

```markdown
---
name: code-reviewer
description: Common read-only code review agent. Uses shared rule source at ~/.agents/common-agents/code-reviewer.md.
model: sonnet
effort: high
---

# Code Reviewer Adapter

Before acting, read and follow `/Users/<name>/.agents/common-agents/code-reviewer.md`.
```

Codex adapter 예:

```toml
name = "code-reviewer"
description = "Common read-only code review agent. Uses shared rule source at ~/.agents/common-agents/code-reviewer.md."
model_reasoning_effort = "high"
developer_instructions = """
# Code Reviewer Adapter

Before acting, read and follow `/Users/<name>/.agents/common-agents/code-reviewer.md`.
"""
```

## 4. Team Install 동작

`scripts/install-skills.sh --team`은 더 이상 `~/.claude/agents`에 repo agent를 직접 복사하지 않는다.

변경된 동작:

1. `agents.yaml`, `prompts/`, `workflows/`, `context/`, `hooks/`, `scripts/`는 기존처럼 `~/.claude/team/`에 복사한다.
2. `agents/*.md`는 validator용 team package로 `~/.claude/team/agents/`에 복사한다.
3. active Claude agent adapter는 `~/.agents/adapters/claude/`에 복사한다.
4. `~/.claude/agents/*.md`는 해당 adapter를 symlink로 참조한다.
5. 기존 active adapter 파일이 있고 `--force`가 없으면 덮어쓰지 않는다.
6. `--force`로 교체할 때는 `~/.agents/backups/`에 백업한다.

## 5. 검증

전역 adapter 확인:

```bash
find ~/.claude/agents ~/.codex/agents -maxdepth 1 -type l -print
```

Codex TOML adapter 검증:

```bash
for f in ~/.agents/adapters/codex/*.toml; do
  tomlq . "$f" >/dev/null
done
```

Claude team system 검증:

```bash
bash ~/.claude/team/scripts/validate-system.sh
```

이 검증은 agent symlink가 아니라 `~/.claude/team/agents/`의 team package agent 정의를 본다. 또한 YAML 파싱, `~/.claude/settings.json`, `~/.claude/settings.local.json`, hooks, skills까지 함께 본다. Python `yaml` 모듈(PyYAML)이 없거나 settings hooks가 없으면 shared agent 설치가 정상이어도 실패할 수 있다.

검증 실패가 `~/.claude/team` 미설치 때문이면 `scripts/install-skills.sh --team <target>`을 먼저 실행한다. 기존 프로젝트 특화 전역 agent가 있는 경우 `--force` 없이 실행해 충돌 파일을 확인한다.

## 6. 운영 규칙

- 공통 역할 변경은 `~/.agents/common-agents/<role>.md`를 먼저 수정한다.
- adapter는 런타임 metadata나 참조 경로가 바뀔 때만 수정한다.
- 프로젝트 특화 규칙은 repo 내부 agent에 둔다.
- 전역 agent 이름과 프로젝트 agent 이름이 같아도 프로젝트 내부 agent가 우선해야 한다.
- 기존 전역 agent를 공통 adapter로 교체할 때는 먼저 백업한다.
