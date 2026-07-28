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
#
# ── Fail 정책 (P2-H9, 의도된 비대칭) ──
#   ▸ fail-open  (시스템 에러):  jq 미설치 / JSON 파싱 실패 → exit 0 (Agent 허용)
#   ▸ fail-closed (정책 위반):   subagent_type 블랙리스트 / 강한 탐색 의도 패턴
#                                → exit 2 (차단)
#   비대칭 근거: jq 같은 시스템 도구 부재로 Agent 호출 자체를 막으면 사용자
#                작업 흐름이 깨짐. 정책 매칭(BLOCKED_TYPES, ANALYSIS_*)은
#                의도적으로 정의된 경계라 차단이 안전. 오탐은 CUSTOMIZE 또는
#                CLAUDE_HOOK_TEST=1 로 우회.
#
# ── Dev mode bypass (P0-H2) ──
#   CLAUDE_HOOK_TEST=1  환경변수 설정 시 모든 체크 스킵
#   .claude/hooks/bypass 파일이 존재하면 모든 체크 스킵
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${CLAUDE_HOOK_TEST:-0}" = "1" ] \
   || [ -f "$SCRIPT_DIR/bypass" ] \
   || [ -f "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/hooks/bypass" ]; then
  echo "[hook-bypass] guard-agent: dev mode, allow all" >&2
  exit 0
fi

HOOK_STATE_DIR=""
prepare_hook_state_dir() {
  if [ -n "$HOOK_STATE_DIR" ]; then
    return 0
  fi
  local runtime_root owner current_uid
  runtime_root="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
  HOOK_STATE_DIR="${CLAUDE_HOOK_STATE_DIR:-$runtime_root/claude-code-guide-hooks-$(id -u)}"
  if [ -L "$HOOK_STATE_DIR" ]; then
    echo "[guard-agent] unsafe hook state symlink; persistent checks skipped: $HOOK_STATE_DIR" >&2
    HOOK_STATE_DIR=""
    return 1
  fi
  umask 077
  if ! mkdir -p -m 700 "$HOOK_STATE_DIR" 2>/dev/null; then
    echo "[guard-agent] hook state directory unavailable; persistent checks skipped: $HOOK_STATE_DIR" >&2
    HOOK_STATE_DIR=""
    return 1
  fi
  current_uid=$(id -u)
  owner=$(stat -c '%u' "$HOOK_STATE_DIR" 2>/dev/null \
    || stat -f '%u' "$HOOK_STATE_DIR" 2>/dev/null \
    || echo "")
  if [ "$owner" != "$current_uid" ] || [ ! -d "$HOOK_STATE_DIR" ] || [ -L "$HOOK_STATE_DIR" ]; then
    echo "[guard-agent] unsafe hook state ownership; persistent checks skipped: $HOOK_STATE_DIR" >&2
    HOOK_STATE_DIR=""
    return 1
  fi
  chmod 700 "$HOOK_STATE_DIR" 2>/dev/null || {
    echo "[guard-agent] hook state permissions unavailable; persistent checks skipped: $HOOK_STATE_DIR" >&2
    HOOK_STATE_DIR=""
    return 1
  }
}

hash_session_id() {
  if command -v sha256sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 256 | awk '{print $1}'
  else
    printf '%s' "$1" | cksum | awk '{print $1 "-" $2}'
  fi
}

# fail-open: hook 자체 오류 시 허용 (명시적 || exit 0 패턴 — P0-H3)
# (기존 trap 'exit 0' ERR 제거: set -e 없이는 대부분의 에러에서 발동 안 됨)

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# │    프로젝트에 맞게 아래 변수를 수정하세요    │
# ╰──────────────────────────────────────────╯

