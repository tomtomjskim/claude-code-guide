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
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

prepare_project_directory() {
    local path="$1"
    local resolved
    case "$path" in
        "$TARGET/.claude"|"$TARGET/.claude/"*) ;;
        *)
            echo "ERROR: project install path escapes target: $path" >&2
            exit 1
            ;;
    esac
    if [ -L "$path" ]; then
        echo "ERROR: project install path must not be a symlink: $path" >&2
        exit 1
    fi
    if [ -e "$path" ] && [ ! -d "$path" ]; then
        echo "ERROR: project install path must be a directory: $path" >&2
        exit 1
    fi
    mkdir -p "$path"
    resolved="$(cd "$path" && pwd -P)"
    case "$resolved" in
        "$TARGET/.claude"|"$TARGET/.claude/"*) ;;
        *)
            echo "ERROR: project install path resolves outside target: $path" >&2
            exit 1
            ;;
    esac
}

publish_managed_file() {
    local scope="$1"
    local relative="$2"
    local source="$3"
    python3 "$SCRIPT_DIR/install_state.py" publish \
        --target "$TARGET" \
        --claude-home "$CLAUDE_HOME" \
        --snapshot "$CLAUDE_CODE_GUIDE_TRANSACTION" \
        --scope "$scope" \
        --path "$relative" \
        --source "$source"
}

publish_managed_tree() {
    local scope="$1"
    local source_root="$2"
    local destination_prefix="$3"
    local source relative
    while IFS= read -r -d '' source; do
        relative="${source#"$source_root"/}"
        publish_managed_file \
            "$scope" \
            "$destination_prefix/$relative" \
            "$source"
    done < <(find "$source_root" -type f -print0 | sort -z)
}

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
    echo "  --team            Also install team system; agents go through ~/.agents/adapters/claude symlinks"
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
    echo "  breakdown     PRD → feature breakdown + Goal execution order"
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
    echo "  design-creative CREATIVE mode design (landing/prototype)"
    echo "  setup-wizard  Auto-install claude-code-guide (profile-aware)"
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

if [ -L "$TARGET" ]; then
    echo "ERROR: Target directory must not be a symlink: $TARGET" >&2
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo "ERROR: Target directory '$TARGET' does not exist." >&2
    exit 1
fi

TARGET="$(cd "$TARGET" && pwd -P)"

TARGET_SKILLS="$TARGET/.claude/skills"
prepare_project_directory "$TARGET/.claude"
prepare_project_directory "$TARGET_SKILLS"

# --- Install skills ---
echo "=== PDARR Workflow Skills Installer ==="
echo ""
echo "Source:  $SKILLS_SRC"
echo "Target:  $TARGET_SKILLS"
echo "Force:   $FORCE"
echo ""

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

    if [ -L "$target_dir" ]; then
        echo "ERROR: skill destination must not be a symlink: $target_dir" >&2
        exit 1
    fi
    if [ -e "$target_dir" ] && [ ! -d "$target_dir" ]; then
        echo "ERROR: skill destination must be a directory: $target_dir" >&2
        exit 1
    fi

    if [ -d "$target_dir" ] && [ "$FORCE" = false ]; then
        echo "  SKIP  $skill_name (already exists, use --force to overwrite)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    if [ -d "$target_dir" ] && [ "$FORCE" = true ]; then
        OVERWRITTEN=$((OVERWRITTEN + 1))
    fi

    if [ -n "${CLAUDE_CODE_GUIDE_TRANSACTION:-}" ]; then
        publish_managed_tree \
            project \
            "${skill_dir%/}" \
            "skills/$skill_name"
    else
        mkdir -p "$target_dir"
        cp -R "$skill_dir". "$target_dir"/
    fi
    echo "  OK    $skill_name"
    INSTALLED=$((INSTALLED + 1))
done

