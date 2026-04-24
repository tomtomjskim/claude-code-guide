#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  hooks/tests/run-tests.sh — Hook 회귀 테스트 러너          ║
# ║  Bundle H-P0 (버그 수정) 보증용 테스트 스위트              ║
# ╚══════════════════════════════════════════════════════════╝
#
# Usage: bash hooks/tests/run-tests.sh
# 테스트 통과: exit 0, 실패: exit 1
#
# 각 테스트는:
#   1. stdin JSON 입력
#   2. hook 실행
#   3. exit code 비교 (expected)
#   4. 필요 시 stderr 내용 체크

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/hooks/boilerplates"

PASS=0
FAIL=0
FAILED_NAMES=()

# ──────────────────────────────────────────
# 테스트 헬퍼
# ──────────────────────────────────────────
# args: name, hook_script, expected_exit, stdin_json, [stderr_grep_pattern]
run_test() {
  local name="$1"
  local hook="$2"
  local expected="$3"
  local input="$4"
  local stderr_check="${5:-}"

  local actual_exit stderr_content
  stderr_content=$(echo "$input" | bash "$hook" 2>&1 >/dev/null)
  actual_exit=$?

  local stderr_pass=true
  if [ -n "$stderr_check" ]; then
    if ! echo "$stderr_content" | grep -qE "$stderr_check"; then
      stderr_pass=false
    fi
  fi

  if [ "$actual_exit" = "$expected" ] && [ "$stderr_pass" = "true" ]; then
    echo "  ✓ $name"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $name"
    echo "    expected exit: $expected, actual: $actual_exit"
    [ -n "$stderr_check" ] && echo "    stderr pattern: $stderr_check"
    [ -n "$stderr_content" ] && echo "    stderr: $(echo "$stderr_content" | head -3)"
    FAIL=$((FAIL + 1))
    FAILED_NAMES+=("$name")
  fi
}

# ──────────────────────────────────────────
# safety-careful.sh 테스트
# ──────────────────────────────────────────
echo ""
echo "=== safety-careful.sh ==="

HOOK="$HOOKS_DIR/safety-careful.sh"

# P0-H1: rm -rf / 앵커 — 정상 절대경로는 Level 4에 걸리지 않음
# (단, Safe rm policy로 SAFE_RM_DIRS 외부는 여전히 차단 — 이는 별도 정책, P1에서 논의)
# 여기서는 "Level 4 message가 안 나옴"을 확인
run_test "rm -rf /tmp/foo — Level 4 메시지 아닌 Safe rm 메시지 (P0-H1 anchor 정상)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}' \
  "허용 목록 외 경로"

run_test "rm -rf /var/log/app — 동일" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /var/log/app"}}' \
  "허용 목록 외 경로"

# P0-H1: rm -rf / 앵커 — 진짜 루트는 차단
run_test "rm -rf / 차단 (루트 단독)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  "BLOCKED"

run_test "rm -rf /* 차단 (루트 글로브)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /*"}}' \
  "BLOCKED"

# P0-H4: argv literal — echo/printf는 위험 패턴 포함해도 허용
run_test "echo rm -rf / (문자열 리터럴) 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"echo rm -rf /"}}'

run_test "printf DROP DATABASE 허용 (문자열 리터럴)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"printf %s DROP DATABASE foo"}}'

# P0-H4: shell chaining이 있으면 argv literal 모드 해제 — 차단 복귀
run_test "echo && rm -rf / (chaining) 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo foo && rm -rf /"}}' \
  "BLOCKED"

run_test "echo; rm -rf / (semicolon) 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo foo; rm -rf /"}}' \
  "BLOCKED"

run_test "echo | bash (pipe to shell) — literal 모드 해제" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo rm -rf / | bash"}}' \
  "BLOCKED"

# P0-H2: Dev mode bypass (env variable — export로 bash process에 전달)
export CLAUDE_HOOK_TEST=1
bypass_exit=$(echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
bypass_exit=$(echo "$bypass_exit" | tail -1)
unset CLAUDE_HOOK_TEST
if [ "$bypass_exit" = "0" ]; then
  echo "  ✓ CLAUDE_HOOK_TEST=1 env bypass 작동 (safety-careful)"
  PASS=$((PASS + 1))
else
  echo "  ✗ CLAUDE_HOOK_TEST=1 env bypass 실패 (exit $bypass_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("env bypass")
fi

# P0-H2: bypass 파일 방식
BYPASS_FILE="$HOOKS_DIR/bypass"
touch "$BYPASS_FILE"
bypass_file_exit=$(echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
bypass_file_exit=$(echo "$bypass_file_exit" | tail -1)
rm -f "$BYPASS_FILE"
if [ "$bypass_file_exit" = "0" ]; then
  echo "  ✓ .claude/hooks/bypass 파일 bypass 작동"
  PASS=$((PASS + 1))
else
  echo "  ✗ bypass 파일 방식 실패 (exit $bypass_file_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("bypass file")
fi

# 진짜 위험 명령 통제 (앵커 수정과 별개)
run_test "DROP DATABASE 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"mysql -e \"DROP DATABASE foo\""}}' \
  "BLOCKED"

run_test "git push --force 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
  "BLOCKED"

run_test "mkfs.ext4 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"mkfs.ext4 /dev/sda1"}}' \
  "BLOCKED"

# 정상 명령 통과
run_test "ls -la 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

run_test "npm install 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"npm install typescript"}}'

# Safe rm -rf 예외 (node_modules 등)
run_test "rm -rf node_modules 허용 (SAFE_RM_DIRS)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf node_modules"}}'

run_test "rm -rf dist 허용 (SAFE_RM_DIRS)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf dist"}}'

# ──────────────────────────────────────────
# guard-agent.sh 테스트
# ──────────────────────────────────────────
echo ""
echo "=== guard-agent.sh ==="

HOOK="$HOOKS_DIR/guard-agent.sh"

# P0-H2: Dev mode bypass (env variable — export 로 bash에 전달)
export CLAUDE_HOOK_TEST=1
guard_bypass_exit=$(echo '{"tool_name":"Agent","tool_input":{"subagent_type":"Explore","description":"test","prompt":"short"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
guard_bypass_exit=$(echo "$guard_bypass_exit" | tail -1)
unset CLAUDE_HOOK_TEST
if [ "$guard_bypass_exit" = "0" ]; then
  echo "  ✓ CLAUDE_HOOK_TEST=1 env bypass 작동 (guard-agent)"
  PASS=$((PASS + 1))
else
  echo "  ✗ CLAUDE_HOOK_TEST=1 env bypass 실패 (guard-agent, exit $guard_bypass_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("guard-agent bypass")
fi

# Non-Agent tool은 즉시 통과
run_test "Bash tool은 guard-agent 대상 아님 (즉시 허용)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"ls"}}'

# BLOCKED_TYPES: Explore는 차단
run_test "subagent_type Explore 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"Explore","description":"explore code","prompt":"x"}}' \
  "BLOCKED"

# ──────────────────────────────────────────
# 결과 요약
# ──────────────────────────────────────────
echo ""
echo "=========================================="
echo "  통과: $PASS / 실패: $FAIL"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "실패 테스트:"
  for name in "${FAILED_NAMES[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

exit 0