# 차단할 subagent_type (공백 구분) — P2-H11 설계 의도 명시
#
# 설계 원칙: "탐색-only 에이전트"만 기본 차단. 구현 가능한 에이전트는 허용.
#   ▸ Explore  : 탐색 전용 (Read/Grep/Glob만) — 메인이 직접 하는 게 토큰 효율적
#   ▸ Plan     : 계획 수립 — 계획은 보통 토큰 가치 충분히 함
#                (단, 단순 계획에 Plan 스폰 시 비효율, MIN_PROMPT_LENGTH로 추가 가드)
#   ▸ general-purpose : 범용 — 구현/리뷰까지 가능, 차단 시 정상 워크플로우 막힘
#
# 보수적 차단 원하면 "Explore Plan general-purpose" 등으로 확장.
# 비워두면 타입 기반 차단 비활성화 (Rule 1 스킵).
#
# 참고: subagent 토큰 효율은 BLOCKED_TYPES 외에도 Rule 3 (단순 작업)·Rule 5
# (토큰 효율 경고)에서 별도로 가드. 모델 비용 자체는 model_routing(agents.yaml)
# 으로 분리 관리.
BLOCKED_TYPES="Explore"

# 세션당 최대 Agent 호출 횟수 (P2-H12)
#
# ⚠️ heuristic — 보안 경계 아님. 실 사용 시나리오(PM 오케스트레이션 +
#    specialist 4-6명 + retry 버퍼) 고려 시 10은 과도하게 타이트.
#    기본 50으로 완화. 더 엄격 원하면 MAX_AGENT_CALLS=10 으로 override.
# 비활성: MAX_AGENT_CALLS=0 (무제한)
# 환경변수 우선: 호출자가 export 한 값이 있으면 그 값 사용
MAX_AGENT_CALLS="${MAX_AGENT_CALLS:-50}"

# 단순 작업 감지 임계값 (P1-H6)
# ⚠️ heuristic — 보안 경계 아님. "짧은 prompt = 단순 작업"이라는 가정.
#    실제 보안 결정은 prompt 내용 검토 필요. 이 휴리스틱은 토큰 효율 권고용.
# 비활성: MIN_PROMPT_LENGTH=0 환경변수로 설정 (Rule 3 전체 스킵)
# 환경변수 우선: 호출자가 export 한 값이 있으면 그 값을, 없으면 default 사용
MIN_PROMPT_LENGTH="${MIN_PROMPT_LENGTH:-200}"
MIN_FILE_COUNT="${MIN_FILE_COUNT:-2}"

# 탐색/분석 패턴 (PCRE, 대소문자 무시) — P1-H5: 2-tier 매칭으로 오탐 축소
#
# STRONG 패턴: 단독 매칭만으로 차단 (명확한 광범위 탐색 의도)
ANALYSIS_STRONG_PATTERN='(explore\s+(the\s+)?(entire\s+)?(code|codebase|project)|search\s+through\s+(all|every|the\s+entire)|find\s+(all|every)\s+(file|usage|reference|instance|occurrence)|코드베이스\s*전체\s*(탐색|분석|조사)|전수\s*조사|모든\s*파일\s*검색|전체\s*분석)'
#
# WEAK 패턴: SCOPE_HINT와 같이 매칭해야만 차단 (일반 동사라 단독 매칭 시 오탐)
# 예: "이 함수 확인해 봐" 는 SCOPE 없으므로 통과,
#     "전체 코드 확인해 봐" 는 SCOPE("전체") + WEAK("확인해") 매칭 → 차단
ANALYSIS_WEAK_PATTERN='(분석해|탐색해|조사해|파악해|찾아봐|검색해|살펴봐|확인해\s*봐)'

# 광범위 SCOPE 힌트 — WEAK 매칭과 같이 나오면 진짜 탐색 의도로 판단
SCOPE_HINT_PATTERN='(전체|모든|전수|every\s+(file|module)|all\s+(files|modules)|across|throughout|entire\s+(codebase|repo|project)|코드베이스|디렉토리\s*전체)'

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
  # 1회 안내 (P2-M1) — ERE fallback 사용 중임을 알림 (영문 word boundary 정확도 영향)
  # 같은 세션 동안 반복 출력 방지
  GREP_NOTICE_FILE=""
  prepare_hook_state_dir && GREP_NOTICE_FILE="$HOOK_STATE_DIR/grep-fallback-notice"
  if [ -z "$GREP_NOTICE_FILE" ] || [ ! -f "$GREP_NOTICE_FILE" ]; then
    echo "[guard-agent] note: grep -P (PCRE) 미지원 — ERE fallback 사용 중." >&2
    echo "  영문 word boundary (\\b) 정확도 손실 가능. 정확한 PCRE 원하면: brew install grep" >&2
    [ -n "$GREP_NOTICE_FILE" ] && touch "$GREP_NOTICE_FILE" 2>/dev/null
  fi
