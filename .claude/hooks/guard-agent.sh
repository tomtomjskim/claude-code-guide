#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  guard-agent.sh — Agent 호출 제어 Hook (PreToolUse)      ║
# ║  서브에이전트 남용/탐색 용도 호출/토큰 낭비 방지           ║
# ╚══════════════════════════════════════════════════════════╝
#
# exit 0 = 허용  |  exit 2 = 차단 (stderr → 모델에 피드백)
#
# ── 설치: scripts/install-hooks.sh 또는 수동 복사 ──
# ── 등록: settings.local.json → hooks.PreToolUse[matcher:"Agent"] ──

# fail-open: hook 자체 오류(jq 미설치, JSON 파싱 실패 등) 시 허용
trap 'exit 0' ERR

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# │    프로젝트에 맞게 아래 변수를 수정하세요    │
# ╰──────────────────────────────────────────╯

# 차단할 subagent_type (공백 구분)
# - "Explore": 탐색 전용 에이전트
# - "Plan": 계획 수립 에이전트
# - 비워두면 타입 기반 차단 비활성화
BLOCKED_TYPES="Explore"

# 세션당 최대 Agent 호출 횟수 (0 = 무제한)
MAX_AGENT_CALLS=10

# 단순 작업 감지 임계값
# prompt가 이 길이 미만이고 파일이 이 개수 이하이면 차단
MIN_PROMPT_LENGTH=200
MIN_FILE_COUNT=2

# 탐색/분석 패턴 (PCRE, 대소문자 무시)
# 프로젝트 언어에 맞게 패턴 추가/제거
ANALYSIS_PATTERN='(explore\s+(the\s+)?code|search\s+(for|through)\s+files|find\s+(all|every|the)\s+(file|usage|reference|instance)|분석해|탐색해|조사해|파악해|찾아봐|검색해|살펴봐|확인해\s*봐)'

# 제약사항 키워드 (이 중 하나라도 있으면 "제약 있음"으로 판단)
CONSTRAINT_PATTERN='(금지|forbidden|must not|하지\s*마|do not|only modify|변경 범위|scope|제약)'

# 제약사항 미포함 시 동작: "warn" = 경고만 | "block" = 차단
CONSTRAINT_MISSING_ACTION="warn"

# 토큰 효율 기준: 서브에이전트 고정 오버헤드(~14k tokens)를 감안한 최소 작업 규모
# 파일 수가 이 값 미만이면 "메인이 직접 하는 게 효율적" 경고
# Rule 3(차단): files <= MIN_FILE_COUNT → Rule 5(경고): files < MIN_EFFICIENT_FILES
MIN_EFFICIENT_FILES=4

# ╭──────────────────────────────────────────╮
# │      커스터마이징 영역 끝                  │
# ╰──────────────────────────────────────────╯

# PCRE 가용 여부 체크 (macOS는 grep -P 미지원)
if echo "test" | grep -qP "test" 2>/dev/null; then
  GREP_MODE="-P"
else
  GREP_MODE="-E"
fi

# grep 래퍼: PCRE 우선, 미지원 시 ERE 호환 패턴으로 자동 전환
grep_compat() {
  local pattern="$1"
  if [ "$GREP_MODE" = "-P" ]; then
    grep -qi "$GREP_MODE" "$pattern" 2>/dev/null
  else
    # ERE: \s → [[:space:]], \b → 제거 (근사치)
    local ere_pattern
    ere_pattern=$(echo "$pattern" | sed -E 's/\\s/[[:space:]]/g; s/\\b//g')
    grep -qi "$GREP_MODE" "$ere_pattern" 2>/dev/null
  fi
}

INPUT=$(cat 2>/dev/null || echo '{}')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name' 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Agent" ]; then
  exit 0
fi

DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null || echo "")
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // ""' 2>/dev/null || echo "")
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // ""' 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")

# ── Rule 1: subagent_type 블랙리스트 ──
if [ -n "$BLOCKED_TYPES" ]; then
  for TYPE in $BLOCKED_TYPES; do
    if [ "$SUBAGENT_TYPE" = "$TYPE" ]; then
      echo "[BLOCKED] subagent_type='$TYPE' 사용 금지. 메인에서 직접 Read/Grep/Glob으로 수행하세요." >&2
      exit 2
    fi
  done
fi

# ── Rule 2: 분석/탐색 패턴 감지 (부정형 제외) ──
COMBINED="$DESCRIPTION $PROMPT"

# 부정어 패턴: 매칭 앞에 이 단어가 있으면 오탐으로 간주
NEGATION_PATTERN='(not|don'\''t|do not|하지|금지|않|마세요|마십시오|없이|말고)'

