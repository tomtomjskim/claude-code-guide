#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  safety-careful.sh — 파괴적 명령 차단 Hook (PreToolUse)  ║
# ║  Bash 도구의 위험 명령을 사전 차단                        ║
# ╚══════════════════════════════════════════════════════════╝
#
# exit 0 = 허용  |  exit 2 = 차단 (stderr → 모델에 피드백)
#
# ── 등록: settings.local.json → hooks.PreToolUse[matcher:"Bash"] ──

# fail-open: hook 자체 오류 시 명령 허용
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
LEVEL4_PATTERNS=(
  'rm[[:space:]]+-rf[[:space:]]+/'          # rm -rf / (루트)
  'DROP[[:space:]]+DATABASE'                 # DB 전체 삭제
  'DROP[[:space:]]+SCHEMA.*CASCADE'          # 스키마 캐스케이드 삭제
  'TRUNCATE[[:space:]]+'                     # 테이블 데이터 전체 삭제
  'git[[:space:]]+push[[:space:]]+.*--force' # 강제 푸시
  'git[[:space:]]+push[[:space:]]+.*-f([[:space:]]|$)' # 강제 푸시 (short flag)
  'git[[:space:]]+reset[[:space:]]+--hard'   # 하드 리셋
  'mkfs\.'                                   # 파일시스템 포맷
  'dd[[:space:]]+.*of=/dev/'                 # 디스크 직접 쓰기
  'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/' # 루트 권한 변경
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
for pattern in "${TRUSTED_PATHS[@]}"; do
  if [[ -n "$pattern" && "$FIRST_TOKEN" == "$pattern"* ]]; then
    exit 0
  fi
done

# Level 4: 절대 차단
for pattern in "${LEVEL4_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qEi "$pattern" 2>/dev/null; then
    echo "BLOCKED: 파괴적 명령 감지 — $pattern" >&2
    exit 2
  fi
done

# Safe rm -rf 예외: 모든 피연산자가 safe 목록에 있어야 허용
if echo "$COMMAND" | grep -qEi 'rm[[:space:]]+-rf' 2>/dev/null; then
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
