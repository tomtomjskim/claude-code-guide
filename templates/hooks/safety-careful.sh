#!/usr/bin/env bash
# Safety Careful Hook (PreToolUse: Bash)
# v3.2: 파괴적 명령 사전 차단
# exit 0 = 허용, exit 2 = 차단

set -euo pipefail

# stdin에서 tool input JSON 읽기
TOOL_INPUT=$(cat)
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

# 빈 명령이면 허용
[[ -z "$COMMAND" ]] && exit 0

# ── NightOps Trusted Context 예외 ──
# NightOps 스크립트 경로에서 실행되는 명령은 통과
NIGHTOPS_TRUSTED=(
  "/home/ubuntu/nightops/"
  "/home/ubuntu/scripts/lotto-fetch.sh"
  "/home/ubuntu/scripts/backup.sh"
  "/home/ubuntu/scripts/health-check.sh"
)
for pattern in "${NIGHTOPS_TRUSTED[@]}"; do
  if [[ "$COMMAND" == *"$pattern"* ]]; then
    exit 0
  fi
done

# ── Level 4: 절대 차단 (forbidden) ──
LEVEL4_PATTERNS=(
  'rm\s+-rf\s+/'                    # rm -rf / (루트)
  'rm\s+-rf\s+/home(?!/ubuntu/)'    # /home 아래 다른 사용자
  'DROP\s+DATABASE'                  # DB 전체 삭제
  'DROP\s+SCHEMA.*CASCADE'           # 스키마 캐스케이드 삭제
  'TRUNCATE\s+'                      # 테이블 데이터 전체 삭제
  'git\s+push\s+.*--force'           # 강제 푸시
  'git\s+push\s+.*-f\b'             # 강제 푸시 (short flag)
  'git\s+reset\s+--hard'            # 하드 리셋
  'mkfs\.'                           # 파일시스템 포맷
  'dd\s+.*of=/dev/'                  # 디스크 직접 쓰기
  ':(){.*};:'                        # fork bomb
  'chmod\s+-R\s+777\s+/'            # 루트 권한 변경
)

for pattern in "${LEVEL4_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qPi "$pattern"; then
    echo "BLOCKED: Level 4 forbidden command detected: $pattern" >&2
    exit 2
  fi
done

# ── Safe Exceptions: 빌드 아티팩트 정리 허용 ──
SAFE_DIRS=(
  "node_modules"
  ".next"
  "dist"
  "build"
  "__pycache__"
  ".pytest_cache"
  ".turbo"
  "coverage"
  ".nyc_output"
)

# rm -rf 명령이지만 safe 디렉토리 대상이면 허용
if echo "$COMMAND" | grep -qPi 'rm\s+-rf'; then
  for safe in "${SAFE_DIRS[@]}"; do
    if echo "$COMMAND" | grep -qP "(^|\s)rm\s+-rf\s+(\./|\.\./)?\S*${safe}\b"; then
      exit 0
    fi
  done
fi

# ── Level 3: 경고 (사용자 승인 필요) ──
LEVEL3_PATTERNS=(
  'ALTER\s+TABLE'                    # DB 스키마 변경
  'CREATE\s+TABLE'                   # 새 테이블 생성
  'DROP\s+TABLE'                     # 테이블 삭제
  'docker\s+rm\s+-f'                 # 컨테이너 강제 삭제
  'docker\s+container\s+rm'          # 컨테이너 삭제
  'kubectl\s+delete'                 # K8s 리소스 삭제
)

for pattern in "${LEVEL3_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qPi "$pattern"; then
    echo "WARNING: Level 3 caution command. Pattern: $pattern" >&2
    # exit 0으로 허용하되, Claude Code가 사용자에게 확인을 요청하도록 stderr 경고
    exit 0
  fi
done

# 기본: 허용
exit 0
