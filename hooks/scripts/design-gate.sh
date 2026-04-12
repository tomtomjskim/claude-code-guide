#!/bin/bash
# design-gate.sh — 디자인 컨벤션 위반 감지 (PostToolUse:Edit|Write)
# 하드코딩된 색상/폰트 사용 시 경고
#
# 등록: settings.json → hooks.PostToolUse에 추가
# { "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "bash hooks/scripts/design-gate.sh" }] }

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 프론트엔드 파일만 검사
case "$FILE" in
  *.tsx|*.jsx|*.vue|*.svelte|*.css|*.scss)
    ;;
  *)
    exit 0
    ;;
esac

# 파일 존재 확인
[ -f "$FILE" ] || exit 0

VIOLATIONS=""

# 1. 하드코딩된 hex 색상 감지 (CSS 변수 내 정의, 주석, token-override 표시 제외)
HEX_COUNT=$(grep -P '#[0-9a-fA-F]{3,8}' "$FILE" 2>/dev/null | grep -v 'var(--' | grep -v '//' | grep -v 'token-override' | grep -v '^\s*\*' | grep -v '^\s*--' | wc -l | tr -d ' ')

if [ "$HEX_COUNT" -gt 0 ]; then
  VIOLATIONS="${VIOLATIONS}하드코딩 색상 ${HEX_COUNT}건 감지. CSS 변수 토큰(var(--primary) 등) 사용 권장. "
fi

# 2. 금지 폰트 감지 (디자인 시스템 외 폰트)
if grep -PiqE "font-family:.*\b(Arial|Helvetica|Times|Roboto|Inter)\b" "$FILE" 2>/dev/null; then
  VIOLATIONS="${VIOLATIONS}디자인 시스템 외 폰트 사용 감지. 프로젝트 font-family 토큰 확인 필요. "
fi

# 3. 임의 픽셀값 감지 (4px 단위가 아닌 값)
ODD_PX=$(grep -PoE '\b[0-9]+px' "$FILE" 2>/dev/null | grep -vE '^(0|4|8|12|16|20|24|28|32|36|40|44|48|52|56|60|64)px$' | head -5 | wc -l | tr -d ' ')
if [ "$ODD_PX" -gt 2 ]; then
  VIOLATIONS="${VIOLATIONS}4px 단위가 아닌 간격값 ${ODD_PX}건. --space-* 토큰 또는 Tailwind 유틸리티 사용 권장. "
fi

if [ -n "$VIOLATIONS" ]; then
  echo "{\"decision\": \"warn\", \"reason\": \"디자인 컨벤션 경고: ${VIOLATIONS}\"}"
  exit 0
fi
