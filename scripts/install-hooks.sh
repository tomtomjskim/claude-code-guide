#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Claude Code Hook Installer v1.0                             ║
# ║  보일러플레이트 Hook을 프로젝트에 설치하고 settings에 등록     ║
# ╚══════════════════════════════════════════════════════════════╝
#
# Usage:
#   bash scripts/install-hooks.sh <target-project-path>
#   bash scripts/install-hooks.sh --hooks guard-agent,safety-careful /path/to/project
#   bash scripts/install-hooks.sh --list
#   bash scripts/install-hooks.sh --preset minimal /path/to/project

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
HOOKS_SRC="$REPO_DIR/hooks/boilerplates"

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

# ── Hook 카탈로그 ──
# name:matcher:event:description
HOOK_CATALOG=(
  "guard-agent:Agent:PreToolUse:서브에이전트 호출 제어 (탐색 차단, 횟수 제한, 제약사항 검증)"
  "safety-careful:Bash:PreToolUse:파괴적 Bash 명령 차단 (rm -rf /, DROP DATABASE 등)"
  "safety-freeze:Edit|Write:PreToolUse:보호 파일 수정 차단 (.env, 프로덕션 설정 등)"
  "audit-agent:Agent:PostToolUse:서브에이전트 호출 감사 로그 기록"
)

# ── 프리셋 정의 ──
PRESET_MINIMAL="guard-agent,safety-careful"
PRESET_STANDARD="guard-agent,safety-careful,safety-freeze,audit-agent"

# ── 인수 파싱 ──
FORCE=false
TARGET=""
SELECTED_HOOKS=()
PRESET=""
SKIP_SETTINGS=false

print_usage() {
    cat <<'USAGE'
Usage: bash scripts/install-hooks.sh [options] <target-project-path>

Options:
  --hooks <list>     설치할 Hook 선택 (쉼표 구분)
                     예: --hooks guard-agent,safety-careful
  --preset <name>    프리셋으로 일괄 설치
                     minimal:  guard-agent, safety-careful
                     standard: 전체 (기본값)
  --force            기존 Hook 덮어쓰기
  --no-settings      settings.local.json 자동 수정 건너뛰기
  --list             사용 가능한 Hook 목록 출력
  --help             도움말

Examples:
  bash scripts/install-hooks.sh /path/to/my-project
  bash scripts/install-hooks.sh --preset minimal /path/to/my-project
  bash scripts/install-hooks.sh --hooks guard-agent --force /path/to/my-project
USAGE
}

list_hooks() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║             사용 가능한 Hook 보일러플레이트                   ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    for entry in "${HOOK_CATALOG[@]}"; do
        IFS=':' read -r name matcher event desc <<< "$entry"
        printf "║  %-18s [%s → %s]\n" "$name" "$event" "$matcher"
        printf "║    %s\n" "$desc"
        echo "║                                                            ║"
    done
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  프리셋                                                     ║"
    echo "║    minimal:   guard-agent, safety-careful                   ║"
    echo "║    standard:  전체 Hook (기본값)                             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "각 Hook 파일 상단의 '🔧 커스터마이징 영역'에서 프로젝트별 설정을 조정하세요."
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)       FORCE=true; shift ;;
        --hooks)
            if [ -z "${2:-}" ] || [[ "$2" == --* ]]; then
                echo "ERROR: --hooks 옵션에 Hook 목록이 필요합니다."
                echo "  예: --hooks guard-agent,safety-careful"
                exit 1
            fi
            IFS=',' read -ra SELECTED_HOOKS <<< "$2"; shift 2 ;;
        --preset)
            if [ -z "${2:-}" ] || [[ "$2" == --* ]]; then
                echo "ERROR: --preset 옵션에 프리셋 이름이 필요합니다. (minimal | standard)"
                exit 1
            fi
            PRESET="$2"; shift 2 ;;
        --no-settings) SKIP_SETTINGS=true; shift ;;
        --list)        list_hooks; exit 0 ;;
        --help|-h)     print_usage; exit 0 ;;
        *)             TARGET="$1"; shift ;;
    esac
done

if [ -z "$TARGET" ]; then
    print_usage
    exit 1
fi

if [ -L "$TARGET" ]; then
    echo "ERROR: 대상 디렉토리는 symlink일 수 없습니다: $TARGET" >&2
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo "ERROR: 대상 디렉토리 '$TARGET'가 존재하지 않습니다." >&2
    exit 1
fi

TARGET="$(cd "$TARGET" && pwd -P)"

if [ ! -d "$HOOKS_SRC" ]; then
    echo "ERROR: 보일러플레이트 디렉토리를 찾을 수 없습니다: $HOOKS_SRC"
    echo "       claude-code-guide 레포 루트에서 실행하세요."
    exit 1
fi