if echo "$COMBINED" | grep_compat "$ANALYSIS_PATTERN"; then
  # 부정형 체크: 매칭된 구간 앞 40자에 부정어가 있으면 스킵
  IS_NEGATED=false
  if [ "$GREP_MODE" = "-P" ]; then
    MATCH_CONTEXT=$(echo "$COMBINED" | grep -oiP ".{0,40}($ANALYSIS_PATTERN)" 2>/dev/null | head -1)
  else
    ERE_ANALYSIS=$(echo "$ANALYSIS_PATTERN" | sed -E 's/\\s/[[:space:]]/g; s/\\b//g')
    MATCH_CONTEXT=$(echo "$COMBINED" | grep -oiE ".{0,40}($ERE_ANALYSIS)" 2>/dev/null | head -1)
  fi
  if [ -n "$MATCH_CONTEXT" ]; then
    if echo "$MATCH_CONTEXT" | grep_compat "$NEGATION_PATTERN"; then
      IS_NEGATED=true
    fi
  fi

  if [ "$IS_NEGATED" = false ]; then
    echo "[BLOCKED] 분석/탐색 목적의 Agent 호출 감지. 메인에서 직접 Read/Grep/Glob을 사용하세요." >&2
    echo "감지된 패턴: description='$DESCRIPTION'" >&2
    exit 2
  fi
fi

# ── Rule 3: 단순 작업 감지 ──
PROMPT_LEN=${#PROMPT}
FILE_COUNT=$(echo "$PROMPT" | grep -oE '[a-zA-Z0-9_/.-]+\.(ts|tsx|js|jsx|py|php|css|scss|md|json|yaml|yml|sh|go|rs|java|rb|swift|kt)' | sort -u | wc -l | tr -d ' ')

if [ "$PROMPT_LEN" -lt "$MIN_PROMPT_LENGTH" ] && [ "$FILE_COUNT" -le "$MIN_FILE_COUNT" ]; then
  echo "[BLOCKED] 단순 작업(prompt ${PROMPT_LEN}자, 파일 ${FILE_COUNT}개)에 서브에이전트는 비효율적입니다." >&2
  echo "메인에서 직접 수행하세요. ${MIN_FILE_COUNT}개 초과 파일에 걸친 구현 작업만 서브에이전트를 사용합니다." >&2
  exit 2
fi

# ── Rule 4: 제약사항 포함 여부 ──
HAS_CONSTRAINTS=false
if echo "$PROMPT" | grep_compat "$CONSTRAINT_PATTERN"; then
  HAS_CONSTRAINTS=true
fi

if [ "$HAS_CONSTRAINTS" = false ]; then
  MSG="[WARNING] 서브에이전트 prompt에 작업 제약사항이 없습니다."
  MSG="$MSG\n서브에이전트는 Hook/rules 상속이 안 되므로, prompt에 다음을 포함하세요:"
  MSG="$MSG\n  - 변경 대상 파일 목록"
  MSG="$MSG\n  - 불필요한 탐색 금지 지시"
  MSG="$MSG\n  - 결과물 검증 기준"

  if [ "$CONSTRAINT_MISSING_ACTION" = "block" ]; then
    echo -e "$MSG" >&2
    exit 2
  else
    echo -e "$MSG" >&2
    echo "이번 호출은 허용하되, 향후 제약사항 포함을 권장합니다." >&2
  fi
fi

# ── Rule 5: 토큰 효율 경고 ──
# 서브에이전트 1회 = 고정 오버헤드 ~14k tokens (시스템 프롬프트 + 도구 스키마 + CLAUDE.md 중복)
# 파일 수가 적으면 메인이 직접 하는 게 토큰 효율적
if [ "$FILE_COUNT" -lt "$MIN_EFFICIENT_FILES" ] && [ "$FILE_COUNT" -gt "$MIN_FILE_COUNT" ]; then
  echo "[WARNING] 파일 ${FILE_COUNT}개 작업에 서브에이전트 오버헤드(~14k tokens)가 비효율적일 수 있습니다." >&2
  echo "  - ${MIN_EFFICIENT_FILES}개 이상 파일이면 서브에이전트 위임 권장" >&2
  echo "  - 단순 편집은 model:\"sonnet\" 지정으로 비용 절감 가능" >&2
  echo "  - 독립 작업 여러 개를 하나의 서브에이전트로 합치면 오버헤드 1회만 발생" >&2
fi

# ── Rule 6: 세션당 호출 횟수 제한 ──
if [ "$MAX_AGENT_CALLS" -gt 0 ]; then
  COUNT_DIR="/tmp/claude-hooks"
  mkdir -p "$COUNT_DIR"
  COUNT_FILE="$COUNT_DIR/agent-count-${SESSION_ID}"

  COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
  COUNT=$((COUNT + 1))
  echo "$COUNT" > "$COUNT_FILE"

  if [ "$COUNT" -gt "$MAX_AGENT_CALLS" ]; then
    echo "[BLOCKED] 세션당 Agent 호출 ${MAX_AGENT_CALLS}회 초과 (현재: ${COUNT}회). 메인에서 직접 작업하세요." >&2
    exit 2
  fi
fi

exit 0
