#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  safety-careful.sh — 파괴적 명령 차단 Hook (PreToolUse)  ║
# ║  Bash 도구의 위험 명령을 사전 차단                        ║
# ╚══════════════════════════════════════════════════════════╝
#
# exit 0 = 허용  |  exit 2 = 차단 (stderr → 모델에 피드백)
#
# ── 등록: settings.local.json → hooks.PreToolUse[matcher:"Bash"] ──
#
# ── Dev mode bypass (P0-H2) ──
#   CLAUDE_HOOK_TEST=1  환경변수 설정 시 모든 체크 스킵
#   .claude/hooks/bypass 파일이 존재하면 모든 체크 스킵
#   → hook 자체 개발·테스트·문서화 시 self-block 회피용
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${CLAUDE_HOOK_TEST:-0}" = "1" ] \
   || [ -f "$SCRIPT_DIR/bypass" ] \
   || [ -f "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/hooks/bypass" ]; then
  echo "[hook-bypass] safety-careful: dev mode, allow all" >&2
  exit 0
fi

# fail-open: hook 자체 오류 시 명령 허용 (명시적, trap 의존 안 함 — P0-H3)
TOOL_INPUT=$(cat 2>/dev/null || echo '{}')
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
if [[ -z "$COMMAND" ]]; then exit 0; fi

# ╭──────────────────────────────────────────╮
# │         🔧 커스터마이징 영역              │
# ╰──────────────────────────────────────────╯

# 신뢰 경로: 이 경로로 시작하는 명령은 무조건 허용
# 자동화 스크립트, CI/CD 등 등록
TRUSTED_PATHS=(
  # "/home/ubuntu/scripts/deploy.sh"
  # "/opt/ci/run-tests.sh"
)

# Level 4 (절대 차단): 복구 불가능한 파괴적 명령 (ERE 패턴)
# P0-H1: 경로 기반 패턴은 `/` 루트 자체만 매칭하도록 앵커 — /tmp/foo 등 정상 경로 오탐 방지
LEVEL4_PATTERNS=(
  'rm[[:space:]]+-rf[[:space:]]+/([[:space:]]|$|\*)'   # rm -rf / (루트 자체만, /tmp/x 제외)
  'rm[[:space:]]+-rf[[:space:]]+~/?([[:space:]]|$|\*)' # rm -rf ~ (홈 자체)
  'rm[[:space:]]+-rf[[:space:]]+\$HOME([[:space:]]|$|/\*)' # rm -rf $HOME
  'DROP[[:space:]]+DATABASE'                 # DB 전체 삭제
  'DROP[[:space:]]+SCHEMA.*CASCADE'          # 스키마 캐스케이드 삭제
  'TRUNCATE[[:space:]]+'                     # 테이블 데이터 전체 삭제
  'git[[:space:]]+push[[:space:]]+.*--force' # 강제 푸시
  'git[[:space:]]+push[[:space:]]+.*-f([[:space:]]|$)' # 강제 푸시 (short flag)
  'git[[:space:]]+reset[[:space:]]+--hard'   # 하드 리셋
  'mkfs\.'                                   # 파일시스템 포맷
  'dd[[:space:]]+.*of=/dev/'                 # 디스크 직접 쓰기
  'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/([[:space:]]|$)' # 루트 권한 변경 (앵커 추가)
)

# Level 3 (경고): 주의 필요하지만 허용 가능한 명령
LEVEL3_PATTERNS=(
  'ALTER[[:space:]]+TABLE'                   # DB 스키마 변경
  'CREATE[[:space:]]+TABLE'                  # 새 테이블 생성
  'DROP[[:space:]]+TABLE'                    # 테이블 삭제
  'docker[[:space:]]+rm[[:space:]]+-f'       # 컨테이너 강제 삭제
  'kubectl[[:space:]]+delete'                # K8s 리소스 삭제
)

# rm -rf 허용 디렉토리 (빌드 아티팩트 등)
SAFE_RM_DIRS=(
  "node_modules"
  ".next"
  "dist"
  "build"
  "__pycache__"
  ".pytest_cache"
  "coverage"
)