fi

# grep 래퍼: PCRE 우선, 미지원 시 ERE 호환 패턴으로 자동 전환 (P1-H8)
#
# PCRE → ERE 변환 시 정확도 손실 항목:
#   - \b (word boundary): 한글에 영향 미미하나 영어 단어 경계 정확도 ↓
#   - (?=...) lookahead: 미지원 → 패턴 제거 시 부정어 검사 정확도 ↓
#   - (?:...) non-capturing: ERE는 capturing group (...)으로 변환 가능
#
# 정확한 PCRE 필요 시: brew install grep (gnu-grep) → ggrep 사용 가능
# 또는 settings에서 USE_PCRE 환경변수 강제 (현재 자동 감지)
grep_compat() {
  local pattern="$1"
  if [ "$GREP_MODE" = "-P" ]; then
    grep -qi "$GREP_MODE" "$pattern" 2>/dev/null
  else
    # ERE 변환 (P1-H8 개선):
    local ere_pattern
    ere_pattern=$(echo "$pattern" | sed -E '
      s/\\s/[[:space:]]/g
      s/\\S/[^[:space:]]/g
      s/\\b//g
      s/\(\?:/(/g
      s/\(\?=[^)]*\)//g
      s/\(\?![^)]*\)//g
    ')
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
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id | select(type == "string") // ""' 2>/dev/null || echo "")

# ── Rule 1: subagent_type 블랙리스트 ──
if [ -n "$BLOCKED_TYPES" ]; then
  for TYPE in $BLOCKED_TYPES; do
    if [ "$SUBAGENT_TYPE" = "$TYPE" ]; then
      echo "[BLOCKED] subagent_type='$TYPE' 사용 금지. 메인에서 직접 Read/Grep/Glob으로 수행하세요." >&2
      exit 2
    fi
  done
fi

# ── Rule 2: 분석/탐색 패턴 감지 (P1-H5 — 2-tier 매칭) ──
COMBINED="$DESCRIPTION $PROMPT"

# 부정어 패턴: 매칭 앞에 이 단어가 있으면 오탐으로 간주
NEGATION_PATTERN='(not|don'\''t|do not|하지|금지|않|마세요|마십시오|없이|말고)'

# 매칭 전략:
#   1. STRONG 패턴 단독 매칭 → 강한 탐색 의도 (즉시 차단 후보)
#   2. WEAK + SCOPE 동시 매칭 → 약한 동사 + 광범위 scope (차단 후보)
#   3. WEAK만 매칭 → "이 함수 확인해 봐" 같은 일반 검토 (스킵, 차단 안함)
ANALYSIS_REASON=""
ANALYSIS_PATTERN_USED=""

if echo "$COMBINED" | grep_compat "$ANALYSIS_STRONG_PATTERN"; then
  ANALYSIS_REASON="STRONG (광범위 탐색 의도)"
  ANALYSIS_PATTERN_USED="$ANALYSIS_STRONG_PATTERN"
elif echo "$COMBINED" | grep_compat "$ANALYSIS_WEAK_PATTERN" \
     && echo "$COMBINED" | grep_compat "$SCOPE_HINT_PATTERN"; then
  ANALYSIS_REASON="WEAK + SCOPE_HINT"
  ANALYSIS_PATTERN_USED="$ANALYSIS_WEAK_PATTERN"
fi

if [ -n "$ANALYSIS_REASON" ]; then
  # 부정형 체크: 매칭된 구간 앞 40자에 부정어가 있으면 스킵
  IS_NEGATED=false
  if [ "$GREP_MODE" = "-P" ]; then
    MATCH_CONTEXT=$(echo "$COMBINED" | grep -oiP ".{0,40}($ANALYSIS_PATTERN_USED)" 2>/dev/null | head -1)
  else
    ERE_ANALYSIS=$(echo "$ANALYSIS_PATTERN_USED" | sed -E '
      s/\\s/[[:space:]]/g
      s/\\S/[^[:space:]]/g
      s/\\b//g
      s/\(\?:/(/g
      s/\(\?=[^)]*\)//g
      s/\(\?![^)]*\)//g
    ')
    MATCH_CONTEXT=$(echo "$COMBINED" | grep -oiE ".{0,40}($ERE_ANALYSIS)" 2>/dev/null | head -1)
  fi
  if [ -n "$MATCH_CONTEXT" ]; then
    if echo "$MATCH_CONTEXT" | grep_compat "$NEGATION_PATTERN"; then
      IS_NEGATED=true
    fi
  fi

  if [ "$IS_NEGATED" = false ]; then
    echo "[BLOCKED] 분석/탐색 목적의 Agent 호출 감지 ($ANALYSIS_REASON)" >&2
    echo "메인에서 직접 Read/Grep/Glob을 사용하세요." >&2
    echo "감지된 description: '$DESCRIPTION'" >&2
    echo "(오탐이면 prompt에 부정어 추가 또는 CLAUDE_HOOK_TEST=1 사용)" >&2
    exit 2
  fi
fi

# ── Rule 3: 단순 작업 감지 (P1-H6 — heuristic, MIN_PROMPT_LENGTH=0 비활성) ──
PROMPT_LEN=${#PROMPT}
FILE_COUNT=$(echo "$PROMPT" | grep -oE '[a-zA-Z0-9_/.-]+\.(ts|tsx|js|jsx|py|php|css|scss|md|json|yaml|yml|sh|go|rs|java|rb|swift|kt)' | sort -u | wc -l | tr -d ' ')

if [ "$MIN_PROMPT_LENGTH" -gt 0 ] && [ "$PROMPT_LEN" -lt "$MIN_PROMPT_LENGTH" ] && [ "$FILE_COUNT" -le "$MIN_FILE_COUNT" ]; then
  echo "[BLOCKED] 단순 작업(prompt ${PROMPT_LEN}자, 파일 ${FILE_COUNT}개)에 서브에이전트는 비효율적입니다." >&2
  echo "메인에서 직접 수행하세요. ${MIN_FILE_COUNT}개 초과 파일에 걸친 구현 작업만 서브에이전트를 사용합니다." >&2
  echo "(이 휴리스틱 비활성화: MIN_PROMPT_LENGTH=0 설정)" >&2
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
  if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "unknown" ]; then
    echo "[guard-agent] session_id missing; Agent call counter skipped (fail-open)." >&2
    exit 0
  fi
  if ! prepare_hook_state_dir; then
    exit 0
  fi
  find "$HOOK_STATE_DIR" -maxdepth 1 -type f -name 'agent-count-*' \
    -mtime +7 -delete 2>/dev/null || true
  SESSION_KEY=$(hash_session_id "$SESSION_ID")
  COUNT_FILE="$HOOK_STATE_DIR/agent-count-${SESSION_KEY}"
  if [ -L "$COUNT_FILE" ]; then
    echo "[guard-agent] unsafe counter symlink; Agent call counter skipped (fail-open)." >&2
    exit 0
  fi
  umask 077
  : >> "$COUNT_FILE" 2>/dev/null || {
    echo "[guard-agent] counter unavailable; Agent call counter skipped (fail-open)." >&2
    exit 0
  }
  chmod 600 "$COUNT_FILE" 2>/dev/null || {
    echo "[guard-agent] counter permissions unavailable; Agent call counter skipped (fail-open)." >&2
    exit 0
  }
  exec 9<> "$COUNT_FILE"
  if ! command -v flock >/dev/null 2>&1; then
    echo "[guard-agent] flock unavailable; Agent call counter skipped (fail-open)." >&2
    exit 0
  fi
  flock -x 9 || {
    echo "[guard-agent] counter lock unavailable; Agent call counter skipped (fail-open)." >&2
    exit 0
  }
  COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
  case "$COUNT" in
    ''|*[!0-9]*) COUNT=0 ;;
  esac
  COUNT=$((COUNT + 1))
  printf '%s\n' "$COUNT" > "$COUNT_FILE"
  flock -u 9

  if [ "$COUNT" -gt "$MAX_AGENT_CALLS" ]; then
    echo "[BLOCKED] 세션당 Agent 호출 ${MAX_AGENT_CALLS}회 초과 (현재: ${COUNT}회). 메인에서 직접 작업하세요." >&2
    exit 2
  fi
fi

exit 0
