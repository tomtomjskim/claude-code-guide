#!/bin/bash
# Multi-Agent Team System Validation Script
# 시스템 일관성 검증 (읽기 전용)

set -e

PROJECT_ROOT=""
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

usage() {
    cat <<'USAGE'
Usage: bash scripts/validate-system.sh [--project <path>] [--claude-home <path>]

Without arguments the validator checks the traditional global installation.
Use --project for project-local skills and settings.local.json.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            PROJECT_ROOT="${2:-}"
            shift 2
            ;;
        --claude-home)
            CLAUDE_HOME="${2:-}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument '$1'" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ -n "$PROJECT_ROOT" ]; then
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo "ERROR: project directory not found: $PROJECT_ROOT" >&2
        exit 2
    fi
    PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
fi

if [ -d "$CLAUDE_HOME" ]; then
    CLAUDE_HOME="$(cd "$CLAUDE_HOME" && pwd)"
else
    CLAUDE_HOME="$(cd "$(dirname "$CLAUDE_HOME")" && pwd)/$(basename "$CLAUDE_HOME")"
fi

PROMPTS_DIR="$CLAUDE_HOME/team/prompts"
AGENTS_DIR="$CLAUDE_HOME/agents"
WORKFLOWS_DIR="$CLAUDE_HOME/team/workflows"
HOOKS_DIR="$CLAUDE_HOME/team/hooks"
AGENTS_YAML="$CLAUDE_HOME/team/agents.yaml"

if [ -n "$PROJECT_ROOT" ]; then
    SKILLS_DIR="$PROJECT_ROOT/.claude/skills"
    if [ -f "$PROJECT_ROOT/.claude/settings.local.json" ]; then
        SETTINGS_JSON="$PROJECT_ROOT/.claude/settings.local.json"
    else
        SETTINGS_JSON="$PROJECT_ROOT/.claude/settings.json"
    fi
else
    SKILLS_DIR="$CLAUDE_HOME/skills"
    SETTINGS_JSON="$CLAUDE_HOME/settings.json"
fi

# v4.0 P1-1: 버전 canonical 중앙화 (strategy.md Decision 1)
# 이 스크립트가 검증하는 team system의 예상 버전. agents.yaml:4의 value와 일치해야 함.
# 버전 bump 시 (1) agents.yaml:4 (2) 아래 EXPECTED_VERSION 두 곳만 동시 업데이트.
EXPECTED_VERSION="3.2"

ERRORS=0
WARNINGS=0

HOOKS_SCRIPTS_DIR="$CLAUDE_HOME/team/hooks/scripts"
SESSION_SCHEMA="$CLAUDE_HOME/team/context/session-state-schema.yaml"

# v4.0 P0-4: agents.yaml을 SSOT로 삼는 동적 에이전트 이름 파싱
# bash grep 기반 — yq 외부 의존 회피 (strategy.md Decision 3)
if [ -f "$AGENTS_YAML" ]; then
    ALL_AGENTS=$(awk '/^agents:$/{in_block=1; next} in_block && /^[a-z_]+:/{in_block=0} in_block && /^  [a-z-]+:$/{gsub(/^  |:$/,""); print}' "$AGENTS_YAML")
    REVIEWERS=$(echo "$ALL_AGENTS" | grep -E -- '-reviewer$' || true)
    # domain_specific = 리뷰어·엔지니어·PM을 제외한 에이전트 (terminology 체크 skip 대상)
    DOMAIN_SPECIFIC=$(echo "$ALL_AGENTS" | grep -vE -- '-reviewer$|^(developer|qa-engineer|architect|pm)$' || true)
else
    ALL_AGENTS=""
    REVIEWERS=""
    DOMAIN_SPECIFIC=""
fi

echo "=== Multi-Agent Team System v$EXPECTED_VERSION Validation ==="
echo ""

