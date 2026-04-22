# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**This is a meta-repository.** It does not build, run, or test. It ships Claude Code configuration to *other* projects via installer scripts:

- `skills/` → copied into target project's `.claude/skills/` by `scripts/install-skills.sh`
- `hooks/boilerplates/` → copied into target's `.claude/hooks/` by `scripts/install-hooks.sh` (also patches `.claude/settings.local.json` via `jq`)
- `agents/`, `prompts/`, `workflows/`, `context/`, `agents.yaml` → copied into `~/.claude/team/` and `~/.claude/agents/` by `install-skills.sh --team`

There is no `package.json`, no test runner, no lint config at the repo root. The deliverables are bash + markdown + YAML.

## Commands that matter

```bash
# Validate the team system after a --team install (checks 18 categories)
bash scripts/validate-system.sh

# Sanity-check the current repo/project for token-wasting config
bash scripts/selfcheck-token-waste.sh

# Generate a context packet to paste into a subagent prompt
# (lists source files, detects stack, summarizes git state)
bash scripts/preflight-collect.sh [target-path]

# List installable skills / hooks without installing
bash scripts/install-skills.sh --list
bash scripts/install-hooks.sh --list
```

The validators and installers are idempotent: `install-skills.sh` and `install-hooks.sh` **SKIP** existing files unless `--force` is passed. Prefer re-running with `--force` over hand-editing target files when iterating on a skill or hook.

## Architecture: five components of the "harness"

Work in this repo is organized around a unified model (see `docs/29-harness-engineering.md`). Changes to one component usually require touching siblings:

1. **settings.json / settings.local.json** — user vs project scope; hooks are registered here
2. **Hooks** (`hooks/`) — boilerplates vs reference scripts (see next section)
3. **CLAUDE.md / rules** — the `.claude/rules/*.md` files are loaded as context
4. **Skills** (`skills/`) — slash commands; each is a `SKILL.md` with frontmatter + optional `references/`
5. **Memory** (`MEMORY.md` + `memory/*.md`) — persistent cross-session facts

When designing a new feature, ask "which of the five does this live in?" before writing. A policy that belongs in a hook should not become a CLAUDE.md rule (and vice versa).

## Hooks directory has TWO meanings — do not confuse

- `hooks/boilerplates/*.sh` — **user-facing templates** shipped by `install-hooks.sh`. Each contains a `🔧 커스터마이징 영역` block. Edit here to change what ships to new projects.
- `hooks/scripts/*.sh` — **reference implementation** for the team system (v3.2). Installed under `~/.claude/team/hooks/scripts/` by `--team`. Do not edit these for project-level customization.

**This repo's own active hooks** are registered in `.claude/settings.local.json` (gitignored) pointing *directly* to `hooks/boilerplates/{guard-agent,audit-agent}.sh`. Downstream projects that run `install-hooks.sh` get a per-project copy at `.claude/hooks/<hook>.sh` (intended fork point for CUSTOMIZE blocks) — this repo bypasses that copy layer because it doesn't customize the hooks, keeping `hooks/boilerplates/` as the SSOT.

Changing one does not change the others.

## PDARR + preset system (what the skills encode)

- **Flow**: `/dispatch` → `/prd` → `/analyze` → `/spec` → `/run` → `/check-code` → `/reflect` → `/complete` → `/stage`
- **2-axis presets** on `analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`:
  - depth: `--quick` / standard / `--thorough`
  - execution: single (default) / `--team`
  - `--team` used alone implies `--thorough`
- Complexity tiers (Trivial / Simple / Medium / Complex) in `/dispatch` drive which subset of the flow runs. Keep these tier names consistent across skills and docs — `/dispatch` and `.claude/rules/subagent-strategy.md` both reference them.

## CUSTOMIZE blocks in skills

Skills are intentionally stack-agnostic except inside `<!-- CUSTOMIZE: ... -->` HTML comments. The default examples are PHP/MySQL. When editing a skill:

- Keep the CUSTOMIZE block boundaries intact — installer users rely on them as hand-off points.
- Do not hard-code project paths (`docs/prd/`, `docs/spec/`, etc. are conventions enforced by `templates/project-structure/`).
- `dispatch`, `flow`, `stage`, `reflect`, `complete`, `organize-docs`, `workflow`, `prd` are stack-independent and should stay that way.

## Subagent use inside this repo

`.claude/rules/subagent-strategy.md` is binding for work in this repo. Key points:

- Each subagent call costs ~14k tokens of fixed overhead. For ≤2-file or ≤20-line changes, the main agent does it directly.
- Use `scripts/preflight-collect.sh` to build a context packet and inline it into the subagent prompt rather than letting the subagent explore.
- Same file, parallel subagents: never. Run sequentially or combine the work.

## Design mode (`.claude/rules/design-mode.md`)

- Default is **SYSTEMATIC**: use existing tokens (`--primary`, `--text-*`, `--space-*`), reuse components, no `frontend-design` skill auto-trigger.
- **CREATIVE** mode only on explicit user signal ("새 디자인", "랜딩페이지", "프로토타입"). Any creative output must be token-mapped afterward; new tokens require a Design System Extension Spec.

## Versioning

The team system version is set in **two places** and `validate-system.sh` checks they match:

- `agents.yaml` → `version: "3.2"`
- Prompts under `prompts/` must contain the 6 required sections (`## Opening`, `## Working Mode`, `## Focus On`, `## Quality Checks`, `## Return`, `## Boundary`)

When bumping the version, update both, then re-run `validate-system.sh` with 0 errors expected.

## Language

All docs, prompts, skills, and comments are written in **Korean** (user-facing) with English technical terms inline. Keep new content consistent with this convention.
