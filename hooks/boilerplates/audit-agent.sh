#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  audit-agent.sh — Agent 호출 감사 로그 (PostToolUse)     ║
# ║  서브에이전트 호출 이력을 파일에 기록                      ║
# ╚══════════════════════════════════════════════════════════╝
#
# ── 등록: settings.local.json → hooks.PostToolUse[matcher:"Agent"] ──
#
# ── Dev mode bypass (P0-H2) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${CLAUDE_HOOK_TEST:-0}" = "1" ] \
   || [ -f "$SCRIPT_DIR/bypass" ] \
   || [ -f "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/hooks/bypass" ]; then
  exit 0
fi

# fail-open: hook 자체 오류 시 허용 (PostToolUse는 차단 불가)
# (기존 trap 'exit 0' ERR 제거 — set -e 없이 무효, 명시적 || exit 0 사용)

prepare_hook_state_dir() {
  local runtime_root owner current_uid
  runtime_root="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
  HOOK_STATE_DIR="${CLAUDE_HOOK_STATE_DIR:-$runtime_root/claude-code-guide-hooks-$(id -u)}"
  if [ -L "$HOOK_STATE_DIR" ]; then
    echo "[audit-agent] unsafe hook state symlink; audit log skipped: $HOOK_STATE_DIR" >&2
    return 1
  fi
  umask 077
  if ! mkdir -p -m 700 "$HOOK_STATE_DIR" 2>/dev/null; then
    echo "[audit-agent] hook state directory unavailable; audit log skipped: $HOOK_STATE_DIR" >&2
    return 1
  fi
  current_uid=$(id -u)
  owner=$(stat -c '%u' "$HOOK_STATE_DIR" 2>/dev/null \
    || stat -f '%u' "$HOOK_STATE_DIR" 2>/dev/null \
    || echo "")
  if [ "$owner" != "$current_uid" ] || [ ! -d "$HOOK_STATE_DIR" ] || [ -L "$HOOK_STATE_DIR" ]; then
    echo "[audit-agent] unsafe hook state ownership; audit log skipped: $HOOK_STATE_DIR" >&2
    return 1
  fi
  chmod 700 "$HOOK_STATE_DIR" 2>/dev/null || {
    echo "[audit-agent] hook state permissions unavailable; audit log skipped: $HOOK_STATE_DIR" >&2
    return 1
  }
}

INPUT=$(cat 2>/dev/null || echo '{}')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name' 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Agent" ]; then
  exit 0
fi

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# ╰──────────────────────────────────────────╯

# 로그 파일 경로. AGENT_AUDIT_LOG="" 이면 비활성화.
if [ "${AGENT_AUDIT_LOG+x}" = "x" ]; then
  LOG_FILE="$AGENT_AUDIT_LOG"
else
  prepare_hook_state_dir || exit 0
  LOG_FILE="$HOOK_STATE_DIR/agent-audit.log"
fi

# prompt 미리보기 최대 길이 (바이트)
PROMPT_PREVIEW_LENGTH=120

# ╭──────────────────────────────────────────╮
# │      커스터마이징 영역 끝                  │
# ╰──────────────────────────────────────────╯

[ -z "$LOG_FILE" ] && exit 0
if [ -L "$LOG_FILE" ]; then
  echo "[audit-agent] unsafe audit log symlink; audit log skipped: $LOG_FILE" >&2
  exit 0
fi
umask 077
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || exit 0

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
SESSION_ID=$(echo "$INPUT" | jq -jr '.session_id // "unknown"' 2>/dev/null \
  | tr '\n\r' '  ' | sed 's/"/\\"/g' || echo "unknown")

# 로그 주입 방지: 개행 → 공백, 따옴표 이스케이프
DESCRIPTION=$(echo "$INPUT" | jq -jr '.tool_input.description // ""' 2>/dev/null | tr '\n\r' '  ' | sed 's/"/\\"/g')
SUBAGENT_TYPE=$(echo "$INPUT" | jq -jr '.tool_input.subagent_type // "general-purpose"' 2>/dev/null \
  | tr '\n\r' '  ' | sed 's/"/\\"/g' || echo "unknown")
# UTF-8 안전 절단 (P2-L5): head -c는 바이트 단위라 한글 등 multibyte 중간에서 절단 가능
# iconv -c 로 invalid sequence(잘린 multibyte) 제거 후 sanitize
PROMPT_PREVIEW=$(echo "$INPUT" | jq -jr '.tool_input.prompt // ""' 2>/dev/null \
  | head -c "$PROMPT_PREVIEW_LENGTH" \
  | iconv -c -f UTF-8 -t UTF-8 2>/dev/null \
  | tr '\n\r' '  ' | sed 's/"/\\"/g')
# iconv 미설치 fallback
if [ -z "$PROMPT_PREVIEW" ] && [ -n "$DESCRIPTION" ]; then
  PROMPT_PREVIEW=$(echo "$INPUT" | jq -jr '.tool_input.prompt // ""' 2>/dev/null \
    | head -c "$PROMPT_PREVIEW_LENGTH" | tr '\n\r' '  ' | sed 's/"/\\"/g')
fi

echo "[$TIMESTAMP] session=$SESSION_ID type=$SUBAGENT_TYPE desc=\"$DESCRIPTION\" prompt=\"$PROMPT_PREVIEW...\"" >> "$LOG_FILE" 2>/dev/null || true
chmod 600 "$LOG_FILE" 2>/dev/null || true

exit 0
