#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  safety-freeze.sh — 보호 파일 수정 차단 Hook (PreToolUse)║
# ║  Edit/Write 도구로 동결 파일 수정 시 차단                 ║
# ╚══════════════════════════════════════════════════════════╝
#
# exit 0 = 허용  |  exit 2 = 차단
#
# ── 등록: settings.local.json → hooks.PreToolUse[matcher:"Edit","Write"] ──
#
# ── Dev mode bypass (P0-H2) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${CLAUDE_HOOK_TEST:-0}" = "1" ] \
   || [ -f "$SCRIPT_DIR/bypass" ] \
   || [ -f "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/hooks/bypass" ]; then
  echo "[hook-bypass] safety-freeze: dev mode, allow all" >&2
  exit 0
fi

# fail-open
TOOL_INPUT=$(cat 2>/dev/null || echo '{}')
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // ""' 2>/dev/null || echo "")
if [[ -z "$FILE_PATH" ]]; then exit 0; fi

# 경로 정규화
if command -v realpath &>/dev/null; then
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

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# ╰──────────────────────────────────────────╯

# Tier 1: 절대 수정 불가 (패턴 또는 정확한 경로)
FROZEN_TIER1=(
  # "*.env"                       # 환경변수 파일
  # "/etc/"                       # 시스템 설정
  # "/path/to/production.config"  # 프로덕션 설정
)

# Tier 2: 경고 (허용하되 stderr 경고)
FROZEN_TIER2=(
  # "docker-compose.yml"
  # ".claude/settings.json"
  # "package-lock.json"
)

# ╭──────────────────────────────────────────╮
# │      커스터마이징 영역 끝                  │
# ╰──────────────────────────────────────────╯

# Tier 1 체크
for frozen in "${FROZEN_TIER1[@]}"; do
  if [[ -z "$frozen" ]]; then continue; fi
  # 와일드카드 패턴
  if [[ "$frozen" == *"*"* ]]; then
    # shellcheck disable=SC2053
    if [[ "$(basename "$FILE_PATH")" == $frozen ]]; then
      echo "BLOCKED: 보호 파일 수정 불가 — $FILE_PATH (pattern: $frozen)" >&2
      exit 2
    fi
  # 디렉토리 경로
  elif [[ "$frozen" == */ ]]; then
    if [[ "$FILE_PATH" == "$frozen"* ]]; then
      echo "BLOCKED: 보호 디렉토리 내 파일 수정 불가 — $FILE_PATH" >&2
      exit 2
    fi
  # 정확한 경로 또는 파일명
  elif [[ "$frozen" == /* ]]; then
    # 절대 경로: 완전 일치
    if [[ "$FILE_PATH" == "$frozen" ]]; then
      echo "BLOCKED: 보호 파일 수정 불가 — $FILE_PATH" >&2
      exit 2
    fi
  else
    # 파일명: basename 비교
    if [[ "$(basename "$FILE_PATH")" == "$frozen" ]]; then
      echo "BLOCKED: 보호 파일 수정 불가 — $FILE_PATH (name: $frozen)" >&2
      exit 2
    fi
  fi
done

# Tier 2 체크
for frozen in "${FROZEN_TIER2[@]}"; do
  if [[ -z "$frozen" ]]; then continue; fi
  if [[ "$frozen" == /* ]]; then
    # 절대 경로: 완전 일치
    [[ "$FILE_PATH" == "$frozen" ]] || continue
  else
    # 파일명: basename 비교
    [[ "$(basename "$FILE_PATH")" == "$frozen" ]] || continue
  fi
  echo "WARNING: 보호 파일 수정 — $FILE_PATH (사용자 승인 필요)" >&2
  exit 0
done

exit 0