# --- Install team system (optional) ---
if [ "$INSTALL_TEAM" = true ]; then
    echo ""
    echo "--- Installing Team System ---"

    TEAM_DIR="$CLAUDE_HOME/team"
    TEAM_AGENTS_DIR="$TEAM_DIR/agents"
    SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.agents}"
    SHARED_CLAUDE_ADAPTERS="$SHARED_AGENTS_HOME/adapters/claude"
    AGENTS_DST="$CLAUDE_HOME/agents"

    mkdir -p "$TEAM_DIR"/{agents,prompts,workflows,context,hooks/scripts,scripts}

    # Copy team components
    if [ -n "${CLAUDE_CODE_GUIDE_TRANSACTION:-}" ]; then
        [ -f "$REPO_DIR/agents.yaml" ] \
            && publish_managed_file claude-home team/agents.yaml "$REPO_DIR/agents.yaml" \
            && echo "  OK    agents.yaml"
        for source in "$REPO_DIR/prompts/"*.md; do
            [ -f "$source" ] && publish_managed_file claude-home "team/prompts/$(basename "$source")" "$source"
        done
        echo "  OK    prompts/"
        for source in "$REPO_DIR/workflows/"*.yaml; do
            [ -f "$source" ] && publish_managed_file claude-home "team/workflows/$(basename "$source")" "$source"
        done
        echo "  OK    workflows/"
        [ -d "$REPO_DIR/context" ] && publish_managed_tree claude-home "$REPO_DIR/context" team/context && echo "  OK    context/"
        [ -d "$REPO_DIR/hooks" ] && publish_managed_tree claude-home "$REPO_DIR/hooks" team/hooks && echo "  OK    hooks/"
        for source in "$REPO_DIR/agents/"*.md; do
            [ -f "$source" ] && publish_managed_file claude-home "team/agents/$(basename "$source")" "$source"
        done
        echo "  OK    team agents/"
        for source in "$REPO_DIR/scripts/"*.sh; do
            [ -f "$source" ] && publish_managed_file claude-home "team/scripts/$(basename "$source")" "$source"
        done
        echo "  OK    scripts/"
    else
        mkdir -p "$SHARED_CLAUDE_ADAPTERS" "$AGENTS_DST"
        [ -f "$REPO_DIR/agents.yaml" ] && cp "$REPO_DIR/agents.yaml" "$TEAM_DIR/" && echo "  OK    agents.yaml"
        [ -d "$REPO_DIR/prompts" ] && cp -r "$REPO_DIR/prompts/"*.md "$TEAM_DIR/prompts/" 2>/dev/null && echo "  OK    prompts/ ($(ls -1 "$REPO_DIR/prompts/"*.md | wc -l) files)"
        [ -d "$REPO_DIR/workflows" ] && cp -r "$REPO_DIR/workflows/"*.yaml "$TEAM_DIR/workflows/" 2>/dev/null && echo "  OK    workflows/ ($(ls -1 "$REPO_DIR/workflows/"*.yaml | wc -l) files)"
        [ -d "$REPO_DIR/context" ] && cp -r "$REPO_DIR/context/"* "$TEAM_DIR/context/" 2>/dev/null && echo "  OK    context/"
        [ -d "$REPO_DIR/hooks" ] && cp -r "$REPO_DIR/hooks/"* "$TEAM_DIR/hooks/" 2>/dev/null && echo "  OK    hooks/"
        [ -d "$REPO_DIR/agents" ] && cp -r "$REPO_DIR/agents/"*.md "$TEAM_AGENTS_DIR/" 2>/dev/null && echo "  OK    team agents/ ($(ls -1 "$REPO_DIR/agents/"*.md | wc -l) files)"
        if [ -d "$REPO_DIR/agents" ]; then
            AGENT_COUNT=0
            AGENT_SKIPPED=0
            AGENT_BACKUP_DIR="$SHARED_AGENTS_HOME/backups/claude-team-agents-$(date +%Y%m%d-%H%M%S)"

            for agent_file in "$REPO_DIR/agents/"*.md; do
                [ -f "$agent_file" ] || continue
                agent_name=$(basename "$agent_file")
                adapter_path="$SHARED_CLAUDE_ADAPTERS/$agent_name"
                link_path="$AGENTS_DST/$agent_name"

                if [ "$FORCE" = false ] && {
                    [ -e "$adapter_path" ] || [ -L "$adapter_path" ] \
                        || [ -e "$link_path" ] || [ -L "$link_path" ];
                }; then
                    echo "  SKIP  agents/$agent_name (adapter or active path exists, use --force to overwrite)"
                    AGENT_SKIPPED=$((AGENT_SKIPPED + 1))
                    continue
                fi

                if { [ -e "$adapter_path" ] || [ -L "$adapter_path" ]; } && [ "$FORCE" = true ]; then
                    mkdir -p "$AGENT_BACKUP_DIR/adapters"
                    mv "$adapter_path" "$AGENT_BACKUP_DIR/adapters/"
                fi

                cp "$agent_file" "$adapter_path"

                if [ -L "$link_path" ]; then
                    mkdir -p "$AGENT_BACKUP_DIR/links"
                    mv "$link_path" "$AGENT_BACKUP_DIR/links/"
                elif [ -e "$link_path" ]; then
                    if [ "$FORCE" = false ]; then
                        echo "  SKIP  $AGENTS_DST/$agent_name (file exists, use --force to replace with symlink)"
                        AGENT_SKIPPED=$((AGENT_SKIPPED + 1))
                        continue
                    fi
                    mkdir -p "$AGENT_BACKUP_DIR/global"
                    mv "$link_path" "$AGENT_BACKUP_DIR/global/"
                fi

                ln -s "$adapter_path" "$link_path"
                AGENT_COUNT=$((AGENT_COUNT + 1))
            done

            echo "  OK    agents/ ($AGENT_COUNT symlinked via ~/.agents/adapters/claude, $AGENT_SKIPPED skipped)"
        fi
        [ -d "$REPO_DIR/scripts" ] && cp "$REPO_DIR/scripts/"*.sh "$TEAM_DIR/scripts/" 2>/dev/null && echo "  OK    scripts/"
    fi

    # Set executable permissions
    chmod +x "$TEAM_DIR/hooks/scripts/"*.sh 2>/dev/null
    chmod +x "$TEAM_DIR/scripts/"*.sh 2>/dev/null

    echo ""
    echo "Team system installed to $TEAM_DIR/"
    echo "Validator agents are installed to $TEAM_AGENTS_DIR/."
    if [ -n "${CLAUDE_CODE_GUIDE_TRANSACTION:-}" ]; then
        echo "Shared active agent adapters were left unchanged by the managed transaction."
    else
        echo "Claude agents are installed via $SHARED_CLAUDE_ADAPTERS symlinks."
    fi
    echo "Run 'bash $TEAM_DIR/scripts/validate-system.sh --project $TARGET --claude-home $CLAUDE_HOME' to verify."
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