# 1. Check all 16 prompts have 6 required sections
echo "--- 1. Prompt Template Sections ---"
REQUIRED_SECTIONS=("## Opening" "## Working Mode" "## Focus On" "## Quality Checks" "## Return" "## Boundary")
for prompt in "$PROMPTS_DIR"/*.md; do
    filename=$(basename "$prompt")
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if ! grep -q "$section" "$prompt" 2>/dev/null; then
            echo "ERROR: $filename missing '$section'"
            ERRORS=$((ERRORS + 1))
        fi
    done
done
PROMPT_COUNT=$(ls -1 "$PROMPTS_DIR"/*.md 2>/dev/null | wc -l)
echo "  Checked $PROMPT_COUNT prompts for 6 sections"

# 2. Check all agents have ## Template and ## Boundary sections
echo ""
echo "--- 2. Subagent Definition Files ---"
for agent in "$AGENTS_DIR"/*.md; do
    filename=$(basename "$agent")
    if ! grep -q "^## Template$" "$agent" 2>/dev/null; then
        echo "ERROR: $filename missing '## Template'"
        ERRORS=$((ERRORS + 1))
    fi
    if ! grep -q "## Boundary" "$agent" 2>/dev/null; then
        echo "ERROR: $filename missing '## Boundary'"
        ERRORS=$((ERRORS + 1))
    fi
done
# v4.0 P0-1: agents.yaml 선언 ↔ agents/*.md 파일 매칭
if [ -n "$ALL_AGENTS" ]; then
    for agent_name in $ALL_AGENTS; do
        if [ ! -f "$AGENTS_DIR/$agent_name.md" ]; then
            echo "ERROR: agents.yaml declares '$agent_name' but $agent_name.md not found"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi
AGENT_COUNT=$(ls -1 "$AGENTS_DIR"/*.md 2>/dev/null | wc -l)
echo "  Checked $AGENT_COUNT agent definitions"

# 2b. Check v3.1 frontmatter fields (effort, color, maxTurns)
echo ""
echo "--- 2b. Agent Frontmatter v3.1 Fields ---"
V31_FIELDS=("effort:" "color:" "maxTurns:")
for agent in "$AGENTS_DIR"/*.md; do
    filename=$(basename "$agent")
    for field in "${V31_FIELDS[@]}"; do
        if ! grep -q "^$field" "$agent" 2>/dev/null; then
            echo "WARNING: $filename missing frontmatter '$field'"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
done
echo "  Checked $AGENT_COUNT agents for v3.1 frontmatter"

# 2c. Check selective fields
echo ""
echo "--- 2c. Selective Agent Fields ---"
# 선택 검증: isolation은 파일 수정권을 가진 developer·qa-engineer 에이전트에만 요구되는 설계 정책 (drift 재생산 엔진 아님, 하드코딩 유지)
# isolation: worktree on developer and qa-engineer
for agent_name in developer qa-engineer; do
    if ! grep -q "^isolation:" "$AGENTS_DIR/$agent_name.md" 2>/dev/null; then
        echo "WARNING: $agent_name.md missing 'isolation: worktree'"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 선택 검증: memory: project는 장기 컨텍스트 축적이 필요한 핵심 리뷰어 4종에만 요구되는 설계 정책 (하드코딩 유지)
# memory: project on key reviewers
for agent_name in security-reviewer performance-reviewer test-coverage-reviewer code-reviewer; do
    if ! grep -q "^memory:" "$AGENTS_DIR/$agent_name.md" 2>/dev/null; then
        echo "WARNING: $agent_name.md missing 'memory: project'"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 선택 검증: disallowedTools는 탐색 전용 explorer에만 요구되는 설계 정책 (하드코딩 유지)
# disallowedTools on explorer
if ! grep -q "^disallowedTools:" "$AGENTS_DIR/explorer.md" 2>/dev/null; then
    echo "WARNING: explorer.md missing 'disallowedTools'"
    WARNINGS=$((WARNINGS + 1))
fi
echo "  Checked selective fields (isolation, memory, disallowedTools)"

# 3. Check agents.yaml version and key sections
echo ""
echo "--- 3. agents.yaml Configuration ---"
if grep -q "version: \"$EXPECTED_VERSION\"" "$AGENTS_YAML" 2>/dev/null; then
    echo "  Version: $EXPECTED_VERSION ✓"
else
    echo "ERROR: agents.yaml version is not $EXPECTED_VERSION"
    ERRORS=$((ERRORS + 1))
fi

# Check handoff_protocol exists
if grep -q 'handoff_protocol:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Handoff protocol: present ✓"
else
    echo "ERROR: agents.yaml missing handoff_protocol section"
    ERRORS=$((ERRORS + 1))
fi

# Check model_routing exists
if grep -q 'model_routing:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Model routing: present ✓"
else
    echo "ERROR: agents.yaml missing model_routing section"
    ERRORS=$((ERRORS + 1))
fi

# 3b. Check v3.1 additions in agents.yaml
echo ""
echo "--- 3b. agents.yaml v3.1 Additions ---"

# Check routing thresholds
THRESHOLD_COUNT=$(grep -c 'threshold:' "$AGENTS_YAML" 2>/dev/null || echo 0)
if [ "$THRESHOLD_COUNT" -ge 6 ]; then
    echo "  Routing thresholds: $THRESHOLD_COUNT ✓"
else
    echo "WARNING: Expected 6+ routing thresholds, found $THRESHOLD_COUNT"
    WARNINGS=$((WARNINGS + 1))
fi

# Check conflict_resolution
if grep -q 'conflict_resolution:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Conflict resolution: present ✓"
else
    echo "WARNING: agents.yaml missing conflict_resolution"
    WARNINGS=$((WARNINGS + 1))
fi

# Check token_budget
if grep -q 'token_budget:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Token budget: present ✓"
else
    echo "WARNING: agents.yaml missing token_budget section"
    WARNINGS=$((WARNINGS + 1))
fi

# Check circuit_breaker
if grep -q 'circuit_breaker:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Circuit breaker: present ✓"
else
    echo "WARNING: agents.yaml missing circuit_breaker section"
    WARNINGS=$((WARNINGS + 1))
fi

# Check all agents have handoff block
echo ""
echo "--- 4. Agent Handoff Fields ---"
AGENTS_WITH_HANDOFF=$(grep -c 'handoff:' "$AGENTS_YAML" 2>/dev/null || echo 0)
echo "  Agents with handoff block: $AGENTS_WITH_HANDOFF"
if [ "$AGENTS_WITH_HANDOFF" -lt 10 ]; then
    echo "WARNING: Expected 16+ handoff blocks, found $AGENTS_WITH_HANDOFF"
    WARNINGS=$((WARNINGS + 1))
fi

# 5. Check all workflows have failure_policy reference
echo ""
echo "--- 5. Workflow Failure Policy ---"
for workflow in "$WORKFLOWS_DIR"/*.yaml; do
    filename=$(basename "$workflow")
    if [ "$filename" = "failure-policy.yaml" ]; then continue; fi
    if ! grep -q 'failure_policy:' "$workflow" 2>/dev/null; then
        echo "ERROR: $filename missing failure_policy reference"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check failure-policy.yaml exists
if [ -f "$WORKFLOWS_DIR/failure-policy.yaml" ]; then
    echo "  failure-policy.yaml: exists ✓"
else
    echo "ERROR: failure-policy.yaml not found"
    ERRORS=$((ERRORS + 1))
fi

# 6. Check handoff-protocol.md exists
echo ""
echo "--- 6. Handoff Protocol ---"
CONTEXT_DIR="$CLAUDE_HOME/team/context"
if [ -f "$CONTEXT_DIR/handoff-protocol.md" ]; then
    echo "  handoff-protocol.md: exists ✓"
else
    echo "ERROR: handoff-protocol.md not found"
    ERRORS=$((ERRORS + 1))
fi

# 7. Check PM prompt has key sections
echo ""
echo "--- 7. PM Prompt Key Sections ---"
PM_PROMPT="$PROMPTS_DIR/pm.md"
PM_SECTIONS=("## Context Passing" "## Failure Handling" "## Tiebreaker Protocol" "## Model Routing" "## Adaptive Workflow Selection" "## Event-Driven Review Integration")
for section in "${PM_SECTIONS[@]}"; do
    if grep -q "$section" "$PM_PROMPT" 2>/dev/null; then
        echo "  $section ✓"
    else
        echo "ERROR: pm.md missing '$section'"
        ERRORS=$((ERRORS + 1))
    fi
done

# 8. Check Confidence Scoring in reviewers
echo ""
echo "--- 8. Confidence Scoring (v3.1) ---"
# v4.0 P0-4: REVIEWERS($AGENTS_YAML에서 동적 추출) + qa-engineer(P0-5 rename 후 정식명)
REVIEWER_PROMPTS=()
while IFS= read -r r; do
    [ -n "$r" ] && REVIEWER_PROMPTS+=("$r")
done <<< "$REVIEWERS"
REVIEWER_PROMPTS+=("qa-engineer")
CONF_COUNT=0
for reviewer in "${REVIEWER_PROMPTS[@]}"; do
    if grep -q "신뢰도 점수" "$PROMPTS_DIR/$reviewer.md" 2>/dev/null; then
        CONF_COUNT=$((CONF_COUNT + 1))
    else
        echo "WARNING: $reviewer.md missing confidence scoring"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo "  Confidence scoring: $CONF_COUNT/${#REVIEWER_PROMPTS[@]} reviewers"

# 9. Check validation terminology consistency
echo ""
echo "--- 9. Validation Terminology (v3.1) ---"
TERM_CHECK=0
TERM_TOTAL=0
for prompt in "$PROMPTS_DIR"/*.md; do
    filename=$(basename "$prompt")
    # Skip pm.md (uses quality gates) and domain-specific prompts
    # v4.0 P0-4: DOMAIN_SPECIFIC(agents.yaml 동적 추출) + pm(orchestrator, 별도 skip)
    skip=0
    case "$filename" in
        pm.md) skip=1 ;;
    esac
    if [ "$skip" = "0" ]; then
        for ds in $DOMAIN_SPECIFIC; do
            if [ "$filename" = "${ds}.md" ]; then
                skip=1
                break
            fi
        done
    fi
    if [ "$skip" = "1" ]; then
        continue
    fi
    TERM_TOTAL=$((TERM_TOTAL + 1))
    if grep -q "경계 조건(boundary condition)" "$prompt" 2>/dev/null; then
        TERM_CHECK=$((TERM_CHECK + 1))
    else
        echo "WARNING: $filename uses non-standard validation terminology"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo "  Standard terminology: $TERM_CHECK/$TERM_TOTAL prompts"

# 10. Check Event-Driven Hooks (v3.1)
echo ""
echo "--- 10. Event-Driven Hooks (v3.1) ---"
if [ -f "$HOOKS_DIR/event-driven-review.yaml" ]; then
    echo "  event-driven-review.yaml: exists ✓"
    # Validate YAML
    if python3 -c "import yaml; yaml.safe_load(open('$HOOKS_DIR/event-driven-review.yaml'))" 2>/dev/null; then
        echo "  YAML syntax: valid ✓"
    else
        echo "ERROR: event-driven-review.yaml has invalid YAML"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "WARNING: event-driven-review.yaml not found"
    WARNINGS=$((WARNINGS + 1))
fi

# 11. Check Progressive Escalation (v3.1)
echo ""
echo "--- 11. Progressive Escalation (v3.1) ---"
CODE_REVIEW="$WORKFLOWS_DIR/code-review.yaml"
if grep -q 'escalation:' "$CODE_REVIEW" 2>/dev/null; then
    echo "  Escalation rules: present ✓"
else
    echo "WARNING: code-review.yaml missing escalation section"
    WARNINGS=$((WARNINGS + 1))
fi
if grep -q 'quick_to_standard:' "$CODE_REVIEW" 2>/dev/null; then
    echo "  quick→standard rules: present ✓"
else
    echo "WARNING: code-review.yaml missing quick_to_standard rules"
    WARNINGS=$((WARNINGS + 1))
fi
if grep -q 'standard_to_thorough:' "$CODE_REVIEW" 2>/dev/null; then
    echo "  standard→thorough rules: present ✓"
else
    echo "WARNING: code-review.yaml missing standard_to_thorough rules"
    WARNINGS=$((WARNINGS + 1))
fi

# 12. YAML Validation (all config files)
echo ""
echo "--- 12. YAML Syntax Validation ---"
YAML_FILES=("$AGENTS_YAML" "$CODE_REVIEW" "$WORKFLOWS_DIR/failure-policy.yaml" "$WORKFLOWS_DIR/standard.yaml")
for yf in "${YAML_FILES[@]}"; do
    fname=$(basename "$yf")
    if [ -f "$yf" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('$yf'))" 2>/dev/null; then
            echo "  $fname: valid ✓"
        else
            echo "ERROR: $fname has invalid YAML"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# 13. v3.2: Safety Hook Scripts
echo ""
echo "--- 13. Safety Hook Scripts (v3.2) ---"
HOOK_SCRIPTS=("safety-careful.reference.sh" "safety-freeze.reference.sh" "event-review-trigger.reference.sh")
for script in "${HOOK_SCRIPTS[@]}"; do
    if [ -f "$HOOKS_SCRIPTS_DIR/$script" ]; then
        if [ -x "$HOOKS_SCRIPTS_DIR/$script" ]; then
            echo "  $script: exists + executable ✓"
        else
            echo "WARNING: $script exists but not executable"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "ERROR: $script not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# 14. v3.2: settings.json Hooks Registration
echo ""
echo "--- 14. settings.json Hooks (v3.2) ---"
if [ -f "$SETTINGS_JSON" ]; then
    HOOK_COUNT=$(python3 -c "
import json
with open('$SETTINGS_JSON') as f:
    d = json.load(f)
hooks = d.get('hooks', {})
pre = len(hooks.get('PreToolUse', []))
post = len(hooks.get('PostToolUse', []))
print(f'{pre + post}')
" 2>/dev/null || echo "0")
    if [ "$HOOK_COUNT" -ge 3 ]; then
        echo "  Registered hooks: $HOOK_COUNT ✓"
    else
        echo "WARNING: Expected 3+ hooks, found $HOOK_COUNT"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "ERROR: settings.json not found"
    ERRORS=$((ERRORS + 1))
fi

# 15. v3.2: Completion Status in Handoff Protocol
echo ""
echo "--- 15. Handoff Protocol v2.0 (v3.2) ---"
HANDOFF_FILE="$CONTEXT_DIR/handoff-protocol.md"
if grep -q 'completion_status:' "$HANDOFF_FILE" 2>/dev/null; then
    echo "  completion_status field: present ✓"
else
    echo "ERROR: handoff-protocol.md missing completion_status"
    ERRORS=$((ERRORS + 1))
fi
if grep -q 'Protocol v2.0' "$HANDOFF_FILE" 2>/dev/null; then
    echo "  Protocol version: v2.0 ✓"
else
    echo "WARNING: handoff-protocol.md not v2.0"
    WARNINGS=$((WARNINGS + 1))
fi

# 16. v3.2: Blast-Radius + Autonomy Levels in agents.yaml
echo ""
echo "--- 16. Blast-Radius & Autonomy (v3.2) ---"
if grep -q 'blast_radius:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Blast-radius config: present ✓"
else
    echo "WARNING: agents.yaml missing blast_radius section"
    WARNINGS=$((WARNINGS + 1))
fi
if grep -q 'autonomy_levels:' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Autonomy levels: present ✓"
else
    echo "WARNING: agents.yaml missing autonomy_levels section"
    WARNINGS=$((WARNINGS + 1))
fi

# 17. v3.2: Phase 0 in code-review.yaml
echo ""
echo "--- 17. Code Review Phase 0 (v3.2) ---"
if grep -q 'diff_analysis:' "$CODE_REVIEW" 2>/dev/null; then
    echo "  Phase 0 diff_analysis: present ✓"
else
    echo "WARNING: code-review.yaml missing Phase 0 diff_analysis"
    WARNINGS=$((WARNINGS + 1))
fi

# 18. v3.2: Session State Schema
echo ""
echo "--- 18. Session State Schema (v3.2) ---"
if [ -f "$SESSION_SCHEMA" ]; then
    echo "  session-state-schema.yaml: exists ✓"
    if python3 -c "import yaml; yaml.safe_load(open('$SESSION_SCHEMA'))" 2>/dev/null; then
        echo "  YAML syntax: valid ✓"
    else
        echo "ERROR: session-state-schema.yaml has invalid YAML"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "WARNING: session-state-schema.yaml not found"
    WARNINGS=$((WARNINGS + 1))
fi

# 19. Preset canonical marker check (v4.0 P1-2)
# 6 스킬의 SKILL.md에 canonical 링크 마커 존재 + 2축 테이블 중복 선언 부재 확인
echo ""
echo "--- 19. Preset canonical markers (6 skills) ---"
PRESET_SKILLS=("analyze" "spec" "check-spec" "check-code" "qa-test" "qa-e2e")
PRESET_MARKER="<!-- PRESET_CANONICAL_LINK -->"
MISSING_MARKERS=0
DUPLICATE_TABLES=0

for skill in "${PRESET_SKILLS[@]}"; do
    skill_file="$SKILLS_DIR/$skill/SKILL.md"
    if [ ! -f "$skill_file" ]; then
        echo "  WARNING: $skill/SKILL.md not found (skipping)"
        continue
    fi

    # (a) canonical 마커 존재
    if ! grep -q "$PRESET_MARKER" "$skill_file"; then
        echo "ERROR: $skill/SKILL.md missing preset canonical marker '$PRESET_MARKER'"
        ERRORS=$((ERRORS + 1))
        MISSING_MARKERS=$((MISSING_MARKERS + 1))
    fi

    # (b) 중복 2축 테이블 선언 탐지 — `| ... --quick ... standard ... --thorough ... |` 헤더 패턴
    # qa-test의 alias 매핑 테이블은 헤더가 `| 4단계 라벨 | 2축 alias | 범위 |`로 다르므로 매칭 안됨
    if grep -qE '^\|[^|]*--quick[^|]*\|[^|]*standard[^|]*\|[^|]*--thorough[^|]*\|[[:space:]]*$' "$skill_file"; then
        echo "WARNING: $skill/SKILL.md contains 2-axis depth table — canonical duplication (should link only)"
        WARNINGS=$((WARNINGS + 1))
        DUPLICATE_TABLES=$((DUPLICATE_TABLES + 1))
    fi
done

echo "  Preset canonical markers: $((${#PRESET_SKILLS[@]} - MISSING_MARKERS))/${#PRESET_SKILLS[@]} skills"
if [ "$DUPLICATE_TABLES" -gt 0 ]; then
    echo "  Duplicate 2-axis tables detected: $DUPLICATE_TABLES"
fi

# Summary
echo ""
echo "=== Validation Summary ==="
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo "  Checks: 19 categories (v3.0: 7 + v3.1: 5 + v3.2: 6 + v4.0: 1)"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ System validation PASSED (v$EXPECTED_VERSION) — no issues"
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  System validation PASSED with $WARNINGS warnings (v$EXPECTED_VERSION)"
else
    echo "❌ System validation FAILED with $ERRORS errors, $WARNINGS warnings"
fi

exit $ERRORS