# ╭──────────────────────────────────────────╮
# │      커스터마이징 영역 끝                  │
# ╰──────────────────────────────────────────╯

# 신뢰 경로 체크
FIRST_TOKEN=$(echo "$COMMAND" | awk '{print $1}')
FIRST_TOKEN_BASE=$(basename "$FIRST_TOKEN" 2>/dev/null || echo "$FIRST_TOKEN")
for pattern in "${TRUSTED_PATHS[@]}"; do
  if [[ -n "$pattern" && "$FIRST_TOKEN" == "$pattern"* ]]; then
    exit 0
  fi
done

# argv structure 체크 (P0-H4): echo/printf/주석이 first token이고 shell chaining이 없으면
# 위험 패턴은 문자열 리터럴로 간주 → 차단 스킵 (hook 자체 테스트/문서화 자기모순 해소)
# (chaining 감지는 보수적으로 — &&, ||, ;, |, $(), backtick 중 하나라도 있으면 일반 체크 진행)
ARGV_LITERAL_MODE=false
case "$FIRST_TOKEN_BASE" in
  echo|printf|\#*)
    if ! echo "$COMMAND" | grep -qE '(&&|\|\||;|`|\$\()' 2>/dev/null; then
      # |는 pipe인데 echo 문자열 안에 있을 수도 있음 — 보수적으로 pipe 뒤에 shell 명령 있는지 체크
      if ! echo "$COMMAND" | grep -qE '\|[[:space:]]*(bash|sh|zsh|xargs|eval)' 2>/dev/null; then
        ARGV_LITERAL_MODE=true
      fi
    fi
    ;;
esac

# Level 4: 절대 차단 (argv literal 모드에서는 스킵)
if [ "$ARGV_LITERAL_MODE" = false ]; then
  for pattern in "${LEVEL4_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qEi "$pattern" 2>/dev/null; then
      echo "BLOCKED: 파괴적 명령 감지 — $pattern" >&2
      echo "  (hook 테스트/문서화 상황이면 CLAUDE_HOOK_TEST=1 또는 .claude/hooks/bypass 사용)" >&2
      exit 2
    fi
  done
else
  echo "[info] echo/printf literal mode — Level 4 check skipped" >&2
fi

# Safe rm -rf 예외: 모든 피연산자가 safe 목록에 있어야 허용
# (argv literal 모드에서는 이 체크도 스킵 — echo/printf 안 문자열은 실행 대상 아님)
if [ "$ARGV_LITERAL_MODE" = false ] && echo "$COMMAND" | grep -qEi 'rm[[:space:]]+-rf' 2>/dev/null; then
  # rm ... -rf 이후의 피연산자 추출: rm과 플래그를 제거하고 경로만 남김
  OPERANDS=$(echo "$COMMAND" | sed -E 's/.*rm[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*//' | tr '&;|' '\n' | head -1 | tr ' ' '\n' | grep -v '^-' | grep -v '^$')

  if [ -n "$OPERANDS" ]; then
    ALL_SAFE=true
    while IFS= read -r operand; do
      [ -z "$operand" ] && continue
      OPERAND_SAFE=false
      OPERAND_BASE=$(basename "$operand")
      for safe in "${SAFE_RM_DIRS[@]}"; do
        if [[ "$OPERAND_BASE" == "$safe" ]]; then
          OPERAND_SAFE=true
          break
        fi
      done
      if [ "$OPERAND_SAFE" = false ]; then
        ALL_SAFE=false
        break
      fi
    done <<< "$OPERANDS"

    if [ "$ALL_SAFE" = true ]; then
      exit 0
    else
      echo "BLOCKED: rm -rf 대상에 허용 목록 외 경로 포함 — 확인 필요" >&2
      exit 2
    fi
  fi
fi

# Level 3: 경고 (허용하되 stderr 출력)
for pattern in "${LEVEL3_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qEi "$pattern" 2>/dev/null; then
    echo "WARNING: 주의 필요한 명령 — $pattern" >&2
    exit 0
  fi
done

exit 0
