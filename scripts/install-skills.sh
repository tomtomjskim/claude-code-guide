#!/bin/bash
# PDARR Workflow Skills Installer v1.0
# Usage: bash scripts/install-skills.sh [target-project-path]
#
# Installs PDARR workflow skills into a Claude Code project.
# Skills are copied to <target>/.claude/skills/
# Existing skills with the same name are NOT overwritten (use --force to override).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC="$REPO_DIR/skills"

# --- Parse arguments ---
FORCE=false
TARGET=""
SELECTED_SKILLS=()
INSTALL_TEAM=false

print_usage() {
    echo "Usage: bash scripts/install-skills.sh [options] <target-project-path>"
    echo ""
    echo "Options:"
    echo "  --force           Overwrite existing skills"
    echo "  --skills <list>   Install specific skills only (comma-separated)"
    echo "                    e.g., --skills dispatch,run,check-code"
    echo "  --team            Also install team system (agents, prompts, workflows, hooks)"
    echo "  --list            List available skills and exit"
    echo "  --help            Show this help"
    echo ""
    echo "Examples:"
    echo "  bash scripts/install-skills.sh /path/to/my-project"
    echo "  bash scripts/install-skills.sh --skills dispatch,run,stage /path/to/my-project"
    echo "  bash scripts/install-skills.sh --team /path/to/my-project"
    echo "  bash scripts/install-skills.sh --force /path/to/my-project"
}

list_skills() {
    echo "=== Available PDARR Workflow Skills ==="
    echo ""
    echo "[PLAN]"
    echo "  dispatch      Smart router - routes tasks by complexity"
    echo "  prd           PRD (Product Requirements Document) creation"
    echo "  analyze       Codebase analysis + execution strategy"
    echo "  spec          Technical specification writing"
    echo ""
    echo "[ACT]"
    echo "  test          TDD test case writing"
    echo "  run           Implementation (Orchestrator-Worker pattern)"
    echo ""
    echo "[REVIEW]"
    echo "  check-spec    Spec document review"
    echo "  check-code    Code quality review (6-stage system)"
    echo "  qa-test       Automated QA testing"
    echo "  qa-e2e        E2E business logic testing"
    echo ""
    echo "[REFLECT]"
    echo "  reflect       Self-reflection + memory storage"
    echo "  complete      Work completion + docs/complete/ integration"
    echo ""
    echo "[UTILITY]"
    echo "  stage         Git staging + commit message suggestion"
    echo "  flow          Session context summary"
    echo "  organize-docs Documentation catch-up"
    echo "  workflow      Full PDARR orchestrator"
    echo "  profile       Performance profiling"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --skills)
            IFS=',' read -ra SELECTED_SKILLS <<< "$2"
            shift 2
            ;;
        --team)
            INSTALL_TEAM=true
            shift
            ;;
        --list)
            list_skills
            exit 0
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

if [ -z "$TARGET" ]; then
    print_usage
    exit 1
fi

# --- Validate ---
if [ ! -d "$SKILLS_SRC" ]; then
    echo "ERROR: Skills directory not found at $SKILLS_SRC"
    echo "       Make sure you're running from the claude-code-guide repo root."
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo "ERROR: Target directory '$TARGET' does not exist."
    exit 1
fi

TARGET_SKILLS="$TARGET/.claude/skills"

# --- Install skills ---
echo "=== PDARR Workflow Skills Installer ==="
echo ""
echo "Source:  $SKILLS_SRC"
echo "Target:  $TARGET_SKILLS"
echo "Force:   $FORCE"
echo ""

mkdir -p "$TARGET_SKILLS"

INSTALLED=0
SKIPPED=0
OVERWRITTEN=0