# ── 프리셋 적용 ──
if [ -n "$PRESET" ]; then
    case "$PRESET" in
        minimal)  IFS=',' read -ra SELECTED_HOOKS <<< "$PRESET_MINIMAL" ;;
        standard) IFS=',' read -ra SELECTED_HOOKS <<< "$PRESET_STANDARD" ;;
        *)
            echo "ERROR: 알 수 없는 프리셋 '$PRESET'. (minimal | standard)"
            exit 1
            ;;
    esac
fi

# 선택 없으면 전체 설치
if [ ${#SELECTED_HOOKS[@]} -eq 0 ]; then
    for entry in "${HOOK_CATALOG[@]}"; do
        IFS=':' read -r name _ _ _ <<< "$entry"
        SELECTED_HOOKS+=("$name")
    done
fi

for hook_name in "${SELECTED_HOOKS[@]}"; do
    if [[ ! "$hook_name" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
        echo "ERROR: unsafe Hook name: $hook_name" >&2
        exit 1
    fi
    catalog_match=false
    for entry in "${HOOK_CATALOG[@]}"; do
        IFS=':' read -r cat_name _ _ _ <<< "$entry"
        if [ "$cat_name" = "$hook_name" ]; then
            catalog_match=true
            break
        fi
    done
    if [ "$catalog_match" = false ]; then
        echo "ERROR: Hook is not in the catalog: $hook_name" >&2
        exit 1
    fi
done

TARGET_HOOKS="$TARGET/.claude/hooks"
TARGET_SETTINGS="$TARGET/.claude/settings.local.json"
prepare_project_directory "$TARGET/.claude"
prepare_project_directory "$TARGET_HOOKS"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Claude Code Hook Installer v1.0                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Source:  $HOOKS_SRC"
echo "  Target:  $TARGET_HOOKS"
echo "  Hooks:   ${SELECTED_HOOKS[*]}"
echo "  Force:   $FORCE"
echo ""

# ── Hook 파일 복사 ──
INSTALLED=0
SKIPPED=0

for hook_name in "${SELECTED_HOOKS[@]}"; do
    SRC_FILE="$HOOKS_SRC/${hook_name}.sh"
    DST_FILE="$TARGET_HOOKS/${hook_name}.sh"

    if [ -L "$DST_FILE" ]; then
        echo "ERROR: Hook destination must not be a symlink: $DST_FILE" >&2
        exit 1
    fi

    if [ ! -f "$SRC_FILE" ]; then
        echo "  WARN  $hook_name — 보일러플레이트 파일 없음, 건너뜀"
        continue
    fi

    if [ -f "$DST_FILE" ] && [ "$FORCE" = false ]; then
        echo "  SKIP  $hook_name (이미 존재, --force로 덮어쓰기)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    if [ -n "${CLAUDE_CODE_GUIDE_TRANSACTION:-}" ]; then
        python3 "$SCRIPT_DIR/install_state.py" publish \
          --target "$TARGET" \
          --claude-home "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" \
          --snapshot "$CLAUDE_CODE_GUIDE_TRANSACTION" \
          --scope project \
          --path "hooks/${hook_name}.sh" \
          --source "$SRC_FILE"
    else
        cp "$SRC_FILE" "$DST_FILE"
        chmod +x "$DST_FILE"
    fi
    echo "  OK    $hook_name"
    INSTALLED=$((INSTALLED + 1))
done

# ── settings.local.json에 Hook 등록 ──
if [ "$SKIP_SETTINGS" = false ]; then
    echo ""
    echo "--- settings.local.json Hook 등록 ---"

    if [ -L "$TARGET_SETTINGS" ]; then
        echo "ERROR: settings destination must not be a symlink: $TARGET_SETTINGS" >&2
        exit 1
    fi

    # 기존 설정 읽기 또는 빈 객체 생성
    if [ -f "$TARGET_SETTINGS" ]; then
        SETTINGS=$(cat "$TARGET_SETTINGS")
    else
        SETTINGS='{}'
        mkdir -p "$(dirname "$TARGET_SETTINGS")"
    fi

    # Hook 등록을 위한 jq 스크립트 생성
    JQ_SCRIPT='.'

    for hook_name in "${SELECTED_HOOKS[@]}"; do
        # 카탈로그에서 매칭 정보 조회
        for entry in "${HOOK_CATALOG[@]}"; do
            IFS=':' read -r cat_name cat_matcher cat_event _ <<< "$entry"
            if [ "$cat_name" = "$hook_name" ]; then
                HOOK_CMD="bash .claude/hooks/${hook_name}.sh"

                # matcher가 "|"를 포함하면 분리하여 각각 등록
                IFS='|' read -ra MATCHERS <<< "$cat_matcher"
                for matcher in "${MATCHERS[@]}"; do
                    # 이미 등록되어 있는지 확인
                    EXISTING=$(echo "$SETTINGS" | jq -r \
                        --arg event "$cat_event" \
                        --arg matcher "$matcher" \
                        --arg cmd "$HOOK_CMD" \
                        '.hooks[$event] // [] | map(select(.matcher == $matcher)) | .[].hooks // [] | map(select(.command == $cmd)) | length' \
                        2>/dev/null || echo "0")

                    if [ "$EXISTING" != "0" ] && [ "$FORCE" = false ]; then
                        echo "  SKIP  settings: $cat_event[$matcher] → $hook_name (이미 등록됨)"
                        continue
                    fi

                    # jq로 Hook 항목 추가 (중복 방지)
                    SETTINGS=$(echo "$SETTINGS" | jq \
                        --arg event "$cat_event" \
                        --arg matcher "$matcher" \
                        --arg cmd "$HOOK_CMD" \
                        '
                        .hooks //= {} |
                        .hooks[$event] //= [] |
                        # 동일 matcher가 있으면 hooks 배열에 추가, 없으면 새 항목
                        if (.hooks[$event] | map(select(.matcher == $matcher)) | length) > 0
                        then
                          .hooks[$event] |= map(
                            if .matcher == $matcher
                            then .hooks += [{"type": "command", "command": $cmd}]
                                 | .hooks |= unique_by(.command)
                            else .
                            end
                          )
                        else
                          .hooks[$event] += [{"matcher": $matcher, "hooks": [{"type": "command", "command": $cmd}]}]
                        end
                        ')

                    echo "  OK    settings: $cat_event[$matcher] → $hook_name"
                done
                break
            fi
        done
    done

    SETTINGS_TMP=$(mktemp "${TARGET_SETTINGS}.tmp.XXXXXX")
    trap 'rm -f "$SETTINGS_TMP"' EXIT
    echo "$SETTINGS" | jq '.' > "$SETTINGS_TMP"
    if [ -n "${CLAUDE_CODE_GUIDE_TRANSACTION:-}" ]; then
        python3 "$SCRIPT_DIR/install_state.py" publish \
          --target "$TARGET" \
          --claude-home "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" \
          --snapshot "$CLAUDE_CODE_GUIDE_TRANSACTION" \
          --scope project \
          --path settings.local.json \
          --source "$SETTINGS_TMP"
    else
        mv "$SETTINGS_TMP" "$TARGET_SETTINGS"
    fi
    # CCG_SETTINGS_PUBLISHED
    trap - EXIT
    echo ""
    echo "  settings.local.json 업데이트 완료"
fi

# ── 결과 요약 ──
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  설치 완료                                                   ║"
echo "╠══════════════════════════════════════════════════════════════╣"
printf "║  설치됨: %-3d  건너뜀: %-3d                                   ║\n" "$INSTALLED" "$SKIPPED"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ $INSTALLED -gt 0 ]; then
    echo "다음 단계:"
    echo ""
    echo "  1. 각 Hook 파일의 '🔧 커스터마이징 영역'을 프로젝트에 맞게 수정하세요"
    echo ""

    for hook_name in "${SELECTED_HOOKS[@]}"; do
        DST_FILE="$TARGET_HOOKS/${hook_name}.sh"
        [ -f "$DST_FILE" ] && echo "     $DST_FILE"
    done

    echo ""
    echo "  2. 커스터마이징 예시:"
    echo ""

    for hook_name in "${SELECTED_HOOKS[@]}"; do
        case "$hook_name" in
            guard-agent)
                echo "     guard-agent.sh:"
                echo "       BLOCKED_TYPES=\"Explore Plan\"     # Plan도 차단하려면"
                echo "       MAX_AGENT_CALLS=5                 # 더 엄격하게"
                echo "       CONSTRAINT_MISSING_ACTION=\"block\" # 제약 없으면 차단"
                ;;
            safety-careful)
                echo "     safety-careful.sh:"
                echo "       TRUSTED_PATHS에 CI/CD 스크립트 경로 추가"
                echo "       LEVEL4_PATTERNS에 프로젝트별 위험 명령 추가"
                ;;
            safety-freeze)
                echo "     safety-freeze.sh:"
                echo "       FROZEN_TIER1에 절대 수정 불가 파일 추가"
                echo "       FROZEN_TIER2에 경고 대상 파일 추가"
                ;;
            audit-agent)
                echo "     audit-agent.sh:"
                echo "       LOG_DIR 경로를 프로젝트 로그 디렉토리로 변경"
                ;;
        esac
        echo ""
    done

    echo "  3. 테스트:"
    echo "     Claude Code를 재시작하면 Hook이 자동으로 적용됩니다."
    echo "     Agent 호출, Bash 명령 실행 시 Hook 동작을 확인하세요."
fi
