#!/usr/bin/env bash
# Event-Driven Review Trigger (PostToolUse: Edit|Write)
# v3.2: 파일 변경 후 리뷰어 트리거 정보 기록
# 항상 exit 0 (PostToolUse는 워크플로우를 차단하지 않음)

# fail-open: hook 자체 오류 시 허용 (PostToolUse는 차단 불가)
TOOL_INPUT=$(cat 2>/dev/null || echo '{}')
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // ""' 2>/dev/null || echo "")
if [[ -z "$FILE_PATH" ]]; then exit 0; fi

# 트리거 기록 파일
TRIGGER_FILE="/home/ubuntu/.claude/team/context/review-triggers.log"
mkdir -p "$(dirname "$TRIGGER_FILE")"

# ── 파일 패턴 매칭 → 리뷰어 결정 ──
REVIEWERS=""

# 보안 관련
case "$FILE_PATH" in
  *auth* | *login* | *password* | *token* | *secret* | *crypto* | *session*)
    REVIEWERS="security-reviewer" ;;
  *.env* | *credentials* | *config/secret*)
    REVIEWERS="security-reviewer" ;;
esac

# API 관련
case "$FILE_PATH" in
  *routes/* | *api/* | *controller* | *endpoint* | *middleware*)
    REVIEWERS="${REVIEWERS:+$REVIEWERS,}api-reviewer" ;;
esac

# UI 관련
case "$FILE_PATH" in
  *.tsx | *.jsx | *.vue | *.svelte | *components/* | *pages/*)
    REVIEWERS="${REVIEWERS:+$REVIEWERS,}ux-reviewer,accessibility-reviewer" ;;
  *.css | *.scss | *.tailwind*)
    REVIEWERS="${REVIEWERS:+$REVIEWERS,}ux-reviewer" ;;
esac

# DB 관련
case "$FILE_PATH" in
  *migration* | *schema* | *.sql | *models/*)
    REVIEWERS="${REVIEWERS:+$REVIEWERS,}dba,performance-reviewer" ;;
esac

# 인프라 관련
case "$FILE_PATH" in
  *docker* | *nginx* | *Dockerfile* | *compose*)
    REVIEWERS="${REVIEWERS:+$REVIEWERS,}security-reviewer,publisher" ;;
esac

# 매칭된 리뷰어가 있으면 기록
if [[ -n "$REVIEWERS" ]]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $FILE_PATH | $REVIEWERS" >> "$TRIGGER_FILE"
fi

exit 0