# Get list of skills to install
if [ ${#SELECTED_SKILLS[@]} -eq 0 ]; then
    SKILL_DIRS=($(ls -d "$SKILLS_SRC"/*/))
else
    SKILL_DIRS=()
    for s in "${SELECTED_SKILLS[@]}"; do
        if [ -d "$SKILLS_SRC/$s" ]; then
            SKILL_DIRS+=("$SKILLS_SRC/$s/")
        else
            echo "WARNING: Skill '$s' not found, skipping."
        fi
    done
fi

for skill_dir in "${SKILL_DIRS[@]}"; do
    skill_name=$(basename "$skill_dir")
    target_dir="$TARGET_SKILLS/$skill_name"

    if [ -d "$target_dir" ] && [ "$FORCE" = false ]; then
        echo "  SKIP  $skill_name (already exists, use --force to overwrite)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    if [ -d "$target_dir" ] && [ "$FORCE" = true ]; then
        rm -rf "$target_dir"
        OVERWRITTEN=$((OVERWRITTEN + 1))
    fi

    cp -r "$skill_dir" "$target_dir"
    echo "  OK    $skill_name"
    INSTALLED=$((INSTALLED + 1))
done

# --- Install team system (optional) ---
if [ "$INSTALL_TEAM" = true ]; then
    echo ""
    echo "--- Installing Team System ---"

    TEAM_DIR="$HOME/.claude/team"
    AGENTS_DST="$HOME/.claude/agents"

    mkdir -p "$TEAM_DIR"/{prompts,workflows,context,hooks/scripts,scripts}
    mkdir -p "$AGENTS_DST"

    # Copy team components
    [ -f "$REPO_DIR/agents.yaml" ] && cp "$REPO_DIR/agents.yaml" "$TEAM_DIR/" && echo "  OK    agents.yaml"
    [ -d "$REPO_DIR/prompts" ] && cp -r "$REPO_DIR/prompts/"*.md "$TEAM_DIR/prompts/" 2>/dev/null && echo "  OK    prompts/ ($(ls -1 "$REPO_DIR/prompts/"*.md | wc -l) files)"
    [ -d "$REPO_DIR/workflows" ] && cp -r "$REPO_DIR/workflows/"*.yaml "$TEAM_DIR/workflows/" 2>/dev/null && echo "  OK    workflows/ ($(ls -1 "$REPO_DIR/workflows/"*.yaml | wc -l) files)"
    [ -d "$REPO_DIR/context" ] && cp -r "$REPO_DIR/context/"* "$TEAM_DIR/context/" 2>/dev/null && echo "  OK    context/"
    [ -d "$REPO_DIR/hooks" ] && cp -r "$REPO_DIR/hooks/"* "$TEAM_DIR/hooks/" 2>/dev/null && echo "  OK    hooks/"
    [ -d "$REPO_DIR/agents" ] && cp -r "$REPO_DIR/agents/"*.md "$AGENTS_DST/" 2>/dev/null && echo "  OK    agents/ ($(ls -1 "$REPO_DIR/agents/"*.md | wc -l) files)"
    [ -d "$REPO_DIR/scripts" ] && cp "$REPO_DIR/scripts/"*.sh "$TEAM_DIR/scripts/" 2>/dev/null && echo "  OK    scripts/"

    # Set executable permissions
    chmod +x "$TEAM_DIR/hooks/scripts/"*.sh 2>/dev/null
    chmod +x "$TEAM_DIR/scripts/"*.sh 2>/dev/null

    echo ""
    echo "Team system installed to ~/.claude/team/"
    echo "Run 'bash ~/.claude/team/scripts/validate-system.sh' to verify."
fi

# --- Summary ---
echo ""
echo "=== Summary ==="
echo "  Installed:   $INSTALLED"
[ $OVERWRITTEN -gt 0 ] && echo "  Overwritten: $OVERWRITTEN"
[ $SKIPPED -gt 0 ] && echo "  Skipped:     $SKIPPED"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo "Skills are now available in your project."
    echo "Try: /dispatch, /run, /check-code, /stage"
    echo ""
    echo "Next steps:"
    echo "  1. Review CUSTOMIZE blocks in each SKILL.md for your tech stack"
    echo "  2. Edit skills to match your project conventions"
    echo "  3. See: skills/README.md for customization guide"
fi
