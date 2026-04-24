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

INPUT=$(cat 2>/dev/null || echo '{}')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name' 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Agent" ]; then
  exit 0
fi

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# ╰──────────────────────────────────────────╯

# 로그 파일 경로
LOG_DIR="/tmp/claude-hooks"
LOG_FILE="$LOG_DIR/agent-audit.log"

# prompt 미리보기 최대 길이 (바이트)
PROMPT_PREVIEW_LENGTH=120

# ╭──────────────────────────────────────────╮
# │      커스터마이징 영역 끝                  │
# ╰──────────────────────────────────────────╯

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")

# 로그 주입 방지: 개행 → 공백, 따옴표 이스케이프
DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null | tr '\n\r' '  ' | sed 's/"/\\"/g')
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // "general-purpose"' 2>/dev/null || echo "unknown")
PROMPT_PREVIEW=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null | head -c "$PROMPT_PREVIEW_LENGTH" | tr '\n\r' '  ' | sed 's/"/\\"/g')

echo "[$TIMESTAMP] session=$SESSION_ID type=$SUBAGENT_TYPE desc=\"$DESCRIPTION\" prompt=\"$PROMPT_PREVIEW...\"" >> "$LOG_FILE"

exit 0
