#!/usr/bin/env bash
# Safety Freeze Hook (PreToolUse: Edit|Write)
# v3.2: 동결 파일 수정 차단
# exit 0 = 허용, exit 2 = 차단

set -euo pipefail

# stdin에서 tool input JSON 읽기
TOOL_INPUT=$(cat)
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // ""' 2>/dev/null || echo "")

# 빈 경로면 허용
[[ -z "$FILE_PATH" ]] && exit 0

# 경로 정규화 (symlink/traversal 우회 방지)
if command -v realpath &>/dev/null; then
  # 파일이 아직 없으면 디렉토리까지만 정규화
  if [[ -e "$FILE_PATH" ]]; then
    FILE_PATH=$(realpath "$FILE_PATH" 2>/dev/null || echo "$FILE_PATH")
  else
    DIR_PATH=$(dirname "$FILE_PATH")
    BASE_NAME=$(basename "$FILE_PATH")
    if [[ -d "$DIR_PATH" ]]; then
      FILE_PATH="$(realpath "$DIR_PATH")/$BASE_NAME"
    fi
  fi
fi

# ── Tier 1: 절대 수정 불가 ──
FROZEN_TIER1=(
  "/home/ubuntu/.env"
  "/home/ubuntu/scripts/backup.sh"
  "/etc/"
  "/root/"
)

for frozen in "${FROZEN_TIER1[@]}"; do
  if [[ "$FILE_PATH" == "$frozen"* ]]; then
    echo "BLOCKED: Tier 1 frozen file: $FILE_PATH" >&2
    exit 2
  fi
done

# ── Tier 2: 경고 (사용자 승인 필요) ──
FROZEN_TIER2=(
  "/home/ubuntu/docker-compose.yml"
  "/home/ubuntu/.claude/settings.json"
  "/home/ubuntu/nginx/nginx.conf"
)

for frozen in "${FROZEN_TIER2[@]}"; do
  if [[ "$FILE_PATH" == "$frozen" ]]; then
    echo "WARNING: Tier 2 protected file: $FILE_PATH — modification requires user approval" >&2
    # 허용하되 경고 출력 (Claude Code의 permission 시스템이 처리)
    exit 0
  fi
done

# ── NightOps Trusted Context ──
# NightOps 관련 파일 수정은 항상 허용
if [[ "$FILE_PATH" == /home/ubuntu/nightops/* ]]; then
  exit 0
fi

# 기본: 허용
exit 0
