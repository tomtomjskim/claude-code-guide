#!/bin/bash
# Multi-Agent Team System v3.2 Validation Script
# 시스템 일관성 검증 (읽기 전용)

set -e

PROMPTS_DIR="$HOME/.claude/team/prompts"
AGENTS_DIR="$HOME/.claude/agents"
WORKFLOWS_DIR="$HOME/.claude/team/workflows"
HOOKS_DIR="$HOME/.claude/team/hooks"
AGENTS_YAML="$HOME/.claude/team/agents.yaml"

ERRORS=0
WARNINGS=0

HOOKS_SCRIPTS_DIR="$HOME/.claude/team/hooks/scripts"
SETTINGS_JSON="$HOME/.claude/settings.json"
SESSION_SCHEMA="$HOME/.claude/team/context/session-state-schema.yaml"

echo "=== Multi-Agent Team System v3.2 Validation ==="
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

# 2. Check all agents have v3.0 Template and Boundary sections
echo ""
echo "--- 2. Subagent Definition Files ---"
for agent in "$AGENTS_DIR"/*.md; do
    filename=$(basename "$agent")
    if ! grep -q "## v3.0 Template" "$agent" 2>/dev/null; then
        echo "ERROR: $filename missing '## v3.0 Template'"
        ERRORS=$((ERRORS + 1))
    fi
    if ! grep -q "## Boundary" "$agent" 2>/dev/null; then
        echo "ERROR: $filename missing '## Boundary'"
        ERRORS=$((ERRORS + 1))
    fi
done
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
# isolation: worktree on developer and qa-engineer
for agent_name in developer qa-engineer; do
    if ! grep -q "^isolation:" "$AGENTS_DIR/$agent_name.md" 2>/dev/null; then
        echo "WARNING: $agent_name.md missing 'isolation: worktree'"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# memory: project on key reviewers
for agent_name in security-reviewer performance-reviewer test-coverage-reviewer code-reviewer; do
    if ! grep -q "^memory:" "$AGENTS_DIR/$agent_name.md" 2>/dev/null; then
        echo "WARNING: $agent_name.md missing 'memory: project'"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# disallowedTools on explorer
if ! grep -q "^disallowedTools:" "$AGENTS_DIR/explorer.md" 2>/dev/null; then
    echo "WARNING: explorer.md missing 'disallowedTools'"
    WARNINGS=$((WARNINGS + 1))
fi
echo "  Checked selective fields (isolation, memory, disallowedTools)"

# 3. Check agents.yaml version and key sections
echo ""
echo "--- 3. agents.yaml Configuration ---"
if grep -q 'version: "3.2"' "$AGENTS_YAML" 2>/dev/null; then
    echo "  Version: 3.2 ✓"
else
    echo "ERROR: agents.yaml version is not 3.2"
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
CONTEXT_DIR="$HOME/.claude/team/context"
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
REVIEWER_PROMPTS=("security-reviewer" "performance-reviewer" "test-coverage-reviewer" "accessibility-reviewer" "ux-reviewer" "api-reviewer" "code-reviewer" "qa")
CONF_COUNT=0
for reviewer in "${REVIEWER_PROMPTS[@]}"; do
    if grep -q "신뢰도 점수" "$PROMPTS_DIR/$reviewer.md" 2>/dev/null; then
        CONF_COUNT=$((CONF_COUNT + 1))
    else
        echo "WARNING: $reviewer.md missing confidence scoring"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo "  Confidence scoring: $CONF_COUNT/8 reviewers"

# 9. Check validation terminology consistency
echo ""
echo "--- 9. Validation Terminology (v3.1) ---"
TERM_CHECK=0
TERM_TOTAL=0
for prompt in "$PROMPTS_DIR"/*.md; do
    filename=$(basename "$prompt")
    # Skip pm.md (uses quality gates) and domain-specific prompts
    if [ "$filename" = "pm.md" ] || [ "$filename" = "dba.md" ] || [ "$filename" = "publisher.md" ] || [ "$filename" = "documenter.md" ] || [ "$filename" = "explorer.md" ] || [ "$filename" = "designer.md" ]; then
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
HOOK_SCRIPTS=("safety-careful.sh" "safety-freeze.sh" "event-review-trigger.sh")
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

# Summary
echo ""
echo "=== Validation Summary ==="
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo "  Checks: 18 categories (v3.0: 7 + v3.1: 5 + v3.2: 6)"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ System validation PASSED (v3.2) — no issues"
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  System validation PASSED with $WARNINGS warnings (v3.2)"
else
    echo "❌ System validation FAILED with $ERRORS errors, $WARNINGS warnings"
fi

exit $ERRORS
